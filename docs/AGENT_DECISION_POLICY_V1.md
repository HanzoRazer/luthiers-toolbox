# Agent Decision Policy Spec v1

**Version:** 1.0.0
**Date:** 2026-02-06
**Status:** Phase 2 Spine Document
**Depends On:** `ToolCapabilityV1`, `AgentEventV1`, `AttentionDirectiveV1`, `UWSMv1`

---

## 0. Purpose

This document defines **when the system emits** attention directives and **what the agent is allowed to do** at each rollout phase. It is the executable "when/why/how" logic layer that respects repo autonomy.

**This spec contains no tool-internal logic.** It only consumes:
- Capabilities (`ToolCapabilityV1`)
- Events (`AgentEventV1`)
- UWSM state (`UWSMv1`)

---

## 1. Operating Modes

The agent operates in one of three modes, forming a hard gate on allowed actions.

### 1.1 Mode Definitions

| Mode | ID | Description | User-Facing Output |
|------|----|-------------|-------------------|
| **Shadow** | `M0` | Observe only, log decisions | None |
| **Advisory** | `M1` | Suggest actions, user decides | Attention directives |
| **Actuated** | `M2` | Can adjust analyzer view (opt-in) | Directives + view commands |

### 1.2 Mode M0 — Shadow

```
MUST:
- Read all AgentEventV1 from event stream
- Compute decisions using full policy pipeline
- Emit diagnostic events with payload: {would_have_emitted: AttentionDirectiveV1}

MUST NOT:
- Emit user-facing attention directives
- Send any analyzer commands
- Modify any state
```

**Shadow Mode Event Format:**

```json
{
  "event_type": "system_health",
  "payload": {
    "mode": "shadow",
    "would_have_emitted": {
      "directive_id": "attn_shadow_001",
      "action": "review",
      "summary": "Potential wolf tone at 247Hz"
    },
    "policy_trace": {
      "moment": "MOMENT_FINDING",
      "intervention_class": "I2_REVIEW",
      "uwsm_gates_applied": ["cognitive_load_sensitivity"]
    }
  }
}
```

### 1.3 Mode M1 — Advisory

```
MUST:
- Emit AttentionDirectiveV1 via ATTENTION_REQUESTED event
- Respect UWSM gating rules (Section 5)
- Limit directive frequency per session

MAY:
- Suggest next steps as part of directive detail
- Emit INSPECT, REVIEW, COMPARE, DECIDE actions

MUST NOT:
- Send analyzer attention commands
- Change analyzer/tool state
- Auto-dismiss user data or views
```

### 1.4 Mode M2 — Actuated (Opt-In)

```
MUST:
- Check ToolCapabilityV1.safe_defaults.require_confirmation before acting
- Respect automation_limits from capability declaration
- Fall back to M1 if capability disallows view adjustment

MAY:
- Send Analyzer Attention Contract commands:
  - focus_trace(trace_id)
  - hide_all_except(panel_id)
  - highlight_delta(from_state_id, to_state_id)
  - reset_view()

MUST NOT:
- Change measurement parameters
- Start/stop acquisition
- Export data
- Persist analyzer state
```

**Capability Gate Rule:**

```python
# Rule: MODE_ACTUATED_GATE_v1
def can_actuate(tool_id: str) -> bool:
    cap = get_capability_by_id(tool_id)
    if cap is None:
        return False
    # Check if tool allows agent view adjustment
    # (Future: add automation_limits to ToolCapabilityV1)
    return cap.safe_defaults.require_confirmation is False
```

---

## 2. Decision Pipeline

The agent processes events through a deterministic 5-step pipeline.

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  A: Ingest  │ ──▶ │  B: Detect  │ ──▶ │  C: Choose  │ ──▶ │  D: Apply   │ ──▶ │  E: Emit    │
│  & Normalize│     │   Moments   │     │ Intervention│     │ UWSM Gates  │     │   Output    │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

### 2.1 Step A: Ingest & Normalize

**Input:** Stream of `AgentEventV1`

**Normalization produces:**

| Context | Fields |
|---------|--------|
| Session | `session_id`, `session_start`, `event_count` |
| Tool | `active_tool_id`, `tool_capabilities`, `tool_state` |
| Analyzer | `active_panels`, `visible_traces`, `last_result` |
| User | `last_action_at`, `action_count`, `undo_count` |

