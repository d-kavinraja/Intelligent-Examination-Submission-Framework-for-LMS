# LOCAL DEPLOYMENT GUIDE
## Exam Submission Middleware - Saveetha College Edition

This guide explains how to run the Exam Submission Middleware **locally** on your machine, connected to your college's Moodle instance at `lms.ai.saveetha.in`.

---

## 📋 Prerequisites

### System Requirements
- **OS**: Windows 10+, macOS 10.14+, or Linux (Ubuntu 18.04+)
- **Python**: 3.10 or higher
- **RAM**: 8GB minimum (16GB recommended for ML model inference)
- **Disk**: 5GB free space (includes models directory)
- **Network**: Access to `lms.ai.saveetha.in` from your machine

### Software Requirements
- **Git**: For cloning the repository
- **PostgreSQL**: 12+ (local database)
- **Redis**: 6.0+ (optional for session management)
- **Poppler**: Required for PDF processing (see installation below)

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Clone Repository

```bash
git clone https://github.com/your-username/Intelligent-Examination-Submission-Framework-for-LMS.git
cd Intelligent-Examination-Submission-Framework-for-LMS/exam_middleware
```

### Step 2: Create Python Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Note**: This includes PyTorch and YOLO for local model inference. First install may take 5-10 minutes.

### Step 4: Setup Database

```bash
# Create PostgreSQL database
createdb exam_middleware

# Or using PostgreSQL admin tool:
# CREATE DATABASE exam_middleware;
```

### Step 5: Configure Environment

Copy the template and edit for your setup:

```bash
cp .env.local .env
# Edit .env and set your Moodle credentials
```

### Step 6: Initialize Database

```bash
python init_db.py
```

This creates all necessary tables.

### Step 7: Start the Application

```bash
python run.py
```

You should see:

```
============================================================
  Examination Middleware - Starting Server
============================================================

  Port:           8000
  Mode:           Development
  Staff Portal:   /portal/staff
  Student Portal: /portal/student
  API Docs:       /docs
  Health Check:   /health

============================================================
```

### Step 8: Access the Application

Open your browser and navigate to:

- **Staff Portal**: http://localhost:8000/portal/staff
- **Student Portal**: http://localhost:8000/portal/student
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## 🔧 Detailed Configuration

### Database Setup

#### Option 1: PostgreSQL (Recommended)

**Windows:**

```bash
# Install PostgreSQL 14+ from https://www.postgresql.org/download/windows/
# During installation, remember the password you set

# Then create database:
createdb -U postgres exam_middleware

# Set password (when prompted):
psql -U postgres -c "ALTER USER postgres PASSWORD 'your_password';"
```

**macOS (with Homebrew):**

```bash
brew install postgresql
brew services start postgresql
createdb exam_middleware
```

**Linux (Ubuntu):**

```bash
sudo apt-get install postgresql postgresql-contrib
sudo -u postgres createdb exam_middleware
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'postgres';"
```

#### Option 2: SQLite (Simpler, but not for production)

If you want a quick test without PostgreSQL:

```bash
# Edit config.py:
# database_url = "sqlite:///exam_middleware.db"
python init_db.py
```

### Moodle Configuration

#### 1. Register Mobile App Service

Your Moodle instance needs to allow the "Moodle Mobile app" web service.

1. Log in to `lms.ai.saveetha.in` as an **administrator**
2. Go to **Site Administration** → **Development** → **Web Services** → **Manage Tokens**
3. Check that **"Moodle mobile app"** service is enabled

#### 2. Student Token Generation

Students need their own Moodle web service tokens:

