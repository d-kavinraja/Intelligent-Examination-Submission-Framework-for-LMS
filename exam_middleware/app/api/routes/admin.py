"""
Admin API Routes
Administrative functions for system management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy import text
from typing import Optional
from sqlalchemy.exc import IntegrityError
import logging

from app.db.database import get_db
from app.db.models import StaffUser, SubjectMapping, ExaminationArtifact, StudentUsernameRegister
from app.schemas import (
    SubjectMappingCreate,
    SubjectMappingResponse,
    AuditLogResponse,
    SystemStatsResponse,
)
from app.services.artifact_service import ArtifactService, SubjectMappingService, AuditService
from app.services.submission_service import SubmissionService
from app.services.moodle_client import MoodleClient, MoodleAPIError
from app.api.routes.auth import get_current_staff
from app.core.config import settings
from app.core.security import generate_transaction_id
from app.db.models import AuditLog

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================
# Subject Mapping Management
# ============================================

@router.get("/mappings", response_model=list[SubjectMappingResponse])
async def list_subject_mappings(
    db: AsyncSession = Depends(get_db),
    current_staff: StaffUser = Depends(get_current_staff)
):
    """
    List all subject to assignment mappings
    """
    mapping_service = SubjectMappingService(db)
    mappings = await mapping_service.get_all_active()
    
    return [
        SubjectMappingResponse(
            id=m.id,
            subject_code=m.subject_code,
            subject_name=m.subject_name,
            moodle_course_id=m.moodle_course_id,
            moodle_assignment_id=m.moodle_assignment_id,
            moodle_assignment_name=m.moodle_assignment_name,
            exam_session=m.exam_session,
            is_active=m.is_active,
            created_at=m.created_at,
            last_verified_at=m.last_verified_at
        )
        for m in mappings
    ]


@router.post("/mappings", response_model=SubjectMappingResponse)
async def create_subject_mapping(
    mapping: SubjectMappingCreate,
    db: AsyncSession = Depends(get_db),
    current_staff: StaffUser = Depends(get_current_staff)
):
    """
    Create a new subject to assignment mapping
    """
    mapping_service = SubjectMappingService(db)
    
    # Check if mapping already exists
    existing = await mapping_service.get_mapping(mapping.subject_code)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Mapping for {mapping.subject_code} already exists"
        )
    
    new_mapping = await mapping_service.create_mapping(
        subject_code=mapping.subject_code,
        moodle_course_id=mapping.moodle_course_id,
        moodle_assignment_id=mapping.moodle_assignment_id,
        subject_name=mapping.subject_name,
        moodle_assignment_name=mapping.moodle_assignment_name,
        exam_session=mapping.exam_session
    )
    
    await db.commit()
    
    return SubjectMappingResponse(
        id=new_mapping.id,
        subject_code=new_mapping.subject_code,
        subject_name=new_mapping.subject_name,
        moodle_course_id=new_mapping.moodle_course_id,
        moodle_assignment_id=new_mapping.moodle_assignment_id,
        moodle_assignment_name=new_mapping.moodle_assignment_name,
        exam_session=new_mapping.exam_session,
        is_active=new_mapping.is_active,
        created_at=new_mapping.created_at,
        last_verified_at=new_mapping.last_verified_at
    )


@router.post("/mappings/sync")
async def sync_mappings_from_config(
    db: AsyncSession = Depends(get_db),
    current_staff: StaffUser = Depends(get_current_staff)
):
    """
    Sync subject mappings from configuration
    """
    mapping_service = SubjectMappingService(db)
    created = await mapping_service.sync_from_config()
    await db.commit()
    
    return {
        "message": f"Synced {created} new mappings from configuration",
        "created": created
    }


@router.post("/mappings/auto")
async def auto_create_subject_mapping(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_staff: StaffUser = Depends(get_current_staff)
):
    """
    Auto-discover assignments from Moodle and create subject mapping.
    Body: {
        "subject_code": "19AI411",
        "moodle_course_id": 2,
        "subject_name": "Machine Learning" (optional),
        "exam_session": "2025-2026" (optional)
    }

    Uses admin token to call Moodle API, fetches assignments for the course,
    and creates a mapping for each discovered assignment.
    """
    if not settings.moodle_admin_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MOODLE_ADMIN_TOKEN not configured on server"
        )

    subject_code = (payload.get("subject_code") or "").strip().upper()
    course_id = payload.get("moodle_course_id")
    subject_name = (payload.get("subject_name") or "").strip() or None
    exam_session = (payload.get("exam_session") or "").strip() or "2025-2026"
    cmid = payload.get("cmid")  # Optional: course module ID from Moodle URL

    if not subject_code or not course_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="subject_code and moodle_course_id are required"
        )

    client = MoodleClient(token=settings.moodle_admin_token)

    try:
        # Fetch assignments for this course from Moodle
        assignments_data = await client.get_assignments([int(course_id)])
        courses = assignments_data.get("courses", [])

        if not courses:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No course found with ID {course_id} on Moodle, or admin token lacks access"
            )

        assignments = courses[0].get("assignments", [])
        if not assignments:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No assignments found in course {course_id}"
            )

        # Find the right assignment
        if cmid:
            # Match by cmid (the id= from the Moodle assignment URL)
            assignment = next((a for a in assignments if a.get("cmid") == int(cmid)), None)
            if not assignment:
                names = ", ".join([f"{a.get('name','')} (cmid={a.get('cmid')})" for a in assignments])
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No assignment with module ID {cmid} found. Available: {names}"
                )
        else:
            # Auto-select: use the first (only works well for single-assignment courses)
            assignment = assignments[0]

        assignment_id = assignment["id"]
        assignment_name = assignment.get("name", "Unknown")

        # Upsert: update existing or create new
        result = await db.execute(
            select(SubjectMapping).where(SubjectMapping.subject_code == subject_code)
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.moodle_course_id = int(course_id)
            existing.moodle_assignment_id = assignment_id
            existing.moodle_assignment_name = assignment_name
            existing.subject_name = subject_name or assignment_name
            existing.exam_session = exam_session
            existing.is_active = True
            await db.commit()
            action = "Updated"
            mapping = existing
        else:
            mapping = SubjectMapping(
                subject_code=subject_code,
                subject_name=subject_name or assignment_name,
                moodle_course_id=int(course_id),
                moodle_assignment_id=assignment_id,
                moodle_assignment_name=assignment_name,
                exam_session=exam_session,
                is_active=True,
            )
            db.add(mapping)
            await db.commit()
            await db.refresh(mapping)
            action = "Created"

        return {
            "message": f"{action} mapping: {subject_code} → Course {course_id}, Assignment {assignment_id} ({assignment_name})",
            "mapping": {
                "id": mapping.id,
                "subject_code": mapping.subject_code,
                "subject_name": mapping.subject_name,
                "moodle_course_id": mapping.moodle_course_id,
                "moodle_assignment_id": mapping.moodle_assignment_id,
                "moodle_assignment_name": mapping.moodle_assignment_name,
                "exam_session": mapping.exam_session,
            },
            "all_assignments": [
                {"id": a["id"], "name": a.get("name", ""), "cmid": a.get("cmid")}
                for a in assignments
            ],
        }

    except MoodleAPIError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Moodle API error: {e.message}"
        )
    finally:
        await client.close()


@router.delete("/mappings/{mapping_id}")
async def delete_subject_mapping(
    mapping_id: int,
    db: AsyncSession = Depends(get_db),
    current_staff: StaffUser = Depends(get_current_staff)
):
    """
    Delete (deactivate) a subject mapping
    """
    result = await db.execute(
        select(SubjectMapping).where(SubjectMapping.id == mapping_id)
    )
    mapping = result.scalar_one_or_none()
    
    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mapping not found"
        )
    
    mapping.is_active = False
    await db.commit()
    
    return {"message": f"Mapping {mapping.subject_code} deactivated"}


# ============================================
# System Statistics
# ============================================

@router.get("/stats", response_model=SystemStatsResponse)
async def get_system_stats(
    db: AsyncSession = Depends(get_db),
    current_staff: StaffUser = Depends(get_current_staff)
):
    """
    Get system-wide statistics
    """
    artifact_service = ArtifactService(db)
    stats = await artifact_service.get_stats()
    
    # Count active sessions
    from app.db.models import StudentSession
    from datetime import datetime
    
    result = await db.execute(
        select(StudentSession).where(StudentSession.expires_at > datetime.utcnow())
    )
    active_sessions = len(result.scalars().all())
    
    return SystemStatsResponse(
        total_artifacts=sum(stats.values()),
        pending_review=stats.get("pending", 0) + stats.get("pending_review", 0),
        submitted=stats.get("completed", 0) + stats.get("submitted_to_lms", 0),
        failed=stats.get("failed", 0),
        queued=stats.get("queued", 0),
        active_sessions=active_sessions
    )


# ============================================
# Audit Logs
# ============================================

@router.get("/audit-logs", response_model=list[AuditLogResponse])
async def get_audit_logs(
    limit: int = Query(default=100, le=500),
    artifact_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_staff: StaffUser = Depends(get_current_staff)
):
    """
    Get audit logs
    """
    audit_service = AuditService(db)
    
    if artifact_id:
        logs = await audit_service.get_for_artifact(artifact_id)
    else:
        logs = await audit_service.get_recent(limit=limit)
    
    return [
        {
            "id": log.id,
            "action": log.action,
            "action_category": log.action_category,
            "description": log.description,
            "actor_type": log.actor_type,
            "actor_id": log.actor_id,
            "actor_username": log.actor_username,
            "actor_ip": log.actor_ip,
            "artifact_id": log.artifact_id,
            "target_type": log.target_type,
            "target_id": log.target_id,
            "request_data": log.request_data,
            "response_data": log.response_data,
            "created_at": log.created_at,
        }
        for log in logs
    ]


# ============================================
# Queue Management
# ============================================

@router.post("/queue/retry")
async def retry_queued_submissions(
    db: AsyncSession = Depends(get_db),
    current_staff: StaffUser = Depends(get_current_staff)
):
    """
    Manually trigger retry of queued submissions
    """
    if not settings.moodle_admin_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin token not configured for queue processing"
        )
    
    submission_service = SubmissionService(db)
    result = await submission_service.retry_queued_submissions(settings.moodle_admin_token)
    
    return result


@router.get("/queue/status")
async def get_queue_status(
    db: AsyncSession = Depends(get_db),
    current_staff: StaffUser = Depends(get_current_staff)
):
    """
    Get status of the submission queue
    """
    from app.db.models import SubmissionQueue
    
    result = await db.execute(select(SubmissionQueue))
    queue_items = result.scalars().all()
    
    status_counts = {}
    for item in queue_items:
        status_counts[item.status] = status_counts.get(item.status, 0) + 1
    
    return {
        "total_items": len(queue_items),
        "by_status": status_counts,
        "items": [
            {
                "id": item.id,
                "artifact_id": item.artifact_id,
                "status": item.status,
                "retry_count": item.retry_count,
                "queued_at": item.queued_at.isoformat() if item.queued_at else None,
                "last_error": item.last_error
            }
            for item in queue_items[:50]
        ]
    }


# ============================================
# Artifact Management
# ============================================

@router.get("/artifacts/{artifact_uuid}")
async def get_artifact_details(
    artifact_uuid: str,
    db: AsyncSession = Depends(get_db),
    current_staff: StaffUser = Depends(get_current_staff)
):
    """
    Get detailed artifact information (admin view)
    """
    artifact_service = ArtifactService(db)
    artifact = await artifact_service.get_by_uuid(artifact_uuid)
    
    if not artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artifact not found"
        )
    
    return {
        "id": artifact.id,
        "artifact_uuid": str(artifact.artifact_uuid),
        "raw_filename": artifact.raw_filename,
        "original_filename": artifact.original_filename,
        "parsed_reg_no": artifact.parsed_reg_no,
        "parsed_subject_code": artifact.parsed_subject_code,
        "file_hash": artifact.file_hash,
        "file_size_bytes": artifact.file_size_bytes,
        "workflow_status": artifact.workflow_status.value,
        "moodle_user_id": artifact.moodle_user_id,
        "moodle_assignment_id": artifact.moodle_assignment_id,
        "moodle_draft_item_id": artifact.moodle_draft_item_id,
        "moodle_submission_id": artifact.moodle_submission_id,
        "transaction_id": artifact.transaction_id,
        "uploaded_at": artifact.uploaded_at.isoformat() if artifact.uploaded_at else None,
        "submit_timestamp": artifact.submit_timestamp.isoformat() if artifact.submit_timestamp else None,
        "error_message": artifact.error_message,
        "retry_count": artifact.retry_count,
        "transaction_log": artifact.transaction_log
    }


@router.post("/artifacts/{artifact_uuid}/reset")
async def reset_artifact_status(
    artifact_uuid: str,
    db: AsyncSession = Depends(get_db),
    current_staff: StaffUser = Depends(get_current_staff)
):
    """
    Reset artifact status to pending (for retry)
    """
    artifact_service = ArtifactService(db)
    artifact = await artifact_service.get_by_uuid(artifact_uuid)
    
    if not artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artifact not found"
        )
    
    from app.db.models import WorkflowStatus
    
    artifact = await artifact_service.update_status(
        artifact_id=artifact.id,
        status=WorkflowStatus.PENDING_REVIEW,
        log_action="admin_reset",
        log_details={"reset_by": current_staff.username}
    )
    
    # Clear error state
    artifact.error_message = None
    artifact.moodle_draft_item_id = None
    
    await db.commit()
    
    return {"message": "Artifact status reset to pending"}



@router.post("/artifacts/{artifact_uuid}/edit")
async def edit_artifact_metadata(
    artifact_uuid: str,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_staff: StaffUser = Depends(get_current_staff)
):
    """
    Allow staff to edit parsed metadata of an artifact (reg no, subject code)
    Body: { 
        "parsed_reg_no": Optional[str], 
        "parsed_subject_code": Optional[str],
        "original_filename": Optional[str],
        "resolve_reports": Optional[bool] - if true, auto-resolve all active reports for this artifact
    }
    """
    artifact_service = ArtifactService(db)
    audit_service = AuditService(db)

    artifact = await artifact_service.get_by_uuid(artifact_uuid)
    if not artifact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found")

    parsed_reg = payload.get("parsed_reg_no")
    parsed_sub = payload.get("parsed_subject_code")
    original_fname = payload.get("original_filename")

    # Determine the target values after edit (use existing if not provided)
    new_parsed_reg = parsed_reg if parsed_reg is not None else artifact.parsed_reg_no
    new_parsed_sub = parsed_sub if parsed_sub is not None else artifact.parsed_subject_code

    # If both values are present, ensure uniqueness of the (parsed_reg_no, parsed_subject_code) pair
    if new_parsed_reg and new_parsed_sub:
        existing_q = await db.execute(
            select(ExaminationArtifact).where(
                ExaminationArtifact.parsed_reg_no == new_parsed_reg,
                ExaminationArtifact.parsed_subject_code == new_parsed_sub,
                ExaminationArtifact.id != artifact.id
            )
        )
        existing_art = existing_q.scalar_one_or_none()
        if existing_art:
            # If the conflicting artifact is already deleted, allow reuse by clearing the identifiers
            from app.db.models import WorkflowStatus as _WS
            if getattr(existing_art, 'workflow_status', None) == _WS.DELETED:
                existing_art.add_log_entry("cleared_identifiers_for_reuse", {
                    "cleared_by": current_staff.username,
                    "reason": "reusing (reg,subject) for another artifact"
                })
                existing_art.parsed_reg_no = None
                existing_art.parsed_subject_code = None
                existing_art.transaction_id = None
                # flush the change so unique constraint is freed
                await db.flush()
            else:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        f"Another artifact (id={existing_art.id}) already has parsed_reg_no='{new_parsed_reg}' "
                        f"and parsed_subject_code='{new_parsed_sub}'. Edit rejected to preserve uniqueness."
                    )
                )

    changes = {}
    if parsed_reg and parsed_reg != artifact.parsed_reg_no:
        changes["parsed_reg_no"] = {"old": artifact.parsed_reg_no, "new": parsed_reg}

    if parsed_sub and parsed_sub != artifact.parsed_subject_code:
        changes["parsed_subject_code"] = {"old": artifact.parsed_subject_code, "new": parsed_sub}

    if original_fname and original_fname != artifact.original_filename:
        changes["original_filename"] = {"old": artifact.original_filename, "new": original_fname}

    if not changes:
        return {"message": "No changes applied"}

    # Policy: instead of mutating the existing artifact in-place, create a new artifact
    # with the updated metadata and mark the original artifact as deleted/superseded.
    try:
        # Determine target values for the new artifact
        target_reg = parsed_reg if parsed_reg is not None else artifact.parsed_reg_no
        target_sub = parsed_sub if parsed_sub is not None else artifact.parsed_subject_code
        target_original = original_fname if original_fname is not None else artifact.original_filename

        # Create a new artifact record by copying file metadata from the existing artifact
        new_artifact = await artifact_service.create_artifact(
            raw_filename=artifact.raw_filename,
            original_filename=target_original,
            file_blob_path=artifact.file_blob_path,
            file_hash=artifact.file_hash,
            parsed_reg_no=target_reg,
            parsed_subject_code=target_sub,
            file_size_bytes=artifact.file_size_bytes,
            mime_type=artifact.mime_type,
            uploaded_by_staff_id=current_staff.id,
            file_content=artifact.file_content # Preserve the database-backed file content
        )

        # Mark the old artifact as deleted/superseded
        from app.db.models import WorkflowStatus as _WS
        try:
            artifact.workflow_status = _WS.DELETED
            # Clear transaction_id and parsed identifiers so this row no longer blocks uploads
            artifact.transaction_id = None
            artifact.parsed_reg_no = None
            artifact.parsed_subject_code = None
        except Exception:
            artifact.error_message = (artifact.error_message or "") + f"; Superseded by artifact {new_artifact.id}"

        artifact.add_log_entry("admin_replaced", {"replaced_by": new_artifact.id, "replaced_by_uuid": str(new_artifact.artifact_uuid), "edited_by": current_staff.username})

        # Migrate reports (report_issue audit logs) from old artifact to new artifact
        # so that reports continue to show on the updated artifact
        report_logs_q = await db.execute(
            select(AuditLog).where(
                AuditLog.artifact_id == artifact.id,
                AuditLog.action == 'report_issue'
            )
        )
        report_logs = report_logs_q.scalars().all()
        migrated_report_ids = []
        for rlog in report_logs:
            # Update the artifact_id to point to the new artifact
            rlog.artifact_id = new_artifact.id
            migrated_report_ids.append(rlog.id)
        
        # Also migrate any report_resolved and report_deleted entries
        related_logs_q = await db.execute(
            select(AuditLog).where(
                AuditLog.artifact_id == artifact.id,
                AuditLog.action.in_(['report_resolved', 'report_deleted'])
            )
        )
        related_logs = related_logs_q.scalars().all()
        for rlog in related_logs:
            rlog.artifact_id = new_artifact.id

        # Auto-resolve reports if requested
        resolve_reports = payload.get("resolve_reports", False)
        resolved_report_ids = []
        if resolve_reports and migrated_report_ids:
            for report_id in migrated_report_ids:
                # Check if already resolved
                resolved_check = await db.execute(
                    select(AuditLog).where(
                        AuditLog.action == 'report_resolved',
                        AuditLog.target_id == str(report_id)
                    )
                )
                if resolved_check.scalars().first():
                    continue  # Already resolved
                
                # Check if deleted/withdrawn
                deleted_check = await db.execute(
                    select(AuditLog).where(
                        AuditLog.action == 'report_deleted',
                        AuditLog.target_id == str(report_id)
                    )
                )
                if deleted_check.scalars().first():
                    continue  # Withdrawn, can't resolve
                
                # Auto-resolve this report
                await audit_service.log_action(
                    action="report_resolved",
                    action_category="report",
                    actor_type="staff",
                    actor_id=str(current_staff.id),
                    actor_username=current_staff.username,
                    artifact_id=new_artifact.id,
                    description=f"Auto-resolved with metadata edit: {changes}",
                    request_data={"resolved_report_id": report_id, "auto_resolved": True},
                    response_data={"note": "Resolved via metadata edit"},
                    target_type='audit_log',
                    target_id=str(report_id)
                )
                resolved_report_ids.append(report_id)

        # Audit the replacement
        await audit_service.log_action(
            action="admin_replace",
            action_category="admin",
            actor_type="staff",
            actor_id=str(current_staff.id),
            actor_username=current_staff.username,
            artifact_id=new_artifact.id,
            description=f"Created new artifact {new_artifact.id} replacing {artifact.id}",
            request_data={"original_artifact": artifact.id, "changes": changes, "migrated_reports": migrated_report_ids, "resolved_reports": resolved_report_ids},
            response_data={"new_artifact": new_artifact.id}
        )

        await db.commit()

        msg = "Artifact replaced by new artifact with updated metadata"
        if resolved_report_ids:
            msg += f" ({len(resolved_report_ids)} report(s) auto-resolved)"
        if migrated_report_ids:
            msg += f" ({len(migrated_report_ids)} report(s) migrated)"

        return {
            "message": msg,
            "artifact": {
                "id": new_artifact.id,
                "artifact_uuid": str(new_artifact.artifact_uuid),
                "parsed_reg_no": new_artifact.parsed_reg_no,
                "parsed_subject_code": new_artifact.parsed_subject_code
            },
            "migrated_reports": len(migrated_report_ids),
            "resolved_reports": len(resolved_report_ids)
        }
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Update failed: unique constraint violation")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))



@router.delete("/artifacts/{artifact_uuid}")
async def delete_artifact(
    artifact_uuid: str,
    reason: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_staff: StaffUser = Depends(get_current_staff)
):
    """
    Delete an artifact: remove physical file (if present) and mark artifact as failed/removed.
    This keeps an audit trail while removing it from student/staff listings.
    """
    import os
    from app.db.models import WorkflowStatus

    artifact_service = ArtifactService(db)
    audit_service = AuditService(db)

    artifact = await artifact_service.get_by_uuid(artifact_uuid)
    if not artifact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found")

    # Attempt to delete physical file
    try:
        if artifact.file_blob_path:
            path = artifact.file_blob_path.replace('\\', '/')
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    # Log but continue to allow DB update
                    pass
    except Exception:
        pass

    # Ensure the DB enum contains the DELETED value (Postgres enum types must be altered)
    # Try to set the workflow status to DELETED. If the DB enum doesn't support it
    # (e.g. the enum type wasn't migrated), fall back to annotating the artifact
    # error_message and leaving the status unchanged so we don't run DDL here.
    try:
        artifact.workflow_status = WorkflowStatus.DELETED
        artifact.error_message = f"Deleted by staff {current_staff.username}" + (f": {reason}" if reason else "")
        artifact.add_log_entry("admin_delete", {"deleted_by": current_staff.username, "reason": reason})
        await db.flush()
    except Exception as e:
        logger.debug("Could not assign WorkflowStatus.DELETED (possibly DB enum missing): %s", e)
        artifact.error_message = (artifact.error_message or "") + f"; Deleted by staff {current_staff.username}" + (f": {reason}" if reason else "")
        artifact.add_log_entry("admin_delete", {"deleted_by": current_staff.username, "reason": reason, "note": "enum assignment failed"})
        # Do not attempt DDL here; leave status as-is and continue

    await db.commit()

    # Log audit entry
    await audit_service.log_action(
        action="admin_delete",
        action_category="admin",
        actor_type="staff",
        actor_id=str(current_staff.id),
        actor_username=current_staff.username,
        artifact_id=artifact.id,
        description=f"Artifact deleted by staff: {current_staff.username}",
        request_data={"reason": reason}
    )
    await db.commit()

    return {"message": "Artifact removed"}


@router.post("/artifacts/{artifact_uuid}/reports/{report_id}/resolve")
async def resolve_report(
    artifact_uuid: str,
    report_id: int,
    payload: dict = None,
    db: AsyncSession = Depends(get_db),
    current_staff: StaffUser = Depends(get_current_staff)
):
    """
    Mark a student report as resolved. Creates an audit entry `report_resolved`
    that targets the original report audit log entry.
    Body: { "note": Optional[str] }
    """
    artifact_service = ArtifactService(db)
    audit_service = AuditService(db)

    artifact = await artifact_service.get_by_uuid(artifact_uuid)
    if not artifact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found")

    # Ensure the referenced audit log exists and belongs to this artifact
    result = await db.execute(
        select(AuditLog).where(AuditLog.id == report_id, AuditLog.artifact_id == artifact.id)
    )
    report_log = result.scalar_one_or_none()
    if not report_log or report_log.action != 'report_issue':
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report entry not found")

    # Prevent resolving a report that the student has withdrawn
    deleted_q = await db.execute(
        select(AuditLog).where(AuditLog.action == 'report_deleted', AuditLog.target_id == str(report_id))
    )
    deleted_entry = deleted_q.scalars().first()
    if deleted_entry:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot resolve a withdrawn report")

    note = None
    if isinstance(payload, dict):
        note = payload.get('note')

    # Create resolution audit log referencing the original report id
    await audit_service.log_action(
        action="report_resolved",
        action_category="report",
        actor_type="staff",
        actor_id=str(current_staff.id),
        actor_username=current_staff.username,
        artifact_id=artifact.id,
        description=note or f"Resolved report {report_id}",
        request_data={"resolved_report_id": report_id},
        response_data={"note": note} if note else None,
        target_type='audit_log',
        target_id=str(report_id)
    )

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    return {"message": "Report marked resolved"}


@router.post("/artifacts/{artifact_uuid}/clear-transaction")
async def clear_artifact_transaction_id(
    artifact_uuid: str,
    db: AsyncSession = Depends(get_db),
    current_staff: StaffUser = Depends(get_current_staff)
):
    """
    Clear the transaction_id for a given artifact.

    Use this when a stale or incorrect transaction_id is preventing new uploads.
    This action is audited and requires staff authentication.
    """
    artifact_service = ArtifactService(db)
    audit_service = AuditService(db)

    artifact = await artifact_service.get_by_uuid(artifact_uuid)
    if not artifact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found")

    old_tid = artifact.transaction_id
    if not old_tid:
        return {"message": "No transaction_id set on this artifact"}

    artifact.transaction_id = None
    artifact.add_log_entry("cleared_transaction_id", {"cleared_by": current_staff.username})

    await audit_service.log_action(
        action="clear_transaction_id",
        action_category="admin",
        actor_type="staff",
        actor_id=str(current_staff.id),
        actor_username=current_staff.username,
        artifact_id=artifact.id,
        description=f"Cleared transaction_id on artifact {artifact.id}",
        request_data={"old_transaction_id": old_tid}
    )

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not clear transaction_id")

    return {"message": "transaction_id cleared", "old_transaction_id": old_tid}


# ============================================
# Student Username → Register Number Mappings
# ============================================

@router.get("/username-mappings")
async def list_username_mappings(
    db: AsyncSession = Depends(get_db),
    current_staff: StaffUser = Depends(get_current_staff)
):
    """List all Moodle username → register number mappings."""
    result = await db.execute(
        select(StudentUsernameRegister).order_by(StudentUsernameRegister.created_at.desc())
    )
    mappings = result.scalars().all()
    return [
        {
            "id": m.id,
            "moodle_username": m.moodle_username,
            "register_number": m.register_number,
            "created_at": m.created_at.isoformat() if m.created_at else None,
            "updated_at": m.updated_at.isoformat() if m.updated_at else None,
        }
        for m in mappings
    ]


@router.post("/username-mappings")
async def create_username_mapping(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_staff: StaffUser = Depends(get_current_staff)
):
    """
    Create or update a Moodle username → register number mapping.
    Body: { "moodle_username": "22007928", "register_number": "212222240047" }
    """
    username = (payload.get("moodle_username") or "").strip()
    register = (payload.get("register_number") or "").strip()

    if not username or not register:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both moodle_username and register_number are required"
        )

    # Upsert: update if username exists, else create
    result = await db.execute(
        select(StudentUsernameRegister).where(
            StudentUsernameRegister.moodle_username == username
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.register_number = register
        await db.commit()
        return {
            "message": f"Updated mapping: {username} → {register}",
            "id": existing.id,
            "moodle_username": existing.moodle_username,
            "register_number": existing.register_number,
        }
    else:
        new_mapping = StudentUsernameRegister(
            moodle_username=username,
            register_number=register
        )
        db.add(new_mapping)
        await db.commit()
        await db.refresh(new_mapping)
        return {
            "message": f"Created mapping: {username} → {register}",
            "id": new_mapping.id,
            "moodle_username": new_mapping.moodle_username,
            "register_number": new_mapping.register_number,
        }


@router.delete("/username-mappings/{mapping_id}")
async def delete_username_mapping(
    mapping_id: int,
    db: AsyncSession = Depends(get_db),
    current_staff: StaffUser = Depends(get_current_staff)
):
    """Delete a username → register number mapping."""
    result = await db.execute(
        select(StudentUsernameRegister).where(StudentUsernameRegister.id == mapping_id)
    )
    mapping = result.scalar_one_or_none()

    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mapping not found"
        )

    await db.delete(mapping)
    await db.commit()
    return {"message": f"Deleted mapping for {mapping.moodle_username}"}

