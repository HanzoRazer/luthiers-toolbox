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


def test_research_only_false_rejected():
    """
    research_only is constitutional for MESH-MAT-001, not a caller preference.

    Accepting false would let a payload mint a non-research bundle out of a
    package whose whole premise is that it carries no CAM authority.
    """
    payload = copy.deepcopy(fixture("complete_spruce_evidence.json"))
    payload["research_only"] = False
    with pytest.raises(MaterialEvidenceError, match="research_only"):
        import_material_evidence(payload)


def test_research_only_true_and_absent_both_accepted():
    payload = copy.deepcopy(fixture("complete_spruce_evidence.json"))
    payload["research_only"] = True
    assert import_material_evidence(payload).research_only is True
    payload.pop("research_only", None)
    assert import_material_evidence(payload).research_only is True


def test_duplicate_property_rejected():
    """``bundle.get()`` returns the first match, so a duplicate is silent precedence."""
    payload = copy.deepcopy(fixture("complete_spruce_evidence.json"))
    first = copy.deepcopy(payload["values"][0])
    first["value"] = float(first["value"]) * 2.0
    payload["values"].append(first)
    with pytest.raises(MaterialEvidenceError, match="Duplicate evidence"):
        import_material_evidence(payload)


def test_duplicate_after_canonicalization_rejected():
    """
    E_L (GPa) and E_L_Pa (Pa) both normalize onto E_L_Pa, so a bundle carrying
    both is a duplicate even though the payload names look distinct.
    """
    payload = copy.deepcopy(fixture("complete_spruce_evidence.json"))
    payload["values"].append(
        {
            "property": "E_L",
            "value": 9.0,
            "unit": "GPa",
            "epistemic_status": "estimated",
        }
    )
    with pytest.raises(MaterialEvidenceError, match="Duplicate evidence"):
        import_material_evidence(payload)


def test_values_string_rejected_not_treated_as_sequence():
    """``str`` satisfies ``Sequence``; a JSON array is what is actually required."""
    payload = copy.deepcopy(fixture("complete_spruce_evidence.json"))
    payload["values"] = "E_L_Pa"
    with pytest.raises(MaterialEvidenceError, match="non-empty list"):
        import_material_evidence(payload)
