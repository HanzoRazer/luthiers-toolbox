# Event Moments Catalog v1

**Version**: 1.0.0
**Status**: Normative
**Effective**: 2026-02-06
**Audience**: Agent developers, UWSM implementers, orchestration engineers

---

## 1. Overview

A **Moment** is a named pattern recognized over a sequence of `AgentEventV1` emissions. Moments abstract raw event streams into semantically meaningful user behavior signals that drive UWSM updates and operating mode transitions.

### 1.1 Design Principles

| Principle | Description |
|-----------|-------------|
| **Pattern-Based** | Moments emerge from event sequences, not individual events |
| **Causally Linked** | Each moment specifies which UWSM dimensions it updates |
| **Mode-Aware** | Moment detection may vary by operating mode |
| **Privacy-Preserving** | Moment metadata respects event privacy layers |
| **Testable** | Each moment has explicit trigger conditions and test cases |

### 1.2 Moment Lifecycle

```
Events → Pattern Matcher → Moment Detected → UWSM Update → Mode Check → Action
```

---

## 2. Moment Definitions

### 2.1 FIRST_SIGNAL

**ID**: `MOM-001`
**Category**: Onboarding
**Description**: User's first meaningful interaction with an analyzer or agent capability.

#### Trigger Pattern

```yaml
trigger:
  event_sequence:
    - event_type: ANALYSIS_STARTED
      constraints:
        - source.component NOT IN user_history.components_used
  window: single_event
```

#### UWSM Updates

| Dimension | Update | Rationale |
|-----------|--------|-----------|
| `trust_agent_suggestions` | No change | Insufficient data |
| `detail_preference` | Set to 0.5 (neutral) | No preference signal yet |
| `automation_comfort` | Set to 0.3 (conservative) | Start cautious |

#### Operating Mode Implications

- **M0 (Shadow)**: Log moment, no user-visible action
- **M1 (Advisory)**: May show "Welcome to [Analyzer]" tooltip
- **M2 (Actuated)**: Same as M1, plus initialize user-specific defaults

#### Test Cases

| Test ID | Scenario | Expected |
|---------|----------|----------|
| `MOM-001-T1` | User runs wolf_detector for first time | FIRST_SIGNAL emitted for wolf_detector |
| `MOM-001-T2` | User runs wolf_detector second time | No FIRST_SIGNAL (already seen) |
| `MOM-001-T3` | User runs chladni_analyzer (new tool) | FIRST_SIGNAL emitted for chladni_analyzer |

---

### 2.2 HESITATION

**ID**: `MOM-002`
**Category**: Uncertainty
**Description**: User pauses or backtracks after receiving an agent suggestion, indicating uncertainty or disagreement.

#### Trigger Pattern

```yaml
trigger:
  event_sequence:
    - event_type: ATTENTION_DIRECTIVE_SHOWN
      label: directive_shown
    - event_type: USER_ACTION
      constraints:
        - action_type IN [UNDO, DISMISS, HOVER_LONG, NO_ACTION]
        - occurred_at - directive_shown.occurred_at < 30s
  window: 30_seconds
  min_occurrences: 1
```

#### UWSM Updates

| Dimension | Update | Rationale |
|-----------|--------|-----------|
| `trust_agent_suggestions` | Decrease by 0.05 | User didn't follow suggestion |
| `detail_preference` | Increase by 0.03 | May want more explanation |
| `interruption_tolerance` | Decrease by 0.02 | User didn't appreciate interruption |

#### Operating Mode Implications

- **M0 (Shadow)**: Log for pattern analysis
- **M1 (Advisory)**: Reduce suggestion frequency temporarily
- **M2 (Actuated)**: Fall back to M1 for this capability

#### Hysteresis

- **Cooldown**: 60 seconds before another HESITATION can fire
- **Threshold**: 3 HESITATION moments in 5 minutes triggers TRUST_EROSION

#### Test Cases

