# Application Architecture Analysis
## Moodle Login & Submission Without Admin Token

---

## 🏗️ System Overview

The application is a **3-tier examination submission framework** that bridges scanned papers with Moodle LMS using **student credentials instead of admin token**.

```
┌─────────────────────┐
│   SCANNED PAPERS    │  Staff uploads scanned exam papers
│   (Scanner Agent)   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  EXAMINATION SYSTEM │  AI extracts register & subject
│  (Local Middleware) │  Matches to student papers
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   STUDENT PORTAL    │  Student logs with Moodle credentials
│  (No Admin Token)   │  Submits papers directly to Moodle
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   MOODLE LMS        │  User token used for submission
│   (Moodle Server)   │
└─────────────────────┘
```

---

## 🔐 Authentication Flow (NO ADMIN TOKEN)

### **Key Principle: Student-Owned Submissions**

Instead of using an admin credential, the system uses **each student's own Moodle token** for submission.

### **Step-by-Step Login Flow**

```
1. STUDENT LOGIN
   └─ Enter: Moodle Username, Password, Register Number
   
2. AUTHENTICATE WITH MOODLE
   └─ POST /login/token.php?username=X&password=Y
   └─ Returns: Student's Personal Web Service Token
   
3. FETCH STUDENT IDENTITY
   └─ GET /webservice/rest/server.php
   └─ Function: core_webservice_get_site_info
   └─ Returns: User ID, Full Name, Username (no password needed)
   
4. VERIFY REGISTER MAPPING
   └─ Check: student_username_registers table
   └─ Validates: Username → Register Number link
   └─ Prevents: Unauthorized access to papers
   
5. CREATE SESSION
   └─ Store: Token (AES-256 encrypted)
   └─ Store: User ID, Register Number, Username
   └─ Expiry: 24 hours
   └─ Return: Session ID to student
```

### **Token Management (AES-256 Encryption)**

```python
# Code from auth.py (line 254)
encrypted_token = token_encryption.encrypt(moodle_token)

# Stored in student_sessions table
session = StudentSession(
    session_id=session_id,
    moodle_user_id=moodle_user_id,          # User's real ID
    moodle_username=moodle_username,
    register_number=credentials.register_number,
    encrypted_token=encrypted_token,        # ENCRYPTED
    ip_address=request.client.host,
    token_expires_at=token_expiry_time
)
```

---

## 📝 Submission Workflow (3-Step Process)

### **No Admin Token = Direct Student Submission**

Each step uses **student's own token**, not admin credentials:

```
STEP 1: UPLOAD TO DRAFT AREA
┌────────────────────────────────────┐
│ Function: core_files_upload        │
│ Token: Student's personal token    │
│ Endpoint: /webservice/upload.php   │
│ Input: PDF file bytes              │
│ Output: Draft Item ID              │
└────────────────────────────────────┘
                 ↓
STEP 2: LINK DRAFT TO ASSIGNMENT
┌────────────────────────────────────┐
│ Function: mod_assign_save_submission│
│ Token: Student's personal token    │
│ Endpoint: /webservice/rest/...     │
│ Input: Assignment ID + Item ID     │
│ Output: Submission ID              │
└────────────────────────────────────┘
                 ↓
STEP 3: FINALIZE SUBMISSION
┌────────────────────────────────────┐
│ Function: mod_assign_submit...     │
│ Token: Student's personal token    │
│ Endpoint: /webservice/rest/...     │
│ Input: Assignment ID               │
│ Output: Confirmation               │
└────────────────────────────────────┘
```

### **Code Location: submission_service.py (line 22)**

```python
async def submit_artifact(
    artifact_uuid: str,
    moodle_token: str,            # ← STUDENT'S TOKEN, NOT ADMIN
    moodle_user_id: int,          # ← Student's ID from Moodle
    moodle_username: str,
    register_number: str,
    lock_submission: bool=True
) -> Tuple[bool, str, Optional[Dict]]:
    """
    3-step submission:
    1. Upload to Draft Area (core_files_upload)
    2. Associate Draft (mod_assign_save_submission)
    3. Finalize Submission (mod_assign_submit_for_grading)
    """
```

---

## 🔑 Why No Admin Token Needed?

### **Traditional Approach (REJECTED)**
```
❌ Admin logs in
❌ Gets admin token
❌ Uses admin credentials to submit ALL papers
❌ All submissions appear "by admin"
❌ Difficulty tracking "who submitted what"
❌ Security issue: admin can modify any student's submission
```

### **This Application (IMPLEMENTED)**
```
✅ Student logs in with OWN credentials
✅ Gets STUDENT'S personal token
✅ Submission appears "submitted by student"
✅ Easy audit trail: UUID → Student → Register Number
✅ Secure: student can ONLY submit their own papers
✅ Moodle records real submitter, not admin
```

