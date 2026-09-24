"""Contain the ten live probe emitters. Not a qualification."""

from __future__ import annotations

import ast
import hashlib
import inspect

import pytest

from test_p2_neck_gcode_proof import program_records, walk_routes

pytestmark = pytest.mark.allow_missing_request_id

FAMILIES = (
    ("boss", "boss_probe_gcode", "generate_boss_probe", "app.routers.probe.boss_router"),
    ("corner", "corner_probe_gcode", "generate_corner_probe", "app.routers.probe.corner_router"),
    ("pocket", "pocket_probe_gcode", "generate_pocket_probe", "app.routers.probe.pocket_router"),
    ("surface_z", "surface_z_probe_gcode", "generate_surface_z_probe", "app.routers.probe.surface_z_router"),
    ("vise_square", "vise_square_probe_gcode", "generate_vise_square_probe", "app.routers.probe.vise_square_router"),
)
TOOL_IDS = {tool_id for _slug, tool_id, _gen, _mod in FAMILIES}
OUTPUT_NAMES = {
    "generate_boss_probe",
    "generate_corner_probe",
    "generate_pocket_probe",
    "generate_surface_z_probe",
    "generate_vise_square_probe",
    "persist_authorized_probe_program",
    "get_statistics",
    "create_governed_probe_response",
}


def _paths(slug: str) -> dict[str, str]:
    base = f"/api/probe/{slug}/gcode"
    return {"json": base, "download": f"{base}/download", "governed": f"{base}/download_governed"}


def expected_routes() -> set[tuple[str, str]]:
    routes = set()
    for slug, _tool, _gen, _mod in FAMILIES:
        for path in _paths(slug).values():
            routes.add(("POST", path))
    return routes


def census_problems(found: set[tuple[str, str]]) -> list[str]:
    if not found:
        return ["empty probe-output population"]
    missing = [f"missing {method} {path}" for method, path in sorted(expected_routes() - found)]
    extra = [f"added {method} {path}" for method, path in sorted(found - expected_routes())]
    bad_method = [f"unexpected method {method} {path}" for method, path in sorted(found) if method != "POST"]
    return missing + extra + bad_method


def _probe_posts(resolved) -> set[tuple[str, str]]:
    found = set()
    for route in resolved:
        path = route.path or ""
        if route.method == "POST" and path.startswith("/api/probe/") and "/gcode" in path:
            found.add((route.method, path))
    return found


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
def cf2_probe_permit(monkeypatch):
    """Test-only GREEN for the five probe tool ids. Not autouse. Not qualification."""
    from app.rmos.manufacturing_output_authority import compute_feasibility_internal

    real = compute_feasibility_internal

    def compute(*, tool_id, req, context=None):
        if tool_id not in TOOL_IDS:
            return real(tool_id=tool_id, req=req, context=context)
        return {
            "tool_id": tool_id,
            "risk_level": "GREEN",
            "warnings": ["cf2-test-only-not-qualification"],
            "score": 1,
        }

    monkeypatch.setattr(
        "app.rmos.manufacturing_output_authority.compute_feasibility_internal",
        compute,
    )


def _refuse(response, tool_id: str) -> None:
    disposition = response.headers.get("content-disposition") or ""
    detail = response.json()["detail"]
    assert response.status_code == 409
    assert detail["error"] == "SAFETY_BLOCKED"
    assert detail["tool_id"] == tool_id
    assert response.headers.get("X-ToolBox-Lane") == "governed"
    assert response.headers.get("X-Run-ID")
    assert response.headers.get("X-GCode-SHA256") is None
    assert program_records(response.headers.get("content-type", ""), response.content) == []
    assert "attachment" not in disposition.lower()
    assert "gcode" not in detail


def _order_problems(source: str, fn_name: str) -> list[str]:
    tree = ast.parse(source)
    fn = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.AsyncFunctionDef) and node.name == fn_name
    )
    names: list[str] = []

    def visit(node: ast.AST) -> None:
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                names.append(func.id)
            elif isinstance(func, ast.Attribute):
                names.append(func.attr)
        for child in ast.iter_child_nodes(node):
            visit(child)

    for stmt in fn.body:
        visit(stmt)
    authority_at = [i for i, name in enumerate(names) if name == "require_probe_manufacturing_authority"]
    if not authority_at:
        return ["no authority call"]
    first = authority_at[0]
    return [f"{name} precedes authority" for i, name in enumerate(names) if name in OUTPUT_NAMES and i < first]


