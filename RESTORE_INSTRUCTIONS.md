# 🔄 Instruções de Restauração do Sistema

## 📋 **Pré-requisitos**

### **Sistema Operacional:**

- Ubuntu 20.04+ ou similar
- Python 3.12+
- PostgreSQL 12+
- Nginx
- Redis (para Celery)

### **Pacotes Necessários:**

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv postgresql postgresql-contrib nginx redis-server git
```

## 🚀 **Passo a Passo da Restauração**

### **1. Clonar o Repositório**

```bash
git clone https://github.com/fabricionext/form-google.git
cd form-google
git checkout backup/complete-system-backup-20250623-221938
```

### **2. Configurar Ambiente Python**

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### **3. Configurar Banco de Dados**

#### **3.1 Criar Usuário e Banco:**

```bash
sudo -u postgres psql
CREATE USER form_user WITH PASSWORD 'form_password';
CREATE DATABASE form_google OWNER form_user;
GRANT ALL PRIVILEGES ON DATABASE form_google TO form_user;
\q
```

#### **3.2 Restaurar Backup:**

```bash
sudo -u postgres psql -d form_google < database_backup_20250623_222107.sql
```

#### **3.3 Aplicar Migrações:**

```bash
source venv/bin/activate
flask db upgrade
alembic upgrade head
```

### **4. Configurar Variáveis de Ambiente**

Criar arquivo `.env` na raiz do projeto:

```bash
# Banco de Dados
DB_USER=form_user
DB_PASS=form_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=form_google
SQLALCHEMY_DATABASE_URI=postgresql://form_user:form_password@localhost:5432/form_google

# Flask
SECRET_KEY=sua-chave-secreta-aqui
FLASK_ENV=production

# Google API
GOOGLE_SERVICE_ACCOUNT_JSON=/caminho/para/credentials.json
SPREADSHEET_ID=seu-spreadsheet-id
PARENT_FOLDER_ID=seu-folder-id
ADMIN_EMAIL=admin@exemplo.com
BACKUP_FOLDER_ID=seu-backup-folder-id
INTERNAL_API_KEY=sua-api-key

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### **5. Configurar Google API**

#### **5.1 Criar Projeto no Google Cloud:**

1. Acesse [Google Cloud Console](https://console.cloud.google.com)
2. Crie um novo projeto
3. Ative as APIs: Google Drive, Google Docs, Google Sheets
4. Crie uma Service Account
5. Baixe o arquivo JSON de credenciais
6. Coloque o arquivo em local seguro e atualize o caminho no `.env`

### **6. Configurar Serviços do Sistema**

#### **6.1 Serviço Principal (form_google.service):**

```bash
sudo cp form_google.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable form_google
```

#### **6.2 Serviço Celery (form_google_celery.service):**

```bash
sudo cp form_google_celery.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable form_google_celery
```

#### **6.3 Configurar Nginx:**

```bash
sudo cp appform.estevaoalmeida.com.br /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/appform.estevaoalmeida.com.br /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### **7. Configurar Monitoramento (Opcional)**

#### **7.1 Loki e Grafana:**

```bash
cd monitoring
docker-compose up -d
```

### **8. Iniciar Serviços**

#### **8.1 Iniciar Todos os Serviços:**

```bash
sudo systemctl start redis
sudo systemctl start form_google
sudo systemctl start form_google_celery
sudo systemctl restart nginx
```

#### **8.2 Verificar Status:**

```bash
sudo systemctl status form_google
sudo systemctl status form_google_celery
sudo systemctl status nginx
sudo systemctl status redis
```

## 🧪 **Testes de Verificação**

### **1. Testar Aplicação:**

```bash
curl -I https://appform.estevaoalmeida.com.br
# Deve retornar 200 ou 401 (normal para não autenticado)
```

### **2. Testar Banco de Dados:**

```bash
source venv/bin/activate
python -c "from application import app; print('Aplicação carregada com sucesso')"
```

### **3. Testar Celery:**

```bash
source venv/bin/activate
celery -A celery_worker.celery worker --loglevel=info
```

## 🔧 **Troubleshooting**

### **Problemas Comuns:**

#### **1. Erro de Conexão com Banco:**

```bash
# Verificar se PostgreSQL está rodando
sudo systemctl status postgresql

# Verificar conexão
psql -h localhost -U form_user -d form_google
```

#### **2. Erro de Permissões:**

```bash
# Ajustar permissões do diretório
sudo chown -R www-data:www-data /var/www/estevaoalmeida.com.br/form-google
sudo chmod -R 755 /var/www/estevaoalmeida.com.br/form-google
```

#### **3. Erro de Porta em Uso:**

```bash
# Verificar portas em uso
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :443
```

#### **4. Erro de Logs:**

```bash
# Verificar logs do sistema
sudo journalctl -u form_google -f
sudo tail -f /var/log/nginx/error.log
```

## 📊 **Verificação Final**

### **Checklist de Restauração:**

- ✅ Repositório clonado
- ✅ Ambiente Python configurado
- ✅ Banco de dados restaurado
- ✅ Migrações aplicadas
- ✅ Variáveis de ambiente configuradas
- ✅ Google API configurada
- ✅ Serviços iniciados
- ✅ Nginx configurado
- ✅ Aplicação respondendo
- ✅ Celery funcionando

### **Comandos de Verificação:**

```bash
# Status dos serviços
sudo systemctl status form_google form_google_celery nginx redis

# Teste da aplicação
curl -I https://appform.estevaoalmeida.com.br

# Logs em tempo real
sudo journalctl -u form_google -f
```

## 🔗 **Links Úteis**

- **Documentação:** README.md
- **Issues:** GitHub Issues
- **Monitoramento:** http://localhost:3000 (Grafana)
- **Logs:** http://localhost:3100 (Loki)

---

**⚠️ IMPORTANTE:** Sempre faça backup antes de restaurar e teste em ambiente de desenvolvimento primeiro!
