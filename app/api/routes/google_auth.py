"""
Rotas de autenticação OAuth 2.0 para Google Drive.
"""

import logging
from flask import Blueprint, request, jsonify, session, redirect, url_for, current_app
from flask_login import login_required, current_user

from app.services.google_auth_service import google_auth_service
from app.utils.exceptions import AuthenticationException, GoogleDriveException
from app.extensions import limiter

logger = logging.getLogger(__name__)

# Blueprint para autenticação Google
google_auth_bp = Blueprint('google_auth', __name__, url_prefix='/api/google')


@google_auth_bp.route('/auth/status', methods=['GET'])
@limiter.limit("30 per minute")
@login_required
def auth_status():
    """
    Verifica status de autenticação do usuário atual.
    
    Returns:
        JSON com status de autenticação e informações do usuário
    """
    try:
        user_id = str(current_user.id)
        
        is_authenticated = google_auth_service.is_authenticated(user_id)
        
        response_data = {
            'authenticated': is_authenticated,
            'user_id': user_id,
            'timestamp': google_auth_service.test_connection(user_id).get('connection_time')
        }
        
        if is_authenticated:
            # Obtém informações do usuário Google
            user_info = google_auth_service.get_user_info(user_id)
            if user_info:
                response_data['google_user'] = user_info
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Erro ao verificar status de autenticação: {e}")
        return jsonify({
            'authenticated': False,
            'error': 'Erro interno do servidor',
            'timestamp': None
        }), 500


