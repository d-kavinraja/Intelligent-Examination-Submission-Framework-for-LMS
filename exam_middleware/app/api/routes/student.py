"""
Student API Routes
Handles student dashboard and submission
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query, Header
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging
import os
from pathlib import Path

from app.db.database import get_db
from app.db.models import StudentSession
from app.schemas import (
    StudentDashboardResponse,
    StudentPendingPaper,
    SubmissionRequest,
    SubmissionResponse,
    ArtifactResponse,
    WorkflowStatusEnum,
)
from app.services.artifact_service import ArtifactService, SubjectMappingService, AuditService
from app.services.submission_service import SubmissionService
from app.api.routes.auth import get_current_student_session, get_decrypted_token

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_session_register_number(session: StudentSession) -> str:
    import re

    register_number = session.register_number
    if not register_number and session.moodle_fullname:
        match = re.search(r"\b(\d{12})\b", session.moodle_fullname)
        if match:
            register_number = match.group(1)

    return register_number or session.moodle_username


def _resolve_artifact_file_path(
    file_blob_path: str,
    original_filename: str,
    parsed_reg_no: Optional[str] = None,
    parsed_subject_code: Optional[str] = None,
) -> Optional[str]:
    """Resolve an artifact file path robustly across relative/Windows paths.

    The DB may contain a relative path (e.g. ./uploads/...) or a stale path.
    This attempts safe resolutions within the project directory.
    """
    base_dir = Path(__file__).resolve().parents[3]  # .../exam_middleware

    candidates: list[Path] = []

    if file_blob_path:
        raw = Path(os.path.normpath(file_blob_path))
        candidates.append(raw)
        # If it is a relative path, also try resolving from the project root
        if not raw.is_absolute():
            candidates.append((base_dir / raw).resolve())
            # Common case: stored as "./uploads/..." with a leading "./"
            if str(raw).startswith("./") or str(raw).startswith(".\\"):
                candidates.append((base_dir / str(raw)[2:]).resolve())

    blob_name = Path(file_blob_path).name if file_blob_path else ""
    orig_name = Path(original_filename).name if original_filename else ""

    # Search in known upload directories only
    search_dirs = [
        base_dir / "uploads" / "pending",
        base_dir / "uploads" / "processed",
        base_dir / "uploads" / "failed",
        base_dir / "uploads" / "temp",
        base_dir / "uploads",
        base_dir / "storage" / "uploads" / "pending",
        base_dir / "storage" / "uploads" / "processed",
        base_dir / "storage" / "uploads" / "failed",
        base_dir / "storage" / "uploads" / "temp",
        base_dir / "storage" / "uploads",
        base_dir,
    ]

    for d in search_dirs:
        if blob_name:
            candidates.append(d / blob_name)
        if orig_name and orig_name != blob_name:
            candidates.append(d / orig_name)

    # Last-resort: reconstruct standard filename pattern used by uploads
    # Example: 212222240047_19AI405.pdf
    if parsed_reg_no and parsed_subject_code:
        # Try common allowed extensions without expensive recursion
        for ext in (".pdf", ".jpg", ".jpeg", ".png"):
            guessed = f"{parsed_reg_no}_{parsed_subject_code}{ext}"
            candidates.append(base_dir / guessed)
            candidates.append(base_dir / "uploads" / "pending" / guessed)
            candidates.append(base_dir / "uploads" / "processed" / guessed)
            candidates.append(base_dir / "uploads" / "failed" / guessed)
            candidates.append(base_dir / "uploads" / "temp" / guessed)
            candidates.append(base_dir / "uploads" / guessed)

    for p in candidates:
        try:
            if p and p.exists() and p.is_file():
                return str(p)
        except OSError:
            continue

    # Very last-resort: glob match in a few small directories (non-recursive)
    if parsed_reg_no and parsed_subject_code:
        pattern = f"{parsed_reg_no}_{parsed_subject_code}.*"
        for d in [
            base_dir,
            base_dir / "uploads",
            base_dir / "uploads" / "pending",
            base_dir / "uploads" / "processed",
            base_dir / "uploads" / "failed",
            base_dir / "uploads" / "temp",
        ]:
            try:
                if d.exists() and d.is_dir():
                    for hit in d.glob(pattern):
                        if hit.is_file():
                            return str(hit)
            except OSError:
                continue

    return None


async def get_student_session(
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    session: Optional[str] = Query(None, alias="session"),
    db: AsyncSession = Depends(get_db),
) -> StudentSession:
    """Get student session from header or query.

    - Use `X-Session-ID` header for normal `fetch()` requests.
    - Use `?session=...` for iframe/preview URLs (iframes can't send custom headers).
    """
    session_id = x_session_id or session
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-Session-ID header or session query parameter required",
        )
    return await get_current_student_session(session_id, db)


@router.get("/dashboard", response_model=StudentDashboardResponse)
async def get_dashboard(
    request: Request,
    session: StudentSession = Depends(get_student_session),
    db: AsyncSession = Depends(get_db)
):
    """
    Get student dashboard
    
    Returns:
    - List of papers pending submission
    - List of already submitted papers
    - User information
    """
    artifact_service = ArtifactService(db)
    mapping_service = SubjectMappingService(db)
    
    # Use register number from session (provided during login)
    # Fallback to extracting from fullname or using moodle_username
    import re
    register_number = session.register_number  # Primary: use stored register number
    if not register_number:
        # Fallback: try to extract from fullname
        if session.moodle_fullname:
            match = re.search(r'\b(\d{12})\b', session.moodle_fullname)
            if match:
                register_number = match.group(1)
        # Final fallback: use moodle username
        if not register_number:
            register_number = session.moodle_username
    
    logger.info(f"Dashboard for register_number: {register_number}")
    
    # Get pending papers for this student
    pending_artifacts = await artifact_service.get_pending_for_student(
        register_number=register_number,
        moodle_user_id=session.moodle_user_id
    )
    
    # Get submitted papers
    submitted_artifacts = await artifact_service.get_submitted_for_student(
        register_number=register_number
    )
    
    # Build pending papers list with subject info
    pending_papers = []
    for artifact in pending_artifacts:
        # Get subject mapping for additional info
        mapping = None
        if artifact.parsed_subject_code:
            mapping = await mapping_service.get_mapping(artifact.parsed_subject_code)
        
        # Check if we have a valid assignment mapping
        assignment_id = await mapping_service.get_assignment_id(artifact.parsed_subject_code) if artifact.parsed_subject_code else None
        
        pending_papers.append(StudentPendingPaper(
            artifact_uuid=str(artifact.artifact_uuid),
            subject_code=artifact.parsed_subject_code or "Unknown",
            subject_name=mapping.subject_name if mapping else None,
            assignment_name=mapping.moodle_assignment_name if mapping else None,
            filename=artifact.original_filename,
            uploaded_at=artifact.uploaded_at,
            workflow_status=artifact.workflow_status.value.lower() if artifact.workflow_status else None,
            can_submit=assignment_id is not None,
            message=None if assignment_id else "Assignment mapping not found. Contact admin."
        ))
    
    # Build submitted papers list (include subject_name from mapping if available)
    submitted_papers = []
    for a in submitted_artifacts:
        mapping = None
        if a.parsed_subject_code:
            mapping = await mapping_service.get_mapping(a.parsed_subject_code)

        submitted_papers.append(
            ArtifactResponse(
                id=a.id,
                artifact_uuid=str(a.artifact_uuid),
                raw_filename=a.raw_filename,
                original_filename=a.original_filename,
                subject_name=mapping.subject_name if mapping else None,
                parsed_reg_no=a.parsed_reg_no,
                parsed_subject_code=a.parsed_subject_code,
                workflow_status=WorkflowStatusEnum(a.workflow_status.value),
                moodle_assignment_id=a.moodle_assignment_id,
                uploaded_at=a.uploaded_at,
                submit_timestamp=a.submit_timestamp
            )
        )
    
    return StudentDashboardResponse(
        moodle_user_id=session.moodle_user_id,
        moodle_username=session.moodle_username,
        full_name=session.moodle_fullname,
        pending_papers=pending_papers,
        submitted_papers=submitted_papers,
        total_pending=len(pending_papers),
        total_submitted=len(submitted_papers)
    )


@router.get("/paper/{artifact_uuid}")
async def get_paper_details(
    artifact_uuid: str,
    session: StudentSession = Depends(get_student_session),
    db: AsyncSession = Depends(get_db)
):
    """
    Get details of a specific paper
    
    Security: Only returns if the paper belongs to the logged-in student
    """
    artifact_service = ArtifactService(db)
    artifact = await artifact_service.get_by_uuid(artifact_uuid)
    
    if not artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found"
        )
    
    # Security check (match against the student's register number)
    session_reg_no = _get_session_register_number(session)
    if artifact.parsed_reg_no != session_reg_no:
        logger.warning(
            f"Unauthorized access attempt: {session_reg_no} tried to access "
            f"paper belonging to {artifact.parsed_reg_no}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own papers"
        )
    
    # Log the view
    audit_service = AuditService(db)
    await audit_service.log_action(
        action="paper_viewed",
        action_category="view",
        actor_type="student",
        actor_id=str(session.moodle_user_id),
        actor_username=session.moodle_username,
        artifact_id=artifact.id,
        description=f"Student viewed paper: {artifact.original_filename}"
    )
    await db.commit()
    
    return {
        "artifact_uuid": str(artifact.artifact_uuid),
        "filename": artifact.original_filename,
        "register_number": artifact.parsed_reg_no,
        "subject_code": artifact.parsed_subject_code,
        "status": artifact.workflow_status.value,
        "uploaded_at": artifact.uploaded_at.isoformat() if artifact.uploaded_at else None,
        "submitted_at": artifact.submit_timestamp.isoformat() if artifact.submit_timestamp else None,
        "file_size": artifact.file_size_bytes,
        "mime_type": artifact.mime_type
    }


@router.get("/paper/{artifact_uuid}/view")
async def view_paper_file(
    artifact_uuid: str,
    session: StudentSession = Depends(get_student_session),
    db: AsyncSession = Depends(get_db)
):
    """
    View/download the actual paper file
    
    Returns the file for display in the browser
    """
    artifact_service = ArtifactService(db)
    artifact = await artifact_service.get_by_uuid(artifact_uuid)
    
    if not artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found"
        )
    
    # Security check (match against the student's register number)
    session_reg_no = _get_session_register_number(session)
    if artifact.parsed_reg_no != session_reg_no:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own papers"
        )
    
    resolved_path = _resolve_artifact_file_path(
        artifact.file_blob_path,
        artifact.original_filename,
        parsed_reg_no=artifact.parsed_reg_no,
        parsed_subject_code=artifact.parsed_subject_code,
    )
    if not resolved_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on server"
        )

    # Self-heal: update stored blob path if it was stale
    try:
        if artifact.file_blob_path != resolved_path:
            artifact.file_blob_path = resolved_path.replace('\\', '/')
            await db.commit()
    except Exception:
        await db.rollback()
    
    # Determine media type
    media_type = artifact.mime_type or "application/pdf"
    
    safe_name = (artifact.original_filename or "paper").replace('"', "")
    return FileResponse(
        path=resolved_path,
        media_type=media_type,
        filename=safe_name,
        headers={"Content-Disposition": f'inline; filename="{safe_name}"'},
    )


@router.post("/submit/{artifact_uuid}", response_model=SubmissionResponse)
async def submit_paper_by_uuid(
    artifact_uuid: str,
    request: Request,
    session: StudentSession = Depends(get_student_session),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit a paper to Moodle by artifact UUID (simplified endpoint)
    """
    import re
    
    # Use register number from session (provided during login)
    register_number = session.register_number  # Primary: use stored register number
    if not register_number:
        # Fallback: try to extract from fullname
        if session.moodle_fullname:
            match = re.search(r'\b(\d{12})\b', session.moodle_fullname)
            if match:
                register_number = match.group(1)
        # Final fallback: use moodle username
        if not register_number:
            register_number = session.moodle_username
    
    logger.info(f"Submit attempt for {artifact_uuid} by register_number: {register_number}")
    
    # Get the decrypted Moodle token
    moodle_token = get_decrypted_token(session)
    
    # Create submission service
    submission_service = SubmissionService(db)
    
    # Execute submission
    success, message, result = await submission_service.submit_artifact(
        artifact_uuid=artifact_uuid,
        moodle_token=moodle_token,
        moodle_user_id=session.moodle_user_id,
        moodle_username=session.moodle_username,
        register_number=register_number,
        actor_ip=request.client.host if request.client else None,
        lock_submission=True
    )
    
    await db.commit()
    
    if not success:
        if result and result.get("queued"):
            return SubmissionResponse(
                success=False,
                message=message,
                artifact_uuid=artifact_uuid,
                workflow_status=WorkflowStatusEnum.QUEUED
            )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    # Get updated artifact for response
    artifact_service = ArtifactService(db)
    artifact = await artifact_service.get_by_uuid(artifact_uuid)
    
    return SubmissionResponse(
        success=True,
        message=message,
        artifact_uuid=artifact_uuid,
        workflow_status=WorkflowStatusEnum(artifact.workflow_status.value),
        moodle_submission_id=artifact.moodle_submission_id,
        submitted_at=artifact.submit_timestamp
    )


@router.post("/submit", response_model=SubmissionResponse)
async def submit_paper(
    submission: SubmissionRequest,
    request: Request,
    session: StudentSession = Depends(get_student_session),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit a paper to Moodle
    
    This is the main submission endpoint that:
    1. Validates the student owns the paper
    2. Uploads the file to Moodle draft area
    3. Links the file to the assignment
    4. Finalizes the submission
    
    The submission is atomic - if any step fails, the operation can be retried.
    """
    import re
    
    if not submission.confirm_submission:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must confirm the submission"
        )
    
    # Use register number from session (provided during login)
    register_number = session.register_number  # Primary: use stored register number
    if not register_number:
        # Fallback: try to extract from fullname
        if session.moodle_fullname:
            match = re.search(r'\b(\d{12})\b', session.moodle_fullname)
            if match:
                register_number = match.group(1)
        # Final fallback: use moodle username
        if not register_number:
            register_number = session.moodle_username
    
    logger.info(f"Submit request for {submission.artifact_uuid} by register_number: {register_number}")
    
    # Get the decrypted Moodle token
    moodle_token = get_decrypted_token(session)
    
    # Create submission service
    submission_service = SubmissionService(db)
    
    # Execute submission
    success, message, result = await submission_service.submit_artifact(
        artifact_uuid=submission.artifact_uuid,
        moodle_token=moodle_token,
        moodle_user_id=session.moodle_user_id,
        moodle_username=session.moodle_username,
        register_number=register_number,
        actor_ip=request.client.host if request.client else None,
        lock_submission=True
    )
    
    await db.commit()
    
    if not success:
        # Check if it was queued
        if result and result.get("queued"):
            return SubmissionResponse(
                success=False,
                message=message,
                artifact_uuid=submission.artifact_uuid,
                workflow_status=WorkflowStatusEnum.QUEUED
            )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    # Get updated artifact for response
    artifact_service = ArtifactService(db)
    artifact = await artifact_service.get_by_uuid(submission.artifact_uuid)
    
    return SubmissionResponse(
        success=True,
        message=message,
        artifact_uuid=submission.artifact_uuid,
        workflow_status=WorkflowStatusEnum(artifact.workflow_status.value),
        moodle_submission_id=artifact.moodle_submission_id,
        submitted_at=artifact.submit_timestamp
    )


@router.get("/submission/{artifact_uuid}/status")
async def get_submission_status(
    artifact_uuid: str,
    session: StudentSession = Depends(get_student_session),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the status of a submission
    """
    artifact_service = ArtifactService(db)
    artifact = await artifact_service.get_by_uuid(artifact_uuid)
    
    if not artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found"
        )
    
    # Security check
    session_reg_no = _get_session_register_number(session)
    if artifact.parsed_reg_no != session_reg_no:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own submissions"
        )
    
    return {
        "artifact_uuid": str(artifact.artifact_uuid),
        "status": artifact.workflow_status.value,
        "moodle_submission_id": artifact.moodle_submission_id,
        "submitted_at": artifact.submit_timestamp.isoformat() if artifact.submit_timestamp else None,
        "error_message": artifact.error_message,
        "retry_count": artifact.retry_count
    }


@router.get("/history")
async def get_submission_history(
    limit: int = Query(default=20, le=100),
    session: StudentSession = Depends(get_student_session),
    db: AsyncSession = Depends(get_db)
):
    """
    Get submission history for the student
    """
    artifact_service = ArtifactService(db)
    
    # Get all artifacts for this student
    pending = await artifact_service.get_pending_for_student(
        register_number=session.moodle_username,
        moodle_user_id=session.moodle_user_id
    )
    
    submitted = await artifact_service.get_submitted_for_student(
        register_number=session.moodle_username
    )
    
    history = []
    
    for a in pending + submitted:
        history.append({
            "artifact_uuid": str(a.artifact_uuid),
            "filename": a.original_filename,
            "subject_code": a.parsed_subject_code,
            "status": a.workflow_status.value,
            "uploaded_at": a.uploaded_at.isoformat() if a.uploaded_at else None,
            "submitted_at": a.submit_timestamp.isoformat() if a.submit_timestamp else None
        })
    
    # Sort by upload date, newest first
    history.sort(key=lambda x: x["uploaded_at"] or "", reverse=True)
    
    return {
        "total": len(history),
        "history": history[:limit]
    }
