"""
soundhole_climate.py — Climate and Environmental Corrections
=============================================================
DECOMP-002 Phase 4: Extracted from soundhole_calc.py

This module provides climate and environmental factors for soundhole design:
- Humidity-adjusted ring width calculations
- Seasonal wood movement considerations
- Climate zone classifications
- Temperature and humidity effects on structural requirements

Note: This module focuses on structural/construction implications of climate,
not acoustic corrections (speed of sound, air density adjustments). The base
acoustic calculations in soundhole_physics.py use standard conditions (20°C).

For wood movement physics, see wood_movement_calc.py.
For air property corrections, see plate_design/calibration.py.

Extracted from:
  services/api/app/calculators/soundhole_calc.py
  Lines 1159-1267 (climate zones and humidity-adjusted ring width)
"""

from __future__ import annotations

from typing import Dict, List

# ── Climate Zone Definitions ──────────────────────────────────────────────────

# Climate zones by representative annual RH swing (high - low)
# Used to adjust ring width recommendation based on seasonal humidity variation
CLIMATE_ZONES: Dict[str, Dict] = {
    "arid": {
        "label": "Arid / Desert",
        "rh_swing": 25,
        "example": "Tucson AZ, Denver CO"
    },
    "temperate": {
        "label": "Temperate",
        "rh_swing": 35,
        "example": "Seattle WA, Portland OR"
    },
    "continental": {
        "label": "Continental",
        "rh_swing": 45,
        "example": "Chicago IL, Minneapolis MN"
    },
    "humid": {
        "label": "Humid Subtropical",
        "rh_swing": 55,
        "example": "Houston TX, New Orleans LA"
    },
    "tropical": {
        "label": "Tropical / Coastal",
        "rh_swing": 65,
        "example": "Miami FL, Honolulu HI"
    },
}


# ── Climate Adjustment Constants ──────────────────────────────────────────────

# Ring width addition per 10% RH swing above the 35% base (temperate climate)
# Based on: Δdim = plate_width × MC_change_pct × grain_factor / 100
# where MC_change_pct ≈ RH_swing × 0.18 (simplified EMC relationship)
# and grain_factor ≈ 0.003 (radial movement for spruce)
# For 400mm wide plate: Δ ≈ 400 × (swing × 0.18) × 0.003 = 0.216 × swing mm
# But we only need the ring to accommodate the edge movement, not full plate:
# Edge zone ≈ 15mm wide → Δedge ≈ Δ × (15/400) = negligible
# The real driver is shear stress at the glue line of the ring itself.
# Empirical recommendation: add 0.5mm to min_ring per 10% RH swing above base 35%
RING_WIDTH_HUMIDITY_ADDITION_PER_10PCT_SWING = 0.5  # mm

# Standard ring width constants (from soundhole_calc.py)
RING_WIDTH_RADIUS_FRACTION: float = 0.15  # min ring = 15% of soundhole radius
RING_WIDTH_ABSOLUTE_MIN_MM: float = 6.0   # hard floor regardless of hole size


# ── Climate-Adjusted Ring Width Functions ─────────────────────────────────────

def get_ring_width_humidity_note(
    soundhole_radius_mm: float,
    ring_width_mm: float,
    climate_key: str = "temperate",
) -> Dict:
    """
    Seasonal humidity note for ring width check.

    Extends check_ring_width() with climate-specific guidance.
    The standard 6mm absolute minimum assumes temperate conditions (~35% RH swing).
    High-humidity-swing climates (Houston: 50-55% swing) need larger rings.

    Args:
        soundhole_radius_mm: Soundhole radius (mm)
        ring_width_mm:       Actual ring width at narrowest point (mm)
        climate_key:         Key from CLIMATE_ZONES (default "temperate")

    Returns:
        Dict with adjusted_min_mm, climate_note, and seasonal_guidance
    """
    climate = CLIMATE_ZONES.get(climate_key, CLIMATE_ZONES["temperate"])
    swing = climate["rh_swing"]

    # Base minimum (from check_ring_width)
    base_min = max(
        soundhole_radius_mm * RING_WIDTH_RADIUS_FRACTION,
        RING_WIDTH_ABSOLUTE_MIN_MM
    )

    # Climate adjustment — addition above base for high-swing environments
    swing_above_base = max(0, swing - 35)
    humidity_addition = (
        (swing_above_base / 10.0) * RING_WIDTH_HUMIDITY_ADDITION_PER_10PCT_SWING
    )
    adjusted_min = base_min + humidity_addition

    if ring_width_mm >= adjusted_min * 1.3:
        seasonal_status = "adequate"
        seasonal_note = (
            f"Ring width {ring_width_mm:.1f}mm is adequate for {climate['label']} "
            f"conditions (~{swing}% annual RH swing)."
        )
    elif ring_width_mm >= adjusted_min:
        seasonal_status = "marginal"
        seasonal_note = (
            f"Ring width {ring_width_mm:.1f}mm meets adjusted minimum "
            f"({adjusted_min:.1f}mm) for {climate['label']} conditions "
            f"(~{swing}% RH swing) but is marginal. Consider 12–15mm if possible."
        )
    else:
        seasonal_status = "insufficient"
        seasonal_note = (
            f"Ring width {ring_width_mm:.1f}mm is below the climate-adjusted "
            f"minimum of {adjusted_min:.1f}mm for {climate['label']} conditions "
            f"(~{swing}% annual RH swing, e.g. {climate['example']}). "
            f"Tops in this climate move significantly with seasonal humidity — "
            f"thin rings at the soundhole edge are the most common crack initiation "
            f"point. Reduce hole diameter or move hole toward body center."
        )

    # Full humidity guidance text
    # MC change ≈ swing × 0.18%; radial movement ≈ 0.2% per 1% MC change
    plate_width = soundhole_radius_mm * 6  # rough estimate of plate width from hole size
    estimated_movement_mm = plate_width * (swing * 0.18 * 0.0002)

    return {
        "climate": climate["label"],
        "rh_swing_pct": swing,
        "base_min_mm": round(base_min, 1),
        "humidity_addition_mm": round(humidity_addition, 1),
        "adjusted_min_mm": round(adjusted_min, 1),
        "seasonal_status": seasonal_status,
        "seasonal_note": seasonal_note,
        "estimated_seasonal_movement_mm": round(estimated_movement_mm, 1),
        "guidance": (
            f"Annual humidity swing ~{swing}%. "
            f"For a top ~{plate_width:.0f}mm wide this creates an estimated "
            f"seasonal movement of ~{estimated_movement_mm:.1f}mm across the grain. "
            f"Recommend ring width ≥ {adjusted_min:.0f}mm for this climate zone."
        ),
    }


