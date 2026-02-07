"""
AI Platform Vision Client - Image Analysis Transport Layer

This module provides HTTP transport for Vision/Image Analysis APIs.
Handles GPT-4o Vision for image understanding and structured extraction.

DATE: January 2026

INVARIANTS:
- This module must NOT import from domain modules (Vision, Art Studio, etc.)
- All external vision analysis API calls go through this layer
- Provider-specific config lives in ai.providers.*

Usage:
    from app.ai.transport import get_vision_client

    client = get_vision_client(provider="openai")
    response = client.analyze(
        image_bytes=image_data,
        prompt="Extract the guitar body outline as polygon coordinates",
        response_format="json"
    )
    result = response.content  # Parsed JSON or text
"""
from __future__ import annotations

import os
import base64
import json
import time
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Literal, Tuple, Union
from enum import Enum

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class VisionClientError(Exception):
    """Base exception for vision client errors."""
    pass


class VisionAuthError(VisionClientError):
    """Authentication failed."""
    pass


class VisionTimeoutError(VisionClientError):
    """Request timed out."""
    pass


class VisionAnalysisError(VisionClientError):
    """Image analysis failed."""
    pass


class VisionParseError(VisionClientError):
    """Failed to parse response as expected format."""
    pass


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

class VisionProvider(str, Enum):
    """Supported vision analysis providers."""
    OPENAI = "openai"       # GPT-4o, GPT-4 Vision
    STUB = "stub"           # Testing


@dataclass
class VisionConfig:
    """Configuration for vision client."""
    provider: VisionProvider = VisionProvider.STUB
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    timeout_seconds: int = 60
    max_retries: int = 2
    retry_delay_seconds: float = 1.0
    default_model: Optional[str] = None
    max_tokens: int = 4096

    def __post_init__(self):
        # Load from environment if not provided
        if self.api_key is None and self.provider == VisionProvider.OPENAI:
            self.api_key = os.environ.get("OPENAI_API_KEY")

        if self.default_model is None:
            if self.provider == VisionProvider.OPENAI:
                self.default_model = "gpt-4o"


# ---------------------------------------------------------------------------
# Response types
# ---------------------------------------------------------------------------

@dataclass
class VisionResponse:
    """Response from vision analysis."""
    content: Union[str, Dict[str, Any], List[Any]]  # Text or parsed JSON
    raw_response: str                                # Original response text
    model: str                                       # Model used
    provider: str                                    # Provider name
    usage: Dict[str, int] = field(default_factory=dict)  # Token usage

    @property
    def as_json(self) -> Dict[str, Any]:
        """Return content as JSON dict."""
        if isinstance(self.content, dict):
            return self.content
        if isinstance(self.content, str):
            try:
                return json.loads(self.content)
            except json.JSONDecodeError:
                raise VisionParseError(f"Cannot parse response as JSON: {self.content[:200]}")
        return {"data": self.content}


# ---------------------------------------------------------------------------
# Abstract Base Client
# ---------------------------------------------------------------------------

class VisionClient(ABC):
    """Abstract base class for vision analysis clients."""

    @abstractmethod
    def analyze(
        self,
        image_bytes: bytes,
        prompt: str,
        *,
        model: Optional[str] = None,
        response_format: Literal["json", "text"] = "text",
        detail: Literal["low", "high", "auto"] = "auto",
    ) -> VisionResponse:
        """
        Analyze an image with a text prompt.

        Args:
            image_bytes: Raw image bytes (PNG, JPG, WebP, GIF)
            prompt: Text prompt describing what to extract/analyze
            model: Model to use (provider-specific)
            response_format: Expected response format
            detail: Image detail level (affects token usage)

        Returns:
            VisionResponse with analysis result
        """
        pass

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        """Check if client is properly configured."""
        pass


# ---------------------------------------------------------------------------
# OpenAI Vision Client (GPT-4o)
# ---------------------------------------------------------------------------

