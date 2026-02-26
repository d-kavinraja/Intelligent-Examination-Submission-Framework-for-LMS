"""
Upload API Routes
Handles file uploads from staff
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional, Dict
import logging

from app.db.database import get_db
from app.db.models import StaffUser
from app.schemas import (
    FileUploadResponse,
    BulkUploadResponse,
    ErrorResponse,
)
from app.services.file_processor import file_processor
from app.services.artifact_service import ArtifactService, SubjectMappingService, AuditService
from app.api.routes.auth import get_current_staff
from app.db.models import WorkflowStatus, ExaminationArtifact, SubjectMapping, StudentUsernameRegister

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/single", response_model=FileUploadResponse)
async def upload_single_file(
    file: UploadFile = File(...),
    exam_type: str = Form("CIA1"),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    current_staff: StaffUser = Depends(get_current_staff)
):
    """
    Upload a single examination paper
    
    The filename should follow the pattern: REGISTER_SUBJECT.pdf
    Example: 212223240065_19AI405.pdf
    
    Staff members upload scanned papers here. The system will:
    1. Validate the file format
    2. Parse the filename for register number and subject code
    3. Store the file and create a database record
    4. The paper will appear in the student's dashboard
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required"
        )
    
    # Read file content
    content = await file.read()
    
    # Validate file
    is_valid, message, metadata = file_processor.validate_file(content, file.filename)
    
    if not is_valid:
        logger.warning(f"File validation failed: {message}")
        return FileUploadResponse(
            success=False,
            message=message,
            errors=[message]
        )
    
    # Save file
    try:
        file_path, file_hash = await file_processor.save_file(
            file_content=content,
            original_filename=file.filename,
            subfolder="pending"
        )
    except Exception as e:
        logger.error(f"Failed to save file: {e}")
        return FileUploadResponse(
            success=False,
            message="Failed to save file",
            errors=[str(e)]
        )
    
    # Create artifact record
    artifact_service = ArtifactService(db)
    audit_service = AuditService(db)
    
    try:
        artifact = await artifact_service.create_artifact(
            raw_filename=file.filename,
            original_filename=metadata.get("original_filename", file.filename),
            file_blob_path=file_path,
            file_hash=file_hash,
            parsed_reg_no=metadata.get("parsed_register_no"),
            parsed_subject_code=metadata.get("parsed_subject_code"),
            exam_type=exam_type,
            file_size_bytes=metadata.get("size_bytes"),
            mime_type=metadata.get("mime_type"),
            uploaded_by_staff_id=current_staff.id,
            file_content=content
        )
        
        # Log the upload
        await audit_service.log_action(
            action="file_uploaded",
            action_category="upload",
            actor_type="staff",
            actor_id=str(current_staff.id),
            actor_username=current_staff.username,
            actor_ip=request.client.host if request and request.client else None,
            artifact_id=artifact.id,
            description=f"Uploaded file: {file.filename}",
            request_data={"filename": file.filename, "size": metadata.get("size_bytes")}
        )
        
        await db.commit()
        
        return FileUploadResponse(
            success=True,
            message="File uploaded successfully",
            artifact_uuid=str(artifact.artifact_uuid),
            parsed_register_number=artifact.parsed_reg_no,
            parsed_subject_code=artifact.parsed_subject_code,
            exam_type=artifact.exam_type,
            attempt_number=artifact.attempt_number,
            attempt_2_locked=artifact.attempt_2_locked,
            workflow_status=artifact.workflow_status.value
        )
        
    except Exception as e:
        logger.error(f"Failed to create artifact: {e}")
        await db.rollback()
        
        # Clean up the saved file
        await file_processor.delete_file(file_path)
        
        return FileUploadResponse(
            success=False,
            message="Failed to process file",
            errors=[str(e)]
        )


