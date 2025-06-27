"""
Form Schemas - Validação Pydantic para Formulários Dinâmicos
============================================================

Schemas para estrutura de saída dos formulários e validação de dados.
Define estruturas JSON Schema conforme especificações.
"""

from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


class FieldTypeEnum(str, Enum):
    """Enum para tipos de campo válidos."""
    TEXT = "text"
    EMAIL = "email"
    PASSWORD = "password"
    NUMBER = "number"
    DATE = "date"
    DATETIME = "datetime-local"
    TEXTAREA = "textarea"
    SELECT = "select"
    RADIO = "radio"
    CHECKBOX = "checkbox"
    AUTOCOMPLETE = "autocomplete"
    FILE = "file"
    HIDDEN = "hidden"


class FormFieldSchema(BaseModel):
    """Schema para definição de campo de formulário."""
    
    name: str = Field(..., description="Nome do campo")
    label: str = Field(..., description="Label do campo")
    type: FieldTypeEnum = Field(..., description="Tipo do campo")
    
    # Configurações básicas
    required: bool = Field(False, description="Se é obrigatório")
    placeholder: Optional[str] = Field(None, description="Placeholder")
    default_value: Optional[Union[str, int, float, bool]] = Field(None, description="Valor padrão")
    help_text: Optional[str] = Field(None, description="Texto de ajuda")
    
    # Validação
    min_length: Optional[int] = Field(None, description="Comprimento mínimo")
    max_length: Optional[int] = Field(None, description="Comprimento máximo")
    min_value: Optional[Union[int, float]] = Field(None, description="Valor mínimo")
    max_value: Optional[Union[int, float]] = Field(None, description="Valor máximo")
    pattern: Optional[str] = Field(None, description="Regex pattern")
    
    # Configurações específicas por tipo
    options: Optional[List[Dict[str, Any]]] = Field(None, description="Opções para select/radio")
    multiple: Optional[bool] = Field(False, description="Múltiplas seleções")
    rows: Optional[int] = Field(None, description="Linhas para textarea")
    cols: Optional[int] = Field(None, description="Colunas para textarea")
    
    # Autocomplete
    autocomplete_config: Optional[Dict[str, Any]] = Field(
        None, 
        description="Configuração de autocomplete"
    )
    
    # Formatação e máscara
    mask: Optional[str] = Field(None, description="Máscara de entrada")
    format: Optional[str] = Field(None, description="Formato de exibição")
    
    # Classes CSS
    css_classes: Optional[str] = Field(None, description="Classes CSS")
    wrapper_classes: Optional[str] = Field(None, description="Classes do wrapper")
    
    # Lógica condicional
    show_if: Optional[Dict[str, Any]] = Field(None, description="Condição para exibir")
    required_if: Optional[Dict[str, Any]] = Field(None, description="Condição para ser obrigatório")
    
    # Metadados
    category: Optional[str] = Field(None, description="Categoria do campo")
    order: Optional[int] = Field(None, description="Ordem de exibição")
    
    @validator('autocomplete_config')
    def validate_autocomplete_config(cls, v):
        """Valida configuração de autocomplete."""
        if v is not None:
            required_keys = ['endpoint', 'min_chars']
            for key in required_keys:
                if key not in v:
                    raise ValueError(f'Autocomplete config deve ter {key}')
        return v


class FormSectionSchema(BaseModel):
    """Schema para seção de formulário."""
    
    id: str = Field(..., description="ID da seção")
    title: str = Field(..., description="Título da seção")
    description: Optional[str] = Field(None, description="Descrição da seção")
    
    # Configurações
    required: bool = Field(False, description="Se a seção é obrigatória")
    collapsible: bool = Field(False, description="Se pode ser colapsada")
    collapsed: bool = Field(False, description="Se inicia colapsada")
    
    # Campos
    fields: List[FormFieldSchema] = Field(..., description="Campos da seção")
    
    # Lógica condicional
    show_if: Optional[Dict[str, Any]] = Field(None, description="Condição para exibir")
    
    # Configurações específicas
    type: Optional[str] = Field(None, description="Tipo especial de seção")
    max_items: Optional[int] = Field(None, description="Máximo de itens (para seções repetíveis)")
    min_items: Optional[int] = Field(1, description="Mínimo de itens")
    
    # Metadados
    order: Optional[int] = Field(None, description="Ordem da seção")
    css_classes: Optional[str] = Field(None, description="Classes CSS")


class FormValidationRuleSchema(BaseModel):
    """Schema para regra de validação."""
    
    field: str = Field(..., description="Campo alvo")
    rule_type: str = Field(..., description="Tipo da regra")
    condition: Optional[Dict[str, Any]] = Field(None, description="Condição")
    message: str = Field(..., description="Mensagem de erro")
    severity: str = Field("error", description="Severidade (error, warning, info)")


