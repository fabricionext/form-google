"""
Rotas da API do sistema.
"""

from . import api_bp
from .document_api import register_document_api_routes
from extensions import limiter
from security_middleware import require_api_key

# Registrar as rotas da API de documentos no blueprint
register_document_api_routes(api_bp, limiter, require_api_key)
