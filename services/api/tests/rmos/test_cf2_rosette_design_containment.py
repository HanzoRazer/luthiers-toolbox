"""Contain the Rosette multi-ring `/design` manufacturing emitter. Not a qualification.

CF2-ROSETTE-DESIGN-CONTAINMENT-003R (Phase B).

`/design` resolves the shared manufacturing-output authority exactly once for the
complete design, outside and before the ring loop and all generation side
effects. A blocking decision returns HTTP 409 with no ring output and one BLOCKED
artifact; a permitted decision generates every ring, persists the single
`combined_gcode` once, and stamps governed headers.

Pattern disposition (documented, not hidden): `pattern` affects the emitted
program only via tile-count parity (alternating patterns force an even tile
count), so different patterns can produce different G-code. The manufacturing-
output evaluator does NOT currently consume `pattern_type` for its risk decision
(authority is based on geometry, ring count, material, and RPM). The summary
carries a truthful `pattern_type` (uniform value or `"mixed"`) plus a
`pattern_types` diagnostic; closing evaluator pattern-awareness is future work.
"""

from __future__ import annotations

import ast
import hashlib
import inspect
import json
from pathlib import Path

import pytest

from app.rmos import rosette_cam_router as rcr
from app.rmos.rosette_output_authority import _rosette_design_feasibility_summary as design_summary

pytestmark = pytest.mark.allow_missing_request_id

DESIGN_PATH = "/api/rmos/rosette/design"
EXPORT_PATH = "/api/rmos/rosette/export-cnc"
DESIGN_TOOL_ID = "rosette:design"

GENERATOR_NAMES = (
    "compute_tile_segmentation",
    "generate_slices_for_ring",
    "build_ring_cnc_export",
    "generate_gcode_from_toolpaths",
)

# Two-ring design; both rings default checkerboard unless overridden.
VALID_BODY = {
    "soundhole_diameter_mm": 85.0,
    "rings": [
        {"width_mm": 5.0, "pattern": "checkerboard"},
        {"width_mm": 6.0, "pattern": "checkerboard"},
    ],
}
MIXED_BODY = {
    "soundhole_diameter_mm": 85.0,
    "rings": [
        {"width_mm": 5.0, "pattern": "checkerboard"},
        {"width_mm": 6.0, "pattern": "radial"},
    ],
}

INVENTORY_PATH = (
    Path(__file__).resolve().parents[2] / "governance" / "manufacturing_output_inventory.json"
)


class _MemoryStore:
    def __init__(self) -> None:
        self.saved: list = []

    def put(self, artifact):
        self.saved.append(artifact)
        return artifact


@pytest.fixture
def memory_store(monkeypatch):
    store = _MemoryStore()
    monkeypatch.setattr("app.rmos.runs_v2.store._get_default_store", lambda: store)
    return store


def _force_decision(monkeypatch, risk):
    import app.rmos.manufacturing_output_authority as moa

    real = moa.compute_feasibility_internal

    def forced(*, tool_id, req, context=None):
        if tool_id == DESIGN_TOOL_ID:
            # An evaluator ERROR is a feasibility RESULT with risk_level "ERROR"
            # (error_feasibility), not a raised exception; RED/UNKNOWN/ERROR all block.
            return {
                "tool_id": tool_id,
                "risk_level": risk,
                "warnings": ["cf2-design-test-only"],
                "score": 0,
                "block_reason": f"forced {risk} (test only)",
            }
        return real(tool_id=tool_id, req=req, context=context)

    monkeypatch.setattr(
        "app.rmos.manufacturing_output_authority.compute_feasibility_internal", forced
    )


def _count_generators(monkeypatch) -> dict:
    counts = {n: 0 for n in GENERATOR_NAMES}
    for name in GENERATOR_NAMES:
        real = getattr(rcr, name)

        def make(real_fn, key):
            def wrapped(*a, **k):
                counts[key] += 1
                return real_fn(*a, **k)

            return wrapped

        monkeypatch.setattr(rcr, name, make(real, name))
    return counts


