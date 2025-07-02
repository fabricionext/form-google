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
from app.config.constants import GOOGLE_DRIVE_CONFIG

from app.extensions import db, limiter, csrf
from app.peticionador.models import Cliente, TipoPessoaEnum
from app.peticionador.schemas.cliente_schema import ClienteCreateSchema
from app.adapters.enhanced_google_drive import EnhancedGoogleDriveAdapter
from app.services.document_generation_service import DocumentGenerationService
from app.services.google_service_account import GoogleServiceAccountAuth
from app.services.hybrid_google_service import HybridGoogleService

# Blueprint para APIs públicas
public_bp = Blueprint('public_api', __name__, url_prefix='/api/public')

# Desabilitar CSRF para este blueprint
csrf.exempt(public_bp)

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
@csrf.exempt
def create_cliente():
    """
    Criar cliente via formulário público com geração automática de documentos.
    
    Este endpoint permite que qualquer pessoa cadastre um cliente
    sem necessidade de autenticação e gera automaticamente os documentos especificados.
    
    Body:
        {
            "email": "cliente@example.com",
            "primeiro_nome": "João",
            "sobrenome": "Silva",
            "cpf": "123.456.789-00",
            "telefone_celular": "(11) 99999-9999",
            "documentos_gerar": ["FICHA_CADASTRAL", "CONTRATO_HONORARIOS"]  // opcional
        }
    
    Returns:
        {
            "success": true,
            "cliente": {...},
            "documentos": [...],
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
        
        # Extrair documentos a gerar (se especificado)
        documentos_gerar = data.pop('documentos_gerar', [])
        
        # Se não informado, usar templates padrão (PF=6, PJ=4)
        if not documentos_gerar:
            tipo_pessoa = str(data.get('tipo_pessoa', 'FISICA'))
            if 'FISICA' in tipo_pessoa or 'Física' in tipo_pessoa:
                default_key = 'PF'
            elif 'JURIDICA' in tipo_pessoa or 'Jurídica' in tipo_pessoa:
                default_key = 'PJ'
            else:
                default_key = 'PF'  # default
            documentos_gerar = list(GOOGLE_DRIVE_CONFIG.get('TEMPLATES', {}).get(default_key, {}).keys())
        
        # Validar dados usando schema
        schema = ClienteCreateSchema()
        validated_data = schema.load(data)
        
        # Verificar se cliente já existe por CPF ou email
        cpf = validated_data.get('cpf')
        email = validated_data.get('email')
        
        existing_cliente = None
        if cpf:
            existing_cliente = Cliente.query.filter_by(cpf=cpf).first()
        
        if not existing_cliente and email:
            existing_cliente = Cliente.query.filter_by(email=email).first()
        
        # Se cliente existe, arquivar dados antigos e atualizar
        if existing_cliente:
            logger.info(f"Cliente existente encontrado (ID: {existing_cliente.id}), arquivando dados antigos")
            
            # Arquivar dados atuais no histórico
            _ = existing_cliente.arquivar_para_historico("Atualização via formulário público")
            
            # Atualizar dados do cliente existente
            tipo_pessoa_str = validated_data.pop('tipo_pessoa', existing_cliente.tipo_pessoa.value)
            if tipo_pessoa_str == 'FISICA':
                existing_cliente.tipo_pessoa = TipoPessoaEnum.FISICA
            elif tipo_pessoa_str == 'JURIDICA':
                existing_cliente.tipo_pessoa = TipoPessoaEnum.JURIDICA
            
            # Atualizar outros campos
            for key, value in validated_data.items():
                if hasattr(existing_cliente, key) and value is not None:
                    setattr(existing_cliente, key, value)
            
            # Atualizar timestamp de modificação
            existing_cliente.atualizado_em = _dt.datetime.utcnow()
            
            db.session.commit()
            
            logger.info(f"Cliente atualizado: {existing_cliente.email} (ID: {existing_cliente.id}, versão: {existing_cliente.versao})")
            
            # Usar cliente existente atualizado
            cliente = existing_cliente
            is_update = True
        else:
            # Criar novo cliente
            cliente = Cliente()
            
            # Tratar enum separadamente
            tipo_pessoa_str = validated_data.pop('tipo_pessoa', 'FISICA')
            if tipo_pessoa_str == 'FISICA':
                cliente.tipo_pessoa = TipoPessoaEnum.FISICA
            elif tipo_pessoa_str == 'JURIDICA':
                cliente.tipo_pessoa = TipoPessoaEnum.JURIDICA
            else:
                cliente.tipo_pessoa = TipoPessoaEnum.FISICA  # default
            
            # Setar outros campos
            for key, value in validated_data.items():
                if hasattr(cliente, key):
                    setattr(cliente, key, value)
            
            # Setar como ativo por padrão
            cliente.ativo = True
            
            db.session.add(cliente)
            db.session.commit()
            
            logger.info(f"Cliente público criado: {cliente.email} (ID: {cliente.id})")
            is_update = False
        
        # Preparar resposta base
        response_data = {
            'success': True,
            'cliente': {
                'id': cliente.id,
                'email': cliente.email,
                'primeiro_nome': cliente.primeiro_nome,
                'sobrenome': cliente.sobrenome,
                'tipo_pessoa': cliente.tipo_pessoa.value if hasattr(cliente.tipo_pessoa, 'value') else str(cliente.tipo_pessoa),
                'versao': getattr(cliente, 'versao', 1),
                'atualizado_em': cliente.atualizado_em.isoformat() if hasattr(cliente, 'atualizado_em') and cliente.atualizado_em else None
            },
            'documentos': [],
            'message': 'Cliente atualizado com sucesso' if is_update else 'Cliente cadastrado com sucesso',
            'is_update': is_update
        }
        
        # Criar pasta no Google Drive para o cliente mesmo que nenhum documento seja pedido,
        # pois a pasta servirá para armazenar arquivos futuros.
        # A criação continua opcional caso a integração esteja desativada.
        try:
            # Determinar nome da pasta baseado no tipo de pessoa
            if cliente.tipo_pessoa == TipoPessoaEnum.FISICA:
                if cliente.primeiro_nome and cliente.sobrenome:
                    client_name = f"{cliente.primeiro_nome} {cliente.sobrenome}".strip()
                else:
                    client_name = cliente.email.split('@')[0]  # fallback
            else:
                if cliente.razao_social:
                    client_name = cliente.razao_social.strip()
                else:
                    client_name = cliente.email.split('@')[0]  # fallback
            
            # Criar pasta do cliente no Google Drive
            google_service = HybridGoogleService()
            
            # Nome da pasta padronizado: [ANO]-Nome Cliente
            current_year = _dt.datetime.now().year
            folder_name = f"[{current_year}]-{client_name}"
            
            # ID da pasta raiz "Clientes" 
            clientes_folder_id = "1sTSGNuAP81x_3Vtq3FCC8xdqfM1rqzdx"
            
            # Criar pasta do cliente
            folder_id = google_service.create_folder(folder_name, clientes_folder_id)
            logger.info(f"Pasta do Google Drive criada para cliente {cliente.id}: {folder_id}")
            
            # Adicionar folder_id à resposta
            response_data['google_drive'] = {
                'folder_id': folder_id,
                'folder_name': folder_name,
                'created': True,
                'service_used': google_service.active_service
            }
            
        except Exception as e:
            # Logar e continuar mesmo com falha na criação da pasta
            logger.error(f"Erro ao criar pasta do Google Drive para cliente {cliente.id}: {str(e)}")
            response_data['google_drive'] = {
                'folder_id': None,
                'folder_name': None,
                'created': False,
                'error': str(e)
            }
        
        # Gerar documentos somente se solicitados
        if documentos_gerar:
            doc_service = DocumentGenerationService()
            
            # Preparar dados do cliente para geração de documentos
            cliente_data_for_docs = {
                'tipo_pessoa': cliente.tipo_pessoa.value if cliente.tipo_pessoa else 'FISICA',
                'primeiro_nome': cliente.primeiro_nome,
                'sobrenome': cliente.sobrenome,
                'email': cliente.email,
                'cpf': getattr(cliente, 'cpf', None),
                'cnpj': getattr(cliente, 'cnpj', None),
                'razao_social': getattr(cliente, 'razao_social', None),
                'telefone_celular': getattr(cliente, 'telefone_celular', None),
                'telefone_fixo': getattr(cliente, 'telefone_fixo', None),
                'endereco_logradouro': getattr(cliente, 'endereco_logradouro', None),
                'endereco_numero': getattr(cliente, 'endereco_numero', None),
                'endereco_complemento': getattr(cliente, 'endereco_complemento', None),
                'endereco_bairro': getattr(cliente, 'endereco_bairro', None),
                'endereco_cidade': getattr(cliente, 'endereco_cidade', None),
                'endereco_estado': getattr(cliente, 'endereco_estado', None),
                'endereco_cep': getattr(cliente, 'endereco_cep', None),
                'rg': getattr(cliente, 'rg', None),
                'estado_civil': getattr(cliente, 'estado_civil', None),
                'profissao': getattr(cliente, 'profissao', None),
                'nacionalidade': getattr(cliente, 'nacionalidade', 'Brasileira'),
                'inscricao_estadual': getattr(cliente, 'inscricao_estadual', None),
                'representante_legal': getattr(cliente, 'representante_legal', None),
                'representante_cpf': getattr(cliente, 'representante_cpf', None)
            }
            
            # Gerar cada documento solicitado
            for document_type in documentos_gerar:
                try:
                    result = doc_service.generate_document(cliente_data_for_docs, document_type)
                    if result['success']:
                        response_data['documentos'].append({
                            'type': document_type,
                            'id': result['document_id'],
                            'name': result['document_name'],
                            'view_url': f"https://docs.google.com/document/d/{result['document_id']}/edit",
                            'status': 'success'
                        })
                        logger.info(f"Documento {document_type} gerado para cliente {cliente.id}: {result['document_name']}")
                    else:
                        response_data['documentos'].append({
                            'type': document_type,
                            'error': result['error'],
                            'status': 'error'
                        })
                        logger.error(f"Erro ao gerar documento {document_type} para cliente {cliente.id}: {result['error']}")
                except Exception as e:
                    response_data['documentos'].append({
                        'type': document_type,
                        'error': str(e),
                        'status': 'error'
                    })
                    logger.error(f"Exceção ao gerar documento {document_type} para cliente {cliente.id}: {str(e)}")
            
            # Atualizar mensagem se documentos foram gerados
            docs_success = len([d for d in response_data['documentos'] if d['status'] == 'success'])
            docs_error = len([d for d in response_data['documentos'] if d['status'] == 'error'])
            
            if docs_success > 0:
                response_data['message'] += f'. {docs_success} documento(s) gerado(s) com sucesso'
                if docs_error > 0:
                    response_data['message'] += f', {docs_error} com erro(s)'
            elif docs_error > 0:
                response_data['message'] += f'. Erro na geração de {docs_error} documento(s)'
        
        return jsonify(response_data), 201
        
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


@public_bp.route('/documentos/gerar', methods=['POST'])
@limiter.limit("5 per minute")
@csrf.exempt
def generate_document():
    """
    Gerar documento a partir dos dados do cliente.
    
    Body:
        {
            "cliente_id": 123,
            "document_type": "FICHA_CADASTRAL",
            "cliente_data": {...}  // opcional, se não informado usa dados do BD
        }
    
    Returns:
        {
            "success": true,
            "document": {...},
            "message": "Documento gerado com sucesso"
        }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'Dados requeridos',
                'message': 'É necessário enviar os dados para geração do documento.'
            }), 400
        
        cliente_id = data.get('cliente_id')
        document_type = data.get('document_type')
        cliente_data_override = data.get('cliente_data')
        
        if not cliente_id and not cliente_data_override:
            return jsonify({
                'error': 'Cliente requerido',
                'message': 'É necessário informar cliente_id ou cliente_data.'
            }), 400
        
        if not document_type:
            return jsonify({
                'error': 'Tipo de documento requerido',
                'message': 'É necessário informar o document_type.'
            }), 400
        
        # Validar tipo de documento
        valid_types = [
            'FICHA_CADASTRAL', 'CONTRATO_HONORARIOS', 'PROCURACAO_JUDICIAL',
            'PROCURACAO_ADMINISTRATIVA', 'CONTRATO_ADMINISTRATIVO', 'DECLARACAO_POBREZA'
        ]
        
        if document_type not in valid_types:
            return jsonify({
                'error': 'Tipo de documento inválido',
                'message': f'Tipos válidos: {", ".join(valid_types)}'
            }), 400
        
        # Obter dados do cliente
        if cliente_data_override:
            cliente_data = cliente_data_override
        else:
            cliente = Cliente.query.get(cliente_id)
            if not cliente:
                return jsonify({
                    'error': 'Cliente não encontrado',
                    'message': f'Cliente com ID {cliente_id} não encontrado.'
                }), 404
            
            # Converter modelo para dicionário
            cliente_data = {
                'tipo_pessoa': cliente.tipo_pessoa.value if hasattr(cliente.tipo_pessoa, 'value') else str(cliente.tipo_pessoa),
                'primeiro_nome': cliente.primeiro_nome,
                'sobrenome': cliente.sobrenome,
                'email': cliente.email,
                'cpf': getattr(cliente, 'cpf', None),
                'cnpj': getattr(cliente, 'cnpj', None),
                'razao_social': getattr(cliente, 'razao_social', None),
                'telefone_celular': getattr(cliente, 'telefone_celular', None),
                'telefone_fixo': getattr(cliente, 'telefone_fixo', None),
                'endereco_logradouro': getattr(cliente, 'endereco_logradouro', None),
                'endereco_numero': getattr(cliente, 'endereco_numero', None),
                'endereco_complemento': getattr(cliente, 'endereco_complemento', None),
                'endereco_bairro': getattr(cliente, 'endereco_bairro', None),
                'endereco_cidade': getattr(cliente, 'endereco_cidade', None),
                'endereco_estado': getattr(cliente, 'endereco_estado', None),
                'endereco_cep': getattr(cliente, 'endereco_cep', None),
                'rg': getattr(cliente, 'rg', None),
                'estado_civil': getattr(cliente, 'estado_civil', None),
                'profissao': getattr(cliente, 'profissao', None),
                'nacionalidade': getattr(cliente, 'nacionalidade', 'Brasileira'),
                'inscricao_estadual': getattr(cliente, 'inscricao_estadual', None),
                'representante_legal': getattr(cliente, 'representante_legal', None),
                'representante_cpf': getattr(cliente, 'representante_cpf', None)
            }
        
        # Gerar documento
        doc_service = DocumentGenerationService()
        result = doc_service.generate_document(cliente_data, document_type)
        
        if result['success']:
            logger.info(f"Documento gerado via API pública: {result['document_name']}")
            
            return jsonify({
                'success': True,
                'document': {
                    'id': result['document_id'],
                    'name': result['document_name'],
                    'type': result['type'],
                    'pessoa_type': result['pessoa_type'],
                    'client_folder_id': result['client_folder_id']
                },
                'message': 'Documento gerado com sucesso',
                'view_url': f"https://docs.google.com/document/d/{result['document_id']}/edit"
            }), 201
        else:
            return jsonify({
                'error': 'Erro na geração',
                'message': result['error']
            }), 500
            
    except Exception as e:
        logger.error(f"Erro ao gerar documento: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Erro interno',
            'message': 'Erro interno do servidor. Tente novamente.'
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