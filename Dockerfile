# Dockerfile para Form Google - Peticionador ADV
# FASE 6.1 - Transição para Nova Arquitetura
# Configuração completa para produção com Nginx + Gunicorn

FROM python:3.11-slim

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    nginx \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Instalar Node.js (para build do frontend)
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Criar usuário para a aplicação
RUN useradd --create-home --shell /bin/bash app
WORKDIR /home/app

# Copiar e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .
RUN chown -R app:app /home/app

# Build do frontend Vue.js
USER app
RUN npm install
RUN npm run build

# Configurar Nginx
USER root
COPY docker/nginx.conf /etc/nginx/nginx.conf
COPY docker/app.conf /etc/nginx/sites-available/app
RUN ln -s /etc/nginx/sites-available/app /etc/nginx/sites-enabled/
RUN rm /etc/nginx/sites-enabled/default

# Configurar Supervisor
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Configurar permissões
RUN chown -R app:app /home/app
RUN chmod +x /home/app/docker/start.sh

# Criar diretórios necessários
RUN mkdir -p /var/log/supervisor
RUN mkdir -p /var/log/gunicorn
RUN mkdir -p /var/log/nginx
RUN chown -R app:app /var/log/gunicorn

# Expor porta
EXPOSE 80

# Comando de inicialização
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost/health || exit 1