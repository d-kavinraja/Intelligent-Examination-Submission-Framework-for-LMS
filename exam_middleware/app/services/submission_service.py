"""
Submission Service
Orchestrates the complete submission workflow to Moodle
"""

import logging
import os
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ExaminationArtifact, WorkflowStatus, ExamSubmission
from app.services.moodle_client import MoodleClient, MoodleAPIError
from app.services.artifact_service import ArtifactService, SubjectMappingService, AuditService
from app.core.security import token_encryption
from app.core.config import settings

logger = logging.getLogger(__name__)


class SubmissionService:
    """
    Orchestrates the 3-step submission process to Moodle
    
    Implements the workflow from Section 4.3 of the design document:
    1. Upload to Draft Area (core_files_upload)
    2. Associate Draft with Assignment (mod_assign_save_submission)
    3. Lock the Submission (mod_assign_submit_for_grading)
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.artifact_service = ArtifactService(db)
        self.mapping_service = SubjectMappingService(db)
        self.audit_service = AuditService(db)

    @staticmethod
    def _is_local_moodle_url(url: Optional[str]) -> bool:
        """Return True only for localhost/127.0.0.1 Moodle targets."""
        if not url:
            return False
        normalized = url.rstrip("/").lower()
        return normalized in {
            "http://localhost",
            "https://localhost",
            "http://127.0.0.1",
            "https://127.0.0.1",
        }

    async def _apply_local_admin_post_submit_restrictions(
        self,
        assignment_id: int,
        moodle_user_id: int,
        target_site_url: Optional[str],
    ) -> Dict[str, Any]:
        """
        After successful student submission, try to prevent further edits
        using manager/admin APIs.
        
        This is best-effort and should not fail the student submission.
        """
        effective_url = (target_site_url or settings.moodle_base_url or "").rstrip("/")
        result: Dict[str, Any] = {
            "attempted": False,
            "success": False,
            "target_site_url": effective_url,
            "actions": [],
            "errors": [],
        }

        admin_token = (
            (getattr(settings, "local_moodle_admin_token", None) or "").strip()
            or (settings.moodle_admin_token or "").strip()
        )
        
        if not admin_token:
            result["reason"] = "admin_token_missing"
            return result

        result["attempted"] = True
        client = MoodleClient(base_url=effective_url, token=admin_token)
        try:
            try:
                flags_res = await client.set_user_flags_locked(
                    assignment_id=assignment_id,
                    user_id=moodle_user_id,
                    locked=True,
                    token=admin_token,
                )
                result["actions"].append({"name": "mod_assign_set_user_flags", "result": flags_res})
            except Exception as e:
                result["errors"].append(f"set_user_flags_failed: {e}")

            try:
                lock_res = await client.lock_submission_for_users(
                    assignment_id=assignment_id,
                    user_ids=[moodle_user_id],
                    token=admin_token,
                )
                result["actions"].append({"name": "mod_assign_lock_submissions", "result": lock_res})
            except Exception as e:
                result["errors"].append(f"lock_submissions_failed: {e}")

            result["success"] = len(result["actions"]) > 0
            if not result["success"]:
                result["reason"] = "all_admin_lock_actions_failed"
            return result
        finally:
            await client.close()
    
    async def submit_artifact(
        self,
        artifact_uuid: str,
        moodle_token: str,
        moodle_user_id: int,
        moodle_username: str,
        register_number: str,
        actor_ip: Optional[str] = None,
        lock_submission: bool = True
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Submit an artifact to Moodle
        
        This is the main entry point for the submission workflow.
        
        Args:
            artifact_uuid: UUID of the artifact to submit
            moodle_token: Student's Moodle web service token
            moodle_user_id: Student's Moodle user ID
            moodle_username: Student's Moodle username
            register_number: Student's register number (extracted from fullname)
            actor_ip: IP address of the student
            lock_submission: Whether to finalize/lock the submission
            
        Returns:
            Tuple of (success, message, result_data)
        """
        # Get artifact
        artifact = await self.artifact_service.get_by_uuid(artifact_uuid)
        if not artifact:
            return False, "Artifact not found", None
        
        # Security check: Verify the artifact belongs to this user (compare register numbers)
        if artifact.parsed_reg_no != register_number:
            logger.warning(
                f"Security violation: User {moodle_username} attempted to submit "
                f"artifact belonging to {artifact.parsed_reg_no}"
            )
            await self.audit_service.log_action(
                action="unauthorized_submission_attempt",
                action_category="security",
                actor_type="student",
                actor_id=str(moodle_user_id),
                actor_username=moodle_username,
                actor_ip=actor_ip,
                artifact_id=artifact.id,
                description=f"User attempted to submit artifact belonging to {artifact.parsed_reg_no}"
            )
            return False, "You can only submit your own papers", None

        # Attempt window validation
        attempt_ok, attempt_message, attempt_details = await self.validate_attempt_submission_window(artifact)
        if not attempt_ok:
            await self.audit_service.log_action(
                action="attempt_submission_blocked",
                action_category="submit",
                actor_type="student",
                actor_id=str(moodle_user_id),
                actor_username=moodle_username,
                actor_ip=actor_ip,
                artifact_id=artifact.id,
                description=attempt_message,
                request_data=attempt_details,
            )
            return False, attempt_message, attempt_details
        
        # Check if already submitted
        if artifact.workflow_status in [WorkflowStatus.COMPLETED, WorkflowStatus.SUBMITTED_TO_LMS]:
            return False, "This paper has already been submitted", {
                "already_submitted": True,
                "submitted_at": artifact.submit_timestamp.isoformat() if artifact.submit_timestamp else None
            }

        # Check exam_submissions table: prevent any re-submission for this student+subject+exam+attempt
        from sqlalchemy import select, and_
        existing_sub = await self.db.execute(
            select(ExamSubmission).where(
                and_(
                    ExamSubmission.student_id == register_number,
                    ExamSubmission.subject_code == artifact.parsed_subject_code,
                    ExamSubmission.exam_type == (getattr(artifact, 'exam_type', 'CIA1') or 'CIA1'),
                    ExamSubmission.attempt_number == getattr(artifact, 'attempt_number', 1),
                    ExamSubmission.status == "COMPLETED",
                )
            )
        )
        completed_record = existing_sub.scalar_one_or_none()
        if completed_record:
            logger.warning(
                f"Blocked re-submission: student={register_number}, "
                f"subject={artifact.parsed_subject_code}, exam={artifact.exam_type} "
                f"— already COMPLETED at {completed_record.submitted_at}"
            )
            return False, "This exam has already been submitted and locked. Re-submission is not allowed.", {
                "already_submitted": True,
                "locked": True,
                "submitted_at": completed_record.submitted_at.isoformat() if completed_record.submitted_at else None,
            }
        
        # Get assignment ID
        assignment_id, target_site_url, error_msg = await self._resolve_assignment_id(artifact)
        if not assignment_id:
            return False, error_msg or f"No assignment mapping found for subject code: {artifact.parsed_subject_code}", None

        effective_target_site_url = target_site_url or settings.moodle_base_url

        unlock_result: Dict[str, Any] = {}
        if (getattr(artifact, "attempt_number", 1) or 1) == 2:
            unlock_result = await self.unlock_previous_attempt_for_replacement(
                artifact=artifact,
                assignment_id=assignment_id,
                moodle_user_id=moodle_user_id,
                target_site_url=effective_target_site_url,
            )
            if not unlock_result.get("success"):
                message = (
                    "Attempt 2 cannot be submitted because Moodle could not unlock "
                    "or revert the Attempt 1 submission. Ask staff to verify the "
                    "Moodle admin token and assignment permissions, then try again."
                )
                await self.audit_service.log_action(
                    action="attempt_2_moodle_unlock_failed",
                    action_category="error",
                    actor_type="student",
                    actor_id=str(moodle_user_id),
                    actor_username=moodle_username,
                    actor_ip=actor_ip,
                    artifact_id=artifact.id,
                    description=message,
                    response_data=unlock_result,
                )
                return False, message, unlock_result

        # Update artifact with Moodle info
        artifact.moodle_user_id = moodle_user_id
        artifact.moodle_username = moodle_username
        artifact.moodle_assignment_id = assignment_id

        # Log submission start
        await self.audit_service.log_action(
            action="submission_started",
            action_category="submit",
            actor_type="student",
            actor_id=str(moodle_user_id),
            actor_username=moodle_username,
            actor_ip=actor_ip,
            artifact_id=artifact.id,
            description=f"Starting submission for assignment {assignment_id} on {target_site_url}"
        )

        # Execute the 3-step submission process
        try:
            result = await self._execute_submission(
                artifact=artifact,
                assignment_id=assignment_id,
                moodle_token=moodle_token,
                target_site_url=effective_target_site_url,
            )
            
            # Log the complete result for debugging
            logger.info(f"Submission result: {result}")
            logger.info(f"Steps completed: {result.get('steps_completed', [])}")
            if unlock_result:
                result["attempt_2_unlock"] = unlock_result
            
            # Mark as completed (only after all verification and submit steps)
            await self.artifact_service.mark_submitted(
                artifact_id=artifact.id,
                moodle_submission_id=result.get("submission_id"),
                lms_transaction_id=result.get("transaction_id")
            )

            # Local Moodle only: apply admin lock to prevent further edits after submit.
            # Best-effort: failure here should not mark submission as failed.
            admin_lock_result = await self._apply_local_admin_post_submit_restrictions(
                assignment_id=assignment_id,
                moodle_user_id=moodle_user_id,
                target_site_url=effective_target_site_url,
            )
            result["admin_lock"] = admin_lock_result
            if admin_lock_result.get("attempted") and not admin_lock_result.get("success"):
                logger.warning(
                    f"Post-submit admin lock failed for assignment {assignment_id}, "
                    f"user {moodle_user_id}: {admin_lock_result}"
                )

            # Record in exam_submissions table as COMPLETED to block future re-submissions
            from sqlalchemy import select, and_
            es_result = await self.db.execute(
                select(ExamSubmission).where(
                    and_(
                        ExamSubmission.student_id == register_number,
                        ExamSubmission.subject_code == artifact.parsed_subject_code,
                        ExamSubmission.exam_type == (getattr(artifact, 'exam_type', 'CIA1') or 'CIA1'),
                        ExamSubmission.attempt_number == getattr(artifact, 'attempt_number', 1),
                    )
                )
            )
            exam_sub = es_result.scalar_one_or_none()
            now = datetime.utcnow()
            if exam_sub:
                exam_sub.status = "COMPLETED"
                exam_sub.submitted_at = now
                exam_sub.locked_at = now
                exam_sub.assignment_id = assignment_id
                exam_sub.artifact_id = artifact.id
                exam_sub.moodle_user_id = moodle_user_id
                exam_sub.moodle_username = moodle_username
                exam_sub.target_site_url = effective_target_site_url
                exam_sub.transaction_id = result.get("transaction_id")
            else:
                exam_sub = ExamSubmission(
                    student_id=register_number,
                    moodle_user_id=moodle_user_id,
                    moodle_username=moodle_username,
                    subject_code=artifact.parsed_subject_code,
                    assignment_id=assignment_id,
                    exam_type=getattr(artifact, 'exam_type', 'CIA1') or 'CIA1',
                    attempt_number=getattr(artifact, 'attempt_number', 1) or 1,
                    artifact_id=artifact.id,
                    status="COMPLETED",
                    submitted_at=now,
                    locked_at=now,
                    target_site_url=effective_target_site_url,
                    transaction_id=result.get("transaction_id"),
                )
                self.db.add(exam_sub)
            await self.db.flush()
            logger.info(
                f"Recorded exam_submission COMPLETED: student={register_number}, "
                f"subject={artifact.parsed_subject_code}, exam={artifact.exam_type}"
            )

            # If this is attempt 1, lock the assessment; if attempt 2, replace attempt 1
            if (getattr(artifact, "attempt_number", 1) or 1) == 1:
                await self.lock_assessment_after_attempt_1_submission(
                    artifact=artifact,
                    moodle_user_id=moodle_user_id,
                    moodle_username=moodle_username,
                    actor_ip=actor_ip,
                )
            elif (getattr(artifact, "attempt_number", 1) or 1) == 2:
                await self.replace_attempt_1_with_attempt_2(
                    attempt2=artifact,
                    moodle_user_id=moodle_user_id,
                    moodle_username=moodle_username,
                    actor_ip=actor_ip,
                    unlock_result=unlock_result,
                )
            
            # Log success
            await self.audit_service.log_action(
                action="submission_completed",
                action_category="submit",
                actor_type="student",
                actor_id=str(moodle_user_id),
                actor_username=moodle_username,
                actor_ip=actor_ip,
                artifact_id=artifact.id,
                response_data=result,
                description="Submission completed successfully"
            )
            
            return True, "Submission completed successfully", result
            
        except MoodleAPIError as e:
            logger.error(f"Moodle API error during submission: {e}")
            
            # Check if this is a transient error that should be queued
            should_queue = self._should_queue_for_retry(e)
            
            await self.artifact_service.mark_failed(
                artifact_id=artifact.id,
                error_message=str(e),
                queue_for_retry=should_queue
            )
            
            await self.audit_service.log_action(
                action="submission_failed",
                action_category="error",
                actor_type="student",
                actor_id=str(moodle_user_id),
                actor_username=moodle_username,
                actor_ip=actor_ip,
                artifact_id=artifact.id,
                description=str(e),
                response_data={
                    "error": str(e),
                    "queued_for_retry": should_queue
                }
            )
            
            if should_queue:
                return False, "Submission queued - Moodle is temporarily unavailable", {
                    "queued": True,
                    "error": str(e)
                }
            
            return False, f"Submission failed: {e.message}", {"error": str(e)}
            
        except Exception as e:
            logger.error(f"Unexpected error during submission: {e}")
            
            await self.artifact_service.mark_failed(
                artifact_id=artifact.id,
                error_message=str(e),
                queue_for_retry=False
            )
            
            return False, f"Unexpected error: {str(e)}", None

    async def validate_attempt_submission_window(
        self,
        artifact: ExaminationArtifact,
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Enforce staff/student synchronization before Moodle submission.

        Attempt 2 can only be submitted after staff unlocks it and uploads the
        attempt 2 paper. If staff opened attempt 2 but has not uploaded a paper,
        submitting the old attempt 1 artifact is rejected with a clear message.
        """
        attempt_number = getattr(artifact, "attempt_number", 1) or 1

        if attempt_number == 2:
            if getattr(artifact, "attempt_2_locked", True):
                return False, "Attempt 2 is locked. Staff must unlock Attempt 2 before you can submit.", {
                    "attempt_2_locked": True,
                }
            if not self._artifact_has_uploaded_paper(artifact):
                return False, "Attempt 2 is open, but no Attempt 2 paper has been uploaded.", {
                    "attempt_2_missing_paper": True,
                }
            return True, "", None

        if getattr(artifact, "attempt_2_locked", True) is False:
            attempt2 = await self._find_attempt_artifact(artifact, attempt_number=2)
            if not attempt2:
                return False, "Attempt 2 is open, but no Attempt 2 paper has been uploaded.", {
                    "attempt_2_missing_paper": True,
                }

        return True, "", None

    async def unlock_previous_attempt_for_replacement(
        self,
        artifact: ExaminationArtifact,
        assignment_id: int,
        moodle_user_id: int,
        target_site_url: Optional[str],
    ) -> Dict[str, Any]:
        """
        Unlock the existing Moodle submission before attempt 2 replaces it.

        This uses teacher/admin APIs to clear Moodle's lock flag,
        revert the previous submitted attempt to draft, and remove it. Without this
        step Moodle can keep showing the Attempt 1 submission timestamp/files.
        """
        result: Dict[str, Any] = {
            "attempted": False,
            "success": False,
            "assignment_id": assignment_id,
            "moodle_user_id": moodle_user_id,
        }

        if (getattr(artifact, "attempt_number", 1) or 1) != 2:
            result["reason"] = "not_attempt_2"
            return result

        admin_token = self._get_admin_token()
        if not admin_token:
            result["reason"] = "admin_token_missing"
            return result

        effective_url = (target_site_url or settings.moodle_base_url or "").rstrip("/")
        client = MoodleClient(base_url=effective_url, token=admin_token)
        result["attempted"] = True
        result["target_site_url"] = effective_url
        result["actions"] = []
        result["errors"] = []

        try:
            try:
                unlock_res = await client.set_user_flags_locked(
                    assignment_id=assignment_id,
                    user_id=moodle_user_id,
                    locked=False,
                    token=admin_token,
                )
                result["actions"].append({
                    "name": "mod_assign_set_user_flags",
                    "result": unlock_res,
                })
            except Exception as e:
                result["errors"].append(f"set_user_flags_unlock_failed: {e}")

            try:
                unlock_sub_res = await client.unlock_submissions(
                    assignment_id=assignment_id,
                    user_ids=[moodle_user_id],
                    token=admin_token,
                )
                result["actions"].append({
                    "name": "mod_assign_unlock_submissions",
                    "result": unlock_sub_res,
                })
            except Exception as e:
                result["errors"].append(f"unlock_submissions_failed: {e}")

            try:
                draft_res = await client.revert_submissions_to_draft(
                    assignment_id=assignment_id,
                    user_ids=[moodle_user_id],
                    token=admin_token,
                )
                result["actions"].append({
                    "name": "mod_assign_revert_submissions_to_draft",
                    "result": draft_res,
                })
            except Exception as e:
                result["errors"].append(f"revert_submissions_to_draft_failed: {e}")

            try:
                remove_res = await client.remove_submission(
                    assignment_id=assignment_id,
                    user_id=moodle_user_id,
                    token=admin_token,
                )
                result["actions"].append({
                    "name": "mod_assign_remove_submission",
                    "result": remove_res,
                })
            except Exception as e:
                result["errors"].append(f"remove_submission_failed: {e}")

            result["success"] = len(result["actions"]) > 0
            if not result["success"]:
                result["reason"] = "all_admin_unlock_actions_failed"
            return result
        except Exception as e:
            result["error"] = str(e)
            logger.warning(
                "Could not unlock previous Moodle submission before attempt 2 replacement: %s",
                e,
            )
            return result
        finally:
            await client.close()

    async def lock_assessment_after_attempt_1_submission(
        self,
        artifact: ExaminationArtifact,
        moodle_user_id: int,
        moodle_username: str,
        actor_ip: Optional[str],
    ) -> None:
        """Lock the group after attempt 1 is submitted so attempt 2 needs staff action."""
        if (getattr(artifact, "attempt_number", 1) or 1) != 1:
            return

        await self._set_group_attempt_lock(artifact, locked=True)
        artifact.add_log_entry("assessment_locked_after_attempt_1", {
            "reason": "attempt_1_submitted",
        })
        await self.audit_service.log_action(
            action="assessment_locked_after_attempt_1",
            action_category="submit",
            actor_type="student",
            actor_id=str(moodle_user_id),
            actor_username=moodle_username,
            actor_ip=actor_ip,
            artifact_id=artifact.id,
            description="Assessment locked automatically after Attempt 1 submission",
            request_data={
                "reg_no": artifact.parsed_reg_no,
                "subject_code": artifact.parsed_subject_code,
                "exam_type": artifact.exam_type,
                "attempt_number": 1,
            },
        )

    async def replace_attempt_1_with_attempt_2(
        self,
        attempt2: ExaminationArtifact,
        moodle_user_id: int,
        moodle_username: str,
        actor_ip: Optional[str],
        unlock_result: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Make attempt 2 the active submission and retire attempt 1.

        Database replacement flow:
        1. Delete the attempt 1 row from exam_submissions.
        2. Mark the attempt 1 artifact SUPERSEDED for history.
        3. Re-lock the group after attempt 2 is submitted.
        4. Write an audit log linking old and new artifacts.
        """
        if (getattr(attempt2, "attempt_number", 1) or 1) != 2:
            return

        attempt1 = await self._find_attempt_artifact(attempt2, attempt_number=1)
        await self._delete_exam_submission_record(attempt2, attempt_number=1)

        if attempt1:
            attempt1.workflow_status = WorkflowStatus.SUPERSEDED
            attempt1.add_log_entry("attempt_1_removed_for_attempt_2", {
                "attempt_2_artifact_id": attempt2.id,
                "reason": "attempt_2_submitted",
            })

        attempt2.add_log_entry("attempt_2_replaced_attempt_1", {
            "attempt_1_artifact_id": attempt1.id if attempt1 else None,
            "unlock_result": unlock_result or {},
        })

        await self._set_group_attempt_lock(attempt2, locked=True)
        await self.audit_service.log_action(
            action="attempt_1_replaced_by_attempt_2",
            action_category="submit",
            actor_type="student",
            actor_id=str(moodle_user_id),
            actor_username=moodle_username,
            actor_ip=actor_ip,
            artifact_id=attempt2.id,
            target_type="examination_artifact",
            target_id=str(attempt1.id) if attempt1 else None,
            description="Attempt 1 submission removed and replaced by Attempt 2",
            request_data={
                "reg_no": attempt2.parsed_reg_no,
                "subject_code": attempt2.parsed_subject_code,
                "exam_type": attempt2.exam_type,
                "removed_attempt": 1,
                "active_attempt": 2,
                "attempt_1_artifact_id": attempt1.id if attempt1 else None,
                "attempt_2_artifact_id": attempt2.id,
            },
            response_data={
                "unlock_previous_submission": unlock_result or {},
            },
        )

    def _artifact_has_uploaded_paper(self, artifact: ExaminationArtifact) -> bool:
        """Return True if the artifact has a paper file path or content."""
        return bool(artifact.file_blob_path or artifact.file_content)

    async def _find_attempt_artifact(
        self,
        artifact: ExaminationArtifact,
        attempt_number: int,
    ) -> Optional[ExaminationArtifact]:
        """Find an artifact for the same student/subject/exam with a specific attempt number."""
        from sqlalchemy import select, and_
        query = await self.db.execute(
            select(ExaminationArtifact).where(
                and_(
                    ExaminationArtifact.parsed_reg_no == artifact.parsed_reg_no,
                    ExaminationArtifact.parsed_subject_code == artifact.parsed_subject_code,
                    ExaminationArtifact.exam_type == artifact.exam_type,
                    ExaminationArtifact.attempt_number == attempt_number,
                    ExaminationArtifact.workflow_status != WorkflowStatus.DELETED,
                )
            )
        )
        return query.scalars().first()

    async def _delete_exam_submission_record(
        self,
        artifact: ExaminationArtifact,
        attempt_number: int,
    ) -> None:
        """Remove the active submission row for a specific attempt."""
        from sqlalchemy import delete, and_
        await self.db.execute(
            delete(ExamSubmission).where(
                and_(
                    ExamSubmission.student_id == artifact.parsed_reg_no,
                    ExamSubmission.subject_code == artifact.parsed_subject_code,
                    ExamSubmission.exam_type == artifact.exam_type,
                    ExamSubmission.attempt_number == attempt_number,
                )
            )
        )
        await self.db.flush()

    async def _set_group_attempt_lock(
        self,
        artifact: ExaminationArtifact,
        locked: bool,
    ) -> None:
        """Lock or unlock Attempt 2 for the entire group of artifacts."""
        from sqlalchemy import update, and_
        await self.db.execute(
            update(ExaminationArtifact)
            .where(
                and_(
                    ExaminationArtifact.parsed_reg_no == artifact.parsed_reg_no,
                    ExaminationArtifact.parsed_subject_code == artifact.parsed_subject_code,
                    ExaminationArtifact.exam_type == artifact.exam_type,
                )
            )
            .values(attempt_2_locked=locked)
        )
        await self.db.flush()

    def _get_admin_token(self) -> Optional[str]:
        """Get the configured local Moodle admin token."""
        return (
            (getattr(settings, "local_moodle_admin_token", None) or "").strip()
            or (settings.moodle_admin_token or "").strip()
        )

    
    async def _resolve_assignment_id(self, artifact: ExaminationArtifact) -> Tuple[Optional[int], Optional[str], Optional[str]]:
        """Resolve the Moodle assignment ID for an artifact. Returns (assignment_id, target_site_url, error_message)"""
        # Always try to get the latest mapping first to handle re-mappings/retries correctly
        if artifact.parsed_subject_code:
            exam_type = getattr(artifact, 'exam_type', 'CIA1') or 'CIA1'
            mapping = await self.mapping_service.get_mapping(artifact.parsed_subject_code, exam_type)
            if mapping:
                if mapping.moodle_assignment_id:
                    # Update the artifact's field to keep it in sync with the latest mapping
                    artifact.moodle_assignment_id = mapping.moodle_assignment_id
                    return mapping.moodle_assignment_id, mapping.target_site_url, None
                elif mapping.cmid:
                    return None, mapping.target_site_url, f"Mapping for {artifact.parsed_subject_code} is pending auto-resolution. Please try again in a few moments."

        # Fallback to what was previously stored (or None)
        if artifact.moodle_assignment_id:
            return artifact.moodle_assignment_id, None, None

        return None, None, f"No assignment mapping found for subject code: {artifact.parsed_subject_code}"
    
    async def _execute_submission(
        self,
        artifact: ExaminationArtifact,
        assignment_id: int,
        moodle_token: str,
        target_site_url: Optional[str] = None,
        lock_submission: bool = True
    ) -> Dict[str, Any]:
        """
        Execute the 3-step submission process

        Step 1: Upload file to draft area
        Step 2: Link draft to assignment
        Step 3: Finalize submission (optional)
        """
        client = MoodleClient(base_url=target_site_url, token=moodle_token)
        result = {
            "assignment_id": assignment_id,
            "steps_completed": []
        }
        
        try:
            # Check if we have a previous draft that failed
            if artifact.moodle_draft_item_id and artifact.workflow_status == WorkflowStatus.UPLOADING:
                logger.info(f"Reusing existing draft item: {artifact.moodle_draft_item_id}")
                item_id = artifact.moodle_draft_item_id
                result["steps_completed"].append("upload_skipped_reuse")
            else:
                # Step 1: Upload to draft area
                logger.info(f"Step 1/3: Uploading file to draft area")
                artifact.workflow_status = WorkflowStatus.UPLOADING
                await self.db.flush()
                
                # Check if file exists on disk (safely handling None paths)
                file_content = None
                file_on_disk = False
                
                if artifact.file_blob_path and os.path.exists(artifact.file_blob_path):
                    file_on_disk = True
                
                if not file_on_disk:
                    logger.warning(f"File {artifact.file_blob_path} missing on disk (or path is None) for artifact {artifact.artifact_uuid}")
                    if artifact.file_content:
                        logger.info(f"Using database content for artifact {artifact.artifact_uuid}")
                        file_content = artifact.file_content
                    else:
                        logger.error(f"File missing on disk and no database content for artifact {artifact.artifact_uuid}")
                        raise MoodleAPIError(f"File not found on disk or database for submission.")
                
                upload_result = await client.upload_file(
                    file_path=artifact.file_blob_path if file_on_disk else None,
                    file_content=file_content,
                    token=moodle_token,
                    filename=artifact.original_filename
                )
                
                item_id = upload_result["itemid"]
                artifact.moodle_draft_item_id = item_id
                await self.db.flush()
                
                result["item_id"] = item_id
                result["steps_completed"].append("upload")
            
            # Step 2: Verify assignment exists and is accessible BEFORE saving
            logger.info(f"Verifying assignment {assignment_id} exists and is accessible...")
            try:
                # Try to get submission status - this will fail if assignment doesn't exist
                verify_status = await client.get_submission_status(
                    assignment_id=assignment_id,
                    token=moodle_token
                )
                logger.info(f"Assignment {assignment_id} verified and accessible")
            except MoodleAPIError as verify_error:
                logger.error(
                    f"Assignment {assignment_id} verification failed: {verify_error.message}. "
                    f"This usually means the assignment ID is incorrect or the student doesn't have access."
                )
                raise MoodleAPIError(
                    f"Assignment {assignment_id} not found or not accessible: {verify_error.message}. "
                    f"Please verify the assignment ID in your subject mapping matches the Moodle assignment instance ID (not the course module ID).",
                    response_data={"assignment_id": assignment_id, "error": str(verify_error)}
                )
            
            # Step 2: Save submission
            logger.info(f"Step 2/3: Linking draft to assignment")
            artifact.workflow_status = WorkflowStatus.SUBMITTING
            await self.db.flush()
            
            save_result = await client.save_submission(
                assignment_id=assignment_id,
                item_id=item_id,
                token=moodle_token
            )
            
            result["save_result"] = save_result
            result["steps_completed"].append("save")
            
            # Verify the submission was actually saved by checking status
            logger.info(f"Verifying submission status after save...")
            status_result = await client.get_submission_status(
                assignment_id=assignment_id,
                token=moodle_token
            )
            
            # Log the full status for debugging
            logger.info(f"Full submission status response: {status_result}")
            
            # Check submission status details
            submission_status = "unknown"
            submission_files = []
            submission_id = None
            cansubmit = False
            if "lastattempt" in status_result:
                lastattempt = status_result["lastattempt"]
                submission = lastattempt.get("submission", {})
                submission_status = submission.get("status", "unknown")
                submission_id = submission.get("id")
                logger.info(f"Submission status: {submission_status}")
                logger.info(f"Submission ID: {submission_id}")
                logger.info(f"Submission timecreated: {submission.get('timecreated')}")
                logger.info(f"Submission timemodified: {submission.get('timemodified')}")
                
                # Check gradingstatus
                grading_status = lastattempt.get("gradingstatus", "unknown")
                logger.info(f"Grading status: {grading_status}")
                
                # Check submissionsenabled
                submissionsenabled = lastattempt.get("submissionsenabled", False)
                logger.info(f"Submissions enabled: {submissionsenabled}")
                
                # Check canedit
                canedit = lastattempt.get("canedit", False)
                logger.info(f"Can edit: {canedit}")
                
                # Check cansubmit (whether Moodle expects an explicit submit-for-grading action)
                cansubmit = lastattempt.get("cansubmit", False)
                logger.info(f"Can submit: {cansubmit}")
                
                plugins = submission.get("plugins", [])
                for plugin in plugins:
                    if plugin.get("type") == "file":
                        fileareas = plugin.get("fileareas", [])
                        for area in fileareas:
                            if area.get("area") == "submission_files":
                                submission_files = area.get("files", [])
                                break
            
            result["submission_status"] = submission_status
            if submission_id is not None:
                # Expose Moodle's internal submission id so we can persist it
                # Convert to string since database column is VARCHAR
                result["submission_id"] = str(submission_id)
            
            logger.info(f"Submission verification - Files found: {len(submission_files)}")
            if submission_files:
                logger.info(f"Verified files: {[f.get('filename') for f in submission_files]}")
                result["verified_files"] = [f.get("filename") for f in submission_files]
            else:
                # Moodle can sometimes be slow to report files after save.
                # Retry the status check once after a short delay before failing.
                import asyncio
                logger.warning(
                    "No files found in submission immediately after save. "
                    "Retrying status check after 2 seconds..."
                )
                await asyncio.sleep(2)
                retry_status = await client.get_submission_status(
                    assignment_id=assignment_id,
                    token=moodle_token
                )
                # Re-parse the retry response
                retry_files = []
                if "lastattempt" in retry_status:
                    retry_sub = retry_status["lastattempt"].get("submission", {})
                    for plugin in retry_sub.get("plugins", []):
                        if plugin.get("type") == "file":
                            for area in plugin.get("fileareas", []):
                                if area.get("area") == "submission_files":
                                    retry_files = area.get("files", [])
                                    break

                if retry_files:
                    logger.info(f"Retry succeeded - files found: {[f.get('filename') for f in retry_files]}")
                    result["verified_files"] = [f.get("filename") for f in retry_files]
                    submission_files = retry_files
                else:
                    # Treat this as a hard failure
                    logger.error(
                        f"No files found in submission after save AND retry for "
                        f"assignment_id={assignment_id}. "
                        f"This may indicate the Moodle assignment does not accept file submissions, "
                        f"or the assignment configuration needs to be checked."
                    )
                    raise MoodleAPIError(
                        f"Moodle did not attach any files to the submission (assignment_id={assignment_id}). "
                        f"Please verify the assignment accepts file submissions in Moodle, then retry.",
                        response_data=retry_status
                    )
            
            # Step 3: Submit for grading (lock), but ONLY if Moodle reports that
            # this user can actually perform an explicit submit action.
            #
            # For many assignment configurations (submission drafts off), Moodle
            # treats file upload as the final submission and returns
            #   - submission.status = 'submitted'
            #   - cansubmit = False
            # In those cases calling mod_assign_submit_for_grading will return
            # 'couldnotsubmitforgrading', which we now treat as an error. To
            # avoid false failures, we simply skip the explicit submit call.
            if lock_submission and cansubmit:
                logger.info(f"Step 3/3: Finalizing submission")
                submit_result = await client.submit_for_grading(
                    assignment_id=assignment_id,
                    token=moodle_token
                )
                
                result["submit_result"] = submit_result
                result["steps_completed"].append("finalize")
            elif lock_submission and not cansubmit:
                logger.info(
                    "Skipping explicit submit_for_grading call because Moodle "
                    "reports cansubmit=False. Treating current 'submitted' "
                    "state as final."
                )
                result["submit_skipped"] = True
            
            result["success"] = True
            result["transaction_id"] = f"TXN_{artifact.artifact_uuid}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            
            return result
            
        finally:
            await client.close()
    
    def _should_queue_for_retry(self, error: MoodleAPIError) -> bool:
        """Determine if an error should trigger a retry queue"""
        # Queue for transient errors (Moodle maintenance, timeouts, etc.)
        if error.error:
            transient_errors = [
                "moodleoff",
                "maintenance",
                "timeout",
                "connection",
                "unavailable"
            ]
            errorcode = getattr(error.error, "errorcode", None) or ""
            errormsg = getattr(error.error, "message", None) or ""
            return any(
                te in errorcode.lower() or te in errormsg.lower()
                for te in transient_errors
            )
        
        return "timeout" in str(error).lower() or "connection" in str(error).lower()
    
    async def get_submission_status(
        self,
        artifact_uuid: str,
        moodle_token: str
    ) -> Dict[str, Any]:
        """Get the current submission status from Moodle"""
        artifact = await self.artifact_service.get_by_uuid(artifact_uuid)
        if not artifact:
            return {"error": "Artifact not found"}
        
        if not artifact.moodle_assignment_id:
            return {
                "artifact_status": artifact.workflow_status.value,
                "moodle_status": None
            }
        
        client = MoodleClient(token=moodle_token)
        try:
            status = await client.get_submission_status(
                assignment_id=artifact.moodle_assignment_id,
                token=moodle_token
            )
            
            return {
                "artifact_status": artifact.workflow_status.value,
                "moodle_status": status
            }
        finally:
            await client.close()
    
    async def retry_queued_submissions(self, admin_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Retry all queued submissions (for background worker)
        
        This implements the buffer pattern from Section 6.4.
        
        NOTE: admin_token is optional. If not provided, submissions will not be retried
        automatically. You can still manually trigger retry through the API.
        """
        from app.db.models import SubmissionQueue
        from sqlalchemy import select
        
        result = {
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "details": [],
            "note": "Admin token not configured - automatic retry disabled" if not admin_token else None
        }
        
        if not admin_token:
            # Without admin token, queue processing is disabled for background tasks
            # Students can still submit individually with their own credentials
            logger.warning("Retry queue: Admin token not configured - skipping automatic queue processing")
            result["skipped"] = True
            return result
        
        # Get queued items
        query = await self.db.execute(
            select(SubmissionQueue)
            .where(SubmissionQueue.status == "QUEUED")
            .order_by(SubmissionQueue.priority, SubmissionQueue.queued_at)
            .limit(50)
        )
        
        queue_items = query.scalars().all()
        
        for item in queue_items:
            result["processed"] += 1
            
            artifact = await self.artifact_service.get_by_id(item.artifact_id)
            if not artifact:
                item.status = "FAILED"
                item.last_error = "Artifact not found"
                result["failed"] += 1
                continue
            
            # For queued items, we use the admin token
            # In production, you'd need to handle this differently
            try:
                client = MoodleClient(token=admin_token)
                
                submit_result = await self._execute_submission(
                    artifact=artifact,
                    assignment_id=artifact.moodle_assignment_id,
                    moodle_token=admin_token,
                    lock_submission=True
                )
                
                item.status = "COMPLETED"
                item.processed_at = datetime.utcnow()
                
                await self.artifact_service.mark_submitted(
                    artifact_id=artifact.id,
                    moodle_submission_id=submit_result.get("submission_id")
                )
                
                result["successful"] += 1
                result["details"].append({
                    "artifact_uuid": str(artifact.artifact_uuid),
                    "status": "success"
                })
                
            except Exception as e:
                item.retry_count += 1
                item.last_error = str(e)
                
                if item.retry_count >= item.max_retries:
                    item.status = "FAILED"
                    await self.artifact_service.mark_failed(
                        artifact_id=artifact.id,
                        error_message=f"Max retries exceeded: {e}",
                        queue_for_retry=False
                    )
                
                result["failed"] += 1
                result["details"].append({
                    "artifact_uuid": str(artifact.artifact_uuid),
                    "status": "failed",
                    "error": str(e)
                })
            
            finally:
                await client.close()
        
        await self.db.commit()
        return result
