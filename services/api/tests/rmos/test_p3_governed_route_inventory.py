"""Nine-route census, authority order, and the self-minted GREEN scan."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

from test_p2_neck_gcode_proof import program_records, walk_routes

pytestmark = pytest.mark.allow_missing_request_id

P3_TARGETS = {
    ("POST", "/api/cam/polygon_offset_governed.nc"),
    ("POST", "/api/geometry/export_gcode_governed"),
    ("POST", "/api/probe/boss/gcode/download_governed"),
    ("POST", "/api/probe/corner/gcode/download_governed"),
    ("POST", "/api/probe/pocket/gcode/download_governed"),
    ("POST", "/api/probe/surface_z/gcode/download_governed"),
    ("POST", "/api/probe/vise_square/gcode/download_governed"),
}
RETRACT_ENFORCED = {
    ("POST", "/api/cam/retract/gcode_governed"),
    ("POST", "/api/cam/retract/gcode/download_governed"),
}
ORIGINAL_NINE = P3_TARGETS | RETRACT_ENFORCED
DRAFT_SIBLINGS = {
    ("POST", "/api/cam/polygon_offset.nc"),
    ("POST", "/api/geometry/export_gcode"),
}
# Contained by LTB-CF2-PROBE-CONTAIN-001. These were not part of the original nine.
PROBE_NEWLY_ENFORCED = {
    ("POST", "/api/probe/boss/gcode"),
    ("POST", "/api/probe/boss/gcode/download"),
    ("POST", "/api/probe/corner/gcode"),
    ("POST", "/api/probe/corner/gcode/download"),
    ("POST", "/api/probe/pocket/gcode"),
    ("POST", "/api/probe/pocket/gcode/download"),
    ("POST", "/api/probe/surface_z/gcode"),
    ("POST", "/api/probe/surface_z/gcode/download"),
    ("POST", "/api/probe/vise_square/gcode"),
    ("POST", "/api/probe/vise_square/gcode/download"),
}
AUTHORITY_CALLS = {
    "require_manufacturing_output_authority",
    "require_probe_manufacturing_authority",
    "_authorize_retract",
}
OUTPUT_CALLS = {
    "generate_polygon_offset_nc_program",
    "generate_boss_probe",
    "generate_corner_probe",
    "generate_pocket_probe",
    "generate_surface_z_probe",
    "generate_vise_square_probe",
    "_load_posts",
    "create_governed_probe_response",
    "persist_authorized_manufacturing_output",
    "persist_authorized_probe_program",
    "get_statistics",
    "RunDecision",
    "_build_simple_retract_gcode",
    "_build_download_retract_gcode",
}
DELEGATED_AUTHORITY = {
    "generate_simple_retract_gcode",
    "download_retract_gcode",
}
TARGET_MODULES = [
    "app/rmos/manufacturing_output_authority.py",
    "app/cam/probe_service.py",
    "app/routers/polygon_offset_router.py",
    "app/routers/geometry/export_router.py",
    "app/routers/probe/boss_router.py",
    "app/routers/probe/corner_router.py",
    "app/routers/probe/pocket_router.py",
    "app/routers/probe/surface_z_router.py",
    "app/routers/probe/vise_square_router.py",
]
NEW_TEST_FILES = [
    "tests/rmos/test_p3_governed_authority_policy.py",
    "tests/rmos/test_p3_governed_route_refusals.py",
    "tests/rmos/test_p3_governed_route_inventory.py",
]


def _call_name(node: ast.Call) -> str:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return ""


def _ordered_calls(fn: ast.AST) -> list[str]:
    names: list[str] = []

    def visit(node: ast.AST) -> None:
        if isinstance(node, ast.Call):
            names.append(_call_name(node))
        for child in ast.iter_child_nodes(node):
            visit(child)

    body = list(fn.body)
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        body = body[1:]
    for stmt in body:
        visit(stmt)
    return names


def order_problems(source: str, fn_name: str) -> list[str]:
    tree = ast.parse(source)
    fn = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == fn_name
    )
    names = _ordered_calls(fn)
    authority_at = [i for i, name in enumerate(names) if name in AUTHORITY_CALLS]
    if not authority_at:
        return ["no authority call"]
    first = authority_at[0]
    return [
        f"{name} precedes authority"
        for i, name in enumerate(names)
        if name in OUTPUT_CALLS and i < first
    ]


def green_literals(source: str) -> list[int]:
    hits = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call) or _call_name(node) != "RunDecision":
            continue
        for keyword in node.keywords:
            value = keyword.value
            if (
                keyword.arg == "risk_level"
                and isinstance(value, ast.Constant)
                and value.value == "GREEN"
            ):
                hits.append(node.lineno)
    return hits


def _is_governed_manufacturing(method: str, path: str) -> bool:
    if method != "POST":
        return False
    if "_governed" not in path:
        return False
    return "gcode" in path or path.endswith(".nc")


def test_detector_still_reads_commands_and_ignores_prose():
    assert program_records("text/plain", b"G0 X0\nG1 Z-1\nM3\n") == ["G0", "G1", "M3"]
    raw = b'{"gcode": "G0 X0\\nG1 Z-1\\nM3\\n", "detail": "quote G0"}'
    assert program_records("application/json", raw) == ["G0", "G1", "M3"]
    prose = b'{"detail": {"reason": "G0", "message": "M3", "evidence": "G1"}}'
    assert program_records("application/json", prose) == []


def test_get_routes_are_not_manufacturing_population():
    assert _is_governed_manufacturing("GET", "/api/rmos/governed/gcode") is False


def test_the_original_nine_routes_are_discovered():
    from app.main import app

    resolved, unresolved = walk_routes(app.routes)
    found = {
        (route.method, route.path)
        for route in resolved
        if _is_governed_manufacturing(route.method, route.path)
    }
    drafts = {(route.method, route.path) for route in resolved} & DRAFT_SIBLINGS
    assert unresolved == []
    assert found == ORIGINAL_NINE
    assert drafts == DRAFT_SIBLINGS
    assert len(found & P3_TARGETS) == 7
    assert found & RETRACT_ENFORCED == RETRACT_ENFORCED


def census_problems(found: set[tuple[str, str]]) -> list[str]:
    if not found:
        return ["census discovered zero governed manufacturing routes"]
    problems = [f"missing {method} {path}" for method, path in sorted(ORIGINAL_NINE - found)]
    problems.extend(
        f"undeclared {method} {path}" for method, path in sorted(found - ORIGINAL_NINE)
    )
    return problems


def test_empty_added_and_removed_populations_fail():
    extra = ORIGINAL_NINE | {("POST", "/api/cam/extra_governed.nc")}
    missing = ORIGINAL_NINE - {("POST", "/api/geometry/export_gcode_governed")}
    assert census_problems(set()) == ["census discovered zero governed manufacturing routes"]
    assert census_problems(extra) == ["undeclared POST /api/cam/extra_governed.nc"]
    assert census_problems(missing) == ["missing POST /api/geometry/export_gcode_governed"]
    assert census_problems(ORIGINAL_NINE) == []


def test_unresolved_route_objects_fail_the_census():
    class Mystery:
        pass

    resolved, unresolved = walk_routes([Mystery()])
    assert resolved == []
    assert unresolved


def test_ordered_handlers_pass_and_misordered_fixtures_fail():
    ordered = (
        "def polygon_offset_nc_governed(req):\n"
        "    summary = req.model_dump()\n"
        "    require_manufacturing_output_authority(tool_id='cam_polygon_offset_nc')\n"
        "    program = generate_polygon_offset_nc_program(req)\n"
    )
    generated_first = (
        "def polygon_offset_nc_governed(req):\n"
        "    program = generate_polygon_offset_nc_program(req)\n"
        "    require_manufacturing_output_authority(tool_id='cam_polygon_offset_nc')\n"
    )
    green_first = (
        "def export_gcode_governed(body):\n"
        "    decision = RunDecision(risk_level='GREEN')\n"
        "    require_manufacturing_output_authority(tool_id='geometry_export_gcode')\n"
        "    persist_authorized_manufacturing_output(context=decision)\n"
    )
    attachment_first = (
        "def download_boss_probe_governed(body):\n"
        "    return create_governed_probe_response(gcode)\n"
    )
    assert order_problems(ordered, "polygon_offset_nc_governed") == []
    assert order_problems(generated_first, "polygon_offset_nc_governed")
    assert any("RunDecision" in problem for problem in order_problems(green_first, "export_gcode_governed"))
    assert green_literals(green_first) == [2]
    assert order_problems(attachment_first, "download_boss_probe_governed")


def test_live_handlers_consult_authority_before_output():
    from app.main import app

    resolved, _unresolved = walk_routes(app.routes)
    checked = 0
    for route in resolved:
        key = (route.method, route.path)
        if key not in ORIGINAL_NINE:
            continue
        source = inspect.getsource(route.endpoint)
        problems = order_problems(source, route.endpoint.__name__)
        if problems == ["no authority call"]:
            names = _ordered_calls(
                next(
                    node
                    for node in ast.walk(ast.parse(source))
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and node.name == route.endpoint.__name__
                )
            )
            delegated = [name for name in names if name in DELEGATED_AUTHORITY]
            if len(delegated) == 1:
                module_source = inspect.getsource(inspect.getmodule(route.endpoint))
                problems = order_problems(module_source, delegated[0])
        assert problems == [], key
        checked += 1
    assert checked == 9


def test_probe_draft_routes_are_enforced_without_rewriting_p3_history():
    """The ten routes were live in #403. This order contains them. The original nine stay nine."""
    from app.main import app

    resolved, unresolved = walk_routes(app.routes)
    found = {(route.method, route.path) for route in resolved}
    assert unresolved == []
    assert PROBE_NEWLY_ENFORCED <= found
    assert PROBE_NEWLY_ENFORCED.isdisjoint(ORIGINAL_NINE)
    checked = 0
    for route in resolved:
        if (route.method, route.path) not in PROBE_NEWLY_ENFORCED:
            continue
        source = inspect.getsource(route.endpoint)
        assert order_problems(source, route.endpoint.__name__) == [], route.path
        checked += 1
    assert checked == 10


def test_target_modules_do_not_mint_green():
    root = Path(__file__).resolve().parents[2]
    for relative in TARGET_MODULES:
        source = (root / relative).read_text()
        assert green_literals(source) == [], relative
    fixture = "def bad():\n    return RunDecision(risk_level='GREEN')\n"
    assert green_literals(fixture) == [2]


def test_probe_response_helper_cannot_create_authority():
    import app.cam.probe_service as module

    source = inspect.getsource(module.create_governed_probe_response)
    assert "compute_feasibility_internal" not in source
    assert "RunDecision" not in source
    assert "require_manufacturing_output_authority" not in source


def test_retract_source_is_not_rewritten_onto_the_new_helper():
    import app.routers.retract.retract_gcode_router as module

    source = inspect.getsource(module)
    assert "manufacturing_output_authority" not in source
    assert "def _authorize_retract" in source
    assert green_literals(source) == []


def test_new_p3_test_files_stay_under_500_lines():
    root = Path(__file__).resolve().parents[2]
    for relative in NEW_TEST_FILES:
        count = len((root / relative).read_text().splitlines())
        assert count < 500, (relative, count)
