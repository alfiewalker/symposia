"""
OpenAI GPT service implementation.
"""

import os
from typing import Dict, Any, Optional

import openai

from .base import LLMService
from ...config.models import LLMServiceConfig
from ...utils.cache import SimpleCache


class OpenAIService(LLMService):
    """OpenAI GPT service implementation."""
    
    def __init__(self, config: LLMServiceConfig, cache: Optional[SimpleCache] = None):
        super().__init__(config, cache)
        api_key = config.api_key or os.getenv("OPENAI_API_KEY")
        self.client = openai.AsyncOpenAI(api_key=api_key)
    
    async def _perform_query(self, prompt: str, role_prompt: str) -> Dict[str, Any]:
        completion = await self.client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": role_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        
        response_text = completion.choices[0].message.content or ""
        tokens_used = completion.usage.total_tokens if completion.usage else 0
        
        # Safely calculate cost with fallbacks
        try:
            if hasattr(completion.usage, 'prompt_tokens') and hasattr(completion.usage, 'completion_tokens'):
                input_tokens = completion.usage.prompt_tokens
                output_tokens = completion.usage.completion_tokens
                cost = (input_tokens * self.config.cost_per_token.input + 
                       output_tokens * self.config.cost_per_token.output)
            else:
                # Fallback to total tokens if breakdown not available
                cost = tokens_used * self.config.cost_per_token.input
        except (AttributeError, TypeError, ValueError):
            # If cost calculation fails, default to 0
            cost = 0.0
        
        return {
            "response": response_text,
            "tokens_used": tokens_used,
            "cost": cost
        } 