"""
CAM Envelope Validation

CAM Dev Order 7S: Pre-export envelope/bounds validation.

Provides:
  - Bounds representation (2D/3D)
  - Machine envelope representation
  - Envelope validation evaluation (GREEN/YELLOW/RED)
  - Default machine envelope registry

7S invariants:
  - execution_authorized always False
  - machine_output_allowed always False

Salvaged pattern:
  Pre-export envelope check concept from OpenBuilds-CAM review.
  OpenBuilds lacked this check; 7S implements it as governed validation.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


EnvelopeGate = Literal["green", "yellow", "red"]
OriginMode = Literal["lower_left", "center", "machine_zero"]


class CAMBounds2D(BaseModel):
    """
    2D/3D bounding box representation.

    All dimensions in millimeters.
    """

    min_x_mm: float = Field(..., description="Minimum X coordinate (mm)")
    max_x_mm: float = Field(..., description="Maximum X coordinate (mm)")
    min_y_mm: float = Field(..., description="Minimum Y coordinate (mm)")
    max_y_mm: float = Field(..., description="Maximum Y coordinate (mm)")
    min_z_mm: Optional[float] = Field(default=None, description="Minimum Z coordinate (mm)")
    max_z_mm: Optional[float] = Field(default=None, description="Maximum Z coordinate (mm)")

    @property
    def width_mm(self) -> float:
        """Width in X direction."""
        return self.max_x_mm - self.min_x_mm

    @property
    def height_mm(self) -> float:
        """Height in Y direction."""
        return self.max_y_mm - self.min_y_mm

    @property
    def depth_mm(self) -> Optional[float]:
        """Depth in Z direction (if Z bounds present)."""
        if self.min_z_mm is not None and self.max_z_mm is not None:
            return self.max_z_mm - self.min_z_mm
        return None

    def contains_point(self, x: float, y: float, z: Optional[float] = None) -> bool:
        """Check if a point is within bounds."""
        in_xy = (
            self.min_x_mm <= x <= self.max_x_mm and
            self.min_y_mm <= y <= self.max_y_mm
        )
        if z is not None and self.min_z_mm is not None and self.max_z_mm is not None:
            return in_xy and self.min_z_mm <= z <= self.max_z_mm
        return in_xy


class CAMMachineEnvelope(BaseModel):
    """
    Machine envelope/working area definition.

    All dimensions in millimeters.
    """

    machine_id: str = Field(..., description="Machine identifier")
    display_name: str = Field(default="", description="Human-readable name")

    max_x_mm: float = Field(..., description="Maximum X travel (mm)")
    max_y_mm: float = Field(..., description="Maximum Y travel (mm)")
    max_z_mm: Optional[float] = Field(default=None, description="Maximum Z travel (mm)")

    origin_mode: OriginMode = Field(
        default="lower_left",
        description="Origin position convention"
    )

    margin_mm: float = Field(
        default=5.0,
        description="Safety margin from envelope edges (mm)"
    )

    description: str = Field(default="", description="Machine description")

    def get_safe_bounds(self) -> CAMBounds2D:
        """Get bounds with safety margin applied."""
        return CAMBounds2D(
            min_x_mm=self.margin_mm,
            max_x_mm=self.max_x_mm - self.margin_mm,
            min_y_mm=self.margin_mm,
            max_y_mm=self.max_y_mm - self.margin_mm,
            min_z_mm=-self.max_z_mm if self.max_z_mm else None,
            max_z_mm=0.0 if self.max_z_mm else None,
        )


MACHINE_ENVELOPE_REGISTRY: Dict[str, CAMMachineEnvelope] = {
    "generic_3018": CAMMachineEnvelope(
        machine_id="generic_3018",
        display_name="Generic 3018 CNC",
        max_x_mm=300.0,
        max_y_mm=180.0,
        max_z_mm=45.0,
        origin_mode="lower_left",
        margin_mm=5.0,
        description="Common hobby 3018-style CNC router",
    ),
    "generic_6040": CAMMachineEnvelope(
        machine_id="generic_6040",
        display_name="Generic 6040 CNC",
        max_x_mm=600.0,
        max_y_mm=400.0,
        max_z_mm=75.0,
        origin_mode="lower_left",
        margin_mm=5.0,
        description="Common 6040-style CNC router",
    ),
    "luthier_body_router": CAMMachineEnvelope(
        machine_id="luthier_body_router",
        display_name="Luthier Body Router",
        max_x_mm=700.0,
        max_y_mm=500.0,
        max_z_mm=100.0,
        origin_mode="lower_left",
        margin_mm=10.0,
        description="Typical luthier CNC for guitar body work",
    ),
    "luthier_neck_router": CAMMachineEnvelope(
        machine_id="luthier_neck_router",
        display_name="Luthier Neck Router",
        max_x_mm=800.0,
        max_y_mm=200.0,
        max_z_mm=80.0,
        origin_mode="lower_left",
        margin_mm=5.0,
        description="Luthier CNC sized for neck work",
    ),
    "laser_k40": CAMMachineEnvelope(
        machine_id="laser_k40",
        display_name="K40 Laser",
        max_x_mm=300.0,
        max_y_mm=200.0,
        max_z_mm=None,
        origin_mode="lower_left",
        margin_mm=5.0,
        description="Common K40-style CO2 laser cutter",
    ),
}


MACHINE_ENVELOPE_INDEX: Dict[str, CAMMachineEnvelope] = {}


def _initialize_envelope_index() -> None:
    """Initialize envelope index from registry."""
    for machine_id, envelope in MACHINE_ENVELOPE_REGISTRY.items():
        MACHINE_ENVELOPE_INDEX[machine_id] = envelope


_initialize_envelope_index()


class CAMEnvelopeValidationEvaluation(BaseModel):
    """
    Envelope validation evaluation result.

    7S invariants (model-enforced):
      - execution_authorized always False
      - machine_output_allowed always False
    """

    evaluation_id: str = Field(
        default_factory=lambda: f"envelope-eval-{uuid4().hex[:12]}",
        description="Unique evaluation identifier"
    )

    subject_id: str = Field(..., description="ID of subject being validated")
    subject_type: str = Field(
        default="bounds",
        description="Type of subject (bounds, export_object, workspace)"
    )

    gate: EnvelopeGate = Field(..., description="Validation gate result")

    bounds_checked: CAMBounds2D = Field(..., description="Bounds that were checked")
    machine_envelope: CAMMachineEnvelope = Field(
        ..., description="Machine envelope used for validation"
    )

    blocking_issues: List[str] = Field(
        default_factory=list,
        description="RED blocking issues"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="YELLOW warnings"
    )

    margin_violations: List[str] = Field(
        default_factory=list,
        description="Specific margin/edge violations"
    )

    execution_authorized: bool = Field(
        default=False,
        description="Always False — 7S does not authorize execution"
    )
    machine_output_allowed: bool = Field(
        default=False,
        description="Always False — 7S does not allow machine output"
    )

    deterministic_evaluation_hash: str = Field(
        default="",
        description="Deterministic hash of evaluation"
    )

    evaluated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Evaluation timestamp"
    )

    @model_validator(mode="after")
    def enforce_7s_invariants(self) -> "CAMEnvelopeValidationEvaluation":
        """Enforce 7S invariants."""
        if self.execution_authorized:
            raise ValueError(
                "7S invariant violation: execution_authorized must be False"
            )
        if self.machine_output_allowed:
            raise ValueError(
                "7S invariant violation: machine_output_allowed must be False"
            )
        return self

    def compute_hash(self) -> str:
        """Compute deterministic hash of evaluation."""
        hash_input = {
            "subject_id": self.subject_id,
            "gate": self.gate,
            "bounds": {
                "min_x": self.bounds_checked.min_x_mm,
                "max_x": self.bounds_checked.max_x_mm,
                "min_y": self.bounds_checked.min_y_mm,
                "max_y": self.bounds_checked.max_y_mm,
                "min_z": self.bounds_checked.min_z_mm,
                "max_z": self.bounds_checked.max_z_mm,
            },
            "envelope": {
                "machine_id": self.machine_envelope.machine_id,
                "max_x": self.machine_envelope.max_x_mm,
                "max_y": self.machine_envelope.max_y_mm,
                "max_z": self.machine_envelope.max_z_mm,
            },
            "blocking_issues": sorted(self.blocking_issues),
            "warnings": sorted(self.warnings),
        }
        canonical = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()


CAM_ENVELOPE_EVALUATION_INDEX: Dict[str, CAMEnvelopeValidationEvaluation] = {}


def get_machine_envelope(machine_id: str) -> Optional[CAMMachineEnvelope]:
    """Get machine envelope by ID."""
    return MACHINE_ENVELOPE_INDEX.get(machine_id)


def list_machine_envelopes() -> List[CAMMachineEnvelope]:
    """List all registered machine envelopes."""
    return list(MACHINE_ENVELOPE_INDEX.values())


def register_machine_envelope(envelope: CAMMachineEnvelope) -> None:
    """Register a custom machine envelope."""
    MACHINE_ENVELOPE_INDEX[envelope.machine_id] = envelope


def evaluate_bounds_against_envelope(
    bounds: CAMBounds2D,
    envelope: CAMMachineEnvelope,
    subject_id: str = "unknown",
    subject_type: str = "bounds",
) -> CAMEnvelopeValidationEvaluation:
    """
    Evaluate bounds against a machine envelope.

    Returns GREEN/YELLOW/RED evaluation with issues and warnings.

    Gate logic:
      - RED: Bounds exceed envelope limits
      - YELLOW: Bounds within margin zone (near edges)
      - GREEN: Bounds safely within envelope
    """
    blocking_issues: List[str] = []
    warnings: List[str] = []
    margin_violations: List[str] = []

    safe_bounds = envelope.get_safe_bounds()

    if bounds.min_x_mm < 0:
        blocking_issues.append(
            f"X minimum ({bounds.min_x_mm:.2f}mm) is negative"
        )
    elif bounds.min_x_mm < envelope.margin_mm:
        margin_violations.append(
            f"X minimum ({bounds.min_x_mm:.2f}mm) within margin zone"
        )
        warnings.append(f"Near left edge: X min = {bounds.min_x_mm:.2f}mm")

    if bounds.max_x_mm > envelope.max_x_mm:
        blocking_issues.append(
            f"X maximum ({bounds.max_x_mm:.2f}mm) exceeds envelope ({envelope.max_x_mm:.2f}mm)"
        )
    elif bounds.max_x_mm > safe_bounds.max_x_mm:
        margin_violations.append(
            f"X maximum ({bounds.max_x_mm:.2f}mm) within margin zone"
        )
        warnings.append(f"Near right edge: X max = {bounds.max_x_mm:.2f}mm")

    if bounds.min_y_mm < 0:
        blocking_issues.append(
            f"Y minimum ({bounds.min_y_mm:.2f}mm) is negative"
        )
    elif bounds.min_y_mm < envelope.margin_mm:
        margin_violations.append(
            f"Y minimum ({bounds.min_y_mm:.2f}mm) within margin zone"
        )
        warnings.append(f"Near front edge: Y min = {bounds.min_y_mm:.2f}mm")

    if bounds.max_y_mm > envelope.max_y_mm:
        blocking_issues.append(
            f"Y maximum ({bounds.max_y_mm:.2f}mm) exceeds envelope ({envelope.max_y_mm:.2f}mm)"
        )
    elif bounds.max_y_mm > safe_bounds.max_y_mm:
        margin_violations.append(
            f"Y maximum ({bounds.max_y_mm:.2f}mm) within margin zone"
        )
        warnings.append(f"Near back edge: Y max = {bounds.max_y_mm:.2f}mm")

    if bounds.min_z_mm is not None and envelope.max_z_mm is not None:
        if bounds.min_z_mm < -envelope.max_z_mm:
            blocking_issues.append(
                f"Z minimum ({bounds.min_z_mm:.2f}mm) exceeds envelope depth ({-envelope.max_z_mm:.2f}mm)"
            )
        elif bounds.min_z_mm < -(envelope.max_z_mm - envelope.margin_mm):
            warnings.append(f"Near Z depth limit: Z min = {bounds.min_z_mm:.2f}mm")
    elif bounds.min_z_mm is not None and envelope.max_z_mm is None:
        warnings.append("Z bounds specified but machine has no Z limit defined")

    if blocking_issues:
        gate: EnvelopeGate = "red"
    elif warnings or margin_violations:
        gate = "yellow"
    else:
        gate = "green"

    evaluation = CAMEnvelopeValidationEvaluation(
        subject_id=subject_id,
        subject_type=subject_type,
        gate=gate,
        bounds_checked=bounds,
        machine_envelope=envelope,
        blocking_issues=blocking_issues,
        warnings=warnings,
        margin_violations=margin_violations,
    )

    evaluation.deterministic_evaluation_hash = evaluation.compute_hash()

    CAM_ENVELOPE_EVALUATION_INDEX[evaluation.evaluation_id] = evaluation

    return evaluation


def get_envelope_evaluation(evaluation_id: str) -> Optional[CAMEnvelopeValidationEvaluation]:
    """Get envelope evaluation by ID."""
    return CAM_ENVELOPE_EVALUATION_INDEX.get(evaluation_id)


def list_envelope_evaluations() -> List[CAMEnvelopeValidationEvaluation]:
    """List all envelope evaluations."""
    return list(CAM_ENVELOPE_EVALUATION_INDEX.values())


def clear_envelope_evaluation_index() -> None:
    """Clear envelope evaluation index (for testing)."""
    CAM_ENVELOPE_EVALUATION_INDEX.clear()


def extract_bounds_from_dict(data: Dict[str, Any]) -> Optional[CAMBounds2D]:
    """
    Extract bounds from a dictionary.

    Looks for common key patterns:
      - min_x, max_x, min_y, max_y
      - bounds.min_x, etc.
      - bbox_min_x, bbox_max_x, etc.
    """
    if "bounds" in data and isinstance(data["bounds"], dict):
        data = data["bounds"]

    keys_to_try = [
        ("min_x", "max_x", "min_y", "max_y", "min_z", "max_z"),
        ("min_x_mm", "max_x_mm", "min_y_mm", "max_y_mm", "min_z_mm", "max_z_mm"),
        ("bbox_min_x", "bbox_max_x", "bbox_min_y", "bbox_max_y", "bbox_min_z", "bbox_max_z"),
    ]

    for min_x_key, max_x_key, min_y_key, max_y_key, min_z_key, max_z_key in keys_to_try:
        if all(k in data for k in [min_x_key, max_x_key, min_y_key, max_y_key]):
            return CAMBounds2D(
                min_x_mm=float(data[min_x_key]),
                max_x_mm=float(data[max_x_key]),
                min_y_mm=float(data[min_y_key]),
                max_y_mm=float(data[max_y_key]),
                min_z_mm=float(data[min_z_key]) if min_z_key in data and data[min_z_key] is not None else None,
                max_z_mm=float(data[max_z_key]) if max_z_key in data and data[max_z_key] is not None else None,
            )

    return None
