import hashlib
import hmac
import os
import secrets
import time
import traceback
from datetime import datetime, timedelta
from functools import wraps

import requests
from flask import (
    Flask,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    current_app,
    url_for,
)

# Importar extensões de segurança
from flask_limiter import RateLimitExceeded
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_talisman import Talisman
from flask_wtf.csrf import CSRFProtect, generate_csrf
from werkzeug.security import check_password_hash, generate_password_hash

from config import CONFIG
from document_generator import buscar_ou_criar_pasta_cliente, gerar_documento_cliente
from security_middleware import SecurityMiddleware, require_api_key

# Inicializar extensões
from extensions import csrf, limiter, login_manager, migrate, talisman

# Criar a aplicação Flask
app = Flask(
    __name__,
    static_folder="static",
    template_folder="templates",
    instance_relative_config=True,
)


# Carregar configurações do dicionário CONFIG de config.py
app.config.from_mapping(CONFIG)

# Configurações básicas de segurança
app.config.update(
    SEND_FILE_MAX_AGE_DEFAULT=60 * 60 * 24,  # 1 dia
    SECRET_KEY=os.getenv("FLASK_SECRET_KEY", secrets.token_hex(32)),
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16MB
    # Configurações do banco de dados
    SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "sqlite:///app.db"),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    # Configurações de segurança adicionais
    WTF_CSRF_ENABLED=True,
    WTF_CSRF_TIME_LIMIT=3600,  # 1 hora
)

# Carregar configurações adicionais de segurança
# app.config.update(get_security_config())  # Removido pois o módulo não existe mais

# Inicializar extensões
csrf.init_app(app)
limiter.init_app(app)

# Configurar Talisman para headers de segurança
csp = {
    "default-src": ["'self'"],
    "script-src": [
        "'self'",
        "'unsafe-inline'",
        "'unsafe-eval'",  # Necessário para alguns plugins do CKEditor
        "https://cdn.jsdelivr.net",
        "https://code.jquery.com",
        "https://stackpath.bootstrapcdn.com",
        "https://unpkg.com",  # Adicionado para permitir o carregamento do IMask
        "https://cdnjs.cloudflare.com"  # Adicionado para permitir o carregamento do Sortable.js
    ],
    "style-src": [
        "'self'",
        "'unsafe-inline'",
        "https://fonts.googleapis.com",
        "https://cdnjs.cloudflare.com",
        "https://cdn.jsdelivr.net",
        "https://stackpath.bootstrapcdn.com"
    ],
    "img-src": [
        "'self'",
        "data:",
        "https:",
        "http:",  # Necessário para alguns serviços de CEP
        "https://via.placeholder.com"
    ],
    "font-src": [
        "'self'",
        "data:",
        "https://fonts.gstatic.com",
        "https://cdnjs.cloudflare.com",
        "https://stackpath.bootstrapcdn.com"
    ],
    "connect-src": [
        "'self'",
        "https:",
        "http:"  # Necessário para alguns serviços de CEP
    ],
    "frame-ancestors": ["'self'"],  # Proteção contra clickjacking
    "form-action": ["'self'"],  # Restringe para onde os formulários podem enviar dados
    "base-uri": ["'self'"],  # Restringe a tag <base>
    "object-src": ["'none'"],  # Previne injeção de objetos inseguros
}

# Configurações do Talisman
talisman_config = {
    'force_https': False,  # Temporariamente desativado para testes
    'force_https_permanent': False,  # Temporariamente desativado para testes
    'strict_transport_security': True,
    'strict_transport_security_max_age': 31536000,  # 1 ano em segundos
    'strict_transport_security_include_subdomains': True,
    'strict_transport_security_preload': True,
    'session_cookie_secure': True,
    'session_cookie_http_only': True,
    'content_security_policy': csp,
    # 'content_security_policy_nonce_in': ['script-src'],  # Temporariamente desabilitado para permitir eventos inline
    'referrer_policy': 'strict-origin-when-cross-origin',
    'x_content_type_options': True,
    'x_xss_protection': True,
}

# Inicializar Talisman com as configurações de segurança
Talisman(app, **talisman_config)

# Adicionar manualmente o cabeçalho X-Frame-Options, se necessário
@app.after_request
def set_x_frame_options(response):
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    return response