def list_climate_zones() -> List[Dict]:
    """Return list of climate zones for UI dropdown."""
    return [{"key": k, **v} for k, v in CLIMATE_ZONES.items()]


def get_climate_zone(climate_key: str) -> Dict:
    """Get climate zone info by key."""
    return CLIMATE_ZONES.get(climate_key, CLIMATE_ZONES["temperate"])


def estimate_seasonal_movement(
    plate_width_mm: float,
    climate_key: str = "temperate",
) -> Dict:
    """
    Estimate seasonal wood movement for a given plate width and climate.

    Uses simplified EMC relationship: MC_change ≈ RH_swing × 0.18%
    Radial movement coefficient ≈ 0.002 (0.2% per 1% MC change for spruce)

    Args:
        plate_width_mm: Plate width across grain (mm)
        climate_key:    Key from CLIMATE_ZONES

    Returns:
        Dict with movement estimate and climate info
    """
    climate = CLIMATE_ZONES.get(climate_key, CLIMATE_ZONES["temperate"])
    swing = climate["rh_swing"]

    # Simplified movement calculation
    # Full formula in wood_movement_calc.py
    mc_change_pct = swing * 0.18  # MC change from RH swing
    radial_coeff = 0.0002         # radial shrinkage coefficient for spruce
    movement_mm = plate_width_mm * mc_change_pct * radial_coeff

    return {
        "climate": climate["label"],
        "climate_key": climate_key,
        "rh_swing_pct": swing,
        "plate_width_mm": plate_width_mm,
        "estimated_movement_mm": round(movement_mm, 2),
        "mc_change_pct": round(mc_change_pct, 2),
        "note": (
            f"In {climate['label']} conditions ({swing}% RH swing), "
            f"a {plate_width_mm:.0f}mm wide plate moves ~{movement_mm:.1f}mm "
            f"across grain seasonally. Use wood_movement_calc.py for "
            f"species-specific calculations."
        ),
    }


# ── Notes on Acoustic Climate Corrections ─────────────────────────────────────
"""
FUTURE ENHANCEMENT: Temperature and humidity corrections for acoustic properties

Currently, soundhole_physics.py uses C_AIR = 343.0 m/s (20°C standard conditions).
For more accurate predictions across temperature/humidity ranges, consider:

1. Temperature correction for speed of sound:
   c(T) = 331.3 + 0.606 × T_celsius
   Example: 0°C → 331.3 m/s, 20°C → 343.4 m/s, 30°C → 349.5 m/s

2. Humidity correction for air density:
   ρ_humid = ρ_dry × (1 - 0.378 × e/P)
   where e = water vapor pressure, P = total pressure
   Example: 20°C, 50% RH → ρ ≈ 1.19 kg/m³ (vs 1.20 dry)

3. Combined effect on Helmholtz frequency:
   f_H ∝ c / √ρ (from Helmholtz formula)

   Temperature dominates (c increases ~0.18% per °C)
   Humidity has minor effect (ρ decreases slightly with RH increase)

   Net effect over typical range (10-30°C, 30-70% RH): ~±3-5 Hz
   This is within measurement uncertainty for most luthier applications.

4. Altitude correction:
   Air density decreases with altitude: ρ(h) = ρ₀ × e^(-h/H)
   where H ≈ 8500m (scale height)
   Example: Denver (1600m) → ρ ≈ 1.00 kg/m³ (vs 1.20 sea level)
   Speed of sound nearly constant with altitude (temperature-dependent)
   f_H increases ~10% at Denver altitude

Implementation location:
  Add to soundhole_physics.py as optional parameters:
  - compute_helmholtz_multiport(temp_celsius=20.0, rh_pct=50.0, altitude_m=0.0)
  - adjust_speed_of_sound(temp_celsius) -> float
  - adjust_air_density(temp_celsius, rh_pct, altitude_m) -> float

References:
  - Beranek, "Acoustics" (1954), Ch. 4
  - Fletcher & Rossing, "Physics of Musical Instruments" (1998), Ch. 9
  - NIST air properties tables
"""
