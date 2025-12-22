"""
AI Provider Base Protocols

Defines the contracts that all AI providers must implement.
These protocols ensure consistent interfaces across OpenAI, Anthropic, Local, etc.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable
from enum import Enum


class AIProvider(str, Enum):
    """Enumeration of supported AI providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"
    STUB = "stub"


@runtime_checkable
class LLMProviderProtocol(Protocol):
    """
    Protocol for LLM providers.

    Any class implementing this protocol can be used for text generation.
    """

    @property
    def provider_name(self) -> str:
        """Return the provider identifier."""
        ...

    @property
    def is_available(self) -> bool:
        """Check if provider is configured and available."""
        ...

    def generate_text(
        self,
        prompt: str,
        *,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Generate text response from prompt."""
        ...

    def generate_json(
        self,
        prompt: str,
        *,
        system_prompt: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate structured JSON response from prompt."""
        ...


@runtime_checkable
class ImageProviderProtocol(Protocol):
    """
    Protocol for Image generation providers.

    Any class implementing this protocol can be used for image generation.
    """

    @property
    def provider_name(self) -> str:
        """Return the provider identifier."""
        ...

    @property
    def is_available(self) -> bool:
        """Check if provider is configured and available."""
        ...

    @property
    def supported_sizes(self) -> List[str]:
        """Return list of supported image sizes."""
        ...

    def generate_image(
        self,
        prompt: str,
        *,
        size: str = "1024x1024",
        quality: str = "standard",
        negative_prompt: Optional[str] = None,
    ) -> bytes:
        """Generate image bytes from prompt."""
        ...


class BaseProvider(ABC):
    """
    Abstract base class for AI providers.

    Provides common functionality for all provider implementations.
    """

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider identifier."""
        pass

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is configured and available."""
        pass

    def __repr__(self) -> str:
        available = "available" if self.is_available else "not configured"
        return f"<{self.__class__.__name__} ({self.provider_name}, {available})>"
