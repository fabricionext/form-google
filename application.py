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
    url_for,
)

# Importar extensões de segurança
from flask_limiter import Limiter
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
csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_remote_address, default_limits=["200 per day", "50 per hour"]
)

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
    "script-src": ["'self'", "'unsafe-inline'", "https:"],
    "style-src": [
        "'self'",
        "'unsafe-inline'",
        "https://fonts.googleapis.com",
        "https://cdnjs.cloudflare.com",
        "https://cdn.jsdelivr.net",
    ],
    "img-src": ["'self'", "data:", "https:"],
    "font-src": ["'self'", "data:", "https:"],
    "connect-src": ["'self'", "https:"],
}

Talisman(
    app,
    force_https=True,
    strict_transport_security=True,
    session_cookie_secure=True,
    content_security_policy=csp,
    content_security_policy_nonce_in=["script-src"],
    referrer_policy="strict-origin-when-cross-origin",
)

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

# Registrar rotas da API refatorada
from app.api.document_api import register_document_api_routes

register_document_api_routes(app, limiter, require_api_key)


# Rota para favicon
@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        app.static_folder, "favicon.ico", mimetype="image/vnd.microsoft.icon"
    )


from app.peticionador.models import User as PeticionadorUser

# Importar e configurar o banco de dados
from extensions import db, login_manager

db.init_app(app)
login_manager.init_app(app)
migrate = Migrate(app, db)

# A criação de tabelas agora é gerenciada pelo Flask-Migrate
# with app.app_context():
#     db.create_all()

# Dicionário para rastrear tentativas de login
login_attempts = {}


# Decorador para verificar tentativas de login
def check_attempts(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        ip = request.remote_addr
        now = time.time()

        # Limpar tentativas antigas (últimos 5 minutos)
        if ip in login_attempts:
            login_attempts[ip] = [t for t in login_attempts[ip] if now - t < 300]

            # Bloquear se mais de 5 tentativas em 5 minutos
            if len(login_attempts[ip]) >= 5:
                return (
                    jsonify(
                        {
                            "status": "erro",
                            "mensagem": "Muitas tentativas. Tente novamente em 5 minutos.",
                        }
                    ),
                    429,
                )

        # Registrar tentativa
        if ip not in login_attempts:
            login_attempts[ip] = []
        login_attempts[ip].append(now)

        return f(*args, **kwargs)

    return decorated_function


# Middleware para registrar requisições
@app.before_request
def before_request():
    g.start_time = time.time()
    # Log estruturado da requisição
    app.logger.info(
        "Requisição recebida",
        extra={
            "extra_fields": {
                "ip": request.remote_addr,
                "method": request.method,
                "path": request.path,
                "user_agent": request.headers.get("User-Agent", ""),
                "referer": request.headers.get("Referer", ""),
                "x_forwarded_for": request.headers.get("X-Forwarded-For", ""),
                "x_forwarded_proto": request.headers.get("X-Forwarded-Proto", ""),
            }
        },
    )
    forwarded_proto = request.headers.get("X-Forwarded-Proto", "").lower()
    if not app.debug and forwarded_proto == "http":
        url = request.url.replace("http://", "https://", 1)
        app.logger.info(f"Redirecting to HTTPS (behind proxy): {url}")
        return redirect(url, code=301)
    if forwarded_proto == "https":
        request.environ["wsgi.url_scheme"] = "https"


# Middleware para adicionar headers de segurança e log de resposta
@app.after_request
def add_security_headers(response):
    duration = time.time() - getattr(g, "start_time", time.time())
    try:
        # Verificar se a resposta não é streaming antes de tentar acessar get_data()
        if not response.direct_passthrough:
            log_request_info(request, response, duration)
    except Exception as log_exc:
        app.logger.error(f"Erro ao registrar log da resposta: {log_exc}", exc_info=True)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    # Configurações de CORS - ajuste conforme necessário
    if "Origin" in request.headers:
        response.headers["Access-Control-Allow-Origin"] = (
            "https://appform.estevaoalmeida.com.br"
        )
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Credentials"] = "true"
    # Prevenção de cache para respostas da API
    if request.path.startswith("/api"):
        response.cache_control.no_store = True
        response.cache_control.max_age = 0
    return response


# Proteção básica contra ataques de força bruta
RATE_LIMIT = {}
RATE_LIMIT_WINDOW = 60  # 1 minuto
RATE_LIMIT_MAX_REQUESTS = 30  # 30 requisições por minuto


@app.before_request
def rate_limit():
    if request.path.startswith("/api"):
        client_ip = request.remote_addr
        current_time = int(time.time())

        # Limpar requisições antigas
        if client_ip in RATE_LIMIT:
            RATE_LIMIT[client_ip] = [
                t for t in RATE_LIMIT[client_ip] if t > current_time - RATE_LIMIT_WINDOW
            ]
        else:
            RATE_LIMIT[client_ip] = []

        # Adicionar nova requisição
        RATE_LIMIT[client_ip].append(current_time)

        # Verificar limite
        if len(RATE_LIMIT[client_ip]) > RATE_LIMIT_MAX_REQUESTS:
            app.logger.warning(f"Rate limit excedido para o IP: {client_ip}")
            return (
                jsonify(
                    {
                        "status": "erro",
                        "mensagem": "Muitas requisições. Tente novamente mais tarde.",
                    }
                ),
                429,
            )


@app.route("/")
@limiter.limit("100 per day")  # Limite de 100 requisições por dia
@csrf.exempt  # Página inicial pode ser acessada sem CSRF
def home():
    """Rota principal que redireciona para o formulário de cadastro."""
    # Usando o caminho direto em vez de url_for para evitar problemas de roteamento
    return redirect("/cadastrodecliente")


@app.route("/cadastrodecliente")
@limiter.limit("100 per hour")  # Limite de 100 requisições por hora
def cadastro_de_cliente():
    """Exibe o formulário de cadastro de cliente com proteção CSRF."""
    csrf_token = generate_csrf()
    return render_template("index.html", csrf_token=csrf_token)


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


@app.route("/api/cep/<cep>")
@limiter.limit("10 per minute")  # Limite de 10 requisições por minuto
def cep_lookup(cep):
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


@app.route("/api/gerar-documento", methods=["POST"])
@limiter.limit("10 per minute")  # Limite de 10 requisições por minuto
@require_api_key  # Exige chave de API válida
def gerar_documento_api():
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