# Headers de segurança adicionais são definidos na função add_security_headers unificada abaixo

# Configurar filtros personalizados do Jinja2
@app.template_filter('safe_json')
def safe_json_filter(obj):
    """Filtro Jinja2 para serialização JSON segura de objetos SQLAlchemy."""
    try:
        # Lazy import to avoid circular dependency
        try:
            from app.peticionador.utils import safe_serialize_model
        except ImportError:
            # Fallback if utils not available
            def safe_serialize_model(obj):
                return str(obj)
        return safe_serialize_model(obj)
    except Exception as e:
        app.logger.warning(f"Erro na serialização JSON segura: {e}")
        return {"error": "Objeto não serializável"}

@app.template_filter('format_cpf')
def format_cpf_filter(cpf):
    """Formata CPF com máscara xxx.xxx.xxx-xx"""
    if not cpf:
        return ""
    cpf = str(cpf).replace(".", "").replace("-", "").replace(" ", "")
    if len(cpf) != 11:
        return cpf
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"

@app.template_filter('format_cnpj')
def format_cnpj_filter(cnpj):
    """Formata CNPJ com máscara xx.xxx.xxx/xxxx-xx"""
    if not cnpj:
        return ""
    cnpj = str(cnpj).replace(".", "").replace("/", "").replace("-", "").replace(" ", "")
    if len(cnpj) != 14:
        return cnpj
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"

@app.template_filter('format_phone')
def format_phone_filter(phone):
    """Formata telefone brasileiro com máscara (xx) xxxxx-xxxx ou (xx) xxxx-xxxx"""
    if not phone:
        return ""
    phone = str(phone).replace("(", "").replace(")", "").replace("-", "").replace(" ", "")
    if len(phone) == 11:
        return f"({phone[:2]}) {phone[2:7]}-{phone[7:]}"
    elif len(phone) == 10:
        return f"({phone[:2]}) {phone[2:6]}-{phone[6:]}"
    return phone

@app.template_filter('format_cep')
def format_cep_filter(cep):
    """Formata CEP com máscara xxxxx-xxx"""
    if not cep:
        return ""
    cep = str(cep).replace("-", "").replace(" ", "")
    if len(cep) != 8:
        return cep
    return f"{cep[:5]}-{cep[5:]}"

@app.template_filter('currency')
def currency_filter(value):
    """Formata valor como moeda brasileira"""
    if value is None:
        return "R$ 0,00"
    try:
        value = float(value)
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return str(value)

@app.template_filter('title_case')
def title_case_filter(text):
    """Aplica title case respeitando preposições em português"""
    try:
        if not text:
            return ""
        
        prepositions = ['de', 'da', 'do', 'das', 'dos', 'e', 'em', 'na', 'no', 'para', 'por', 'com', 'sem', 'sob', 'sobre']
        words = str(text).lower().split()
        
        if not words:
            return ""
        
        # Primeira palavra sempre maiúscula
        result = [words[0].capitalize()]
        
        # Demais palavras: minúsculas se preposição, maiúsculas caso contrário
        for word in words[1:]:
            if word in prepositions:
                result.append(word)
            else:
                result.append(word.capitalize())
        
        return " ".join(result)
    except Exception as e:
        app.logger.warning(f"Erro no filtro title_case: {e}")
        return str(text) if text else ""

@app.template_filter('truncate_smart')
def truncate_smart_filter(text, length=50, suffix='...'):
    """Trunca texto de forma inteligente, evitando cortar palavras"""
    if not text or len(text) <= length:
        return text
    
    truncated = text[:length]
    last_space = truncated.rfind(' ')
    
    if last_space > length * 0.7:  # Se encontrou espaço em posição razoável
        return truncated[:last_space] + suffix
    else:
        return truncated + suffix

# Configurar logging estruturado
from app.logging_config import log_request_info, setup_logging

setup_logging(app, log_level="INFO")

# Importar e registrar o blueprint principal
from app.main import main_bp

app.register_blueprint(main_bp)

# Isentar o blueprint da API da proteção CSRF
csrf.exempt(main_bp)

from app.peticionador import peticionador_bp

app.register_blueprint(peticionador_bp)
csrf.exempt(peticionador_bp)

# Importar e registrar o blueprint da API
from app.api import api_bp
from app.api import routes  # Importa as rotas para registrá-las no blueprint