@router.post("/bulk", response_model=BulkUploadResponse)
async def upload_bulk_files(
    files: List[UploadFile] = File(...),
    exam_type: str = Form("CIA1"),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    current_staff: StaffUser = Depends(get_current_staff)
):
    """
    Upload multiple examination papers at once
    
    Each file should follow the pattern: REGISTER_SUBJECT.pdf
    """
    results = []
    successful = 0
    failed = 0
    
    for file in files:
        if not file.filename:
            results.append(FileUploadResponse(
                success=False,
                filename="unknown",
                message="Filename is required",
                errors=["Missing filename"]
            ))
            failed += 1
            continue
        
        # Read file content
        content = await file.read()
        
        # Validate file
        is_valid, message, metadata = file_processor.validate_file(content, file.filename)
        
        if not is_valid:
            results.append(FileUploadResponse(
                success=False,
                filename=file.filename,
                message=message,
                errors=[message]
            ))
            failed += 1
            continue
        
        # Save file and create artifact inside a savepoint so a single
        # file failure does not poison the DB session for later files.
        try:
            file_path, file_hash = await file_processor.save_file(
                file_content=content,
                original_filename=file.filename,
                subfolder="pending"
            )
            
            # Use a nested transaction (savepoint) per file
            async with db.begin_nested():
                artifact_service = ArtifactService(db)
                artifact = await artifact_service.create_artifact(
                    raw_filename=file.filename,
                    original_filename=metadata.get("original_filename", file.filename),
                    file_blob_path=file_path,
                    file_hash=file_hash,
                    parsed_reg_no=metadata.get("parsed_register_no"),
                    parsed_subject_code=metadata.get("parsed_subject_code"),
                    exam_type=exam_type,
                    file_size_bytes=metadata.get("size_bytes"),
                    mime_type=metadata.get("mime_type"),
                    uploaded_by_staff_id=current_staff.id,
                    file_content=content
                )
            
            results.append(FileUploadResponse(
                success=True,
                filename=file.filename,
                message="File uploaded successfully",
                artifact_uuid=str(artifact.artifact_uuid),
                parsed_register_number=artifact.parsed_reg_no,
                parsed_subject_code=artifact.parsed_subject_code,
                exam_type=artifact.exam_type,
                attempt_number=artifact.attempt_number,
                attempt_2_locked=artifact.attempt_2_locked,
                workflow_status=artifact.workflow_status.value
            ))
            successful += 1
            
        except Exception as e:
            logger.error(f"Failed to process file {file.filename}: {e}")
            # The savepoint rollback already happened via the context manager,
            # so the session is clean for the next iteration.
            results.append(FileUploadResponse(
                success=False,
                filename=file.filename,
                message=f"Failed to process: {str(e)}",
                errors=[str(e)]
            ))
            failed += 1
    
    # Log bulk upload
    audit_service = AuditService(db)
    await audit_service.log_action(
        action="bulk_upload",
        action_category="upload",
        actor_type="staff",
        actor_id=str(current_staff.id),
        actor_username=current_staff.username,
        actor_ip=request.client.host if request and request.client else None,
        description=f"Bulk upload: {successful} successful, {failed} failed",
        request_data={"total": len(files), "successful": successful, "failed": failed}
    )
    
    await db.commit()
    
    return BulkUploadResponse(
        total_files=len(files),
        successful=successful,
        failed=failed,
        results=results
    )