@google_auth_bp.route('/auth/start', methods=['POST'])
@limiter.limit("10 per minute")
@login_required
def start_auth():
    """
    Inicia processo de autenticação OAuth 2.0.
    
    Returns:
        JSON com URL de autorização do Google
    """
    try:
        user_id = str(current_user.id)
        
        # URL de callback
        redirect_uri = url_for('google_auth.auth_callback', _external=True)
        
        # Gera URL de autorização
        auth_url = google_auth_service.get_authorization_url(user_id, redirect_uri)
        
        # Salva user_id na sessão para validação no callback
        session['auth_user_id'] = user_id
        
        logger.info(f"Autenticação iniciada para usuário {user_id}")
        
        return jsonify({
            'auth_url': auth_url,
            'redirect_uri': redirect_uri,
            'user_id': user_id
        }), 200
        
    except AuthenticationException as e:
        logger.error(f"Erro de autenticação: {e}")
        return jsonify({
            'error': 'Erro na autenticação',
            'message': str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"Erro inesperado ao iniciar autenticação: {e}")
        return jsonify({
            'error': 'Erro interno do servidor',
            'message': 'Falha ao iniciar autenticação'
        }), 500


@google_auth_bp.route('/auth/callback', methods=['GET'])
@limiter.limit("10 per minute")
def auth_callback():
    """
    Processa callback de autenticação OAuth 2.0.
    
    Returns:
        Redirecionamento para frontend com status
    """
    try:
        # Verifica se há erro na resposta
        error = request.args.get('error')
        if error:
            logger.warning(f"Erro no callback OAuth: {error}")
            return redirect(f"{current_app.config.get('FRONTEND_URL', 'http://localhost')}/auth/error?error={error}")
        
        # Obtém código de autorização
        code = request.args.get('code')
        if not code:
            logger.error("Código de autorização não fornecido")
            return redirect(f"{current_app.config.get('FRONTEND_URL', 'http://localhost')}/auth/error?error=no_code")
        
        # Verifica user_id na sessão
        user_id = session.get('auth_user_id')
        if not user_id:
            logger.error("User ID não encontrado na sessão")
            return redirect(f"{current_app.config.get('FRONTEND_URL', 'http://localhost')}/auth/error?error=session_expired")
        
        # URL de callback
        redirect_uri = url_for('google_auth.auth_callback', _external=True)
        
        # Processa autenticação
        success = google_auth_service.handle_callback(user_id, code, redirect_uri)
        
        if success:
            logger.info(f"Autenticação concluída com sucesso para usuário {user_id}")
            
            # Remove user_id da sessão
            session.pop('auth_user_id', None)
            
            # Redireciona para frontend com sucesso
            return redirect(f"{current_app.config.get('FRONTEND_URL', 'http://localhost')}/auth/success")
        else:
            logger.error(f"Falha na autenticação para usuário {user_id}")
            return redirect(f"{current_app.config.get('FRONTEND_URL', 'http://localhost')}/auth/error?error=auth_failed")
    
    except AuthenticationException as e:
        logger.error(f"Erro de autenticação no callback: {e}")
        return redirect(f"{current_app.config.get('FRONTEND_URL', 'http://localhost')}/auth/error?error=auth_exception")
        
    except Exception as e:
        logger.error(f"Erro inesperado no callback: {e}")
        return redirect(f"{current_app.config.get('FRONTEND_URL', 'http://localhost')}/auth/error?error=internal_error")


@google_auth_bp.route('/auth/revoke', methods=['POST'])
@limiter.limit("5 per minute")
@login_required
def revoke_auth():
    """
    Revoga autenticação do usuário atual.
    
    Returns:
        JSON confirmando revogação
    """
    try:
        user_id = str(current_user.id)
        
        success = google_auth_service.revoke_access(user_id)
        
        if success:
            logger.info(f"Acesso revogado para usuário {user_id}")
            return jsonify({
                'revoked': True,
                'message': 'Acesso ao Google Drive revogado com sucesso'
            }), 200
        else:
            logger.warning(f"Falha ao revogar acesso para usuário {user_id}")
            return jsonify({
                'revoked': False,
                'message': 'Erro ao revogar acesso'
            }), 400
    
    except Exception as e:
        logger.error(f"Erro ao revogar autenticação: {e}")
        return jsonify({
            'revoked': False,
            'error': 'Erro interno do servidor'
        }), 500


@google_auth_bp.route('/test-connection', methods=['POST'])
@limiter.limit("20 per minute")
@login_required
def test_connection():
    """
    Testa conexão com Google Drive do usuário atual.
    
    Returns:
        JSON com informações da conexão
    """
    try:
        user_id = str(current_user.id)
        
        connection_info = google_auth_service.test_connection(user_id)
        
        return jsonify(connection_info), 200
        
    except AuthenticationException as e:
        logger.error(f"Erro de autenticação no teste: {e}")
        return jsonify({
            'authenticated': False,
            'error': 'Usuário não autenticado',
            'message': str(e)
        }), 401
        
    except GoogleDriveException as e:
        logger.error(f"Erro do Google Drive no teste: {e}")
        return jsonify({
            'authenticated': False,
            'error': 'Erro de conexão com Google Drive',
            'message': str(e)
        }), 503
        
    except Exception as e:
        logger.error(f"Erro inesperado no teste de conexão: {e}")
        return jsonify({
            'authenticated': False,
            'error': 'Erro interno do servidor'
        }), 500


@google_auth_bp.route('/user-info', methods=['GET'])
@limiter.limit("30 per minute")
@login_required
def get_user_info():
    """
    Obtém informações do usuário Google autenticado.
    
    Returns:
        JSON com informações do usuário
    """
    try:
        user_id = str(current_user.id)
        
        if not google_auth_service.is_authenticated(user_id):
            return jsonify({
                'authenticated': False,
                'message': 'Usuário não autenticado no Google Drive'
            }), 401
        
        user_info = google_auth_service.get_user_info(user_id)
        
        if user_info:
            return jsonify({
                'authenticated': True,
                'user': user_info
            }), 200
        else:
            return jsonify({
                'authenticated': False,
                'message': 'Erro ao obter informações do usuário'
            }), 500
            
    except Exception as e:
        logger.error(f"Erro ao obter informações do usuário: {e}")
        return jsonify({
            'authenticated': False,
            'error': 'Erro interno do servidor'
        }), 500


# Middleware para verificação de autenticação Google
def require_google_auth(f):
    """
    Decorator para rotas que requerem autenticação Google.
    
    Args:
        f: Função da rota
        
    Returns:
        Função decorada
    """
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({
                'error': 'Login requerido',
                'message': 'Usuário deve estar logado'
            }), 401
        
        user_id = str(current_user.id)
        
        if not google_auth_service.is_authenticated(user_id):
            return jsonify({
                'error': 'Autenticação Google requerida',
                'message': 'Usuário deve estar autenticado no Google Drive',
                'auth_required': True
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function