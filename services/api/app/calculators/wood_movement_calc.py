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

Data source:
  Shrinkage values loaded from wood_species.json with per-field attribution.
  See CLAUDE.md "Wood species data sourcing policy" for source hierarchy.
"""

from __future__ import annotations

import json
import logging
import warnings
from dataclasses import dataclass, asdict
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger(__name__)

# ─── Alias Mapping ───────────────────────────────────────────────────────────
# Maps legacy TANGENTIAL_SHRINKAGE keys to canonical JSON IDs.
# Accepts both forms; logs deprecation warning for legacy keys.

ALIAS_MAP: Dict[str, str] = {
    # Naming convention difference: modifier_category → category_modifier
    "sitka_spruce": "spruce_sitka",
    "engelmann_spruce": "spruce_engelmann",
    "red_spruce": "spruce_adirondack",      # Red Spruce = Adirondack Spruce (Picea rubens)
    "western_red_cedar": "cedar_western_red",
    "port_orford_cedar": "port_orford_cedar",  # same in both
    "indian_rosewood": "rosewood_east_indian",
    "brazilian_rosewood": "rosewood_brazilian",
    "honduran_mahogany": "mahogany_honduran",
    "african_mahogany": "mahogany_african",
    # Bare aliases — assumed defaults (legacy compatibility)
    "spruce": "spruce_sitka",               # legacy alias; assumed Sitka
    "cedar": "cedar_western_red",           # legacy alias; assumed Western Red Cedar
    "rosewood": "rosewood_east_indian",     # legacy alias; assumed East Indian
    "mahogany": "mahogany_honduran",        # legacy alias; assumed Honduran
    "maple": "maple_hard",                  # legacy alias; assumed Hard Maple (Acer saccharum)
    "walnut": "walnut_black",               # legacy alias; assumed Black Walnut
    # Species with same ID in both conventions
    "redwood": "redwood",
    "sapele": "sapele",
    "koa": "koa",
    "cocobolo": "cocobolo",
    "bubinga": "bubinga",
    "ovangkol": "ovangkol",
    "ziricote": "ziricote",
}

# Reverse map for canonical → canonical (identity)
_CANONICAL_IDS = set(ALIAS_MAP.values())

# MC change per 1% RH change (approximate linear relationship)
MC_CHANGE_PER_RH_PCT = 0.30  # %MC / %RH

# Green-to-oven-dry MC range (FPL standard)
GREEN_TO_OD_MC_RANGE = 30.0


# ─── Data Loader ─────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _load_shrinkage_data() -> Dict[str, Dict[str, float]]:
    """
    Load tangential and radial shrinkage values from canonical species registry.

    Returns dict mapping species_id to:
        {"tangential": coeff, "radial": coeff, "tangential_pct": %, "radial_pct": %}

    Conversion: FPL/Wood Database gives % shrinkage for full green-to-oven-dry
    range (~30% MC). The calc expects coefficient per 1% MC change, so:
        coeff = tangential_pct / 100 / GREEN_TO_OD_MC_RANGE = tangential_pct / 3000
    """
    json_path = (
        Path(__file__).parents[1]
        / "data_registry" / "system" / "materials" / "wood_species.json"
    )

    try:
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.warning(f"wood_species.json not found at {json_path}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in wood_species.json: {e}")
        return {}

    result = {}
    for species_id, species in data.get("species", {}).items():
        phys = species.get("physical", {})
        tang_pct = phys.get("contraction_tangential_pct")
        rad_pct = phys.get("contraction_radial_pct")

        if tang_pct is not None:
            result[species_id] = {
                "tangential": tang_pct / (100 * GREEN_TO_OD_MC_RANGE),
                "radial": rad_pct / (100 * GREEN_TO_OD_MC_RANGE) if rad_pct else None,
                "tangential_pct": tang_pct,
                "radial_pct": rad_pct,
                "source": phys.get("_shrinkage_tangential_source", "unknown"),
            }

    return result


def _resolve_species_id(species_input: str) -> Tuple[str, bool]:
    """
    Resolve user input to canonical species ID.

    Returns (canonical_id, was_legacy) where was_legacy indicates if
    the input used the legacy naming convention.
    """
    key = species_input.lower().strip().replace(" ", "_").replace("-", "_")

    # Check if it's already a canonical ID
    if key in _CANONICAL_IDS:
        return key, False

    # Check alias map
    if key in ALIAS_MAP:
        canonical = ALIAS_MAP[key]
        return canonical, True

    # Not found
    return key, False


def get_shrinkage_data(species: str, grain_direction: str = "tangential") -> Tuple[float, str]:
    """
    Get shrinkage coefficient for a species from JSON registry.

    Args:
        species: Species name (accepts both legacy and canonical IDs)
        grain_direction: "tangential" or "radial"

    Returns:
        (coefficient, canonical_species_id)

    Raises:
        ValueError: If species not found or lacks shrinkage data
    """
    canonical_id, was_legacy = _resolve_species_id(species)

    if was_legacy:
        warnings.warn(
            f"Species '{species}' uses legacy naming. "
            f"Consider using canonical ID '{canonical_id}' instead.",
            DeprecationWarning,
            stacklevel=3,
        )

    data = _load_shrinkage_data()

    if canonical_id not in data:
        supported = list(data.keys())
        raise ValueError(
            f"No shrinkage data for species '{species}' (resolved to '{canonical_id}'). "
            f"Add to wood_species.json with verified source attribution. "
            f"Supported species: {supported[:10]}{'...' if len(supported) > 10 else ''}"
        )

    species_data = data[canonical_id]

    if grain_direction.lower() == "radial":
        coeff = species_data.get("radial")
        if coeff is None:
            tang_coeff = species_data["tangential"]
            coeff = tang_coeff * 0.55
            logger.debug(f"No radial data for {canonical_id}, using 0.55 × tangential")
    else:
        coeff = species_data["tangential"]

    return coeff, canonical_id


# ─── Legacy Compatibility ────────────────────────────────────────────────────
# TANGENTIAL_SHRINKAGE dict maintained for backward compatibility with tests.
# New code should use get_shrinkage_data() instead.

def _build_legacy_dict() -> Dict[str, float]:
    """Build TANGENTIAL_SHRINKAGE from JSON for backward compatibility."""
    data = _load_shrinkage_data()
    result = {}

    # Add canonical IDs
    for species_id, values in data.items():
        result[species_id] = values["tangential"]

    # Add legacy aliases
    for legacy_key, canonical_id in ALIAS_MAP.items():
        if canonical_id in data:
            result[legacy_key] = data[canonical_id]["tangential"]

    return result


# Lazy initialization to avoid import-time JSON loading
_TANGENTIAL_SHRINKAGE_CACHE: Optional[Dict[str, float]] = None

def _get_tangential_shrinkage() -> Dict[str, float]:
    global _TANGENTIAL_SHRINKAGE_CACHE
    if _TANGENTIAL_SHRINKAGE_CACHE is None:
        _TANGENTIAL_SHRINKAGE_CACHE = _build_legacy_dict()
    return _TANGENTIAL_SHRINKAGE_CACHE


class _LegacyShrinkageDict(dict):
    """Dict wrapper that loads from JSON on first access."""

    def __getitem__(self, key):
        return _get_tangential_shrinkage()[key]

    def __contains__(self, key):
        return key in _get_tangential_shrinkage()

    def keys(self):
        return _get_tangential_shrinkage().keys()

    def values(self):
        return _get_tangential_shrinkage().values()

    def items(self):
        return _get_tangential_shrinkage().items()

    def get(self, key, default=None):
        return _get_tangential_shrinkage().get(key, default)


TANGENTIAL_SHRINKAGE = _LegacyShrinkageDict()

# Legacy constant maintained for backward compatibility
RADIAL_TO_TANGENTIAL_RATIO = 0.55


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
        species: Wood species name (accepts both legacy and canonical IDs)
        dimension_mm: Current dimension in mm
        rh_from: Starting relative humidity %
        rh_to: Ending relative humidity %
        grain_direction: "tangential" or "radial"

    Returns:
        WoodMovementSpec with movement details and risk assessment

    Raises:
        ValueError: If species is unknown or RH values invalid
    """
    if not (0 <= rh_from <= 100) or not (0 <= rh_to <= 100):
        raise ValueError("RH values must be between 0 and 100%")

    if dimension_mm <= 0:
        raise ValueError("Dimension must be positive")

    # Get shrinkage coefficient from JSON registry
    coeff, canonical_id = get_shrinkage_data(species, grain_direction)

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
        species=canonical_id,
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
    coeff, canonical_id = get_shrinkage_data(species, "tangential")
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
        notes.append(f"Tight tolerance: ±{rh_delta:.1f}% RH for {canonical_id}")
    if min_rh < 30:
        notes.append("Warning: Below 30% RH causes significant cracking risk")
    if max_rh > 70:
        notes.append("Warning: Above 70% RH can cause swelling and glue issues")

    return SafeHumidityRange(
        species=canonical_id,
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
    return list(_get_tangential_shrinkage().keys())


def get_shrinkage_coefficient(
    species: str,
    grain_direction: str = "tangential",
) -> float:
    """Get shrinkage coefficient for a species."""
    coeff, _ = get_shrinkage_data(species, grain_direction)
    return coeff
