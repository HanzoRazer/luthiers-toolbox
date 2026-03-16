# services/api/app/materials/recommendation/scorer.py
"""
Materials Recommendation Engine (MAT-001)

Scores and ranks tonewoods for a given instrument role using a deterministic
weighted scoring model. No ML — the dataset is rich enough for rule-based ranking.

Scoring dimensions (weights adjustable per role):
    - acoustic suitability  (radiation ratio relative to role target)
    - structural suitability (hardness / MOE for load-bearing roles)
    - machinability          (burn/tearout risk, workability)

See docs/PLATFORM_ARCHITECTURE.md — Layer 1 / Materials Intelligence.
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple

from ..schemas import TonewoodEntry, MaterialCompareResult, MachiningNotes
from ..registry.tonewoods import load_tonewoods, filter_by_role


# ---------------------------------------------------------------------------
# Role target profiles (empirical references from luthierie literature)
# ---------------------------------------------------------------------------

# For each instrument role: (target_radiation_ratio, target_density_kg_m3)
# Derived from established species for that role.
# Role scores are normalised 0-1 against these targets.

_ROLE_TARGETS: Dict[str, Dict[str, float]] = {
    "soundboard":  {"radiation_ratio": 11.5, "density": 420,  "moe": 9.5,  "hardness": 500},
    "top":         {"radiation_ratio": 11.5, "density": 420,  "moe": 9.5,  "hardness": 500},
    "body_top":    {"radiation_ratio": 11.5, "density": 420,  "moe": 9.5,  "hardness": 500},
    "back_sides":  {"radiation_ratio": 8.0,  "density": 700,  "moe": 12.0, "hardness": 1500},
    "neck":        {"radiation_ratio": 6.0,  "density": 600,  "moe": 10.0, "hardness": 900},
    "fretboard":   {"radiation_ratio": 4.0,  "density": 900,  "moe": 13.0, "hardness": 2500},
    "bridge":      {"radiation_ratio": 4.0,  "density": 750,  "moe": 13.5, "hardness": 2000},
    "bracing":     {"radiation_ratio": 12.0, "density": 410,  "moe": 10.0, "hardness": 400},
    "body":        {"radiation_ratio": 7.0,  "density": 550,  "moe": 10.0, "hardness": 900},
}

# Role dimension weights: how much each dimension matters for this role
_ROLE_WEIGHTS: Dict[str, Dict[str, float]] = {
    "soundboard": {"acoustic": 0.55, "structural": 0.15, "machinability": 0.30},
    "top":        {"acoustic": 0.55, "structural": 0.15, "machinability": 0.30},
    "body_top":   {"acoustic": 0.55, "structural": 0.15, "machinability": 0.30},
    "back_sides": {"acoustic": 0.30, "structural": 0.45, "machinability": 0.25},
    "neck":       {"acoustic": 0.10, "structural": 0.60, "machinability": 0.30},
    "fretboard":  {"acoustic": 0.05, "structural": 0.70, "machinability": 0.25},
    "bridge":     {"acoustic": 0.10, "structural": 0.65, "machinability": 0.25},
    "bracing":    {"acoustic": 0.50, "structural": 0.25, "machinability": 0.25},
    "body":       {"acoustic": 0.20, "structural": 0.35, "machinability": 0.45},
}

_RISK_MAP = {"low": 1.0, "medium": 0.6, "high": 0.2}


def _score_acoustic(entry: TonewoodEntry, target: Dict[str, float]) -> float:
    """
    Score acoustic suitability 0-1 using radiation ratio proximity to target.
    Uses a Gaussian falloff: full score at target, ~0.37 at 2× target deviation.
    """
    rr = entry.radiation_ratio
    if rr is None:
        return 0.5  # neutral score when data unavailable
    target_rr = target.get("radiation_ratio", 10.0)
    # σ = 3.0 radiation ratio units → generous tolerance
    sigma = 3.0
    return math.exp(-0.5 * ((rr - target_rr) / sigma) ** 2)


def _score_structural(entry: TonewoodEntry, target: Dict[str, float]) -> float:
    """
    Score structural suitability 0-1 using hardness + MOE proximity to targets.
    """
    scores: List[float] = []

    # Density proximity
    if entry.density_kg_m3 and "density" in target:
        ratio = entry.density_kg_m3 / target["density"]
        scores.append(math.exp(-0.5 * ((math.log(ratio)) / 0.4) ** 2))

    # MOE proximity
    if entry.modulus_of_elasticity_gpa and "moe" in target:
        ratio = entry.modulus_of_elasticity_gpa / target["moe"]
        scores.append(math.exp(-0.5 * ((math.log(ratio)) / 0.5) ** 2))

    # Janka hardness for load-bearing roles
    if entry.janka_hardness_lbf and "hardness" in target:
        h_ratio = entry.janka_hardness_lbf / target["hardness"]
        scores.append(min(1.0, h_ratio))  # more hardness is OK for fretboard/bridge

    if not scores:
        return 0.5
    return sum(scores) / len(scores)


def _score_machinability(entry: TonewoodEntry) -> float:
    """
    Score machinability 0-1 using burn/tearout risk (lower risk = higher score).
    """
    if not entry.machining_notes:
        return 0.6  # assume OK if no data
    mn = entry.machining_notes
    burn    = _RISK_MAP.get(mn.burn_risk,    0.6)
    tearout = _RISK_MAP.get(mn.tearout_risk, 0.6)
    dust    = _RISK_MAP.get(mn.dust_hazard,  0.8)
    return (burn * 0.4 + tearout * 0.4 + dust * 0.2)


def score_for_role(entry: TonewoodEntry, role: str) -> float:
    """
    Compute a 0-1 role suitability score for a tonewood entry.
    Returns 0.5 (neutral) if the role has no target profile.
    """
    target  = _ROLE_TARGETS.get(role, _ROLE_TARGETS.get("body", {}))
    weights = _ROLE_WEIGHTS.get(role, {"acoustic": 0.33, "structural": 0.33, "machinability": 0.34})

    acoustic       = _score_acoustic(entry, target)
    structural     = _score_structural(entry, target)
    machinability  = _score_machinability(entry)

    return round(
        acoustic      * weights["acoustic"] +
        structural    * weights["structural"] +
        machinability * weights["machinability"],
        3,
    )


def recommend_for_role(
    role: str,
    instrument_type: Optional[str] = None,
    limit: int = 10,
) -> List[Tuple[TonewoodEntry, float]]:
    """
    Return top `limit` tonewoods ranked by role suitability score.

    Returns list of (TonewoodEntry, score) sorted descending by score.
    Only returns entries that have `role` in their typical_uses.
    """
    candidates = filter_by_role(role)

    # For electric body, prefer lighter woods
    if instrument_type == "electric_guitar" and role == "body":
        candidates = [e for e in candidates if not e.density_kg_m3 or e.density_kg_m3 < 700]

    scored = [(entry, score_for_role(entry, role)) for entry in candidates]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:limit]


def compare_species(
    species_ids: List[str],
    role: Optional[str] = None,
) -> List[MaterialCompareResult]:
    """
    Compare a list of species IDs, optionally scoring for a given role.
    Returns MaterialCompareResult list sorted by role_score desc (if role provided).
    """
    from ..registry.tonewoods import get_tonewoods_index
    index = get_tonewoods_index()

    results: List[MaterialCompareResult] = []
    for sid in species_ids:
        entry = index.get(sid)
        if not entry:
            continue
        role_score = score_for_role(entry, role) if role else None
        results.append(MaterialCompareResult(
            species_id=entry.id,
            name=entry.name,
            role_score=role_score,
            radiation_ratio=entry.radiation_ratio,
            specific_moe=entry.specific_moe,
            ashby_index=entry.ashby_index,
            acoustic_impedance_mrayl=entry.acoustic_impedance_mrayl,
            density_kg_m3=entry.density_kg_m3,
            tone_character=entry.tone_character,
            machining_notes=entry.machining_notes,
        ))

    if role:
        results.sort(key=lambda r: r.role_score or 0, reverse=True)
    return results
