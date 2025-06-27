# Standard library imports

# Third party imports
from flask import Blueprint
from flask_restx import Api

# Create blueprint for API routes
api_bp = Blueprint("peticionador_api", __name__, url_prefix="/api/v1")

# Create Flask-RESTX API instance
api = Api(
    api_bp,
    version="1.0",
    title="Peticionador API",
    description="API para gerenciamento de petições e formulários dinâmicos",
    doc="/docs/",
    authorizations={
        "Bearer": {"type": "apiKey", "in": "header", "name": "Authorization"},
        "session": {"type": "apiKey", "in": "cookie", "name": "session"},
    },
    security=["Bearer", "session"],
)

from .auth import auth_ns

# Import and register namespaces
from .clientes import clientes_ns
from .formularios import formularios_ns
from .modelos import modelos_ns

# Add namespaces to API
api.add_namespace(auth_ns, path="/auth")
api.add_namespace(clientes_ns, path="/clientes")
api.add_namespace(modelos_ns, path="/modelos")
api.add_namespace(formularios_ns, path="/formularios")

__all__ = ["api_bp", "api"]
