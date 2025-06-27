# Módulo de APIs
from flask import Blueprint

# Criar o blueprint para a API
api_bp = Blueprint('api', __name__, url_prefix='/api')

from .controllers import (
    BaseController,
    TemplateController,
    DocumentController,
    ClientController,
    FormController
)

__all__ = [
    # ... existing exports ...
    'BaseController',
    'TemplateController', 
    'DocumentController',
    'ClientController',
    'FormController'
]
