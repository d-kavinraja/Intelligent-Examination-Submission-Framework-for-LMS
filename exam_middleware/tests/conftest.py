"""
Shared test fixtures and configuration for the exam_middleware test suite.

Stubs out heavy app infrastructure (database engine, ORM models) so that
unit tests can import individual services without needing asyncpg or a
running PostgreSQL instance.
"""

import os
import sys
import types

import pytest

# ---------------------------------------------------------------------------
# Project root on sys.path
# ---------------------------------------------------------------------------
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# ---------------------------------------------------------------------------
# Stub out heavy packages BEFORE any app module is loaded.
#
# Import chain that causes problems:
#   app.__init__ → app.main → app.db.database (creates async engine → asyncpg)
#   app.services.__init__ → artifact_service → app.db.models → app.db.database
#
# We pre-create lightweight stubs for:
#   app, app.db, app.db.database, app.db.models, app.main
# ---------------------------------------------------------------------------

def _stub_module(name, path=None, attrs=None):
    """Register a stub module in sys.modules if not already present."""
    if name not in sys.modules:
        mod = types.ModuleType(name)
        if path:
            mod.__path__ = [path]
        mod.__package__ = name.rsplit(".", 1)[0] if "." in name else name
        if attrs:
            for k, v in attrs.items():
                setattr(mod, k, v)
        sys.modules[name] = mod
    return sys.modules[name]


# Base stub that SQLAlchemy models inherit from
class _FakeBase:
    """Minimal stub to stand in for SQLAlchemy declarative Base."""
    __tablename__ = None
    metadata = type("meta", (), {"create_all": lambda *a, **kw: None})()


_stub_module("app", path=os.path.join(_project_root, "app"))
_stub_module("app.db", path=os.path.join(_project_root, "app", "db"))
_stub_module("app.db.database", attrs={
    "Base": _FakeBase,
    "engine": None,
    "async_session_maker": None,
    "get_db": None,
    "init_db": None,
    "close_db": None,
})
# app.main — prevent full FastAPI app creation
_stub_module("app.main", attrs={"app": None})


# ---------------------------------------------------------------------------
# Dummy file content fixtures
# ---------------------------------------------------------------------------

PDF_MAGIC = b"%PDF-1.4 fake pdf content for testing"
JPEG_MAGIC = b"\xff\xd8\xff\xe0fake jpeg content for testing"
PNG_MAGIC = b"\x89PNG\r\n\x1a\nfake png content for testing"
INVALID_CONTENT = b"this is not a valid file format"


@pytest.fixture
def pdf_content():
    return PDF_MAGIC

@pytest.fixture
def jpeg_content():
    return JPEG_MAGIC

@pytest.fixture
def png_content():
    return PNG_MAGIC

@pytest.fixture
def invalid_content():
    return INVALID_CONTENT