def _forbid_generators(monkeypatch) -> None:
    for name in GENERATOR_NAMES:
        def make(gen):
            def forbidden(*a, **k):
                raise AssertionError(f"{gen} reached on blocked path")

            return forbidden

        monkeypatch.setattr(rcr, name, make(name))


def _count_authority(monkeypatch) -> dict:
    import app.rmos.manufacturing_output_authority as moa

    real = moa.compute_feasibility_internal
    n = {"calls": 0}

    def wrapped(*, tool_id, req, context=None):
        if tool_id == DESIGN_TOOL_ID:
            n["calls"] += 1
        return real(tool_id=tool_id, req=req, context=context)

    monkeypatch.setattr(
        "app.rmos.manufacturing_output_authority.compute_feasibility_internal", wrapped
    )
    return n


# ---- Summary and validation (RDS-01..10) ----

@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"rings": []},
        {"rings": None},
        {"rings": "not-a-list"},
        {"rings": [None]},
    ],
)
def test_rds01_empty_or_invalid_design_is_artifact_free(
    client, memory_store, monkeypatch, payload
):
    def forbidden(*args, **kwargs):
        raise AssertionError("authority or persistence reached on empty/invalid design")

    monkeypatch.setattr(rcr, "require_manufacturing_output_authority", forbidden)
    monkeypatch.setattr(rcr, "persist_authorized_manufacturing_output", forbidden)

    r = client.post(DESIGN_PATH, json=payload)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is False and body["combined_gcode"] is None
    assert memory_store.saved == []
    assert r.headers.get("X-Run-ID") is None


def test_rds02_summary_authorized_fields_only():
    rings = rcr._design_rings_from_payload(VALID_BODY)
    s = design_summary(rings, VALID_BODY)
    assert set(s) == {
        "outer_diameter_mm", "inner_diameter_mm", "ring_count",
        "material_id", "rpm", "pattern_type", "pattern_types",
    }


def test_rds03_ring_count_complete_design():
    rings = rcr._design_rings_from_payload(VALID_BODY)
    assert design_summary(rings, VALID_BODY)["ring_count"] == 2


def test_rds04_05_outer_inner_from_complete_design():
    rings = rcr._design_rings_from_payload(VALID_BODY)
    s = design_summary(rings, VALID_BODY)
    outers = [2 * (r["radius_mm"] + r["width_mm"] / 2) for r in rings]
    inners = [2 * (r["radius_mm"] - r["width_mm"] / 2) for r in rings]
    assert s["outer_diameter_mm"] == pytest.approx(max(outers))  # outermost, not ring 1
    assert s["inner_diameter_mm"] == pytest.approx(min(inners))  # innermost
    assert s["outer_diameter_mm"] > outers[0]  # ring 1 alone would understate it


def test_rds06_material_rpm_match_generation():
    rings = rcr._design_rings_from_payload({**VALID_BODY, "material": "Softwood", "spindle_rpm": 15000})
    s = design_summary(rings, {**VALID_BODY, "material": "Softwood", "spindle_rpm": 15000})
    assert s["material_id"] == "softwood"
    assert s["rpm"] == 15000


def test_rds07_no_invented_fields():
    rings = rcr._design_rings_from_payload(VALID_BODY)
    s = design_summary(rings, VALID_BODY)
    for absent in ("depth_mm", "tool_diameter_mm", "feed_rate_mm_min", "petal_count", "stock_thickness_mm"):
        assert absent not in s


def test_rds08_invalid_geometry_fails_before_authority(client, memory_store):
    # width larger than diameter -> inner radius <= 0
    with pytest.raises(ValueError):
        design_summary([{"ring_id": 0, "radius_mm": 2.0, "width_mm": 10.0, "pattern": "checkerboard"}], {})
    # explicit per-ring radius smaller than half-width -> inner radius <= 0
    r = client.post(DESIGN_PATH, json={"rings": [{"radius_mm": 2.0, "width_mm": 10.0}]})
    assert r.status_code == 200, r.text
    assert r.json()["ok"] is False
    assert memory_store.saved == []  # never reached authority


