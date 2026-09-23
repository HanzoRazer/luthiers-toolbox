"""Proof hardening for LTB-REMEDIATE-P2. Tests only.

The production handlers on the merged P-2 tree already refuse. These tests
make the regression proof durable: gate order by AST, a program detector that
reads JSON fields and attachment bytes, a five-route census, and an
implementation-to-readiness map.

Nothing here qualifies a generator or drives a machine.
"""
from __future__ import annotations

import ast
import inspect
import json
import re
import textwrap
from collections import defaultdict
from dataclasses import dataclass

import pytest

pytestmark = pytest.mark.allow_missing_request_id

GENERATE = "/api/neck/gcode/generate"
DOWNLOAD = "/api/neck/gcode/download"
P2_KEY = "neck_gcode_generator"

#: The five neck program routes. Geometry helpers such as
#: ``/api/neck/generate`` are a different surface and are not in this set.
DECLARED_NECK_PROGRAM_ROUTES = {
    ("POST", "/api/cam/guitar/{model_id}/neck/gcode"),
    ("POST", "/api/neck/gcode/generate"),
    ("POST", "/api/neck/gcode/download"),
    ("POST", "/api/cam-workspace/neck/generate-full"),
    ("POST", "/api/cam-workspace/neck/generate/{op}"),
}

_CONVERTER = re.compile(r"\{([^{}:]+):[^{}]+\}")
_COMMAND = re.compile(r"[GM]\d+", re.IGNORECASE)
_LINE_NUMBER = re.compile(r"N\d+", re.IGNORECASE)
_COMMENT = re.compile(r"\([^)]*\)")
_PROSE_KEYS = {"reason", "evidence", "detail", "message", "exit_condition"}
_PROGRAM_KEYS = {"gcode"}


def _normalize_path(path: str) -> str:
    return _CONVERTER.sub(r"{\1}", path)


def _is_neck_program_route(path: str, methods: set) -> bool:
    """Routes this census accounts for. Not every URL that mentions a neck."""
    if "POST" not in methods:
        return False
    if path.endswith("/neck/gcode") or "/neck/gcode/" in path:
        return True
    return path.startswith("/api/cam-workspace/neck/generate")


# -----------------------------------------------------------------------------
# Gate order (AST)
# -----------------------------------------------------------------------------

def _first_executable(fn: ast.AST):
    body = list(getattr(fn, "body", []))
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        body = body[1:]
    return body[0] if body else None


def _find_function(tree: ast.AST, name: str):
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    return None


def first_statement_gate_key(source: str, fn_name: str) -> str | None:
    """Readiness key if that call is the function's first executable statement.

    A gate later in the body does not count. Docstrings are not executable.
    """
    fn = _find_function(ast.parse(textwrap.dedent(source)), fn_name)
    if fn is None:
        return None
    stmt = _first_executable(fn)
    if not isinstance(stmt, ast.Expr) or not isinstance(stmt.value, ast.Call):
        return None
    call = stmt.value
    func = call.func
    if not isinstance(func, ast.Name) or func.id != "_readiness_gate":
        return None
    if len(call.args) != 1 or not isinstance(call.args[0], ast.Constant):
        return None
    value = call.args[0].value
    return value if isinstance(value, str) else None


def test_p2_handlers_open_on_the_readiness_gate():
    import app.routers.neck.gcode_router as module

    source = inspect.getsource(module)
    assert first_statement_gate_key(source, "generate_neck_gcode") == P2_KEY
    assert first_statement_gate_key(source, "download_neck_gcode") == P2_KEY


def test_an_ordered_handler_fixture_passes_the_guard():
    source = (
        "def generate_neck_gcode(req):\n"
        '    """Admitted body."""\n'
        '    _readiness_gate("neck_gcode_generator")\n'
        "    return req\n"
    )
    assert first_statement_gate_key(source, "generate_neck_gcode") == P2_KEY