def _event_type(source: str, fn_name: str) -> str | None:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if not isinstance(node, ast.AsyncFunctionDef) or node.name != fn_name:
            continue
        for child in ast.walk(node):
            if not isinstance(child, ast.Call):
                continue
            func = child.func
            name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
            if name != "require_probe_manufacturing_authority":
                continue
            for keyword in child.keywords:
                if keyword.arg == "event_type" and isinstance(keyword.value, ast.Constant):
                    return keyword.value.value
    return None


def test_detector_controls():
    assert program_records("text/plain", b"G0 X0\nG1 Z-1\nM3\n") == ["G0", "G1", "M3"]
    raw = b'{"gcode": "G0 X0\\nG1 Z-1\\nM3\\n", "detail": "quote G0"}'
    assert program_records("application/json", raw) == ["G0", "G1", "M3"]
    prose = b'{"detail": {"reason": "G0", "message": "M3", "evidence": "G1"}}'
    assert program_records("application/json", prose) == []


def test_census_rejects_empty_added_and_removed_populations():
    assert census_problems(set()) == ["empty probe-output population"]
    extra = expected_routes() | {("POST", "/api/probe/boss/gcode/extra")}
    missing = expected_routes() - {("POST", "/api/probe/boss/gcode")}
    assert any(item.startswith("added ") for item in census_problems(extra))
    assert any(item.startswith("missing ") for item in census_problems(missing))
    assert census_problems(expected_routes() | {("GET", "/api/probe/boss/gcode")})


def test_live_census_is_exactly_fifteen_probe_output_routes():
    from app.main import app

    resolved, unresolved = walk_routes(app.routes)
    assert unresolved == []
    assert census_problems(_probe_posts(resolved)) == []
    assert len(_probe_posts(resolved)) == 15
    paths = {route.path for route in resolved}
    assert "/api/probe/patterns" in paths
    assert "/api/probe/setup_sheet/svg" in paths


def test_authority_precedes_generation_and_misordered_fixture_fails():
    from app.main import app

    resolved, _unresolved = walk_routes(app.routes)
    by_path = {route.path: route for route in resolved}
    for slug, tool_id, _gen, _mod in FAMILIES:
        carriers = _paths(slug)
        expected = {
            "json": f"{tool_id}_json",
            "download": f"{tool_id}_download",
            "governed": tool_id,
        }
        for carrier, path in carriers.items():
            route = by_path[path]
            source = inspect.getsource(route.endpoint)
            assert _order_problems(source, route.endpoint.__name__) == [], path
            assert _event_type(source, route.endpoint.__name__) == expected[carrier]
    late = (
        "async def generate_boss_probe(body, response):\n"
        "    gcode = generate_boss_probe(body)\n"
        "    require_probe_manufacturing_authority(tool_id='boss_probe_gcode')\n"
        "    persist_authorized_probe_program(gcode)\n"
    )
    assert _order_problems(late, "generate_boss_probe")


@pytest.mark.parametrize("slug,tool_id,generator,module_name", FAMILIES)
@pytest.mark.parametrize("carrier", ("json", "download"))
def test_new_carriers_refuse_before_generation(
    client, memory_store, monkeypatch, slug, tool_id, generator, module_name, carrier
):
    module = __import__(module_name, fromlist=["probe_patterns"])

    def forbidden(**kwargs):
        raise AssertionError(generator)

    monkeypatch.setattr(module.probe_patterns, generator, forbidden)
    response = client.post(_paths(slug)[carrier], json={})
    _refuse(response, tool_id)
    assert len(memory_store.saved) == 1
    artifact = memory_store.saved[0]
    assert artifact.status == "BLOCKED"
    assert artifact.tool_id == tool_id
    assert artifact.mode == "probing"
    assert artifact.decision.risk_level == "UNKNOWN"
    assert artifact.hashes.gcode_sha256 is None
    assert artifact.event_type == f"{tool_id}_{carrier}_blocked"
    assert all(item.status != "OK" for item in memory_store.saved)


@pytest.mark.parametrize("slug,tool_id,generator,module_name", FAMILIES)
def test_governed_download_still_refuses_independently(
    client, memory_store, monkeypatch, slug, tool_id, generator, module_name
):
    module = __import__(module_name, fromlist=["probe_patterns"])

    def forbidden(**kwargs):
        raise AssertionError(generator)

    monkeypatch.setattr(module.probe_patterns, generator, forbidden)
    response = client.post(_paths(slug)["governed"], json={})
    _refuse(response, tool_id)
    assert memory_store.saved[0].event_type == f"{tool_id}_blocked"
    assert memory_store.saved[0].status == "BLOCKED"


