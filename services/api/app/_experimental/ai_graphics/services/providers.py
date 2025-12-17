"""
AI Graphics Providers - High-Level Provider Adapter/Registry

This module provides the high-level interface for AI rosette generation.
It normalizes outputs to internal schemas and exposes a stable interface.

IMPORTANT: This module imports from llm_client.py.
llm_client.py must NOT import from this module (one-way dependency).

Usage:
    from .providers import get_provider, StubProvider

    provider = get_provider()
    candidates = provider.generate_rosette_params(prompt="...", count=3)

Architecture:
    providers.py (this file)
        ↓ imports
    llm_client.py (transport layer)
"""
from __future__ import annotations

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from ..schemas.ai_schemas import RosetteParamSpec, RingParam
from .llm_client import (
    LLMClient,
    LLMConfig,
    LLMProvider as LLMProviderEnum,
    LLMClientError,
    get_llm_client,
)


# ---------------------------------------------------------------------------
# Provider Protocol
# ---------------------------------------------------------------------------

@runtime_checkable
class AiProvider(Protocol):
    """
    Protocol for AI rosette parameter providers.

    Implementations must provide generate_rosette_params() which takes
    a natural language prompt and returns domain-specific RosetteParamSpec.
    """

    def generate_rosette_params(
        self,
        prompt: str,
        *,
        count: int = 3,
        options: Optional[Dict[str, Any]] = None,
    ) -> List[RosetteParamSpec]:
        """
        Generate rosette parameter candidates from a natural language prompt.

        Args:
            prompt: Natural language description of desired rosette
            count: Number of candidates to generate
            options: Provider-specific options

        Returns:
            List of RosetteParamSpec candidates
        """
        ...


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class AiImageResult:
    """Result from image generation."""
    image_bytes: bytes
    format: str = "png"
    prompt_used: str = ""
    model: str = ""


# ---------------------------------------------------------------------------
# Stub Provider (mock generation for testing)
# ---------------------------------------------------------------------------

class StubProvider:
    """
    Stub provider that returns mock candidates.

    This is the default provider when no real AI backend is configured.
    It parses prompt keywords to generate plausible mock data.
    """

    def generate_rosette_params(
        self,
        prompt: str,
        *,
        count: int = 3,
        options: Optional[Dict[str, Any]] = None,
    ) -> List[RosetteParamSpec]:
        """Generate mock rosette candidates based on prompt keywords."""
        candidates: List[RosetteParamSpec] = []

        # Parse prompt for sizing hints
        base_outer = 80.0
        base_inner = 15.0

        prompt_lower = prompt.lower()

        if "large" in prompt_lower:
            base_outer = 120.0
            base_inner = 25.0
        elif "small" in prompt_lower:
            base_outer = 50.0
            base_inner = 10.0

        # Parse ring width hints
        if "thin" in prompt_lower:
            ring_width_range = (1.5, 3.0)
        elif "thick" in prompt_lower or "wide" in prompt_lower:
            ring_width_range = (4.0, 8.0)
        else:
            ring_width_range = (2.5, 5.0)

        # Parse complexity hints
        ring_count = 4
        if "simple" in prompt_lower or "minimal" in prompt_lower:
            ring_count = 2
        elif "complex" in prompt_lower or "intricate" in prompt_lower:
            ring_count = 6

        # Parse pattern type
        pattern = "herringbone"
        if "radial" in prompt_lower:
            pattern = "radial"
        elif "chevron" in prompt_lower:
            pattern = "chevron"
        elif "spiral" in prompt_lower:
            pattern = "spiral"

        # Generate variations
        for i in range(count):
            outer = base_outer + random.uniform(-10, 10)
            inner = base_inner + random.uniform(-3, 3)

            rings: List[RingParam] = []
            for r in range(ring_count):
                width = random.uniform(*ring_width_range)
                rings.append(
                    RingParam(
                        ring_index=r,
                        width_mm=round(width, 2),
                    )
                )

            candidates.append(
                RosetteParamSpec(
                    outer_diameter_mm=round(outer, 1),
                    inner_diameter_mm=round(inner, 1),
                    ring_params=rings,
                    pattern_type=pattern,
                    notes=f"AI candidate #{i+1} for: {prompt[:50]}",
                )
            )

        return candidates

    def generate_image(
        self,
        prompt: str,
        *,
        options: Optional[Dict[str, Any]] = None,
    ) -> AiImageResult:
        """Stub image generation - returns empty bytes."""
        return AiImageResult(
            image_bytes=b"",
            format="png",
            prompt_used=prompt,
            model="stub",
        )


# ---------------------------------------------------------------------------
# OpenAI Provider (uses llm_client transport)
# ---------------------------------------------------------------------------

