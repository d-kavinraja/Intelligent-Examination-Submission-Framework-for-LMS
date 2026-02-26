"""
Tests for EmailService.

All SMTP interactions are mocked — no real network calls.

Covers:
  - Service initialisation (configured vs unconfigured)
  - send_email (STARTTLS, SSL, and disabled modes)
  - notify_student_upload (template rendering, missing email)
  - Fire-and-forget guarantee (SMTP exceptions never propagate)
"""

import smtplib
from unittest.mock import patch, MagicMock

import pytest


# ---------------------------------------------------------------------------
# We need to patch settings BEFORE importing EmailService so the global
# instance doesn't try to read the real .env file.
# ---------------------------------------------------------------------------

def _make_service(overrides: dict):
    """Create an EmailService with patched settings."""
    defaults = {
        "smtp_host": "smtp.test.com",
        "smtp_port": 587,
        "smtp_user": "test@test.com",
        "smtp_password": "secret",
        "smtp_from_email": "noreply@test.com",
        "smtp_use_tls": True,
        "smtp_use_ssl": False,
        "email_notifications_enabled": True,
    }
    defaults.update(overrides)

    mock_settings = MagicMock(**defaults)

    with patch("app.services.email_service.settings", mock_settings):
        from app.services.email_service import EmailService
        return EmailService()


# ======================================================================
# Initialisation
# ======================================================================

class TestInit:
    def test_configured_when_credentials_present(self):
        svc = _make_service({})
        assert svc._configured is True

    def test_not_configured_when_user_missing(self):
        svc = _make_service({"smtp_user": None})
        assert svc._configured is False

    def test_not_configured_when_password_missing(self):
        svc = _make_service({"smtp_password": None})
        assert svc._configured is False

    def test_not_configured_when_disabled(self):
        svc = _make_service({"email_notifications_enabled": False})
        assert svc._configured is False


# ======================================================================
# send_email
# ======================================================================

class TestSendEmail:
    def test_returns_false_when_not_configured(self):
        svc = _make_service({"smtp_user": None})
        result = svc.send_email("a@b.com", "subj", "<p>hi</p>")
        assert result is False

    @patch("app.services.email_service.smtplib.SMTP")
    def test_starttls_mode(self, mock_smtp_class):
        """STARTTLS: smtp_use_tls=True, smtp_use_ssl=False"""
        mock_server = MagicMock()
        mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)

        svc = _make_service({"smtp_use_tls": True, "smtp_use_ssl": False})

        with patch("app.services.email_service.settings") as ms:
            ms.smtp_host = "smtp.test.com"
            ms.smtp_port = 587
            ms.smtp_user = "test@test.com"
            ms.smtp_password = "secret"
            ms.smtp_from_email = "noreply@test.com"
            ms.smtp_use_tls = True
            ms.smtp_use_ssl = False

            result = svc.send_email("student@uni.edu", "Test", "<p>hello</p>")

        assert result is True
        mock_smtp_class.assert_called_once_with("smtp.test.com", 587, timeout=10)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("test@test.com", "secret")
        mock_server.sendmail.assert_called_once()

    @patch("app.services.email_service.smtplib.SMTP_SSL")
    def test_ssl_mode(self, mock_smtp_ssl_class):
        """SSL: smtp_use_ssl=True"""
        mock_server = MagicMock()
        mock_smtp_ssl_class.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_ssl_class.return_value.__exit__ = MagicMock(return_value=False)

        svc = _make_service({"smtp_use_ssl": True})

        with patch("app.services.email_service.settings") as ms:
            ms.smtp_host = "smtp.test.com"
            ms.smtp_port = 465
            ms.smtp_user = "test@test.com"
            ms.smtp_password = "secret"
            ms.smtp_from_email = "noreply@test.com"
            ms.smtp_use_ssl = True
            ms.smtp_use_tls = False

            result = svc.send_email("student@uni.edu", "Test", "<p>hello</p>")

        assert result is True
        mock_smtp_ssl_class.assert_called_once_with("smtp.test.com", 465, timeout=10)

    @patch("app.services.email_service.smtplib.SMTP")
    def test_smtp_exception_returns_false(self, mock_smtp_class):
        """Fire-and-forget: SMTP failure returns False, never raises."""
        mock_smtp_class.side_effect = smtplib.SMTPException("connection refused")

        svc = _make_service({"smtp_use_ssl": False})

        with patch("app.services.email_service.settings") as ms:
            ms.smtp_host = "smtp.test.com"
            ms.smtp_port = 587
            ms.smtp_user = "test@test.com"
            ms.smtp_password = "secret"
            ms.smtp_from_email = "noreply@test.com"
            ms.smtp_use_ssl = False
            ms.smtp_use_tls = True

            result = svc.send_email("student@uni.edu", "Test", "<p>fail</p>")

        assert result is False  # Never raises


# ======================================================================
# notify_student_upload
# ======================================================================

class TestNotifyStudentUpload:
    def test_returns_false_for_empty_email(self):
        svc = _make_service({})
        assert svc.notify_student_upload("", "212222240047", "19AI405") is False

    def test_returns_false_for_none_email(self):
        svc = _make_service({})
        assert svc.notify_student_upload(None, "212222240047", "19AI405") is False

    @patch("app.services.email_service.smtplib.SMTP")
    def test_sends_with_correct_subject(self, mock_smtp_class):
        mock_server = MagicMock()
        mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)

        svc = _make_service({})

        with patch("app.services.email_service.settings") as ms:
            ms.smtp_host = "smtp.test.com"
            ms.smtp_port = 587
            ms.smtp_user = "test@test.com"
            ms.smtp_password = "secret"
            ms.smtp_from_email = "noreply@test.com"
            ms.smtp_use_ssl = False
            ms.smtp_use_tls = True

            result = svc.notify_student_upload(
                student_email="student@uni.edu",
                register_number="212222240047",
                subject_code="19AI405",
            )

        assert result is True
        # Verify sendmail was called with the student's address
        call_args = mock_server.sendmail.call_args
        assert "student@uni.edu" in call_args[0][1]

    def test_template_contains_subject_and_register(self):
        """Verify the HTML template renders register number and subject code."""
        from app.services.email_service import UPLOAD_NOTIFICATION_TEMPLATE

        html = UPLOAD_NOTIFICATION_TEMPLATE.format(
            subject_code="19AI405",
            register_number="212222240047",
            portal_url="http://localhost:8000",
        )
        assert "19AI405" in html
        assert "212222240047" in html
        assert "http://localhost:8000" in html
