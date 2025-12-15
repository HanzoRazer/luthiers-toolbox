# N16.4 - Material-specific spindle/feed presets
#
# Extends the feed rule to include spindle RPM and per-pass depth limits.
# These values are tuned for typical rosette CNC operations with small
# router bits (1/8" or 3mm) in various tonewoods.

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from .cnc_feed_table import MaterialType


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
