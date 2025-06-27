"""
Módulo de Segurança - Autenticação e Autorização
===============================================

Decoradores e utilitários para controle de acesso da nova API.
"""

from .decorators import permission_required, require_api_key

__all__ = [
    'permission_required',
    'require_api_key'
] 