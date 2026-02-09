"""AI Platform Image Client - Canonical Transport Layer"""
from __future__ import annotations

import os
import base64
import time
import logging
import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class ImageClientError(Exception):
    """Base exception for image client errors."""
    pass


class ImageAuthError(ImageClientError):
    """Authentication failed."""
    pass


class ImageTimeoutError(ImageClientError):
    """Request timed out."""
    pass


class ImageGenerationError(ImageClientError):
    """Image generation failed."""
    pass


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

class ImageProvider(str, Enum):
    """Supported image generation providers."""
    OPENAI = "openai"           # DALL-E
    STABLE_DIFFUSION = "sd"     # Automatic1111, ComfyUI
    STUB = "stub"               # Testing


@dataclass
class ImageConfig:
    """Configuration for image client."""
    provider: ImageProvider = ImageProvider.STUB
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    timeout_seconds: int = 120
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    default_model: Optional[str] = None

    def __post_init__(self):
        # Load from environment if not provided
        if self.api_key is None and self.provider == ImageProvider.OPENAI:
            self.api_key = os.environ.get("OPENAI_API_KEY")

        if self.base_url is None:
            if self.provider == ImageProvider.STABLE_DIFFUSION:
                self.base_url = os.environ.get("SD_API_URL", "http://localhost:7860")

        if self.default_model is None:
            if self.provider == ImageProvider.OPENAI:
                self.default_model = "dall-e-3"
            elif self.provider == ImageProvider.STABLE_DIFFUSION:
                self.default_model = "sd_xl_base_1.0"


# ---------------------------------------------------------------------------
# Response types
# ---------------------------------------------------------------------------

@dataclass
class ImageResponse:
    """Response from image generation."""
    image_bytes: bytes
    format: str  # "png", "jpg", "webp"
    provider: str
    model: str
    size: str
    revised_prompt: Optional[str] = None
    seed: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    request_hash: Optional[str] = None  # For audit/dedup

    @property
    def size_bytes(self) -> int:
        return len(self.image_bytes)

    @property
    def sha256(self) -> str:
        """Content hash for deduplication."""
        return hashlib.sha256(self.image_bytes).hexdigest()


# ---------------------------------------------------------------------------
# Abstract Image Client
# ---------------------------------------------------------------------------

