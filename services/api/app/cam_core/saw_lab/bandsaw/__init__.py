"""Bandsaw machine model, blade library, and physics."""

from .blade_spec import BandsawBladeSpec, get_blade_by_id, load_blade_library
from .machine import Bandsaw
from .physics import (
    compute_blade_tension,
    compute_drift_angle,
    compute_feed_rate,
    plan_curve_cut,
    plan_resaw_cut,
    validate_resaw_setup,
)

__all__ = [
    "Bandsaw",
    "BandsawBladeSpec",
    "load_blade_library",
    "get_blade_by_id",
    "compute_blade_tension",
    "compute_drift_angle",
    "compute_feed_rate",
    "validate_resaw_setup",
    "plan_curve_cut",
    "plan_resaw_cut",
]
