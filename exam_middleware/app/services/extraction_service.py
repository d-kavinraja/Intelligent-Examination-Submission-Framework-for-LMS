"""
Extraction Service — YOLO + CRNN pipeline for extracting
register number and subject code from scanned answer sheets.

Models are loaded lazily on first extraction request to save memory.
"""

import os
import logging
import tempfile
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from torchvision import transforms

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model directory — resolve relative to this file → exam_middleware/models/
# ---------------------------------------------------------------------------
MODELS_DIR = Path(__file__).resolve().parent.parent.parent / "models"

PRIMARY_YOLO_WEIGHTS = MODELS_DIR / "improved_weights.pt"
FALLBACK_YOLO_WEIGHTS = MODELS_DIR / "weights.pt"  # optional
REGISTER_CRNN_WEIGHTS = MODELS_DIR / "best_crnn_model(git).pth"
SUBJECT_CRNN_WEIGHTS = MODELS_DIR / "best_subject_model_final.pth"


# ---------------------------------------------------------------------------
# CRNN architecture (must match training code exactly)
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Helper: strip DataParallel 'module.' prefix from state-dict keys
# ---------------------------------------------------------------------------
def _clean_state_dict(raw):
    sd = raw.get("model_state_dict", raw)
    cleaned = {}
    for k, v in sd.items():
        cleaned[k.removeprefix("module.")] = v
    return cleaned


# ---------------------------------------------------------------------------
# Singleton extractor — loaded once, reused across requests
# ---------------------------------------------------------------------------
_extractor_instance: "AnswerSheetExtractor | None" = None


def get_extractor() -> "AnswerSheetExtractor":
    """Return (or lazily create) the global AnswerSheetExtractor."""
    global _extractor_instance
    if _extractor_instance is None:
        logger.info("Loading extraction models for the first time …")
        _extractor_instance = AnswerSheetExtractor()
        logger.info("Extraction models loaded successfully.")
    return _extractor_instance


def is_extraction_available() -> bool:
    """Check whether the required model weight files exist."""
    return PRIMARY_YOLO_WEIGHTS.exists() and REGISTER_CRNN_WEIGHTS.exists() and SUBJECT_CRNN_WEIGHTS.exists()


