"""
Agentic Policy Module - UWSM-based directive generation.

This module implements the policy decision logic that determines
what directive (if any) to show the user based on:
1. The detected moment
2. The user's working style model (UWSM)
3. The current agentic mode (M0/M1/M2)
"""

from __future__ import annotations

from typing import Literal

from .schemas import (
    AttentionDirective,
    DetectedMoment,
    PolicyDecision,
    PolicyDiagnostic,
    UWSMSnapshot,
    DEFAULT_UWSM,
)

# Module is now implemented
IMPLEMENTED = True

# Type alias for agentic mode
AgenticMode = Literal["M0", "M1", "M2"]


# Moment to action mapping
MOMENT_TO_ACTION = {
    "FIRST_SIGNAL": "INSPECT",
    "HESITATION": "INSPECT",
    "OVERLOAD": "REVIEW",
    "DECISION_REQUIRED": "DECIDE",
    "FINDING": "REVIEW",
    "ERROR": "REVIEW",
}

# Action titles for UI
ACTION_TITLES = {
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
    """
    Build an attention directive from action and context.

    Args:
        action: The action type (INSPECT, REVIEW, etc.)
        guidance: Guidance density from UWSM
        soft_prompt: Whether to use soft prompting language

    Returns:
        AttentionDirective with title and detail
    """
    title = ACTION_TITLES.get(action, "Next step")

    # Build detail text based on action
    if action == "INSPECT":
        detail = "Focus on one signal and make a small change."
    elif action == "REVIEW":
        detail = "Let's simplify and confirm what changed."
    elif action == "DECIDE":
        detail = "Choose one option to proceed."
    else:
        detail = ""

    # Soft prompt override
    if soft_prompt:
        detail = "Want a suggestion for what to try next?"

    # Low guidance density = minimal detail
    if guidance in ("very_low", "low"):
        detail = ""

    return AttentionDirective(
        action=action,  # type: ignore
        title=title,
        detail=detail,
    )


def decide(
    moment: DetectedMoment,
    uwsm: UWSMSnapshot = None,
    mode: AgenticMode = "M1",
) -> PolicyDecision:
    """
    Apply UWSM policy to a detected moment.

    Args:
        moment: The detected moment
        uwsm: User working style model (defaults to DEFAULT_UWSM)
        mode: Agentic mode (M0=shadow, M1=advisory, M2=actuated)

    Returns:
        PolicyDecision with directive and diagnostics
    """
    if uwsm is None:
        uwsm = DEFAULT_UWSM

    moment_name = moment.moment
    dims = uwsm.dimensions

    guidance = dims.guidance_density.value
    initiative = dims.initiative_tolerance.value
    load = dims.cognitive_load_sensitivity.value

    # Determine max directives based on cognitive load
    max_directives = 1 if load in ("high", "very_high") else 2

    # Map moment to action
    action = MOMENT_TO_ACTION.get(moment_name, "NONE")
    soft_prompt = False

    # Initiative gate: user_led users only see critical directives
    if initiative == "user_led":
        if moment_name in ("HESITATION", "FINDING", "FIRST_SIGNAL"):
            if moment_name == "HESITATION":
                soft_prompt = True
            else:
                action = "NONE"

    # Build diagnostic info
    diagnostic = PolicyDiagnostic(
        rule_id=f"POLICY_{moment_name}_{action}_v1",
        max_directives=max_directives,
    )

    # Shadow mode: don't emit, but track what would have been emitted
    if mode == "M0":
        would_have = build_directive(action, guidance, soft_prompt)
        diagnostic.would_have_emitted = would_have
        return PolicyDecision(
            attention_action=action,
            emit_directive=False,
            directive=AttentionDirective(action="NONE", title="", detail=""),
            diagnostic=diagnostic,
        )

    # M1/M2: emit if action != NONE
    emit_directive = action != "NONE"
    directive = (
        build_directive(action, guidance, soft_prompt)
        if emit_directive
        else AttentionDirective(action="NONE", title="", detail="")
    )

    return PolicyDecision(
        attention_action=action,
        emit_directive=emit_directive,
        directive=directive,
        diagnostic=diagnostic,
    )