| Test ID | Scenario | Expected |
|---------|----------|----------|
| `MOM-002-T1` | User dismisses wolf tone alert within 10s | HESITATION detected |
| `MOM-002-T2` | User hovers on suggestion for 20s then clicks away | HESITATION detected |
| `MOM-002-T3` | User accepts suggestion within 5s | No HESITATION |
| `MOM-002-T4` | User ignores suggestion for 45s | No HESITATION (outside window) |

---

### 2.3 OVERLOAD

**ID**: `MOM-003`
**Category**: Cognitive Load
**Description**: User receives too many signals in a short period, risking cognitive overload and disengagement.

#### Trigger Pattern

```yaml
trigger:
  event_sequence:
    - event_type: ATTENTION_DIRECTIVE_SHOWN
      count: ">= 5"
  window: 60_seconds
  aggregate: count
```

#### UWSM Updates

| Dimension | Update | Rationale |
|-----------|--------|-----------|
| `interruption_tolerance` | Decrease by 0.15 | User is overwhelmed |
| `trust_agent_suggestions` | Decrease by 0.05 | Suggestions feel spammy |
| `batch_vs_realtime` | Shift toward batch by 0.1 | Prefer consolidated updates |

#### Operating Mode Implications

- **M0 (Shadow)**: Log pattern, no action
- **M1 (Advisory)**: Throttle suggestions for 5 minutes
- **M2 (Actuated)**: Pause automated actions, switch to M1

#### Recovery

- OVERLOAD suppression lifts after:
  - 5 minutes of reduced activity, OR
  - User explicitly requests more suggestions

#### Test Cases

| Test ID | Scenario | Expected |
|---------|----------|----------|
| `MOM-003-T1` | 5 wolf tone alerts in 30 seconds | OVERLOAD detected |
| `MOM-003-T2` | 4 alerts in 60 seconds | No OVERLOAD (below threshold) |
| `MOM-003-T3` | 5 alerts spread over 90 seconds | No OVERLOAD (outside window) |
| `MOM-003-T4` | OVERLOAD fires, then 3 more alerts | Alerts suppressed for 5 min |

---

### 2.4 CONFIDENCE_CLIMB

**ID**: `MOM-004`
**Category**: Trust Building
**Description**: User consistently accepts agent suggestions, indicating growing trust.

#### Trigger Pattern

```yaml
trigger:
  event_sequence:
    - event_type: ATTENTION_DIRECTIVE_SHOWN
      label: directive
    - event_type: USER_ACTION
      constraints:
        - action_type IN [ACCEPT, APPLY, CONFIRM]
        - correlation_id == directive.directive_id
  window: session
  min_occurrences: 5
  success_rate: ">= 0.8"  # 4 of 5 accepted
```

#### UWSM Updates

| Dimension | Update | Rationale |
|-----------|--------|-----------|
| `trust_agent_suggestions` | Increase by 0.1 | Consistent positive signals |
| `automation_comfort` | Increase by 0.05 | User comfortable with agent actions |
| `interruption_tolerance` | Increase by 0.03 | User engages with interruptions |

#### Operating Mode Implications

- **M0 (Shadow)**: Log pattern, prepare for M1 transition
- **M1 (Advisory)**: Consider M2 transition for specific capabilities
- **M2 (Actuated)**: Increase automation scope

#### Mode Transition Gate

CONFIDENCE_CLIMB is a prerequisite for M1→M2 transition:

```python
def can_transition_to_m2(uwsm, capability_id):
    return (
        uwsm.dimensions["trust_agent_suggestions"] >= 0.7 and
        uwsm.dimensions["automation_comfort"] >= 0.6 and
        moment_history.count("CONFIDENCE_CLIMB", capability_id) >= 2
    )
```

#### Test Cases

| Test ID | Scenario | Expected |
|---------|----------|----------|
| `MOM-004-T1` | User accepts 5 of 6 suggestions in session | CONFIDENCE_CLIMB detected |
| `MOM-004-T2` | User accepts 3 of 5 suggestions | No CONFIDENCE_CLIMB (60% < 80%) |
| `MOM-004-T3` | User accepts 4 of 4 suggestions | No CONFIDENCE_CLIMB (need 5+) |
| `MOM-004-T4` | CONFIDENCE_CLIMB fires twice | M2 transition gate opens |

