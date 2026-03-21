"""
LLM service implementations for different providers.
"""

from .providers.base import LLMService


def __getattr__(name: str):
    if name == "OpenAIService":
        from .providers.openai_service import OpenAIService

        return OpenAIService
    if name == "ClaudeService":
        from .providers.claude_service import ClaudeService

        return ClaudeService
    if name == "GeminiService":
        from .providers.gemini_service import GeminiService

        return GeminiService
    raise AttributeError(name)


__all__ = ["LLMService", "OpenAIService", "ClaudeService", "GeminiService"]