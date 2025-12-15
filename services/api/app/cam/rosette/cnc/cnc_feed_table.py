# Patch N14.0 - Feed rule skeleton

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class MaterialType(str, Enum):
    HARDWOOD = "hardwood"
    SOFTWOOD = "softwood"
    COMPOSITE = "composite"


@dataclass
class FeedRule:
    material: MaterialType
    feed_min_mm_per_min: float
    feed_max_mm_per_min: float
    feed_recommend_mm_per_min: float


HARDWOOD_RULE = FeedRule(
    material=MaterialType.HARDWOOD,
    feed_min_mm_per_min=300.0,
    feed_max_mm_per_min=900.0,
    feed_recommend_mm_per_min=500.0,
)

SOFTWOOD_RULE = FeedRule(
    material=MaterialType.SOFTWOOD,
    feed_min_mm_per_min=500.0,
    feed_max_mm_per_min=1500.0,
    feed_recommend_mm_per_min=800.0,
)

COMPOSITE_RULE = FeedRule(
    material=MaterialType.COMPOSITE,
    feed_min_mm_per_min=200.0,
    feed_max_mm_per_min=600.0,
    feed_recommend_mm_per_min=400.0,
)


def select_feed_rule(material: MaterialType) -> FeedRule:
    """
    Return the feed rule for a given material type.

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
