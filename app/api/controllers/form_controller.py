"""
Form Controller - Gerenciamento completo de formulários dinâmicos
================================================================

Controller para geração de schemas, validação e processamento de formulários dinâmicos.
"""

from typing import Dict, Any, List, Optional
from flask import request, current_app
from pydantic import ValidationError

from .base import BaseController
from app.services.dynamic_form_service import DynamicFormService
from app.services.template_service import TemplateService
from app.services.validation_service import ValidationService
from app.services.placeholder_service import PlaceholderService
from app.utils.exceptions import (
    NotFoundException, 
    ValidationException, 
    TemplateNotFoundException,
    FormProcessingException
)


class FormController(BaseController):
    """Controller para operações com formulários dinâmicos."""
    
    def __init__(self):
        super().__init__()
        self.form_service = DynamicFormService()
        self.template_service = TemplateService()
        self.validation_service = ValidationService()
        self.placeholder_service = PlaceholderService()
    
    def get_form_schema(self, template_id: int) -> Dict[str, Any]:
        """Gera schema do formulário baseado no template."""
        try:
            # Verificar se template existe
            template = self.template_service.get_template_by_id(template_id)
            if not template:
                raise TemplateNotFoundException(template_id)
            
            # Gerar schema via service
            form_schema = self.form_service.generate_form_schema(template_id)
            
            return self.success_response(
                data={'schema': form_schema},
                message="Schema gerado com sucesso"
            )
            
        except TemplateNotFoundException as e:
            return self.error_response(str(e), 404)
        except Exception as e:
            current_app.logger.error(f"Erro ao gerar schema {template_id}: {str(e)}")
            return self.error_response("Erro ao gerar schema do formulário")
    
    def validate_form_data(self, template_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Valida dados do formulário contra o schema do template."""
        try:
            # Verificar se template existe
            template = self.template_service.get_template_by_id(template_id)
            if not template:
                raise TemplateNotFoundException(template_id)
            
            # Validar dados via service
            validation_result = self.form_service.validate_form_data(template_id, data)
            
            return self.success_response(
                data=validation_result,
                message="Validação concluída"
            )
            
        except TemplateNotFoundException as e:
            return self.error_response(str(e), 404)
        except Exception as e:
            current_app.logger.error(f"Erro ao validar formulário {template_id}: {str(e)}")
            return self.error_response("Erro ao validar formulário")
    
    def validate_field(self, template_id: int, field_name: str, 
                      field_value: Any) -> Dict[str, Any]:
        """Valida campo individual em tempo real."""
        try:
            # Verificar se template existe
            template = self.template_service.get_template_by_id(template_id)
            if not template:
                raise TemplateNotFoundException(template_id)
            
            # Validar campo específico
            validation_result = self.form_service.validate_field(
                template_id, field_name, field_value
            )
            
            return self.success_response(
                data=validation_result,
                message="Campo validado"
            )
            
        except TemplateNotFoundException as e:
            return self.error_response(str(e), 404)
        except Exception as e:
            current_app.logger.error(f"Erro ao validar campo {field_name}: {str(e)}")
            return self.error_response("Erro ao validar campo")
    
    def get_field_suggestions(self, template_id: int, field_name: str, 
                             query: str = "") -> Dict[str, Any]:
        """Retorna sugestões para autocomplete de campo."""
        try:
            # Verificar se template existe
            template = self.template_service.get_template_by_id(template_id)
            if not template:
                raise TemplateNotFoundException(template_id)
            
            # Buscar sugestões via service
            suggestions = self.form_service.get_field_suggestions(
                template_id, field_name, query
            )
            
            return self.success_response(
                data={'suggestions': suggestions},
                message="Sugestões obtidas com sucesso"
            )
            
        except TemplateNotFoundException as e:
            return self.error_response(str(e), 404)
        except Exception as e:
            current_app.logger.error(f"Erro ao obter sugestões {field_name}: {str(e)}")
            return self.error_response("Erro ao obter sugestões")
    
    def get_conditional_fields(self, template_id: int, 
                              current_data: Dict[str, Any]) -> Dict[str, Any]:
        """Retorna campos que devem ser exibidos baseado nos dados atuais."""
        try:
            # Verificar se template existe
            template = self.template_service.get_template_by_id(template_id)
            if not template:
                raise TemplateNotFoundException(template_id)
            
            # Processar lógica condicional
            conditional_result = self.form_service.evaluate_conditional_fields(
                template_id, current_data
            )
            
            return self.success_response(
                data=conditional_result,
                message="Campos condicionais avaliados"
            )
            
        except TemplateNotFoundException as e:
            return self.error_response(str(e), 404)
        except Exception as e:
            current_app.logger.error(f"Erro ao avaliar campos condicionais {template_id}: {str(e)}")
            return self.error_response("Erro ao avaliar campos condicionais")
    
    def process_form_submission(self, template_id: int, 
                               data: Dict[str, Any]) -> Dict[str, Any]:
        """Processa submissão completa do formulário."""
        try:
            # Verificar se template existe
            template = self.template_service.get_template_by_id(template_id)
            if not template:
                raise TemplateNotFoundException(template_id)
            
            # Processar submissão via service
            processing_result = self.form_service.process_form_submission(
                template_id=template_id,
                data=data,
                user_id=getattr(request, 'user_id', None)
            )
            
            return self.success_response(
                data=processing_result,
                message="Formulário processado com sucesso"
            )
            
        except TemplateNotFoundException as e:
            return self.error_response(str(e), 404)
        except ValidationException as e:
            return self.error_response(str(e), 400)
        except FormProcessingException as e:
            return self.error_response(str(e), 422)
        except Exception as e:
            current_app.logger.error(f"Erro ao processar formulário {template_id}: {str(e)}")
            return self.error_response("Erro ao processar formulário")
    
    def get_form_templates(self, category: str = None) -> Dict[str, Any]:
        """Lista templates disponíveis para formulários."""
        try:
            # Filtros baseados na categoria
            filters = {}
            if category:
                filters['categoria'] = category
            
            # Buscar templates via service
            templates = self.form_service.get_available_templates(filters)
            
            return self.success_response(
                data={'templates': templates},
                message="Templates obtidos com sucesso"
            )
            
        except Exception as e:
            current_app.logger.error(f"Erro ao listar templates: {str(e)}")
            return self.error_response("Erro ao listar templates")
    
    def get_field_metadata(self, template_id: int, field_name: str) -> Dict[str, Any]:
        """Retorna metadados detalhados de um campo."""
        try:
            # Verificar se template existe
            template = self.template_service.get_template_by_id(template_id)
            if not template:
                raise TemplateNotFoundException(template_id)
            
            # Buscar metadados do campo
            field_metadata = self.form_service.get_field_metadata(template_id, field_name)
            
            if not field_metadata:
                return self.error_response("Campo não encontrado", 404)
            
            return self.success_response(
                data={'field': field_metadata},
                message="Metadados obtidos com sucesso"
            )
            
        except TemplateNotFoundException as e:
            return self.error_response(str(e), 404)
        except Exception as e:
            current_app.logger.error(f"Erro ao obter metadados {field_name}: {str(e)}")
            return self.error_response("Erro ao obter metadados do campo")
    
    def update_field_configuration(self, template_id: int, field_name: str,
                                  config: Dict[str, Any]) -> Dict[str, Any]:
        """Atualiza configuração de um campo (apenas admins)."""
        try:
            # Verificar permissões
            is_admin = getattr(request, 'is_admin', False)
            if not is_admin:
                return self.error_response("Acesso não autorizado", 403)
            
            # Verificar se template existe
            template = self.template_service.get_template_by_id(template_id)
            if not template:
                raise TemplateNotFoundException(template_id)
            
            # Atualizar configuração via service
            updated_config = self.form_service.update_field_configuration(
                template_id, field_name, config
            )
            
            return self.success_response(
                data={'field_config': updated_config},
                message="Configuração atualizada com sucesso"
            )
            
        except TemplateNotFoundException as e:
            return self.error_response(str(e), 404)
        except ValidationException as e:
            return self.error_response(str(e), 400)
        except Exception as e:
            current_app.logger.error(f"Erro ao atualizar configuração {field_name}: {str(e)}")
            return self.error_response("Erro ao atualizar configuração")
    
    def export_form_schema(self, template_id: int, format: str = 'json') -> Dict[str, Any]:
        """Exporta schema do formulário em diferentes formatos."""
        try:
            # Verificar se template existe
            template = self.template_service.get_template_by_id(template_id)
            if not template:
                raise TemplateNotFoundException(template_id)
            
            # Exportar schema via service
            exported_schema = self.form_service.export_form_schema(template_id, format)
            
            return self.success_response(
                data={
                    'schema': exported_schema,
                    'format': format,
                    'template_id': template_id
                },
                message="Schema exportado com sucesso"
            )
            
        except TemplateNotFoundException as e:
            return self.error_response(str(e), 404)
        except ValueError as e:
            return self.error_response(f"Formato inválido: {str(e)}", 400)
        except Exception as e:
            current_app.logger.error(f"Erro ao exportar schema {template_id}: {str(e)}")
            return self.error_response("Erro ao exportar schema")
    
    def get_form_analytics(self, template_id: int, 
                          period: str = '30d') -> Dict[str, Any]:
        """Retorna analytics de uso do formulário."""
        try:
            # Verificar permissões (apenas admins ou donos do template)
            is_admin = getattr(request, 'is_admin', False)
            user_id = getattr(request, 'user_id', None)
            
            template = self.template_service.get_template_by_id(template_id)
            if not template:
                raise TemplateNotFoundException(template_id)
            
            if not is_admin and template.get('created_by') != user_id:
                return self.error_response("Acesso não autorizado", 403)
            
            # Buscar analytics via service
            analytics = self.form_service.get_form_analytics(template_id, period)
            
            return self.success_response(
                data={'analytics': analytics},
                message="Analytics obtidos com sucesso"
            )
            
        except TemplateNotFoundException as e:
            return self.error_response(str(e), 404)
        except Exception as e:
            current_app.logger.error(f"Erro ao obter analytics {template_id}: {str(e)}")
            return self.error_response("Erro ao obter analytics") 