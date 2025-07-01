"""
Serviço de geração de previews dinâmicos de formulários.
Cria representações visuais de como os templates aparecerão quando renderizados.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from app.services.template_converter import ConvertedTemplate, TemplateField

logger = logging.getLogger(__name__)


class FormPreviewGenerator:
    """
    Gerador de previews dinâmicos para formulários.
    
    Cria representações JSON que podem ser renderizadas em diferentes frontends
    (Vue.js, React, HTML puro, etc.).
    """
    
    # Mapeamento de tipos para componentes de UI
    UI_COMPONENT_MAPPING = {
        'text': 'input',
        'email': 'input',
        'tel': 'input',
        'number': 'input',
        'date': 'date-picker',
        'textarea': 'textarea',
        'select': 'select',
        'checkbox': 'checkbox',
        'radio': 'radio-group'
    }
    
    # Configurações de layout responsivo
    LAYOUT_CONFIGS = {
        'single_column': {'columns': 1, 'spacing': 'normal'},
        'two_column': {'columns': 2, 'spacing': 'compact'},
        'grouped': {'columns': 'auto', 'spacing': 'grouped'},
        'wizard': {'columns': 1, 'spacing': 'wizard'}
    }
    
    # Estilos visuais disponíveis
    VISUAL_THEMES = {
        'default': {
            'primary_color': '#3b82f6',
            'border_radius': '8px',
            'spacing': 'medium',
            'font_family': 'system'
        },
        'modern': {
            'primary_color': '#10b981',
            'border_radius': '12px',
            'spacing': 'large',
            'font_family': 'inter'
        },
        'compact': {
            'primary_color': '#6366f1',
            'border_radius': '4px',
            'spacing': 'small',
            'font_family': 'system'
        }
    }
    
    def generate_form_preview(
        self, 
        template: ConvertedTemplate,
        layout: str = 'single_column',
        theme: str = 'default',
        include_sample_data: bool = True
    ) -> Dict[str, Any]:
        """
        Gera preview completo de um formulário.
        
        Args:
            template: Template convertido
            layout: Layout do formulário ('single_column', 'two_column', 'grouped', 'wizard')
            theme: Tema visual ('default', 'modern', 'compact')
            include_sample_data: Se deve incluir dados de exemplo
            
        Returns:
            Preview completo do formulário
        """
        try:
            logger.info(f"Gerando preview do formulário para template '{template.name}'")
            
            # Gera componentes dos campos
            form_components = self._generate_field_components(template.fields)
            
            # Organiza layout
            layout_structure = self._organize_layout(form_components, layout, template)
            
            # Aplica tema visual
            visual_config = self._apply_visual_theme(theme)
            
            # Gera dados de exemplo se solicitado
            sample_data = None
            if include_sample_data:
                sample_data = self._generate_sample_data(template.fields)
            
            preview = {
                'template_info': {
                    'id': template.template_id,
                    'name': template.name,
                    'description': template.description,
                    'category': template.category,
                    'field_count': len(template.fields)
                },
                'form_structure': layout_structure,
                'visual_config': visual_config,
                'validation_schema': self._extract_validation_schema(template),
                'preview_metadata': {
                    'layout': layout,
                    'theme': theme,
                    'generated_at': datetime.now().isoformat(),
                    'estimated_height': self._estimate_form_height(layout_structure),
                    'complexity': self._assess_form_complexity(template)
                }
            }
            
            if sample_data:
                preview['sample_data'] = sample_data
                preview['filled_preview'] = self._generate_filled_preview(layout_structure, sample_data)
            
            logger.info(f"Preview gerado com sucesso: {len(form_components)} componentes")
            return preview
            
        except Exception as e:
            logger.error(f"Erro ao gerar preview do formulário: {e}")
            raise
    
    def _generate_field_components(self, fields: List[TemplateField]) -> List[Dict[str, Any]]:
        """
        Gera componentes de UI para cada campo.
        
        Args:
            fields: Lista de campos do template
            
        Returns:
            Lista de componentes de UI
        """
        components = []
        
        for field in fields:
            component = {
                'id': f"field_{field.name}",
                'name': field.name,
                'type': self.UI_COMPONENT_MAPPING.get(field.type, 'input'),
                'label': field.label,
                'required': field.required,
                'category': field.category,
                'description': field.description,
                'props': self._generate_component_props(field),
                'validation': self._generate_component_validation(field),
                'accessibility': self._generate_accessibility_props(field)
            }
            
            components.append(component)
        
        return components
    
    def _generate_component_props(self, field: TemplateField) -> Dict[str, Any]:
        """Gera propriedades específicas do componente."""
        props = {
            'placeholder': field.placeholder or f"Digite {field.label.lower()}",
            'name': field.name,
            'id': f"field_{field.name}"
        }
        
        # Propriedades específicas por tipo
        if field.type == 'email':
            props.update({
                'type': 'email',
                'autocomplete': 'email',
                'inputmode': 'email'
            })
        elif field.type == 'tel':
            props.update({
                'type': 'tel',
                'autocomplete': 'tel',
                'inputmode': 'tel'
            })
        elif field.type == 'number':
            props.update({
                'type': 'number',
                'inputmode': 'numeric'
            })
        elif field.type == 'date':
            props.update({
                'type': 'date',
                'format': 'DD/MM/YYYY'
            })
        elif field.type == 'textarea':
            props.update({
                'rows': 3,
                'resize': 'vertical'
            })
        elif field.type == 'select' and field.options:
            props.update({
                'options': field.options,
                'searchable': len(field.options) > 5
            })
        elif field.type == 'checkbox':
            props.update({
                'value': field.default_value or 'false'
            })
        
        # Valor padrão
        if field.default_value:
            props['defaultValue'] = field.default_value
        
        return props
    
    def _generate_component_validation(self, field: TemplateField) -> Dict[str, Any]:
        """Gera regras de validação do componente."""
        validation = {
            'required': field.required
        }
        
        if field.validation_rules:
            validation.update(field.validation_rules)
        
        # Validações específicas por tipo
        if field.type == 'email':
            validation['pattern'] = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            validation['message'] = 'Digite um email válido'
        elif field.type == 'tel':
            validation['pattern'] = r'^\(\d{2}\)\s\d{4,5}-\d{4}$'
            validation['message'] = 'Digite um telefone válido (XX) XXXXX-XXXX'
        elif field.type == 'number':
            validation['type'] = 'number'
            validation['min'] = 0
        
        return validation
    
    def _generate_accessibility_props(self, field: TemplateField) -> Dict[str, Any]:
        """Gera propriedades de acessibilidade."""
        return {
            'aria-label': field.label,
            'aria-required': field.required,
            'aria-describedby': f"{field.name}_description" if field.description else None,
            'role': 'textbox' if field.type in ['text', 'email', 'tel'] else None
        }
    
    def _organize_layout(
        self, 
        components: List[Dict[str, Any]], 
        layout: str, 
        template: ConvertedTemplate
    ) -> Dict[str, Any]:
        """
        Organiza componentes no layout especificado.
        
        Args:
            components: Lista de componentes
            layout: Tipo de layout
            template: Template original
            
        Returns:
            Estrutura do layout
        """
        layout_config = self.LAYOUT_CONFIGS.get(layout, self.LAYOUT_CONFIGS['single_column'])
        
        if layout == 'grouped':
            return self._create_grouped_layout(components, template)
        elif layout == 'two_column':
            return self._create_two_column_layout(components)
        elif layout == 'wizard':
            return self._create_wizard_layout(components, template)
        else:  # single_column
            return self._create_single_column_layout(components)
    
    def _create_single_column_layout(self, components: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Cria layout de coluna única."""
        return {
            'type': 'single_column',
            'sections': [{
                'id': 'main_section',
                'title': 'Formulário',
                'fields': components
            }],
            'config': self.LAYOUT_CONFIGS['single_column']
        }
    
    def _create_two_column_layout(self, components: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Cria layout de duas colunas."""
        # Distribui campos entre duas colunas
        mid_point = len(components) // 2
        left_column = components[:mid_point]
        right_column = components[mid_point:]
        
        return {
            'type': 'two_column',
            'sections': [
                {
                    'id': 'left_column',
                    'title': 'Coluna Esquerda',
                    'fields': left_column,
                    'column': 1
                },
                {
                    'id': 'right_column', 
                    'title': 'Coluna Direita',
                    'fields': right_column,
                    'column': 2
                }
            ],
            'config': self.LAYOUT_CONFIGS['two_column']
        }
    
    def _create_grouped_layout(
        self, 
        components: List[Dict[str, Any]], 
        template: ConvertedTemplate
    ) -> Dict[str, Any]:
        """Cria layout agrupado por categoria."""
        # Agrupa campos por categoria
        grouped_fields = {}
        for component in components:
            category = component.get('category', 'geral')
            if category not in grouped_fields:
                grouped_fields[category] = []
            grouped_fields[category].append(component)
        
        sections = []
        for category, fields in grouped_fields.items():
            sections.append({
                'id': f"section_{category}",
                'title': category.title(),
                'category': category,
                'fields': fields,
                'collapsible': len(fields) > 5
            })
        
        return {
            'type': 'grouped',
            'sections': sections,
            'config': self.LAYOUT_CONFIGS['grouped']
        }
    
    def _create_wizard_layout(
        self, 
        components: List[Dict[str, Any]], 
        template: ConvertedTemplate
    ) -> Dict[str, Any]:
        """Cria layout de wizard (multi-step)."""
        # Divide em páginas de 3-5 campos cada
        fields_per_page = 4
        pages = []
        
        for i in range(0, len(components), fields_per_page):
            page_fields = components[i:i + fields_per_page]
            pages.append({
                'id': f"page_{i // fields_per_page + 1}",
                'title': f"Etapa {i // fields_per_page + 1}",
                'step': i // fields_per_page + 1,
                'fields': page_fields,
                'navigation': {
                    'previous': i > 0,
                    'next': i + fields_per_page < len(components)
                }
            })
        
        return {
            'type': 'wizard',
            'sections': pages,
            'config': {
                **self.LAYOUT_CONFIGS['wizard'],
                'total_steps': len(pages),
                'progress_indicator': True
            }
        }
    
    def _apply_visual_theme(self, theme: str) -> Dict[str, Any]:
        """Aplica tema visual ao formulário."""
        base_theme = self.VISUAL_THEMES.get(theme, self.VISUAL_THEMES['default'])
        
        return {
            'theme_name': theme,
            'colors': {
                'primary': base_theme['primary_color'],
                'secondary': '#64748b',
                'success': '#10b981',
                'error': '#ef4444',
                'warning': '#f59e0b',
                'background': '#ffffff',
                'surface': '#f8fafc'
            },
            'typography': {
                'font_family': base_theme['font_family'],
                'heading_size': '1.5rem',
                'body_size': '1rem',
                'small_size': '0.875rem'
            },
            'spacing': {
                'size': base_theme['spacing'],
                'field_margin': '1rem',
                'section_padding': '1.5rem',
                'component_gap': '0.75rem'
            },
            'borders': {
                'radius': base_theme['border_radius'],
                'width': '1px',
                'color': '#d1d5db'
            },
            'shadows': {
                'small': '0 1px 2px 0 rgb(0 0 0 / 0.05)',
                'medium': '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                'large': '0 10px 15px -3px rgb(0 0 0 / 0.1)'
            }
        }
    
    def _extract_validation_schema(self, template: ConvertedTemplate) -> Dict[str, Any]:
        """Extrai schema de validação do template."""
        return {
            'type': 'object',
            'properties': template.form_schema.get('properties', {}),
            'required': template.form_schema.get('required', []),
            'field_groups': template.form_schema.get('field_groups', {})
        }
    
    def _generate_sample_data(self, fields: List[TemplateField]) -> Dict[str, Any]:
        """Gera dados de exemplo para o formulário."""
        sample_data = {}
        
        for field in fields:
            if field.default_value:
                sample_data[field.name] = field.default_value
            else:
                sample_data[field.name] = self._generate_sample_value(field)
        
        return sample_data
    
    def _generate_sample_value(self, field: TemplateField) -> str:
        """Gera valor de exemplo para um campo."""
        field_name_lower = field.name.lower()
        
        sample_values = {
            'nome': 'João Silva',
            'email': 'joao.silva@exemplo.com',
            'telefone': '(11) 99999-9999',
            'cpf': '123.456.789-00',
            'cnpj': '12.345.678/0001-90',
            'endereco': 'Rua das Flores, 123',
            'cidade': 'São Paulo',
            'cep': '01234-567',
            'data': '01/01/1990',
            'valor': '1500.00'
        }
        
        # Busca por correspondência no nome do campo
        for key, value in sample_values.items():
            if key in field_name_lower:
                return value
        
        # Valores por tipo
        if field.type == 'email':
            return 'usuario@exemplo.com'
        elif field.type == 'tel':
            return '(11) 99999-9999'
        elif field.type == 'date':
            return '01/01/2025'
        elif field.type == 'number':
            return '100'
        elif field.type == 'select' and field.options:
            return field.options[0] if field.options else 'Opção 1'
        elif field.type == 'checkbox':
            return 'true'
        elif field.type == 'textarea':
            return 'Texto de exemplo mais longo para demonstrar como o campo de texto área será exibido no formulário.'
        else:
            return f'Exemplo {field.label}'
    
    def _generate_filled_preview(
        self, 
        layout_structure: Dict[str, Any], 
        sample_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Gera preview com dados preenchidos."""
        filled_structure = layout_structure.copy()
        
        # Preenche dados nos campos
        for section in filled_structure.get('sections', []):
            for field in section.get('fields', []):
                field_name = field.get('name')
                if field_name in sample_data:
                    field['filled_value'] = sample_data[field_name]
                    field['is_filled'] = True
                else:
                    field['is_filled'] = False
        
        return filled_structure
    
    def _estimate_form_height(self, layout_structure: Dict[str, Any]) -> str:
        """Estima altura do formulário."""
        total_fields = sum(
            len(section.get('fields', [])) 
            for section in layout_structure.get('sections', [])
        )
        
        layout_type = layout_structure.get('type', 'single_column')
        
        if layout_type == 'two_column':
            estimated_px = total_fields * 40  # Menos altura por campo
        elif layout_type == 'wizard':
            estimated_px = 300  # Altura fixa por página
        else:
            estimated_px = total_fields * 80  # Altura padrão por campo
        
        return f"{estimated_px}px"
    
    def _assess_form_complexity(self, template: ConvertedTemplate) -> str:
        """Avalia complexidade do formulário."""
        field_count = len(template.fields)
        categories = len(template.form_schema.get('field_groups', {}))
        
        if field_count <= 5 and categories <= 2:
            return 'Simples'
        elif field_count <= 15 and categories <= 4:
            return 'Moderado'
        elif field_count <= 30 and categories <= 6:
            return 'Complexo'
        else:
            return 'Muito Complexo'


# Instância global do gerador
preview_generator = FormPreviewGenerator()