app.register_blueprint(api_bp)
csrf.exempt(api_bp)

# Registrar blueprints da nova arquitetura (Fase 3)
try:
    from app.api.routes import register_new_api_routes, get_api_status
    
    # Registrar as novas rotas da arquitetura refatorada
    blueprint_count = register_new_api_routes(app)
    
    # Isentar os novos blueprints da proteção CSRF
    from app.api.routes import FEATURE_FLAGS
    if FEATURE_FLAGS.get('NEW_AUTH_API'):
        from app.api.routes.auth import auth_bp
        csrf.exempt(auth_bp)
    
    if FEATURE_FLAGS.get('NEW_CLIENTS_API'):
        from app.api.routes.clients import clients_bp
        csrf.exempt(clients_bp)
    
    app.logger.info(f"🎯 Fase 3 - Nova Arquitetura: {blueprint_count} APIs registradas com sucesso")
    
    # Adicionar endpoint para verificar status da nova arquitetura
    @app.route("/api/architecture-status", methods=["GET"])
    def architecture_status():
        """Endpoint para verificar status da nova arquitetura."""
        try:
            status = get_api_status()
            return jsonify({
                "success": True,
                "data": status,
                "message": "Status da nova arquitetura obtido com sucesso"
            }), 200
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e),
                "message": "Erro ao obter status da nova arquitetura"
            }), 500
    
except ImportError as e:
    app.logger.warning(f"⚠️  Nova arquitetura não disponível: {str(e)}")
except Exception as e:
    app.logger.error(f"❌ Erro ao registrar nova arquitetura: {str(e)}", exc_info=True)


# Rota para favicon
@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        app.static_folder, "favicon.ico", mimetype="image/vnd.microsoft.icon"
    )


from app.peticionador.models import User as PeticionadorUser

# Importar e configurar o banco de dados
from extensions import db, login_manager, migrate

db.init_app(app)
login_manager.init_app(app)
migrate.init_app(app, db)

# A criação de tabelas agora é gerenciada pelo Flask-Migrate
# with app.app_context():
#     db.create_all()

# Configurações de segurança para tentativas de login
MAX_LOGIN_ATTEMPTS = 5  # Número máximo de tentativas
LOGIN_BLOCK_TIME = 300  # 5 minutos em segundos

# Dicionário para rastrear tentativas de login
# Formato: { 'ip': {'count': int, 'blocked_until': datetime} }
login_attempts = {}

# Adicionar o dicionário como atributo da aplicação
app.login_attempts = login_attempts

# Decorador para verificar tentativas de login
def check_attempts(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        ip = request.remote_addr
        now = datetime.now()

        # Verificar se o IP está bloqueado
        if ip in login_attempts and login_attempts[ip].get('blocked_until', now) > now:
            remaining_time = int((login_attempts[ip]['blocked_until'] - now).total_seconds())
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"Muitas tentativas de login. Tente novamente em {remaining_time} segundos.",
                    }
                ),
                429,
            )

        # Se o tempo de bloqueio expirou, resetar as tentativas
        if ip in login_attempts and login_attempts[ip].get('blocked_until', now) <= now:
            login_attempts.pop(ip, None)

        return f(*args, **kwargs)
    return decorated_function

def record_failed_attempt(ip):
    """Registra uma tentativa de login malsucedida e bloqueia o IP se necessário."""
    now = datetime.now()
    
    # Inicializar contador se não existir
    if ip not in current_app.login_attempts:
        current_app.login_attempts[ip] = {'count': 0, 'blocked_until': None}
    
    # Incrementar contador de tentativas
    current_app.login_attempts[ip]['count'] += 1
    
    # Se excedeu o número máximo de tentativas, bloquear
    if current_app.login_attempts[ip]['count'] >= MAX_LOGIN_ATTEMPTS:
        block_until = now + timedelta(seconds=LOGIN_BLOCK_TIME)
        current_app.login_attempts[ip]['blocked_until'] = block_until
        current_app.logger.warning(f"IP {ip} bloqueado até {block_until} por excesso de tentativas de login")
        return True
    
    return False

def clear_login_attempts(ip):
    """Limpa as tentativas de login para um IP específico após login bem-sucedido."""
    if ip in current_app.login_attempts:
        del current_app.login_attempts[ip]
        current_app.logger.info(f"Tentativas de login para IP {ip} foram resetadas após login bem-sucedido")

