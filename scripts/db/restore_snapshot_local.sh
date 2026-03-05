#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: docker command not found. Install Docker Desktop/Engine first."
  exit 1
fi

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <path-to-render-backup.dump>"
  exit 1
fi

BACKUP_FILE="$1"
if [[ ! -f "$BACKUP_FILE" ]]; then
  echo "ERROR: Backup file not found: $BACKUP_FILE"
  exit 1
fi

LOCAL_POSTGRES_DB="${LOCAL_POSTGRES_DB:-exam_middleware}"
LOCAL_POSTGRES_USER="${LOCAL_POSTGRES_USER:-exam_user}"

echo "Starting local postgres container..."
docker compose up -d postgres

echo "Waiting for local postgres readiness..."
for i in {1..30}; do
  if docker compose exec -T postgres pg_isready -U "$LOCAL_POSTGRES_USER" -d "$LOCAL_POSTGRES_DB" >/dev/null 2>&1; then
    break
  fi
  if [[ "$i" -eq 30 ]]; then
    echo "ERROR: postgres did not become ready in time"
    exit 1
  fi
  sleep 2
done

echo "Copying backup into postgres container..."
cat "$BACKUP_FILE" | docker compose exec -T postgres sh -lc 'cat > /tmp/render_snapshot.dump'

echo "Recreating target database..."
docker compose exec -T postgres dropdb -U "$LOCAL_POSTGRES_USER" --if-exists "$LOCAL_POSTGRES_DB"
docker compose exec -T postgres createdb -U "$LOCAL_POSTGRES_USER" "$LOCAL_POSTGRES_DB"

echo "Restoring snapshot into local postgres..."
docker compose exec -T postgres pg_restore \
  -U "$LOCAL_POSTGRES_USER" \
  -d "$LOCAL_POSTGRES_DB" \
  --no-owner \
  --no-privileges \
  --clean \
  --if-exists \
  /tmp/render_snapshot.dump

echo "Local DB snapshot restore completed successfully."
