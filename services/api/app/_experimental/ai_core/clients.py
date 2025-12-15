# services/api/app/ai_core/clients.py
"""
AI client abstraction layer.
Placeholder for future AI model integrations.
"""

from __future__ import annotations

from typing import Any, Optional, Protocol


class AiClient(Protocol):
    """Protocol for AI clients."""
    
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


_ai_client: Optional[AiClient] = None


def get_ai_client() -> AiClient:
    """
    Get the configured AI client.
    Returns a stub client if none is configured.
    """
    global _ai_client
    if _ai_client is None:
        _ai_client = StubAiClient()
    return _ai_client


def set_ai_client(client: AiClient) -> None:
    """
    Configure the AI client to use.
    Call this during app startup if using a real AI backend.
    """
    global _ai_client
    _ai_client = client
