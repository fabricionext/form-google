import traceback

from flask import Blueprint, current_app, jsonify, render_template, request

# Criar o blueprint
peticionador_bp = Blueprint(
    "peticionador", __name__, url_prefix="/peticionador", static_folder="static"
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


@peticionador_bp.route("/api/test")
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
    return (
        jsonify({"status": "erro", "message": "Erro interno no módulo peticionador"}),
        500,
    )


from . import forms, models, routes