# Middleware para registrar requisições e timing
@app.before_request
def rate_limit_and_timing():
    # Definir tempo de início para logging
    g.start_time = time.time()
    
    ip = request.remote_addr
    now = datetime.now()

    # Obtém a lista de timestamps para o IP atual, filtrando os antigos.
    requests_for_ip = [
        t
        for t in RATE_LIMIT.get(ip, [])
        if (now - t).total_seconds() <= RATE_LIMIT_WINDOW
    ]

    # Verifica o limite
    if len(requests_for_ip) >= RATE_LIMIT_MAX_REQUESTS:
        return (
            jsonify({"status": "erro", "mensagem": "Limite de requisições excedido"}),
            429,
        )

    # Adiciona o timestamp da requisição atual e atualiza o dicionário
    requests_for_ip.append(now)
    RATE_LIMIT[ip] = requests_for_ip


# Middleware unificado para adicionar headers de segurança e log de resposta
@app.after_request
def add_security_headers(response):
    # Calcular duração de forma segura
    start_time = getattr(g, "start_time", None)
    if start_time:
        duration = time.time() - start_time
    else:
        duration = 0
    
    try:
        # Verificar se a resposta não é streaming antes de tentar acessar get_data()
        if not response.direct_passthrough:
            log_request_info(request, response, duration)
    except Exception as log_exc:
        app.logger.error(f"Erro ao registrar log da resposta: {log_exc}", exc_info=True)
    
    # Headers de segurança básicos
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['X-DNS-Prefetch-Control'] = 'off'
    
    # Configuração CORS para a API
    if request.path.startswith("/api/"):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Credentials"] = "true"
    
    # Prevenção de cache para respostas da API
    if request.path.startswith("/api"):
        response.cache_control.no_store = True
        response.cache_control.max_age = 0
    elif 'Cache-Control' not in response.headers:
        # Cache padrão para outras respostas
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    
    return response

# Configuração de proteção básica contra ataques de força bruta
# Essas variáveis são usadas pelo middleware rate_limit
RATE_LIMIT = {}
RATE_LIMIT_WINDOW = 60  # 1 minuto
RATE_LIMIT_MAX_REQUESTS = 100  # Número máximo de requisições por janela


@app.route("/healthz_check")
def healthz_check():
    """Rota de verificação de saúde da aplicação."""
    try:
        # Verificar se o banco de dados está acessível
        db.session.execute("SELECT 1")
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "ok"
        }), 200
    except Exception as e:
        app.logger.error(f"Erro na verificação de saúde: {str(e)}", exc_info=True)
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500

@app.route("/")
@limiter.limit("100 per day")  # Limite de 100 requisições por dia
@csrf.exempt  # Página inicial pode ser acessada sem CSRF
def home():
    """Rota principal que redireciona para o formulário de cadastro."""
    return redirect(url_for("main.cadastro_de_cliente"))


# Rota removida - usando blueprint main


@app.route("/static/<path:filename>")
@limiter.limit("1000 per hour")  # Limite mais alto para arquivos estáticos
def static_files(filename):
    """Serve arquivos estáticos com headers de cache apropriados."""
    response = send_from_directory(app.static_folder, filename)

    # Configurar cache para arquivos estáticos (1 dia)
    cache_timeout = 60 * 60 * 24  # 1 dia em segundos
    response.cache_control.max_age = cache_timeout
    response.cache_control.public = True

    return response


# CEP API moved to main blueprint to avoid conflicts
# @app.route("/api/cep/<cep>")
# @limiter.limit("10 per minute")  # Limite de 10 requisições por minuto
def _disabled_cep_lookup(cep):
    """Consulta CEP com validação e tratamento de erros."""
    try:
        # Validar formato do CEP (apenas números, 8 dígitos)
        if not cep.isdigit() or len(cep) != 8:
            return jsonify({"status": "erro", "mensagem": "CEP inválido"}), 400

        # Fazer a requisição com timeout
        response = requests.get(
            f"https://viacep.com.br/ws/{cep}/json/", timeout=5  # Timeout de 5 segundos
        )

        # Verificar se a requisição foi bem-sucedida
        response.raise_for_status()

        # Retornar os dados do CEP
        return jsonify(response.json())

    except requests.exceptions.RequestException as e:
        app.logger.error(f"Erro ao consultar CEP {cep}: {str(e)}")
        return (
            jsonify(
                {
                    "status": "erro",
                    "mensagem": "Erro ao consultar CEP. Tente novamente mais tarde.",
                }
            ),
            500,
        )


