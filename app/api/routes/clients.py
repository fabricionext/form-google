"""
Rotas de Clientes - Nova Arquitetura
====================================

Migradas das rotas legacy para a nova estrutura de Controllers.
Integração com EntityService e validações aprimoradas.
"""

from flask import Blueprint, request, current_app
from flask_login import login_required
from marshmallow import ValidationError

from app.api.controllers import BaseController
from app.services import EntityService
from app.validators.cliente_validator import ClienteValidator
from app.peticionador.models import Cliente
from app.config.constants import (
    CACHE_TTL_CLIENTES,
    VALIDATION_RULES,
    FIELD_TYPES
)
from app.extensions import db, limiter
from .auth import permission_required

# Blueprint para rotas de clientes
clients_bp = Blueprint('clients_api', __name__, url_prefix='/api/clients')


class ClientsController(BaseController):
    """Controller para operações com clientes."""
    
    def __init__(self):
        super().__init__()
        self.entity_service = EntityService()
    
    def list_clients(self):
        """Lista clientes com paginação e filtros."""
        try:
            # Parâmetros de consulta
            page = request.args.get('page', 1, type=int)
            per_page = min(request.args.get('per_page', 20, type=int), 100)
            search = request.args.get('search', '').strip()
            tipo_pessoa = request.args.get('tipo_pessoa', '').strip()
            ativo = request.args.get('ativo', type=bool)
            
            # Validar parâmetros
            if page < 1:
                return self.error_response("Página deve ser maior que 0", status_code=400)
            
            # Construir query
            query = Cliente.query
            
            # Aplicar filtros
            if search:
                query = query.filter(
                    db.or_(
                        Cliente.nome.ilike(f"%{search}%"),
                        Cliente.email.ilike(f"%{search}%"),
                        Cliente.cpf.ilike(f"%{search}%"),
                        Cliente.cnpj.ilike(f"%{search}%")
                    )
                )
            
            if tipo_pessoa:
                query = query.filter(Cliente.tipo_pessoa == tipo_pessoa)
            
            if ativo is not None:
                query = query.filter(Cliente.ativo == ativo)
            
            # Ordenar e paginar
            query = query.order_by(Cliente.nome)
            pagination = query.paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
            
            # Formatar resultados
            clientes = []
            for cliente in pagination.items:
                clientes.append({
                    'id': cliente.id,
                    'nome': cliente.nome,
                    'email': cliente.email,
                    'cpf': cliente.cpf,
                    'cnpj': cliente.cnpj,
                    'telefone': cliente.telefone,
                    'tipo_pessoa': cliente.tipo_pessoa,
                    'ativo': cliente.ativo,
                    'created_at': cliente.created_at.isoformat() if cliente.created_at else None
                })
            
            return self.paginated_response(
                data=clientes,
                pagination=pagination,
                message=f"Encontrados {pagination.total} clientes"
            )
            
        except Exception as e:
            current_app.logger.error(f"Erro ao listar clientes: {str(e)}")
            return self.error_response("Erro interno no servidor")
    
    def get_client(self, client_id):
        """Obtém dados detalhados de um cliente."""
        try:
            # Usar EntityService para buscar com cache
            cliente = self.entity_service.get_client_by_id(client_id)
            
            if not cliente:
                return self.error_response("Cliente não encontrado", status_code=404)
            
            # Dados detalhados
            dados = {
                'id': cliente.id,
                'nome': cliente.nome,
                'email': cliente.email,
                'cpf': cliente.cpf,
                'cnpj': cliente.cnpj,
                'telefone': cliente.telefone,
                'endereco': cliente.endereco,
                'cidade': cliente.cidade,
                'estado': cliente.estado,
                'cep': cliente.cep,
                'tipo_pessoa': cliente.tipo_pessoa,
                'profissao': cliente.profissao,
                'rg': cliente.rg,
                'nacionalidade': cliente.nacionalidade,
                'estado_civil': cliente.estado_civil,
                'ativo': cliente.ativo,
                'observacoes': cliente.observacoes,
                'created_at': cliente.created_at.isoformat() if cliente.created_at else None,
                'updated_at': cliente.updated_at.isoformat() if cliente.updated_at else None,
                # Estatísticas
                'total_documentos': getattr(cliente, 'total_documentos', 0),
                'ultimo_documento': getattr(cliente, 'ultimo_documento', None)
            }
            
            return self.success_response(
                data=dados,
                message="Cliente encontrado com sucesso"
            )
            
        except Exception as e:
            current_app.logger.error(f"Erro ao obter cliente {client_id}: {str(e)}")
            return self.error_response("Erro interno no servidor")
    
    def search_by_cpf(self):
        """Busca cliente por CPF."""
        try:
            cpf_raw = request.args.get('cpf', '').strip()
            
            if not cpf_raw:
                return self.error_response("CPF é obrigatório", status_code=400)
            
            # Validar CPF usando EntityService
            cliente = self.entity_service.search_client_by_cpf(cpf_raw)
            
            if not cliente:
                return self.success_response(
                    data=None,
                    message="Cliente não encontrado"
                )
            
            # Dados básicos para preenchimento de formulário
            dados = {
                'id': cliente.id,
                'nome': cliente.nome,
                'email': cliente.email,
                'cpf': cliente.cpf,
                'telefone': cliente.telefone,
                'endereco': cliente.endereco,
                'cidade': cliente.cidade,
                'estado': cliente.estado,
                'cep': cliente.cep,
                'tipo_pessoa': cliente.tipo_pessoa,
                'profissao': cliente.profissao,
                'rg': cliente.rg,
                'nacionalidade': cliente.nacionalidade,
                'estado_civil': cliente.estado_civil
            }
            
            return self.success_response(
                data=dados,
                message="Cliente encontrado por CPF"
            )
            
        except ValueError as e:
            return self.error_response(str(e), status_code=400)
        except Exception as e:
            current_app.logger.error(f"Erro na busca por CPF: {str(e)}")
            return self.error_response("Erro interno no servidor")
    
    def search_by_name(self):
        """Busca clientes por nome (autocomplete)."""
        try:
            termo = request.args.get('q', '').strip()
            limite = request.args.get('limit', 10, type=int)
            
            if not termo:
                return self.error_response("Termo de busca é obrigatório", status_code=400)
            
            if len(termo) < 2:
                return self.error_response(
                    "Termo de busca deve ter pelo menos 2 caracteres",
                    status_code=400
                )
            
            # Buscar usando EntityService
            resultados = self.entity_service.search_clients_by_name(termo, limit=limite)
            
            # Formatar para autocomplete
            dados = []
            for cliente in resultados:
                dados.append({
                    'id': cliente.id,
                    'label': f"{cliente.nome} - {cliente.cpf or cliente.cnpj}",
                    'value': cliente.nome,
                    'cpf': cliente.cpf,
                    'cnpj': cliente.cnpj,
                    'email': cliente.email,
                    'telefone': cliente.telefone,
                    'tipo_pessoa': cliente.tipo_pessoa
                })
            
            return self.success_response(
                data=dados,
                message=f"Encontrados {len(dados)} resultados"
            )
            
        except Exception as e:
            current_app.logger.error(f"Erro na busca por nome: {str(e)}")
            return self.error_response("Erro interno no servidor")
    
    def create_client(self):
        """Cria novo cliente."""
        try:
            dados = request.get_json() or {}
            
            if not dados:
                return self.error_response(
                    "Dados do cliente são obrigatórios",
                    status_code=400
                )
            
            # Validar usando EntityService
            resultado = self.entity_service.create_client(dados)
            
            if not resultado['success']:
                return self.error_response(
                    resultado['message'],
                    status_code=400,
                    data=resultado.get('errors')
                )
            
            cliente = resultado['data']
            
            # Dados de retorno
            dados_retorno = {
                'id': cliente.id,
                'nome': cliente.nome,
                'email': cliente.email,
                'cpf': cliente.cpf,
                'cnpj': cliente.cnpj,
                'telefone': cliente.telefone,
                'tipo_pessoa': cliente.tipo_pessoa,
                'ativo': cliente.ativo,
                'created_at': cliente.created_at.isoformat()
            }
            
            return self.success_response(
                data=dados_retorno,
                message="Cliente criado com sucesso",
                status_code=201
            )
            
        except ValidationError as e:
            return self.error_response(f"Erro de validação: {e.messages}")
        except Exception as e:
            current_app.logger.error(f"Erro ao criar cliente: {str(e)}")
            return self.error_response("Erro interno no servidor")
    
    def update_client(self, client_id):
        """Atualiza dados de um cliente."""
        try:
            dados = request.get_json() or {}
            
            if not dados:
                return self.error_response(
                    "Dados de atualização são obrigatórios",
                    status_code=400
                )
            
            # Usar EntityService para atualizar
            resultado = self.entity_service.update_client(client_id, dados)
            
            if not resultado['success']:
                return self.error_response(
                    resultado['message'],
                    status_code=400 if 'não encontrado' not in resultado['message'] else 404,
                    data=resultado.get('errors')
                )
            
            cliente = resultado['data']
            
            # Dados de retorno
            dados_retorno = {
                'id': cliente.id,
                'nome': cliente.nome,
                'email': cliente.email,
                'cpf': cliente.cpf,
                'cnpj': cliente.cnpj,
                'telefone': cliente.telefone,
                'tipo_pessoa': cliente.tipo_pessoa,
                'ativo': cliente.ativo,
                'updated_at': cliente.updated_at.isoformat()
            }
            
            return self.success_response(
                data=dados_retorno,
                message="Cliente atualizado com sucesso"
            )
            
        except ValidationError as e:
            return self.error_response(f"Erro de validação: {e.messages}")
        except Exception as e:
            current_app.logger.error(f"Erro ao atualizar cliente {client_id}: {str(e)}")
            return self.error_response("Erro interno no servidor")
    
    def delete_client(self, client_id):
        """Remove um cliente (soft delete)."""
        try:
            resultado = self.entity_service.delete_client(client_id)
            
            if not resultado['success']:
                return self.error_response(
                    resultado['message'],
                    status_code=404 if 'não encontrado' in resultado['message'] else 400
                )
            
            return self.success_response(
                message="Cliente removido com sucesso"
            )
            
        except Exception as e:
            current_app.logger.error(f"Erro ao remover cliente {client_id}: {str(e)}")
            return self.error_response("Erro interno no servidor")
    
    def validate_field(self):
        """Valida um campo específico de cliente em tempo real."""
        try:
            dados = request.get_json() or {}
            
            field_name = dados.get('field_name')
            field_value = dados.get('field_value')
            
            if not field_name:
                return self.error_response(
                    "Nome do campo é obrigatório",
                    status_code=400
                )
            
            # Usar EntityService para validação
            resultado = self.entity_service.validate_client_field(field_name, field_value)
            
            return self.success_response(
                data=resultado,
                message="Validação concluída"
            )
            
        except Exception as e:
            current_app.logger.error(f"Erro na validação de campo: {str(e)}")
            return self.error_response("Erro interno no servidor")


