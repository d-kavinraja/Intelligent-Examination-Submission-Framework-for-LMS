"""
Remote Extraction Service — Calls HuggingFace Spaces ML inference API
instead of running models locally. This reduces Render's resource usage
and offloads computation to HF Spaces (which can have GPU).

Falls back to local extraction if HF_SPACE_URL is not configured.
"""

import os
import logging
import io
from pathlib import Path
from typing import Optional

import httpx
import structlog

logger = structlog.get_logger(__name__)

# HF Space configuration
HF_SPACE_URL = os.getenv("HF_SPACE_URL", "").strip()
EXTRACT_ENDPOINT = f"{HF_SPACE_URL}/extract" if HF_SPACE_URL else None
HEALTH_ENDPOINT = f"{HF_SPACE_URL}/health" if HF_SPACE_URL else None

# Request timeout (HF Spaces can be slow if waking up from sleep)
REQUEST_TIMEOUT = 300  # 5 minutes


async def check_hf_space_health() -> bool:
    """Check if HF Space API is available."""
    if not HEALTH_ENDPOINT:
        logger.warning("HF_SPACE_URL not configured — using local extraction")
        return False

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(HEALTH_ENDPOINT)
            return resp.status_code == 200
    except Exception as e:
        logger.warning("HF Space health check failed", error=str(e))
        return False


async def extract_from_hf_space(file_bytes: bytes, filename: str) -> dict:
    """Send file to HF Space API and get extraction results."""
    if not EXTRACT_ENDPOINT:
        return {"success": False, "error": "HF_SPACE_URL not configured"}

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            files = {"file": (filename, io.BytesIO(file_bytes))}
            resp = await client.post(EXTRACT_ENDPOINT, files=files)

            if resp.status_code == 200:
                return resp.json()
            else:
                logger.error("HF Space extraction failed", status=resp.status_code, text=resp.text)
                return {"success": False, "error": f"HF Space error: {resp.status_code}"}
    except httpx.ReadTimeout:
        logger.warning("HF Space request timeout")
        return {"success": False, "error": "Extraction service timeout"}
    except Exception as e:
        logger.error("HF Space extraction error", error=str(e))
        return {"success": False, "error": str(e)}


def get_extractor_mode() -> str:
    """Return whether we're using 'remote' (HF) or 'local' extraction."""
    if EXTRACT_ENDPOINT and HF_SPACE_URL:
        return "remote"
    return "local"


# ============================================================================
# Fallback to local extraction if HF Space is not available
# ============================================================================

_local_extractor: Optional[object] = None
_use_local_fallback = not bool(EXTRACT_ENDPOINT)


def _get_local_extractor():
    """Lazy load local extractor as fallback."""
    global _local_extractor
    if _local_extractor is None:
        try:
            from app.services.extraction_service import get_extractor
            _local_extractor = get_extractor()
            logger.info("Local extraction service loaded as fallback")
        except Exception as e:
            logger.error("Failed to load local extraction", error=str(e))
            _local_extractor = None
    return _local_extractor


async def extract_from_bytes_with_fallback(file_bytes: bytes, filename: str) -> dict:
    """
    Try HF Space first, fall back to local extraction if needed.
    """
    # Try remote first
    if EXTRACT_ENDPOINT:
        logger.info("Attempting remote extraction via HF Space")
        result = await extract_from_hf_space(file_bytes, filename)
        if result.get("success"):
            logger.info("Remote extraction succeeded")
            return result
        else:
            logger.warning("Remote extraction failed", error=result.get("error"))

    # Fallback to local
    logger.info("Falling back to local extraction")
    try:
        local_extractor = _get_local_extractor()
        if local_extractor:
            return local_extractor.extract_from_bytes(file_bytes, filename)
        else:
            return {"success": False, "error": "No extraction service available"}
    except Exception as e:
        logger.error("Local extraction fallback failed", error=str(e))
        return {"success": False, "error": str(e)}


def is_extraction_available() -> bool:
    """Check if extraction is available (local or remote)."""
    if EXTRACT_ENDPOINT:
        return True

    try:
        from app.services.extraction_service import is_extraction_available
        return is_extraction_available()
    except Exception:
        return False
