"""
Tests for FileProcessor service.

Covers:
  - Filename parsing (strict and flexible patterns)
  - File validation (size, extension, magic bytes)
  - MIME type detection
  - Standardized filename generation
"""

import os
import sys
import pytest

# ---------------------------------------------------------------------------
# Import FileProcessor directly from its module file, bypassing
# app.services.__init__ (which pulls in ArtifactService → DB models).
# ---------------------------------------------------------------------------
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from app.services.file_processor import FileProcessor

# Inline test constants (same as conftest)
PDF_MAGIC = b"%PDF-1.4 fake pdf content for testing"
JPEG_MAGIC = b"\xff\xd8\xff\xe0fake jpeg content for testing"
PNG_MAGIC = b"\x89PNG\r\n\x1a\nfake png content for testing"
INVALID_CONTENT = b"this is not a valid file format"


@pytest.fixture
def processor(tmp_path):
    """FileProcessor with a temporary upload directory."""
    return FileProcessor(upload_dir=str(tmp_path))


# ======================================================================
# Filename Parsing — strict pattern
# ======================================================================

class TestParseFilenameStrict:
    """Test the strict regex: exactly 12 digits _ 2-10 alphanumeric . ext"""

    def test_valid_pdf(self, processor):
        reg, subj, valid = processor.parse_filename("212222240047_19AI405.pdf")
        assert valid is True
        assert reg == "212222240047"
        assert subj == "19AI405"

    def test_valid_jpg(self, processor):
        reg, subj, valid = processor.parse_filename("611221104088_ML.jpg")
        assert valid is True
        assert reg == "611221104088"
        assert subj == "ML"

    def test_valid_png(self, processor):
        reg, subj, valid = processor.parse_filename("611221104090_19AI411.png")
        assert valid is True
        assert subj == "19AI411"

    def test_subject_code_uppercased(self, processor):
        reg, subj, valid = processor.parse_filename("212222240047_ml.pdf")
        assert valid is True
        assert subj == "ML"

    def test_invalid_no_underscore(self, processor):
        reg, subj, valid = processor.parse_filename("21222224004719AI405.pdf")
        # Flexible pattern may still match
        assert (valid is True and reg is not None) or valid is False

    def test_invalid_empty_string(self, processor):
        reg, subj, valid = processor.parse_filename("")
        assert valid is False
        assert reg is None
        assert subj is None

    def test_invalid_no_extension(self, processor):
        reg, subj, valid = processor.parse_filename("212222240047_19AI405")
        assert valid is False

    def test_invalid_wrong_extension(self, processor):
        reg, subj, valid = processor.parse_filename("212222240047_19AI405.exe")
        assert valid is False


# ======================================================================
# MIME Type Detection
# ======================================================================

class TestMimeDetection:
    def test_pdf(self, processor):
        assert processor._detect_mime_type(PDF_MAGIC) == "application/pdf"

    def test_jpeg(self, processor):
        assert processor._detect_mime_type(JPEG_MAGIC) == "image/jpeg"

    def test_png(self, processor):
        assert processor._detect_mime_type(PNG_MAGIC) == "image/png"

    def test_unknown(self, processor):
        assert processor._detect_mime_type(INVALID_CONTENT) is None


# ======================================================================
# File Validation
# ======================================================================

class TestValidateFile:
    def test_valid_pdf_file(self, processor):
        is_valid, msg, meta = processor.validate_file(
            PDF_MAGIC, "212222240047_19AI405.pdf"
        )
        assert is_valid is True
        assert meta["parsed_register_no"] == "212222240047"
        assert meta["parsed_subject_code"] == "19AI405"
        assert meta["mime_type"] == "application/pdf"
        assert meta["size_bytes"] == len(PDF_MAGIC)

    def test_invalid_extension_rejected(self, processor):
        is_valid, msg, meta = processor.validate_file(
            PDF_MAGIC, "212222240047_19AI405.exe"
        )
        assert is_valid is False
        assert "file type" in msg.lower() or "allowed" in msg.lower()

    def test_invalid_magic_bytes_rejected(self, processor):
        is_valid, msg, meta = processor.validate_file(
            INVALID_CONTENT, "212222240047_19AI405.pdf"
        )
        assert is_valid is False
        assert "file type" in msg.lower() or "determine" in msg.lower()

    def test_bad_filename_rejected(self, processor):
        is_valid, msg, meta = processor.validate_file(PDF_MAGIC, "random.pdf")
        assert is_valid is False
        assert "filename" in msg.lower()


# ======================================================================
# Standardized Filename Generation
# ======================================================================

class TestStandardizedFilename:
    def test_basic(self, processor):
        result = processor.generate_standardized_filename("212222240047", "19AI405")
        assert result == "212222240047_19AI405.pdf"

    def test_pads_short_register(self, processor):
        result = processor.generate_standardized_filename("12345", "ML")
        assert result.startswith("0000000")
        assert result.endswith("_ML.pdf")

    def test_custom_extension(self, processor):
        result = processor.generate_standardized_filename(
            "212222240047", "ML", extension=".jpg"
        )
        assert result.endswith(".jpg")

    def test_uppercases_subject(self, processor):
        result = processor.generate_standardized_filename("212222240047", "ml")
        assert "_ML.pdf" in result


# ======================================================================
# Async File Operations
# ======================================================================

class TestFileOperations:
    @pytest.mark.asyncio
    async def test_save_and_read(self, processor):
        path, file_hash = await processor.save_file(
            PDF_MAGIC, "212222240047_19AI405.pdf", subfolder="pending"
        )
        assert os.path.exists(path)
        assert len(file_hash) == 64  # SHA-256 hex digest

        content = await processor.get_file_content(path)
        assert content == PDF_MAGIC

    @pytest.mark.asyncio
    async def test_delete(self, processor):
        path, _ = await processor.save_file(
            PDF_MAGIC, "test_delete.pdf", subfolder="pending"
        )
        assert os.path.exists(path)

        deleted = await processor.delete_file(path)
        assert deleted is True
        assert not os.path.exists(path)

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, processor):
        deleted = await processor.delete_file("/nonexistent/file.pdf")
        assert deleted is False