def test_a_misordered_handler_fails_the_guard():
    """Work before the gate must not look contained."""
    source = (
        "def download_neck_gcode(req):\n"
        '    """Still documented."""\n'
        "    result = generate_neck_gcode(req)\n"
        '    _readiness_gate("neck_gcode_generator")\n'
        "    return result\n"
    )
    assert first_statement_gate_key(source, "download_neck_gcode") is None


# -----------------------------------------------------------------------------
# Program detector
# -----------------------------------------------------------------------------

def command_token(line: str) -> str | None:
    """First G/M command token on a line. Prose and N-words are not commands."""
    stripped = _COMMENT.sub(" ", line).strip()
    if not stripped or stripped.startswith(";"):
        return None
    for token in stripped.split():
        if _LINE_NUMBER.fullmatch(token):
            continue
        match = _COMMAND.fullmatch(token)
        if match:
            return match.group(0).upper()
        return None
    return None


def records_in_program_text(text: str) -> list[str]:
    return [token for line in text.splitlines() if (token := command_token(line))]


def records_in_json(node, key: str | None = None) -> list[str]:
    """Program records in program-bearing fields. Prose keys are not entered."""
    found: list[str] = []
    if isinstance(node, dict):
        for child_key, child in node.items():
            if child_key in _PROSE_KEYS:
                continue
            found.extend(records_in_json(child, child_key))
    elif isinstance(node, list):
        for child in node:
            found.extend(records_in_json(child, key))
    elif isinstance(node, str) and key in _PROGRAM_KEYS:
        found.extend(records_in_program_text(node))
    return found


def program_records(content_type: str, body: bytes) -> list[str]:
    if "json" in content_type.lower():
        return records_in_json(json.loads(body.decode()))
    return records_in_program_text(body.decode())


def test_detector_recognizes_g0_g1_and_m3():
    text = "G0 X0 Y0\nG1 Z-1.0 F10\nM3\n"
    assert records_in_program_text(text) == ["G0", "G1", "M3"]
    attachment = program_records("text/x-gcode", text.encode())
    assert attachment == ["G0", "G1", "M3"]


def test_detector_ignores_prose_that_quotes_gcode():
    payload = {
        "detail": {
            "code": "GENERATOR_READINESS_BLOCKED",
            "reason": "G0 rapids and G1 feeds and M3 remain unqualified.",
            "evidence": ["G0 Z-1\nM3"],
            "message": "see G1",
            "exit_condition": "quote G0 until qualified",
        }
    }
    assert records_in_json(payload) == []


def test_detector_reads_escaped_newlines_inside_json():
    raw = '{"gcode": "G0 X0 Y0\\nG1 Z-1.0 F10\\nM3\\n"}'
    assert re.search(r"(?m)^\s*[GM]\d", raw) is None
    assert program_records("application/json", raw.encode()) == ["G0", "G1", "M3"]


@pytest.mark.parametrize("route", [GENERATE, DOWNLOAD])
def test_blocked_responses_carry_no_program_records(client, route):
    response = client.post(route, json={})
    records = program_records(response.headers["content-type"], response.content)
    disposition = response.headers.get("content-disposition") or ""

    assert response.status_code == 422
    assert records == []
    assert "attachment" not in disposition.lower()


def test_schema_invalid_body_never_enters_the_handler(client):
    """Pydantic rejects a wrong type before the handler, and before the gate.

    ``scale_length`` is ``float | None``. A string is schema-invalid. The
    refusal is FastAPI's validation error, not ``GENERATOR_READINESS_BLOCKED``.
    """
    response = client.post(GENERATE, json={"scale_length": "not-a-number"})
    detail = response.json()["detail"]

    assert response.status_code == 422
    assert isinstance(detail, list)
    assert response.json().get("code") != "GENERATOR_READINESS_BLOCKED"


# -----------------------------------------------------------------------------
# Census
# -----------------------------------------------------------------------------

