# Production Dockerfile for Render — SINGLE STAGE (no multi-stage library mismatch)
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    QT_QPA_PLATFORM=offscreen \
    OPENCV_IO_ENABLE_OPENEXR=0 \
    DISPLAY="" \
    XDG_RUNTIME_DIR=/tmp

# Install ALL system dependencies in one layer, then refresh linker cache
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    postgresql-client \
    libpq5 \
    libmagic1 \
    curl \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    libxcb1 \
    libx11-6 \
    libxext6 \
    libxrender1 \
    libsm6 \
    libice6 \
    libxinerama1 \
    libxi6 \
    libxrandr2 \
    libxcursor1 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libfontconfig1 \
    libfreetype6 \
    && rm -rf /var/lib/apt/lists/* \
    && ldconfig

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-warn-script-location -r requirements.txt && \
    pip uninstall -y opencv-python 2>/dev/null; \
    pip install --no-warn-script-location --force-reinstall opencv-python-headless && \
    ldconfig

# BUILD-TIME SMOKE TEST — if cv2 cannot import, deploy FAILS here
RUN python -c "import cv2; print('[OK] cv2', cv2.__version__)" && \
    python -c "from ultralytics import YOLO; print('[OK] ultralytics')" && \
    python -c "import torch; print('[OK] torch', torch.__version__)" && \
    echo "=== All imports verified ==="

# Copy application code and model weights
COPY --chown=appuser:appuser . .
COPY --chown=appuser:appuser models/ models/

# Create necessary directories
RUN mkdir -p uploads storage migrations logs && \
    chown -R appuser:appuser /app

# Clean up build-only packages
RUN apt-get purge -y gcc && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

USER appuser
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2