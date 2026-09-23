"""LTB-REMEDIATE-CF4: contain the three Flying V toolpath routes.

Each handler's first executable statement is ``_readiness_gate("flying_v_body")``.
The readiness record stays REVIEW_REQUIRED. This module does not qualify the
generator, lift the gate, or drive a machine.

FastAPI binds query parameters before the handler runs. The gate is before
in-handler parsing and generation, not before that framework binding.
"""
from __future__ import annotations

import ast
import importlib
import inspect
import textwrap

import pytest

from test_p2_neck_gcode_proof import first_statement_gate_key, program_records

pytestmark = pytest.mark.allow_missing_request_id

KEY = "flying_v_body"
PREFIX = "/api/cam/guitar/flying_v"
CONTROL = f"{PREFIX}/toolpath/control_cavity"
NECK_POCKET = f"{PREFIX}/toolpath/neck_pocket"
PICKUP = f"{PREFIX}/toolpath/pickup"
SPEC = f"{PREFIX}/spec"
VALIDATE = f"{PREFIX}/validate"
BODY_GCODE = f"{PREFIX}/body/gcode"

DECLARED = {
    ("POST", CONTROL),
    ("POST", NECK_POCKET),
    ("POST", PICKUP),
}

HANDLERS = (
    "generate_control_cavity_toolpath",
    "generate_neck_pocket_toolpath",
    "generate_pickup_toolpath",
)

_CONVERTER_PREFIX = "{file_path:"


def _router():
    return importlib.import_module("app.routers.cam.guitar.flying_v_cam_router")


def _normalize(path: str) -> str:
    while _CONVERTER_PREFIX in path:
        start = path.index(_CONVERTER_PREFIX)
        end = path.index("}", start)
        name = path[start + len(_CONVERTER_PREFIX):end]
        path = path[:start] + "{" + name + "}" + path[end + 1:]
    return path


def _walk(routes, prefix: str = ""):
    """(method, path, response_model) for every HTTP route under nested routers."""
    found = []
    for route in routes:
        if type(route).__name__ == "_IncludedRouter":
            context = getattr(route, "include_context", None)
            original = getattr(route, "original_router", None)
            if original is None:
                continue
            child = prefix + (getattr(context, "prefix", "") or "")
            found.extend(_walk(original.routes, child))
            continue
        path = getattr(route, "path", None)
        if path is None:
            nested = getattr(route, "routes", None)
            if nested:
                found.extend(_walk(nested, prefix))
            continue
        methods = getattr(route, "methods", None) or set()
        model = getattr(route, "response_model", None)
        full = _normalize(prefix + path)
        for method in methods:
            if method in {"HEAD", "OPTIONS"}:
                continue
            found.append((method, full, model))
    return found


def _toolpath_posts(routes, prefix: str = "") -> set[tuple[str, str]]:
    model = _router().ToolpathResponse
    return {
        (method, path)
        for method, path, response_model in _walk(routes, prefix)
        if method == "POST" and response_model is model
    }


def _census_problems(found: set[tuple[str, str]]) -> list[str]:
    problems = []
    if not found:
        problems.append("census discovered zero Flying V toolpath routes")
    for item in sorted(DECLARED - found):
        problems.append(f"missing {item[0]} {item[1]}")
    for item in sorted(found - DECLARED):
        problems.append(f"undeclared {item[0]} {item[1]}")
    return problems


def _function(source: str, name: str):
    for node in ast.walk(ast.parse(textwrap.dedent(source))):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    return None


def _import_modules(source: str, name: str) -> set[str]:
    fn = _function(source, name)
    if fn is None:
        return set()
    return {
        node.module
        for node in ast.walk(fn)
        if isinstance(node, ast.ImportFrom) and node.module
    }


def _call_names(source: str, name: str) -> set[str]:
    fn = _function(source, name)
    if fn is None:
        return set()
    names = set()
    for node in ast.walk(fn):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name):
            names.add(func.id)
        elif isinstance(func, ast.Attribute):
            names.add(func.attr)
    return names


