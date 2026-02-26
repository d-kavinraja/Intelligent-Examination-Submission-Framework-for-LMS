"""
Mail Service
Handles SMTP email notifications for student-facing events.
"""

import asyncio
import logging
import smtplib
from datetime import datetime
from email.message import EmailMessage
from typing import Optional, Tuple

from app.core.config import settings

logger = logging.getLogger(__name__)


class MailService:
    """Service for sending outbound emails via SMTP."""

    def is_configured(self) -> bool:
        """Return True when SMTP is enabled and minimally configured."""
        return bool(
            settings.smtp_enabled
            and settings.smtp_host
            and settings.smtp_sender_email
        )

    async def send_student_upload_notification(
        self,
        *,
        recipient_email: str,
        recipient_name: Optional[str],
        register_number: str,
        subject_code: str,
        subject_name: Optional[str],
        exam_type: str,
        exam_session: Optional[str],
        filename: str,
        uploaded_by: str,
        uploaded_at: Optional[datetime] = None,
    ) -> Tuple[bool, str]:
        """
        Send notification when a staff member uploads a student's paper.
        """
        if not self.is_configured():
            return False, "SMTP is not configured"

        if not recipient_email:
            return False, "Recipient email not available"

        display_name = recipient_name or "Student"
        paper_title = subject_name or subject_code
        uploaded_at_text = (uploaded_at or datetime.utcnow()).strftime("%d %b %Y, %I:%M %p UTC")

        email_message = EmailMessage()
        email_message["From"] = f"{settings.smtp_from_name} <{settings.smtp_sender_email}>"
        email_message["To"] = recipient_email
        email_message["Subject"] = f"[{exam_type}] Paper Uploaded - {subject_code}"

        body = (
            f"Hello {display_name},\n\n"
            f"A paper has been uploaded to your student portal.\n\n"
            f"Details:\n"
            f"- Exam Type: {exam_type}\n"
            f"- Subject Code: {subject_code}\n"
            f"- Subject Name: {paper_title}\n"
            f"- Exam Session: {exam_session or 'Not specified'}\n"
            f"- File: {filename}\n"
            f"- Uploaded By: {uploaded_by}\n"
            f"- Uploaded At: {uploaded_at_text}\n"
            f"- Register Number: {register_number}\n\n"
            f"Please login to the student portal to review and submit the paper.\n\n"
            f"Regards,\n"
            f"{settings.smtp_from_name}"
        )
        email_message.set_content(body)

        try:
            await asyncio.to_thread(self._send_message_sync, email_message)
            return True, "Notification sent"
        except Exception as exc:
            logger.error("Failed to send notification email: %s", exc)
            return False, f"Failed to send email: {exc}"

    def _send_message_sync(self, message: EmailMessage) -> None:
        """Blocking SMTP send, executed in a worker thread."""
        if settings.smtp_use_ssl:
            with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=20) as server:
                if settings.smtp_username and settings.smtp_password:
                    server.login(settings.smtp_username, settings.smtp_password)
                server.send_message(message)
            return

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:
            if settings.smtp_use_tls:
                server.starttls()
            if settings.smtp_username and settings.smtp_password:
                server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(message)


mail_service = MailService()
