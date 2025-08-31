"""
Core LLM service package.

Public API:
- LLMService: Facade for text generation (free-form and structured JSON).

Existing imports like `from core.llm_service import LLMService` keep working
because this package exposes LLMService at the top level.
"""

from .service import LLMService

__all__ = ["LLMService"]

