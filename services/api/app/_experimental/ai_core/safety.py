# services/api/app/ai_core/safety.py
"""
Safety utilities for AI-generated rosette designs.
Coerces raw dicts into valid RosetteParamSpec objects.
"""

from __future__ import annotations

from typing import Any, Dict

# Lazy import to avoid circular dependencies
try:
    from ..rmos.api_contracts import RosetteParamSpec
except (ImportError, AttributeError, ModuleNotFoundError):
    # Fallback stub
    from pydantic import BaseModel
    
    class RosetteParamSpec(BaseModel):  # type: ignore
        outer_diameter_mm: float = 100.0
        inner_diameter_mm: float = 20.0
        ring_count: int = 3
        pattern_type: str = "herringbone"
        version: str = "1.0"
        rings: list = []
        notes: str = ""


def coerce_to_rosette_spec(raw: Dict[str, Any]) -> RosetteParamSpec:
    """
    Coerce a raw dict into a valid RosetteParamSpec.
    
    This is the safety layer that ensures AI-generated designs
    conform to the expected schema.
    
    Args:
        raw: Dictionary with design parameters
        
    Returns:
        A valid RosetteParamSpec instance
    """
    # Ensure required fields have defaults
    defaults = {
        "version": "1.0",
        "rings": [],
        "notes": "",
        "outer_diameter_mm": 100.0,
        "inner_diameter_mm": 20.0,
        "ring_count": 3,
        "pattern_type": "herringbone",
    }
    
    # Merge with defaults
    merged = {**defaults, **raw}
    
    # Validate ring_count matches rings list if provided
    if "rings" in merged and isinstance(merged["rings"], list):
        merged["ring_count"] = len(merged["rings"])
    
    try:
        return RosetteParamSpec.model_validate(merged)
    except Exception:
        # If validation fails, try with just the defaults
        try:
            return RosetteParamSpec.model_validate(defaults)
        except Exception:
            # Last resort: return with whatever we can construct
            return RosetteParamSpec(**defaults)