---

### 2.5 TRUST_EROSION

**ID**: `MOM-005`
**Category**: Trust Degradation
**Description**: Sustained pattern of user rejecting or ignoring agent suggestions.

#### Trigger Pattern

```yaml
trigger:
  event_sequence:
    - moment_type: HESITATION
      count: ">= 3"
  window: 300_seconds  # 5 minutes
  aggregate: count
```

OR

```yaml
trigger:
  event_sequence:
    - event_type: ATTENTION_DIRECTIVE_SHOWN
      label: directive
    - event_type: USER_ACTION
      constraints:
        - action_type IN [REJECT, DISMISS, OVERRIDE]
        - correlation_id == directive.directive_id
  window: session
  min_occurrences: 5
  rejection_rate: ">= 0.6"  # 3 of 5 rejected
```

#### UWSM Updates

| Dimension | Update | Rationale |
|-----------|--------|-----------|
| `trust_agent_suggestions` | Decrease by 0.2 | Strong negative signal |
| `automation_comfort` | Decrease by 0.15 | User wants manual control |
| `interruption_tolerance` | Decrease by 0.1 | Suggestions unwelcome |

#### Operating Mode Implications

- **M0 (Shadow)**: Log, no action
- **M1 (Advisory)**: Reduce suggestion frequency by 50%
- **M2 (Actuated)**: **Mandatory fallback to M1**

#### Recovery Path

Trust recovery requires explicit positive signals:
1. 3x CONFIDENCE_CLIMB moments, OR
2. User explicitly re-enables automation, OR
3. 7-day decay brings dimensions back to neutral

#### Test Cases

| Test ID | Scenario | Expected |
|---------|----------|----------|
| `MOM-005-T1` | 3 HESITATION moments in 4 minutes | TRUST_EROSION detected |
| `MOM-005-T2` | User rejects 4 of 6 suggestions | TRUST_EROSION detected |
| `MOM-005-T3` | User rejects 2 of 6 suggestions | No TRUST_EROSION (33% < 60%) |
| `MOM-005-T4` | TRUST_EROSION in M2 mode | Automatic fallback to M1 |

---

### 2.6 WORKFLOW_SHIFT

**ID**: `MOM-006`
**Category**: Behavior Change
**Description**: User's workflow pattern changes significantly, indicating learning or preference shift.

#### Trigger Pattern

```yaml
trigger:
  condition: statistical_shift
  metrics:
    - session_duration_delta: "> 50%"
    - tool_sequence_change: "> 3 tools reordered"
    - time_between_actions_delta: "> 30%"
  window: 7_days
  comparison: rolling_average
```

#### UWSM Updates

| Dimension | Update | Rationale |
|-----------|--------|-----------|
| All dimensions | Decrease confidence by 20% | Model may be stale |
| `detail_preference` | Reset toward 0.5 | Re-learn preference |

#### Operating Mode Implications

- **M0 (Shadow)**: Log pattern change
- **M1 (Advisory)**: Temporarily increase explanation detail
- **M2 (Actuated)**: Consider fallback to M1 until new pattern stabilizes

#### Stabilization

WORKFLOW_SHIFT suppression lifts after:
- 5 consistent sessions matching new pattern, OR
- User explicitly confirms preference change

#### Test Cases

| Test ID | Scenario | Expected |
|---------|----------|----------|
| `MOM-006-T1` | Average session length doubles over 7 days | WORKFLOW_SHIFT detected |
| `MOM-006-T2` | User starts using tools in new order | WORKFLOW_SHIFT detected |
| `MOM-006-T3` | Minor session length variation (±15%) | No WORKFLOW_SHIFT |
| `MOM-006-T4` | WORKFLOW_SHIFT fires | UWSM confidence drops 20% |

---

### 2.7 MASTERY_PLATEAU

**ID**: `MOM-007`
**Category**: Expertise
**Description**: User demonstrates consistent expert-level behavior, indicating mastery.

#### Trigger Pattern

```yaml
trigger:
  event_sequence:
    - event_type: ANALYSIS_COMPLETED
      constraints:
        - result.quality_score >= 0.9
        - source.component == target_analyzer
  window: 30_days
  min_occurrences: 20
  consistency: "> 0.85"  # 17 of 20 high-quality
```

