"""
Configuração JWT Otimizada
=========================

Implementa sistema JWT + CSRF híbrido conforme proposta do usuário:
- JWT para stateless authentication 
- CSRF para proteção adicional
- RBAC preparado para escalabilidade
"""

import os
from datetime import timedelta
from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS


class JWTConfig:
    """Configuração centralizada do JWT."""
    
    # JWT Settings
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'dev-jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # Security Headers
    JWT_ALGORITHM = 'HS256'
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    
    # CORS Settings para SPA
    CORS_ORIGINS = [
        'https://appform.estevaoalmeida.com.br',
        'http://localhost:3000',  # Vue.js dev
        'http://localhost:5173',  # Vite dev
    ]


def configure_jwt(app: Flask) -> JWTManager:
    """
    Configura JWT + CORS otimizado para SPA.
    
    Args:
        app: Instância Flask
        
    Returns:
        JWTManager configurado
    """
    # Configurar JWT
    app.config['JWT_SECRET_KEY'] = JWTConfig.JWT_SECRET_KEY
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = JWTConfig.JWT_ACCESS_TOKEN_EXPIRES
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = JWTConfig.JWT_REFRESH_TOKEN_EXPIRES
    app.config['JWT_ALGORITHM'] = JWTConfig.JWT_ALGORITHM
    
    jwt = JWTManager(app)
    
    # Configurar CORS otimizado para SPA
    CORS(app, 
         origins=JWTConfig.CORS_ORIGINS,
         supports_credentials=True,
         allow_headers=['Content-Type', 'Authorization', 'X-CSRFToken'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
    
    # Error handlers customizados
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return {
            'error': 'Token expirado',
            'message': 'O token de acesso expirou. Faça login novamente.',
            'code': 'TOKEN_EXPIRED'
        }, 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error_string):
        return {
            'error': 'Token inválido',
            'message': 'Token de acesso inválido ou malformado.',
            'code': 'INVALID_TOKEN'
        }, 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error_string):
        return {
            'error': 'Token de acesso requerido',
            'message': 'É necessário fazer login para acessar este recurso.',
            'code': 'MISSING_TOKEN'
        }, 401
    
    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return {
            'error': 'Token revogado',
            'message': 'O token de acesso foi revogado. Faça login novamente.',
            'code': 'TOKEN_REVOKED'
        }, 401
    
    @jwt.additional_claims_loader
    def add_claims_to_access_token(identity):
        """Adiciona claims customizados ao token."""
        # Aqui você pode buscar roles/permissões do usuário
        # Por enquanto, retorna role padrão
        from app.peticionador.models import User
        user = User.query.get(identity)
        
        return {
            'role': getattr(user, 'role', 'user'),
            'email': getattr(user, 'email', ''),
            'permissions': getattr(user, 'permissions', [])
        }
    
    app.logger.info("JWT + CORS configurado com sucesso")
    return jwt


def require_role(role: str):
    """
    Decorator para RBAC (Role-Based Access Control).
    
    Usage:
        @require_role('admin')
        def admin_endpoint():
            pass
    """
    from functools import wraps
    from flask_jwt_extended import jwt_required, get_jwt
    from flask import jsonify
    
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            claims = get_jwt()
            user_role = claims.get('role', 'user')
            
            # Hierarquia de roles: admin > editor > viewer > user
            role_hierarchy = {
                'admin': 4,
                'editor': 3, 
                'viewer': 2,
                'user': 1
            }
            
            required_level = role_hierarchy.get(role, 1)
            user_level = role_hierarchy.get(user_role, 1)
            
            if user_level < required_level:
                return jsonify({
                    'error': 'Permissão insuficiente',
                    'message': f'É necessário ser {role} para acessar este recurso.',
                    'required_role': role,
                    'user_role': user_role
                }), 403
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator 