"""
APIs Públicas - Sem Autenticação
===============================

Endpoints que podem ser acessados sem login:
- Cadastro de clientes
- Health check
- Informações públicas do sistema
"""

from flask import Blueprint, request, jsonify, current_app
from marshmallow import ValidationError
import logging
import datetime as _dt

from app.extensions import db, limiter
from app.peticionador.models import Cliente
from app.peticionador.schemas.cliente_schema import ClienteCreateSchema

# Blueprint para APIs públicas
public_bp = Blueprint('public_api', __name__, url_prefix='/api/public')

logger = logging.getLogger(__name__)


@public_bp.route('/health', methods=['GET'])
@limiter.limit("60 per minute")
def health_check():
    """
    Health check público do sistema.
    
    Returns:
        {
            "status": "healthy",
            "version": "1.0.0",
            "database": "connected"
        }
    """
    try:
        # Testar conexão com banco
        db.session.execute(db.text('SELECT 1'))
        db_status = "connected"
    except Exception:
        db_status = "error"
    
    return jsonify({
        "status": "healthy" if db_status == "connected" else "degraded",
        "version": "1.0.0",
        "database": db_status,
        "service": "appform-api",
        "timestamp": _dt.datetime.utcnow().isoformat() if db_status == "connected" else None
    }), 200


@public_bp.route('/clientes', methods=['POST'])
@limiter.limit("10 per minute")
def create_cliente():
    """
    Criar cliente via formulário público.
    
    Este endpoint permite que qualquer pessoa cadastre um cliente
    sem necessidade de autenticação.
    
    Body:
        {
            "email": "cliente@example.com",
            "primeiro_nome": "João",
            "sobrenome": "Silva",
            "cpf": "123.456.789-00",
            "telefone_celular": "(11) 99999-9999"
        }
    
    Returns:
        {
            "success": true,
            "cliente": {...},
            "message": "Cliente cadastrado com sucesso"
        }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'Dados requeridos',
                'message': 'É necessário enviar os dados do cliente.'
            }), 400
        
        # Validar dados usando schema
        schema = ClienteCreateSchema()
        validated_data = schema.load(data)
        
        # Verificar se cliente já existe
        existing_cliente = Cliente.query.filter_by(
            email=validated_data.get('email')
        ).first()
        
        if existing_cliente:
            return jsonify({
                'error': 'Cliente já existe',
                'message': 'Já existe um cliente cadastrado com este email.',
                'existing_cliente_id': existing_cliente.id
            }), 409
        
        # Criar novo cliente
        cliente = Cliente()
        for key, value in validated_data.items():
            setattr(cliente, key, value)
        
        # Adicionar metadados
        cliente.tipo_pessoa = validated_data.get('tipo_pessoa', 'FISICA')
        cliente.ativo = True
        
        db.session.add(cliente)
        db.session.commit()
        
        logger.info(f"Cliente público criado: {cliente.email} (ID: {cliente.id})")
        
        return jsonify({
            'success': True,
            'cliente': {
                'id': cliente.id,
                'email': cliente.email,
                'primeiro_nome': cliente.primeiro_nome,
                'sobrenome': cliente.sobrenome,
                'tipo_pessoa': cliente.tipo_pessoa.value if hasattr(cliente, 'tipo_pessoa') else None
            },
            'message': 'Cliente cadastrado com sucesso',
            'next_steps': 'Aguarde contato da nossa equipe.'
        }), 201
        
    except ValidationError as e:
        return jsonify({
            'error': 'Dados inválidos',
            'message': 'Os dados enviados contêm erros.',
            'details': e.messages
        }), 400
        
    except Exception as e:
        logger.error(f"Erro ao criar cliente público: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Erro interno',
            'message': 'Erro interno do servidor. Tente novamente.'
        }), 500


@public_bp.route('/clientes/<int:cliente_id>/status', methods=['GET'])
@limiter.limit("30 per minute")
def get_cliente_status(cliente_id):
    """
    Verificar status de processamento de um cliente.
    
    Endpoint público para cliente verificar andamento do seu processo.
    
    Returns:
        {
            "status": "processando|concluido|erro",
            "message": "...",
            "documents": [...]
        }
    """
    try:
        cliente = Cliente.query.get(cliente_id)
        
        if not cliente:
            return jsonify({
                'error': 'Cliente não encontrado',
                'message': 'Cliente não existe ou foi removido.'
            }), 404
        
        # Determinar status baseado nos dados disponíveis
        status = "cadastrado"
        message = "Cliente cadastrado, aguardando processamento."
        documents = []
        
        # TODO: Implementar lógica real de status baseada nos documentos gerados
        
        return jsonify({
            'status': status,
            'message': message,
            'cliente': {
                'nome': f"{cliente.primeiro_nome} {cliente.sobrenome}",
                'email': cliente.email,
                'cadastrado_em': cliente.data_registro.isoformat() if hasattr(cliente, 'data_registro') else None
            },
            'documents': documents
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao buscar status do cliente {cliente_id}: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Erro interno',
            'message': 'Erro ao verificar status.'
        }), 500


@public_bp.route('/info', methods=['GET'])
@limiter.limit("100 per minute")
def system_info():
    """
    Informações públicas do sistema.
    
    Returns:
        {
            "name": "AppForm",
            "description": "...",
            "features": [...],
            "contact": {...}
        }
    """
    return jsonify({
        "name": "AppForm - Gerador de Documentos",
        "description": "Sistema para geração automatizada de documentos jurídicos",
        "version": "2.0.0",
        "features": [
            "Cadastro de clientes",
            "Geração de documentos personalizados",
            "Formulários dinâmicos",
            "Integração com Google Drive"
        ],
        "contact": {
            "email": "contato@estevaoalmeida.com.br",
            "website": "https://appform.estevaoalmeida.com.br"
        },
        "api": {
            "version": "v1",
            "base_url": "/api",
            "documentation": "/api/docs"
        }
    }), 200


@public_bp.route('/stats', methods=['GET'])
@limiter.limit("30 per minute")
def public_stats():
    """
    Estatísticas públicas (não sensíveis) do sistema.
    
    Returns:
        {
            "total_clientes": 1000,
            "documentos_gerados": 5000,
            "uptime": "99.9%"
        }
    """
    try:
        # Buscar estatísticas básicas
        total_clientes = Cliente.query.filter_by(ativo=True).count()
        
        return jsonify({
            "total_clientes": total_clientes,
            "documentos_gerados": "Em desenvolvimento",
            "sistema": {
                "status": "operacional",
                "uptime": "99.9%",
                "last_update": "2025-01-01"
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao buscar estatísticas públicas: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Erro ao carregar estatísticas"
        }), 500


# Error handlers específicos para este blueprint
@public_bp.errorhandler(ValidationError)
def handle_validation_error(e):
    """Handler para erros de validação."""
    return jsonify({
        'error': 'Dados inválidos',
        'message': 'Os dados enviados são inválidos.',
        'details': e.messages
    }), 400


@public_bp.errorhandler(429)
def handle_rate_limit_error(e):
    """Handler para rate limiting."""
    return jsonify({
        'error': 'Rate limit excedido',
        'message': 'Muitas requisições. Tente novamente em alguns minutos.'
    }), 429


@public_bp.errorhandler(Exception)
def handle_generic_error(e):
    """Handler genérico para erros."""
    logger.error(f"Erro não tratado na API pública: {str(e)}", exc_info=True)
    return jsonify({
        'error': 'Erro interno',
        'message': 'Erro interno do servidor.'
    }), 500 