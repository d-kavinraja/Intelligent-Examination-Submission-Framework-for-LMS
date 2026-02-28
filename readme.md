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
- **Real-time Dashboard** - Auto-refreshing stats, reports, and file listings
- **Audit Trail** - Complete chain of custody logging

</td>
<td width="50%">

### Security & Reliability
- **JWT Authentication** - Secure staff access
- **AES-256 Encryption** - Protected Moodle token storage (Fernet)
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

1. **Login** - Student uses Moodle credentials
2. **Dashboard** - View all papers tagged with their Register Number
3. **Review** - Preview PDF to verify it's their paper
4. **Submit** - One-click submission to Moodle
5. **Confirmation** - Status updates to `SUBMITTED_TO_LMS`

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
        boolean is_active
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
| `subject_mappings` | Subject to Moodle mapping | `subject_code`, `moodle_assignment_id` |
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
Heavy ML models (YOLO + CRNN) are **not** installed on Render. Instead, inference is offloaded to a separate **HuggingFace Spaces** service:
- **HF Space URL**: `https://kavinraja-ml-service.hf.space`
- The Render app calls this via HTTP for register number / subject code extraction
- If the HF Space is unavailable, extraction falls back to filename parsing only

### Key Deployment Files
- **`Dockerfile.render`**: Lightweight Python 3.11-slim image (no ML dependencies)
- **`render.yaml`**: Blueprint for one-click deployment including PostgreSQL

### One-Click Deploy
1. In Render, select **New → Blueprint**
2. Connect your repository
3. Render will automatically detect `render.yaml` and provision the Web Service and Managed PostgreSQL

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
  - `mod_assign_save_submission`
  - `mod_assign_submit_for_grading`
  - `core_user_get_users_by_field`

**3. Create Token**
- `Site administration` → `Server` → `Web services` → `Manage tokens`
- Create token for admin user with **FileUpload** service
- Copy token to `.env` as `MOODLE_ADMIN_TOKEN`

**4. Enable Upload**
- Ensure `webservice/upload.php` is accessible
- Set max upload size ≥ 50MB in `Site administration` → `Security` → `Site security settings`

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
│   ├── Dockerfile.render          # Render deployment container
│   ├── init_db.py                 # DB initialization
│   ├── run.py                     # App runner
│   ├── scanner_agent.py           # Ricoh scanner integration
│   ├── setup_username_reg.py      # Username mapping utility
│   ├── setup_subject_mapping.py   # Subject mapping utility
│   └── requirements.txt           # Python dependencies
│
└── hf_space/                      # HuggingFace Spaces ML service
    ├── app.py                     # FastAPI ML inference server
    ├── Dockerfile                 # HF Space container
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

### Version 1.4.0 (2026-02-28)

#### Real-time Dashboard Updates
- **Auto-refresh**: Staff portal auto-refreshes uploaded files, scan logs, and stats every 15 seconds
- **Instant feedback**: All mutation operations (upload, delete, edit, purge) immediately refresh all data views
- **Purge All simplified**: Removed double confirmation — single confirmation is sufficient
- **Manual refresh preserved**: Refresh buttons remain for immediate on-demand refresh

#### Cleanup
- **Removed unused Docker files**: `Dockerfile.prod`, `docker-compose.yml`, and `DOCKER.md` removed from exam_middleware (deployment uses `Dockerfile.render` via Render)
- **Updated documentation**: Corrected GitHub URLs, removed references to non-existent Celery/Redis/Flower services, aligned with actual application state

### Version 1.3.0 (2026-02-21)

#### Persistent Storage & Cloud Readiness
- **Database-Backed File Persistence**: Self-healing storage layer — uploads mirrored to PostgreSQL BYTEA
- **Render.com Optimization**: `render.yaml` and `Dockerfile.render` for one-click cloud deployment
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
