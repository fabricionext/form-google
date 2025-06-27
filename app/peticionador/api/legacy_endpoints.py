"""
Legacy API Endpoints Registration
=================================

Registra todos os endpoints legacy migrados do routes.py
para manter compatibilidade com o frontend existente.
"""

from flask import Blueprint

# Importar todos os blueprints legacy
from .clientes_legacy import clientes_legacy_bp
from .autoridades_legacy import autoridades_legacy_bp
from .formularios_legacy import formularios_legacy_bp

# Criar blueprint principal para endpoints legacy
legacy_api_bp = Blueprint('legacy_api', __name__)

# Registrar todos os sub-blueprints
legacy_api_bp.register_blueprint(clientes_legacy_bp)
legacy_api_bp.register_blueprint(autoridades_legacy_bp)
legacy_api_bp.register_blueprint(formularios_legacy_bp)

__all__ = ['legacy_api_bp']