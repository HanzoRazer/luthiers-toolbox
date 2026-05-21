"""
CAM Envelope Validation

CAM Dev Order 7S: Pre-export envelope/bounds validation.

7S invariants:
  - execution_authorized always False
  - machine_output_allowed always False
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


EnvelopeGate = Literal["green", "yellow", "red"]


class CAMBounds2D(BaseModel):
    """2D/3D bounding box representation."""

    min_x_mm: float
    max_x_mm: float
    min_y_mm: float
    max_y_mm: float
    min_z_mm: Optional[float] = None
    max_z_mm: Optional[float] = None

    @property
    def width_mm(self) -> float:
        return self.max_x_mm - self.min_x_mm

    @property
    def height_mm(self) -> float:
        return self.max_y_mm - self.min_y_mm


class CAMMachineEnvelope(BaseModel):
    """Machine envelope/working area definition."""

    machine_id: str
    display_name: str = ""
    max_x_mm: float
    max_y_mm: float
    max_z_mm: Optional[float] = None
    margin_mm: float = 5.0
    description: str = ""

    def get_safe_bounds(self) -> CAMBounds2D:
        return CAMBounds2D(
            min_x_mm=self.margin_mm,
            max_x_mm=self.max_x_mm - self.margin_mm,
            min_y_mm=self.margin_mm,
            max_y_mm=self.max_y_mm - self.margin_mm,
            min_z_mm=-self.max_z_mm if self.max_z_mm else None,
            max_z_mm=0.0 if self.max_z_mm else None,
        )


MACHINE_ENVELOPE_REGISTRY: Dict[str, CAMMachineEnvelope] = {
    "generic_3018": CAMMachineEnvelope(machine_id="generic_3018", display_name="Generic 3018 CNC", max_x_mm=300.0, max_y_mm=180.0, max_z_mm=45.0),
    "generic_6040": CAMMachineEnvelope(machine_id="generic_6040", display_name="Generic 6040 CNC", max_x_mm=600.0, max_y_mm=400.0, max_z_mm=75.0),
    "luthier_body_router": CAMMachineEnvelope(machine_id="luthier_body_router", display_name="Luthier Body Router", max_x_mm=700.0, max_y_mm=500.0, max_z_mm=100.0, margin_mm=10.0),
    "luthier_neck_router": CAMMachineEnvelope(machine_id="luthier_neck_router", display_name="Luthier Neck Router", max_x_mm=800.0, max_y_mm=200.0, max_z_mm=80.0),
    "laser_k40": CAMMachineEnvelope(machine_id="laser_k40", display_name="K40 Laser", max_x_mm=300.0, max_y_mm=200.0),
}

MACHINE_ENVELOPE_INDEX: Dict[str, CAMMachineEnvelope] = dict(MACHINE_ENVELOPE_REGISTRY)


class CAMEnvelopeValidationEvaluation(BaseModel):
    """Envelope validation evaluation result."""

    evaluation_id: str = Field(default_factory=lambda: f"envelope-eval-{uuid4().hex[:12]}")
    subject_id: str
    gate: EnvelopeGate
    bounds_checked: CAMBounds2D
    machine_envelope: CAMMachineEnvelope
    blocking_issues: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    execution_authorized: bool = Field(default=False)
    machine_output_allowed: bool = Field(default=False)

    @model_validator(mode="after")
    def enforce_7s_invariants(self) -> "CAMEnvelopeValidationEvaluation":
        if self.execution_authorized:
            raise ValueError("7S invariant violation: execution_authorized must be False")
        if self.machine_output_allowed:
            raise ValueError("7S invariant violation: machine_output_allowed must be False")
        return self


CAM_ENVELOPE_EVALUATION_INDEX: Dict[str, CAMEnvelopeValidationEvaluation] = {}


def get_machine_envelope(machine_id: str) -> Optional[CAMMachineEnvelope]:
    return MACHINE_ENVELOPE_INDEX.get(machine_id)


def list_machine_envelopes() -> List[CAMMachineEnvelope]:
    return list(MACHINE_ENVELOPE_INDEX.values())


def register_machine_envelope(envelope: CAMMachineEnvelope) -> None:
    MACHINE_ENVELOPE_INDEX[envelope.machine_id] = envelope


def evaluate_bounds_against_envelope(
    bounds: CAMBounds2D,
    envelope: CAMMachineEnvelope,
    subject_id: str = "unknown",
) -> CAMEnvelopeValidationEvaluation:
    blocking_issues: List[str] = []
    warnings: List[str] = []
    safe_bounds = envelope.get_safe_bounds()

    if bounds.min_x_mm < 0:
        blocking_issues.append(f"X minimum ({bounds.min_x_mm:.2f}mm) is negative")
    elif bounds.min_x_mm < envelope.margin_mm:
        warnings.append(f"Near left edge: X min = {bounds.min_x_mm:.2f}mm")

    if bounds.max_x_mm > envelope.max_x_mm:
        blocking_issues.append(f"X maximum ({bounds.max_x_mm:.2f}mm) exceeds envelope ({envelope.max_x_mm:.2f}mm)")
    elif bounds.max_x_mm > safe_bounds.max_x_mm:
        warnings.append(f"Near right edge: X max = {bounds.max_x_mm:.2f}mm")

    if bounds.min_y_mm < 0:
        blocking_issues.append(f"Y minimum ({bounds.min_y_mm:.2f}mm) is negative")
    elif bounds.min_y_mm < envelope.margin_mm:
        warnings.append(f"Near front edge: Y min = {bounds.min_y_mm:.2f}mm")

    if bounds.max_y_mm > envelope.max_y_mm:
        blocking_issues.append(f"Y maximum ({bounds.max_y_mm:.2f}mm) exceeds envelope ({envelope.max_y_mm:.2f}mm)")
    elif bounds.max_y_mm > safe_bounds.max_y_mm:
        warnings.append(f"Near back edge: Y max = {bounds.max_y_mm:.2f}mm")

    gate: EnvelopeGate = "red" if blocking_issues else ("yellow" if warnings else "green")

    evaluation = CAMEnvelopeValidationEvaluation(
        subject_id=subject_id,
        gate=gate,
        bounds_checked=bounds,
        machine_envelope=envelope,
        blocking_issues=blocking_issues,
        warnings=warnings,
    )
    CAM_ENVELOPE_EVALUATION_INDEX[evaluation.evaluation_id] = evaluation
    return evaluation


def get_envelope_evaluation(evaluation_id: str) -> Optional[CAMEnvelopeValidationEvaluation]:
    return CAM_ENVELOPE_EVALUATION_INDEX.get(evaluation_id)


def list_envelope_evaluations() -> List[CAMEnvelopeValidationEvaluation]:
    return list(CAM_ENVELOPE_EVALUATION_INDEX.values())


def clear_envelope_evaluation_index() -> None:
    CAM_ENVELOPE_EVALUATION_INDEX.clear()


def extract_bounds_from_dict(data: Dict[str, Any]) -> Optional[CAMBounds2D]:
    if "bounds" in data and isinstance(data["bounds"], dict):
        data = data["bounds"]
    keys = [("min_x_mm", "max_x_mm", "min_y_mm", "max_y_mm")]
    for min_x, max_x, min_y, max_y in keys:
        if all(k in data for k in [min_x, max_x, min_y, max_y]):
            return CAMBounds2D(
                min_x_mm=float(data[min_x]),
                max_x_mm=float(data[max_x]),
                min_y_mm=float(data[min_y]),
                max_y_mm=float(data[max_y]),
            )
    return None
