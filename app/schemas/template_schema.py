"""
Template Schemas - Validação Pydantic para Templates
====================================================

Schemas para validação de dados de entrada e saída para templates.
Garante validação rigorosa antes do processamento pelos Services.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum

from app.config.constants import DocumentTypes


class TemplateTypeEnum(str, Enum):
    """Enum para tipos de documento válidos."""
    FICHA_CADASTRAL_PF = DocumentTypes.FICHA_CADASTRAL_PF.value
    FICHA_CADASTRAL_PJ = DocumentTypes.FICHA_CADASTRAL_PJ.value
    DEFESA_PREVIA = DocumentTypes.DEFESA_PREVIA.value
    RECURSO_JARI = DocumentTypes.RECURSO_JARI.value
    TERMO_ACORDO = DocumentTypes.TERMO_ACORDO.value
    ACAO_ANULATORIA = DocumentTypes.ACAO_ANULATORIA.value


class TemplateCreateSchema(BaseModel):
    """Schema para criação de template."""
    
    nome: str = Field(
        ..., 
        min_length=3, 
        max_length=150,
        description="Nome do template"
    )
    
    descricao: Optional[str] = Field(
        None,
        max_length=500,
        description="Descrição do template"
    )
    
    tipo: TemplateTypeEnum = Field(
        ...,
        description="Tipo de documento"
    )
    
    google_doc_id: str = Field(
        ...,
        min_length=10,
        max_length=100,
        description="ID do documento Google Docs"
    )
    
    categoria: Optional[str] = Field(
        None,
        max_length=50,
        description="Categoria do template"
    )
    
    ativo: bool = Field(
        True,
        description="Se o template está ativo"
    )
    
    tags: Optional[List[str]] = Field(
        None,
        description="Tags para categorização"
    )
    
    @validator('nome')
    def validate_nome(cls, v):
        """Valida nome do template."""
        if not v.strip():
            raise ValueError('Nome não pode ser vazio')
        return v.strip()
    
    @validator('google_doc_id')
    def validate_google_doc_id(cls, v):
        """Valida formato do Google Doc ID."""
        if not v.strip():
            raise ValueError('Google Doc ID é obrigatório')
        # Validação básica do formato
        if len(v.strip()) < 10:
            raise ValueError('Google Doc ID deve ter pelo menos 10 caracteres')
        return v.strip()
    
    @validator('tags')
    def validate_tags(cls, v):
        """Valida tags."""
        if v is not None:
            if len(v) > 10:
                raise ValueError('Máximo de 10 tags permitidas')
            for tag in v:
                if len(tag) > 30:
                    raise ValueError('Tags devem ter no máximo 30 caracteres')
        return v
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TemplateUpdateSchema(BaseModel):
    """Schema para atualização de template."""
    
    nome: Optional[str] = Field(
        None, 
        min_length=3, 
        max_length=150,
        description="Nome do template"
    )
    
    descricao: Optional[str] = Field(
        None,
        max_length=500,
        description="Descrição do template"
    )
    
    tipo: Optional[TemplateTypeEnum] = Field(
        None,
        description="Tipo de documento"
    )
    
    google_doc_id: Optional[str] = Field(
        None,
        min_length=10,
        max_length=100,
        description="ID do documento Google Docs"
    )
    
    categoria: Optional[str] = Field(
        None,
        max_length=50,
        description="Categoria do template"
    )
    
    ativo: Optional[bool] = Field(
        None,
        description="Se o template está ativo"
    )
    
    tags: Optional[List[str]] = Field(
        None,
        description="Tags para categorização"
    )
    
    @validator('nome')
    def validate_nome(cls, v):
        """Valida nome do template."""
        if v is not None and not v.strip():
            raise ValueError('Nome não pode ser vazio')
        return v.strip() if v else None
    
    @validator('google_doc_id')
    def validate_google_doc_id(cls, v):
        """Valida formato do Google Doc ID."""
        if v is not None:
            if not v.strip():
                raise ValueError('Google Doc ID não pode ser vazio')
            if len(v.strip()) < 10:
                raise ValueError('Google Doc ID deve ter pelo menos 10 caracteres')
            return v.strip()
        return None


class PlaceholderSchema(BaseModel):
    """Schema para placeholder."""
    
    chave: str = Field(..., description="Chave do placeholder")
    descricao: Optional[str] = Field(None, description="Descrição do placeholder")
    tipo: str = Field("text", description="Tipo do campo")
    obrigatorio: bool = Field(False, description="Se é obrigatório")
    categoria: Optional[str] = Field(None, description="Categoria do placeholder")
    exemplo: Optional[str] = Field(None, description="Exemplo de valor")


class TemplateSchema(BaseModel):
    """Schema completo para template (response)."""
    
    id: int = Field(..., description="ID do template")
    nome: str = Field(..., description="Nome do template")
    descricao: Optional[str] = Field(None, description="Descrição do template")
    tipo: str = Field(..., description="Tipo de documento")
    google_doc_id: str = Field(..., description="ID do Google Doc")
    categoria: Optional[str] = Field(None, description="Categoria do template")
    ativo: bool = Field(..., description="Se está ativo")
    tags: Optional[List[str]] = Field(None, description="Tags")
    
    # Metadados
    created_at: datetime = Field(..., description="Data de criação")
    updated_at: Optional[datetime] = Field(None, description="Data de atualização")
    last_sync: Optional[datetime] = Field(None, description="Última sincronização")
    
    # Placeholders relacionados
    placeholders: Optional[List[PlaceholderSchema]] = Field(
        None, 
        description="Placeholders do template"
    )
    
    # Estatísticas
    usage_count: Optional[int] = Field(None, description="Quantidade de usos")
    success_rate: Optional[float] = Field(None, description="Taxa de sucesso")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TemplateSyncSchema(BaseModel):
    """Schema para resultado de sincronização."""
    
    template_id: int = Field(..., description="ID do template")
    placeholders_found: int = Field(..., description="Placeholders encontrados")
    placeholders_new: int = Field(..., description="Novos placeholders")
    placeholders_updated: int = Field(..., description="Placeholders atualizados")
    placeholders_removed: int = Field(..., description="Placeholders removidos")
    sync_timestamp: datetime = Field(..., description="Timestamp da sincronização")
    errors: Optional[List[str]] = Field(None, description="Erros durante sincronização")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TemplateStatisticsSchema(BaseModel):
    """Schema para estatísticas do template."""
    
    template_id: int = Field(..., description="ID do template")
    total_documents: int = Field(0, description="Total de documentos gerados")
    successful_documents: int = Field(0, description="Documentos gerados com sucesso")
    failed_documents: int = Field(0, description="Documentos com falha")
    success_rate: float = Field(0.0, description="Taxa de sucesso")
    average_generation_time: Optional[float] = Field(None, description="Tempo médio de geração")
    last_generation: Optional[datetime] = Field(None, description="Última geração")
    most_common_errors: Optional[List[Dict[str, Any]]] = Field(
        None, 
        description="Erros mais comuns"
    )
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TemplateListFiltersSchema(BaseModel):
    """Schema para filtros de listagem."""
    
    tipo: Optional[TemplateTypeEnum] = Field(None, description="Filtrar por tipo")
    categoria: Optional[str] = Field(None, description="Filtrar por categoria")
    ativo: Optional[bool] = Field(None, description="Filtrar por status ativo")
    search: Optional[str] = Field(None, description="Busca textual")
    tags: Optional[List[str]] = Field(None, description="Filtrar por tags")
    created_after: Optional[datetime] = Field(None, description="Criados após")
    created_before: Optional[datetime] = Field(None, description="Criados antes")
    
    @validator('search')
    def validate_search(cls, v):
        """Valida termo de busca."""
        if v is not None and len(v.strip()) < 2:
            raise ValueError('Termo de busca deve ter pelo menos 2 caracteres')
        return v.strip() if v else None 