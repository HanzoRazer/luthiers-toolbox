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
