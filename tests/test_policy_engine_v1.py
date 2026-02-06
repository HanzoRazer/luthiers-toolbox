# tests/test_policy_engine_v1.py
"""
Executable tests for the decision policy engine.

Assumes you implement a policy engine in luthiers-toolbox, e.g.:

    from app.agentic.spine.policy import decide

Suggested signature:
    decide(
        *,
        moment: dict,
        uwsm: dict,
        mode: str,  # "M0"|"M1"|"M2"
        capability: dict,
        context: dict | None = None
    ) -> dict

Where result contains:
    - "attention_action": str (INSPECT/REVIEW/COMPARE/DECIDE/CONFIRM/INTERVENE/ABORT)
    - "emit_directive": bool
    - "issue_commands": list[dict]  # analyzer attention commands
    - "diagnostic": dict

Until that module exists, these tests will be SKIPPED.
"""

from __future__ import annotations

import pytest

POLICY_IMPORT_PATH = "app.agentic.spine.policy"


def _import_decider():
    mod = pytest.importorskip(POLICY_IMPORT_PATH, reason=f"{POLICY_IMPORT_PATH} not implemented yet")
    decide = getattr(mod, "decide", None)
    assert callable(decide), "Expected a callable decide(...) in spine.policy"
    return decide


@pytest.fixture
def uwsm_default():
    return {
        "dimensions": {
            "guidance_density": {"value": "medium", "confidence": 0.6},
            "initiative_tolerance": {"value": "shared_control", "confidence": 0.6},
            "cognitive_load_sensitivity": {"value": "medium", "confidence": 0.6},
        }
    }


@pytest.fixture
def uwsm_high_load():
    return {
        "dimensions": {
            "guidance_density": {"value": "medium", "confidence": 0.6},
            "initiative_tolerance": {"value": "shared_control", "confidence": 0.6},
            "cognitive_load_sensitivity": {"value": "very_high", "confidence": 0.8},
        }
    }


@pytest.fixture
def uwsm_user_led():
    return {
        "dimensions": {
            "guidance_density": {"value": "medium", "confidence": 0.6},
            "initiative_tolerance": {"value": "user_led", "confidence": 0.8},
            "cognitive_load_sensitivity": {"value": "medium", "confidence": 0.6},
        }
    }


@pytest.fixture
def uwsm_low_guidance():
    return {
        "dimensions": {
            "guidance_density": {"value": "very_low", "confidence": 0.8},
            "initiative_tolerance": {"value": "shared_control", "confidence": 0.6},
            "cognitive_load_sensitivity": {"value": "medium", "confidence": 0.6},
        }
    }


@pytest.fixture
def cap_view_allowed():
    return {"automation_limits": {"agent_can_adjust_view": True}}


@pytest.fixture
def cap_view_denied():
    return {"automation_limits": {"agent_can_adjust_view": False}}


def test_policy_first_signal_maps_to_inspect(uwsm_default, cap_view_allowed):
    decide = _import_decider()
    out = decide(moment={"moment": "FIRST_SIGNAL"}, uwsm=uwsm_default, mode="M1", capability=cap_view_allowed)
    assert out["attention_action"] == "INSPECT"
    assert out["emit_directive"] is True


def test_policy_overload_maps_to_review(uwsm_default, cap_view_allowed):
    decide = _import_decider()
    out = decide(moment={"moment": "OVERLOAD"}, uwsm=uwsm_default, mode="M1", capability=cap_view_allowed)
    assert out["attention_action"] == "REVIEW"


def test_gate_high_cognitive_load_limits_to_one(uwsm_high_load, cap_view_allowed):
    decide = _import_decider()
    out = decide(moment={"moment": "FINDING"}, uwsm=uwsm_high_load, mode="M1", capability=cap_view_allowed)
    assert out.get("diagnostic", {}).get("max_directives", 1) == 1
    # If you return multiple directives, assert it's clamped to 1
    directives = out.get("directives", [])
    if directives:
        assert len(directives) <= 1


def test_gate_user_led_suppresses_proactive(uwsm_user_led, cap_view_allowed):
    decide = _import_decider()
    out = decide(moment={"moment": "HESITATION"}, uwsm=uwsm_user_led, mode="M1", capability=cap_view_allowed)
    # Policy allows either no directive or a very soft "Want a suggestion?" INSPECT
    assert out["attention_action"] in ("INSPECT", "NONE")
    if out["attention_action"] == "INSPECT":
        assert out.get("diagnostic", {}).get("soft_prompt", False) is True


def test_gate_low_guidance_summary_only(uwsm_low_guidance, cap_view_allowed):
    decide = _import_decider()
    out = decide(moment={"moment": "FIRST_SIGNAL"}, uwsm=uwsm_low_guidance, mode="M1", capability=cap_view_allowed)
    directive = out.get("directive", {})
    # Implementation choice: omit detail or keep it minimal
    assert directive.get("detail", "") in ("", None) or len(directive.get("detail", "")) <= 140


def test_mode_m0_shadow_emits_diagnostic_only(uwsm_default, cap_view_allowed):
    decide = _import_decider()
    out = decide(moment={"moment": "FINDING"}, uwsm=uwsm_default, mode="M0", capability=cap_view_allowed)
    assert out["emit_directive"] is False
    assert out.get("diagnostic", {}).get("would_have_emitted") is not None


def test_mode_m2_issues_commands_if_allowed(uwsm_default, cap_view_allowed):
    decide = _import_decider()
    out = decide(
        moment={"moment": "FIRST_SIGNAL"},
        uwsm=uwsm_default,
        mode="M2",
        capability=cap_view_allowed,
        context={"first_time_user": True, "primary_panel": "spectrum", "primary_trace": "main"},
    )
    assert out["emit_directive"] is True
    cmds = out.get("issue_commands", [])
    assert any(c.get("name") == "hide_all_except" for c in cmds)
    assert any(c.get("name") == "focus_trace" for c in cmds)


def test_mode_m2_falls_back_if_denied(uwsm_default, cap_view_denied):
    decide = _import_decider()
    out = decide(
        moment={"moment": "FIRST_SIGNAL"},
        uwsm=uwsm_default,
        mode="M2",
        capability=cap_view_denied,
        context={"first_time_user": True, "primary_panel": "spectrum", "primary_trace": "main"},
    )
    assert out["emit_directive"] is True
    assert out.get("issue_commands", []) == []
    assert out.get("diagnostic", {}).get("fallback_mode") in ("M1", "ADVISORY")
