"""
Modelos de dados do sistema peticionador.
"""

from .base import BaseModel
from .template import Template
from .document import Document
from .placeholder import Placeholder
from .client import Client

__all__ = [
    'BaseModel',
    'Template',
    'Document', 
    'Placeholder',
    'Client'
]