**Normalization Rules:**

```python
# Rule: NORMALIZE_SESSION_v1
def normalize_session(events: list[AgentEventV1]) -> SessionContext:
    return SessionContext(
        session_id=events[0].correlation_id or generate_session_id(),
        session_start=events[0].occurred_at,
        event_count=len(events),
    )

# Rule: NORMALIZE_TOOL_v1
def normalize_tool(events: list[AgentEventV1]) -> ToolContext:
    # Find most recent TOOL_RENDERED or ANALYSIS_COMPLETED
    tool_events = [e for e in events if e.event_type in (
        EventType.ARTIFACT_CREATED,
        EventType.ANALYSIS_COMPLETED,
    )]
    if not tool_events:
        return ToolContext.empty()

    latest = tool_events[-1]
    return ToolContext(
        active_tool_id=latest.source.component,
        tool_capabilities=get_capability_by_id(latest.source.component),
    )
```

### 2.2 Step B: Detect Moments

Moments are named patterns over events. See [EVENT_MOMENTS_CATALOG_V1.md](EVENT_MOMENTS_CATALOG_V1.md) for full definitions.

**Moment Types (v1):**

| Moment ID | Description | Detection Window |
|-----------|-------------|------------------|
| `MOMENT_FIRST_SIGNAL` | First analyzer result rendered | Session start |
| `MOMENT_HESITATION` | Inactivity or repeated hover | 8+ seconds idle |
| `MOMENT_OVERLOAD` | Undo spikes or explicit feedback | 3+ undos in 60s |
| `MOMENT_DECISION_REQUIRED` | Tool emits decision request | Immediate |
| `MOMENT_ERROR` | Analysis failed | Immediate |
| `MOMENT_FINDING` | Attention-worthy finding | When artifact created |

**Moment Detection Rules:**

```python
# Rule: DETECT_FIRST_SIGNAL_v1
def detect_first_signal(events: list[AgentEventV1], session: SessionContext) -> bool:
    if session.event_count > 10:
        return False  # Not first anymore
    return any(
        e.event_type == EventType.ANALYSIS_COMPLETED
        for e in events[-5:]
    )

# Rule: DETECT_HESITATION_v1
def detect_hesitation(events: list[AgentEventV1], now: datetime) -> bool:
    if not events:
        return False
    last_action = max(
        (e.occurred_at for e in events if e.event_type == EventType.USER_ACTION),
        default=None
    )
    if last_action is None:
        return False
    idle_seconds = (now - last_action).total_seconds()
    return idle_seconds >= 8.0

# Rule: DETECT_OVERLOAD_v1
def detect_overload(events: list[AgentEventV1]) -> bool:
    recent = [e for e in events if is_within_seconds(e, 60)]
    undo_count = sum(1 for e in recent if e.payload.get("action") == "undo")
    return undo_count >= 3

# Rule: DETECT_FINDING_v1
def detect_finding(events: list[AgentEventV1]) -> bool:
    return any(
        e.event_type == EventType.ATTENTION_REQUESTED
        for e in events[-3:]
    )
```

### 2.3 Step C: Choose Intervention Class

Intervention classes map to `AttentionAction` values.

| Class | ID | AttentionAction | Description |
|-------|----|--------------------|-------------|
| None | `I0_NONE` | (no directive) | No intervention needed |
| Point | `I1_POINT` | `INSPECT` | Gentle highlight, FYI |
| Review | `I2_REVIEW` | `REVIEW` | Please look at this |
| Compare | `I3_COMPARE` | `COMPARE` | Compare two things |
| Decide | `I4_DECIDE` | `DECIDE` / `CONFIRM` | User must choose |
| Intervene | `I5_INTERVENE` | `INTERVENE` / `ABORT` | Safety-critical |

**Default Moment → Intervention Mapping:**

| Moment | Default Intervention | Rationale |
|--------|---------------------|-----------|
| `MOMENT_FIRST_SIGNAL` | `I1_POINT` | Teach "one panel, one trace" |
| `MOMENT_HESITATION` | `I1_POINT` | Offer single next micro-action |
| `MOMENT_OVERLOAD` | `I2_REVIEW` | Reduce options, reset view |
| `MOMENT_DECISION_REQUIRED` | `I4_DECIDE` | Present 2–3 options max |
| `MOMENT_FINDING` | `I2_REVIEW` | "Potential wolf tone at X Hz" |
| `MOMENT_ERROR` | `I2_REVIEW` | Summarize + recovery action |

