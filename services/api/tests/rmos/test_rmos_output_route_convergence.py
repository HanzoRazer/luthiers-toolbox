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
def client(tmp_path, monkeypatch):
    runs_dir = tmp_path / "rmos_runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    (runs_dir / "_index.json").write_text("{}", encoding="utf-8")
    monkeypatch.setenv("RMOS_RUNS_DIR", str(runs_dir))
    monkeypatch.setenv("RMOS_RUN_ATTACHMENTS_DIR", str(tmp_path / "att"))
    monkeypatch.setenv("ENV", "test")
    try:
        from app.rmos.runs_v2 import store as runs_v2_store

        runs_v2_store._default_store = None
    except ImportError:
        pass
    try:
        from fastapi.testclient import TestClient
        from app.main import app
    except Exception as e:  # pragma: no cover
        pytest.skip(f"Could not import FastAPI app: {e}")
    yield TestClient(app)
    try:
        from app.rmos.runs_v2 import store as runs_v2_store

        runs_v2_store._default_store = None
    except ImportError:
        pass


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

def test_generation_is_unreachable_before_authorization():
    """
    The builders are pure and are called only after `_authorize_retract`
    returns, so blocking is structural rather than a matter of statement order.
    Before 001B every route built its G-code first and (in two cases) minted a
    run around it afterwards.
    """
    import inspect

    from app.routers.retract import retract_gcode_router as rr

    for builder in (rr._build_simple_retract_gcode, rr._build_download_retract_gcode):
        src = inspect.getsource(builder)
        assert "compute_feasibility_internal" not in src
        assert "RunDecision" not in src

    for route_fn in (rr.generate_simple_retract_gcode, rr.download_retract_gcode):
        src = inspect.getsource(route_fn)
        assert src.index("_authorize_retract") < src.index("_build_")

    # No route may construct its own GREEN decision. Checked on the AST rather
    # than the source text, so the module may still *describe* the retired
    # anti-pattern in its docstring without tripping the guard.
    import ast

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
                    f"risk_level={kw.value.value!r}) at line {node.lineno}"
                )
