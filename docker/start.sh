#!/bin/bash
# Start script for Form Google - Peticionador ADV
# FASE 6.1 - Script de inicialização

set -e

echo "🚀 Starting Form Google - Peticionador ADV"

# Wait for database to be ready
echo "⏳ Waiting for database..."
python -c "
import time
import sys
import os
sys.path.insert(0, '/home/app')
from extensions import db
from application import app

with app.app_context():
    max_retries = 30
    retry_count = 0
    while retry_count < max_retries:
        try:
            db.engine.execute('SELECT 1')
            print('✅ Database is ready!')
            break
        except Exception as e:
            retry_count += 1
            print(f'⏳ Database not ready, retrying ({retry_count}/{max_retries})...')
            time.sleep(2)
    else:
        print('❌ Could not connect to database')
        sys.exit(1)
"

# Run database migrations
echo "🔄 Running database migrations..."
cd /home/app
python run_migration.py

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p /var/log/gunicorn
mkdir -p /var/log/nginx
mkdir -p /home/app/documents
mkdir -p /home/app/static/uploads

# Set proper permissions
echo "🔐 Setting permissions..."
chown -R app:app /home/app
chown -R app:app /var/log/gunicorn

# Test configuration
echo "🧪 Testing Nginx configuration..."
nginx -t

echo "✅ All checks passed. Starting services..."

# Start supervisor (which starts nginx and gunicorn)
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf