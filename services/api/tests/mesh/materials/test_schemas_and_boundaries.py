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
