# services/api/app/schemas/instrument_project.py
"""
Instrument Project Graph — Canonical Project Data Schema (ARCH-001/002/003)

This is Layer 0 of The Production Shop platform architecture.

Every instrument build is represented as one InstrumentProjectData object.
This object is persisted in the Project.data JSONB field — no additional
database tables required.

API surface:
    GET  /api/projects/{id}/design-state
    PUT  /api/projects/{id}/design-state

Rules:
    - Only persisted fields belong here (see PERSISTED vs DERIVED below)
    - All optional fields default to None — missing fields never break existing projects
    - schema_version must be incremented on breaking changes (field rename/removal)
    - Derived values (fret positions, break angle, string tension, toolpaths) are
      NEVER stored here — always compute on demand from engine layer

See docs/PLATFORM_ARCHITECTURE.md for the full architectural context.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Tuple

from pydantic import BaseModel, Field


# =============================================================================
# SCHEMA VERSION
# Increment MINOR on additive changes (new optional fields).
# Increment MAJOR on breaking changes (field removal, rename, type change).
# =============================================================================

CURRENT_SCHEMA_VERSION = "1.1"


# =============================================================================
# ENUMERATIONS
# =============================================================================

class InstrumentCategory(str, Enum):
    """Top-level instrument category."""
    ACOUSTIC_GUITAR = "acoustic_guitar"
    ELECTRIC_GUITAR = "electric_guitar"
    BASS = "bass"
    VIOLIN = "violin"
    MANDOLIN = "mandolin"
    UKULELE = "ukulele"
    BANJO = "banjo"
    CLASSICAL = "classical"
    ARCHTOP = "archtop"
    CUSTOM = "custom"


class BodySymmetry(str, Enum):
    SYMMETRIC = "symmetric"
    ASYMMETRIC = "asymmetric"   # Explorer, Flying V
    OFFSET = "offset"           # Jazzmaster, Jaguar
    UNKNOWN = "unknown"


class BlueprintSource(str, Enum):
    PHOTO = "photo"
    DXF = "dxf"
    MANUAL = "manual"           # user entered manually, overriding blueprint


class NeckJointType(str, Enum):
    BOLT_ON = "bolt_on"
    SET_NECK = "set_neck"
    NECK_THROUGH = "neck_through"
    DOVETAIL = "dovetail"


class TremoloStyle(str, Enum):
    VINTAGE_6SCREW = "vintage_6screw"
    TWO_POINT = "2point"
    FLOYD_ROSE = "floyd_rose"
    HARDTAIL = "hardtail"
    NONE = "none"


class BreakAngleRating(str, Enum):
    ADEQUATE = "adequate"       # >= 6° (Carruth empirical minimum)
    TOO_SHALLOW = "too_shallow" # < 6°
    TOO_STEEP = "too_steep"     # > 38° (mechanical binding risk)


class ManufacturingStatus(str, Enum):
    DRAFT = "draft"
    DESIGN_COMPLETE = "design_complete"
    CAM_APPROVED = "cam_approved"
    IN_PRODUCTION = "in_production"
    COMPLETE = "complete"


# =============================================================================
# LAYER 0 SUB-SCHEMAS
# Each sub-schema lives in its own section and is imported by InstrumentProjectData.
# Sub-schemas with domain-specific depth may be split to domain packages later.
# =============================================================================

# ---------------------------------------------------------------------------
# InstrumentSpec — core instrument dimensions
# ---------------------------------------------------------------------------

class InstrumentSpec(BaseModel):
    """
    Core instrument dimensional specification.

    These are the canonical facts of the instrument — inputs to every
    downstream computation. Changing these invalidates all derived values.
    """
    scale_length_mm: float = Field(
        ...,
        gt=200,
        lt=900,
        description="Nominal scale length in mm (nut to saddle). All fret positions derive from this.",
    )
    fret_count: int = Field(
        default=22,
        ge=12,
        le=30,
        description="Total number of frets.",
    )
    string_count: int = Field(
        default=6,
        ge=4,
        le=12,
        description="Number of strings.",
    )
    nut_width_mm: float = Field(
        default=43.0,
        gt=20,
        lt=80,
        description="Nut width in mm.",
    )
    heel_width_mm: float = Field(
        default=56.0,
        gt=30,
        lt=100,
        description="Fretboard width at heel / body joint in mm.",
    )
    neck_angle_degrees: float = Field(
        default=0.0,
        ge=-5.0,
        le=10.0,
        description=(
            "Neck angle relative to body top surface in degrees. "
            "0 = flat (Fender bolt-on), positive = angled back (Gibson). "
            "Critical input for bridge height and break angle chain."
        ),
    )
    neck_joint_type: NeckJointType = Field(
        default=NeckJointType.BOLT_ON,
        description="Neck attachment method.",
    )
    body_join_fret: int = Field(
        default=14,
        ge=10,
        le=22,
        description="Fret number at which neck meets body.",
    )
    tremolo_style: TremoloStyle = Field(
        default=TremoloStyle.HARDTAIL,
        description="Bridge/tremolo hardware type.",
    )
    # Multi-scale / fan-fret extension (optional)
    bass_scale_length_mm: Optional[float] = Field(
        default=None,
        description="Bass-side scale length for multiscale instruments (mm). None = single scale.",
    )
    perpendicular_fret: Optional[int] = Field(
        default=None,
        description="Fret number where strings are perpendicular to centerline (multiscale only).",
    )

    @property
    def is_multiscale(self) -> bool:
        return self.bass_scale_length_mm is not None


# ---------------------------------------------------------------------------
# BlueprintDerivedGeometry — output of Blueprint Reader
# ---------------------------------------------------------------------------

class BlueprintDerivedGeometry(BaseModel):
    """
    Geometry derived from Blueprint Reader import.

    Produced by the blueprint pipeline (phases 1–4) and written into
    the project on completion. Manual overrides preserve the original
    blueprint data under blueprint_original.

    Source / provenance tracking is mandatory — every field must record
    whether it came from the photo/DXF pipeline or was manually entered.
    """
    source: BlueprintSource = Field(
        ...,
        description="Origin of the geometry data.",
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Detection confidence 0-1. 1.0 = high confidence from clean source.",
    )
    # Body outline
    body_outline_mm: Optional[List[Tuple[float, float]]] = Field(
        default=None,
        description="Body outline as (x, y) point list in mm, counterclockwise.",
    )
    # Centerline
    centerline_x_mm: Optional[float] = Field(
        default=None,
        description="Body centerline X position in mm (from CenterlineResult).",
    )
    axis_angle_deg: float = Field(
        default=0.0,
        description="Symmetry axis angle from vertical in degrees. Non-zero for Flying V / Explorer.",
    )
    symmetry: BodySymmetry = Field(
        default=BodySymmetry.UNKNOWN,
        description="Body symmetry classification.",
    )
    symmetry_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="How symmetric the outline is (1.0 = perfect). From centerline.compute_symmetry_score().",
    )
    # Extracted dimensions (may be None if not detected)
    body_length_mm: Optional[float] = None
    lower_bout_mm: Optional[float] = None
    upper_bout_mm: Optional[float] = None
    waist_mm: Optional[float] = None
    scale_length_detected_mm: Optional[float] = Field(
        default=None,
        description="Scale length detected from blueprint (may differ from spec.scale_length_mm if manually overridden).",
    )
    instrument_classification: Optional[str] = Field(
        default=None,
        description="Instrument type detected from blueprint (e.g. 'acoustic_guitar', 'electric_guitar').",
    )
    # Provenance
    captured_at: Optional[str] = Field(
        default=None,
        description="ISO timestamp of blueprint import.",
    )
    notes: List[str] = Field(
        default_factory=list,
        description="Detection warnings or notes from the blueprint pipeline.",
    )
    # When source is MANUAL, preserve the original blueprint output
    blueprint_original: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Original blueprint-derived values before manual override.",
    )


# ---------------------------------------------------------------------------
# BridgeState — bridge geometry and saddle chain
# ---------------------------------------------------------------------------

class BridgeState(BaseModel):
    """
    Bridge geometry state as edited in Bridge Lab.

    This is the authoritative source for bridge-related values in the project.
    Break angle, downforce, and compensation offsets are DERIVED from these
    inputs by the Geometry Engine — they are never stored here.

    Edited in Bridge Lab, committed to project on explicit user action.
    String Tension utility reads from these values when in project context.
    """
    # Saddle location
    saddle_line_from_nut_mm: Optional[float] = Field(
        default=None,
        description=(
            "Saddle line distance from nut in mm. "
            "Theoretical = scale_length_mm + average compensation. "
            "Set by bridge placement calculation."
        ),
    )
    # String spacing at bridge
    string_spread_mm: float = Field(
        default=54.0,
        description="String spread at bridge saddle in mm (treble E to bass E).",
    )
    # Compensation
    compensation_treble_mm: float = Field(
        default=2.0,
        description="Treble E string intonation compensation offset in mm.",
    )
    compensation_bass_mm: float = Field(
        default=4.0,
        description="Bass E string intonation compensation offset in mm.",
    )
    # Saddle geometry (inputs to break angle calculation)
    saddle_slot_width_mm: float = Field(
        default=3.2,
        description="Width of the saddle slot in mm.",
    )
    saddle_slot_depth_mm: float = Field(
        default=10.0,
        description="Depth of the saddle slot in mm.",
    )
    saddle_projection_mm: float = Field(
        default=2.5,
        gt=0,
        description=(
            "Saddle height above the bridge TOP SURFACE in mm. "
            "NOT above the bridge plate. "
            "Inputs to break angle via Geometry Engine. "
            "Practical minimum: 1.6mm (1/16\"). See BRIDGE_BREAK_ANGLE_DERIVATION.md."
        ),
    )
    pin_to_saddle_center_mm: float = Field(
        default=5.5,
        description="Horizontal distance from bridge pin center to saddle crown center in mm.",
    )
    slot_offset_mm: float = Field(
        default=1.2,
        description=(
            "Slot offset: distance the slotted pin hole moves the string exit "
            "point closer to the saddle (mm). Typical: 1.0–1.5mm."
        ),
    )
    # Bridge family preset ID (if seeded from preset)
    preset_id: Optional[str] = Field(
        default=None,
        description="Bridge family preset ID (e.g. 'om', 'dread', 'strat_tele').",
    )
    # Metadata
    last_committed_at: Optional[str] = Field(
        default=None,
        description="ISO timestamp of last explicit Bridge Lab commit.",
    )


# ---------------------------------------------------------------------------
# NeckState — neck geometry state
# ---------------------------------------------------------------------------

class NeckState(BaseModel):
    """
    Neck geometry as edited in the Neck subsystem.

    Pocket depth, projection, and nut break angle are DERIVED from these
    inputs by the Geometry Engine — not stored here.
    """
    # Heel geometry
    heel_length_mm: Optional[float] = Field(
        default=None,
        description="Neck heel length in mm.",
    )
    heel_depth_mm: Optional[float] = Field(
        default=None,
        description="Neck heel depth (pocket depth input) in mm.",
    )
    # Headstock
    headstock_type: Literal["angled", "flat", "scarf"] = Field(
        default="flat",
        description="Headstock type. Angled = Gibson/PRS. Flat = Fender. Scarf = classical.",
    )
    headstock_angle_deg: float = Field(
        default=0.0,
        ge=0.0,
        le=20.0,
        description="Headstock pitch-back angle in degrees. Gibson: 14–17°. PRS: 10°. Fender: 0°.",
    )
    # Fretboard radius
    nut_radius_inches: float = Field(
        default=9.5,
        description="Fretboard radius at nut position (inches). Compound radius start.",
    )
    heel_radius_inches: float = Field(
        default=14.0,
        description="Fretboard radius at heel (inches). Compound radius end.",
    )
    # Profile
    profile_shape: Literal["c", "d", "v", "u", "asymmetric"] = Field(
        default="c",
        description="Neck profile shape identifier.",
    )
    thickness_at_1st_mm: Optional[float] = Field(
        default=None,
        description="Neck thickness at 1st fret in mm.",
    )
    thickness_at_12th_mm: Optional[float] = Field(
        default=None,
        description="Neck thickness at 12th fret in mm.",
    )


# ---------------------------------------------------------------------------
# MaterialSelection — component material choices
# ---------------------------------------------------------------------------

class MaterialSelection(BaseModel):
    """
    Material (wood species) selections per instrument component role.

    Each field holds the species ID from the tonewood registry.
    Use GET /api/system/materials/tonewoods to fetch valid IDs.

    The Materials Intelligence engine computes acoustic properties,
    machining guidance, and recommendations from these selections.
    The Analyzer can validate them against measured acoustic behavior.
    """
    top: Optional[str] = Field(
        default=None,
        description="Soundboard / top wood species ID (e.g. 'spruce_adirondack', 'cedar_western_red').",
    )
    back_sides: Optional[str] = Field(
        default=None,
        description="Back and sides wood species ID.",
    )
    neck: Optional[str] = Field(
        default=None,
        description="Neck wood species ID (e.g. 'mahogany_honduran', 'maple_hard').",
    )
    fretboard: Optional[str] = Field(
        default=None,
        description="Fretboard wood species ID (e.g. 'ebony_african', 'rosewood_east_indian').",
    )
    bridge: Optional[str] = Field(
        default=None,
        description="Bridge plate / saddle platform wood species ID.",
    )
    brace_stock: Optional[str] = Field(
        default=None,
        description="Top bracing wood species ID (e.g. 'spruce_adirondack', 'spruce_sitka').",
    )
    binding: Optional[str] = Field(
        default=None,
        description="Binding material species ID (optional).",
    )
    # Metadata
    selection_notes: Optional[str] = Field(
        default=None,
        description="Free-text notes on material choices.",
    )




# ---------------------------------------------------------------------------
# BodyConfig — electric/acoustic body configuration (GEN-2)
# ---------------------------------------------------------------------------

class BodyConfig(BaseModel):
    """
    Body configuration for electric and acoustic instruments.

    Captures build-specific body options that affect CAM operations and
    construction decisions. Seeds from model specs in GEN-1.
    """
    pickup_config: Optional[str] = Field(
        default=None,
        description="Pickup configuration (e.g., 'sss', 'hss', 'hh', 'p90_single').",
    )
    tremolo_style: Optional[str] = Field(
        default=None,
        description="Tremolo type (e.g., 'vintage_6screw', '2point', 'floyd_rose', 'hardtail').",
    )
    belly_contour: bool = Field(
        default=True,
        description="Whether body has belly contour (comfort carve on back).",
    )
    arm_contour: bool = Field(
        default=True,
        description="Whether body has forearm contour.",
    )
    rear_routed: bool = Field(
        default=True,
        description="Whether electronics cavity is rear-routed (vs. front-routed like LP).",
    )
    stock_thickness_mm: Optional[float] = Field(
        default=None,
        gt=20,
        lt=100,
        description="Body blank thickness in mm.",
    )
    body_style_id: Optional[str] = Field(
        default=None,
        description="Electric body style reference ID (e.g., 'stratocaster', 'les_paul').",
    )
    acoustic_body_style_id: Optional[str] = Field(
        default=None,
        description="Acoustic body style ID (e.g., 'dreadnought', 'om', 'jumbo').",
    )


# ---------------------------------------------------------------------------
# AnalyzerObservation — tap-tone measurement result
# ---------------------------------------------------------------------------

class AnalyzerObservation(BaseModel):
    """
    Advisory observation from the acoustic analyzer.

    The Analyzer ENRICHES the project with measurement data.
    It does NOT override bridge_state, material_selection, or spec.

    Hard boundary: tap-tone-pi produces viewer_pack data.
    This platform interprets that data. Never import tap-tone-pi code.
    See docs/ANALYZER_BOUNDARY_SPEC.md.
    """
    run_id: str = Field(
        ...,
        description="RMOS run ID for this measurement session.",
    )
    specimen_id: str = Field(
        ...,
        description="Specimen identifier (may be a component: top, back, complete body).",
    )
    observed_at: str = Field(
        ...,
        description="ISO timestamp of measurement.",
    )
    # Acoustic findings
    primary_modes_hz: List[float] = Field(
        default_factory=list,
        description="Primary modal frequencies detected (Hz).",
    )
    wsi: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Wolf Susceptibility Index (0-1). Lower is better.",
    )
    tonal_character: Optional[str] = Field(
        default=None,
        description="Interpreted tonal character ('warm', 'bright', 'balanced', etc.).",
    )
    # Advisory content
    findings: List[str] = Field(
        default_factory=list,
        description="Human-readable findings from design_advisor.py.",
    )
    reference_instrument: Optional[str] = Field(
        default=None,
        description="Reference instrument ID used for comparison (e.g. 'martin_d28_1937').",
    )
    # Confidence
    interpretation_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence in the interpretation (0-1).",
    )


# ---------------------------------------------------------------------------
# ManufacturingState — CAM approval and production status
# ---------------------------------------------------------------------------

class ManufacturingState(BaseModel):
    """
    Manufacturing readiness state.

    CAM operations read from this to determine whether the project
    has been validated for production. Toolpaths are NOT stored here —
    they are generated on demand from validated project state.
    """
    status: ManufacturingStatus = Field(
        default=ManufacturingStatus.DRAFT,
        description="Current manufacturing status.",
    )
    approved_at: Optional[str] = Field(
        default=None,
        description="ISO timestamp of CAM approval.",
    )
    approved_by: Optional[str] = Field(
        default=None,
        description="User ID who approved for production.",
    )
    operations_completed: List[str] = Field(
        default_factory=list,
        description="List of completed CNC operations (e.g. 'neck_pocket', 'body_contour', 'fret_slots').",
    )
    notes: Optional[str] = Field(
        default=None,
        description="Manufacturing notes.",
    )


# =============================================================================
# ROOT SCHEMA — InstrumentProjectData
# This is what lives in Project.data (JSONB)
# =============================================================================

class InstrumentProjectData(BaseModel):
    """
    The canonical Instrument Project Graph.

    Stored in Project.data JSONB field.
    Accessed via GET/PUT /api/projects/{id}/design-state

    All fields except schema_version and instrument_type are optional to ensure
    backward compatibility with projects created before specific sub-schemas existed.
    Missing fields never break existing projects.

    PERSIST:
        instrument_type, spec, blueprint_geometry, bridge_state,
        neck_state, material_selection, analyzer_observations, manufacturing_state

    DERIVE (never store):
        fret_positions, break_angle_deg, string_tension_lbs,
        stiffness_index, compensation_offsets, cam_toolpaths
    """

    schema_version: str = Field(
        default=CURRENT_SCHEMA_VERSION,
        description="Schema version for migration safety. Increment on breaking changes.",
    )

    # --- Core identity ---
    instrument_type: InstrumentCategory = Field(
        ...,
        description="Instrument category. Required on all saves.",
    )

    # --- Design spec (mandatory for meaningful computation) ---
    spec: Optional[InstrumentSpec] = Field(
        default=None,
        description="Core instrument dimensional spec. Required for engine computations.",
    )

    # --- Blueprint geometry (from Blueprint Reader) ---
    blueprint_geometry: Optional[BlueprintDerivedGeometry] = Field(
        default=None,
        description="Geometry derived from Blueprint Reader import. Null until blueprint is processed.",
    )

    # --- Bridge Lab state ---
    bridge_state: Optional[BridgeState] = Field(
        default=None,
        description="Bridge geometry state. Edited in Bridge Lab, committed explicitly.",
    )

    # --- Neck state ---
    neck_state: Optional[NeckState] = Field(
        default=None,
        description="Neck geometry state.",
    )

    # --- Material selections ---
    material_selection: Optional[MaterialSelection] = Field(
        default=None,
        description="Wood species selection per instrument component role.",
    )

    # --- Body configuration (GEN-2) ---
    body_config: Optional[BodyConfig] = Field(
        default=None,
        description="Body configuration for electric/acoustic instruments. Seeds from model spec.",
    )

    # --- Analyzer observations (advisory enrichment) ---
    analyzer_observations: List[AnalyzerObservation] = Field(
        default_factory=list,
        description=(
            "Acoustic analyzer observations. Advisory only — never override design state. "
            "Appended by analyzer on each measurement run."
        ),
    )

    # --- Manufacturing state ---
    manufacturing_state: Optional[ManufacturingState] = Field(
        default=None,
        description="CAM approval and production status. Set by production workflow.",
    )

    # --- Freeform extension area (use sparingly) ---
    custom_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description=(
            "Escape hatch for instrument-specific or experimental data. "
            "Should be promoted to typed fields once stable."
        ),
    )

    class Config:
        # Allow unknown fields in for forward-compatibility reading old/future versions
        extra = "allow"

    def is_ready_for_cam(self) -> bool:
        """Check if project has minimum data for CAM operations."""
        return (
            self.spec is not None
            and self.instrument_type is not None
        )

    def has_bridge_geometry(self) -> bool:
        """Check if bridge state has been committed."""
        return (
            self.bridge_state is not None
            and self.bridge_state.saddle_line_from_nut_mm is not None
        )

    def has_material_selection(self) -> bool:
        """Check if any materials have been selected."""
        if self.material_selection is None:
            return False
        return any([
            self.material_selection.top,
            self.material_selection.neck,
            self.material_selection.fretboard,
        ])


# =============================================================================
# REQUEST / RESPONSE MODELS for the project state API
# =============================================================================

class DesignStateResponse(BaseModel):
    """Response from GET /api/projects/{id}/design-state"""
    project_id: str
    name: str
    instrument_type: Optional[str]
    design_state: Optional[InstrumentProjectData]
    created_at: str
    updated_at: str


class DesignStatePutRequest(BaseModel):
    """Request body for PUT /api/projects/{id}/design-state"""
    design_state: InstrumentProjectData
    commit_message: Optional[str] = Field(
        default=None,
        description="Optional human-readable description of what changed (for audit trail).",
    )
