"""
Cache Adapter - Placeholder
==========================

Adapter básico para cache.
"""

import logging

logger = logging.getLogger(__name__)


class CacheAdapter:
    """Adapter para cache."""
    
    def __init__(self):
        self.logger = logger
    
    def get(self, key: str):
        """Get value from cache."""
        return None
    
    def set(self, key: str, value, ttl: int = 3600):
        """Set value in cache."""
        pass
    
    def delete(self, key: str):
        """Delete value from cache."""
        pass 