@dataclass(frozen=True)
class ResolvedRoute:
    method: str
    path: str
    endpoint: object


@dataclass(frozen=True)
class UnresolvedRoute:
    type_name: str
    prefix: str


def walk_routes(routes, prefix: str = ""):
    """Resolved routes plus route objects the walker could not classify."""
    resolved: list[ResolvedRoute] = []
    unresolved: list[UnresolvedRoute] = []
    for route in routes:
        if type(route).__name__ == "_IncludedRouter":
            context = getattr(route, "include_context", None)
            original = getattr(route, "original_router", None)
            if original is None:
                unresolved.append(UnresolvedRoute("_IncludedRouter", prefix))
                continue
            child_prefix = prefix + (getattr(context, "prefix", "") or "")
            child_resolved, child_unresolved = walk_routes(original.routes, child_prefix)
            resolved.extend(child_resolved)
            unresolved.extend(child_unresolved)
            continue
        path = getattr(route, "path", None)
        if path is None:
            unresolved.append(UnresolvedRoute(type(route).__name__, prefix))
            continue
        methods = getattr(route, "methods", None) or {"GET"}
        full = _normalize_path(prefix + path)
        endpoint = getattr(route, "endpoint", None)
        for method in methods:
            resolved.append(ResolvedRoute(method, full, endpoint))
    return resolved, unresolved


def neck_program_routes(routes) -> tuple[set[tuple[str, str]], list[UnresolvedRoute]]:
    resolved, unresolved = walk_routes(routes)
    found = {
        (route.method, route.path)
        for route in resolved
        if _is_neck_program_route(route.path, {route.method})
    }
    return found, unresolved


def census_problems(found: set[tuple[str, str]], declared: set[tuple[str, str]]) -> list[str]:
    if not found and not declared:
        return ["census is empty"]
    problems = [f"missing {method} {path}" for method, path in sorted(declared - found)]
    problems.extend(
        f"undeclared {method} {path}" for method, path in sorted(found - declared)
    )
    if not found:
        problems.append("census discovered zero neck program routes")
    return problems


def _live_app():
    from app.main import app

    return app


def test_unresolved_route_objects_are_reported():
    class Mystery:
        pass

    resolved, unresolved = walk_routes([Mystery()])
    assert resolved == []
    assert [item.type_name for item in unresolved] == ["Mystery"]


def test_the_five_neck_program_routes_are_discovered():
    app = _live_app()
    found, unresolved = neck_program_routes(app.routes)
    openapi_found = {
        ("POST", _normalize_path(path))
        for path, operations in app.openapi()["paths"].items()
        if _is_neck_program_route(path, {method.upper() for method in operations})
    }

    assert unresolved == []
    assert found == DECLARED_NECK_PROGRAM_ROUTES
    assert openapi_found == DECLARED_NECK_PROGRAM_ROUTES
    assert census_problems(found, DECLARED_NECK_PROGRAM_ROUTES) == []
    assert len(found) == 5


def test_an_added_neck_gcode_route_fails_the_census():
    extra = DECLARED_NECK_PROGRAM_ROUTES | {("POST", "/api/neck/gcode/extra")}
    problems = census_problems(extra, DECLARED_NECK_PROGRAM_ROUTES)
    assert problems == ["undeclared POST /api/neck/gcode/extra"]


def test_a_missing_neck_route_fails_the_census():
    short = DECLARED_NECK_PROGRAM_ROUTES - {("POST", DOWNLOAD)}
    problems = census_problems(short, DECLARED_NECK_PROGRAM_ROUTES)
    assert problems == [f"missing POST {DOWNLOAD}"]


def test_an_empty_census_fails():
    assert "zero" in " ".join(census_problems(set(), DECLARED_NECK_PROGRAM_ROUTES))


# -----------------------------------------------------------------------------
# Identity: handler -> implementation -> readiness key
# -----------------------------------------------------------------------------

