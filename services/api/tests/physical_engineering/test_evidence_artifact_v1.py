"""Stored-evidence record rules. Construction failure writes nothing."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.physical_engineering.evidence_artifact_v1 import (
    EvidenceProvenance,
    EvidenceRecordError,
    make_evidence_artifact,
    record_fields,
)
from app.physical_engineering.evidence_serialization import payload_digest


def provenance() -> EvidenceProvenance:
    return EvidenceProvenance(
        source_type="manual_measurement",
        source_id="caliper-17",
        operator_or_process="bench-measurement",
    )


def make_record(**over):
    observed = datetime(2026, 10, 23, 15, 0, tzinfo=timezone.utc)
    base = dict(
        evidence_id="thk-plate-007",
        evidence_type="MEASURED",
        evidence_kind="thickness_map",
        subject_id="plate-007",
        subject_revision="rev-3",
        region_id="lower-bout-R17",
        coordinate_frame="plate-local",
        quantity_name="thickness",
        quantity_value="2.9",
        unit="mm",
        uncertainty="0.05",
        observed_at=observed,
        recorded_at=observed,
        provenance=provenance(),
    )
    base.update(over)
    return make_evidence_artifact(**base)


def test_valid_record_is_accepted_and_digest_matches():
    record = make_record()
    assert record.schema_id == "ltb_stored_evidence_artifact"
    assert record.evidence_type == "MEASURED"
    assert record.payload_digest == payload_digest(record_fields(record))
    assert "approved" not in record_fields(record)


def test_blank_evidence_id_is_refused():
    with pytest.raises(EvidenceRecordError):
        make_record(evidence_id=" ")


def test_blank_subject_id_is_refused():
    with pytest.raises(EvidenceRecordError):
        make_record(subject_id="")


def test_missing_subject_revision_is_refused():
    with pytest.raises(EvidenceRecordError):
        make_record(subject_revision=" ")


def test_missing_region_is_refused():
    with pytest.raises(EvidenceRecordError):
        make_record(region_id="")


def test_unknown_evidence_type_is_refused():
    with pytest.raises(EvidenceRecordError, match="evidence type"):
        make_record(evidence_type="GUESSED")


def test_non_identifier_unit_is_refused_without_conversion():
    with pytest.raises(EvidenceRecordError, match="unit"):
        make_record(unit="MM")


def test_non_finite_quantity_text_is_refused():
    with pytest.raises(EvidenceRecordError):
        make_record(quantity_value="nan")
    with pytest.raises(EvidenceRecordError):
        make_record(quantity_value="inf")
    with pytest.raises(EvidenceRecordError):
        make_record(uncertainty="-1")


def test_naive_timestamp_is_refused():
    with pytest.raises(EvidenceRecordError, match="timezone-aware"):
        make_record(observed_at=datetime(2026, 10, 23, 15, 0))


def test_changed_digest_is_refused_at_construction():
    record = make_record()
    fields = record_fields(record)
    fields["payload_digest"] = "0" * 64
    with pytest.raises(EvidenceRecordError, match="DIGEST_MISMATCH"):
        from app.physical_engineering.evidence_artifact_v1 import (
            LtbStoredEvidenceArtifactV1,
        )

        LtbStoredEvidenceArtifactV1(
            **{key: fields[key] for key in fields if key != "provenance"},
            provenance=record.provenance,
        )
