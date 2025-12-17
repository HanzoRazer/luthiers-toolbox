"""
AI Graphics Services

Provides:
- ai_parameter_suggester: Main suggestion generation with RMOS feedback
- providers: High-level provider interface (AiProvider protocol, StubProvider, OpenAIProvider)
- llm_client: Low-level transport layer (HTTP calls, auth, retries)

Architecture:
    ai_parameter_suggester → providers → llm_client
                             (one-way dependency chain)
"""

from .ai_parameter_suggester import suggest_rosette_parameters
from .providers import (
    AiProvider,
    StubProvider,
    OpenAIProvider,
    LocalUploadProvider,
    get_provider,
    set_provider,
    generate_rosette_param_candidates,
)

__all__ = [
    "suggest_rosette_parameters",
    "AiProvider",
    "StubProvider",
    "OpenAIProvider",
    "LocalUploadProvider",
    "get_provider",
    "set_provider",
    "generate_rosette_param_candidates",
]
