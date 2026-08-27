"""RMOS-PROFILING-CONVERGE-001 — production /gcode authority (PROF-001–024).

Isolated TestClient witnesses. Ephemeral RMOS stores. No machine hardware.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
REGISTRY_PATH = (
    REPO_ROOT / "services/api/app/rmos/manufacturing_authority_registry.json"
)

RECT = [
    {"x": 0.0, "y": 0.0},
    {"x": 80.0, "y": 0.0},
    {"x": 80.0, "y": 50.0},
    {"x": 0.0, "y": 50.0},
]


def _gcode(text: str) -> bool:
    return any(m in text for m in ("G21", "G90", "M30", "G0 Z", "G1 Z"))


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


def _request(**overrides):
    body = {"contour": RECT}
    body.update(overrides)
    return body


def test_prof_001_and_002_evaluator_fields_have_real_sources():
    from app.cam.routers.profiling.profile_router import (
        PROFILE_FEASIBILITY_SOURCES,
        ProfileRequest,
        feasibility_req_from_config,
        profile_config_from_request,
    )

    names = [row[0] for row in PROFILE_FEASIBILITY_SOURCES]
    assert names == [
        "tool_diameter_mm",
        "cut_depth_mm",
        "stepdown_mm",
        "feed_rate_mm_min",
        "plunge_rate_mm_min",
        "safe_z_mm",
        "retract_z_mm",
        "contour_point_count",
        "tab_count",
        "tab_height_mm",
        "use_tabs",
        "finishing_pass",
        "finishing_allowance_mm",
    ]
    units = {row[0]: row[2] for row in PROFILE_FEASIBILITY_SOURCES}
    assert units["tool_diameter_mm"] == "mm"
    assert units["feed_rate_mm_min"] == "mm/min"

    req = ProfileRequest(contour=[{"x": 0, "y": 0}, {"x": 10, "y": 0}, {"x": 10, "y": 10}])
    config = profile_config_from_request(req)
    payload = feasibility_req_from_config(
        config, contour_point_count=3, use_tabs=req.use_tabs
    )
    for name in names:
        assert payload[name] is not None, name


def test_prof_003_finishing_defaults_match_generator_runtime():
    from app.cam.profiling.profile_toolpath import ProfileConfig
    from app.cam.routers.profiling.profile_router import (
        ProfileRequest,
        feasibility_req_from_config,
        profile_config_from_request,
    )

    req = ProfileRequest(contour=[{"x": 0, "y": 0}, {"x": 10, "y": 0}, {"x": 10, "y": 10}])
    config = profile_config_from_request(req)
    payload = feasibility_req_from_config(config, contour_point_count=3, use_tabs=True)
    bare = ProfileConfig()
    assert payload["finishing_pass"] is True
    assert payload["finishing_pass"] == config.finishing_pass == bare.finishing_pass
    assert payload["finishing_allowance_mm"] == config.finishing_allowance_mm == bare.finishing_allowance_mm


def test_prof_004_005_016_017_valid_request_is_governed_gcode(client):
    from app.rmos.api.rmos_feasibility_router import resolve_feasibility_engine

    assert resolve_feasibility_engine("profiling") is not None
    r = client.post("/api/cam/profiling/gcode", json=_request())
    assert r.status_code == 200, r.text
    assert _gcode(r.text)
    assert r.headers.get("X-Run-ID")
    assert r.headers.get("X-GCode-SHA256")
    assert r.headers.get("X-ToolBox-Lane") == "governed"
    assert r.headers.get("X-Risk-Level") == "GREEN"


def test_prof_006_yellow_is_not_rewritten_green(client):
    # Two warnings (tiny tool + aggressive feed) → evaluator medium → YELLOW.
    r = client.post(
        "/api/cam/profiling/gcode",
        json=_request(tool_diameter_mm=0.8, feed_rate_mm_min=6000.0),
    )
    assert r.status_code == 200, r.text
    assert _gcode(r.text)
    assert r.headers.get("X-Risk-Level") == "YELLOW"


def test_prof_007_015_red_blocks_without_gcode(client):
    r = client.post(
        "/api/cam/profiling/gcode",
        json=_request(use_tabs=True, tab_height_mm=10.0, cut_depth_mm=6.0),
    )
    assert r.status_code == 409, r.text
    assert not _gcode(r.text)
    assert "X-GCode-SHA256" not in r.headers
    detail = r.json().get("detail") or {}
    assert detail.get("error") == "SAFETY_BLOCKED"
    assert (detail.get("decision") or {}).get("risk_level") == "RED"
    run_id = (detail.get("run_id") or r.headers.get("X-Run-ID"))
    assert run_id
    from app.rmos.runs_v2 import get_run

    artifact = get_run(run_id)
    assert artifact is not None
    assert artifact.status == "BLOCKED"
    assert artifact.decision.risk_level == "RED"
    assert artifact.hashes.gcode_sha256 is None


def test_prof_008_evaluator_error_fails_closed(client):
    from app.cam.profiling import feasibility as feas_mod

    def _boom(**kwargs):
        raise TypeError("forced evaluator failure")

    with patch.object(feas_mod, "compute_profile_feasibility", side_effect=_boom):
        r = client.post("/api/cam/profiling/gcode", json=_request())
    assert r.status_code == 409, r.text
    assert not _gcode(r.text)
    detail = r.json().get("detail") or {}
    assert (detail.get("decision") or {}).get("risk_level") == "ERROR"


def test_prof_009_unknown_blocks_when_engine_missing(client):
    from app.rmos.api import rmos_feasibility_router as fr

    with patch.dict(fr._PRODUCTION_FEASIBILITY_ENGINES, {}, clear=True):
        r = client.post("/api/cam/profiling/gcode", json=_request())
    assert r.status_code == 409, r.text
    assert not _gcode(r.text)
    detail = r.json().get("detail") or {}
    assert (detail.get("decision") or {}).get("risk_level") == "UNKNOWN"


def _first_call_lineno(func_node: ast.FunctionDef, name: str):
    for stmt in func_node.body:
        for node in ast.walk(stmt):
            func = getattr(node, "func", None)
            if isinstance(node, ast.Call) and isinstance(func, ast.Name) and func.id == name:
                return node.lineno
    return None


def _first_name_lineno(func_node: ast.FunctionDef, name: str):
    for stmt in func_node.body:
        for node in ast.walk(stmt):
            if isinstance(node, ast.Name) and node.id == name:
                return node.lineno
    return None


def test_prof_010_authority_structurally_precedes_generation():
    src_path = (
        REPO_ROOT / "services/api/app/cam/routers/profiling/profile_router.py"
    )
    source = src_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    auth_fn = next(
        n for n in tree.body
        if isinstance(n, ast.FunctionDef) and n.name == "_authorize_profiling"
    )
    auth_src = ast.get_source_segment(source, auth_fn) or ""
    assert "ProfileToolpath" not in auth_src
    assert ".generate(" not in auth_src

    handler = next(
        n for n in tree.body
        if isinstance(n, ast.FunctionDef) and n.name == "generate_profile_gcode"
    )
    auth_line = _first_call_lineno(handler, "_authorize_profiling")
    gen_line = _first_name_lineno(handler, "ProfileToolpath")
    assert auth_line is not None
    assert gen_line is not None
    assert auth_line < gen_line


def test_prof_011_blocked_path_does_not_call_generator(client):
    from app.cam.profiling.profile_toolpath import ProfileToolpath

    with patch.object(ProfileToolpath, "generate") as gen:
        r = client.post(
            "/api/cam/profiling/gcode",
            json=_request(use_tabs=True, tab_height_mm=10.0, cut_depth_mm=6.0),
        )
    assert r.status_code == 409, r.text
    gen.assert_not_called()


def test_prof_012_013_014_persisted_decision_matches_authority(client):
    from app.rmos.runs_v2 import get_run, sha256_of_text

    r = client.post("/api/cam/profiling/gcode", json=_request())
    assert r.status_code == 200, r.text
    run_id = r.headers["X-Run-ID"]
    artifact = get_run(run_id)
    assert artifact is not None
    assert artifact.decision.risk_level == r.headers["X-Risk-Level"]
    assert artifact.hashes.feasibility_sha256
    assert artifact.hashes.gcode_sha256 == r.headers["X-GCode-SHA256"]
    assert artifact.hashes.gcode_sha256 == sha256_of_text(r.text)
    assert artifact.hashes.feasibility_sha256 != sha256_of_text(r.text)
    assert artifact.hashes.feasibility_sha256 != sha256_of_text(
        json.dumps(_request(), sort_keys=True)
    )


def test_prof_018_020_malformed_and_binding(client):
    missing = client.post("/api/cam/profiling/gcode")
    assert missing.status_code == 422
    locs = [tuple(err.get("loc", ())) for err in missing.json()["detail"]]
    assert all(loc[:1] != ("query",) for loc in locs), locs
    assert any(loc[:1] == ("body",) for loc in locs), locs


def test_prof_019_client_cannot_inject_authority(client):
    r = client.post(
        "/api/cam/profiling/gcode",
        json=_request(
            risk_level="GREEN",
            decision={"risk_level": "GREEN"},
            feasibility={"risk_level": "GREEN"},
            export_allowed=True,
            use_tabs=True,
            tab_height_mm=10.0,
            cut_depth_mm=6.0,
        ),
    )
    assert r.status_code == 409, r.text
    assert not _gcode(r.text)


def test_prof_021_preview_untouched(client):
    # Known TabGenerator(contour=...) defect is out of scope. This increment
    # must neither repair preview nor start returning G-code from it.
    with pytest.raises(TypeError, match="unexpected keyword argument 'contour'"):
        client.post(
            "/api/cam/profiling/preview",
            json={"contour": RECT, "tab_count": 4},
        )


def test_prof_022_adaptive_still_governed(registry, client):
    cap = _by_id(registry)["adaptive"]
    assert cap["authority_disposition"] == "GOVERNED"


def test_prof_023_retract_still_blocked_by_design(registry, client):
    cap = _by_id(registry)["retract"]
    assert cap["authority_disposition"] == "BLOCKED_BY_DESIGN"
    r = client.post("/api/cam/retract/gcode")
    assert r.status_code == 409, r.text
    assert not _gcode(r.text)


def test_prof_024_only_profiling_disposition_changes(registry):
    cap = _by_id(registry)["profiling"]
    assert cap["authority_disposition"] == "GOVERNED"
    assert cap["reachability"] == "RUNTIME_REACHABLE"
    assert cap["ungated_output_exposure"] == "NO"
    assert _by_id(registry)["vcarve"]["authority_disposition"] == "POST_MERGE_AUTHORITY_EXPOSURE"
    assert _by_id(registry)["drilling"]["authority_disposition"] == "AUTHORITY_CONTRACT_MISMATCH"
    assert _by_id(registry)["rosette"]["authority_disposition"] == "GOVERNED"
    assert _by_id(registry)["rosette"]["reachability"] == "RUNTIME_BROKEN"
