"""Tests for MaterialEvidenceBundle import (MESH-MAT-001)."""

from __future__ import annotations

import copy

import pytest

from app.mesh.materials.evidence import (
    MaterialEvidenceError,
    import_material_evidence,
)

from ._helpers import fixture


def test_import_complete_fixture_canonicalizes_si():
    bundle = import_material_evidence(fixture("complete_spruce_evidence.json"))
    assert bundle.specimen_id == "FIXTURE-SPRUCE-001"
    assert bundle.research_only is True
    el = bundle.get("E_L_Pa")
    ec = bundle.get("E_C_Pa")
    rho = bundle.get("density_kg_m3")
    assert el is not None and abs(el.value - 11.5e9) < 1.0
    assert ec is not None and abs(ec.value - 0.85e9) < 1.0
    assert rho is not None and rho.value == 420.0
    assert el.epistemic_status == "observed"
    assert el.source_artifact_id is not None
    assert len(bundle.modal_evidence) == 2


def test_observed_without_provenance_rejected():
    payload = fixture("complete_spruce_evidence.json")
    payload = copy.deepcopy(payload)
    payload["values"][0].pop("source_artifact_id", None)
    payload["values"][0].pop("source_hash", None)
    with pytest.raises(MaterialEvidenceError, match="requires source_artifact_id"):
        import_material_evidence(payload)


def test_caller_hardware_true_rejected():
    payload = copy.deepcopy(fixture("complete_spruce_evidence.json"))
    payload["provenance"]["HARDWARE"] = True
    with pytest.raises(MaterialEvidenceError, match="HARDWARE=true is forbidden"):
        import_material_evidence(payload)


def test_legacy_measured_status_rejected():
    payload = copy.deepcopy(fixture("complete_spruce_evidence.json"))
    payload["values"][0]["epistemic_status"] = "measured"
    with pytest.raises(MaterialEvidenceError, match="Unsupported epistemic_status"):
        import_material_evidence(payload)


def test_unknown_status_rejected_use_absence():
    payload = copy.deepcopy(fixture("complete_spruce_evidence.json"))
    payload["values"][0]["epistemic_status"] = "unknown"
    with pytest.raises(MaterialEvidenceError, match="Unsupported epistemic_status"):
        import_material_evidence(payload)


def test_empty_values_rejected():
    with pytest.raises(MaterialEvidenceError, match="non-empty"):
        import_material_evidence({"specimen_id": "x", "values": []})