```python
# Rule: MOMENT_TO_INTERVENTION_v1
MOMENT_INTERVENTION_MAP = {
    "MOMENT_FIRST_SIGNAL": "I1_POINT",
    "MOMENT_HESITATION": "I1_POINT",
    "MOMENT_OVERLOAD": "I2_REVIEW",
    "MOMENT_DECISION_REQUIRED": "I4_DECIDE",
    "MOMENT_FINDING": "I2_REVIEW",
    "MOMENT_ERROR": "I2_REVIEW",
}

def choose_intervention(moment: str) -> str:
    return MOMENT_INTERVENTION_MAP.get(moment, "I0_NONE")
```

### 2.4 Step D: Apply UWSM Policy Gates

UWSM dimensions gate intervention intensity.

**Gate Rules:**

```python
# Rule: UWSM_MAX_DIRECTIVES_v1
def max_simultaneous_directives(uwsm: UWSMv1) -> int:
    cls = uwsm.get_dimension(PreferenceDimension.COGNITIVE_LOAD_SENSITIVITY)
    if cls.value >= 0.7 and cls.confidence >= 0.5:
        return 1  # High sensitivity → single directive
    return 2

# Rule: UWSM_DIRECTIVE_VERBOSITY_v1
def directive_verbosity(uwsm: UWSMv1) -> str:
    gd = uwsm.get_dimension(PreferenceDimension.GUIDANCE_DENSITY)
    if gd.value <= 0.3:
        return "summary_only"
    elif gd.value <= 0.6:
        return "summary_plus_hint"
    else:
        return "full_explanation"

# Rule: UWSM_PROACTIVE_SUGGESTIONS_v1
def allow_proactive_suggestions(uwsm: UWSMv1) -> bool:
    it = uwsm.get_dimension(PreferenceDimension.INITIATIVE_TOLERANCE)
    # user_led (0.0-0.3) → only after user asks
    # shared_control (0.3-0.7) → suggest at moments
    # agent_led (0.7-1.0) → suggest after most events
    return it.value >= 0.3 or it.confidence < 0.4  # Default to suggestions if uncertain
```

**Verbosity Templates:**

| Level | Template |
|-------|----------|
| `summary_only` | `"{summary}"` |
| `summary_plus_hint` | `"{summary}\n\nTry: {hint}"` |
| `full_explanation` | `"{summary}\n\n{detail}\n\nWhy it matters: {why}\n\nTry: {hint}"` |

### 2.5 Step E: Emit Output

Output depends on operating mode.

```python
# Rule: EMIT_OUTPUT_v1
def emit_output(
    mode: str,
    intervention: str,
    directive: AttentionDirectiveV1,
    analyzer_commands: list[dict],
) -> list[AgentEventV1]:

    if mode == "M0":  # Shadow
        return [AgentEventV1(
            event_type=EventType.SYSTEM_HEALTH,
            payload={
                "mode": "shadow",
                "would_have_emitted": directive.to_dict(),
            },
        )]

    elif mode == "M1":  # Advisory
        return [AgentEventV1(
            event_type=EventType.ATTENTION_REQUESTED,
            payload={"directive": directive.to_dict()},
        )]

    elif mode == "M2":  # Actuated
        events = [AgentEventV1(
            event_type=EventType.ATTENTION_REQUESTED,
            payload={"directive": directive.to_dict()},
        )]
        for cmd in analyzer_commands:
            events.append(AgentEventV1(
                event_type=EventType.USER_ACTION,  # Or new type
                payload={"analyzer_command": cmd},
            ))
        return events

    return []
```

---

## 3. Analyzer-Specific Policies

### 3.1 First-Time User Experience (FTUE) Policy

**Rule ID:** `POLICY_FTUE_ONE_TRACE_v1`

When `MOMENT_FIRST_SIGNAL` fires and user is in FTUE:

