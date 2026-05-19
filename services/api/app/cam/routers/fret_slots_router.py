"""
Fret Slots Router

Fret slot preview endpoint for guitar neck CAM operations.
Extracted from stub_routes.py during decomposition.

GOVERNED PREVIEW STATUS: CANDIDATE (normalizing to standard)
Gate Semantics: Derived from messages (error→RED, warning→YELLOW, else→GREEN)
Coordinate System: Nut-origin, X=scale length, Y=bass-to-treble, Z=depth

Normalization: Dev Order 5C (2026-05-09)
Reference: nut_slot_cam.py is canonical pattern
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.instrument_geometry import load_model_spec
from app.instrument_geometry.neck.neck_profiles import FretboardSpec
from app.calculators.fret_slots_cam import generate_fret_slot_toolpaths, compute_cam_statistics
from app.calculators.fret_slots_fan_cam import generate_fan_fret_cam
from app.rmos.context import RmosContext


router = APIRouter(tags=["cam", "fret-slots"])


# --- Governed Preview Standard Types (5C Normalization) ---

class CamGate(str, Enum):
    """CAM safety gate classification."""
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


class CamIssue(BaseModel):
    """Structured issue for governed preview."""
    code: str
    severity: Literal["green", "yellow", "red"]
    message: str
    field: Optional[str] = None


class CoordinateSystem(BaseModel):
    """Coordinate system metadata for governed preview."""
    units: str = "mm"
    origin: str
    x_axis: str
    y_axis: str
    z_axis: str
    z_zero: str
    handedness: str = "right_handed"
    frame: str = "local_part"
    notes: Optional[str] = None
    coordinate_confidence: Optional[str] = None


class PreviewMetadata(BaseModel):
    """Generator metadata for governed preview."""
    generator_id: str
    generator_version: Optional[str] = None
    preview_only: bool = True
    machine_ready: bool = False
    risk_class: str = "A"
    generated_at: str
    mode: Optional[str] = None


# Fret Slot coordinate system constant (documented from fret_slots_cam.py behavior)
FRET_SLOT_COORDINATE_SYSTEM = CoordinateSystem(
    units="mm",
    origin="nut_edge",
    x_axis="scale_length_direction",
    y_axis="bass_to_treble",
    z_axis="depth_into_fretboard",
    z_zero="top_of_fretboard",
    handedness="right_handed",
    frame="local_part",
    coordinate_confidence="documented_from_current_code",
)

# Fan Fret coordinate system (extends standard with angled slot notes)
FAN_FRET_COORDINATE_SYSTEM = CoordinateSystem(
    units="mm",
    origin="nut_edge",
    x_axis="scale_length_direction",
    y_axis="bass_to_treble",
    z_axis="depth_into_fretboard",
    z_zero="top_of_fretboard",
    handedness="right_handed",
    frame="local_part",
    notes="Fan fret slots are angled; each slot has separate bass and treble X positions. "
          "Perpendicular fret is marked with is_perpendicular=true.",
    coordinate_confidence="documented_from_current_code",
)


class FretSlotsPreviewRequest(BaseModel):
    """Request for fret slot preview."""
    model_id: str
    fret_count: int = Field(22, ge=1, le=36)
    slot_width_mm: float = Field(0.58, gt=0, le=2.0)
    slot_depth_mm: float = Field(3.0, gt=0, le=10.0)
    bit_diameter_mm: float = Field(0.58, gt=0, le=10.0)
    mode: Optional[str] = Field("standard", pattern="^(standard|fan_fret)$")
    perpendicular_fret: Optional[int] = None
    bass_scale_mm: Optional[float] = None
    treble_scale_mm: Optional[float] = None


class FretSlotOut(BaseModel):
    """Single fret slot data."""
    fret: int
    stringIndex: int = 0
    positionMm: float
    widthMm: float
    depthMm: float
    angleRad: Optional[float] = None
    isPerpendicular: bool = False


class RmosMessageOut(BaseModel):
    """RMOS validation message."""
    code: str
    severity: str
    message: str
    context: Dict[str, Any] = Field(default_factory=dict)
    hint: Optional[str] = None


class FretSlotsPreviewResponse(BaseModel):
    """
    Response for fret slot preview.

    GOVERNED PREVIEW fields (5C normalization):
    - operation, status, gate, units: standard envelope
    - coordinate_system: spatial reference metadata
    - canonical_toolpath: wrapper for slots data
    - warnings, errors, issues: structured validation output
    - metadata: generator provenance

    LEGACY fields (preserved for frontend compatibility):
    - model_id, fret_count, slots, messages, statistics
    """
    # --- Governed Preview Standard Fields ---
    operation: str = "fret_slot_preview"
    status: str = "preview"
    gate: CamGate = CamGate.GREEN
    units: str = "mm"
    coordinate_system: CoordinateSystem = Field(default_factory=lambda: FRET_SLOT_COORDINATE_SYSTEM)
    canonical_toolpath: Optional[Dict[str, Any]] = None
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    issues: List[CamIssue] = Field(default_factory=list)
    metadata: Optional[PreviewMetadata] = None

    # --- Legacy Fields (preserved) ---
    model_id: str
    fret_count: int
    slots: List[FretSlotOut]
    messages: List[RmosMessageOut]
    statistics: Optional[Dict[str, Any]] = None


def _derive_gate_from_messages(messages: List[RmosMessageOut]) -> CamGate:
    """
    Derive gate status from RMOS messages.

    Gate escalation (never de-escalates):
    - error severity → RED
    - warning severity → YELLOW (if not already RED)
    - info/other → GREEN (default)
    """
    gate = CamGate.GREEN
    for msg in messages:
        if msg.severity == "error":
            return CamGate.RED  # RED is terminal
        if msg.severity == "warning" and gate != CamGate.RED:
            gate = CamGate.YELLOW
    return gate


def _messages_to_issues(messages: List[RmosMessageOut]) -> List[CamIssue]:
    """Convert RMOS messages to structured CamIssue format."""
    severity_map = {
        "error": "red",
        "warning": "yellow",
        "info": "green",
    }
    return [
        CamIssue(
            code=msg.code,
            severity=severity_map.get(msg.severity, "green"),
            message=msg.message,
            field=None,
        )
        for msg in messages
    ]


def _normalize_statistics(
    raw_stats: Optional[Dict[str, Any]],
    slot_count: int,
) -> Dict[str, Any]:
    """
    Normalize statistics to governed preview standard.

    Adds required core statistics alongside existing fields.
    """
    if raw_stats is None:
        return {
            "operation_count": slot_count,
            "move_count": slot_count * 4,  # rapid + plunge + cut + retract per slot
            "warning_count": 0,
            "error_count": 0,
        }

    # Add required core statistics if missing
    normalized = dict(raw_stats)
    normalized.setdefault("operation_count", normalized.get("slot_count", slot_count))
    normalized.setdefault("move_count", slot_count * 4)
    normalized.setdefault("warning_count", 0)
    normalized.setdefault("error_count", 0)
    return normalized


@router.post("/fret_slots/preview")
def preview_fret_slots(req: FretSlotsPreviewRequest) -> FretSlotsPreviewResponse:
    """
    Preview fret slot positions using real calculator.

    GOVERNED PREVIEW endpoint (5C/5D normalization).
    Returns standard preview envelope with legacy fields preserved.

    Modes:
    - standard: Perpendicular fret slots (5C)
    - fan_fret: Angled multi-scale fret slots (5D)
    """
    messages: List[RmosMessageOut] = []
    mode = req.mode or "standard"
    is_fan_fret = mode == "fan_fret"

    try:
        model_spec = load_model_spec(req.model_id)
        scale_length_mm = model_spec.scale.scale_length_mm
        nut_width_mm = 42.0
        heel_width_mm = 56.0
    except (FileNotFoundError, KeyError, ValueError, TypeError, AttributeError):
        messages.append(RmosMessageOut(
            code="MODEL_NOT_FOUND",
            severity="warning",
            message=f"Model '{req.model_id}' not found, using defaults",
            context={"model_id": req.model_id},
            hint="Check model registry for available model IDs",
        ))
        scale_length_mm = 648.0
        nut_width_mm = 42.0
        heel_width_mm = 56.0

    spec = FretboardSpec(
        nut_width_mm=nut_width_mm,
        heel_width_mm=heel_width_mm,
        scale_length_mm=scale_length_mm,
        fret_count=req.fret_count,
    )

    context = RmosContext(model_id=req.model_id, model_spec={})
    toolpaths = []
    statistics = None

    try:
        if is_fan_fret:
            # Fan fret mode: use dedicated fan fret generator (5D wiring)
            if req.bass_scale_mm is None or req.treble_scale_mm is None:
                messages.append(RmosMessageOut(
                    code="FAN_FRET_PARAMS_MISSING",
                    severity="error",
                    message="Fan fret mode requires bass_scale_mm and treble_scale_mm",
                    context={"mode": mode},
                    hint="Provide both scale lengths for multi-scale fretting",
                ))
            else:
                perpendicular = req.perpendicular_fret or 7
                cam_output = generate_fan_fret_cam(
                    spec=spec,
                    context=context,
                    treble_scale_mm=req.treble_scale_mm,
                    bass_scale_mm=req.bass_scale_mm,
                    perpendicular_fret=perpendicular,
                    slot_depth_mm=req.slot_depth_mm,
                    slot_width_mm=req.slot_width_mm,
                    safe_z_mm=5.0,
                    post_id="GRBL",
                )
                toolpaths = cam_output.toolpaths
                statistics = cam_output.statistics
        else:
            # Standard mode: perpendicular fret slots
            toolpaths = generate_fret_slot_toolpaths(
                spec=spec,
                context=context,
                slot_depth_mm=req.slot_depth_mm,
                slot_width_mm=req.slot_width_mm,
            )
            statistics = compute_cam_statistics(toolpaths)
    except (ValueError, TypeError, KeyError, AttributeError, ZeroDivisionError) as e:
        messages.append(RmosMessageOut(
            code="CALCULATION_ERROR",
            severity="error",
            message=f"Fret slot calculation failed: {str(e)}",
            context={"mode": mode},
        ))
        toolpaths = []
        statistics = None

    slots = [
        FretSlotOut(
            fret=tp.fret_number,
            positionMm=tp.position_mm,
            widthMm=tp.width_mm,
            depthMm=tp.slot_depth_mm,
            angleRad=tp.angle_rad if hasattr(tp, 'angle_rad') else None,
            isPerpendicular=tp.is_perpendicular if hasattr(tp, 'is_perpendicular') else False,
        )
        for tp in toolpaths
    ]

    if req.bit_diameter_mm > req.slot_width_mm * 1.5:
        messages.append(RmosMessageOut(
            code="BIT_TOO_LARGE",
            severity="warning",
            message=f"Bit diameter ({req.bit_diameter_mm}mm) exceeds slot width ({req.slot_width_mm}mm)",
            context={"bit_diameter_mm": req.bit_diameter_mm, "slot_width_mm": req.slot_width_mm},
            hint="Use a smaller bit or increase slot width",
        ))

    if req.slot_depth_mm > 5.0:
        messages.append(RmosMessageOut(
            code="SLOT_DEPTH_HIGH",
            severity="info",
            message=f"Slot depth ({req.slot_depth_mm}mm) is deeper than typical (2.5-3.5mm)",
            context={"slot_depth_mm": req.slot_depth_mm},
        ))

    # --- Governed Preview Normalization (5C/5D) ---
    gate = _derive_gate_from_messages(messages)
    issues = _messages_to_issues(messages)
    warnings_list = [m.message for m in messages if m.severity == "warning"]
    errors_list = [m.message for m in messages if m.severity == "error"]

    normalized_stats = _normalize_statistics(statistics, req.fret_count)
    normalized_stats["warning_count"] = len(warnings_list)
    normalized_stats["error_count"] = len(errors_list)

    # Mode-aware operation and coordinate system (5D)
    operation = "fan_fret_preview" if is_fan_fret else "fret_slot_preview"
    coordinate_system = FAN_FRET_COORDINATE_SYSTEM if is_fan_fret else FRET_SLOT_COORDINATE_SYSTEM
    generator_id = "fret_slots_fan_cam" if is_fan_fret else "fret_slots_cam"

    metadata = PreviewMetadata(
        generator_id=generator_id,
        generator_version="1.0.0",
        preview_only=True,
        machine_ready=False,
        risk_class="A",
        generated_at=datetime.now(timezone.utc).isoformat(),
        mode=mode,
    )

    canonical_toolpath = {
        "slots": [slot.model_dump() for slot in slots],
        "slot_count": len(slots),
        "mode": mode,
    }

    # Add fan-fret specific fields to canonical_toolpath
    if is_fan_fret and req.bass_scale_mm and req.treble_scale_mm:
        canonical_toolpath["bass_scale_mm"] = req.bass_scale_mm
        canonical_toolpath["treble_scale_mm"] = req.treble_scale_mm
        canonical_toolpath["perpendicular_fret"] = req.perpendicular_fret or 7

    return FretSlotsPreviewResponse(
        # Governed preview fields
        operation=operation,
        status="preview",
        gate=gate,
        units="mm",
        coordinate_system=coordinate_system,
        canonical_toolpath=canonical_toolpath,
        warnings=warnings_list,
        errors=errors_list,
        issues=issues,
        metadata=metadata,
        # Legacy fields (preserved)
        model_id=req.model_id,
        fret_count=req.fret_count,
        slots=slots,
        messages=messages,
        statistics=normalized_stats,
    )
