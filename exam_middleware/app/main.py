"""
Examination Middleware - Main FastAPI Application

This is the main entry point for the FastAPI application that bridges
scanned examination papers with Moodle LMS for student submissions.
"""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.core.config import settings
from app.db.database import engine, Base
from app.api.routes import (
    auth_router,
    upload_router,
    student_router,
    admin_router,
    health_router,
)

# Configure logging - use stdout only in production (Render)
_is_production = os.environ.get("RENDER") or os.environ.get("DEBUG", "true").lower() == "false"
_handlers = [logging.StreamHandler()]
if not _is_production:
    try:
        Path("logs").mkdir(parents=True, exist_ok=True)
        _handlers.append(logging.FileHandler("exam_middleware.log"))
    except Exception:
        pass  # Skip file logging if not writable

logging.basicConfig(
    level=logging.DEBUG if not _is_production else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=_handlers,
)
# Set specific loggers to INFO to reduce SQLAlchemy noise
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events handler.
    Manages startup and shutdown events.
    """
    # Startup
    logger.info("Starting Examination Middleware...")
    
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
        # Auto-migration: Update for CIA types and attempts
        try:
            from sqlalchemy import text
            
            # 1. Handle examination_artifacts table
            # Check for file_content
            res = await conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='examination_artifacts' AND column_name='file_content'"))
            if not res.fetchone():
                logger.info("Adding file_content to examination_artifacts...")
                await conn.execute(text("ALTER TABLE examination_artifacts ADD COLUMN file_content BYTEA"))

            # Check for exam_type
            res = await conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='examination_artifacts' AND column_name='exam_type'"))
            if not res.fetchone():
                logger.info("Adding exam_type to examination_artifacts...")
                await conn.execute(text("ALTER TABLE examination_artifacts ADD COLUMN exam_type VARCHAR(10) NOT NULL DEFAULT 'CIA1'"))

            # Check for attempt_number
            res = await conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='examination_artifacts' AND column_name='attempt_number'"))
            if not res.fetchone():
                logger.info("Adding attempt_number to examination_artifacts...")
                await conn.execute(text("ALTER TABLE examination_artifacts ADD COLUMN attempt_number INTEGER NOT NULL DEFAULT 1"))

            # Check for attempt_2_locked
            res = await conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='examination_artifacts' AND column_name='attempt_2_locked'"))
            if not res.fetchone():
                logger.info("Adding attempt_2_locked to examination_artifacts...")
                await conn.execute(text("ALTER TABLE examination_artifacts ADD COLUMN attempt_2_locked BOOLEAN NOT NULL DEFAULT TRUE"))

            # Check for auto_processed
            res = await conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='examination_artifacts' AND column_name='auto_processed'"))
            if not res.fetchone():
                logger.info("Adding auto_processed to examination_artifacts...")
                await conn.execute(text("ALTER TABLE examination_artifacts ADD COLUMN auto_processed BOOLEAN NOT NULL DEFAULT FALSE"))
                # Create index for fast filtering
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_examination_artifacts_auto_processed ON examination_artifacts(auto_processed) WHERE auto_processed = true"))

            # 2. Handle subject_mappings table
            # Check for exam_type
            res = await conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='subject_mappings' AND column_name='exam_type'"))
            if not res.fetchone():
                logger.info("Adding exam_type to subject_mappings...")
                await conn.execute(text("ALTER TABLE subject_mappings ADD COLUMN exam_type VARCHAR(10) NOT NULL DEFAULT 'CIA1'"))

            # 3. Update Constraints
            # Drop old subject_mappings unique constraints/indices if they exist
            try:
                # SQLAlchemy often creates an index named ix_subject_mappings_subject_code
                await conn.execute(text("DROP INDEX IF EXISTS ix_subject_mappings_subject_code"))
                await conn.execute(text("ALTER TABLE subject_mappings DROP CONSTRAINT IF EXISTS subject_mappings_subject_code_key"))
                await conn.execute(text("ALTER TABLE subject_mappings DROP CONSTRAINT IF EXISTS uq_subject_code"))
                
                # Add new one if not exists
                # Check if uq_subject_exam_type already exists to avoid redundant errors
                res = await conn.execute(text("SELECT conname FROM pg_constraint WHERE conname='uq_subject_exam_type'"))
                if not res.fetchone():
                    await conn.execute(text("ALTER TABLE subject_mappings ADD CONSTRAINT uq_subject_exam_type UNIQUE (subject_code, exam_type)"))
            except Exception as ce:
                logger.debug(f"Constraint update (subject_mappings) skipped or already done: {ce}")

            # Drop old examination_artifacts unique constraints/indices
            try:
                await conn.execute(text("DROP INDEX IF EXISTS ix_examination_artifacts_parsed_reg_no"))
                await conn.execute(text("DROP INDEX IF EXISTS ix_examination_artifacts_parsed_subject_code"))
                await conn.execute(text("ALTER TABLE examination_artifacts DROP CONSTRAINT IF EXISTS examination_artifacts_parsed_reg_no_parsed_subject_code_key"))
                await conn.execute(text("ALTER TABLE examination_artifacts DROP CONSTRAINT IF EXISTS uq_paper_submission"))
                
                # Add new one if not exists
                res = await conn.execute(text("SELECT conname FROM pg_constraint WHERE conname='uq_paper_submission'"))
                if not res.fetchone():
                    await conn.execute(text("ALTER TABLE examination_artifacts ADD CONSTRAINT uq_paper_submission UNIQUE (parsed_reg_no, parsed_subject_code, exam_type, attempt_number)"))
            except Exception as ce:
                logger.debug(f"Constraint update (artifacts) skipped or already done: {ce}")

            # 4. Update Enum
            try:
                # PostgreSQL specific: check if value exists in enum
                res = await conn.execute(text("SELECT 1 FROM pg_type t JOIN pg_enum e ON t.oid = e.enumtypid WHERE t.typname = 'workflowstatus' AND e.enumlabel = 'SUPERSEDED'"))
                if not res.fetchone():
                    logger.info("Adding SUPERSEDED to workflowstatus enum...")
                    # Note: ALTER TYPE ... ADD VALUE cannot run in a transaction block in some PG versions
                    # But engine.begin() is a transaction. We try it anyway as async pg handles this usually
                    await conn.execute(text("COMMIT")) # End current transaction if needed
                    await conn.execute(text("ALTER TYPE workflowstatus ADD VALUE 'SUPERSEDED'"))
            except Exception as ee:
                logger.debug(f"Enum update skipped or failed: {ee}")

        except Exception as e:
            logger.error(f"Migration error during startup: {e}")
            
    logger.info("Database tables created/verified")
    
    # Seed default admin user if not exists
    try:
        from sqlalchemy import text
        from app.db.database import async_session_maker
        from app.db.models import StaffUser
        from app.core.security import get_password_hash, verify_password
        
        async with async_session_maker() as session:
            # Check if admin exists
            result = await session.execute(
                text("SELECT id, hashed_password FROM staff_users WHERE username = 'admin'")
            )
            row = result.fetchone()
            
            if not row:
                # Create admin user
                admin = StaffUser(
                    username="admin",
                    hashed_password=get_password_hash("admin123"),
                    full_name="Administrator",
                    email="admin@example.com",
                    role="admin",
                    is_active=True,
                )
                session.add(admin)
                await session.commit()
                logger.info("Default admin user CREATED (admin/admin123)")
            else:
                # Admin exists - verify password works, update if not
                if not verify_password("admin123", row[1]):
                    new_hash = get_password_hash("admin123")
                    await session.execute(
                        text("UPDATE staff_users SET hashed_password = :hash WHERE username = 'admin'"),
                        {"hash": new_hash}
                    )
                    await session.commit()
                    logger.info("Admin password RESET to admin123 (hash was invalid)")
                else:
                    logger.info("Admin user exists and password verified OK")
    except Exception as e:
        logger.error(f"Error seeding admin user: {e}", exc_info=True)
    
    # Ensure upload and storage directories exist
    upload_path = Path(settings.upload_dir)
    upload_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Upload directory: {upload_path.absolute()}")
    
    storage_path = Path("./storage")
    storage_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Storage directory: {storage_path.absolute()}")
    
    # Create templates directory
    templates_path = Path("app/templates")
    templates_path.mkdir(parents=True, exist_ok=True)
    
    # Create static directory
    static_path = Path("app/static")
    static_path.mkdir(parents=True, exist_ok=True)
    
    logger.info("Examination Middleware started successfully")

    # Preload AI extraction models at startup to avoid timeout on first request
    try:
        import asyncio
        from app.services.extraction_service import is_extraction_available, get_extractor
        if is_extraction_available():
            logger.info("Preloading AI extraction models (this may take ~30s)...")
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, get_extractor)
            logger.info("✓ AI extraction models loaded and ready")
        else:
            logger.warning("AI extraction models not found — skipping preload")
    except Exception as e:
        logger.warning(f"Could not preload extraction models: {e}")

    yield
    
    # Shutdown
    logger.info("Shutting down Examination Middleware...")
    await engine.dispose()
    logger.info("Database connections closed")


# Create FastAPI application
app = FastAPI(
    title="Examination Middleware",
    description="""
    ## Examination Paper Submission Middleware
    
    This API provides a secure bridge between scanned examination papers 
    and the Moodle LMS, enabling students to submit their answer sheets.
    
    ### Features:
    - **Staff Upload Portal**: Bulk upload of scanned answer sheets
    - **Student Portal**: View and submit assigned papers to Moodle
    - **Moodle Integration**: Direct submission to assignment modules
    - **Security**: JWT authentication, encrypted token storage
    - **Audit Trail**: Complete logging of all operations
    
    ### Workflow:
    1. Staff uploads scanned papers with standardized filenames
    2. System extracts student register number and subject code
    3. Students authenticate via Moodle credentials
    4. Students view their assigned papers and submit to Moodle
    5. System handles the complete submission workflow
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "An internal server error occurred",
            "detail": str(exc) if settings.debug else None,
        },
    )


