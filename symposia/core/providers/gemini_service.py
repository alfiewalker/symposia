"""
Google Gemini service implementation.
"""

import asyncio
import os
from typing import Dict, Any, Optional

from google import genai as google_genai
from google.genai import types as google_genai_types

from .base import LLMService
from ...config.models import LLMServiceConfig
from ...utils.cache import SimpleCache


class GeminiService(LLMService):
    """Google Gemini service implementation."""
    
    def __init__(self, config: LLMServiceConfig, cache: Optional[SimpleCache] = None):
        super().__init__(config, cache)
        api_key = config.api_key or os.getenv("GOOGLE_API_KEY")
        self.client = google_genai.Client(api_key=api_key)
    
    async def _perform_query(self, prompt: str, role_prompt: str) -> Dict[str, Any]:
        response = await self._generate(prompt=prompt, role_prompt=role_prompt)
        response_text = getattr(response, "text", "") or ""

        input_tokens = 0
        output_tokens = 0
        usage = getattr(response, "usage_metadata", None)
        if usage is not None:
            input_tokens = int(
                getattr(usage, "prompt_token_count", 0)
                or getattr(usage, "input_token_count", 0)
                or 0
            )
            output_tokens = int(
                getattr(usage, "candidates_token_count", 0)
                or getattr(usage, "output_token_count", 0)
                or 0
            )
        tokens_used = input_tokens + output_tokens
        cost = (
            input_tokens * self.config.cost_per_token.input
            + output_tokens * self.config.cost_per_token.output
        )
        
        return {
            "response": response_text,
            "tokens_used": tokens_used,
            "cost": cost
        }

    async def _generate(self, *, prompt: str, role_prompt: str):
        def _sync_generate():
            config = google_genai_types.GenerateContentConfig(
                system_instruction=role_prompt,
                temperature=0.7,
            )
            return self.client.models.generate_content(
                model=self.config.model,
                contents=prompt,
                config=config,
            )

        return await asyncio.to_thread(_sync_generate)