def test_rds09_uniform_pattern_truthful():
    rings = rcr._design_rings_from_payload(VALID_BODY)
    s = design_summary(rings, VALID_BODY)
    assert s["pattern_type"] == "checkerboard"
    assert s["pattern_types"] == ["checkerboard"]


def test_rds10_mixed_pattern_truthful_no_stop():
    rings = rcr._design_rings_from_payload(MIXED_BODY)
    s = design_summary(rings, MIXED_BODY)
    assert s["pattern_type"] == "mixed"
    assert s["pattern_types"] == ["checkerboard", "radial"]


# ---- Ordering and cardinality (RDS-11..14) ----

_AUTHORITY = "require_manufacturing_output_authority"


def _design_src():
    return inspect.getsource(rcr.design_rosette)


def _call_label(node: ast.Call) -> str:
    return getattr(node.func, "id", getattr(node.func, "attr", ""))


def _design_fn(src: str) -> ast.FunctionDef:
    tree = ast.parse(src.lstrip())
    return next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "design_rosette")


def _call_linenos(node: ast.AST, label: str) -> list:
    return [n.lineno for n in ast.walk(node) if isinstance(n, ast.Call) and _call_label(n) == label]


def _authority_inside_any_loop(fn: ast.FunctionDef) -> bool:
    loops = [n for n in ast.walk(fn) if isinstance(n, ast.For)]
    return any(_call_linenos(loop, _AUTHORITY) for loop in loops)


def _authority_outside_before_loop(src: str) -> bool:
    fn = _design_fn(src)
    auth = _call_linenos(fn, _AUTHORITY)
    fors = [n.lineno for n in ast.walk(fn) if isinstance(n, ast.For)]
    if not auth or not fors or _authority_inside_any_loop(fn):
        return False
    return min(auth) < min(fors)


def test_rds11_authority_outside_and_before_loop():
    assert _authority_outside_before_loop(_design_src())


def test_rds13_generators_and_persist_after_authority():
    fn = _design_fn(_design_src())
    auth = min(_call_linenos(fn, _AUTHORITY))
    after = set(GENERATOR_NAMES) | {"persist_authorized_manufacturing_output"}
    later = [lineno for name in after for lineno in _call_linenos(fn, name)]
    assert later and all(lineno > auth for lineno in later)


def test_rds14_misordered_fixture_fails():
    bad = (
        "def design_rosette(payload=None, response=None):\n"
        "    ring_dicts = _design_rings_from_payload(payload)\n"
        "    for ring_dict in ring_dicts:\n"
        "        authority = require_manufacturing_output_authority(tool_id='rosette:design')\n"
        "        gcode = generate_gcode_from_toolpaths(x, y)\n"
    )
    assert not _authority_outside_before_loop(bad)


def test_rds12_25_authority_once_per_multiring(client, memory_store, monkeypatch):
    calls = _count_authority(monkeypatch)
    r = client.post(DESIGN_PATH, json=VALID_BODY)
    assert r.status_code == 200, r.text
    assert calls["calls"] == 1


# ---- Blocked path (RDS-15..22) ----

@pytest.mark.parametrize("risk", ["RED", "UNKNOWN", "ERROR"])
def test_rds15_16_blocking_verdicts_return_409(client, monkeypatch, risk):
    _force_decision(monkeypatch, risk)
    r = client.post(DESIGN_PATH, json=VALID_BODY)
    assert r.status_code == 409, r.text
    assert r.json()["detail"]["error"] == "SAFETY_BLOCKED"


def test_rds17_19_no_generator_no_partial_on_block(client, monkeypatch):
    _force_decision(monkeypatch, "RED")
    _forbid_generators(monkeypatch)
    r = client.post(DESIGN_PATH, json=VALID_BODY)
    assert r.status_code == 409  # generators would AssertionError if reached