def _refusal(client, path: str, **params):
    return client.post(path, params=params or None)


# -----------------------------------------------------------------------------
# Registry and identity
# -----------------------------------------------------------------------------

def test_flying_v_body_stays_review_required_and_unqualified():
    from app.cam.generator_readiness import (
        GENERATOR_READINESS,
        GeneratorReadiness,
    )

    record = GENERATOR_READINESS[KEY]
    assert record.readiness is GeneratorReadiness.REVIEW_REQUIRED
    assert record.permits_emission is False
    assert "cavity depth and placement" in record.reason
    assert "not wired" in record.reason
    assert record.exit_condition.startswith("Depth and placement validated")
    assert record.evidence == (
        "LTB-CAM-EXPOSURE-MATRIX_2026-09-20.md FV-1, FV-2, FV-4",
    )
    flying = [key for key in GENERATOR_READINESS if key.startswith("flying_v")]
    assert flying == [KEY]


def test_historical_pre_containment_counts_stay_in_the_module_note():
    import app.cam.generator_readiness as readiness

    note = inspect.getsource(readiness).split("class GeneratorReadiness", 1)[0]
    assert "394" in note and "117" in note and "337" in note
    assert "REVIEW_REQUIRED" in note


def test_four_flying_v_paths_reach_pocket_generator():
    import app.cam.flying_v as facade
    import app.cam.flying_v.pocket_generator as pocket

    for name in (
        "load_flying_v_spec",
        "generate_control_cavity_toolpath",
        "generate_neck_pocket_toolpath",
        "generate_pickup_cavity_toolpath",
    ):
        assert getattr(facade, name) is getattr(pocket, name)

    router_source = inspect.getsource(_router())
    body = importlib.import_module("app.routers.cam.guitar.body_gcode_router")
    body_source = inspect.getsource(body)

    assert _import_modules(router_source, "generate_control_cavity_toolpath") == {
        "app.cam.flying_v"
    }
    assert _import_modules(router_source, "generate_neck_pocket_toolpath") == {
        "app.cam.flying_v"
    }
    assert _import_modules(router_source, "generate_pickup_toolpath") == {
        "app.cam.flying_v"
    }
    body_imports = _import_modules(body_source, "generate_flying_v_body_gcode")
    assert body_imports == {"cam.flying_v"}
    assert first_statement_gate_key(body_source, "generate_flying_v_body_gcode") == KEY


def test_a_similar_handler_name_does_not_inherit_pocket_generator():
    source = textwrap.dedent(
        '''
        def generate_control_cavity_toolpath():
            _readiness_gate("flying_v_body")
            from app.cam.other_family import generate_control_cavity_toolpath as gen
            return gen()
        '''
    )
    assert _import_modules(source, "generate_control_cavity_toolpath") == {
        "app.cam.other_family"
    }


def test_p1_and_p2_readiness_records_are_unchanged():
    from app.cam.generator_readiness import GENERATOR_READINESS, GeneratorReadiness

    assert GENERATOR_READINESS["neck_pipeline_full"].readiness is GeneratorReadiness.BLOCKED
    assert GENERATOR_READINESS["neck_gcode_generator"].readiness is GeneratorReadiness.BLOCKED
    assert GENERATOR_READINESS["neck"].readiness is GeneratorReadiness.REVIEW_REQUIRED


def test_router_does_not_import_asset_or_manufacturing_output_authority():
    source = inspect.getsource(_router())
    assert "manufacturing_output_authority" not in source
    assert "require_manufacturing_authority" not in source
    for handler in HANDLERS:
        calls = _call_names(source, handler)
        assert not any(name.startswith("validate_") for name in calls)


def test_handlers_remain_safety_critical():
    source = inspect.getsource(_router())
    for handler in HANDLERS:
        fn = _function(source, handler)
        assert fn is not None
        rendered = [ast.dump(dec) for dec in fn.decorator_list]
        assert any("safety_critical" in item for item in rendered)


# -----------------------------------------------------------------------------
# Static order
# -----------------------------------------------------------------------------

