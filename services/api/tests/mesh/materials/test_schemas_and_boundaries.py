"""Schema + package boundary checks (MESH-MAT-001)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")

from app.mesh.materials.evidence import import_material_evidence
from app.mesh.materials.orthotropic import OrthotropicMaterialState, PlateGeometry
from app.mesh.materials.predictor import predict_plate_modes
from app.mesh.materials.residuals import compare_modal_prediction

from ._helpers import contract_schema, fixture, load_json

REPO_ROOT = Path(__file__).resolve().parents[5]


def test_evidence_fixture_validates_against_schema():
    schema = contract_schema("material_evidence.schema.json")
    jsonschema.validate(fixture("complete_spruce_evidence.json"), schema)
    jsonschema.validate(fixture("incomplete_missing_ec.json"), schema)


def test_prediction_and_residual_validate():
    bundle = import_material_evidence(fixture("complete_spruce_evidence.json"))
    state = OrthotropicMaterialState.from_evidence(bundle)
    geom = PlateGeometry(**load_json(
        Path(__file__).resolve().parents[2]
        / "fixtures"
        / "materials"
        / "plate_geometry.json"
    ))
    pred = predict_plate_modes(state, geom, n_modes_return=3)
    pred_schema = contract_schema("material_prediction.schema.json")
    jsonschema.validate(pred.to_dict(), pred_schema)

    residual = compare_modal_prediction(pred, bundle.modal_evidence)
    res_schema = contract_schema("prediction_residual.schema.json")
    jsonschema.validate(residual.to_dict(), res_schema)


def test_schema_registry_lists_mesh_mat_contracts():
    registry = json.loads(
        (REPO_ROOT / "contracts" / "schema_registry.json").read_text(encoding="utf-8")
    )
    ids = {s["schema_id"] for s in registry["schemas"]}
    assert {"material_evidence", "material_prediction", "prediction_residual"} <= ids


def test_no_qa_core_or_cam_policy_mutation_in_diff_scope():
    """Guards that MESH-MAT research sidecars do not touch manufacturing contracts."""
    for name in ("qa_core.schema.json", "cam_policy.schema.json"):
        path = REPO_ROOT / "contracts" / name
        assert path.is_file()
        # Presence only — mutation would be a git-level concern; pin that
        # materials package does not import those schema modules.
    pkg = REPO_ROOT / "services" / "api" / "app" / "mesh" / "materials"
    for path in pkg.glob("*.py"):
        src = path.read_text(encoding="utf-8")
        assert "qa_core" not in src
        assert "cam_policy" not in src


def test_not_under_app_materials_tonewood_registry():
    """Specimen evidence must live under app.mesh.materials, not app.materials."""
    mesh_pkg = REPO_ROOT / "services" / "api" / "app" / "mesh" / "materials"
    assert (mesh_pkg / "evidence.py").is_file()
    # Ensure we did not drop research modules into the tonewood package.
    tonewood = REPO_ROOT / "services" / "api" / "app" / "materials"
    for forbidden in ("evidence.py", "orthotropic.py", "predictor.py", "residuals.py"):
        assert not (tonewood / forbidden).exists()


@pytest.mark.parametrize("status", ["observed", "derived"])
def test_schema_and_importer_agree_on_provenance_requirement(status):
    """
    The importer rejects observed/derived evidence without provenance. If the
    schema did not encode the same rule, a payload could pass contract
    validation at an integration boundary and still be rejected at import —
    which makes the published contract a weaker promise than it looks.
    """
    import copy

    from app.mesh.materials.evidence import MaterialEvidenceError

    schema = contract_schema("material_evidence.schema.json")
    payload = copy.deepcopy(fixture("complete_spruce_evidence.json"))
    payload["values"] = [
        {
            "property": "density_kg_m3",
            "value": 420.0,
            "unit": "kg/m3",
            "epistemic_status": status,
        }
    ]

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(payload, schema)
    with pytest.raises(MaterialEvidenceError, match="source_artifact_id or source_hash"):
        import_material_evidence(payload)

    # With provenance, both accept it.
    payload["values"][0]["source_hash"] = "a" * 64
    jsonschema.validate(payload, schema)
    assert import_material_evidence(payload).get("density_kg_m3") is not None


def test_schema_and_importer_agree_on_research_only():
    import copy

    from app.mesh.materials.evidence import MaterialEvidenceError

    schema = contract_schema("material_evidence.schema.json")
    payload = copy.deepcopy(fixture("complete_spruce_evidence.json"))
    payload["research_only"] = False
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(payload, schema)
    with pytest.raises(MaterialEvidenceError, match="research_only"):
        import_material_evidence(payload)


def test_contract_hashes_match_schema_bytes():
    """
    Each *.schema.sha256 must be the sha256 of its schema file, as a single
    lowercase 64-hex line — the form scripts/ci/check_contracts_governance.py
    enforces. A stale hash silently detaches the contract from its checksum.
    """
    import hashlib
    import re

    contracts_dir = REPO_ROOT / "contracts"
    for name in ("material_evidence", "material_prediction", "prediction_residual"):
        schema_path = contracts_dir / f"{name}.schema.json"
        sha_path = contracts_dir / f"{name}.schema.sha256"
        recorded = sha_path.read_text(encoding="utf-8").strip()
        assert re.fullmatch(r"[0-9a-f]{64}", recorded), f"{name}: malformed sha file"
        assert recorded == hashlib.sha256(schema_path.read_bytes()).hexdigest(), (
            f"{name}.schema.sha256 does not match {name}.schema.json"
        )
