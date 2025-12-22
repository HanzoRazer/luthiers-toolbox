"""
AI Providers - High-Level Provider Interfaces

This module defines protocols and implementations for AI providers.
Transport layer (ai.transport) handles raw HTTP; this layer handles:
- Provider selection logic
- Response normalization
- Domain-specific output parsing

INVARIANT: Only this module may directly reference external AI SDKs (openai, anthropic).
"""

from .base import (
    AIProvider,
    LLMProviderProtocol,
    ImageProviderProtocol,
)

__all__ = [
    "AIProvider",
    "LLMProviderProtocol",
    "ImageProviderProtocol",
]
