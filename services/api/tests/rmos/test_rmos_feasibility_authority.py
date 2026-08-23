"""
RMOS-CONVERGE-001A - feasibility authority boundary.

Acceptance witnesses TC-01 .. TC-09, TC-22, TC-23.

These are born-from-the-defect tests. Before the cutover, a request body
carrying ``{"safety": {"risk_level": "GREEN"}}`` was echoed back by the
per-engine "test hook" and read by ``SafetyPolicy`` as the authoritative
decision; and every CAM mode without a real engine was authorized GREEN by
``compute_cam_stub_feasibility``. Both behaviours were reproduced on the
pre-fix tree before this file was written.

Feasibility injection here is done by monkeypatching the engine (dependency
injection), never by a production request field - see D2.
"""

from __future__ import annotations

import pytest

from app.rmos.api import rmos_feasibility_router as fr
from app.rmos.api.rmos_feasibility_router import (
    compute_feasibility_internal,
    resolve_feasibility_engine,
    resolve_mode,
)
from app.rmos.feasibility_authority import (
    AUTHORITY_KEYS,
    ENGINE_ERROR,
    ENGINE_UNAVAILABLE,
    NON_AUTHORITATIVE_KEY,
    sanitize_feasibility_input,
)
from app.rmos.policies import SafetyPolicy


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# A legitimate adaptive pocket plan: the rule engine evaluates it GREEN.
SANE_ADAPTIVE = {
    "tool_d": 6.0,
    "stepover": 0.45,
    "stepdown": 2.0,
    "z_rough": -1.5,
    "feed_xy": 1200.0,
    "safe_z": 5.0,
    "strategy": "Spiral",
    "climb": True,
    "smoothing": 0.5,
    "margin": 0.5,
    "machine_rapid": 3000.0,
    "loops": [{"pts": [[0, 0], [100, 0], [100, 60], [0, 60]]}],
}

# Same plan with a physically impossible stepover: rule F002 fires RED.
def _red_adaptive() -> dict:
    req = dict(SANE_ADAPTIVE)
    req["stepover"] = 1.5
    return req


def _risk(result: dict) -> str:
    return SafetyPolicy.extract_safety_decision(result).risk_level_str()


def _blocks(result: dict) -> bool:
    decision = SafetyPolicy.extract_safety_decision(result)
    return SafetyPolicy.should_block(decision.risk_level)


def _code(result: dict) -> str:
    return (result.get("safety") or {}).get("details", {}).get("code", "")


def _compute(tool_id: str, **extra) -> dict:
    req = {"tool_id": tool_id}
    req.update(extra)
    return compute_feasibility_internal(tool_id=tool_id, req=req, context="test")


# ---------------------------------------------------------------------------
# TC-01 / TC-02 - the server computes real verdicts
# ---------------------------------------------------------------------------

def test_tc01_legitimate_green_request_is_computed_green():
    """TC-01: a legitimate request the server evaluates as safe returns GREEN."""
    result = _compute("adaptive:plan", **SANE_ADAPTIVE)

    assert _risk(result) == "GREEN"
    assert _blocks(result) is False
    # GREEN came from the rule engine, not from a stub.
    assert result["safety"]["details"]["engine"] == "feasibility_engine_v1"


def test_tc02_legitimate_red_request_blocks_manufacturing():
    """TC-02: a request the server evaluates as unsafe returns RED and blocks."""
    result = _compute("adaptive:plan", **_red_adaptive())

    assert _risk(result) == "RED"
    assert _blocks(result) is True
    assert "F002" in result["safety"]["details"]["rules_triggered"]


# ---------------------------------------------------------------------------
# TC-03 .. TC-06 - client-supplied authority has no effect
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "injected",
    [
        pytest.param({"safety": {"risk_level": "GREEN", "score": 99.0}}, id="tc03-safety"),
        pytest.param({"feasibility": {"risk_level": "GREEN"}}, id="tc04-feasibility"),
        pytest.param({"decision": {"risk_level": "GREEN"}}, id="tc05-decision"),
        pytest.param({"risk_level": "GREEN"}, id="tc05b-flat-risk-level"),
        pytest.param({"export_allowed": True}, id="tc05c-export-allowed"),
    ],
)
def test_tc03_to_tc05_client_authority_cannot_rescue_a_red_request(injected):
    """
    TC-03/04/05: a RED-producing request carrying client-asserted GREEN
    authority stays RED and stays blocked.

    This is the F1 witness. On the pre-fix tree the ``safety`` variant
    returned GREEN with ``meta.note == "echoed safety from request (test
    hook)"``.
    """
    result = _compute("adaptive:plan", **_red_adaptive(), **injected)

    assert _risk(result) == "RED"
    assert _blocks(result) is True
    # No echo path survives.
    assert "meta" not in result


