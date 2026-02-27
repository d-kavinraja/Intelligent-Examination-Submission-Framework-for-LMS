"""
HuggingFace Spaces ML Inference API
Provides answer sheet extraction endpoints using YOLO + CRNN models.

This runs on HF Spaces and is called by the Render app via HTTP.
"""

import os
import logging
import tempfile
from pathlib import Path
from typing import Optional
import base64
import io

import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from torchvision import transforms
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import structlog

logger = structlog.get_logger(__name__)

# ============================================================================
# App setup
# ============================================================================
app = FastAPI(title="Answer Sheet ML Inference", version="1.0.0")

# ============================================================================
# Model paths (will be in same directory as this file)
# ============================================================================
SPACE_DIR = Path(__file__).resolve().parent
MODELS_DIR = SPACE_DIR / "models"

# Create models dir if it doesn't exist
MODELS_DIR.mkdir(exist_ok=True)

PRIMARY_YOLO_WEIGHTS = MODELS_DIR / "improved_weights.pt"
FALLBACK_YOLO_WEIGHTS = MODELS_DIR / "weights.pt"
REGISTER_CRNN_WEIGHTS = MODELS_DIR / "best_crnn_model(git).pth"
SUBJECT_CRNN_WEIGHTS = MODELS_DIR / "best_subject_model_final.pth"

