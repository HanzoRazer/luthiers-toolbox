"""Tests for IBG sandbox landmark candidate intake.

CI-RED-015-L: vectorizer-sandbox landmark candidates are evidence-only inputs
to luthiers' constitutional IBG intake model. They must preserve provenance and
caveats, while staying review-required and blocked from IBG memory/export.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from app.governance import ConfidenceType
from app.instrument_geometry.body.ibg.body_grid.body_grid_schema import (
    CoordinateSpace,
    EvidenceSource,
)
from app.instrument_geometry.body.ibg.ibg_intake_gate import IntakeRejectionReason
from app.instrument_geometry.body.ibg.morphology_harvest.sandbox_landmark_candidate_adapter import (
    CalibrationRequiredError,
    SandboxLandmarkCandidateError,
    adapt_sandbox_landmark_candidate,
    candidate_to_body_evidence,
    load_sandbox_landmark_candidate,
    sandbox_candidate_to_solver_landmarks,
    validate_sandbox_landmark_candidate,
)


FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "ibg_sandbox_landmarks"


def _fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def _adapt_melody_maker():
    record = load_sandbox_landmark_candidate(
        FIXTURE_DIR / "melody_maker_body.landmarks.json"
    )
    result = adapt_sandbox_landmark_candidate(record)

    assert result.success is True
    assert result.candidate is not None
    return result, result.candidate


def test_melody_maker_candidate_is_review_required_evidence():
    _result, candidate = _adapt_melody_maker()

    assert candidate.has_provenance()
    assert candidate.review_required is True
    assert candidate.approved_for_ibg_memory is False
    assert candidate.authority_state.value == "advisory_candidate"
    assert candidate.confidence.confidence_type == ConfidenceType.HEURISTIC
    assert candidate.confidence.value == 0.8


def test_melody_maker_gate_preserves_authority_labels():
    result, candidate = _adapt_melody_maker()

    assert result.gate_result is not None
    assert result.gate_result.is_valid is False
    assert IntakeRejectionReason.AUTHORITY_INSUFFICIENT in result.gate_result.rejections
    assert IntakeRejectionReason.REVIEW_REQUIRED in result.gate_result.rejections

    assert candidate.metadata["geometry_role"] == "evidence"
    assert candidate.metadata["authority_state"] == "governed_evidence_candidate"
    assert candidate.metadata["authority_source"] == "vectorizer_sandbox:ibg_geo_acquisition"
    assert candidate.metadata["source_repo"] == "vectorizer_sandbox"
    assert candidate.metadata["calibration_status"] == "absent_no_mm_conversion_allowed"


def test_provenance_and_sandbox_facts_are_preserved():
    record = _fixture("melody_maker_body.landmarks.json")

    result = adapt_sandbox_landmark_candidate(record)
    assert result.candidate is not None
    metadata = result.candidate.metadata

    assert metadata["source_sha256"] == record["provenance"]["source_sha256"]
    assert len(metadata["source_sha256"]) == 64
    assert metadata["admissibility"]["verdict"] == "ADMISSIBLE"
    assert "P1_P5" in metadata["admissibility"]
    assert metadata["coordinate_space"] == record["coordinate_space"]
    assert "NO mm" in metadata["coordinate_space"]
    assert metadata["scope_note"] == record["scope_note"]
    assert metadata["landmark_widths_px"]["waist"] == 919.0

    provenance = result.candidate.provenance
    assert provenance is not None
    assert "vectorizer-sandbox:melody_maker_body" in provenance.source_artifact
    assert provenance.metadata["source_sha256"] == record["provenance"]["source_sha256"]


def test_pixel_facts_are_not_solver_ready_mm_landmarks():
    record = _fixture("melody_maker_body.landmarks.json")

    evidence = candidate_to_body_evidence(record)

    assert evidence.source_type == EvidenceSource.IBG_SANDBOX_LANDMARK_CANDIDATE
    assert evidence.outline_points == []
    assert evidence.bounding_box_mm is None
    assert evidence.centerline_x_mm is None
    assert len(evidence.landmarks) == 3
    assert {lm.label for lm in evidence.landmarks} == {
        "upper_bout",
        "waist",
        "lower_bout",
    }
    assert {lm.point.x_norm for lm in evidence.landmarks} == {0.0}
    assert {lm.point.raw.space for lm in evidence.landmarks if lm.point.raw} == {
        CoordinateSpace.RAW_PIXEL
    }

    with pytest.raises(CalibrationRequiredError):
        sandbox_candidate_to_solver_landmarks(record)

    with pytest.raises(CalibrationRequiredError):
        sandbox_candidate_to_solver_landmarks(record, mm_per_px=0.1)


def test_jazzmaster_offset_caveat_survives_intake():
    record = _fixture("jazzmaster62_body.landmarks.json")

    result = adapt_sandbox_landmark_candidate(record)

    assert result.success is True
    assert result.candidate is not None
    metadata = result.candidate.metadata

    assert metadata["non_degenerate"] is True
    assert metadata["width_structure_resolved"] is True
    assert metadata["bout_ordering_lower_ge_upper"] is False
    assert metadata["ordering_ok"] is False
    assert metadata["extraction_confidence"] == "medium"
    assert result.candidate.confidence.value == 0.5
    assert result.gate_result is not None
    assert result.gate_result.is_valid is False


@pytest.mark.parametrize(
    "mutate, expected",
    [
        (lambda r: r.update({"schema_version": "wrong"}), "schema_version"),
        (lambda r: r["provenance"].pop("source_sha256"), "source_sha256"),
        (lambda r: r["landmarks"].pop(), "expected exactly 3 landmarks"),
        (lambda r: r.update({"extraction_confidence": "certain"}), "extraction_confidence"),
        (lambda r: r.pop("coordinate_space"), "coordinate_space"),
    ],
)
def test_malformed_schema_fails_loudly(mutate, expected):
    record = copy.deepcopy(_fixture("melody_maker_body.landmarks.json"))
    mutate(record)

    with pytest.raises(SandboxLandmarkCandidateError, match=expected):
        validate_sandbox_landmark_candidate(record)


def test_review_json_preserves_fail_closed_posture():
    record = _fixture("melody_maker_body.landmarks.json")

    payload = adapt_sandbox_landmark_candidate(record).to_review_json()

    assert payload["success"] is True
    assert payload["review_required"] is True
    assert payload["approved_for_ibg_memory"] is False
    assert payload["gate_decision"]["is_valid"] is False
    assert "review_required" in payload["gate_decision"]["rejections"]
    assert payload["metadata"]["geometry_role"] == "evidence"
