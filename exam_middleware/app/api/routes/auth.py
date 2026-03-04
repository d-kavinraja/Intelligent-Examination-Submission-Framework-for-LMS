"""
Authentication API Routes
Handles staff and student authentication
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta, timezone
import asyncio
import logging
import secrets

from app.db.database import get_db
from app.db.models import StaffUser, StudentSession
from app.db.models import StudentUsernameRegister
from app.schemas import (
    StaffLoginRequest,
    StaffLoginResponse,
    StudentLoginRequest,
    StudentLoginResponse,
    ErrorResponse,
)
from app.core.security import (
    create_access_token,
    decode_access_token,
    verify_password,
    get_password_hash,
    token_encryption,
)
from app.core.config import settings
from app.services.moodle_client import MoodleClient, MoodleAPIError
from app.services.artifact_service import ArtifactService

logger = logging.getLogger(__name__)

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/staff/login")


# ============================================
# Staff Authentication
# ============================================

@router.post("/staff/login", response_model=StaffLoginResponse)
async def staff_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Staff login endpoint
    
    Returns JWT token for accessing staff-only endpoints
    """
    # Find staff user
    result = await db.execute(
        select(StaffUser).where(StaffUser.username == form_data.username)
    )
    staff = result.scalar_one_or_none()
    
    if not staff or not verify_password(form_data.password, staff.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not staff.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )
    
    # Update last login
    staff.last_login_at = datetime.now(timezone.utc)
    await db.commit()
    
    # Create access token
    access_token = create_access_token(
        data={
            "sub": str(staff.id),
            "username": staff.username,
            "type": "staff",
            "role": staff.role
        }
    )
    
    return StaffLoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        staff_id=staff.id,
        username=staff.username,
        role=staff.role
    )


