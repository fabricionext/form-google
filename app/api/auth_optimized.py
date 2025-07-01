"""
API de Autenticação JWT Otimizada
================================

Implementa endpoints de autenticação usando JWT + CSRF conforme proposta:
- Login/logout JWT
- Renovação de tokens
- Endpoint /me para verificar autenticação
- Integração com RBAC
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token, create_refresh_token, jwt_required, 
    get_jwt_identity, get_jwt, verify_jwt_in_request
)
from flask_wtf.csrf import CSRFProtect
from marshmallow import ValidationError
import logging
from flask_login import current_user

from app.peticionador.models import User
from app.extensions import db
from app.config.jwt_config import require_role

# Blueprint para autenticação JWT
auth_bp = Blueprint('auth_optimized', __name__, url_prefix='/api/auth')

# Configurar CSRF
csrf = CSRFProtect()

logger = logging.getLogger(__name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Endpoint de login JWT otimizado.
    
    Body:
        {
            "email": "user@example.com",
            "password": "password123",
            "remember": false
        }
    
    Returns:
        {
            "access_token": "jwt_token",
            "refresh_token": "refresh_token", 
            "user": {...}
        }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'Dados de login requeridos',
                'message': 'É necessário enviar email e senha.'
            }), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        remember = data.get('remember', False)
        
        # Validações básicas
        if not email or not password:
            return jsonify({
                'error': 'Campos obrigatórios',
                'message': 'Email e senha são obrigatórios.'
            }), 400
        
        # Buscar e validar usuário
        user = User.query.filter_by(email=email).first()
        
        if not user:
            logger.warning(f"Tentativa de login com email inexistente: {email}")
            return jsonify({
                'error': 'Credenciais inválidas',
                'message': 'Email ou senha incorretos.'
            }), 401
        
        if not user.check_password(password):
            logger.warning(f"Tentativa de login com senha incorreta: {email}")
            return jsonify({
                'error': 'Credenciais inválidas', 
                'message': 'Email ou senha incorretos.'
            }), 401
        
        if not getattr(user, 'is_active', True):
            return jsonify({
                'error': 'Conta inativa',
                'message': 'Sua conta está desativada. Entre em contato com o suporte.'
            }), 401
        
        # Criar tokens JWT
        additional_claims = {
            'role': getattr(user, 'role', 'user'),
            'email': user.email,
            'name': getattr(user, 'name', getattr(user, 'nome', ''))
        }
        
        access_token = create_access_token(
            identity=user.id,
            additional_claims=additional_claims,
            fresh=True
        )
        
        refresh_token = create_refresh_token(identity=user.id)
        
        # Atualizar último login
        user.last_login = db.func.now()
        db.session.commit()
        
        logger.info(f"Login JWT realizado com sucesso: {email}")
        
        return jsonify({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': user.id,
                'email': user.email,
                'name': getattr(user, 'name', getattr(user, 'nome', '')),
                'role': getattr(user, 'role', 'user'),
                'last_login': user.last_login.isoformat() if user.last_login else None
            },
            'message': 'Login realizado com sucesso'
        }), 200
        
    except Exception as e:
        logger.error(f"Erro no login JWT: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Erro interno',
            'message': 'Erro interno do servidor. Tente novamente.'
        }), 500


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Renovar token de acesso usando refresh token.
    
    Headers:
        Authorization: Bearer <refresh_token>
    
    Returns:
        {
            "access_token": "new_jwt_token"
        }
    """
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or not getattr(user, 'is_active', True):
            return jsonify({
                'error': 'Usuário inválido',
                'message': 'Usuário não encontrado ou inativo.'
            }), 401
        
        # Criar novo access token
        additional_claims = {
            'role': getattr(user, 'role', 'user'),
            'email': user.email,
            'name': getattr(user, 'name', getattr(user, 'nome', ''))
        }
        
        new_access_token = create_access_token(
            identity=current_user_id,
            additional_claims=additional_claims
        )
        
        return jsonify({
            'access_token': new_access_token,
            'message': 'Token renovado com sucesso'
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao renovar token: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Erro ao renovar token',
            'message': 'Não foi possível renovar o token.'
        }), 500


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    """
    Obter dados do usuário autenticado.
    
    Headers:
        Authorization: Bearer <access_token>
    
    Returns:
        {
            "user": {...},
            "claims": {...}
        }
    """
    try:
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({
                'error': 'Usuário não encontrado',
                'message': 'Usuário não existe mais no sistema.'
            }), 404
        
        return jsonify({
            'user': {
                'id': user.id,
                'email': user.email,
                'name': getattr(user, 'name', getattr(user, 'nome', '')),
                'role': claims.get('role', 'user'),
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'is_active': getattr(user, 'is_active', True)
            },
            'claims': {
                'role': claims.get('role'),
                'permissions': claims.get('permissions', [])
            },
            'token_info': {
                'issued_at': claims.get('iat'),
                'expires_at': claims.get('exp')
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter dados do usuário: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Erro interno',
            'message': 'Não foi possível obter dados do usuário.'
        }), 500


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    Logout (invalidar token).
    
    No JWT stateless, o logout é feito no frontend removendo o token.
    Este endpoint serve para logging e possível blacklist futura.
    """
    try:
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        
        logger.info(f"Logout realizado para usuário ID: {current_user_id}")
        
        # TODO: Implementar blacklist de tokens se necessário
        # Por ora, apenas retorna sucesso
        
        return jsonify({
            'message': 'Logout realizado com sucesso',
            'info': 'Token invalidado no cliente'
        }), 200
        
    except Exception as e:
        logger.error(f"Erro no logout: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Erro no logout',
            'message': 'Erro interno durante logout.'
        }), 500


@auth_bp.route('/check', methods=['GET'])
def check_auth():
    """
    Verificar se o token está presente e válido (sem exigir).
    
    Útil para o frontend verificar se o usuário está logado.
    """
    try:
        verify_jwt_in_request(optional=True)
        current_user_id = get_jwt_identity()
        
        if current_user_id:
            return jsonify({
                'authenticated': True,
                'user_id': current_user_id
            }), 200
        else:
            return jsonify({
                'authenticated': False
            }), 200
            
    except Exception:
        return jsonify({
            'authenticated': False
        }), 200


@auth_bp.route('/status', methods=['GET'])
def status():
    """
    Verifica o status de autenticação do usuário com base no cookie de sessão.
    """
    if current_user.is_authenticated:
        return jsonify({
            "logged_in": True,
            "user": {
                "id": current_user.id,
                "email": current_user.email,
                "name": current_user.name,
                "roles": ["admin"] # Substituir por lógica de roles real se aplicável
            }
        }), 200
    else:
        return jsonify({"logged_in": False}), 200


# Error handlers específicos para este blueprint
@auth_bp.errorhandler(ValidationError)
def handle_validation_error(e):
    """Handler para erros de validação."""
    return jsonify({
        'error': 'Dados inválidos',
        'message': 'Os dados enviados são inválidos.',
        'details': e.messages
    }), 400


@auth_bp.errorhandler(Exception)
def handle_generic_error(e):
    """Handler genérico para erros."""
    logger.error(f"Erro não tratado na API de auth: {str(e)}", exc_info=True)
    return jsonify({
        'error': 'Erro interno',
        'message': 'Erro interno do servidor.'
    }), 500 