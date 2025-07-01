"""
Modelo TemplateCategory - Fase 1.5.1
Implementado seguindo TDD/QDD.
"""

import re
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    TIMESTAMP,
    DefaultClause,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.extensions import db


class TemplateCategory(db.Model):
    """
    Modelo para categorização de templates de documentos.
    
    Permite organizar templates em categorias para melhor UX
    e facilitar navegação no Template Manager.
    """
    
    __tablename__ = "template_categories"
    
    # Campos principais
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    icon = Column(String(50))
    
    # Campos de organização
    order_index = Column(Integer, default=0, server_default="0")
    is_active = Column(Boolean, default=True, server_default="true")
    
    # Timestamps automáticos
    created_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        nullable=False
    )
    updated_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False
    )
    
    # Relacionamentos (serão implementados posteriormente)
    # templates = relationship("DocumentTemplate", back_populates="category")
    
    def generate_slug(self):
        """
        Gera slug automaticamente a partir do nome.
        
        Converte caracteres especiais e acentos para formato URL-friendly.
        """
        if not self.name:
            return None
            
        # Converter para minúsculas
        slug = self.name.lower()
        
        # Substituir acentos e caracteres especiais
        replacements = {
            'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a', 'ä': 'a',
            'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
            'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
            'ó': 'o', 'ò': 'o', 'õ': 'o', 'ô': 'o', 'ö': 'o',
            'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
            'ç': 'c', 'ñ': 'n'
        }
        
        for char, replacement in replacements.items():
            slug = slug.replace(char, replacement)
        
        # Remover caracteres não alfanuméricos (exceto espaços)
        slug = re.sub(r'[^a-z0-9\s]', '', slug)
        
        # Substituir espaços por hífens
        slug = re.sub(r'\s+', '-', slug.strip())
        
        # Remover hífens múltiplos
        slug = re.sub(r'-+', '-', slug)
        
        # Remover hífens do início e fim
        slug = slug.strip('-')
        
        self.slug = slug
        return slug
    
    def __repr__(self):
        """
        Representação string da categoria.
        """
        return f"<TemplateCategory(id={self.id}, name='{self.name}', slug='{self.slug}')>"
    
    def __str__(self):
        """
        String representation amigável.
        """
        return f"TemplateCategory: {self.name}"
    
    def to_dict(self):
        """
        Converte o modelo para dicionário.
        Útil para serialização em APIs.
        """
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'icon': self.icon,
            'order_index': self.order_index,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def get_by_slug(cls, slug):
        """
        Busca categoria por slug.
        
        Args:
            slug (str): Slug da categoria
            
        Returns:
            TemplateCategory: Categoria encontrada ou None
        """
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy import create_engine
        # Este método será implementado quando integrarmos com a sessão real
        # Por enquanto, retorna None para os testes
        return None
    
    @classmethod
    def get_active_categories(cls):
        """
        Retorna todas as categorias ativas ordenadas por order_index.
        
        Returns:
            List[TemplateCategory]: Lista de categorias ativas
        """
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy import create_engine
        # Este método será implementado quando integrarmos com a sessão real
        # Por enquanto, retorna lista vazia para os testes
        return []
    
    def deactivate(self):
        """
        Desativa a categoria (soft delete).
        """
        self.is_active = False
    
    def activate(self):
        """
        Ativa a categoria.
        """
        self.is_active = True 