#!/usr/bin/env python3
"""
Image Providers — Governance-Aligned Implementation

GOVERNANCE CONTRACT (from OpenAI_Provider_Contract.md):

    @dataclass
    class AiImageResult:
        image_bytes: bytes
        format: str = "png"
        prompt_used: str = ""
        model: str = ""

    class AiImageProvider(Protocol):
        def generate_image(
            self,
            prompt: str,
            *,
            size: str = "1024x1024",
            format: str = "png",
            model: Optional[str] = None,
            options: Optional[Dict[str, Any]] = None,
        ) -> AiImageResult: ...

HARD RULES:
    - providers.py owns normalization + provider selection
    - transport (image_transport.py) owns HTTP only
    - One-way dependency: providers → transport

This file is designed to merge INTO services/providers.py using
capability-based design (Option C).

Author: Luthier's ToolBox
Date: December 17, 2025
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Dict, Optional, Any, Protocol, runtime_checkable
from enum import Enum

# Transport layer (one-way dependency)
from .image_transport import (
    ImageTransport,
    OpenAIImageTransport,
    StableDiffusionTransport,
    StubImageTransport,
    get_image_transport,
)


# =============================================================================
# GOVERNANCE CONTRACT — DO NOT MODIFY WITHOUT REVIEW
# =============================================================================

@dataclass
class AiImageResult:
    """
    Result from image generation.
    
    GOVERNANCE: This is the canonical contract. All providers return this.
    """
    image_bytes: bytes
    format: str = "png"
    prompt_used: str = ""
    model: str = ""
    
    @property
    def base64(self) -> str:
        """Base64 encoding for JSON serialization."""
        return base64.b64encode(self.image_bytes).decode('ascii')
    
    @classmethod
    def from_base64(cls, b64: str, **kwargs) -> "AiImageResult":
        """Construct from base64 string."""
        return cls(image_bytes=base64.b64decode(b64), **kwargs)
    
    @property
    def size_bytes(self) -> int:
        """Size of image in bytes."""
        return len(self.image_bytes)


@runtime_checkable
class AiImageProvider(Protocol):
    """
    Protocol for image generation providers.
    
    GOVERNANCE: All image providers must implement this interface.
    """
    
    def generate_image(
        self,
        prompt: str,
        *,
        size: str = "1024x1024",
        format: str = "png",
        model: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> AiImageResult:
        """Generate an image from prompt."""
        ...


# =============================================================================
# PROVIDER IMPLEMENTATIONS
# =============================================================================

class OpenAIProvider:
    """
    OpenAI-backed provider using the transport layer.
    
    GOVERNANCE:
        - providers.py owns normalization + provider selection
        - image_transport.py owns HTTP transport only
    """
    
    def __init__(self, transport: Optional[ImageTransport] = None):
        self.transport = transport or OpenAIImageTransport()
    
    def generate_image(
        self,
        prompt: str,
        *,
        size: str = "1024x1024",
        format: str = "png",
        model: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> AiImageResult:
        """Generate image via OpenAI DALL-E."""
        
        prompt_used = (prompt or "").strip()
        if not prompt_used:
            raise ValueError("prompt is required")
        
        # Transport returns tuple[bytes, dict]
        image_bytes, meta = self.transport.generate_image_bytes(
            prompt=prompt_used,
            size=size,
            format=format,
            model=model or "dall-e-3",
            options=options or {},
        )
        
        if not isinstance(image_bytes, (bytes, bytearray)):
            raise RuntimeError(
                "transport.generate_image_bytes must return raw bytes as first value"
            )
        
        used_model = ""
        if isinstance(meta, dict):
            used_model = str(meta.get("model") or "")
        
        return AiImageResult(
            image_bytes=bytes(image_bytes),
            format=format,
            prompt_used=prompt_used,
            model=used_model or (model or "dall-e-3"),
        )
    
    def health_check(self) -> bool:
        """Check provider health."""
        return self.transport.health_check()


class StableDiffusionProvider:
    """
    Stable Diffusion provider (Automatic1111, ComfyUI).
    
    Supports LoRA models for guitar-specific generation.
    """
    
    def __init__(self, transport: Optional[ImageTransport] = None):
        self.transport = transport or StableDiffusionTransport()
    
    def generate_image(
        self,
        prompt: str,
        *,
        size: str = "1024x1024",
        format: str = "png",
        model: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> AiImageResult:
        """Generate image via Stable Diffusion."""
        
        prompt_used = (prompt or "").strip()
        if not prompt_used:
            raise ValueError("prompt is required")
        
        image_bytes, meta = self.transport.generate_image_bytes(
            prompt=prompt_used,
            size=size,
            format=format,
            model=model,
            options=options or {},
        )
        
        if not isinstance(image_bytes, (bytes, bytearray)):
            raise RuntimeError(
                "transport.generate_image_bytes must return raw bytes"
            )
        
        used_model = ""
        if isinstance(meta, dict):
            used_model = str(meta.get("model") or "")
        
        return AiImageResult(
            image_bytes=bytes(image_bytes),
            format=format,
            prompt_used=prompt_used,
            model=used_model or (model or "sd"),
        )
    
    def health_check(self) -> bool:
        """Check provider health."""
        return self.transport.health_check()


class StubProvider:
    """
    Mock provider for testing.
    
    Returns deterministic placeholder images without network calls.
    """
    
    def __init__(self, transport: Optional[ImageTransport] = None):
        self.transport = transport or StubImageTransport()
        self.call_count = 0
        self.last_prompt: Optional[str] = None
    
    def generate_image(
        self,
        prompt: str,
        *,
        size: str = "1024x1024",
        format: str = "png",
        model: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> AiImageResult:
        """Generate placeholder image."""
        
        prompt_used = (prompt or "").strip()
        self.call_count += 1
        self.last_prompt = prompt_used
        
        image_bytes, meta = self.transport.generate_image_bytes(
            prompt=prompt_used,
            size=size,
            format=format,
            model=model,
            options=options or {},
        )
        
        return AiImageResult(
            image_bytes=bytes(image_bytes),
            format=format,
            prompt_used=prompt_used,
            model="stub",
        )
    
    def health_check(self) -> bool:
        """Stub is always healthy."""
        return True


class LocalUploadProvider:
    """
    Provider for user-uploaded images.
    
    No network calls — validates and passes through user-provided images.
    """
    
    def __init__(self):
        self.call_count = 0
    
    def generate_image(
        self,
        prompt: str,
        *,
        size: str = "1024x1024",
        format: str = "png",
        model: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> AiImageResult:
        """
        'Generate' from user-provided image bytes.
        
        Expects options["image_bytes"] or options["image_base64"].
        """
        options = options or {}
        
        if "image_bytes" in options:
            image_bytes = options["image_bytes"]
        elif "image_base64" in options:
            image_bytes = base64.b64decode(options["image_base64"])
        else:
            raise ValueError(
                "LocalUploadProvider requires options['image_bytes'] or options['image_base64']"
            )
        
        if not isinstance(image_bytes, (bytes, bytearray)):
            raise ValueError("image_bytes must be bytes")
        
        self.call_count += 1
        
        return AiImageResult(
            image_bytes=bytes(image_bytes),
            format=format,
            prompt_used=prompt or "user_upload",
            model="local_upload",
        )
    
    def health_check(self) -> bool:
        """Local upload is always healthy."""
        return True


# =============================================================================
# PROVIDER REGISTRY
# =============================================================================

class ImageProviderType(str, Enum):
    """Available image provider types."""
    OPENAI = "openai"
    DALLE = "dalle"
    STABLE_DIFFUSION = "sd"
    SDXL = "sdxl"
    LORA = "lora"
    STUB = "stub"
    LOCAL = "local"


# Global registry
_provider_registry: Dict[str, AiImageProvider] = {}
_default_provider: Optional[AiImageProvider] = None


def register_provider(name: str, provider: AiImageProvider) -> None:
    """Register a provider by name."""
    _provider_registry[name.lower()] = provider


def get_provider(name: Optional[str] = None) -> AiImageProvider:
    """
    Get provider by name, or default.
    
    Args:
        name: Provider name ("openai", "sd", "stub", etc.)
              If None, returns default provider.
    
    Returns:
        AiImageProvider instance
    """
    global _default_provider
    
    if name is None:
        if _default_provider is None:
            _default_provider = StubProvider()
        return _default_provider
    
    name = name.lower()
    
    if name in _provider_registry:
        return _provider_registry[name]
    
    # Create on demand
    if name in ("openai", "dalle", "dall-e", "dalle3"):
        provider = OpenAIProvider()
    elif name in ("sd", "stable_diffusion", "sdxl", "sd15", "lora"):
        provider = StableDiffusionProvider()
    elif name == "local":
        provider = LocalUploadProvider()
    else:
        provider = StubProvider()
    
    _provider_registry[name] = provider
    return provider


def set_provider(provider: AiImageProvider, name: Optional[str] = None) -> None:
    """
    Set provider, optionally by name.
    
    Args:
        provider: Provider instance
        name: If provided, registers by name. If None, sets as default.
    """
    global _default_provider
    
    if name is not None:
        _provider_registry[name.lower()] = provider
    else:
        _default_provider = provider


def set_default_provider(provider: AiImageProvider) -> None:
    """Set the default provider."""
    global _default_provider
    _default_provider = provider


def list_providers() -> Dict[str, bool]:
    """
    List available providers and their health status.
    
    Returns:
        Dict mapping provider name to health status
    """
    providers = {
        "openai": OpenAIProvider(),
        "sd": StableDiffusionProvider(),
        "stub": StubProvider(),
        "local": LocalUploadProvider(),
    }
    
    return {name: p.health_check() for name, p in providers.items()}


# =============================================================================
# CONVENIENCE FUNCTION (backward compatibility)
# =============================================================================

def generate_image(
    prompt: str,
    *,
    provider: Optional[str] = None,
    size: str = "1024x1024",
    format: str = "png",
    model: Optional[str] = None,
    options: Optional[Dict[str, Any]] = None,
) -> AiImageResult:
    """
    Generate image using specified or default provider.
    
    Convenience wrapper for quick usage.
    
    Args:
        prompt: Image generation prompt
        provider: Provider name (default: use default provider)
        size: Image size (e.g., "1024x1024")
        format: Image format ("png", "jpg")
        model: Model override
        options: Provider-specific options
    
    Returns:
        AiImageResult with image bytes
    """
    p = get_provider(provider)
    return p.generate_image(
        prompt,
        size=size,
        format=format,
        model=model,
        options=options,
    )


# =============================================================================
# ROUTE-FACING TYPES (wrap governance contract for API layer)
# =============================================================================

class ImageProvider(str, Enum):
    """Provider enum for routes."""
    DALLE3 = "dalle3"
    SDXL = "sdxl"
    SD15 = "sd15"
    GUITAR_LORA = "guitar_lora"
    MIDJOURNEY = "midjourney"
    STUB = "stub"


class ImageSize(str, Enum):
    """Image size options."""
    SQUARE_SM = "512x512"
    SQUARE_MD = "768x768"
    SQUARE_LG = "1024x1024"
    PORTRAIT = "768x1024"
    LANDSCAPE = "1024x768"
    WIDE = "1792x1024"
    TALL = "1024x1792"


class ImageQuality(str, Enum):
    """Quality levels."""
    DRAFT = "draft"
    STANDARD = "standard"
    HD = "hd"
    ULTRA = "ultra"


# Provider cost per image (USD)
PROVIDER_COSTS: Dict[ImageProvider, Dict[ImageQuality, float]] = {
    ImageProvider.DALLE3: {
        ImageQuality.DRAFT: 0.04,
        ImageQuality.STANDARD: 0.04,
        ImageQuality.HD: 0.08,
        ImageQuality.ULTRA: 0.12,
    },
    ImageProvider.SDXL: {
        ImageQuality.DRAFT: 0.002,
        ImageQuality.STANDARD: 0.004,
        ImageQuality.HD: 0.006,
        ImageQuality.ULTRA: 0.01,
    },
    ImageProvider.SD15: {
        ImageQuality.DRAFT: 0.001,
        ImageQuality.STANDARD: 0.002,
        ImageQuality.HD: 0.003,
        ImageQuality.ULTRA: 0.005,
    },
    ImageProvider.GUITAR_LORA: {
        ImageQuality.DRAFT: 0.002,
        ImageQuality.STANDARD: 0.004,
        ImageQuality.HD: 0.006,
        ImageQuality.ULTRA: 0.01,
    },
    ImageProvider.STUB: {
        ImageQuality.DRAFT: 0.0,
        ImageQuality.STANDARD: 0.0,
        ImageQuality.HD: 0.0,
        ImageQuality.ULTRA: 0.0,
    },
    ImageProvider.MIDJOURNEY: {
        ImageQuality.DRAFT: 0.02,
        ImageQuality.STANDARD: 0.04,
        ImageQuality.HD: 0.06,
        ImageQuality.ULTRA: 0.08,
    },
}


@dataclass
class GeneratedImage:
    """Single generated image (route-facing)."""
    image_id: str
    url: Optional[str] = None
    base64_data: Optional[str] = None
    provider: ImageProvider = ImageProvider.STUB
    generation_time_ms: float = 0.0
    seed_used: Optional[int] = None
    
    # Underlying governance result
    _result: Optional[AiImageResult] = None
    
    @classmethod
    def from_ai_result(
        cls,
        result: AiImageResult,
        image_id: str,
        provider: ImageProvider,
        generation_time_ms: float,
    ) -> "GeneratedImage":
        """Create from governance AiImageResult."""
        return cls(
            image_id=image_id,
            base64_data=result.base64,
            provider=provider,
            generation_time_ms=generation_time_ms,
            _result=result,
        )


@dataclass
class GenerationRequest:
    """Generation request (route-facing)."""
    request_id: str
    user_prompt: str
    engineered_prompt: str
    negative_prompt: str
    provider: ImageProvider
    size: ImageSize
    quality: ImageQuality
    num_images: int = 1
    
    def estimated_cost(self) -> float:
        """Estimate generation cost."""
        per_image = PROVIDER_COSTS.get(self.provider, {}).get(self.quality, 0.04)
        return per_image * self.num_images


@dataclass
class ImageGenerationResult:
    """Result from generation (route-facing)."""
    success: bool
    request: GenerationRequest
    images: list  # List[GeneratedImage]
    actual_cost: float = 0.0
    error: Optional[str] = None


class GuitarVisionEngine:
    """
    High-level engine for guitar image generation.
    
    Wraps the governance AiImageProvider contract with:
    - Guitar-specific prompt engineering
    - Provider routing based on quality/cost preferences
    - Cost tracking
    - Rich result types for API layer
    
    GOVERNANCE: Uses AiImageProvider internally, exposes route-facing types.
    """
    
    def __init__(self):
        self._providers: Dict[ImageProvider, AiImageProvider] = {}
        self._init_providers()
    
    def _init_providers(self):
        """Initialize available providers."""
        self._providers[ImageProvider.DALLE3] = OpenAIProvider()
        self._providers[ImageProvider.SDXL] = StableDiffusionProvider()
        self._providers[ImageProvider.SD15] = StableDiffusionProvider()
        self._providers[ImageProvider.GUITAR_LORA] = StableDiffusionProvider()
        self._providers[ImageProvider.STUB] = StubProvider()
    
    def _select_provider(
        self,
        force_provider: Optional[ImageProvider] = None,
        prefer_quality: bool = False,
        prefer_cost: bool = False,
    ) -> ImageProvider:
        """Select best provider based on preferences."""
        if force_provider:
            return force_provider
        
        # Check what's available
        available = []
        for p, impl in self._providers.items():
            if impl.health_check():
                available.append(p)
        
        if not available:
            return ImageProvider.STUB
        
        if prefer_quality and ImageProvider.DALLE3 in available:
            return ImageProvider.DALLE3
        elif prefer_cost:
            # Prefer cheaper providers
            for p in [ImageProvider.STUB, ImageProvider.SD15, ImageProvider.SDXL]:
                if p in available:
                    return p
        
        # Default preference
        if ImageProvider.DALLE3 in available:
            return ImageProvider.DALLE3
        return available[0]
    
    def generate(
        self,
        user_prompt: str,
        num_images: int = 1,
        size: ImageSize = ImageSize.SQUARE_LG,
        quality: ImageQuality = ImageQuality.STANDARD,
        photo_style: Optional[str] = None,
        prefer_quality: bool = False,
        prefer_cost: bool = False,
        force_provider: Optional[ImageProvider] = None,
    ) -> ImageGenerationResult:
        """
        Generate guitar images.
        
        Args:
            user_prompt: Natural language description
            num_images: Number of images (1-4)
            size: Output size
            quality: Quality level
            photo_style: Photography style override
            prefer_quality: Prefer higher quality provider
            prefer_cost: Prefer cheaper provider
            force_provider: Force specific provider
        
        Returns:
            ImageGenerationResult with generated images
        """
        import time
        from uuid import uuid4
        
        # Select provider
        provider = self._select_provider(force_provider, prefer_quality, prefer_cost)
        impl = self._providers.get(provider, StubProvider())
        
        # Engineer prompt (import here to avoid circular)
        try:
            from .prompt_engine import engineer_guitar_prompt
            guitar_prompt = engineer_guitar_prompt(user_prompt, photo_style=photo_style)
            engineered = guitar_prompt.positive_prompt
            negative = guitar_prompt.negative_prompt
        except ImportError:
            engineered = user_prompt
            negative = ""
        
        # Build request
        request_id = f"gen_{uuid4().hex[:12]}"
        request = GenerationRequest(
            request_id=request_id,
            user_prompt=user_prompt,
            engineered_prompt=engineered,
            negative_prompt=negative,
            provider=provider,
            size=size,
            quality=quality,
            num_images=num_images,
        )
        
        # Generate images
        images = []
        total_cost = 0.0
        errors = []
        
        for i in range(num_images):
            start = time.time()
            try:
                # Call governance contract
                result = impl.generate_image(
                    engineered,
                    size=size.value,
                    format="png",
                    options={
                        "quality": quality.value,
                        "negative_prompt": negative,
                    },
                )
                
                elapsed = (time.time() - start) * 1000
                
                image = GeneratedImage.from_ai_result(
                    result=result,
                    image_id=f"{request_id}_img{i}",
                    provider=provider,
                    generation_time_ms=elapsed,
                )
                images.append(image)
                
                # Track cost
                per_image = PROVIDER_COSTS.get(provider, {}).get(quality, 0.04)
                total_cost += per_image
                
            except Exception as e:
                errors.append(str(e))
        
        success = len(images) > 0
        error_msg = "; ".join(errors) if errors else None
        
        return ImageGenerationResult(
            success=success,
            request=request,
            images=images,
            actual_cost=total_cost,
            error=error_msg,
        )
    
    def available_providers(self) -> list:
        """List providers with health status."""
        return [
            {"id": p.value, "available": impl.health_check()}
            for p, impl in self._providers.items()
        ]


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Governance Contract
    "AiImageResult",
    "AiImageProvider",
    # Providers
    "OpenAIProvider",
    "StableDiffusionProvider",
    "StubProvider",
    "LocalUploadProvider",
    # Registry
    "ImageProviderType",
    "get_provider",
    "set_provider",
    "set_default_provider",
    "register_provider",
    "list_providers",
    # Convenience
    "generate_image",
    # Route-facing (wraps governance)
    "ImageProvider",
    "ImageSize",
    "ImageQuality",
    "PROVIDER_COSTS",
    "GeneratedImage",
    "GenerationRequest",
    "ImageGenerationResult",
    "GuitarVisionEngine",
]
