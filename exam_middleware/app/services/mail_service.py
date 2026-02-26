"""
Mail Service
Handles email notifications via SendGrid (HTTP API) or SMTP fallback.
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
    """Service for sending outbound emails via SendGrid or SMTP."""

    def is_configured(self) -> bool:
        """Return True when email sending is configured (SendGrid or SMTP)."""
        # Prefer SendGrid (works from cloud platforms)
        if settings.sendgrid_api_key and settings.email_sender_email:
            return True
        
        # Fallback to SMTP (local dev only, blocked on most cloud platforms)
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
        Uses SendGrid if configured, falls back to SMTP for local dev.
        """
        if not self.is_configured():
            return False, "Email service not configured"

        if not recipient_email:
            return False, "Recipient email not available"

        display_name = recipient_name or "Student"
        paper_title = subject_name or subject_code
        uploaded_at_text = (uploaded_at or datetime.utcnow()).strftime("%d %b %Y, %I:%M %p UTC")

        subject = f"[{exam_type}] Paper Uploaded - {subject_code}"
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
            f"{settings.email_from_name}"
        )

        # Try SendGrid first (works from cloud platforms)
        if settings.sendgrid_api_key:
            try:
                return await self._send_via_sendgrid(
                    to_email=recipient_email,
                    to_name=display_name,
                    subject=subject,
                    body=body,
                )
            except Exception as exc:
                logger.error("SendGrid send failed: %s", exc)
                # Don't fall back to SMTP on cloud - it will fail too
                return False, f"SendGrid error: {exc}"

        # Fallback to SMTP (local dev only)
        if settings.smtp_enabled and settings.smtp_host:
            try:
                return await self._send_via_smtp(
                    to_email=recipient_email,
                    to_name=display_name,
                    subject=subject,
                    body=body,
                )
            except Exception as exc:
                logger.error("SMTP send failed: %s", exc)
                return False, f"SMTP error: {exc}"

        return False, "No email backend available"

    async def _send_via_sendgrid(
        self, to_email: str, to_name: str, subject: str, body: str
    ) -> Tuple[bool, str]:
        """Send email via SendGrid HTTP API."""
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail, Email, To, Content
        except ImportError:
            return False, "SendGrid library not installed"

        message = Mail(
            from_email=Email(settings.email_sender_email, settings.email_from_name),
            to_emails=To(to_email, to_name),
            subject=subject,
            plain_text_content=Content("text/plain", body),
        )

        sg = SendGridAPIClient(settings.sendgrid_api_key)
        response = await asyncio.to_thread(sg.send, message)
        
        if response.status_code in (200, 201, 202):
            logger.info("SendGrid email sent to %s (status: %s)", to_email, response.status_code)
            return True, "Notification sent"
        else:
            logger.error("SendGrid returned status %s: %s", response.status_code, response.body)
            return False, f"SendGrid error: {response.status_code}"

    async def _send_via_smtp(
        self, to_email: str, to_name: str, subject: str, body: str
    ) -> Tuple[bool, str]:
        """Send email via SMTP (fallback for local dev)."""
        email_message = EmailMessage()
        email_message["From"] = f"{settings.smtp_from_name} <{settings.smtp_sender_email}>"
        email_message["To"] = to_email
        email_message["Subject"] = subject
        email_message.set_content(body)

        await asyncio.to_thread(self._send_message_sync, email_message)
        return True, "Notification sent"

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