class OpenAIVisionClient(VisionClient):
    """
    OpenAI GPT-4o Vision client.

    Uses the chat completions API with image content blocks.
    """

    def __init__(self, config: Optional[VisionConfig] = None):
        self.config = config or VisionConfig(provider=VisionProvider.OPENAI)
        self._validate_config()

    def _validate_config(self):
        if self.config.provider != VisionProvider.OPENAI:
            raise VisionClientError(f"OpenAIVisionClient requires OPENAI provider, got {self.config.provider}")

    @property
    def is_configured(self) -> bool:
        return bool(self.config.api_key)

    def _encode_image(self, image_bytes: bytes) -> Tuple[str, str]:
        """Encode image to base64 data URL."""
        # Detect image type from magic bytes
        if image_bytes[:8] == b'\x89PNG\r\n\x1a\n':
            mime_type = "image/png"
        elif image_bytes[:2] == b'\xff\xd8':
            mime_type = "image/jpeg"
        elif image_bytes[:4] == b'RIFF' and image_bytes[8:12] == b'WEBP':
            mime_type = "image/webp"
        elif image_bytes[:6] in (b'GIF87a', b'GIF89a'):
            mime_type = "image/gif"
        else:
            mime_type = "image/png"  # Default

        b64 = base64.b64encode(image_bytes).decode("utf-8")
        data_url = f"data:{mime_type};base64,{b64}"
        return data_url, mime_type

    def analyze(
        self,
        image_bytes: bytes,
        prompt: str,
        *,
        model: Optional[str] = None,
        response_format: Literal["json", "text"] = "text",
        detail: Literal["low", "high", "auto"] = "auto",
    ) -> VisionResponse:
        """Analyze image using GPT-4o Vision."""
        import httpx

        if not self.is_configured:
            raise VisionAuthError("OpenAI API key not configured")

        model = model or self.config.default_model or "gpt-4o"
        data_url, mime_type = self._encode_image(image_bytes)

        # Build messages with image content
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": data_url,
                            "detail": detail,
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt,
                    }
                ]
            }
        ]

        # Build request payload
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": self.config.max_tokens,
        }

        # Request JSON response format if needed
        if response_format == "json":
            payload["response_format"] = {"type": "json_object"}
            # Ensure prompt mentions JSON
            if "json" not in prompt.lower():
                messages[0]["content"][1]["text"] = prompt + "\n\nRespond with valid JSON."

        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

        url = "https://api.openai.com/v1/chat/completions"

        # Retry loop
        last_error = None
        for attempt in range(self.config.max_retries + 1):
            try:
                with httpx.Client(timeout=self.config.timeout_seconds) as client:
                    response = client.post(url, json=payload, headers=headers)

                if response.status_code == 401:
                    raise VisionAuthError("OpenAI API authentication failed")
                if response.status_code == 429:
                    if attempt < self.config.max_retries:
                        time.sleep(self.config.retry_delay_seconds * (2 ** attempt))
                        continue
                    raise VisionClientError("Rate limit exceeded")
                if response.status_code >= 500:
                    if attempt < self.config.max_retries:
                        time.sleep(self.config.retry_delay_seconds)
                        continue
                    raise VisionClientError(f"OpenAI server error: {response.status_code}")

                response.raise_for_status()
                data = response.json()

                # Extract response content
                raw_content = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})

                # Parse JSON if expected
                if response_format == "json":
                    try:
                        content = json.loads(raw_content)
                    except json.JSONDecodeError as e:
                        # Try to extract JSON from markdown code block
                        if "```json" in raw_content:
                            json_str = raw_content.split("```json")[1].split("```")[0].strip()
                            content = json.loads(json_str)
                        elif "```" in raw_content:
                            json_str = raw_content.split("```")[1].split("```")[0].strip()
                            content = json.loads(json_str)
                        else:
                            raise VisionParseError(f"Failed to parse JSON response: {e}")
                else:
                    content = raw_content

                return VisionResponse(
                    content=content,
                    raw_response=raw_content,
                    model=data.get("model", model),
                    provider="openai",
                    usage={
                        "prompt_tokens": usage.get("prompt_tokens", 0),
                        "completion_tokens": usage.get("completion_tokens", 0),
                        "total_tokens": usage.get("total_tokens", 0),
                    }
                )

            except httpx.TimeoutException as e:
                last_error = VisionTimeoutError(f"Request timed out: {e}")
                if attempt < self.config.max_retries:
                    time.sleep(self.config.retry_delay_seconds)
                    continue
            except httpx.HTTPStatusError as e:
                last_error = VisionClientError(f"HTTP error: {e}")
                if attempt < self.config.max_retries:
                    time.sleep(self.config.retry_delay_seconds)
                    continue
            except Exception as e:  # WP-1: keep broad — AI API retry loop catch-all
                if isinstance(e, (VisionAuthError, VisionParseError)):
                    raise
                last_error = VisionAnalysisError(f"Analysis failed: {e}")
                if attempt < self.config.max_retries:
                    time.sleep(self.config.retry_delay_seconds)
                    continue

        raise last_error or VisionAnalysisError("Unknown error during analysis")


