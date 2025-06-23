# Sistema de Cadastro de Clientes ADV - Versão 1.04

Este projeto é uma aplicação Flask para automação de documentos Google Docs, publicada de forma segura e profissional usando Gunicorn, Nginx e Cloudflare Tunnel (sem necessidade de portas abertas no roteador).

## 🚀 Visão Geral

- **Back-end**: Flask (Python) com recursos avançados de segurança
- **Servidor de aplicação**: Gunicorn (via Unix socket) com configurações otimizadas
- **Proxy reverso**: Nginx com headers de segurança
- **Backup Automático**: Backup diário local e sincronização com Google Drive
- **Segurança**: Rate limiting, CSRF protection, CORS, Headers de segurança
  - Configurações extras carregadas de `security_config.py` em `application.py`
- **Monitoramento**: Grafana Loki (logs centralizados)
- **Qualidade de Código**: ESLint + Prettier para JavaScript/TypeScript
- **Publicação externa**: Cloudflare Tunnel (cloudflared)
- **Subdomínio**: [https://appform.estevaoalmeida.com.br](https://appform.estevaoalmeida.com.br)
- **DNS e proteção**: Cloudflare com regras de segurança

---

## ✨ Melhorias Recentes (v1.04)

### 🔍 Monitoramento e Observabilidade

- **Grafana Loki**: Agregação e visualização de logs centralizados
- **Grafana**: Dashboards para análise de logs e métricas
- **Logs estruturados**: Sistema de logging avançado com contexto

### 🛠️ Qualidade de Código

- **ESLint**: Linting automático para JavaScript/TypeScript
- **Prettier**: Formatação automática de código
- **Scripts npm**: Automação de lint e formatação

### 🗄️ Banco de Dados

- **Migração melhorada**: Sistema de migração robusto com Alembic
- **Coluna de observações expandida**: Suporte a logs detalhados de erro
- **Histórico de migração**: Gerenciamento automático de versões

### 📝 Interface e UX

- **Interface do Formulário:**
  - Remoção dos textos informativos de formato de campo (CPF, CEP, Telefone Celular) para uma interface mais limpa.
  - Reorganização dos campos na seção "Dados Pessoais" para melhor fluxo: Primeiro Nome, Sobrenome, Nacionalidade, Estado Civil, Profissão, Data de Nascimento.
  - Movimentação do campo CPF da seção "Dados Pessoais" para o início da seção "Documentos".

---

## 📊 Monitoramento e Observabilidade

### Grafana Loki - Logs Centralizados

Sistema de logs estruturados com Grafana Loki para análise avançada.

**Iniciar stack de monitoramento:**

```bash
./start_monitoring.sh
```

**Acessar Grafana:**

- URL: http://localhost:3000
- Login: admin / admin

**Uso no código:**

```python
from loki_logger import setup_loki_logging, log_google_api_operation, log_document_generation

# Configurar logging para Loki
setup_loki_logging()

# Log de operação da API
log_google_api_operation('create_document', 'success', {'document_id': '123'})

# Log de geração de documento
log_document_generation(form_id=123, user_id=456, status='completed')
```

---

## 🛠️ Qualidade de Código

### ESLint + Prettier

O projeto está configurado com ferramentas de qualidade de código para JavaScript/TypeScript.

**Comandos disponíveis:**

```bash
# Linting
npm run lint

# Formatação automática
npm run format

# Verificar formatação (sem alterar)
npm run format:check
```

**Configuração:**

- `.eslintrc.js`: Configuração do ESLint
- `.prettierrc`: Configuração do Prettier
- `package.json`: Scripts automatizados

---

## 📄 Geração de Documentos e Placeholders

O núcleo da aplicação é a capacidade de gerar documentos Google Docs automaticamente a partir de templates pré-definidos. O sistema utiliza um mecanismo de placeholders para substituir variáveis no template pelos dados fornecidos no formulário.

### Mapeamento de Placeholders

- **Formato:** Os placeholders no seu template do Google Docs devem seguir o formato `{{Nome_Do_Placeholder}}`.
- **Mapeamento Interno:** O sistema possui um mapa interno (`document_generator.py`) que converte os campos do formulário (ex: `primeiroNome`) para os placeholders correspondentes no template (ex: `{{Primeiro Nome}}`).
- **Placeholders de Endereço:** Para endereços, utilize os placeholders detalhados para garantir o preenchimento correto: `{{Endereço_Logradouro}}`, `{{Endereço_Numero}}`, `{{Endereço_Bairro}}`, `{{Endereço_CEP}}`, `{{Endereço_Cidade}}`, `{{Endereço_Estado}}` e `{{Endereço_Complemento}}`.

### Placeholders Especiais

- `{{Data_Preenchimento}}`: Este placeholder é preenchido automaticamente com a data em que o documento foi gerado, no formato `DD/MM/YYYY`.
- `{{Nascimento}}` e `{{Data de Fundação}}`: Estes campos de data são automaticamente formatados para `DD/MM/YYYY`.

### Configuração de Templates no `.env`

Para que o sistema encontre os templates corretos, é **essencial** configurar os IDs dos seus documentos Google Docs no arquivo `.env`. Cada variável corresponde a um tipo de documento:

```env
# IDs dos Templates do Google Docs
TEMPLATE_FICHA_CADASTRAL_ID="SEU_ID_DO_TEMPLATE_AQUI"
TEMPLATE_CONTRATO_HONORARIOS_ID="SEU_ID_DO_TEMPLATE_AQUI"
TEMPLATE_PROCURACAO_JUDICIAL_ID="SEU_ID_DO_TEMPLATE_AQUI"
TEMPLATE_PROCURACAO_ADMINISTRATIVA_ID="SEU_ID_DO_TEMPLATE_AQUI"
TEMPLATE_CONTRATO_ADMINISTRATIVO_ID="SEU_ID_DO_TEMPLATE_AQUI"
TEMPLATE_DECLARACAO_POBREZA_ID="SEU_ID_DO_TEMPLATE_AQUI"
```

Certifique-se de que cada variável contém o ID correto extraído da URL do seu documento no Google Docs.

---

## 🔄 Sistema de Backup Automático

O sistema de backup automático garante a segurança dos seus dados com as seguintes funcionalidades:

### 📂 O que é feito backup

- **Banco de Dados PostgreSQL**: Dump completo do banco de dados
- **Arquivos do Aplicativo**: Todo o código-fonte (exceto arquivos temporários e de ambiente)
- **Configurações**: Arquivos de configuração do Nginx, systemd e .env
- **Logs**: Logs da aplicação e do sistema

### ⚙️ Configuração

O backup é configurado automaticamente durante a instalação. Os arquivos principais estão em:

```
/var/backups/appform/
├── appform_backup_*.tar.gz    # Backups compactados
└── scripts/
    ├── backup_appform.sh       # Script principal de backup
    ├── restore_appform.sh      # Script de restauração
    └── sync_backup_gdrive.sh   # Sincronização com Google Drive
```

### 📅 Agendamento

- **Backup diário**: 2h da manhã
- **Sincronização com Google Drive**: Imediatamente após cada backup
- **Limpeza de logs**: 1h da manhã (mantém 30 dias)

### 📝 Como Usar

1. **Fazer backup manual**:

   ```bash
   sudo /var/backups/appform/scripts/backup_appform.sh
   ```

2. **Restaurar de um backup**:

   ```bash
   sudo /var/backups/appform/scripts/restore_appform.sh /caminho/para/backup.tar.gz
   ```

3. **Sincronizar manualmente com Google Drive**:

   ```bash
   sudo /var/backups/appform/scripts/sync_backup_gdrive.sh
   ```

4. **Verificar logs**:

   ```bash
   # Logs do backup
   sudo tail -f /var/log/appform_backup.log

   # Logs da sincronização com Google Drive
   sudo tail -f /var/log/appform_backup_gdrive.log
   ```

### 🔍 Verificação

1. **Verifique os backups locais**:

   ```bash
   sudo ls -lh /var/backups/appform/appform_backup_*.tar.gz
   ```

2. **Verifique os backups no Google Drive**:

   - Acesse a pasta de backup: [Google Drive Backup](https://drive.google.com/drive/u/1/folders/13-8UjrTJ3HkIBvNSyRLs2MEtNHOvZNhU)
   - Verifique se os arquivos de backup estão sendo sincronizados corretamente

3. **Verifique o espaço em disco**:
   ```bash
   df -h /var
   ```

### ⚠️ Solução de Problemas

- **Falha no backup**: Verifique os logs em `/var/log/appform_backup.log`
- **Falha na sincronização**: Verifique os logs em `/var/log/appform_backup_gdrive.log`
- **Espaço em disco insuficiente**: Limpe backups antigos manualmente se necessário

---

## ⚙️ Requisitos

- **Python 3.8+** com suporte a ambientes virtuais
- **Node.js 16+** para ferramentas de qualidade de código
- **Docker** para Grafana Loki (opcional)
- **Conta Cloudflare** com domínio configurado
- **Conta Google Cloud** para autenticação com Google Drive
- **Servidor Ubuntu** (testado em 20.04+ e 22.04 LTS)
- Acesso **root/sudo**
- Ferramentas básicas instaladas:
  ```bash
  sudo apt update && sudo apt install -y git python3-venv python3-pip python3-dev build-essential libssl-dev libffi-dev python3-setuptools rclone nodejs npm
  ```
- **OpenSSL** para geração de certificados (já incluído na maioria das distribuições)

---

## 🛠️ Instalação e Configuração

### 1. Instalação Automatizada com `install.sh` (Recomendado)

O script `install.sh` automatiza a configuração do ambiente e instalação da aplicação.

**Passos:**

1. **Clone o repositório e acesse o diretório:**

   ```bash
   git clone <URL_DO_SEU_REPOSITORIO_GIT> form-google
   cd form-google
   ```

   _Substitua `<URL_DO_SEU_REPOSITORIO_GIT>` pela URL do seu repositório._

2. **Configure as credenciais do Google Drive:**

   - Crie uma conta de serviço no Google Cloud Console
   - Baixe o arquivo JSON de credenciais
   - Mova o arquivo para `/var/www/estevaoalmeida.com.br/form-google/`
   - Garanta que o arquivo seja de propriedade do usuário correto:
     ```bash
     sudo chown fabricioalmeida:www-data /var/www/estevaoalmeida.com.br/form-google/*.json
     sudo chmod 600 /var/www/estevaoalmeida.com.br/form-google/*.json
     ```

3. **Torne o script executável e execute como root:**

   ```bash
   chmod +x install.sh
   sudo ./install.sh
   ```

   O script irá executar as seguintes etapas:

   - Instalar dependências do sistema (python3-venv, nginx, rclone, nodejs, etc.)
   - Criar e configurar ambiente virtual Python (`venv`)
   - Instalar dependências Python (a partir do arquivo `requirements.txt`)
   - Instalar dependências Node.js para ferramentas de qualidade
   - Configurar diretórios de log e backup com permissões adequadas
   - Configurar serviço systemd otimizado para produção
   - Configurar Nginx como proxy reverso com headers de segurança
   - Configurar sistema de backup automático
   - Configurar sincronização com Google Drive
   - Auxiliar na configuração do Cloudflare Tunnel

4. **Pós-instalação:**
   - O script criará um arquivo `.env` de exemplo
   - Edite esse arquivo conforme necessário. Ele contém variáveis como `GOOGLE_SERVICE_ACCOUNT_JSON` e `BACKUP_FOLDER_ID` e define os horários de backup (`BACKUP_SCHEDULE`, `SYNC_GDRIVE_SCHEDULE`, `LOG_CLEANUP_SCHEDULE`).
   - Serão configuradas permissões de arquivos e diretórios
   - Serão habilitados e iniciados os serviços necessários
   - O primeiro backup será executado automaticamente

### 2. Configuração do Monitoramento (Opcional)

**Grafana Loki:**

```bash
# Iniciar stack de monitoramento
./start_monitoring.sh

# Acessar Grafana: http://localhost:3000
# Login: admin / admin
```

### 3. Configuração do Google Drive (se necessário)

Se precisar reconfigurar o acesso ao Google Drive:

1. **Crie uma conta de serviço no Google Cloud Console**

   - Acesse [Google Cloud Console](https://console.cloud.google.com/)
   - Vá para "APIs & Serviços" > "Credenciais"
   - Crie uma nova conta de serviço
   - Baixe o arquivo JSON de credenciais

2. **Configure o Rclone**

   ```bash
   sudo mkdir -p /root/.config/rclone/
   sudo nano /root/.config/rclone/rclone.conf
   ```

   Adicione a seguinte configuração (substitua pelos seus valores):

   ```ini
   [gdrive]
   type = drive
   scope = drive
   service_account_file = /caminho/para/seu/arquivo-de-credenciais.json
   team_drive =
   root_folder_id = 13-8UjrTJ3HkIBvNSyRLs2MEtNHOvZNhU
   ```

3. **Teste a configuração**
   ```bash
   sudo rclone lsd gdrive:
   ```

---

## 🚀 Como Acessar

- **Formulário principal**: [https://appform.estevaoalmeida.com.br/cadastrodecliente](https://appform.estevaoalmeida.com.br/cadastrodecliente)
- **Endpoints da API**: Geralmente sob o prefixo `/api/` (ex: `/api/gerar-documento`)
- **Grafana (monitoramento)**: http://localhost:3000 (admin/admin)
- **Loki (logs)**: http://localhost:3100
- **Logs do sistema**: `/var/log/form_google/`
- **Logs de backup**: `/var/log/appform_backup.log` e `/var/log/appform_backup_gdrive.log`

---

## 🛠️ Manutenção

### Atualizando a Aplicação

1. **Pare o serviço**

   ```bash
   sudo systemctl stop form_google
   ```

2. **Faça backup**

   ```bash
   sudo /var/backups/appform/scripts/backup_appform.sh
   ```

3. **Atualize o código**

   ```bash
   cd /var/www/estevaoalmeida.com.br/form-google
   git pull origin main  # ou sua branch principal
   ```

4. **Atualize as dependências**

   ```bash
   source venv/bin/activate
   pip install .
   npm install  # Para ferramentas de qualidade de código
   ```

5. **Execute migrações do banco (se necessário)**

   ```bash
   source venv/bin/activate
   env FLASK_APP=run_migration.py flask db upgrade
   ```

6. **Reinicie os serviços**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl restart form_google
   sudo systemctl restart nginx
   ```

### Monitoramento

1. **Verifique o status dos serviços**

   ```bash
   sudo systemctl status form_google
   sudo systemctl status nginx
   sudo systemctl status cloudflared
   ```

2. **Verifique os logs**

   ```bash
   # Logs da aplicação
   sudo journalctl -u form_google -f

   # Logs do Nginx
   sudo tail -f /var/log/nginx/appform.estevaoalmeida.com.br.error.log

   # Logs de backup
   sudo tail -f /var/log/appform_backup.log
   sudo tail -f /var/log/appform_backup_gdrive.log
   ```

3. **Qualidade de código**

   ```bash
   # Linting
   npm run lint

   # Formatação
   npm run format
   ```

### Monitoramento Avançado

1. **Grafana**: http://localhost:3000 (admin/admin)
2. **Loki**: http://localhost:3100

---

## 📄 Licença

[MIT](LICENSE) (Se você tiver um arquivo LICENSE, caso contrário, pode remover ou especificar outra licença)

---

## 👨‍💻 Suporte

Para suporte, entre em contato:

- **E-mail**: fabricionext@gmail.com
- **Telefone**: (11) 9 9999-9999

---

## 📝 Notas de Atualização

### v1.0.4 - 16/01/2025

- **Monitoramento e Observabilidade:**
  - Grafana Loki para agregação e visualização de logs centralizados
  - Grafana com dashboards para análise de logs e métricas
  - Sistema de logging estruturado com contexto
- **Qualidade de Código:**
  - ESLint para linting automático de JavaScript/TypeScript
  - Prettier para formatação automática de código
  - Scripts npm para automação de lint e formatação
- **Banco de Dados:**
  - Sistema de migração robusto com Alembic
  - Coluna de observações expandida para logs detalhados
  - Gerenciamento automático de versões de migração
- **Documentação:**
  - README atualizado com novas funcionalidades
  - Documentação de monitoramento e observabilidade
  - Guias de configuração para Grafana Loki
- **Remoção:**
  - Sentry removido (apenas planos pagos disponíveis)

### v1.0.3 - 16/01/2025

- **Monitoramento e Observabilidade:**
  - Integração com Sentry para rastreamento de erros e performance
  - Grafana Loki para agregação e visualização de logs centralizados
  - Grafana com dashboards para análise de logs e métricas
  - Sistema de logging estruturado com contexto
- **Qualidade de Código:**
  - ESLint para linting automático de JavaScript/TypeScript
  - Prettier para formatação automática de código
  - Scripts npm para automação de lint e formatação
- **Banco de Dados:**
  - Sistema de migração robusto com Alembic
  - Coluna de observações expandida para logs detalhados
  - Gerenciamento automático de versões de migração
- **Documentação:**
  - README atualizado com novas funcionalidades
  - Documentação de monitoramento e observabilidade
  - Guias de configuração para Sentry e Grafana Loki

### v1.0.2 - 08/06/2025

- **Interface do Formulário:**
  - Remoção dos textos informativos de formato de campo (CPF, CEP, Telefone Celular).
  - Reorganização dos campos em "Dados Pessoais" (Nome, Sobrenome, Nacionalidade, Estado Civil, Profissão, Data de Nascimento).
  - Movimentação do campo CPF para o início da seção "Documentos".
- Atualização da documentação para v1.0.2.

### v1.0.1 - 08/06/2025

- Adicionado sistema de backup automático (originalmente listado como v1.1.0).
- Integração com Google Drive para armazenamento seguro.
- Scripts de backup e restauração.
- Documentação atualizada (referente às melhorias da v1.0.1 conforme seção "Melhorias Recentes" da versão anterior).

### v1.0.0 - 01/06/2025

- Versão inicial do sistema
- Funcionalidades básicas de cadastro e geração de documentos
- Configuração de produção com Gunicorn, Nginx e Cloudflare Tunnel
