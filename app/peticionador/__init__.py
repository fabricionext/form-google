import traceback

from flask import Blueprint, current_app, jsonify, render_template, request
from flask_login import login_required

# Criar o blueprint
peticionador_bp = Blueprint(
    "peticionador",
    __name__,
    url_prefix="/peticionador",
    static_folder="static",
    template_folder="../../templates",
)

# @peticionador_bp.route('/')
# def index():
#     """Página principal do peticionador"""
#     try:
#         current_app.logger.info("Acessando página do peticionador")
#         return render_template('peticionador/index.html')
#     except Exception as e:
#         current_app.logger.error(f"Erro na página do peticionador: {e}")
#         current_app.logger.error(f"Traceback: {traceback.format_exc()}")
#         return f"Erro interno: {str(e)}", 500


# Este endpoint de teste deve ser acessível apenas por usuários autenticados para evitar exposição pública.
# Portanto, adicionamos o decorator `login_required`.
@peticionador_bp.route("/api/test")
@login_required
def api_test():
    """Endpoint de teste para verificar se o blueprint está funcionando"""
    return jsonify(
        {
            "status": "ok",
            "message": "Blueprint peticionador funcionando",
            "blueprint": "peticionador",
        }
    )


# Manipulador de erro específico para este blueprint
@peticionador_bp.errorhandler(404)
def peticionador_not_found(error):
    return (
        jsonify(
            {"status": "erro", "message": "Rota não encontrada no módulo peticionador"}
        ),
        404,
    )


@peticionador_bp.errorhandler(500)
def peticionador_error(error):
    current_app.logger.error(f"Erro 500 no peticionador: {error}")
    # Para requests de API, retorna JSON
    if request.path.startswith("/peticionador/api/") or request.is_json:
        return (
            jsonify({"status": "erro", "message": "Erro interno no módulo peticionador"}),
            500,
        )
    # Para requests web, retorna template HTML se disponível
    try:
        return render_template("peticionador/login.html", 
                             form=None, 
                             error_message="Sistema temporariamente indisponível. Tente novamente."), 500
    except:
        return "Sistema temporariamente indisponível. Tente novamente.", 500


@peticionador_bp.errorhandler(502)
def peticionador_bad_gateway(error):
    current_app.logger.critical(f"Erro 502 (Bad Gateway) no peticionador: {error}")
    # Para requests de API, retorna JSON
    if request.path.startswith("/peticionador/api/") or request.is_json:
        return (
            jsonify({"status": "erro", "message": "Serviço temporariamente indisponível"}),
            502,
        )
    # Para requests web, retorna template HTML se disponível
    try:
        return render_template("peticionador/login.html", 
                             form=None, 
                             error_message="Serviço temporariamente indisponível. Tente novamente em alguns minutos."), 502
    except:
        return "Serviço temporariamente indisponível. Tente novamente em alguns minutos.", 502


# Middleware para monitoramento de erros específicos
@peticionador_bp.before_request
def monitor_requests():
    """Monitora requests para detectar problemas potenciais."""
    try:
        # Log básico de entrada
        current_app.logger.debug(f"Peticionador request: {request.method} {request.path}")
        
        # Removed database health check to prevent deadlocks
        # Database connectivity will be checked by the application health endpoint instead
                
    except Exception as monitor_error:
        # Não deve falhar o request por erro de monitoramento
        current_app.logger.warning(f"Erro no monitoramento de request: {monitor_error}")


from . import forms, models
from . import routes  # ✅ Rotas ativadas para o novo sistema

# Register legacy API endpoints for compatibility
try:
    from .api.legacy_endpoints import legacy_api_bp
    peticionador_bp.register_blueprint(legacy_api_bp)
except ImportError as e:
    print(f"Warning: Could not import legacy_api_bp: {e}")
except Exception as e:
    print(f"Warning: Error registering legacy_api_bp: {e}")

