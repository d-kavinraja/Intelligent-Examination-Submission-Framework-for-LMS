# Render Deployment Guide

## Overview
The application is deployed on Render with ML inference offloaded to HuggingFace Spaces for reduced resource usage and cost.

## Architecture
- **Render**: FastAPI web service (~200MB Docker image)
- **PostgreSQL**: Exam database on Render
- **HuggingFace Spaces**: ML inference service for extraction (`https://kavinraja-ml-service.hf.space`)

## Deployment Steps

### 1. Initial Setup (First Time)
1. Connect your Git repository to Render
2. Create a PostgreSQL database
3. Configure environment variables in `render.yaml`:
   - `DATABASE_URL` (auto-generated from database)
   - `HF_SPACE_URL=https://kavinraja-ml-service.hf.space`
   - `SECRET_KEY` (auto-generated)
   - Other Moodle/config variables

### 2. Database Migrations (After Code Deploy)
After the app is deployed, run the migration script to add new columns:

```sql
-- SSH into Render or use psql client:
psql -U exam_user -d exam_middleware -h <render-db-host> -f scripts/add_auto_processed_field.sql
```

Or run directly in PostgreSQL console:

```sql
-- Add auto_processed field for tracking ML-extracted files
ALTER TABLE examination_artifacts ADD COLUMN IF NOT EXISTS auto_processed BOOLEAN NOT NULL DEFAULT false;

-- Create index for fast filtering
CREATE INDEX IF NOT EXISTS idx_examination_artifacts_auto_processed 
ON examination_artifacts(auto_processed) 
WHERE auto_processed = true;
```

### 3. Verify Deployment

Check application health:
```bash
curl https://your-render-url.onrender.com/health
```

Check HF Space connectivity:
```bash
curl https://your-render-url.onrender.com/api/extract/health
```

Check ML extraction status:
```bash
curl https://kavinraja-ml-service.hf.space/status
```

## New Features in This Build

### 1. Auto-Processing Pipeline
- **Flexible File Upload**: Accept ANY filename (no strict format required)
- **ML Extraction**: Extract register number and subject code automatically
- **Auto-Rename**: Automatically rename to `{register}_{subject}_{examtype}.pdf`
- **Tracking**: Mark files with `auto_processed = true` in database

### 2. Filtering Endpoint
New endpoint to view auto-processed uploads:
```
GET /upload/auto-processed
```

Returns list of files that were extracted and renamed via ML pipeline.

## Environment Variables

| Variable | Value | Purpose |
|----------|-------|---------|
| `DATABASE_URL` | Auto-generated | PostgreSQL connection |
| `HF_SPACE_URL` | `https://kavinraja-ml-service.hf.space` | ML inference service URL |
| `SECRET_KEY` | Auto-generated | JWT secret |
| `DEBUG` | `false` | Production mode |
| `MOODLE_BASE_URL` | Configured | Moodle integration |
| `MOODLE_ADMIN_TOKEN` | Configured | Moodle API auth |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

## Docker Build

The `Dockerfile.render` is optimized for Render:
- **Size**: ~200MB (lightweight)
- **Build Time**: ~2-3 minutes
- **Memory Usage**: ~300MB at runtime
- **Models**: None (uses remote HF Space)

Key optimizations:
- No torch, ultralytics, or heavy ML packages
- Uses remote extraction with local fallback
- Minimal system dependencies

## Troubleshooting

### 1. ML Extraction Not Working
- Check `HF_SPACE_URL` environment variable is set correctly
- Verify HF Space is running: `https://kavinraja-ml-service.hf.space/health`
- Check application logs for extraction errors

### 2. Auto-Processed Endpoint Returns Empty
- Ensure database migration was run
- Verify `auto_processed` column exists: 
  ```sql
  SELECT column_name FROM information_schema.columns WHERE table_name = 'examination_artifacts';
  ```

### 3. File Upload Fails
- Check file size limits in configuration
- Verify PDF/JPG magic bytes are valid
- Check storage permissions in `/uploads` directory

## Rollback

If deployment has issues:
1. Render will keep previous builds
2. Use Render dashboard to select previous build
3. Database migration is safe (adding columns with defaults)

## Monitoring

Monitor these endpoints in production:
- `GET /health` - Application health
- `GET /api/extract/health` - HF Space connectivity  
- `GET /upload/auto-processed` - Auto-processed file count

## Logs

Access Render logs:
1. Go to Render Dashboard → Service
2. Scroll to "Logs" section
3. Check for errors related to:
   - Database connections
   - HF Space API calls
   - File processing

## Support

For issues:
1. Check the application logs
2. Verify HF Space status at `https://kavinraja-ml-service.hf.space`
3. Test database connectivity with psql client
4. Review recent git commits for code changes
