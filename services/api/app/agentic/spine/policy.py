# app/agentic/spine/policy.py
"""
Decision Policy Engine — Reference Implementation

Applies decision policy based on detected moments, UWSM state, and operating mode.
This is a conservative implementation designed to:
1. Pass the test suite
2. Work correctly in shadow mode (M0)
3. Provide reasonable defaults for M1/M2

For full specification, see: docs/AGENT_DECISION_POLICY_V1.md
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def _dim(uwsm: dict, name: str, default_value: str = "medium") -> str:
    return (
        (uwsm or {})
        .get("dimensions", {})
        .get(name, {})
        .get("value", default_value)
    )


def _capability_allows_view_adjustment(capability: dict) -> bool:
    return bool((capability or {}).get("automation_limits", {}).get("agent_can_adjust_view", False))


def _max_directives_for_load(load_value: str) -> int:
    # "very_high" sensitivity => max 1 directive (per spec)
    return 1 if load_value in ("high", "very_high") else 2


def decide(
    *,
    moment: dict,
    uwsm: dict,
    mode: str,
    capability: dict,
    context: Optional[dict] = None,
) -> dict:
    """
    Minimal reference policy engine.

    Returns dict with keys used by tests:
      - attention_action: str
      - emit_directive: bool
      - directive: dict (optional)
      - directives: list (optional)
      - issue_commands: list[dict]
      - diagnostic: dict

    This implementation is conservative and designed to pass bootstrap tests.
    """
    context = context or {}
    moment_name = (moment or {}).get("moment", "UNKNOWN")

    guidance = _dim(uwsm, "guidance_density", "medium")
    initiative = _dim(uwsm, "initiative_tolerance", "shared_control")
    load = _dim(uwsm, "cognitive_load_sensitivity", "medium")

    max_directives = _max_directives_for_load(load)

    # Default mapping (spec)
    mapping = {
        "FIRST_SIGNAL": "INSPECT",
        "HESITATION": "INSPECT",
        "OVERLOAD": "REVIEW",
        "DECISION_REQUIRED": "DECIDE",
        "FINDING": "REVIEW",
        "ERROR": "REVIEW",
    }
    action = mapping.get(moment_name, "NONE")

    diagnostic: dict = {
        "rule_id": f"POLICY_{moment_name}_{action}_v1",
        "max_directives": max_directives,
    }

    # Initiative gate: user_led suppresses proactive suggestions
    soft_prompt = False
    if initiative == "user_led" and moment_name in ("HESITATION", "FINDING", "FIRST_SIGNAL"):
        # Allow either no directive or a very soft INSPECT with a "Want a suggestion?" prompt.
        if moment_name == "HESITATION":
            action = "INSPECT"
            soft_prompt = True
            diagnostic["soft_prompt"] = True
        else:
            action = "NONE"
            diagnostic["suppressed_due_to_initiative"] = True

    # Mode behavior
    issue_commands: List[dict] = []

    if mode == "M0":
        # Shadow: never emit directive; instead produce diagnostic "would_have_emitted"
        would = _build_directive(action, guidance=guidance, soft_prompt=soft_prompt)
        diagnostic["would_have_emitted"] = would
        return {
            "attention_action": action,
            "emit_directive": False,
            "issue_commands": [],
            "diagnostic": diagnostic,
        }

    # In M1/M2: emit directive unless action == NONE
    emit_directive = action != "NONE"
    directive = _build_directive(action, guidance=guidance, soft_prompt=soft_prompt) if emit_directive else {}

    # Guidance density gate: summary-only when very_low
    if guidance in ("very_low", "low") and emit_directive:
        # keep detail empty or very short
        directive["detail"] = ""

    # M2: analyzer attention commands if allowed + FIRST_SIGNAL onboarding rule
    if mode == "M2":
        if _capability_allows_view_adjustment(capability):
            # One-Trace onboarding for FIRST_SIGNAL + FTUE
            if moment_name == "FIRST_SIGNAL" and bool(context.get("first_time_user", False)):
                primary_panel = context.get("primary_panel", "spectrum")
                primary_trace = context.get("primary_trace", "main")
                issue_commands = [
                    {"name": "hide_all_except", "parameters": {"panel_id": primary_panel}},
                    {"name": "focus_trace", "parameters": {"trace_id": primary_trace}},
                ]
        else:
            # Fallback to M1 behavior
            diagnostic["fallback_mode"] = "M1"
            issue_commands = []

    out = {
        "attention_action": action,
        "emit_directive": emit_directive,
        "directive": directive if emit_directive else {},
        "directives": [directive] if emit_directive else [],
        "issue_commands": issue_commands,
        "diagnostic": diagnostic,
    }
    return out


def _build_directive(action: str, *, guidance: str, soft_prompt: bool) -> dict:
    """
    Minimal AttentionDirectiveV1-ish structure.
    """
    title = {
        "INSPECT": "Inspect this",
        "REVIEW": "Review this",
        "COMPARE": "Compare options",
        "DECIDE": "Make a choice",
        "CONFIRM": "Confirm",
        "INTERVENE": "Stop and check",
        "ABORT": "Abort",
        "NONE": "",
    }.get(action, "Next step")

    detail = ""
    if action == "INSPECT":
        detail = "Focus on one signal and make a small change."
    elif action == "REVIEW":
        detail = "Let's simplify and confirm what changed."
    elif action == "DECIDE":
        detail = "Choose one option to proceed."

    if soft_prompt:
        detail = "Want a suggestion for what to try next?"

    return {
        "action": action,
        "title": title,
        "detail": detail,
    }
