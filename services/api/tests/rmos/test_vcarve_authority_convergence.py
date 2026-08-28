"""RMOS-VCARVE-CONVERGE-001 — HOLD: no authorized V-carve feasibility path.

This module proves the authority gap. It does not gate production G-code.
Gating without a truthful evaluator would turn valid 200 jobs into 409
UNKNOWN, which D3 forbids without an owner availability ruling.

Isolated TestClient witnesses. Ephemeral RMOS stores. No machine hardware.
"""
from __future__ import annotations

import ast
import inspect
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
REGISTRY_PATH = (
    REPO_ROOT / "services/api/app/rmos/manufacturing_authority_registry.json"
)
PRODUCTION_ROUTER = (
    REPO_ROOT / "services/api/app/cam/routers/vcarve/production_router.py"
)
VCARVE_PKG = REPO_ROOT / "services/api/app/cam/vcarve"
ENGINE_ROUTER = (
    REPO_ROOT / "services/api/app/rmos/api/rmos_feasibility_router.py"
)

GCODE_MARKERS = ("G21", "G90", "M30", "G0 Z", "G1 Z")

VALID_BODY = {
    "paths": [
        {
            "points": [{"x": 0, "y": 0}, {"x": 20, "y": 0}, {"x": 20, "y": 10}],
            "is_closed": False,
        }
    ],
    "bit_angle_deg": 60.0,
    "target_line_width_mm": 2.0,
}

# Adjacent evaluators D1 forbids reusing by analogy.
ADJACENT_EVALUATOR_NAMES = (
    "compute_profile_feasibility",
    "compute_profiling_feasibility",
    "compute_drilling_feasibility",
    "compute_pocket_feasibility",
    "compute_adaptive_feasibility",
    "compute_feasibility_internal",
)

# PR #328 / #329 frozen dispositions. Asserted in-process so CI shallow
# checkouts do not need origin/main.
FROZEN_DISPOSITIONS = {
    "vcarve": "POST_MERGE_AUTHORITY_EXPOSURE",
    "profiling": "GOVERNED",
    "retract": "BLOCKED_BY_DESIGN",
    "adaptive": "GOVERNED",
    "drilling": "AUTHORITY_CONTRACT_MISMATCH",
}

HOLD_MARK = "RMOS-VCARVE-CONVERGE-001 HOLD"

AUTHORITY_CONTRACT = "NOT SATISFIABLE"

# Mandatory checkpoint matrix: there is no V-carve evaluator, so there are
# no evaluator inputs that a production request could truthfully satisfy.
EVALUATOR_INPUT_MATRIX: tuple[tuple[str, str, str, str], ...] = ()


def _by_id(registry):
    return {c["capability_id"]: c for c in registry["capabilities"]}


def _has_gcode(text: str) -> bool:
    return any(m in text for m in GCODE_MARKERS)


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


def _production_fn() -> tuple[str, ast.FunctionDef]:
    src = PRODUCTION_ROUTER.read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "generate_production_vcarve_gcode":
            return src, node
    raise AssertionError("generate_production_vcarve_gcode not found")


def _called_names(fn: ast.FunctionDef) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(fn):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                names.add(node.func.attr)
    return names


# ---------------------------------------------------------------------------
# Contract discovery (VCARVE-001–004)
# ---------------------------------------------------------------------------


def test_vcarve_001_production_route_reachable(client):
    r = client.post("/api/cam/vcarve/production/gcode", json=VALID_BODY)
    assert r.status_code == 200, r.text
    assert _has_gcode(r.text)
    assert "text/plain" in (r.headers.get("content-type") or "")


def test_vcarve_002_evaluator_identity_is_none():
    from app.rmos.api.rmos_feasibility_router import (
        _PRODUCTION_FEASIBILITY_ENGINES,
        resolve_feasibility_engine,
        resolve_mode,
    )

    assert resolve_mode("vcarve:default") == "vcarve"
    assert resolve_feasibility_engine("vcarve") is None
    assert "vcarve" not in _PRODUCTION_FEASIBILITY_ENGINES
    assert set(_PRODUCTION_FEASIBILITY_ENGINES) == {
        "saw",
        "rosette",
        "adaptive",
        "profiling",
    }
    assert not (VCARVE_PKG / "feasibility.py").is_file()
    named = list(VCARVE_PKG.glob("*feasib*"))
    assert named == [], named
    engine_src = ENGINE_ROUTER.read_text(encoding="utf-8")
    assert "compute_vcarve" not in engine_src


def test_vcarve_003_authority_contract_not_satisfiable():
    assert AUTHORITY_CONTRACT == "NOT SATISFIABLE"
    assert EVALUATOR_INPUT_MATRIX == ()
    # Adjacent CAM feasibility modules exist but are not V-carve-capable (D1).
    for name in (
        "services/api/app/cam/profiling/feasibility.py",
        "services/api/app/cam/drilling/feasibility.py",
        "services/api/app/cam/pocketing/feasibility.py",
        "services/api/app/rmos/feasibility/engine.py",
    ):
        assert (REPO_ROOT / name).is_file(), name
    prod = PRODUCTION_ROUTER.read_text(encoding="utf-8")
    for name in ADJACENT_EVALUATOR_NAMES:
        assert name not in prod, name


