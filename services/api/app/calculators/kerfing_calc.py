"""
GEOMETRY-003: Kerfing Geometry Calculator

Kerfing adds depth to the sides at the top and back.
It provides the gluing surface for top and back plates.

Standard kerfing dimensions:
  width_mm: 6.35  (1/4")
  height_mm: 7.94  (5/16") for standard
  kerf_spacing_mm: 3.0  (slot spacing)
  kerf_depth_ratio: 0.66  (2/3 of height)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

KerfingType = Literal[
    "standard_lining",
    "reverse_kerfing",
    "laminate_lining",
    "carbon_fiber",
    "solid_lining",
]


# Standard kerfing type specifications
KERFING_TYPES = {
    "standard_lining": {
        "height_mm": 7.94,       # 5/16"
        "width_mm": 6.35,        # 1/4"
        "kerf_spacing_mm": 3.0,
        "kerf_depth_ratio": 0.66,
        "has_kerfs": True,
        "flexibility": "flexible",
        "material": "basswood",
    },
    "reverse_kerfing": {
        "height_mm": 9.53,       # 3/8" - taller for more glue surface
        "width_mm": 6.35,
        "kerf_spacing_mm": 3.5,
        "kerf_depth_ratio": 0.66,
        "has_kerfs": True,
        "flexibility": "semi-stiff",
        "material": "mahogany",
    },
    "laminate_lining": {
        "height_mm": 6.35,       # 1/4" - thinner, very flexible
        "width_mm": 6.35,
        "kerf_spacing_mm": 2.5,
        "kerf_depth_ratio": 0.70,
        "has_kerfs": True,
        "flexibility": "very flexible",
        "material": "basswood",
    },
    "carbon_fiber": {
        "height_mm": 6.35,
        "width_mm": 6.35,
        "kerf_spacing_mm": 0.0,  # No kerfs
        "kerf_depth_ratio": 0.0,
        "has_kerfs": False,
        "flexibility": "rigid",
        "material": "carbon_fiber",
    },
    "solid_lining": {
        "height_mm": 9.53,       # 3/8" - no kerfs, bent with heat
        "width_mm": 9.53,
        "kerf_spacing_mm": 0.0,  # No kerfs
        "kerf_depth_ratio": 0.0,
        "has_kerfs": False,
        "flexibility": "rigid",
        "material": "mahogany",
    },
}

# Body style defaults
BODY_STYLE_KERFING = {
    "dreadnought": "standard_lining",
    "om_000": "standard_lining",
    "parlor": "laminate_lining",
    "classical": "standard_lining",
    "jumbo": "reverse_kerfing",
    "archtop": "solid_lining",
    "concert": "standard_lining",
    "auditorium": "standard_lining",
}


@dataclass
class KerfingDimensions:
    """Dimensions for a single kerfing strip."""

    width_mm: float
    height_mm: float
    kerf_spacing_mm: float
    kerf_depth_mm: float
    material: str


@dataclass
class KerfingSpec:
    """Complete kerfing specification for a guitar body."""

    kerfing_type: str
    side_depth_mm: float
    top_kerfing: KerfingDimensions
    back_kerfing: KerfingDimensions
    total_side_depth_mm: float
    flexibility_note: str


def compute_kerfing_dimensions(
    kerfing_type: str,
    custom_height_mm: Optional[float] = None,
) -> KerfingDimensions:
    """
    Compute kerfing dimensions for a given type.

    Args:
        kerfing_type: Type of kerfing (standard_lining, reverse_kerfing, etc.)
        custom_height_mm: Optional override for height

    Returns:
        KerfingDimensions with width, height, spacing, depth, material
    """
    if kerfing_type not in KERFING_TYPES:
        # Default to standard lining
        kerfing_type = "standard_lining"

    spec = KERFING_TYPES[kerfing_type]

    height = custom_height_mm if custom_height_mm is not None else spec["height_mm"]
    kerf_depth = height * spec["kerf_depth_ratio"] if spec["has_kerfs"] else 0.0

    return KerfingDimensions(
        width_mm=spec["width_mm"],
        height_mm=height,
        kerf_spacing_mm=spec["kerf_spacing_mm"],
        kerf_depth_mm=round(kerf_depth, 2),
        material=spec["material"],
    )


def compute_kerfing_schedule(
    side_depth_mm: float,
    body_style: str,
    kerfing_type: str = "standard_lining",
) -> KerfingSpec:
    """
    Compute complete kerfing schedule for a guitar body.

    Args:
        side_depth_mm: Side depth from SIDE_PROFILE (without kerfing)
        body_style: Guitar body style (dreadnought, om_000, etc.)
        kerfing_type: Type of kerfing to use

    Returns:
        KerfingSpec with top/back kerfing dimensions and total depth
    """
    # Normalize inputs
    style_key = body_style.lower().replace("-", "_").replace(" ", "_")
    kerf_key = kerfing_type.lower().replace("-", "_").replace(" ", "_")

    # Get default kerfing type for body style if not specified
    if kerf_key not in KERFING_TYPES:
        kerf_key = BODY_STYLE_KERFING.get(style_key, "standard_lining")

    # Compute kerfing dimensions for top and back
    # Typically the same, but back can sometimes use stiffer kerfing
    top_kerfing = compute_kerfing_dimensions(kerf_key)
    back_kerfing = compute_kerfing_dimensions(kerf_key)

    # For archtop, back kerfing is often different
    if style_key == "archtop":
        back_kerfing = compute_kerfing_dimensions("solid_lining")

    # Compute total side depth
    total_depth = compute_total_side_depth(
        side_depth_mm=side_depth_mm,
        top_kerfing_height_mm=top_kerfing.height_mm,
        back_kerfing_height_mm=back_kerfing.height_mm,
    )

    # Get flexibility note
    spec = KERFING_TYPES.get(kerf_key, KERFING_TYPES["standard_lining"])
    flexibility_note = f"{spec['flexibility'].capitalize()} - suitable for {body_style}"

    return KerfingSpec(
        kerfing_type=kerf_key,
        side_depth_mm=side_depth_mm,
        top_kerfing=top_kerfing,
        back_kerfing=back_kerfing,
        total_side_depth_mm=total_depth,
        flexibility_note=flexibility_note,
    )


def compute_total_side_depth(
    side_depth_mm: float,
    top_kerfing_height_mm: float,
    back_kerfing_height_mm: float,
) -> float:
    """
    Compute total side depth including kerfing.

    Total depth = side depth + top kerfing height + back kerfing height

    Args:
        side_depth_mm: Raw side depth (bent wood only)
        top_kerfing_height_mm: Height of top kerfing strip
        back_kerfing_height_mm: Height of back kerfing strip

    Returns:
        Total side depth in mm
    """
    return round(side_depth_mm + top_kerfing_height_mm + back_kerfing_height_mm, 2)


def list_kerfing_types() -> list[str]:
    """Return list of supported kerfing types."""
    return list(KERFING_TYPES.keys())


def get_kerfing_type_info(kerfing_type: str) -> dict:
    """Get detailed info about a kerfing type."""
    if kerfing_type not in KERFING_TYPES:
        return {}
    return KERFING_TYPES[kerfing_type].copy()
