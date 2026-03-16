# services/api/app/routers/system/materials_router.py
"""
System Materials Router (MAT-002 / MAT-003)

Provides the materials API surface for the platform.

Endpoints:
    GET  /api/registry/tonewoods                    — all curated tonewoods (MAT-002 / R-8)
    GET  /api/registry/tonewoods/{id}               — single tonewood by ID
    GET  /api/system/materials/tonewoods            — canonical path (same data, new URL)
    GET  /api/system/materials/species              — full 473-species wood database
    GET  /api/system/materials/species/{id}         — single species
    POST /api/system/materials/compare              — compare species for a role
    POST /api/system/materials/recommend            — recommend species for a role

Route aliases:
    /api/registry/tonewoods → /api/system/materials/tonewoods
    Both remain active through Phase 7 cleanup. Frontend code should use
    /api/registry/tonewoods for now (that's what StiffnessIndexPanel already calls).

Note on CNC material data:
    The legacy /api/material/* router (cutting energy, heat partition) serves
    CNC-specific data. It will be merged into /api/system/materials/machining/*
    in Phase 7. Do not extend it; add new machining endpoints here.

See docs/PLATFORM_ARCHITECTURE.md — Layer 1 / Materials Intelligence.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from .schemas import (
    MaterialCompareRequest,
    MaterialCompareResponse,
    MaterialRecommendRequest,
    TonewoodsResponse,
    TonewoodEntry,
    WoodSpeciesEntry,
)
from .registry.tonewoods import (
    load_tonewoods,
    load_wood_species,
    get_tonewood,
    get_wood_species,
    filter_by_role,
)
from .recommendation.scorer import compare_species, recommend_for_role

logger = logging.getLogger(__name__)

# Two routers — one for /api/registry prefix, one for /api/system/materials prefix
registry_router = APIRouter(prefix="/api/registry", tags=["Materials", "Registry"])
system_router   = APIRouter(prefix="/api/system/materials", tags=["Materials", "System"])


# =============================================================================
# /api/registry/tonewoods  (MAT-002 / R-8)
# This is the short-path endpoint that StiffnessIndexPanel and other panels call.
# =============================================================================

@registry_router.get(
    "/tonewoods",
    response_model=TonewoodsResponse,
    summary="Get curated tonewood reference (71 species with acoustic data)",
)
def get_tonewoods(
    role: Optional[str] = Query(
        default=None,
        description="Filter by instrument role (soundboard, back_sides, neck, fretboard, bridge, bracing, body)",
    ),
    tier: Optional[str] = Query(
        default=None,
        description="Filter by tier: 'tier_1' (primary) or 'tier_2' (emerging)",
    ),
    acoustic_data_only: bool = Query(
        default=False,
        description="If true, only return entries with MOE + density data for acoustic index computation",
    ),
) -> TonewoodsResponse:
    """
    Return the curated tonewood reference.

    All 71 entries include computed acoustic indices:
    - radiation_ratio (Schelleng c/ρ)
    - specific_moe (E/ρ)
    - ashby_index (E^1/3 / ρ)
    - acoustic_impedance_mrayl (ρ×c in MRayl)

    Indices are None when MOE or density data is unavailable for that species.

    This is endpoint R-8 — the one that unblocks StiffnessIndexPanel, WoodIntelligenceHub,
    and InstrumentMaterialSelector from using live data.
    """
    all_entries = load_tonewoods()

    if role:
        all_entries = [e for e in all_entries if role in e.typical_uses]
    if tier:
        all_entries = [e for e in all_entries if e.tier == tier]
    if acoustic_data_only:
        all_entries = [e for e in all_entries if e.has_acoustic_data]

    return TonewoodsResponse(
        tonewoods=all_entries,
        total_count=len(all_entries),
        tier_1_count=sum(1 for e in all_entries if e.tier == "tier_1"),
        tier_2_count=sum(1 for e in all_entries if e.tier == "tier_2"),
        with_acoustic_data=sum(1 for e in all_entries if e.has_acoustic_data),
    )


@registry_router.get(
    "/tonewoods/{species_id}",
    response_model=TonewoodEntry,
    summary="Get single tonewood entry by ID",
)
def get_tonewood_by_id(species_id: str) -> TonewoodEntry:
    entry = get_tonewood(species_id)
    if not entry:
        raise HTTPException(
            status_code=404,
            detail=f"Tonewood '{species_id}' not found. "
                   f"Use GET /api/registry/tonewoods to browse available IDs.",
        )
    return entry


# =============================================================================
# /api/system/materials/* (MAT-003)
# Canonical path for all materials operations.
# =============================================================================

@system_router.get(
    "/tonewoods",
    response_model=TonewoodsResponse,
    summary="Canonical tonewoods path — same as /api/registry/tonewoods",
)
def get_tonewoods_canonical(
    role: Optional[str] = Query(default=None),
    tier: Optional[str] = Query(default=None),
    acoustic_data_only: bool = Query(default=False),
) -> TonewoodsResponse:
    """Canonical URL for tonewoods. Identical to GET /api/registry/tonewoods."""
    return get_tonewoods(role=role, tier=tier, acoustic_data_only=acoustic_data_only)


@system_router.get(
    "/species",
    response_model=List[WoodSpeciesEntry],
    summary="Full wood species database (473 species with CNC machining data)",
)
def get_all_species(
    guitar_relevance: Optional[str] = Query(
        default=None,
        description="Filter by relevance: 'primary', 'established', 'emerging'",
    ),
) -> List[WoodSpeciesEntry]:
    """
    Return the full wood species database (473 entries).

    Each entry includes CNC machining parameters:
    - specific_cutting_energy_j_per_mm3
    - burn_tendency, tearout_tendency (0-1 scale)
    - feed/speed limits per operation type

    This consolidates the CNC data currently scattered in /api/material/list.
    """
    species = load_wood_species()
    if guitar_relevance:
        species = [s for s in species if s.guitar_relevance == guitar_relevance]
    return species


@system_router.get(
    "/species/{species_id}",
    response_model=WoodSpeciesEntry,
    summary="Get single wood species with CNC data",
)
def get_species_by_id(species_id: str) -> WoodSpeciesEntry:
    entry = get_wood_species(species_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Species '{species_id}' not found.")
    return entry


@system_router.post(
    "/compare",
    response_model=MaterialCompareResponse,
    summary="Compare two or more tonewoods for a given instrument role",
)
def compare_materials(body: MaterialCompareRequest) -> MaterialCompareResponse:
    """
    Compare 2-8 species side-by-side with role-specific scoring.

    Scoring dimensions (weighted per role):
    - Acoustic suitability (radiation ratio proximity to role target)
    - Structural suitability (density, MOE, hardness proximity)
    - Machinability (burn/tearout risk penalty)

    Returns results sorted by role_score descending (if role is specified).
    """
    results = compare_species(body.species_ids, role=body.role)
    if not results:
        raise HTTPException(
            status_code=404,
            detail="None of the requested species IDs were found in the tonewood database.",
        )
    return MaterialCompareResponse(role=body.role, results=results)


@system_router.post(
    "/recommend",
    response_model=List[TonewoodEntry],
    summary="Recommend tonewoods for an instrument role",
)
def recommend_materials(body: MaterialRecommendRequest) -> List[TonewoodEntry]:
    """
    Return top candidates for an instrument role, ranked by suitability score.

    Roles: soundboard, back_sides, neck, fretboard, bridge, bracing, body.

    Only returns species that have the role in their typical_uses — no spurious
    recommendations from unrelated species.
    """
    scored = recommend_for_role(
        role=body.role,
        instrument_type=body.instrument_type,
        limit=body.limit,
    )
    return [entry for entry, _ in scored]
