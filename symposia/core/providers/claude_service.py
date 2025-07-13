"""
Anthropic Claude service implementation.
"""

import os
from typing import Dict, Any, Optional

import anthropic

from .base import LLMService
from ...config.models import LLMServiceConfig
from ...utils.cache import SimpleCache


class ClaudeService(LLMService):
    """Anthropic Claude service implementation."""
    
    def __init__(self, config: LLMServiceConfig, cache: Optional[SimpleCache] = None):
        super().__init__(config, cache)
        api_key = config.api_key or os.getenv("ANTHROPIC_API_KEY")
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
    
    async def _perform_query(self, prompt: str, role_prompt: str) -> Dict[str, Any]:
        message = await self.client.messages.create(
            model=self.config.model,
            system=role_prompt,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = message.content[0].text if message.content else ""
        
        # Safely get token counts with fallbacks
        try:
            input_tokens = message.usage.input_tokens
            output_tokens = message.usage.output_tokens
            tokens_used = input_tokens + output_tokens
            
            # Calculate cost based on input/output token breakdown
            cost = (input_tokens * self.config.cost_per_token.input + 
                   output_tokens * self.config.cost_per_token.output)
        except (AttributeError, TypeError, ValueError):
            # If token counting fails, default to 0
            tokens_used = 0
            cost = 0.0
        
        return {
            "response": response_text,
            "tokens_used": tokens_used,
            "cost": cost
        } 