@dataclass(frozen=True)
class IdentityRow:
    handler: str
    implementation: str
    readiness_key: str | None


def implementation_of(source: str, fn_name: str) -> str:
    fn = _find_function(ast.parse(textwrap.dedent(source)), fn_name)
    if fn is None:
        return "unresolved"
    calls: set[str] = set()
    names: set[str] = set()
    for node in ast.walk(fn):
        if isinstance(node, ast.Name):
            names.add(node.id)
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                calls.add(func.id)
            elif isinstance(func, ast.Attribute):
                calls.add(func.attr)
    constructors = calls & {"NeckPipeline", "NeckGCodeGenerator"}
    if len(constructors) > 1:
        return "ambiguous"
    if "NeckPipeline" in constructors:
        return "NeckPipeline"
    if "NeckGCodeGenerator" in constructors or "generate_neck_gcode" in calls:
        return "NeckGCodeGenerator"
    if "gcode_lines" in names:
        return "inline"
    return "unresolved"


def shared_key_problems(rows: list[IdentityRow]) -> list[str]:
    impls_for_key: dict[str | None, set[str]] = defaultdict(set)
    for row in rows:
        impls_for_key[row.readiness_key].add(row.implementation)
    return [
        f"{key} governs {sorted(impls)}"
        for key, impls in sorted(impls_for_key.items(), key=lambda item: str(item[0]))
        if len(impls) > 1
    ]


def _identity_rows() -> list[IdentityRow]:
    resolved, _unresolved = walk_routes(_live_app().routes)
    rows = []
    for route in resolved:
        if (route.method, route.path) not in DECLARED_NECK_PROGRAM_ROUTES:
            continue
        endpoint = route.endpoint
        source = inspect.getsource(endpoint)
        handler = endpoint.__name__
        rows.append(
            IdentityRow(
                handler=handler,
                implementation=implementation_of(source, handler),
                readiness_key=first_statement_gate_key(source, handler),
            )
        )
    return rows


_EXPECTED_IDENTITY = {
    "generate_neck_gcode": ("NeckGCodeGenerator", P2_KEY),
    "download_neck_gcode": ("NeckGCodeGenerator", P2_KEY),
    "generate_guitar_neck_gcode": ("inline", "neck"),
    "generate_full_neck": ("NeckPipeline", "neck_pipeline_full"),
    "generate_neck_op": ("NeckPipeline", "neck_pipeline_full"),
}


def test_handler_implementation_and_readiness_key_stay_distinct():
    rows = _identity_rows()
    observed = {row.handler: (row.implementation, row.readiness_key) for row in rows}

    assert observed == _EXPECTED_IDENTITY
    assert shared_key_problems(rows) == []
    assert {row.implementation for row in rows} == {
        "NeckGCodeGenerator",
        "inline",
        "NeckPipeline",
    }


def test_two_implementations_cannot_share_a_readiness_key():
    rows = [
        IdentityRow("generate_neck_gcode", "NeckGCodeGenerator", P2_KEY),
        IdentityRow("generate_full_neck", "NeckPipeline", P2_KEY),
    ]
    assert shared_key_problems(rows) == [f"{P2_KEY} governs ['NeckGCodeGenerator', 'NeckPipeline']"]


# -----------------------------------------------------------------------------
# Lift negative control
# -----------------------------------------------------------------------------

def test_emitting_functional_assertion_fails_without_the_lift(client):
    """The smoke suite's 200/program assertion fails when the gate stays closed.

    ``neck_gcode_gate_lifted`` is test-only. It is not qualification evidence.
    This test does not lift the gate.
    """
    response = client.post(GENERATE, json={})

    def functional_assertion():
        assert response.status_code == 200
        data = response.json()
        assert "gcode" in data
        assert "G0" in data["gcode"] or "G1" in data["gcode"]

    with pytest.raises(AssertionError):
        functional_assertion()
    assert response.status_code == 422
    assert response.json()["detail"]["route"] == P2_KEY
