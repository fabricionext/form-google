"""
ENUMs do sistema - Fase 1.5.2
Implementado seguindo TDD/QDD com validações robustas.
"""

from enum import Enum
from typing import Set, Dict


class FieldType(Enum):
    """
    Tipos de campo suportados no sistema de formulários dinâmicos.
    
    Valores definidos baseado nos requisitos de negócio e testes TDD.
    """
    TEXT = "text"
    EMAIL = "email"
    NUMBER = "number"
    DATE = "date"
    SELECT = "select"
    MULTISELECT = "multiselect"
    TEXTAREA = "textarea"
    CHECKBOX = "checkbox"
    FILE = "file"
    
    def __eq__(self, other):
        """Permite comparação com strings para flexibilidade."""
        if isinstance(other, str):
            return self.value == other
        return super().__eq__(other)
    
    def __hash__(self):
        """Mantém ENUMs hashable para uso em sets e dicionários."""
        return super().__hash__()
    
    @classmethod
    def from_string(cls, value: str) -> 'FieldType':
        """
        Cria FieldType a partir de string com validação.
        
        Args:
            value (str): Valor string do tipo de campo
            
        Returns:
            FieldType: Instância do enum
            
        Raises:
            ValueError: Se o valor não for válido
        """
        try:
            return cls(value)
        except ValueError:
            valid_values = [field.value for field in cls]
            raise ValueError(f"Tipo de campo inválido: {value}. Valores válidos: {valid_values}")
    
    @classmethod
    def get_all_values(cls) -> Set[str]:
        """Retorna todos os valores possíveis como set."""
        return {field.value for field in cls}


class DocumentStatus(Enum):
    """
    Status possíveis para documentos no sistema.
    
    Fluxo de vida do documento:
    DRAFT → ACTIVE → ARCHIVED/DEPRECATED
    """
    DRAFT = "draft"         # Documento em elaboração
    ACTIVE = "active"       # Documento ativo e disponível
    ARCHIVED = "archived"   # Documento arquivado (pode ser reativado)
    DEPRECATED = "deprecated"  # Documento obsoleto (estado final)
    
    def __eq__(self, other):
        """Permite comparação com strings."""
        if isinstance(other, str):
            return self.value == other
        return super().__eq__(other)
    
    def __hash__(self):
        """Mantém ENUMs hashable para uso em sets e dicionários."""
        return super().__hash__()
    
    @classmethod 
    def get_valid_transitions(cls) -> Dict['DocumentStatus', Set['DocumentStatus']]:
        """
        Retorna mapeamento de transições válidas entre status.
        
        Returns:
            Dict: Mapeamento de status origem para set de status destino válidos
        """
        return {
            cls.DRAFT: {cls.ACTIVE, cls.ARCHIVED},
            cls.ACTIVE: {cls.ARCHIVED, cls.DEPRECATED},
            cls.ARCHIVED: {cls.ACTIVE},
            cls.DEPRECATED: set()  # Estado final - sem transições
        }
    
    def can_transition_to(self, target_status: 'DocumentStatus') -> bool:
        """
        Verifica se transição para status alvo é válida.
        
        Args:
            target_status: Status de destino
            
        Returns:
            bool: True se transição é válida
        """
        valid_transitions = self.get_valid_transitions()
        return target_status in valid_transitions.get(self, set())
    
    @classmethod
    def get_default_status(cls) -> 'DocumentStatus':
        """Retorna o status padrão para novos documentos."""
        return cls.DRAFT


class TemplateStatus(Enum):
    """
    Status possíveis para templates no sistema.
    
    Fluxo de publicação:
    DRAFT → REVIEWING → PUBLISHED
    ARCHIVED (pode vir de qualquer estado)
    """
    DRAFT = "draft"           # Template em elaboração
    REVIEWING = "reviewing"   # Template em revisão
    PUBLISHED = "published"   # Template publicado e disponível
    ARCHIVED = "archived"     # Template arquivado
    
    def __eq__(self, other):
        """Permite comparação com strings."""
        if isinstance(other, str):
            return self.value == other
        return super().__eq__(other)
    
    def __hash__(self):
        """Mantém ENUMs hashable para uso em sets e dicionários."""
        return super().__hash__()
    
    @classmethod
    def get_valid_transitions(cls) -> Dict['TemplateStatus', Set['TemplateStatus']]:
        """
        Retorna mapeamento de transições válidas entre status de template.
        """
        return {
            cls.DRAFT: {cls.REVIEWING, cls.ARCHIVED},
            cls.REVIEWING: {cls.PUBLISHED, cls.DRAFT, cls.ARCHIVED},
            cls.PUBLISHED: {cls.ARCHIVED, cls.REVIEWING},  # Pode voltar para revisão
            cls.ARCHIVED: {cls.DRAFT}  # Pode ser reativado como draft
        }
    
    def can_transition_to(self, target_status: 'TemplateStatus') -> bool:
        """Verifica se transição para status alvo é válida."""
        valid_transitions = self.get_valid_transitions()
        return target_status in valid_transitions.get(self, set())
    
    @classmethod
    def get_default_status(cls) -> 'TemplateStatus':
        """Retorna o status padrão para novos templates."""
        return cls.DRAFT
    
    def is_public(self) -> bool:
        """Verifica se template está em estado público (visível para usuários)."""
        return self == TemplateStatus.PUBLISHED


# Utilitários para validação e conversão de ENUMs
class EnumValidator:
    """
    Classe utilitária para validação de ENUMs.
    Implementa validações robustas conforme especificado.
    """
    
    @staticmethod
    def validate_field_type(value: str) -> bool:
        """Valida se string é um tipo de campo válido."""
        try:
            FieldType(value)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_document_status(value: str) -> bool:
        """Valida se string é um status de documento válido."""
        try:
            DocumentStatus(value)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_template_status(value: str) -> bool:
        """Valida se string é um status de template válido."""
        try:
            TemplateStatus(value)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_status_transition(current_status: str, target_status: str, 
                                 status_type: str = "document") -> bool:
        """
        Valida se transição de status é permitida.
        
        Args:
            current_status: Status atual
            target_status: Status alvo
            status_type: Tipo do status ("document" ou "template")
            
        Returns:
            bool: True se transição é válida
        """
        try:
            if status_type == "document":
                current = DocumentStatus(current_status)
                target = DocumentStatus(target_status)
                return current.can_transition_to(target)
            elif status_type == "template":
                current = TemplateStatus(current_status)
                target = TemplateStatus(target_status)
                return current.can_transition_to(target)
            else:
                return False
        except ValueError:
            return False


# Constantes para uso em modelos SQLAlchemy
FIELD_TYPE_CHOICES = [(field.value, field.value.title()) for field in FieldType]
DOCUMENT_STATUS_CHOICES = [(status.value, status.value.title()) for status in DocumentStatus]
TEMPLATE_STATUS_CHOICES = [(status.value, status.value.title()) for status in TemplateStatus]

# Exportações principais
__all__ = [
    "FieldType",
    "DocumentStatus", 
    "TemplateStatus",
    "EnumValidator",
    "FIELD_TYPE_CHOICES",
    "DOCUMENT_STATUS_CHOICES",
    "TEMPLATE_STATUS_CHOICES"
] 