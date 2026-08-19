"""OrthotropicMaterialState from evidence (MESH-MAT-001)."""

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

from ._helpers import fixture

MATERIALS_PKG = (
    Path(__file__).resolve().parents[3] / "app" / "mesh" / "materials"
)


def test_complete_state_serializes_assumptions_not_from_wood():
    bundle = import_material_evidence(fixture("complete_spruce_evidence.json"))
    state = OrthotropicMaterialState.from_evidence(bundle)
    assert state.is_complete_for_prediction
    assert state.e_crossgrain_pa is not None
    names = {a.name for a in state.assumptions}
    assert "G_LC_Pa" in names
    assert "nu_LC" in names
    assert "nu_CL" in names
    for a in state.assumptions:
        assert a.assumption is True
    plate = state.to_orthotropic_plate(
        PlateGeometry(thickness_m=0.003, length_m=0.4, width_m=0.28)
    )
    assert plate.E_L == state.e_longitudinal_pa
    assert plate.E_C == state.e_crossgrain_pa
    assert abs(plate.G_LC - 0.06 * state.e_longitudinal_pa) < 1.0


def test_missing_ec_incomplete_fail_closed():
    bundle = import_material_evidence(fixture("incomplete_missing_ec.json"))
    state = OrthotropicMaterialState.from_evidence(bundle)
    assert not state.is_complete_for_prediction
    assert state.e_crossgrain_pa is None
    with pytest.raises(IncompleteMaterialStateError, match="without E_C"):
        state.to_orthotropic_plate(
            PlateGeometry(thickness_m=0.003, length_m=0.4, width_m=0.28)
        )


def test_materials_package_never_calls_from_wood():
    """Static guard: research path must not invoke OrthotropicPlate.from_wood."""
    for path in MATERIALS_PKG.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr == "from_wood":
                pytest.fail(f"{path.name} references from_wood")
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Attribute) and func.attr == "from_wood":
                    pytest.fail(f"{path.name} calls from_wood")


def test_incomplete_state_omits_nu_cl_rather_than_publishing_zero():
    """
    Without E_C, Poisson reciprocity is undefined — nu_CL is unknown, not zero.

    A serialized ``"nu_CL": 0.0`` would read as a known measurement of zero,
    which is a different and false claim than "unavailable".
    """
    bundle = import_material_evidence(fixture("incomplete_missing_ec.json"))
    state = OrthotropicMaterialState.from_evidence(bundle)
    d = state.to_dict()
    assert state.nu_cl is None
    assert "nu_CL" not in d
    assert d["complete_for_prediction"] is False
    assert all(a["name"] != "nu_CL" for a in d["assumptions"])


def test_complete_state_publishes_nu_cl_from_reciprocity():
    bundle = import_material_evidence(fixture("complete_spruce_evidence.json"))
    d = OrthotropicMaterialState.from_evidence(bundle).to_dict()
    assert d["nu_CL"] > 0
    assert any(
        a["name"] == "nu_CL" and "Reciprocity" in a["rationale"]
        for a in d["assumptions"]
    )


def test_caller_overrides_are_recorded_as_assumptions():
    """
    An override bypasses evidence and the literature defaults alike. If it did
    not surface in ``assumptions`` it would be indistinguishable from measured
    evidence in the serialized state.
    """
    bundle = import_material_evidence(fixture("complete_spruce_evidence.json"))
    state = OrthotropicMaterialState.from_evidence(
        bundle, g_lc_pa=7.0e8, nu_lc=0.42, nu_cl=0.05
    )
    by_name = {a["name"]: a for a in state.to_dict()["assumptions"]}
    for name, value in (("G_LC_Pa", 7.0e8), ("nu_LC", 0.42), ("nu_CL", 0.05)):
        assert by_name[name]["value"] == value
        assert "override" in by_name[name]["rationale"].lower()
        assert by_name[name]["assumption"] is True
