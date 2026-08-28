"""RMOS-DRILLING-CONTRACT-001 — truthful drilling authority contract.

No production gate. Modal G81/G83 remain 200. Drilling stays
AUTHORITY_CONTRACT_MISMATCH. Isolated TestClient. Ephemeral RMOS stores.
"""
from __future__ import annotations

import ast
import inspect
import json
from pathlib import Path

import pytest

from app.cam.drilling.feasibility import (
    compute_drilling_feasibility,
    compute_drilling_feasibility_from_spec,
)
from app.cam.drilling.operation_contract import (
    HeterogeneousFeedError,
    IncompleteDrillingContractError,
    feasibility_kwargs,
    physical_depth_mm,
    spec_from_intent,
    spec_from_modal,
    spec_from_pattern,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
REGISTRY_PATH = (
    REPO_ROOT / "services/api/app/rmos/manufacturing_authority_registry.json"
)
CONTRACT = REPO_ROOT / "services/api/app/cam/drilling/operation_contract.py"
MODAL_ROUTER = (
    REPO_ROOT / "services/api/app/cam/routers/drilling/drill_modal_router.py"
)
ENGINE_ROUTER = (
    REPO_ROOT / "services/api/app/rmos/api/rmos_feasibility_router.py"
)

FROZEN_DISPOSITIONS = {
    "drilling": "AUTHORITY_CONTRACT_MISMATCH",
    "profiling": "GOVERNED",
    "vcarve": "POST_MERGE_AUTHORITY_EXPOSURE",
    "retract": "BLOCKED_BY_DESIGN",
    "adaptive": "GOVERNED",
}

MODAL_G81 = {
    "holes": [{"x": 10.0, "y": 20.0, "z": -5.0, "feed": 100.0}],
    "cycle": "G81",
    "safe_z": 5.0,
    "r_clear": 2.0,
}
MODAL_G83 = {
    "holes": [{"x": 15.0, "y": 25.0, "z": -10.0, "feed": 80.0}],
    "cycle": "G83",
    "peck_q": 2.0,
    "safe_z": 5.0,
    "r_clear": 3.0,
}


def _by_id(registry):
    return {c["capability_id"]: c for c in registry["capabilities"]}


@pytest.fixture(scope="module")
def registry():
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


@pytest.fixture()
def client(tmp_path, monkeypatch):
    runs = tmp_path / "rmos_runs"
    runs.mkdir(parents=True, exist_ok=True)
    (runs / "_index.json").write_text("{}", encoding="utf-8")
    monkeypatch.setenv("RMOS_RUNS_DIR", str(runs))
    monkeypatch.setenv("RMOS_RUN_ATTACHMENTS_DIR", str(tmp_path / "att"))
    monkeypatch.setenv("RMOS_ARTIFACT_ROOT", str(tmp_path / "run_artifacts"))
    monkeypatch.setenv("ART_STUDIO_DB_PATH", str(tmp_path / "art.db"))
    monkeypatch.setenv("ENV", "test")
    try:
        from app.rmos.runs_v2 import store_api as runs_v2_store_api
        runs_v2_store_api._default_store = None
    except ImportError:
        pass
    from fastapi.testclient import TestClient
    from app.main import app

    return TestClient(app)


def _complete_modal(**ov):
    body = dict(
        holes=[(10.0, 20.0, -5.0, 100.0)],
        r_clear=2.0,
        peck_q=None,
        cycle="G81",
        safe_z=5.0,
        units="mm",
        rpm=2000.0,
        tool=4,
        hole_diameter=3.0,
        surface_z=0.0,
    )
    body.update(ov)
    return spec_from_modal(**body)


def _intent_spec(**ov):
    kw = dict(
        holes_xy=[(0.0, 0.0), (10.5, 0.0)],
        per_hole_depth_mm=[None, None],
        hole_depth_mm=20.0,
        hole_diameter_mm=3.0,
        peck_drilling=True,
        peck_depth_mm=5.0,
        feed_rate_mm_min=100.0,
        spindle_rpm=2000.0,
        safe_z_mm=10.0,
        retract_z_mm=2.0,
    )
    kw.update(ov)
    return spec_from_intent(**kw)


# --- contract 001–010 ---


def test_drill_001_diameter_is_explicit():
    spec = _complete_modal()
    assert spec.hole_diameter_mm == 3.0
    assert spec.is_complete_for_feasibility()


def test_drill_002_target_z_is_not_depth():
    spec = spec_from_modal(
        holes=[(0.0, 0.0, -5.0, 100.0)],
        r_clear=2.0,
        peck_q=None,
        cycle="G81",
        safe_z=5.0,
        units="mm",
        rpm=2000.0,
        tool=1,
    )
    assert spec.holes[0].target_z_mm == -5.0
    assert spec.holes[0].depth_mm is None
    assert spec.hole_depth_mm is None
    assert "missing_hole_depth_mm" in spec.incomplete_reasons


def test_drill_003_datum_is_explicit():
    assert physical_depth_mm(surface_z_mm=0.0, target_z_mm=-5.0) == 5.0
    spec = _complete_modal(surface_z=0.0)
    assert spec.surface_z_mm == 0.0
    assert spec.hole_depth_mm == 5.0
    bare = spec_from_modal(
        holes=[(0.0, 0.0, -5.0, 100.0)],
        r_clear=2.0, peck_q=None, cycle="G81", safe_z=5.0,
        units="mm", rpm=2000.0, tool=None, hole_diameter=3.0,
    )
    assert "missing_surface_z_mm" in bare.incomplete_reasons


def test_drill_004_tool_is_not_diameter():
    spec = spec_from_modal(
        holes=[(0.0, 0.0, -5.0, 100.0)],
        r_clear=2.0, peck_q=None, cycle="G81", safe_z=5.0,
        units="mm", rpm=2000.0, tool=6, hole_diameter=None, surface_z=0.0,
    )
    assert spec.tool_number == 6
    assert spec.hole_diameter_mm is None
    assert "missing_hole_diameter_mm" in spec.incomplete_reasons


def test_drill_005_units_normalization_is_explicit():
    spec = _complete_modal(units="inch", holes=[(1.0, 2.0, -0.2, 4.0)],
                           r_clear=0.1, safe_z=0.2, hole_diameter=0.125,
                           surface_z=0.0, rpm=2000.0)
    assert spec.units == "mm"
    assert spec.holes[0].x_mm == pytest.approx(25.4)
    assert spec.hole_diameter_mm == pytest.approx(0.125 * 25.4)
    bad = _complete_modal(units="furlongs")
    assert "unsupported_units" in bad.incomplete_reasons


def test_drill_006_g81_is_non_peck():
    spec = _complete_modal(cycle="G81")
    assert spec.peck_drilling is False
    assert spec.peck_depth_mm == 0.0


def test_drill_007_g83_is_peck():
    spec = _complete_modal(cycle="G83", peck_q=2.0)
    assert spec.peck_drilling is True


def test_drill_008_peck_depth_maps_truthfully():
    spec = _complete_modal(cycle="G83", peck_q=2.5)
    assert spec.peck_depth_mm == 2.5
    defaulted = _complete_modal(cycle="G83", peck_q=None)
    assert defaulted.peck_depth_mm == 1.0


def test_drill_009_safe_z_preserved():
    spec = _complete_modal(safe_z=7.5)
    assert spec.safe_z_mm == 7.5


def test_drill_010_retract_is_r_plane():
    spec = _complete_modal(r_clear=2.0)
    assert spec.retract_z_mm == 2.0
    defaulted = _complete_modal(r_clear=None)
    assert defaulted.retract_z_mm == 5.0


# --- feed / spindle 011–014 ---


def test_drill_011_per_hole_feeds_remain_distinguishable():
    spec = spec_from_modal(
        holes=[(0.0, 0.0, -5.0, 80.0), (10.0, 0.0, -5.0, 120.0)],
        r_clear=2.0, peck_q=None, cycle="G81", safe_z=5.0,
        units="mm", rpm=2000.0, tool=None, hole_diameter=3.0, surface_z=0.0,
    )
    assert [h.feed_mm_min for h in spec.holes] == [80.0, 120.0]


def test_drill_012_heterogeneous_feed_does_not_collapse():
    spec = spec_from_modal(
        holes=[(0.0, 0.0, -5.0, 80.0), (10.0, 0.0, -5.0, 120.0)],
        r_clear=2.0, peck_q=None, cycle="G81", safe_z=5.0,
        units="mm", rpm=2000.0, tool=None, hole_diameter=3.0, surface_z=0.0,
    )
    assert "heterogeneous_feed" in spec.incomplete_reasons
    with pytest.raises(HeterogeneousFeedError):
        feasibility_kwargs(spec)


def test_drill_013_missing_rpm_is_not_fabricated():
    spec = _complete_modal(rpm=None)
    assert spec.spindle_rpm is None
    assert "missing_spindle_rpm" in spec.incomplete_reasons
    with pytest.raises(IncompleteDrillingContractError):
        feasibility_kwargs(spec)


def test_drill_014_tool_number_is_identity():
    spec = _complete_modal(tool=12, hole_diameter=3.0)
    assert spec.tool_number == 12
    assert spec.hole_diameter_mm == 3.0


# --- evaluator adapter 015–020 ---


def test_drill_015_to_020_canonical_maps_to_evaluator():
    spec = _intent_spec()
    kwargs = feasibility_kwargs(spec)
    assert kwargs["hole_diameter_mm"] == 3.0
    assert kwargs["hole_depth_mm"] == 20.0
    assert kwargs["peck_drilling"] is True
    assert kwargs["peck_depth_mm"] == 5.0
    assert kwargs["feed_rate_mm_min"] == 100.0
    assert kwargs["spindle_rpm"] == 2000.0
    direct = compute_drilling_feasibility(**kwargs)
    via = compute_drilling_feasibility_from_spec(spec)
    assert via.to_dict() == direct.to_dict()


# --- production 021–025 ---


def test_drill_021_modal_g81_still_200(client):
    r = client.post("/api/cam/drilling/gcode", json=MODAL_G81)
    assert r.status_code == 200, r.text
    assert "G81" in r.text and "G80" in r.text


def test_drill_022_modal_g83_still_200(client):
    r = client.post("/api/cam/drilling/gcode", json=MODAL_G83)
    assert r.status_code == 200, r.text
    assert "G83" in r.text and "Q2.000" in r.text


def test_drill_023_no_rmos_gate_on_modal():
    src = MODAL_ROUTER.read_text(encoding="utf-8")
    tree = ast.parse(src)
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
        if isinstance(node, ast.Import):
            imported.extend(a.name for a in node.names)
    assert not any("rmos" in m for m in imported)
    assert "SafetyPolicy" not in src
    fn = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "drill_gcode"][0]
    called = [n.func.id for n in ast.walk(fn) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)]
    assert "compute_drilling_feasibility" not in called


