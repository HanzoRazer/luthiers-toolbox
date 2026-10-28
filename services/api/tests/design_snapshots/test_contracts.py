"""Contract, digest, and non-authority checks for LtbDesignSnapshotV1."""
from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime, timezone
from types import MappingProxyType

import pytest

from app.design_snapshots import (
    SCHEMA_ID,
    ActorReferenceV1,
    ArtifactReferenceV1,
    ExternalJobReferenceV1,
    GeneratorReferenceV1,
    LtbDesignSnapshotV1,
    LtbProjectReferenceV1,
    capture_design_snapshot,
)
from app.design_snapshots.contracts import snapshot_fields
from app.design_snapshots.errors import DesignSnapshotError
from app.design_snapshots.repository import canonical_record_text
from app.design_snapshots.serialization import canonical_json, payload_digest

from .conftest import FIXTURES, T0


def _capture(state, **kwargs):
    args = dict(
        project_id="project-synth-0001", job_id="JOB-SYNTH-0001", design_state=state,
        captured_at=T0, captured_by="operator-synth", design_snapshot_id="dsn-synth-0001",
    )
    args.update(kwargs)
    return capture_design_snapshot(**args)


@pytest.mark.unit
def test_golden_snapshot_round_trips_and_ignores_key_order(baseline_state, golden_text):
    snap = _capture(baseline_state)
    assert canonical_record_text(snap) == golden_text
    assert snap.design_payload_digest == snap.project_ref.source_state_digest
    shuffled = json.loads(golden_text)
    moved = {"snapshot_digest": shuffled.pop("snapshot_digest"), **shuffled}
    assert payload_digest(moved) == snap.snapshot_digest
    again = _capture(dict(reversed(list(baseline_state.items()))))
    assert again.design_payload_digest == snap.design_payload_digest


@pytest.mark.unit
def test_one_design_change_changes_both_digests(baseline_state):
    original = _capture(baseline_state)
    changed = json.loads(json.dumps(baseline_state))
    changed["spec"]["scale_length_mm"] = 646.0
    nxt = _capture(changed, design_snapshot_id="dsn-synth-0002")
    assert nxt.design_payload_digest != original.design_payload_digest
    assert nxt.snapshot_digest != original.snapshot_digest
    assert nxt.design_payload["spec"]["scale_length_mm"] == 646.0


@pytest.mark.unit
def test_identity_timestamps_digests_and_versions_fail_closed():
    with pytest.raises(DesignSnapshotError) as blank:
        ExternalJobReferenceV1("CNC-Production-Shop", "  ", "UNVERIFIED_EXTERNAL_REFERENCE")
    assert blank.value.code == "JOB_ID"
    with pytest.raises(DesignSnapshotError) as digest:
        ArtifactReferenceV1("art-1", "opaque", "XYZ")
    assert digest.value.code == "MALFORMED_DIGEST"
    with pytest.raises(DesignSnapshotError) as version:
        LtbDesignSnapshotV1(
            SCHEMA_ID, "1.2", "dsn-synth-0001", None, None, "", None, {}, "", (), (), "",
        )
    assert version.value.code == "UNKNOWN_SCHEMA_VERSION"
    with pytest.raises(DesignSnapshotError) as number:
        _capture({"scale_length_mm": float("nan")})
    assert number.value.code == "NON_FINITE"
    with pytest.raises(DesignSnapshotError) as clock:
        _capture({}, captured_at=datetime(2026, 10, 28, 17, 0))
    assert clock.value.code == "TIMESTAMP"


@pytest.mark.unit
def test_unicode_uses_ascii_escapes_and_digest_excludes_itself(baseline_state):
    snap = _capture({"label": "café"})
    text = canonical_record_text(snap)
    assert "\\u00e9" in text
    fields = snapshot_fields(snap)
    held = fields.pop("snapshot_digest")
    assert payload_digest(fields) == held
    assert "snapshot_digest" not in canonical_json(fields)


