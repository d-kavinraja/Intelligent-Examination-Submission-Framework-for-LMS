# Local Docker Setup (Moodle External)

This setup runs the full middleware stack locally in Docker while keeping Moodle external (middleware communicates to your existing Moodle URL). The setup is fully self-contained and optimized for both CPU and GPU.

## What runs in Docker

- `frontend` (Nginx serving the landing page)
- `middleware` (FastAPI app)
- `postgres` (local DB with persistent storage)
- `ml-service` (YOLO + CRNN inference API with baked-in models)
- `mailhog` (local SMTP sink)

## Prerequisites

- Docker + Docker Compose plugin
- For GPU mode: NVIDIA GPU + NVIDIA Container Toolkit

No local Python / PostgreSQL installation is required. Models are automatically built into the ML container.

## 0) Prepare environment file

```bash
cp .env.docker.example .env
```

Edit `.env` and configure:

- `MOODLE_BASE_URL` (your external Moodle URL)
- `MOODLE_ADMIN_TOKEN` (if needed)

## 1) Start full local stack (CPU-only / Default)

```bash
docker compose up -d --build
```

Database behavior:
- `postgres` container creates the `exam_middleware` database.
- `middleware` entrypoint waits for DB and runs `python init_db.py` automatically.
- Required tables + default seed data are created idempotently on startup.

## 2) Start full local stack (GPU Inference)

If you have an NVIDIA GPU and the Container Toolkit installed:

```bash
docker compose --profile gpu up -d --build
```

## 3) Verify services

Access points:
- Landing Page: http://localhost:8080
- Staff portal: http://localhost:8000/portal/staff
- Student portal: http://localhost:8000/portal/student
- API docs: http://localhost:8000/docs
- MailHog UI: http://localhost:8025

Check health:
```bash
docker compose ps
curl http://localhost:8000/health
curl http://localhost:7860/health
```

## Useful commands

```bash
# View logs
docker compose logs -f middleware
docker compose logs -f ml-service

# Stop all containers
docker compose down

# Stop + delete local DB volume (WARNING: Destroys all local data)
docker compose down -v
```