# Document generation API moved to main blueprint to avoid conflicts
# @app.route("/api/gerar-documento", methods=["POST"])
# @limiter.limit("10 per minute")  # Limite de 10 requisições por minuto
# @require_api_key  # Exige chave de API válida
def _disabled_gerar_documento_api():
    """API para geração de documentos com proteção contra abuso."""
    try:
        # Verificar se o conteúdo é JSON
        if not request.is_json:
            return (
                jsonify({"status": "erro", "mensagem": "Conteúdo deve ser JSON"}),
                400,
            )

        data = request.get_json()

        # Validar dados de entrada
        required_fields = ["nome", "email"]  # Ajuste conforme necessário
        for field in required_fields:
            if field not in data:
                return (
                    jsonify(
                        {
                            "status": "erro",
                            "mensagem": f"Campo obrigatório ausente: {field}",
                        }
                    ),
                    400,
                )

        # Registrar a requisição
        app.logger.info(f"Documento gerado para IP: {request.remote_addr}")

        # Processar a geração do documento
        # ... (código existente)
        # Mapeia campos do frontend para os nomes esperados pelo backend/document_generator
        tipo_pessoa = data.get("tipoPessoa", "pf")
        # Mapeamento dos dados do cliente (como estava antes)
        dados_cliente = {
            "Primeiro Nome": data.get("primeiroNome", ""),
            "Sobrenome": data.get("sobrenome", ""),
            "Nacionalidade": data.get("nacionalidade", "Brasileiro(a)"),
            "RG": data.get("rg", ""),
            "Estado emissor do RG": data.get("estadoEmissorRG", ""),
            "Estado Civil": data.get("estadoCivil", ""),
            "CPF": data.get("cpf", ""),
            "Profissão": data.get("profissao", ""),
            "CNH": data.get("cnh", ""),
            # Novo formato estruturado
            "Logradouro": data.get("logradouro", ""),
            "Número": data.get("numero", ""),
            "Complemento": data.get("complemento", ""),
            # Para compatibilidade com templates antigos, monta o campo completo
            "Endereço": (
                (data.get("logradouro", "") + ", " if data.get("logradouro") else "")
                + (
                    data.get("numero", "") + (", " if data.get("complemento") else "")
                    if data.get("numero")
                    else ""
                )
                + (
                    data.get("complemento", "") + ", "
                    if data.get("complemento")
                    else ""
                )
                + (data.get("bairro", "") if data.get("bairro") else "")
            )
            or data.get("endereco", ""),
            "Bairro": data.get("bairro", ""),
            "Cidade": data.get("cidade", ""),
            "Estado": data.get("estado", ""),
            "CEP": data.get("cep", ""),
            "E-mail": data.get("email", ""),
            "Nascimento": data.get("dataNascimento", ""),
            "Telefone Celular": data.get("telefoneCelular", ""),
            "Outro telefone": data.get("outroTelefone", ""),
        }

        # 1. Buscar ou criar a pasta do cliente UMA VEZ
        primeiro_nome_pasta = dados_cliente.get("Primeiro Nome")
        sobrenome_pasta = dados_cliente.get("Sobrenome")
        ano_atual = datetime.datetime.now().year

        if not primeiro_nome_pasta or not sobrenome_pasta:
            return (
                jsonify(
                    {
                        "status": "erro",
                        "mensagem": "Primeiro nome e Sobrenome são obrigatórios para criar a pasta do cliente.",
                    }
                ),
                400,
            )

        # Inicializar serviços do Google
        from document_generator import _initialize_google_services

        google_credentials_json_str = CONFIG.get("GOOGLE_CREDENTIALS_AS_JSON_STR")
        if not google_credentials_json_str:
            return (
                jsonify(
                    {
                        "status": "erro",
                        "mensagem": "Credenciais do Google não configuradas.",
                    }
                ),
                500,
            )

        drive_service, docs_service = _initialize_google_services(
            google_credentials_json_str
        )

        # Buscar ou criar pasta do cliente (usando a importação global)
        id_pasta_cliente = buscar_ou_criar_pasta_cliente(
            drive_service, primeiro_nome_pasta, sobrenome_pasta, ano_atual
        )

        # 2. Gerar todos os documentos configurados para o tipo_pessoa
        documentos_a_gerar = CONFIG["TEMPLATES"].get(tipo_pessoa, {})
        if not documentos_a_gerar:
            return (
                jsonify(
                    {
                        "status": "erro",
                        "mensagem": f"Nenhum template configurado para tipoPessoa: {tipo_pessoa}",
                    }
                ),
                400,
            )

        links_gerados = []
        erros_ocorridos = []

        for tipo_doc_atual in documentos_a_gerar.keys():
            try:
                # Obter ID do template
                id_template = documentos_a_gerar[tipo_doc_atual]
                if not id_template:
                    app.logger.warning(
                        f"Template ID para '{tipo_doc_atual}' não encontrado. Pulando..."
                    )
                    continue

                # Chamar gerar_documento_cliente com parâmetros corretos
                from document_generator import gerar_documento_cliente

                resultado_doc = gerar_documento_cliente(
                    drive_service=drive_service,
                    docs_service=docs_service,
                    id_template=id_template,
                    tipo_doc=tipo_doc_atual,
                    dados_cliente=dados_cliente,
                    id_pasta_cliente=id_pasta_cliente,
                    tipo_pessoa=tipo_pessoa,
                )

                links_gerados.append(
                    {
                        "tipo_documento": tipo_doc_atual,
                        "link": resultado_doc["link_documento"],
                        "id": resultado_doc["id_documento"],
                        "nome_arquivo": resultado_doc["nome_arquivo"],
                    }
                )
            except Exception as sub_e:
                print(f"--- ERRO AO GERAR DOCUMENTO: {tipo_doc_atual} ---")
                traceback.print_exc()
                print("--- FIM ERRO DOCUMENTO ---")
                erros_ocorridos.append(
                    {"tipo_documento": tipo_doc_atual, "erro": str(sub_e)}
                )

        if erros_ocorridos:
            # Se houve erros, mas também sucessos, retorna ambos
            if links_gerados:
                return (
                    jsonify(
                        {
                            "status": "parcialmente_ok",
                            "links_sucesso": links_gerados,
                            "erros": erros_ocorridos,
                            "id_pasta_cliente": id_pasta_cliente,  # Adicionado para feedback
                        }
                    ),
                    207,
                )  # Multi-Status
            # Se todos falharam
            return (
                jsonify(
                    {
                        "status": "erro_multiplo",
                        "erros": erros_ocorridos,
                        "id_pasta_cliente": id_pasta_cliente,
                    }
                ),
                500,
            )

        return (
            jsonify(
                {
                    "status": "ok",
                    "documentos_gerados": links_gerados,
                    "id_pasta_cliente": id_pasta_cliente,
                }
            ),
            200,
        )
    except Exception as e:
        print("--- TRACEBACK START ---")
        traceback.print_exc()
        print("--- TRACEBACK END ---")
        # app.logger.error(f"Erro em /api/gerar-documento: {traceback.format_exc()}") # Alternativa com logger Flask
        return jsonify({"status": "erro", "mensagem": str(e)}), 500


# Handlers para erros 404 e 500 com log detalhado
@app.errorhandler(404)
def not_found_error(error):
    app.logger.warning(
        f"404 Not Found: {request.path} | IP: {request.remote_addr} | User: {getattr(g, 'user', None)}"
    )
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_error(error):
    import traceback

    tb = traceback.format_exc()
    app.logger.error(
        f"500 Internal Server Error: {request.path} | IP: {request.remote_addr} | User: {getattr(g, 'user', None)} | Traceback: {tb}"
    )
    return render_template("500.html"), 500


@login_manager.user_loader
def load_user(user_id):
    try:
        return PeticionadorUser.query.get(int(user_id))
    except:
        return None


@app.errorhandler(RateLimitExceeded)
def handle_ratelimit_exceeded(e):
    flash("Muitas tentativas de login. Por favor, aguarde alguns minutos antes de tentar novamente.", "error")
    return redirect(url_for('peticionador.login'))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
