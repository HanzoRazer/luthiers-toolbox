"""RMOS-AUTHORITY-MAP-001 Stage 2 — authority semantics (MAR-009–020).

Safe TestClient witnesses only: ephemeral RMOS dirs, side-effect-free compute
POSTs, GET of missing retrieval ids. No machine-control, no production DB,
no operator-file export, no planted durable state.

Presence of the registry grants no execution authority. These tests classify;
they do not remediate.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
REGISTRY_PATH = (
    REPO_ROOT / "services/api/app/rmos/manufacturing_authority_registry.json"
)

GCODE_MARKERS = ("G21", "G90", "M30", "G0 Z", "G1 Z")

SANE_ADAPTIVE = {
    "loops": [{"pts": [[0, 0], [100, 0], [100, 60], [0, 60]]}],
    "units": "mm",
    "tool_d": 6.0,
    "stepover": 0.45,
    "stepdown": 2.0,
    "margin": 0.5,
    "strategy": "Spiral",
    "smoothing": 0.5,
    "climb": True,
    "feed_xy": 1200.0,
    "safe_z": 5.0,
    "z_rough": -1.5,
}

RECT = [
    {"x": 0.0, "y": 0.0},
    {"x": 80.0, "y": 0.0},
    {"x": 80.0, "y": 50.0},
    {"x": 0.0, "y": 50.0},
]


def _by_id(registry):
    return {c["capability_id"]: c for c in registry["capabilities"]}


@pytest.fixture(scope="module")
def registry():
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


@pytest.fixture()
def client(tmp_path, monkeypatch):
    runs_dir = tmp_path / "rmos_runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    (runs_dir / "_index.json").write_text("{}", encoding="utf-8")
    monkeypatch.setenv("RMOS_RUNS_DIR", str(runs_dir))
    monkeypatch.setenv("RMOS_RUN_ATTACHMENTS_DIR", str(tmp_path / "att"))
    monkeypatch.setenv("RMOS_ARTIFACT_ROOT", str(tmp_path / "run_artifacts"))
    monkeypatch.setenv("ART_STUDIO_DB_PATH", str(tmp_path / "art.db"))
    monkeypatch.setenv("ENV", "test")
    try:
        from fastapi.testclient import TestClient
        from app.main import app
    except Exception as e:  # pragma: no cover
        pytest.skip(f"Could not import FastAPI app: {e}")
    return TestClient(app)


def _has_gcode(text: str) -> bool:
    return any(m in text for m in GCODE_MARKERS)


# ---------------------------------------------------------------------------
# MAR-009 / MAR-010 — GREEN persistence is not GOVERNED
# ---------------------------------------------------------------------------


def test_mar_009_green_persistence_is_not_governed(registry):
    by_id = _by_id(registry)
    for cid in ("polygon-offset", "rmos-wrap"):
        cap = by_id[cid]
        assert cap["persistence"]["status"] == "FALSE_PROVENANCE", cid
        assert cap["authority_disposition"] != "GOVERNED", cid
        assert cap["authority_disposition"] == "GOVERNED_PROVENANCE_DEFECT", cid


def test_mar_010_operator_pack_retrieval_is_not_governed(registry):
    cap = _by_id(registry)["operator-pack"]
    assert cap["surface_kind"] == "artifact_retrieval"
    assert cap["authority_disposition"] != "GOVERNED"
    assert cap["ungated_output_exposure"] == "RETRIEVAL_ONLY"


# ---------------------------------------------------------------------------
# MAR-011 / MAR-016 — drilling contract mismatch preserved
# ---------------------------------------------------------------------------


def test_mar_011_and_016_drilling_modal_cannot_feed_evaluator(registry, client):
    cap = _by_id(registry)["drilling"]
    assert cap["authority_disposition"] == "AUTHORITY_CONTRACT_MISMATCH"
    assert cap["input_contract_status"] == "MISMATCH"
    assert cap["authority"]["status"] == "MISMATCH"
    note = " ".join(e.get("note", "") for e in cap["evidence"])
    assert "hole_diameter_mm" in note
    assert "DrillReq" in note or "drill_modal" in note.lower() or "Modal" in note or "modal" in note

    r = client.post(
        "/api/cam/drilling/gcode",
        json={
            "holes": [{"x": 10, "y": 10, "z": -5, "feed": 500}],
            "cycle": "G83",
            "peck_q": 2.0,
            "safe_z": 5.0,
            "units": "mm",
        },
    )
    assert r.status_code == 200, r.text
    assert _has_gcode(r.text)
    assert cap["ungated_output_exposure"] == "YES"


# ---------------------------------------------------------------------------
# MAR-012 — 422/500 is not LIVE_UNGOVERNED_OUTPUT
# ---------------------------------------------------------------------------


def test_mar_012_validation_error_is_not_live_ungoverned(registry, client):
    missing = client.post("/api/cam/profiling/gcode")
    assert missing.status_code == 422
    cap = _by_id(registry)["profiling"]
    # 422 on an empty body is still not a reachability class. After
    # RMOS-PROFILING-CONVERGE-001 the 200 path is GOVERNED; the 422
    # binding behaviour from #324 is unchanged.
    assert cap["authority_disposition"] == "GOVERNED"
    # Classification rests on the 200 emission path, not the 422.
    ok = client.post("/api/cam/profiling/gcode", json={"contour": RECT})
    assert ok.status_code == 200, ok.text
    assert _has_gcode(ok.text)


# ---------------------------------------------------------------------------
# MAR-013 / MAR-014 / MAR-019 — policy 409 is not RUNTIME_BROKEN
# ---------------------------------------------------------------------------


def test_mar_013_and_014_retract_fail_closed(registry, client):
    cap = _by_id(registry)["retract"]
    assert cap["authority_disposition"] == "BLOCKED_BY_DESIGN"
    assert cap["reachability"] == "RUNTIME_BLOCKED_BY_POLICY"
    assert cap["reachability"] != "RUNTIME_BROKEN"
    assert cap["authority"]["evaluator"] is None

    simple = client.post("/api/cam/retract/gcode")
    download = client.post(
        "/api/cam/retract/gcode/download",
        json={"strategy": "direct", "features": []},
    )
    assert simple.status_code == 409, simple.text
    assert download.status_code == 409, download.text
    for resp in (simple, download):
        assert not _has_gcode(resp.text)
        assert "X-GCode-SHA256" not in resp.headers


def test_mar_019_roughing_and_helical_blocked_by_design(registry, client):
    for cid, path, payload in (
        (
            "roughing",
            "/api/cam/toolpath/roughing/gcode",
            {
                "width": 80.0,
                "height": 50.0,
                "stepdown": 2.0,
                "stepover": 0.4,
                "feed": 1200.0,
                "safe_z": 5.0,
            },
        ),
        (
            "helical",
            "/api/cam/toolpath/helical_entry",
            {
                "cx": 0.0,
                "cy": 0.0,
                "radius_mm": 6.0,
                "z_target_mm": -3.0,
                "pitch_mm_per_rev": 1.5,
            },
        ),
        (
            "biarc-contour",
            "/api/cam/toolpath/biarc/gcode",
            {
                "path": [{"x": 0, "y": 0}, {"x": 40, "y": 0}, {"x": 40, "y": 20}],
                "z": -2.0,
                "feed": 800.0,
            },
        ),
    ):
        cap = _by_id(registry)[cid]
        assert cap["authority_disposition"] == "BLOCKED_BY_DESIGN", cid
        assert cap["reachability"] != "RUNTIME_BROKEN", cid
        r = client.post(path, json=payload)
        assert r.status_code == 409, (cid, r.status_code, r.text[:500])
        assert not _has_gcode(r.text), cid


# ---------------------------------------------------------------------------
# MAR-015 — adaptive governed
# ---------------------------------------------------------------------------


def test_mar_015_adaptive_authority_and_truthful_persistence(registry, client):
    cap = _by_id(registry)["adaptive"]
    assert cap["authority_disposition"] == "GOVERNED"
    assert cap["authority"]["status"] == "NAMED"
    assert cap["authority"]["evaluator"]
    assert "compute_adaptive_feasibility" in cap["authority"]["evaluator"]
    assert cap["persistence"]["status"] == "RUN_ARTIFACT"
    assert cap["persistence"]["status"] != "FALSE_PROVENANCE"

    ok = client.post("/api/cam/pocket/adaptive/gcode", json=SANE_ADAPTIVE)
    assert ok.status_code == 200, ok.text
    assert ok.headers.get("X-Run-ID")
    assert ok.headers.get("X-GCode-SHA256")

    blocked = dict(SANE_ADAPTIVE)
    blocked["z_rough"] = 1.5
    bad = client.post("/api/cam/pocket/adaptive/gcode", json=blocked)
    assert bad.status_code == 409, bad.text
    assert not _has_gcode(bad.text)


# ---------------------------------------------------------------------------
# MAR-017 — profiling post-#324
# ---------------------------------------------------------------------------


def test_mar_017_profiling_post_324_emits_without_rmos(registry, client):
    # RMOS-PROFILING-CONVERGE-001: sibling /gcode is now GOVERNED. Binding
    # from #324 is preserved (200 + G-code); authority is no longer absent.
    cap = _by_id(registry)["profiling"]
    assert cap["authority_disposition"] == "GOVERNED"
    assert cap["ungated_output_exposure"] == "NO"
    assert cap["authority_disposition"] != "POST_MERGE_AUTHORITY_EXPOSURE"
    r = client.post("/api/cam/profiling/gcode", json={"contour": RECT})
    assert r.status_code == 200, r.text
    assert _has_gcode(r.text)
    assert r.headers.get("X-Run-ID")


# ---------------------------------------------------------------------------
# MAR-018 — vcarve post-merge exposure
# ---------------------------------------------------------------------------


def test_mar_018_vcarve_production_reachable_without_rmos(registry, client):
    cap = _by_id(registry)["vcarve"]
    assert cap["authority_disposition"] == "POST_MERGE_AUTHORITY_EXPOSURE"

    prod = client.post(
        "/api/cam/vcarve/production/gcode",
        json={
            "paths": [
                {
                    "points": [{"x": 0, "y": 0}, {"x": 20, "y": 0}, {"x": 20, "y": 10}],
                    "is_closed": False,
                }
            ],
            "bit_angle_deg": 60.0,
            "target_line_width_mm": 2.0,
        },
    )
    assert prod.status_code == 200, prod.text
    assert _has_gcode(prod.text)

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


# ---------------------------------------------------------------------------
# MAR-020 — rosette real evaluator, not historical fail-open
# ---------------------------------------------------------------------------


def test_mar_020_rosette_evaluator_is_named(registry):
    cap = _by_id(registry)["rosette"]
    assert cap["authority"]["status"] == "NAMED"
    assert "compute_rosette_feasibility" in (cap["authority"]["evaluator"] or "")
    assert cap["authority_disposition"] == "GOVERNED"
    # GOVERNED != FUNCTIONAL != AVAILABLE: generation is currently broken.
    assert cap["reachability"] == "RUNTIME_BROKEN"


def test_mar_020_cam_stub_is_retired_for_named_modes():
    from app.rmos.api.rmos_feasibility_router import resolve_feasibility_engine

    assert resolve_feasibility_engine("rosette") is not None
    assert resolve_feasibility_engine("profiling") is not None
    assert resolve_feasibility_engine("vcarve") is None
    assert resolve_feasibility_engine("roughing") is None


def test_mar_020_rosette_plan_does_not_fail_open(client):
    r = client.post(
        "/api/cam/rosette/plan-toolpath",
        json={
            "inner_radius": 10.0,
            "outer_radius": 40.0,
            "tool_d": 3.0,
            "cut_depth": 2.0,
            "feed_xy": 800.0,
        },
    )
    # Frozen before-state: evaluator ran; generation then 400. No G-code leaked.
    assert r.status_code == 400, r.text
    assert not _has_gcode(r.text)
    detail = r.json().get("detail") or {}
    assert detail.get("error") == "TOOLPATH_PLAN_ERROR"


# ---------------------------------------------------------------------------
# Binding / feeds-speeds / polygon-offset / retrieval witnesses
# ---------------------------------------------------------------------------


def test_binding_channel_emits_ungated_gcode(registry, client):
    cap = _by_id(registry)["binding"]
    assert cap["authority_disposition"] == "LIVE_UNGOVERNED_OUTPUT"
    r = client.post(
        "/api/cam/binding/channel/gcode",
        json={"body_outline": RECT},
    )
    assert r.status_code == 200, r.text
    assert _has_gcode(r.text)


def test_feeds_speeds_is_advisory_json(registry, client):
    cap = _by_id(registry)["feeds-speeds"]
    assert cap["surface_kind"] == "advisory"
    assert cap["authority_disposition"] == "ADVISORY_ONLY"
    r = client.post(
        "/api/cam/opt/feeds-speeds",
        json={"tool_id": "endmill_6mm", "material": "hardwood", "strategy": "roughing"},
    )
    assert r.status_code == 200, r.text
    assert not _has_gcode(r.text)
    data = r.json()
    assert "feed_xy" in data or "rpm" in data or "notes" in data


def test_polygon_offset_governed_mints_green_without_evaluator(registry, client):
    cap = _by_id(registry)["polygon-offset"]
    assert cap["authority_disposition"] == "GOVERNED_PROVENANCE_DEFECT"
    r = client.post(
        "/api/cam/polygon_offset_governed.nc",
        json={
            "polygon": [[0, 0], [60, 0], [60, 40], [0, 40], [0, 0]],
            "tool_dia": 6.0,
            "stepover": 0.4,
        },
    )
    if r.status_code == 500 and "pyclipper" in r.text.lower():
        pytest.skip("pyclipper not installed")
    assert r.status_code == 200, r.text
    assert r.headers.get("X-ToolBox-Lane") == "governed"
    assert r.headers.get("X-Run-ID")


def test_operator_pack_and_saw_batch_are_retrieval_not_generators(registry, client):
    op = _by_id(registry)["operator-pack"]
    saw = _by_id(registry)["saw-batch"]
    assert op["surface_kind"] == "artifact_retrieval"
    assert saw["surface_kind"] == "artifact_retrieval"
    assert op["authority_disposition"] != "GOVERNED"

    missing_pack = client.get("/api/rmos/runs_v2/does-not-exist/operator-pack")
    assert missing_pack.status_code in {404, 409, 422}

    missing_saw = client.get(
        "/api/saw/batch/op-toolpaths/does-not-exist/gcode"
    )
    assert missing_saw.status_code in {404, 409, 422}
    assert not _has_gcode(missing_saw.text)


def test_post_wrap_v1_remain_separate(registry):
    by_id = _by_id(registry)
    assert by_id["cam-post"]["capability_id"] != by_id["rmos-wrap"]["capability_id"]
    assert by_id["v1-dxf"]["authority_disposition"] == "EXPLICITLY_NON_PRODUCTION"
    assert by_id["cam-post"]["authority_disposition"] == "LIVE_UNGOVERNED_OUTPUT"
    assert by_id["rmos-wrap"]["authority_disposition"] == "GOVERNED_PROVENANCE_DEFECT"
