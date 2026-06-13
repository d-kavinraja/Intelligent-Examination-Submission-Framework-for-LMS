from types import SimpleNamespace

import pytest

from app.db.models import WorkflowStatus
from app.services.submission_service import SubmissionService
import app.services.submission_service as submission_module


class FakeAuditService:
    def __init__(self):
        self.entries = []

    async def log_action(self, **kwargs):
        self.entries.append(kwargs)
        return SimpleNamespace(id=len(self.entries), **kwargs)


class FakeArtifact(SimpleNamespace):
    def __init__(self, **kwargs):
        defaults = {
            "id": 1,
            "parsed_reg_no": "212223240065",
            "parsed_subject_code": "19AI405",
            "exam_type": "CIA1",
            "attempt_number": 1,
            "attempt_2_locked": True,
            "workflow_status": WorkflowStatus.PENDING,
            "file_blob_path": "uploads/pending/paper.pdf",
            "file_content": None,
            "transaction_log": [],
        }
        defaults.update(kwargs)
        super().__init__(**defaults)

    def add_log_entry(self, action, details):
        self.transaction_log.append({"action": action, "details": details})


def make_service():
    service = SubmissionService.__new__(SubmissionService)
    service.audit_service = FakeAuditService()
    return service


@pytest.mark.asyncio
async def test_locking_after_attempt_1_submission(monkeypatch):
    service = make_service()
    artifact = FakeArtifact(attempt_number=1, attempt_2_locked=False)
    lock_calls = []

    async def fake_set_group_attempt_lock(target, locked):
        target.attempt_2_locked = locked
        lock_calls.append((target.id, locked))

    monkeypatch.setattr(service, "_set_group_attempt_lock", fake_set_group_attempt_lock)

    await service.lock_assessment_after_attempt_1_submission(
        artifact=artifact,
        moodle_user_id=405,
        moodle_username="student1",
        actor_ip="127.0.0.1",
    )

    assert artifact.attempt_2_locked is True
    assert lock_calls == [(artifact.id, True)]
    assert artifact.transaction_log[-1]["action"] == "assessment_locked_after_attempt_1"
    assert service.audit_service.entries[-1]["action"] == "assessment_locked_after_attempt_1"


@pytest.mark.asyncio
async def test_attempt_2_submit_replaces_attempt_1(monkeypatch):
    service = make_service()
    attempt1 = FakeArtifact(id=10, attempt_number=1, workflow_status=WorkflowStatus.COMPLETED)
    attempt2 = FakeArtifact(id=20, attempt_number=2, attempt_2_locked=False)
    deleted_attempts = []
    lock_calls = []

    async def fake_find_attempt_artifact(_artifact, attempt_number):
        return attempt1 if attempt_number == 1 else None

    async def fake_delete_exam_submission_record(_artifact, attempt_number):
        deleted_attempts.append(attempt_number)

    async def fake_set_group_attempt_lock(target, locked):
        target.attempt_2_locked = locked
        lock_calls.append((target.id, locked))

    monkeypatch.setattr(service, "_find_attempt_artifact", fake_find_attempt_artifact)
    monkeypatch.setattr(service, "_delete_exam_submission_record", fake_delete_exam_submission_record)
    monkeypatch.setattr(service, "_set_group_attempt_lock", fake_set_group_attempt_lock)

    await service.replace_attempt_1_with_attempt_2(
        attempt2=attempt2,
        moodle_user_id=405,
        moodle_username="student1",
        actor_ip="127.0.0.1",
        unlock_result={"attempted": True, "success": True},
    )

    assert deleted_attempts == [1]
    assert attempt1.workflow_status == WorkflowStatus.SUPERSEDED
    assert attempt2.attempt_2_locked is True
    assert lock_calls == [(attempt2.id, True)]
    assert attempt1.transaction_log[-1]["action"] == "attempt_1_removed_for_attempt_2"
    assert attempt2.transaction_log[-1]["action"] == "attempt_2_replaced_attempt_1"
    assert service.audit_service.entries[-1]["action"] == "attempt_1_replaced_by_attempt_2"


@pytest.mark.asyncio
async def test_attempt_2_open_without_uploaded_paper_is_rejected(monkeypatch):
    service = make_service()
    attempt1 = FakeArtifact(attempt_number=1, attempt_2_locked=False)

    async def fake_find_attempt_artifact(_artifact, attempt_number):
        assert attempt_number == 2
        return None

    monkeypatch.setattr(service, "_find_attempt_artifact", fake_find_attempt_artifact)

    ok, message, details = await service.validate_attempt_submission_window(attempt1)

    assert ok is False
    assert "no Attempt 2 paper has been uploaded" in message
    assert details == {"attempt_2_missing_paper": True}


@pytest.mark.asyncio
async def test_attempt_2_submit_without_staff_unlock_is_rejected():
    service = make_service()
    attempt2 = FakeArtifact(attempt_number=2, attempt_2_locked=True)

    ok, message, details = await service.validate_attempt_submission_window(attempt2)

    assert ok is False
    assert "Attempt 2 is locked" in message
    assert details == {"attempt_2_locked": True}


@pytest.mark.asyncio
async def test_attempt_2_moodle_unlock_reverts_previous_submission_to_draft(monkeypatch):
    service = make_service()
    attempt2 = FakeArtifact(attempt_number=2, attempt_2_locked=False)

    class FakeMoodleClient:
        def __init__(self, base_url, token):
            self.base_url = base_url
            self.token = token

        async def set_user_flags_locked(self, assignment_id, user_id, locked, token):
            assert assignment_id == 77
            assert user_id == 405
            assert locked is False
            assert token == "admin-token"
            return {"success": True}

        async def unlock_submissions(self, assignment_id, user_ids, token):
            assert assignment_id == 77
            assert user_ids == [405]
            assert token == "admin-token"
            return {"success": True}

        async def revert_submissions_to_draft(self, assignment_id, user_ids, token):
            assert assignment_id == 77
            assert user_ids == [405]
            assert token == "admin-token"
            return {"success": True}

        async def remove_submission(self, assignment_id, user_id, token):
            assert assignment_id == 77
            assert user_id == 405
            assert token == "admin-token"
            return {"success": True}

        async def close(self):
            return None

    monkeypatch.setattr(service, "_get_admin_token", lambda: "admin-token")
    monkeypatch.setattr(submission_module, "MoodleClient", FakeMoodleClient)

    result = await service.unlock_previous_attempt_for_replacement(
        artifact=attempt2,
        assignment_id=77,
        moodle_user_id=405,
        target_site_url="https://moodle.example.com",
    )

    assert result["success"] is True
    assert [a["name"] for a in result["actions"]] == [
        "mod_assign_set_user_flags",
        "mod_assign_unlock_submissions",
        "mod_assign_revert_submissions_to_draft",
        "mod_assign_remove_submission",
    ]
