# Production Dockerfile for Render
# ML inference is offloaded to HuggingFace Spaces API
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install minimal system dependencies (no heavy ML libs)
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

# Install Python dependencies (ML packages commented out)
COPY requirements.txt .
RUN pip install --no-warn-script-location -r requirements.txt

# Copy application code (NO models directory — inference via HF Spaces)
COPY --chown=appuser:appuser . .

# Create necessary directories (but NOT models/)
RUN mkdir -p uploads storage migrations logs && \
    chown -R appuser:appuser /app

USER appuser
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2