# ---------------------------------------------------------------------------
# Stub Client (for testing)
# ---------------------------------------------------------------------------

class StubVisionClient(VisionClient):
    """
    Stub vision client for testing.

    Returns predefined responses without making API calls.
    """

    def __init__(self, config: Optional[VisionConfig] = None):
        self.config = config or VisionConfig(provider=VisionProvider.STUB)
        self.call_count = 0
        self.last_prompt = None
        self.last_image_size = 0
        # Configurable stub response
        self._stub_response: Dict[str, Any] = {
            "body_outline": [
                [100, 50], [150, 80], [180, 150], [190, 250],
                [180, 350], [150, 420], [100, 450], [50, 420],
                [20, 350], [10, 250], [20, 150], [50, 80], [100, 50]
            ],
            "confidence": 0.92,
            "guitar_type": "les_paul",
            "notes": "Stub response - clear guitar body detected"
        }

    @property
    def is_configured(self) -> bool:
        return True

    def set_stub_response(self, response: Dict[str, Any]):
        """Configure the stub response for testing."""
        self._stub_response = response

    def analyze(
        self,
        image_bytes: bytes,
        prompt: str,
        *,
        model: Optional[str] = None,
        response_format: Literal["json", "text"] = "text",
        detail: Literal["low", "high", "auto"] = "auto",
    ) -> VisionResponse:
        """Return stub response."""
        self.call_count += 1
        self.last_prompt = prompt
        self.last_image_size = len(image_bytes)

        if response_format == "json":
            content = self._stub_response
            raw_response = json.dumps(self._stub_response)
        else:
            content = json.dumps(self._stub_response, indent=2)
            raw_response = content

        return VisionResponse(
            content=content,
            raw_response=raw_response,
            model=model or "stub-vision-1.0",
            provider="stub",
            usage={
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150,
            }
        )


# ---------------------------------------------------------------------------
# Factory Functions
# ---------------------------------------------------------------------------

# Global client instance (can be overridden for testing)
_vision_client: Optional[VisionClient] = None


def get_vision_client(provider: str = "openai") -> VisionClient:
    """
    Get a vision analysis client.

    Args:
        provider: Provider name ("openai" or "stub")

    Returns:
        Configured VisionClient instance
    """
    global _vision_client

    if _vision_client is not None:
        return _vision_client

    provider_enum = VisionProvider(provider.lower())

    if provider_enum == VisionProvider.OPENAI:
        return OpenAIVisionClient(VisionConfig(provider=provider_enum))
    elif provider_enum == VisionProvider.STUB:
        return StubVisionClient(VisionConfig(provider=provider_enum))
    else:
        raise VisionClientError(f"Unknown vision provider: {provider}")


def set_vision_client(client: Optional[VisionClient]):
    """
    Set the global vision client (for testing).

    Args:
        client: VisionClient instance or None to reset
    """
    global _vision_client
    _vision_client = client
