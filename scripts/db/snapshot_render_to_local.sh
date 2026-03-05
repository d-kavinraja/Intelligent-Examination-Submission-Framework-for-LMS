#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BACKUP_DIR="${BACKUP_DIR:-$ROOT_DIR/backups}"

mkdir -p "$BACKUP_DIR"

echo "Step 1/2: Backing up Render DB..."
BACKUP_PATH="$($ROOT_DIR/scripts/db/backup_render_db.sh "$@" | tail -n 1)"

if [[ ! -f "$BACKUP_PATH" ]]; then
  echo "ERROR: Backup was not created as expected: $BACKUP_PATH"
  exit 1
fi

echo "Step 2/2: Restoring backup into local postgres..."
$ROOT_DIR/scripts/db/restore_snapshot_local.sh "$BACKUP_PATH"

echo "Render DB snapshot is now available in local dockerized PostgreSQL."
