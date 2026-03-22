# services/api/app/calculators/neck_block_calc.py
"""
Neck and tail block sizing — GEOMETRY-005 (router + unit-test API).

This module exposes the stable `compute_neck_block` / `compute_tail_block` /
`compute_both_blocks` surface used by FastAPI and tests.

For first-principles shear / glue-area analysis (string tension, joint types),
see `neck_block_physics.py`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


# Heel width + kerfing / margin (6 mm each side) — matches legacy GEOMETRY-005 tests
NECK_BLOCK_SIDE_MARGIN_MM: float = 12.0

# Typical neck-block depth (along body axis) for dovetail / bolt-on pockets
DEFAULT_NECK_BLOCK_DEPTH_MM: float = 65.0

# Tail block depth: end pin + structural margin (GEOMETRY-005 convention)
DEFAULT_TAIL_BLOCK_DEPTH_MM: float = 28.0


@dataclass
class BlockSpec:
    """Single neck or tail block specification for API responses."""

    block_type: str  # "neck" | "tail"
    height_mm: float
    width_mm: float
    depth_mm: float
    material: str
    grain_orientation: str
    gate: str
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        return {
            "block_type": self.block_type,
            "height_mm": self.height_mm,
            "width_mm": self.width_mm,
            "depth_mm": self.depth_mm,
            "material": self.material,
            "grain_orientation": self.grain_orientation,
            "gate": self.gate,
            "notes": list(self.notes),
        }


# Defaults when optional dimensions are omitted (typical steel-string acoustics)
_BODY_STYLE_DEFAULTS: Dict[str, Dict[str, float]] = {
    "dreadnought": {
        "heel_width_mm": 56.0,
        "side_depth_neck_mm": 100.0,
        "side_depth_tail_mm": 105.0,
    },
    "om_000": {
        "heel_width_mm": 56.0,
        "side_depth_neck_mm": 95.0,
        "side_depth_tail_mm": 100.0,
    },
    "parlor": {
        "heel_width_mm": 52.0,
        "side_depth_neck_mm": 95.0,
        "side_depth_tail_mm": 90.0,
    },
    "classical": {
        "heel_width_mm": 52.0,
        "side_depth_neck_mm": 92.0,
        "side_depth_tail_mm": 96.0,
    },
    "archtop": {
        "heel_width_mm": 54.0,
        "side_depth_neck_mm": 98.0,
        "side_depth_tail_mm": 102.0,
    },
    "jumbo": {
        "heel_width_mm": 58.0,
        "side_depth_neck_mm": 105.0,
        "side_depth_tail_mm": 110.0,
    },
    "concert": {
        "heel_width_mm": 54.0,
        "side_depth_neck_mm": 98.0,
        "side_depth_tail_mm": 100.0,
    },
}

# Tail block width (mm, treble–bass) by style — dreadnought wider than parlor (tests)
_TAIL_BLOCK_WIDTH_MM: Dict[str, float] = {
    "dreadnought": 72.0,
    "om_000": 68.0,
    "parlor": 52.0,
    "classical": 54.0,
    "archtop": 60.0,
    "jumbo": 76.0,
    "concert": 58.0,
}


def _normalize_body_style(body_style: str) -> str:
    key = body_style.strip().lower().replace("-", "_")
    if key in _BODY_STYLE_DEFAULTS:
        return key
    # tolerate synonyms
    aliases = {
        "om": "om_000",
        "orchestra": "om_000",
        "000": "om_000",
    }
    return aliases.get(key, "dreadnought")


def _neck_gate(height_mm: float, width_mm: float) -> str:
    """GREEN / YELLOW / RED heuristic aligned with unit tests."""
    if height_mm < 85.0 or width_mm < 60.0:
        return "RED"
    if height_mm >= 95.0 and width_mm >= 65.0:
        return "GREEN"
    return "YELLOW"


def _tail_gate(height_mm: float, width_mm: float) -> str:
    if height_mm < 80.0 or width_mm < 45.0:
        return "RED"
    if height_mm >= 90.0 and width_mm >= 50.0:
        return "GREEN"
    return "YELLOW"


def compute_neck_block(
    *,
    side_depth_at_neck_mm: float,
    neck_heel_width_mm: float,
    body_style: str = "dreadnought",
    material: str = "mahogany",
    depth_mm: float = DEFAULT_NECK_BLOCK_DEPTH_MM,
) -> BlockSpec:
    """Size neck block from side depth and heel width (GEOMETRY-005)."""
    _ = _normalize_body_style(body_style)
    width_mm = neck_heel_width_mm + NECK_BLOCK_SIDE_MARGIN_MM
    height_mm = side_depth_at_neck_mm
    gate = _neck_gate(height_mm, width_mm)
    notes: List[str] = [
        f"Width = neck heel ({neck_heel_width_mm:.1f} mm) + {NECK_BLOCK_SIDE_MARGIN_MM:.0f} mm margin.",
        "Grain vertical for bending strength across the joint.",
    ]
    return BlockSpec(
        block_type="neck",
        height_mm=height_mm,
        width_mm=width_mm,
        depth_mm=depth_mm,
        material=material,
        grain_orientation="vertical",
        gate=gate,
        notes=notes,
    )


def compute_tail_block(
    side_depth_at_tail_mm: float,
    body_style: str = "dreadnought",
    *,
    material: str = "mahogany",
    depth_mm: float = DEFAULT_TAIL_BLOCK_DEPTH_MM,
) -> BlockSpec:
    """Size tail block from side depth at tail and body style."""
    style = _normalize_body_style(body_style)
    width_mm = _TAIL_BLOCK_WIDTH_MM.get(style, _TAIL_BLOCK_WIDTH_MM["dreadnought"])
    height_mm = side_depth_at_tail_mm
    gate = _tail_gate(height_mm, width_mm)
    notes: List[str] = [
        "Tail block is geometry-driven; width scales with body style.",
        "Grain horizontal for end-pin support.",
    ]
    return BlockSpec(
        block_type="tail",
        height_mm=height_mm,
        width_mm=width_mm,
        depth_mm=depth_mm,
        material=material,
        grain_orientation="horizontal",
        gate=gate,
        notes=notes,
    )


def compute_both_blocks(
    *,
    body_style: str = "dreadnought",
    neck_heel_width_mm: Optional[float] = None,
    side_depth_at_neck_mm: Optional[float] = None,
    side_depth_at_tail_mm: Optional[float] = None,
    material: str = "mahogany",
) -> Dict[str, BlockSpec]:
    """Neck + tail blocks for POST /api/instrument/blocks."""
    style = _normalize_body_style(body_style)
    defaults = _BODY_STYLE_DEFAULTS.get(style, _BODY_STYLE_DEFAULTS["dreadnought"])
    heel = float(neck_heel_width_mm if neck_heel_width_mm is not None else defaults["heel_width_mm"])
    sd_neck = float(side_depth_at_neck_mm if side_depth_at_neck_mm is not None else defaults["side_depth_neck_mm"])
    sd_tail = float(side_depth_at_tail_mm if side_depth_at_tail_mm is not None else defaults["side_depth_tail_mm"])

    neck = compute_neck_block(
        side_depth_at_neck_mm=sd_neck,
        neck_heel_width_mm=heel,
        body_style=style,
        material=material,
    )
    tail = compute_tail_block(sd_tail, style, material=material)
    return {"neck": neck, "tail": tail}


def list_body_styles() -> List[str]:
    """Supported body_style keys for block presets."""
    return sorted(_BODY_STYLE_DEFAULTS.keys())


__all__ = [
    "BlockSpec",
    "compute_both_blocks",
    "compute_neck_block",
    "compute_tail_block",
    "list_body_styles",
]


def get_default_side_depths(body_style: str = "dreadnought") -> Dict[str, float]:
    """
    Return default side depths (mm) for common acoustic body styles.
    Used by instrument_geometry_router for block calculations.
    """
    DEFAULTS = {
        "dreadnought": {"upper_bout": 100.0, "waist": 100.0, "lower_bout": 115.0},
        "om": {"upper_bout": 90.0, "waist": 85.0, "lower_bout": 100.0},
        "parlor": {"upper_bout": 85.0, "waist": 80.0, "lower_bout": 95.0},
        "jumbo": {"upper_bout": 105.0, "waist": 105.0, "lower_bout": 120.0},
        "classical": {"upper_bout": 95.0, "waist": 90.0, "lower_bout": 100.0},
        "concert": {"upper_bout": 90.0, "waist": 85.0, "lower_bout": 100.0},
        "auditorium": {"upper_bout": 95.0, "waist": 92.0, "lower_bout": 105.0},
    }
    key = _normalize_body_style(body_style)
    return DEFAULTS.get(key, DEFAULTS["dreadnought"])