---

## 💾 Database Architecture

### **Key Tables for Authentication & Submission**

#### **1. student_sessions** (Temporary Token Storage)
```sql
CREATE TABLE student_sessions (
    id INTEGER PRIMARY KEY,
    session_id VARCHAR(64) UNIQUE,           -- Browser cookie/session
    
    moodle_user_id BIGINT,                   -- Student's real Moodle ID
    moodle_username VARCHAR(100),            -- Username from Moodle
    moodle_fullname VARCHAR(255),            -- Display name
    
    register_number VARCHAR(20),             -- University register number
    
    encrypted_token TEXT,                    -- AES-256 encrypted Moodle token
    token_expires_at TIMESTAMP,              -- Moodle token expiry
    
    ip_address VARCHAR(45),                  -- For audit
    user_agent VARCHAR(500),
    
    created_at TIMESTAMP,
    last_activity_at TIMESTAMP,
    expires_at TIMESTAMP                     -- Session expiry (24 hours)
);
```

#### **2. student_username_registers** (Authorization Mapping)
```sql
CREATE TABLE student_username_registers (
    id INTEGER PRIMARY KEY,
    moodle_username VARCHAR(100) UNIQUE,
    register_number VARCHAR(20),
    created_at TIMESTAMP
);
```

**Purpose**: Map Moodle username → Register number
**When Used**: During login, validate student has access to register

#### **3. examination_artifacts** (Scanned Papers)
```sql
CREATE TABLE examination_artifacts (
    ...
    parsed_reg_no VARCHAR(20),               -- Extracted register number
    parsed_subject_code VARCHAR(20),         -- Extracted subject code
    
    moodle_user_id BIGINT,                   -- Who will submit this paper
    moodle_username VARCHAR(100),
    moodle_assignment_id INTEGER,            -- Assignment in Moodle
    
    moodle_submission_id VARCHAR(100),       -- Submission ID after upload
    workflow_status ENUM,                    -- PENDING → SUBMITTED → COMPLETED
    
    auto_processed BOOLEAN,                  -- AI extracted metadata
    register_confidence INTEGER,             -- AI confidence (0-100%)
    subject_confidence INTEGER,
    ...
);
```

---

## 🔄 Complete Submission Flow (Code Walkthrough)

### **1. Student Logs In**

**Endpoint**: `POST /auth/student/login`  
**File**: `auth.py` (line 195)

```python
async def student_login(
    credentials: StudentLoginRequest,  # username, password, register_number
    request: Request,
    db: AsyncSession
):
    # Step 1: Authenticate with Moodle
    base_url = settings.get_moodle_base_url(credentials.subject_code)
    client = MoodleClient(base_url=base_url)
    
    # Get token from Moodle (NO ADMIN NEEDED)
    token_response = await client.get_token(
        username=credentials.username,      # Student's username
        password=credentials.password       # Student's password
    )
    moodle_token = token_response["token"]  # ← STUDENT'S TOKEN
    
    # Step 2: Get user info from Moodle
    site_info = await client.get_site_info(token=moodle_token)
    moodle_user_id = site_info["userid"]
    
    # Step 3: Validate username → register mapping
    mapping = await db.execute(
        select(StudentUsernameRegister)
        .where(StudentUsernameRegister.moodle_username == moodle_username)
    )
    if not mapping or mapping.register_number != credentials.register_number:
        raise HTTPException(403, "Register number mismatch")
    
    # Step 4: Create encrypted session
    encrypted_token = token_encryption.encrypt(moodle_token)
    session = StudentSession(
        session_id=secrets.token_urlsafe(32),
        moodle_user_id=moodle_user_id,
        register_number=credentials.register_number,
        encrypted_token=encrypted_token,    # AES-256
        expires_at=datetime.now() + timedelta(hours=24)
    )
    db.add(session)
    await db.commit()
    
    return {
        "session_id": session.session_id,
        "moodle_user_id": moodle_user_id,
        "pending_submissions": len(papers)
    }
```

---

### **2. Student Views Assigned Papers**

**Endpoint**: `GET /student/dashboard`  
**File**: `student.py` (line ~400)

```python
@router.get("/dashboard")
async def get_dashboard(
    session: StudentSession = Depends(get_student_session),  # ← FROM SESSION
    db: AsyncSession = Depends(get_db)
):
    # Get papers for this student's register number
    artifact_service = ArtifactService(db)
    papers = await artifact_service.get_pending_for_student(
        register_number=session.register_number,      # ← AUTHENTICATED
        moodle_user_id=session.moodle_user_id,
        moodle_username=session.moodle_username
    )
    
    return {
        "papers": [
            {
                "artifact_uuid": paper.artifact_uuid,
                "register_number": paper.parsed_reg_no,
                "subject_code": paper.parsed_subject_code,
                "filename": paper.original_filename,
                "status": paper.workflow_status.value,
                "register_confidence": paper.register_confidence,
                "subject_confidence": paper.subject_confidence
            } for paper in papers
        ]
    }
```