```python
def ftue_one_trace_policy(ctx: AnalyzerContext) -> list:
    """Simplify view to single panel/trace for new users."""
    commands = []
    directives = []

    if ctx.is_ftue and ctx.visible_panels > 1:
        # Hide all except primary
        commands.append({
            "command": "hide_all_except",
            "panel_id": ctx.primary_panel_id,
        })

    if ctx.visible_traces > 1:
        # Focus primary trace
        commands.append({
            "command": "focus_trace",
            "trace_id": ctx.primary_trace_id,
        })

    directives.append(AttentionDirectiveV1(
        directive_id=generate_directive_id(),
        action=AttentionAction.INSPECT,
        summary="Watch this line change when you tap",
        detail="This trace shows the frequency response. Try tapping the instrument.",
        focus=FocusTarget(
            target_type="trace",
            target_id=ctx.primary_trace_id,
        ),
        urgency=0.3,
        confidence=0.9,
    ))

    return commands, directives
```

### 3.2 Wolf Tone Finding Policy

**Rule ID:** `POLICY_WOLF_TONE_FINDING_v1`

When wolf detector emits finding:

```python
def wolf_tone_finding_policy(finding: dict) -> AttentionDirectiveV1:
    """Create attention directive for wolf tone detection."""
    freq_hz = finding["freq_hz"]
    confidence = finding["confidence"]

    urgency = 0.7 if confidence > 0.8 else 0.5

    return AttentionDirectiveV1(
        directive_id=generate_directive_id(),
        action=AttentionAction.REVIEW,
        summary=f"Potential wolf tone at {freq_hz:.0f}Hz",
        detail=(
            f"The analyzer detected a potential wolf tone at {freq_hz:.1f}Hz "
            f"with {confidence*100:.0f}% confidence. This frequency may cause "
            f"tonal issues in the B3-C4 range.\n\n"
            f"Consider adjusting bracing or soundboard thickness."
        ),
        focus=FocusTarget(
            target_type="spectrum_region",
            target_id=finding["peak_id"],
            highlight_region={
                "freq_hz": freq_hz,
                "bandwidth_hz": 10,
            },
        ),
        urgency=urgency,
        confidence=confidence,
        evidence_refs=[f"wolf_candidates_v1:{finding['bundle_sha256']}:{finding['peak_id']}"],
        source_tool="tap_tone_wolf_detector",
    )
```

### 3.3 Overload Recovery Policy

**Rule ID:** `POLICY_OVERLOAD_RECOVERY_v1`

When `MOMENT_OVERLOAD` fires:

```python
def overload_recovery_policy(ctx: SessionContext) -> tuple:
    """Reduce cognitive load when user is overwhelmed."""
    commands = [
        {"command": "reset_view"},
    ]

    directive = AttentionDirectiveV1(
        directive_id=generate_directive_id(),
        action=AttentionAction.REVIEW,
        summary="Let's simplify",
        detail=(
            "Looks like things got complex. I've reset the view to defaults.\n\n"
            "Would you like to:\n"
            "• Focus on one measurement at a time\n"
            "• Compare just two traces\n"
            "• Start a new analysis"
        ),
        focus=FocusTarget(
            target_type="session",
            target_id=ctx.session_id,
        ),
        urgency=0.6,
        confidence=0.8,
    )

    return commands, directive
```

---

## 4. Policy Debugging

### 4.1 Policy Trace Format

Every decision emits a trace for debugging:

```json
{
  "trace_id": "policy_trace_abc123",
  "timestamp": "2026-02-06T12:00:00Z",
  "input": {
    "events_count": 15,
    "session_id": "session_xyz",
    "mode": "M1"
  },
  "pipeline": {
    "step_a_normalize": {
      "session": {"event_count": 15},
      "tool": {"active_tool_id": "tap_tone_analyzer"}
    },
    "step_b_moments": ["MOMENT_FINDING"],
    "step_c_intervention": "I2_REVIEW",
    "step_d_uwsm_gates": {
      "max_directives": 2,
      "verbosity": "summary_plus_hint",
      "proactive_allowed": true
    },
    "step_e_output": {
      "directive_id": "attn_001",
      "action": "review"
    }
  },
  "rules_fired": [
    "DETECT_FINDING_v1",
    "MOMENT_TO_INTERVENTION_v1",
    "UWSM_DIRECTIVE_VERBOSITY_v1",
    "POLICY_WOLF_TONE_FINDING_v1"
  ]
}
```

