"""
Decoradores de Segurança - Nova API
===================================

Decoradores para autenticação e autorização da nova arquitetura.
"""

from functools import wraps
from flask import request, jsonify, current_app
from typing import Optional, List


def permission_required(permission: str):
    """
    Decorator para verificar permissões.
    
    Args:
        permission: Permissão necessária (ex: 'clients:read', 'templates:create')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # TODO: Implementar verificação real de permissões
                # Por enquanto, permitir tudo para testes
                
                # Simular usuário logado para testes
                request.user_id = 1
                request.is_admin = True
                
                return f(*args, **kwargs)
                
            except Exception as e:
                current_app.logger.error(f"Erro na verificação de permissão {permission}: {str(e)}")
                return jsonify({
                    'success': False,
                    'message': 'Erro de autorização'
                }), 403
                
        return decorated_function
    return decorator


def require_api_key(f):
    """
    Decorator para exigir API key.
    
    Para uso futuro com API keys.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # TODO: Implementar verificação de API key
            # Por enquanto, permitir tudo para testes
            return f(*args, **kwargs)
            
        except Exception as e:
            current_app.logger.error(f"Erro na verificação de API key: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'API key inválida'
            }), 401
            
    return decorated_function


def admin_required(f):
    """
    Decorator para exigir privilégios de administrador.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # TODO: Implementar verificação real de admin
            # Por enquanto, permitir tudo para testes
            request.is_admin = True
            
            return f(*args, **kwargs)
            
        except Exception as e:
            current_app.logger.error(f"Erro na verificação de admin: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Acesso de administrador necessário'
            }), 403
            
    return decorated_function


def rate_limit_per_user(limit: str):
    """
    Decorator para rate limiting por usuário.
    
    Args:
        limit: Limite no formato "10/minute", "100/hour", etc.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # TODO: Implementar rate limiting por usuário
                # Por enquanto, permitir tudo para testes
                return f(*args, **kwargs)
                
            except Exception as e:
                current_app.logger.error(f"Erro no rate limiting: {str(e)}")
                return jsonify({
                    'success': False,
                    'message': 'Limite de requisições excedido'
                }), 429
                
        return decorated_function
    return decorator 