class ConditionalLogicSchema(BaseModel):
    """Schema para lógica condicional."""
    
    trigger_field: str = Field(..., description="Campo gatilho")
    condition: str = Field(..., description="Condição")
    action: str = Field(..., description="Ação (show, hide, require, etc.)")
    target_fields: List[str] = Field(..., description="Campos alvo")
    description: Optional[str] = Field(None, description="Descrição da regra")


class FormMetadataSchema(BaseModel):
    """Schema para metadados do formulário."""
    
    title: str = Field(..., description="Título do formulário")
    description: Optional[str] = Field(None, description="Descrição")
    version: str = Field("1.0", description="Versão do schema")
    
    # Estimativas
    complexity: str = Field("medium", description="Complexidade (low, medium, high)")
    estimated_time: int = Field(5, description="Tempo estimado em minutos")
    
    # Contadores
    required_fields_count: int = Field(0, description="Campos obrigatórios")
    optional_fields_count: int = Field(0, description="Campos opcionais")
    total_sections: int = Field(1, description="Total de seções")
    
    # Configurações
    auto_save: bool = Field(False, description="Auto-salvar")
    show_progress: bool = Field(True, description="Mostrar progresso")
    allow_partial_save: bool = Field(True, description="Permitir salvamento parcial")


class FormSchema(BaseModel):
    """
    Schema principal para formulário dinâmico.
    
    Estrutura JSON Schema que descreve o formulário dinâmico conforme especificação.
    """
    
    template_id: int = Field(..., description="ID do template")
    template_name: str = Field(..., description="Nome do template")
    template_type: str = Field(..., description="Tipo do template")
    
    # Estrutura básica
    sections: List[Dict[str, Any]] = Field(..., description="Seções do formulário")
    metadata: Dict[str, Any] = Field(..., description="Metadados")
    
    # Validação
    validation_rules: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Regras de validação"
    )
    
    # Lógica condicional
    conditional_logic: Dict[str, Any] = Field(
        default_factory=dict,
        description="Lógica condicional"
    )
    
    # Timestamps
    generated_at: datetime = Field(..., description="Timestamp de geração")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class FormValidationSchema(BaseModel):
    """Schema para resultado de validação de formulário."""
    
    valid: bool = Field(..., description="Se o formulário é válido")
    errors: List[str] = Field(default_factory=list, description="Lista de erros")
    warnings: List[str] = Field(default_factory=list, description="Lista de avisos")
    
    # Dados processados
    processed_data: Optional[Dict[str, Any]] = Field(None, description="Dados processados")


class FormSubmissionSchema(BaseModel):
    """Schema para submissão de formulário."""
    
    template_id: int = Field(..., description="ID do template")
    form_data: Dict[str, Any] = Field(..., description="Dados do formulário")
    
    # Metadados da submissão
    user_id: Optional[int] = Field(None, description="ID do usuário")
    session_id: Optional[str] = Field(None, description="ID da sessão")
    submission_time: datetime = Field(default_factory=datetime.now)
    
    # Configurações
    validate_only: bool = Field(False, description="Apenas validar")
    save_draft: bool = Field(False, description="Salvar como rascunho")
    generate_document: bool = Field(True, description="Gerar documento")
    
    # Opções adicionais
    options: Optional[Dict[str, Any]] = Field(None, description="Opções adicionais")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class FormFieldSuggestionSchema(BaseModel):
    """Schema para sugestões de campo."""
    
    field_name: str = Field(..., description="Nome do campo")
    suggestions: List[Dict[str, Any]] = Field(..., description="Lista de sugestões")
    total_count: int = Field(0, description="Total de sugestões disponíveis")
    
    # Configurações
    query: Optional[str] = Field(None, description="Query de busca")
    limit: int = Field(10, description="Limite de resultados")
    
    # Metadados
    source: str = Field("database", description="Fonte das sugestões")
    cached: bool = Field(False, description="Se está em cache")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class FormAnalyticsSchema(BaseModel):
    """Schema para analytics de formulário."""
    
    template_id: int = Field(..., description="ID do template")
    period: str = Field(..., description="Período analisado")
    
    # Estatísticas de uso
    total_submissions: int = Field(0, description="Total de submissões")
    successful_submissions: int = Field(0, description="Submissões bem-sucedidas")
    failed_submissions: int = Field(0, description="Submissões falharam")
    
    # Estatísticas de campos
    field_completion_rates: Dict[str, float] = Field(default_factory=dict)
    most_common_errors: List[Dict[str, Any]] = Field(default_factory=list)
    average_completion_time: Optional[float] = Field(None, description="Tempo médio em segundos")
    
    # Padrões de uso
    peak_usage_hours: List[int] = Field(default_factory=list)
    user_agents: Dict[str, int] = Field(default_factory=dict)
    
    # Tendências
    submission_trend: List[Dict[str, Any]] = Field(default_factory=list)
    error_trend: List[Dict[str, Any]] = Field(default_factory=list)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        } 