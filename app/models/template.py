"""
Modelo de Template para o sistema peticionador.
"""

from typing import Dict, Any, List, Optional
from sqlalchemy import Column, String, Text, Boolean, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
from app.config.constants import MAX_TEMPLATE_NAME_LENGTH


class Template(BaseModel):
    """Modelo para templates de documentos."""
    
    __tablename__ = "templates"
    
    # Identificação
    name = Column(String(MAX_TEMPLATE_NAME_LENGTH), nullable=False, index=True)
    slug = Column(String(MAX_TEMPLATE_NAME_LENGTH), nullable=False, unique=True, index=True)
    description = Column(Text)
    
    # Google Drive
    google_drive_id = Column(String(100), nullable=False, unique=True)
    google_drive_folder_id = Column(String(100))
    
    # Status e configuração
    is_active = Column(Boolean, default=True, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    
    # Metadata
    category = Column(String(50), index=True)
    tags = Column(Text)  # JSON string
    
    # Relacionamentos
    placeholders = relationship(
        "Placeholder", 
        back_populates="template", 
        cascade="all, delete-orphan",
        lazy="select"
    )
    
    documents = relationship(
        "Document",
        back_populates="template",
        lazy="select"
    )
    
    def to_dict(self, include_placeholders: bool = False, exclude: list = None) -> Dict[str, Any]:
        """
        Converte template para dicionário.
        
        Args:
            include_placeholders: Se deve incluir placeholders
            exclude: Campos para excluir
            
        Returns:
            Dicionário com dados do template
        """
        data = super().to_dict(exclude)
        
        if include_placeholders:
            data['placeholders'] = [ph.to_dict() for ph in self.placeholders]
        else:
            data['placeholders_count'] = len(self.placeholders)
        
        # Parse tags if exists
        if self.tags:
            try:
                import json
                data['tags'] = json.loads(self.tags)
            except (json.JSONDecodeError, TypeError):
                data['tags'] = []
        else:
            data['tags'] = []
        
        return data
    
    def set_tags(self, tags: List[str]) -> None:
        """
        Define tags do template.
        
        Args:
            tags: Lista de tags
        """
        import json
        self.tags = json.dumps(tags) if tags else None
    
    def get_tags(self) -> List[str]:
        """
        Retorna tags do template.
        
        Returns:
            Lista de tags
        """
        if not self.tags:
            return []
        
        try:
            import json
            return json.loads(self.tags)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def add_placeholder(self, placeholder: 'Placeholder') -> None:
        """
        Adiciona placeholder ao template.
        
        Args:
            placeholder: Instância de placeholder
        """
        placeholder.template = self
        self.placeholders.append(placeholder)
    
    def get_placeholders_by_category(self, category: str) -> List['Placeholder']:
        """
        Retorna placeholders de uma categoria específica.
        
        Args:
            category: Categoria dos placeholders
            
        Returns:
            Lista de placeholders da categoria
        """
        return [ph for ph in self.placeholders if ph.category == category]
    
    def get_required_placeholders(self) -> List['Placeholder']:
        """
        Retorna placeholders obrigatórios.
        
        Returns:
            Lista de placeholders obrigatórios
        """
        return [ph for ph in self.placeholders if ph.required]
    
    def validate_data(self, data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Valida dados contra placeholders do template.
        
        Args:
            data: Dados para validar
            
        Returns:
            Tupla (is_valid, error_messages)
        """
        errors = []
        
        # Verifica placeholders obrigatórios
        required_placeholders = self.get_required_placeholders()
        for placeholder in required_placeholders:
            if placeholder.name not in data or not data[placeholder.name]:
                errors.append(f"Campo obrigatório '{placeholder.label}' não preenchido")
        
        # Valida tipos de dados
        for placeholder in self.placeholders:
            if placeholder.name in data:
                value = data[placeholder.name]
                if not placeholder.validate_value(value):
                    errors.append(f"Valor inválido para '{placeholder.label}'")
        
        return len(errors) == 0, errors
    
    @classmethod
    def find_by_slug(cls, slug: str) -> Optional['Template']:
        """
        Busca template por slug.
        
        Args:
            slug: Slug do template
            
        Returns:
            Template ou None
        """
        return cls.query.filter_by(slug=slug, is_active=True).first()
    
    @classmethod
    def find_active(cls) -> List['Template']:
        """
        Retorna todos os templates ativos.
        
        Returns:
            Lista de templates ativos
        """
        return cls.query.filter_by(is_active=True).order_by(cls.name).all()
    
    @classmethod
    def find_by_category(cls, category: str) -> List['Template']:
        """
        Busca templates por categoria.
        
        Args:
            category: Categoria dos templates
            
        Returns:
            Lista de templates da categoria
        """
        return cls.query.filter_by(category=category, is_active=True).order_by(cls.name).all()
    
    def deactivate(self) -> None:
        """Desativa template (soft delete)."""
        self.is_active = False
        self.save()
    
    def increment_version(self) -> None:
        """Incrementa versão do template."""
        self.version += 1
        self.save()
    
    def __repr__(self) -> str:
        """Representação string do template."""
        return f"<Template(id={self.id}, name='{self.name}', slug='{self.slug}')>"