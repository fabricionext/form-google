#!/bin/bash
# Backup script for Form Google - Peticionador ADV
# FASE 6.1 - Script de backup automático

set -e

# Configurações
DB_HOST="db"
DB_NAME="form_google"
DB_USER="postgres"
BACKUP_DIR="/backups"
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}

# Criar diretório de backup se não existir
mkdir -p $BACKUP_DIR

# Nome do arquivo com timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/form_google_backup_$TIMESTAMP.sql"

echo "🗄️ Starting database backup..."

# Fazer backup do banco de dados
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME > $BACKUP_FILE

# Comprimir o arquivo
gzip $BACKUP_FILE
BACKUP_FILE_GZ="$BACKUP_FILE.gz"

echo "✅ Backup completed: $BACKUP_FILE_GZ"

# Verificar se o backup foi criado
if [ ! -f "$BACKUP_FILE_GZ" ]; then
    echo "❌ Backup file not created!"
    exit 1
fi

# Verificar tamanho do arquivo
BACKUP_SIZE=$(stat -c%s "$BACKUP_FILE_GZ")
if [ $BACKUP_SIZE -lt 1000 ]; then
    echo "❌ Backup file too small ($BACKUP_SIZE bytes), possible error!"
    exit 1
fi

echo "📁 Backup size: $(du -h $BACKUP_FILE_GZ | cut -f1)"

# Limpar backups antigos
echo "🧹 Cleaning old backups (older than $RETENTION_DAYS days)..."
find $BACKUP_DIR -name "form_google_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete

# Listar backups restantes
echo "📋 Remaining backups:"
ls -lah $BACKUP_DIR/form_google_backup_*.sql.gz 2>/dev/null || echo "No backups found"

# Upload para S3 (opcional)
if [ ! -z "$BACKUP_S3_BUCKET" ] && [ ! -z "$AWS_ACCESS_KEY_ID" ]; then
    echo "☁️ Uploading to S3..."
    aws s3 cp $BACKUP_FILE_GZ s3://$BACKUP_S3_BUCKET/form-google-backups/
    echo "✅ Uploaded to S3: s3://$BACKUP_S3_BUCKET/form-google-backups/$(basename $BACKUP_FILE_GZ)"
fi

echo "🎉 Backup process completed successfully!"