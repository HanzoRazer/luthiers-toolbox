# Agent Decision Policy Tests — v1.0

These tests validate `AGENT_DECISION_POLICY_V1.md` policy mappings and gates.

## Inputs
- Detected moment
- UWSM snapshot
- Mode (M0/M1/M2)
- Tool capability flags

## Output
- Intervention class and AttentionAction
- Whether analyzer attention commands are issued (M2 only)
- Suppressions due to UWSM gates

---

## Moment → Default Action Mapping

### POLICY_001 — FIRST_SIGNAL maps to INSPECT
**Given**
- Moment: FIRST_SIGNAL
- Mode: M1
- UWSM: default (medium guidance, shared_control, medium load)

**Then**
- Emit `AttentionDirectiveV1.action = INSPECT`
- Intervention class `I1_POINT`

---

### POLICY_002 — HESITATION maps to INSPECT
**Given**
- Moment: HESITATION

**Then**
- Action = INSPECT

---

### POLICY_003 — OVERLOAD maps to REVIEW
**Given**
- Moment: OVERLOAD

**Then**
- Action = REVIEW
- Intervention class `I2_REVIEW`

---

### POLICY_004 — DECISION_REQUIRED maps to DECIDE
**Given**
- Moment: DECISION_REQUIRED

**Then**
- Action = DECIDE (or CONFIRM depending on tool payload)
- Intervention class `I4_DECIDE`

---

### POLICY_005 — FINDING maps to REVIEW
**Given**
- Moment: FINDING

**Then**
- Action = REVIEW

---

### POLICY_006 — ERROR maps to REVIEW (recovery guidance)
**Given**
- Moment: ERROR

**Then**
- Action = REVIEW
- Directive includes recovery path (implementation-specific)

---

## UWSM Gates

### GATE_001 — High cognitive load limits directives to 1
**Given**
- Moment: FINDING (would produce directive)
- UWSM: cognitive_load_sensitivity = very_high
- Mode: M1

**Then**
- Exactly one directive emitted
- Any secondary suggestions suppressed

---

### GATE_002 — user_led initiative suppresses proactive suggestions
**Given**
- Moment: HESITATION
- UWSM: initiative_tolerance = user_led
- Mode: M1

**Then**
- Either:
  - No directive emitted, OR
  - INSPECT directive emitted with UI prompt "Want a suggestion?"
- No multi-step plan suggestion

---

### GATE_003 — Low guidance density produces summary-only
**Given**
- Moment: FIRST_SIGNAL
- UWSM: guidance_density = very_low

**Then**
- Directive.detail is empty or minimal
- No "why it matters" paragraph

---

## Operating Modes

### MODE_001 — M0 emits diagnostic only (no ATTENTION_REQUESTED)
**Given**
- Mode: M0 (Shadow)
- Moment: FINDING

**Then**
- Emit `AgentEventV1` diagnostic payload `{would_have_emitted: <directive>}`
- Do NOT emit `ATTENTION_REQUESTED`

---

### MODE_002 — M1 emits directive but no analyzer command
**Given**
- Mode: M1
- Moment: FIRST_SIGNAL
- Capability: agent_can_adjust_view = true

**Then**
- Emit directive (ATTENTION_REQUESTED)
- No analyzer attention command is issued

---

### MODE_003 — M2 issues analyzer commands if allowed
**Given**
- Mode: M2
- Moment: FIRST_SIGNAL
- Capability: agent_can_adjust_view = true

**Then**
- Emit directive (ATTENTION_REQUESTED)
- Issue `hide_all_except` and `focus_trace` (One-Trace Onboarding Rule)

---

### MODE_004 — M2 falls back to M1 if tool denies view adjustment
**Given**
- Mode: M2
- Moment: FIRST_SIGNAL
- Capability: agent_can_adjust_view = false

**Then**
- Emit directive only
- No analyzer commands issued
- Diagnostic notes fallback reason

---

## Analyzer-Specific One-Trace Onboarding

### ANALYZER_001 — One-Trace Onboarding triggers on FIRST_SIGNAL + FTUE
**Given**
- FIRST_SIGNAL
- user is first-time
- Mode: M2
- Capability: agent_can_adjust_view = true

**Then**
- Commands issued:
  - hide_all_except(panel_id=<primary_panel>)
  - focus_trace(trace_id=<primary_trace>)
- Directive explains "watch this line" (INSPECT)

---

### ANALYZER_002 — One-Trace Onboarding suppressed if OVERLOAD
**Given**
- Moment priority: OVERLOAD detected at same time as FIRST_SIGNAL
- Mode: M2

**Then**
- OVERLOAD policy wins
- reset/simplify view (optional)
- No "watch this line" onboarding sequence
