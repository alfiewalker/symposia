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
        
        # Initialize model - try with system instruction support first
        try:
            self.model = genai.GenerativeModel(
                model_name=config.model,
                # Note: system_instruction would be set per query since it varies
            )
        except Exception:
            # Fallback to basic model initialization
            self.model = genai.GenerativeModel(config.model)
    
    async def _perform_query(self, prompt: str, role_prompt: str) -> Dict[str, Any]:
        # Use system instruction if available, otherwise prepend to content
        try:
            # Try to use system instruction (newer Gemini API feature)
            if hasattr(self.model, '_system_instruction'):
                response = await self.model.generate_content_async(
                    prompt,
                    generation_config={"temperature": 0.7}
                )
            else:
                # Fallback to concatenated prompt
                full_prompt = f"Role: {role_prompt}\n\nTask: {prompt}"
                response = await self.model.generate_content_async(full_prompt)
        except Exception:
            # Final fallback to concatenated prompt
            full_prompt = f"Role: {role_prompt}\n\nTask: {prompt}"
            response = await self.model.generate_content_async(full_prompt)
        
        response_text = response.text if response.text else ""
        
        # Safely get token count and calculate cost with fallbacks
        try:
            # Count tokens for input prompt only
            input_tokens = 0
            output_tokens = 0
            
            # Try to get usage metadata from response
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                input_tokens = getattr(response.usage_metadata, 'prompt_token_count', 0)
                output_tokens = getattr(response.usage_metadata, 'candidates_token_count', 0)
                tokens_used = input_tokens + output_tokens
                
                # Calculate cost with proper input/output breakdown
                cost = (input_tokens * self.config.cost_per_token.input + 
                       output_tokens * self.config.cost_per_token.output)
            else:
                # No usage metadata available - default to 0 for safety
                tokens_used = 0
                cost = 0.0
                
        except (AttributeError, TypeError, ValueError, Exception):
            # If token counting fails, default to 0
            tokens_used = 0
            cost = 0.0
        
        return {
            "response": response_text,
            "tokens_used": tokens_used,
            "cost": cost
        } 