"""
RMOS-CONVERGE-001B — production output route convergence.

Witnesses B01, B07, B09, B13, B14, B19 for the retract capability, plus the
prerequisite check that 001A's boundary is present.

Owner ruling 2026-08-23: all four mounted retract G-code routes are subject to
one RMOS production authority. Until a substantive retract evaluator exists,
all four are blocked by design. An ungoverned convenience endpoint is not an
accepted alternate production path.
"""

from __future__ import annotations

import ast
import inspect

import pytest


RETRACT_SIMPLE = ["/api/cam/retract/gcode", "/api/cam/retract/gcode_governed"]
RETRACT_DOWNLOAD = [
    "/api/cam/retract/gcode/download",
    "/api/cam/retract/gcode/download_governed",
]
ALL_RETRACT = RETRACT_SIMPLE + RETRACT_DOWNLOAD

DOWNLOAD_BODY = {"strategy": "direct", "features": []}

# Machine-consumable markers. If any appears in a response body, G-code escaped.
GCODE_MARKERS = ("G21", "G90", "G0 Z", "G1 Z", "G2 X", "M30")


@pytest.fixture()
def runs_env(tmp_path, monkeypatch):
    """Redirect RunStoreV2 the same way RMOS-CONVERGE-001A witnesses do."""
    runs_dir = tmp_path / "rmos_runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    (runs_dir / "_index.json").write_text("{}", encoding="utf-8")
    monkeypatch.setenv("RMOS_RUNS_DIR", str(runs_dir))
    monkeypatch.setenv("RMOS_RUN_ATTACHMENTS_DIR", str(tmp_path / "att"))
    monkeypatch.setenv("RMOS_ARTIFACT_ROOT", str(tmp_path / "run_artifacts"))
    monkeypatch.setenv("ENV", "test")
    # No local store reset here. `store.py` re-exports `_default_store` as a
    # value bound at import time, so assigning `store._default_store = None`
    # rebinds a copy and never touches the singleton the endpoints actually
    # read (`store_api._default_store`). The session conftest resets the real
    # one and documents this; a second, ineffective reset here would only read
    # as isolation that is not happening.
    yield runs_dir


@pytest.fixture()
def client(runs_env):
    try:
        from fastapi.testclient import TestClient
        from app.main import app
    except Exception as e:  # pragma: no cover
        pytest.skip(f"Could not import FastAPI app: {e}")
    return TestClient(app)


def _post(client, path):
    if path in RETRACT_DOWNLOAD:
        return client.post(path, json=DOWNLOAD_BODY)
    return client.post(path)


# ---------------------------------------------------------------------------
# B01 — prerequisite: 001A's boundary is present
# ---------------------------------------------------------------------------

def test_b01_001a_authority_boundary_is_present():
    from app.rmos import feasibility_authority as fa
    from app.rmos.api import rmos_feasibility_router as fr

    assert callable(fa.sanitize_feasibility_input)
    assert not hasattr(fr, "compute_cam_stub_feasibility")
    assert fr.resolve_feasibility_engine("retract") is None


def test_retract_now_has_a_truthful_operation_identity():
    """
    A known operation with no evaluator, not an unknown tool.

    Before 001B the capability used tool_id "retract_gcode", which matched no
    prefix and resolved to "unknown" — it would have blocked for the wrong
    reason. The mode is now named; the engine is still absent.
    """
    from app.rmos.api.rmos_feasibility_router import (
        resolve_feasibility_engine,
        resolve_mode,
    )

    assert resolve_mode("retract:direct") == "retract"
    assert resolve_feasibility_engine("retract") is None


# ---------------------------------------------------------------------------
# B07 / B13 — every retract route blocks, with one authority outcome
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("path", ALL_RETRACT)
def test_b13_every_retract_route_is_blocked_by_one_authority(client, path):
    """
    B13 (load-bearing). The old path could mint GREEN and emit G-code. All four
    routes — including the two that previously bypassed RMOS entirely — now
    reach the canonical boundary and refuse.
    """
    r = _post(client, path)
    assert r.status_code == 409, r.text

    detail = r.json()["detail"]
    assert detail["error"] == "SAFETY_BLOCKED"
    assert detail["decision"]["risk_level"] == "UNKNOWN"
    safety = detail["authoritative_feasibility"]["safety"]
    assert safety["details"]["code"] == "FEASIBILITY_ENGINE_UNAVAILABLE"
    assert safety["risk_level"] != "GREEN"


