"""
Repositories para acesso a dados do sistema peticionador.
"""

from .base import BaseRepository
from .template_repository import TemplateRepository
from .document_repository import DocumentRepository
from .placeholder_repository import PlaceholderRepository
from .client_repository import ClientRepository

__all__ = [
    'BaseRepository',
    'TemplateRepository', 
    'DocumentRepository',
    'PlaceholderRepository',
    'ClientRepository'
]