def test_drill_024_no_new_409(client):
    r = client.post("/api/cam/drilling/gcode", json=MODAL_G81)
    assert r.status_code != 409
    extra = dict(MODAL_G81)
    extra["hole_diameter_mm"] = 3.0
    extra["surface_z_mm"] = 0.0
    extra["rpm"] = 2000.0
    r2 = client.post("/api/cam/drilling/gcode", json=extra)
    assert r2.status_code == 200, r2.text
    assert "G81" in r2.text


def test_drill_025_malformed_still_422(client):
    r = client.post("/api/cam/drilling/gcode", json={})
    assert r.status_code == 422


# --- lane isolation 026–031 ---


def test_drill_026_intent_lane_unchanged(client):
    body = {
        "mode": "router_3axis",
        "units": "mm",
        "design": {
            "holes": [{"x": 0, "y": 0}, {"x": 10.5, "y": 0}],
            "hole_depth_mm": 20.0,
            "hole_diameter_mm": 3.0,
            "peck_drilling": True,
            "peck_depth_mm": 5.0,
        },
        "context": {"feed_rate_mm_min": 100.0, "spindle_rpm": 2000},
        "options": {},
    }
    r = client.post("/api/cam/drilling/intent-gcode", json=body)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["gcode"]
    assert data["metadata"]["hole_count"] == 2
    bad = dict(body)
    bad["design"] = {**body["design"], "peck_depth_mm": 20.0}
    blocked = client.post("/api/cam/drilling/intent-gcode", json=bad)
    assert blocked.status_code == 409
    assert blocked.json()["detail"]["error"] == "FEASIBILITY_BLOCKED"


