from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Text,
    ForeignKey,
    DefaultClause,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from .base import Base


class TemplatePlaceholder(Base):
    __tablename__ = "template_placeholders"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=DefaultClause(func.gen_random_uuid()),
    )
    template_id = Column(
        UUID(as_uuid=True),
        ForeignKey("document_templates.id", ondelete="CASCADE"),
        nullable=False,
    )
    key = Column(String(255), nullable=False)
    label = Column(String(255))
    type = Column(String(50))
    required = Column(Boolean, default=False, server_default="false")
    validation_rules = Column(JSONB)
    default_value = Column(Text)
    options = Column(JSONB)
    order_index = Column(Integer)

    # Relationships
    template = relationship("DocumentTemplate", back_populates="placeholders")

    def __repr__(self):
        return f"<TemplatePlaceholder(id={self.id}, key='{self.key}')>" 