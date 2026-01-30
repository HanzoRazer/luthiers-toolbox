"""Feeds and speeds helpers for CAM-Core."""

from .calculator import calculate_feed_plan, resolve_feeds_speeds
from .chipload_calc import calc_chipload_mm
from .heat_model import estimate_heat_rating
from .deflection_model import estimate_deflection_mm
from .presets_db import (
    PRESETS_DB,
    load_presets,
    get_preset,
    list_materials,
    list_presets_for_material,
)
from .schemas import SpeedFeedPreset

__all__ = [
    "calculate_feed_plan",
    "resolve_feeds_speeds",
    "calc_chipload_mm",
    "estimate_heat_rating",
    "estimate_deflection_mm",
    "PRESETS_DB",
    "load_presets",
    "get_preset",
    "list_materials",
    "list_presets_for_material",
    "SpeedFeedPreset",
]
