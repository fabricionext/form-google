#!/bin/bash
set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Usage: $0 <backup_file.tar.gz>"
    exit 1
fi

BACKUP_FILE="$1"
APP_DIR="${APP_DIR:-/var/www/estevaoalmeida.com.br/form-google}"
LOG_FILE="${LOG_FILE:-/var/log/appform_backup.log}"

log() {
    echo "[$(date '+%F %T')] $1" | tee -a "$LOG_FILE"
}

TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT

tar xzf "$BACKUP_FILE" -C "$TEMP_DIR"

DB_USER="${DB_USER:-postgres}"
DB_PASS="${DB_PASS:-}" 
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-form_google}"

log "Restoring database $DB_NAME..."
export PGPASSWORD="$DB_PASS"
pg_restore -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" --clean "$TEMP_DIR/db.dump" >> "$LOG_FILE" 2>&1
unset PGPASSWORD

log "Restoring application files to $APP_DIR..."
mkdir -p "$APP_DIR"
tar xzf "$TEMP_DIR/app_files.tar.gz" -C "$APP_DIR" >> "$LOG_FILE" 2>&1

log "Restore completed"
