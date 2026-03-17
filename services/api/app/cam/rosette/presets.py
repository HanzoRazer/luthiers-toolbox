"""
Rosette Preset Matrices — Thin re-export shim.

Preset data lives in preset_definitions; registry lookup in preset_registry.
This module keeps existing imports working (e.g. from .presets import PRESET_MATRICES).
"""

from __future__ import annotations

from .preset_definitions import PRESET_MATRICES
from .preset_registry import get_preset, list_preset_ids, validate_preset_id

__all__ = [
    "PRESET_MATRICES",
    "get_preset",
    "list_preset_ids",
    "validate_preset_id",
]