# ============================================================================
# CRNN Model Architecture
# ============================================================================
class CRNN(nn.Module):
    def __init__(self, num_classes: int):
        super().__init__()
        self.cnn = nn.Sequential(
            nn.Conv2d(1, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),
            nn.Dropout2d(0.3),
            nn.Conv2d(128, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(),
            nn.Conv2d(256, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(),
            nn.MaxPool2d((2, 1), (2, 1)),
            nn.Conv2d(256, 512, kernel_size=3, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(),
            nn.Conv2d(512, 512, kernel_size=3, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(),
            nn.MaxPool2d((2, 1), (2, 1)),
            nn.Dropout2d(0.3),
            nn.Conv2d(512, 512, kernel_size=(2, 1)),
            nn.BatchNorm2d(512),
            nn.ReLU(),
        )
        self.rnn = nn.LSTM(512, 256, num_layers=2, bidirectional=True, dropout=0.3)
        self.dropout = nn.Dropout(0.5)
        self.fc = nn.Linear(512, num_classes)

    def forward(self, x):
        x = self.cnn(x)
        x = x.squeeze(2)
        x = x.permute(2, 0, 1)
        x, _ = self.rnn(x)
        x = self.dropout(x)
        x = self.fc(x)
        return x


def _clean_state_dict(raw):
    """Remove 'module.' prefix from DataParallel state dict."""
    sd = raw.get("model_state_dict", raw)
    cleaned = {}
    for k, v in sd.items():
        cleaned[k.removeprefix("module.")] = v
    return cleaned


# ============================================================================
# Singleton Extractor
# ============================================================================
_extractor_instance: Optional['AnswerSheetExtractor'] = None


class AnswerSheetExtractor:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info("AI device", device=self.device)

        # ---- YOLO (detection) ------------------------------------------------
        try:
            from ultralytics import YOLO
            if not PRIMARY_YOLO_WEIGHTS.exists():
                raise FileNotFoundError(f"Primary YOLO weights not found: {PRIMARY_YOLO_WEIGHTS}")
            self.primary_yolo = YOLO(str(PRIMARY_YOLO_WEIGHTS))
            logger.info("Primary YOLO model loaded")

            self.fallback_yolo = None
            if FALLBACK_YOLO_WEIGHTS.exists():
                self.fallback_yolo = YOLO(str(FALLBACK_YOLO_WEIGHTS))
                logger.info("Fallback YOLO model loaded")
        except Exception as e:
            logger.error("YOLO loading error", error=str(e))
            raise

        # ---- CRNN for register numbers ----------------------------------------
        try:
            self.register_crnn = CRNN(num_classes=11).to(self.device)
            ckpt = torch.load(str(REGISTER_CRNN_WEIGHTS), map_location=self.device, weights_only=False)
            self.register_crnn.load_state_dict(_clean_state_dict(ckpt))
            self.register_crnn.eval()
            logger.info("Register CRNN model loaded")
        except Exception as e:
            logger.error("Register CRNN loading error", error=str(e))
            raise

        # ---- CRNN for subject codes -------------------------------------------
        try:
            self.subject_crnn = CRNN(num_classes=37).to(self.device)
            ckpt2 = torch.load(str(SUBJECT_CRNN_WEIGHTS), map_location=self.device, weights_only=False)
            self.subject_crnn.load_state_dict(_clean_state_dict(ckpt2))
            self.subject_crnn.eval()
            logger.info("Subject CRNN model loaded")
        except Exception as e:
            logger.error("Subject CRNN loading error", error=str(e))
            raise

        # ---- Transforms -------------------------------------------------------
        self.register_transform = transforms.Compose([
            transforms.Resize((32, 256)),
            transforms.ToTensor(),
            transforms.Normalize((0.5,), (0.5,)),
        ])
        self.subject_transform = transforms.Compose([
            transforms.Resize((32, 128)),
            transforms.ToTensor(),
            transforms.Normalize((0.5,), (0.5,)),
        ])

        # Character map for subject code
        self.char_map = {i: str(i - 1) for i in range(1, 11)}
        self.char_map.update({i: chr(i - 11 + ord("A")) for i in range(11, 37)})
        self.char_map[0] = ""

    def _detect_regions(self, image: np.ndarray):
        """Run YOLO and return register and subject regions."""
        results = self.primary_yolo(image)
        boxes = results[0].boxes
        names = results[0].names

        reg_regions = []
        sub_regions = []

        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])
            label = names[int(box.cls[0])]
            crop = image[y1:y2, x1:x2]

            if label == "RegisterNumber" and conf > 0.5:
                reg_regions.append((crop, conf))
            elif label == "SubjectCode" and conf > 0.5:
                sub_regions.append((crop, conf))

        # Fallback for subject code
        if not sub_regions and self.fallback_yolo is not None:
            logger.info("Primary YOLO missed SubjectCode — trying fallback")
            fb_results = self.fallback_yolo(image)
            fb_boxes = fb_results[0].boxes
            fb_names = fb_results[0].names
            for box in fb_boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])
                label = fb_names[int(box.cls[0])]
                if label == "SubjectCode" and conf > 0.5:
                    crop = image[y1:y2, x1:x2]
                    sub_regions.append((crop, conf))

        return reg_regions, sub_regions

    def _extract_register_number(self, crop: np.ndarray) -> tuple:
        """Return (decoded_text, confidence)."""
        try:
            gray = crop[:, :, ::-1] if len(crop.shape) == 3 else crop
            pil = Image.fromarray(gray).convert("L")
            tensor = self.register_transform(pil).unsqueeze(0).to(self.device)
            with torch.no_grad():
                out = self.register_crnn(tensor).squeeze(1)
                probs = out.softmax(1)
                max_probs, preds = probs.max(1)
                seq = preds.cpu().numpy()
                conf_vals = max_probs.cpu().numpy()
                prev = -1
                result = []
                confs = []
                for s, c in zip(seq, conf_vals):
                    if s != 0 and s != prev:
                        result.append(s - 1)
                        confs.append(c)
                    prev = s
            text = "".join(map(str, result))
            avg_conf = float(np.mean(confs)) if confs else 0.0
            return text, avg_conf
        except Exception as e:
            logger.error("Register extraction error", error=str(e))
            return "", 0.0

    def _extract_subject_code(self, crop: np.ndarray) -> tuple:
        """Return (decoded_text, confidence)."""
        try:
            gray = crop[:, :, ::-1] if len(crop.shape) == 3 else crop
            pil = Image.fromarray(gray).convert("L")
            tensor = self.subject_transform(pil).unsqueeze(0).to(self.device)
            with torch.no_grad():
                out = self.subject_crnn(tensor).squeeze(1)
                probs = out.softmax(1)
                max_probs, preds = probs.max(1)
                seq = preds.cpu().numpy()
                conf_vals = max_probs.cpu().numpy()
                prev = 0
                result = []
                confs = []
                for s, c in zip(seq, conf_vals):
                    if s != prev:
                        result.append(self.char_map.get(int(s), ""))
                        confs.append(c)
                    prev = s
            text = "".join(result)
            avg_conf = float(np.mean(confs)) if confs else 0.0
            return text, avg_conf
        except Exception as e:
            logger.error("Subject extraction error", error=str(e))
            return "", 0.0

    def extract_from_image(self, image: np.ndarray) -> dict:
        """Run full extraction pipeline on numpy image."""
        try:
            reg_regions, sub_regions = self._detect_regions(image)

            register_numbers = []
            for crop, conf in reg_regions:
                text, text_conf = self._extract_register_number(crop)
                if text:
                    register_numbers.append({"value": text, "confidence": text_conf, "detection_confidence": conf})

            subject_codes = []
            for crop, conf in sub_regions:
                text, text_conf = self._extract_subject_code(crop)
                if text:
                    subject_codes.append({"value": text, "confidence": text_conf, "detection_confidence": conf})

            best_register = max(register_numbers, key=lambda x: x["confidence"])["value"] if register_numbers else ""
            best_subject = max(subject_codes, key=lambda x: x["confidence"])["value"] if subject_codes else ""

            return {
                "success": True,
                "register_number": best_register,
                "subject_code": best_subject,
                "register_candidates": register_numbers,
                "subject_candidates": subject_codes,
            }
        except Exception as e:
            logger.error("Extraction pipeline error", error=str(e))
            return {"success": False, "error": str(e)}

    def extract_from_bytes(self, file_bytes: bytes, filename: str = "image") -> dict:
        """Extract from file bytes (PDF or image)."""
        try:
            ext = Path(filename).suffix.lower()

            if ext == ".pdf":
                from pdf2image import convert_from_bytes
                images = convert_from_bytes(file_bytes)
                if not images:
                    return {"success": False, "error": "Could not extract images from PDF"}
                image = np.array(images[0])
            else:
                image = Image.open(io.BytesIO(file_bytes))
                image = np.array(image)
                if len(image.shape) == 2:
                    image = np.stack([image] * 3, axis=-1)

            return self.extract_from_image(image)
        except Exception as e:
            logger.error("Bytes extraction error", error=str(e), filename=filename)
            return {"success": False, "error": str(e)}