---

### **3. Student Submits Paper**

**Endpoint**: `POST /student/submit/{artifact_uuid}`  
**File**: `student.py` (line 584)

```python
@router.post("/submit/{artifact_uuid}", response_model=SubmissionResponse)
async def submit_paper_by_uuid(
    artifact_uuid: str,
    request: Request,
    session: StudentSession = Depends(get_student_session),
    db: AsyncSession = Depends(get_db)
):
    # Decrypt student's Moodle token
    moodle_token = get_decrypted_token(session)  # ← DECRYPT FROM SESSION
    
    # Create submission service
    submission_service = SubmissionService(db)
    
    # Execute 3-step submission with STUDENT'S TOKEN
    success, message, result = await submission_service.submit_artifact(
        artifact_uuid=artifact_uuid,
        moodle_token=moodle_token,              # ← STUDENT'S TOKEN
        moodle_user_id=session.moodle_user_id,  # ← STUDENT'S ID
        moodle_username=session.moodle_username,
        register_number=session.register_number,
        actor_ip=request.client.host,
        lock_submission=True
    )
    
    if success:
        return {
            "success": True,
            "message": f"Submitted to Moodle successfully",
            "moodle_submission_id": result.get("submission_id")
        }
```

---

### **4. Internal 3-Step Submission Process**

**File**: `submission_service.py` (line ~150)

```python
async def _execute_submission(
    self,
    artifact: ExaminationArtifact,
    assignment_id: int,
    moodle_token: str,                 # ← STUDENT'S TOKEN
    base_url: str,
    lock_submission: bool
) -> Dict[str, Any]:
    
    client = MoodleClient(base_url=base_url)
    
    # ╔═══════════════════════════════════════════════════════════╗
    # ║ STEP 1: UPLOAD FILE TO DRAFT AREA                        ║
    # ╚═══════════════════════════════════════════════════════════╝
    draft_item_id = await client.upload_file(
        file_path=artifact.file_blob_path,
        token=moodle_token  # ← STUDENT UPLOADS
    )
    
    # ╔═══════════════════════════════════════════════════════════╗
    # ║ STEP 2: LINK DRAFT TO ASSIGNMENT SUBMISSION              ║
    # ╚═══════════════════════════════════════════════════════════╝
    save_result = await client.save_submission(
        assignment_id=assignment_id,
        item_id=draft_item_id,
        token=moodle_token  # ← STUDENT LINKS
    )
    
    # ╔═══════════════════════════════════════════════════════════╗
    # ║ STEP 3: FINALIZE SUBMISSION (LOCK FROM EDITING)          ║
    # ╚═══════════════════════════════════════════════════════════╝
    if lock_submission:
        submit_result = await client.submit_for_grading(
            assignment_id=assignment_id,
            token=moodle_token  # ← STUDENT FINALIZES
        )
    
    # Update artifact status
    artifact.workflow_status = WorkflowStatus.SUBMITTED_TO_LMS
    artifact.moodle_submission_id = draft_item_id
    artifact.submit_timestamp = datetime.now(timezone.utc)
    await db.commit()
    
    return {
        "success": True,
        "draft_item_id": draft_item_id,
        "submission_status": submit_result
    }
```

---

## 🎯 Key Security Features

### **1. Token Encryption (AES-256)**
```python
# From security.py
class TokenEncryption:
    def encrypt(self, token: str) -> str:
        # Converts plain token to encrypted blob
        # Stored in database as base64 string
        return base64.urlsafe_b64encode(
            cipher.encrypt(token.encode())
        ).decode()
    
    def decrypt(self, encrypted: str) -> str:
        # Decrypted only when needed for submission
        # Never exposed in logs or responses
        return cipher.decrypt(
            base64.urlsafe_b64decode(encrypted)
        ).decode()
```

### **2. Authentication Mapping**
```
Moodle Username → Register Number

student001 → 212223210001  ✅ CAN ACCESS
student002 → 212223210002  ✅ CAN ACCESS
student001 → 212223210050  ❌ REJECTED (mismatch)
```

### **3. Session Isolation**
- Each session has unique 32-char random ID
- Token encrypted and stored securely
- Session expires after 24 hours
- Last activity tracking for abuse detection

### **4. File Validation**
- Only PDFs allowed (mime-type checked)
- File size limits enforced
- Hash verification for integrity
- Original filename preserved for audit

