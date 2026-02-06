# Agentic Spine Architecture — One Page (v1)

This diagram ties together:
- Contracts (thin waist)
- Moments catalog
- Decision policy
- UWSM updates
- Modes (Shadow/Advisory/Actuated)
- Privacy layers

---

## System Diagram

```mermaid
flowchart LR
  subgraph A[Tool / Analyzer Repos<br/>(e.g., tap_tone_pi)]
    CAP[ToolCapabilityV1<br/>manifest]
    EVT[AgentEventV1<br/>emit_* helpers]
    ATTNCAND[AttentionDirectiveV1<br/>(optional candidates)]
  end

  subgraph B[Experience Shell<br/>(luthiers-toolbox UI/API)]
    CONSUME[Event Consumer<br/>parse AgentEventV1]
    RENDER[UI Renderer<br/>Directives + Highlights]
    ATTNAPI[Analyzer Attention Adapter<br/>(commands)]
  end

  subgraph C[Agent Orchestration<br/>(luthiers-toolbox)]
    MOMENTS[Moment Detector<br/>EVENT_MOMENTS_CATALOG_V1]
    POLICY[Decision Policy Engine<br/>AGENT_DECISION_POLICY_V1]
    UWSM[UWSM Store + Update Engine<br/>UWSM_UPDATE_RULES_V1]
  end

  subgraph D[Telemetry / Evaluation]
    L0[L0 Raw Ephemeral<br/>(runtime only)]
    L2[L2 Telemetry<br/>(no content)]
    L3[L3 UWSM Snapshot]
    L4[L4 Redacted Diagnostics]
    L5[L5 Cohort Aggregates]
  end

  CAP -->|capabilities discovery| POLICY
  EVT -->|events| CONSUME
  CONSUME -->|normalized timeline| MOMENTS
  MOMENTS -->|moment + triggers| POLICY
  POLICY -->|directive decision| RENDER
  POLICY -->|M2 only: view commands| ATTNAPI
  ATTNAPI -->|focus/hide/highlight/reset| A

  CONSUME -->|behavior signals| UWSM
  UWSM -->|preferences snapshot| POLICY

  CONSUME --> L0
  L0 -->|redaction| L2
  UWSM --> L3
  POLICY --> L4
  L2 --> L5
  L3 --> L5
  L4 --> L5

  classDef thinwaist fill:#f3f3f3,stroke:#333,stroke-width:1px;
  class CAP,EVT,ATTNCAND thinwaist;
```

---

## Control Surfaces (What can change what)

### Tool/Analyzer Repos

* Own correctness, computation, measurement
* Emit events and optional attention candidates
* Declare capability + safety defaults

### Agent Orchestration

* Derives moments
* Chooses interventions (INSPECT/REVIEW/COMPARE/DECIDE)
* Updates UWSM deterministically
* Never performs tool internals

### Experience Shell

* Renders directives
* Optionally issues view-only attention commands (M2)

---

## Operating Modes (Gates)

* **M0 Shadow:** decisions logged only (no UI actions)
* **M1 Advisory:** directives rendered (no state changes)
* **M2 Actuated:** view-only attention commands (if capability allows)

---

## Privacy Spine

* **L0:** ephemeral runtime
* **L2:** interaction telemetry only
* **L3:** structured preferences only
* **L4:** templated diagnostics only
* **L5:** cohort aggregates only

---

## Spine Docs (Canonical References)

| Document | Purpose |
|----------|---------|
| `AGENTIC_CONTRACTS_ENGINEER_HANDOFF.md` | Contract specifications (ToolCapabilityV1, AttentionDirectiveV1, AgentEventV1, UWSMv1) |
| `EVENT_MOMENTS_CATALOG_V1.md` | Moment patterns + priority rules |
| `AGENT_DECISION_POLICY_V1.md` | Mode gates + action mappings |
| `UWSM_UPDATE_RULES_V1.md` | Deterministic preference updates |

---

## Test Suites

| Test File | Validates |
|-----------|-----------|
| `tests/test_moments_v1.md` | Moment detector Given/When/Then cases |
| `tests/test_policy_v1.md` | Policy engine gate + action mapping cases |

---

## Quick Reference: Data Flow

```
┌──────────────────┐
│   Analyzer Repo  │
│  (tap_tone_pi)   │
└────────┬─────────┘
         │ AgentEventV1
         ▼
┌──────────────────┐
│  Event Consumer  │
└────────┬─────────┘
         │ normalized events
         ▼
┌──────────────────┐     ┌──────────────────┐
│ Moment Detector  │────▶│   UWSM Updater   │
└────────┬─────────┘     └────────┬─────────┘
         │ moments                │ preferences
         ▼                        ▼
┌──────────────────────────────────────────┐
│           Decision Policy Engine          │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐   │
│  │   M0    │  │   M1    │  │   M2    │   │
│  │ Shadow  │  │Advisory │  │Actuated │   │
│  └─────────┘  └─────────┘  └─────────┘   │
└────────┬─────────────────────────┬───────┘
         │ directive               │ commands (M2)
         ▼                         ▼
┌──────────────────┐     ┌──────────────────┐
│   UI Renderer    │     │ Analyzer Adapter │
└──────────────────┘     └──────────────────┘
```

---

## Implementation Checklist

### Phase 1: Shadow Mode (M0)
- [ ] Event consumer parses AgentEventV1
- [ ] Moment detectors implemented
- [ ] Policy engine logs `would_have_emitted`
- [ ] UWSM updates from behavioral signals

### Phase 2: Advisory Mode (M1)
- [ ] UI renders AttentionDirectiveV1
- [ ] UWSM gates applied to directives
- [ ] Directive acknowledgment tracking

### Phase 3: Actuated Mode (M2)
- [ ] Analyzer Attention Adapter
- [ ] Capability-gated view commands
- [ ] Fallback to M1 on capability denial

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-02-06 | Initial release |
