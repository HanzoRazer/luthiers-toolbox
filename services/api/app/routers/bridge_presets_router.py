"""Bridge Presets Router - Saddle compensation presets for Bridge Calculator.

Provides preset data for acoustic bridge saddle geometry calculations.
"""

from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel


router = APIRouter(prefix="/cam/bridge", tags=["cam", "bridge"])


class FamilyPreset(BaseModel):
    """Guitar family preset with default bridge geometry."""
    id: str
    label: str
    scaleLength: float  # mm
    stringSpread: float  # mm
    compTreble: float  # mm compensation
    compBass: float  # mm compensation
    slotWidth: float  # mm
    slotLength: float  # mm


class AdjustmentPreset(BaseModel):
    """Gauge/action adjustment preset."""
    id: str
    label: str
    trebleAdjust: Optional[float] = None  # mm delta
    bassAdjust: Optional[float] = None  # mm delta
    compAdjust: Optional[float] = None  # mm delta (legacy, use treble/bass)


class BridgePresetsResponse(BaseModel):
    """Complete bridge presets response."""
    families: List[FamilyPreset]
    gauges: List[AdjustmentPreset]
    actions: List[AdjustmentPreset]


# Preset data - matches frontend FALLBACK_* constants
FAMILY_PRESETS: List[FamilyPreset] = [
    FamilyPreset(
        id="les_paul",
        label='Les Paul (24.75")',
        scaleLength=628.65,
        stringSpread=52,
        compTreble=1.5,
        compBass=3,
        slotWidth=3,
        slotLength=75,
    ),
    FamilyPreset(
        id="strat_tele",
        label='Strat/Tele (25.5")',
        scaleLength=647.7,
        stringSpread=52.5,
        compTreble=2,
        compBass=3.5,
        slotWidth=3,
        slotLength=75,
    ),
    FamilyPreset(
        id="om",
        label='OM Acoustic (25.4")',
        scaleLength=645.16,
        stringSpread=54,
        compTreble=2,
        compBass=4.2,
        slotWidth=3.2,
        slotLength=80,
    ),
    FamilyPreset(
        id="dread",
        label='Dreadnought (25.4")',
        scaleLength=645.16,
        stringSpread=54,
        compTreble=2,
        compBass=4.5,
        slotWidth=3.2,
        slotLength=80,
    ),
    FamilyPreset(
        id="archtop",
        label='Archtop (25.0")',
        scaleLength=635,
        stringSpread=52,
        compTreble=1.8,
        compBass=3.2,
        slotWidth=3,
        slotLength=75,
    ),
]

GAUGE_PRESETS: List[AdjustmentPreset] = [
    AdjustmentPreset(id="light", label="Light Gauge", trebleAdjust=-0.3, bassAdjust=-0.3),
    AdjustmentPreset(id="medium", label="Medium Gauge", trebleAdjust=0, bassAdjust=0),
    AdjustmentPreset(id="heavy", label="Heavy Gauge", trebleAdjust=0.3, bassAdjust=0.4),
]

ACTION_PRESETS: List[AdjustmentPreset] = [
    AdjustmentPreset(id="low", label="Low Action", trebleAdjust=-0.2, bassAdjust=-0.2),
    AdjustmentPreset(id="standard", label="Standard Action", trebleAdjust=0, bassAdjust=0),
    AdjustmentPreset(id="high", label="High Action", trebleAdjust=0.3, bassAdjust=0.4),
]


@router.get("/presets", response_model=BridgePresetsResponse)
def get_bridge_presets() -> BridgePresetsResponse:
    """
    Get bridge saddle compensation presets.

    Returns presets for guitar families (scale length, string spread, compensation),
    string gauges (adjustment deltas), and action heights (adjustment deltas).
    """
    return BridgePresetsResponse(
        families=FAMILY_PRESETS,
        gauges=GAUGE_PRESETS,
        actions=ACTION_PRESETS,
    )






