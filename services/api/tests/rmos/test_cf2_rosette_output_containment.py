"""Contain the two Rosette manufacturing-output emitters. Not a qualification.

CF2-ROSETTE-OUTPUT-CONTAINMENT-001, Phase A (/export-cnc checkpoint).

`/export-cnc` resolves the shared manufacturing-output authority before any
segmentation, slice, CNC-export, G-code, or job-id work. A blocking decision
returns HTTP 409 with no program; a permitted decision persists the exact
returned G-code under the same authority context.

Containment note: the static inventory label for a governed route is
``FAIL_CLOSED`` (authority runs before generation and blocks when authority is
unavailable or returns a blocking decision). ``FAIL_CLOSED`` does not mean every
request is refused: the real evaluator returns a non-blocking ``YELLOW`` for
ordinary geometry, so this route both fails closed *and* permits real jobs. The
``PERMITTED_BY_AUTHORITY`` enum stays unused by design (per the CF2 true-A
ruling); the classifier is not modified to activate it.
"""

from __future__ import annotations

import ast
import hashlib
import inspect
import json
from pathlib import Path

import pytest

from app.rmos import rosette_cam_router as rcr

from test_p2_neck_gcode_proof import program_records, walk_routes

pytestmark = pytest.mark.allow_missing_request_id

EXPORT_PATH = "/api/rmos/rosette/export-cnc"
DESIGN_PATH = "/api/rmos/rosette/design"
EXPORT_TOOL_ID = "rosette:export_cnc"

# The two known Rosette G-code emitters governed by this order.
EMITTERS = {("POST", EXPORT_PATH), ("POST", DESIGN_PATH)}

# Export-stage generators that must never run on a blocked request.
GENERATOR_NAMES = (
    "compute_tile_segmentation",
    "generate_slices_for_ring",
    "build_ring_cnc_export",
    "generate_gcode_from_toolpaths",
)

VALID_BODY = {
    "ring": {
        "ring_id": 1,
        "radius_mm": 50.0,
        "width_mm": 5.0,
        "tile_length_mm": 10.0,
        "kerf_mm": 0.3,
    }
}

INVENTORY_PATH = (
    Path(__file__).resolve().parents[2] / "governance" / "manufacturing_output_inventory.json"
)


# Fixtures


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


@pytest.fixture
def force_block(monkeypatch):
    """Deterministic blocking decision for the export tool id only.

    A narrowly scoped fixture is required for the blocked arm because the real
    evaluator returns a non-blocking YELLOW for ordinary geometry. It does not
    touch production thresholds.
    """
    import app.rmos.manufacturing_output_authority as moa

    real = moa.compute_feasibility_internal

    def blocked(*, tool_id, req, context=None):
        if tool_id == EXPORT_TOOL_ID:
            return {
                "tool_id": tool_id,
                "risk_level": "RED",
                "warnings": ["cf2-rosette-test-only-forced-block"],
                "score": 0,
                "block_reason": "forced RED (test only)",
            }
        return real(tool_id=tool_id, req=req, context=context)

    monkeypatch.setattr(
        "app.rmos.manufacturing_output_authority.compute_feasibility_internal", blocked
    )


@pytest.fixture
def rosette_permit(monkeypatch):
    """Supplemental test-only GREEN for the export tool id. Not autouse.

    The primary permitted witness uses the real YELLOW result; this fixture only
    exists to prove tool-id isolation (REX-12). Not a qualification.
    """
    import app.rmos.manufacturing_output_authority as moa

    real = moa.compute_feasibility_internal

    def permit(*, tool_id, req, context=None):
        if tool_id == EXPORT_TOOL_ID:
            return {
                "tool_id": tool_id,
                "risk_level": "GREEN",
                "warnings": ["cf2-rosette-test-only-not-qualification"],
                "score": 1,
            }
        return real(tool_id=tool_id, req=req, context=context)

    monkeypatch.setattr(
        "app.rmos.manufacturing_output_authority.compute_feasibility_internal", permit
    )


def _count_generators(monkeypatch) -> dict[str, int]:
    counts = {name: 0 for name in GENERATOR_NAMES}
    for name in GENERATOR_NAMES:
        real = getattr(rcr, name)

        def make(real_fn, key):
            def wrapped(*args, **kwargs):
                counts[key] += 1
                return real_fn(*args, **kwargs)

            return wrapped

        monkeypatch.setattr(rcr, name, make(real, name))
    return counts