def test_rds20_22_blocked_persistence_and_headers(client, memory_store, monkeypatch):
    _force_decision(monkeypatch, "RED")

    def forbidden(*args, **kwargs):
        raise AssertionError("successful persistence reached on blocked design")

    monkeypatch.setattr(rcr, "persist_authorized_manufacturing_output", forbidden)

    r = client.post(DESIGN_PATH, json=VALID_BODY)
    assert r.status_code == 409
    assert len(memory_store.saved) == 1
    art = memory_store.saved[0]
    assert art.status == "BLOCKED"
    assert art.tool_id == DESIGN_TOOL_ID
    assert art.mode == "rosette"
    assert art.event_type == "rosette_design_blocked"
    assert art.hashes.gcode_sha256 is None
    assert all(a.status != "OK" for a in memory_store.saved)
    assert r.headers.get("X-Run-ID")
    assert r.headers.get("X-ToolBox-Lane") == "governed"
    assert r.headers.get("X-GCode-SHA256") is None


# ---- Permitted path (RDS-23..32) ----

def test_rds23_24_permitted_multiring_generates_each_ring(client, memory_store, monkeypatch):
    counts = _count_generators(monkeypatch)
    r = client.post(DESIGN_PATH, json=VALID_BODY)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True and body["combined_gcode"]
    assert body["ring_count"] == 2
    assert all(counts[n] == 2 for n in GENERATOR_NAMES), counts  # once per ring


def test_rds26_response_shape_and_order_intact(client, memory_store):
    r = client.post(DESIGN_PATH, json=VALID_BODY)
    assert r.status_code == 200
    body = r.json()
    for k in ("ok", "soundhole_diameter_mm", "ring_count", "segmentations", "gcode_by_ring", "combined_gcode", "job_ids"):
        assert k in body
    ring_ids = [g["ring_id"] for g in body["gcode_by_ring"]]
    assert ring_ids == [0, 1]


def test_rds27_30_single_ok_artifact_hash_and_runid(client, memory_store):
    r = client.post(DESIGN_PATH, json=VALID_BODY)
    assert r.status_code == 200, r.text
    digest = hashlib.sha256(r.json()["combined_gcode"].encode()).hexdigest()
    assert r.headers.get("X-GCode-SHA256") == digest
    ok = [a for a in memory_store.saved if a.status == "OK"]
    assert len(ok) == 1
    assert ok[0].hashes.gcode_sha256 == digest
    assert ok[0].run_id == r.headers.get("X-Run-ID")


def test_rds31_persisted_decision_is_real_not_synthesized(client, memory_store):
    from app.rmos.manufacturing_output_authority import require_manufacturing_output_authority
    rings = rcr._design_rings_from_payload(VALID_BODY)
    summary = design_summary(rings, VALID_BODY)
    ctx = require_manufacturing_output_authority(
        tool_id=DESIGN_TOOL_ID, mode="rosette", event_type="rosette_design", request_summary=summary
    )
    assert ctx.risk_level != "GREEN"  # real evaluator yields YELLOW here
    r = client.post(DESIGN_PATH, json=VALID_BODY)
    art = [a for a in memory_store.saved if a.status == "OK"][-1]
    assert art.decision.risk_level == ctx.risk_level
    assert art.event_type == "rosette_design_execution"


def test_rds32_artifact_metadata_lists_rings_and_jobs(client, memory_store):
    r = client.post(DESIGN_PATH, json=VALID_BODY)
    assert r.status_code == 200
    body = r.json()
    art = [a for a in memory_store.saved if a.status == "OK"][-1]
    assert art.meta.get("ring_count") == 2
    assert art.meta.get("ring_ids") == [0, 1]
    assert art.meta.get("job_ids") == body["job_ids"]


# ---- Pattern regressions (per owner ruling A) ----

def test_pattern_reg_summary_truthful_uniform_and_mixed():
    assert design_summary(rcr._design_rings_from_payload(VALID_BODY), VALID_BODY)["pattern_type"] == "checkerboard"
    assert design_summary(rcr._design_rings_from_payload(MIXED_BODY), MIXED_BODY)["pattern_type"] == "mixed"