#### UWSM Updates

| Dimension | Update | Rationale |
|-----------|--------|-----------|
| `detail_preference` | Decrease by 0.2 | Expert needs less explanation |
| `trust_agent_suggestions` | Cap at 0.7 | Expert may know better |
| `error_handling_style` | Shift toward terse | Expert can interpret errors |

#### Operating Mode Implications

- **M0 (Shadow)**: Log mastery pattern
- **M1 (Advisory)**: Reduce explanation verbosity
- **M2 (Actuated)**: Increase agent confidence in user corrections

#### Expert Mode Unlocks

MASTERY_PLATEAU enables:
1. Advanced UI features (if gated)
2. Reduced confirmation dialogs
3. Higher default risk tolerance for suggestions

#### Test Cases

| Test ID | Scenario | Expected |
|---------|----------|----------|
| `MOM-007-T1` | 18 of 20 analyses score >= 0.9 over 30 days | MASTERY_PLATEAU detected |
| `MOM-007-T2` | 15 of 20 analyses score >= 0.9 | No MASTERY_PLATEAU (75% < 85%) |
| `MOM-007-T3` | 20 analyses in 15 days | Partial signal (continue tracking) |
| `MOM-007-T4` | MASTERY_PLATEAU + new tool | Mastery doesn't transfer |

---

## 3. Moment Detection Engine

### 3.1 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Event Stream (AgentEventV1)                  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Sliding Window Buffer                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ [evt_n-9] [evt_n-8] ... [evt_n-1] [evt_n]               │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Pattern Matchers                            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│  │ HESITATION  │ │  OVERLOAD   │ │ CONFIDENCE  │  ...          │
│  │   Matcher   │ │   Matcher   │ │   Matcher   │               │
│  └─────────────┘ └─────────────┘ └─────────────┘               │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Moment Emitter                              │
│  - Applies hysteresis                                            │
│  - Respects cooldowns                                            │
│  - Emits MomentDetectedV1                                        │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      UWSM Updater                                │
│  - Applies dimension updates                                     │
│  - Recalculates confidence                                       │
│  - Checks mode transition gates                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 MomentDetectedV1 Schema

```python
@dataclass
class MomentDetectedV1:
    moment_id: str           # Unique ID (e.g., "mom_abc123")
    moment_type: str         # HESITATION, OVERLOAD, etc.
    detected_at: str         # ISO 8601 timestamp
    trigger_events: list     # Event IDs that triggered this moment
    uwsm_updates: dict       # Dimension changes applied
    mode_implications: str   # Description of mode impact
    confidence: float        # Detection confidence (0.0-1.0)
    privacy_layer: int       # Inherited from trigger events
    schema_version: str = "1.0.0"
```

### 3.3 Hysteresis Rules

| Moment | Cooldown | Max per Session | Max per Day |
|--------|----------|-----------------|-------------|
| FIRST_SIGNAL | N/A (once per tool) | 1 per tool | N/A |
| HESITATION | 60 seconds | 10 | 30 |
| OVERLOAD | 5 minutes | 3 | 10 |
| CONFIDENCE_CLIMB | 30 minutes | 5 | 15 |
| TRUST_EROSION | 10 minutes | 3 | 5 |
| WORKFLOW_SHIFT | 24 hours | 1 | 1 |
| MASTERY_PLATEAU | 7 days | 1 per tool | N/A |

---

## 4. Cross-Analyzer Moment Aggregation

### 4.1 Scope Rules

| Moment | Scope | Rationale |
|--------|-------|-----------|
| FIRST_SIGNAL | Per-analyzer | Each tool is new |
| HESITATION | Per-analyzer | Trust is tool-specific |
| OVERLOAD | Global | Cognitive load is global |
| CONFIDENCE_CLIMB | Per-analyzer | Trust builds per-tool |
| TRUST_EROSION | Per-analyzer, affects global | Erosion spreads |
| WORKFLOW_SHIFT | Global | Workflow is holistic |
| MASTERY_PLATEAU | Per-analyzer | Mastery is tool-specific |

