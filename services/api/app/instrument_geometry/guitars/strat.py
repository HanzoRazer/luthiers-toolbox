"""
Stratocaster Model — GAP-08 Fix

Wave 14 Guitar Model - Fender Stratocaster

Specifications:
- Scale Length: 648.0mm (25.5")
- Frets: 21 (vintage), 22 (modern), 24 (extended)
- Strings: 6
- Radius: 9.5" (241.3mm) modern, 7.25" (184.15mm) vintage
- Category: Electric Guitar

GAP-08: Removed hardcoded fret count. Now supports variants:
  - "vintage": 21 frets, 7.25" radius
  - "modern": 22 frets, 9.5"-12" compound radius (default)
  - "24fret": 24 frets, 12"-16" compound radius
"""

from typing import Literal, Optional
import json
from pathlib import Path

from ..neck.neck_profiles import InstrumentSpec

# Variant type for type hints
StratVariant = Literal["vintage", "modern", "24fret"]

# Load specs from JSON (single source of truth)
_SPEC_FILE = Path(__file__).parent.parent / "specs" / "stratocaster.json"


def _load_strat_spec() -> dict:
    """Load stratocaster.json spec file."""
    if _SPEC_FILE.exists():
        return json.loads(_SPEC_FILE.read_text(encoding="utf-8"))
    # Fallback if file missing
    return {}


def get_model_info(variant: StratVariant = "modern") -> dict:
    """
    Get MODEL_INFO dict for a Strat variant.

    Args:
        variant: "vintage", "modern", or "24fret"

    Returns:
        Dict with model specifications
    """
    spec = _load_strat_spec()
    var_data = spec.get("variants", {}).get(variant, {})
    neck = var_data.get("neck", {})

    return {
        "id": f"stratocaster_{variant}",
        "display_name": f"Fender Stratocaster ({variant})",
        "manufacturer": "Fender",
        "year_introduced": 1954,
        "scale_length_mm": var_data.get("scale_length_mm", 648.0),
        "fret_count": var_data.get("fret_count", 22),
        "string_count": 6,
        "nut_width_mm": neck.get("nut_width_mm", 42.0),
        "body_width_mm": 330.0,
        "body_length_mm": 460.0,
        "radius_mm": neck.get("fretboard_radius_mm", neck.get("fretboard_radius_start_mm", 241.3)),
        "category": "electric_guitar",
        "variant": variant,
    }


# Default MODEL_INFO for backward compatibility
MODEL_INFO = get_model_info("modern")


def get_spec(variant: StratVariant = "modern") -> InstrumentSpec:
    """
    Get InstrumentSpec for a Stratocaster variant.

    Args:
        variant: "vintage", "modern", or "24fret"

    Returns:
        InstrumentSpec configured for the variant

    Example:
        >>> spec = get_spec("24fret")
        >>> spec.fret_count
        24
    """
    spec = _load_strat_spec()
    var_data = spec.get("variants", {}).get(variant, {})
    neck = var_data.get("neck", {})

    # Get fret count from JSON, with sensible defaults
    fret_count = var_data.get("fret_count", 22)

    # Handle single vs compound radius
    if neck.get("compound_radius", False):
        base_radius = neck.get("fretboard_radius_start_mm", 241.3)
        end_radius = neck.get("fretboard_radius_end_mm", 304.8)
    else:
        base_radius = neck.get("fretboard_radius_mm", 184.15)
        end_radius = base_radius  # Single radius

    return InstrumentSpec(
        instrument_type="electric",
        scale_length_mm=var_data.get("scale_length_mm", 648.0),
        fret_count=fret_count,
        string_count=6,
        base_radius_mm=base_radius,
        end_radius_mm=end_radius,
    )


def list_variants() -> list[str]:
    """List available Strat variants."""
    spec = _load_strat_spec()
    return list(spec.get("variants", {}).keys())
