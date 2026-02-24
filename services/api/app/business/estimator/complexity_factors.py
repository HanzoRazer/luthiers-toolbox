"""
Complexity Factors — Multipliers for design choices.

These factors are applied to base WBS task hours based on design selections.
Factors > 1.0 increase time, < 1.0 decrease time.

Sources:
- Industry surveys of custom builders
- Time studies from production shops
- Adjusted for one-off/small-batch work
"""
from typing import Dict

from .schemas import (
    BodyComplexity,
    BindingComplexity,
    NeckComplexity,
    FretboardInlay,
    FinishType,
    RosetteComplexity,
    BuilderExperience,
)


# =============================================================================
# BODY COMPLEXITY FACTORS
# =============================================================================

BODY_FACTORS: Dict[BodyComplexity, float] = {
    BodyComplexity.STANDARD: 1.0,
    BodyComplexity.CUTAWAY_SOFT: 1.15,
    BodyComplexity.CUTAWAY_FLORENTINE: 1.25,
    BodyComplexity.CUTAWAY_VENETIAN: 1.20,
    BodyComplexity.ARM_BEVEL: 1.10,
    BodyComplexity.TUMMY_CUT: 1.08,
    BodyComplexity.CARVED_TOP: 1.45,  # Significant hand carving
}

# Which WBS task groups these factors apply to
BODY_FACTOR_APPLIES_TO = [
    "body_assembly",
    "sides_bend",
    "top_work",
    "back_work",
]


# =============================================================================
# BINDING COMPLEXITY FACTORS
# =============================================================================

BINDING_BODY_FACTORS: Dict[BindingComplexity, float] = {
    BindingComplexity.NONE: 0.0,  # Skip binding tasks entirely
    BindingComplexity.SINGLE: 1.0,
    BindingComplexity.MULTIPLE: 1.35,
    BindingComplexity.HERRINGBONE: 1.50,
}

BINDING_NECK_FACTOR = 1.20  # Additional factor for bound fretboard
BINDING_HEADSTOCK_FACTOR = 1.15  # Additional factor for bound headstock


# =============================================================================
# NECK COMPLEXITY FACTORS
# =============================================================================

NECK_FACTORS: Dict[NeckComplexity, float] = {
    NeckComplexity.STANDARD: 1.0,
    NeckComplexity.VOLUTE: 1.08,
    NeckComplexity.SCARF_JOINT: 1.18,
    NeckComplexity.MULTI_SCALE: 1.40,  # Fan fret requires careful layout
}

NECK_FACTOR_APPLIES_TO = [
    "neck_carve",
    "neck_blank",
    "fretboard",
]


# =============================================================================
# INLAY COMPLEXITY FACTORS
# =============================================================================

FRETBOARD_INLAY_FACTORS: Dict[FretboardInlay, float] = {
    FretboardInlay.NONE: 0.85,  # Faster without inlay routing
    FretboardInlay.DOTS: 1.0,
    FretboardInlay.BLOCKS: 1.25,
    FretboardInlay.TRAPEZOIDS: 1.30,
    FretboardInlay.CUSTOM: 1.80,  # Hand-cut custom inlays
}

HEADSTOCK_INLAY_FACTOR = 1.25  # Additional factor for headstock inlay


# =============================================================================
# FINISH COMPLEXITY FACTORS
# =============================================================================

FINISH_FACTORS: Dict[FinishType, float] = {
    FinishType.OIL: 0.50,
    FinishType.WAX: 0.45,
    FinishType.SHELLAC_WIPE: 0.70,
    FinishType.SHELLAC_FRENCH_POLISH: 2.20,  # Very labor intensive
    FinishType.NITRO_SOLID: 1.0,
    FinishType.NITRO_BURST: 1.45,
    FinishType.NITRO_VINTAGE: 1.70,  # Aging, checking, relic work
    FinishType.POLY_SOLID: 0.75,
    FinishType.POLY_BURST: 1.10,
}

FINISH_FACTOR_APPLIES_TO = [
    "finish_prep",
    "finish_apply",
    "finish_buff",
]


# =============================================================================
# ROSETTE COMPLEXITY FACTORS (Acoustic only)
# =============================================================================

ROSETTE_FACTORS: Dict[RosetteComplexity, float] = {
    RosetteComplexity.NONE: 0.0,  # Skip rosette task
    RosetteComplexity.SIMPLE_RINGS: 1.0,
    RosetteComplexity.MOSAIC: 1.60,
    RosetteComplexity.CUSTOM_ART: 2.50,  # Hand-cut custom design
}


# =============================================================================
# ELECTRONICS COMPLEXITY (Electric only)
# =============================================================================

def get_electronics_factor(pickup_count: int, active: bool) -> float:
    """Calculate electronics complexity factor."""
    base = 1.0

    # Each pickup adds routing and wiring time
    if pickup_count == 1:
        base = 1.0
    elif pickup_count == 2:
        base = 1.15
    elif pickup_count >= 3:
        base = 1.30

    # Active electronics add battery box routing, preamp install
    if active:
        base *= 1.25

    return base


# =============================================================================
# BUILDER EXPERIENCE FACTORS
# =============================================================================

EXPERIENCE_FACTORS: Dict[BuilderExperience, float] = {
    BuilderExperience.BEGINNER: 1.50,      # 50% slower
    BuilderExperience.INTERMEDIATE: 1.20,  # 20% slower
    BuilderExperience.EXPERIENCED: 1.00,   # Baseline
    BuilderExperience.MASTER: 0.85,        # 15% faster
}


# =============================================================================
# COMBINATION RULES
# =============================================================================

def calculate_body_complexity(selections: list) -> float:
    """
    Calculate combined body complexity.

    Multiple features are combined with diminishing returns:
    - First feature: full factor
    - Additional features: (factor - 1) * 0.7
    """
    if not selections or selections == [BodyComplexity.STANDARD]:
        return 1.0

    factors = [BODY_FACTORS[s] for s in selections if s != BodyComplexity.STANDARD]

    if not factors:
        return 1.0

    # Sort descending, apply diminishing returns
    factors.sort(reverse=True)

    total = factors[0]
    for f in factors[1:]:
        # Add 70% of the marginal increase
        total += (f - 1.0) * 0.7

    return round(total, 3)


def calculate_neck_complexity(selections: list) -> float:
    """Calculate combined neck complexity with diminishing returns."""
    if not selections or selections == [NeckComplexity.STANDARD]:
        return 1.0

    factors = [NECK_FACTORS[s] for s in selections if s != NeckComplexity.STANDARD]

    if not factors:
        return 1.0

    factors.sort(reverse=True)
    total = factors[0]
    for f in factors[1:]:
        total += (f - 1.0) * 0.7

    return round(total, 3)


def get_all_factors_summary() -> Dict[str, Dict[str, float]]:
    """Return all factors for API/UI consumption."""
    return {
        "body": {k.value: v for k, v in BODY_FACTORS.items()},
        "binding_body": {k.value: v for k, v in BINDING_BODY_FACTORS.items()},
        "neck": {k.value: v for k, v in NECK_FACTORS.items()},
        "fretboard_inlay": {k.value: v for k, v in FRETBOARD_INLAY_FACTORS.items()},
        "finish": {k.value: v for k, v in FINISH_FACTORS.items()},
        "rosette": {k.value: v for k, v in ROSETTE_FACTORS.items()},
        "experience": {k.value: v for k, v in EXPERIENCE_FACTORS.items()},
    }