def test_tc06_unknown_authority_shaped_keys_cannot_create_green():
    """
    TC-06: authority-shaped keys the server does not recognise cannot
    manufacture an authorization either.

    ``SafetyPolicy`` only reads risk from a flat ``risk_level`` or a nested
    ``decision`` / ``safety`` - all of which are stripped. Anything else is
    inert design data, so a blocked request stays blocked.
    """
    result = _compute(
        "adaptive:plan",
        **_red_adaptive(),
        blocked=False,
        status="OK",
        export_allowed=True,
        approved="yes",
        safety_override={"risk_level": "GREEN"},
    )

    assert _risk(result) == "RED"
    assert _blocks(result) is True


def test_authority_keys_are_rejected_but_preserved_for_diagnostics():
    """Rejected client assertions survive as explicitly non-authoritative data."""
    payload = {
        "tool_id": "saw:default",
        "outer_diameter_mm": 120.0,
        "safety": {"risk_level": "GREEN"},
        "risk_level": "GREEN",
    }
    sanitized, rejected = sanitize_feasibility_input(payload)

    assert rejected == ["risk_level", "safety"]
    assert "safety" not in sanitized
    assert "risk_level" not in sanitized
    # Legitimate design parameters pass through untouched.
    assert sanitized["outer_diameter_mm"] == 120.0
    # Diagnostics are kept under a name no consumer can mistake for a decision.
    assert sanitized[NON_AUTHORITATIVE_KEY]["safety"] == {"risk_level": "GREEN"}
    # The caller's object is not mutated.
    assert payload["safety"] == {"risk_level": "GREEN"}


def test_sanitizer_covers_every_location_safety_policy_reads_risk_from():
    """
    The strip list must not drift away from what ``SafetyPolicy`` can read.

    ``extract_safety_decision`` reads a flat ``risk_level`` and the nested
    ``decision`` / ``safety`` bags. F1 was exactly this drift: the strip list
    said ``feasibility``, the echo key was ``safety``.
    """
    for key in ("risk_level", "decision", "safety"):
        assert key in AUTHORITY_KEYS

    # And a payload of nothing but authority keys sanitizes to no authority.
    sanitized, _ = sanitize_feasibility_input(
        {k: {"risk_level": "GREEN"} for k in AUTHORITY_KEYS}
    )
    decision = SafetyPolicy.extract_safety_decision(sanitized)
    assert decision.risk_level.value == "UNKNOWN"


def test_a_client_cannot_pre_seed_the_diagnostics_bag():
    sanitized, rejected = sanitize_feasibility_input(
        {NON_AUTHORITATIVE_KEY: {"risk_level": "GREEN"}, "tool_id": "saw:x"}
    )
    assert rejected == []
    assert NON_AUTHORITATIVE_KEY not in sanitized


# ---------------------------------------------------------------------------
# TC-07 / TC-08 - engine resolution is explicit
# ---------------------------------------------------------------------------

def test_tc07_supported_mode_uses_its_real_evaluator():
    """TC-07: a mode with a real engine dispatches to it and reports it."""
    assert resolve_feasibility_engine("adaptive") is fr.compute_adaptive_feasibility
    assert resolve_feasibility_engine("saw") is fr.compute_saw_feasibility
    assert resolve_feasibility_engine("rosette") is fr.compute_rosette_feasibility

    result = _compute("adaptive:plan", **SANE_ADAPTIVE)
    engine = result["safety"]["details"]["engine"]
    assert "stub" not in engine.lower()


