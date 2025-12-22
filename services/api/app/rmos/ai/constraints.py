"""
RMOS Generator Constraints (Canonical)

DOMAIN-SPECIFIC: Rosette parameter constraints for AI generation.
Maps RMOS context (machine/tool/material) to AI generation constraints.

Migrated from: _experimental/ai_core/generator_constraints.py (December 2025)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# RMOS contracts
try:
    from app.rmos.api_contracts import RmosContext
except (ImportError, AttributeError, ModuleNotFoundError):
    from pydantic import BaseModel

    class RmosContext(BaseModel):  # type: ignore
        material_id: Optional[str] = None
        tool_id: Optional[str] = None
        machine_profile_id: Optional[str] = None
        use_shapely_geometry: bool = True


@dataclass
class RosetteGeneratorConstraints:
    """
    High-level constraints for rosette param generation.

    This is intentionally abstract — it does NOT encode geometry directly.
    It only captures things like ring counts, widths, and allowed palettes.
    """

    min_rings: int = 1
    max_rings: int = 8

    min_ring_width_mm: float = 0.3
    max_ring_width_mm: float = 2.5

    min_total_width_mm: float = 1.0
    max_total_width_mm: float = 10.0

    # Whether to allow "complex" patterns like mosaics or segmented patterns.
    allow_mosaic: bool = True
    allow_segmented: bool = True

    # A simple material palette key, to be interpreted elsewhere.
    # e.g. "classic_ebony_maple", "economy", "premium_shell".
    palette_key: str = "default"

    # Whether to bias towards simpler designs (few rings, wider bands).
    bias_simple: bool = True


def constraints_from_context(ctx: RmosContext) -> RosetteGeneratorConstraints:
    """
    Thin adapter to the RMOS constraint profile registry.

    Keeps the AI-side import stable while centralizing rules under rmos/.
    """
    try:
        from app.rmos.constraint_profiles import resolve_constraints_for_context
        return resolve_constraints_for_context(ctx)
    except (ImportError, AttributeError, ModuleNotFoundError):
        # Fallback to basic constraints if constraint_profiles not available
        return _constraints_from_context_basic(ctx)


def _constraints_from_context_basic(ctx: RmosContext) -> RosetteGeneratorConstraints:
    """
    Derive a reasonable constraint profile from RmosContext.
    Basic fallback when constraint_profiles module is not available.
    """
    c = RosetteGeneratorConstraints()

    tool_id = getattr(ctx, "tool_id", None)
    material_id = getattr(ctx, "material_id", None)
    machine_id = getattr(ctx, "machine_profile_id", None)

    # Example: enforce wider minimum ring width based on tool kerf hints.
    if tool_id:
        if "saw" in str(tool_id).lower():
            c.min_ring_width_mm = 0.4
            c.max_ring_width_mm = 2.0
            c.max_total_width_mm = 8.0
        if "router" in str(tool_id).lower():
            c.min_ring_width_mm = 0.5

    # Example: adjust palette based on material.
    if material_id:
        lower = str(material_id).lower()
        if "maple" in lower:
            c.palette_key = "maple_contrast"
        elif "shell" in lower or "abalone" in lower:
            c.palette_key = "premium_shell"
            c.allow_mosaic = True

    # Example: change complexity by machine.
    if machine_id:
        lower = str(machine_id).lower()
        if "proto" in lower or "test" in lower:
            c.max_rings = 4
            c.bias_simple = True
        elif "prod" in lower or "production" in lower:
            c.max_rings = 8
            c.bias_simple = False

    return c


__all__ = [
    "RosetteGeneratorConstraints",
    "constraints_from_context",
]
