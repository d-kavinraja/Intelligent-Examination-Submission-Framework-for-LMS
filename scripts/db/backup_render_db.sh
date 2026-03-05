#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BACKUP_DIR="${BACKUP_DIR:-$ROOT_DIR/backups}"
SOURCE_DATABASE_URL="${RENDER_DATABASE_URL:-${DATABASE_URL:-}}"

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: docker command not found. Install Docker Desktop/Engine first."
  exit 1
fi

if [[ $# -ge 1 ]]; then
  SOURCE_DATABASE_URL="$1"
fi

if [[ -z "${SOURCE_DATABASE_URL}" ]]; then
  echo "ERROR: Source Render DB URL is missing."
  echo "Set RENDER_DATABASE_URL (recommended) or DATABASE_URL, or pass as first arg."
  exit 1
fi

mkdir -p "$BACKUP_DIR"

TS="$(date +%Y%m%d_%H%M%S)"
BACKUP_FILE="render_db_${TS}.dump"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_FILE"

echo "Creating backup from Render PostgreSQL..."
docker run --rm \
  -e SOURCE_DATABASE_URL="$SOURCE_DATABASE_URL" \
  -v "$BACKUP_DIR:/backups" \
  postgres:16-alpine \
  sh -lc 'pg_dump --format=custom --no-owner --no-privileges "$SOURCE_DATABASE_URL" -f "/backups/'"$BACKUP_FILE"'"'

echo "Backup complete: $BACKUP_PATH"
echo "$BACKUP_PATH"
