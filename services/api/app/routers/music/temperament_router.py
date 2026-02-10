"""
Music Temperament Router
========================

Global temperament system for all instruments.
Not model-locked - shared music theory endpoints.

Endpoints:
  GET /health - Temperament subsystem health
  GET /systems - List temperament systems
  GET /keys - List available keys
  GET /tunings - List standard tunings
  POST /compare - Compare temperament to 12-TET
  GET /compare-all - Compare all temperaments
  GET /equal-temperament - Get 12-TET positions
  GET /resolve - Model-specific temperament resolution

Moved from /api/smart-guitar/temperaments (Wave 6)

Wave 15: Option C API Restructuring
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

# Import from existing calculator module
from ...calculators.alternative_temperaments import (
    TemperamentSystem,
    compute_just_intonation_positions,
    compute_pythagorean_positions,
    compute_meantone_positions,
    compute_equal_temperament_position,
    analyze_temperament_deviations,
    list_temperament_systems,
    get_temperament_info,
    NOTE_NAMES,
    STANDARD_TUNING_SEMITONES,
)

router = APIRouter(tags=["Music", "Temperaments"])

# =============================================================================
# MODELS
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
    List available root keys for key-optimized calculations.
    """
    return {
        "keys": NOTE_NAMES,
        "default": "E",
        "description": "Root note for key-optimized temperament calculations"
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
        "note": "For bass, mandolin, and other instruments, use /resolve endpoint with instrument_type"
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
        positions = compute_just_intonation_positions(req.scale_length_mm, req.fret_count)
    
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

@router.get("/resolve")
def resolve_temperament(
    instrument_type: str = Query(default="guitar", description="guitar, bass, mandolin, ukulele"),
    model_id: Optional[str] = Query(default=None, description="Optional model override"),
    scale_length_mm: Optional[float] = Query(default=None, ge=200.0, le=1200.0),
    temperament: str = Query(default="equal", description="equal, just_major, pythagorean, meantone")
):
    """
    Resolve temperament for a specific instrument type.
    
    Use this for model-specific overrides when needed.
    Falls back to standard values if model_id not recognized.
    """
    # Default scale lengths by instrument
    defaults = {
        "guitar": {"scale_mm": 648.0, "frets": 22, "strings": 6},
        "bass": {"scale_mm": 863.6, "frets": 20, "strings": 4},
        "mandolin": {"scale_mm": 330.0, "frets": 20, "strings": 8},
        "ukulele": {"scale_mm": 330.0, "frets": 12, "strings": 4},
        "banjo": {"scale_mm": 660.4, "frets": 22, "strings": 5},
    }
    
    inst_defaults = defaults.get(instrument_type, defaults["guitar"])
    final_scale = scale_length_mm or inst_defaults["scale_mm"]
    
    # Model-specific overrides
    model_overrides = {
        "archtop": {"scale_mm": 635.0, "frets": 20},
        "stratocaster": {"scale_mm": 648.0, "frets": 22},
        "les_paul": {"scale_mm": 628.65, "frets": 22},
        "om": {"scale_mm": 645.16, "frets": 20},
        "smart": {"scale_mm": 648.0, "frets": 22},
    }
    
    if model_id and model_id in model_overrides:
        overrides = model_overrides[model_id]
        if not scale_length_mm:
            final_scale = overrides["scale_mm"]
    
    return {
        "ok": True,
        "resolved": {
            "instrument_type": instrument_type,
            "model_id": model_id,
            "scale_length_mm": final_scale,
            "temperament": temperament,
            "fret_count": inst_defaults["frets"],
            "string_count": inst_defaults["strings"]
        },
        "endpoint_for_positions": f"/api/music/temperament/{'compare' if temperament != 'equal' else 'equal-temperament'}",
        "note": "Use resolved values with /compare or /equal-temperament endpoints"
    }

@router.get("/tables")
def get_temperament_tables(
    scale_length_mm: float = Query(default=648.0, ge=400.0, le=900.0),
    fret_count: int = Query(default=22, ge=12, le=36)
):
    """
    Get formatted temperament comparison tables.
    
    Returns data suitable for display in UI tables.
    """
    equal_positions = []
    for fret in range(1, fret_count + 1):
        pos = compute_equal_temperament_position(scale_length_mm, fret)
        equal_positions.append({
            "fret": fret,
            "position_mm": round(pos, 3)
        })
    
    return {
        "ok": True,
        "scale_length_mm": scale_length_mm,
        "fret_count": fret_count,
        "tables": {
            "equal_temperament": equal_positions,
            "available_comparisons": [
                {"id": "just_major", "name": "Just Intonation (Major)"},
                {"id": "pythagorean", "name": "Pythagorean"},
                {"id": "meantone_quarter", "name": "Quarter-comma Meantone"}
            ]
        },
        "use_compare_endpoint": "POST /api/music/temperament/compare for full comparison data"
    }
