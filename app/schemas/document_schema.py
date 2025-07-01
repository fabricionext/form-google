from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class DocumentTemplateBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=255, description="Nome do template")
    description: Optional[str] = Field(None, description="Descrição do template")
    category: Optional[str] = Field(None, description="Categoria do template")
    google_doc_id: str = Field(..., max_length=255, description="ID do documento no Google Docs")
    pasta_destino_id: Optional[str] = Field(None, max_length=255, description="ID da pasta de destino no Google Drive")
    status: str = Field("draft", description="Status do template (draft, active, archived)")


class DocumentTemplateCreate(DocumentTemplateBase):
    pass


class DocumentTemplateUpdate(DocumentTemplateBase):
    name: Optional[str] = Field(None, min_length=3, max_length=255)
    google_doc_id: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    pasta_destino_id: Optional[str] = None
    status: Optional[str] = None


class DocumentTemplateInDB(DocumentTemplateBase):
    id: UUID
    version: int
    thumbnail: Optional[str] = None
    usage_count: int = 0
    last_sync: Optional[datetime] = None
    detected_fields: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DocumentTemplateSchema(DocumentTemplateInDB):
    """Schema para expor na API."""
    pass


class DocumentTemplateListSchema(BaseModel):
    """Schema para listagem de templates."""
    id: UUID
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    status: str
    thumbnail: Optional[str] = None
    usage_count: int
    last_sync: Optional[datetime] = None
    detected_fields: Optional[List[str]] = None
    updated_at: datetime

    class Config:
        from_attributes = True 