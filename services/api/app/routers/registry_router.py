"""
Data Registry API Router

Provides API endpoints for accessing edition-based data:
- System tier (all editions): scales, woods, formulas
- Edition tier (Pro/Enterprise): empirical limits, machines, tools
- Registry metadata and health

Registered at: /api/registry/*
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field

from ..data_registry import Registry, Edition as RegistryEdition, EntitlementError
from ..middleware import get_edition, require_feature, EditionContext


router = APIRouter()


# ============================================================================
# Response Models
# ============================================================================

class RegistryInfoResponse(BaseModel):
    """Registry metadata response."""
    edition: str = Field(..., description="Current edition (express, pro, enterprise)")
    version: str = Field(default="1.0.0", description="Registry version")
    tiers: List[str] = Field(default=["system", "edition", "user"], description="Available data tiers")
    system_datasets: List[str] = Field(..., description="System tier datasets available")
    edition_datasets: List[str] = Field(..., description="Edition tier datasets (if entitled)")


class ScaleLengthResponse(BaseModel):
    """Scale length data response."""
    scales: Dict[str, Any] = Field(..., description="Scale length specifications")
    count: int = Field(..., description="Number of scales")


class WoodSpeciesResponse(BaseModel):
    """Wood species reference data response."""
    species: Dict[str, Any] = Field(..., description="Wood species data")
    count: int = Field(..., description="Number of species")


class EmpiricalLimitsResponse(BaseModel):
    """Empirical limits response (Pro/Enterprise only)."""
    limits: Dict[str, Any] = Field(..., description="Feed/speed limits per wood species")
    count: int = Field(..., description="Number of species with limits")
    edition_required: str = Field(default="pro", description="Minimum edition required")


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/info", response_model=RegistryInfoResponse)
def get_registry_info(
    edition: str = Query(default="express", description="Edition to query (express, pro, enterprise)")
) -> RegistryInfoResponse:
    """
    Get registry metadata and available datasets.
    
    Returns information about what data is available for the specified edition.
    """
    try:
        registry = Registry(edition=edition)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # System tier datasets (always available)
    system_datasets = [
        "scale_lengths",
        "wood_species", 
        "fret_formulas",
        "body_templates",
        "neck_profiles"
    ]
    
    # Edition tier datasets (Pro/Enterprise only)
    edition_datasets = []
    if edition in ["pro", "enterprise"]:
        edition_datasets = [
            "empirical_limits",
            "machines",
            "tools",
            "cam_presets",
            "posts"
        ]
    
    return RegistryInfoResponse(
        edition=edition,
        version="1.0.0",
        tiers=["system", "edition", "user"],
        system_datasets=system_datasets,
        edition_datasets=edition_datasets
    )


@router.get("/scale_lengths", response_model=ScaleLengthResponse)
def get_scale_lengths(
    edition: str = Query(default="express", description="Edition (all editions have access)")
) -> ScaleLengthResponse:
    """
    Get standard scale length specifications.
    
    System tier data - available to all editions.
    Includes: Fender 25.5", Gibson 24.75", PRS 25", etc.
    """
    try:
        registry = Registry(edition=edition)
        data = registry.get_scale_lengths()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load scale lengths: {e}")
    
    scales = data.get("scales", {})
    return ScaleLengthResponse(
        scales=scales,
        count=len(scales)
    )


@router.get("/wood_species", response_model=WoodSpeciesResponse)
def get_wood_species(
    edition: str = Query(default="express", description="Edition (all editions have access)")
) -> WoodSpeciesResponse:
    """
    Get wood species reference data.
    
    System tier data - available to all editions.
    Includes: density, hardness, workability ratings for 13 species.
    """
    try:
        registry = Registry(edition=edition)
        data = registry.get_wood_species()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load wood species: {e}")
    
    species = data.get("species", {})
    return WoodSpeciesResponse(
        species=species,
        count=len(species)
    )


@router.get("/empirical_limits", response_model=EmpiricalLimitsResponse)
def get_empirical_limits(
    ctx: EditionContext = Depends(require_feature("empirical_limits"))
) -> EmpiricalLimitsResponse:
    """
    Get empirical feed/speed limits per wood species.
    
    Edition tier data - requires Pro or Enterprise edition.
    Express users will receive 403 Forbidden.
    
    Includes per-species:
    - feed_clamp: roughing_max, finishing_max, plunge_max (mm/min)
    - speed_clamp: min_rpm, max_rpm, optimal_sfm
    - doc_limits: max depth of cut
    - warnings: burn risk, tearout risk, dust hazard
    """
    try:
        registry = Registry(edition=ctx.edition.value)
        data = registry.get_empirical_limits()
    except EntitlementError as e:
        raise HTTPException(
            status_code=403, 
            detail=f"Upgrade required: {e}. Empirical limits require Pro or Enterprise edition."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load empirical limits: {e}")
    
    limits = data.get("limits", {})
    return EmpiricalLimitsResponse(
        limits=limits,
        count=len(limits),
        edition_required="pro"
    )


@router.get("/empirical_limits/{wood_id}")
def get_empirical_limit_by_wood(
    wood_id: str,
    ctx: EditionContext = Depends(require_feature("empirical_limits"))
) -> Dict[str, Any]:
    """
    Get empirical limits for a specific wood species.
    
    Edition tier data - requires Pro or Enterprise edition.
    
    Args:
        wood_id: Wood species ID (e.g., "maple_hard", "ebony_african")
        
    Returns:
        Feed/speed limits for the specified wood species.
    """
    try:
        registry = Registry(edition=ctx.edition.value)
        data = registry.get_empirical_limits()
    except EntitlementError as e:
        raise HTTPException(
            status_code=403, 
            detail=f"Upgrade required: {e}. Empirical limits require Pro or Enterprise edition."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load empirical limits: {e}")
    
    limits = data.get("limits", {})
    if wood_id not in limits:
        available = list(limits.keys())
        raise HTTPException(
            status_code=404,
            detail=f"Wood species '{wood_id}' not found. Available: {available}"
        )
    
    return {
        "wood_id": wood_id,
        "limits": limits[wood_id],
        "edition": ctx.edition.value
    }


@router.get("/fret_formulas")
def get_fret_formulas(
    edition: str = Query(default="express", description="Edition (all editions have access)")
) -> Dict[str, Any]:
    """
    Get fret calculation formulas.
    
    System tier data - available to all editions.
    Includes: 12-TET standard, Buzz Feiten, true temperament constants.
    """
    try:
        registry = Registry(edition=edition)
        data = registry.get_fret_formulas()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load fret formulas: {e}")
    
    return {
        "formulas": data.get("formulas", {}),
        "count": len(data.get("formulas", {})),
        "edition": edition
    }


@router.get("/health")
def registry_health() -> Dict[str, Any]:
    """
    Health check for registry system.
    
    Verifies that registry can load data from all tiers.
    """
    health = {
        "status": "healthy",
        "checks": {}
    }
    
    # Test Express (system tier)
    try:
        registry = Registry(edition="express")
        scales = registry.get_scale_lengths()
        health["checks"]["system_tier"] = {
            "status": "ok",
            "scales_loaded": len(scales.get("scales", {}))
        }
    except Exception as e:
        health["status"] = "degraded"
        health["checks"]["system_tier"] = {"status": "error", "error": str(e)}
    
    # Test Pro (edition tier)
    try:
        registry = Registry(edition="pro")
        limits = registry.get_empirical_limits()
        health["checks"]["edition_tier"] = {
            "status": "ok",
            "limits_loaded": len(limits.get("limits", {}))
        }
    except Exception as e:
        health["status"] = "degraded"
        health["checks"]["edition_tier"] = {"status": "error", "error": str(e)}
    
    return health