def _forbid_generators(monkeypatch) -> None:
    for name in GENERATOR_NAMES:
        def make(gen_name):
            def forbidden(*args, **kwargs):
                raise AssertionError(f"{gen_name} reached on blocked path")

            return forbidden

        monkeypatch.setattr(rcr, name, make(name))


# REX-01 census


def _found_emitters(resolved) -> set[tuple[str, str]]:
    return {(r.method, r.path) for r in resolved if (r.method, r.path) in EMITTERS}


def census_problems(found: set[tuple[str, str]]) -> list[str]:
    if not found:
        return ["empty rosette-emitter population"]
    missing = [f"missing {m} {p}" for m, p in sorted(EMITTERS - found)]
    extra = [f"added {m} {p}" for m, p in sorted(found - EMITTERS)]
    bad_method = [
        f"unexpected method {m} {p}" for m, p in sorted(found) if m != "POST"
    ]
    return missing + extra + bad_method


def test_rex01_census_rejects_empty_added_removed_method_changed():
    assert census_problems(set()) == ["empty rosette-emitter population"]
    assert any(
        s.startswith("added ")
        for s in census_problems(EMITTERS | {("POST", "/api/rmos/rosette/extra")})
    )
    assert any(
        s.startswith("missing ")
        for s in census_problems(EMITTERS - {("POST", EXPORT_PATH)})
    )
    assert census_problems({("GET", EXPORT_PATH), ("POST", DESIGN_PATH)})


def test_rex01_live_census_is_exactly_two_emitters():
    from app.main import app

    resolved, unresolved = walk_routes(app.routes)
    assert unresolved == []
    assert census_problems(_found_emitters(resolved)) == []
    assert _found_emitters(resolved) == EMITTERS


# REX-02 summary derivation


def test_rex02_summary_derivation_exact_and_omits_invented_facts():
    ring = rcr._parse_ring_config(
        {"ring_id": 3, "radius_mm": 50.0, "width_mm": 10.0}
    )
    summary = rcr._rosette_ring_feasibility_summary(
        ring, {"material": "Softwood", "spindle_rpm": 15000}
    )
    assert summary["outer_diameter_mm"] == pytest.approx(110.0)
    assert summary["inner_diameter_mm"] == pytest.approx(90.0)
    assert summary["ring_count"] == 1
    assert summary["material_id"] == "softwood"
    assert summary["rpm"] == 15000
    # No invented manufacturing facts and no evaluator-default substitution.
    for absent in (
        "depth_mm",
        "tool_diameter_mm",
        "stock_thickness_mm",
        "petal_count",
        "feed_rate_mm_min",
        "pattern_type",
        "tool_id",
    ):
        assert absent not in summary


# REX-03 invalid inner geometry


def test_rex03_invalid_inner_geometry_never_reaches_authority(client, memory_store):
    ring = rcr._parse_ring_config({"radius_mm": 2.0, "width_mm": 10.0})
    with pytest.raises(ValueError):
        rcr._rosette_ring_feasibility_summary(ring, {})

    r = client.post(EXPORT_PATH, json={"ring": {"radius_mm": 2.0, "width_mm": 10.0}})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is False
    assert body["gcode"] is None
    # Authority was never resolved: no artifact of any kind.
    assert memory_store.saved == []
    assert r.headers.get("X-Run-ID") is None


# REX-04 evaluator request capture


def test_rex04_exact_request_reaching_evaluator(client, monkeypatch):
    import app.rmos.manufacturing_output_authority as moa

    real = moa.compute_feasibility_internal
    captured: dict = {}

    def capture(*, tool_id, req, context=None):
        if tool_id == EXPORT_TOOL_ID:
            captured["tool_id"] = tool_id
            captured["req"] = dict(req)
            captured["context"] = context
        return real(tool_id=tool_id, req=req, context=context)

    monkeypatch.setattr(
        "app.rmos.manufacturing_output_authority.compute_feasibility_internal", capture
    )
    r = client.post(
        EXPORT_PATH,
        json={"ring": {"radius_mm": 50.0, "width_mm": 10.0}, "material": "hardwood", "spindle_rpm": 12000},
    )
    assert r.status_code == 200, r.text
    assert captured["tool_id"] == EXPORT_TOOL_ID
    assert captured["context"] == "rosette_export_cnc"
    req = captured["req"]
    assert req["tool_id"] == EXPORT_TOOL_ID
    assert req["outer_diameter_mm"] == pytest.approx(110.0)
    assert req["inner_diameter_mm"] == pytest.approx(90.0)
    assert req["ring_count"] == 1
    assert req["material_id"] == "hardwood"
    assert req["rpm"] == 12000
    # No invented manufacturing facts leaked into the evaluator request.
    for absent in ("depth_mm", "tool_diameter_mm", "stock_thickness_mm", "pattern_type", "feed_rate_mm_min"):
        assert absent not in req


