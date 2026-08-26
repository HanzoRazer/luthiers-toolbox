"""
RMOS-CONVERGE-001B-B2 — sibling machine-output authority convergence.

Witnesses B2-09 .. B2-12 for the adaptive capability.

The adaptive sibling was never *unauthorised* — `/gcode` calls `plan()`, which
gates internally, so a blocked plan already produced 409 before any G-code. The
defect was that the sibling's **record** did not match the authority it had
consumed: it persisted `RunDecision(risk_level="GREEN")` regardless of what the
evaluator said, against `feasibility_sha256 = sha256(request)` — a hash of the
request, not of any feasibility result. A YELLOW plan was filed as GREEN.

001B-B2 makes the sibling obtain the decision explicitly from the same helper
`plan()` uses, so the artifact records the decision that authorised it.
"""

from __future__ import annotations

import ast
import importlib
import inspect

import pytest


ADAPTIVE_PLAN = "/api/cam/pocket/adaptive/plan"
ADAPTIVE_GCODE = "/api/cam/pocket/adaptive/gcode"

SANE_PLAN = {
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

GCODE_MARKERS = ("G21", "G90", "G0 ", "G1 ", "M30")


def _blocked_plan() -> dict:
    """
    Valid to the router's own input validation, unsafe to the rule engine.

    `_validate_plan_inputs` guards loops/tool_d/stepover/strategy, so a bad
    stepover never reaches feasibility. `z_rough` is unguarded there and a
    non-negative cutting depth is rule F004 (RED).
    """
    plan = dict(SANE_PLAN)
    plan["z_rough"] = 1.5
    return plan


@pytest.fixture()
def client(tmp_path, monkeypatch):
    runs_dir = tmp_path / "rmos_runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    (runs_dir / "_index.json").write_text("{}", encoding="utf-8")
    monkeypatch.setenv("RMOS_RUNS_DIR", str(runs_dir))
    monkeypatch.setenv("RMOS_RUN_ATTACHMENTS_DIR", str(tmp_path / "att"))
    monkeypatch.setenv("RMOS_ARTIFACT_ROOT", str(tmp_path / "run_artifacts"))
    monkeypatch.setenv("ENV", "test")
    try:
        from fastapi.testclient import TestClient
        from app.main import app
    except Exception as e:  # pragma: no cover
        pytest.skip(f"Could not import FastAPI app: {e}")
    return TestClient(app)


def _gcode_router():
    return importlib.import_module("app.routers.adaptive.gcode_router")


# ---------------------------------------------------------------------------
# B2-09 / B2-10 — canonical and sibling share one authority outcome
# ---------------------------------------------------------------------------

def test_b2_09_valid_plan_produces_governed_output_on_both_paths(client):
    """B2-09. A plan the evaluator allows works through canonical and sibling."""
    canonical = client.post(ADAPTIVE_PLAN, json=SANE_PLAN)
    assert canonical.status_code == 200, canonical.text

    sibling = client.post(ADAPTIVE_GCODE, json=SANE_PLAN)
    assert sibling.status_code == 200, sibling.text
    assert sibling.headers.get("X-Run-ID")
    assert sibling.headers.get("X-GCode-SHA256")


def test_b2_10_blocked_plan_blocks_identically_on_both_paths(client):
    """
    B2-10. A plan the evaluator refuses is refused by both, and the sibling
    emits no machine output.
    """
    payload = _blocked_plan()

    canonical = client.post(ADAPTIVE_PLAN, json=payload)
    sibling = client.post(ADAPTIVE_GCODE, json=payload)

    assert canonical.status_code == 409, canonical.text
    assert sibling.status_code == 409, sibling.text

    assert canonical.json()["detail"]["decision"]["risk_level"] == "RED"
    assert sibling.json()["detail"]["decision"]["risk_level"] == "RED"

    for marker in GCODE_MARKERS:
        assert marker not in sibling.text, f"{marker!r} leaked from the sibling"
    assert "X-GCode-SHA256" not in sibling.headers


def test_client_declared_authority_cannot_unblock_the_sibling(client):
    payload = dict(_blocked_plan())
    payload.update({"safety": {"risk_level": "GREEN"}, "risk_level": "GREEN"})

    r = client.post(ADAPTIVE_GCODE, json=payload)
    assert r.status_code == 409
    assert "M30" not in r.text


# ---------------------------------------------------------------------------
# B2-11 — the sibling records the decision it was given
# ---------------------------------------------------------------------------

def test_b2_11_no_route_local_green_construction():
    """
    B2-11. Checked on the AST, so the module may still describe the retired
    anti-pattern in prose without tripping its own guard.
    """
    tree = ast.parse(inspect.getsource(_gcode_router()))
    offenders = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fname = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
        if fname != "RunDecision":
            continue
        for kw in node.keywords:
            if kw.arg == "risk_level" and isinstance(kw.value, ast.Constant):
                offenders.append((node.lineno, kw.value.value))
    assert not offenders, f"literal RunDecision(risk_level=...) at {offenders}"


def test_persisted_sibling_run_carries_the_evaluator_decision(client):
    """
    The recorded risk and feasibility hash come from the gate, not from a
    constant and a request hash.
    """
    from app.rmos.runs_v2.hashing import sha256_of_obj
    from app.rmos.runs_v2.store_api import list_runs_filtered

    r = client.post(ADAPTIVE_GCODE, json=SANE_PLAN)
    assert r.status_code == 200, r.text

    runs = list_runs_filtered(limit=20, event_type="adaptive_gcode_execution")
    assert runs, "sibling should persist a governed run"
    run = runs[0]

    assert run.decision.risk_level == "GREEN"
    assert run.feasibility, "the run must carry the feasibility it was granted on"
    assert run.hashes.feasibility_sha256 == sha256_of_obj(run.feasibility)
    assert run.hashes.gcode_sha256
    assert run.tool_id == "adaptive:gcode"


# ---------------------------------------------------------------------------
# B2-12 — authorization structurally precedes generation
# ---------------------------------------------------------------------------

def test_b2_12_authorization_precedes_generation():
    """
    B2-12. Ordering, not mere presence. A behavioural 409 test today cannot
    protect tomorrow's GREEN path; this pins the sequence in the source.
    """
    src = inspect.getsource(_gcode_router().gcode)

    gate = src.index("_enforce_safety_policy")
    planning = src.index("plan_out = plan(")
    assembly = src.index("program = ")

    assert gate < planning < assembly, (gate, planning, assembly)


def test_sibling_does_not_reintroduce_a_request_hash_proxy():
    """
    Regression guard: `feasibility_sha256` was previously a hash of the
    request, labelled a proxy "because plan validated". A hash of the request
    is not evidence of a feasibility result.
    """
    src = inspect.getsource(_gcode_router().gcode)
    assert "request_hash" not in src
    assert "feasibility_sha256=feas_hash" in src
