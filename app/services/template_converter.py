"""
Serviço de conversão de documentos analisados em templates utilizáveis.
Transforma placeholders extraídos em formulários dinâmicos.
"""

import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

from app.services.google_docs_analyzer import google_docs_analyzer
from app.services.google_service_account import google_service_account
from app.services.cache_service import document_cache
from app.models.client import Client, TipoPessoaEnum
from app.utils.exceptions import (
    TemplateServiceException,
    DocumentNotFoundException,
    ValidationException
)

logger = logging.getLogger(__name__)


@dataclass
class TemplateField:
    """Estrutura de um campo de template."""
    name: str
    label: str
    type: str
    category: str
    required: bool
    description: str
    options: Optional[List[str]] = None
    placeholder: Optional[str] = None
    validation_rules: Optional[Dict[str, Any]] = None
    default_value: Optional[str] = None


@dataclass
class ConvertedTemplate:
    """Template convertido pronto para uso."""
    template_id: str
    name: str
    description: str
    category: str
    fields: List[TemplateField]
    metadata: Dict[str, Any]
    form_schema: Dict[str, Any]
    suitability_score: float
    created_at: str


class TemplateConverter:
    """
    Conversor de documentos analisados em templates funcionais.
    
    Transforma a análise de placeholders em formulários dinâmicos
    que podem ser utilizados para gerar documentos.
    """
    
    # Mapeamento de tipos de campos para controles de formulário
    FIELD_TYPE_MAPPING = {
        'texto': 'text',
        'email': 'email',
        'telefone': 'tel',
        'data': 'date',
        'numero': 'number',
        'endereco': 'text',
        'valor': 'number',
        'texto_longo': 'textarea',
        'selecao': 'select',
        'booleano': 'checkbox'
    }
    
    # Regras de validação por tipo
    VALIDATION_RULES = {
        'email': {
            'pattern': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            'message': 'Email deve ter formato válido'
        },
        'telefone': {
            'pattern': r'^\(\d{2}\)\s\d{4,5}-\d{4}$',
            'message': 'Telefone deve ter formato (XX) XXXXX-XXXX'
        },
        'numero': {
            'type': 'number',
            'min': 0
        },
        'valor': {
            'type': 'number',
            'min': 0,
            'step': 0.01
        }
    }
    
    # Opções pré-definidas para campos de seleção
    SELECTION_OPTIONS = {
        'estado_civil': ['Solteiro(a)', 'Casado(a)', 'Divorciado(a)', 'Viúvo(a)', 'União Estável'],
        'tipo_pessoa': ['Física', 'Jurídica'],
        'estado': ['AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'],
        'sexo': ['Masculino', 'Feminino', 'Outro'],
        'escolaridade': ['Fundamental', 'Médio', 'Superior', 'Pós-graduação', 'Mestrado', 'Doutorado']
    }
    
    def __init__(self):
        """Inicializa o conversor."""
        self.analyzer = google_docs_analyzer
        self.auth_service = google_service_account
    
    def convert_document_to_template(
        self, 
        user_id: str, 
        document_id: str, 
        template_name: Optional[str] = None,
        template_category: Optional[str] = None
    ) -> ConvertedTemplate:
        """
        Converte um documento analisado em template utilizável.
        
        Args:
            user_id: ID do usuário autenticado
            document_id: ID do documento no Google Drive
            template_name: Nome personalizado para o template
            template_category: Categoria personalizada para o template
            
        Returns:
            Template convertido e pronto para uso
        """
        try:
            # Verifica cache primeiro
            cached_template = document_cache.get_template(document_id)
            if cached_template:
                logger.info(f"✅ Template do documento {document_id} obtido do cache")
                # Converte dict cached para ConvertedTemplate
                return self._dict_to_converted_template(cached_template)
            
            logger.info(f"Iniciando conversão do documento {document_id} em template")
            
            # Analisa documento primeiro
            analysis = self.analyzer.analyze_document(user_id, document_id)
            
            # Verifica se documento é adequado
            if not analysis['suitable_for_template']['suitable']:
                logger.warning(f"Documento {document_id} não é adequado para template")
                raise ValidationException(
                    'document_suitability',
                    f"Documento não é adequado para template (score: {analysis['suitable_for_template']['score']})"
                )
            
            # Converte placeholders em campos
            template_fields = self._convert_placeholders_to_fields(
                analysis['placeholders']['placeholders']
            )
            
            # Gera metadados do template
            metadata = self._generate_template_metadata(analysis)
            
            # Cria schema do formulário
            form_schema = self._create_form_schema(template_fields)
            
            # Determina nome e categoria
            final_name = template_name or analysis['metadata']['name'] or f"Template {document_id}"
            final_category = template_category or self._infer_template_category(analysis)
            
            converted_template = ConvertedTemplate(
                template_id=document_id,
                name=final_name,
                description=self._generate_template_description(analysis),
                category=final_category,
                fields=template_fields,
                metadata=metadata,
                form_schema=form_schema,
                suitability_score=analysis['suitable_for_template']['percentage'],
                created_at=datetime.now().isoformat()
            )
            
            logger.info(f"Template convertido com sucesso: {len(template_fields)} campos criados")
            
            # Armazena no cache (TTL: 4 horas)
            template_dict = self._converted_template_to_dict(converted_template)
            document_cache.set_template(document_id, template_dict, ttl_minutes=240)
            logger.debug(f"Template do documento {document_id} armazenado no cache")
            
            return converted_template
            
        except DocumentNotFoundException:
            raise
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"Erro na conversão de template: {e}")
            raise TemplateServiceException(f"Falha na conversão: {e}", 'convert_document_to_template')
    
    def _convert_placeholders_to_fields(self, placeholders: List[Dict[str, Any]]) -> List[TemplateField]:
        """
        Converte placeholders extraídos em campos de template.
        
        Args:
            placeholders: Lista de placeholders analisados
            
        Returns:
            Lista de campos de template
        """
        fields = []
        
        for i, placeholder in enumerate(placeholders):
            field = TemplateField(
                name=self._normalize_field_name(placeholder['name']),
                label=self._generate_field_label(placeholder['name']),
                type=self.FIELD_TYPE_MAPPING.get(placeholder['type'], 'text'),
                category=placeholder['category'],
                required=placeholder['required'],
                description=placeholder['description'],
                options=self._get_field_options(placeholder['name'], placeholder['type']),
                placeholder=self._generate_placeholder_text(placeholder['name']),
                validation_rules=self._get_validation_rules(placeholder['type']),
                default_value=self._get_default_value(placeholder['name'], placeholder['type'])
            )
            
            fields.append(field)
        
        # Ordena campos por categoria e importância
        fields.sort(key=lambda f: (f.category, not f.required, f.name))
        
        return fields
    
    def _normalize_field_name(self, name: str) -> str:
        """
        Normaliza nome do campo para uso em formulários.
        
        Args:
            name: Nome original do placeholder
            
        Returns:
            Nome normalizado
        """
        # Remove caracteres especiais e normaliza
        normalized = name.lower().strip()
        normalized = normalized.replace(' ', '_')
        normalized = normalized.replace('-', '_')
        normalized = ''.join(char for char in normalized if char.isalnum() or char == '_')
        
        # Remove underscores duplicados
        while '__' in normalized:
            normalized = normalized.replace('__', '_')
        
        return normalized.strip('_')
    
    def _generate_field_label(self, name: str) -> str:
        """
        Gera label amigável para o campo.
        
        Args:
            name: Nome do placeholder
            
        Returns:
            Label formatado
        """
        # Converte para formato legível
        label = name.replace('_', ' ').replace('-', ' ')
        label = ' '.join(word.capitalize() for word in label.split())
        
        return label
    
    def _get_field_options(self, name: str, field_type: str) -> Optional[List[str]]:
        """
        Obtém opções para campos de seleção.
        
        Args:
            name: Nome do campo
            field_type: Tipo do campo
            
        Returns:
            Lista de opções ou None
        """
        if field_type != 'selecao':
            return None
        
        name_lower = name.lower()
        
        # Busca opções pré-definidas
        for key, options in self.SELECTION_OPTIONS.items():
            if key in name_lower:
                return options
        
        # Opções padrão para campos de seleção não identificados
        return ['Opção 1', 'Opção 2', 'Opção 3']
    
    def _generate_placeholder_text(self, name: str) -> str:
        """
        Gera texto de placeholder para o campo.
        
        Args:
            name: Nome do campo
            
        Returns:
            Texto de placeholder
        """
        name_lower = name.lower()
        
        placeholder_map = {
            'nome': 'Digite o nome completo',
            'email': 'exemplo@email.com',
            'telefone': '(11) 99999-9999',
            'cpf': '000.000.000-00',
            'cnpj': '00.000.000/0000-00',
            'cep': '00000-000',
            'endereco': 'Rua, Avenida, etc.',
            'numero': 'Número da residência',
            'data': 'dd/mm/aaaa'
        }
        
        for key, placeholder in placeholder_map.items():
            if key in name_lower:
                return placeholder
        
        return f'Digite {self._generate_field_label(name).lower()}'
    
    def _get_validation_rules(self, field_type: str) -> Optional[Dict[str, Any]]:
        """
        Obtém regras de validação para o tipo de campo.
        
        Args:
            field_type: Tipo do campo
            
        Returns:
            Regras de validação
        """
        return self.VALIDATION_RULES.get(field_type)
    
    def _get_default_value(self, name: str, field_type: str) -> Optional[str]:
        """
        Obtém valor padrão para o campo.
        
        Args:
            name: Nome do campo
            field_type: Tipo do campo
            
        Returns:
            Valor padrão ou None
        """
        name_lower = name.lower()
        
        # Valores padrão comuns
        if 'data' in name_lower and 'hoje' in name_lower:
            return 'today'
        elif 'pais' in name_lower:
            return 'Brasil'
        elif field_type == 'booleano':
            return 'false'
        
        return None
    
    def _generate_template_metadata(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gera metadados do template.
        
        Args:
            analysis: Análise completa do documento
            
        Returns:
            Metadados do template
        """
        return {
            'source_document': {
                'id': analysis['document_id'],
                'name': analysis['metadata']['name'],
                'modified_time': analysis['metadata']['modified_time']
            },
            'analysis_summary': {
                'total_placeholders': analysis['placeholders']['total_count'],
                'unique_placeholders': analysis['placeholders']['unique_count'],
                'categories': list(analysis['placeholders']['categories'].keys()),
                'word_count': analysis['content']['word_count']
            },
            'suitability': analysis['suitable_for_template'],
            'creation_method': 'automatic_conversion',
            'version': '1.0'
        }
    
    def _create_form_schema(self, fields: List[TemplateField]) -> Dict[str, Any]:
        """
        Cria schema JSON para o formulário dinâmico.
        
        Args:
            fields: Lista de campos do template
            
        Returns:
            Schema do formulário
        """
        schema = {
            'type': 'object',
            'properties': {},
            'required': [],
            'field_groups': self._group_fields_by_category(fields)
        }
        
        for field in fields:
            field_schema = {
                'type': 'string',
                'title': field.label,
                'description': field.description
            }
            
            # Adiciona propriedades específicas do tipo
            if field.type == 'email':
                field_schema['format'] = 'email'
            elif field.type == 'date':
                field_schema['format'] = 'date'
            elif field.type == 'number':
                field_schema['type'] = 'number'
            elif field.type == 'select' and field.options:
                field_schema['enum'] = field.options
            
            # Adiciona validações
            if field.validation_rules:
                field_schema.update(field.validation_rules)
            
            # Adiciona placeholder
            if field.placeholder:
                field_schema['placeholder'] = field.placeholder
            
            # Adiciona valor padrão
            if field.default_value:
                field_schema['default'] = field.default_value
            
            schema['properties'][field.name] = field_schema
            
            # Adiciona a campos obrigatórios
            if field.required:
                schema['required'].append(field.name)
        
        return schema
    
    def _group_fields_by_category(self, fields: List[TemplateField]) -> Dict[str, List[str]]:
        """
        Agrupa campos por categoria para organização do formulário.
        
        Args:
            fields: Lista de campos
            
        Returns:
            Grupos de campos por categoria
        """
        groups = {}
        
        for field in fields:
            category = field.category
            if category not in groups:
                groups[category] = []
            groups[category].append(field.name)
        
        return groups
    
    def _infer_template_category(self, analysis: Dict[str, Any]) -> str:
        """
        Infere categoria do template baseado na análise.
        
        Args:
            analysis: Análise do documento
            
        Returns:
            Categoria inferida
        """
        categories = analysis['placeholders']['categories']
        
        # Categoria com mais placeholders
        if categories:
            main_category = max(categories, key=categories.get)
            
            # Mapeia para categorias de template
            category_mapping = {
                'cliente': 'Dados Pessoais',
                'juridico': 'Jurídico',
                'documento': 'Documentos',
                'financeiro': 'Financeiro',
                'temporal': 'Prazos e Datas'
            }
            
            return category_mapping.get(main_category, 'Geral')
        
        return 'Geral'
    
    def _generate_template_description(self, analysis: Dict[str, Any]) -> str:
        """
        Gera descrição automática do template.
        
        Args:
            analysis: Análise do documento
            
        Returns:
            Descrição gerada
        """
        total_fields = analysis['placeholders']['unique_count']
        categories = list(analysis['placeholders']['categories'].keys())
        score = analysis['suitable_for_template']['percentage']
        
        description = f"Template com {total_fields} campos variáveis "
        
        if categories:
            description += f"nas categorias: {', '.join(categories)}. "
        
        description += f"Adequação: {score:.1f}%. "
        description += f"Convertido automaticamente em {datetime.now().strftime('%d/%m/%Y')}."
        
        return description
    
    def create_instance_from_template(
        self, 
        converted_template: ConvertedTemplate, 
        form_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Cria instância de documento a partir do template e dados do formulário.
        
        Args:
            converted_template: Template convertido
            form_data: Dados preenchidos no formulário
            
        Returns:
            Dados processados para geração do documento
        """
        try:
            # Valida dados contra schema
            validation_errors = self._validate_form_data(converted_template.form_schema, form_data)
            
            if validation_errors:
                raise ValidationException(
                    'form_data',
                    'Dados do formulário inválidos',
                    validation_errors
                )
            
            # Processa dados
            processed_data = {}
            
            for field in converted_template.fields:
                field_name = field.name
                field_value = form_data.get(field_name)
                
                # Aplica transformações específicas do tipo
                if field_value is not None:
                    processed_data[field_name] = self._process_field_value(field, field_value)
                elif field.default_value:
                    processed_data[field_name] = field.default_value
                elif field.required:
                    raise ValidationException(
                        field_name,
                        f'Campo obrigatório {field.label} não preenchido'
                    )
            
            return {
                'template_id': converted_template.template_id,
                'template_name': converted_template.name,
                'processed_data': processed_data,
                'generation_timestamp': datetime.now().isoformat(),
                'field_count': len(processed_data)
            }
            
        except Exception as e:
            logger.error(f"Erro ao criar instância do template: {e}")
            raise TemplateServiceException(f"Falha na criação de instância: {e}", 'create_instance_from_template')
    
    def _validate_form_data(self, schema: Dict[str, Any], data: Dict[str, Any]) -> List[str]:
        """
        Valida dados do formulário contra o schema.
        
        Args:
            schema: Schema do formulário
            data: Dados a serem validados
            
        Returns:
            Lista de erros de validação
        """
        errors = []
        
        # Verifica campos obrigatórios
        for required_field in schema.get('required', []):
            if required_field not in data or not data[required_field]:
                errors.append(f"Campo obrigatório '{required_field}' não preenchido")
        
        # Valida tipos e formatos
        for field_name, field_schema in schema.get('properties', {}).items():
            if field_name in data:
                value = data[field_name]
                
                # Validação de email
                if field_schema.get('format') == 'email':
                    import re
                    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', str(value)):
                        errors.append(f"Email inválido em '{field_name}'")
                
                # Validação de enums
                if 'enum' in field_schema and value not in field_schema['enum']:
                    errors.append(f"Valor inválido em '{field_name}': deve ser um de {field_schema['enum']}")
        
        return errors
    
    def _process_field_value(self, field: TemplateField, value: Any) -> str:
        """
        Processa valor do campo conforme seu tipo.
        
        Args:
            field: Campo do template
            value: Valor a ser processado
            
        Returns:
            Valor processado
        """
        if field.type == 'data':
            # Converte data para formato brasileiro
            try:
                from datetime import datetime
                if isinstance(value, str):
                    date_obj = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    return date_obj.strftime('%d/%m/%Y')
            except:
                pass
        
        elif field.type == 'telefone':
            # Formata telefone
            digits = ''.join(char for char in str(value) if char.isdigit())
            if len(digits) == 11:
                return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"
            elif len(digits) == 10:
                return f"({digits[:2]}) {digits[2:6]}-{digits[6:]}"
        
        elif field.type == 'number':
            # Formata números
            try:
                if '.' in str(value):
                    return f"{float(value):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                else:
                    return f"{int(value):,}".replace(',', '.')
            except:
                pass
        
        return str(value)
    
    def _converted_template_to_dict(self, template: ConvertedTemplate) -> Dict[str, Any]:
        """
        Converte ConvertedTemplate para dict (para cache).
        
        Args:
            template: Template convertido
            
        Returns:
            Representação em dict
        """
        return {
            'template_id': template.template_id,
            'name': template.name,
            'description': template.description,
            'category': template.category,
            'fields': [
                {
                    'name': field.name,
                    'label': field.label,
                    'type': field.type,
                    'category': field.category,
                    'required': field.required,
                    'description': field.description,
                    'options': field.options,
                    'placeholder': field.placeholder,
                    'validation_rules': field.validation_rules,
                    'default_value': field.default_value
                }
                for field in template.fields
            ],
            'metadata': template.metadata,
            'form_schema': template.form_schema,
            'suitability_score': template.suitability_score,
            'created_at': template.created_at
        }
    
    def _dict_to_converted_template(self, template_dict: Dict[str, Any]) -> ConvertedTemplate:
        """
        Converte dict para ConvertedTemplate (do cache).
        
        Args:
            template_dict: Representação em dict
            
        Returns:
            Template convertido
        """
        fields = [
            TemplateField(
                name=field_data['name'],
                label=field_data['label'],
                type=field_data['type'],
                category=field_data['category'],
                required=field_data['required'],
                description=field_data['description'],
                options=field_data.get('options'),
                placeholder=field_data.get('placeholder'),
                validation_rules=field_data.get('validation_rules'),
                default_value=field_data.get('default_value')
            )
            for field_data in template_dict['fields']
        ]
        
        return ConvertedTemplate(
            template_id=template_dict['template_id'],
            name=template_dict['name'],
            description=template_dict['description'],
            category=template_dict['category'],
            fields=fields,
            metadata=template_dict['metadata'],
            form_schema=template_dict['form_schema'],
            suitability_score=template_dict['suitability_score'],
            created_at=template_dict['created_at']
        )


# Instância global do conversor
template_converter = TemplateConverter()