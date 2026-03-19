"""
Side Bending Parameters Calculator (GEOMETRY-010)
==================================================

Calculates bending preparation parameters for guitar sides:
- Target side thickness by instrument type
- Bending temperature and moisture by wood species
- Minimum bend radius safety check
- Spring-back estimation
- GREEN/YELLOW/RED risk gating
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any


# ─── Side Thickness Targets by Instrument Type ───────────────────────────────

SIDE_THICKNESS_TARGETS_MM: Dict[str, Dict[str, float]] = {
    "steel_string_acoustic": {"min": 2.0, "max": 2.5, "optimal": 2.3},
    "classical":             {"min": 1.8, "max": 2.2, "optimal": 2.0},
    "archtop_jazz":          {"min": 2.5, "max": 3.0, "optimal": 2.8},
    "electric_hollow":       {"min": 1.8, "max": 2.3, "optimal": 2.0},
    "ukulele":               {"min": 1.5, "max": 2.0, "optimal": 1.8},
}


# ─── Bending Parameters by Species ────────────────────────────────────────────

@dataclass
class BendingSpec:
    """Bending parameters for a wood species."""
    temp_c: float           # Recommended bending temperature (Celsius)
    moisture_pct: float     # Target moisture content (%)
    min_radius_mm: float    # Minimum safe bend radius (mm)


BENDING_PARAMS: Dict[str, BendingSpec] = {
    "mahogany":  BendingSpec(150, 8,  50),
    "rosewood":  BendingSpec(170, 10, 45),
    "maple":     BendingSpec(160, 9,  55),
    "koa":       BendingSpec(155, 8,  50),
    "sapele":    BendingSpec(155, 8,  48),
    "walnut":    BendingSpec(160, 9,  52),
    "cedar":     BendingSpec(145, 7,  55),
    "spruce":    BendingSpec(150, 8,  58),
}

# Default for unknown species
DEFAULT_BENDING_SPEC = BendingSpec(temp_c=155, moisture_pct=8, min_radius_mm=50)


# ─── Output Dataclasses ───────────────────────────────────────────────────────

@dataclass
class BendingPlan:
    """Complete bending plan with risk assessment."""
    species: str
    side_thickness_mm: float
    waist_radius_mm: float
    temp_c: float
    moisture_pct: float
    risk: str                   # GREEN, YELLOW, RED
    spring_back_deg: float
    notes: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SideThicknessSpec:
    """Side thickness recommendation for an instrument/species combo."""
    instrument_type: str
    species: str
    target_mm: float
    min_mm: float
    max_mm: float
    note: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ─── Core Functions ───────────────────────────────────────────────────────────

def compute_bending_parameters(
    species: str,
    side_thickness_mm: float,
    waist_radius_mm: float,
    instrument_type: str,
) -> BendingPlan:
    """
    Compute bending parameters and risk assessment.

    Gate logic:
        GREEN:  waist_radius >= species.min_radius_mm
        YELLOW: waist_radius >= min_radius × 0.85 (borderline)
        RED:    waist_radius < min_radius × 0.85 (risk of cracking)

    Spring-back estimate: ~5-8° for most species.
    Higher temp/moisture = less spring-back.
    """
    species_lower = species.lower().strip()
    spec = BENDING_PARAMS.get(species_lower, DEFAULT_BENDING_SPEC)

    notes: List[str] = []

    # Check if species is known
    if species_lower not in BENDING_PARAMS:
        notes.append(f"Unknown species '{species}' — using default parameters")

    # Get thickness targets for instrument type
    thickness_targets = SIDE_THICKNESS_TARGETS_MM.get(
        instrument_type.lower().strip(),
        {"min": 1.8, "max": 2.5, "optimal": 2.0}
    )

    # Check thickness against targets
    if side_thickness_mm < thickness_targets["min"]:
        notes.append(
            f"Thickness {side_thickness_mm}mm below minimum "
            f"({thickness_targets['min']}mm) — increased breakage risk"
        )
    elif side_thickness_mm > thickness_targets["max"]:
        notes.append(
            f"Thickness {side_thickness_mm}mm above maximum "
            f"({thickness_targets['max']}mm) — harder to bend, may need more heat"
        )

    # Risk assessment based on bend radius
    min_radius = spec.min_radius_mm
    yellow_threshold = min_radius * 0.85

    if waist_radius_mm >= min_radius:
        risk = "GREEN"
    elif waist_radius_mm >= yellow_threshold:
        risk = "YELLOW"
        notes.append(
            f"Borderline radius ({waist_radius_mm}mm < {min_radius}mm safe minimum) — "
            "consider reducing thickness or increasing moisture"
        )
    else:
        risk = "RED"
        notes.append(
            f"Tight radius ({waist_radius_mm}mm) below safe threshold "
            f"({yellow_threshold:.1f}mm) — high cracking risk"
        )

    # Spring-back estimation
    # Base: 6° for most woods
    # Adjustments: higher temp/moisture = less spring-back
    base_spring_back = 6.0

    # Temperature adjustment: every 10°C above 150 reduces spring-back by 0.5°
    temp_adjustment = (spec.temp_c - 150) / 10 * 0.5

    # Moisture adjustment: every 1% above 8% reduces spring-back by 0.3°
    moisture_adjustment = (spec.moisture_pct - 8) * 0.3

    spring_back_deg = max(3.0, base_spring_back - temp_adjustment - moisture_adjustment)

    # Thickness affects spring-back: thicker = more spring-back
    if side_thickness_mm > 2.5:
        spring_back_deg += 0.5
        notes.append("Thicker sides — expect slightly more spring-back")
    elif side_thickness_mm < 1.8:
        spring_back_deg -= 0.3

    spring_back_deg = round(spring_back_deg, 1)

    return BendingPlan(
        species=species,
        side_thickness_mm=side_thickness_mm,
        waist_radius_mm=waist_radius_mm,
        temp_c=spec.temp_c,
        moisture_pct=spec.moisture_pct,
        risk=risk,
        spring_back_deg=spring_back_deg,
        notes=notes,
    )


def check_side_thickness(
    instrument_type: str,
    species: str,
) -> SideThicknessSpec:
    """
    Get recommended side thickness for an instrument type and species.
    """
    instrument_lower = instrument_type.lower().strip()
    species_lower = species.lower().strip()

    # Get thickness targets
    targets = SIDE_THICKNESS_TARGETS_MM.get(
        instrument_lower,
        {"min": 1.8, "max": 2.5, "optimal": 2.0}
    )

    # Check if species has special considerations
    note = ""
    if species_lower in ("rosewood", "ebony"):
        note = "Dense wood — may use slightly thinner for easier bending"
    elif species_lower in ("cedar", "spruce"):
        note = "Soft wood — use thicker end of range for durability"
    elif species_lower in ("maple", "walnut"):
        note = "Figured woods may need extra care; avoid minimum thickness"
    elif instrument_lower not in SIDE_THICKNESS_TARGETS_MM:
        note = f"Unknown instrument type '{instrument_type}' — using acoustic defaults"

    return SideThicknessSpec(
        instrument_type=instrument_type,
        species=species,
        target_mm=targets["optimal"],
        min_mm=targets["min"],
        max_mm=targets["max"],
        note=note,
    )


def list_supported_species() -> List[str]:
    """Return list of supported wood species."""
    return list(BENDING_PARAMS.keys())


def list_instrument_types() -> List[str]:
    """Return list of supported instrument types."""
    return list(SIDE_THICKNESS_TARGETS_MM.keys())
