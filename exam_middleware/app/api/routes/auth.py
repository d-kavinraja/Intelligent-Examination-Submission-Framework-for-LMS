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

async def _resolve_pending_mappings(successful_tokens_by_url: dict) -> None:
    """
    Background task: resolve any SubjectMappings that have a cmid stored
    but no moodle_assignment_id yet (i.e., staff created the mapping before
    any student had logged in). Called after a student login succeeds.

    Runs as a fire-and-forget asyncio task so it doesn't delay the login response.
    """
    from app.db.database import async_session_maker
    from app.db.models import SubjectMapping
    from app.services.moodle_client import MoodleClient, MoodleAPIError

    logger.info("[resolve_mappings] Checking for unresolved subject mappings…")
    try:
        async with async_session_maker() as db:
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

            # Group unresolved by target_site_url so we can batch calls per LMS
            by_url = {}
            for m in unresolved:
                url = m.target_site_url or settings.moodle_base_url
                if url not in by_url:
                    by_url[url] = []
                by_url[url].append(m)
            
            resolved_count = 0
            
            for url, mappings in by_url.items():
                if url not in successful_tokens_by_url:
                    logger.warning(f"[resolve_mappings] No token available for {url}, skipping {len(mappings)} mappings")
                    continue
                
                token = successful_tokens_by_url[url]
                client = MoodleClient(base_url=url, token=token, timeout=30.0)
                try:
                    site_info = await client.get_site_info(token=token)
                    user_id = site_info.get("userid")
                    if not user_id:
                        logger.error(f"[resolve_mappings] Could not determine student user_id from token for {url}.")
                        continue
                        
                    courses_data = await client.get_user_courses(user_id)
                    courses = courses_data.get("courses", [])
                    if not courses:
                        logger.warning(f"[resolve_mappings] Student has no enrolled courses on {url} — cannot resolve.")
                        continue
                        
                    course_ids = [c["id"] for c in courses]
                    assignments_data = await client.get_assignments(course_ids)
                    
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
                                
                    for mapping in mappings:
                        info = cmid_map.get(mapping.cmid)
                        if info:
                            mapping.moodle_assignment_id = info["assignment_id"]
                            mapping.moodle_assignment_name = info["assignment_name"]
                            mapping.moodle_course_id = info["course_id"]
                            mapping.resolved_at = datetime.utcnow()
                            resolved_count += 1
                            logger.info(
                                f"[resolve_mappings] Resolved {mapping.subject_code} ({mapping.exam_type}): "
                                f"cmid={mapping.cmid} → assignment_id={info['assignment_id']} ({info['assignment_name']}) on {url}"
                            )
                        else:
                            logger.warning(
                                f"[resolve_mappings] cmid={mapping.cmid} not found in student's enrolled courses "
                                f"for {mapping.subject_code} ({mapping.exam_type}) on {url}"
                            )
                except MoodleAPIError as e:
                    logger.warning(f"[resolve_mappings] Moodle API error for {url}: {e}")
                finally:
                    await client.close()
            
            if resolved_count:
                await db.commit()
                logger.info(f"[resolve_mappings] Committed {resolved_count} resolved mapping(s).")
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
    """
    # Generate session ID and expiry upfront
    session_id = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=1440)  # 24-hour session
    
    try:
        logger.info(f"Student login attempt: {credentials.username} with reg_no: {credentials.register_number}")
        # Step 1: Base Authentication and get user info
        base_url_candidates = []
        configured_base_url = settings.moodle_base_url.rstrip("/")
        base_url_candidates.append(configured_base_url)
        if configured_base_url != "http://localhost":
            base_url_candidates.append("http://localhost")

        base_url = None
        base_token = None
        base_site_info = None
        last_base_error = None

        for candidate_base_url in base_url_candidates:
            base_client = MoodleClient(base_url=candidate_base_url)
            logger.info(f"Authenticating with Base LMS: {candidate_base_url}")
            try:
                resp = await base_client.get_token(credentials.username, credentials.password)
                base_token = resp["token"]
                base_site_info = await base_client.get_site_info(token=base_token)
                base_url = candidate_base_url
                logger.info(f"Base LMS token acquired successfully from {candidate_base_url}.")
                logger.info(f"Base site info retrieved. UserId: {base_site_info.get('userid')}")
                break
            except Exception as e:
                last_base_error = e
                logger.warning(f"Base LMS login failed for {candidate_base_url}: {e}")
            finally:
                await base_client.close()

        if not base_token or not base_site_info or not base_url:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication with Base LMS failed: {last_base_error}"
            )


        primary_user_id = base_site_info["userid"]
        primary_username = base_site_info["username"]
        primary_fullname = base_site_info.get("fullname", "")
        
        # Use the existing db session (don't create a new one - avoids connection pool exhaustion)
        logger.info(f"Checking StudentUsernameRegister mapping for {primary_username}...")
        # Validate mapping between Moodle username and provided register number
        result_map = await db.execute(
            select(StudentUsernameRegister).where(StudentUsernameRegister.moodle_username == primary_username)
        )
        mapping = result_map.scalar_one_or_none()
        
        if mapping is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please register your Moodle username first. Use /auth/student/register-mapping endpoint."
            )
        if mapping.register_number != credentials.register_number:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Register number does not match the account. Access denied."
            )

        # Identify Pending Papers dynamically
        artifact_service = ArtifactService(db)
        pending_papers = await artifact_service.get_pending_for_student(
            register_number=credentials.register_number,
            moodle_user_id=primary_user_id,
            moodle_username=primary_username
        )
            
        # Load mappings to find target URLs
        from app.db.models import SubjectMapping
        subject_codes = list({p.parsed_subject_code for p in pending_papers if p.parsed_subject_code})
        
        url_to_subjects = {base_url: set(["DEFAULT"])}
        if subject_codes:
            result_mappings = await db.execute(
                select(SubjectMapping).where(SubjectMapping.subject_code.in_(subject_codes))
            )
            db_mappings = result_mappings.scalars().all()
            for m in db_mappings:
                target_url = m.target_site_url or base_url
                if target_url not in url_to_subjects:
                    url_to_subjects[target_url] = set()
                url_to_subjects[target_url].add(m.subject_code)
                
        # Target cross-site auth
        async def _login_portal(url):
            if url == base_url:
                return url, base_token, base_site_info
            
            portal_client = MoodleClient(base_url=url)
            try:
                # Add overall timeout (increased to 30 seconds for slow remote Moodle servers)
                async with asyncio.timeout(30.0):
                    resp = await portal_client.get_token(credentials.username, credentials.password)
                    site_info = await portal_client.get_site_info(token=resp["token"])
                await portal_client.close()
                return url, resp["token"], site_info
            except Exception as e:
                logger.warning(f"Login failed for target url {url}: {e}")
                await portal_client.close()
                return url, None, None
                
        # Authenticate with targets in parallel
        urls_to_auth = list(url_to_subjects.keys())
        tasks = [_login_portal(url) for url in urls_to_auth]
        results = await asyncio.gather(*tasks)
        
        encrypted_tokens_dict = {}
        moodle_user_ids_dict = {}
        successful_tokens_by_url = {}
        
        for url, url_token, url_site_info in results:
            if url_token and url_site_info:
                enc = token_encryption.encrypt(url_token)
                successful_tokens_by_url[url] = url_token
                # Associate the token and userid to every subject_code hosted on this url
                if url in url_to_subjects:
                    for subj in url_to_subjects[url]:
                        encrypted_tokens_dict[subj] = enc
                        moodle_user_ids_dict[subj] = url_site_info["userid"]
        new_session = StudentSession(
            session_id=session_id,
            moodle_user_id=primary_user_id,
            moodle_user_ids=moodle_user_ids_dict,
            moodle_username=primary_username,
            moodle_fullname=primary_fullname,
            register_number=credentials.register_number,
            encrypted_token=token_encryption.encrypt(base_token),
            encrypted_tokens=encrypted_tokens_dict,
            ip_address=request.client.host if request.client else None,
            expires_at=expires_at
        )
        db.add(new_session)
        await db.commit()
        
        # Start background task to resolve mappings if needed
        asyncio.create_task(_resolve_pending_mappings(successful_tokens_by_url))

        return StudentLoginResponse(
            success=True,
            session_id=session_id,
            moodle_user_id=primary_user_id,
            moodle_username=primary_username,
            full_name=primary_fullname,
            expires_at=expires_at,
            pending_submissions=len(pending_papers)
        )


    except asyncio.TimeoutError:
        logger.error("Database or portal authentication TIMED OUT")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Request timed out. Please try again."
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in student_login: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


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
        
    except MoodleAPIError as e:
        logger.warning(f"Moodle authentication failed for {credentials.username}: {e}")
        if "Cannot connect" in e.message:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=e.message
            )
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


def get_decrypted_token(session: StudentSession, subject_code: str = None) -> str:
    """
    Decrypt the Moodle token from session.
    If subject_code is given, gets the specific portal token.
    Otherwise returns the DEFAULT token.
    """
    if getattr(session, "encrypted_tokens", None):
        enc_token = None
        if subject_code:
            enc_token = session.encrypted_tokens.get(subject_code)
            # Fallback to lms_registry for backwards compatibility
            if not enc_token:
                from app.core.lms_registry import get_lms_prefix
                prefix = get_lms_prefix(subject_code)
                enc_token = session.encrypted_tokens.get(prefix)
                
        if not enc_token:
            enc_token = session.encrypted_tokens.get("DEFAULT")
            
        if not enc_token and session.encrypted_tokens:
             enc_token = list(session.encrypted_tokens.values())[0]
             
        if enc_token:
             return token_encryption.decrypt(enc_token)
             
    # Legacy fallback
    if getattr(session, "encrypted_token", None) and session.encrypted_token:
        return token_encryption.decrypt(session.encrypted_token)
        
    return ""


def get_moodle_user_id(session: StudentSession, subject_code: str = None) -> int:
    """
    Get the Moodle User ID for the specific portal based on subject code.
    """
    if getattr(session, "moodle_user_ids", None):
        uid = None
        if subject_code:
            uid = session.moodle_user_ids.get(subject_code)
            if not uid:
                from app.core.lms_registry import get_lms_prefix
                prefix = get_lms_prefix(subject_code)
                uid = session.moodle_user_ids.get(prefix)
                
        if not uid:
            uid = session.moodle_user_ids.get("DEFAULT")
            
        if not uid and session.moodle_user_ids:
             uid = list(session.moodle_user_ids.values())[0]
             
        if uid:
             return int(uid)
             
    return getattr(session, "moodle_user_id", 0)


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
