"""
Dynamic Form Service - Business logic for dynamic form generation.

Generates dynamic forms based on templates, handles multi-author forms,
authority selection, and conditional field logic.
"""

from typing import List, Dict, Any, Optional, Tuple
import logging
import re
from datetime import datetime

from app.repositories.template_repository import TemplateRepository
from app.repositories.placeholder_repository import PlaceholderRepository
from app.services.entity_service import EntityService
from app.config.constants import DocumentTypes, FIELD_TYPES
from app.utils.exceptions import (
    TemplateNotFoundException,
    ValidationException,
    BusinessException
)


logger = logging.getLogger(__name__)


class DynamicFormService:
    """
    Service for dynamic form generation.
    
    Generates forms based on:
    - Template placeholders
    - Multi-author requirements
    - Authority selection needs
    - Conditional field logic
    """
    
    def __init__(self):
        self.template_repo = TemplateRepository()
        self.placeholder_repo = PlaceholderRepository()
        self.entity_service = EntityService()
    
    def generate_form_for_template(self, template_id: int, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generates complete form structure for template.
        
        Args:
            template_id: ID of template to generate form for
            options: Additional options like max_authors, include_optional, etc.
            
        Returns:
            Dict with complete form structure
            
        Raises:
            TemplateNotFoundException: If template not found
        """
        logger.info(f"Generating form for template {template_id}")
        
        template = self.template_repo.find_by_id(template_id)
        if not template:
            raise TemplateNotFoundException(f"Template {template_id} not found")
        
        options = options or {}
        
        try:
            # Get placeholders for template
            placeholders = self.placeholder_repo.find_by_template_id(template_id)
            
            # Analyze placeholder structure
            structure_analysis = self._analyze_placeholder_structure(placeholders)
            
            # Generate form sections
            form_sections = self._generate_form_sections(placeholders, structure_analysis, options)
            
            # Add meta information
            form_metadata = self._generate_form_metadata(template, structure_analysis, options)
            
            # Generate validation rules
            validation_rules = self._generate_validation_rules(placeholders, structure_analysis)
            
            # Generate conditional logic
            conditional_logic = self._generate_conditional_logic(placeholders, template.tipo)
            
            form_structure = {
                'template_id': template_id,
                'template_name': template.nome,
                'template_type': template.tipo,
                'sections': form_sections,
                'metadata': form_metadata,
                'validation_rules': validation_rules,
                'conditional_logic': conditional_logic,
                'generated_at': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Form generated with {len(form_sections)} sections")
            return form_structure
            
        except Exception as e:
            logger.error(f"Error generating form: {str(e)}")
            raise BusinessException(f"Failed to generate form: {str(e)}")
    
    def generate_multi_author_form(self, template_id: int, max_authors: int = 3) -> Dict[str, Any]:
        """
        Generates form with support for multiple authors.
        
        Args:
            template_id: Template ID
            max_authors: Maximum number of authors supported
            
        Returns:
            Form structure with multi-author support
        """
        logger.info(f"Generating multi-author form for template {template_id}")
        
        placeholders = self.placeholder_repo.find_by_template_id(template_id)
        
        # Find author-related placeholders
        author_placeholders = self._extract_author_placeholders(placeholders)
        
        if not author_placeholders:
            # No multi-author structure, generate regular form
            return self.generate_form_for_template(template_id)
        
        # Group placeholders by author number
        grouped_authors = self._group_author_placeholders(author_placeholders)
        
        # Generate author sections
        author_sections = []
        for author_num in range(1, max_authors + 1):
            author_fields = grouped_authors.get(author_num, [])
            
            if author_fields or author_num == 1:  # Always include first author
                section = self._generate_author_section(author_num, author_fields)
                author_sections.append(section)
        
        # Get non-author placeholders
        other_placeholders = [p for p in placeholders if not self._is_author_placeholder(p.chave)]
        other_sections = self._generate_sections_from_placeholders(other_placeholders)
        
        return {
            'type': 'multi_author',
            'author_sections': author_sections,
            'other_sections': other_sections,
            'max_authors': max_authors,
            'validation_rules': self._generate_multi_author_validation_rules(grouped_authors)
        }
    
    def generate_authority_selection_form(self, max_authorities: int = 3) -> Dict[str, Any]:
        """
        Generates form for authority selection with autocomplete.
        
        Args:
            max_authorities: Maximum number of authorities
            
        Returns:
            Authority selection form structure
        """
        logger.info(f"Generating authority selection form for {max_authorities} authorities")
        
        authority_sections = []
        
        for auth_num in range(1, max_authorities + 1):
            section = {
                'id': f'autoridade_{auth_num}',
                'title': f'Autoridade {auth_num}' if auth_num > 1 else 'Autoridade',
                'required': auth_num == 1,
                'fields': [
                    {
                        'name': f'autoridade_{auth_num}_nome',
                        'label': 'Nome da Autoridade',
                        'type': 'autocomplete',
                        'required': auth_num == 1,
                        'autocomplete_config': {
                            'endpoint': '/api/authorities/search',
                            'min_chars': 2,
                            'max_results': 10
                        },
                        'validation': {
                            'min_length': 2,
                            'max_length': 200
                        }
                    },
                    {
                        'name': f'autoridade_{auth_num}_cnpj',
                        'label': 'CNPJ',
                        'type': 'text',
                        'required': False,
                        'mask': '##.###.###/####-##',
                        'validation': {
                            'pattern': r'^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$'
                        }
                    },
                    {
                        'name': f'autoridade_{auth_num}_endereco',
                        'label': 'Endereço',
                        'type': 'textarea',
                        'required': False,
                        'rows': 2
                    }
                ]
            }
            authority_sections.append(section)
        
        return {
            'type': 'authority_selection',
            'sections': authority_sections,
            'max_authorities': max_authorities,
            'common_authorities': self.entity_service.get_common_authority_sets()
        }
    
    def generate_conditional_fields(self, template_id: int) -> Dict[str, Any]:
        """
        Generates conditional field configuration.
        
        Args:
            template_id: Template ID
            
        Returns:
            Conditional fields configuration
        """
        template = self.template_repo.find_by_id(template_id)
        if not template:
            raise TemplateNotFoundException(f"Template {template_id} not found")
        
        conditional_config = {
            'conditions': [],
            'field_groups': [],
            'visibility_rules': []
        }
        
        # Document type specific conditions
        if template.tipo == DocumentTypes.ACAO_ANULATORIA.value:
            conditional_config['conditions'].extend([
                {
                    'condition': 'num_autores > 1',
                    'show_fields': ['autor_2_nome', 'autor_2_cpf', 'autor_2_endereco'],
                    'description': 'Campos do segundo autor'
                },
                {
                    'condition': 'num_autoridades > 1',
                    'show_fields': ['autoridade_2_nome', 'autoridade_2_cnpj'],
                    'description': 'Segunda autoridade'
                },
                {
                    'condition': 'num_autoridades > 2',
                    'show_fields': ['autoridade_3_nome', 'autoridade_3_cnpj'],
                    'description': 'Terceira autoridade'
                }
            ])
        
        elif template.tipo == DocumentTypes.TERMO_ACORDO.value:
            conditional_config['conditions'].extend([
                {
                    'condition': 'has_veiculo === true',
                    'show_fields': ['veiculo_modelo', 'veiculo_placa', 'veiculo_ano'],
                    'description': 'Dados do veículo'
                },
                {
                    'condition': 'tipo_transferencia === "total"',
                    'show_fields': ['transferencia_total_condicoes'],
                    'description': 'Condições para transferência total'
                }
            ])
        
        elif template.tipo == DocumentTypes.DEFESA_PREVIA.value:
            conditional_config['conditions'].extend([
                {
                    'condition': 'tem_imagem_notificacao === true',
                    'show_fields': ['imagem_notificacao_upload'],
                    'description': 'Upload da imagem da notificação'
                },
                {
                    'condition': 'tipo_infracao === "velocidade"',
                    'show_fields': ['velocidade_permitida', 'velocidade_aferida'],
                    'description': 'Dados específicos de velocidade'
                }
            ])
        
        return conditional_config
    
    def get_form_suggestions(self, template_id: int, partial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gets form suggestions based on partial data.
        
        Args:
            template_id: Template ID
            partial_data: Partially filled form data
            
        Returns:
            Suggestions for completing the form
        """
        suggestions = {
            'client_suggestions': [],
            'authority_suggestions': [],
            'field_suggestions': [],
            'validation_warnings': []
        }
        
        # Client suggestions based on CPF/CNPJ
        if 'cliente_cpf' in partial_data and partial_data['cliente_cpf']:
            client = self.entity_service.find_client_by_cpf(partial_data['cliente_cpf'])
            if client:
                suggestions['client_suggestions'].append({
                    'type': 'existing_client',
                    'data': client,
                    'message': 'Cliente encontrado no sistema'
                })
        
        # Authority suggestions
        for key, value in partial_data.items():
            if 'autoridade' in key and 'nome' in key and value:
                auth_suggestions = self.entity_service.suggest_authorities(value)
                suggestions['authority_suggestions'].extend(auth_suggestions)
        
        # Field completion suggestions
        placeholders = self.placeholder_repo.find_by_template_id(template_id)
        required_fields = [p.chave for p in placeholders if p.obrigatorio]
        
        missing_required = [field for field in required_fields if not partial_data.get(field)]
        if missing_required:
            suggestions['field_suggestions'].append({
                'type': 'missing_required',
                'fields': missing_required,
                'message': 'Campos obrigatórios não preenchidos'
            })
        
        return suggestions
    
    def _analyze_placeholder_structure(self, placeholders: List[Any]) -> Dict[str, Any]:
        """Analyzes placeholder structure for form generation."""
        structure = {
            'has_authors': False,
            'has_authorities': False,
            'has_vehicle_data': False,
            'has_conditional_blocks': False,
            'author_count': 0,
            'authority_count': 0,
            'field_categories': {}
        }
        
        for placeholder in placeholders:
            key = placeholder.chave
            
            # Check for authors
            if key.startswith('autor_') and '_nome' in key:
                structure['has_authors'] = True
                author_num = int(re.search(r'autor_(\d+)_', key).group(1))
                structure['author_count'] = max(structure['author_count'], author_num)
            
            # Check for authorities
            elif key.startswith('autoridade_') and '_nome' in key:
                structure['has_authorities'] = True
                auth_num = int(re.search(r'autoridade_(\d+)_', key).group(1))
                structure['authority_count'] = max(structure['authority_count'], auth_num)
            
            # Check for vehicle data
            elif key.startswith('veiculo_'):
                structure['has_vehicle_data'] = True
            
            # Categorize fields
            category = self._categorize_field(key)
            if category not in structure['field_categories']:
                structure['field_categories'][category] = []
            structure['field_categories'][category].append(placeholder)
        
        return structure
    
    def _generate_form_sections(self, placeholders: List[Any], structure: Dict[str, Any], 
                              options: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generates form sections based on placeholder analysis."""
        sections = []
        
        # Client/Author section
        if structure['has_authors']:
            sections.append(self._generate_authors_section(placeholders, structure))
        else:
            sections.append(self._generate_client_section(placeholders))
        
        # Authorities section
        if structure['has_authorities']:
            sections.append(self._generate_authorities_section(placeholders, structure))
        
        # Vehicle section
        if structure['has_vehicle_data']:
            sections.append(self._generate_vehicle_section(placeholders))
        
        # Document-specific sections
        for category, fields in structure['field_categories'].items():
            if category not in ['client', 'author', 'authority', 'vehicle']:
                sections.append(self._generate_category_section(category, fields))
        
        return sections
    
    def _generate_form_metadata(self, template: Any, structure: Dict[str, Any], 
                              options: Dict[str, Any]) -> Dict[str, Any]:
        """Generates form metadata."""
        return {
            'title': f'Formulário - {template.nome}',
            'description': template.descricao or f'Preencha os dados para gerar {template.tipo}',
            'complexity': self._assess_form_complexity(structure),
            'estimated_time': self._estimate_completion_time(structure),
            'required_fields_count': len([p for p in self.placeholder_repo.find_by_template_id(template.id) if p.obrigatorio]),
            'optional_fields_count': len([p for p in self.placeholder_repo.find_by_template_id(template.id) if not p.obrigatorio])
        }
    
    def _generate_validation_rules(self, placeholders: List[Any], structure: Dict[str, Any]) -> Dict[str, Any]:
        """Generates validation rules for form fields."""
        rules = {}
        
        for placeholder in placeholders:
            field_rules = {
                'required': placeholder.obrigatorio,
                'type': placeholder.tipo or 'text'
            }
            
            # Add type-specific validation
            if placeholder.tipo == 'email':
                field_rules['pattern'] = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
            elif 'cpf' in placeholder.chave.lower():
                field_rules['pattern'] = r'^\d{3}\.\d{3}\.\d{3}-\d{2}$'
                field_rules['custom_validation'] = 'cpf'
            elif 'cnpj' in placeholder.chave.lower():
                field_rules['pattern'] = r'^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$'
                field_rules['custom_validation'] = 'cnpj'
            elif 'data' in placeholder.chave.lower():
                field_rules['format'] = 'date'
            
            rules[placeholder.chave] = field_rules
        
        return rules
    
    def _generate_conditional_logic(self, placeholders: List[Any], document_type: str) -> Dict[str, Any]:
        """Generates conditional logic for form."""
        logic = {
            'field_dependencies': {},
            'show_hide_rules': [],
            'calculated_fields': []
        }
        
        # Document type specific logic
        if document_type == DocumentTypes.ACAO_ANULATORIA.value:
            logic['show_hide_rules'].extend([
                {
                    'trigger_field': 'num_autores',
                    'condition': 'value > 1',
                    'action': 'show',
                    'target_fields': ['autor_2_nome', 'autor_2_cpf']
                }
            ])
        
        return logic
    
    def _extract_author_placeholders(self, placeholders: List[Any]) -> List[Any]:
        """Extracts author-related placeholders."""
        return [p for p in placeholders if self._is_author_placeholder(p.chave)]
    
    def _is_author_placeholder(self, key: str) -> bool:
        """Checks if placeholder is author-related."""
        return bool(re.match(r'^autor_\d+_', key))
    
    def _group_author_placeholders(self, author_placeholders: List[Any]) -> Dict[int, List[Any]]:
        """Groups author placeholders by author number."""
        groups = {}
        
        for placeholder in author_placeholders:
            match = re.match(r'^autor_(\d+)_', placeholder.chave)
            if match:
                author_num = int(match.group(1))
                if author_num not in groups:
                    groups[author_num] = []
                groups[author_num].append(placeholder)
        
        return groups
    
    def _generate_author_section(self, author_num: int, fields: List[Any]) -> Dict[str, Any]:
        """Generates section for a single author."""
        return {
            'id': f'autor_{author_num}',
            'title': f'Autor {author_num}' if author_num > 1 else 'Dados do Autor',
            'required': author_num == 1,
            'fields': [self._placeholder_to_field(field) for field in fields]
        }
    
    def _generate_sections_from_placeholders(self, placeholders: List[Any]) -> List[Dict[str, Any]]:
        """Generates sections from list of placeholders."""
        # Group by category
        categorized = {}
        for placeholder in placeholders:
            category = self._categorize_field(placeholder.chave)
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(placeholder)
        
        sections = []
        for category, fields in categorized.items():
            sections.append(self._generate_category_section(category, fields))
        
        return sections
    
    def _generate_multi_author_validation_rules(self, grouped_authors: Dict[int, List[Any]]) -> Dict[str, Any]:
        """Generates validation rules for multi-author forms."""
        rules = {}
        
        for author_num, placeholders in grouped_authors.items():
            for placeholder in placeholders:
                rules[placeholder.chave] = {
                    'required': author_num == 1 and placeholder.obrigatorio,
                    'conditional_required': author_num > 1
                }
        
        return rules
    
    def _categorize_field(self, field_key: str) -> str:
        """Categorizes field based on key pattern."""
        key_lower = field_key.lower()
        
        if key_lower.startswith('autor_'):
            return 'author'
        elif key_lower.startswith('autoridade_'):
            return 'authority'
        elif key_lower.startswith('cliente_'):
            return 'client'
        elif key_lower.startswith('veiculo_'):
            return 'vehicle'
        elif key_lower.startswith('infracao_'):
            return 'infraction'
        elif key_lower.startswith('processo_'):
            return 'process'
        elif 'endereco' in key_lower:
            return 'address'
        else:
            return 'other'
    
    def _placeholder_to_field(self, placeholder: Any) -> Dict[str, Any]:
        """Converts placeholder to form field definition."""
        field = {
            'name': placeholder.chave,
            'label': placeholder.descricao or placeholder.chave.replace('_', ' ').title(),
            'type': placeholder.tipo or 'text',
            'required': placeholder.obrigatorio,
            'placeholder': placeholder.exemplo if hasattr(placeholder, 'exemplo') else ''
        }
        
        # Add type-specific configurations
        if placeholder.tipo == 'email':
            field['validation'] = {'type': 'email'}
        elif placeholder.tipo == 'date':
            field['type'] = 'date'
        elif 'cpf' in placeholder.chave.lower():
            field['mask'] = '###.###.###-##'
        elif 'cnpj' in placeholder.chave.lower():
            field['mask'] = '##.###.###/####-##'
        elif 'telefone' in placeholder.chave.lower():
            field['mask'] = '(##) #####-####'
        
        return field
    
    def _generate_client_section(self, placeholders: List[Any]) -> Dict[str, Any]:
        """Generates client data section."""
        client_fields = [p for p in placeholders if 'cliente_' in p.chave]
        return {
            'id': 'cliente',
            'title': 'Dados do Cliente',
            'required': True,
            'fields': [self._placeholder_to_field(field) for field in client_fields]
        }
    
    def _generate_authors_section(self, placeholders: List[Any], structure: Dict[str, Any]) -> Dict[str, Any]:
        """Generates authors section."""
        author_fields = [p for p in placeholders if 'autor_' in p.chave]
        return {
            'id': 'autores',
            'title': 'Dados dos Autores',
            'required': True,
            'type': 'multi_author',
            'max_authors': structure['author_count'],
            'fields': [self._placeholder_to_field(field) for field in author_fields]
        }
    
    def _generate_authorities_section(self, placeholders: List[Any], structure: Dict[str, Any]) -> Dict[str, Any]:
        """Generates authorities section."""
        auth_fields = [p for p in placeholders if 'autoridade_' in p.chave]
        return {
            'id': 'autoridades',
            'title': 'Autoridades de Trânsito',
            'required': True,
            'type': 'authority_selection',
            'max_authorities': structure['authority_count'],
            'fields': [self._placeholder_to_field(field) for field in auth_fields]
        }
    
    def _generate_vehicle_section(self, placeholders: List[Any]) -> Dict[str, Any]:
        """Generates vehicle data section."""
        vehicle_fields = [p for p in placeholders if 'veiculo_' in p.chave]
        return {
            'id': 'veiculo',
            'title': 'Dados do Veículo',
            'required': False,
            'fields': [self._placeholder_to_field(field) for field in vehicle_fields]
        }
    
    def _generate_category_section(self, category: str, fields: List[Any]) -> Dict[str, Any]:
        """Generates section for a field category."""
        category_titles = {
            'infraction': 'Dados da Infração',
            'process': 'Dados do Processo',
            'address': 'Endereço',
            'other': 'Outros Dados'
        }
        
        return {
            'id': category,
            'title': category_titles.get(category, category.title()),
            'required': any(field.obrigatorio for field in fields),
            'fields': [self._placeholder_to_field(field) for field in fields]
        }
    
    def _assess_form_complexity(self, structure: Dict[str, Any]) -> str:
        """Assesses form complexity based on structure."""
        complexity_score = 0
        
        if structure['has_authors']:
            complexity_score += structure['author_count'] * 2
        if structure['has_authorities']:
            complexity_score += structure['authority_count']
        
        field_count = sum(len(fields) for fields in structure['field_categories'].values())
        complexity_score += field_count * 0.5
        
        if complexity_score < 5:
            return 'simple'
        elif complexity_score < 15:
            return 'medium'
        else:
            return 'complex'
    
    def _estimate_completion_time(self, structure: Dict[str, Any]) -> int:
        """Estimates completion time in minutes."""
        base_time = 2  # 2 minutes base
        
        field_count = sum(len(fields) for fields in structure['field_categories'].values())
        field_time = field_count * 0.3  # 0.3 minutes per field
        
        if structure['has_authorities']:
            field_time += 2  # Extra time for authority search
        
        return int(base_time + field_time) 