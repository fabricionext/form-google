"""
Adapters package for external service integration.

This module contains adapter classes that provide abstraction
for external services like Google Drive, document generators, etc.
"""

from .google_drive import GoogleDriveAdapter
from .enhanced_google_drive import EnhancedGoogleDriveAdapter
from .document_generator import DocumentGeneratorAdapter
from .cache_adapter import CacheAdapter

__all__ = [
    'GoogleDriveAdapter',
    'EnhancedGoogleDriveAdapter', 
    'DocumentGeneratorAdapter',
    'CacheAdapter'
] 