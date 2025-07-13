"""
Base LLM service abstract class.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from ...config.models import LLMServiceConfig
from ...utils.cache import SimpleCache

logger = logging.getLogger(__name__)


class LLMService(ABC):
    """Abstract base class for LLM service providers."""
    
    def __init__(self, config: LLMServiceConfig, cache: Optional[SimpleCache] = None):
        self.config = config
        self.cache = cache
    
    async def query(self, prompt: str, role_prompt: str, retries: int = 3, delay: float = 1.0) -> Dict[str, Any]:
        """
        Query the LLM service with retry logic and caching.
        
        Args:
            prompt: The user prompt
            role_prompt: The system/role prompt
            retries: Number of retry attempts
            delay: Base delay between retries
            
        Returns:
            Dict containing response, tokens_used, cost, and any errors
        """
        cache_key = f"{self.config.model}-{role_prompt}-{prompt}"
        
        # Check cache first
        if self.cache and (cached_result := self.cache.get(cache_key)):
            logger.info(f"Cache hit for service '{self.config.model}'.")
            return cached_result
        
        # Retry logic
        for attempt in range(retries):
            try:
                result = await self._perform_query(prompt, role_prompt)
                if self.cache:
                    self.cache.set(cache_key, result)
                return result
            except Exception as e:
                logger.warning(f"Query attempt {attempt + 1}/{retries} failed for '{self.config.model}': {e}")
                if attempt + 1 == retries:
                    logger.error(f"All query attempts failed for '{self.config.model}'.")
                    return {"error": str(e), "response": "", "tokens_used": 0, "cost": 0.0}
                await asyncio.sleep(delay * (2 ** attempt))
        
        return {"error": "Exhausted all retry attempts."}
    
    @abstractmethod
    async def _perform_query(self, prompt: str, role_prompt: str) -> Dict[str, Any]:
        """Perform the actual query to the LLM service."""
        pass 