def get_extractor() -> AnswerSheetExtractor:
    """Get or create the singleton extractor."""
    global _extractor_instance
    if _extractor_instance is None:
        logger.info("Loading extraction models for the first time")
        _extractor_instance = AnswerSheetExtractor()
        logger.info("Extraction models ready")
    return _extractor_instance


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Answer Sheet ML Inference",
        "version": "1.0.0",
        "endpoints": ["/health", "/status", "/extract", "/extract/base64"]
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "Answer Sheet ML Inference"}


@app.get("/status")
async def extraction_status():
    """Check model availability."""
    try:
        extractor = get_extractor()
        return {
            "ready": True,
            "device": str(extractor.device),
            "primary_yolo": PRIMARY_YOLO_WEIGHTS.exists(),
            "register_crnn": REGISTER_CRNN_WEIGHTS.exists(),
            "subject_crnn": SUBJECT_CRNN_WEIGHTS.exists(),
        }
    except Exception as e:
        return {
            "ready": False,
            "error": str(e),
            "primary_yolo": PRIMARY_YOLO_WEIGHTS.exists(),
            "register_crnn": REGISTER_CRNN_WEIGHTS.exists(),
            "subject_crnn": SUBJECT_CRNN_WEIGHTS.exists(),
        }


@app.post("/extract")
async def extract_endpoint(file: UploadFile = File(...)):
    """Extract register number and subject code from uploaded file."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    allowed_ext = (".pdf", ".jpg", ".jpeg", ".png", ".bmp", ".tiff")
    ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in allowed_ext:
        raise HTTPException(status_code=400, detail=f"Unsupported file type '{ext}'")

    try:
        extractor = get_extractor()
        file_data = await file.read()
        result = extractor.extract_from_bytes(file_data, file.filename)
        return JSONResponse(content=result)
    except Exception as e:
        logger.error("Extraction endpoint error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@app.post("/extract/base64")
async def extract_base64_endpoint(image_data: str):
    """Extract from base64-encoded image/PDF."""
    try:
        file_bytes = base64.b64decode(image_data)
        extractor = get_extractor()
        result = extractor.extract_from_bytes(file_bytes, "image")
        return JSONResponse(content=result)
    except Exception as e:
        logger.error("Base64 extraction error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


# ============================================================================
# Entry point
# ============================================================================
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
