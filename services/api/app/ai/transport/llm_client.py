"""
AI Platform LLM Client - Canonical Transport Layer

This module provides HTTP transport for LLM API calls.
It handles authentication, retries, timeouts, and raw request/response.

Canonical LLM transport client.
DATE: December 2025

INVARIANTS:
- This module must NOT import from domain modules (Vision, RMOS, etc.)
- All external API calls go through this layer
- Provider-specific logic lives in ai.providers.*

Usage:
    from app.ai.transport import get_llm_client

    client = get_llm_client()
    response = client.request_json(prompt="Generate rosette parameters...")
"""
from __future__ import annotations

import os
import json
import time
import logging
import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Literal
from enum import Enum

logger = logging.getLogger(__name__)


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
    def __init__(self, message: str, retry_after: Optional[float] = None):
        super().__init__(message)
        self.retry_after = retry_after


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
    timeout_seconds: float = 60.0
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    default_model: Optional[str] = None

    def __post_init__(self):
        # Load API key from environment if not provided
        if self.api_key is None:
            if self.provider == LLMProvider.OPENAI:
                self.api_key = os.environ.get("OPENAI_API_KEY")
            elif self.provider == LLMProvider.ANTHROPIC:
                self.api_key = os.environ.get("ANTHROPIC_API_KEY")

        # Set default base URLs
        if self.base_url is None:
            if self.provider == LLMProvider.OPENAI:
                self.base_url = "https://api.openai.com/v1"
            elif self.provider == LLMProvider.ANTHROPIC:
                self.base_url = "https://api.anthropic.com/v1"
            elif self.provider == LLMProvider.LOCAL:
                self.base_url = os.environ.get("OLLAMA_URL", "http://localhost:11434/api")

        # Set default models
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
    provider: str
    usage: Dict[str, int] = field(default_factory=dict)
    finish_reason: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None
    request_hash: Optional[str] = None  # For audit/dedup

    @property
    def prompt_tokens(self) -> int:
        return self.usage.get("prompt_tokens", 0)

    @property
    def completion_tokens(self) -> int:
        return self.usage.get("completion_tokens", 0)

    @property
    def total_tokens(self) -> int:
        return self.usage.get("total_tokens", self.prompt_tokens + self.completion_tokens)


