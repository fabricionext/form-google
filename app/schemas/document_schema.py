"""
Document Schemas - Validação Pydantic para Documentos
=====================================================

Schemas para validação de dados de entrada e saída para geração de documentos.
Define o DocumentGenerationSchema conforme especificações.
"""

from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


class DocumentStatusEnum(str, Enum):
    """Enum para status de documento."""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DocumentGenerationSchema(BaseModel):
    """
    Schema para dados de entrada na geração de documentos.
    
    Define os campos esperados e suas validações conforme especificação:
    - Validação de entrada (data e options) 
    - Campos obrigatórios e opcionais
    - Validação de tipos de dados
    """
    
    # Dados principais do formulário
    template_id: int = Field(..., description="ID do template")
    
    # Dados do cliente/autor principal
    cliente_nome: Optional[str] = Field(None, min_length=2, max_length=150)
    cliente_cpf: Optional[str] = Field(None, pattern=r'^\d{3}\.\d{3}\.\d{3}-\d{2}$')
    cliente_email: Optional[str] = Field(None, pattern=r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
    cliente_telefone: Optional[str] = Field(None)
    cliente_endereco: Optional[str] = Field(None, max_length=500)
    
    # Múltiplos autores (dinâmico)
    autor_1_nome: Optional[str] = Field(None, min_length=2, max_length=150)
    autor_1_cpf: Optional[str] = Field(None, pattern=r'^\d{3}\.\d{3}\.\d{3}-\d{2}$')
    autor_1_endereco: Optional[str] = Field(None, max_length=500)
    
    autor_2_nome: Optional[str] = Field(None, min_length=2, max_length=150)
    autor_2_cpf: Optional[str] = Field(None, pattern=r'^\d{3}\.\d{3}\.\d{3}-\d{2}$')
    autor_2_endereco: Optional[str] = Field(None, max_length=500)
    
    autor_3_nome: Optional[str] = Field(None, min_length=2, max_length=150)
    autor_3_cpf: Optional[str] = Field(None, pattern=r'^\d{3}\.\d{3}\.\d{3}-\d{2}$')
    autor_3_endereco: Optional[str] = Field(None, max_length=500)
    
    # Autoridades de trânsito
    autoridade_1_nome: Optional[str] = Field(None, min_length=2, max_length=200)
    autoridade_1_cnpj: Optional[str] = Field(None, pattern=r'^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$')
    autoridade_1_endereco: Optional[str] = Field(None, max_length=500)
    
    autoridade_2_nome: Optional[str] = Field(None, min_length=2, max_length=200)
    autoridade_2_cnpj: Optional[str] = Field(None, pattern=r'^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$')
    autoridade_2_endereco: Optional[str] = Field(None, max_length=500)
    
    autoridade_3_nome: Optional[str] = Field(None, min_length=2, max_length=200)
    autoridade_3_cnpj: Optional[str] = Field(None, pattern=r'^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$')
    autoridade_3_endereco: Optional[str] = Field(None, max_length=500)
    
    # Dados específicos de veículo
    veiculo_placa: Optional[str] = Field(None, pattern=r'^[A-Z]{3}-?\d{4}$')
    veiculo_modelo: Optional[str] = Field(None, max_length=100)
    veiculo_ano: Optional[int] = Field(None, ge=1950, le=2030)
    veiculo_cor: Optional[str] = Field(None, max_length=50)
    veiculo_chassi: Optional[str] = Field(None, max_length=50)
    veiculo_renavam: Optional[str] = Field(None, max_length=20)
    
    # Dados de infração
    infracao_numero: Optional[str] = Field(None, max_length=50)
    infracao_data: Optional[str] = Field(None)  # Formato ISO ou dd/mm/yyyy
    infracao_local: Optional[str] = Field(None, max_length=300)
    infracao_codigo: Optional[str] = Field(None, max_length=20)
    infracao_velocidade_permitida: Optional[int] = Field(None, ge=0, le=200)
    infracao_velocidade_aferida: Optional[int] = Field(None, ge=0, le=300)
    
    # Dados de processo
    processo_numero: Optional[str] = Field(None, max_length=50)
    processo_data: Optional[str] = Field(None)
    processo_valor: Optional[float] = Field(None, ge=0)
    
    # Metadados do documento
    document_name: Optional[str] = Field(None, max_length=200)
    observacoes: Optional[str] = Field(None, max_length=1000)
    
    # Opções de geração
    options: Optional[Dict[str, Any]] = Field(
        None,
        description="Opções específicas de geração"
    )
    
    @validator('infracao_data', 'processo_data')
    def validate_date_format(cls, v):
        """Valida formato de data."""
        if v is None:
            return v
        
        # Tentar diferentes formatos
        for fmt in ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y']:
            try:
                datetime.strptime(v, fmt)
                return v
            except ValueError:
                continue
        
        raise ValueError('Data deve estar no formato dd/mm/yyyy ou yyyy-mm-dd')
    
    @validator('template_id')
    def validate_template_id(cls, v):
        """Valida template ID."""
        if v <= 0:
            raise ValueError('Template ID deve ser positivo')
        return v
    
    @validator('*', pre=True)
    def strip_strings(cls, v):
        """Remove espaços em branco de strings."""
        if isinstance(v, str):
            return v.strip() if v.strip() else None
        return v
    
    class Config:
        # Permitir campos extras para flexibilidade
        extra = "allow"
        # Validar todos os campos
        validate_assignment = True


class DocumentGenerationOptionsSchema(BaseModel):
    """Schema para opções de geração de documento."""
    
    target_folder: Optional[str] = Field(None, description="Pasta de destino no Google Drive")
    custom_name: Optional[str] = Field(None, description="Nome customizado do documento")
    
    # Opções de nomenclatura
    naming_options: Optional[Dict[str, Any]] = Field(
        None,
        description="Opções para geração do nome do arquivo"
    )
    
    # Processamento condicional
    process_conditional_blocks: bool = Field(
        True,
        description="Processar blocos condicionais"
    )
    
    # Imagens
    images: Optional[Dict[str, str]] = Field(
        None,
        description="Mapeamento placeholder -> caminho da imagem"
    )
    
    # Validação avançada
    skip_validation: bool = Field(
        False,
        description="Pular validação de dados"
    )
    
    # Notificações
    notify_completion: bool = Field(
        True,
        description="Notificar quando completar"
    )
    
    notify_email: Optional[str] = Field(
        None,
        pattern=r'^[^\s@]+@[^\s@]+\.[^\s@]+$',
        description="Email para notificação"
    )


class DocumentResponseSchema(BaseModel):
    """Schema para resposta de documento gerado."""
    
    success: bool = Field(..., description="Se a operação foi bem-sucedida")
    
    # IDs e identificadores
    document_id: Optional[int] = Field(None, description="ID do documento no banco")
    google_doc_id: Optional[str] = Field(None, description="ID do Google Doc")
    task_id: Optional[str] = Field(None, description="ID da tarefa Celery")
    
    # URLs e links
    document_url: Optional[str] = Field(None, description="URL do documento")
    edit_url: Optional[str] = Field(None, description="URL de edição")
    download_url: Optional[str] = Field(None, description="URL de download")
    
    # Informações do documento
    document_name: Optional[str] = Field(None, description="Nome do documento")
    document_type: Optional[str] = Field(None, description="Tipo do documento")
    
    # Status e progresso
    status: DocumentStatusEnum = Field(..., description="Status da geração")
    progress: Optional[int] = Field(None, ge=0, le=100, description="Progresso da geração")
    
    # Timestamps
    started_at: Optional[datetime] = Field(None, description="Início da geração")
    completed_at: Optional[datetime] = Field(None, description="Conclusão da geração")
    estimated_completion: Optional[datetime] = Field(None, description="Estimativa de conclusão")
    
    # Métricas
    generation_time: Optional[float] = Field(None, description="Tempo de geração em segundos")
    estimated_time: Optional[int] = Field(None, description="Tempo estimado em segundos")
    
    # Metadata e detalhes
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadados adicionais")
    
    # Erros e warnings
    errors: Optional[List[str]] = Field(None, description="Lista de erros")
    warnings: Optional[List[str]] = Field(None, description="Lista de avisos")
    
    # Mensagem
    message: str = Field(..., description="Mensagem descritiva")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DocumentStatusSchema(BaseModel):
    """Schema para consulta de status de documento."""
    
    task_id: str = Field(..., description="ID da tarefa")
    status: DocumentStatusEnum = Field(..., description="Status atual")
    progress: int = Field(0, ge=0, le=100, description="Progresso da geração")
    
    # Detalhes do progresso
    current_step: Optional[str] = Field(None, description="Etapa atual")
    total_steps: Optional[int] = Field(None, description="Total de etapas")
    
    # Timestamps
    started_at: Optional[datetime] = Field(None, description="Início da tarefa")
    updated_at: datetime = Field(..., description="Última atualização")
    estimated_completion: Optional[datetime] = Field(None, description="Estimativa de conclusão")
    
    # Resultado
    result: Optional[Dict[str, Any]] = Field(None, description="Resultado da tarefa")
    error: Optional[str] = Field(None, description="Erro se houver")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DocumentListSchema(BaseModel):
    """Schema para listagem de documentos."""
    
    id: int = Field(..., description="ID do documento")
    name: str = Field(..., description="Nome do documento")
    type: str = Field(..., description="Tipo do documento")
    status: DocumentStatusEnum = Field(..., description="Status")
    
    # Template info
    template_id: int = Field(..., description="ID do template")
    template_name: Optional[str] = Field(None, description="Nome do template")
    
    # Cliente info
    client_name: Optional[str] = Field(None, description="Nome do cliente")
    client_cpf: Optional[str] = Field(None, description="CPF do cliente")
    
    # Timestamps
    created_at: datetime = Field(..., description="Data de criação")
    completed_at: Optional[datetime] = Field(None, description="Data de conclusão")
    
    # URLs
    view_url: Optional[str] = Field(None, description="URL de visualização")
    edit_url: Optional[str] = Field(None, description="URL de edição")
    
    # Métricas
    generation_time: Optional[float] = Field(None, description="Tempo de geração")
    file_size: Optional[int] = Field(None, description="Tamanho do arquivo")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DocumentValidationSchema(BaseModel):
    """Schema para resultado de validação de documento."""
    
    is_valid: bool = Field(..., description="Se os dados são válidos")
    errors: List[str] = Field(default_factory=list, description="Lista de erros")
    warnings: List[str] = Field(default_factory=list, description="Lista de avisos")
    suggestions: List[str] = Field(default_factory=list, description="Sugestões de melhoria")
    
    # Detalhes de validação
    required_fields_missing: List[str] = Field(default_factory=list)
    invalid_formats: Dict[str, str] = Field(default_factory=dict)
    business_rule_violations: List[str] = Field(default_factory=list)
    
    # Estatísticas
    total_fields: int = Field(0, description="Total de campos")
    valid_fields: int = Field(0, description="Campos válidos")
    invalid_fields: int = Field(0, description="Campos inválidos")
    
    # Sugestões automáticas
    autocomplete_suggestions: Optional[Dict[str, List[str]]] = Field(
        None, 
        description="Sugestões de autocomplete por campo"
    ) 