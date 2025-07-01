from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    TIMESTAMP,
    ForeignKey,
    DefaultClause,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from .base import Base


class GeneratedForm(Base):
    __tablename__ = "generated_forms"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=DefaultClause(func.gen_random_uuid()),
    )
    template_id = Column(UUID(as_uuid=True), ForeignKey("document_templates.id"))
    name = Column(String(255))
    slug = Column(String(255), unique=True)
    public_url = Column(String(500))
    expires_at = Column(TIMESTAMP)
    max_submissions = Column(Integer)
    status = Column(String(50), default="active", server_default="active")

    # Relationships
    template = relationship("DocumentTemplate", back_populates="generated_forms")
    submissions = relationship(
        "FormSubmission", back_populates="form", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<GeneratedForm(id={self.id}, name='{self.name}')>"


class FormSubmission(Base):
    __tablename__ = "form_submissions"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=DefaultClause(func.gen_random_uuid()),
    )
    form_id = Column(
        UUID(as_uuid=True),
        ForeignKey("generated_forms.id"),
        nullable=False,
    )
    client_id = Column(Integer, ForeignKey("clientes.id"))
    data = Column(JSONB, nullable=False)
    status = Column(String(50), default="draft", server_default="draft")
    submitted_at = Column(TIMESTAMP)
    processed_at = Column(TIMESTAMP)
    document_id = Column(String(255))
    document_url = Column(Text)

    # Relationships
    form = relationship("GeneratedForm", back_populates="submissions")
    # Assuming 'Cliente' model exists in 'client.py' and has a relationship 'submissions'
    # client = relationship("Cliente", back_populates="submissions")

    def __repr__(self):
        return f"<FormSubmission(id={self.id}, form_id='{self.form_id}')>" 