class OpenAIProvider:
    """
    OpenAI-backed provider for rosette generation.

    Uses llm_client.LLMClient for HTTP transport and handles
    prompt formatting and response parsing.
    """

    SYSTEM_PROMPT = """You are a rosette design assistant for guitar soundhole decorations.
When given a description, generate parametric rosette specifications as JSON.

Output format:
{
  "outer_diameter_mm": <float>,
  "inner_diameter_mm": <float>,
  "ring_params": [
    {"ring_index": 0, "width_mm": <float>},
    ...
  ],
  "pattern_type": "<herringbone|radial|chevron|spiral>",
  "notes": "<brief description>"
}

Guidelines:
- Outer diameter typically 80-120mm for acoustic guitars
- Inner diameter typically 10-30mm
- Ring widths typically 2-6mm each
- Consider tool clearance (minimum ~1.5mm for safe cutting)
"""

    def __init__(self, client: Optional[LLMClient] = None):
        """
        Initialize OpenAI provider.

        Args:
            client: LLMClient instance. If None, uses default client.
        """
        self._client = client or get_llm_client()

    def generate_rosette_params(
        self,
        prompt: str,
        *,
        count: int = 3,
        options: Optional[Dict[str, Any]] = None,
    ) -> List[RosetteParamSpec]:
        """Generate rosette candidates using OpenAI API."""
        options = options or {}

        candidates: List[RosetteParamSpec] = []

        for i in range(count):
            user_prompt = f"""Generate a rosette design based on this description:
"{prompt}"

This is candidate {i+1} of {count}. Vary the design slightly from others.
Return ONLY valid JSON matching the specified format."""

            try:
                response = self._client.request_json(
                    prompt=user_prompt,
                    system_prompt=self.SYSTEM_PROMPT,
                    temperature=options.get("temperature", 0.8),
                    max_tokens=options.get("max_tokens", 1024),
                )

                data = response.data
                if not data:
                    # Fallback to stub if no data
                    continue

                # Parse response into RosetteParamSpec
                rings = [
                    RingParam(
                        ring_index=r.get("ring_index", idx),
                        width_mm=float(r.get("width_mm", 3.0)),
                    )
                    for idx, r in enumerate(data.get("ring_params", []))
                ]

                spec = RosetteParamSpec(
                    outer_diameter_mm=float(data.get("outer_diameter_mm", 80.0)),
                    inner_diameter_mm=float(data.get("inner_diameter_mm", 15.0)),
                    ring_params=rings,
                    pattern_type=data.get("pattern_type", "herringbone"),
                    notes=data.get("notes", f"AI candidate #{i+1}"),
                )
                candidates.append(spec)

            except (LLMClientError, ValueError, KeyError) as e:
                # Log error but continue with remaining candidates
                continue

        # If all API calls failed, fall back to stub
        if not candidates:
            stub = StubProvider()
            return stub.generate_rosette_params(prompt, count=count, options=options)

        return candidates

    def generate_image(
        self,
        prompt: str,
        *,
        options: Optional[Dict[str, Any]] = None,
    ) -> AiImageResult:
        """
        Generate image using DALL-E API.

        Note: This is a placeholder - actual implementation would use
        the images API endpoint.
        """
        # Placeholder - would need separate image API endpoint
        return AiImageResult(
            image_bytes=b"",
            format="png",
            prompt_used=prompt,
            model="dall-e-3",
        )


# ---------------------------------------------------------------------------
# Local Upload Provider (no network)
# ---------------------------------------------------------------------------

class LocalUploadProvider:
    """
    Provider for locally-uploaded rosette specifications.

    Does not make network calls - simply validates and returns
    user-provided specifications.
    """

    def generate_rosette_params(
        self,
        prompt: str,
        *,
        count: int = 3,
        options: Optional[Dict[str, Any]] = None,
    ) -> List[RosetteParamSpec]:
        """
        Return user-provided specs from options.

        Expected options:
            specs: List[Dict] - Raw spec data to convert
        """
        options = options or {}
        raw_specs = options.get("specs", [])

        if not raw_specs:
            return []

        candidates: List[RosetteParamSpec] = []

        for data in raw_specs[:count]:
            try:
                rings = [
                    RingParam(
                        ring_index=r.get("ring_index", idx),
                        width_mm=float(r.get("width_mm", 3.0)),
                    )
                    for idx, r in enumerate(data.get("ring_params", []))
                ]

                spec = RosetteParamSpec(
                    outer_diameter_mm=float(data.get("outer_diameter_mm", 80.0)),
                    inner_diameter_mm=float(data.get("inner_diameter_mm", 15.0)),
                    ring_params=rings,
                    pattern_type=data.get("pattern_type", "herringbone"),
                    notes=data.get("notes", "Local upload"),
                )
                candidates.append(spec)
            except (ValueError, KeyError):
                continue

        return candidates

    def generate_image(
        self,
        prompt: str,
        *,
        options: Optional[Dict[str, Any]] = None,
    ) -> AiImageResult:
        """Local provider does not support image generation."""
        return AiImageResult(
            image_bytes=b"",
            format="png",
            prompt_used=prompt,
            model="local",
        )


# ---------------------------------------------------------------------------
# Provider Registry
# ---------------------------------------------------------------------------

_current_provider: Optional[AiProvider] = None


def get_provider() -> AiProvider:
    """
    Get the current AI provider.

    Returns StubProvider if none is configured.
    """
    global _current_provider
    if _current_provider is None:
        _current_provider = StubProvider()
    return _current_provider


def set_provider(provider: AiProvider) -> None:
    """
    Set the AI provider to use.

    Call this during app startup to configure the provider.

    Args:
        provider: An AiProvider implementation
    """
    global _current_provider
    _current_provider = provider


def reset_provider() -> None:
    """Reset provider to default (StubProvider)."""
    global _current_provider
    _current_provider = None


# ---------------------------------------------------------------------------
# Backward compatibility
# ---------------------------------------------------------------------------

def generate_rosette_param_candidates(
    prompt: str,
    count: int = 3,
) -> List[RosetteParamSpec]:
    """
    Generate rosette parameter candidates from a natural language prompt.

    This is a backward-compatible wrapper that uses the current provider.

    Args:
        prompt: Natural language description of desired rosette
        count: Number of candidates to generate

    Returns:
        List of RosetteParamSpec candidates
    """
    provider = get_provider()
    return provider.generate_rosette_params(prompt, count=count)