# Mount static files
try:
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
except Exception:
    logger.warning("Static files directory not found, skipping mount")

# Include API routers
app.include_router(
    health_router,
    prefix="/health",
    tags=["Health"],
)

app.include_router(
    auth_router,
    prefix="/auth",
    tags=["Authentication"],
)

app.include_router(
    upload_router,
    prefix="/upload",
    tags=["Upload"],
)

app.include_router(
    student_router,
    prefix="/student",
    tags=["Student"],
)

app.include_router(
    admin_router,
    prefix="/admin",
    tags=["Administration"],
)

# Extraction (OCR) router
from app.api.routes.extract import router as extract_router
app.include_router(
    extract_router,
    prefix="/extract",
    tags=["Extraction"],
)


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint - API information.
    """
    return {
        "name": "Examination Middleware API",
        "version": "1.0.0",
        "description": "Examination Paper Submission Middleware for Moodle LMS",
        "documentation": "/docs",
        "health_check": "/health",
        "endpoints": {
            "staff_login": "/auth/staff/login",
            "student_login": "/auth/student/login",
            "upload": "/upload/single",
            "bulk_upload": "/upload/bulk",
            "student_dashboard": "/student/dashboard",
            "submit": "/student/submit/{artifact_id}",
            "admin": "/admin/mappings",
        },
    }


# Templates setup
templates = Jinja2Templates(directory="app/templates")


@app.get("/portal/staff", tags=["Portal"], include_in_schema=False)
async def staff_portal(request: Request):
    """Staff upload portal page."""
    return templates.TemplateResponse(
        "staff_upload.html",
        {"request": request, "title": "Staff Upload Portal"},
    )


@app.get("/portal/student", tags=["Portal"], include_in_schema=False)
async def student_portal(request: Request):
    """Student submission portal page."""
    return templates.TemplateResponse(
        "student_portal.html",
        {"request": request, "title": "Student Submission Portal"},
    )


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info",
    )

