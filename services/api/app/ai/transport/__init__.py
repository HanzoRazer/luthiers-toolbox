"""
AI Transport Layer - HTTP/SDK clients for external AI APIs.

This module handles RAW transport only:
- HTTP requests to LLM APIs (OpenAI, Anthropic, Local)
- HTTP requests to Image APIs (DALL-E, Stable Diffusion)
- Authentication, retries, timeouts
- Response parsing

This module does NOT handle:
- Business logic
- Domain-specific parsing (rosette specs, etc.)
- Provider selection policy
- Safety enforcement

Those responsibilities belong in providers/ and safety/.

INVARIANT: This layer may only import from:
- Python stdlib
- httpx/requests (HTTP clients)
- ai.providers (for protocol types)
"""

from .llm_client import (
    LLMClient,
    LLMConfig,
    LLMProvider,
    LLMResponse,
    LLMJsonResponse,
    LLMClientError,
    LLMAuthError,
    LLMTimeoutError,
    LLMRateLimitError,
    get_llm_client,
    set_llm_client,
)

from .image_client import (
    ImageClient,
    ImageConfig,
    ImageProvider,
    ImageResponse,
    ImageClientError,
    get_image_client,
    set_image_client,
)

__all__ = [
    # LLM Client
    "LLMClient",
    "LLMConfig",
    "LLMProvider",
    "LLMResponse",
    "LLMJsonResponse",
    "LLMClientError",
    "LLMAuthError",
    "LLMTimeoutError",
    "LLMRateLimitError",
    "get_llm_client",
    "set_llm_client",
    # Image Client
    "ImageClient",
    "ImageConfig",
    "ImageProvider",
    "ImageResponse",
    "ImageClientError",
    "get_image_client",
    "set_image_client",
]
