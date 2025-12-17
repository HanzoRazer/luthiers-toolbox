"""
AI Graphics LLM Client - Low-Level Transport Layer

This module provides HTTP transport for LLM API calls.
It handles authentication, retries, timeouts, and raw request/response.

IMPORTANT: This module must NOT import from providers.py.
providers.py imports this module - one-way dependency only.

Usage:
    client = LLMClient(api_key="sk-...", provider="openai")
    response = client.request_json(prompt="...", model="gpt-4")
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Literal
from enum import Enum


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class LLMClientError(Exception):
    """Base exception for LLM client errors."""
    pass


class LLMAuthError(LLMClientError):
    """Authentication failed (invalid API key, etc.)."""
    pass


class LLMTimeoutError(LLMClientError):
    """Request timed out."""
    pass


class LLMRateLimitError(LLMClientError):
    """Rate limit exceeded."""
    retry_after: Optional[float] = None


class LLMResponseError(LLMClientError):
    """Invalid or unexpected response from LLM API."""
    pass


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

class LLMProvider(str, Enum):
    """Supported LLM API providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"  # Ollama, llama.cpp, etc.


@dataclass
class LLMConfig:
    """Configuration for LLM client."""
    provider: LLMProvider = LLMProvider.OPENAI
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    timeout_seconds: float = 30.0
    max_retries: int = 3
    retry_delay_seconds: float = 1.0

    # Default models per provider
    default_model: Optional[str] = None

    def __post_init__(self):
        # Set defaults based on provider
        if self.base_url is None:
            if self.provider == LLMProvider.OPENAI:
                self.base_url = "https://api.openai.com/v1"
            elif self.provider == LLMProvider.ANTHROPIC:
                self.base_url = "https://api.anthropic.com/v1"
            elif self.provider == LLMProvider.LOCAL:
                self.base_url = "http://localhost:11434/api"  # Ollama default

        if self.default_model is None:
            if self.provider == LLMProvider.OPENAI:
                self.default_model = "gpt-4"
            elif self.provider == LLMProvider.ANTHROPIC:
                self.default_model = "claude-3-sonnet-20240229"
            elif self.provider == LLMProvider.LOCAL:
                self.default_model = "llama2"


# ---------------------------------------------------------------------------
# Response types
# ---------------------------------------------------------------------------

@dataclass
class LLMResponse:
    """Raw response from LLM API."""
    content: str
    model: str
    usage: Dict[str, int] = field(default_factory=dict)
    finish_reason: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None


@dataclass
class LLMJsonResponse:
    """Parsed JSON response from LLM API."""
    data: Dict[str, Any]
    model: str
    usage: Dict[str, int] = field(default_factory=dict)
    raw_response: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------------------
# LLM Client - Transport Layer
# ---------------------------------------------------------------------------

