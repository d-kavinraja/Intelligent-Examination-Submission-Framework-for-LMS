import pytest
from types import SimpleNamespace
from sqlalchemy.exc import IntegrityError
from app.db.models import WorkflowStatus, ExaminationArtifact
from app.services.artifact_service import ArtifactService


class FakeResult:
    def __init__(self, items):
        self.items = items

    def scalars(self):
        return self

    def all(self):
        return self.items

    def scalar_one_or_none(self):
        return self.items[0] if self.items else None


class FakeDBSession:
    def __init__(self):
        self.added = []
        self.executed_queries = []
        self.existing_artifacts = []

    async def execute(self, query):
        self.executed_queries.append(query)
        # In create_artifact, the first execute() is get_by_transaction_id.
        # We simulate no match by transaction ID so it proceeds to check the group artifacts.
        if len(self.executed_queries) == 1:
            return FakeResult([])
        # Subsequent queries return the group's existing artifacts.
        return FakeResult(self.existing_artifacts)

    def add(self, model_instance):
        self.added.append(model_instance)

    async def flush(self):
        pass

    async def refresh(self, model_instance):
        pass

    async def rollback(self):
        pass


@pytest.mark.asyncio
async def test_attempt_2_inherits_unlocked_status_from_attempt_1():
    db = FakeDBSession()
    
    # Simulate an existing Attempt 1 artifact which has attempt_2_locked = False
    existing_attempt_1 = ExaminationArtifact(
        id=1,
        parsed_reg_no="212223240065",
        parsed_subject_code="19AI405",
        exam_type="CIA1",
        attempt_number=1,
        attempt_2_locked=False,
        workflow_status=WorkflowStatus.COMPLETED,
        transaction_id="tx_attempt1"
    )
    db.existing_artifacts = [existing_attempt_1]

    service = ArtifactService(db)
    
    # Upload the Attempt 2 paper
    new_artifact = await service.create_artifact(
        raw_filename="212223240065_19AI405.pdf",
        original_filename="212223240065_19AI405.pdf",
        file_blob_path="uploads/pending/212223240065_19AI405.pdf",
        file_hash="hash2",
        parsed_reg_no="212223240065",
        parsed_subject_code="19AI405",
        exam_type="CIA1",
        file_size_bytes=1234,
        mime_type="application/pdf"
    )

    # Verify that the new artifact has attempt_number = 2
    assert new_artifact.attempt_number == 2
    # Verify that the new artifact inherits attempt_2_locked = False from the existing Attempt 1
    assert new_artifact.attempt_2_locked is False
    # Verify that the existing Attempt 1 is marked as SUPERSEDED
    assert existing_attempt_1.workflow_status == WorkflowStatus.SUPERSEDED


@pytest.mark.asyncio
async def test_attempt_2_creation_fails_if_attempt_1_is_locked():
    db = FakeDBSession()
    
    # Simulate an existing Attempt 1 artifact which has attempt_2_locked = True (default)
    existing_attempt_1 = ExaminationArtifact(
        id=1,
        parsed_reg_no="212223240065",
        parsed_subject_code="19AI405",
        exam_type="CIA1",
        attempt_number=1,
        attempt_2_locked=True,
        workflow_status=WorkflowStatus.COMPLETED,
        transaction_id="tx_attempt1"
    )
    db.existing_artifacts = [existing_attempt_1]

    service = ArtifactService(db)
    
    # Attempt to upload Attempt 2 paper while it is locked should raise an Exception
    with pytest.raises(Exception) as exc_info:
        await service.create_artifact(
            raw_filename="212223240065_19AI405.pdf",
            original_filename="212223240065_19AI405.pdf",
            file_blob_path="uploads/pending/212223240065_19AI405.pdf",
            file_hash="hash2",
            parsed_reg_no="212223240065",
            parsed_subject_code="19AI405",
            exam_type="CIA1",
            file_size_bytes=1234,
            mime_type="application/pdf"
        )
    
    assert "Attempt 2 is locked" in str(exc_info.value)