@dataclass
class LLMJsonResponse:
    """Parsed JSON response from LLM API."""
    data: Dict[str, Any]
    model: str
    provider: str
    usage: Dict[str, int] = field(default_factory=dict)
    raw_response: Optional[Dict[str, Any]] = None
    request_hash: Optional[str] = None


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
    - Domain-specific output parsing
    - Provider selection logic
    - Business logic
    """

    def __init__(self, config: Optional[LLMConfig] = None):
        if config is None:
            config = LLMConfig()
        self.config = config
        self._http_client = None  # Lazy-loaded

    @property
    def is_configured(self) -> bool:
        """Check if client has required configuration."""
        if self.config.provider == LLMProvider.LOCAL:
            return bool(self.config.base_url)
        return bool(self.config.api_key)

    def _get_http_client(self):
        """Lazy initialization of HTTP client."""
        if self._http_client is None:
            try:
                import httpx
                self._http_client = httpx.Client(timeout=self.config.timeout_seconds)
            except ImportError:
                # Fallback to requests
                import requests
                self._http_client = requests.Session()
        return self._http_client

    def _get_headers(self) -> Dict[str, str]:
        """Build authentication headers for API request."""
        headers = {"Content-Type": "application/json"}

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
            return {
                "model": model,
                "prompt": prompt,
                "stream": False,
            }

        raise LLMClientError(f"Unsupported provider: {self.config.provider}")

    def _get_endpoint(self) -> str:
        """Get the API endpoint URL."""
        if self.config.provider == LLMProvider.OPENAI:
            return f"{self.config.base_url}/chat/completions"
        elif self.config.provider == LLMProvider.ANTHROPIC:
            return f"{self.config.base_url}/messages"
        elif self.config.provider == LLMProvider.LOCAL:
            return f"{self.config.base_url}/generate"
        raise LLMClientError(f"Unsupported provider: {self.config.provider}")

    def _parse_response(self, raw: Dict[str, Any]) -> LLMResponse:
        """Parse raw API response into LLMResponse."""
        if self.config.provider == LLMProvider.OPENAI:
            choice = raw.get("choices", [{}])[0]
            return LLMResponse(
                content=choice.get("message", {}).get("content", ""),
                model=raw.get("model", ""),
                provider="openai",
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
                provider="anthropic",
                usage=raw.get("usage", {}),
                finish_reason=raw.get("stop_reason"),
                raw_response=raw,
            )

        elif self.config.provider == LLMProvider.LOCAL:
            return LLMResponse(
                content=raw.get("response", ""),
                model=raw.get("model", ""),
                provider="local",
                usage={},
                finish_reason=raw.get("done_reason"),
                raw_response=raw,
            )

        raise LLMClientError(f"Unsupported provider: {self.config.provider}")

    def _compute_request_hash(self, prompt: str, model: str) -> str:
        """Compute hash for request deduplication/audit."""
        content = f"{self.config.provider}:{model}:{prompt}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

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
        if not self.is_configured:
            raise LLMAuthError(f"API key not configured for {self.config.provider}")

        model = model or self.config.default_model
        request_hash = self._compute_request_hash(prompt, model)

        endpoint = self._get_endpoint()
        headers = self._get_headers()
        body = self._build_request_body(
            prompt,
            model=model,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                client = self._get_http_client()

                # Handle both httpx and requests
                if hasattr(client, 'post'):
                    response = client.post(endpoint, headers=headers, json=body)
                else:
                    import requests
                    response = requests.post(
                        endpoint,
                        headers=headers,
                        json=body,
                        timeout=self.config.timeout_seconds
                    )

                if response.status_code == 401:
                    raise LLMAuthError("Invalid API key")
                elif response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    raise LLMRateLimitError(
                        "Rate limit exceeded",
                        retry_after=float(retry_after) if retry_after else None
                    )
                elif response.status_code >= 400:
                    raise LLMClientError(f"API error {response.status_code}: {response.text}")

                raw = response.json()
                result = self._parse_response(raw)
                result.request_hash = request_hash

                logger.debug(f"LLM request completed: {model}, {result.total_tokens} tokens")
                return result

            except LLMAuthError:
                raise
            except LLMRateLimitError as e:
                if e.retry_after and attempt < self.config.max_retries - 1:
                    time.sleep(e.retry_after)
                    continue
                raise
            except Exception as e:  # WP-1: keep broad — AI API retry loop
                last_error = e
                if attempt < self.config.max_retries - 1:
                    delay = self.config.retry_delay_seconds * (2 ** attempt)
                    logger.warning(f"LLM attempt {attempt + 1} failed: {e}, retrying in {delay}s")
                    time.sleep(delay)

        raise LLMClientError(f"Request failed after {self.config.max_retries} attempts: {last_error}")

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

        Args:
            prompt: User prompt text (should request JSON output)
            model: Model identifier
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response

        Returns:
            LLMJsonResponse with parsed JSON data

        Raises:
            LLMResponseError: Response is not valid JSON
        """
        # Add JSON instruction to system prompt
        json_system = (system_prompt or "") + "\nRespond with valid JSON only."

        response = self.request_text(
            prompt,
            model=model,
            system_prompt=json_system.strip(),
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Parse JSON from response
        content = response.content.strip()

        # Handle markdown code blocks
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise LLMResponseError(f"Invalid JSON response: {e}\nContent: {content[:500]}")

        return LLMJsonResponse(
            data=data,
            model=response.model,
            provider=response.provider,
            usage=response.usage,
            raw_response=response.raw_response,
            request_hash=response.request_hash,
        )

    def health_check(self) -> bool:
        """Check if the LLM service is reachable."""
        if not self.is_configured:
            return False
        try:
            # Simple models list request for OpenAI
            if self.config.provider == LLMProvider.OPENAI:
                client = self._get_http_client()
                headers = self._get_headers()
                response = client.get(f"{self.config.base_url}/models", headers=headers)
                return response.status_code == 200
            return True
        except Exception:  # WP-1: keep broad — health probe, any failure = unhealthy
            return False


# ---------------------------------------------------------------------------
# Module-level convenience functions
# ---------------------------------------------------------------------------

_default_client: Optional[LLMClient] = None


def get_llm_client(provider: str = "openai") -> LLMClient:
    """
    Get an LLM client instance.

    Args:
        provider: "openai", "anthropic", or "local"

    Returns:
        Configured LLMClient instance
    """
    global _default_client

    provider_enum = LLMProvider(provider.lower())

    if _default_client is None or _default_client.config.provider != provider_enum:
        _default_client = LLMClient(LLMConfig(provider=provider_enum))

    return _default_client


def set_llm_client(client: LLMClient) -> None:
    """Set the default LLM client instance (for testing)."""
    global _default_client
    _default_client = client
