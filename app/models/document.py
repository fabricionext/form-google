"""
Modelo de Document para o sistema peticionador.
"""

from typing import Dict, Any, Optional
from sqlalchemy import Column, String, Text, Integer, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import BaseModel
from app.config.constants import (
    MAX_DOCUMENT_TITLE_LENGTH,
    DOCUMENT_STATUSES,
    DOCUMENT_STATUS_DRAFT
)


class Document(BaseModel):
    """Modelo para documentos gerados."""
    
    __tablename__ = "documents"
    
    # Identificação
    title = Column(String(MAX_DOCUMENT_TITLE_LENGTH), nullable=False)
    slug = Column(String(MAX_DOCUMENT_TITLE_LENGTH), nullable=False, unique=True, index=True)
    
    # Status e progresso
    status = Column(String(50), nullable=False, default=DOCUMENT_STATUS_DRAFT, index=True)
    progress_percentage = Column(Integer, default=0)
    
    # Google Drive
    google_drive_id = Column(String(100), unique=True)
    google_drive_url = Column(Text)
    
    # Relacionamentos
    template_id = Column(Integer, ForeignKey('templates.id'), nullable=False)
    template = relationship("Template", back_populates="documents")
    
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=True)
    client = relationship("Client", back_populates="documents")
    
    # Dados preenchidos
    form_data = Column(JSON)  # Dados do formulário submetido
    
    # Metadados de processamento
    generation_started_at = Column(DateTime)
    generation_completed_at = Column(DateTime)
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    
    # Auditoria
    created_by_user_id = Column(Integer)  # ID do usuário que criou
    
    def to_dict(self, include_form_data: bool = False, exclude: list = None) -> Dict[str, Any]:
        """
        Converte documento para dicionário.
        
        Args:
            include_form_data: Se deve incluir dados do formulário
            exclude: Campos para excluir
            
        Returns:
            Dicionário com dados do documento
        """
        exclude = exclude or []
        if not include_form_data:
            exclude.append('form_data')
        
        data = super().to_dict(exclude)
        
        # Adiciona informações do template
        if self.template:
            data['template_name'] = self.template.name
            data['template_slug'] = self.template.slug
        
        # Adiciona informações do cliente
        if self.client:
            data['client_name'] = self.client.nome_completo
            data['client_email'] = self.client.email
        
        # Calcula duração da geração se disponível
        if self.generation_started_at and self.generation_completed_at:
            duration = self.generation_completed_at - self.generation_started_at
            data['generation_duration_seconds'] = duration.total_seconds()
        
        return data
    
    def start_generation(self) -> None:
        """Marca início da geração do documento."""
        self.status = "processing"
        self.generation_started_at = datetime.utcnow()
        self.progress_percentage = 0
        self.save()
    
    def complete_generation(self, google_drive_id: str, google_drive_url: str) -> None:
        """
        Marca conclusão da geração do documento.
        
        Args:
            google_drive_id: ID do arquivo no Google Drive
            google_drive_url: URL do arquivo no Google Drive
        """
        self.status = "completed"
        self.generation_completed_at = datetime.utcnow()
        self.progress_percentage = 100
        self.google_drive_id = google_drive_id
        self.google_drive_url = google_drive_url
        self.error_message = None
        self.save()
    
    def fail_generation(self, error_message: str) -> None:
        """
        Marca falha na geração do documento.
        
        Args:
            error_message: Mensagem de erro
        """
        self.status = "error"
        self.error_message = error_message
        self.retry_count += 1
        self.save()
    
    def update_progress(self, percentage: int) -> None:
        """
        Atualiza progresso da geração.
        
        Args:
            percentage: Percentual de progresso (0-100)
        """
        self.progress_percentage = max(0, min(100, percentage))
        self.save()
    
    def reset_for_retry(self) -> None:
        """Reseta documento para nova tentativa de geração."""
        self.status = DOCUMENT_STATUS_DRAFT
        self.progress_percentage = 0
        self.generation_started_at = None
        self.generation_completed_at = None
        self.google_drive_id = None
        self.google_drive_url = None
        self.error_message = None
        self.save()
    
    def can_retry(self, max_retries: int = 3) -> bool:
        """
        Verifica se pode tentar gerar novamente.
        
        Args:
            max_retries: Número máximo de tentativas
            
        Returns:
            True se pode tentar novamente
        """
        return self.status == "error" and self.retry_count < max_retries
    
    def is_processing(self) -> bool:
        """Verifica se documento está sendo processado."""
        return self.status == "processing"
    
    def is_completed(self) -> bool:
        """Verifica se documento foi gerado com sucesso."""
        return self.status == "completed" and self.google_drive_id is not None
    
    def has_error(self) -> bool:
        """Verifica se documento tem erro."""
        return self.status == "error"
    
    def get_form_data_value(self, placeholder_name: str, default: Any = None) -> Any:
        """
        Obtém valor de um placeholder dos dados do formulário.
        
        Args:
            placeholder_name: Nome do placeholder
            default: Valor padrão se não encontrado
            
        Returns:
            Valor do placeholder
        """
        if not self.form_data:
            return default
        
        return self.form_data.get(placeholder_name, default)
    
    def set_form_data(self, data: Dict[str, Any]) -> None:
        """
        Define dados do formulário.
        
        Args:
            data: Dados do formulário
        """
        self.form_data = data
        self.save()
    
    def validate_form_data(self) -> tuple[bool, list]:
        """
        Valida dados do formulário contra o template.
        
        Returns:
            Tupla (is_valid, error_messages)
        """
        if not self.template:
            return False, ["Template não encontrado"]
        
        if not self.form_data:
            return False, ["Dados do formulário não fornecidos"]
        
        return self.template.validate_data(self.form_data)
    
    @classmethod
    def find_by_status(cls, status: str) -> list:
        """
        Busca documentos por status.
        
        Args:
            status: Status dos documentos
            
        Returns:
            Lista de documentos
        """
        return cls.query.filter_by(status=status).order_by(cls.created_at.desc()).all()
    
    @classmethod
    def find_by_template(cls, template_id: int) -> list:
        """
        Busca documentos por template.
        
        Args:
            template_id: ID do template
            
        Returns:
            Lista de documentos
        """
        return cls.query.filter_by(template_id=template_id).order_by(cls.created_at.desc()).all()
    
    @classmethod
    def find_by_client(cls, client_id: int) -> list:
        """
        Busca documentos por cliente.
        
        Args:
            client_id: ID do cliente
            
        Returns:
            Lista de documentos
        """
        return cls.query.filter_by(client_id=client_id).order_by(cls.created_at.desc()).all()
    
    @classmethod
    def find_by_slug(cls, slug: str) -> Optional['Document']:
        """
        Busca documento por slug.
        
        Args:
            slug: Slug do documento
            
        Returns:
            Documento ou None
        """
        return cls.query.filter_by(slug=slug).first()
    
    @classmethod
    def find_pending_processing(cls) -> list:
        """
        Busca documentos pendentes de processamento.
        
        Returns:
            Lista de documentos em status draft ou error (que podem ser retentados)
        """
        return cls.query.filter(
            cls.status.in_([DOCUMENT_STATUS_DRAFT, "error"])
        ).order_by(cls.created_at).all()
    
    @classmethod
    def count_by_status(cls) -> Dict[str, int]:
        """
        Conta documentos por status.
        
        Returns:
            Dicionário com contagem por status
        """
        from sqlalchemy import func
        
        results = cls.query.with_entities(
            cls.status, 
            func.count(cls.id)
        ).group_by(cls.status).all()
        
        return {status: count for status, count in results}
    
    def __repr__(self) -> str:
        """Representação string do documento."""
        return f"<Document(id={self.id}, title='{self.title}', status='{self.status}')>"