### 4.2 Policy Test Cases

```python
# Test: FTUE user sees first analysis result
def test_ftue_first_signal():
    events = [
        AgentEventV1(event_type=EventType.ANALYSIS_COMPLETED, ...),
    ]
    session = SessionContext(event_count=1, is_ftue=True)

    moments = detect_moments(events, session)
    assert "MOMENT_FIRST_SIGNAL" in moments

    intervention = choose_intervention(moments[0])
    assert intervention == "I1_POINT"

# Test: Overload triggers recovery
def test_overload_triggers_recovery():
    events = [
        AgentEventV1(event_type=EventType.USER_ACTION, payload={"action": "undo"}),
        AgentEventV1(event_type=EventType.USER_ACTION, payload={"action": "undo"}),
        AgentEventV1(event_type=EventType.USER_ACTION, payload={"action": "undo"}),
    ]

    assert detect_overload(events) is True

# Test: High cognitive load limits directives
def test_high_load_limits_directives():
    uwsm = UWSMv1()
    uwsm.dimensions[PreferenceDimension.COGNITIVE_LOAD_SENSITIVITY] = DimensionState(
        dimension=PreferenceDimension.COGNITIVE_LOAD_SENSITIVITY,
        value=0.8,
        confidence=0.7,
    )

    assert max_simultaneous_directives(uwsm) == 1
```

---

## 5. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-02-06 | Initial release |

---

---

## Appendix A: Intervention Intensity Scale

| ID | AttentionAction |
|-----|--------|
| `I0_NONE` | Do nothing |
| `I1_POINT` | INSPECT |
| `I2_REVIEW` | REVIEW |
| `I3_COMPARE` | COMPARE |
| `I4_DECIDE` | DECIDE / CONFIRM |
| `I5_INTERVENE` | INTERVENE / ABORT (safety only) |

---

## Appendix B: UWSM Gate Constraints (Quick Reference)

UWSM dimensions constrain intensity:

- High `cognitive_load_sensitivity` → max 1 directive
- `initiative_tolerance=user_led` → suggest only after user request
- Low `guidance_density` → minimal explanation

---

## Appendix C: Mode → Allowed Outputs

| Mode | Allowed Outputs |
|----|----------------|
| M0 | Diagnostic `AgentEventV1` only |
| M1 | `AttentionDirectiveV1` |
| M2 | Directive + Analyzer Attention commands |

---

## Appendix D: Moment → Default Action (Quick Reference)

| Moment | Default Action |
|------|----------------|
| FIRST_SIGNAL | INSPECT |
| HESITATION | INSPECT |
| OVERLOAD | REVIEW |
| DECISION_REQUIRED | DECIDE |
| FINDING | REVIEW |
| ERROR | REVIEW |

---

## Appendix E: One-Trace Onboarding Rule

**Rule ID:** `POLICY_FTUE_ONE_TRACE_v1`

If:
- FIRST_SIGNAL
- First-time user
- Analyzer supports attention commands

Then:
- `hide_all_except(primary_panel)`
- `focus_trace(primary_trace)`
- Emit directive explaining *what to watch*

---

## Appendix F: Safety Rules

- Never emit more than one critical directive at once
- Never override explicit user dismissal
- Never escalate urgency without new evidence
- Never act without capability confirmation

---

## Appendix G: Diagnostic Output Format

Every decision emits an internal diagnostic record:

```json
{
  "moment": "OVERLOAD",
  "uwsm_snapshot": "...",
  "selected_action": "REVIEW",
  "mode": "M1",
  "suppressed_actions": ["COMPARE"],
  "rule_id": "POLICY_OVERLOAD_REVIEW_v1"
}
```

---

## Appendix H: Non-Goals

- **No learning** — UWSM lives elsewhere
- **No personalization updates** — handled by UWSM updater
- **No tool orchestration** — tools are autonomous

This document defines **decision policy only**.

---

**Document Version:** 1.0.0
**Last Updated:** 2026-02-06
**See Also:** [UWSM_UPDATE_RULES_V1.md](UWSM_UPDATE_RULES_V1.md), [EVENT_MOMENTS_CATALOG_V1.md](EVENT_MOMENTS_CATALOG_V1.md)