# REX-05 authority ordering


def _ordered_call_names(fn_src: str) -> list[str]:
    tree = ast.parse(fn_src)
    fn = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "export_rosette_cnc"
    )
    names: list[str] = []

    def visit(node):
        if isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Name):
                names.append(f.id)
            elif isinstance(f, ast.Attribute):
                names.append(f.attr)
        for child in ast.iter_child_nodes(node):
            visit(child)

    for stmt in fn.body:
        visit(stmt)
    return names


def _order_problems(fn_src: str) -> list[str]:
    names = _ordered_call_names(fn_src)
    if "require_manufacturing_output_authority" not in names:
        return ["no authority call"]
    authority_at = names.index("require_manufacturing_output_authority")
    after = set(GENERATOR_NAMES) | {"persist_authorized_manufacturing_output"}
    return [
        f"{name} precedes authority"
        for i, name in enumerate(names)
        if name in after and i < authority_at
    ]


def test_rex05_authority_precedes_all_generation_and_persistence():
    fn_src = inspect.getsource(rcr.export_rosette_cnc)
    assert _order_problems(fn_src) == []
    # job-id creation must also follow authority.
    src_lines = fn_src.splitlines()
    auth_line = next(i for i, ln in enumerate(src_lines) if "require_manufacturing_output_authority" in ln)
    job_line = next(i for i, ln in enumerate(src_lines) if "JOB-ROSETTE-" in ln)
    assert auth_line < job_line


def test_rex05_misordered_fixture_fails():
    bad = (
        "def export_rosette_cnc(payload=None, response=None):\n"
        "    ring = _parse_ring_config(payload)\n"
        "    gcode = generate_gcode_from_toolpaths(x, y)\n"
        "    authority = require_manufacturing_output_authority(tool_id='rosette:export_cnc')\n"
        "    persist_authorized_manufacturing_output(context=authority, gcode_text=gcode)\n"
    )
    assert _order_problems(bad) == ["generate_gcode_from_toolpaths precedes authority"]


# REX-06 / REX-07 / REX-08 blocked path


def test_rex06_blocking_response_carries_no_program(client, force_block):
    r = client.post(EXPORT_PATH, json=VALID_BODY)
    assert r.status_code == 409, r.text
    detail = r.json()["detail"]
    assert detail["error"] == "SAFETY_BLOCKED"
    assert detail["tool_id"] == EXPORT_TOOL_ID
    assert r.headers.get("X-ToolBox-Lane") == "governed"
    assert r.headers.get("X-Run-ID")
    assert r.headers.get("X-GCode-SHA256") is None
    assert "attachment" not in (r.headers.get("content-disposition") or "").lower()
    assert program_records(r.headers.get("content-type", ""), r.content) == []
    assert "gcode" not in detail


def test_rex07_no_generator_runs_on_blocked_path(client, force_block, monkeypatch):
    _forbid_generators(monkeypatch)
    r = client.post(EXPORT_PATH, json=VALID_BODY)
    assert r.status_code == 409, r.text


def test_rex08_blocked_persistence_is_single_blocked_artifact(client, force_block, memory_store):
    r = client.post(EXPORT_PATH, json=VALID_BODY)
    assert r.status_code == 409
    assert len(memory_store.saved) == 1
    artifact = memory_store.saved[0]
    assert artifact.status == "BLOCKED"
    assert artifact.tool_id == EXPORT_TOOL_ID
    assert artifact.mode == "rosette"
    assert artifact.event_type == "rosette_export_cnc_blocked"
    assert artifact.hashes.gcode_sha256 is None
    assert all(a.status != "OK" for a in memory_store.saved)


# REX-09 / REX-10 / REX-11 permitted path (real YELLOW)


def test_rex09_permitted_execution_calls_each_stage_once(client, memory_store, monkeypatch):
    counts = _count_generators(monkeypatch)
    r = client.post(EXPORT_PATH, json=VALID_BODY)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True
    assert body["gcode"]
    assert body["job_id"].startswith("JOB-ROSETTE-")
    assert all(counts[name] == 1 for name in GENERATOR_NAMES), counts


