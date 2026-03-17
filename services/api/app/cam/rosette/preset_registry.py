"""
Rosette Preset Registry — Lookup and validation for preset matrices.

Uses preset_definitions.PRESET_MATRICES; no preset data lives here.
"""

from __future__ import annotations

from typing import List, Optional

from .pattern_schemas import MatrixFormula
from .preset_definitions import PRESET_MATRICES

__all__ = [
    "get_preset",
    "list_preset_ids",
    "validate_preset_id",
]


def get_preset(preset_id: str) -> Optional[MatrixFormula]:
    """
    Get a preset matrix formula by id.

    Args:
        preset_id: Preset identifier (e.g. "classic_rope_5x9")

    Returns:
        MatrixFormula if found, else None
    """
    return PRESET_MATRICES.get(preset_id)


def list_preset_ids() -> List[str]:
    """Return all registered preset ids in stable order."""
    return list(PRESET_MATRICES.keys())


def validate_preset_id(preset_id: str) -> bool:
    """Return True if preset_id is registered."""
    return preset_id in PRESET_MATRICES