1. Each student logs into `lms.ai.saveetha.in`
2. **Security** → **User Account** → **Manage Tokens**
3. Create a token for "Moodle mobile app" service
4. Copy the token (they'll use this to submit papers in your app)

#### 3. (OPTIONAL) Admin Token Setup

Admin token is **optional** and only needed for:
- Automatic email notifications when papers are uploaded
- Auto-lookup of student emails from Moodle

**To set up admin token:**

1. Log in to `lms.ai.saveetha.in` as **administrator**
2. Go to **Administration** → **Development** → **Web Services** → **Manage Tokens**
3. Add token for admin user for "Moodle mobile app" service
4. In `.env`, set: `MOODLE_ADMIN_TOKEN=<your-admin-token>`

If you don't set admin token, the app works fine - students just manually provide their own tokens.

### Subject-to-Assignment Mapping

Before students can submit, you need to tell the system which Moodle assignments correspond to which subjects.

#### Option 1: Manual SQL Setup

```sql
-- Run these in PostgreSQL
INSERT INTO subject_mappings (subject_code, subject_name, moodle_course_id, moodle_assignment_id, exam_session, is_active)
VALUES 
  ('19AI405', 'Data Structures', 3, 12, '2025-2026', true),
  ('19AI411', 'Machine Learning', 3, 15, '2025-2026', true);
```

To find assignment IDs, look at the Moodle URL:
- Go to assignment in Moodle
- URL will be like: `https://lms.ai.saveetha.in/mod/assign/view.php?id=15`
- The `id=15` is your assignment ID

#### Option 2: Admin API Setup (if admin token configured)

```bash
curl -X POST http://localhost:8000/api/admin/subject-mapping \
  -H "Content-Type: application/json" \
  -d '{
    "subject_code": "19AI405",
    "cmid": 15,
    "subject_name": "Data Structures",
    "exam_session": "2025-2026"
  }'
```

---

## 📦 ML Model Details

The application uses two ML models locally:

### Models Included

Location: `exam_middleware/models/`

| Model | Purpose | File Size |
|-------|---------|-----------|
| **improved_weights.pt** | YOLO detection | ~200MB |
| **best_crnn_model(git).pth** | Register number recognition | ~50MB |
| **best_subject_model_final.pth** | Subject code recognition | ~50MB |

### On First Run

The first time you upload a paper, the models will be loaded:

1. App downloads/initializes models (one-time)
2. GPU/CPU checks available (uses GPU if available)
3. Model inference runs (~2-5 seconds per document)

**If models are missing:**

- Models should be in `exam_middleware/models/`
- Download from: [Model Release URL]
- Or run with `HF_SPACE_URL` configured for remote inference

### Performance Notes

| Setup | Speed | GPU Required |
|-------|-------|--------------|
| CPU (8-core) | 5-10 sec/page | No |
| GPU (CUDA) | 1-2 sec/page | Yes (NVIDIA) |
| GPU (MPS) | 2-3 sec/page | Yes (Apple Silicon) |

For best experience, ensure:
- PyTorch can find your GPU: `python -c "import torch; print(torch.cuda.is_available())"`
- RAM available (models + other processes)

---

## 📚 Running the Application

### Development Mode (with auto-reload)

```bash
python run.py
```

The app will reload when you modify source files.

### Production Mode

```bash
SET DEBUG=false
python run.py
```

Or:

```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000
```

---

## 👥 User Roles & Setup

### Staff Portal (Admin)

**URL**: http://localhost:8000/portal/staff

**Default Credentials**:
- Username: `admin`
- Password: `admin123`

**After login, you can:**
1. Upload bulk papers (PDF or images)
2. View uploaded papers
3. See student submission status
4. Check processing logs

**Change password** (important!):
```bash
python setup_username_reg.py
```

### Student Portal

**URL**: http://localhost:8000/portal/student

**Students need:**
1. Moodle username (from college Moodle)
2. Moodle password
3. Register number (12 digits)
4. Moodle token (generated in Moodle settings)

**Student workflow:**
1. Login with credentials
2. View papers assigned to them
3. Click "Submit" to send to Moodle
4. View submission confirmation

---

## 🧪 Testing the System

### 1. Upload Test Paper

```bash
# Staff Portal → Upload
# Select any PDF file with filename format: {REGISTER}_{SUBJECT}.pdf
# Example: 212223240065_19AI405.pdf
```

### 2. Test Extraction

```bash
curl -F "file=@test_paper.pdf" http://localhost:8000/api/extract/extract
```

Response:
```json
{
  "success": true,
  "register_number": "212223240065",
  "register_confidence": 0.95,
  "subject_code": "19AI405",
  "subject_confidence": 0.92,
  "suggested_filename": "212223240065_19AI405.pdf"
}
```

### 3. Check Health

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "extraction": "local",
  "models_loaded": true,
  "database": "connected"
}
```

---

## 🐛 Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'torch'"

**Solution:**

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

For GPU (NVIDIA):
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

For Apple Silicon:
```bash
pip install torch torchvision
```

---

### Issue: "Database connection refused"

**Check PostgreSQL is running:**

```bash
# Windows
sqlcmd -S localhost -U postgres -Q "SELECT 1"

# macOS/Linux
psql -U postgres -c "SELECT 1;"
```

**If not running:**
```bash
# Windows - Use Services app to start PostgreSQL

# macOS
brew services start postgresql

# Linux
sudo systemctl start postgresql
```

---

### Issue: "Models not found" / Extraction fails

**For local models:**

1. Ensure models directory exists:
   ```bash
   ls exam_middleware/models/
   # Should show: improved_weights.pt, best_crnn_model(git).pth, best_subject_model_final.pth
   ```

2. If models are missing, download from release or use remote extraction:
   ```bash
   # In .env, set:
   # HF_SPACE_URL=https://kavinraja-ml-service.hf.space
   ```

3. Check disk space (models need ~300MB):
   ```bash
   du -sh exam_middleware/models/
   ```

---

### Issue: "Connection to lms.ai.saveetha.in failed"

1. Check internet connectivity:
   ```bash
   ping lms.ai.saveetha.in
   ```

2. Check Moodle is accessible:
   ```bash
   curl -I https://lms.ai.saveetha.in
   ```

3. Check firewall rules allow HTTPS (port 443)

4. Verify Moodle endpoints are accessible:
   ```bash
   curl https://lms.ai.saveetha.in/webservice/rest/server.php
   ```

---

### Issue: "Invalid token" errors during login

1. Double-check Moodle token is correct (copy-paste from Moodle)

2. Ensure token is for "Moodle mobile app" service:
   - Log into `lms.ai.saveetha.in`
   - Go to Security → User Account → Manage Tokens
   - Verify token is listed for "Moodle mobile app"

3. Token may have expired - regenerate in Moodle

---

## 📝 Common Tasks

### Change Staff Admin Password

```bash
python setup_username_reg.py
# Follow prompts to change password
```

### Add New Subject Mapping

```bash
python setup_subject_mapping.py
# Prompts:
# - Enter subject code: 19AI411
# - Enter assignment ID from Moodle: 15
# - (Optional) Subject name: Machine Learning
```

### Reset Database

```bash
# Delete and recreate
dropdb exam_middleware
createdb exam_middleware
python init_db.py
```

### View Application Logs

```bash
# Linux/macOS
tail -f logs/app.log

