# tests/test_policy_engine_v1.py
"""
Decision Policy Engine Tests — validates decide() behavior across modes.

Tests ensure:
1. M0 (shadow) never emits directives
2. M1 (advisory) emits directives but no commands
3. M2 (actuated) can issue commands when capability allows
4. UWSM dimensions affect behavior (initiative, guidance, load)
5. Policy is deterministic
"""

from __future__ import annotations

import pytest


def test_decide_import():
    """Smoke test: policy module is importable."""
    from app.agentic.spine.policy import decide
    assert callable(decide)


def _default_uwsm() -> dict:
    """Minimal UWSM with medium defaults."""
    return {
        "dimensions": {
            "guidance_density": {"value": "medium"},
            "initiative_tolerance": {"value": "shared_control"},
            "cognitive_load_sensitivity": {"value": "medium"},
        }
    }


def _default_capability() -> dict:
    """Minimal capability with no automation."""
    return {"automation_limits": {"agent_can_adjust_view": False}}


# --- M0 Shadow Mode Tests ---

def test_m0_never_emits_directive():
    """Shadow mode must never emit a directive."""
    from app.agentic.spine.policy import decide

    moment = {"moment": "FIRST_SIGNAL", "confidence": 0.75, "trigger_events": ["e1"]}
    result = decide(moment=moment, uwsm=_default_uwsm(), mode="M0", capability=_default_capability())

    assert result["emit_directive"] is False
    assert "would_have_emitted" in result["diagnostic"]


def test_m0_diagnostic_includes_would_have_emitted():
    """Shadow mode should track what would have been emitted."""
    from app.agentic.spine.policy import decide

    moment = {"moment": "HESITATION", "confidence": 0.8, "trigger_events": ["e1"]}
    result = decide(moment=moment, uwsm=_default_uwsm(), mode="M0", capability=_default_capability())

    would = result["diagnostic"]["would_have_emitted"]
    assert would["action"] == "INSPECT"
    assert "title" in would


def test_m0_no_commands_issued():
    """Shadow mode must not issue any commands."""
    from app.agentic.spine.policy import decide

    moment = {"moment": "FIRST_SIGNAL", "confidence": 0.75, "trigger_events": ["e1"]}
    result = decide(moment=moment, uwsm=_default_uwsm(), mode="M0", capability=_default_capability())

    assert result["issue_commands"] == []


# --- M1 Advisory Mode Tests ---

def test_m1_emits_directive_for_first_signal():
    """Advisory mode emits directive for FIRST_SIGNAL."""
    from app.agentic.spine.policy import decide

    moment = {"moment": "FIRST_SIGNAL", "confidence": 0.75, "trigger_events": ["e1"]}
    result = decide(moment=moment, uwsm=_default_uwsm(), mode="M1", capability=_default_capability())

    assert result["emit_directive"] is True
    assert result["directive"]["action"] == "INSPECT"


def test_m1_emits_directive_for_overload():
    """Advisory mode emits REVIEW directive for OVERLOAD."""
    from app.agentic.spine.policy import decide

    moment = {"moment": "OVERLOAD", "confidence": 0.9, "trigger_events": ["e1"]}
    result = decide(moment=moment, uwsm=_default_uwsm(), mode="M1", capability=_default_capability())

    assert result["emit_directive"] is True
    assert result["directive"]["action"] == "REVIEW"


def test_m1_no_commands_issued():
    """Advisory mode does not issue analyzer commands."""
    from app.agentic.spine.policy import decide

    moment = {"moment": "FIRST_SIGNAL", "confidence": 0.75, "trigger_events": ["e1"]}
    result = decide(moment=moment, uwsm=_default_uwsm(), mode="M1", capability=_default_capability())

    assert result["issue_commands"] == []


def test_m1_diagnostic_has_rule_id():
    """Every decision includes a rule_id for debugging."""
    from app.agentic.spine.policy import decide

    moment = {"moment": "HESITATION", "confidence": 0.8, "trigger_events": ["e1"]}
    result = decide(moment=moment, uwsm=_default_uwsm(), mode="M1", capability=_default_capability())

    assert "rule_id" in result["diagnostic"]
    assert "POLICY_" in result["diagnostic"]["rule_id"]


# --- M2 Actuated Mode Tests ---

