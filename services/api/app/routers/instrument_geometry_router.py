"""
Wave 14: Instrument Geometry Router

Provides API endpoints for:
- Listing all 19 instrument models
- Getting model details and specifications
- Computing fret positions, fretboard geometry, bridge placement
- Querying model registry status (PRODUCTION, PARTIAL, STUB)

Registered at: /api/instrument_geometry/*
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

# Import Wave 14 modules
from ..instrument_geometry.models import InstrumentModelId, InstrumentModelStatus
from ..instrument_geometry.model_registry import (
    get_model_info,
    list_models,
    get_all_models_summary,
)
from ..instrument_geometry.model_registry import get_default_scale
from ..instrument_geometry.neck import (
    compute_fret_positions_mm,
    compute_compound_radius_at_fret,
    InstrumentSpec,
    FretboardSpec,
)
from ..instrument_geometry.neck.neck_profiles import get_default_neck_profile
from ..instrument_geometry.neck.fret_math import (
    compute_fan_fret_positions,
    validate_fan_fret_geometry,
    FanFretPoint,
    FAN_FRET_PRESETS,
)
from ..instrument_geometry.body import (
    compute_fretboard_outline,
    compute_fret_slot_lines,
)
from ..instrument_geometry.bridge import (
    compute_bridge_location_mm,
    compute_saddle_positions_mm,
)

router = APIRouter()


# ============================================================================
# Response Models
# ============================================================================

class ModelSummary(BaseModel):
    """Summary info for a single instrument model."""
    id: str
    name: str
    category: str
    status: str
    description: Optional[str] = None


class ModelListResponse(BaseModel):
    """Response for listing all models."""
    count: int
    models: List[ModelSummary]


class ModelDetailResponse(BaseModel):
    """Full detail response for a single model."""
    id: str
    name: str
    category: str
    subcategory: Optional[str] = None
    manufacturer: Optional[str] = None
    status: str
    description: Optional[str] = None
    spec: Optional[Dict[str, Any]] = None


class FretPositionsRequest(BaseModel):
    """Request body for fret position calculation."""
    scale_length_mm: float = Field(..., gt=0, description="Scale length in mm")
    num_frets: int = Field(22, ge=1, le=36, description="Number of frets")
    compensation_mm: float = Field(0.0, ge=0, description="Bridge compensation in mm")


class FanFretCalculateRequest(BaseModel):
    """Request body for fan-fret position calculation."""
    treble_scale_mm: float = Field(..., gt=0, description="Treble side scale length in mm")
    bass_scale_mm: float = Field(..., gt=0, description="Bass side scale length in mm")
    num_frets: int = Field(24, ge=1, le=36, description="Number of frets")
    nut_width_mm: float = Field(42.0, gt=0, description="Nut width in mm")
    heel_width_mm: float = Field(56.0, gt=0, description="Heel width in mm")
    perpendicular_fret: int = Field(7, ge=0, description="Fret number that remains perpendicular")


class FanFretPointResponse(BaseModel):
    """Single fan-fret point data."""
    fret_number: int
    treble_pos_mm: float
    bass_pos_mm: float
    angle_rad: float
    angle_deg: float
    center_x: float
    center_y: float
    is_perpendicular: bool


class FanFretCalculateResponse(BaseModel):
    """Response for fan-fret calculation."""
    treble_scale_mm: float
    bass_scale_mm: float
    perpendicular_fret: int
    num_frets: int
    fret_points: List[FanFretPointResponse]
    max_angle_deg: float


class FanFretValidateRequest(BaseModel):
    """Request body for fan-fret geometry validation."""
    treble_scale_mm: float = Field(..., gt=0, description="Treble side scale length in mm")
    bass_scale_mm: float = Field(..., gt=0, description="Bass side scale length in mm")
    num_frets: int = Field(24, ge=1, le=36, description="Number of frets")
    perpendicular_fret: int = Field(7, ge=0, description="Fret number that remains perpendicular")


class FanFretValidateResponse(BaseModel):
    """Response for fan-fret validation."""
    valid: bool
    message: str
    warnings: Optional[List[str]] = None


class FretPositionsResponse(BaseModel):
    """Response with calculated fret positions."""
    scale_length_mm: float
    num_frets: int
    compensation_mm: float
    positions_mm: List[float]
    spacings_mm: List[float]


class FretboardOutlineRequest(BaseModel):
    """Request body for fretboard outline calculation."""
    scale_length_mm: float = Field(..., gt=0)
    nut_width_mm: float = Field(43.0, gt=0)
    width_at_12th_mm: float = Field(52.0, gt=0)
    num_frets: int = Field(22, ge=1, le=36)
    overhang_mm: float = Field(3.0, ge=0)


class FretboardOutlineResponse(BaseModel):
    """Response with fretboard outline points."""
    outline_points: List[List[float]]
    slot_lines: List[Dict[str, Any]]


class BridgePlacementRequest(BaseModel):
    """Request body for bridge placement calculation."""
    scale_length_mm: float = Field(..., gt=0)
    num_strings: int = Field(6, ge=1, le=12)
    string_spacing_mm: float = Field(10.5, gt=0)
    compensation_offsets_mm: Optional[List[float]] = None


class BridgePlacementResponse(BaseModel):
    """Response with bridge and saddle positions."""
    bridge_y_mm: float
    saddle_positions: List[Dict[str, float]]


class RadiusAtFretRequest(BaseModel):
    """Request body for compound radius calculation."""
    nut_radius_mm: float = Field(..., gt=0)
    heel_radius_mm: float = Field(..., gt=0)
    scale_length_mm: float = Field(..., gt=0)
    fret_number: int = Field(..., ge=0, le=36)
    total_frets: int = Field(22, ge=1, le=36)


class RadiusAtFretResponse(BaseModel):
    """Response with radius at specified fret."""
    fret_number: int
    radius_mm: float
    radius_inches: float


class ScaleLengthResponse(BaseModel):
    """Response model for scale length lookup."""
    model_id: str
    scale_length_mm: float
    num_frets: int
    description: Optional[str] = None
    multiscale: bool = False
    bass_length_mm: Optional[float] = None
    treble_length_mm: Optional[float] = None


class NeckProfileResponse(BaseModel):
    """Response model for neck profile lookup."""
    model_id: str
    nut_width_mm: float
    twelve_fret_width_mm: float
    thickness_1st_mm: float
    thickness_12th_mm: float
    radius_nut_mm: float
    radius_12th_mm: float
    description: Optional[str] = None
    profile_shape: Optional[str] = None


# ============================================================================
# Model Registry Endpoints
# ============================================================================

@router.get("/models", response_model=ModelListResponse, tags=["Instrument Geometry"])
async def list_all_models(
    status: Optional[str] = Query(None, description="Filter by status: PRODUCTION, PARTIAL, STUB"),
    category: Optional[str] = Query(None, description="Filter by category: electric, acoustic, bass, other"),
):
    """
    List all instrument models in the registry.
    
    Optional filters:
    - **status**: Filter by implementation status
    - **category**: Filter by instrument category
    """
    # Get all models via the summary function
    summary = get_all_models_summary()
    all_model_data = summary.get("models", [])
    
    # Apply filters
    filtered = []
    for m in all_model_data:
        if status and m.get("status", "").upper() != status.upper():
            continue
        if category and m.get("category", "").lower() != category.lower():
            continue
        filtered.append(m)
    
    summaries = [
        ModelSummary(
            id=m["id"],
            name=m.get("display_name", m["id"]),
            category=m.get("category", "unknown"),
            status=m.get("status", "STUB"),
            description=None,  # Not in summary
        )
        for m in filtered
    ]
    
    return ModelListResponse(count=len(summaries), models=summaries)


@router.get("/models/{model_id}", response_model=ModelDetailResponse, tags=["Instrument Geometry"])
async def get_model_detail(model_id: str):
    """
    Get detailed information for a specific instrument model.
    
    Use the model ID (e.g., 'stratocaster', 'les_paul', 'dreadnought').
    """
    # Try to resolve from enum first
    try:
        model_enum = InstrumentModelId(model_id)
    except ValueError:
        raise HTTPException(404, f"Model not found: {model_id}")
    
    info = get_model_info(model_enum)
    if not info:
        raise HTTPException(404, f"Model not found: {model_id}")
    
    return ModelDetailResponse(
        id=info.get("id", model_id),
        name=info.get("display_name", model_id),
        category=info.get("category", "unknown"),
        subcategory=info.get("subcategory"),
        manufacturer=info.get("manufacturer"),
        status=info.get("status", "STUB"),
        description=info.get("description"),
        spec=info.get("default_spec"),
    )


@router.get("/status", tags=["Instrument Geometry"])
async def get_status_summary():
    """
    Get summary of model implementation status across the registry.
    """
    summary = get_all_models_summary()
    
    return {
        "total_models": summary.get("total", 0),
        "by_status": summary.get("by_status", {}),
        "by_category": summary.get("by_category", {}),
    }


# ============================================================================


# ============================================================================
# Geometry Calculation Endpoints
# ============================================================================

@router.post("/frets/positions", response_model=FretPositionsResponse, tags=["Instrument Geometry"])
async def calculate_fret_positions(body: FretPositionsRequest):
    """
    Calculate fret positions for a given scale length.
    
    Returns positions (distance from nut) and spacings (fret-to-fret distances).
    """
    positions = compute_fret_positions_mm(
        scale_length_mm=body.scale_length_mm,
        num_frets=body.num_frets,
    )
    
    # Calculate spacings
    spacings = [positions[0]]  # First fret spacing from nut
    for i in range(1, len(positions)):
        spacings.append(positions[i] - positions[i - 1])
    
    # Apply compensation to final bridge position (informational)
    compensated_positions = [p for p in positions]
    
    return FretPositionsResponse(
        scale_length_mm=body.scale_length_mm,
        num_frets=body.num_frets,
        compensation_mm=body.compensation_mm,
        positions_mm=[round(p, 4) for p in compensated_positions],
        spacings_mm=[round(s, 4) for s in spacings],
    )


@router.post("/fretboard/outline", response_model=FretboardOutlineResponse, tags=["Instrument Geometry"])
async def calculate_fretboard_outline(body: FretboardOutlineRequest):
    """
    Calculate fretboard outline and fret slot positions.
    
    Returns outline polygon and fret slot line coordinates.
    """
    # Create a FretboardSpec from the request
    spec = FretboardSpec(
        scale_length_mm=body.scale_length_mm,
        nut_width_mm=body.nut_width_mm,
        width_at_12th_fret_mm=body.width_at_12th_mm,
        num_frets=body.num_frets,
        fret_overhang_mm=body.overhang_mm,
    )
    
    outline = compute_fretboard_outline(spec)
    slot_lines = compute_fret_slot_lines(spec)
    
    return FretboardOutlineResponse(
        outline_points=[[round(p[0], 4), round(p[1], 4)] for p in outline],
        slot_lines=[
            {
                "fret": sl["fret"],
                "x1": round(sl["x1"], 4),
                "y1": round(sl["y1"], 4),
                "x2": round(sl["x2"], 4),
                "y2": round(sl["y2"], 4),
            }
            for sl in slot_lines
        ],
    )


@router.post("/bridge/placement", response_model=BridgePlacementResponse, tags=["Instrument Geometry"])
async def calculate_bridge_placement(body: BridgePlacementRequest):
    """
    Calculate bridge and saddle positions for a guitar.
    
    Returns the bridge centerline Y position and individual saddle positions.
    """
    bridge_y = compute_bridge_location_mm(
        scale_length_mm=body.scale_length_mm,
        compensation_mm=0.0,  # Base position without compensation
    )
    
    # Get saddle positions
    compensation_offsets = body.compensation_offsets_mm
    if compensation_offsets is None:
        # Default compensation pattern for 6-string
        if body.num_strings == 6:
            compensation_offsets = [2.0, 1.5, 1.0, 1.0, 1.5, 2.5]  # Low E to high E
        elif body.num_strings == 4:
            compensation_offsets = [2.5, 2.0, 1.5, 1.0]  # Bass pattern
        else:
            compensation_offsets = [1.5] * body.num_strings
    
    saddle_positions = compute_saddle_positions_mm(
        scale_length_mm=body.scale_length_mm,
        num_strings=body.num_strings,
        string_spacing_mm=body.string_spacing_mm,
        compensation_offsets_mm=compensation_offsets[:body.num_strings],
    )
    
    return BridgePlacementResponse(
        bridge_y_mm=round(bridge_y, 4),
        saddle_positions=[
            {
                "string": sp["string"],
                "x": round(sp["x"], 4),
                "y": round(sp["y"], 4),
            }
            for sp in saddle_positions
        ],
    )


@router.post("/radius/at_fret", response_model=RadiusAtFretResponse, tags=["Instrument Geometry"])
async def calculate_radius_at_fret(body: RadiusAtFretRequest):
    """
    Calculate the fretboard radius at a specific fret for compound radius necks.
    
    Interpolates between nut and heel radius based on fret position.
    """
    radius_mm = compute_compound_radius_at_fret(
        nut_radius_mm=body.nut_radius_mm,
        heel_radius_mm=body.heel_radius_mm,
        fret_number=body.fret_number,
        total_frets=body.total_frets,
    )
    
    return RadiusAtFretResponse(
        fret_number=body.fret_number,
        radius_mm=round(radius_mm, 4),
        radius_inches=round(radius_mm / 25.4, 4),
    )


# ============================================================================
# Utility Endpoints
# ============================================================================

@router.get("/enums/model_ids", tags=["Instrument Geometry"])
async def list_model_ids():
    """
    List all valid InstrumentModelId enum values.
    """
    return {
        "enum_values": [
            {"key": m.name, "value": m.value}
            for m in InstrumentModelId
        ]
    }


@router.get("/enums/statuses", tags=["Instrument Geometry"])
async def list_statuses():
    """
    List all valid InstrumentModelStatus enum values.
    """
    return {
        "enum_values": [
            {"key": s.name, "value": s.value}
            for s in InstrumentModelStatus
        ]
    }



@router.get("/scale-length/{model_id}", response_model=ScaleLengthResponse, tags=["Instrument Geometry"])
async def api_get_scale_length(model_id: str):
    """
    Return the default ScaleLengthSpec for a given model_id.
    """
    try:
        model_enum = InstrumentModelId(model_id)
    except ValueError:
        raise HTTPException(404, f"Model not found: {model_id}")

    spec = get_default_scale(model_enum)
    return ScaleLengthResponse(
        model_id=model_enum.value,
        scale_length_mm=spec.scale_length_mm,
        num_frets=spec.num_frets,
        description=getattr(spec, "description", None),
        multiscale=getattr(spec, "multiscale", False),
        bass_length_mm=getattr(spec, "bass_length_mm", None),
        treble_length_mm=getattr(spec, "treble_length_mm", None),
    )


@router.get("/neck-profile/{model_id}", response_model=NeckProfileResponse, tags=["Instrument Geometry"])
async def api_get_neck_profile(model_id: str):
    """
    Return the default NeckProfileSpec for a given model_id.
    """
    try:
        model_enum = InstrumentModelId(model_id)
    except ValueError:
        raise HTTPException(404, f"Model not found: {model_id}")

    spec = get_default_neck_profile(model_enum)
    return NeckProfileResponse(
        model_id=model_enum.value,
        nut_width_mm=spec.nut_width_mm,
        twelve_fret_width_mm=spec.twelve_fret_width_mm,
        thickness_1st_mm=spec.thickness_1st_mm,
        thickness_12th_mm=spec.thickness_12th_mm,
        radius_nut_mm=spec.radius_nut_mm,
        radius_12th_mm=spec.radius_12th_mm,
        description=getattr(spec, "description", None),
        profile_shape=getattr(spec, "profile_shape", None),
    )


# ============================================================================
# Fan-Fret Endpoints (Wave 19 Phase A)
# ============================================================================

@router.post("/fan_fret/calculate", response_model=FanFretCalculateResponse, tags=["Instrument Geometry"])
async def api_calculate_fan_fret(body: FanFretCalculateRequest):
    """
    Calculate fan-fret (multi-scale) fret positions.
    
    Returns position data for each fret including:
    - Treble and bass side positions
    - Slot angle in radians and degrees
    - Center point coordinates
    - Perpendicular fret marker
    
    Example:
        7-string standard: treble=648mm (25.5"), bass=686mm (27"), perp=7
    """
    # Compute fan-fret positions
    fret_points = compute_fan_fret_positions(
        treble_scale_mm=body.treble_scale_mm,
        bass_scale_mm=body.bass_scale_mm,
        fret_count=body.num_frets,
        nut_width_mm=body.nut_width_mm,
        heel_width_mm=body.heel_width_mm,
        perpendicular_fret=body.perpendicular_fret,
        scale_length_reference_mm=body.treble_scale_mm,
    )
    
    # Convert to response format
    response_points = []
    max_angle_deg = 0.0
    
    for fp in fret_points:
        angle_deg = fp.angle_rad * 180.0 / 3.14159265359
        is_perp = abs(fp.angle_rad) < 0.001
        
        response_points.append(FanFretPointResponse(
            fret_number=fp.fret_number,
            treble_pos_mm=fp.treble_pos_mm,
            bass_pos_mm=fp.bass_pos_mm,
            angle_rad=fp.angle_rad,
            angle_deg=angle_deg,
            center_x=fp.center_x,
            center_y=fp.center_y,
            is_perpendicular=is_perp,
        ))
        
        max_angle_deg = max(max_angle_deg, abs(angle_deg))
    
    return FanFretCalculateResponse(
        treble_scale_mm=body.treble_scale_mm,
        bass_scale_mm=body.bass_scale_mm,
        perpendicular_fret=body.perpendicular_fret,
        num_frets=body.num_frets,
        fret_points=response_points,
        max_angle_deg=max_angle_deg,
    )


@router.post("/fan_fret/validate", response_model=FanFretValidateResponse, tags=["Instrument Geometry"])
async def api_validate_fan_fret(body: FanFretValidateRequest):
    """
    Validate fan-fret geometry parameters.
    
    Checks:
    - Bass scale >= treble scale
    - Scale lengths in reasonable range (500-900mm)
    - Perpendicular fret within valid range
    
    Returns validation status with detailed message.
    """
    result = validate_fan_fret_geometry(
        treble_scale_mm=body.treble_scale_mm,
        bass_scale_mm=body.bass_scale_mm,
        fret_count=body.num_frets,
        perpendicular_fret=body.perpendicular_fret,
    )
    
    return FanFretValidateResponse(
        valid=result["valid"],
        message=result["message"],
        warnings=result.get("warnings"),
    )


@router.get("/fan_fret/presets", tags=["Instrument Geometry"])
async def api_get_fan_fret_presets():
    """
    Get predefined fan-fret configurations.
    
    Returns presets for:
    - 7-string standard (25.5"-27")
    - 8-string standard (25.5"-28")
    - Baritone 6-string (26"-27")
    """
    return {
        "presets": FAN_FRET_PRESETS,
        "count": len(FAN_FRET_PRESETS),
    }