def test_drill_027_pattern_lane_not_repaired(client):
    payload = {
        "pat": {
            "type": "grid",
            "origin_x": 0.0,
            "origin_y": 0.0,
            "grid": {"cols": 2, "rows": 1, "dx": 10.0, "dy": 10.0},
        },
        "prm": {"z": -5.0, "feed": 100.0, "cycle": "G81", "safe_z": 5.0, "units": "mm"},
    }
    r = client.post("/api/cam/drilling/pattern/gcode", json=payload)
    assert r.status_code in (409, 422), r.text
    spec = spec_from_pattern(
        points_xy=[(0.0, 0.0), (10.0, 0.0)],
        z=-5.0, feed=100.0, cycle="G81", r_clear=None, peck_q=None,
        safe_z=5.0, units="mm", rpm=None, tool=None,
    )
    assert not spec.is_complete_for_feasibility()
    assert "missing_hole_diameter_mm" in spec.incomplete_reasons


@pytest.mark.parametrize("cid,disp", list(FROZEN_DISPOSITIONS.items()))
def test_drill_028_to_031_adjacent_dispositions(registry, cid, disp):
    assert _by_id(registry)[cid]["authority_disposition"] == disp
    if cid == "drilling":
        cap = _by_id(registry)[cid]
        assert cap["ungated_output_exposure"] == "YES"
        assert cap["input_contract_status"] == "MISMATCH"
        assert cap["authority_disposition"] != "GOVERNED"