async def get_current_staff(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> StaffUser:
    """
    Dependency to get current authenticated staff user
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    if payload.get("type") != "staff":
        raise credentials_exception
    
    staff_id = payload.get("sub")
    if staff_id is None:
        raise credentials_exception
    
    result = await db.execute(
        select(StaffUser).where(StaffUser.id == int(staff_id))
    )
    staff = result.scalar_one_or_none()
    
    if staff is None:
        raise credentials_exception
    
    if not staff.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )
    
    return staff


@router.post("/staff/register", response_model=dict)
async def register_staff(
    username: str,
    password: str,
    email: str,
    full_name: str = None,
    db: AsyncSession = Depends(get_db),
    current_staff: StaffUser = Depends(get_current_staff)
):
    """
    Register a new staff user (admin only)
    """
    # Only admins can create new staff accounts
    if current_staff.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can register new staff accounts"
        )
    # Check if username exists
    result = await db.execute(
        select(StaffUser).where(StaffUser.username == username)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Create staff user
    staff = StaffUser(
        username=username,
        email=email,
        hashed_password=get_password_hash(password),
        full_name=full_name,
        role="staff",
        is_active=True
    )
    
    db.add(staff)
    await db.commit()
    await db.refresh(staff)
    
    return {"message": "Staff user created", "staff_id": staff.id}


# ============================================
# Helper: auto-resolve unresolved subject mappings
# ============================================

async def _resolve_pending_mappings(moodle_token: str) -> None:
    """
    Background task: resolve any SubjectMappings that have a cmid stored
    but no moodle_assignment_id yet (i.e., staff created the mapping before
    any student had logged in).  Called after a student login succeeds.

    Uses the student's own Moodle token (no admin token required).
    Runs as a fire-and-forget asyncio task so it doesn't delay the login response.
    """
    from app.db.database import async_session_maker
    from app.db.models import SubjectMapping
    from app.services.moodle_client import MoodleClient, MoodleAPIError

    logger.info("[resolve_mappings] Checking for unresolved subject mappings…")
    try:
        async with async_session_maker() as db:
            # Find all mappings that have a cmid but no resolved assignment_id
            result = await db.execute(
                select(SubjectMapping).where(
                    SubjectMapping.cmid.isnot(None),
                    SubjectMapping.moodle_assignment_id.is_(None),
                    SubjectMapping.is_active == True,
                )
            )
            unresolved = result.scalars().all()

            if not unresolved:
                logger.info("[resolve_mappings] No unresolved mappings found.")
                return

            logger.info(f"[resolve_mappings] Found {len(unresolved)} unresolved mapping(s).")

            client = MoodleClient(token=moodle_token)
            try:
                # Get user_id from site_info, then fetch enrolled courses
                site_info = await client.get_site_info(token=moodle_token)
                user_id = site_info.get("userid")
                
                if not user_id:
                    logger.error("[resolve_mappings] Could not determine student user_id from token.")
                    return

                # Get enrolled courses using the student's token
                courses_data = await client.get_user_courses(user_id)
                courses = courses_data.get("courses", [])

                if not courses:
                    logger.warning("[resolve_mappings] Student has no enrolled courses — cannot resolve.")
                    return

                course_ids = [c["id"] for c in courses]
                assignments_data = await client.get_assignments(course_ids)

                # Build a cmid → (assignment_id, assignment_name, course_id) lookup map
                cmid_map: dict = {}
                for course_data in assignments_data.get("courses", []):
                    c_id = course_data.get("id")
                    for assignment in course_data.get("assignments", []):
                        a_cmid = assignment.get("cmid")
                        if a_cmid is not None:
                            cmid_map[a_cmid] = {
                                "assignment_id": assignment["id"],
                                "assignment_name": assignment.get("name", ""),
                                "course_id": c_id,
                            }

                # Resolve each unresolved mapping
                resolved_count = 0
                for mapping in unresolved:
                    info = cmid_map.get(mapping.cmid)
                    if info:
                        mapping.moodle_assignment_id = info["assignment_id"]
                        mapping.moodle_assignment_name = info["assignment_name"]
                        mapping.moodle_course_id = info["course_id"]
                        mapping.resolved_at = datetime.utcnow()
                        resolved_count += 1
                        logger.info(
                            f"[resolve_mappings] Resolved {mapping.subject_code} ({mapping.exam_type}): "
                            f"cmid={mapping.cmid} → assignment_id={info['assignment_id']} ({info['assignment_name']})"
                        )
                    else:
                        logger.warning(
                            f"[resolve_mappings] cmid={mapping.cmid} not found in student's enrolled courses "
                            f"for {mapping.subject_code} ({mapping.exam_type})"
                        )

                if resolved_count:
                    await db.commit()
                    logger.info(f"[resolve_mappings] Committed {resolved_count} resolved mapping(s).")

            except MoodleAPIError as e:
                logger.warning(f"[resolve_mappings] Moodle API error: {e}")
            finally:
                await client.close()

    except Exception as e:
        logger.error(f"[resolve_mappings] Unexpected error: {e}", exc_info=True)


# ============================================
# Student Authentication (via Moodle)
# ============================================

@router.post("/student/login", response_model=StudentLoginResponse)
async def student_login(
    credentials: StudentLoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Student login using Moodle credentials
    
    This endpoint:
    1. Authenticates with Moodle to get a web service token
    2. Gets user information from Moodle
    3. Creates a local session
    4. Returns session information and pending papers
    
    NOTE: First time users must register their mapping via /auth/student/register-mapping
    """
    client = MoodleClient()
    
    try:
        # Step 1: Get Moodle token
        logger.info(f"Authenticating student: {credentials.username}")
        
        token_response = await client.get_token(
            username=credentials.username,
            password=credentials.password
        )
        
        moodle_token = token_response["token"]
        
        # Step 2: Get user info
        site_info = await client.get_site_info(token=moodle_token)
        
        moodle_user_id = site_info["userid"]
        moodle_username = site_info["username"]
        moodle_fullname = site_info.get("fullname", "")
        
        # Step 3: Validate mapping between Moodle username and provided register number
        # Look up mapping table to ensure the Moodle account is allowed to claim the provided register number
        result_map = await db.execute(
            select(StudentUsernameRegister).where(StudentUsernameRegister.moodle_username == moodle_username)
        )
        mapping = result_map.scalar_one_or_none()
        if mapping is None:
            # No explicit mapping found; guide user to register mapping first
            logger.warning(f"Login denied: no username->register mapping for {moodle_username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please register your Moodle username first. Use /auth/student/register-mapping endpoint."
            )

        if mapping.register_number != credentials.register_number:
            logger.warning(f"Login denied: register mismatch for {moodle_username} (provided {credentials.register_number} expected {mapping.register_number})")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Register number does not match the account. Access denied."
            )

        # Step 4: Create session
        session_id = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
        
        # Encrypt the token for storage
        encrypted_token = token_encryption.encrypt(moodle_token)
        
        # Store session with register number
        session = StudentSession(
            session_id=session_id,
            moodle_user_id=moodle_user_id,
            moodle_username=moodle_username,
            moodle_fullname=moodle_fullname,
            register_number=credentials.register_number,  # Store the provided register number
            encrypted_token=encrypted_token,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent", "")[:500],
            expires_at=expires_at
        )
        
        db.add(session)
        await db.commit()

        # Fire-and-forget: resolve any cmid-only subject mappings in the background
        # using this student's Moodle token — doesn't block the login response.
        asyncio.create_task(_resolve_pending_mappings(moodle_token))

        # Step 4: Get pending papers count
        artifact_service = ArtifactService(db)
        pending_papers = await artifact_service.get_pending_for_student(
            register_number=credentials.register_number,
            moodle_user_id=moodle_user_id,
            moodle_username=moodle_username
        )
        
        logger.info(f"Student {moodle_username} (reg: {credentials.register_number}) logged in. Pending papers: {len(pending_papers)}")
        
        return StudentLoginResponse(
            success=True,
            session_id=session_id,
            moodle_user_id=moodle_user_id,
            moodle_username=moodle_username,
            full_name=moodle_fullname,
            expires_at=expires_at,
            pending_submissions=len(pending_papers)
        )
        
    except MoodleAPIError as e:
        logger.warning(f"Moodle authentication failed for {credentials.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {e.message}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during student login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )
    finally:
        await client.close()


@router.post("/student/register-mapping", response_model=dict)
async def register_student_mapping(
    credentials: StudentLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Register Moodle username to register number mapping
    
    First time users must call this endpoint to create the mapping,
    then they can use the login endpoint.
    """
    client = MoodleClient()
    
    try:
        # Authenticate with Moodle to verify credentials
        logger.info(f"Registering mapping for student: {credentials.username}")
        
        token_response = await client.get_token(
            username=credentials.username,
            password=credentials.password
        )
        
        moodle_token = token_response["token"]
        
        # Get user info
        site_info = await client.get_site_info(token=moodle_token)
        
        moodle_username = site_info["username"]
        moodle_fullname = site_info.get("fullname", "")
        
        # Check if mapping already exists
        result = await db.execute(
            select(StudentUsernameRegister).where(
                StudentUsernameRegister.moodle_username == moodle_username
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            return {
                "success": True,
                "message": f"Mapping already exists for {moodle_username}",
                "register_number": existing.register_number,
                "moodle_username": existing.moodle_username
            }
        
        # Create new mapping
        mapping = StudentUsernameRegister(
            moodle_username=moodle_username,
            register_number=credentials.register_number,
            full_name=moodle_fullname,
            created_at=datetime.now(timezone.utc)
        )
        
        db.add(mapping)
        await db.commit()
        
        logger.info(f"Registered mapping: {moodle_username} -> {credentials.register_number}")
        
        return {
            "success": True,
            "message": "Mapping registered successfully",
            "register_number": credentials.register_number,
            "moodle_username": moodle_username,
            "full_name": moodle_fullname,
            "next_step": "Use /auth/student/login with the same credentials"
        }
        
        # Store session with register number
        session = StudentSession(
            session_id=session_id,
            moodle_user_id=moodle_user_id,
            moodle_username=moodle_username,
            moodle_fullname=moodle_fullname,
            register_number=credentials.register_number,  # Store the provided register number
            encrypted_token=encrypted_token,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent", "")[:500],
            expires_at=expires_at
        )
        
        db.add(session)
        await db.commit()
        
        # Step 4: Get pending papers count
        artifact_service = ArtifactService(db)
        pending_papers = await artifact_service.get_pending_for_student(
            register_number=credentials.register_number,
            moodle_user_id=moodle_user_id,
            moodle_username=moodle_username
        )
        
        logger.info(f"Student {moodle_username} (reg: {credentials.register_number}) logged in. Pending papers: {len(pending_papers)}")
        
        return StudentLoginResponse(
            success=True,
            session_id=session_id,
            moodle_user_id=moodle_user_id,
            moodle_username=moodle_username,
            full_name=moodle_fullname,
            expires_at=expires_at,
            pending_submissions=len(pending_papers)
        )
        
    except MoodleAPIError as e:
        logger.warning(f"Moodle authentication failed for {credentials.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {e.message}"
        )
    except Exception as e:
        logger.error(f"Unexpected error during register mapping: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )
    finally:
        await client.close()


async def get_current_student_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
) -> StudentSession:
    """
    Get and validate student session
    """
    result = await db.execute(
        select(StudentSession).where(StudentSession.session_id == session_id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session"
        )
    
    if session.expires_at < datetime.now(timezone.utc):
        # Clean up expired session
        await db.delete(session)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired"
        )
    
    # Update last activity
    session.last_activity_at = datetime.now(timezone.utc)
    await db.commit()
    
    return session


def get_decrypted_token(session: StudentSession) -> str:
    """
    Decrypt the Moodle token from session
    """
    return token_encryption.decrypt(session.encrypted_token)


@router.post("/student/logout")
async def student_logout(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Logout student and invalidate session
    """
    result = await db.execute(
        select(StudentSession).where(StudentSession.session_id == session_id)
    )
    session = result.scalar_one_or_none()
    
    if session:
        await db.delete(session)
        await db.commit()
    
    return {"message": "Logged out successfully"}


@router.get("/student/session/{session_id}")
async def get_session_info(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get current session information
    """
    session = await get_current_student_session(session_id, db)
    
    return {
        "session_id": session.session_id,
        "moodle_user_id": session.moodle_user_id,
        "moodle_username": session.moodle_username,
        "full_name": session.moodle_fullname,
        "expires_at": session.expires_at.isoformat(),
        "is_valid": True
    }
