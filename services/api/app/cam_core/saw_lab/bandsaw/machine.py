"""
Bandsaw machine model — blade path length, rim speed, and resaw feed heuristics.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Optional

# SFPM conversion: 1 m/s ≈ 196.85 surface feet per minute
_MPS_TO_SFPM = 196.85


@dataclass
class Bandsaw:
    """
    Two-wheel bandsaw with equal crown diameters and fixed wheel spacing.

    Blade length (closed loop):  π × D + 2 × C  where C is center-to-center distance.
    Cutting speed uses wheel diameter (same as rim speed on the drive wheel).
    """

    wheel_diameter_mm: float
    wheel_center_distance_mm: float
    kerf_mm: float = 0.6
    max_resaw_height_mm: Optional[float] = None
    name: str = ""

    def nominal_blade_length_mm(self) -> float:
        """Approximate blade length for ordering (two equal wheels)."""
        d = self.wheel_diameter_mm
        c = self.wheel_center_distance_mm
        if d <= 0 or c <= 0:
            return 0.0
        return math.pi * d + 2.0 * c

    def surface_speed_m_per_s(self, rpm: float) -> float:
        """Tangential speed at the wheel rim (m/s)."""
        if self.wheel_diameter_mm <= 0 or rpm <= 0:
            return 0.0
        d_m = self.wheel_diameter_mm / 1000.0
        return math.pi * d_m * rpm / 60.0

    def surface_speed_m_per_min(self, rpm: float) -> float:
        """Rim speed in m/min (common in some CAM tables)."""
        return self.surface_speed_m_per_s(rpm) * 60.0

    def surface_speed_sfpm(self, rpm: float) -> float:
        """Surface feet per minute at the rim."""
        return self.surface_speed_m_per_s(rpm) * _MPS_TO_SFPM

    def rpm_for_surface_speed_m_per_s(self, target_m_per_s: float) -> float:
        """Solve RPM for a target rim speed (m/s)."""
        d_m = self.wheel_diameter_mm / 1000.0
        if d_m <= 0 or target_m_per_s <= 0:
            return 0.0
        return (target_m_per_s * 60.0) / (math.pi * d_m)

    def rpm_for_sfpm(self, target_sfpm: float) -> float:
        """Solve RPM for a target SFPM."""
        target_m_s = target_sfpm / _MPS_TO_SFPM
        return self.rpm_for_surface_speed_m_per_s(target_m_s)

    def resaw_feed_mm_s(
        self,
        stock_thickness_mm: float,
        *,
        sfpm: float,
        aggressive: float = 0.5,
    ) -> float:
        """
        Rough feed-rate hint for resaw (mm/s along cut), not a guarantee.

        Heuristic scales with thickness and stays conservative at low SFPM.
        `aggressive` in (0,1]: 1.0 = faster (experienced operator / sharp blade).
        """
        if stock_thickness_mm <= 0 or sfpm <= 0:
            return 0.0
        a = max(0.05, min(1.0, aggressive))
        base_ipm = (sfpm / 4000.0) * (12.0 / max(stock_thickness_mm / 25.4, 0.25)) * 8.0 * a
        ipm = max(0.5, min(base_ipm, 120.0))
        mm_s = ipm * 25.4 / 60.0
        return round(mm_s, 3)

    def to_dict(self) -> dict[str, Any]:
        """Serializable snapshot."""
        return {
            "kind": "bandsaw",
            "name": self.name,
            "wheel_diameter_mm": self.wheel_diameter_mm,
            "wheel_center_distance_mm": self.wheel_center_distance_mm,
            "kerf_mm": self.kerf_mm,
            "max_resaw_height_mm": self.max_resaw_height_mm,
            "nominal_blade_length_mm": round(self.nominal_blade_length_mm(), 3),
        }

    @classmethod
    def from_wheel_inches(cls, diameter_in: float, center_distance_in: float, **kw: Any) -> "Bandsaw":
        """Build from inch dimensions (wheel OD and center distance)."""
        return cls(
            wheel_diameter_mm=diameter_in * 25.4,
            wheel_center_distance_mm=center_distance_in * 25.4,
            **kw,
        )
