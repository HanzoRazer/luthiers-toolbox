"""
Art Studio SVG Generator

Prompt→SVG generation using ai.image_client directly (Option 2).
This provides cleaner separation from Vision service while
using the canonical AI Platform transport layer.

Architecture:
    Prompt → ai.transport.image_client → PNG bytes → Vectorize → SVG

The AI Platform layer handles:
- Provider selection (DALL-E, Stable Diffusion, Stub)
- Safety enforcement
- Cost estimation
- Audit logging

This module handles:
- SVG-specific prompt engineering
- PNG→SVG vectorization (potrace/vtracer)
- Style presets for lutherie patterns
"""

from .generator import (
    generate_svg_from_prompt,
    SVGGeneratorConfig,
    SVGResult,
    VectorizeMethod,
)

from .styles import (
    SVG_STYLE_PRESETS,
    get_style_prompt_suffix,
)

__all__ = [
    "generate_svg_from_prompt",
    "SVGGeneratorConfig",
    "SVGResult",
    "VectorizeMethod",
    "SVG_STYLE_PRESETS",
    "get_style_prompt_suffix",
]