# ---------------------------------------------------------------------------
# Main extractor class
# ---------------------------------------------------------------------------
class AnswerSheetExtractor:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # ---- YOLO (detection) ------------------------------------------------
        from ultralytics import YOLO

        if not PRIMARY_YOLO_WEIGHTS.exists():
            raise FileNotFoundError(f"Primary YOLO weights not found: {PRIMARY_YOLO_WEIGHTS}")
        self.primary_yolo = YOLO(str(PRIMARY_YOLO_WEIGHTS))

        self.fallback_yolo = None
        if FALLBACK_YOLO_WEIGHTS.exists():
            self.fallback_yolo = YOLO(str(FALLBACK_YOLO_WEIGHTS))
            logger.info("Fallback YOLO model loaded.")
        else:
            logger.warning("Fallback YOLO weights not found — will use primary model only.")

        # ---- CRNN for register numbers (10 digits + blank = 11 classes) ------
        self.register_crnn = CRNN(num_classes=11).to(self.device)
        ckpt = torch.load(str(REGISTER_CRNN_WEIGHTS), map_location=self.device, weights_only=False)
        self.register_crnn.load_state_dict(_clean_state_dict(ckpt))
        self.register_crnn.eval()

        # ---- CRNN for subject codes (blank + 0-9 + A-Z = 37 classes) --------
        self.subject_crnn = CRNN(num_classes=37).to(self.device)
        ckpt2 = torch.load(str(SUBJECT_CRNN_WEIGHTS), map_location=self.device, weights_only=False)
        self.subject_crnn.load_state_dict(_clean_state_dict(ckpt2))
        self.subject_crnn.eval()

        # ---- Transforms ------------------------------------------------------
        self.register_transform = transforms.Compose([
            transforms.Grayscale(num_output_channels=1),
            transforms.Resize((32, 256)),
            transforms.ToTensor(),
            transforms.Normalize((0.5,), (0.5,)),
        ])
        self.subject_transform = transforms.Compose([
            transforms.Grayscale(num_output_channels=1),
            transforms.Resize((32, 128)),
            transforms.ToTensor(),
            transforms.Normalize((0.5,), (0.5,)),
        ])

        # Character map for subject code: index 0 = blank, 1-10 = digits 0-9, 11-36 = A-Z
        self.char_map = {i: str(i - 1) for i in range(1, 11)}
        self.char_map.update({i: chr(i - 11 + ord("A")) for i in range(11, 37)})
        self.char_map[0] = ""

    # ------------------------------------------------------------------
    # Region detection (YOLO)
    # ------------------------------------------------------------------
    def _detect_regions(self, image: np.ndarray):
        """
        Run YOLO on the image and return lists of
        (cropped_ndarray, confidence) for register and subject regions.
        """
        h, w = image.shape[:2]
        PADDING = 10  # px around each detection box (prevents edge chars from being cut)
        CONF_THRESH = 0.2  # match the working Streamlit threshold

        def _padded_crop(img, x1, y1, x2, y2):
            """Crop with padding, clamped to image boundaries."""
            px1 = max(0, x1 - PADDING)
            py1 = max(0, y1 - PADDING)
            px2 = min(w, x2 + PADDING)
            py2 = min(h, y2 + PADDING)
            return img[py1:py2, px1:px2]

        results = self.primary_yolo(image)
        boxes = results[0].boxes
        names = results[0].names

        reg_regions: list[tuple[np.ndarray, float]] = []
        sub_regions: list[tuple[np.ndarray, float]] = []

        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])
            label = names[int(box.cls[0])]
            # Clamp to image boundaries
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)
            if x1 >= x2 or y1 >= y2:
                continue

            crop = _padded_crop(image, x1, y1, x2, y2)

            if label == "RegisterNumber" and conf > CONF_THRESH:
                reg_regions.append((crop, conf))
            elif label == "SubjectCode" and conf > CONF_THRESH:
                sub_regions.append((crop, conf))

        # Fallback YOLO for BOTH register and subject if either is missing
        if (not reg_regions or not sub_regions) and self.fallback_yolo is not None:
            missing = []
            if not reg_regions:
                missing.append("RegisterNumber")
            if not sub_regions:
                missing.append("SubjectCode")
            logger.info(f"Primary YOLO missed regions — trying fallback: {missing}")

            fb_results = self.fallback_yolo(image)
            fb_boxes = fb_results[0].boxes
            fb_names = fb_results[0].names
            for box in fb_boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])
                label = fb_names[int(box.cls[0])]
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(w, x2), min(h, y2)
                if x1 >= x2 or y1 >= y2:
                    continue

                crop = _padded_crop(image, x1, y1, x2, y2)

                if label == "RegisterNumber" and conf > CONF_THRESH and not reg_regions:
                    reg_regions.append((crop, conf))
                elif label == "SubjectCode" and conf > CONF_THRESH and not sub_regions:
                    sub_regions.append((crop, conf))

        return reg_regions, sub_regions

    # ------------------------------------------------------------------
    # CRNN inference helpers
    # ------------------------------------------------------------------
    def _extract_register_number(self, crop: np.ndarray) -> tuple[str, float]:
        """Return (decoded_text, confidence)."""
        try:
            # Convert BGR numpy array → grayscale PIL without cv2
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
            logger.error(f"Register extraction error: {e}")
            return "", 0.0

    def _extract_subject_code(self, crop: np.ndarray) -> tuple[str, float]:
        """Return (decoded_text, confidence)."""
        try:
            # Convert BGR numpy array → grayscale PIL without cv2
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
                    if s != 0 and s != prev:
                        result.append(self.char_map.get(s, ""))
                        confs.append(c)
                    prev = s
            text = "".join(result)
            avg_conf = float(np.mean(confs)) if confs else 0.0
            return text, avg_conf
        except Exception as e:
            logger.error(f"Subject extraction error: {e}")
            return "", 0.0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def extract_from_image(self, image: np.ndarray) -> dict:
        """
        Run the full pipeline on a single OpenCV image (BGR).
        Returns dict with register_number, subject_code, and confidence scores.
        """
        reg_regions, sub_regions = self._detect_regions(image)

        register_number = ""
        register_confidence = 0.0
        subject_code = ""
        subject_confidence = 0.0

        # Best register region by detection confidence
        if reg_regions:
            best_crop = max(reg_regions, key=lambda x: x[1])[0]
            register_number, register_confidence = self._extract_register_number(best_crop)

        # Subject code: if >=2 regions, pick the second (matches training heuristic)
        if sub_regions:
            if len(sub_regions) >= 2:
                chosen = sub_regions[1][0]
            else:
                chosen = sub_regions[0][0]
            subject_code, subject_confidence = self._extract_subject_code(chosen)

        return {
            "register_number": register_number,
            "register_confidence": round(register_confidence * 100, 1),
            "subject_code": subject_code,
            "subject_confidence": round(subject_confidence * 100, 1),
            "regions_found": {
                "register_regions": len(reg_regions),
                "subject_regions": len(sub_regions),
            },
        }

    def extract_from_file(self, file_path: str) -> dict:
        """
        Run extraction on a file (image or PDF).
        For PDFs, only the first page is processed.
        """
        ext = Path(file_path).suffix.lower()

        if ext == ".pdf":
            # Convert first page to image
            try:
                from pdf2image import convert_from_path
                images = convert_from_path(file_path, dpi=300, first_page=1, last_page=1)
                if not images:
                    return {"error": "Could not convert PDF to image"}
                # PIL gives RGB, convert to BGR numpy for YOLO
                image = np.array(images[0])[:, :, ::-1]
            except ImportError:
                return {"error": "pdf2image not installed — cannot process PDFs"}
            except Exception as e:
                return {"error": f"PDF conversion failed: {e}"}
        elif ext in (".jpg", ".jpeg", ".png", ".bmp", ".tiff"):
            # Load image with PIL, convert RGB→BGR numpy for YOLO
            image = np.array(Image.open(file_path).convert("RGB"))[:, :, ::-1]
            if image is None or image.size == 0:
                return {"error": f"Could not read image: {file_path}"}
        else:
            return {"error": f"Unsupported file type: {ext}"}

        return self.extract_from_image(image)

    def extract_from_bytes(self, data: bytes, filename: str) -> dict:
        """
        Run extraction on raw file bytes.
        Writes to a temp file, processes, then cleans up.
        """
        ext = Path(filename).suffix.lower() or ".pdf"
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name

        try:
            return self.extract_from_file(tmp_path)
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
