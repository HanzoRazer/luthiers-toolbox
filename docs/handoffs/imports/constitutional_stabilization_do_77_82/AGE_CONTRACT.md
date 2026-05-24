# AGE Contract — Analyzer Guidance Engine Operational Rules

**Version:** 1.0.0  
**Date:** 2026-05-23  
**Constitutional Foundation:** ADR-0010 (Advisory Authority Constitutional Boundary)  
**Instrument Class:** DECISION SUPPORT

---

## Purpose

This document defines the operational contract for the Analyzer Guidance Engine (AGE). It derives from ADR-0010's constitutional framework and provides implementation-facing rules for AGE development and maintenance.

AGE is the highest-risk advisory system in tap-tone-pi because it sits at the boundary between measurement, interpretation, and operator guidance. This contract exists to prevent authority creep at that boundary.

---

## Constitutional Classification

AGE operates in the **Advisory** domain (per ADR-0010):

| Domain | AGE Role |
|--------|----------|
| Measurement | Read-only consumer |
| Advisory | Primary function |
| Interpretive | Secondary function (contextual framing) |
| Operator | Must not bypass or pre-empt |

---

## Operational Rules

### 1. Data Access

#### May Read

- Finished measurement data (post-analysis)
- Session state and history
- UWSM (User Working-Set Model) preferences
- Tool capability declarations
- Event streams (`AgentEventV1`)

#### May NOT Read

- In-progress measurement buffers
- Acquisition-phase data streams
- Raw audio before WAV I/O processing

### 2. Output Emissions

#### May Emit

- `AttentionDirectiveV1` to display layer (`GuidancePanelWidget`)
- Diagnostic events with `would_have_emitted` payloads (Shadow Mode)
- Policy trace records for debugging

#### May NOT Emit

- Artifacts to `viewer_pack_v1`
- Measurement modifications
- Session file mutations
- Calibration adjustments

### 3. System Behavior

#### Must Do

- Run API calls in daemon threads (never block Qt event loop)
- Fall back silently when `ANTHROPIC_API_KEY` is absent
- Fall back silently when API calls fail or timeout
- Respect UWSM gating rules (cognitive load, initiative tolerance)
- Include uncertainty qualifiers in all interpretive output

#### Must NOT Do

- Block measurement pipelines
- Require operator acknowledgment to proceed
- Escalate confidence into implied validation
- Persist advisory state to measurement artifacts
- Override explicit operator dismissal

### 4. Operating Mode Compliance

AGE must respect the operating mode gates defined in `AGENT_DECISION_POLICY_V1.md`:

| Mode | AGE Behavior |
|------|--------------|
| M0 (Shadow) | Log decisions only; no user-facing output |
| M1 (Advisory) | Emit directives; operator decides |
| M2 (Actuated) | Emit directives + view-only attention commands (if capability allows) |

In all modes, AGE:
- Never modifies measurement parameters
- Never starts/stops acquisition
- Never exports data
- Never persists analyzer state

### 5. Vocabulary Compliance

AGE output must comply with ADR-0010 vocabulary rules:

#### Forbidden in AGE Output

```
confirmed, verified, diagnosed, resolved, proven, certified,
validated, optimal, correct, approved, canonical, best, fixed
```

#### Required Patterns

- Use `"potential"` not `"definite"`
- Use `"may indicate"` not `"indicates"`
- Use `"suggested for review"` not `"requires attention"`
- Use `"possible anomaly"` not `"detected anomaly"`

### 6. Operator Sovereignty

AGE must preserve operator sovereignty at all times:

- Operator may ignore all AGE output
- Operator rejection is not an error condition
- AGE must not record operator choices as training signals without explicit consent
- AGE must not escalate urgency without new measurement evidence

### 7. Presentation Boundary

AGE outputs must render as attention guidance, not diagnostic conclusion.

#### Visual Rules

| Allowed | Forbidden |
|---------|-----------|
| Amber/neutral attention styling | Green "approved" styling |
| `REVIEW` / `INFO` badges | `VALIDATED` / `CONFIRMED` badges |
| Dot (●) attention indicator | Checkmark (✓) approval indicator |
| Urgency via intensity | Urgency via approval/rejection |

#### Confidence Display Rules

AGE confidence must not be displayed as measurement confidence:

| Forbidden | Required |
|-----------|----------|
| `Confidence: 85%` | `Advisory confidence: high` |
| `High confidence` (bare) | `Guidance confidence: high (heuristic)` |
| Confidence as validation | Confidence as guidance strength |

#### Text Rules

- AGE summaries must use hedged language ("may indicate", "suggests")
- AGE must not use definitive language ("confirms", "proves", "validates")
- Grade references must include "(heuristic)" qualifier

See: `docs/ADVISORY_PRESENTATION_BOUNDARY.md` for complete visual rules.

---

## API Integration Rules

### Claude API Calls

```python
# Correct: daemon thread, silent fallback
def _call_claude(user_prompt: str) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return ""  # Silent fallback
    try:
        # ... API call ...
    except Exception:
        return ""  # Silent fallback
```

### Stage-Aware Prompting

AGE must vary output verbosity by user stage:

| Stage | Verbosity |
|-------|-----------|
| `first_run` | Full explanation + next step |
| `novice` | Lutherie-contextualized explanation |
| `regular` | Brief interpretation |
| `expert` | Minimal (one sentence max, or nothing) |

### Suppression Logic

AGE must not repeat guidance already given in the current session:

```python
if directive_id in self._emitted_this_session:
    return None  # Suppress duplicate
```

---

## Relationship to Other Systems

### WolfAdvisor

WolfAdvisor is a peer DECISION SUPPORT system. AGE may:
- Consume WolfAdvisor findings as input
- Emit directives based on wolf-tone detection

AGE must NOT:
- Validate WolfAdvisor findings
- Canonize wolf-tone detection as confirmed

### viewer_pack_v1

AGE has no write access to viewer_pack_v1. This is enforced by:
- ADR-0009 export isolation
- `check_advisory_boundary.py` CI gate

### Agentic Spine

AGE is one component of the agentic spine. It must comply with:
- `ToolCapabilityV1` declarations
- `AgentEventV1` event contracts
- `AttentionDirectiveV1` output format
- `UWSMv1` preference gating

---

## Testing Requirements

AGE tests must verify:

1. **Silent fallback** — API unavailability does not raise exceptions
2. **Thread isolation** — API calls do not block main thread
3. **Vocabulary compliance** — No forbidden vocabulary in output strings
4. **Operator sovereignty** — No blocking on operator acknowledgment
5. **Mode compliance** — Correct behavior in M0/M1/M2 modes
6. **UWSM gating** — Respects cognitive load and initiative tolerance

---

## Change Control

Changes to AGE behavior require:

1. Review against ADR-0010 constitutional boundaries
2. Verification that no forbidden vocabulary is introduced
3. Confirmation that operator sovereignty is preserved
4. Test coverage for new behavior
5. Documentation update if contract rules change

---

## References

- ADR-0010: Advisory Authority Constitutional Boundary
- ADR-0009: Advisory Boundary — Measurement vs Decision Support
- `AGENT_DECISION_POLICY_V1.md`: Operating mode definitions
- `AGENTIC_SPINE_ARCHITECTURE_ONEPAGER.md`: System architecture
- `analyzer/guidance/engine.py`: AGE implementation

---

**Document Version:** 1.0.0  
**Last Updated:** 2026-05-23  
**Owner:** tap-tone-pi governance
