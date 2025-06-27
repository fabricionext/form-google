"""
Rotas de Autenticação - Nova Arquitetura
========================================

Migradas das rotas legacy para a nova estrutura de Controllers.
Foco em segurança, validação e integração com os Services.
"""

from functools import wraps
from flask import Blueprint, request, jsonify, session, current_app
from flask_login import current_user, login_user, logout_user, login_required
from marshmallow import ValidationError

from app.api.controllers import BaseController
from app.peticionador.models import User
from app.peticionador.forms import LoginForm
from extensions import db, limiter

# Blueprint para rotas de autenticação
auth_bp = Blueprint('auth_api', __name__, url_prefix='/api/auth')


class AuthController(BaseController):
    """Controller para operações de autenticação."""
    
    def __init__(self):
        super().__init__()
    
    def login(self):
        """Autentica usuário e cria sessão."""
        try:
            # Validar dados de entrada
            dados = request.get_json() or {}
            
            if not dados:
                return self.error_response(
                    "Dados de login são obrigatórios",
                    status_code=400
                )
            
            email = dados.get('email', '').strip()
            password = dados.get('password', '')
            remember = dados.get('remember', False)
            
            # Validações básicas
            if not email or not password:
                return self.error_response(
                    "Email e senha são obrigatórios",
                    status_code=400
                )
            
            # Buscar usuário
            user = User.query.filter_by(email=email).first()
            
            if not user or not user.check_password(password):
                current_app.logger.warning(f"Tentativa de login inválida para: {email}")
                return self.error_response(
                    "Email ou senha inválidos",
                    status_code=401
                )
            
            # Realizar login
            login_user(user, remember=remember)
            
            # Atualizar último login
            user.last_login = db.func.now()
            db.session.commit()
            
            current_app.logger.info(f"Login realizado com sucesso: {email}")
            
            return self.success_response(
                data={
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "nome": user.nome
                    },
                    "session_id": session.get('_id')
                },
                message="Login realizado com sucesso"
            )
            
        except ValidationError as e:
            return self.error_response(f"Erro de validação: {e.messages}")
        except Exception as e:
            current_app.logger.error(f"Erro no login: {str(e)}")
            return self.error_response("Erro interno no servidor")
    
    def logout(self):
        """Realiza logout do usuário."""
        try:
            user_email = current_user.email if current_user.is_authenticated else "Anônimo"
            logout_user()
            
            current_app.logger.info(f"Logout realizado: {user_email}")
            
            return self.success_response(
                message="Logout realizado com sucesso"
            )
            
        except Exception as e:
            current_app.logger.error(f"Erro no logout: {str(e)}")
            return self.error_response("Erro interno no servidor")
    
    def get_current_user(self):
        """Retorna dados do usuário autenticado."""
        try:
            if not current_user.is_authenticated:
                return self.error_response(
                    "Usuário não autenticado",
                    status_code=401
                )
            
            return self.success_response(
                data={
                    "user": {
                        "id": current_user.id,
                        "email": current_user.email,
                        "nome": current_user.nome,
                        "last_login": current_user.last_login.isoformat() if current_user.last_login else None,
                        "created_at": current_user.created_at.isoformat() if current_user.created_at else None
                    }
                }
            )
            
        except Exception as e:
            current_app.logger.error(f"Erro ao obter usuário atual: {str(e)}")
            return self.error_response("Erro interno no servidor")


# Instanciar controller
auth_controller = AuthController()


# Decorador para validação de API key
def require_api_key(f):
    """Decorador para validar API key em endpoints específicos."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        expected_key = current_app.config.get('API_KEY')
        
        if not api_key or api_key != expected_key:
            return jsonify({
                'success': False,
                'error': 'API key inválida ou ausente'
            }), 401
        
        return f(*args, **kwargs)
    return decorated_function


# Decorador para controle de permissões
def permission_required(permission):
    """Decorador para validar permissões específicas."""
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if not current_user.has_permission(permission):
                return jsonify({
                    'success': False,
                    'error': f'Permissão {permission} requerida'
                }), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# =============================================================================
# ROTAS DE AUTENTICAÇÃO
# =============================================================================

@auth_bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    """Endpoint de login."""
    return auth_controller.login()


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """Endpoint de logout."""
    return auth_controller.logout()


@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """Endpoint para obter dados do usuário autenticado."""
    return auth_controller.get_current_user()


@auth_bp.route('/validate-session', methods=['GET'])
def validate_session():
    """Valida se a sessão atual é válida."""
    try:
        if current_user.is_authenticated:
            return auth_controller.success_response(
                data={
                    "valid": True,
                    "user": {
                        "id": current_user.id,
                        "email": current_user.email,
                        "nome": current_user.nome
                    }
                }
            )
        else:
            return auth_controller.success_response(
                data={"valid": False}
            )
    except Exception as e:
        current_app.logger.error(f"Erro na validação de sessão: {str(e)}")
        return auth_controller.error_response("Erro interno no servidor") 