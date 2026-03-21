"""
Core domain logic for the Symposia framework.
"""

from .llm_service import LLMService
from .member import CommitteeMember
from .reputation import ReputationManager
from .result import DeliberationResult
from .committee import Committee


def __getattr__(name: str):
    if name in {"OpenAIService", "ClaudeService", "GeminiService"}:
        from . import llm_service as _llm_service

        return getattr(_llm_service, name)
    raise AttributeError(name)

__all__ = [
    "LLMService",
    "OpenAIService",
    "ClaudeService",
    "GeminiService",
    "CommitteeMember",
    "ReputationManager",
    "DeliberationResult",
    "Committee",
] 