"""Capture uses the current project serializer and does not change it."""
from __future__ import annotations

import json

import pytest

from app.design_snapshots import ArtifactReferenceV1, GeneratorReferenceV1, capture_design_snapshot
from app.design_snapshots.errors import DesignSnapshotError
from app.projects.service import create_default_design_state, serialize_design_state
from app.schemas.instrument_project import (
    BlueprintDerivedGeometry,
    BlueprintSource,
    ManufacturingState,
    ManufacturingStatus,
)

from .conftest import FIXTURES, T0


def _capture(state, **kwargs):
    args = dict(
        project_id="project-synth-0001", job_id="JOB-SYNTH-0001", design_state=state,
        captured_at=T0, captured_by="operator-synth", design_snapshot_id="dsn-synth-0001",
    )
    args.update(kwargs)
    return capture_design_snapshot(**args)


@pytest.mark.unit
def test_routed_serializer_matches_the_frozen_baseline_and_is_not_mutated():
    state = create_default_design_state("acoustic_guitar")
    before = serialize_design_state(state)
    raw_text = (FIXTURES / "baseline_acoustic_guitar_design_state.json").read_text(encoding="utf-8")
    assert json.dumps(before, sort_keys=True, separators=(",", ":"), allow_nan=False) == raw_text
    snap = _capture(before)
    after = serialize_design_state(state)
    assert after == before
    assert before == snap.design_payload
    assert snap.design_payload["spec"]["scale_length_mm"] == 645.0
    assert snap.design_payload["spec"]["nut_width_mm"] == 43.0
    assert "name" not in snap.design_payload
    assert "updated_at" not in snap.design_payload
    assert "commit_message" not in snap.design_payload


@pytest.mark.unit
def test_geometry_units_and_copied_manufacturing_assertion_survive():
    state = create_default_design_state("acoustic_guitar")
    outline = [(0.0, 0.0), (120.0, 0.0), (0.0, 400.0)]
    state = state.model_copy(update={
        "blueprint_geometry": BlueprintDerivedGeometry(
            source=BlueprintSource.MANUAL, body_outline_mm=outline, axis_angle_deg=0.0,
        ),
        "manufacturing_state": ManufacturingState(status=ManufacturingStatus.CAM_APPROVED),
    })
    raw = serialize_design_state(state)
    snap = _capture(raw)
    geometry = snap.design_payload["blueprint_geometry"]
    assert geometry["body_outline_mm"] == [[0.0, 0.0], [120.0, 0.0], [0.0, 400.0]]
    assert geometry["axis_angle_deg"] == 0.0
    assert snap.design_payload["manufacturing_state"]["status"] == "cam_approved"
    assert "manufacturing_state" not in snap.__dataclass_fields__


@pytest.mark.unit
def test_changed_source_design_yields_a_new_digest():
    state = create_default_design_state("acoustic_guitar")
    first = _capture(serialize_design_state(state))
    longer = state.model_copy(update={
        "spec": state.spec.model_copy(update={"scale_length_mm": 650.0}),
    })
    second = _capture(serialize_design_state(longer), design_snapshot_id="dsn-synth-0002")
    assert second.design_payload_digest != first.design_payload_digest
    assert serialize_design_state(state)["spec"]["scale_length_mm"] == 645.0


@pytest.mark.unit
def test_artifacts_need_digests_and_generators_are_not_invented():
    with pytest.raises(DesignSnapshotError):
        ArtifactReferenceV1("run-1", "rmos-run", "")
    digest = "a" * 64
    artifact = ArtifactReferenceV1("run-1", "rmos-run", digest, source_path_hint="sources/run-1.json")
    generator = GeneratorReferenceV1("blueprint-reader", "phase3", output_digest=digest)
    snap = _capture({}, artifact_refs=(artifact,), generator_refs=(generator,))
    assert snap.artifact_refs[0].content_digest == digest
    assert snap.generator_refs[0].generator_id == "blueprint-reader"
    assert snap.generator_refs[0].input_digest is None
    plain = _capture({})
    assert plain.artifact_refs == () and plain.generator_refs == ()


@pytest.mark.unit
def test_caller_id_is_kept_and_factory_is_not_called_for_it():
    def boom() -> str:
        raise AssertionError("factory must not replace a caller id")

    kept = _capture({}, id_factory=boom)
    assert kept.design_snapshot_id == "dsn-synth-0001"
    minted = capture_design_snapshot(
        project_id="project-synth-0001", job_id="JOB-SYNTH-0001", design_state={},
        captured_at=T0, captured_by="operator-synth", id_factory=lambda: "dsn-injected",
    )
    assert minted.design_snapshot_id == "dsn-injected"
    with pytest.raises(DesignSnapshotError):
        _capture({}, design_snapshot_id="Has Space")
