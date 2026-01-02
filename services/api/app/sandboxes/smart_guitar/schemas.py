"""
Smart Guitar Schemas (SG-SBX-0.1)
=================================

Manufacturing-focused schemas for headed + headless Smart Guitar variants.
Includes electronics fitting, CAM planning, and toolpath operations.

Contract Version: 1.0
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, conint, confloat


CONTRACT_VERSION = "1.0"


# =============================================================================
# CORE ENUMS
# =============================================================================


class ModelVariant(str, Enum):
    """Guitar headstock variant."""
    headed = "headed"
    headless = "headless"


class Handedness(str, Enum):
    """Player handedness."""
    RH = "RH"
    LH = "LH"


class Connectivity(str, Enum):
    """Smart Guitar connectivity options."""
    BLE = "ble"
    WIFI = "wifi"
    USB = "usb"
    MIDI = "midi"
    OSC = "osc"
    AUDIO_USB = "audio_usb"


class Feature(str, Enum):
    """Smart Guitar software features."""
    DAW_MODE = "daw_mode"
    LOOPER = "looper"
    TUNER = "tuner"
    METRONOME = "metronome"
    FX_CHAIN = "fx_chain"
    RECORDING = "recording"


class UnitSystem(str, Enum):
    """Measurement unit system."""
    inch = "in"
    mm = "mm"


# =============================================================================
# GEOMETRY / ELECTRONICS MODELS
# =============================================================================


class Vec2(BaseModel):
    """2D vector."""
    x: float
    y: float


class BBox3D(BaseModel):
    """Component bounding box in mm (for electronics fit)."""
    w_mm: confloat(gt=0) = Field(..., description="Width (X) in mm")
    d_mm: confloat(gt=0) = Field(..., description="Depth (Y) in mm")
    h_mm: confloat(gt=0) = Field(..., description="Height (Z) in mm")


class Clearance(BaseModel):
    """Extra margin around component for cables/airflow."""
    margin_mm: confloat(ge=0) = Field(3.0)
    cable_bend_mm: confloat(ge=0) = Field(8.0)


class Mounting(BaseModel):
    """Conceptual mounting plane reference."""
    plane: Literal["pod_lid", "pod_floor", "body_spine", "body_floor"] = "pod_floor"
    fastener: Literal["m2_5", "m3", "wood_screw", "standoff"] = "m3"
    standoff_mm: confloat(ge=0) = 6.0


class ElectronicsComponent(BaseModel):
    """Electronics component with fitting constraints."""
    id: str
    name: str
    bbox: BBox3D
    clearance: Clearance = Field(default_factory=Clearance)
    mounting: Mounting = Field(default_factory=Mounting)
    notes: List[str] = Field(default_factory=list)


# =============================================================================
# SPEC SUBSYSTEM MODELS
# =============================================================================


class PowerSpec(BaseModel):
    """Power system specification."""
    battery_wh: confloat(gt=0) = 30.0
    battery_voltage_nom: confloat(gt=0) = 7.4
    has_bms: bool = True
    charge_port: Literal["usb_c", "barrel_jack"] = "usb_c"


class ThermalSpec(BaseModel):
    """Thermal management specification."""
    cooling: Literal["active_fan"] = "active_fan"
    fan_size_mm: conint(gt=0) = 40
    vents_defined: bool = False  # v0.1: warn if false
    max_internal_c: confloat(gt=0) = 60.0


class BodyDims(BaseModel):
    """Body dimension constraints."""
    units: UnitSystem = UnitSystem.inch
    thickness_in: confloat(gt=0) = 1.50
    top_skin_in: confloat(gt=0) = 0.30
    back_skin_in: confloat(gt=0) = 0.18
    rim_in: confloat(gt=0) = 0.50
    spine_w_in: confloat(gt=0) = 1.50


# =============================================================================
# SMART GUITAR SPEC (DESIGN TRUTH)
# =============================================================================


class SmartGuitarSpec(BaseModel):
    """
    Smart Guitar design specification (design truth).
    
    This is the authoritative source for:
    - Model variant (headed/headless)
    - Handedness
    - Electronics inventory
    - Body dimensions
    - CAM projection parameters
    """
    contract_version: str = CONTRACT_VERSION

    model_id: str = Field("smart_guitar", description="Stable model id")
    model_variant: ModelVariant = ModelVariant.headed
    handedness: Handedness = Handedness.RH

    connectivity: List[Connectivity] = Field(
        default_factory=lambda: [Connectivity.BLE, Connectivity.WIFI, Connectivity.USB]
    )
    features: List[Feature] = Field(
        default_factory=lambda: [Feature.DAW_MODE, Feature.RECORDING]
    )

    body: BodyDims = Field(default_factory=BodyDims)
    power: PowerSpec = Field(default_factory=PowerSpec)
    thermal: ThermalSpec = Field(default_factory=ThermalSpec)

    electronics: List[ElectronicsComponent] = Field(default_factory=list)

    # "Design intent" knobs for CAM projection (v0.1: simple)
    target_hollow_depth_in: confloat(gt=0) = 1.05
    pod_depth_in: confloat(gt=0) = 1.20
    pickup_depth_in: confloat(gt=0) = 0.75
    rear_cover_recess_in: confloat(gt=0) = 0.12


# =============================================================================
# CAM PLAN MODELS
# =============================================================================


class PlanWarning(BaseModel):
    """Non-blocking plan warning."""
    code: str
    message: str
    severity: Literal["info", "warn"] = "warn"


class PlanError(BaseModel):
    """Blocking plan error."""
    code: str
    message: str


class CavityKind(str, Enum):
    """Cavity types for body milling."""
    pod = "pod"
    bass = "bass_main"
    treble = "treble_main"
    tail = "tail_wing"


class CavityPlan(BaseModel):
    """Cavity milling plan."""
    kind: CavityKind
    depth_in: float
    # For v0.1 we reference "template ids" rather than emitting geometry
    template_id: str
    notes: List[str] = Field(default_factory=list)


class ChannelKind(str, Enum):
    """Wire channel types."""
    route = "route"
    drill = "drill"


class ChannelPlan(BaseModel):
    """Wire channel plan."""
    kind: ChannelKind
    template_id: str
    notes: List[str] = Field(default_factory=list)


class BracketPlan(BaseModel):
    """Component mounting bracket plan."""
    component_id: str
    template_id: str
    notes: List[str] = Field(default_factory=list)


class ToolpathOp(BaseModel):
    """Individual toolpath operation."""
    op_id: str
    title: str
    strategy: Literal["2d_adaptive", "2d_pocket", "2d_contour", "drill"] = "2d_adaptive"
    tool: str = Field(..., description="Tool library id, e.g. T2_1_4_UPCUT")
    max_stepdown_in: float
    stepover_in: float
    depth_in: float
    dxf_layer_ref: Optional[str] = None
    notes: List[str] = Field(default_factory=list)


class SmartCamPlan(BaseModel):
    """
    Smart Guitar CAM plan (manufacturing projection).
    
    Generated from SmartGuitarSpec via the planner.
    Contains cavities, brackets, channels, and toolpath ops.
    """
    contract_version: str = CONTRACT_VERSION
    model_id: str
    model_variant: ModelVariant
    handedness: Handedness

    cavities: List[CavityPlan]
    brackets: List[BracketPlan]
    channels: List[ChannelPlan]
    ops: List[ToolpathOp]

    warnings: List[PlanWarning] = Field(default_factory=list)
    errors: List[PlanError] = Field(default_factory=list)


# =============================================================================
# DEFAULT TOOLPATH PARAMETERS
# =============================================================================


# Conservative defaults used by planner (execution defaults; not "design truth")
DEFAULT_TOOLPATHS: Dict[str, Dict[str, Any]] = {
    "T2_1_4_UPCUT": {"max_stepdown_in": 0.125, "stepover_in": 0.11},
    "T3_1_8_UPCUT": {"max_stepdown_in": 0.0625, "stepover_in": 0.06},
    "T1_1_4_DOWNCUT": {"max_stepdown_in": 0.1875, "stepover_in": 0.12},
}
