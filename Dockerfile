# =============================================================================
# MULTI-STAGE DOCKERFILE - Form Google Peticionador ADV
# =============================================================================
# Stage 1: Build dependencies and Node.js build
# Stage 2: Runtime image

# =============================================================================
# STAGE 1: BUILD
# =============================================================================
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js for frontend build
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Set working directory
WORKDIR /build

# Copy and install Python dependencies first (for better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy package files for Node.js dependencies
COPY package.json ./
COPY package-lock.json ./
RUN npm ci

# Install TypeScript compiler globally for vue-tsc
RUN npm install -g typescript vue-tsc

# Copy source code and build frontend
COPY . .
RUN npm run build

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

# Copy built application and frontend
COPY --from=builder /build/ /home/app/
RUN chown -R app:app /home/app

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