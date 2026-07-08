"""
Student API Routes
Handles student dashboard and submission
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query, Header, Response
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
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
from app.services.moodle_client import MoodleClient
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


@router.get("/avatar")
async def get_moodle_avatar(
    session: StudentSession = Depends(get_student_session),
):
    """
    Get student's Moodle profile photo.
    If not available in Moodle or if it fails, it will raise an HTTP 404
    so the frontend can fall back to the default avatar.
    """
    import httpx
    token = get_decrypted_token(session)
    
    # We can get site info
    client = MoodleClient(token=token)
    try:
        site_info = await client.get_site_info(token=token)
        userpictureurl = site_info.get("userpictureurl")
        if not userpictureurl:
            raise HTTPException(status_code=404, detail="No profile picture URL in Moodle")
            
        # Download and stream the image
        async with httpx.AsyncClient() as http_client:
            url = userpictureurl
            if "?" not in url:
                url += f"?token={token}"
            else:
                if "token=" not in url:
                    url += f"&token={token}"
                    
            resp = await http_client.get(url, timeout=10.0, follow_redirects=True)
            if resp.status_code == 200:
                return Response(content=resp.content, media_type=resp.headers.get("content-type", "image/jpeg"))
            else:
                raise HTTPException(status_code=404, detail="Failed to retrieve picture from Moodle")
    except Exception as e:
        logger.warning(f"Failed to fetch moodle avatar: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    finally:
        await client.close()


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
    
    # Derive a strict register number (12-digit) if available; otherwise rely on Moodle identity
    import re
    extracted_reg = None
    if session.register_number:
        extracted_reg = session.register_number
    else:
        if session.moodle_fullname:
            match = re.search(r'\b(\d{12})\b', session.moodle_fullname)
            if match:
                extracted_reg = match.group(1)

    # Only use the register_number when it looks like a 10-12 digit university register
    register_number = extracted_reg if extracted_reg and re.fullmatch(r"\d{10,12}", extracted_reg) else None

    logger.info(f"Dashboard for register_number: {register_number or '(none)'} moodle_username: {session.moodle_username}")

    # Get pending papers for this student. Provide both register (when present) and Moodle identity.
    pending_artifacts = await artifact_service.get_pending_for_student(
        register_number=register_number,
        moodle_user_id=None, # Use username only, since ID varies by portal
        moodle_username=session.moodle_username
    )
    
    # Get submitted papers
    submitted_artifacts = await artifact_service.get_submitted_for_student(
        register_number=register_number
    )
    
    # Build pending papers list with subject info
    pending_papers = []
    for artifact in pending_artifacts:
        # Get subject mapping for additional info
        exam_type = getattr(artifact, 'exam_type', 'CIA1') or 'CIA1'
        mapping = None
        if artifact.parsed_subject_code:
            mapping = await mapping_service.get_mapping(artifact.parsed_subject_code, exam_type)
        
        # Check if we have a valid assignment mapping
        assignment_id = await mapping_service.get_assignment_id(artifact.parsed_subject_code, exam_type) if artifact.parsed_subject_code else None
        attempt_number = getattr(artifact, 'attempt_number', 1) or 1
        attempt_2_locked = getattr(artifact, 'attempt_2_locked', True)
        workflow_status = artifact.workflow_status
        is_retained_attempt = workflow_status == WorkflowStatusEnum.SUPERSEDED or (
            getattr(workflow_status, "value", workflow_status) == "SUPERSEDED"
        )
        can_submit = assignment_id is not None and not (attempt_number == 2 and attempt_2_locked) and not is_retained_attempt
        message = None
        if not assignment_id:
            message = "This subject is not mapped yet. Please contact admin."
        elif is_retained_attempt:
            message = "Attempt 1 is retained for reference after Attempt 2 replacement."
        elif attempt_number == 2 and attempt_2_locked:
            message = "Attempt 2 is locked. Staff must unlock it before submission."
        
        pending_papers.append(StudentPendingPaper(
            artifact_uuid=str(artifact.artifact_uuid),
            subject_code=artifact.parsed_subject_code or "Unknown",
            subject_name=mapping.subject_name if mapping else None,
            assignment_name=mapping.moodle_assignment_name if mapping else None,
            filename=artifact.original_filename,
            uploaded_at=artifact.uploaded_at,
            workflow_status=artifact.workflow_status.value.lower() if artifact.workflow_status else None,
            exam_type=exam_type,
            attempt_number=attempt_number,
            attempt_2_locked=attempt_2_locked,
            can_submit=can_submit,
            message=message,
            target_site_url=mapping.target_site_url if mapping else None
        ))
    
    # Build submitted papers list (include subject_name from mapping if available)
    submitted_papers = []
    for a in submitted_artifacts:
        a_exam_type = getattr(a, 'exam_type', 'CIA1') or 'CIA1'
        mapping = None
        if a.parsed_subject_code:
            mapping = await mapping_service.get_mapping(a.parsed_subject_code, a_exam_type)

        submitted_papers.append(
            ArtifactResponse(
                id=a.id,
                artifact_uuid=str(a.artifact_uuid),
                raw_filename=a.raw_filename,
                original_filename=a.original_filename,
                subject_name=mapping.subject_name if mapping else None,
                target_site_url=mapping.target_site_url if mapping else None,
                parsed_reg_no=a.parsed_reg_no,
                parsed_subject_code=a.parsed_subject_code,
                exam_type=a_exam_type,
                attempt_number=getattr(a, 'attempt_number', 1) or 1,
                attempt_2_locked=getattr(a, 'attempt_2_locked', True),
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
        # Fallback: Serve from database if disk file is missing
        if artifact.file_content:
            from io import BytesIO
            logger.info(f"File missing on disk, serving from DB for artifact {artifact_uuid}")
            safe_name = (artifact.original_filename or "paper").replace('"', "")
            media_type = artifact.mime_type or "application/pdf"
            return StreamingResponse(
                BytesIO(artifact.file_content),
                media_type=media_type,
                headers={
                    "Content-Disposition": f'inline; filename="{safe_name}"',
                    "X-Source": "database"
                }
            )
            
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on server or database"
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


@router.get("/paper/{artifact_uuid}/receipt")
async def get_digital_receipt(
    artifact_uuid: str,
    session: StudentSession = Depends(get_student_session),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate and download a cryptographically signed digital receipt (PDF).
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
            detail="You can only view your own receipts"
        )

    # Check status
    from app.db.models import WorkflowStatus
    if artifact.workflow_status not in [WorkflowStatus.SUBMITTED_TO_LMS, WorkflowStatus.COMPLETED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Receipts are only available for successfully submitted papers"
        )

    import hmac
    import hashlib
    import json
    from io import BytesIO
    from app.core.config import settings
    import qrcode
    from reportlab.pdfgen import canvas
    import hmac
    import hashlib
    import json
    from io import BytesIO
    from app.core.config import settings
    import qrcode
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.colors import HexColor

    # Prepare data for signature
    receipt_data = {
        "artifact_uuid": str(artifact.artifact_uuid),
        "register_number": artifact.parsed_reg_no,
        "subject_code": artifact.parsed_subject_code,
        "submit_timestamp": artifact.submit_timestamp.isoformat() if artifact.submit_timestamp else "",
        "file_hash": artifact.file_hash
    }
    data_string = json.dumps(receipt_data, sort_keys=True)
    
    # Generate HMAC signature
    secret = settings.secret_key.encode('utf-8')
    signature = hmac.new(secret, data_string.encode('utf-8'), hashlib.sha256).hexdigest()
    
    # Generate QR Code
    qr_data = f"Receipt Verification\nSignature: {signature}\nUUID: {artifact_uuid}"
    qr = qrcode.QRCode(version=1, box_size=5, border=1)
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Save QR to a BytesIO
    from reportlab.lib.utils import ImageReader
    qr_bytes = BytesIO()
    qr_img.save(qr_bytes, format='PNG')
    qr_bytes.seek(0)

    # Generate PDF
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    width, height = letter # 612 x 792

    # Outer Card
    c.setStrokeColor(HexColor('#cbd5e1'))
    c.setLineWidth(1)
    c.roundRect(20, 20, width - 40, height - 40, 12, stroke=1, fill=0)

    # --- Header Banner ---
    c.saveState()
    path = c.beginPath()
    r = 12
    x, y, w, h = 20, 20, width - 40, height - 40
    # Top banner rect height = 110pt
    path.moveTo(x, y + h - r)
    path.arcTo(x, y + h - 2*r, x + 2*r, y + h, 90, 90)
    path.lineTo(x + w - r, y + h)
    path.arcTo(x + w - 2*r, y + h - 2*r, x + w, y + h, 0, 90)
    path.lineTo(x + w, y + h - 110)
    path.lineTo(x, y + h - 110)
    path.close()
    c.clipPath(path, fill=1, stroke=0)
    
    # Background fill for banner
    c.setFillColor(HexColor('#0d47a1')) # Deep Blue
    c.rect(x, y + h - 110, w, 110, fill=1, stroke=0)
    
    # Draw Shield Check in Header
    c.setStrokeColor(HexColor('#ffffff'))
    c.setLineWidth(2.5)
    c.setLineJoin(1)
    hx, hy = 60, height - 60
    # Shield outline
    c.setFillColor(HexColor('#0d47a1'))
    shield = c.beginPath()
    shield.moveTo(hx - 16, hy + 18)
    shield.lineTo(hx + 16, hy + 18)
    shield.lineTo(hx + 16, hy - 2)
    shield.curveTo(hx + 16, hy - 14, hx + 8, hy - 22, hx, hy - 26)
    shield.curveTo(hx - 8, hy - 22, hx - 16, hy - 14, hx - 16, hy - 2)
    shield.close()
    c.drawPath(shield, fill=1, stroke=1)
    # Checkmark inside
    c.setLineWidth(2.5)
    check = c.beginPath()
    check.moveTo(hx - 6, hy + 2)
    check.lineTo(hx - 2, hy - 4)
    check.lineTo(hx + 8, hy + 8)
    c.drawPath(check, fill=0, stroke=1)
    
    # Draw Badge in Header Right
    bx, by = width - 60, height - 60
    c.setFillColor(HexColor('#ffffff'))
    c.setStrokeColor(HexColor('#ffffff'))
    c.setLineWidth(1)
    # Ribbon tails
    ribbon = c.beginPath()
    ribbon.moveTo(bx - 10, by)
    ribbon.lineTo(bx - 18, by - 30)
    ribbon.lineTo(bx - 8, by - 24)
    ribbon.lineTo(bx + 2, by - 30)
    ribbon.lineTo(bx + 10, by)
    ribbon.close()
    c.drawPath(ribbon, fill=1, stroke=0)
    # Outer circle
    c.circle(bx, by, 18, fill=1, stroke=0)
    # Inner blue circle
    c.setFillColor(HexColor('#0d47a1'))
    c.circle(bx, by, 14, fill=1, stroke=0)
    # Checkmark
    c.setStrokeColor(HexColor('#ffffff'))
    c.setLineWidth(2)
    check2 = c.beginPath()
    check2.moveTo(bx - 5, by + 1)
    check2.lineTo(bx - 2, by - 3)
    check2.lineTo(bx + 6, by + 5)
    c.drawPath(check2, fill=0, stroke=1)

    c.restoreState()

    # Header Text
    c.setFillColor(HexColor('#ffffff'))
    c.setFont("Helvetica-Bold", 22)
    c.drawString(100, height - 58, "Digital Submission Receipt")
    c.setFont("Helvetica", 10)
    c.setFillColor(HexColor('#bfdbfe'))
    c.drawString(100, height - 76, "Saveetha Engineering College — Intelligent Examination Submission Framework")

    # --- Submission Details Section ---
    c.setFillColor(HexColor('#1e3a8a'))
    c.setFont("Helvetica-Bold", 14)
    # Sheet Icon
    c.setFillColor(HexColor('#eff6ff'))
    c.roundRect(40, height - 165, 26, 26, 6, fill=1, stroke=0)
    c.setStrokeColor(HexColor('#3b82f6'))
    c.setLineWidth(1.5)
    doc = c.beginPath()
    doc.moveTo(48, height - 146)
    doc.lineTo(58, height - 146)
    doc.moveTo(48, height - 152)
    doc.lineTo(58, height - 152)
    doc.moveTo(48, height - 158)
    doc.lineTo(54, height - 158)
    c.drawPath(doc, fill=0, stroke=1)
    
    c.setFillColor(HexColor('#1e3a8a'))
    c.drawString(75, height - 157, "Submission Details")

    details = [
        ("Name", f"{session.moodle_fullname or 'Unknown'}"),
        ("Register Number", f"{artifact.parsed_reg_no}"),
        ("Subject Code", f"{artifact.parsed_subject_code}"),
        ("Moodle Assignment ID", f"{artifact.moodle_assignment_id}"),
        ("Submitted At", f"{artifact.submit_timestamp.strftime('%Y-%m-%d %H:%M:%S (UTC)') if artifact.submit_timestamp else 'N/A'}")
    ]
    
    start_y = height - 200
    row_height = 32
    
    for i, (label, val) in enumerate(details):
        curr_y = start_y - (i * row_height)
        
        if i < len(details):
            c.setStrokeColor(HexColor('#f1f5f9'))
            c.setLineWidth(1)
            c.line(40, curr_y - 12, width - 230, curr_y - 12)
            
        c.setFillColor(HexColor('#334155'))
        c.setFont("Helvetica-Bold", 10)
        c.drawString(40, curr_y, label)
        
        c.drawString(190, curr_y, ":")
        
        # Draw Light Blue Icon Container
        c.setFillColor(HexColor('#eff6ff'))
        c.roundRect(210, curr_y - 4, 18, 18, 4, fill=1, stroke=0)
        
        c.setStrokeColor(HexColor('#3b82f6'))
        c.setFillColor(HexColor('#3b82f6'))
        c.setLineWidth(1.2)
        ix, iy = 219, curr_y + 5
        
        if i == 0: # User
            c.circle(ix, iy+1, 2.5, fill=1, stroke=0)
            up = c.beginPath()
            up.moveTo(ix-4, iy-5)
            up.curveTo(ix-4, iy-2, ix+4, iy-2, ix+4, iy-5)
            c.drawPath(up, fill=0, stroke=1)
        elif i == 1: # ID Card
            c.roundRect(ix-5, iy-4, 10, 7, 1, fill=0, stroke=1)
            c.rect(ix-3, iy-1, 2, 2, fill=1, stroke=0)
            c.line(ix+1, iy, ix+3, iy)
            c.line(ix-3, iy-2, ix+3, iy-2)
        elif i == 2: # Book
            c.rect(ix-4, iy-4, 4, 7, fill=0, stroke=1)
            c.rect(ix, iy-4, 4, 7, fill=0, stroke=1)
        elif i == 3: # Doc
            c.roundRect(ix-4, iy-5, 8, 10, 1, fill=0, stroke=1)
            c.line(ix-2, iy+2, ix+2, iy+2)
            c.line(ix-2, iy, ix+2, iy)
        elif i == 4: # Calendar
            c.roundRect(ix-5, iy-5, 10, 9, 1, fill=0, stroke=1)
            c.line(ix-5, iy+1, ix+5, iy+1)
            c.line(ix-2, iy+4, ix-2, iy+5)
            c.line(ix+2, iy+4, ix+2, iy+5)
            c.circle(ix-2, iy-2, 0.5, fill=1, stroke=0)
        
        c.setFillColor(HexColor('#1e293b'))
        c.setFont("Helvetica", 10)
        c.drawString(240, curr_y, val)

    # --- Document Lock Illustration ---
    ill_x, ill_y = width - 130, height - 250
    # Shadow
    c.setFillColor(HexColor('#f1f5f9'))
    c.roundRect(ill_x - 45, ill_y - 65, 90, 110, 12, fill=1, stroke=0)
    # Doc
    c.setFillColor(HexColor('#ffffff'))
    c.setStrokeColor(HexColor('#cbd5e1'))
    c.setLineWidth(2)
    c.roundRect(ill_x - 50, ill_y - 60, 90, 110, 8, fill=1, stroke=1)
    # Lines
    c.setFillColor(HexColor('#e2e8f0'))
    c.rect(ill_x - 35, ill_y + 25, 45, 6, fill=1, stroke=0)
    c.rect(ill_x - 35, ill_y + 10, 60, 6, fill=1, stroke=0)
    c.rect(ill_x - 35, ill_y - 5, 60, 6, fill=1, stroke=0)
    # Green Check Badge
    c.setFillColor(HexColor('#10b981'))
    c.circle(ill_x - 20, ill_y - 25, 18, fill=1, stroke=0)
    c.setStrokeColor(HexColor('#ffffff'))
    c.setLineWidth(3)
    cb = c.beginPath()
    cb.moveTo(ill_x - 28, ill_y - 25)
    cb.lineTo(ill_x - 23, ill_y - 32)
    cb.lineTo(ill_x - 12, ill_y - 18)
    c.drawPath(cb, fill=0, stroke=1)
    # Padlock
    c.setFillColor(HexColor('#3b82f6'))
    c.roundRect(ill_x + 10, ill_y - 55, 30, 24, 4, fill=1, stroke=0)
    c.setStrokeColor(HexColor('#3b82f6'))
    c.setLineWidth(3)
    shackle = c.beginPath()
    shackle.moveTo(ill_x + 16, ill_y - 31)
    shackle.lineTo(ill_x + 16, ill_y - 25)
    shackle.arcTo(ill_x + 16, ill_y - 34, ill_x + 34, ill_y - 16, 180, -180)
    shackle.lineTo(ill_x + 34, ill_y - 31)
    c.drawPath(shackle, fill=0, stroke=1)
    c.setFillColor(HexColor('#ffffff'))
    c.circle(ill_x + 25, ill_y - 42, 3, fill=1, stroke=0)
    c.rect(ill_x + 24, ill_y - 48, 2, 6, fill=1, stroke=0)

    # --- File Hash Card ---
    c.setFillColor(HexColor('#ffffff'))
    c.setStrokeColor(HexColor('#e2e8f0'))
    c.setLineWidth(1)
    c.roundRect(40, height - 480, 310, 85, 8, fill=1, stroke=1)
    
    # Shield Icon in hash card
    c.setFillColor(HexColor('#eff6ff'))
    c.circle(70, height - 437, 20, fill=1, stroke=0)
    c.setStrokeColor(HexColor('#1d4ed8'))
    c.setLineWidth(2)
    sc = c.beginPath()
    sc.moveTo(60, height - 432)
    sc.lineTo(80, height - 432)
    sc.lineTo(80, height - 442)
    sc.curveTo(80, height - 448, 75, height - 452, 70, height - 454)
    sc.curveTo(65, height - 452, 60, height - 448, 60, height - 442)
    sc.close()
    c.drawPath(sc, fill=0, stroke=1)
    
    c.setFillColor(HexColor('#1e3a8a'))
    c.setFont("Helvetica-Bold", 10)
    c.drawString(100, height - 427, "File Hash (SHA-256)")
    
    # Textbox with Hash
    c.setFillColor(HexColor('#ffffff'))
    c.setStrokeColor(HexColor('#cbd5e1'))
    c.roundRect(100, height - 462, 235, 26, 4, fill=1, stroke=1)
    c.setFillColor(HexColor('#475569'))
    c.setFont("Courier", 7.5)
    c.drawString(108, height - 452, artifact.file_hash)

    # --- Digital Signature Card ---
    c.setFillColor(HexColor('#ffffff'))
    c.setStrokeColor(HexColor('#e2e8f0'))
    c.roundRect(40, height - 580, 310, 85, 8, fill=1, stroke=1)
    
    # Key Icon in signature card
    c.setFillColor(HexColor('#ecfdf5'))
    c.circle(70, height - 537, 20, fill=1, stroke=0)
    c.setStrokeColor(HexColor('#10b981'))
    c.setLineWidth(2)
    kc = c.beginPath()
    kc.moveTo(74, height - 533)
    kc.lineTo(60, height - 547)
    kc.moveTo(64, height - 543)
    kc.lineTo(67, height - 546)
    kc.moveTo(68, height - 539)
    kc.lineTo(71, height - 542)
    c.drawPath(kc, fill=0, stroke=1)
    c.circle(76, height - 531, 3.5, fill=0, stroke=1)
    
    c.setFillColor(HexColor('#1e3a8a'))
    c.setFont("Helvetica-Bold", 10)
    c.drawString(100, height - 527, "Digital Signature")
    
    # Textbox with Signature
    c.setFillColor(HexColor('#ffffff'))
    c.setStrokeColor(HexColor('#cbd5e1'))
    c.roundRect(100, height - 562, 235, 26, 4, fill=1, stroke=1)
    c.setFillColor(HexColor('#475569'))
    c.setFont("Courier", 7.5)
    c.drawString(108, height - 552, signature)

    # --- Verify Receipt Box ---
    c.setFillColor(HexColor('#eff6ff'))
    c.setStrokeColor(HexColor('#bfdbfe'))
    c.roundRect(370, height - 580, 202, 185, 8, fill=1, stroke=1)
    
    c.setFillColor(HexColor('#1d4ed8'))
    c.setFont("Helvetica-Bold", 10)
    c.drawString(385, height - 415, "Verify Receipt")
    c.setFillColor(HexColor('#4b5563'))
    c.setFont("Helvetica", 8)
    c.drawString(385, height - 428, "Scan the QR code to verify the authenticity")
    c.drawString(385, height - 438, "of this submission.")
    
    # Draw QR Code
    c.drawImage(ImageReader(qr_bytes), 421, height - 545, width=100, height=100)
    
    timestamp_str = artifact.submit_timestamp.strftime('%Y%m%d-%H%M%S') if artifact.submit_timestamp else "00000000-000000"
    ref_code = f"SUB-{timestamp_str}"
    c.setFillColor(HexColor('#1e3a8a'))
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(471, height - 562, ref_code)

    # --- Footer ---
    c.setStrokeColor(HexColor('#e2e8f0'))
    c.setLineWidth(1)
    c.line(40, 60, width - 40, 60)
    
    c.setFillColor(HexColor('#10b981'))
    shield_f = c.beginPath()
    fx, fy = 50, 42
    shield_f.moveTo(fx - 8, fy + 8)
    shield_f.lineTo(fx + 8, fy + 8)
    shield_f.lineTo(fx + 8, fy - 1)
    shield_f.curveTo(fx + 8, fy - 7, fx + 4, fy - 11, fx, fy - 13)
    shield_f.curveTo(fx - 4, fy - 11, fx - 8, fy - 7, fx - 8, fy - 1)
    shield_f.close()
    c.drawPath(shield_f, fill=1, stroke=0)
    
    c.setStrokeColor(HexColor('#ffffff'))
    c.setLineWidth(1.5)
    check_f = c.beginPath()
    check_f.moveTo(fx - 3, fy)
    check_f.lineTo(fx - 1, fy - 3)
    check_f.lineTo(fx + 4, fy + 3)
    c.drawPath(check_f, fill=0, stroke=1)
    
    c.setFillColor(HexColor('#047857'))
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(65, 39, "This receipt is cryptographically signed and serves as proof of submission.")

    c.setFillColor(HexColor('#64748b'))
    c.setFont("Helvetica", 8)
    time_str = artifact.submit_timestamp.strftime('%Y-%m-%d %H:%M:%S (UTC)') if artifact.submit_timestamp else 'N/A'
    c.drawRightString(width - 40, 39, f"Generated on: {time_str}")

    c.showPage()
    c.save()
    
    pdf_buffer.seek(0)
    
    filename = f"Receipt_{artifact.parsed_subject_code}_{artifact.parsed_reg_no}.pdf"
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.post("/paper/{artifact_uuid}/report")
async def report_artifact_issue(
    artifact_uuid: str,
    request: Request,
    session: StudentSession = Depends(get_student_session),
    db: AsyncSession = Depends(get_db)
):
    """
    Allow a student to report an issue with an uploaded paper (wrong reg/subject etc.)

    Body: { "message": str, "suggested_reg_no": Optional[str], "suggested_subject_code": Optional[str] }
    """
    artifact_service = ArtifactService(db)
    audit_service = AuditService(db)

    payload = await request.json()
    message = (payload or {}).get("message")
    suggested_reg = (payload or {}).get("suggested_reg_no")
    suggested_subject = (payload or {}).get("suggested_subject_code")

    if not message:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Report message is required")

    artifact = await artifact_service.get_by_uuid(artifact_uuid)
    if not artifact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found")

    # Security: only the owning student may report this artifact
    session_reg = _get_session_register_number(session)
    if artifact.parsed_reg_no != session_reg:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You may only report your own papers")

    # Log the report in audit logs so staff can view
    await audit_service.log_action(
        action="report_issue",
        action_category="report",
        actor_type="student",
        actor_id=str(session.moodle_user_id),
        actor_username=session.moodle_username,
        artifact_id=artifact.id,
        description=message,
        request_data={
            "suggested_reg_no": suggested_reg,
            "suggested_subject_code": suggested_subject
        }
    )

    # Persist audit log
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    return {"success": True, "message": "Report submitted. Staff will review and take action."}


@router.get("/reports")
async def get_my_reports(
    session: StudentSession = Depends(get_student_session),
    db: AsyncSession = Depends(get_db)
):
    """
    Return reports submitted by the currently logged-in student, with resolved status.
    """
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session required")

    artifact_service = ArtifactService(db)

    from app.db.models import AuditLog

    result = await db.execute(
        select(AuditLog)
        .where(
            AuditLog.actor_type == 'student',
            AuditLog.actor_id == str(session.moodle_user_id),
            AuditLog.action == 'report_issue'
        )
        .order_by(AuditLog.created_at.desc())
    )

    reports = result.scalars().all()
    out = []

    for r in reports:
        artifact = await artifact_service.get_by_id(r.artifact_id) if r.artifact_id else None
        # Skip reports that have been deleted (student withdrew) - check audit logs
        deleted_q = await db.execute(
            select(AuditLog).where(AuditLog.action == 'report_deleted', AuditLog.target_id == str(r.id)).order_by(AuditLog.created_at.desc())
        )
        deleted_entry = deleted_q.scalars().first()
        if deleted_entry:
            # skip this report (it was deleted/withdrawn)
            continue

        resolved_q = await db.execute(
            select(AuditLog).where(AuditLog.action == 'report_resolved', AuditLog.target_id == str(r.id)).order_by(AuditLog.created_at.desc())
        )
        # use scalars().first() to tolerate multiple resolution entries and pick latest
        resolved = resolved_q.scalars().first()

        resolved_note = None
        if resolved:
            rd = resolved.request_data or {}
            resolved_note = rd.get('note') or (resolved.response_data and resolved.response_data.get('note'))

        out.append({
            "id": r.id,
            "artifact_id": r.artifact_id,
            "artifact_uuid": str(artifact.artifact_uuid) if artifact else None,
            "original_filename": artifact.original_filename if artifact else None,
            "parsed_reg_no": artifact.parsed_reg_no if artifact else None,
            "parsed_subject_code": artifact.parsed_subject_code if artifact else None,
            "description": r.description,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "resolved": bool(bool(resolved)),
            "resolved_by": resolved.actor_username if resolved and resolved.actor_username else (resolved.actor_id if resolved else None),
            "resolved_at": resolved.created_at.isoformat() if resolved and resolved.created_at else None,
            "resolved_note": resolved_note
        })

    return out


@router.delete("/reports/{report_id}")
async def delete_my_report(
    report_id: int,
    session: StudentSession = Depends(get_student_session),
    db: AsyncSession = Depends(get_db)
):
    """
    Allow a student to delete (withdraw) a previously submitted report.
    This creates an audit entry `report_deleted` and leaves original report for traceability.
    """
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session required")

    from app.db.models import AuditLog

    # Verify the report exists and belongs to this student
    q = await db.execute(
        select(AuditLog).where(
            AuditLog.id == int(report_id),
            AuditLog.actor_type == 'student',
            AuditLog.actor_id == str(session.moodle_user_id),
            AuditLog.action == 'report_issue'
        )
    )
    rpt = q.scalar_one_or_none()
    if not rpt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found or not owned by you")

    # Use AuditService to create a proper audit entry (ensures action_category is set)
    audit_service = AuditService(db)
    try:
        await audit_service.log_action(
            action='report_deleted',
            action_category='report',
            actor_type='student',
            actor_id=str(session.moodle_user_id),
            actor_username=session.moodle_username,
            artifact_id=rpt.artifact_id,
            target_type='audit_log',
            target_id=str(report_id),
            description='Student withdrew their report'
        )
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete report: {e}")

    return {"success": True, "message": "Report deleted"}


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
    
    # Get the artifact first to know which subject code (and thus which portal) is needed
    from app.api.routes.auth import get_moodle_user_id
    artifact_service = ArtifactService(db)
    artifact = await artifact_service.get_by_uuid(artifact_uuid)
    
    if not artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found"
        )
    
    # Get the decrypted Moodle token and portal-specific user ID
    moodle_token = get_decrypted_token(session, artifact.parsed_subject_code)
    moodle_user_id = get_moodle_user_id(session, artifact.parsed_subject_code)
    
    if not moodle_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The required portal for this subject was unreachable during login. Please log out and log in again."
        )
    
    # Create submission service
    submission_service = SubmissionService(db)
    
    # Execute submission
    success, message, result = await submission_service.submit_artifact(
        artifact_uuid=artifact_uuid,
        moodle_token=moodle_token,
        moodle_user_id=moodle_user_id,
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
    
    # Get the artifact first to know which subject code (and thus which portal) is needed
    from app.api.routes.auth import get_moodle_user_id
    artifact_service = ArtifactService(db)
    artifact = await artifact_service.get_by_uuid(submission.artifact_uuid)
    
    if not artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found"
        )
    
    # Get the decrypted Moodle token and portal-specific user ID
    moodle_token = get_decrypted_token(session, artifact.parsed_subject_code)
    moodle_user_id = get_moodle_user_id(session, artifact.parsed_subject_code)
    
    if not moodle_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The required portal for this subject was unreachable during login. Please log out and log in again."
        )
    
    # Create submission service
    submission_service = SubmissionService(db)
    
    # Execute submission
    success, message, result = await submission_service.submit_artifact(
        artifact_uuid=submission.artifact_uuid,
        moodle_token=moodle_token,
        moodle_user_id=moodle_user_id,
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
    
    # Get all artifacts for this student (use Moodle identity for history view)
    pending = await artifact_service.get_pending_for_student(
        register_number=None,
        moodle_user_id=None, # Use username only
        moodle_username=session.moodle_username
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


@router.get("/activities")
async def get_student_activities(
    session: StudentSession = Depends(get_student_session),
    db: AsyncSession = Depends(get_db)
):
    """
    Get activities timeline for the student
    """
    from datetime import datetime
    artifact_service = ArtifactService(db)
    mapping_service = SubjectMappingService(db)
    
    # Get university register number
    reg_no = _get_session_register_number(session)
    
    # Get all student artifacts
    pending = await artifact_service.get_pending_for_student(
        register_number=reg_no,
        moodle_user_id=None,
        moodle_username=session.moodle_username
    )
    
    submitted = await artifact_service.get_submitted_for_student(
        register_number=reg_no
    )
    
    activities = []
    
    # For every pending artifact, staff added it
    for a in pending:
        # Get subject mapping info
        exam_type = getattr(a, 'exam_type', 'CIA1') or 'CIA1'
        mapping = await mapping_service.get_mapping(a.parsed_subject_code, exam_type) if a.parsed_subject_code else None
        subj_name = mapping.subject_name if mapping else "Examination Paper"
        
        activities.append({
            "type": "added",
            "subject_code": a.parsed_subject_code or "Unknown",
            "subject_name": subj_name,
            "exam_type": exam_type,
            "timestamp": a.uploaded_at.isoformat() if a.uploaded_at else datetime.now().isoformat(),
            "filename": a.original_filename
        })
        
    # For every submitted artifact, staff added it first, then student submitted it
    for a in submitted:
        exam_type = getattr(a, 'exam_type', 'CIA1') or 'CIA1'
        mapping = await mapping_service.get_mapping(a.parsed_subject_code, exam_type) if a.parsed_subject_code else None
        subj_name = mapping.subject_name if mapping else "Examination Paper"
        
        # 1. Added by staff
        activities.append({
            "type": "added",
            "subject_code": a.parsed_subject_code or "Unknown",
            "subject_name": subj_name,
            "exam_type": exam_type,
            "timestamp": a.uploaded_at.isoformat() if a.uploaded_at else datetime.now().isoformat(),
            "filename": a.original_filename
        })
        
        # 2. Submitted by student
        if a.submit_timestamp:
            activities.append({
                "type": "submitted",
                "subject_code": a.parsed_subject_code or "Unknown",
                "subject_name": subj_name,
                "exam_type": exam_type,
                "timestamp": a.submit_timestamp.isoformat(),
                "student_name": session.moodle_fullname or session.moodle_username,
                "filename": a.original_filename
            })
            
    # Sort activities by timestamp desc
    activities.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return {"activities": activities}

