import datetime
import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask, g, redirect, request
from flask_talisman import Talisman
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.routing import BaseConverter
import uuid

from .extensions import db, login_manager, csrf, limiter, migrate
from app.peticionador.models import User as PeticionadorUser

logging.basicConfig(level=logging.DEBUG)  # Ensure basicConfig is called if not already

class UUIDConverter(BaseConverter):
    def to_python(self, value):
        try:
            return uuid.UUID(value)
        except ValueError:
            raise ValidationError(self.map, f"Invalid UUID: {value}")

    def to_url(self, value):
        return str(value)

def create_app(config_object=None):
    logging.debug("APP/__INIT__.PY: ENTERING create_app()")
    logging.debug("APP/__INIT__.PY: About to create Flask app object")
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
        instance_relative_config=True,
    )
    app.url_map.converters['uuid'] = UUIDConverter
    logging.debug("APP/__INIT__.PY: Flask app object created")
    # ----------------------
    # Carregamento de configuração
    # ----------------------
    if config_object is None:
        # Determina ambiente a partir da variável FLASK_CONFIG ou "development" como padrão
        # Prioriza FLASK_CONFIG; se ausente, usa FLASK_ENV para manter compatibilidade
        env_name = os.getenv("FLASK_CONFIG") or os.getenv("FLASK_ENV", "development")
        env_name = env_name.lower()
        from app.config.settings import CONFIG_MAP

        config_object = CONFIG_MAP.get(env_name, CONFIG_MAP["default"])
        logging.debug(
            f'APP/__INIT__.PY: Carregando configuração baseada em classe para env "{env_name}" -> {config_object}'
        )

    if isinstance(config_object, dict):
        app.config.from_mapping(config_object)
    else:
        app.config.from_object(config_object)
    logging.debug("APP/__INIT__.PY: Configuração carregada no app")
    
    # Adicionar ProxyFix para lidar com headers X-Forwarded-*
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    
    # Inicializa as extensões
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    limiter.init_app(app)
    login_manager.init_app(app)
    
    # Configurar CORS para desenvolvimento local
    CORS(app, resources={
        r"/api/*": {"origins": "*"},
        r"/health": {"origins": "*"}  # Permitir health check
    })

    # ----------------------
    # Configuração de segurança
    # ----------------------
    # CSP condicional baseado no ambiente
    if app.config.get('FLASK_ENV') == 'development' or app.debug:
        # CSP mais permissiva para desenvolvimento
        csp_config = {
            'default-src': "'self' 'unsafe-inline' 'unsafe-eval' data: blob: *",
            'script-src': "'self' 'unsafe-inline' 'unsafe-eval' *",
            'style-src': "'self' 'unsafe-inline' *",
            'img-src': "'self' data: blob: *",
            'font-src': "'self' data: *",
            'connect-src': "'self' *"
        }
        talisman = Talisman(
            app,
            force_https=False,
            strict_transport_security=False,
            content_security_policy=csp_config,
            content_security_policy_nonce_in=[]
        )
    else:
        # CSP gerenciada pelo nginx para produção - sem CSP duplicada no Flask
        talisman = Talisman(
            app,
            force_https=False,  
            strict_transport_security=False,
            content_security_policy=False,  # Desabilita CSP do Flask (nginx gerencia)
            content_security_policy_nonce_in=[]
        )

    # Registrar comandos CLI
    from . import commands as app_commands

    app.cli.add_command(app_commands.import_clients_cli)
    app.cli.add_command(app_commands.find_client_by_cpf_cli)
    app.cli.add_command(app_commands.find_client_by_email_cli)

    login_manager.login_view = "peticionador.login"
    login_manager.login_message = "Por favor, realize o login para acessar esta página."
    login_manager.login_message_category = "info"

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(PeticionadorUser, int(user_id))

    from app.peticionador import peticionador_bp
    
    # Temporarily disable problematic API and schemas
    try:
        from app.peticionador.api import api_bp
        from app.extensions import ma
        # Inicializar Marshmallow
        if ma:
            ma.init_app(app)
        # STEP 7: Configure JWT + CORS (Solução Otimizada)
        from app.config.jwt_config import configure_jwt
        jwt = configure_jwt(app)
        
        # STEP 8: Register API blueprints (Estrutura Otimizada)
        from app.api.auth_optimized import auth_bp
        from app.api.public_api import public_bp
        from app.api.admin_api import admin_bp
        
        # Registro da API refatorada (legacy)
        app.register_blueprint(api_bp)
        
        # Registro das novas APIs JWT otimizadas
        app.register_blueprint(auth_bp)     # APIs de autenticação JWT
        app.register_blueprint(public_bp)   # APIs públicas (sem auth)
        app.register_blueprint(admin_bp)    # APIs administrativas (JWT required)
    except Exception as e:
        app.logger.warning(f"Could not register API/schemas: {e}")

    # Registro do blueprint Peticionador
    # O próprio blueprint já define url_prefix='/peticionador', portanto não passamos novamente
    app.register_blueprint(peticionador_bp)
    
    # Registro do blueprint público (sem autenticação)
    try:
        from app.public import public_bp
        app.register_blueprint(public_bp)
        app.logger.info("Public routes registered successfully")
    except Exception as e:
        app.logger.warning(f"Could not register public routes: {e}")

    # Registro das APIs REST com ENUMs - Fase 2
    try:
        from app.api.routes.templates import templates_bp
        app.register_blueprint(templates_bp)
        app.logger.info("Template API routes registered successfully")
    except Exception as e:
        app.logger.warning(f"Could not register Template API routes: {e}")

    # CSRF proteção habilitada para peticionador (login requer CSRF)
    # csrf.exempt(peticionador_bp)  # Removido para permitir login
    try:
        csrf.exempt(api_bp)
        csrf.exempt(templates_bp)
    except:
        pass

    from app.main import main_bp
    app.register_blueprint(main_bp)

    if not app.debug and not app.testing:
        if not os.path.exists("logs"):
            os.mkdir("logs")
        file_handler = RotatingFileHandler(
            "logs/app.log", maxBytes=10240, backupCount=10
        )
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
            )
        )
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info("Aplicação Form-Google iniciada")

    @app.context_processor
    def inject_current_year():
        return {"current_year": datetime.datetime.now().year}

    @app.before_request
    def before_request_logging():
        g.start_time = getattr(g, "start_time", datetime.datetime.utcnow())
        if app.debug:
            app.logger.debug(
                f"Request: {request.method} {request.path} from {request.remote_addr}"
            )
            app.logger.debug(f"Headers: {request.headers}")
            app.logger.debug(f"Body: {request.get_data(as_text=True)}")

    @app.after_request
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        if "Origin" in request.headers and request.headers["Origin"] == app.config.get(
            "ALLOWED_ORIGIN", "https://appform.estevaoalmeida.com.br"
        ):
            response.headers["Access-Control-Allow-Origin"] = app.config.get(
                "ALLOWED_ORIGIN"
            )
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = (
                "Content-Type, Authorization, X-CSRFToken"
            )
            response.headers["Access-Control-Allow-Credentials"] = "true"

        if request.path.startswith("/api"):
            response.cache_control.no_store = True
            response.cache_control.max_age = 0
            response.cache_control.must_revalidate = True
            response.cache_control.no_cache = True
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        if hasattr(g, "start_time"):
            response_time_ms = (
                datetime.datetime.utcnow() - g.start_time
            ).total_seconds() * 1000
            app.logger.info(
                f"Response: {response.status_code} for {request.method} {request.path} in {response_time_ms:.2f}ms"
            )

        return response

    # ----------------------
    # Rota de Health Check Central
    # ----------------------
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check central da aplicação."""
        try:
            # Verificar conexão com banco de dados
            db.session.execute("SELECT 1")
            
            return {
                'status': 'healthy',
                'timestamp': datetime.datetime.utcnow().isoformat(),
                'database': 'ok',
                'version': app.config.get('VERSION', '1.0.0')
            }, 200
            
        except Exception as e:
            app.logger.error(f"Health check falhou: {str(e)}")
            return {
                'status': 'unhealthy',
                'timestamp': datetime.datetime.utcnow().isoformat(),
                'error': str(e)
            }, 503

    return app
