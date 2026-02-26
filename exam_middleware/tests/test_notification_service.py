from types import SimpleNamespace

import pytest

from app.services.notification_service import NotificationService


class _ScalarResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class _FakeDB:
    def __init__(self, mapping_obj):
        self.mapping_obj = mapping_obj

    async def execute(self, _query):
        return _ScalarResult(self.mapping_obj)


class _FakeMoodleClient:
    def __init__(self, token=None):
        self.token = token

    async def get_user_by_username(self, username):
        return {
            "username": username,
            "email": "student@example.com",
            "fullname": "Demo Student",
        }

    async def close(self):
        return None


@pytest.mark.asyncio
async def test_notify_student_on_upload_skips_without_smtp(monkeypatch):
    artifact = SimpleNamespace(
        id=1,
        parsed_reg_no="212222240047",
        parsed_subject_code="19AI405",
        exam_type="CIA1",
        original_filename="212222240047_19AI405.pdf",
        uploaded_at=None,
    )

    db = _FakeDB(mapping_obj=SimpleNamespace(moodle_username="u1", register_number="212222240047"))
    service = NotificationService(db)

    monkeypatch.setattr("app.services.notification_service.mail_service.is_configured", lambda: False)

    actions = []

    async def fake_log_action(**kwargs):
        actions.append(kwargs)

    monkeypatch.setattr(service.audit_service, "log_action", fake_log_action)

    await service.notify_student_on_upload(
        artifact=artifact,
        uploaded_by_username="staff1",
        actor_ip="127.0.0.1",
    )

    assert actions == []


@pytest.mark.asyncio
async def test_notify_student_on_upload_success(monkeypatch):
    artifact = SimpleNamespace(
        id=7,
        parsed_reg_no="212222240047",
        parsed_subject_code="19AI405",
        exam_type="CIA2",
        original_filename="212222240047_19AI405.pdf",
        uploaded_at=None,
    )

    db = _FakeDB(mapping_obj=SimpleNamespace(moodle_username="demo.user", register_number="212222240047"))
    service = NotificationService(db)

    monkeypatch.setattr("app.services.notification_service.settings.moodle_admin_token", "token-1")
    monkeypatch.setattr("app.services.notification_service.mail_service.is_configured", lambda: True)
    monkeypatch.setattr("app.services.notification_service.MoodleClient", _FakeMoodleClient)

    async def fake_get_mapping(subject_code, exam_type):
        assert subject_code == "19AI405"
        assert exam_type == "CIA2"
        return SimpleNamespace(subject_name="Deep Learning", exam_session="2025-2026")

    monkeypatch.setattr(service.mapping_service, "get_mapping", fake_get_mapping)

    async def fake_send_mail(**kwargs):
        assert kwargs["recipient_email"] == "student@example.com"
        assert kwargs["subject_code"] == "19AI405"
        assert kwargs["exam_type"] == "CIA2"
        return True, "Notification sent"

    monkeypatch.setattr("app.services.notification_service.mail_service.send_student_upload_notification", fake_send_mail)

    actions = []

    async def fake_log_action(**kwargs):
        actions.append(kwargs)

    monkeypatch.setattr(service.audit_service, "log_action", fake_log_action)

    await service.notify_student_on_upload(
        artifact=artifact,
        uploaded_by_username="staff1",
        actor_ip="127.0.0.1",
    )

    assert any(a.get("action") == "student_notification_sent" for a in actions)


@pytest.mark.asyncio
async def test_send_test_upload_notification_returns_failure_without_mapping(monkeypatch):
    db = _FakeDB(mapping_obj=None)
    service = NotificationService(db)

    monkeypatch.setattr("app.services.notification_service.settings.moodle_admin_token", "token-1")
    monkeypatch.setattr("app.services.notification_service.mail_service.is_configured", lambda: True)

    result = await service.send_test_upload_notification(
        register_number="212222240047",
        subject_code="19AI405",
        exam_type="CIA1",
        filename="212222240047_19AI405.pdf",
        uploaded_by_username="staff1",
    )

    assert result["success"] is False
    assert "No username mapping" in result["message"]
