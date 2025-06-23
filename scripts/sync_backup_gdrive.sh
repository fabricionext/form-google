#!/bin/bash
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/var/backups/appform}"
REMOTE="${GDRIVE_REMOTE:-gdrive:appform_backup}"
LOG_FILE="${LOG_FILE_SYNC:-/var/log/appform_backup_gdrive.log}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR" "$(dirname "$LOG_FILE")"

# rotate logs (keep 30 days)
find "$(dirname "$LOG_FILE")" -name "$(basename "$LOG_FILE").*" -mtime +30 -delete 2>/dev/null || true
if [ -f "$LOG_FILE" ]; then
    mv "$LOG_FILE" "$LOG_FILE.$TIMESTAMP"
fi
: > "$LOG_FILE"

log() {
    echo "[$(date '+%F %T')] $1" | tee -a "$LOG_FILE"
}

log "Syncing $BACKUP_DIR to $REMOTE..."
if ! command -v rclone >/dev/null 2>&1; then
    log "rclone not found"
    exit 1
fi
rclone sync "$BACKUP_DIR" "$REMOTE" >> "$LOG_FILE" 2>&1
log "Sync completed"
