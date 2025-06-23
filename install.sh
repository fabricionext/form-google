#!/bin/bash
set -e

# Caminho base
BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$BASE_DIR"

# 1. Atualizar pacotes do sistema
sudo apt update && sudo apt install -y python3 python3-venv python3-pip redis-server nginx git

# 2. Criar e ativar ambiente virtual
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate

# 3. Instalar dependências Python
pip install --upgrade pip
if [ -f requirements.txt ]; then
  pip install -r requirements.txt
elif [ -f pyproject.toml ] || [ -f setup.py ]; then
  pip install .
else
  echo "[WARN] Nenhum arquivo requirements.txt ou pyproject.toml/setup.py encontrado."
fi

# 4. Instalar dependências extras de desenvolvimento (opcional)
if [ -f requirements-dev.txt ]; then
  pip install -r requirements-dev.txt
fi

# 5. Configurar variáveis de ambiente
if [ ! -f .env ]; then
  cp .env.example .env
  echo "[INFO] Edite o arquivo .env com suas configurações."
fi

# 6. Migrar banco de dados
if [ -f alembic.ini ]; then
  echo "[INFO] Rodando migrações Alembic..."
  alembic upgrade head
fi

# 7. Configurar permissões para logs e sockets
sudo mkdir -p logs run
sudo chown -R $USER:www-data logs run
sudo chmod -R 775 logs run

# 8. Configurar serviços systemd
if [ -f form_google.service ]; then
  sudo cp form_google.service /etc/systemd/system/
  sudo systemctl daemon-reload
  sudo systemctl enable form_google.service
fi
if [ -f form_google_celery.service ]; then
  sudo cp form_google_celery.service /etc/systemd/system/
  sudo systemctl daemon-reload
  sudo systemctl enable form_google_celery.service
fi

# 9. Configurar Nginx (exemplo)
if [ -f /etc/nginx/sites-available/default ]; then
  sudo cp nginx_example.conf /etc/nginx/sites-available/form_google || true
  sudo ln -sf /etc/nginx/sites-available/form_google /etc/nginx/sites-enabled/form_google || true
  sudo nginx -t && sudo systemctl reload nginx
fi

# 10. Iniciar serviços
sudo systemctl restart redis-server || true
sudo systemctl restart form_google.service || true
sudo systemctl restart form_google_celery.service || true

# 11. Mensagem final
cat <<EOF

✅ Instalação concluída!
- Edite o arquivo .env conforme necessário.
- Verifique as configurações de Nginx, Gunicorn e Celery.
- Acesse o sistema normalmente.

EOF
