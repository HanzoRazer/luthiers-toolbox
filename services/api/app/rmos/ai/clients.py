"""
RMOS AI Client Helpers (Canonical)

Legacy adapter over app.ai.transport for RMOS-specific needs.

NOTE: This module exists for backwards compatibility with RMOS code that
calls get_ai_client(). New code should use app.ai.transport.get_llm_client() directly.

Migrated from: _experimental/ai_core/clients.py (December 2025)
"""

from __future__ import annotations

from typing import Any, Optional, Protocol

# Platform transport
from app.ai.transport import get_llm_client, LLMClient


class AiClient(Protocol):
    """Protocol for AI clients (legacy interface)."""

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate text from a prompt."""
        ...


class StubAiClient:
    """
    Stub AI client that returns empty responses.
    Used when no real AI backend is configured.
    """

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Return empty string (stub behavior)."""
        return ""


class LLMClientAdapter:
    """
    Adapts new app.ai.transport.LLMClient to legacy AiClient protocol.
    """

    def __init__(self, llm_client: LLMClient):
        self._client = llm_client

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate text using LLM client."""
        try:
            response = self._client.request_text(
                prompt=prompt,
                model=kwargs.get("model"),
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 2048),
            )
            return response.content
        except Exception:  # WP-1: keep broad — external LLM API can raise arbitrary errors
            return ""


_ai_client: Optional[AiClient] = None


def get_ai_client() -> AiClient:
    """
    Get the configured AI client.
    
    Returns adapter over app.ai.transport.get_llm_client() if available,
    otherwise returns stub client.
    
    DEPRECATED: New code should use app.ai.transport.get_llm_client() directly.
    """
    global _ai_client
    if _ai_client is None:
        try:
            llm = get_llm_client()
            if getattr(llm, "is_configured", False):
                _ai_client = LLMClientAdapter(llm)
            else:
                _ai_client = StubAiClient()
        except (ImportError, AttributeError):  # WP-1: narrowed from except Exception
            _ai_client = StubAiClient()
    return _ai_client


def set_ai_client(client: AiClient) -> None:
    """
    Configure the AI client to use.
    
    DEPRECATED: This is legacy API. Configure LLM client via
    app.ai.transport.set_llm_client() instead.
    """
    global _ai_client
    _ai_client = client


__all__ = [
    "AiClient",
    "StubAiClient",
    "get_ai_client",
    "set_ai_client",
]