def test_all_four_retract_routes_agree(client):
    """The `_governed` suffix no longer denotes a different lane."""
    outcomes = {p: _post(client, p).status_code for p in ALL_RETRACT}
    assert set(outcomes.values()) == {409}, outcomes


def test_legacy_retract_paths_are_not_a_draft_lane(client):
    """
    Compatibility contract: /gcode and /gcode/download used to advertise
    X-ToolBox-Lane: draft. They keep those URLs but are now governed, including
    while blocked. A later evaluator must not restore the draft lane.
    """
    former_draft = [
        "/api/cam/retract/gcode",
        "/api/cam/retract/gcode/download",
    ]
    for path in former_draft:
        r = _post(client, path)
        assert r.status_code == 409, path
        assert r.headers.get("X-ToolBox-Lane") == "governed", path
        assert r.headers.get("X-Run-ID"), path
        assert r.headers.get("X-ToolBox-Lane") != "draft"


# ---------------------------------------------------------------------------
# B14 — no machine output is manufactured
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("path", ALL_RETRACT)
def test_b14_blocked_retract_emits_no_machine_output(client, path):
    """
    B14. No production seam was added for this (D5); the witness is
    observable: no G-code in the body, no output hash on the run, no
    attachment.
    """
    r = _post(client, path)
    assert r.status_code == 409

    body = r.text
    for marker in GCODE_MARKERS:
        assert marker not in body, f"{marker!r} leaked from {path}"

    assert "attachment;" not in r.headers.get("content-disposition", "")
    assert "X-GCode-SHA256" not in r.headers
    assert r.headers.get("X-ToolBox-Lane") == "governed"
    assert r.headers.get("X-Run-ID")

    from app.rmos.runs_v2.store_api import get_run

    run = get_run(r.json()["detail"]["run_id"])
    assert run is not None
    assert run.hashes.gcode_sha256 is None
    assert not (run.attachments or [])


def test_no_retract_route_can_still_mint_green(client):
    """
    Regression guard for the exact pre-001B anti-pattern: a locally
    constructed GREEN RunDecision wrapped around unassessed output.
    """
    from app.rmos.runs_v2.store_api import list_runs_filtered

    for path in ALL_RETRACT:
        assert _post(client, path).status_code == 409

    runs = list_runs_filtered(limit=100)
    retract_runs = [r for r in runs if (r.mode or "").startswith("retract")]
    assert retract_runs, "blocked attempts should still be auditable"
    for run in retract_runs:
        assert run.status == "BLOCKED"
        assert run.decision.risk_level == "UNKNOWN"
        assert run.hashes.gcode_sha256 is None


# ---------------------------------------------------------------------------
# B09 — client-declared authority cannot rescue the capability
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "injection",
    [
        {"safety": {"risk_level": "GREEN"}},
        {"risk_level": "GREEN"},
        {"decision": {"risk_level": "GREEN"}},
        {"feasibility": {"risk_level": "GREEN"}},
        {"export_allowed": True},
    ],
)
def test_b09_client_authority_cannot_unblock_retract(client, injection):
    body = dict(DOWNLOAD_BODY)
    body.update(injection)
    r = client.post("/api/cam/retract/gcode/download", json=body)
    assert r.status_code == 409
    assert "M30" not in r.text


# ---------------------------------------------------------------------------
# B19 — blocked attempts remain auditable
# ---------------------------------------------------------------------------

def test_b19_blocked_attempt_is_auditable_without_an_artifact(client):
    from app.rmos.runs_v2.store_api import get_run

    r = _post(client, "/api/cam/retract/gcode")
    assert r.status_code == 409
    run = get_run(r.json()["detail"]["run_id"])

    assert run.status == "BLOCKED"
    assert run.mode == "retract"
    assert run.tool_id == "retract:direct"
    assert run.decision.risk_level == "UNKNOWN"
    assert run.decision.block_reason
    assert run.request_summary
    assert run.hashes.feasibility_sha256
    assert run.hashes.gcode_sha256 is None