def test_pattern_reg_variants_can_produce_different_gcode():
    from app.cam.rosette.tile_segmentation import compute_tile_segmentation, generate_slices_for_ring
    from app.cam.rosette.rosette_cnc_wiring import build_ring_cnc_export
    from app.cam.rosette.cnc import (
        MaterialType, JigAlignment, MachineEnvelope, MachineProfile, GCodePostConfig,
        generate_gcode_from_toolpaths,
    )
    env = MachineEnvelope(x_min_mm=-200, x_max_mm=200, y_min_mm=-200, y_max_mm=200, z_min_mm=-50, z_max_mm=50)
    jig = JigAlignment(origin_x_mm=0, origin_y_mm=0, rotation_deg=0)
    post = GCodePostConfig(profile=MachineProfile.GRBL, safe_z_mm=5.0, spindle_rpm=12000, tool_id=1)

    def g(pattern):
        rd = {"ring_id": 0, "radius_mm": 50.0, "width_mm": 5.0, "tile_length_mm": 10.0, "kerf_mm": 0.3, "pattern": pattern}
        rc = rcr._parse_ring_config(rd)
        seg = compute_tile_segmentation(rd)
        batch = generate_slices_for_ring(rc, seg)
        bundle, _ = build_ring_cnc_export(ring=rc, slice_batch=batch, material=MaterialType.HARDWOOD, jig_alignment=jig, envelope=env)
        return generate_gcode_from_toolpaths(bundle.toolpaths, post)

    # alternating (even tile count) vs non-alternating (odd) -> different emitted program
    assert g("checkerboard") != g("radial")


def test_pattern_reg_authority_once_before_generation():
    # structural: authority is outside and before the loop (same proof as RDS-11)
    assert _authority_outside_before_loop(_design_src())


def test_pattern_reg_persisted_summary_retains_pattern_disposition(client, memory_store):
    r = client.post(DESIGN_PATH, json=MIXED_BODY)
    assert r.status_code == 200, r.text
    art = [a for a in memory_store.saved if a.status == "OK"][-1]
    assert art.request_summary.get("pattern_type") == "mixed"
    assert art.request_summary.get("pattern_types") == ["checkerboard", "radial"]


def test_pattern_reg_no_pattern_value_changes_evaluator_risk():
    from app.rmos.api.rmos_feasibility_router import compute_rosette_feasibility as f
    base = {"outer_diameter_mm": 125.0, "inner_diameter_mm": 85.0, "ring_count": 3, "material_id": "hardwood", "rpm": 12000}
    risks = set()
    for pat in [None, "checkerboard", "radial", "mixed"]:
        req = dict(base)
        if pat is not None:
            req["pattern_type"] = pat
        res = f(req=req, tool_id=DESIGN_TOOL_ID, context="rosette_design")
        s = res.get("safety", res)
        risks.add((s.get("risk_level"), s.get("score")))
    assert len(risks) == 1  # evaluator is pattern-blind under current implementation


# ---- Inventory and non-regression (RDS-33..38) ----

def test_rds33_37_inventory_design_moves_only():
    doc = json.loads(INVENTORY_PATH.read_text())
    rows = {(r["method"], r["path"]): r for r in doc["rows"]}
    design = rows[("POST", DESIGN_PATH)]
    assert design["containment"] == "FAIL_CLOSED"
    assert design["authority_key"] == DESIGN_TOOL_ID
    assert design["authority_order"] == "before_generation"
    assert design["authority_layer"] == "manufacturing_output"
    # /export-cnc unchanged
    exp = rows[("POST", EXPORT_PATH)]
    assert exp["containment"] == "FAIL_CLOSED"
    assert exp["authority_key"] == "rosette:export_cnc"
    ung = [r for r in doc["rows"] if r["containment"] == "LIVE_UNGOVERNED"]
    assert len(ung) == 13
    assert all(r["containment"] != "PERMITTED_BY_AUTHORITY" for r in doc["rows"])


def test_rds38_probe_census_unchanged():
    doc = json.loads(INVENTORY_PATH.read_text())
    rows = {(r["method"], r["path"]): r for r in doc["rows"]}
    for slug in ("boss", "corner", "pocket", "surface_z", "vise_square"):
        for suffix in ("", "/download", "/download_governed"):
            row = rows[("POST", f"/api/probe/{slug}/gcode{suffix}")]
            assert row["containment"] == "FAIL_CLOSED"