# Instanciar controller
clients_controller = ClientsController()


# =============================================================================
# ROTAS DE CLIENTES
# =============================================================================

@clients_bp.route('/', methods=['GET'])
@login_required
@permission_required('view_clients')
@limiter.limit("30 per minute")
def list_clients():
    """Lista clientes com filtros e paginação."""
    return clients_controller.list_clients()


@clients_bp.route('/<int:client_id>', methods=['GET'])
@login_required
@permission_required('view_clients')
@limiter.limit("60 per minute")
def get_client(client_id):
    """Obtém dados de um cliente específico."""
    return clients_controller.get_client(client_id)


@clients_bp.route('/search/cpf', methods=['GET'])
@login_required
@permission_required('view_clients')
@limiter.limit("20 per minute")
def search_by_cpf():
    """Busca cliente por CPF."""
    return clients_controller.search_by_cpf()


@clients_bp.route('/search/name', methods=['GET'])
@login_required
@permission_required('view_clients')
@limiter.limit("30 per minute")
def search_by_name():
    """Busca clientes por nome (autocomplete)."""
    return clients_controller.search_by_name()


@clients_bp.route('/', methods=['POST'])
@login_required
@permission_required('create_clients')
@limiter.limit("10 per minute")
def create_client():
    """Cria novo cliente."""
    return clients_controller.create_client()


@clients_bp.route('/<int:client_id>', methods=['PUT'])
@login_required
@permission_required('edit_clients')
@limiter.limit("15 per minute")
def update_client(client_id):
    """Atualiza dados de um cliente."""
    return clients_controller.update_client(client_id)


@clients_bp.route('/<int:client_id>', methods=['DELETE'])
@login_required
@permission_required('delete_clients')
@limiter.limit("5 per minute")
def delete_client(client_id):
    """Remove um cliente."""
    return clients_controller.delete_client(client_id)


@clients_bp.route('/validate-field', methods=['POST'])
@login_required
@permission_required('create_clients')
@limiter.limit("60 per minute")
def validate_field():
    """Valida campo de cliente em tempo real."""
    return clients_controller.validate_field() 