# Advisory Mode Thin Slice — Engineer Handoff (M1) v1.0

**Status:** Ready for implementation
**Objective:** Ship a **single, low-risk UI surface** that renders `AttentionDirectiveV1` in **Advisory mode** (M1) using the existing spine:
- `detect_moments()` → `decide()` → UI renders directive
- No analyzer/tool state changes
- Minimal new event emissions: user feedback only

---

## 0) Scope and Non-Goals

### In scope
- Add a **Coach Bubble / Side Panel** UI component that renders **at most one** directive at a time
- Wire M1 decision outputs from policy engine to the UI
- Emit minimal `AgentEventV1` feedback events (`helpful`, `too_much`)
- Record and replay sessions with `replay.py` for deterministic validation

### Non-goals (explicit)
- ❌ No analyzer attention commands (M2)
- ❌ No tool parameter changes
- ❌ No exports or persistence changes
- ❌ No new "meaning" event types (keep payload factual)
- ❌ No multi-step plans; single directive only

---

## 1) Rollout Strategy

### Feature flags
- `AGENTIC_MODE`:
  - `M0` = shadow (no UI)
  - `M1` = advisory (render directive)
- `AGENTIC_FTUE_ENABLED` (bool) — optional guard to restrict to FTUE flows
- `AGENTIC_RECORD_EVENTS` (bool) — dev/QA recording to JSONL

### Launch phases
1. **Dev**: M1 enabled for internal users only, recording enabled
2. **QA**: M1 enabled for test cohort, recording enabled
3. **Dogfood**: M1 enabled for small % behind remote config
4. **Public**: Expand cohort gradually

**Rollback:** flip `AGENTIC_MODE=M0` remotely (no code rollback required)

---

## 2) Architecture Wiring (Thin Slice)

### Data flow (M1)
1. UI/Tools emit `AgentEventV1`
2. Experience Shell consumes events and builds a per-session timeline
3. Moment detector derives 0–1 top moment
4. Policy engine decides a single directive (Advisory output)
5. UI renders directive
6. User feedback emits `AgentEventV1.user_feedback` events

**Important:** The UI renderer must be dumb. It should not infer. It only renders the directive object.

---

## 3) Required Interfaces

### Input: Policy output contract (minimum)
The UI expects a decision payload shaped like:

```json
{
  "attention_action": "INSPECT",
  "emit_directive": true,
  "directive": {
    "action": "INSPECT",
    "title": "Inspect this",
    "detail": "Focus on one signal and make a small change."
  },
  "diagnostic": {
    "rule_id": "POLICY_FIRST_SIGNAL_INSPECT_v1"
  }
}
```

### UI contract: `AttentionDirectiveV1` (render-only fields)

Required:

* `action` (INSPECT/REVIEW/COMPARE/DECIDE/CONFIRM)
* `title` (string)

Optional:

* `detail` (string, may be empty under low guidance density)

---

## 4) UI Component: Coach Bubble (Minimal)

### Placement options (pick one and keep it stable)

* Option A: Bottom-right floating bubble
* Option B: Right-side panel "Coach"
* Option C: Top banner inline below toolbar

**Recommendation:** Option B (Side panel) if analyzer UI is dense; Option A if workspace is spacious.

### UI behaviors (must)

* Shows **0 or 1** directive at a time
* Has **two buttons**:
  * "Helpful" (thumbs up)
  * "Too much" (thumbs down)
* Has dismiss "X" (dismiss is not the same as "Too much")

### UI behaviors (must not)

* Must not show chains of suggestions
* Must not auto-open other tools
* Must not animate aggressively (avoid "nagging")

---

## 5) Event Emission Additions (M1 Feedback)

### Emit `AgentEventV1` on feedback clicks

#### Helpful click

```json
{
  "event_type": "user_feedback",
  "payload": {
    "feedback": "helpful",
    "directive_action": "INSPECT",
    "rule_id": "POLICY_FIRST_SIGNAL_INSPECT_v1"
  }
}
```

#### Too much click

```json
{
  "event_type": "user_feedback",
  "payload": {
    "feedback": "too_much",
    "directive_action": "REVIEW",
    "rule_id": "POLICY_OVERLOAD_REVIEW_v1"
  }
}
```

#### Dismiss click (separate signal)

```json
{
  "event_type": "user_action",
  "payload": {
    "action": "dismiss_directive",
    "directive_action": "INSPECT",
    "rule_id": "POLICY_FIRST_SIGNAL_INSPECT_v1"
  }
}
```

**Notes**

* Keep payload small and factual.
* Never include free text.
* Always include `rule_id` so we can debug policy impact.

