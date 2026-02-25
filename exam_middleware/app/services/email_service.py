"""
Email Notification Service
Sends student notifications via SMTP when staff uploads answer sheets.

Follows the global-instance pattern used by MoodleClient and FileProcessor.
Uses Python's built-in smtplib — no third-party email SDK required.

Supports two connection modes:
  - STARTTLS on port 587 (smtp_use_tls=True, smtp_use_ssl=False)  — default
  - Direct SSL on port 465 (smtp_use_ssl=True)                    — fallback
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

# HTML email template for student upload notification
UPLOAD_NOTIFICATION_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f4f6f8; margin: 0; padding: 0; }}
    .container {{ max-width: 520px; margin: 40px auto; background: #ffffff; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); overflow: hidden; }}
    .header {{ background: linear-gradient(135deg, #1a73e8 0%, #0d47a1 100%); padding: 28px 32px; text-align: center; }}
    .header h1 {{ color: #ffffff; margin: 0; font-size: 20px; font-weight: 600; }}
    .body {{ padding: 32px; color: #333333; line-height: 1.7; }}
    .highlight {{ display: inline-block; background: #e8f0fe; color: #1a73e8; padding: 3px 12px; border-radius: 6px; font-weight: 600; font-size: 15px; }}
    .cta {{ display: block; text-align: center; margin: 28px 0 8px; }}
    .cta a {{ background: #1a73e8; color: #ffffff; text-decoration: none; padding: 12px 32px; border-radius: 8px; font-weight: 600; font-size: 15px; }}
    .footer {{ text-align: center; padding: 16px 32px 24px; color: #888888; font-size: 12px; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>📄 Answer Sheet Ready for Review</h1>
    </div>
    <div class="body">
      <p>Hello,</p>
      <p>
        Your physical answer sheet for <span class="highlight">{subject_code}</span>
        has been scanned and uploaded to the Examination Portal.
      </p>
      <p>
        <strong>Register Number:</strong> {register_number}<br>
        <strong>Subject Code:</strong> {subject_code}
      </p>
      <p>
        Please log in to the <strong>Student Portal</strong> to review the
        scanned PDF and confirm your final submission to Moodle LMS.
      </p>
      <div class="cta">
        <a href="{portal_url}">Open Student Portal</a>
      </div>
    </div>
    <div class="footer">
      Examination Middleware &mdash; Automated notification. Do not reply to this email.
    </div>
  </div>
</body>
</html>
"""


class EmailService:
    """
    Service for sending email notifications via SMTP.

    Implements a fire-and-forget notification pattern:
    - If SMTP credentials are not configured, methods log a warning and
      return gracefully.
    - Email failures never propagate to the caller (upload must never fail
      because of a notification issue).

    Connection modes (controlled via settings):
    - STARTTLS (port 587): smtp_use_tls=True,  smtp_use_ssl=False  (default)
    - Direct SSL (port 465): smtp_use_ssl=True

    Global instance: ``email_service`` (bottom of this module).
    """

    def __init__(self):
        self._configured = False
        if (
            settings.smtp_user
            and settings.smtp_password
            and settings.email_notifications_enabled
        ):
            self._configured = True
            mode = "SSL" if settings.smtp_use_ssl else ("STARTTLS" if settings.smtp_use_tls else "plain")
            logger.info(
                f"EmailService initialised — SMTP via {settings.smtp_host}:{settings.smtp_port} ({mode})"
            )
        else:
            logger.info(
                "EmailService: email notifications disabled "
                "(SMTP credentials not set or EMAIL_NOTIFICATIONS_ENABLED=false)"
            )

    # ------------------------------------------------------------------
    # Core send
    # ------------------------------------------------------------------

    def send_email(
        self,
        to: str,
        subject: str,
        html_body: str,
    ) -> bool:
        """
        Send an email via SMTP.

        Returns True on success, False on failure.  Never raises.
        """
        if not self._configured:
            logger.warning("Email not sent — SMTP not configured")
            return False

        from_addr = settings.smtp_from_email or settings.smtp_user

        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = from_addr
            msg["To"] = to
            msg["Subject"] = subject
            msg.attach(MIMEText(html_body, "html"))

            if settings.smtp_use_ssl:
                # Direct SSL connection (typically port 465)
                with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=10) as server:
                    server.login(settings.smtp_user, settings.smtp_password)
                    server.sendmail(from_addr, [to], msg.as_string())
            else:
                # Plain or STARTTLS connection (typically port 587)
                with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
                    if settings.smtp_use_tls:
                        server.starttls()
                    server.login(settings.smtp_user, settings.smtp_password)
                    server.sendmail(from_addr, [to], msg.as_string())

            logger.info(f"Email sent to {to} via {settings.smtp_host}")
            return True

        except Exception as exc:
            logger.error(f"Failed to send email to {to}: {exc}", exc_info=True)
            return False

    # ------------------------------------------------------------------
    # Convenience: student upload notification
    # ------------------------------------------------------------------

    def notify_student_upload(
        self,
        student_email: str,
        register_number: str,
        subject_code: str,
        portal_url: Optional[str] = None,
    ) -> bool:
        """
        Notify a student that their answer sheet has been uploaded.

        Args:
            student_email: Destination email address.
            register_number: Student's 12-digit register number.
            subject_code: Parsed subject code from the filename.
            portal_url: Link to the student portal (defaults to localhost).

        Returns True on success, False on failure.  Never raises.
        """
        if not student_email:
            logger.warning("Cannot send notification — no student email provided")
            return False

        url = portal_url or "http://localhost:8000/portal/student"

        html = UPLOAD_NOTIFICATION_TEMPLATE.format(
            subject_code=subject_code,
            register_number=register_number,
            portal_url=url,
        )

        return self.send_email(
            to=student_email,
            subject=f"Your answer sheet for {subject_code} is ready to review",
            html_body=html,
        )


# Global instance (follows moodle_client / file_processor pattern)
email_service = EmailService()
