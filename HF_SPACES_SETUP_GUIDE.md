# HuggingFace Spaces ML Inference Setup Guide

## Overview

This guide walks you through setting up ML inference on HuggingFace Spaces to offload model inference from Render. This approach:

✅ **Reduces Render costs** — no heavy ML models/dependencies  
✅ **Faster inference** — HF Spaces supports GPU acceleration  
✅ **Better resource management** — separates ML and web app concerns  
✅ **Automatic fallback** — app uses local extraction if HF Space is unavailable  

---

## Step 1: Create the HuggingFace Space

### 1a. Create Account & API Token

1. Go to https://huggingface.co and sign up (or log in)
2. Go to Settings → Access Tokens
3. Create a new token with **write** access
4. Save it securely (you'll need it for git operations)

### 1b. Create the Space

1. Go to https://huggingface.co/spaces
2. Click **"Create new Space"**
3. Fill in details:
   - **Space name**: `answer-sheet-ml` (or your preferred name)
   - **Owner**: Select your account
   - **License**: MIT
   - **Space SDK**: **Docker**
   - **Private**: No (recommended for CI/CD access)
4. Click **"Create Space"**

---

## Step 2: Prepare Files for Upload

### 2a. Copy Space Files

Navigate to your project root and run:

```bash
# Create a temporary directory for the space
mkdir -p /tmp/hf-space-upload
cd /tmp/hf-space-upload

# Copy space files from your repo
cp -r <your-repo>/hf_space/* .

# This should contain:
# - app.py (FastAPI inference server)
# - app.requirements.txt (ML dependencies)
# - Dockerfile (container setup)
# - README.md (documentation)

ls -la
```

### 2b. Prepare Model Files

The model files are large. You have two options:

**Option A: Upload via Git LFS (Recommended for large files)**

```bash
cd /tmp/hf-space-upload

# Initialize Git LFS
git lfs install

# Create models directory
mkdir -p models

# Copy model files
cp <your-repo>/exam_middleware/models/*.pt models/
cp <your-repo>/exam_middleware/models/*.pth models/

# Track large files with LFS
git lfs track "models/*.pt"
git lfs track "models/*.pth"

# Start git
git init
git add .gitattributes models/
git commit -m "Add model weights with LFS"
```

**Option B: Let HF Spaces download from your server after deployment**

If your models are on a server, you can enhance the Dockerfile to download them:

```dockerfile
# Add to hf_space/Dockerfile before RUN pip install
RUN mkdir -p models && \
    wget https://your-server.com/improved_weights.pt -O models/improved_weights.pt && \
    wget https://your-server.com/best_crnn_model.pth -O models/best_crnn_model.pth
```

---

## Step 3: Push to HuggingFace Space

### 3a. Clone the Space Repository

```bash
git clone https://huggingface.co/spaces/<your-username>/answer-sheet-ml
cd answer-sheet-ml
```

### 3b. Add Your Files

```bash
# Copy all files from /tmp/hf-space-upload
cp -r /tmp/hf-space-upload/* .

# Verify files are present
ls -la
cat app.py | head -20
```

### 3c. Push to HF

```bash
# Configure git with your HF token
git config user.email "your-email@example.com"
git config user.name "Your Name"

# Add and commit
git add .
git commit -m "Initial ML inference setup with models"

# Push (will prompt for password — use your HF token)
git push

# When prompted for password: paste your HF API token
```

### 3d. Wait for Space to Build

The Space will automatically start building the Docker container. This can take 5-15 minutes depending on:
- Model file size (large files take longer)
- PyPI package downloads
- HF Spaces queue

Monitor the build here: `https://huggingface.co/spaces/<your-username>/answer-sheet-ml`

Once **"Building" → "Running"**, your API is ready.

---

## Step 4: Get Your HF Space URL

Once the Space is running:

1. Go to `https://huggingface.co/spaces/<your-username>/answer-sheet-ml`
2. Look for the **"Use this Space"** button → **"API"** tab
3. You'll see an endpoint like: `https://your-username-answer-sheet-ml.hf.space`
4. Copy this URL

---

## Step 5: Configure Your Render App

### 5a. Set Environment Variable

On your Render dashboard:

1. Go to your service settings
2. Under **Environment**, add:
   ```
   HF_SPACE_URL=https://your-username-answer-sheet-ml.hf.space
   ```
3. Redeploy

### 5b. Verify Configuration

After deployment, check the `/extract/status` endpoint:

```bash
curl https://your-render-app.onrender.com/extract/status
```

Expected response:
```json
{
  "extraction_available": true,
  "mode": "remote",
  "hf_space_url": "https://your-username-answer-sheet-ml.hf.space"
}
```

---

## Step 6: Test the Integration

### 6a. Test Extract Endpoint

```bash
curl -X POST https://your-render-app.onrender.com/extract \
  -F "file=@test_image.pdf"
```

This will:
1. Send the file to your Render app
2. Render app forwards to HF Space API
3. HF Space runs ML models
4. Results returned to your app

### 6b. Verify in Logs

Check Render logs:
```
INFO:     10.x.x.x:0 - "POST /extract HTTP/1.1" 200 OK
```

Check HF Space logs at: `https://huggingface.co/spaces/<your-username>/answer-sheet-ml#logs`

---

## Troubleshooting

### Space Build Failed

**Issue**: Docker build failed on HF Spaces

**Solutions**:
1. Check HF Space logs for errors
2. Verify all files are present (`app.py`, `Dockerfile`, `requirements.txt`)
3. Ensure `Dockerfile` is not in a subdirectory (should be at root)
4. Rebuild: click "App" → "Restart"

### Extraction Times Out

**Issue**: Requests to HF Space endpoint timeout

**Solutions**:
1. **First request slow**: HF Spaces puts inactive spaces to sleep. First request wakes it (can take 1-2 min)
2. **Upgrade space**: HF Spaces has CPU (free) and GPU (paid). For faster inference, consider GPU
3. **Check space logs**: Verify no errors during inference

### "HF_SPACE_URL not configured"

**Issue**: Status shows local mode instead of remote

**Solutions**:
1. Verify environment variable is set on Render: `echo $HF_SPACE_URL`
2. Check .env file in your repo (should use env vars, not hardcoded)
3. Redeploy after setting env var

### Models Not Found on HF Space

**Issue**: "Model weights not found" error

**Solutions**:
1. Verify models/ directory exists on HF Space
2. Check file sizes match your local files
3. Use `git lfs` for large files (>git 100MB limit)
4. Re-upload models via HF web UI if needed

---

## File Sizes Reference

Typical model file sizes:
- `improved_weights.pt` — ~200MB (YOLO)
- `best_crnn_model(git).pth` — ~50MB
- `best_subject_model_final.pth` — ~50MB
- **Total**: ~300MB

Upload via Git LFS to avoid issues.

---

## Next: Enable Local Fallback (Optional)

If you want local extraction as a fallback, uncomment in `exam_middleware/requirements.txt`:

```
# Uncomment these lines to enable local extraction fallback
--extra-index-url https://download.pytorch.org/whl/cpu
torch
torchvision
opencv-python-headless
ultralytics
pdf2image
numpy
```

Then redeploy. Now if HF Space is down, local extraction kicks in automatically.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  Render App (FastAPI)                                       │
│  - No ML models, minimal dependencies                       │
│  - Lightweight, fast startup                                │
└──────────────┬──────────────────────────────────────────────┘
               │ HTTP POST /extract
               │ (file, exam_type)
               ↓
┌─────────────────────────────────────────────────────────────┐
│  HuggingFace Spaces (Docker)                                │
│  - YOLO Detection Model                                     │
│  - CRNN OCR Models (Register + Subject)                     │
│  - GPU-accelerated inference                                │
│  - Can scale independently                                  │
└──────────────┬──────────────────────────────────────────────┘
               │ JSON Response
               │ {register_number, subject_code, confidence,...}
               ↓
┌─────────────────────────────────────────────────────────────┐
│  Render App continues                                       │
│  - Stores extracted data in DB                              │
│  - Returns result to user                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Support

For issues:
1. Check HF Space logs: https://huggingface.co/spaces/<your-username>/answer-sheet-ml#logs
2. Check Render logs: Dashboard → Logs
3. Test endpoint directly: `https://your-hf-space.hf.space/status`

