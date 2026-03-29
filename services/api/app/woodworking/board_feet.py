"""
Board feet, wood weight, and seasonal movement (wraps wood_movement_calc only).

Coefficients for movement come exclusively from app.calculators.wood_movement_calc.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict

from app.calculators.wood_movement_calc import (
    TANGENTIAL_SHRINKAGE,
    compute_wood_movement,
)


# lb/ft³ — keyed to match wood_movement_calc species keys where possible
_DENSITY_LB_PER_FT3: Dict[str, float] = {
    "sitka_spruce": 28.0,
    "engelmann_spruce": 29.0,
    "red_spruce": 30.0,
    "western_red_cedar": 23.0,
    "port_orford_cedar": 29.0,
    "redwood": 28.0,
    "indian_rosewood": 52.0,
    "brazilian_rosewood": 54.0,
    "honduran_mahogany": 37.0,
    "african_mahogany": 35.0,
    "sapele": 36.0,
    "maple": 44.0,
    "walnut": 38.0,
    "koa": 40.0,
    "cocobolo": 54.0,
    "bubinga": 42.0,
    "ovangkol": 38.0,
    "ziricote": 50.0,
    "spruce": 28.0,
    "cedar": 23.0,
    "rosewood": 52.0,
    "mahogany": 37.0,
}


def _species_key(species: str) -> str:
    return species.lower().replace(" ", "_").replace("-", "_")


def board_feet(
    thickness_in: float,
    width_in: float,
    length_in: float,
    quantity: int = 1,
) -> float:
    """
    Board feet: (T × W × L) / 144 × quantity (all dimensions in inches).
    """
    if quantity < 0:
        quantity = 0
    return (thickness_in * width_in * length_in / 144.0) * float(quantity)


def wood_weight(
    thickness_in: float,
    width_in: float,
    length_in: float,
    species: str,
) -> Dict[str, Any]:
    """
    Weight from board volume (ft³) × density (lb/ft³).

    Returns mass in lb and kg plus density used.
    """
    key = _species_key(species)
    density_lb_ft3 = _DENSITY_LB_PER_FT3.get(key)
    if density_lb_ft3 is None:
        density_lb_ft3 = 40.0  # generic hardwood nominal
        note = f"Unknown species '{species}'; using nominal 40 lb/ft³."
    else:
        note = ""

    vol_ft3 = (thickness_in * width_in * length_in) / 1728.0
    weight_lb = vol_ft3 * density_lb_ft3
    weight_kg = weight_lb * 0.45359237
    density_kg_m3 = density_lb_ft3 * 16.018463

    return {
        "species_key": key,
        "volume_ft3": round(vol_ft3, 6),
        "density_lb_per_ft3": density_lb_ft3,
        "density_kg_per_m3": round(density_kg_m3, 2),
        "weight_lb": round(weight_lb, 4),
        "weight_kg": round(weight_kg, 4),
        "note": note,
    }


def seasonal_movement(
    dimension_mm: float,
    species: str,
    rh_from: float,
    rh_to: float,
    grain_direction: str = "tangential",
) -> Dict[str, Any]:
    """
    Seasonal / humidity movement using ``compute_wood_movement`` — no duplicated coefficients.

    Raises ValueError for unknown species (same as wood_movement_calc).
    """
    spec = compute_wood_movement(
        species=species,
        dimension_mm=dimension_mm,
        rh_from=rh_from,
        rh_to=rh_to,
        grain_direction=grain_direction,
    )
    return asdict(spec)


def movement_budget_for_species(
    species: str,
    grain_direction: str = "tangential",
) -> Dict[str, Any]:
    """
    Expose tangential shrinkage coefficient from registry (read-only) for UI/budget tools.

    Does not duplicate numeric tables — uses TANGENTIAL_SHRINKAGE from wood_movement_calc.
    """
    key = _species_key(species)
    if key not in TANGENTIAL_SHRINKAGE:
        raise ValueError(
            f"Unknown species: '{species}'. Supported: {list(TANGENTIAL_SHRINKAGE.keys())}"
        )
    coeff = TANGENTIAL_SHRINKAGE[key]
    if grain_direction.lower() == "radial":
        from app.calculators.wood_movement_calc import RADIAL_TO_TANGENTIAL_RATIO

        coeff = coeff * RADIAL_TO_TANGENTIAL_RATIO
    return {
        "species_key": key,
        "grain_direction": grain_direction.lower(),
        "shrinkage_coefficient_per_pct_mc": coeff,
        "source": "wood_movement_calc.TANGENTIAL_SHRINKAGE",
    }
