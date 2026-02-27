---
title: Answer Sheet ML Inference
emoji: 📄
colorFrom: blue
colorTo: green
sdk: docker
app_file: app.py
pinned: false
---

# HuggingFace Spaces ML Inference Setup

This directory contains the ML inference service that runs on HuggingFace Spaces and is called by the main Render application.

## Setup Instructions

### 1. Create HuggingFace Space

1. Go to https://huggingface.co/spaces
2. Click "Create new Space"
3. Fill in:
   - **Space name**: `answer-sheet-ml` (or your preferred name)
   - **Owner**: Select your account
   - **License**: MIT
   - **Space SDK**: Docker
   - **Docker public availability**: No
4. Click "Create Space"

### 2. Upload Files to the Space

Push this directory to the Space repository:

```bash
# Clone the space
git clone https://huggingface.co/spaces/YOUR-USERNAME/answer-sheet-ml
cd answer-sheet-ml

# Copy files from this directory
cp -r ..../hf_space/* .

# Copy model weights
cp ../models/*.pt models/
cp ../models/*.pth models/

# Git add, commit, push
git add .
git commit -m "Initial ML inference setup"
git push
```

### 3. Create models/ Directory on Space

Once pushed, the Space will start building. After the Docker build completes, use the HuggingFace web UI to create a `models/` folder and upload your model weights:

- `improved_weights.pt` (YOLO model)
- `best_crnn_model(git).pth` (Register CRNN)
- `best_subject_model_final.pth` (Subject CRNN)

Or add them via git:

```bash
mkdir models
cp ../exam_middleware/models/*.pt models/
cp ../exam_middleware/models/*.pth models/
git add models/
git commit -m "Add model weights"
git push
```

### 4. Dockerfile

Create a `Dockerfile` in the space with:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 libsm6 libxrender1 libxcb1 \
    poppler-utils gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and models
COPY app.py .
COPY models/ models/

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:7860/health').read()"

# Run app
CMD ["python", "app.py"]
```

### 5. Get the Inference URL

Once the Space is running:
- Go to your space page
- Look for the "Use this Space" section → "API" tab
- The API URL will be: `https://YOUR-USERNAME-answer-sheet-ml.hf.space`

### 6. Update Render App Config

In your Render app's `.env` or config:

```env
HF_SPACE_URL=https://YOUR-USERNAME-answer-sheet-ml.hf.space
```

Or set it as a Render environment variable in the dashboard.

---

## Model Files

The space expects these model weights in the `models/` directory:

| File | Size | Purpose |
|------|------|---------|
| `improved_weights.pt` | ~200MB | YOLO object detection for register/subject regions |
| `best_crnn_model(git).pth` | ~50MB | CRNN for register number OCR |
| `best_subject_model_final.pth` | ~50MB | CRNN for subject code OCR |

## Testing Locally

To test the inference service locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Run app
python app.py

# Test extraction
curl -X POST http://localhost:7860/extract \
  -F "file=@test_image.pdf"
```

## API Endpoints

- `GET /health` - Health check
- `GET /status` - Model availability status
- `POST /extract` - Extract from uploaded file (PDF, JPG, PNG, etc.)
- `POST /extract/base64` - Extract from base64-encoded data

## Notes

- The Space uses CPU for inference by default. Consider upgrading to GPU for faster processing.
- Models are loaded once on startup and kept in memory for subsequent requests.
- The service is stateless and can handle concurrent requests.
