"""Plate prediction via Rayleigh–Ritz wrapper (MESH-MAT-001)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from app.mesh.materials.evidence import import_material_evidence
from app.mesh.materials.orthotropic import (
    IncompleteMaterialStateError,
    OrthotropicMaterialState,
    PlateGeometry,
)
from app.mesh.materials.predictor import predict_plate_modes

from ._helpers import fixture, load_json

MATERIALS_PKG = (
    Path(__file__).resolve().parents[3] / "app" / "mesh" / "materials"
)


def _complete_prediction():
    bundle = import_material_evidence(fixture("complete_spruce_evidence.json"))
    state = OrthotropicMaterialState.from_evidence(bundle)
    geom = PlateGeometry(**load_json(
        Path(__file__).resolve().parents[2] / "fixtures" / "materials" / "plate_geometry.json"
    ))
    return predict_plate_modes(state, geom, n_modes_return=4)


def test_predict_emits_predicted_research_only():
    pred = _complete_prediction()
    d = pred.to_dict()
    assert d["epistemic_status"] == "predicted"
    assert d["research_only"] is True
    assert d["schema_id"] == "material_prediction"
    assert len(d["predicted_modes"]) >= 1
    freqs = [m["frequency_hz"] for m in d["predicted_modes"]]
    assert freqs == sorted(freqs)
    assert all(a.get("assumption") is True for a in d["assumptions"])


def test_predict_fail_closed_without_ec():
    bundle = import_material_evidence(fixture("incomplete_missing_ec.json"))
    state = OrthotropicMaterialState.from_evidence(bundle)
    geom = PlateGeometry(thickness_m=0.003, length_m=0.4, width_m=0.28)
    with pytest.raises(IncompleteMaterialStateError, match="requires E_C"):
        predict_plate_modes(state, geom)


def test_no_inverse_solver_imports():
    for path in MATERIALS_PKG.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                mod = getattr(node, "module", None) or ""
                names = [
                    (alias.name if hasattr(alias, "name") else "")
                    for alias in getattr(node, "names", [])
                ]
                blob = " ".join([mod, *names])
                assert "inverse_solver" not in blob, (
                    f"{path.name} must not import inverse_solver"
                )


def test_no_thickness_recommendation_surface():
    for path in MATERIALS_PKG.glob("*.py"):
        src = path.read_text(encoding="utf-8").lower()
        assert "recommend_thickness" not in src
        assert "thickness_recommendation" not in src