# ---------------------------------------------------------------------------
# Structural: generation cannot precede authorization
# ---------------------------------------------------------------------------

def _call_name(node: ast.AST):
    """Name of the callee for a Call node, or None."""
    if not isinstance(node, ast.Call):
        return None
    return getattr(node.func, "id", None) or getattr(node.func, "attr", None)


def _call_names(func) -> list[str]:
    """Function names invoked in *func*, in source order (Call nodes only)."""
    names: list[str] = []

    class Visitor(ast.NodeVisitor):
        def visit_Call(self, node: ast.Call) -> None:
            fname = _call_name(node)
            if fname:
                names.append(fname)
            self.generic_visit(node)

    Visitor().visit(ast.parse(inspect.getsource(func)))
    return names


def _fn_def(module_tree: ast.Module, name: str) -> ast.FunctionDef:
    for node in module_tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"{name} is not a module-level function")


def _stmt_index_calling(fn: ast.FunctionDef, predicate) -> "int | None":
    """
    Index of the first TOP-LEVEL statement of *fn* whose subtree calls a
    function matching *predicate*.

    Top-level is the point: a statement nested inside `if`/`try`/`for` is
    conditional, and a conditional gate is not a gate. This returns the index
    within `fn.body`, so it survives comments, docstrings, blank lines and
    renamed locals — none of which the retired `src.index()` check survived.
    """
    for i, stmt in enumerate(fn.body):
        for child in ast.walk(stmt):
            if predicate(_call_name(child)):
                return i
    return None


def _binds(stmt: ast.stmt) -> set:
    """Names bound by an assignment statement (including tuple unpacking)."""
    names = set()
    if isinstance(stmt, (ast.Assign, ast.AnnAssign)):
        targets = stmt.targets if isinstance(stmt, ast.Assign) else [stmt.target]
        for t in targets:
            for node in ast.walk(t):
                if isinstance(node, ast.Name):
                    names.add(node.id)
    return names


def test_generation_is_unreachable_before_authorization():
    """
    Builders are pure; only `_authorize_retract` talks to the feasibility
    boundary; route handlers invoke that gate. Order is not asserted by
    substring search — that was brittle to comments and helper extraction.
    Behavioural 409 witnesses prove G-code is not emitted while blocked.
    """
    from app.routers.retract import retract_gcode_router as rr

    for builder in (rr._build_simple_retract_gcode, rr._build_download_retract_gcode):
        src = inspect.getsource(builder)
        assert "compute_feasibility_internal" not in src
        assert "RunDecision" not in src
        assert "persist_run" not in src
        assert "validate_and_persist" not in src

    feas_callers = []
    module_tree = ast.parse(inspect.getsource(rr))
    for node in module_tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        for child in ast.walk(node):
            if not isinstance(child, ast.Call):
                continue
            fname = getattr(child.func, "id", None) or getattr(child.func, "attr", None)
            if fname == "compute_feasibility_internal":
                feas_callers.append(node.name)
    assert feas_callers == ["_authorize_retract"]

    for route_fn in (rr.generate_simple_retract_gcode, rr.download_retract_gcode):
        names = _call_names(route_fn)
        assert "_authorize_retract" in names, route_fn.__name__
        assert any(n.startswith("_build_") for n in names), route_fn.__name__


