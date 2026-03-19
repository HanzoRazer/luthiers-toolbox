"""
Wood Movement Calculator — CONSTRUCTION-006.

Computes dimensional changes from humidity variation.
Critical for acoustic guitar building — wood expands/contracts
across the grain as relative humidity changes.

Physics:
  ΔW = W₀ × (MC₂ - MC₁) × S_r
  where:
    ΔW  = dimensional change (mm)
    W₀  = initial dimension (mm)
    MC  = moisture content (%)
    S_r = shrinkage coefficient (species-dependent)

MC change from humidity (approximate):
  delta_MC = (delta_RH / 100) × 0.3
  (wood gains ~0.3% MC per 1% RH change in typical range)
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple, Any


# ─── Shrinkage Coefficients ──────────────────────────────────────────────────
# Tangential shrinkage (% per % MC change)
# Source: Wood Handbook (USDA Forest Products Laboratory)

TANGENTIAL_SHRINKAGE: Dict[str, float] = {
    # Softwoods (tops)
    "sitka_spruce": 0.00176,
    "engelmann_spruce": 0.00164,
    "red_spruce": 0.00182,
    "western_red_cedar": 0.00154,
    "port_orford_cedar": 0.00168,
    "redwood": 0.00142,

    # Hardwoods (backs/sides)
    "indian_rosewood": 0.00168,
    "brazilian_rosewood": 0.00172,
    "honduran_mahogany": 0.00132,
    "african_mahogany": 0.00140,
    "sapele": 0.00148,
    "maple": 0.00224,
    "walnut": 0.00186,
    "koa": 0.00178,
    "cocobolo": 0.00156,
    "bubinga": 0.00192,
    "ovangkol": 0.00164,
    "ziricote": 0.00176,

    # Common aliases
    "spruce": 0.00176,      # defaults to sitka
    "cedar": 0.00154,       # defaults to WRC
    "rosewood": 0.00168,    # defaults to Indian
    "mahogany": 0.00132,    # defaults to Honduran
}

# Radial shrinkage is typically 50-70% of tangential
RADIAL_TO_TANGENTIAL_RATIO = 0.55

# MC change per 1% RH change (approximate linear relationship)
MC_CHANGE_PER_RH_PCT = 0.30  # %MC / %RH


# ─── Data Classes ────────────────────────────────────────────────────────────

@dataclass
class WoodMovementSpec:
    """Result of wood movement calculation."""
    species: str
    dimension_mm: float          # original dimension
    rh_from: float               # starting relative humidity %
    rh_to: float                 # ending relative humidity %
    mc_change_pct: float         # moisture content change %
    movement_mm: float           # dimensional change (absolute)
    direction: str               # "expansion" | "contraction"
    grain_direction: str         # "tangential" | "radial"
    shrinkage_coefficient: float # coefficient used
    gate: str                    # GREEN/YELLOW/RED
    risk_note: str               # human-readable risk assessment

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return asdict(self)


@dataclass
class SafeHumidityRange:
    """Safe humidity range to limit wood movement."""
    species: str
    nominal_rh: float
    max_movement_mm: float
    dimension_mm: float
    min_rh: float
    max_rh: float
    notes: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return asdict(self)


# ─── Core Functions ──────────────────────────────────────────────────────────

def compute_wood_movement(
    species: str,
    dimension_mm: float,
    rh_from: float,
    rh_to: float,
    grain_direction: str = "tangential",
) -> WoodMovementSpec:
    """
    Calculate dimensional change from humidity variation.

    Args:
        species: Wood species name
        dimension_mm: Current dimension in mm
        rh_from: Starting relative humidity %
        rh_to: Ending relative humidity %
        grain_direction: "tangential" or "radial"

    Returns:
        WoodMovementSpec with movement details and risk assessment

    Raises:
        ValueError: If species is unknown or RH values invalid
    """
    # Normalize species name
    species_key = species.lower().replace(" ", "_").replace("-", "_")

    if species_key not in TANGENTIAL_SHRINKAGE:
        raise ValueError(
            f"Unknown species: '{species}'. "
            f"Supported: {list(TANGENTIAL_SHRINKAGE.keys())}"
        )

    if not (0 <= rh_from <= 100) or not (0 <= rh_to <= 100):
        raise ValueError("RH values must be between 0 and 100%")

    if dimension_mm <= 0:
        raise ValueError("Dimension must be positive")

    # Get shrinkage coefficient
    coeff = TANGENTIAL_SHRINKAGE[species_key]
    if grain_direction.lower() == "radial":
        coeff *= RADIAL_TO_TANGENTIAL_RATIO

    # Calculate MC change from RH change
    rh_delta = rh_to - rh_from
    mc_change = (rh_delta / 100.0) * MC_CHANGE_PER_RH_PCT * 100  # as percentage

    # Calculate dimensional change: ΔW = W₀ × ΔMC × S_r
    movement = abs(dimension_mm * (mc_change / 100.0) * coeff * 100)

    # Determine direction
    direction = "expansion" if rh_to > rh_from else "contraction"
    if rh_to == rh_from:
        direction = "none"

    # Risk assessment
    gate, risk_note = _assess_movement_risk(movement, dimension_mm, rh_from, rh_to)

    return WoodMovementSpec(
        species=species_key,
        dimension_mm=dimension_mm,
        rh_from=rh_from,
        rh_to=rh_to,
        mc_change_pct=round(mc_change, 3),
        movement_mm=round(movement, 4),
        direction=direction,
        grain_direction=grain_direction.lower(),
        shrinkage_coefficient=coeff,
        gate=gate,
        risk_note=risk_note,
    )


def safe_humidity_range(
    species: str,
    dimension_mm: float = 400.0,
    max_movement_mm: float = 1.0,
    nominal_rh: float = 45.0,
) -> SafeHumidityRange:
    """
    Calculate safe humidity range to keep wood movement within limits.

    Args:
        species: Wood species name
        dimension_mm: Dimension to evaluate (default 400mm for guitar top)
        max_movement_mm: Maximum acceptable movement
        nominal_rh: Starting/nominal relative humidity %

    Returns:
        SafeHumidityRange with min/max RH values

    Raises:
        ValueError: If species is unknown
    """
    # Normalize species name
    species_key = species.lower().replace(" ", "_").replace("-", "_")

    if species_key not in TANGENTIAL_SHRINKAGE:
        raise ValueError(f"Unknown species: '{species}'")

    coeff = TANGENTIAL_SHRINKAGE[species_key]
    notes: List[str] = []

    # Calculate how much RH change causes max_movement_mm
    # movement = dimension × (rh_delta/100 × MC_factor) × coeff × 100
    # rh_delta = movement × 100 / (dimension × MC_factor × coeff × 100)
    if dimension_mm > 0 and coeff > 0:
        mc_factor = MC_CHANGE_PER_RH_PCT
        # Solve for rh_delta
        rh_delta = (max_movement_mm * 100) / (dimension_mm * mc_factor * coeff * 100)
        rh_delta = abs(rh_delta)
    else:
        rh_delta = 50.0  # fallback

    # Calculate min/max RH
    min_rh = max(0, nominal_rh - rh_delta)
    max_rh = min(100, nominal_rh + rh_delta)

    # Add warnings
    if rh_delta < 10:
        notes.append(f"Tight tolerance: ±{rh_delta:.1f}% RH for {species_key}")
    if min_rh < 30:
        notes.append("Warning: Below 30% RH causes significant cracking risk")
    if max_rh > 70:
        notes.append("Warning: Above 70% RH can cause swelling and glue issues")

    return SafeHumidityRange(
        species=species_key,
        nominal_rh=nominal_rh,
        max_movement_mm=max_movement_mm,
        dimension_mm=dimension_mm,
        min_rh=round(min_rh, 1),
        max_rh=round(max_rh, 1),
        notes=notes,
    )


def _assess_movement_risk(
    movement_mm: float,
    dimension_mm: float,
    rh_from: float,
    rh_to: float,
) -> Tuple[str, str]:
    """Assess risk level for given wood movement."""
    # Percentage movement
    pct_movement = (movement_mm / dimension_mm) * 100 if dimension_mm > 0 else 0

    # Check extreme humidity conditions
    rh_min = min(rh_from, rh_to)
    rh_max = max(rh_from, rh_to)
    rh_swing = abs(rh_to - rh_from)

    if movement_mm < 0.5:
        gate = "GREEN"
        risk_note = "Minimal movement, low risk"
    elif movement_mm < 1.5:
        gate = "YELLOW"
        risk_note = f"Moderate movement ({movement_mm:.2f}mm), monitor humidity"
    else:
        gate = "RED"
        risk_note = f"High movement ({movement_mm:.2f}mm), cracking risk"

    # Additional risk factors
    if rh_min < 25:
        gate = "RED" if gate != "RED" else gate
        risk_note += "; extreme dryness risk"
    elif rh_min < 35:
        if gate == "GREEN":
            gate = "YELLOW"
        risk_note += "; low humidity caution"

    if rh_swing > 40:
        if gate == "GREEN":
            gate = "YELLOW"
        risk_note += f"; large RH swing ({rh_swing:.0f}%)"

    return gate, risk_note


def list_species() -> List[str]:
    """Return list of supported wood species."""
    return list(TANGENTIAL_SHRINKAGE.keys())


def get_shrinkage_coefficient(
    species: str,
    grain_direction: str = "tangential",
) -> float:
    """Get shrinkage coefficient for a species."""
    species_key = species.lower().replace(" ", "_").replace("-", "_")

    if species_key not in TANGENTIAL_SHRINKAGE:
        raise ValueError(f"Unknown species: '{species}'")

    coeff = TANGENTIAL_SHRINKAGE[species_key]
    if grain_direction.lower() == "radial":
        coeff *= RADIAL_TO_TANGENTIAL_RATIO

    return coeff
