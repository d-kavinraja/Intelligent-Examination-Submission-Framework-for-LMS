import pytest

from app.core.config import settings
from app.services.mail_service import MailService


@pytest.mark.asyncio
async def test_send_notification_returns_false_when_smtp_not_configured(monkeypatch):
    monkeypatch.setattr(settings, "smtp_enabled", False)
    monkeypatch.setattr(settings, "smtp_host", "")
    monkeypatch.setattr(settings, "smtp_from_email", "")
    monkeypatch.setattr(settings, "smtp_username", "")

    service = MailService()

    sent, message = await service.send_student_upload_notification(
        recipient_email="student@example.com",
        recipient_name="Student",
        register_number="212222240047",
        subject_code="19AI405",
        subject_name="Deep Learning",
        exam_type="CIA1",
        exam_session="2025-2026",
        filename="212222240047_19AI405.pdf",
        uploaded_by="staff1",
    )

    assert sent is False
    assert "SMTP" in message


@pytest.mark.asyncio
async def test_send_notification_success(monkeypatch):
    monkeypatch.setattr(settings, "smtp_enabled", True)
    monkeypatch.setattr(settings, "smtp_host", "smtp.example.com")
    monkeypatch.setattr(settings, "smtp_port", 587)
    monkeypatch.setattr(settings, "smtp_from_email", "noreply@example.com")
    monkeypatch.setattr(settings, "smtp_from_name", "Exam Middleware")
    monkeypatch.setattr(settings, "smtp_username", "mailer")
    monkeypatch.setattr(settings, "smtp_password", "secret")
    monkeypatch.setattr(settings, "smtp_use_tls", True)
    monkeypatch.setattr(settings, "smtp_use_ssl", False)

    captured = {"called": False}

    def fake_send_sync(_message):
        captured["called"] = True

    service = MailService()
    monkeypatch.setattr(service, "_send_message_sync", fake_send_sync)

    sent, message = await service.send_student_upload_notification(
        recipient_email="student@example.com",
        recipient_name="Student",
        register_number="212222240047",
        subject_code="19AI405",
        subject_name="Deep Learning",
        exam_type="CIA2",
        exam_session="2025-2026",
        filename="212222240047_19AI405.pdf",
        uploaded_by="staff1",
    )

    assert sent is True
    assert message == "Notification sent"
    assert captured["called"] is True
