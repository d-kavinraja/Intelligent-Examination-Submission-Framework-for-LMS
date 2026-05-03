<div align="center">

# Intelligent Examination Submission Framework for LMS

### Examination Middleware (LMS-SAE Bridge)

<p align="center">
  <strong>An intelligent bridge between physical examination papers and Moodle LMS</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/FastAPI-0.104.1-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/PostgreSQL-14%2B-336791?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL"/>
  <img src="https://img.shields.io/badge/Moodle-LMS-F98012?style=for-the-badge&logo=moodle&logoColor=white" alt="Moodle"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Render-Deployed-46E3B7?style=for-the-badge&logo=render&logoColor=white" alt="Render"/>
  <img src="https://img.shields.io/badge/HuggingFace-ML_Inference-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black" alt="HuggingFace"/>
  <img src="https://img.shields.io/badge/License-Proprietary-red?style=for-the-badge" alt="License"/>
</p>

---

**A robust, secure, and automated middleware designed to streamline the digitization and submission of physical examination answer sheets to the Moodle Learning Management System (LMS).**

[Quick Start](#quick-start) •
[Documentation](#api-documentation) •
[Architecture](#architecture) •
[Security](#security-features) •
[Troubleshooting](#troubleshooting)

</div>

---

## Table of Contents

- [Features](#features)
- [Problem Statement](#problem-statement)
- [Solution Overview](#solution-overview)
- [Architecture](#architecture)
- [Database Schema](#database-schema)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Render Deployment](#render-deployment)
- [Access Points](#access-points)
- [File Naming Convention](#file-naming-convention)
- [Authentication](#authentication)
- [API Documentation](#api-documentation)
- [Moodle Configuration](#moodle-configuration)
- [Project Structure](#project-structure)
- [Testing](#testing)
- [Workflow](#workflow)
- [Security Features](#security-features)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)
- [Recent Updates](#recent-updates)
- [Contributing](#contributing)
- [License](#license)

---

## Codebase & Execution Flow Analysis

### Complete System Architecture Overview

This intelligent examination submission framework operates as a sophisticated multi-stage pipeline that bridges physical examination papers with a Learning Management System. The system comprises three primary layers: **Input/Ingestion Layer**, **Processing/Validation Layer**, and **Output/Submission Layer**.

#### 1. SETUP & INITIALIZATION PROCESS

The setup process initializes the complete system infrastructure:

**Environment Configuration** (`exam_middleware/app/core/config.py`):
- PostgreSQL database connection parameters
- Moodle LMS configuration (base URL, WebService endpoints, token management)
- Email service setup (SendGrid or SMTP fallback)
- ML service configuration (local YOLO+CRNN or remote HuggingFace Spaces)
- File storage paths and validation rules
- Security keys for encryption and JWT authentication

**Database Initialization** (`exam_middleware/init_db.py`):
- Creates core tables: `examination_artifacts`, `subject_mappings`, `staff_users`, `student_sessions`, `audit_logs`, `exam_submissions`
- Establishes relationships and indexes for optimal query performance
- Creates default admin user (username: `admin`, password: `admin123`)
- Seeds initial subject-to-assignment mappings
- Implements auto-migration system for schema updates (CIA exam types, attempt tracking)

**Service Dependencies**:
- FastAPI application initialization with middleware stack (CORS, GZip compression)
- Database engine creation with async connection pooling
- OAuth2 authentication scheme setup
- Router registration (auth, upload, student, admin, health)

#### 2. DATA PIPELINE & INGESTION PROCESS

The data pipeline consists of five sequential stages:

**Stage 1: File Reception** (`exam_middleware/app/api/routes/upload.py` - `upload_single_file` & `upload_bulk`):
- Staff authenticates using JWT tokens
- Files submitted through REST endpoint (`/upload/single` or `/upload/bulk`)
- Multipart form-data processing with async file streaming
- Configurable exam type tagging (CIA1, CIA2, END_SEM)

**Stage 2: Filename Parsing & Validation** (`exam_middleware/app/services/file_processor.py`):
- Regex-based pattern matching: `^(\d{12})_([A-Z0-9]{2,10})\.(pdf|jpg|jpeg|png)$`
- Register number extraction (12-digit student ID)
- Subject code parsing (flexible patterns supporting variations)
- File format validation (PDF, JPG, PNG, BMP, TIFF)
- File size constraints (default max 50MB)
- MIME type verification and sanitization

**Stage 3: File Storage & Hashing** (`exam_middleware/app/services/file_processor.py` - `save_file`):
- Async file I/O with `aiofiles` for non-blocking operations
- SHA-256 hash computation for integrity verification and deduplication
- Files organized into subdirectories: `pending/`, `processed/`, `failed/`, `temp/`
- Alternative persistent storage: File content stored in PostgreSQL BYTEA column for cloud deployment resilience
- Normalized path storage (forward slashes for cross-platform compatibility)

**Stage 4: Database Artifact Creation** (`exam_middleware/app/services/artifact_service.py` - `create_artifact`):
- Idempotent operation using transaction ID generation
- Creates `ExaminationArtifact` record with workflow status: `PENDING`
- Stores parsed metadata (register number, subject code, exam type)
- Tracks file blob path, hash, size, and MIME type
- Records uploader information for audit trail
- Initializes JSONB transaction log for state transitions

**Stage 5: Background Processing**:
- Async notification service queues student email notifications
- Audit logging records upload action with actor details (staff username, IP, timestamp)
- Optional AI extraction can be triggered (scanner agent or HF Spaces)

#### 3. CORE LOGIC & BUSINESS RULES

**Artifact Lifecycle Management** (`ExaminationArtifact` state machine):
```
PENDING 
  → PENDING_REVIEW (manual review)
  → VALIDATED (filename parsed successfully)
  → READY_FOR_REVIEW (AI extraction confidence acceptable)
  → LOCKED_BY_USER (student locks for verification)
  → UPLOADING (draft area preparation)
  → SUBMITTING (submission to Moodle in progress)
  → SUBMITTED_TO_LMS (final submission confirmed)
  → COMPLETED (grading finished)
  
Alternative paths:
  → FAILED (validation or parsing failed)
  → DELETED (removal by admin)
  → SUPERSEDED (replaced by newer attempt)
  → QUEUED (during Moodle maintenance)
```

**Multi-Attempt Handling**:
- Single `exam_type` (CIA1, CIA2, END_SEM) can have max 2 attempts per student
- Each attempt tracked with unique `attempt_number` and `attempt_2_locked` flag
- Admin controls attempt unlock via `attempt_2_locked` boolean
- Unique constraint: `(parsed_reg_no, parsed_subject_code, exam_type, attempt_number)` ensures data integrity
- Attempt 2 creation generates distinct transaction ID to bypass attempt 1 collision logic

**Subject Mapping Resolution** (`exam_middleware/app/services/artifact_service.py` - `SubjectMappingService`):
- Maps subject codes (e.g., `19AI405`) to Moodle assignment IDs
- Subject mapping configuration stored in database
- Bidirectional lookup: subject code → assignment ID → course ID
- Supports polymorphic mapping (multiple exam types per subject)

**File Persistence Strategy**:
- **Primary**: File system storage in `uploads/` directories with organized subdirectories
- **Fallback**: BYTEA (binary large object) column in PostgreSQL for cloud deployments
- **Resilience**: File lookup with intelligent path resolution across relative/absolute paths
- **Last-resort**: Filename reconstruction pattern: `{register_no}_{subject_code}.{ext}`

#### 4. MACHINE LEARNING - TRAINING & INFERENCE PIPELINE

**ML Model Architecture Overview**:

The system uses a hybrid YOLO + CRNN pipeline for optical character recognition:

**YOLO (You Only Look Once) Component**:
- Pre-trained YOLOv8 object detection model
- Detects and localizes text regions on scanned answer sheets
- Identifies register number field and subject code field
- Bounding box extraction for region-of-interest cropping
- Model weights: `exam_middleware/models/improved_weights.pt` (primary) or `weights.pt` (fallback)

**CRNN (Convolutional Recurrent Neural Network) Architecture** (`exam_middleware/app/services/extraction_service.py`):
```
Input: Grayscale image patch (height: variable, width: variable)
│
├─ CNN Feature Extraction:
│  ├─ Conv2d(1, 64) + BatchNorm2d(64) + ReLU + MaxPool2d(2,2)
│  ├─ Conv2d(64, 128) + BatchNorm2d(128) + ReLU + MaxPool2d(2,2) + Dropout(0.3)
│  ├─ Conv2d(128, 256) + BatchNorm2d(256) + ReLU
│  ├─ Conv2d(256, 256) + BatchNorm2d(256) + ReLU + MaxPool2d(2,1)
│  ├─ Conv2d(256, 512) + BatchNorm2d(512) + ReLU
│  ├─ Conv2d(512, 512) + BatchNorm2d(512) + ReLU + MaxPool2d(2,1) + Dropout(0.3)
│  └─ Conv2d(512, 512, kernel_size=2,1) + BatchNorm2d(512) + ReLU
│
├─ RNN Sequence Learning:
│  └─ LSTM(512 → 256, bidirectional=True, num_layers=2, Dropout=0.3)
│
├─ Dropout Regularization: Dropout(0.5)
│
└─ Output FC Layer: Linear(512 → num_classes)
   Output: Character-level predictions for OCR
```

**Training Configuration** (inferred from model weights):
- **Register Number CRNN**: Trained on 12-digit numeric patterns
  - Model: `exam_middleware/models/best_crnn_model(git).pth`
  - Alphabet: Digits 0-9
  - CTC loss for sequence-to-sequence learning
  
- **Subject Code CRNN**: Trained on alphanumeric patterns
  - Model: `exam_middleware/models/best_subject_model_final.pth`
  - Alphabet: Digits + Letters (A-Z)
  - Handles variable-length subject codes (2-10 characters)

**Inference Pipeline** (`exam_middleware/app/services/extraction_service.py` & `hf_space/app.py`):

1. **Local Extraction** (default mode):
   - Models loaded on application startup
   - Image preprocessing: grayscale conversion, normalization
   - YOLO detection → crops text regions
   - CRNN inference on each region
   - CTC decoding → character sequence
   - Post-processing: validation, confidence thresholding

2. **Remote Inference** (HuggingFace Spaces fallback):
   - HTTP POST to remote ML service endpoint
   - Base64 image encoding for transmission
   - Async HTTP client with configurable timeout
   - Response parsing: extracted text + confidence scores
   - Fallback to filename parsing if ML fails

**Confidence Scoring**:
- Per-character confidence tracking through softmax outputs
- Register number confidence: average of 12-digit predictions
- Subject code confidence: average of variable-length predictions
- Stored in database: `register_confidence` (0-100%), `subject_confidence` (0-100%)
- Threshold-based filtering: confidence < 60% marked for manual review

**HuggingFace Spaces Deployment** (`hf_space/app.py`):
- Independent FastAPI service for ML inference
- Identical CRNN architecture and model loading logic
- Endpoints:
  - `/extract` (POST): Submit image → receive extracted text + confidence
  - `/health` (GET): Service availability check
- Advantages: Isolates GPU computation, scales independently, free tier support

#### 5. STUDENT PORTAL - VERIFICATION & SUBMISSION FLOW

**Authentication & Session Management** (`exam_middleware/app/api/routes/auth.py`):

*Step 1: Moodle Token Exchange*:
- Student enters Moodle username and password
- System calls Moodle API: `/login/token.php`
- Receives temporary Moodle session token
- Token encrypted with Fernet (AES-256) before storage

*Step 2: Session Creation*:
- Queries Moodle: `core_webservice_get_site_info` → fetches Moodle user ID and full name
- Queries student username register: `student_username_register` table
- Extracts register number from Moodle full name (regex: `\b(\d{12})\b`)
- Creates `StudentSession` record with encrypted token
- Session timeout: configurable (default 1 hour)

*Step 3: Identity Verification*:
- Subsequent requests validated via session token decryption
- Register number cross-reference: student can only view papers tagged with their number
- Moodle credentials verified on each session renewal

**Student Dashboard** (`exam_middleware/app/api/routes/student.py` - `get_dashboard`):

*Artifact Filtering Logic*:
1. Queries `ExaminationArtifact` table filtered by `parsed_reg_no = student_register_number`
2. Includes only artifacts with `workflow_status` in submission-eligible states
3. Groups by exam type (CIA1, CIA2, END_SEM) and attempts
4. For each artifact, resolves:
   - Subject name via `SubjectMapping` table
   - Assignment information (Moodle assignment ID, course ID)
   - File availability (disk vs. database storage)

*Dashboard Response Structure*:
```json
{
  "success": true,
  "student_info": {
    "register_number": "212223240065",
    "moodle_username": "student@college",
    "full_name": "Student Name"
  },
  "papers_by_exam": {
    "CIA1": [
      {
        "artifact_uuid": "uuid-string",
        "subject_name": "Machine Learning",
        "subject_code": "19AI405",
        "exam_type": "CIA1",
        "attempt_number": 1,
        "workflow_status": "READY_FOR_REVIEW",
        "file_available": true,
        "submission_status": "not_submitted",
        "preview_url": "/student/artifact/uuid/preview",
        "submit_url": "/student/artifact/uuid/submit"
      }
    ]
  },
  "submission_summary": {
    "total_papers": 8,
    "submitted": 5,
    "pending": 3
  }
}
```

**File Preview** (`exam_middleware/app/api/routes/student.py` - `preview_artifact`):
- Resolves file path from multiple possible locations
- Streams PDF/image with appropriate MIME type
- Supports Range requests for large files
- Serves from disk if available, falls back to database BYTEA storage

**Submission Workflow** (`exam_middleware/app/services/submission_service.py` - `submit_artifact`):

*Phase 1: Pre-Submission Validation*:
- Artifact ownership verification (register number match)
- Workflow status check (must be submittable state)
- Check existing submission: query `ExamSubmission` table to prevent duplicate submissions
- Moodle assignment ID validation

*Phase 2: Draft Area Upload* (`core_files_upload`):
- Retrieves file from disk or database
- Calls Moodle API: `core_files_upload`
- Uploads to Moodle user's draft area
- Receives `moodle_draft_item_id` for next step
- Stores draft item ID for retry logic

*Phase 3: Assignment Association* (`mod_assign_save_submission`):
- Calls Moodle API with:
  - Assignment ID (from subject mapping)
  - User ID (from student session)
  - Draft item ID (from previous step)
  - Submission data (file reference)
- Moodle links file to student's assignment submission
- Receives submission confirmation

*Phase 4: Submission Finalization* (`mod_assign_submit_for_grading`):
- Calls Moodle API: `mod_assign_submit_for_grading`
- Marks submission as "Submitted" in Moodle
- Prevents student from editing submission in Moodle UI

*Phase 5: Lock Creation & Audit*:
- Creates `ExamSubmission` record with transaction ID (idempotency)
- Updates `ExaminationArtifact` status to `SUBMITTED_TO_LMS`
- Records submission timestamp and metadata
- Triggers admin lock (if token available):
  - Calls `mod_assign_set_user_flags` (locked=true)
  - Calls `mod_assign_lock_submissions` to prevent further edits
  - Best-effort: non-critical if admin token unavailable

*Phase 6: Audit & Notifications*:
- Logs submission action with actor details
- Sends confirmation email to student
- Updates submission cache for dashboard refresh

**Error Handling & Retry Logic**:
- Transactional approach: validates all steps before committing database changes
- Moodle API error handling: captures exception, errorcode, message, debuginfo
- Retry mechanism: transaction ID prevents duplicate submissions if request retried
- Graceful degradation: submission succeeds even if admin lock fails

#### 6. EVALUATION & QUALITY ASSURANCE

**Confidence Score Validation**:
- CRNN models output per-character confidence values
- Confidence calculation: average of softmax outputs across sequence
- Register number confidence: requires ≥60% for auto-accept
- Subject code confidence: requires ≥70% for auto-accept
- Below-threshold extractions marked for manual staff review

**Data Quality Metrics**:
- **Parsing Accuracy**: Regex pattern success rate on filename formats
- **Extraction Accuracy**: ML model confidence vs. manual ground truth
- **Submission Success Rate**: Artifacts successfully submitted ÷ total uploaded
- **Moodle Integration Success**: API call success rate, error frequency

**Audit Trail Verification** (`AuditLog` table):
- Every action logged: upload, validation, extraction, submission
- Immutable transaction history stored as JSONB
- Traces actor (staff/student), timestamp, IP address, action details
- Enables post-submission integrity verification

**System Health Monitoring**:
- Health check endpoint: `/health`
- Database connectivity validation
- ML service availability check
- Moodle LMS connectivity status
- File system accessibility verification

#### 7. DEPLOYMENT & PRODUCTION SETUP

**Deployment Targets**:

**Option A: Render.com (Cloud)** (recommended):
- Free tier with auto-scaling
- PostgreSQL database hosting included
- Environment variables configuration
- Render YAML specification (`render.yaml`)
- Automatic HTTPS/SSL certificates

**Option B: Local Development**:
- Direct Python execution with `python run.py`
- Local PostgreSQL instance
- Optional Redis for session management
- HuggingFace Spaces for remote ML inference

**Deployment Configuration** (`exam_middleware/run.py`):
- Port detection from environment (Render: PORT env var, local: 8000)
- Environment mode detection: Production vs. Development
- Logging configuration: stdout for production, file + stdout for development
- UTF-8 encoding enforcement for Windows compatibility
- Auto-reload disabled in production

**Scaling Considerations**:
- Async operations throughout (FastAPI + asyncpg)
- Database connection pooling for optimal resource usage
- File I/O non-blocking (aiofiles)
- HTTP calls async (httpx, aiohttp)
- Background task queue (Celery integration available)
- Horizontal scaling: Render auto-scales based on load

**Security Hardening**:
- CORS middleware restricts cross-origin requests
- GZip compression reduces bandwidth
- HTTPS enforcement in production
- JWT token expiration (configurable, default 60 minutes)
- Fernet encryption for sensitive data (Moodle tokens)
- Rate limiting available (via FastAPI extensions)
- CSRF protection for form submissions

**Database Backups**:
- Render PostgreSQL daily snapshots
- Manual export option: `exam_middleware/scripts/db/backup_render_db.sh`
- Local restoration: `exam_middleware/scripts/db/restore_snapshot_local.sh`
- Migration scripts tracked in `exam_middleware/migrations/` and `exam_middleware/scripts/`

**Monitoring & Logging**:
- Application logs: `exam_middleware.log` (local) or stdout (production)
- SQLAlchemy logging suppressed to reduce noise
- Structured logging with timestamps, levels, module names
- Error tracking with detailed context
- Moodle API integration logging with request/response details

#### 8. SCANNER AGENT - AUTOMATED INGESTION

**Purpose**: Watches local folder for scanned papers and automatically uploads to server

**Configuration** (`exam_middleware/scanner_agent.py`):
```python
SERVER_URL = "http://localhost:8000"  # Middleware server
STAFF_USERNAME = "admin"
STAFF_PASSWORD = "admin123"
WATCH_FOLDER = r"C:\Users\SEC\Downloads\SCANNED-PAPERS"
DEFAULT_EXAM_TYPE = "CIA1"
POLL_INTERVAL = 3  # seconds
FILE_STABLE_WAIT = 1  # ensure file writing complete
QUEUE_DELAY = 3  # between uploads
MAX_RETRIES = 2
```

**Workflow**:
1. Monitors WATCH_FOLDER for new files (3-second poll interval)
2. Detects file creation via modification timestamp
3. Waits for file stability (1 second no changes) before processing
4. Queues file for upload with retry logic
5. Authenticates as staff member (JWT token)
6. POSTs file to `/extract/scan-upload` endpoint
7. Verifies unique artifact UUID returned
8. Archives original file (moves to subdirectory)
9. Processes next queued file (3-second delay between uploads)

**Windows Console Optimization**:
- Disables Quick Edit mode that freezes process on mouse click
- Implements system API calls for terminal control
- Non-fatal if Windows API unavailable

---

## Features

<table>
<tr>
<td width="50%">

### Core Capabilities
- **Bulk Upload** - Staff can upload hundreds of scanned papers at once
- **Smart Parsing** - Auto-extracts Register Number & Subject Code from filenames
- **AI Extraction** - YOLO + CRNN models extract metadata from scanned answer sheets via HuggingFace Spaces
- **Student Portal** - Students verify and submit their own papers
- **Moodle Integration** - Direct submission to assignment modules
- **Automated Submission Lock** - Uses an Admin Token to instantly lock individual submissions (**does not affect other assignments**)
- **Real-time Dashboard** - Auto-refreshing stats, reports, and file listings
- **Audit Trail** - Complete chain of custody logging

</td>
<td width="50%">

### Security & Reliability
- **JWT Authentication** - Secure staff access
- **AES-256 Encryption** - Protected Moodle token & assignment password storage (Fernet)
- **Submission Finality** - `exam_submissions` table + Automated Admin Lock block re-uploads
- **Idempotent Operations** - Safe re-uploads with transaction IDs
- **Database-Backed Storage** - Self-healing file persistence for cloud deployments
- **File Validation** - Hash verification & format checks
- **Email Notifications** - SendGrid/SMTP upload alerts to students

</td>
</tr>
</table>

---

## Problem Statement

> *In academic institutions transitioning to digital grading, handling physical answer scripts presents significant logistical challenges.*

The key challenges include:

1. **Manual Labor**: Individually scanning, renaming, and uploading hundreds of answer scripts to specific Moodle assignments is time-consuming and inefficient.
2. **Human Error**: Manual processes are prone to errors such as uploading the wrong file to a student's profile or mislabeling files.
3. **Security & Integrity**: Direct database manipulation or unverified bulk uploads can compromise the chain of custody.
4. **Student Verification**: Students often lack a mechanism to verify that their specific physical paper was scanned and submitted correctly before grading begins.
5. **Post-Submission Tampering**: After submitting answer papers in the exam hall, students can log into Moodle, click "Edit submission", and upload a different answer paper — compromising exam integrity.

---

## Solution Overview

This middleware solves these issues by decoupling the **scanning/uploading** process from the **submission** process, introducing a secure validation layer.

### Core Concept

The system utilizes a **3-Step "Upload-Verify-Push" Workflow**:

1. **Bulk Ingestion**: Administrative staff upload bulk batches of scanned PDF/Images.
2. **Intelligent Processing**: The system parses filenames (e.g., `123456_MATH101.pdf`) to extract the Student Register Number and Subject Code, automatically mapping them to the correct Moodle Assignment ID.
3. **Student-Led Submission**: Students log in using their Moodle credentials. They view *only* their specific answer scripts and trigger the final submission to Moodle. This ensures non-repudiation and student verification.

### Visual Workflow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     UPLOAD      │ ──▶ │     VERIFY      │ ──▶ │     SUBMIT      │
│   Staff Portal  │     │ Student Review  │     │  To Moodle LMS  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### Workflow Phases

<details>
<summary><b>Phase 1: Administration & Setup</b></summary>

1. **Mapping Configuration** - Admin maps Subject Codes to Moodle Assignment IDs
2. **Student Mapping** - Admin maps Moodle usernames to Register Numbers
3. **Scanning** - Exam cell scans papers using naming convention: `{RegisterNo}_{SubjectCode}.pdf`

</details>

<details>
<summary><b>Phase 2: Staff Operations</b></summary>

1. **Login** - Staff authenticates via JWT
2. **Bulk Upload** - Drag and drop folders of scanned files
3. **Validation** - System validates filenames, hashes files, stores as `PENDING`
4. **Smart Scan** - Optional AI-powered auto-extraction via Scanner Agent

</details>

<details>
<summary><b>Phase 3: Student Operations</b></summary>

1. **Login** - Student uses Moodle credentials (selects Moodle domain)
2. **Dashboard** - View all papers tagged with their Register Number
3. **Review** - Preview PDF to verify it's their paper
4. **Submit** - One-click submission to Moodle
5. **Lock** - Middleware records submission in `exam_submissions` table (blocks future re-submission)
6. **Finalize** - `submit_for_grading` API call locks the Moodle submission
7. **Confirmation** - Status updates to `SUBMITTED_TO_LMS`

> **Note**: Students only see the Submit button. No passwords or admin tokens are involved. The lock is enforced server-side.

</details>

---

## Architecture

```mermaid
graph TB
    subgraph "Input Layer"
        A[Physical Scans] -->|Bulk Upload| B[Staff Portal]
        S[Scanner Agent] -->|Auto Upload| B
    end
    
    subgraph "Processing Layer"
        B -->|Parse & Validate| C[PostgreSQL]
        C -->|DB Fallback| K((File Persistence))
        H2[HF Spaces] -->|AI Extraction| B
    end
    
    subgraph "Output Layer"
        F[Student Portal] -->|Path check| L{File on Disk?}
        L -->|Yes| M[Serve from Disk]
        L -->|No| N[Serve from DB]
        F -->|Fetch Papers| C
        F -->|Submit| G[Moodle LMS]
        G -->|Token Exchange| F
    end
    
    subgraph "Security Layer"
        H[JWT Auth]
        I[Token Encryption]
        J[Audit Logs]
    end
```

### Tech Stack

| Component | Technology | Purpose |
|:----------|:-----------|:--------|
| **Web Framework** | FastAPI 0.104+ | Async REST API with auto-docs |
| **Database** | PostgreSQL 14+ | Persistent storage with JSONB |
| **Async ORM** | SQLAlchemy 2.0 | Async database operations |
| **ML Inference** | HuggingFace Spaces | Remote YOLO + CRNN extraction |
| **Deployment** | Render.com | Cloud hosting (free tier) |
| **Security** | bcrypt + Fernet | Password hashing & encryption |
| **Email** | SendGrid / SMTP | Upload notification emails |

---

## Database Schema

### Entity Relationship

```mermaid
erDiagram
    ExaminationArtifact ||--o{ AuditLog : "has"
    StaffUser ||--o{ ExaminationArtifact : "uploads"
    SubjectMapping ||--o{ ExaminationArtifact : "maps"
    ExaminationArtifact ||--o| SubmissionQueue : "queued"
    ExaminationArtifact ||--o| ExamSubmission : "locks"
    StudentSession ||--o{ ExaminationArtifact : "submits"
    StudentUsernameRegister ||--o{ StudentSession : "validates"
    
    ExaminationArtifact {
        uuid artifact_uuid PK
        string parsed_reg_no
        string parsed_subject_code
        string file_hash
        binary file_content
        enum workflow_status
        timestamp uploaded_at
    }
    
    SubjectMapping {
        int id PK
        string subject_code UK
        int moodle_assignment_id
        text assignment_password_encrypted
        boolean is_active
    }
    
    ExamSubmission {
        int id PK
        string student_id
        string subject_code
        string exam_type
        string status
        timestamp submitted_at
        timestamp locked_at
    }
    
    AuditLog {
        int id PK
        string action
        string actor_type
        jsonb request_data
        timestamp created_at
    }
```

### Database Tables

<details>
<summary><b>View Complete Table List</b></summary>

| Table | Description | Key Columns |
|:------|:------------|:------------|
| `examination_artifacts` | Core scanned paper records | `artifact_uuid`, `parsed_reg_no`, `workflow_status` |
| `subject_mappings` | Subject to Moodle mapping | `subject_code`, `moodle_assignment_id`, `assignment_password_encrypted` |
| `exam_submissions` | **Submission lock tracking** | `student_id`, `subject_code`, `exam_type`, `status` |
| `staff_users` | Staff accounts | `username`, `hashed_password`, `role` |
| `student_sessions` | Active student sessions | `session_id`, `encrypted_token` |
| `student_username_register` | Username to Register No mapping | `moodle_username`, `register_number` |
| `audit_logs` | Complete action history | `action`, `actor_type`, `created_at` |
| `submission_queue` | Failed submission retry queue | `artifact_id`, `status`, `retry_count` |
| `system_config` | Runtime configuration | `key`, `value` |

</details>

<details>
<summary><b>View Detailed Schema</b></summary>

```sql
-- examination_artifacts
artifact_uuid          | uuid                     | NOT NULL
raw_filename           | character varying        | NOT NULL
original_filename      | character varying        | NOT NULL
parsed_reg_no          | character varying        | NULL (indexed)
parsed_subject_code    | character varying        | NULL (indexed)
file_blob_path         | character varying        | NOT NULL
file_hash              | character varying(64)    | NOT NULL (SHA-256)
file_size_bytes        | bigint                   | NULL
mime_type              | character varying        | NULL
file_content           | bytea                    | NULL (DB Fallback)
moodle_user_id         | bigint                   | NULL
moodle_username        | character varying        | NULL
moodle_course_id       | integer                  | NULL
moodle_assignment_id   | integer                  | NULL
workflow_status        | enum                     | NOT NULL (PENDING, SUBMITTED_TO_LMS, etc.)
moodle_draft_item_id   | bigint                   | NULL
moodle_submission_id   | character varying        | NULL
transaction_id         | character varying(64)    | UNIQUE (idempotency key)
uploaded_at            | timestamp with time zone | DEFAULT now()
validated_at           | timestamp with time zone | NULL
submit_timestamp       | timestamp with time zone | NULL
completed_at           | timestamp with time zone | NULL
uploaded_by_staff_id   | integer                  | FK -> staff_users
submitted_by_user_id   | bigint                   | NULL (Moodle user ID)
transaction_log        | jsonb                    | NULL
error_message          | text                     | NULL
retry_count            | integer                  | DEFAULT 0
```

</details>

### Database Initialization

When you run `python init_db.py`, it creates all database tables and seeds minimal configuration:
- Default admin user (username: `admin`, password: `admin123`)
- Subject mappings (configurable)
- System config settings

```bash
# Basic initialization
python init_db.py

# With sample data for testing
python init_db.py --seed-samples
```

---

## Prerequisites

| Requirement | Version | Notes |
|:------------|:--------|:------|
| **Python** | 3.10+ | Required |
| **PostgreSQL** | 14+ | Primary database |
| **Moodle LMS** | 3.9+ | With Web Services enabled |

---

## Maintenance Scripts

### setup_username_reg.py

Manage Moodle `username → register_number` mappings:

```bash
# Interactive mode
python setup_username_reg.py

# Direct mode
python setup_username_reg.py --username 22007928 --register 212222240047
```

### setup_subject_mapping.py

Configure subject to Moodle assignment mappings:

```bash
python setup_subject_mapping.py
```

---

## Quick Start

> **NEW: Local Deployment Support!** 
> The application now runs locally on your machine with your college's Moodle instance (`lms.ai.saveetha.in`).
> No admin token required - students use their own Moodle credentials for submissions.
> 
> **→ For complete local setup guide, see: [LOCAL_DEPLOYMENT.md](exam_middleware/LOCAL_DEPLOYMENT.md)**

### Step 1: Clone and Navigate

```bash
git clone https://github.com/d-kavinraja/Intelligent-Examination-Submission-Framework-for-LMS.git
cd Intelligent-Examination-Submission-Framework-for-LMS/exam_middleware
```

### Step 2: Create Virtual Environment

```bash
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate

# Activate (Linux/macOS)
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Configure Environment

```bash
copy .env.example .env   # Windows
cp .env.example .env     # Linux/macOS
```

Edit `.env` with your settings:

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/exam_middleware

# Security (CHANGE IN PRODUCTION!)
SECRET_KEY=your-super-secret-key-change-in-production

# Moodle
MOODLE_BASE_URL=https://your-moodle-site.com
MOODLE_ADMIN_TOKEN=your-admin-token
MOODLE_SERVICE=moodle_mobile_app

# Storage
UPLOAD_DIR=./uploads
MAX_FILE_SIZE_MB=50

# AI Extraction (HuggingFace Spaces)
HF_SPACE_URL=https://kavinraja-ml-service.hf.space
```

### Step 5: Setup Database

```bash
psql -U postgres -c "CREATE DATABASE exam_middleware;"
python init_db.py
```

### Step 6: Run

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
# Or: python run.py
```

### Step 7: Verify

- **Health Check**: http://localhost:8000/health
- **API Docs**: http://localhost:8000/docs
- **Staff Portal**: http://localhost:8000/portal/staff

---

## Render Deployment

The middleware is deployed on **Render.com** with a cloud-optimized architecture.

### Deployment Strategy
Due to Render's ephemeral filesystem, this project implements a **Database-Backed Persistent Storage Fallback**:
- Files are saved to local disk for fast performance
- Simultaneously, raw file bytes are stored in PostgreSQL (`file_content` BYTEA column)
- If the local disk is wiped (e.g., during a service restart), the system automatically serves files from the database

### ML Inference Architecture
Heavy ML models (YOLO + CRNN) are offloaded to a separate **HuggingFace Spaces** service:
- **HF Space URL**: `https://kavinraja-ml-service.hf.space`
- The Render app calls this via HTTP for register number / subject code extraction
- If the HF Space is unavailable, extraction falls back to filename parsing only

### Auto-Migrations
The application automatically detects missing columns on startup and applies schema fixes without manual DDL.

---

## Access Points

### Production (Render)
| Portal | URL |
|:-------|:----|
| **Staff Portal** | [https://exam-middleware.onrender.com/portal/staff](https://exam-middleware.onrender.com/portal/staff) |
| **Student Portal** | [https://exam-middleware.onrender.com/portal/student](https://exam-middleware.onrender.com/portal/student) |
| **API Health** | [https://exam-middleware.onrender.com/health](https://exam-middleware.onrender.com/health) |
| **API Docs** | [https://exam-middleware.onrender.com/docs](https://exam-middleware.onrender.com/docs) |
| **HF ML Service** | [https://kavinraja-ml-service.hf.space](https://kavinraja-ml-service.hf.space) |

### Local Development
| Portal | URL | Description |
|:-------|:----|:------------|
| **Staff Portal** | `http://localhost:8000/portal/staff` | Upload scanned papers |
| **Student Portal** | `http://localhost:8000/portal/student` | View and submit papers |
| **Swagger UI** | `http://localhost:8000/docs` | Interactive API docs |
| **Health Check** | `http://localhost:8000/health` | System status |

---

## File Naming Convention

> **Important**: All uploaded files MUST follow this naming pattern for automatic processing.

### Pattern

```
{RegisterNumber}_{SubjectCode}.{extension}
```

### Valid Examples

| Filename | Register No | Subject Code |
|:---------|:------------|:-------------|
| `611221104088_19AI405.pdf` | 611221104088 | 19AI405 |
| `611221104089_ML.jpg` | 611221104089 | ML |
| `611221104090_19AI411.png` | 611221104090 | 19AI411 |
| `212223240065_DL.pdf` | 212223240065 | DL |

### Rules

| Field | Requirement |
|:------|:------------|
| **Register Number** | Exactly 12 digits |
| **Subject Code** | 2-10 alphanumeric characters |
| **Extension** | `.pdf`, `.jpg`, `.jpeg`, `.png` |
| **Max Size** | 50 MB (configurable) |

---

## Authentication

### Staff Authentication

| Aspect | Details |
|:-------|:--------|
| **Method** | JWT Bearer Token |
| **Default Credentials** | `admin` / `admin123` |
| **Token Expiry** | 60 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`) |
| **Refresh** | Re-login required |

### Student Authentication

| Aspect | Details |
|:-------|:--------|
| **Method** | Moodle Token Exchange |
| **Credentials** | University Moodle login |
| **Token Storage** | AES-256 encrypted (Fernet) |
| **Session Expiry** | 24 hours |

---

## API Documentation

### Authentication Endpoints

| Method | Endpoint | Description | Auth |
|:-------|:---------|:------------|:-----|
| `POST` | `/auth/staff/login` | Staff JWT login | No |
| `POST` | `/auth/student/login` | Student Moodle login | No |
| `POST` | `/auth/student/logout` | Invalidate session | Student |

### Upload Endpoints (Staff Only)

| Method | Endpoint | Description | Auth |
|:-------|:---------|:------------|:-----|
| `POST` | `/upload/single` | Upload single file | Staff |
| `POST` | `/upload/bulk` | Upload multiple files | Staff |
| `POST` | `/upload/validate` | Validate filename | Staff |
| `GET` | `/upload/all` | List all artifacts | Staff |
| `GET` | `/upload/auto-processed` | List auto-processed artifacts | Staff |

### Student Endpoints

| Method | Endpoint | Description | Auth |
|:-------|:---------|:------------|:-----|
| `GET` | `/student/dashboard` | Get assigned papers | Student |
| `GET` | `/student/paper/{id}/view` | Preview paper | Student |
| `POST` | `/student/submit/{id}` | Submit to Moodle | Student |
| `GET` | `/student/submission/{id}/status` | Check status | Student |

### Admin Endpoints

| Method | Endpoint | Description | Auth |
|:-------|:---------|:------------|:-----|
| `GET` | `/admin/mappings` | List subject mappings | Staff |
| `POST` | `/admin/mappings` | Create new mapping | Staff |
| `GET` | `/admin/audit-logs` | View audit trail | Staff |
| `GET` | `/admin/artifacts/{uuid}` | Get artifact details | Staff |
| `POST` | `/admin/artifacts/{uuid}/edit` | Edit artifact metadata | Staff |
| `DELETE` | `/admin/artifacts/{uuid}` | Delete single artifact | Staff |
| `DELETE` | `/admin/artifacts/purge-all` | Purge all artifacts | Staff |

### Extraction Endpoints (AI Pipeline)

| Method | Endpoint | Description | Auth |
|:-------|:---------|:------------|:-----|
| `GET` | `/extract/status` | Check ML model availability | No |
| `POST` | `/extract/scan-upload` | AI extract + upload single file | Staff |
| `GET` | `/extract/scan-log` | Get in-memory scan log | No |

---

## Moodle Configuration

### Required Moodle Setup

**1. Enable Web Services**
- `Site administration` → `Advanced features` → Enable web services

**2. Create External Service**
- `Site administration` → `Server` → `Web services` → `External services`
- Add service: **FileUpload** (short name: `fileupload`)
- Add functions:
  - `core_webservice_get_site_info`
  - `mod_assign_get_assignments`
  - `mod_assign_get_submission_status`
  - `mod_assign_save_submission`
  - `mod_assign_submit_for_grading`
  - `mod_assign_set_user_flags` (Required for Automated Locking)
  - `mod_assign_lock_submissions` (Required for Automated Locking)
  - `core_user_get_users_by_field`

**3. Enable Upload**
- Ensure `webservice/upload.php` is accessible
- Set max upload size >= 50MB in `Site administration` → `Security` → `Site security settings`

### Submission Lock — Automated Admin Token Method

The middleware implements a **dual-token locking mechanism** to ensure exam finality. This method is highly surgical—it **only** locks the specific exam paper submitted and **does not affect other assignments or users** in Moodle.

#### Technical Locking Workflow

The middleware orchestrates a 3-step secure submission process using two different tokens:

```mermaid
sequenceDiagram
    participant Student as Student Portal
    participant MW as Middleware (Backend)
    participant DB as Postgres DB
    participant Moodle as Moodle LMS

    Student->>MW: Click "Submit Answer Paper"
    MW->>DB: Check if already COMPLETED (Block if true)
    
    Note over MW,Moodle: [Step 1: Student Context]
    MW->>Moodle: mod_assign_save_submission (Student Token)
    MW->>Moodle: mod_assign_submit_for_grading (Student Token)
    
    Note over MW,Moodle: [Step 2: Admin/Locking Context]
    MW->>Moodle: mod_assign_lock_submissions (Admin Token)
    MW->>Moodle: mod_assign_set_user_flags [locked=1] (Admin Token)
    
    MW->>DB: Record status as COMPLETED
    MW-->>Student: Return Success & Locked Status
```

1.  **Student Identity (Student Token):** The middleware first uses the student's own Moodle token to upload the file and finalize the submission. This ensures the paper is correctly attributed to the student.
2.  **Administrative Lock (Admin Token):** Immediately after the upload, the middleware switches to the `MOODLE_ADMIN_TOKEN` (Manager/Teacher level). It makes an administrative call to Moodle to "Lock" that student's submission.
3.  **Middleware Guard:** Finally, it records the `COMPLETED` status in the local `exam_submissions` database table, providing a second layer of protection against duplicate API calls.

#### Setup Requirements:
1.  **Admin Token:** Provide a token for a user with "Manager" or "Teacher" permissions in `.env` as `MOODLE_ADMIN_TOKEN`.
2.  **Moodle Functions:** The following functions **must** be enabled in your Moodle Web Service:
    *   `mod_assign_set_user_flags`
    *   `mod_assign_lock_submissions`
    *   `mod_assign_submit_for_grading`

---

---

## Project Structure

```
Intelligent-Examination-Submission-Framework-for-LMS/
├── readme.md                     # This file
├── render.yaml                   # Render.com deployment blueprint
├── index.html                    # Landing page
├── requirements.txt              # Root dependencies
│
├── exam_middleware/               # Main application
│   ├── app/
│   │   ├── api/routes/
│   │   │   ├── admin.py          # Admin endpoints
│   │   │   ├── auth.py           # Authentication
│   │   │   ├── extract.py        # AI extraction pipeline
│   │   │   ├── health.py         # Health check
│   │   │   ├── student.py        # Student endpoints
│   │   │   └── upload.py         # File upload
│   │   ├── core/
│   │   │   ├── config.py         # Pydantic settings
│   │   │   └── security.py       # JWT & Fernet encryption
│   │   ├── db/
│   │   │   ├── database.py       # Async DB connection
│   │   │   └── models.py         # SQLAlchemy models
│   │   ├── schemas/schemas.py    # Pydantic schemas
│   │   ├── services/
│   │   │   ├── artifact_service.py        # Artifact CRUD
│   │   │   ├── extraction_service.py      # Local ML extraction
│   │   │   ├── remote_extraction_service.py # HF Spaces extraction
│   │   │   ├── file_processor.py          # File handling
│   │   │   ├── mail_service.py            # Email notifications
│   │   │   ├── moodle_client.py           # Moodle API client
│   │   │   ├── notification_service.py    # Notification orchestration
│   │   │   └── submission_service.py      # Submit logic
│   │   ├── templates/
│   │   │   ├── staff_upload.html  # Staff UI
│   │   │   └── student_portal.html # Student UI
│   │   ├── static/css/style.css   # Styles
│   │   └── main.py               # FastAPI app entry point
│   ├── uploads/                   # Upload staging
│   ├── models/                    # ML model weights (local only)
│   ├── scripts/                   # SQL migration scripts
│   ├── tests/                     # Test suite
│   ├── init_db.py                 # DB initialization
│   ├── run.py                     # App runner
│   ├── scanner_agent.py           # Ricoh scanner integration
│   ├── setup_username_reg.py      # Username mapping utility
│   ├── setup_subject_mapping.py   # Subject mapping utility
│   └── requirements.txt           # Python dependencies
│
└── hf_space/                      # HuggingFace Spaces ML service
    ├── app.py                     # FastAPI ML inference server
    └── requirements.txt           # ML dependencies (torch, ultralytics)
```

---

## Testing

### Manual Testing

1. Create test files: `611221104088_19AI405.pdf`, `611221104089_ML.pdf`
2. Login to Staff Portal (`admin`/`admin123`)
3. Upload files via drag-and-drop
4. Login to Student Portal with Moodle credentials
5. View and submit papers to Moodle

### API Testing with cURL

```bash
# Staff Login
curl -X POST http://localhost:8000/auth/staff/login \
  -F "username=admin" -F "password=admin123"

# Upload File
curl -X POST http://localhost:8000/upload/single \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@611221104088_19AI405.pdf"

# Health Check
curl http://localhost:8000/health
```

### Pytest

```bash
pytest
pytest --cov=app --cov-report=html
pytest tests/test_moodle_client.py -v
```

---

## Workflow

```mermaid
sequenceDiagram
    participant Staff
    participant Middleware
    participant Database
    participant Student
    participant Moodle
    participant HFSpace as HF Spaces

    Note over Staff,HFSpace: Phase 1: Upload
    Staff->>Middleware: Upload scanned papers
    Middleware->>Middleware: Parse filename & SHA-256 hash
    Middleware->>Database: Store artifact (PENDING) + file_content
    Middleware-->>Staff: Upload success

    Note over Staff,HFSpace: Phase 1b: Smart Scan (Optional)
    Staff->>Middleware: Smart Scan (raw image)
    Middleware->>HFSpace: Extract register no + subject
    HFSpace-->>Middleware: AI predictions
    Middleware->>Database: Store with extracted metadata

    Note over Staff,HFSpace: Phase 2: Student Review
    Student->>Middleware: Login (Moodle creds)
    Middleware->>Moodle: Verify credentials
    Moodle-->>Middleware: Token
    Middleware->>Database: Fetch pending papers
    Middleware-->>Student: Dashboard

    Note over Staff,HFSpace: Phase 3: Submission
    Student->>Middleware: Submit paper
    Middleware->>Moodle: Upload → Save → Submit for grading
    Moodle-->>Middleware: Submission ID
    Middleware->>Database: Update status (SUBMITTED)
    Middleware-->>Student: Confirmation
```

---

## Security Features

| Feature | Implementation | Details |
|:--------|:---------------|:--------|
| **Password Hashing** | bcrypt | 12 rounds, salt per password |
| **Token Encryption** | AES-256 (Fernet) | Moodle tokens encrypted at rest |
| **Assignment Password** | AES-256 (Fernet) | Encrypted before storage, never exposed in API responses |
| **Submission Lock** | `exam_submissions` table | Prevents re-submission at middleware level (no admin tokens) |
| **JWT Tokens** | python-jose | Short-lived, signed tokens |
| **File Validation** | python-magic | MIME type verification |
| **File Integrity** | SHA-256 | Hash stored for verification |
| **Audit Logging** | JSONB | All actions logged with metadata |
| **CORS** | Configurable | Whitelist trusted origins |
| **Idempotency** | Transaction ID | Prevents duplicate submissions |

---

## Monitoring

### Health Endpoint

```bash
curl http://localhost:8000/health
```

### Monitoring Points

| Resource | Location | Purpose |
|:---------|:---------|:--------|
| **App Logs** | `logs/app.log` | Application events |
| **Audit Table** | `audit_logs` | Complete action history |
| **Health Check** | `/health` | System status |
| **API Docs** | `/docs` | Swagger UI |

---

## Troubleshooting

<details>
<summary><b>Database Connection Error</b></summary>

**Symptoms**: `ConnectionRefusedError` or `OperationalError`

**Solutions**:
1. Verify PostgreSQL is running: `pg_isready -h localhost -p 5432`
2. Check `DATABASE_URL` in `.env`
3. Verify database exists: `psql -U postgres -l`

</details>

<details>
<summary><b>Moodle Token Error</b></summary>

**Symptoms**: `MoodleAPIError` or "Invalid token"

**Solutions**:
1. Regenerate token in Moodle admin
2. Verify external service is enabled
3. Check required functions are added to service
4. Test token:
   ```bash
   curl "https://your-moodle.com/webservice/rest/server.php?wstoken=YOUR_TOKEN&wsfunction=core_webservice_get_site_info&moodlewsrestformat=json"
   ```

</details>

<details>
<summary><b>File Upload Failed</b></summary>

**Solutions**:
1. Check file size (max 50MB default)
2. Verify filename format: `{12digits}_{subject}.{ext}`
3. Check disk space in `uploads/` directory
4. Review logs: `tail -f logs/app.log`

</details>

<details>
<summary><b>JWT Token Invalid</b></summary>

**Solutions**:
1. Token may be expired (60 minutes default)
2. Re-login to get fresh token
3. Verify `SECRET_KEY` hasn't changed

</details>

<details>
<summary><b>HuggingFace Space Unavailable</b></summary>

**Solutions**:
1. Check status at https://kavinraja-ml-service.hf.space/health
2. Free tier spaces sleep after inactivity — first request wakes it (30-60s delay)
3. Verify `HF_SPACE_URL` environment variable is set
4. AI extraction falls back to filename parsing when HF Space is down

</details>

---

## Recent Updates

### Version 1.5.0 (2026-04-30)

#### Submission Lock System — Prevent Post-Submission Tampering

> **No admin tokens are used.** The lock is enforced through Moodle Administration UI settings + middleware database tracking.

- **`exam_submissions` table**: New database table tracks every finalized submission. Once a student submits, any re-submission attempt is immediately blocked by the middleware — no API workaround possible.
- **`submit_for_grading` workflow**: The middleware calls Moodle's `mod_assign_submit_for_grading` to finalize the submission. Combined with Moodle assignment settings (attempts=1, click-to-submit=yes, reopened=never), students **cannot edit, delete, or re-upload** even if they log into Moodle directly.
- **Assignment Password support**: Staff can set an optional password on subject mappings. The password is encrypted (AES-256/Fernet) and stored securely. The middleware uses it transparently during submission — students never see it.
- **Staff Portal UI**: New password field with show/hide toggle in the Subject Mapping form. New Password column with lock indicator (🔒/🔓) in the mapping list.
- **Files changed**: `models.py`, `main.py`, `submission_service.py`, `schemas.py`, `admin.py`, `staff_upload.html`

### Version 1.4.0 (2026-02-28)

#### Real-time Dashboard Updates
- **Auto-refresh**: Staff portal auto-refreshes uploaded files, scan logs, and stats every 15 seconds
- **Instant feedback**: All mutation operations (upload, delete, edit, purge) immediately refresh all data views
- **Purge All simplified**: Removed double confirmation — single confirmation is sufficient
- **Manual refresh preserved**: Refresh buttons remain for immediate on-demand refresh

#### Cleanup
- **Updated documentation**: Corrected GitHub URLs, removed references to non-existent Celery/Redis/Flower services, aligned with actual application state

### Version 1.3.0 (2026-02-21)

#### Persistent Storage & Cloud Readiness
- **Database-Backed File Persistence**: Self-healing storage layer — uploads mirrored to PostgreSQL BYTEA
- **Auto-Migrations**: Automatic schema fixes on startup

#### Security & Reliability
- **Metadata Edit Content Preservation**: Fixed file content loss during manual metadata edits
- **Moodle Upload Robustness**: Direct binary uploads in `MoodleClient`

### Version 1.2.0 (2026-01-12)

- Maintenance scripts: `setup_username_reg.py`, `setup_subject_mapping.py`
- Reports modal with view/resolve/edit/delete
- Improved file listing with accurate counts
- `IntegrityError` handling with safe rollback

---

## Contributing

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

---

## License

**This project is currently not licensed for public use.**

Contact the maintainers for licensing inquiries.

---

<div align="center">

### Made for Academic Excellence

**Smart Answer Sheet Processor for LMS** © 2024-2026

[Back to Top](#smart-answer-sheet-processor-for-lms)

</div>