@pytest.mark.parametrize("slug,tool_id,generator,module_name", FAMILIES)
def test_permitted_json_persists_the_fixture_decision(
    client, memory_store, cf2_probe_permit, monkeypatch, slug, tool_id, generator, module_name
):
    module = __import__(module_name, fromlist=["probe_patterns"])
    calls = []
    real = getattr(module.probe_patterns, generator)

    def wrapped(**kwargs):
        calls.append(kwargs)
        return real(**kwargs)

    monkeypatch.setattr(module.probe_patterns, generator, wrapped)
    response = client.post(_paths(slug)["json"], json={})
    assert response.status_code == 200, response.text
    body = response.json()
    assert "gcode" in body
    assert response.headers.get("X-ToolBox-Lane") == "governed"
    assert response.headers.get("X-Run-ID")
    digest = hashlib.sha256(body["gcode"].encode()).hexdigest()
    assert response.headers.get("X-GCode-SHA256") == digest
    artifact = memory_store.saved[-1]
    assert artifact.status == "OK"
    assert artifact.tool_id == tool_id
    assert artifact.decision.risk_level == "GREEN"
    assert artifact.decision.warnings == ["cf2-test-only-not-qualification"]
    assert artifact.hashes.gcode_sha256 == digest
    assert artifact.event_type == f"{tool_id}_json_execution"
    assert len(calls) == 1


@pytest.mark.parametrize("slug,tool_id,generator,module_name", FAMILIES)
def test_permitted_download_is_a_governed_attachment(
    client, memory_store, cf2_probe_permit, slug, tool_id, generator, module_name
):
    response = client.post(_paths(slug)["download"], json={})
    assert response.status_code == 200, response.text
    disposition = response.headers.get("content-disposition") or ""
    assert "attachment" in disposition.lower()
    assert ".nc" in disposition
    assert response.headers.get("X-ToolBox-Lane") == "governed"
    assert response.headers.get("X-Run-ID")
    digest = hashlib.sha256(response.content).hexdigest()
    assert response.headers.get("X-GCode-SHA256") == digest
    artifact = memory_store.saved[-1]
    assert artifact.hashes.gcode_sha256 == digest
    assert artifact.decision.risk_level == "GREEN"
    assert artifact.event_type == f"{tool_id}_download_execution"


def test_program_assertion_fails_without_the_permit_fixture(client):
    response = client.post("/api/probe/boss/gcode", json={})

    def functional_assertion():
        assert response.status_code == 200
        assert "gcode" in response.json()

    with pytest.raises(AssertionError):
        functional_assertion()
    _refuse(response, "boss_probe_gcode")


def test_permit_fixture_does_not_release_other_tool_ids(client, cf2_probe_permit):
    response = client.post(
        "/api/cam/polygon_offset_governed.nc",
        json={"polygon": [[0, 0], [1, 0], [1, 1], [0, 0]], "tool_dia": 6.0, "stepover": 0.4},
    )
    assert response.status_code == 409
    assert response.json()["detail"]["error"] == "SAFETY_BLOCKED"


def test_pattern_list_and_setup_sheet_stay_available(client):
    patterns = client.get("/api/probe/patterns")
    assert patterns.status_code == 200
    assert program_records("application/json", patterns.content) == []
    sheet = client.post("/api/probe/setup_sheet/svg", json={"pattern": "corner_outside"})
    assert sheet.status_code == 200
    assert "svg" in sheet.headers.get("content-type", "")
    assert sheet.headers.get("X-GCode-SHA256") is None


def test_inventory_moves_only_the_ten_probe_rows():
    import json
    from pathlib import Path

    document = json.loads(
        (Path(__file__).resolve().parents[2] / "governance" / "manufacturing_output_inventory.json").read_text()
    )
    rows = {(row["method"], row["path"]): row for row in document["rows"]}
    for slug, tool_id, _gen, _mod in FAMILIES:
        for path in _paths(slug).values():
            row = rows[("POST", path)]
            assert row["containment"] == "FAIL_CLOSED", path
            assert row["authority_key"] == tool_id
            assert row["authority_layer"] == "manufacturing_output"
    assert all(row["containment"] != "PERMITTED_BY_AUTHORITY" for row in rows.values())
    assert rows[("POST", "/api/cam/polygon_offset.nc")]["containment"] == "LIVE_UNGOVERNED"
    assert rows[("POST", "/api/geometry/export_gcode")]["containment"] == "LIVE_UNGOVERNED"
    ungoverned = [row for row in rows.values() if row["containment"] == "LIVE_UNGOVERNED"]
    assert len(ungoverned) == 15
