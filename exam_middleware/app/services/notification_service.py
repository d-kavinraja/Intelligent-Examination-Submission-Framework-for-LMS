"""
Notification Service
Coordinates student notifications for artifact lifecycle events.
"""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import ExaminationArtifact, StudentUsernameRegister
from app.services.artifact_service import AuditService, SubjectMappingService
from app.services.mail_service import mail_service
from app.services.moodle_client import MoodleAPIError, MoodleClient

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for dispatching upload notifications to students."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.audit_service = AuditService(db)
        self.mapping_service = SubjectMappingService(db)

    async def notify_student_on_upload(
        self,
        artifact: ExaminationArtifact,
        uploaded_by_username: str,
        actor_ip: Optional[str] = None,
    ) -> None:
        """
        Notify student when a paper is uploaded by staff.

        Best-effort behavior: failures are logged and audited, but **never** raised
        so the upload response is never blocked by notification issues.
        """
        try:
            await self._do_notify_student_on_upload(
                artifact=artifact,
                uploaded_by_username=uploaded_by_username,
                actor_ip=actor_ip,
            )
        except Exception as exc:
            # Catch-all: notification must never break upload flow
            logger.error(
                "Notification failed for artifact %s (best-effort, swallowed): %s",
                getattr(artifact, 'id', '?'), exc,
            )

    async def _do_notify_student_on_upload(
        self,
        artifact: ExaminationArtifact,
        uploaded_by_username: str,
        actor_ip: Optional[str] = None,
    ) -> None:
        """Internal implementation — exceptions propagate to caller wrapper."""
        if not artifact.parsed_reg_no or not artifact.parsed_subject_code:
            return

        if not mail_service.is_configured():
            logger.debug("Skipping notification: email service not configured")
            return

        result = await self.db.execute(
            select(StudentUsernameRegister).where(
                StudentUsernameRegister.register_number == artifact.parsed_reg_no
            )
        )
        username_mapping = result.scalar_one_or_none()

        if not username_mapping:
            await self.audit_service.log_action(
                action="student_notification_skipped",
                action_category="notification",
                actor_type="system",
                actor_username="notification_service",
                actor_ip=actor_ip,
                artifact_id=artifact.id,
                description=(
                    f"No username mapping found for register number {artifact.parsed_reg_no}"
                ),
            )
            return

        if not settings.moodle_admin_token:
            # Admin token not configured - skip user lookup, but don't fail
            # Students can still submit without email notifications
            await self.audit_service.log_action(
                action="student_notification_skipped",
                action_category="notification",
                actor_type="system",
                actor_username="notification_service",
                actor_ip=actor_ip,
                artifact_id=artifact.id,
                description="Moodle admin token not configured - email notification skipped (not critical)",
            )
            logger.info(f"Admin token not configured - skipping email notification for {artifact.parsed_reg_no}")
            return

        moodle_username = username_mapping.moodle_username

        recipient_email = None
        recipient_name = None
        client = MoodleClient(token=settings.moodle_admin_token)
        try:
            user_data = await client.get_user_by_username(moodle_username)
            if user_data:
                recipient_email = user_data.get("email")
                recipient_name = user_data.get("fullname")
        except MoodleAPIError as exc:
            logger.warning("Failed to fetch Moodle user/email for %s: %s", moodle_username, exc)
        except Exception as exc:
            logger.error("Unexpected error during Moodle user lookup for %s: %s", moodle_username, exc)
        finally:
            await client.close()

        if not recipient_email:
            await self.audit_service.log_action(
                action="student_notification_skipped",
                action_category="notification",
                actor_type="system",
                actor_username="notification_service",
                actor_ip=actor_ip,
                artifact_id=artifact.id,
                description=f"No email available in Moodle profile for user {moodle_username}",
            )
            return

        subject_mapping = await self.mapping_service.get_mapping(
            artifact.parsed_subject_code,
            artifact.exam_type,
        )

        sent, message = await mail_service.send_student_upload_notification(
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            register_number=artifact.parsed_reg_no,
            subject_code=artifact.parsed_subject_code,
            subject_name=subject_mapping.subject_name if subject_mapping else None,
            exam_type=artifact.exam_type,
            exam_session=subject_mapping.exam_session if subject_mapping else None,
            filename=artifact.original_filename,
            uploaded_by=uploaded_by_username,
            uploaded_at=artifact.uploaded_at,
        )

        if sent:
            await self.audit_service.log_action(
                action="student_notification_sent",
                action_category="notification",
                actor_type="system",
                actor_username="notification_service",
                actor_ip=actor_ip,
                artifact_id=artifact.id,
                description=f"Upload notification sent to {recipient_email}",
                response_data={"recipient_email": recipient_email},
            )
        else:
            await self.audit_service.log_action(
                action="student_notification_failed",
                action_category="notification",
                actor_type="system",
                actor_username="notification_service",
                actor_ip=actor_ip,
                artifact_id=artifact.id,
                description=message,
                response_data={"recipient_email": recipient_email},
            )

    async def send_test_upload_notification(
        self,
        *,
        register_number: str,
        subject_code: str,
        exam_type: str,
        filename: str,
        uploaded_by_username: str,
    ) -> dict:
        """
        Send a test upload notification email for admin verification.

        Returns a structured result with success flag and resolved recipient details.
        
        NOTE: Admin token is optional. If not configured, returns a message indicating
        email notifications are disabled.
        """
        if not mail_service.is_configured():
            return {
                "success": False,
                "message": "SMTP/SendGrid is not configured",
            }

        if not settings.moodle_admin_token:
            return {
                "success": False,
                "message": "Moodle admin token not configured - email notifications disabled (optional feature)",
                "note": "Configure MOODLE_ADMIN_TOKEN to enable email notifications from admin account"
            }

        result = await self.db.execute(
            select(StudentUsernameRegister).where(
                StudentUsernameRegister.register_number == register_number
            )
        )
        username_mapping = result.scalar_one_or_none()

        if not username_mapping:
            return {
                "success": False,
                "message": f"No username mapping found for register number {register_number}",
            }

        moodle_username = username_mapping.moodle_username

        recipient_email = None
        recipient_name = None
        client = MoodleClient(token=settings.moodle_admin_token)
        try:
            user_data = await client.get_user_by_username(moodle_username)
            if user_data:
                recipient_email = user_data.get("email")
                recipient_name = user_data.get("fullname")
        except MoodleAPIError as exc:
            logger.warning("Failed to fetch Moodle user/email for %s: %s", moodle_username, exc)
        except Exception as exc:
            logger.error("Unexpected error during Moodle user lookup for %s: %s", moodle_username, exc)
        finally:
            await client.close()

        if not recipient_email:
            return {
                "success": False,
                "message": f"No email available in Moodle profile for user {moodle_username}",
            }

        subject_mapping = await self.mapping_service.get_mapping(subject_code, exam_type)

        sent, message = await mail_service.send_student_upload_notification(
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            register_number=register_number,
            subject_code=subject_code,
            subject_name=subject_mapping.subject_name if subject_mapping else None,
            exam_type=exam_type,
            exam_session=subject_mapping.exam_session if subject_mapping else None,
            filename=filename,
            uploaded_by=uploaded_by_username,
            uploaded_at=datetime.utcnow(),
        )

        return {
            "success": sent,
            "message": message,
            "recipient_email": recipient_email,
            "moodle_username": moodle_username,
            "subject_name": subject_mapping.subject_name if subject_mapping else None,
            "exam_session": subject_mapping.exam_session if subject_mapping else None,
        }
