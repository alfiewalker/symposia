"""
Google Gemini service implementation.
"""

import os
from typing import Dict, Any, Optional

import google.generativeai as genai

from .base import LLMService
from ...config.models import LLMServiceConfig
from ...utils.cache import SimpleCache


class GeminiService(LLMService):
    """Google Gemini service implementation."""
    
    def __init__(self, config: LLMServiceConfig, cache: Optional[SimpleCache] = None):
        super().__init__(config, cache)
        api_key = config.api_key or os.getenv("GOOGLE_API_KEY")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(config.model)
    
    async def _perform_query(self, prompt: str, role_prompt: str) -> Dict[str, Any]:
        full_prompt = f"Role: {role_prompt}\n\nTask: {prompt}"
        response = await self.model.generate_content_async(full_prompt)
        
        response_text = response.text
        
        # Safely get token count and calculate cost with fallbacks
        try:
            token_count_response = await self.model.count_tokens_async(full_prompt + response_text)
            tokens_used = token_count_response.total_tokens
            
            # For Gemini, we don't have input/output breakdown, so use input cost for all tokens
            cost = tokens_used * self.config.cost_per_token.input
        except (AttributeError, TypeError, ValueError, Exception):
            # If token counting fails, default to 0
            tokens_used = 0
            cost = 0.0
        
        return {
            "response": response_text,
            "tokens_used": tokens_used,
            "cost": cost
        } 