"""Measured-vs-predicted residual reporting (MESH-MAT-001)."""

from __future__ import annotations

from pathlib import Path

from app.mesh.materials.evidence import import_material_evidence
from app.mesh.materials.orthotropic import OrthotropicMaterialState, PlateGeometry
from app.mesh.materials.predictor import predict_plate_modes
from app.mesh.materials.residuals import compare_modal_prediction

from ._helpers import fixture, load_json


def test_residual_report_research_only():
    bundle = import_material_evidence(fixture("complete_spruce_evidence.json"))
    state = OrthotropicMaterialState.from_evidence(bundle)
    geom = PlateGeometry(**load_json(
        Path(__file__).resolve().parents[2]
        / "fixtures"
        / "materials"
        / "plate_geometry.json"
    ))
    pred = predict_plate_modes(state, geom, n_modes_return=4)
    report = compare_modal_prediction(pred, bundle.modal_evidence, tolerance_hz=50.0)
    d = report.to_dict()
    assert d["schema_id"] == "prediction_residual"
    assert d["epistemic_status"] == "predicted"
    assert d["research_only"] is True
    assert len(d["residuals"]) >= 1
    statuses = {r["status"] for r in d["residuals"]}
    assert statuses <= {"MATCHED", "MISMATCHED", "NO_MEASUREMENT", "NO_PREDICTION"}
