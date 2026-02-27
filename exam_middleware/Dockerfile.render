# Production Dockerfile for Render
# ML inference is offloaded to HuggingFace Spaces API
# Local models are OPTIONAL for fallback only
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install minimal system dependencies (no heavy libs like torch/ultralytics)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    postgresql-client \
    libpq5 \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && ldconfig

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Install Python dependencies
# Note: torch/ultralytics/opencv-* are OPTIONAL (commented out in requirements or marked as extras)
# Remote extraction is primary; local is optional fallback
COPY requirements.txt .
RUN pip install --no-warn-script-location -r requirements.txt

# Copy application code (NO models directory)
COPY --chown=appuser:appuser . .

# Do NOT copy models/ directory — inference happens on HF Spaces

# Create necessary directories (but NOT models/)
RUN mkdir -p uploads storage migrations logs && \
    chown -R appuser:appuser /app

USER appuser
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2