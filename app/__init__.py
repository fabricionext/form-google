import datetime
import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask, g, redirect, request

from app.peticionador.models import AutoridadeTransito
from app.peticionador.models import User as PeticionadorUser
from config import CONFIG
from extensions import csrf, db, limiter, login_manager, talisman
from models import RespostaForm

logging.basicConfig(level=logging.DEBUG)  # Ensure basicConfig is called if not already

db = db
login_manager = login_manager


def create_app(config_object=None):
    logging.debug("APP/__INIT__.PY: ENTERING create_app()")
    logging.debug("APP/__INIT__.PY: About to create Flask app object")
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
        instance_relative_config=True,
    )
    logging.debug("APP/__INIT__.PY: Flask app object created")
    # ----------------------
    # Carregamento de configuração
    # ----------------------
    if config_object is None:
        # Determina ambiente a partir da variável FLASK_CONFIG ou "development" como padrão
        # Prioriza FLASK_CONFIG; se ausente, usa FLASK_ENV para manter compatibilidade
        env_name = os.getenv("FLASK_CONFIG") or os.getenv("FLASK_ENV", "development")
        env_name = env_name.lower()
        from config import config_by_name

        config_object = config_by_name.get(env_name, config_by_name["default"])
        logging.debug(
            f'APP/__INIT__.PY: Carregando configuração baseada em classe para env "{env_name}" -> {config_object}'
        )

    if isinstance(config_object, dict):
        app.config.from_mapping(config_object)
    else:
        app.config.from_object(config_object)
    logging.debug("APP/__INIT__.PY: Configuração carregada no app")
    # Registrar comandos CLI
    from . import commands as app_commands

    app.cli.add_command(app_commands.import_clients_cli)
    app.cli.add_command(app_commands.find_client_by_cpf_cli)
    app.cli.add_command(app_commands.find_client_by_email_cli)

    db.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    login_manager.init_app(app)
    # talisman.init_app(app, # Temporariamente comentado
    #                   force_https=app.config.get('TALISMAN_FORCE_HTTPS', True),
    #                   content_security_policy=app.config.get('TALISMAN_CSP_POLICY', {
    #                       'default-src': ["'self'"],
    #                       'script-src': ["'self'", "'unsafe-inline'", "https:"],
    #                       'style-src': ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com", "https://cdnjs.cloudflare.com"],
    #                       'img-src': ["'self'", "data:", "https:"],
    #                       'font-src': ["'self'", "data:", "https:"],
    #                       'connect-src': ["'self'", "https:"]
    #                   }),
    #                   content_security_policy_nonce_in=['script-src'],
    #                   referrer_policy='strict-origin-when-cross-origin',
    #                   session_cookie_secure=app.config.get('SESSION_COOKIE_SECURE', True)
    #                  )

    login_manager.login_view = "peticionador.login"
    login_manager.login_message = "Por favor, realize o login para acessar esta página."
    login_manager.login_message_category = "info"

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(PeticionadorUser, int(user_id))

    from app.peticionador import peticionador_bp

    # Registro do blueprint Peticionador
    # O próprio blueprint já define url_prefix='/peticionador', portanto não passamos novamente
    app.register_blueprint(peticionador_bp)

    # Isentar o blueprint do peticionador da proteção CSRF temporariamente
    csrf.exempt(peticionador_bp)

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

    @app.before_request
    def ensure_https_behind_proxy():
        forwarded_proto = request.headers.get("X-Forwarded-Proto", "").lower()
        if not app.debug and forwarded_proto == "http":
            url = request.url.replace("http://", "https://", 1)
            app.logger.info(f"Redirecionando para HTTPS (proxy): {url}")
            return redirect(url, code=301)
        if forwarded_proto == "https":
            request.environ["wsgi.url_scheme"] = "https"

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

    return app
