"""
Rotas para testar autenticação da conta de serviço do Google Drive.
"""

import logging
from flask import Blueprint, jsonify
from flask_login import login_required, current_user

from app.services.google_service_account import google_service_account
from app.utils.exceptions import (
    AuthenticationException,
    GoogleDriveException
)
from app.extensions import limiter

logger = logging.getLogger(__name__)

# Blueprint para testes da conta de serviço
service_account_test_bp = Blueprint('service_account_test', __name__, url_prefix='/api/service-account')


@service_account_test_bp.route('/test-connection', methods=['GET'])
@limiter.limit("5 per minute")
@login_required
def test_service_account_connection():
    """
    Testa conexão com Google Drive usando conta de serviço.
    
    Returns:
        JSON com resultado do teste de conexão
    """
    try:
        logger.info(f"Testando conexão da conta de serviço para usuário {current_user.id}")
        
        # Testa conexão
        connection_result = google_service_account.test_connection()
        
        return jsonify({
            'success': True,
            'connection_test': connection_result,
            'message': 'Teste de conexão realizado com sucesso'
        }), 200
        
    except AuthenticationException as e:
        logger.error(f"Erro de autenticação: {e}")
        return jsonify({
            'success': False,
            'error': 'authentication_error',
            'message': str(e)
        }), 401
        
    except GoogleDriveException as e:
        logger.error(f"Erro do Google Drive: {e}")
        return jsonify({
            'success': False,
            'error': 'google_drive_error',
            'message': str(e)
        }), 503
        
    except Exception as e:
        logger.error(f"Erro inesperado no teste: {e}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Erro interno do servidor'
        }), 500


@service_account_test_bp.route('/account-info', methods=['GET'])
@limiter.limit("10 per minute")
@login_required
def get_service_account_info():
    """
    Obtém informações da conta de serviço.
    
    Returns:
        JSON com informações da conta de serviço
    """
    try:
        account_info = google_service_account.get_service_account_info()
        
        return jsonify({
            'success': True,
            'account_info': account_info,
            'message': 'Informações obtidas com sucesso'
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter informações da conta: {e}")
        return jsonify({
            'success': False,
            'error': 'info_error',
            'message': 'Erro ao obter informações da conta'
        }), 500


@service_account_test_bp.route('/search-documents', methods=['GET'])
@limiter.limit("10 per minute")
@login_required
def search_test_documents():
    """
    Busca documentos para teste (limitado).
    
    Query Parameters:
        q: Termo de busca (opcional, padrão: "template")
        
    Returns:
        JSON com documentos encontrados
    """
    try:
        from flask import request
        
        query = request.args.get('q', 'template')
        
        search_result = google_service_account.search_documents(query, max_results=5)
        
        return jsonify({
            'success': True,
            'search': search_result,
            'message': f'Busca realizada: {search_result.get("results_count", 0)} documentos encontrados'
        }), 200
        
    except Exception as e:
        logger.error(f"Erro na busca de documentos: {e}")
        return jsonify({
            'success': False,
            'error': 'search_error',
            'message': 'Erro na busca de documentos'
        }), 500


@service_account_test_bp.route('/file-info/<file_id>', methods=['GET'])
@limiter.limit("20 per minute")
@login_required
def get_file_info(file_id):
    """
    Obtém informações de um arquivo específico.
    
    Args:
        file_id: ID do arquivo no Google Drive
        
    Returns:
        JSON com informações do arquivo
    """
    try:
        file_info = google_service_account.get_file_info(file_id)
        
        return jsonify({
            'success': True,
            'file_info': file_info,
            'message': 'Informações do arquivo obtidas com sucesso'
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter informações do arquivo {file_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'file_info_error',
            'message': 'Erro ao obter informações do arquivo'
        }), 500