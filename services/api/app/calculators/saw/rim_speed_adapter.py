"""
Rim Speed Adapter (Saw Blades)

Calculates surface velocity at the blade edge.

MODEL NOTES:
- Critical for heat generation and cut quality
- Most wood blades: 3000-5000 SFPM (15-25 m/s)
- Carbide-tipped: can go higher
- Exceeding limits causes premature wear and burning

Formula:
    rim_speed_m_s = π * diameter_m * rpm / 60
    rim_speed_sfpm = rim_speed_m_s * 196.85
"""
from __future__ import annotations

import math
from dataclasses import dataclass

# Try to import from Saw Lab if available
try:
    from ...saw_lab.calculators.rim_speed import (
        compute_rim_speed as _saw_lab_rim_speed,
    )
    _HAS_SAW_LAB = True
except ImportError:
    _HAS_SAW_LAB = False


@dataclass
class SawRimSpeedResult:
    """Result from saw rim speed calculation."""
    speed_m_per_s: float
    speed_sfpm: float  # Surface feet per minute (US convention)
    within_limits: bool
    max_speed_m_per_s: float
    message: str


def compute_saw_rim_speed(
    blade_diameter_mm: float,
    rpm: float,
    *,
    max_speed_m_per_s: float = 60.0,  # ~12,000 SFPM - carbide limit
) -> SawRimSpeedResult:
    """
    Calculate rim speed (surface velocity) for a saw blade.

    Args:
        blade_diameter_mm: Blade diameter in mm
        rpm: Blade RPM
        max_speed_m_per_s: Maximum safe rim speed (default 60 m/s)

    Returns:
        SawRimSpeedResult with speed and limit check
    """
    if blade_diameter_mm <= 0 or rpm <= 0:
        return SawRimSpeedResult(
            speed_m_per_s=0.0,
            speed_sfpm=0.0,
            within_limits=False,
            max_speed_m_per_s=max_speed_m_per_s,
            message="Invalid blade diameter or RPM",
        )

    # Delegate to Saw Lab if available
    if _HAS_SAW_LAB:
        speed_m_s = _saw_lab_rim_speed(blade_diameter_mm, rpm)
    else:
        # Direct calculation: v = π * d * rpm / 60
        diameter_m = blade_diameter_mm / 1000.0
        speed_m_s = math.pi * diameter_m * rpm / 60.0

    # Convert to SFPM (surface feet per minute)
    speed_sfpm = speed_m_s * 196.85

    within_limits = speed_m_s <= max_speed_m_per_s

    if not within_limits:
        message = f"Rim speed {speed_m_s:.1f} m/s exceeds limit {max_speed_m_per_s} m/s - REDUCE RPM"
    elif speed_m_s < 10.0:
        message = f"Rim speed low ({speed_m_s:.1f} m/s) - may cause rough cut"
    else:
        message = f"Rim speed OK ({speed_m_s:.1f} m/s, {speed_sfpm:.0f} SFPM)"

    return SawRimSpeedResult(
        speed_m_per_s=speed_m_s,
        speed_sfpm=speed_sfpm,
        within_limits=within_limits,
        max_speed_m_per_s=max_speed_m_per_s,
        message=message,
    )