# --- structural 032–035 ---


def test_drill_032_contract_has_no_rmos_import():
    tree = ast.parse(CONTRACT.read_text(encoding="utf-8"))
    mods = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            mods.append(node.module)
        if isinstance(node, ast.Import):
            mods.extend(a.name for a in node.names)
    assert not any("rmos" in m for m in mods)
    assert "rmos" not in CONTRACT.read_text(encoding="utf-8")


def test_drill_033_router_does_not_fabricate_evaluator_inputs():
    src = inspect.getsource(spec_from_modal)
    assert "abs(" not in src
    assert "hole_diameter" in src
    spec = spec_from_modal(
        holes=[(0.0, 0.0, -5.0, 100.0)],
        r_clear=2.0, peck_q=None, cycle="G81", safe_z=5.0,
        units="mm", rpm=None, tool=8,
    )
    assert spec.hole_diameter_mm is None
    assert spec.spindle_rpm is None
    assert spec.hole_depth_mm is None


def test_drill_034_no_client_authority_fields():
    from app.cam.routers.drilling.drill_modal_router import DrillReq
    names = set(DrillReq.model_fields)
    assert "risk_level" not in names
    assert "authority" not in names
    assert "feasible" not in names
    assert "hole_diameter_mm" in names
    assert "surface_z_mm" in names


def test_drill_035_scoring_rules_unchanged():
    src = inspect.getsource(compute_drilling_feasibility)
    assert "hole_diameter_mm must be > 0" in src
    assert "peck_depth_mm must be > 0 when peck_drilling is True" in src
    assert "must be < hole_depth_mm" in src
    assert "Deep hole: depth:diameter ratio" in src
    engine = ENGINE_ROUTER.read_text(encoding="utf-8")
    table = engine.split("_PRODUCTION_FEASIBILITY_ENGINES")[1].split("}", 1)[0]
    assert "drilling" not in table
    assert "RMOS-DRILLING-CONTRACT-001" in REGISTRY_PATH.read_text(encoding="utf-8")