def test_vcarve_004_units_not_mapped_because_no_evaluator():
    from app.cam.routers.vcarve.production_router import VCarveProductionRequest
    from app.cam.vcarve.toolpath import VCarveConfig
    from app.rmos.feasibility.schemas import FeasibilityInput

    req_fields = set(VCarveProductionRequest.model_fields)
    cfg_fields = set(VCarveConfig.__dataclass_fields__)
    # Production request units that a V-carve evaluator would have to consume.
    vcarve_units = {
        "bit_angle_deg": "deg",
        "tip_diameter_mm": "mm",
        "target_line_width_mm": "mm",
        "target_depth_mm": "mm",
        "safe_z_mm": "mm",
        "retract_z_mm": "mm",
        "feed_rate_mm_min": "mm/min",
        "plunge_rate_mm_min": "mm/min",
        "max_stepdown_mm": "mm",
        "spindle_rpm": "rpm",
    }
    for field_name in vcarve_units:
        assert field_name in req_fields
        assert field_name in cfg_fields
    # Flat-end-mill FeasibilityInput cannot consume V-bit angle semantics.
    fi_fields = set(FeasibilityInput.model_fields)
    assert "bit_angle_deg" not in fi_fields
    assert "tip_diameter_mm" not in fi_fields
    assert "target_line_width_mm" not in fi_fields
    assert "tool_d" in fi_fields  # endmill diameter — not a V-bit included angle


# ---------------------------------------------------------------------------
# Authority (VCARVE-005–009) — HOLD: do not invent a gate
# ---------------------------------------------------------------------------


def test_vcarve_005_016_valid_request_remains_available(client):
    """D3: HOLD preserves the existing 200. Do not newly darken valid jobs."""
    r = client.post("/api/cam/vcarve/production/gcode", json=VALID_BODY)
    assert r.status_code == 200, r.text
    assert _has_gcode(r.text)
    assert not r.headers.get("X-Run-ID")
    assert not r.headers.get("X-Risk-Level")


def test_vcarve_006_007_008_hold_does_not_silently_409(client):
    """No evaluator means no RED/UNKNOWN/ERROR gate on the production route.

    Wiring unavailable_feasibility here would 409 every valid job. HOLD
    forbids that availability change. Intent-gcode already fail-closes.
    """
    prod = client.post("/api/cam/vcarve/production/gcode", json=VALID_BODY)
    assert prod.status_code == 200, prod.text
    intent = client.post(
        "/api/cam/vcarve/intent-gcode",
        json={
            "mode": "router_3axis",
            "units": "mm",
            "design": {
                "paths": [
                    {
                        "points": [{"x": 0, "y": 0}, {"x": 10, "y": 0}],
                        "is_closed": False,
                    }
                ],
                "bit_angle_deg": 60.0,
                "target_line_width_mm": 2.0,
            },
            "context": {"spindle_rpm": 18000, "material": "hardwood"},
            "options": {},
        },
    )
    assert intent.status_code == 409, intent.text
    assert not _has_gcode(intent.text)


def test_vcarve_009_client_cannot_assert_authority(client):
    body = dict(VALID_BODY)
    body.update(
        {
            "risk_level": "GREEN",
            "decision": "ALLOW",
            "feasibility": {"risk_level": "GREEN"},
            "export_allowed": True,
        }
    )
    r = client.post("/api/cam/vcarve/production/gcode", json=body)
    # Ignore (200, extra dropped) or reject (422) — never treat as authority.
    assert r.status_code in (200, 422), r.text
    if r.status_code == 200:
        assert _has_gcode(r.text)
        assert not r.headers.get("X-Risk-Level")
        assert not r.headers.get("X-Run-ID")


# ---------------------------------------------------------------------------
# Ordering (VCARVE-010–011)
# ---------------------------------------------------------------------------


def test_vcarve_010_generation_is_not_preceded_by_authority():
    src, fn = _production_fn()
    names = _called_names(fn)
    assert "generate" in names
    assert "SafetyPolicy" not in names
    assert "should_block" not in names
    assert "validate_and_persist" not in names
    assert "compute_feasibility_internal" not in names
    assert "RunDecision" not in names
    fn_src = ast.get_source_segment(src, fn)
    assert fn_src is not None
    gen_at = fn_src.find(".generate(")
    assert gen_at != -1
    before = fn_src[:gen_at]
    assert "SafetyPolicy" not in before
    assert "compute_feasibility_internal" not in before


