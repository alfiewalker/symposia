"""
Simple in-memory caching for LLM responses.
"""

from typing import Any, Optional


class SimpleCache:
    """A basic in-memory cache for storing LLM responses."""
    
    def __init__(self):
        self._cache = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from cache."""
        return self._cache.get(key)
    
    def set(self, key: str, value: Any) -> None:
        """Store a value in cache."""
        self._cache[key] = value 