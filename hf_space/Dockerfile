FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (including X11 libs for cv2/YOLO)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxcb1 \
    libx11-6 \
    libxext6 \
    poppler-utils \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app.py .

# Create models directory (will be populated after build)
RUN mkdir -p models

# Note: Model files should be uploaded via:
# 1. HF Spaces web UI (drag-drop into Files)
# 2. Or git lfs if using git push

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:7860/health').read()" || exit 1

# Default port for HF Spaces
ENV PORT=7860

# Run application
CMD ["python", "app.py"]
