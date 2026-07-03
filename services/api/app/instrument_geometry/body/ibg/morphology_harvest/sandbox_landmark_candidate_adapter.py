"""
IBG sandbox landmark candidate adapter.

Imports the vectorizer-sandbox ``ibg-landmark-candidate.v1`` records as
review-required evidence candidates. This bridge preserves provenance and
caveats; it does not convert pixels to millimeters, run the solver, or grant
authority.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.governance import ConfidenceType

from ..body_evidence_candidate import (
    BodyEvidenceCandidate,
    create_candidate_from_evidence,
)
from ..ibg_intake_gate import (
    IntakeValidationResult,
    create_default_intake_gate,
)
from ..body_grid.body_grid_schema import (
    BodyEvidence,
    CoordinateSpace,
    EvidenceSource,
    Landmark,
    NormalizedPoint,
    RawCoordinate,
)


SCHEMA_VERSION = "ibg-landmark-candidate.v1"
STATUS = "landmark_candidate"
LANDMARK_NAMES = {"upper_bout", "waist", "lower_bout"}
CONFIDENCE_VALUES = {
    "high": 0.8,
    "medium": 0.5,
    "low": 0.3,
}
GEOMETRY_AUTHORITY_LABELS = {
    "geometry_role": "evidence",
    "authority_state": "governed_evidence_candidate",
    "authority_source": "vectorizer_sandbox:ibg_geo_acquisition",
    "promotion_mechanism": "human_review_and_governance_ratification",
    "export_format_authority": "none",
}


class SandboxLandmarkCandidateError(ValueError):
    """Raised when a sandbox landmark candidate cannot be adapted."""


class CalibrationRequiredError(SandboxLandmarkCandidateError):
    """Raised when a caller tries to produce solver-ready mm landmarks."""


@dataclass
class SandboxLandmarkAdapterResult:
    """Review-ready result for sandbox landmark candidate intake."""

    success: bool
    candidate: Optional[BodyEvidenceCandidate] = None
    gate_result: Optional[IntakeValidationResult] = None
    record: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None

    def to_review_json(self) -> Dict[str, Any]:
        """Return a compact review payload for UI/tests/handoff inspection."""
        if not self.success or self.candidate is None:
            return {
                "success": False,
                "errors": self.errors or ["No candidate produced"],
            }

        gate = self.gate_result
        return {
            "success": True,
            "candidate_id": self.candidate.candidate_id,
            "source_artifact": (
                self.candidate.provenance.source_artifact
                if self.candidate.provenance
                else None
            ),
            "authority_state": self.candidate.authority_state.value,
            "confidence_declaration": self.candidate.confidence.to_dict(),
            "review_required": self.candidate.review_required,
            "approved_for_ibg_memory": self.candidate.approved_for_ibg_memory,
            "gate_decision": {
                "is_valid": gate.is_valid if gate else False,
                "rejections": [r.value for r in gate.rejections] if gate else [],
                "gate_results": gate.gate_results if gate else {},
            },
            "metadata": self.candidate.metadata,
        }


def load_sandbox_landmark_candidate(path: Path | str) -> Dict[str, Any]:
    """Load and validate an ``ibg-landmark-candidate.v1`` record."""
    candidate_path = Path(path)
    with candidate_path.open("r", encoding="utf-8") as handle:
        record = json.load(handle)
    validate_sandbox_landmark_candidate(record)
    return record


def validate_sandbox_landmark_candidate(record: Mapping[str, Any]) -> None:
    """Validate the self-contained subset luthiers consumes from sandbox facts."""
    _require(
        record.get("schema_version") == SCHEMA_VERSION,
        f"schema_version must be {SCHEMA_VERSION!r}",
    )
    _require(record.get("status") == STATUS, f"status must be {STATUS!r}")

    required = {
        "spec_id": str,
        "subject": Mapping,
        "provenance": Mapping,
        "admissibility": Mapping,
        "coordinate_space": str,
        "landmarks": list,
        "body_metrics_px": Mapping,
        "body_bbox_px_xywh": list,
        "ordering_rule": str,
        "extraction_confidence": str,
        "scope_note": str,
        "ordering_ok": bool,
        "bout_ordering_lower_ge_upper": bool,
        "width_structure_resolved": bool,
        "non_degenerate": bool,
        "manual_review_required": bool,
    }
    for key, expected_type in required.items():
        _require(key in record, f"missing required field {key!r}")
        _require(
            isinstance(record[key], expected_type),
            f"{key} must be {getattr(expected_type, '__name__', expected_type)}",
        )

    coordinate_space = record["coordinate_space"].lower()
    _require("pixel" in coordinate_space, "coordinate_space must declare pixel-space")
    _require("no mm" in coordinate_space, "coordinate_space must declare NO mm")

    confidence = record["extraction_confidence"]
    _require(
        confidence in CONFIDENCE_VALUES,
        f"extraction_confidence must be one of {sorted(CONFIDENCE_VALUES)}",
    )

    provenance = record["provenance"]
    for key in ("source_filename", "source_sha256", "dpi", "acquisition"):
        _require(key in provenance, f"provenance.{key} missing")
    source_sha = provenance["source_sha256"]
    _require(
        isinstance(source_sha, str) and len(source_sha) == 64,
        "provenance.source_sha256 must be a 64-character hex digest",
    )

    admissibility = record["admissibility"]
    _require("verdict" in admissibility, "admissibility.verdict missing")
    _require("P1_P5" in admissibility, "admissibility.P1_P5 missing")

    bbox = record["body_bbox_px_xywh"]
    _require(len(bbox) == 4, "body_bbox_px_xywh must contain [x,y,w,h]")

    metrics = record["body_metrics_px"]
    for key in (
        "centerline_x_px",
        "body_length_px",
        "body_max_width_px",
        "waist_to_lower_ratio",
        "upper_to_lower_ratio",
        "width_to_length_ratio",
    ):
        _require(key in metrics, f"body_metrics_px.{key} missing")
        _require(_is_number(metrics[key]), f"body_metrics_px.{key} must be numeric")

    landmarks = record["landmarks"]
    _require(len(landmarks) == 3, "expected exactly 3 landmarks")
    names = {landmark.get("name") for landmark in landmarks}
    _require(names == LANDMARK_NAMES, f"landmarks must be {sorted(LANDMARK_NAMES)}")
    for landmark in landmarks:
        name = landmark.get("name", "<unknown>")
        _require(isinstance(landmark.get("presence"), bool), f"{name}.presence must be bool")
        _require(isinstance(landmark.get("y_px"), int), f"{name}.y_px must be int")
        for key in ("width_px", "y_norm"):
            _require(_is_number(landmark.get(key)), f"{name}.{key} must be numeric")

    _require(
        record["ordering_ok"]
        == (record["width_structure_resolved"] and record["bout_ordering_lower_ge_upper"]),
        "ordering_ok must equal width_structure_resolved AND bout_ordering_lower_ge_upper",
    )
    if record["non_degenerate"]:
        _require(
            record["width_structure_resolved"],
            "non_degenerate=True requires width_structure_resolved=True",
        )


def candidate_to_body_evidence(record: Mapping[str, Any]) -> BodyEvidence:
    """Map a sandbox landmark candidate into luthiers ``BodyEvidence``."""
    validate_sandbox_landmark_candidate(record)

    centerline_x = float(record["body_metrics_px"]["centerline_x_px"])
    landmarks = [
        Landmark(
            label=str(landmark["name"]),
            point=NormalizedPoint(
                x_norm=0.0,
                y_norm=float(landmark["y_norm"]),
                raw=RawCoordinate(
                    x=centerline_x,
                    y=float(landmark["y_px"]),
                    space=CoordinateSpace.RAW_PIXEL,
                    confidence=_confidence_value(record),
                ),
                confidence=_confidence_value(record),
            ),
            source=EvidenceSource.IBG_SANDBOX_LANDMARK_CANDIDATE,
            confidence=_confidence_value(record),
        )
        for landmark in _ordered_landmarks(record["landmarks"])
    ]

    return BodyEvidence(
        outline_points=[],
        contour_segments=[],
        landmarks=landmarks,
        source_type=EvidenceSource.IBG_SANDBOX_LANDMARK_CANDIDATE,
        source_transform={
            "centerline_x_px": centerline_x,
            "coordinate_space": record["coordinate_space"],
            "body_bbox_px_xywh": list(record["body_bbox_px_xywh"]),
            "mm_per_px": None,
        },
        bounding_box_mm=None,
        centerline_x_mm=None,
    )


def candidate_to_body_evidence_candidate(
    record: Mapping[str, Any],
) -> BodyEvidenceCandidate:
    """Create a review-required ``BodyEvidenceCandidate`` from a sandbox record."""
    evidence = candidate_to_body_evidence(record)
    provenance = record["provenance"]
    source_artifact = (
        "vectorizer-sandbox:"
        f"{record['subject']['id']}:{provenance['source_filename']}:"
        f"{provenance['source_sha256']}"
    )

    candidate = create_candidate_from_evidence(
        evidence=evidence,
        source_artifact=source_artifact,
        extraction_method="sandbox_landmark_candidate_adapter",
        extraction_params={
            "schema_version": record["schema_version"],
            "spec_id": record["spec_id"],
            "source_repo": "vectorizer_sandbox",
            "source_subsystem": "ibg_geo_acquisition",
            "coordinate_space": record["coordinate_space"],
            "has_mm_calibration": False,
        },
        confidence_value=_confidence_value(record),
        confidence_origin="vectorizer_sandbox.ibg_geo_acquisition",
    )

    candidate.confidence.confidence_type = ConfidenceType.HEURISTIC
    candidate.confidence.interpretation = (
        "Heuristic extraction confidence from sandbox landmark candidate record; "
        "does not imply correctness, authority, calibration, or solver readiness."
    )
    candidate.confidence.metadata.update(
        {
            "extraction_confidence_label": record["extraction_confidence"],
            "confidence_mapping": dict(CONFIDENCE_VALUES),
        }
    )

    candidate.metadata.update(_candidate_metadata(record))
    if candidate.provenance:
        candidate.provenance.metadata.update(
            {
                "source_repo": "vectorizer_sandbox",
                "source_subsystem": "ibg_geo_acquisition",
                "source_sha256": provenance["source_sha256"],
                "schema_version": record["schema_version"],
            }
        )
    return candidate


def adapt_sandbox_landmark_candidate(
    record: Mapping[str, Any],
) -> SandboxLandmarkAdapterResult:
    """Adapt and gate-validate a sandbox landmark candidate record."""
    try:
        candidate = candidate_to_body_evidence_candidate(record)
        gate_result = create_default_intake_gate().validate(candidate)
        return SandboxLandmarkAdapterResult(
            success=True,
            candidate=candidate,
            gate_result=gate_result,
            record=dict(record),
        )
    except SandboxLandmarkCandidateError as exc:
        return SandboxLandmarkAdapterResult(success=False, errors=[str(exc)])


def sandbox_candidate_to_solver_landmarks(
    record: Mapping[str, Any],
    *,
    mm_per_px: Optional[float] = None,
) -> List[Any]:
    """Refuse pixel-to-mm conversion unless a calibrated follow-up supplies scale."""
    validate_sandbox_landmark_candidate(record)
    if mm_per_px is None:
        raise CalibrationRequiredError(
            "Sandbox landmark candidates are pixel/body-relative evidence only; "
            "mm_per_px calibration is required before producing solver landmarks."
        )
    raise CalibrationRequiredError(
        "Solver landmark conversion is intentionally not implemented in v1. "
        "Add a calibrated follow-up before using sandbox facts as mm landmarks."
    )


def _candidate_metadata(record: Mapping[str, Any]) -> Dict[str, Any]:
    provenance = record["provenance"]
    return {
        **GEOMETRY_AUTHORITY_LABELS,
        "schema_version": record["schema_version"],
        "spec_id": record["spec_id"],
        "status": record["status"],
        "subject": dict(record["subject"]),
        "source_repo": "vectorizer_sandbox",
        "source_subsystem": "ibg_geo_acquisition",
        "source_filename": provenance["source_filename"],
        "source_sha256": provenance["source_sha256"],
        "coordinate_space": record["coordinate_space"],
        "landmark_vocabulary_ref": record.get("landmark_vocabulary_ref"),
        "admissibility": dict(record["admissibility"]),
        "body_bbox_px_xywh": list(record["body_bbox_px_xywh"]),
        "body_metrics_px": dict(record["body_metrics_px"]),
        "landmark_widths_px": {
            landmark["name"]: landmark["width_px"]
            for landmark in record["landmarks"]
        },
        "landmark_y_norm": {
            landmark["name"]: landmark["y_norm"]
            for landmark in record["landmarks"]
        },
        "ordering_rule": record.get("ordering_rule"),
        "ordering_ok": record["ordering_ok"],
        "bout_ordering_lower_ge_upper": record["bout_ordering_lower_ge_upper"],
        "width_structure_resolved": record["width_structure_resolved"],
        "non_degenerate": record["non_degenerate"],
        "manual_review_required": record["manual_review_required"],
        "extraction_confidence": record["extraction_confidence"],
        "diagnostics": dict(record.get("diagnostics", {})),
        "scope_note": record["scope_note"],
        "calibration_status": "absent_no_mm_conversion_allowed",
    }


def _ordered_landmarks(landmarks: Iterable[Mapping[str, Any]]) -> List[Mapping[str, Any]]:
    order = {"upper_bout": 0, "waist": 1, "lower_bout": 2}
    return sorted(landmarks, key=lambda landmark: order[str(landmark["name"])])


def _confidence_value(record: Mapping[str, Any]) -> float:
    return CONFIDENCE_VALUES[str(record["extraction_confidence"])]


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SandboxLandmarkCandidateError(message)