### 4.2 Cross-Analyzer Propagation

When TRUST_EROSION fires for one analyzer:
1. Primary analyzer: Full UWSM update
2. Related analyzers: 50% of UWSM update
3. Unrelated analyzers: No update

"Related" is determined by `ToolCapabilityV1.related_tools` field.

---

## 5. Privacy Considerations

### 5.1 Moment Privacy Layers

Moments inherit the highest privacy layer from their trigger events:

```python
def compute_moment_privacy(trigger_events):
    return max(e.privacy_layer for e in trigger_events)
```

### 5.2 Moment Retention

| Privacy Layer | Retention |
|---------------|-----------|
| 0 (Ephemeral) | Session only |
| 1 (Session) | 24 hours |
| 2 (Short-term) | 7 days |
| 3 (Learning) | 90 days |
| 4 (Profile) | Until user deletion |
| 5 (Cohort-only) | Aggregated, no individual |

---

## 6. Implementation Checklist

### 6.1 Moment Detection Engine

- [ ] Sliding window buffer with configurable size
- [ ] Pattern matcher registry
- [ ] Hysteresis enforcement
- [ ] Cooldown tracking
- [ ] MomentDetectedV1 emission

### 6.2 Per-Moment Implementation

| Moment | Pattern Matcher | UWSM Updater | Mode Handler | Tests |
|--------|-----------------|--------------|--------------|-------|
| FIRST_SIGNAL | [ ] | [ ] | [ ] | [ ] |
| HESITATION | [ ] | [ ] | [ ] | [ ] |
| OVERLOAD | [ ] | [ ] | [ ] | [ ] |
| CONFIDENCE_CLIMB | [ ] | [ ] | [ ] | [ ] |
| TRUST_EROSION | [ ] | [ ] | [ ] | [ ] |
| WORKFLOW_SHIFT | [ ] | [ ] | [ ] | [ ] |
| MASTERY_PLATEAU | [ ] | [ ] | [ ] | [ ] |

### 6.3 Integration Points

- [ ] Event ingestion from `AgentEventV1` stream
- [ ] UWSM update hooks
- [ ] Operating mode transition triggers
- [ ] Privacy layer enforcement
- [ ] Moment persistence (respecting retention)

---

## 7. Appendix: Event Types Reference

### 7.1 Events That Trigger Moments

| Event Type | Triggers Moments |
|------------|------------------|
| `ANALYSIS_STARTED` | FIRST_SIGNAL |
| `ANALYSIS_COMPLETED` | MASTERY_PLATEAU |
| `ATTENTION_DIRECTIVE_SHOWN` | HESITATION, OVERLOAD, CONFIDENCE_CLIMB, TRUST_EROSION |
| `USER_ACTION` | HESITATION, CONFIDENCE_CLIMB, TRUST_EROSION |
| `SESSION_STARTED` | WORKFLOW_SHIFT (comparison) |
| `SESSION_ENDED` | WORKFLOW_SHIFT (comparison) |

### 7.2 User Action Types

| Action Type | Description |
|-------------|-------------|
| `ACCEPT` | User accepts suggestion |
| `REJECT` | User explicitly rejects |
| `DISMISS` | User closes without action |
| `APPLY` | User applies suggested change |
| `CONFIRM` | User confirms automated action |
| `UNDO` | User reverses recent action |
| `OVERRIDE` | User overrides agent decision |
| `HOVER_LONG` | User hovers > 10 seconds |
| `NO_ACTION` | User doesn't interact within window |

---

## 8. Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-02-06 | Initial release |

---

## 9. Related Documents

- [AGENT_DECISION_POLICY_V1.md](./AGENT_DECISION_POLICY_V1.md) - Operating mode definitions
- [UWSM_UPDATE_RULES_V1.md](./UWSM_UPDATE_RULES_V1.md) - Dimension update mechanics
- [AGENTIC_CONTRACTS_ENGINEER_HANDOFF.md](./AGENTIC_CONTRACTS_ENGINEER_HANDOFF.md) - Contract specifications