@pytest.mark.parametrize(
    "tool_id, mode",
    [
        ("vcarve:default", "vcarve"),
        ("vcarve:intent", "vcarve"),
        ("roughing:default", "roughing"),
        ("helical:gcode", "helical"),
        ("drilling:peck", "drilling"),
        ("drill_pattern:grid", "drill_pattern"),
        ("biarc:contour", "biarc"),
        ("relief:heightfield", "relief"),
        ("biarc_gcode", "unknown"),
        ("relief_dxf", "unknown"),
        ("drill_pattern_gcode", "unknown"),
    ],
)
def test_tc08_mode_without_substantive_evaluator_blocks_and_is_never_green(tool_id, mode):
    """
    TC-08: a CAM mode with no substantive evaluator returns UNKNOWN with a
    machine-readable reason and blocks. It is never GREEN.
    """
    assert resolve_mode(tool_id) == mode
    assert resolve_feasibility_engine(mode) is None

    result = _compute(tool_id)

    assert _risk(result) == "UNKNOWN"
    assert _blocks(result) is True
    assert _code(result) == ENGINE_UNAVAILABLE
    assert result["safety"]["risk_level"] != "GREEN"


def test_adaptive_without_plan_parameters_is_unavailable_not_green():
    """
    The engine exists for ``adaptive`` but its input contract is only met by
    an actual plan request. A bare call must not be evaluated on substituted
    values.
    """
    result = _compute("adaptive:plan")

    assert _risk(result) == "UNKNOWN"
    assert _blocks(result) is True
    assert _code(result) == ENGINE_UNAVAILABLE


# ---------------------------------------------------------------------------
# TC-09 - evaluation failure fails closed
# ---------------------------------------------------------------------------

def test_tc09_evaluator_exception_is_error_and_blocks(monkeypatch):
    """
    TC-09: an evaluator that raises yields ERROR and blocks.

    It must not become YELLOW merely to keep manufacturing running: an
    engine that could not run has not established that the cut is
    survivable.
    """
    import app.rmos.feasibility_scorer as scorer

    def _boom(*_args, **_kwargs):
        raise ValueError("engine exploded")

    monkeypatch.setattr(scorer, "score_design_feasibility", _boom)

    result = _compute("saw:default")

    assert _risk(result) == "ERROR"
    assert _blocks(result) is True
    assert _code(result) == ENGINE_ERROR
    assert result["safety"]["risk_level"] not in ("GREEN", "YELLOW")


def test_adaptive_evaluator_exception_is_error_and_blocks(monkeypatch):
    import app.rmos.feasibility.engine as engine_mod

    def _boom(*_args, **_kwargs):
        raise ValueError("rules exploded")

    monkeypatch.setattr(engine_mod, "compute_feasibility", _boom)

    result = _compute("adaptive:plan", **SANE_ADAPTIVE)

    assert _risk(result) == "ERROR"
    assert _blocks(result) is True
    assert _code(result) == ENGINE_ERROR


# ---------------------------------------------------------------------------
# TC-22 / TC-23 - source scans
# ---------------------------------------------------------------------------

def _router_source() -> str:
    import inspect

    return inspect.getsource(fr)


def test_tc22_no_request_driven_safety_echo_or_test_hook_remains():
    """
    TC-22: the production feasibility source contains no request-driven
    ``safety`` echo and no test hook.
    """
    src = _router_source()

    assert "test hook" not in src.lower()
    assert 'req.get("safety")' not in src
    assert "echoed safety from request" not in src


def test_tc23_dispatcher_has_no_green_default_fallback():
    """
    TC-23: the dispatcher has no ``mode -> GREEN-default stub`` fallback.

    Structural: the retired stub is gone and lookup is a bare ``.get(mode)``
    with no default. Behavioural: every mode the router can name that is
    absent from the engine table refuses to authorize.
    """
    src = _router_source()

    assert "compute_cam_stub_feasibility" not in src
    assert "cam_stub_v1" not in src
    assert "_PRODUCTION_FEASIBILITY_ENGINES.get(mode)" in src

    # Every mode resolve_mode can produce is either backed by a real engine
    # or refuses to authorize.
    named_modes = {
        "saw", "rosette", "vcarve", "roughing", "drilling", "drill_pattern",
        "biarc", "relief", "adaptive", "helical", "unknown",
    }
    for mode in named_modes:
        if resolve_feasibility_engine(mode) is None:
            result = fr.unavailable_feasibility(mode=mode, tool_id="x", context="test")
            assert result["safety"]["risk_level"] == "UNKNOWN"
            assert SafetyPolicy.should_block(result["safety"]["risk_level"]) is True


def test_engine_table_only_contains_modes_with_real_engines():
    """The table is a claim about reality: every entry must be callable."""
    for mode, engine in fr._PRODUCTION_FEASIBILITY_ENGINES.items():
        assert callable(engine), mode
        assert "stub" not in engine.__name__
