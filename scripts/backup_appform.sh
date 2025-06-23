#!/bin/bash
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/var/backups/appform}"
APP_DIR="${APP_DIR:-/var/www/estevaoalmeida.com.br/form-google}"
LOG_FILE="${LOG_FILE:-/var/log/appform_backup.log}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="appform_backup_${TIMESTAMP}"

log() {
    echo "[$(date '+%F %T')] $1" | tee -a "$LOG_FILE"
}

mkdir -p "$BACKUP_DIR" "$(dirname "$LOG_FILE")"

# rotate logs (keep 30 days)
find "$(dirname "$LOG_FILE")" -name "$(basename "$LOG_FILE").*" -mtime +30 -delete 2>/dev/null || true
if [ -f "$LOG_FILE" ]; then
    mv "$LOG_FILE" "$LOG_FILE.$TIMESTAMP"
fi
: > "$LOG_FILE"

TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT

DB_USER="${DB_USER:-postgres}"
DB_PASS="${DB_PASS:-}" 
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-form_google}"

log "Dumping database $DB_NAME..."
export PGPASSWORD="$DB_PASS"
pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -F c -f "$TEMP_DIR/db.dump" "$DB_NAME" >> "$LOG_FILE" 2>&1
unset PGPASSWORD

log "Packaging application files..."
# create archive of application excluding heavy/temp dirs
 tar czf "$TEMP_DIR/app_files.tar.gz" \
    --exclude='*.pyc' --exclude='__pycache__' --exclude='.git' \
    --exclude='node_modules' --exclude='venv' \
    -C "$APP_DIR" . >> "$LOG_FILE" 2>&1

log "Creating final archive..."
 tar czf "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" -C "$TEMP_DIR" db.dump app_files.tar.gz >> "$LOG_FILE" 2>&1

log "Removing temporary files..."
rm -rf "$TEMP_DIR"

# delete old backups (older than 30 days)
find "$BACKUP_DIR" -name 'appform_backup_*.tar.gz' -mtime +30 -delete 2>/dev/null || true

log "Synchronizing with Google Drive..."
"$(dirname "$0")/sync_backup_gdrive.sh" "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" >> "$LOG_FILE" 2>&1 || true

log "Backup finished: $BACKUP_DIR/${BACKUP_NAME}.tar.gz"