def test_vcarve_011_no_blocked_production_path_exists():
    """HOLD: there is no authorized block path on production, so none can generate."""
    _src, fn = _production_fn()
    names = _called_names(fn)
    assert "HTTPException" in names  # empty-path validation only
    raises = [
        node for node in ast.walk(fn) if isinstance(node, ast.Raise)
    ]
    status_codes = []
    for node in raises:
        call = node.exc if isinstance(node.exc, ast.Call) else None
        if call is None:
            continue
        for kw in call.keywords:
            if kw.arg == "status_code" and isinstance(kw.value, ast.Constant):
                status_codes.append(kw.value.value)
    assert 400 in status_codes
    assert 409 not in status_codes


# ---------------------------------------------------------------------------
# Persistence (VCARVE-012–015)
# ---------------------------------------------------------------------------


def test_vcarve_012_to_015_production_does_not_mint_or_persist_authority():
    src = PRODUCTION_ROUTER.read_text(encoding="utf-8")
    assert "RunDecision" not in src
    assert 'risk_level="GREEN"' not in src
    assert "risk_level='GREEN'" not in src
    assert "validate_and_persist" not in src
    assert "RunArtifact" not in src
    _src, fn = _production_fn()
    assert "validate_and_persist" not in _called_names(fn)


# ---------------------------------------------------------------------------
# Runtime (VCARVE-016–018) — 016 covered with 005
# ---------------------------------------------------------------------------


def test_vcarve_017_malformed_input_remains_422(client):
    r = client.post("/api/cam/vcarve/production/gcode", json={})
    assert r.status_code == 422, r.text
    locs = [tuple(err.get("loc", ())) for err in r.json()["detail"]]
    assert any(loc[:1] == ("body",) for loc in locs), locs
    assert all(loc[:1] != ("query",) for loc in locs), locs


def test_vcarve_018_binding_behavior_preserved():
    from app.cam.routers.vcarve.production_router import (
        VCarveProductionRequest,
        generate_production_vcarve_gcode,
    )

    annotation = inspect.signature(generate_production_vcarve_gcode).parameters["req"].annotation
    assert annotation is VCarveProductionRequest
    assert not isinstance(annotation, str)


def test_vcarve_d7_no_in_repo_production_consumer():
    client_root = REPO_ROOT / "packages" / "client"
    hits = []
    for path in client_root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".ts", ".vue", ".js", ".tsx"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if "vcarve/production/gcode" in text:
            hits.append(str(path.relative_to(REPO_ROOT)))
    assert hits == [], hits


# ---------------------------------------------------------------------------
# Registry (VCARVE-019–020)
# ---------------------------------------------------------------------------


def test_vcarve_019_frozen_before_state_preserved(registry):
    cap = _by_id(registry)["vcarve"]
    assert cap["authority_disposition"] == FROZEN_DISPOSITIONS["vcarve"]
    assert cap["reachability"] == "RUNTIME_REACHABLE"
    assert cap["ungated_output_exposure"] == "YES"
    assert cap["generation_ordering"] == "MIXED"
    assert cap["authority"]["evaluator"] is None
    assert cap["authority"]["status"] == "NONE"
    notes = " ".join(e.get("note") or "" for e in cap["evidence"])
    assert HOLD_MARK in cap["intent_contract"]
    assert "NOT SATISFIABLE" in cap["intent_contract"] or "NOT SATISFIABLE" in notes
    assert any("HOLD" in (e.get("note") or "") for e in cap["evidence"])
    # HOLD appends evidence; it must not rewrite the #328 classification.
    assert cap["authority_disposition"] != "GOVERNED"


def test_vcarve_020_only_vcarve_registry_record_changes(registry):
    by_id = _by_id(registry)
    hold_caps = [
        cid
        for cid, rec in by_id.items()
        if HOLD_MARK in json.dumps(rec)
    ]
    assert hold_caps == ["vcarve"], hold_caps
    cap = by_id["vcarve"]
    assert cap["authority_disposition"] != "GOVERNED"
    assert cap["ungated_output_exposure"] == "YES"


# ---------------------------------------------------------------------------
# Cross-capability regression (VCARVE-021–024)
# ---------------------------------------------------------------------------


def test_vcarve_021_to_024_other_capabilities_untouched(registry, client):
    by_id = _by_id(registry)
    for cid, disp in FROZEN_DISPOSITIONS.items():
        assert by_id[cid]["authority_disposition"] == disp, cid
    assert by_id["profiling"]["reachability"] == "RUNTIME_REACHABLE"

    production_src = PRODUCTION_ROUTER.read_text(encoding="utf-8")
    profiling_router = (
        REPO_ROOT / "services/api/app/cam/routers/profiling/profile_router.py"
    ).read_text(encoding="utf-8")
    assert HOLD_MARK not in production_src
    assert HOLD_MARK not in profiling_router
    from app.rmos.api.rmos_feasibility_router import resolve_feasibility_engine

    assert resolve_feasibility_engine("vcarve") is None

    retract = client.post("/api/cam/retract/gcode")
    assert retract.status_code == 409, retract.text
    assert not _has_gcode(retract.text)