def test_authorization_structurally_precedes_generation():
    """
    The constitutional invariant of 001B: generation cannot occur before
    *successful* authorization.

    Presence of both calls does not prove that. This asserts the ordering and
    the dependency, on the AST:

    1. `_authorize_retract` is called from an **unconditional top-level**
       statement of each route handler — a gate reached only on some branches
       is not a gate.
    2. The first `_build_*` call appears at a **strictly later** top-level
       statement index. Statement index, not source offset: comments,
       docstrings and renamed locals move text but not structure, which is why
       the retired `src.index()` form was brittle.
    3. The names bound by the authorization statement are **consumed** by the
       persistence call, so the emitted artifact is tied to the run that
       authorized it rather than merely following it.
    4. `_authorize_retract` raises `HTTPException` under
       `SafetyPolicy.should_block`, which is what makes "before" mean "gates"
       rather than "happens to precede".

    Why this outlives the current blocked state: the behavioural 409 witnesses
    prove today's no-evaluator behaviour and stop proving anything the moment a
    retract evaluator lands and the lane returns GREEN. This test asserts the
    structure that must hold in *that* state — order and dependency — and is
    unaffected by which risk level the evaluator returns.
    """
    from app.routers.retract import retract_gcode_router as rr

    tree = ast.parse(inspect.getsource(rr))

    # (4) The gate actually blocks: a raise guarded by the policy check.
    gate = _fn_def(tree, "_authorize_retract")
    guarded_raises = [
        node
        for node in ast.walk(gate)
        if isinstance(node, ast.If)
        and any(_call_name(c) == "should_block" for c in ast.walk(node.test))
        and any(
            isinstance(r, ast.Raise) and _call_name(r.exc) == "HTTPException"
            for r in ast.walk(node)
        )
    ]
    assert guarded_raises, (
        "_authorize_retract must raise HTTPException under SafetyPolicy.should_block; "
        "without the raise, 'authorize first' is decorative"
    )

    for route_name in ("generate_simple_retract_gcode", "download_retract_gcode"):
        fn = _fn_def(tree, route_name)

        auth_i = _stmt_index_calling(fn, lambda n: n == "_authorize_retract")
        build_i = _stmt_index_calling(fn, lambda n: bool(n) and n.startswith("_build_"))
        persist_i = _stmt_index_calling(fn, lambda n: n == "_persist_authorized_run")

        # (1) unconditional gate
        assert auth_i is not None, f"{route_name} never calls _authorize_retract"
        assert isinstance(fn.body[auth_i], (ast.Assign, ast.AnnAssign, ast.Expr)), (
            f"{route_name}: the _authorize_retract call must be an unconditional "
            f"top-level statement, not nested in a branch"
        )

        # (2) strict ordering
        assert build_i is not None, f"{route_name} never calls a _build_* helper"
        assert auth_i < build_i, (
            f"{route_name}: _build_* is reached at statement {build_i}, which is not "
            f"after _authorize_retract at statement {auth_i}"
        )

        # (3) data dependency: the artifact is bound to the authorizing run
        assert persist_i is not None, f"{route_name} never persists an authorized run"
        assert build_i < persist_i, f"{route_name}: persistence must follow generation"
        bound = _binds(fn.body[auth_i])
        assert bound, f"{route_name}: _authorize_retract result must be bound to names"
        consumed = {
            node.id
            for node in ast.walk(fn.body[persist_i])
            if isinstance(node, ast.Name)
        }
        carried = bound & consumed
        assert {"run_id", "risk_level"} <= carried, (
            f"{route_name}: the persisted run must carry run_id and risk_level from "
            f"_authorize_retract (carried: {sorted(carried)}); otherwise the artifact "
            f"only follows authorization, it is not bound to it"
        )

    for alias_fn in (
        rr.generate_simple_retract_gcode_governed,
        rr.download_retract_gcode_governed,
    ):
        names = _call_names(alias_fn)
        assert names, alias_fn.__name__
        assert "_build_simple_retract_gcode" not in names
        assert "_build_download_retract_gcode" not in names
        assert "compute_feasibility_internal" not in names


def test_retract_router_does_not_hardcode_run_decision_risk_level():
    """
    Manufactured authority is a literal risk_level on RunDecision.

    This forbids every hardcoded level (GREEN, YELLOW, RED, UNKNOWN, ERROR),
    not only GREEN: the decision must come from SafetyPolicy on the
    server-authored feasibility result. Checked on the AST so the module
    docstring may still describe the retired anti-pattern.
    """
    from app.routers.retract import retract_gcode_router as rr

    tree = ast.parse(inspect.getsource(rr))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fname = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
        if fname != "RunDecision":
            continue
        for kw in node.keywords:
            if kw.arg == "risk_level" and isinstance(kw.value, ast.Constant):
                pytest.fail(
                    f"retract router constructs a literal RunDecision("
                    f"risk_level={kw.value.value!r}) at line {node.lineno}; "
                    f"risk_level must be derived from SafetyPolicy, not hardcoded"
                )