@router.post("/check-duplicates")
async def check_duplicates(
    payload: Dict,
    db: AsyncSession = Depends(get_db),
    current_staff: StaffUser = Depends(get_current_staff)
):
    """
    Check if artifacts with the same register number + subject code already exist for the given exam type.
    Body: { "items": [{"reg_no": "...", "subject_code": "...", "exam_type": "..."}] }
    Returns: { "results": [{"reg_no": "...", "subject_code": "...", "exam_type": "...", "exists": bool, "status": "...", "uploaded_at": "..."}] }
    """
    items = payload.get("items", [])
    if not items:
        return {"results": []}

    results = []
    for item in items:
        reg_no = (item.get("reg_no") or "").strip()
        subject_code = (item.get("subject_code") or "").strip().upper()
        exam_type = (item.get("exam_type") or "CIA1").strip().upper()

        if not reg_no or not subject_code:
            results.append({
                "reg_no": reg_no,
                "subject_code": subject_code,
                "exists": False,
                "status": None,
                "uploaded_at": None
            })
            continue

        result = await db.execute(
            select(ExaminationArtifact).where(
                and_(
                    ExaminationArtifact.parsed_reg_no == reg_no,
                    ExaminationArtifact.parsed_subject_code == subject_code,
                    ExaminationArtifact.exam_type == exam_type,
                    ExaminationArtifact.workflow_status != WorkflowStatus.DELETED
                )
            ).order_by(ExaminationArtifact.attempt_number.desc())
        )
        existing_all = result.scalars().all()

        if existing_all:
            latest = existing_all[0]
            max_attempt = latest.attempt_number
            attempt_2_locked = getattr(latest, 'attempt_2_locked', True)
            # If attempt 2 is unlocked AND only attempt 1 exists, the file can be
            # uploaded as attempt 2 — so it's not a blocking duplicate.
            can_upload_as_attempt_2 = (not attempt_2_locked and max_attempt == 1)
            results.append({
                "reg_no": reg_no,
                "subject_code": subject_code,
                "exam_type": exam_type,
                "exists": True,
                "status": latest.workflow_status.value,
                "uploaded_at": latest.uploaded_at.isoformat() if latest.uploaded_at else None,
                "attempt_2_locked": attempt_2_locked,
                "max_attempt": max_attempt,
                "can_upload_as_attempt_2": can_upload_as_attempt_2
            })
        else:
            results.append({
                "reg_no": reg_no,
                "subject_code": subject_code,
                "exam_type": exam_type,
                "exists": False,
                "status": None,
                "uploaded_at": None,
                "attempt_2_locked": True,
                "max_attempt": 0,
                "can_upload_as_attempt_2": False
            })

    return {"results": results}


@router.post("/validate-mappings")
async def validate_mappings(
    payload: Dict,
    db: AsyncSession = Depends(get_db),
    current_staff: StaffUser = Depends(get_current_staff)
):
    """
    Validate that subject codes are mapped and register numbers have student mappings for the given exam type.
    Body: { "items": [{"reg_no": "...", "subject_code": "...", "exam_type": "..."}] }
    Returns: { "results": [{"reg_no": "...", "subject_code": "...", "exam_type": "...", "subject_mapped": bool, "student_mapped": bool}] }
    """
    items = payload.get("items", [])
    if not items:
        return {"results": []}

    # Batch-load all active subject mappings for these codes and types
    criteria = []
    for item in items:
        sc = (item.get("subject_code") or "").strip().upper()
        et = (item.get("exam_type") or "CIA1").strip().upper()
        if sc:
            criteria.append(and_(SubjectMapping.subject_code == sc, SubjectMapping.exam_type == et))
    
    mapped_keys = set()
    if criteria:
        from sqlalchemy import or_
        sm_result = await db.execute(
            select(SubjectMapping.subject_code, SubjectMapping.exam_type).where(
                and_(
                    or_(*criteria),
                    SubjectMapping.is_active == True
                )
            )
        )
        mapped_keys = set((row[0], row[1]) for row in sm_result.all())

    # Batch-load all student username/register mappings
    reg_nos = list(set((item.get("reg_no") or "").strip() for item in items if item.get("reg_no")))
    mapped_registers = set()
    if reg_nos:
        sr_result = await db.execute(
            select(StudentUsernameRegister.register_number).where(
                StudentUsernameRegister.register_number.in_(reg_nos)
            )
        )
        mapped_registers = set(row[0] for row in sr_result.all())

    results = []
    for item in items:
        reg_no = (item.get("reg_no") or "").strip()
        subject_code = (item.get("subject_code") or "").strip().upper()
        exam_type = (item.get("exam_type") or "CIA1").strip().upper()
        
        # Check if subject is mapped for this exam type
        subject_mapped = (subject_code, exam_type) in mapped_keys
        
        results.append({
            "reg_no": reg_no,
            "subject_code": subject_code,
            "exam_type": exam_type,
            "subject_mapped": subject_mapped,
            "student_mapped": reg_no in mapped_registers
        })

    return {"results": results}


