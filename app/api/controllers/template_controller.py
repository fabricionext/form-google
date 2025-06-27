"""
Template Controller - Gerenciamento completo de templates
========================================================

Controller para operações CRUD de templates e sincronização de placeholders.
"""

from typing import Dict, Any, List, Optional
from flask import request, current_app
from marshmallow import ValidationError

from .base import BaseController
from app.services.template_service import TemplateService
from app.services.placeholder_service import PlaceholderService
from app.utils.exceptions import (
    NotFoundException, 
    ValidationException, 
    TemplateNotFoundException,
    IntegrationException
)


class TemplateController(BaseController):
    """Controller para operações com templates."""
    
    def __init__(self):
        super().__init__()
        self.template_service = TemplateService()
        self.placeholder_service = PlaceholderService()
    
    def list_templates(self, filters: Dict[str, Any] = None, 
                      pagination: Dict[str, int] = None) -> Dict[str, Any]:
        """Lista templates com filtros e paginação."""
        try:
            # Parâmetros de consulta
            page = pagination.get('page', 1) if pagination else 1
            per_page = min(pagination.get('per_page', 20) if pagination else 20, 100)
            
            # Filtros
            filters = filters or {}
            
            # Buscar templates via service
            templates_data = self.template_service.list_templates(
                filters=filters,
                page=page,
                per_page=per_page
            )
            
            return self.paginated_response(
                items=templates_data['items'],
                total=templates_data['total'],
                pagination_params={
                    'page': page,
                    'per_page': per_page,
                    'pages': templates_data.get('pages', 1)
                },
                message=f"Encontrados {templates_data['total']} templates"
            )
            
        except Exception as e:
            current_app.logger.error(f"Erro ao listar templates: {str(e)}")
            return self.error_response("Erro ao listar templates")
    
    def get_template(self, template_id: int) -> Dict[str, Any]:
        """Busca template por ID com placeholders."""
        try:
            template_data = self.template_service.get_template_by_id(template_id)
            
            if not template_data:
                raise TemplateNotFoundException(template_id)
            
            # Incluir placeholders
            placeholders = self.placeholder_service.get_placeholders_for_template(template_id)
            template_data['placeholders'] = placeholders
            
            return self.success_response(
                data={'template': template_data},
                message="Template encontrado com sucesso"
            )
            
        except TemplateNotFoundException as e:
            return self.error_response(str(e), 404)
        except Exception as e:
            current_app.logger.error(f"Erro ao buscar template {template_id}: {str(e)}")
            return self.error_response("Erro ao buscar template")
    
    def create_template(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Cria novo template."""
        try:
            # Validação básica
            required_fields = ['nome', 'tipo', 'google_doc_id']
            for field in required_fields:
                if not data.get(field):
                    raise ValidationException(f"Campo '{field}' é obrigatório")
            
            # Criar template via service
            template_data = self.template_service.create_template(data)
            
            # Sincronizar placeholders automaticamente
            try:
                self.sync_placeholders(template_data['id'])
            except Exception as e:
                current_app.logger.warning(f"Erro ao sincronizar placeholders: {str(e)}")
            
            return self.success_response(
                data={'template': template_data},
                message="Template criado com sucesso",
                status_code=201
            )
            
        except ValidationException as e:
            return self.error_response(str(e), 400)
        except Exception as e:
            current_app.logger.error(f"Erro ao criar template: {str(e)}")
            return self.error_response("Erro ao criar template")
    
    def update_template(self, template_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Atualiza template existente."""
        try:
            # Verificar se template existe
            existing_template = self.template_service.get_template_by_id(template_id)
            if not existing_template:
                raise TemplateNotFoundException(template_id)
            
            # Atualizar via service
            updated_template = self.template_service.update_template(template_id, data)
            
            # Se google_doc_id foi alterado, re-sincronizar placeholders
            if 'google_doc_id' in data and data['google_doc_id'] != existing_template.get('google_doc_id'):
                try:
                    self.sync_placeholders(template_id)
                except Exception as e:
                    current_app.logger.warning(f"Erro ao re-sincronizar placeholders: {str(e)}")
            
            return self.success_response(
                data={'template': updated_template},
                message="Template atualizado com sucesso"
            )
            
        except TemplateNotFoundException as e:
            return self.error_response(str(e), 404)
        except ValidationException as e:
            return self.error_response(str(e), 400)
        except Exception as e:
            current_app.logger.error(f"Erro ao atualizar template {template_id}: {str(e)}")
            return self.error_response("Erro ao atualizar template")
    
    def delete_template(self, template_id: int) -> Dict[str, Any]:
        """Remove template (soft delete)."""
        try:
            # Verificar se template existe
            template = self.template_service.get_template_by_id(template_id)
            if not template:
                raise TemplateNotFoundException(template_id)
            
            # Verificar se template pode ser removido (não tem documentos gerados)
            can_delete = self.template_service.can_delete_template(template_id)
            if not can_delete:
                return self.error_response(
                    "Template não pode ser removido pois possui documentos gerados",
                    400
                )
            
            # Soft delete via service
            self.template_service.delete_template(template_id)
            
            return self.success_response(
                message="Template removido com sucesso"
            )
            
        except TemplateNotFoundException as e:
            return self.error_response(str(e), 404)
        except Exception as e:
            current_app.logger.error(f"Erro ao remover template {template_id}: {str(e)}")
            return self.error_response("Erro ao remover template")
    
    def sync_placeholders(self, template_id: int) -> Dict[str, Any]:
        """Sincroniza placeholders do Google Docs."""
        try:
            # Verificar se template existe
            template = self.template_service.get_template_by_id(template_id)
            if not template:
                raise TemplateNotFoundException(template_id)
            
            # Sincronizar via service
            sync_result = self.template_service.sync_placeholders(template_id)
            
            return self.success_response(
                data=sync_result,
                message="Placeholders sincronizados com sucesso"
            )
            
        except TemplateNotFoundException as e:
            return self.error_response(str(e), 404)
        except IntegrationException as e:
            return self.error_response(f"Erro de integração: {str(e)}", 502)
        except Exception as e:
            current_app.logger.error(f"Erro ao sincronizar placeholders {template_id}: {str(e)}")
            return self.error_response("Erro ao sincronizar placeholders")
    
    def get_template_preview(self, template_id: int) -> Dict[str, Any]:
        """Gera preview do template com dados fictícios."""
        try:
            # Verificar se template existe
            template = self.template_service.get_template_by_id(template_id)
            if not template:
                raise TemplateNotFoundException(template_id)
            
            # Gerar preview via service
            preview_data = self.template_service.generate_preview(template_id)
            
            return self.success_response(
                data={'preview': preview_data},
                message="Preview gerado com sucesso"
            )
            
        except TemplateNotFoundException as e:
            return self.error_response(str(e), 404)
        except Exception as e:
            current_app.logger.error(f"Erro ao gerar preview {template_id}: {str(e)}")
            return self.error_response("Erro ao gerar preview")
    
    def get_template_statistics(self, template_id: int) -> Dict[str, Any]:
        """Retorna estatísticas de uso do template."""
        try:
            # Verificar se template existe
            template = self.template_service.get_template_by_id(template_id)
            if not template:
                raise TemplateNotFoundException(template_id)
            
            # Buscar estatísticas via service
            stats = self.template_service.get_template_statistics(template_id)
            
            return self.success_response(
                data={'statistics': stats},
                message="Estatísticas obtidas com sucesso"
            )
            
        except TemplateNotFoundException as e:
            return self.error_response(str(e), 404)
        except Exception as e:
            current_app.logger.error(f"Erro ao obter estatísticas {template_id}: {str(e)}")
            return self.error_response("Erro ao obter estatísticas") 