def test_toolpath_handlers_open_on_the_readiness_gate():
    source = inspect.getsource(_router())
    for handler in HANDLERS:
        assert first_statement_gate_key(source, handler) == KEY


def test_ordered_handler_fixture_passes():
    source = textwrap.dedent(
        '''
        def generate_pickup_toolpath(pickup):
            """Admitted query."""
            _readiness_gate("flying_v_body")
            if pickup not in ("neck", "bridge", "both"):
                pickup = "both"
            return pickup
        '''
    )
    assert first_statement_gate_key(source, "generate_pickup_toolpath") == KEY


def test_misordered_handler_fails_the_guard():
    """Pickup normalization before the gate is not containment."""
    source = textwrap.dedent(
        '''
        def generate_pickup_toolpath(pickup):
            """Still documented."""
            if pickup not in ("neck", "bridge", "both"):
                pickup = "both"
            _readiness_gate("flying_v_body")
            return pickup
        '''
    )
    assert first_statement_gate_key(source, "generate_pickup_toolpath") is None


def test_gate_precedes_import_and_generator_call():
    source = inspect.getsource(_router())
    for handler in HANDLERS:
        fn = _function(source, handler)
        assert fn is not None
        body = list(fn.body)
        if (
            isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
        ):
            body = body[1:]
        assert isinstance(body[0], ast.Expr)
        assert isinstance(body[0].value, ast.Call)
        later = body[1:]
        assert any(isinstance(stmt, ast.ImportFrom) for stmt in later)
        assert _call_names(source, handler) >= {"_readiness_gate", "gen"}


# -----------------------------------------------------------------------------
# Runtime refusal
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("path", [CONTROL, NECK_POCKET, PICKUP])
def test_default_request_is_blocked_before_generation(client, path):
    response = _refusal(client, path)
    detail = response.json()["detail"]

    assert response.status_code == 422
    assert detail["code"] == "GENERATOR_READINESS_BLOCKED"
    assert detail["route"] == KEY
    assert detail["generator_readiness"] == "REVIEW_REQUIRED"
    assert program_records(response.headers["content-type"], response.content) == []
    disposition = response.headers.get("content-disposition") or ""
    assert "attachment" not in disposition.lower()
    assert "gcode" not in response.json()


def test_the_three_refusals_are_identical(client):
    details = [_refusal(client, path).json()["detail"] for path in (CONTROL, NECK_POCKET, PICKUP)]
    assert details[0] == details[1] == details[2]
    assert details[0]["route"] == KEY


def test_blocked_request_does_not_load_the_spec_or_call_a_generator(client, monkeypatch):
    import app.cam.flying_v as facade
    import app.cam.flying_v.pocket_generator as pocket

    calls = []

    def boom(*args, **kwargs):
        calls.append(args)
        raise AssertionError("Flying V generator ran during a blocked request")

    for module in (facade, pocket):
        for name in (
            "load_flying_v_spec",
            "generate_control_cavity_toolpath",
            "generate_neck_pocket_toolpath",
            "generate_pickup_cavity_toolpath",
        ):
            monkeypatch.setattr(module, name, boom)

    for path in (CONTROL, NECK_POCKET, PICKUP):
        response = _refusal(client, path, variant="original_1958", pickup="both")
        assert response.status_code == 422
    assert calls == []


def test_missing_record_fails_closed_as_unknown(client, monkeypatch):
    import app.cam.generator_readiness as readiness

    monkeypatch.delitem(readiness.GENERATOR_READINESS, KEY)
    response = _refusal(client, CONTROL)
    detail = response.json()["detail"]

    assert response.status_code == 422
    assert detail["code"] == "GENERATOR_READINESS_BLOCKED"
    assert detail["generator_readiness"] == "UNKNOWN"
    assert detail["route"] == KEY
    assert program_records(response.headers["content-type"], response.content) == []


def test_routes_stay_unauthenticated(client):
    """Containment did not add an auth dependency. Refusal is 422, not 401."""
    for path in (CONTROL, NECK_POCKET, PICKUP):
        response = _refusal(client, path)
        assert response.status_code == 422
        assert response.status_code != 401