def test_m2_issues_commands_when_capability_allows():
    """M2 can issue commands if capability.agent_can_adjust_view is true."""
    from app.agentic.spine.policy import decide

    moment = {"moment": "FIRST_SIGNAL", "confidence": 0.75, "trigger_events": ["e1"]}
    capability = {"automation_limits": {"agent_can_adjust_view": True}}
    context = {"first_time_user": True, "primary_panel": "spectrum", "primary_trace": "main"}

    result = decide(moment=moment, uwsm=_default_uwsm(), mode="M2", capability=capability, context=context)

    assert len(result["issue_commands"]) > 0
    cmd_names = [c["name"] for c in result["issue_commands"]]
    assert "hide_all_except" in cmd_names or "focus_trace" in cmd_names


def test_m2_falls_back_to_m1_when_capability_disallows():
    """M2 falls back to M1 behavior if capability disallows adjustments."""
    from app.agentic.spine.policy import decide

    moment = {"moment": "FIRST_SIGNAL", "confidence": 0.75, "trigger_events": ["e1"]}
    capability = {"automation_limits": {"agent_can_adjust_view": False}}

    result = decide(moment=moment, uwsm=_default_uwsm(), mode="M2", capability=capability)

    assert result["issue_commands"] == []
    assert result.get("diagnostic", {}).get("fallback_mode") == "M1"


# --- UWSM Dimension Tests ---

def test_user_led_initiative_suppresses_first_signal():
    """initiative_tolerance=user_led suppresses proactive suggestions for FIRST_SIGNAL."""
    from app.agentic.spine.policy import decide

    moment = {"moment": "FIRST_SIGNAL", "confidence": 0.75, "trigger_events": ["e1"]}
    uwsm = {
        "dimensions": {
            "guidance_density": {"value": "medium"},
            "initiative_tolerance": {"value": "user_led"},
            "cognitive_load_sensitivity": {"value": "medium"},
        }
    }
    result = decide(moment=moment, uwsm=uwsm, mode="M1", capability=_default_capability())

    # user_led suppresses FIRST_SIGNAL
    assert result["attention_action"] == "NONE" or result["emit_directive"] is False


def test_user_led_initiative_soft_prompt_for_hesitation():
    """initiative_tolerance=user_led produces soft prompt for HESITATION."""
    from app.agentic.spine.policy import decide

    moment = {"moment": "HESITATION", "confidence": 0.8, "trigger_events": ["e1"]}
    uwsm = {
        "dimensions": {
            "guidance_density": {"value": "medium"},
            "initiative_tolerance": {"value": "user_led"},
            "cognitive_load_sensitivity": {"value": "medium"},
        }
    }
    result = decide(moment=moment, uwsm=uwsm, mode="M1", capability=_default_capability())

    # Should still emit with soft prompt
    assert result["emit_directive"] is True
    assert result["diagnostic"].get("soft_prompt") is True


def test_low_guidance_density_clears_detail():
    """guidance_density=low or very_low should clear directive detail."""
    from app.agentic.spine.policy import decide

    moment = {"moment": "FIRST_SIGNAL", "confidence": 0.75, "trigger_events": ["e1"]}
    uwsm = {
        "dimensions": {
            "guidance_density": {"value": "very_low"},
            "initiative_tolerance": {"value": "shared_control"},
            "cognitive_load_sensitivity": {"value": "medium"},
        }
    }
    result = decide(moment=moment, uwsm=uwsm, mode="M1", capability=_default_capability())

    assert result["directive"]["detail"] == ""


def test_high_cognitive_load_limits_directives():
    """High cognitive_load_sensitivity should limit max_directives to 1."""
    from app.agentic.spine.policy import decide

    moment = {"moment": "FIRST_SIGNAL", "confidence": 0.75, "trigger_events": ["e1"]}
    uwsm = {
        "dimensions": {
            "guidance_density": {"value": "medium"},
            "initiative_tolerance": {"value": "shared_control"},
            "cognitive_load_sensitivity": {"value": "high"},
        }
    }
    result = decide(moment=moment, uwsm=uwsm, mode="M1", capability=_default_capability())

    assert result["diagnostic"]["max_directives"] == 1


# --- Determinism Tests ---

def test_determinism_same_input_same_output():
    """Same inputs should always produce the same decision."""
    from app.agentic.spine.policy import decide

    moment = {"moment": "OVERLOAD", "confidence": 0.9, "trigger_events": ["e1"]}

    result1 = decide(moment=moment, uwsm=_default_uwsm(), mode="M1", capability=_default_capability())
    result2 = decide(moment=moment, uwsm=_default_uwsm(), mode="M1", capability=_default_capability())

    assert result1 == result2
