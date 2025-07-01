from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    TIMESTAMP,
    ForeignKey,
    DefaultClause,
    Float,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from .base import Base


class DocumentTemplateVersion(Base):
    __tablename__ = "document_template_versions"

    id = Column(Integer, primary_key=True)
    template_id = Column(UUID(as_uuid=True), ForeignKey("document_templates.id"), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    
    # Campos espelhados do DocumentTemplate
    name = Column(String(255), nullable=False)
    description = Column(Text)
    google_doc_id = Column(String(255))
    detected_fields = Column(JSONB, nullable=True)
    
    # Metadados da versão
    changed_by_id = Column(Integer, nullable=True) # ID do usuário que fez a alteração
    created_at = Column(
        TIMESTAMP, server_default=func.current_timestamp(), nullable=False
    )

    template = relationship("DocumentTemplate", back_populates="versions")

    class Meta:
        unique_together = ("template_id", "version")

    def __repr__(self):
        return f"<DocumentTemplateVersion(template_id={self.template_id}, version={self.version})>"


class DocumentTemplate(Base):
    __tablename__ = "document_templates"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=DefaultClause(func.gen_random_uuid()),
    )
    name = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100))
    google_doc_id = Column(String(255))
    pasta_destino_id = Column(String(255), nullable=True)  # Pasta no Google Drive
    version = Column(Integer, default=1, server_default="1")
    status = Column(String(50), default="draft", server_default="draft")

    # Novos campos para Fase 2
    thumbnail = Column(String(255), nullable=True)
    usage_count = Column(Integer, default=0, server_default="0", nullable=False)
    last_sync = Column(TIMESTAMP, nullable=True)
    detected_fields = Column(JSONB, nullable=True)  # Armazena uma lista de campos

    created_by = Column(Integer, nullable=True)
    created_at = Column(
        TIMESTAMP, server_default=func.current_timestamp(), nullable=False
    )
    updated_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False,
    )

    # Relationships
    versions = relationship("DocumentTemplateVersion", back_populates="template", cascade="all, delete-orphan", order_by="desc(DocumentTemplateVersion.version)")
    placeholders = relationship(
        "TemplatePlaceholder", back_populates="template", cascade="all, delete-orphan"
    )
    generated_forms = relationship("GeneratedForm", back_populates="template")

    def __repr__(self):
        return f"<DocumentTemplate(id={self.id}, name='{self.name}')>" 