"""
Services module initialization
"""

from app.services.moodle_client import MoodleClient, MoodleAPIError, moodle_client
from app.services.file_processor import FileProcessor, file_processor
from app.services.artifact_service import (
    ArtifactService,
    SubjectMappingService,
    AuditService,
)
from app.services.submission_service import SubmissionService
from app.services.mail_service import MailService, mail_service
from app.services.notification_service import NotificationService

__all__ = [
    "MoodleClient",
    "MoodleAPIError",
    "moodle_client",
    "FileProcessor",
    "file_processor",
    "ArtifactService",
    "SubjectMappingService",
    "AuditService",
    "SubmissionService",
    "MailService",
    "mail_service",
    "NotificationService",
]