def test_emitting_assertion_fails_without_a_test_only_lift(client):
    response = _refusal(client, CONTROL)

    def functional_assertion():
        assert response.status_code == 200
        assert "G0" in response.json()["gcode"]

    with pytest.raises(AssertionError):
        functional_assertion()
    assert response.status_code == 422
    assert response.json()["detail"]["route"] == KEY


def test_prose_in_the_refusal_is_not_a_program(client):
    response = _refusal(client, NECK_POCKET)
    assert program_records("application/json", response.content) == []


# -----------------------------------------------------------------------------
# Census
# -----------------------------------------------------------------------------

def test_live_census_is_exactly_the_three_toolpath_routes():
    from app.main import app

    found = _toolpath_posts(app.routes)
    assert _census_problems(found) == []
    assert found == DECLARED
    assert len(found) == 3

    schema = app.openapi()["paths"]
    for _method, path in DECLARED:
        assert "post" in schema[path]
    assert "get" in schema[SPEC]
    assert "post" in schema[VALIDATE]
    assert ("POST", SPEC) not in found
    assert ("POST", VALIDATE) not in found
    assert ("GET", SPEC) not in found
    assert ("POST", BODY_GCODE) not in found


def test_suffix_discovery_cannot_see_the_toolpath_routes():
    from app.main import app

    suffix = {
        path
        for path, ops in app.openapi()["paths"].items()
        if path.startswith("/api/cam/guitar/") and "post" in ops and path.endswith("/gcode")
    }
    assert CONTROL not in suffix
    assert NECK_POCKET not in suffix
    assert PICKUP not in suffix
    assert BODY_GCODE in suffix


def test_synthetic_stealth_route_is_discovered_without_gcode_in_the_path():
    from fastapi import APIRouter

    model = _router().ToolpathResponse
    stealth = APIRouter()

    @stealth.post("/toolpath/stealth", response_model=model)
    def stealth_toolpath():
        return {"ok": True, "gcode": "G0 X0", "operation": "stealth"}

    found = _toolpath_posts(stealth.routes, prefix=PREFIX)
    stealth_path = f"{PREFIX}/toolpath/stealth"
    assert found == {("POST", stealth_path)}
    assert "gcode" not in "/toolpath/stealth"
    assert _census_problems(DECLARED | found) == [f"undeclared POST {stealth_path}"]


def test_empty_missing_and_added_censuses_fail():
    missing = DECLARED - {("POST", PICKUP)}
    added = DECLARED | {("POST", f"{PREFIX}/toolpath/extra")}
    assert any(item.startswith("zero") or "zero" in item for item in _census_problems(set()))
    assert _census_problems(missing) == [f"missing POST {PICKUP}"]
    assert _census_problems(added) == [f"undeclared POST {PREFIX}/toolpath/extra"]


def test_this_module_defines_no_autouse_fixture():
    tree = ast.parse(inspect.getsource(importlib.import_module(__name__)))
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        for dec in node.decorator_list:
            if not isinstance(dec, ast.Call):
                continue
            for keyword in dec.keywords:
                assert not (
                    keyword.arg == "autouse"
                    and isinstance(keyword.value, ast.Constant)
                    and keyword.value.value is True
                ), node.name


# -----------------------------------------------------------------------------
# Boundaries that must keep working
# -----------------------------------------------------------------------------

def test_spec_route_still_returns_the_cavity_summary(client):
    response = client.get(SPEC)
    body = response.json()
    assert response.status_code == 200
    assert body["variant"] == "original_1958"
    assert body["neck_pocket_depth_mm"] == 19.0
    assert "gcode" not in body


def test_validate_route_is_not_readiness_blocked(client):
    response = client.post(
        VALIDATE,
        json={
            "gcode": "G1 Z-19.0 F600\n",
            "operation": "neck_pocket",
            "use_preflight": False,
        },
    )
    body = response.json()
    assert response.status_code == 200
    assert body["operation"] == "neck_pocket"
    assert "GENERATOR_READINESS_BLOCKED" not in response.text