# Windows
type logs\app.log

# Or from application:
# Go to Staff Portal → Logs
```

---

## ⚙️ Advanced Configuration

### Enable Email Notifications

#### Using SendGrid (Recommended)

1. Sign up free at https://sendgrid.com
2. Create API key
3. In `.env`:
   ```
   SENDGRID_API_KEY=SG.xxxxxxxxxxxxx
   EMAIL_FROM_EMAIL=noreply@saveetha.edu.in
   EMAIL_FROM_NAME="Exam Submission"
   ```

#### Using SMTP (Gmail, Outlook, etc.)

In `.env`:
```
SMTP_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password  # Use app-specific password for Gmail
SMTP_USE_TLS=true
EMAIL_FROM_EMAIL=your-email@gmail.com
EMAIL_FROM_NAME="Exam Submission"
```

---

### Optimize for Production

Create `.env.prod`:

```bash
DEBUG=false
LOG_LEVEL=WARNING
RELOAD=false

# Use external services
DATABASE_URL=postgresql+asyncpg://...  # External Postgres
REDIS_URL=redis://...  # External Redis

# Setup SSL/Security
CORS_ORIGINS='["https://yourdomain.com"]'
```

Run with:
```bash
gunicorn -w 8 -k uvicorn.workers.UvicornWorker app.main:app \
  --bind 0.0.0.0:8000 \
  --env-file .env.prod
```

---

## 📞 Support & Troubleshooting

### Check API Health

Access the interactive API documentation at:
- `http://localhost:8000/docs` (Swagger UI)
- `http://localhost:8000/redoc` (ReDoc)

### View Database State

```bash
psql -U postgres -d exam_middleware

# Useful queries:
SELECT COUNT(*) FROM examination_artifacts;
SELECT subject_code, moodle_assignment_id FROM subject_mappings;
SELECT COUNT(*) FROM student_sessions WHERE expires_at > NOW();
```

### Check Python Dependencies

```bash
pip list
pip check  # Find conflicts
```

### Enable Debug Logging

Edit `.env`:
```
DEBUG=true
LOG_LEVEL=DEBUG
```

---

## ✅ Deployment Checklist

Before going live with students:

- [ ] Database is set up and accessible
- [ ] PostgreSQL is running
- [ ] Model files exist in `exam_middleware/models/`
- [ ] Moodle instance is accessible
- [ ] Subject mappings are configured
- [ ] Staff password is changed from default
- [ ] Email notifications are configured (if desired)
- [ ] Firewall allows connections on port 8000 (or your configured port)
- [ ] Test upload works (staff portal)
- [ ] Test extraction works (upload a scanned paper)
- [ ] Test login works with valid Moodle credentials
- [ ] Test submission works (student submits a paper)
- [ ] Backups are scheduled for database

---

## 📚 Additional Resources

- **Moodle Web Services API**: https://docs.moodle.org/dev/Web_service_API
- **YOLO Documentation**: https://docs.ultralytics.com/
- **FastAPI**: https://fastapi.tiangolo.com/
- **PostgreSQL**: https://www.postgresql.org/docs/

---

## 💾 Backing Up Your Data

### Backup Database

```bash
# PostgreSQL
pg_dump exam_middleware > backup_$(date +%Y%m%d).sql

# Restore later:
psql exam_middleware < backup_20250302.sql
```

### Backup Uploads

```bash
# Copy uploads directory
cp -r exam_middleware/uploads exam_middleware/uploads_backup_$(date +%Y%m%d)
```

---

## 🔐 Security Checklist

- [ ] Change default admin password
- [ ] Use strong `SECRET_KEY` in `.env`
- [ ] Only expose port 8000 on trusted network
- [ ] Regularly update Python packages: `pip install --upgrade -r requirements.txt`
- [ ] Enable HTTPS when exposing to internet (use reverse proxy like nginx)
- [ ] Restrict database access to localhost only
- [ ] Regular backups of database

---

## 🎉 You're Ready!

Your Exam Submission Middleware is now running locally, connected to your college's Moodle instance.

**Next steps:**

1. Add subject mappings
2. Have staff upload test papers
3. Test student submissions
4. Enable notifications if desired
5. Scale to production when ready

## Questions?

Refer to the main [README.md](../README.md) for more details or check the API docs at `/docs`.