class ImageClient(ABC):
    """Abstract base for image generation clients."""

    def __init__(self, config: Optional[ImageConfig] = None):
        self.config = config or ImageConfig()

    @abstractmethod
    def generate(
        self,
        prompt: str,
        *,
        size: str = "1024x1024",
        quality: str = "standard",
        model: Optional[str] = None,
        negative_prompt: Optional[str] = None,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> ImageResponse:
        """Generate image from prompt."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Check if service is reachable."""
        pass

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        """Check if client has required configuration."""
        pass

    def _compute_request_hash(self, prompt: str, model: str, size: str) -> str:
        """Compute hash for request deduplication/audit."""
        content = f"{self.config.provider}:{model}:{size}:{prompt}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# OpenAI / DALL-E Client
# ---------------------------------------------------------------------------

class OpenAIImageClient(ImageClient):
    """
    Image client for OpenAI DALL-E API.
    """

    def __init__(self, config: Optional[ImageConfig] = None):
        if config is None:
            config = ImageConfig(provider=ImageProvider.OPENAI)
        super().__init__(config)
        self._client = None

    @property
    def is_configured(self) -> bool:
        return bool(self.config.api_key)

    def _get_client(self):
        """Lazy initialization of OpenAI client."""
        if self._client is None:
            try:
                import openai
                self._client = openai.OpenAI(api_key=self.config.api_key)
            except ImportError:
                raise ImageClientError("openai package not installed: pip install openai")
        return self._client

    def health_check(self) -> bool:
        if not self.is_configured:
            return False
        try:
            client = self._get_client()
            client.models.list()
            return True
        except Exception:  # WP-1: keep broad — health probe, any failure = unhealthy
            return False

    def _map_size(self, size: str) -> str:
        """Map size string to DALL-E supported sizes."""
        # DALL-E 3: 1024x1024, 1792x1024, 1024x1792
        if "x" in size:
            w, h = map(int, size.split("x"))
            if w == h:
                return "1024x1024"
            elif w > h:
                return "1792x1024"
            else:
                return "1024x1792"
        return "1024x1024"

    def generate(
        self,
        prompt: str,
        *,
        size: str = "1024x1024",
        quality: str = "standard",
        model: Optional[str] = None,
        negative_prompt: Optional[str] = None,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> ImageResponse:
        """Generate image via DALL-E."""
        if not self.is_configured:
            raise ImageAuthError("OPENAI_API_KEY not configured")

        model = model or self.config.default_model or "dall-e-3"
        dalle_size = self._map_size(size)
        dalle_quality = "hd" if quality in ("hd", "ultra") else "standard"
        request_hash = self._compute_request_hash(prompt, model, dalle_size)

        client = self._get_client()

        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                response = client.images.generate(
                    model=model,
                    prompt=prompt,
                    size=dalle_size,
                    quality=dalle_quality,
                    response_format="b64_json",
                    n=1,
                )

                b64_data = response.data[0].b64_json
                image_bytes = base64.b64decode(b64_data)

                return ImageResponse(
                    image_bytes=image_bytes,
                    format="png",
                    provider="openai",
                    model=model,
                    size=dalle_size,
                    revised_prompt=response.data[0].revised_prompt,
                    metadata={
                        "quality": dalle_quality,
                        "original_size": size,
                    },
                    request_hash=request_hash,
                )

            except Exception as e:  # WP-1: keep broad — AI API retry loop
                last_error = e
                if attempt < self.config.max_retries - 1:
                    logger.warning(f"DALL-E attempt {attempt + 1} failed: {e}")
                    time.sleep(self.config.retry_delay_seconds * (2 ** attempt))

        raise ImageGenerationError(
            f"DALL-E generation failed after {self.config.max_retries} attempts: {last_error}"
        )


# ---------------------------------------------------------------------------
# Stable Diffusion Client
# ---------------------------------------------------------------------------

class StableDiffusionClient(ImageClient):
    """
    Image client for Stable Diffusion APIs (Automatic1111, ComfyUI).
    """

    def __init__(self, config: Optional[ImageConfig] = None):
        if config is None:
            config = ImageConfig(provider=ImageProvider.STABLE_DIFFUSION)
        super().__init__(config)

    @property
    def is_configured(self) -> bool:
        return bool(self.config.base_url)

    def health_check(self) -> bool:
        try:
            import requests
            resp = requests.get(
                f"{self.config.base_url}/sdapi/v1/options",
                timeout=5
            )
            return resp.status_code == 200
        except Exception:  # WP-1: keep broad — health probe, any failure = unhealthy
            return False

    def generate(
        self,
        prompt: str,
        *,
        size: str = "1024x1024",
        quality: str = "standard",
        model: Optional[str] = None,
        negative_prompt: Optional[str] = None,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> ImageResponse:
        """Generate image via Stable Diffusion API."""
        import requests

        options = options or {}
        model = model or self.config.default_model or "sd"

        # Parse size
        if "x" in size:
            width, height = map(int, size.split("x"))
        else:
            width, height = 1024, 1024

        # Map quality to steps
        steps_map = {"draft": 15, "standard": 25, "hd": 35, "ultra": 50}
        steps = steps_map.get(quality, 25)

        request_hash = self._compute_request_hash(prompt, model, size)

        payload = {
            "prompt": prompt,
            "negative_prompt": negative_prompt or "",
            "width": width,
            "height": height,
            "steps": steps,
            "cfg_scale": options.get("cfg_scale", 7.5),
            "sampler_name": options.get("sampler", "DPM++ 2M Karras"),
            "seed": seed if seed is not None else -1,
        }

        # Add LoRA if specified
        if options.get("lora_name"):
            lora_weight = options.get("lora_weight", 0.8)
            payload["prompt"] = f"<lora:{options['lora_name']}:{lora_weight}> {prompt}"

        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                resp = requests.post(
                    f"{self.config.base_url}/sdapi/v1/txt2img",
                    json=payload,
                    timeout=self.config.timeout_seconds,
                )
                resp.raise_for_status()
                data = resp.json()

                if not data.get("images"):
                    raise ImageGenerationError("No images in SD response")

                image_bytes = base64.b64decode(data["images"][0])
                info = data.get("info", {})
                if isinstance(info, str):
                    import json
                    try:
                        info = json.loads(info)
                    except (ValueError, json.JSONDecodeError):
                        info = {}

                return ImageResponse(
                    image_bytes=image_bytes,
                    format="png",
                    provider="stable_diffusion",
                    model=model,
                    size=size,
                    seed=info.get("seed"),
                    metadata={
                        "steps": steps,
                        "cfg_scale": payload["cfg_scale"],
                        "sampler": payload["sampler_name"],
                    },
                    request_hash=request_hash,
                )

            except requests.exceptions.Timeout:
                last_error = f"Timeout after {self.config.timeout_seconds}s"
            except requests.exceptions.ConnectionError:
                last_error = f"Connection failed to {self.config.base_url}"
            except Exception as e:  # WP-1: keep broad — AI API retry loop catch-all
                last_error = str(e)

            if attempt < self.config.max_retries - 1:
                logger.warning(f"SD attempt {attempt + 1} failed: {last_error}")
                time.sleep(self.config.retry_delay_seconds)

        raise ImageGenerationError(
            f"SD generation failed after {self.config.max_retries} attempts: {last_error}"
        )


# ---------------------------------------------------------------------------
# Stub Client (Testing)
# ---------------------------------------------------------------------------

class StubImageClient(ImageClient):
    """Stub client for testing without real API calls."""

    def __init__(self, config: Optional[ImageConfig] = None):
        if config is None:
            config = ImageConfig(provider=ImageProvider.STUB)
        super().__init__(config)
        self.call_count = 0
        self.last_prompt: Optional[str] = None

    @property
    def is_configured(self) -> bool:
        return True

    def health_check(self) -> bool:
        return True

    def generate(
        self,
        prompt: str,
        *,
        size: str = "1024x1024",
        quality: str = "standard",
        model: Optional[str] = None,
        negative_prompt: Optional[str] = None,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> ImageResponse:
        """Generate placeholder image."""
        self.call_count += 1
        self.last_prompt = prompt

        # Create minimal valid PNG (1x1 white pixel)
        png_bytes = bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
            0x00, 0x00, 0x00, 0x0D,  # IHDR length
            0x49, 0x48, 0x44, 0x52,  # IHDR
            0x00, 0x00, 0x00, 0x01,  # width: 1
            0x00, 0x00, 0x00, 0x01,  # height: 1
            0x08, 0x02,              # 8-bit RGB
            0x00, 0x00, 0x00,        # compression, filter, interlace
            0x90, 0x77, 0x53, 0xDE,  # CRC
            0x00, 0x00, 0x00, 0x0C,  # IDAT length
            0x49, 0x44, 0x41, 0x54,  # IDAT
            0x08, 0xD7, 0x63, 0xF8, 0xFF, 0xFF, 0xFF, 0x00,
            0x05, 0xFE, 0x02, 0xFE,  # CRC
            0x00, 0x00, 0x00, 0x00,  # IEND length
            0x49, 0x45, 0x4E, 0x44,  # IEND
            0xAE, 0x42, 0x60, 0x82,  # CRC
        ])

        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]
        request_hash = self._compute_request_hash(prompt, "stub", size)

        return ImageResponse(
            image_bytes=png_bytes,
            format="png",
            provider="stub",
            model="stub",
            size=size,
            seed=seed or hash(prompt) % 2**32,
            metadata={
                "stub": True,
                "prompt_hash": prompt_hash,
                "call_count": self.call_count,
            },
            request_hash=request_hash,
        )


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

_default_client: Optional[ImageClient] = None


def get_image_client(provider: str = "stub") -> ImageClient:
    """Get an image client instance."""
    global _default_client

    provider = provider.lower()

    if provider in ("openai", "dalle", "dall-e", "dalle3"):
        if _default_client is None or not isinstance(_default_client, OpenAIImageClient):
            _default_client = OpenAIImageClient()
        return _default_client

    elif provider in ("sd", "stable_diffusion", "sdxl", "sd15"):
        if _default_client is None or not isinstance(_default_client, StableDiffusionClient):
            _default_client = StableDiffusionClient()
        return _default_client

    else:
        if _default_client is None or not isinstance(_default_client, StubImageClient):
            _default_client = StubImageClient()
        return _default_client


def set_image_client(client: ImageClient) -> None:
    """Set the default image client instance (for testing)."""
    global _default_client
    _default_client = client
