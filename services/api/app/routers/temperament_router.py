"""
Alternative Temperaments Router

API endpoints for Smart Guitar alternative temperament calculations.
Provides fret position comparisons, staggered fret calculations,
and temperament analysis for key-optimized guitar fretboards.

Wave 6: Smart Guitar Alternative Temperaments System
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..calculators.alternative_temperaments import (
    TemperamentSystem,
    compute_just_intonation_positions,
    compute_pythagorean_positions,
    compute_meantone_positions,
    compute_staggered_fret_positions,
    compute_equal_temperament_position,
    analyze_temperament_deviations,
    list_temperament_systems,
    get_temperament_info,
    NOTE_NAMES,
    STANDARD_TUNING_SEMITONES,
)

router = APIRouter(
    prefix="/temperaments",
    tags=["Smart Guitar", "Temperaments"],
)


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class FretPositionResponse(BaseModel):
    """Single fret position with temperament comparison."""
    fret_number: int
    equal_pos_mm: float
    alt_pos_mm: float
    deviation_cents: float
    interval_name: str
    ratio: List[int]


class TemperamentComparisonRequest(BaseModel):
    """Request for temperament comparison."""
    scale_length_mm: float = Field(
        default=648.0, 
        ge=400.0, 
        le=900.0,
        description="Scale length in mm (e.g., 648 for Fender, 628.65 for Gibson)"
    )
    fret_count: int = Field(
        default=22, 
        ge=12, 
        le=36,
        description="Number of frets to calculate"
    )
    temperament: TemperamentSystem = Field(
        default=TemperamentSystem.JUST_MAJOR,
        description="Alternative temperament system to compare against 12-TET"
    )


class TemperamentComparisonResponse(BaseModel):
    """Response with fret positions for comparison."""
    scale_length_mm: float
    fret_count: int
    temperament: str
    temperament_info: dict
    positions: List[FretPositionResponse]
    summary: dict


class StaggeredFretRequest(BaseModel):
    """Request for staggered fret calculation."""
    scale_length_mm: float = Field(default=648.0, ge=400.0, le=900.0)
    fret_count: int = Field(default=22, ge=12, le=36)
    string_count: int = Field(default=6, ge=4, le=12)
    target_key: str = Field(
        default="E",
        description="Root note for optimization (E, A, C, G, etc.)"
    )
    temperament: TemperamentSystem = Field(default=TemperamentSystem.JUST_MAJOR)
    tuning_semitones: Optional[List[int]] = Field(
        default=None,
        description="Open string pitches in semitones from bass (default: standard tuning)"
    )
    nut_width_mm: float = Field(default=43.0, ge=30.0, le=60.0)
    fret_width_mm: float = Field(default=56.0, ge=40.0, le=80.0)


class StaggeredFretResponse(BaseModel):
    """Single staggered fret with per-string positions."""
    fret_number: int
    string_positions: List[float]
    endpoints: List[List[float]]


class StaggeredFretsResponse(BaseModel):
    """Response with all staggered fret data."""
    scale_length_mm: float
    target_key: str
    temperament: str
    string_count: int
    frets: List[StaggeredFretResponse]


class TemperamentSystemInfo(BaseModel):
    """Information about a temperament system."""
    id: str
    name: str
    description: str
    best_for: str
    tradeoffs: str


class AllTemperamentsResponse(BaseModel):
    """Response comparing all temperament systems."""
    scale_length_mm: float
    fret_count: int
    systems: dict


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/systems", response_model=List[TemperamentSystemInfo])
def get_temperament_systems():
    """
    List all available temperament systems.
    
    Returns descriptions, use cases, and tradeoffs for each system.
    """
    return list_temperament_systems()


@router.get("/keys")
def get_available_keys():
    """
    List available root keys for staggered fret optimization.
    """
    return {
        "keys": NOTE_NAMES,
        "default": "E",
        "description": "Root note for key-optimized staggered frets"
    }


@router.get("/tunings")
def get_standard_tunings():
    """
    List common guitar tunings as semitone offsets.
    """
    return {
        "standard": {
            "name": "Standard (EADGBE)",
            "semitones": STANDARD_TUNING_SEMITONES,
            "notes": ["E", "A", "D", "G", "B", "E"]
        },
        "drop_d": {
            "name": "Drop D (DADGBE)",
            "semitones": [-2, 5, 10, 15, 19, 24],
            "notes": ["D", "A", "D", "G", "B", "E"]
        },
        "open_e": {
            "name": "Open E (EBEG#BE)",
            "semitones": [0, 7, 12, 16, 19, 24],
            "notes": ["E", "B", "E", "G#", "B", "E"]
        },
        "open_g": {
            "name": "Open G (DGDGBD)",
            "semitones": [-2, 5, 7, 12, 14, 19],
            "notes": ["D", "G", "D", "G", "B", "D"]
        },
        "dadgad": {
            "name": "DADGAD",
            "semitones": [-2, 5, 10, 15, 17, 22],
            "notes": ["D", "A", "D", "G", "A", "D"]
        },
    }


@router.post("/compare", response_model=TemperamentComparisonResponse)
def compare_temperament(req: TemperamentComparisonRequest):
    """
    Compare an alternative temperament against equal temperament.
    
    Returns fret positions for both systems with cent deviations,
    showing where pure intervals differ from 12-TET.
    """
    if req.temperament == TemperamentSystem.JUST_MAJOR:
        positions = compute_just_intonation_positions(req.scale_length_mm, req.fret_count)
    elif req.temperament == TemperamentSystem.PYTHAGOREAN:
        positions = compute_pythagorean_positions(req.scale_length_mm, req.fret_count)
    elif req.temperament == TemperamentSystem.MEANTONE_QUARTER:
        positions = compute_meantone_positions(req.scale_length_mm, req.fret_count)
    else:
        # Default to just intonation
        positions = compute_just_intonation_positions(req.scale_length_mm, req.fret_count)
    
    # Convert to response format
    position_responses = [
        FretPositionResponse(
            fret_number=p.fret_number,
            equal_pos_mm=p.equal_pos_mm,
            alt_pos_mm=p.alt_pos_mm,
            deviation_cents=p.deviation_cents,
            interval_name=p.interval_name,
            ratio=list(p.ratio)
        )
        for p in positions
    ]
    
    # Calculate summary statistics
    deviations = [abs(p.deviation_cents) for p in positions]
    significant = [p for p in positions if abs(p.deviation_cents) > 10]
    
    summary = {
        "max_deviation_cents": max(deviations) if deviations else 0,
        "avg_deviation_cents": sum(deviations) / len(deviations) if deviations else 0,
        "significant_deviations": len(significant),
        "worst_intervals": [
            {"fret": p.fret_number, "interval": p.interval_name, "cents": p.deviation_cents}
            for p in sorted(positions, key=lambda x: abs(x.deviation_cents), reverse=True)[:3]
        ]
    }
    
    return TemperamentComparisonResponse(
        scale_length_mm=req.scale_length_mm,
        fret_count=req.fret_count,
        temperament=req.temperament.value,
        temperament_info=get_temperament_info(req.temperament),
        positions=position_responses,
        summary=summary
    )


@router.post("/staggered", response_model=StaggeredFretsResponse)
def compute_staggered_frets(req: StaggeredFretRequest):
    """
    Compute staggered (angled) fret positions for key-optimized intonation.
    
    Staggered frets allow each string to have a different fret position,
    enabling pure intervals for a specific key while maintaining playability.
    
    This is the "Smart Guitar" concept - frets optimized for a single key
    that produce mathematically perfect intervals.
    """
    if req.target_key.upper() not in NOTE_NAMES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid key '{req.target_key}'. Use one of: {NOTE_NAMES}"
        )
    
    frets = compute_staggered_fret_positions(
        scale_length_mm=req.scale_length_mm,
        fret_count=req.fret_count,
        string_count=req.string_count,
        tuning_semitones=req.tuning_semitones,
        target_key=req.target_key,
        temperament=req.temperament,
        nut_width_mm=req.nut_width_mm,
        fret_width_mm=req.fret_width_mm,
    )
    
    fret_responses = [
        StaggeredFretResponse(
            fret_number=f.fret_number,
            string_positions=f.string_positions,
            endpoints=[list(p) for p in f.endpoints]
        )
        for f in frets
    ]
    
    return StaggeredFretsResponse(
        scale_length_mm=req.scale_length_mm,
        target_key=req.target_key,
        temperament=req.temperament.value,
        string_count=req.string_count,
        frets=fret_responses
    )


@router.get("/compare-all", response_model=AllTemperamentsResponse)
def compare_all_temperaments(
    scale_length_mm: float = Query(default=648.0, ge=400.0, le=900.0),
    fret_count: int = Query(default=12, ge=12, le=36)
):
    """
    Compare all temperament systems at once.
    
    Returns fret positions for equal temperament, just intonation,
    Pythagorean, and meantone quarter-comma for easy comparison.
    """
    analysis = analyze_temperament_deviations(scale_length_mm, fret_count)
    
    return AllTemperamentsResponse(
        scale_length_mm=scale_length_mm,
        fret_count=fret_count,
        systems=analysis
    )


@router.get("/equal-temperament")
def get_equal_temperament_positions(
    scale_length_mm: float = Query(default=648.0, ge=400.0, le=900.0),
    fret_count: int = Query(default=22, ge=12, le=36)
):
    """
    Get standard 12-TET fret positions (reference baseline).
    """
    positions = []
    for fret in range(1, fret_count + 1):
        pos = compute_equal_temperament_position(scale_length_mm, fret)
        positions.append({
            "fret_number": fret,
            "position_mm": round(pos, 4),
            "distance_from_previous_mm": round(
                pos - compute_equal_temperament_position(scale_length_mm, fret - 1) 
                if fret > 1 else pos, 
                4
            )
        })
    
    return {
        "temperament": "12-TET (Equal Temperament)",
        "scale_length_mm": scale_length_mm,
        "fret_count": fret_count,
        "positions": positions
    }


@router.get("/status")
def get_temperament_status():
    """
    Get status of the alternative temperaments module.
    """
    return {
        "available": True,
        "version": "1.0.0",
        "wave": "Wave 6",
        "features": {
            "temperament_comparison": True,
            "staggered_frets": True,
            "key_optimization": True,
            "supported_temperaments": [t.value for t in TemperamentSystem if t != TemperamentSystem.CUSTOM],
            "supported_keys": NOTE_NAMES,
        },
        "endpoints": [
            "/systems",
            "/keys", 
            "/tunings",
            "/compare",
            "/staggered",
            "/compare-all",
            "/equal-temperament",
        ]
    }
