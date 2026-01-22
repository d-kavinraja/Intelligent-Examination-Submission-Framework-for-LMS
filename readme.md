<div align="center">

# Smart Answer Sheet Processor for LMS

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
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker"/>
  <img src="https://img.shields.io/badge/Redis-Supported-DC382D?style=for-the-badge&logo=redis&logoColor=white" alt="Redis"/>
  <img src="https://img.shields.io/badge/Celery-Background_Tasks-37814A?style=for-the-badge&logo=celery&logoColor=white" alt="Celery"/>
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
- [Docker Deployment](#docker-deployment)
- [Access Points](#access-points)
- [File Naming Convention](#file-naming-convention)
- [Authentication](#authentication)
- [API Documentation](#api-documentation)
- [Moodle Configuration](#moodle-configuration)
- [Project Structure](#project-structure)
- [Testing](#testing)
- [Workflow](#workflow)
- [Security Features](#security-features)
- [Background Tasks](#background-tasks)
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
- **Student Portal** - Students verify and submit their own papers
- **Moodle Integration** - Direct submission to assignment modules
- **Audit Trail** - Complete chain of custody logging

</td>
<td width="50%">

### Security & Reliability
- **JWT Authentication** - Secure staff access
- **AES-256 Encryption** - Protected Moodle token storage
- **Idempotent Operations** - Safe re-uploads with transaction IDs
- **Submission Queue** - Handles Moodle downtime gracefully
- **File Validation** - Hash verification & format checks

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
2. **Scanning** - Exam cell scans papers using naming convention: `{RegisterNo}_{SubjectCode}.pdf`

</details>

<details>
<summary><b>Phase 2: Staff Operations</b></summary>

1. **Login** - Staff authenticates via JWT
2. **Bulk Upload** - Drag and drop folders of scanned files
3. **Validation** - System validates filenames, hashes files, stores as `PENDING`

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
    end
    
    subgraph "Processing Layer"
        B -->|Parse & Validate| C[PostgreSQL]
        C -->|Queue Failed| D[Submission Queue]
        E[Celery Workers] -->|Retry| D
    end
    
    subgraph "Output Layer"
        F[Student Portal] -->|Fetch Papers| C
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
| **Cache/Queue** | Redis 7+ | Session cache & task queue |
| **Task Queue** | Celery + Flower | Background job processing |
| **Containerization** | Docker + Compose | Production deployment |
| **Security** | bcrypt + Fernet | Password hashing & encryption |

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
<summary><b>View Detailed Schema (information_schema.columns)</b></summary>

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

When you run `python init_db.py`, it executes SQLAlchemy's `Base.metadata.create_all()` which creates the database tables defined in `app/db/models.py`. On PostgreSQL, the necessary sequences for integer primary keys are created automatically.

The `init_db.py` script seeds minimal configuration:
- Default admin user (username: `admin`, password: `admin123`)
- Subject mappings (configurable)
- System config settings

**Optional Sample Data**: If you run with the `--seed-samples` flag, it will also add a sample artifact and `report_issue` audit log useful for local testing.

```bash
# Basic initialization
python init_db.py

# With sample data for testing
python init_db.py --seed-samples
```

**Tables and Sequences Created**:

Below is the full list of tables and sequences that should be present after running `init_db.py`:

```
public | audit_logs                       | table    | postgres
public | audit_logs_id_seq                | sequence | postgres
public | examination_artifacts            | table    | postgres
public | examination_artifacts_id_seq     | sequence | postgres
public | staff_users                      | table    | postgres
public | staff_users_id_seq               | sequence | postgres
public | student_sessions                 | table    | postgres
public | student_sessions_id_seq          | sequence | postgres
public | student_username_register        | table    | postgres
public | student_username_register_id_seq | sequence | postgres
public | subject_mappings                 | table    | postgres
public | subject_mappings_id_seq          | sequence | postgres
public | submission_queue                 | table    | postgres
public | submission_queue_id_seq          | sequence | postgres
public | system_config                    | table    | postgres
public | system_config_id_seq             | sequence | postgres
```

**Troubleshooting**: If any tables are missing after running `init_db.py`:
- Ensure your `DATABASE_URL` is set and points to the correct database
- Confirm the DB user has privileges to create tables in the `public` schema
- Check `init_db.py` output for errors and fix any import or connection issues before re-running

**Production Note**: For production deployments, we strongly recommend using Alembic for schema migrations instead of `create_all()` so you can evolve the schema safely across releases.

---

## Prerequisites

| Requirement | Version | Notes |
|:------------|:--------|:------|
| **Python** | 3.10+ | Required |
| **PostgreSQL** | 14+ | Primary database |
| **Moodle LMS** | 3.9+ | With Web Services enabled |
| **Redis** | 7+ | Optional - for background tasks |
| **Docker** | 20.10+ | Optional - for containerized deployment |

---

## Maintenance Scripts

The project includes utility scripts for managing database mappings:

### setup_username_reg.py

Upsert a single Moodle `username -> register_number` mapping. Useful to seed or correct mappings used during student login and pending-list authorization.

**Usage:**

```bash
# Interactive mode
python setup_username_reg.py

# Direct mode
python setup_username_reg.py --username 22007928 --register 212222240047
```

**Purpose**: This script maintains the `student_username_register` table which validates that a Moodle account is allowed to assert a particular register number during login.

### setup_subject_mapping.py

Interactive workflow to find an assignment by course-module-id (CMID) in Moodle, create or update a `SubjectMapping`, and optionally fix existing artifacts that reference the wrong assignment id.

**Usage:**

```bash
# Interactive mode with guided prompts
python setup_subject_mapping.py
```

**Features**:
- Search for assignments by CMID in Moodle
- Create new subject code to assignment mappings
- Update existing mappings
- Automatically fix artifacts with incorrect assignment references

---

## Quick Start

### Step 1: Clone and Navigate

```bash
git clone https://github.com/yourusername/Smart-answer-sheet-processor-for-LMS.git
cd exam_middleware
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
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
# Copy example configuration
copy .env.example .env   # Windows
cp .env.example .env     # Linux/macOS
```

Edit `.env` with your settings:

```env
# Database Configuration
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/exam_middleware

# Security Keys (CHANGE IN PRODUCTION!)
SECRET_KEY=your-super-secret-key-change-in-production
ENCRYPTION_KEY=your-32-byte-encryption-key-here

# Moodle Configuration
MOODLE_BASE_URL=https://your-moodle-site.com
MOODLE_ADMIN_TOKEN=your-admin-token
MOODLE_SERVICE=moodle_mobile_app

# File Storage
UPLOAD_DIR=./uploads
MAX_FILE_SIZE_MB=50
ALLOWED_EXTENSIONS=.pdf,.jpg,.jpeg,.png

# Redis (Optional)
REDIS_URL=redis://localhost:6379/0
```

### Step 5: Setup Database

```bash
# Create PostgreSQL database
psql -U postgres -c "CREATE DATABASE exam_middleware;"

# Initialize tables and seed data
python init_db.py

# Optional: Add sample data for testing
python init_db.py --seed-samples
```

### Step 6: Run the Application

```bash
# Development mode with hot-reload
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Or use the run script
python run.py
```

### Step 7: Verify Installation

Open your browser and navigate to:
- **Health Check**: http://localhost:8000/health
- **API Docs**: http://localhost:8000/docs

---

## Docker Deployment

### Quick Docker Start

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop all services
docker-compose down
```

### Docker Services

| Service | Port | Description |
|:--------|:-----|:------------|
| `app` | 8000 | Main FastAPI application |
| `postgres` | 5432 | PostgreSQL database |
| `redis` | 6379 | Redis cache/queue |
| `celery_worker` | - | Background task worker |
| `flower` | 5555 | Celery task monitoring |

### Docker Environment Variables

```bash
# Create .env file for Docker
POSTGRES_USER=exam_user
POSTGRES_PASSWORD=exam_password
POSTGRES_DB=exam_middleware
SECRET_KEY=your-production-secret-key
ENVIRONMENT=production
```

---

## Access Points

| Portal | URL | Description |
|:-------|:----|:------------|
| **Staff Portal** | http://localhost:8000/portal/staff | Upload scanned papers |
| **Student Portal** | http://localhost:8000/portal/student | View and submit papers |
| **Swagger UI** | http://localhost:8000/docs | Interactive API documentation |
| **ReDoc** | http://localhost:8000/redoc | Alternative API docs |
| **Health Check** | http://localhost:8000/health | System status endpoint |

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
| **Token Expiry** | 8 hours (480 minutes) |
| **Refresh** | Re-login required |

```bash
# Login request
curl -X POST http://localhost:8000/auth/staff/login \
  -F "username=admin" \
  -F "password=admin123"
```

### Student Authentication

| Aspect | Details |
|:-------|:--------|
| **Method** | Moodle Token Exchange |
| **Credentials** | University Moodle login |
| **Token Storage** | AES-256 encrypted |
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
| `GET` | `/admin/queue` | View submission queue | Staff |
| `GET` | `/admin/stats` | System statistics | Staff |
| `GET` | `/admin/audit-logs` | View audit trail | Staff |

---

## Moodle Configuration

### Required Moodle Setup

Follow these steps to configure Moodle for integration:

**1. Enable Web Services**

- Navigate to: `Site administration` → `Advanced features`
- Check **Enable web services**
- Save changes

**2. Create External Service**

- Navigate to: `Site administration` → `Server` → `Web services` → `External services`
- Click **Add**
- Configure the service:
  - **Name**: `FileUpload`
  - **Short name**: `fileupload`
  - **Enabled**: Yes
- Add required functions:
  - `core_webservice_get_site_info`
  - `mod_assign_save_submission`
  - `mod_assign_submit_for_grading`
  - `core_user_get_users_by_field`

**3. Create Token**

- Navigate to: `Site administration` → `Server` → `Web services` → `Manage tokens`
- Click **Add**
- Select admin user and the **FileUpload** service
- Copy the generated token to your `.env` file as `MOODLE_ADMIN_TOKEN`

**4. Enable Upload**

- Ensure `webservice/upload.php` is accessible on your Moodle instance
- Configure maximum upload file size in Moodle settings to match or exceed your middleware setting (default: 50MB)
- Path: `Site administration` → `Security` → `Site security settings` → **Maximum uploaded file size**

---

## Project Structure

```
exam_middleware/
├── app/
│   ├── api/
│   │   └── routes/
│   │       ├── admin.py          # Admin endpoints
│   │       ├── auth.py           # Authentication
│   │       ├── health.py         # Health check
│   │       ├── student.py        # Student endpoints
│   │       └── upload.py         # File upload
│   ├── core/
│   │   ├── config.py             # Pydantic settings
│   │   └── security.py           # JWT & encryption
│   ├── db/
│   │   ├── database.py           # Async connection
│   │   └── models.py             # SQLAlchemy models
│   ├── schemas/
│   │   └── schemas.py            # Pydantic schemas
│   ├── services/
│   │   ├── artifact_service.py   # Artifact CRUD
│   │   ├── file_processor.py     # File handling
│   │   ├── moodle_client.py      # Moodle API
│   │   └── submission_service.py # Submit logic
│   ├── templates/
│   │   ├── staff_upload.html     # Staff UI
│   │   └── student_portal.html   # Student UI
│   ├── static/
│   │   └── css/
│   │       └── style.css         # Styles
│   └── main.py                   # FastAPI app
├── uploads/                      # Upload staging
│   ├── pending/
│   ├── processed/
│   ├── failed/
│   └── temp/
├── storage/                      # Permanent storage
├── migrations/                   # Alembic migrations
├── scripts/                      # Utility scripts
├── docker-compose.yml            # Docker config
├── Dockerfile                    # Container build
├── init_db.py                    # DB initialization
├── run.py                        # App runner
├── requirements.txt              # Dependencies
├── setup_username_reg.py         # Username mapping
└── setup_subject_mapping.py      # Subject mapping
```

---

## Testing

### Manual Testing Steps

**1. Create test files** with correct naming:
```
611221104088_19AI405.pdf
611221104089_ML.pdf
```

**2. Login to Staff Portal** (`admin`/`admin123`)

**3. Upload test files** via drag-and-drop

**4. Login to Student Portal** with Moodle credentials

**5. View and submit papers** to Moodle

### API Testing with cURL

```bash
# Staff Login
curl -X POST http://localhost:8000/auth/staff/login \
  -F "username=admin" \
  -F "password=admin123"

# Upload File (use token from login)
curl -X POST http://localhost:8000/upload/single \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@611221104088_19AI405.pdf"

# Health Check
curl http://localhost:8000/health

# Get Statistics
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/admin/stats
```

### Pytest

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_upload.py -v
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

    Note over Staff,Moodle: Phase 1: Upload
    Staff->>Middleware: Upload scanned papers
    Middleware->>Middleware: Parse filename
    Middleware->>Middleware: Calculate SHA-256 hash
    Middleware->>Database: Store artifact (PENDING)
    Middleware-->>Staff: Upload success

    Note over Staff,Moodle: Phase 2: Student Review
    Student->>Middleware: Login (Moodle creds)
    Middleware->>Moodle: Verify credentials
    Moodle-->>Middleware: Token
    Middleware->>Database: Fetch pending papers
    Database-->>Middleware: Papers list
    Middleware-->>Student: Dashboard

    Note over Staff,Moodle: Phase 3: Submission
    Student->>Middleware: Submit paper
    Middleware->>Moodle: Upload to draft area
    Middleware->>Moodle: Save submission
    Middleware->>Moodle: Submit for grading
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
| **Audit Logging** | JSONB | All actions logged with IP |
| **CORS** | Configurable | Whitelist trusted origins |
| **Idempotency** | Transaction ID | Prevents duplicate submissions |

---

## Background Tasks

### Celery Setup (Production)

```bash
# Start Redis
redis-server

# Start Celery worker
celery -A app.core.celery_app worker --loglevel=info

# Start Flower monitoring (optional)
celery -A app.core.celery_app flower --port=5555
```

### Background Tasks

| Task | Description | Schedule |
|:-----|:------------|:---------|
| `retry_failed_submissions` | Retry queued submissions | Every 5 min |
| `cleanup_expired_sessions` | Remove old sessions | Every hour |
| `generate_reports` | Create audit reports | Daily |

---

## Monitoring

### Health Endpoint

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "moodle": "reachable",
  "version": "1.0.0"
}
```

### Monitoring Points

| Resource | Location | Purpose |
|:---------|:---------|:--------|
| **App Logs** | `exam_middleware.log` | Application events |
| **Audit Table** | `audit_logs` | Complete action history |
| **Flower** | `http://localhost:5555` | Celery task monitoring |
| **Prometheus** | `/metrics` | Performance metrics |

---

## Troubleshooting

<details>
<summary><b>Database Connection Error</b></summary>

**Symptoms**: `ConnectionRefusedError` or `OperationalError`

**Solutions**:
1. Verify PostgreSQL is running:
   ```bash
   # Windows
   pg_isready -h localhost -p 5432
   
   # Check service
   Get-Service postgresql*
   ```
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

**Symptoms**: Upload returns error or hangs

**Solutions**:
1. Check file size (max 50MB default)
2. Verify filename format: `{12digits}_{subject}.{ext}`
3. Check disk space in `uploads/` directory
4. Review logs: `tail -f exam_middleware.log`

</details>

<details>
<summary><b>JWT Token Invalid</b></summary>

**Symptoms**: `401 Unauthorized` after login

**Solutions**:
1. Token may be expired (8 hours default)
2. Re-login to get fresh token
3. Verify `SECRET_KEY` hasn't changed
4. Check clock sync between client/server

</details>

<details>
<summary><b>Duplicate Transaction ID</b></summary>

**Symptoms**: `IntegrityError` on upload

**Solutions**:
1. Clear transaction_id on archived artifacts:
   ```sql
   UPDATE examination_artifacts 
   SET transaction_id = NULL 
   WHERE workflow_status = 'DELETED';
   ```
2. Or delete the conflicting artifact via admin panel

</details>

---

## Recent Updates

### Version 1.2.0 (2026-01-12)

#### New Maintenance Scripts

- **`setup_username_reg.py`** - Manage Moodle username → register number mappings
  ```bash
  # Interactive mode
  python setup_username_reg.py
  
  # Direct mode
  python setup_username_reg.py --username 22007928 --register 212222240047
  ```

- **`setup_subject_mapping.py`** - Configure subject to Moodle assignment mappings

#### Staff UI Improvements

- Reports modal (view/resolve/edit/delete reports)
- Improved file listing with accurate counts
- Hardened client-side session management

#### Backend Enhancements

- Explicit `IntegrityError` handling with safe rollback
- Stricter identity validation in `get_pending_for_student()`
- Transaction ID collision remediation support

---

## Contributing

We welcome contributions! Please follow these steps:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Code Style

- Follow PEP 8 for Python code
- Use type hints for all functions
- Write docstrings for public APIs
- Add tests for new features

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