@router.get("/all")
async def get_all_uploads(
    limit: int = 50,
    offset: int = 0,
    include_deleted: bool = Query(default=False, description="Include artifacts marked as DELETED"),
    db: AsyncSession = Depends(get_db),
    current_staff: StaffUser = Depends(get_current_staff)
):
    """
    Get list of all uploaded files (staff view)
    """
    artifact_service = ArtifactService(db)
    artifacts, total = await artifact_service.get_all_artifacts(limit=limit, offset=offset)
    audit_service = AuditService(db)
    
    # Filter out DELETED artifacts by default
    filtered = [a for a in artifacts if not (a.workflow_status == WorkflowStatus.DELETED and not include_deleted)]

    artifacts_list = []
    for a in filtered:
        logs = await audit_service.get_for_artifact(a.id)
        deleted_targets = {str(l.target_id) for l in logs if l.action == 'report_deleted'}
        resolved_targets = {str(l.target_id) for l in logs if l.action == 'report_resolved'}
        # Count only ACTIVE reports (not withdrawn, not resolved)
        report_count = sum(1 for l in logs if l.action == 'report_issue' and str(l.id) not in deleted_targets and str(l.id) not in resolved_targets)
        artifacts_list.append({
            "artifact_uuid": str(a.artifact_uuid),
            "filename": a.original_filename,
            "register_number": a.parsed_reg_no,
            "subject_code": a.parsed_subject_code,
            "exam_type": getattr(a, 'exam_type', 'CIA1') or 'CIA1',
            "attempt_number": getattr(a, 'attempt_number', 1) or 1,
            "attempt_2_locked": getattr(a, 'attempt_2_locked', True),
            "status": a.workflow_status.value,
            "uploaded_at": a.uploaded_at.isoformat() if a.uploaded_at else None,
            "report_count": report_count
        })

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "artifacts": artifacts_list
    }


@router.get("/pending")
async def get_pending_uploads(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_staff: StaffUser = Depends(get_current_staff)
):
    """
    Get list of pending uploads (staff view)
    """
    artifact_service = ArtifactService(db)
    artifacts, total = await artifact_service.get_all_pending(limit=limit, offset=offset)
    audit_service = AuditService(db)
    
    artifacts_list = []
    for a in artifacts:
        logs = await audit_service.get_for_artifact(a.id)
        deleted_targets = {str(l.target_id) for l in logs if l.action == 'report_deleted'}
        resolved_targets = {str(l.target_id) for l in logs if l.action == 'report_resolved'}
        # Count only ACTIVE reports (not withdrawn, not resolved)
        report_count = sum(1 for l in logs if l.action == 'report_issue' and str(l.id) not in deleted_targets and str(l.id) not in resolved_targets)
        artifacts_list.append({
            "artifact_uuid": str(a.artifact_uuid),
            "filename": a.original_filename,
            "register_number": a.parsed_reg_no,
            "subject_code": a.parsed_subject_code,
            "exam_type": getattr(a, 'exam_type', 'CIA1') or 'CIA1',
            "attempt_number": getattr(a, 'attempt_number', 1) or 1,
            "attempt_2_locked": getattr(a, 'attempt_2_locked', True),
            "status": a.workflow_status.value,
            "uploaded_at": a.uploaded_at.isoformat() if a.uploaded_at else None,
            "report_count": report_count
        })

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "artifacts": artifacts_list
    }


@router.get("/stats")
async def get_upload_stats(
    db: AsyncSession = Depends(get_db),
    current_staff: StaffUser = Depends(get_current_staff)
):
    """
    Get upload statistics
    """
    artifact_service = ArtifactService(db)
    stats = await artifact_service.get_stats()
    
    return {
        "stats": stats,
        "total": sum(stats.values())
    }
