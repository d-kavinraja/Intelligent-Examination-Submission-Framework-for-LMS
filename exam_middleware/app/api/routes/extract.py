"""
Extract API Route — accepts a scanned answer-sheet (PDF or image),
runs YOLO + CRNN models to detect & extract
register number and subject code, and returns the results.

Also provides a one-shot /scan-upload endpoint that does
extraction + rename + artifact creation in a single call.
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging

from app.db.database import get_db
from app.api.routes.auth import get_current_staff

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/status")
async def extraction_status():
    """Check whether the extraction models are available."""
    from pathlib import Path
    models_dir = Path(__file__).resolve().parent.parent.parent.parent / "models"
    model_files = {}
    if models_dir.exists():
        model_files = {f.name: f.stat().st_size for f in models_dir.iterdir() if f.is_file()}

    try:
        from app.services.extraction_service import is_extraction_available
        available = is_extraction_available()
    except ImportError as e:
        return {
            "extraction_available": False,
            "error": f"Import error: {e}",
            "models_directory": str(models_dir),
            "models_dir_exists": models_dir.exists(),
            "model_files": model_files,
        }
    except Exception as e:
        return {
            "extraction_available": False,
            "error": str(e),
            "models_directory": str(models_dir),
            "model_files": model_files,
        }
    return {
        "extraction_available": available,
        "models_directory": str(models_dir),
        "models_dir_exists": models_dir.exists(),
        "model_files": model_files,
    }


@router.post("/extract")
async def extract_from_upload(file: UploadFile = File(...)):
    """
    Upload a scanned answer sheet (PDF, JPG, PNG) and get back the
    extracted register number and subject code.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    allowed_ext = (".pdf", ".jpg", ".jpeg", ".png", ".bmp", ".tiff")
    ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in allowed_ext:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(allowed_ext)}",
        )

    try:
        from app.services.extraction_service import is_extraction_available, get_extractor

        if not is_extraction_available():
            raise HTTPException(
                status_code=503,
                detail="Extraction models not available on this server. "
                       "Ensure model weight files are present in the models/ directory.",
            )

        data = await file.read()
        if len(data) > 50 * 1024 * 1024:  # 50 MB limit
            raise HTTPException(status_code=413, detail="File too large (max 50 MB)")

        extractor = get_extractor()
        result = extractor.extract_from_bytes(data, file.filename)

        if "error" in result:
            return JSONResponse(
                status_code=422,
                content={"success": False, "error": result["error"]},
            )

        return JSONResponse(content={
            "success": True,
            "register_number": result["register_number"],
            "register_confidence": result["register_confidence"],
            "subject_code": result["subject_code"],
            "subject_confidence": result["subject_confidence"],
            "regions_found": result["regions_found"],
            "suggested_filename": f"{result['register_number']}_{result['subject_code']}.pdf"
            if result["register_number"] and result["subject_code"] else None,
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Extraction failed")
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@router.post("/scan-upload")
async def scan_extract_and_upload(
    file: UploadFile = File(...),
    exam_type: str = Form("CIA1"),
    request: Request = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db),
    current_staff = Depends(get_current_staff),
):
    """
    **One-shot Scanner Pipeline**: accepts a raw scanned file,
    runs AI extraction, renames to {reg_no}_{subject_code}_{exam_type}.pdf,
    and creates the upload artifact — all in one call.

    Used by the local Scanner Agent running on the PC connected to the Ricoh.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    allowed_ext = (".pdf", ".jpg", ".jpeg", ".png", ".bmp", ".tiff")
    raw_ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ".pdf"
    if raw_ext not in allowed_ext:
        raise HTTPException(status_code=400, detail=f"Unsupported file type '{raw_ext}'")

    try:
        from app.services.extraction_service import is_extraction_available, get_extractor

        if not is_extraction_available():
            raise HTTPException(status_code=503, detail="Extraction models not available on server")

        # ---- 1. Read file --------------------------------------------------
        content = await file.read()
        if len(content) > 50 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large (max 50 MB)")

        # ---- 2. Run AI extraction -------------------------------------------
        extractor = get_extractor()
        result = extractor.extract_from_bytes(content, file.filename)

        if "error" in result:
            return JSONResponse(status_code=422, content={
                "success": False,
                "stage": "extraction",
                "error": result["error"],
                "original_filename": file.filename,
            })

        reg_no = result["register_number"]
        sub_code = result["subject_code"]

        if not reg_no or not sub_code:
            return JSONResponse(status_code=422, content={
                "success": False,
                "stage": "extraction",
                "error": "Could not extract register number and/or subject code",
                "register_number": reg_no,
                "subject_code": sub_code,
                "register_confidence": result["register_confidence"],
                "subject_confidence": result["subject_confidence"],
                "original_filename": file.filename,
            })

        # ---- 3. Rename file -------------------------------------------------
        final_ext = raw_ext if raw_ext == ".pdf" else ".pdf"
        renamed_filename = f"{reg_no}_{sub_code}_{exam_type}{final_ext}"

        # ---- 4. Save file via file_processor --------------------------------
        from app.services.file_processor import file_processor
        file_path, file_hash = await file_processor.save_file(
            file_content=content,
            original_filename=renamed_filename,
            subfolder="pending",
        )

        # ---- 5. Validate (use metadata from file_processor) -----------------
        is_valid, message, metadata = file_processor.validate_file(content, renamed_filename)
        if not is_valid:
            await file_processor.delete_file(file_path)
            return JSONResponse(status_code=422, content={
                "success": False,
                "stage": "validation",
                "error": message,
                "renamed_filename": renamed_filename,
            })

        # ---- 6. Create artifact record --------------------------------------
        from app.services.artifact_service import ArtifactService, AuditService
        artifact_service = ArtifactService(db)
        audit_service = AuditService(db)

        artifact = await artifact_service.create_artifact(
            raw_filename=renamed_filename,
            original_filename=file.filename,  # keep original scanner temp name for audit
            file_blob_path=file_path,
            file_hash=file_hash,
            parsed_reg_no=reg_no,
            parsed_subject_code=sub_code,
            exam_type=exam_type,
            file_size_bytes=metadata.get("size_bytes", len(content)),
            mime_type=metadata.get("mime_type", "application/pdf"),
            uploaded_by_staff_id=current_staff.id,
            file_content=content,
        )

        await audit_service.log_action(
            action="scan_auto_uploaded",
            action_category="upload",
            actor_type="staff",
            actor_id=str(current_staff.id),
            actor_username=current_staff.username,
            actor_ip=request.client.host if request and request.client else None,
            artifact_id=artifact.id,
            description=f"Smart Scan: {file.filename} → {renamed_filename}",
            request_data={
                "original_filename": file.filename,
                "renamed_filename": renamed_filename,
                "register_number": reg_no,
                "subject_code": sub_code,
                "register_confidence": result["register_confidence"],
                "subject_confidence": result["subject_confidence"],
            },
        )

        await db.commit()

        # ---- 7. Background notification ------------------------------------
        from app.api.routes.upload import _bg_notify_student
        background_tasks.add_task(
            _bg_notify_student,
            artifact_id=artifact.id,
            uploaded_by_username=current_staff.username,
            actor_ip=request.client.host if request and request.client else None,
        )

        return JSONResponse(content={
            "success": True,
            "original_filename": file.filename,
            "renamed_filename": renamed_filename,
            "register_number": reg_no,
            "register_confidence": result["register_confidence"],
            "subject_code": sub_code,
            "subject_confidence": result["subject_confidence"],
            "exam_type": exam_type,
            "artifact_uuid": str(artifact.artifact_uuid),
            "attempt_number": artifact.attempt_number,
            "workflow_status": artifact.workflow_status.value,
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Scan-upload pipeline failed")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Scan-upload failed: {str(e)}")


# ---- Scanner Agent heartbeat / processed log --------------------------------

# In-memory log of recently processed files (last 100)
_scan_log: list[dict] = []
MAX_SCAN_LOG = 100


def _add_scan_log(entry: dict):
    _scan_log.insert(0, entry)
    if len(_scan_log) > MAX_SCAN_LOG:
        _scan_log.pop()


@router.get("/scan-log")
async def get_scan_log():
    """Return the recent scan-upload processing log."""
    return {"entries": _scan_log, "total": len(_scan_log)}