class LLMClient:
    """
    Low-level HTTP client for LLM API calls.

    This class handles:
    - HTTP transport (POST requests)
    - Authentication headers
    - Retries with exponential backoff
    - Timeout handling
    - Raw response parsing

    It does NOT handle:
    - Prompt templates or formatting
    - Domain-specific output parsing (rosette specs, etc.)
    - Provider selection logic
    - Business logic

    Those responsibilities belong in providers.py.
    """

    def __init__(self, config: Optional[LLMConfig] = None):
        """
        Initialize LLM client.

        Args:
            config: LLM configuration. If None, uses environment defaults.
        """
        if config is None:
            config = LLMConfig(
                api_key=os.environ.get("OPENAI_API_KEY"),
            )
        self.config = config
        self._session = None  # Lazy-loaded httpx client

    def _get_headers(self) -> Dict[str, str]:
        """Build authentication headers for API request."""
        headers = {
            "Content-Type": "application/json",
        }

        if self.config.api_key:
            if self.config.provider == LLMProvider.OPENAI:
                headers["Authorization"] = f"Bearer {self.config.api_key}"
            elif self.config.provider == LLMProvider.ANTHROPIC:
                headers["x-api-key"] = self.config.api_key
                headers["anthropic-version"] = "2023-06-01"

        return headers

    def _build_request_body(
        self,
        prompt: str,
        *,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        response_format: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Build request body for LLM API."""
        model = model or self.config.default_model

        if self.config.provider == LLMProvider.OPENAI:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            body: Dict[str, Any] = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if response_format:
                body["response_format"] = response_format
            return body

        elif self.config.provider == LLMProvider.ANTHROPIC:
            body = {
                "model": model,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            }
            if system_prompt:
                body["system"] = system_prompt
            return body

        elif self.config.provider == LLMProvider.LOCAL:
            # Ollama format
            return {
                "model": model,
                "prompt": prompt,
                "stream": False,
            }

        raise LLMClientError(f"Unsupported provider: {self.config.provider}")

    def _parse_response(self, raw: Dict[str, Any]) -> LLMResponse:
        """Parse raw API response into LLMResponse."""
        if self.config.provider == LLMProvider.OPENAI:
            choice = raw.get("choices", [{}])[0]
            return LLMResponse(
                content=choice.get("message", {}).get("content", ""),
                model=raw.get("model", ""),
                usage=raw.get("usage", {}),
                finish_reason=choice.get("finish_reason"),
                raw_response=raw,
            )

        elif self.config.provider == LLMProvider.ANTHROPIC:
            content_blocks = raw.get("content", [])
            text = "".join(
                block.get("text", "")
                for block in content_blocks
                if block.get("type") == "text"
            )
            return LLMResponse(
                content=text,
                model=raw.get("model", ""),
                usage=raw.get("usage", {}),
                finish_reason=raw.get("stop_reason"),
                raw_response=raw,
            )

        elif self.config.provider == LLMProvider.LOCAL:
            return LLMResponse(
                content=raw.get("response", ""),
                model=raw.get("model", ""),
                usage={},
                finish_reason=raw.get("done_reason"),
                raw_response=raw,
            )

        raise LLMClientError(f"Unsupported provider: {self.config.provider}")

    def request_text(
        self,
        prompt: str,
        *,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        """
        Send a text completion request to the LLM API.

        Args:
            prompt: User prompt text
            model: Model identifier (defaults to config.default_model)
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens in response

        Returns:
            LLMResponse with generated text

        Raises:
            LLMAuthError: Invalid API key
            LLMTimeoutError: Request timed out
            LLMRateLimitError: Rate limit exceeded
            LLMClientError: Other API errors
        """
        # For now, return stub response (httpx integration in future)
        # This allows the transport layer to be tested without real API calls
        return LLMResponse(
            content="",
            model=model or self.config.default_model or "",
            usage={"prompt_tokens": 0, "completion_tokens": 0},
            finish_reason="stub",
            raw_response=None,
        )

    def request_json(
        self,
        prompt: str,
        *,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> LLMJsonResponse:
        """
        Send a JSON-mode completion request to the LLM API.

        The response is expected to be valid JSON.

        Args:
            prompt: User prompt text (should request JSON output)
            model: Model identifier (defaults to config.default_model)
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens in response

        Returns:
            LLMJsonResponse with parsed JSON data

        Raises:
            LLMResponseError: Response is not valid JSON
            LLMAuthError: Invalid API key
            LLMTimeoutError: Request timed out
            LLMRateLimitError: Rate limit exceeded
            LLMClientError: Other API errors
        """
        # Stub implementation - returns empty dict
        return LLMJsonResponse(
            data={},
            model=model or self.config.default_model or "",
            usage={"prompt_tokens": 0, "completion_tokens": 0},
            raw_response=None,
        )


# ---------------------------------------------------------------------------
# Module-level convenience functions
# ---------------------------------------------------------------------------

_default_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get the default LLM client instance."""
    global _default_client
    if _default_client is None:
        _default_client = LLMClient()
    return _default_client


def set_llm_client(client: LLMClient) -> None:
    """Set the default LLM client instance."""
    global _default_client
    _default_client = client
