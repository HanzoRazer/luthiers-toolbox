# N16.4 - Material-specific spindle/feed presets
# Rosette Consolidation: absorbed cnc_feed_table.py and cnc_blade_model.py
#
# Extends the feed rule to include spindle RPM and per-pass depth limits.
# These values are tuned for typical rosette CNC operations with small
# router bits (1/8" or 3mm) in various tonewoods.

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict


# ─────────────────────────────────────────────────────────────────────────────
# Enums (absorbed from cnc_feed_table.py and cnc_blade_model.py)
# ─────────────────────────────────────────────────────────────────────────────

class MaterialType(str, Enum):
    HARDWOOD = "hardwood"
    SOFTWOOD = "softwood"
    COMPOSITE = "composite"


class ToolMode(str, Enum):
    SAW = "saw"
    ROUTER = "router"


# ─────────────────────────────────────────────────────────────────────────────
# Tool Models (absorbed from cnc_blade_model.py)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class SawBladeModel:
    """
    Simplified saw blade representation.

    Fields here are sufficient for later N14.x kerf physics and safety.
    """
    name: str
    kerf_mm: float
    tooth_count: int
    blade_radius_mm: float
    tooth_angle_deg: float = 0.0
    runout_mm: float = 0.05  # wobble tolerance


@dataclass
class RouterBitModel:
    """
    Simplified router bit representation.
    """
    name: str
    diameter_mm: float
    flute_count: int
    max_rpm: int
    recommended_chipload_mm: float = 0.02


# ─────────────────────────────────────────────────────────────────────────────
# Basic Feed Rules (absorbed from cnc_feed_table.py)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class BasicFeedRule:
    """Basic feed rule without spindle/Z-step parameters."""
    material: MaterialType
    feed_min_mm_per_min: float
    feed_max_mm_per_min: float
    feed_recommend_mm_per_min: float


HARDWOOD_RULE = BasicFeedRule(
    material=MaterialType.HARDWOOD,
    feed_min_mm_per_min=300.0,
    feed_max_mm_per_min=900.0,
    feed_recommend_mm_per_min=500.0,
)

SOFTWOOD_RULE = BasicFeedRule(
    material=MaterialType.SOFTWOOD,
    feed_min_mm_per_min=500.0,
    feed_max_mm_per_min=1500.0,
    feed_recommend_mm_per_min=800.0,
)

COMPOSITE_RULE = BasicFeedRule(
    material=MaterialType.COMPOSITE,
    feed_min_mm_per_min=200.0,
    feed_max_mm_per_min=600.0,
    feed_recommend_mm_per_min=400.0,
)


def select_basic_feed_rule(material: MaterialType) -> BasicFeedRule:
    """
    Return the basic feed rule for a given material type.

    N14.x can later add a database or config-driven table. For now,
    this is a fixed mapping.
    """
    if material == MaterialType.HARDWOOD:
        return HARDWOOD_RULE
    if material == MaterialType.SOFTWOOD:
        return SOFTWOOD_RULE
    if material == MaterialType.COMPOSITE:
        return COMPOSITE_RULE
    # default fallback
    return HARDWOOD_RULE


# ─────────────────────────────────────────────────────────────────────────────
# Extended Feed Rules (N16.4 - with spindle RPM and Z-step)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class FeedRule:
    material: MaterialType
    feed_recommend_mm_per_min: float
    feed_max_mm_per_min: float
    spindle_rpm: int
    max_z_step_mm: float  # per-pass depth limit


# Simple defaults; tune later as you gain experience
_MATERIAL_FEED_RULES: Dict[MaterialType, FeedRule] = {}


def _init_rules() -> None:
    """Initialize material-specific feed rules."""
    # Hardwood (maple, oak, etc.) - conservative feeds, moderate spindle
    _MATERIAL_FEED_RULES[MaterialType.HARDWOOD] = FeedRule(
        material=MaterialType.HARDWOOD,
        feed_recommend_mm_per_min=800.0,
        feed_max_mm_per_min=1200.0,
        spindle_rpm=16000,
        max_z_step_mm=0.5,
    )

    # Softwood (pine, cedar, etc.) - faster feeds, higher spindle
    _MATERIAL_FEED_RULES[MaterialType.SOFTWOOD] = FeedRule(
        material=MaterialType.SOFTWOOD,
        feed_recommend_mm_per_min=900.0,
        feed_max_mm_per_min=1300.0,
        spindle_rpm=17000,
        max_z_step_mm=0.6,
    )

    # Composite (plywood, MDF, etc.) - slower feeds, lower spindle
    _MATERIAL_FEED_RULES[MaterialType.COMPOSITE] = FeedRule(
        material=MaterialType.COMPOSITE,
        feed_recommend_mm_per_min=600.0,
        feed_max_mm_per_min=900.0,
        spindle_rpm=14000,
        max_z_step_mm=0.4,
    )


def select_feed_rule(material: MaterialType) -> FeedRule:
    """
    Return the feed rule for a given material type.

    Includes spindle RPM and max Z step per pass for N16.4+.
    """
    if not _MATERIAL_FEED_RULES:
        _init_rules()
    
    # Return specific rule or generic fallback
    if material in _MATERIAL_FEED_RULES:
        return _MATERIAL_FEED_RULES[material]
    
    # Generic fallback for unknown materials
    return FeedRule(
        material=material,
        feed_recommend_mm_per_min=800.0,
        feed_max_mm_per_min=1200.0,
        spindle_rpm=15000,
        max_z_step_mm=0.6,
    )
