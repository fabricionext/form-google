# =============================================================================
# DOCKERFILE SIMPLIFICADO - Form Google Peticionador ADV (Vue CDN)
# =============================================================================
# Stage 1: Build Python dependencies 
# Stage 2: Runtime image

# =============================================================================
# STAGE 1: BUILD PYTHON DEPENDENCIES
# =============================================================================
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /build

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# =============================================================================
# STAGE 2: RUNTIME
# =============================================================================
FROM python:3.11-slim as runtime

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    nginx \
    supervisor \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create app user
RUN useradd --create-home --shell /bin/bash app
WORKDIR /home/app

# Copy Python dependencies from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application files (excluding frontend build artifacts)
COPY . /home/app/
RUN chown -R app:app /home/app

# Remove any leftover Node.js artifacts if they exist
RUN rm -rf /home/app/frontend* \
    && rm -f /home/app/package*.json \
    && rm -f /home/app/vite.config.* \
    && rm -f /home/app/tsconfig.json \
    && rm -f /home/app/env.d.ts \
    && find /home/app -name "*.ts" -delete 2>/dev/null || true

# Copy and configure Nginx
COPY docker/nginx.conf /etc/nginx/nginx.conf
COPY docker/app.conf /etc/nginx/sites-available/app
RUN ln -s /etc/nginx/sites-available/app /etc/nginx/sites-enabled/ \
    && rm -f /etc/nginx/sites-enabled/default

# Configure Supervisor
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Set permissions
RUN chown -R app:app /home/app \
    && chmod +x /home/app/docker/start.sh

# Create necessary directories
RUN mkdir -p /var/run/supervisor

# Expose port
EXPOSE 80

# Health check with proper intervals
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# Run as root to manage nginx and supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]