---

## 6) PR Boundaries (Cross-Repo Safe)

### PR 1 — UI (Experience Shell / luthiers-toolbox)

**Changes**

* Add Coach Bubble component
* Wire it to a per-session "directive store"
* Emit feedback events

**Must not**

* Touch analyzer internals
* Add new tool APIs
* Add persistence changes

**Acceptance**

* In M1, directive renders at correct time
* Feedback buttons emit events (confirmed in recording/replay)

---

### PR 2 — Orchestration (luthiers-toolbox agentic spine)

**Changes**

* Ensure `detect_moments()` and `decide()` are callable from UI layer
* Ensure policy returns the minimal output structure (already present in reference impl)
* Ensure `uwsm_update.py` consumes `user_feedback` events and nudges `cognitive_load_sensitivity`

**Must not**

* Add ML inference
* Add tool-specific logic beyond capability gates

**Acceptance**

* Tests pass (see Section 8)
* Replay produces deterministic outputs

---

### PR 3 — Event Recording (dev/QA only, optional if already built)

**Changes**

* Add JSONL recorder behind `AGENTIC_RECORD_EVENTS`
* Ensure `session_id` + `occurred_at` always present

**Acceptance**

* A real session is saved as JSONL and replayable

---

## 7) Minimal Implementation Steps (Suggested Order)

1. **Create directive store**

   * per session: `latest_decision` object
   * updated on each event tick or debounced interval (e.g., every 250ms)

2. **Wire event stream**

   * feed event list to `detect_moments(events)`
   * feed top moment + current UWSM snapshot to `decide(...)` with `mode="M1"`

3. **Render directive**

   * if `emit_directive=false` → hide bubble
   * else render `directive.title` and `directive.detail`

4. **Emit feedback events**

   * On button click, emit `user_feedback` event
   * Append to event stream
   * UWSM update should incorporate it deterministically

5. **Record JSONL sessions**

   * confirm with replay harness

---

## 8) Test Plan (Must be Green)

### Local

Install:

```bash
pip install -r requirements-dev.txt
```

Run spine tests:

```bash
make test-spine
```

This includes:

* Contract parity tests
* Moment tests
* Policy tests
* Replay smoke test using `tests/fixtures/smoke_session.jsonl`

### Manual smoke test

1. Launch app with:

   * `AGENTIC_MODE=M1`
   * `AGENTIC_RECORD_EVENTS=1`
2. Start FTUE session
3. Confirm:

   * Coach bubble appears once a moment occurs (FIRST_SIGNAL or HESITATION)
   * Click "Too much"
   * Observe directive reduces verbosity (or next directive suppressed) in same session
4. Export JSONL
5. Replay:

```bash
python -m app.agentic.spine.replay recordings/<session>.jsonl --mode M0 --verbose
```

Confirm:

* Same top moment detected
* `would_have_emitted` contains the expected directive
* UWSM audits include `UWSM_CLS_EXPLICIT_TOO_MUCH_v1` after "Too much"

---

## 9) Acceptance Criteria (Hard)

### Functional

* ✅ In `AGENTIC_MODE=M1`, the UI renders **exactly one** directive at a time
* ✅ In `AGENTIC_MODE=M0`, no directive is rendered
* ✅ "Helpful" and "Too much" buttons emit `AgentEventV1.user_feedback` events
* ✅ No analyzer/tool state is modified by the agent

### Determinism

* ✅ Given the same recorded JSONL, replay output is stable (same moment, same decision)
* ✅ No ordering issues: events are sorted by `occurred_at` and not mutated in place

### Safety

* ✅ No raw text stored in telemetry layers (beyond Layer 1 if you have it)
* ✅ No new event types encode interpretation ("confusion", "expertise", "intent")

### Cross-repo survivability

* ✅ No changes required in analyzer/tool repos for M1 beyond existing event emission
* ✅ No new APIs demanded from other teams

---

## 10) Known Follow-ons (Not part of this PR set)

* M2 actuated attention commands (focus/hide/reset) behind capability gates
* Multi-moment streams and multi-directive planning (deferred)
* A/B evaluation wiring (TFMA/TFIS/CSS) once advisory is stable

---

## Appendix A — Recommended Default UI Copy (safe + neutral)

**INSPECT**

* Title: "Inspect this"
* Detail: "Watch this one signal while you make a small change."

**REVIEW**

* Title: "Let's simplify"
* Detail: "We'll focus on one panel to keep it manageable."

**DECIDE**

* Title: "Choose one option"
* Detail: "Pick A or B to continue."

(Keep it short. Avoid sounding like the system is judging the user.)

---

**End of Document**
