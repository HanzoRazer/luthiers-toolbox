# Patch N14.0 - Blade and router bit models (skeleton)

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


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


class ToolMode(str, Enum):
    SAW = "saw"
    ROUTER = "router"