### **5. Audit Trail**
```sql
-- Complete submission history
SELECT 
    artifact_uuid,
    moodle_username,          -- WHO submitted
    moodle_user_id,           -- WHICH student ID
    register_number,          -- WHICH register
    submit_timestamp,         -- WHEN
    workflow_status,          -- RESULT
    transaction_log           -- FULL DETAILS
FROM examination_artifacts
WHERE workflow_status = 'SUBMITTED_TO_LMS'
```

---

## 📊 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                       STUDENT BROWSER                           │
│                                                                 │
│  1. Login Form                                                  │
│     └─> username, password, register_number                    │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │  POST /auth/student/login  │
        └────────┬───────────────────┘
                 │
                 ▼
    ┌─────────────────────────────────────┐
    │   MIDDLEWARE (localhost:8000)       │
    │                                     │
    │  Forwards credentials to Moodle    │
    │  Receives token + user info        │
    │  Encrypts token (AES-256)          │
    │  Creates session (24h expiry)      │
    │  Returns: session_id               │
    └─────────────────────────────────────┘
                 │
                 ▼
    ┌─────────────────────────────────────┐
    │   MOODLE LMS (lms.ai.saveetha.in)   │
    │                                     │
    │  /login/token.php                  │
    │  └─> Returns: student_token        │
    │  /webservice/rest/server.php       │
    │  └─> Returns: user_id, fullname    │
    └─────────────────────────────────────┘
                 │
                 ▼
    ┌─────────────────────────────────────┐
    │  DATABASE (student_sessions)        │
    │                                     │
    │  session_id: xyz123...              │
    │  moodle_user_id: 5674               │
    │  register_number: 212223210001      │
    │  encrypted_token: AeS...BASE64...   │
    │  expires_at: 2026-03-03 23:30       │
    └─────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────────────┐
│             STUDENT SUBMITS PAPER (3-STEP)                      │
│                                                                  │
│  POST /student/submit/{artifact_uuid}                           │
│                                                                  │
│  1. Decrypt session token                                       │
│  2. Upload to Moodle draft (core_files_upload)                 │
│  3. Link draft to assignment (mod_assign_save_submission)      │
│  4. Finalize submission (mod_assign_submit_for_grading)        │
│                                                                  │
│  = All using STUDENT'S TOKEN (not admin)                        │
└──────────────────────────────────────────────────────────────────┘
```

---

## 📈 Advantages of Student Token Approach

| Feature | With Admin Token | With Student Token (This App) |
|---------|-----------------|-------------------------------|
| **Submission Owner** | Admin (incorrect) | Student (correct) ✅ |
| **Audit Trail** | "All by admin" | "Each by student" ✅ |
| **Security** | Admin compromise = all papers exposed | Limited to one student ✅ |
| **Moodle Recording** | Admin in logs | Real student in logs ✅ |
| **Plagiarism Detection** | Harder to track | Clear per-student ✅ |
| **Re-submission** | Admin must submit again | Student can resubmit ✅ |
| **Scalability** | One token for all | Distributed per student ✅ |

---

## 🚀 Current Implementation Status

✅ **Completed**:
- Student login via Moodle credentials
- Token encryption (AES-256)
- Session management (24h expiry)
- 3-step submission workflow
- Register number mapping & validation
- Complete audit trail
- Error handling & recovery
- Moodle API integration

⚠️ **In Progress**:
- Database migration for confidence scores
- Staff portal enhancements
- Confidence badge display (93.8%, 100%)
- Logging Unicode fix (Windows cp1252 issue)

🔄 **Optional Enhancements**:
- Token refresh without re-login
- Bulk submission API
- Mobile app integration
- Admin override capability (for troubleshooting)

---

## 🔗 Related Files

| Component | File Path |
|-----------|-----------|
| **Auth Flow** | `exam_middleware/app/api/routes/auth.py` |
| **Moodle Client** |`exam_middleware/app/services/moodle_client.py` |
| **Submission Logic** | `exam_middleware/app/services/submission_service.py` |
| **Student Routes** | `exam_middleware/app/api/routes/student.py` |
| **Session Model** | `exam_middleware/app/db/models.py` (StudentSession) |
| **Token Encryption** | `exam_middleware/app/core/security.py` |
| **Config** | `exam_middleware/app/core/config.py` |
| **Student Portal UI** | `exam_middleware/app/templates/student_portal.html` |

---

## 📞 Support

**Issue**: Token not working?  
→ Check: `student_sessions.expires_at > NOW()`  
→ Check: `encrypted_token` is not NULL

**Issue**: Registration mismatch?  
→ Check: `student_username_registers` table for mapping  
→ Ensure: Username lowercase matches Moodle  

**Issue**: Submission stuck?  
→ Check: `examination_artifacts.workflow_status`  
→ Check: Moodle assignment accessible by student

---

**Architecture Version**: 1.0  
**Last Updated**: March 2, 2026  
**Framework**: FastAPI + SQLAlchemy + Moodle REST API
