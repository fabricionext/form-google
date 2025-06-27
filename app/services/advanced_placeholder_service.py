"""
Advanced Placeholder Service - Business logic for complex placeholder management.

Handles numbered placeholders, conditional blocks, calculated fields,
and validation of related placeholder data.
"""

from typing import List, Dict, Any, Optional, Tuple
import logging
import re
from datetime import datetime
from decimal import Decimal
import locale

from app.repositories.placeholder_repository import PlaceholderRepository
from app.repositories.template_repository import TemplateRepository
from app.utils.exceptions import (
    PlaceholderValidationException,
    ValidationException,
    BusinessException
)
from app.config.constants import SPECIAL_PLACEHOLDERS


logger = logging.getLogger(__name__)


class AdvancedPlaceholderService:
    """
    Service for advanced placeholder operations.
    
    Handles:
    - Numbered placeholders (autor_1_*, autor_2_*)
    - Conditional blocks ([BLOCO_IMAGEM_NOTIFICACAO])
    - Calculated fields ({{valor_extenso}}, {{saldo_pontos}})
    - Cross-field validation
    """
    
    def __init__(self):
        self.placeholder_repo = PlaceholderRepository()
        self.template_repo = TemplateRepository()
        
        # Set Brazilian locale for number formatting
        try:
            locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
        except locale.Error:
            logger.warning("Brazilian locale not available, using default")
    
    def process_numbered_placeholders(self, template_id: int) -> Dict[str, Any]:
        """
        Processes numbered placeholders and groups them by entity.
        
        Args:
            template_id: ID of the template to process
            
        Returns:
            Dict with placeholder groups and metadata
            
        Raises:
            PlaceholderValidationException: If processing fails
        """
        logger.info(f"Processing numbered placeholders for template {template_id}")
        
        try:
            placeholders = self.placeholder_repo.find_by_template_id(template_id)
            
            # Group placeholders by number pattern
            grouped_placeholders = self._group_numbered_placeholders(placeholders)
            
            # Analyze structure
            structure_analysis = self._analyze_placeholder_structure(grouped_placeholders)
            
            result = {
                'grouped_placeholders': grouped_placeholders,
                'structure': structure_analysis,
                'total_entities': len(grouped_placeholders),
                'processing_date': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Processed {len(placeholders)} placeholders into {len(grouped_placeholders)} groups")
            return result
            
        except Exception as e:
            logger.error(f"Error processing numbered placeholders: {str(e)}")
            raise PlaceholderValidationException(f"Failed to process placeholders: {str(e)}")
    
    def handle_conditional_blocks(self, content: str, data: Dict[str, Any]) -> str:
        """
        Processes conditional blocks in document content.
        
        Args:
            content: Document content with conditional blocks
            data: Data to evaluate conditions
            
        Returns:
            Processed content with blocks resolved
        """
        logger.debug("Processing conditional blocks in content")
        
        # Pattern to match conditional blocks
        block_pattern = r'\[([A-Z_]+)\]'
        
        def replace_block(match):
            block_name = match.group(1)
            return self._process_conditional_block(block_name, data)
        
        processed_content = re.sub(block_pattern, replace_block, content)
        
        # Count processed blocks
        blocks_processed = len(re.findall(block_pattern, content))
        logger.debug(f"Processed {blocks_processed} conditional blocks")
        
        return processed_content
    
    def process_calculated_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates derived fields based on input data.
        
        Args:
            data: Input data dictionary
            
        Returns:
            Data dictionary with calculated fields added
        """
        logger.debug("Processing calculated fields")
        
        enhanced_data = data.copy()
        
        # Calculate valor_extenso (currency in words)
        if 'valor' in data:
            try:
                valor = Decimal(str(data['valor']))
                enhanced_data['valor_extenso'] = self._number_to_words(valor)
            except (ValueError, TypeError) as e:
                logger.warning(f"Error calculating valor_extenso: {e}")
                enhanced_data['valor_extenso'] = "Valor inválido"
        
        # Calculate saldo_pontos (points balance)
        if 'pontos_cnh' in data and 'pontos_infracao' in data:
            try:
                pontos_cnh = int(data['pontos_cnh'])
                pontos_infracao = int(data['pontos_infracao'])
                enhanced_data['saldo_pontos'] = pontos_cnh - pontos_infracao
            except (ValueError, TypeError) as e:
                logger.warning(f"Error calculating saldo_pontos: {e}")
                enhanced_data['saldo_pontos'] = 0
        
        # Calculate data_atual (current date formatted)
        enhanced_data['data_atual'] = datetime.now().strftime('%d de %B de %Y')
        
        # Calculate prazo_defesa (defense deadline)
        if 'data_notificacao' in data:
            try:
                data_notif = datetime.strptime(data['data_notificacao'], '%Y-%m-%d')
                # Assuming 15 days deadline
                prazo = data_notif.replace(day=data_notif.day + 15)
                enhanced_data['prazo_defesa'] = prazo.strftime('%d/%m/%Y')
            except (ValueError, TypeError) as e:
                logger.warning(f"Error calculating prazo_defesa: {e}")
        
        # Calculate valor_atualizado (updated value with interest)
        if 'valor_original' in data and 'data_vencimento' in data:
            enhanced_data['valor_atualizado'] = self._calculate_updated_value(
                data['valor_original'], 
                data['data_vencimento']
            )
        
        calculated_count = len(enhanced_data) - len(data)
        logger.debug(f"Added {calculated_count} calculated fields")
        
        return enhanced_data
    
    def validate_related_fields(self, data: Dict[str, Any], template_id: int = None) -> List[str]:
        """
        Validates consistency between related fields.
        
        Args:
            data: Data to validate
            template_id: Optional template ID for context-specific validation
            
        Returns:
            List of validation error messages
        """
        logger.debug("Validating related fields")
        
        errors = []
        
        # Validate author consistency for multi-author documents
        errors.extend(self._validate_author_consistency(data))
        
        # Validate date consistency
        errors.extend(self._validate_date_consistency(data))
        
        # Validate numeric field consistency
        errors.extend(self._validate_numeric_consistency(data))
        
        # Validate document-specific rules
        if template_id:
            errors.extend(self._validate_template_specific_rules(data, template_id))
        
        logger.debug(f"Found {len(errors)} validation errors")
        return errors
    
    def extract_entity_structure(self, placeholders: List[Any]) -> Dict[str, Any]:
        """
        Extracts entity structure from placeholders (autor_1, autor_2, etc.).
        
        Args:
            placeholders: List of placeholder objects
            
        Returns:
            Dict with entity structure analysis
        """
        entity_pattern = r'^(autor|autoridade|veiculo)_(\d+)_(.+)$'
        entities = {}
        
        for placeholder in placeholders:
            match = re.match(entity_pattern, placeholder.chave)
            if match:
                entity_type, entity_num, field_name = match.groups()
                entity_key = f"{entity_type}_{entity_num}"
                
                if entity_key not in entities:
                    entities[entity_key] = {
                        'type': entity_type,
                        'number': int(entity_num),
                        'fields': []
                    }
                
                entities[entity_key]['fields'].append({
                    'name': field_name,
                    'key': placeholder.chave,
                    'tipo': placeholder.tipo,
                    'obrigatorio': placeholder.obrigatorio
                })
        
        return {
            'entities': entities,
            'entity_count': len(entities),
            'max_number': max([e['number'] for e in entities.values()]) if entities else 0
        }
    
    def _group_numbered_placeholders(self, placeholders: List[Any]) -> Dict[str, List[Dict[str, Any]]]:
        """Groups placeholders by numbered entities."""
        groups = {}
        numbered_pattern = r'^(.+?)_(\d+)_(.+)$'
        
        for placeholder in placeholders:
            match = re.match(numbered_pattern, placeholder.chave)
            if match:
                entity_type, number, field = match.groups()
                group_key = f"{entity_type}_{number}"
                
                if group_key not in groups:
                    groups[group_key] = []
                
                groups[group_key].append({
                    'field': field,
                    'key': placeholder.chave,
                    'tipo': placeholder.tipo,
                    'obrigatorio': placeholder.obrigatorio,
                    'descricao': placeholder.descricao
                })
        
        return groups
    
    def _analyze_placeholder_structure(self, grouped_placeholders: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Analyzes the structure of grouped placeholders."""
        structure = {
            'entity_types': set(),
            'max_entities_per_type': {},
            'common_fields': set(),
            'field_frequency': {}
        }
        
        for group_key, fields in grouped_placeholders.items():
            # Extract entity type and number
            parts = group_key.split('_')
            if len(parts) >= 2:
                entity_type = '_'.join(parts[:-1])
                entity_number = int(parts[-1])
                
                structure['entity_types'].add(entity_type)
                
                # Track max entities per type
                current_max = structure['max_entities_per_type'].get(entity_type, 0)
                structure['max_entities_per_type'][entity_type] = max(current_max, entity_number)
                
                # Track field frequency
                for field in fields:
                    field_name = field['field']
                    structure['field_frequency'][field_name] = structure['field_frequency'].get(field_name, 0) + 1
        
        # Convert sets to lists for JSON serialization
        structure['entity_types'] = list(structure['entity_types'])
        
        # Identify common fields (appear in multiple entities)
        total_entities = sum(structure['max_entities_per_type'].values())
        structure['common_fields'] = [
            field for field, count in structure['field_frequency'].items()
            if count > 1
        ]
        
        return structure
    
    def _process_conditional_block(self, block_name: str, data: Dict[str, Any]) -> str:
        """Processes a single conditional block."""
        block_processors = {
            'BLOCO_IMAGEM_NOTIFICACAO': self._process_image_block,
            'BLOCO_MULTIPLOS_AUTORES': self._process_multiple_authors_block,
            'BLOCO_DADOS_VEICULO': self._process_vehicle_block,
            'BLOCO_AUTORIDADES': self._process_authorities_block
        }
        
        processor = block_processors.get(block_name)
        if processor:
            return processor(data)
        else:
            logger.warning(f"Unknown conditional block: {block_name}")
            return f"[BLOCO_NAO_PROCESSADO: {block_name}]"
    
    def _process_image_block(self, data: Dict[str, Any]) -> str:
        """Processes image notification block."""
        if data.get('tem_imagem_notificacao'):
            return """
            Conforme imagem da notificação anexa, é possível verificar...
            
            [INSERIR_IMAGEM_AQUI]
            """
        return ""
    
    def _process_multiple_authors_block(self, data: Dict[str, Any]) -> str:
        """Processes multiple authors block."""
        authors = []
        i = 1
        while f'autor_{i}_nome' in data:
            authors.append(data[f'autor_{i}_nome'])
            i += 1
        
        if len(authors) > 1:
            return f"Os autores {', '.join(authors[:-1])} e {authors[-1]}"
        elif len(authors) == 1:
            return f"O autor {authors[0]}"
        return "O autor"
    
    def _process_vehicle_block(self, data: Dict[str, Any]) -> str:
        """Processes vehicle data block."""
        if data.get('veiculo_modelo') and data.get('veiculo_placa'):
            return f"veículo {data['veiculo_modelo']}, placa {data['veiculo_placa']}"
        return "veículo"
    
    def _process_authorities_block(self, data: Dict[str, Any]) -> str:
        """Processes authorities block."""
        authorities = []
        i = 1
        while f'autoridade_{i}_nome' in data:
            authorities.append(data[f'autoridade_{i}_nome'])
            i += 1
        
        if len(authorities) > 1:
            return f"as autoridades {', '.join(authorities[:-1])} e {authorities[-1]}"
        elif len(authorities) == 1:
            return f"a autoridade {authorities[0]}"
        return "a autoridade"
    
    def _number_to_words(self, value: Decimal) -> str:
        """Converts a number to words in Portuguese."""
        # Simplified implementation - in production, use a proper library
        try:
            int_value = int(value)
            if int_value == 0:
                return "zero reais"
            elif int_value == 1:
                return "um real"
            elif int_value < 1000:
                return f"{int_value} reais"
            else:
                return f"{int_value:,} reais".replace(',', '.')
        except:
            return "valor inválido"
    
    def _calculate_updated_value(self, original_value: str, due_date: str) -> str:
        """Calculates updated value with interest."""
        try:
            # Simplified calculation - in production, use proper interest rates
            value = Decimal(str(original_value))
            due = datetime.strptime(due_date, '%Y-%m-%d')
            days_late = (datetime.now() - due).days
            
            if days_late > 0:
                # Simplified: 1% per month
                months_late = days_late / 30
                interest = value * Decimal('0.01') * Decimal(str(months_late))
                updated_value = value + interest
                return f"{updated_value:.2f}"
            
            return str(value)
        except:
            return original_value
    
    def _validate_author_consistency(self, data: Dict[str, Any]) -> List[str]:
        """Validates consistency between multiple authors."""
        errors = []
        
        # Check that all authors have required fields
        i = 1
        while f'autor_{i}_nome' in data:
            required_fields = ['nome', 'cpf', 'endereco']
            for field in required_fields:
                field_key = f'autor_{i}_{field}'
                if not data.get(field_key):
                    errors.append(f"Campo obrigatório não preenchido: {field_key}")
            i += 1
        
        return errors
    
    def _validate_date_consistency(self, data: Dict[str, Any]) -> List[str]:
        """Validates date field consistency."""
        errors = []
        
        # Validate that notification date is before defense date
        if 'data_notificacao' in data and 'data_defesa' in data:
            try:
                notif_date = datetime.strptime(data['data_notificacao'], '%Y-%m-%d')
                def_date = datetime.strptime(data['data_defesa'], '%Y-%m-%d')
                
                if def_date <= notif_date:
                    errors.append("Data da defesa deve ser posterior à data de notificação")
            except ValueError:
                errors.append("Formato de data inválido")
        
        return errors
    
    def _validate_numeric_consistency(self, data: Dict[str, Any]) -> List[str]:
        """Validates numeric field consistency."""
        errors = []
        
        # Validate points calculation
        if all(k in data for k in ['pontos_cnh', 'pontos_infracao']):
            try:
                pontos_cnh = int(data['pontos_cnh'])
                pontos_infracao = int(data['pontos_infracao'])
                
                if pontos_infracao > pontos_cnh:
                    errors.append("Pontos da infração não podem ser maiores que pontos na CNH")
                    
                if pontos_cnh < 0 or pontos_infracao < 0:
                    errors.append("Pontos não podem ser negativos")
                    
            except ValueError:
                errors.append("Valores de pontos devem ser números inteiros")
        
        return errors
    
    def _validate_template_specific_rules(self, data: Dict[str, Any], template_id: int) -> List[str]:
        """Validates rules specific to template type."""
        errors = []
        
        # This would be implemented based on specific template requirements
        # For now, just basic validation
        
        template = self.template_repo.find_by_id(template_id)
        if not template:
            return errors
        
        # Example: Ação Anulatória specific validations
        if 'Ação Anulatória' in template.nome:
            if not data.get('autor_1_nome'):
                errors.append("Ação Anulatória requer pelo menos um autor")
            
            if not data.get('autoridade_1_nome'):
                errors.append("Ação Anulatória requer pelo menos uma autoridade")
        
        return errors 