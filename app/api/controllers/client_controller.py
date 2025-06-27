"""
Client Controller - Gerenciamento de clientes
============================================

Controller para operações CRUD de clientes, integrado com
os services da nova arquitetura.
"""

from typing import Dict, Any, List
from flask import request, current_app
from marshmallow import ValidationError

from .base import BaseController
from app.peticionador.models import Cliente
from app.utils.exceptions import NotFoundException, ValidationException
from extensions import db


class ClientController(BaseController):
    """Controller para operações com clientes."""
    
    def __init__(self):
        super().__init__()
    
    def list_clients(self, filters: Dict[str, Any] = None, 
                    pagination: Dict[str, int] = None) -> Dict[str, Any]:
        """Lista clientes com filtros e paginação."""
        try:
            query = Cliente.query
            
            # Aplicar filtros
            if filters:
                if filters.get('nome'):
                    query = query.filter(
                        Cliente.nome.ilike(f"%{filters['nome']}%")
                    )
                if filters.get('cpf'):
                    query = query.filter(Cliente.cpf == filters['cpf'])
                if filters.get('status'):
                    query = query.filter(Cliente.status == filters['status'])
            
            # Paginação
            page = pagination.get('page', 1) if pagination else 1
            per_page = pagination.get('per_page', 20) if pagination else 20
            
            paginated = query.paginate(
                page=page, 
                per_page=per_page,
                error_out=False
            )
            
            clients_data = []
            for client in paginated.items:
                clients_data.append({
                    'id': client.id,
                    'nome': client.nome,
                    'cpf': client.cpf,
                    'email': client.email,
                    'telefone': client.telefone,
                    'status': client.status,
                    'created_at': self.format_datetime(client.created_at)
                })
            
            return self.paginated_response(
                items=clients_data,
                total=paginated.total,
                pagination_params={
                    'page': page,
                    'per_page': per_page,
                    'pages': paginated.pages
                }
            )
            
        except Exception as e:
            current_app.logger.error(f"Erro ao listar clientes: {str(e)}")
            return self.error_response("Erro ao listar clientes")
    
    def get_client(self, client_id: int) -> Dict[str, Any]:
        """Busca cliente por ID."""
        try:
            client = Cliente.query.get(client_id)
            if not client:
                raise NotFoundException(f"Cliente {client_id} não encontrado")
            
            client_data = {
                'id': client.id,
                'nome': client.nome,
                'cpf': client.cpf,
                'email': client.email,
                'telefone': client.telefone,
                'endereco': client.endereco,
                'status': client.status,
                'observacoes': client.observacoes,
                'created_at': self.format_datetime(client.created_at),
                'updated_at': self.format_datetime(client.updated_at)
            }
            
            return self.success_response(
                data={'client': client_data},
                message="Cliente encontrado"
            )
            
        except NotFoundException as e:
            return self.error_response(str(e), 404)
        except Exception as e:
            current_app.logger.error(f"Erro ao buscar cliente {client_id}: {str(e)}")
            return self.error_response("Erro ao buscar cliente")
    
    def search_by_cpf(self, cpf: str) -> Dict[str, Any]:
        """Busca cliente por CPF."""
        try:
            if not cpf:
                raise ValidationException("CPF é obrigatório")
            
            # Limpar CPF (remover pontos e traços)
            cpf_clean = ''.join(filter(str.isdigit, cpf))
            
            client = Cliente.query.filter_by(cpf=cpf_clean).first()
            if not client:
                return self.error_response(
                    f"Cliente com CPF {cpf} não encontrado",
                    404
                )
            
            client_data = {
                'id': client.id,
                'nome': client.nome,
                'cpf': client.cpf,
                'email': client.email,
                'telefone': client.telefone,
                'endereco': client.endereco
            }
            
            return self.success_response(
                data={'client': client_data},
                message="Cliente encontrado por CPF"
            )
            
        except ValidationException as e:
            return self.error_response(str(e), 400)
        except Exception as e:
            current_app.logger.error(f"Erro ao buscar CPF {cpf}: {str(e)}")
            return self.error_response("Erro ao buscar por CPF")
    
    def search_by_name(self, name: str, limit: int = 10) -> Dict[str, Any]:
        """Busca clientes por nome (autocomplete)."""
        try:
            if not name or len(name) < 2:
                raise ValidationException("Nome deve ter pelo menos 2 caracteres")
            
            clients = Cliente.query.filter(
                Cliente.nome.ilike(f"%{name}%")
            ).limit(limit).all()
            
            suggestions = []
            for client in clients:
                suggestions.append({
                    'id': client.id,
                    'nome': client.nome,
                    'cpf': client.cpf,
                    'email': client.email
                })
            
            return self.success_response(
                data={'suggestions': suggestions},
                message=f"Encontrados {len(suggestions)} clientes"
            )
            
        except ValidationException as e:
            return self.error_response(str(e), 400)
        except Exception as e:
            current_app.logger.error(f"Erro ao buscar nome {name}: {str(e)}")
            return self.error_response("Erro ao buscar por nome")
    
    def validate_field(self, field_name: str, field_value: str) -> Dict[str, Any]:
        """Valida campo em tempo real."""
        try:
            validations = {
                'cpf': self._validate_cpf,
                'email': self._validate_email,
                'telefone': self._validate_phone
            }
            
            if field_name not in validations:
                return self.success_response(
                    data={'valid': True},
                    message="Campo não requer validação especial"
                )
            
            validator = validations[field_name]
            is_valid, message = validator(field_value)
            
            return self.success_response(
                data={
                    'valid': is_valid,
                    'message': message,
                    'field': field_name,
                    'value': field_value
                }
            )
            
        except Exception as e:
            current_app.logger.error(f"Erro ao validar {field_name}: {str(e)}")
            return self.error_response("Erro na validação")
    
    def _validate_cpf(self, cpf: str) -> tuple:
        """Valida CPF."""
        if not cpf:
            return False, "CPF é obrigatório"
        
        # Remover formatação
        cpf_clean = ''.join(filter(str.isdigit, cpf))
        
        if len(cpf_clean) != 11:
            return False, "CPF deve ter 11 dígitos"
        
        # Verificar se já existe
        existing = Cliente.query.filter_by(cpf=cpf_clean).first()
        if existing:
            return False, "CPF já cadastrado"
        
        return True, "CPF válido"
    
    def _validate_email(self, email: str) -> tuple:
        """Valida email."""
        if not email:
            return True, "Email é opcional"
        
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(email_pattern, email):
            return False, "Email inválido"
        
        # Verificar se já existe
        existing = Cliente.query.filter_by(email=email).first()
        if existing:
            return False, "Email já cadastrado"
        
        return True, "Email válido"
    
    def _validate_phone(self, phone: str) -> tuple:
        """Valida telefone."""
        if not phone:
            return True, "Telefone é opcional"
        
        # Remover formatação
        phone_clean = ''.join(filter(str.isdigit, phone))
        
        if len(phone_clean) < 10 or len(phone_clean) > 11:
            return False, "Telefone deve ter 10 ou 11 dígitos"
        
        return True, "Telefone válido" 