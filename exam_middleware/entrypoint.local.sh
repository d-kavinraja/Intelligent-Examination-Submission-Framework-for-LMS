#!/usr/bin/env bash
set -euo pipefail

POSTGRES_HOST="${POSTGRES_HOST:-postgres}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER:-exam_user}"
POSTGRES_DB="${POSTGRES_DB:-exam_middleware}"

echo "[entrypoint] Waiting for PostgreSQL at ${POSTGRES_HOST}:${POSTGRES_PORT}..."
for i in {1..60}; do
  if pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null 2>&1; then
    echo "[entrypoint] PostgreSQL is ready."
    break
  fi

  if [[ "$i" -eq 60 ]]; then
    echo "[entrypoint] ERROR: PostgreSQL did not become ready in time."
    exit 1
  fi
  sleep 2
done

echo "[entrypoint] Initializing database tables and seed data..."
python init_db.py

echo "[entrypoint] Starting application..."
exec "$@"