@pytest.mark.unit
def test_job_and_project_identity_stay_unverified_and_mutable(baseline_state):
    first = _capture(baseline_state)
    second = _capture(baseline_state, design_snapshot_id="dsn-synth-0002")
    assert first.external_job_ref.job_id == "JOB-SYNTH-0001"
    assert first.external_job_ref.verification_status == "UNVERIFIED_EXTERNAL_REFERENCE"
    assert first.project_ref.project_id == "project-synth-0001"
    assert first.project_ref.project_schema_id is None
    assert first.project_ref.project_schema_version == "1.1"
    assert first.design_snapshot_id != second.design_snapshot_id
    assert first.design_payload_digest == second.design_payload_digest
    with pytest.raises(DesignSnapshotError) as verified:
        ExternalJobReferenceV1("CNC-Production-Shop", "JOB-1", "VERIFIED_EXTERNAL_REFERENCE")
    assert verified.value.code == "JOB_UNVERIFIED_ONLY"


@pytest.mark.unit
def test_snapshot_types_have_no_approval_field():
    names = set()
    for cls in (
        LtbDesignSnapshotV1, ExternalJobReferenceV1, LtbProjectReferenceV1,
        ActorReferenceV1, ArtifactReferenceV1, GeneratorReferenceV1,
    ):
        names.update(cls.__dataclass_fields__)
    forbidden = ("approv", "safe_to_run", "manufacturing_authorized", "cam_approved", "ready")
    assert [name for name in names if any(word in name for word in forbidden)] == []


@pytest.mark.unit
def test_cnc_conformance_fixture_matches_the_golden_and_claims_no_authority(golden_text):
    doc = json.loads((FIXTURES / "cnc_consumer_conformance.json").read_text(encoding="utf-8"))
    snap = json.loads(golden_text)
    assert doc["design_snapshot_id"] == snap["design_snapshot_id"]
    assert doc["design_payload_digest"] == snap["design_payload_digest"]
    assert doc["snapshot_digest"] == snap["snapshot_digest"]
    assert doc["external_job"]["verification_status"] == "UNVERIFIED_EXTERNAL_REFERENCE"
    assert "does not prove" in doc["statement"]


@pytest.mark.unit
def test_payload_rejects_boolean_numbers_paths_and_secrets():
    with pytest.raises(DesignSnapshotError) as boolean:
        _capture({"scale_length_mm": True})
    assert boolean.value.code == "BOOLEAN_AS_NUMBER"
    with pytest.raises(DesignSnapshotError) as path:
        _capture({"notes": "/var/private/design.json"})
    assert path.value.code == "ABSOLUTE_PATH"
    with pytest.raises(DesignSnapshotError) as secret:
        _capture({"api_key": "not-a-customer-value"})
    assert secret.value.code == "SECRET_KEY"

@pytest.mark.unit
def test_snapshot_payload_is_deeply_immutable_and_accepts_mapping_input():
    source = MappingProxyType({
        "nested": MappingProxyType({"value": 1}),
        "points": [[1.0, 2.0]],
    })
    snap = _capture(source)

    with pytest.raises(TypeError, match="immutable"):
        snap.design_payload["new"] = "value"
    with pytest.raises(TypeError, match="immutable"):
        snap.design_payload["nested"]["value"] = 2
    with pytest.raises(TypeError, match="immutable"):
        snap.design_payload["points"].append([3.0, 4.0])

    assert snap.design_payload["nested"]["value"] == 1
    assert snap.design_payload["points"] == [[1.0, 2.0]]

    rebuilt = replace(snap, artifact_refs=list(snap.artifact_refs), generator_refs=list(snap.generator_refs))
    assert isinstance(rebuilt.artifact_refs, tuple)
    assert isinstance(rebuilt.generator_refs, tuple)
    with pytest.raises(DesignSnapshotError) as bad_ref:
        replace(snap, artifact_refs=[object()])
    assert bad_ref.value.code == "ARTIFACT"