# ---------------------------------------------------------------------------
# Electric bridge catalog endpoint
# ---------------------------------------------------------------------------

from ..instrument_geometry.bridge.electric_bridges import (
    list_electric_bridges,
    get_bridge_preset_dict,
    thread_compatibility as check_thread_compat,
    compatibility_check as check_radius_compat,
    bridge_summary as electric_summary,
    ELECTRIC_BRIDGES,
)


@router.get("/electric")
def get_electric_bridges(family: str = None) -> dict:
    """
    List all electric guitar bridge types with full specifications.
    
    Optional query param: family=fender|gibson|vibrato
    """
    ids = list_electric_bridges(family)
    return {
        "bridges": {bid: get_bridge_preset_dict(bid) for bid in ids},
        "count": len(ids),
        "families": ["fender", "gibson", "vibrato"],
    }


@router.get("/electric/{bridge_id}")
def get_electric_bridge(bridge_id: str, scale_length_mm: float = 647.7) -> dict:
    """Full specification for a single electric bridge type."""
    return get_bridge_preset_dict(bridge_id, scale_length_mm)


@router.get("/electric/{bridge_id_a}/compat/{bridge_id_b}")
def electric_bridge_compat(bridge_id_a: str, bridge_id_b: str) -> dict:
    """Check thread compatibility between two bridges."""
    return {
        "thread_check": check_thread_compat(bridge_id_a, bridge_id_b),
    }

# ---------------------------------------------------------------------------
# Floyd Rose tremolo endpoint
# ---------------------------------------------------------------------------

from ..instrument_geometry.bridge.floyd_rose_tremolo import (
    floyd_rose_bridge_preset,
    compute_routing_spec,
    floyd_rose_routing_gcode,
    radius_match_note,
    FR_ORIGINAL,
)
from typing import Optional


class FloydRoseRequest(BaseModel):
    scale_length_mm: float = 647.7
    body_depth_variant: str = "standard"
    fingerboard_radius_mm: Optional[float] = None
    generate_gcode: bool = False
    tool_dia_mm: float = 6.35


class FloydRoseResponse(BaseModel):
    preset: dict
    routing_notes: list
    radius_advisory: Optional[str] = None
    gcode: Optional[str] = None


@router.post("/floyd-rose", response_model=FloydRoseResponse)
def get_floyd_rose_spec(req: FloydRoseRequest) -> FloydRoseResponse:
    """Floyd Rose Original tremolo — complete bridge design specification."""
    preset = floyd_rose_bridge_preset(req.scale_length_mm, req.body_depth_variant)
    routing = compute_routing_spec(req.body_depth_variant)
    advisory = radius_match_note(req.fingerboard_radius_mm) if req.fingerboard_radius_mm else None
    gcode = floyd_rose_routing_gcode(req.scale_length_mm, req.scale_length_mm - 100.0,
        req.body_depth_variant, req.tool_dia_mm) if req.generate_gcode else None
    return FloydRoseResponse(preset=preset, routing_notes=routing.notes,
        radius_advisory=advisory, gcode=gcode)


@router.get("/floyd-rose/dimensions")
def get_floyd_rose_dimensions() -> dict:
    """Complete Floyd Rose Original dimension table from 2021 official schematic."""
    from dataclasses import asdict
    return asdict(FR_ORIGINAL)

# ---------------------------------------------------------------------------
# Break angle calculator endpoint
# ---------------------------------------------------------------------------

from ..calculators.bridge_break_angle import (
    BreakAngleInput,
    BreakAngleResult,
    calculate_break_angle,
)


@router.post("/break-angle", response_model=BreakAngleResult)
def compute_break_angle(req: BreakAngleInput) -> BreakAngleResult:
    """
    Calculate string break angle over the saddle crown.

    Given pin-to-saddle distance and saddle protrusion height, returns
    the break angle in degrees, an energy coupling rating, and risk flags
    for geometries outside the optimal 23-31 degree range.
    """
    return calculate_break_angle(req)
