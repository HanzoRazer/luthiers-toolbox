"""Applicability checks. Resolution does not grant review or manufacture."""
from __future__ import annotations

import json

import pytest

from app.physical_engineering.errors import EvidenceDigestMismatch, EvidenceNotFound
from app.physical_engineering.evidence import EvidenceRef, ResolvedEvidence
from app.physical_engineering.stored_evidence_repository import FileEvidenceRepository
from app.physical_engineering.stored_evidence_resolver import (
    ApplicabilityContext,
    StoredEvidenceResolutionError,
    StoredEvidenceResolver,
    duplicate_reference_ids,
)
from .test_evidence_artifact_v1 import make_record


def context(**over) -> ApplicabilityContext:
    base = dict(
        subject_id="plate-007",
        subject_revision="rev-3",
        region_id="lower-bout-R17",
        coordinate_frame="plate-local",
        unit_by_kind=(("thickness_map", "mm"), ("modal_frequency", "hz")),
    )
    base.update(over)
    return ApplicabilityContext(**base)


def evidence_dir(tmp_path):
    """Exclusive store directory. The suite fixture writes other JSON in tmp_path."""
    return tmp_path / "evidence"


def resolver(tmp_path, **over):
    return StoredEvidenceResolver(FileEvidenceRepository(evidence_dir(tmp_path)), context(**over))


def test_matching_record_resolves_to_the_protocol_fact(tmp_path):
    record = make_record()
    FileEvidenceRepository(evidence_dir(tmp_path)).save(record)
    fact = resolver(tmp_path).resolve(EvidenceRef(record.evidence_id, "thickness_map"))
    assert isinstance(fact, ResolvedEvidence)
    assert fact.ref_id == record.evidence_id
    assert fact.kind == "thickness_map"
    assert fact.value == 2.9
    assert fact.unit == "mm"
    assert fact.artifact_sha256 == record.payload_digest
    assert not hasattr(fact, "advisory_review_allowed")


def test_missing_id_is_not_found(tmp_path):
    with pytest.raises(EvidenceNotFound):
        resolver(tmp_path).resolve(EvidenceRef("missing-evidence", "thickness_map"))


def test_wrong_subject_is_subject_mismatch(tmp_path):
    FileEvidenceRepository(evidence_dir(tmp_path)).save(make_record())
    with pytest.raises(StoredEvidenceResolutionError, match="SUBJECT_MISMATCH") as caught:
        resolver(tmp_path, subject_id="plate-999").resolve(
            EvidenceRef("thk-plate-007", "thickness_map")
        )
    assert caught.value.code == "SUBJECT_MISMATCH"


def test_wrong_revision_is_revision_mismatch(tmp_path):
    FileEvidenceRepository(evidence_dir(tmp_path)).save(make_record())
    with pytest.raises(StoredEvidenceResolutionError, match="REVISION_MISMATCH"):
        resolver(tmp_path, subject_revision="rev-9").resolve(
            EvidenceRef("thk-plate-007", "thickness_map")
        )


def test_wrong_region_is_region_mismatch(tmp_path):
    FileEvidenceRepository(evidence_dir(tmp_path)).save(make_record())
    with pytest.raises(StoredEvidenceResolutionError, match="REGION_MISMATCH"):
        resolver(tmp_path, region_id="upper-bout").resolve(
            EvidenceRef("thk-plate-007", "thickness_map")
        )


def test_unit_not_in_the_caller_binding_is_unit_mismatch(tmp_path):
    FileEvidenceRepository(evidence_dir(tmp_path)).save(make_record(unit="inches"))
    with pytest.raises(StoredEvidenceResolutionError, match="UNIT_MISMATCH"):
        resolver(tmp_path).resolve(EvidenceRef("thk-plate-007", "thickness_map"))


def test_superseded_record_is_refused(tmp_path):
    repository = FileEvidenceRepository(evidence_dir(tmp_path))
    repository.save(make_record())
    repository.save(make_record(evidence_id="thk-plate-007-b", quantity_value="3.0", supersedes_evidence_id="thk-plate-007"))
    with pytest.raises(StoredEvidenceResolutionError, match="SUPERSEDED"):
        resolver(tmp_path).resolve(EvidenceRef("thk-plate-007", "thickness_map"))
    fact = resolver(tmp_path).resolve(EvidenceRef("thk-plate-007-b", "thickness_map"))
    assert fact.value == 3.0


def test_duplicate_reference_ids_are_reported_in_citation_order():
    first = EvidenceRef("thk-plate-007", "thickness_map")
    second = EvidenceRef("mode-plate-007", "modal_frequency")
    assert duplicate_reference_ids((first, second, first)) == ("thk-plate-007",)


def test_two_active_values_require_policy_instead_of_a_tolerance(tmp_path):
    repository = FileEvidenceRepository(evidence_dir(tmp_path))
    repository.save(make_record())
    repository.save(make_record(evidence_id="thk-plate-007-b", quantity_value="3.1"))
    with pytest.raises(StoredEvidenceResolutionError, match="MULTIPLE_VALUES_REQUIRE_POLICY"):
        resolver(tmp_path).resolve(EvidenceRef("thk-plate-007", "thickness_map"))


def test_different_quantities_are_not_treated_as_contradictions(tmp_path):
    repository = FileEvidenceRepository(evidence_dir(tmp_path))
    repository.save(make_record())
    repository.save(
        make_record(
            evidence_id="mode-plate-007",
            evidence_kind="modal_frequency",
            quantity_name="frequency",
            quantity_value="184.6",
            unit="hz",
            uncertainty="1.8",
        )
    )
    facts = [
        resolver(tmp_path).resolve(EvidenceRef("thk-plate-007", "thickness_map")),
        resolver(tmp_path).resolve(EvidenceRef("mode-plate-007", "modal_frequency")),
    ]
    assert [fact.kind for fact in facts] == ["thickness_map", "modal_frequency"]


def test_resolve_does_not_change_the_stored_bytes(tmp_path):
    record = make_record()
    FileEvidenceRepository(evidence_dir(tmp_path)).save(record)
    path = evidence_dir(tmp_path) / f"{record.evidence_id}.json"
    before = path.read_bytes()
    resolver(tmp_path).resolve(EvidenceRef(record.evidence_id, "thickness_map"))
    assert path.read_bytes() == before


def test_repeated_resolution_is_deterministic(tmp_path):
    FileEvidenceRepository(evidence_dir(tmp_path)).save(make_record())
    engine = resolver(tmp_path)
    ref = EvidenceRef("thk-plate-007", "thickness_map")
    assert engine.resolve(ref) == engine.resolve(ref)


def test_tampered_file_is_digest_mismatch(tmp_path):
    record = make_record()
    FileEvidenceRepository(evidence_dir(tmp_path)).save(record)
    path = evidence_dir(tmp_path) / f"{record.evidence_id}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["quantity_value"] = "8.0"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(EvidenceDigestMismatch):
        resolver(tmp_path).resolve(EvidenceRef(record.evidence_id, "thickness_map"))


def test_stored_record_cannot_be_mutated():
    record = make_record()
    with pytest.raises(AttributeError):
        record.quantity_value = "1.0"
