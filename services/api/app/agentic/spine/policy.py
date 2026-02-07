"""
Policy Engine — Decides what directive to emit based on moment + UWSM.

The policy engine takes:
- A detected moment (from moments.py)
- The user's working style model (UWSM)
- The current operating mode (M0/M1/M2)
- The capability context

And produces a PolicyDecision with:
- attention_action: What action type to take
- emit_directive: Whether to actually show it to the user
- directive: The directive payload (title, detail)
- diagnostic: Debug info including rule_id
"""

from __future__ import annotations

from typing import TypedDict, Dict, Any, Optional, Literal

AgenticMode = Literal["M0", "M1", "M2"]


class AttentionDirective(TypedDict):
    action: str  # INSPECT | REVIEW | COMPARE | DECIDE | CONFIRM | NONE
    title: str
    detail: str


class Command(TypedDict, total=False):
    name: str
    params: Dict[str, Any]


class PolicyDiagnostic(TypedDict, total=False):
    rule_id: str
    max_directives: int
    would_have_emitted: Optional[AttentionDirective]
    soft_prompt: bool
    fallback_mode: Optional[str]


class PolicyDecision(TypedDict):
    attention_action: str
    emit_directive: bool
    directive: AttentionDirective
    diagnostic: PolicyDiagnostic
    issue_commands: list  # List[Command]


# Moment -> Action mapping
MOMENT_TO_ACTION: Dict[str, str] = {
    "FIRST_SIGNAL": "INSPECT",
    "HESITATION": "INSPECT",
    "OVERLOAD": "REVIEW",
    "DECISION_REQUIRED": "DECIDE",
    "FINDING": "REVIEW",
    "ERROR": "REVIEW",
}

# Action titles
ACTION_TITLES: Dict[str, str] = {
    "INSPECT": "Inspect this",
    "REVIEW": "Review this",
    "COMPARE": "Compare options",
    "DECIDE": "Make a choice",
    "CONFIRM": "Confirm",
    "NONE": "",
}


def build_directive(
    action: str,
    guidance: str,
    soft_prompt: bool,
) -> AttentionDirective:
    """Build a directive payload from action and UWSM context."""
    title = ACTION_TITLES.get(action, "Next step")
    
    # Default details by action
    detail = ""
    if action == "INSPECT":
        detail = "Focus on one signal and make a small change."
    elif action == "REVIEW":
        detail = "Let's simplify and confirm what changed."
    elif action == "DECIDE":
        detail = "Choose one option to proceed."
    
    # Soft prompt override
    if soft_prompt:
        detail = "Want a suggestion for what to try next?"
    
    # Low guidance = no detail
    if guidance in ("very_low", "low"):
        detail = ""
    
    return AttentionDirective(
        action=action,
        title=title,
        detail=detail,
    )


def decide(
    moment: Dict[str, Any],
    uwsm: Dict[str, Any],
    mode: AgenticMode,
    capability: Optional[Dict[str, Any]] = None,
    context: Optional[Dict[str, Any]] = None,
) -> PolicyDecision:
    """
    Decide what directive to emit based on moment, UWSM, mode, and capability.

    Args:
        moment: DetectedMoment dict with moment, confidence, trigger_events
        uwsm: User Working Style Model with dimensions
        mode: Operating mode (M0=shadow, M1=advisory, M2=actuated)
        capability: Optional capability context
        context: Optional context for M2 command generation

    Returns:
        PolicyDecision with attention_action, emit_directive, directive, diagnostic
    """
    moment_name = moment.get("moment", "")
    
    # Extract UWSM dimensions
    dims = uwsm.get("dimensions", {})
    guidance = dims.get("guidance_density", {}).get("value", "medium")
    initiative = dims.get("initiative_tolerance", {}).get("value", "shared_control")
    load = dims.get("cognitive_load_sensitivity", {}).get("value", "medium")
    
    # Max directives based on cognitive load
    max_directives = 1 if load in ("high", "very_high") else 2
    
    # Map moment to action
    action = MOMENT_TO_ACTION.get(moment_name, "NONE")
    soft_prompt = False
    
    # Initiative gate: user_led suppresses proactive moments
    if initiative == "user_led" and moment_name in ("HESITATION", "FINDING", "FIRST_SIGNAL"):
        if moment_name == "HESITATION":
            soft_prompt = True
        else:
            action = "NONE"
    
    # Build diagnostic
    diagnostic: PolicyDiagnostic = {
        "rule_id": f"POLICY_{moment_name}_{action}_v1",
        "max_directives": max_directives,
    }

    # Track soft_prompt in diagnostic
    if soft_prompt:
        diagnostic["soft_prompt"] = True

    # M0 shadow mode: don't emit, but track what would have been emitted
    if mode == "M0":
        would_have = build_directive(action, guidance, soft_prompt)
        diagnostic["would_have_emitted"] = would_have
        return PolicyDecision(
            attention_action=action,
            emit_directive=False,
            directive=AttentionDirective(action="NONE", title="", detail=""),
            diagnostic=diagnostic,
            issue_commands=[],
        )

    # M1/M2: emit if action != NONE
    emit_directive = action != "NONE"
    directive = (
        build_directive(action, guidance, soft_prompt)
        if emit_directive
        else AttentionDirective(action="NONE", title="", detail="")
    )

    # M2 can issue commands if capability allows
    issue_commands: list = []
    if mode == "M2":
        cap = capability or {}
        automation_limits = cap.get("automation_limits", {})
        if automation_limits.get("agent_can_adjust_view", False) and context:
            # Generate commands for first-time users
            if context.get("first_time_user"):
                primary_panel = context.get("primary_panel", "spectrum")
                primary_trace = context.get("primary_trace", "main")
                issue_commands.append({
                    "name": "focus_trace",
                    "params": {"panel": primary_panel, "trace": primary_trace},
                })
        else:
            # Fall back to M1 behavior
            diagnostic["fallback_mode"] = "M1"

    return PolicyDecision(
        attention_action=action,
        emit_directive=emit_directive,
        directive=directive,
        diagnostic=diagnostic,
        issue_commands=issue_commands,
    )
