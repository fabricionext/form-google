"""
Blueprint público para formulários acessíveis sem autenticação.
"""

from flask import Blueprint

# Blueprint público para formulários
public_bp = Blueprint(
    'public', 
    __name__,
    template_folder='../templates',
    static_folder='../static'
)

from . import routes