def test_rex10_hash_identity_and_governed_headers(client, memory_store):
    r = client.post(EXPORT_PATH, json=VALID_BODY)
    assert r.status_code == 200, r.text
    digest = hashlib.sha256(r.json()["gcode"].encode()).hexdigest()
    assert r.headers.get("X-GCode-SHA256") == digest
    assert r.headers.get("X-ToolBox-Lane") == "governed"
    run_id = r.headers.get("X-Run-ID")
    assert run_id
    ok = [a for a in memory_store.saved if a.status == "OK"]
    assert len(ok) == 1
    assert ok[0].hashes.gcode_sha256 == digest
    assert ok[0].run_id == run_id


def test_rex11_persisted_decision_is_the_authority_decision(client, memory_store):
    # Independently resolve authority for the same summary to get the real risk.
    from app.rmos.manufacturing_output_authority import require_manufacturing_output_authority

    ring = rcr._parse_ring_config(VALID_BODY["ring"])
    summary = rcr._rosette_ring_feasibility_summary(ring, VALID_BODY)
    ctx = require_manufacturing_output_authority(
        tool_id=EXPORT_TOOL_ID, mode="rosette", event_type="rosette_export_cnc", request_summary=summary
    )
    expected_risk = ctx.risk_level
    assert expected_risk != "GREEN"  # real evaluator yields YELLOW, not a synthesized GREEN

    r = client.post(EXPORT_PATH, json=VALID_BODY)
    assert r.status_code == 200, r.text
    artifact = [a for a in memory_store.saved if a.status == "OK"][-1]
    assert artifact.decision.risk_level == expected_risk
    assert artifact.tool_id == EXPORT_TOOL_ID
    assert artifact.mode == "rosette"
    assert artifact.event_type == "rosette_export_cnc_execution"
    assert artifact.hashes.feasibility_sha256
    assert artifact.request_summary["outer_diameter_mm"] == pytest.approx(summary["outer_diameter_mm"])
    assert artifact.request_summary["ring_count"] == 1


# REX-12 isolation


def test_rex12_permit_fixture_does_not_release_other_tool_ids(client, rosette_permit):
    r = client.post(
        "/api/cam/polygon_offset_governed.nc",
        json={"polygon": [[0, 0], [1, 0], [1, 1], [0, 0]], "tool_dia": 6.0, "stepover": 0.4},
    )
    assert r.status_code == 409
    assert r.json()["detail"]["error"] == "SAFETY_BLOCKED"


# REX-13 existing contract preserved


def test_rex13_existing_contract_preserved(client):
    # Default/empty payload still succeeds (real YELLOW permit) with governed headers.
    r = client.post(EXPORT_PATH, json={})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True and body["gcode"]
    assert "G21" in body["gcode"] and "G90" in body["gcode"]
    assert body["safety"]["decision"] is not None
    assert r.headers.get("X-ToolBox-Lane") == "governed"

    # FANUC profile still selected without breaking the contract.
    r2 = client.post(EXPORT_PATH, json={**VALID_BODY, "machine_profile": "fanuc", "spindle_rpm": 18000})
    assert r2.status_code == 200, r2.text
    assert "S18000" in r2.json()["gcode"]


# REX-14 inventory delta


def test_rex14_inventory_delta_moves_only_export_cnc():
    document = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    rows = {(r["method"], r["path"]): r for r in document["rows"]}

    export_row = rows[("POST", EXPORT_PATH)]
    assert export_row["containment"] == "FAIL_CLOSED"
    assert export_row["authority_layer"] == "manufacturing_output"
    assert export_row["authority_key"] == EXPORT_TOOL_ID
    assert export_row["authority_order"] == "before_generation"

    # Phase B (CF2-ROSETTE-DESIGN-CONTAINMENT-003R) moved /design to FAIL_CLOSED;
    # /export-cnc (asserted above) remains governed. Live-ungoverned 14 -> 13.
    assert rows[("POST", DESIGN_PATH)]["containment"] == "FAIL_CLOSED"

    ungoverned = [r for r in document["rows"] if r["containment"] == "LIVE_UNGOVERNED"]
    assert len(ungoverned) == 13
    # true-A: the PERMITTED_BY_AUTHORITY set remains empty.
    assert all(r["containment"] != "PERMITTED_BY_AUTHORITY" for r in document["rows"])
