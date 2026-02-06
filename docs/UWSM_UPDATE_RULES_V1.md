# UWSM Update Rules Spec v1

**Version:** 1.0.0
**Date:** 2026-02-06
**Status:** Phase 2 Spine Document
**Depends On:** `UWSMv1`, `AgentEventV1`, `PreferenceDimension`

---

## 0. Purpose

Define **exactly how UWSMv1 updates** from the event stream without hidden model magic.

**Inputs:**
- `AgentEventV1` events (behavioral signals)
- `USER_PREFERENCE_UPDATED` events (explicit signals)

**Outputs:**
- Updated UWSM dimensions
- Per-dimension confidence
- Decay parameters
- Audit trail of which rule fired

**Design Principles:**
- Deterministic: Same inputs → same outputs
- Replayable: Can reconstruct UWSM state from event log
- Auditable: Every update traces to a rule ID
- Privacy-safe: UWSM stays at Layer 0 (local-only)

---

## 1. Dimensions (v1.1)

### 1.1 Core Dimensions

| Dimension | ID | Range | Description |
|-----------|----|-------|-------------|
| Guidance Density | `guidance_density` | 0.0–1.0 | How much explanation/help |
| Initiative Tolerance | `initiative_tolerance` | 0.0–1.0 | Who leads (user vs agent) |
| Cognitive Load Sensitivity | `cognitive_load_sensitivity` | 0.0–1.0 | How much to simplify |
| Exploration Style | `exploration_style` | 0.0–1.0 | Depth-first vs breadth-first |
| Risk Posture | `risk_posture` | 0.0–1.0 | Conservative vs adventurous |
| Feedback Style | `feedback_style` | 0.0–1.0 | Gentle vs direct |

### 1.2 Analyzer-Specific Dimension (v1.1 Addition)

| Dimension | ID | Range | Description |
|-----------|----|-------|-------------|
| Representation Preference | `representation_preference` | enum | visual/numeric/narrative/mixed |

### 1.3 Value Interpretation

Each dimension has semantic ranges:

```python
# guidance_density
# 0.0-0.3: minimal (just essentials)
# 0.3-0.6: moderate (summary + hints)
# 0.6-1.0: detailed (full explanations)

# initiative_tolerance
# 0.0-0.3: user_led (only respond when asked)
# 0.3-0.7: shared_control (suggest at key moments)
# 0.7-1.0: agent_led (proactive suggestions)

# cognitive_load_sensitivity
# 0.0-0.3: low (show everything)
# 0.3-0.6: medium (reasonable defaults)
# 0.6-1.0: high (simplify aggressively)

# exploration_style
# 0.0-0.3: deep_focus (one thing at a time)
# 0.3-0.6: iterative (incremental refinement)
# 0.6-1.0: dabble (try many things quickly)

# risk_posture
# 0.0-0.3: cautious (simulate first, undo available)
# 0.3-0.6: balanced (reasonable risks)
# 0.6-1.0: adventurous (big changes, learn by doing)

# feedback_style
# 0.0-0.3: gentle (encouraging, soft)
# 0.3-0.6: neutral (factual)
# 0.6-1.0: direct (blunt, efficient)
```

---

## 2. Update Mechanics

### 2.1 Evidence Events

Each evidence event has:

```python
@dataclass
class EvidenceSignal:
    dimension: PreferenceDimension
    direction: float          # Target value (0.0–1.0)
    signal_strength: float    # Weight (0.0–1.0)
    source: str               # "explicit" or "behavioral"
    event_id: str             # Source event for audit
    timestamp: datetime
```

### 2.2 Confidence Update Rules

| Source | Confidence Delta | Cap |
|--------|------------------|-----|
| Explicit (user choice) | +0.20 | 0.90 |
| Behavioral (inferred) | +0.05 | 0.80 |
| Contradiction | -0.15 | floor 0.20 |

```python
# Rule: CONFIDENCE_UPDATE_v1
def update_confidence(
    current: float,
    source: str,
    is_contradiction: bool,
) -> float:
    if is_contradiction:
        return max(0.20, current - 0.15)

    if source == "explicit":
        return min(0.90, current + 0.20)
    else:  # behavioral
        return min(0.80, current + 0.05)
```

### 2.3 Value Update with Hysteresis

To prevent rapid flipping, value changes require:
1. Confidence ≥ 0.60
2. New value dominant for 2 consecutive evidence windows

```python
# Rule: HYSTERESIS_GATE_v1
@dataclass
class HysteresisState:
    pending_value: float
    pending_count: int  # Consecutive windows favoring this value

def apply_hysteresis(
    current_value: float,
    current_confidence: float,
    new_evidence_value: float,
    hysteresis: HysteresisState,
) -> tuple[float, HysteresisState]:
    """Apply hysteresis to prevent value flipping."""

    # Not enough confidence to change
    if current_confidence < 0.60:
        return current_value, HysteresisState(new_evidence_value, 1)

    # Check if evidence is consistent
    value_diff = abs(new_evidence_value - hysteresis.pending_value)
    if value_diff < 0.15:  # Same direction
        new_count = hysteresis.pending_count + 1
    else:
        new_count = 1

    # Need 2 consecutive windows to change
    if new_count >= 2:
        return new_evidence_value, HysteresisState(new_evidence_value, new_count)
    else:
        return current_value, HysteresisState(new_evidence_value, new_count)
```

### 2.4 Decay Function

Confidence decays over time to allow adaptation:

```python
# Rule: CONFIDENCE_DECAY_v1
def decay_confidence(
    confidence: float,
    days_elapsed: float,
    half_life_days: float,
    floor: float = 0.10,
) -> float:
    """Apply exponential decay to confidence."""
    decay_factor = 0.5 ** (days_elapsed / half_life_days)
    return max(floor, confidence * decay_factor)
```

**Half-Life Values (v1):**

| Dimension | Half-Life (days) | Rationale |
|-----------|-----------------|-----------|
| `cognitive_load_sensitivity` | 7 | Changes quickly with fatigue/context |
| `exploration_style` | 10 | Varies by project phase |
| `risk_posture` | 10 | Varies by project phase |
| `guidance_density` | 14 | Moderately stable |
| `representation_preference` | 14 | Moderately stable |
| `initiative_tolerance` | 21 | Slow to change |
| `feedback_style` | 21 | Personality-like, stable |

---

## 3. Dimension-Specific Update Rules

### 3.1 Guidance Density (`guidance_density`)

**Explicit Signals:**

| Event | Direction | Strength | Rule ID |
|-------|-----------|----------|---------|
| User selects "Guide me" | 0.8 | 1.0 | `GD_EXPLICIT_GUIDE_ME_v1` |
| User selects "Stay light" | 0.2 | 1.0 | `GD_EXPLICIT_STAY_LIGHT_v1` |
| User clicks "Show more" | 0.7 | 0.8 | `GD_EXPLICIT_SHOW_MORE_v1` |
| User clicks "Less detail" | 0.3 | 0.8 | `GD_EXPLICIT_LESS_DETAIL_v1` |

**Behavioral Signals:**

| Pattern | Direction | Strength | Rule ID |
|---------|-----------|----------|---------|
| Expands help panel 3+ times | 0.7 | 0.5 | `GD_BEHAVIOR_EXPAND_HELP_v1` |
| Dismisses tooltips 3+ times | 0.3 | 0.5 | `GD_BEHAVIOR_DISMISS_TOOLTIPS_v1` |
| Reads full explanation (scroll + dwell) | 0.7 | 0.3 | `GD_BEHAVIOR_READ_EXPLANATION_v1` |
| Skips explanations (fast dismiss) | 0.3 | 0.3 | `GD_BEHAVIOR_SKIP_EXPLANATION_v1` |

```python
# Rule: GD_BEHAVIOR_EXPAND_HELP_v1
def detect_expand_help_pattern(events: list[AgentEventV1]) -> EvidenceSignal | None:
    expand_count = sum(
        1 for e in events[-20:]
        if e.event_type == EventType.USER_ACTION
        and e.payload.get("action") == "expand_help"
    )
    if expand_count >= 3:
        return EvidenceSignal(
            dimension=PreferenceDimension.GUIDANCE_DENSITY,
            direction=0.7,
            signal_strength=0.5,
            source="behavioral",
            event_id=events[-1].event_id,
            timestamp=events[-1].occurred_at,
        )
    return None
```

### 3.2 Initiative Tolerance (`initiative_tolerance`)

**Explicit Signals:**

| Event | Direction | Strength | Rule ID |
|-------|-----------|----------|---------|
| User selects "Let me lead" | 0.1 | 1.0 | `IT_EXPLICIT_USER_LED_v1` |
| User selects "Suggest for me" | 0.7 | 1.0 | `IT_EXPLICIT_AGENT_LED_v1` |
| User selects "Work together" | 0.5 | 1.0 | `IT_EXPLICIT_SHARED_v1` |

**Behavioral Signals:**

| Pattern | Direction | Strength | Rule ID |
|---------|-----------|----------|---------|
| Ignores 3 suggestions in a row | 0.2 | 0.5 | `IT_BEHAVIOR_IGNORE_SUGGESTIONS_v1` |
| Accepts suggestion and continues | 0.6 | 0.3 | `IT_BEHAVIOR_ACCEPT_SUGGESTION_v1` |
| Explicitly dismisses suggestion | 0.3 | 0.4 | `IT_BEHAVIOR_DISMISS_SUGGESTION_v1` |
| Asks "What should I do?" | 0.7 | 0.5 | `IT_BEHAVIOR_ASK_GUIDANCE_v1` |

```python
# Rule: IT_BEHAVIOR_IGNORE_SUGGESTIONS_v1
def detect_ignore_suggestions_pattern(events: list[AgentEventV1]) -> EvidenceSignal | None:
    # Find ATTENTION_REQUESTED events
    attention_events = [
        e for e in events
        if e.event_type == EventType.ATTENTION_REQUESTED
    ][-5:]

    if len(attention_events) < 3:
        return None

    # Check if they were acknowledged
    acknowledged_ids = {
        e.payload.get("directive_id")
        for e in events
        if e.event_type == EventType.ATTENTION_ACKNOWLEDGED
    }

    ignored_count = sum(
        1 for e in attention_events
        if e.payload.get("directive", {}).get("directive_id") not in acknowledged_ids
    )

    if ignored_count >= 3:
        return EvidenceSignal(
            dimension=PreferenceDimension.INITIATIVE_TOLERANCE,
            direction=0.2,  # Shift toward user_led
            signal_strength=0.5,
            source="behavioral",
            event_id=attention_events[-1].event_id,
            timestamp=attention_events[-1].occurred_at,
        )
    return None
```

### 3.3 Cognitive Load Sensitivity (`cognitive_load_sensitivity`)

**Explicit Signals:**

| Event | Direction | Strength | Rule ID |
|-------|-----------|----------|---------|
| User indicates "Too much" | 0.8 | 1.0 | `CLS_EXPLICIT_TOO_MUCH_v1` |
| User indicates "I can handle more" | 0.3 | 1.0 | `CLS_EXPLICIT_HANDLE_MORE_v1` |

**Behavioral Signals:**

| Pattern | Direction | Strength | Rule ID |
|---------|-----------|----------|---------|
| Long idle after tool reveal (>8s) | 0.7 | 0.4 | `CLS_BEHAVIOR_LONG_IDLE_v1` |
| Rapid tool close after open (<2s) | 0.8 | 0.5 | `CLS_BEHAVIOR_RAPID_CLOSE_v1` |
| Smooth action sequence (no idle) | 0.3 | 0.3 | `CLS_BEHAVIOR_SMOOTH_FLOW_v1` |
| Multiple undos in sequence | 0.7 | 0.5 | `CLS_BEHAVIOR_UNDO_SEQUENCE_v1` |

```python
# Rule: CLS_BEHAVIOR_LONG_IDLE_v1
def detect_long_idle_pattern(
    events: list[AgentEventV1],
    now: datetime,
) -> EvidenceSignal | None:
    # Find last ARTIFACT_CREATED or ANALYSIS_COMPLETED
    reveal_events = [
        e for e in events
        if e.event_type in (EventType.ARTIFACT_CREATED, EventType.ANALYSIS_COMPLETED)
    ]
    if not reveal_events:
        return None

    last_reveal = reveal_events[-1]

    # Find next user action after reveal
    next_action = None
    for e in events:
        if e.occurred_at > last_reveal.occurred_at and e.event_type == EventType.USER_ACTION:
            next_action = e
            break

    if next_action:
        idle_seconds = (next_action.occurred_at - last_reveal.occurred_at).total_seconds()
    else:
        idle_seconds = (now - last_reveal.occurred_at).total_seconds()

    if idle_seconds >= 8.0:
        return EvidenceSignal(
            dimension=PreferenceDimension.COGNITIVE_LOAD_SENSITIVITY,
            direction=0.7,
            signal_strength=0.4,
            source="behavioral",
            event_id=last_reveal.event_id,
            timestamp=last_reveal.occurred_at,
        )
    return None
```

### 3.4 Exploration Style (`exploration_style`)

**Behavioral Signals Only** (no explicit UI in v1):

| Pattern | Direction | Strength | Rule ID |
|---------|-----------|----------|---------|
| Many tool switches, shallow changes | 0.8 (dabble) | 0.4 | `ES_BEHAVIOR_DABBLE_v1` |
| Repeated tweaks to same parameter | 0.5 (iterative) | 0.4 | `ES_BEHAVIOR_ITERATIVE_v1` |
| Long dwell + deep parameter changes | 0.2 (deep_focus) | 0.4 | `ES_BEHAVIOR_DEEP_FOCUS_v1` |

```python
# Rule: ES_BEHAVIOR_DABBLE_v1
def detect_dabble_pattern(events: list[AgentEventV1]) -> EvidenceSignal | None:
    recent = events[-30:]

    # Count unique tools touched
    tools_touched = set()
    for e in recent:
        if e.event_type in (EventType.ARTIFACT_CREATED, EventType.ANALYSIS_COMPLETED):
            tools_touched.add(e.source.component)

    # Count parameter changes
    param_changes = sum(
        1 for e in recent
        if e.payload.get("action") == "parameter_changed"
    )

    # Dabble: many tools, few deep changes per tool
    if len(tools_touched) >= 3 and param_changes < len(tools_touched) * 2:
        return EvidenceSignal(
            dimension=PreferenceDimension.EXPLORATION_STYLE,
            direction=0.8,
            signal_strength=0.4,
            source="behavioral",
            event_id=recent[-1].event_id,
            timestamp=recent[-1].occurred_at,
        )
    return None
```

### 3.5 Risk Posture (`risk_posture`)

**Behavioral Signals:**

| Pattern | Direction | Strength | Rule ID |
|---------|-----------|----------|---------|
| Undo spikes (3+ in 60s) | 0.2 (cautious) | 0.5 | `RP_BEHAVIOR_UNDO_SPIKE_v1` |
| Uses compare/simulate before commit | 0.3 (cautious) | 0.4 | `RP_BEHAVIOR_SIMULATE_FIRST_v1` |
| Large changes without undo | 0.8 (adventurous) | 0.4 | `RP_BEHAVIOR_BOLD_CHANGES_v1` |
| Exports without preview | 0.7 (adventurous) | 0.3 | `RP_BEHAVIOR_QUICK_EXPORT_v1` |

### 3.6 Feedback Style (`feedback_style`)

**Explicit Signals Only** (to avoid misreading tone):

| Event | Direction | Strength | Rule ID |
|-------|-----------|----------|---------|
| User selects "Be direct" | 0.8 | 1.0 | `FS_EXPLICIT_DIRECT_v1` |
| User selects "Be gentle" | 0.2 | 1.0 | `FS_EXPLICIT_GENTLE_v1` |
| User selects "Just the facts" | 0.5 | 1.0 | `FS_EXPLICIT_NEUTRAL_v1` |

**Default:** 0.5 (neutral) until explicit preference set.

### 3.7 Representation Preference (`representation_preference`)

**Behavioral Signals:**

| Pattern | Direction | Strength | Rule ID |
|---------|-----------|----------|---------|
| Switches to table view | `numeric` | 0.5 | `RP_BEHAVIOR_TABLE_VIEW_v1` |
| Zooms/isolates traces | `visual` | 0.5 | `RP_BEHAVIOR_ZOOM_TRACE_v1` |
| Opens explanation panel | `narrative` | 0.5 | `RP_BEHAVIOR_EXPLANATION_v1` |
| Frequently alternates views | `mixed` | 0.4 | `RP_BEHAVIOR_ALTERNATES_v1` |

```python
# Rule: RP_BEHAVIOR_TABLE_VIEW_v1
def detect_table_view_preference(events: list[AgentEventV1]) -> str | None:
    recent = events[-20:]
    table_switches = sum(
        1 for e in recent
        if e.payload.get("action") == "switch_view"
        and e.payload.get("view") == "table"
    )
    if table_switches >= 2:
        return "numeric"
    return None
```

---

## 4. UWSM Update Pipeline

### 4.1 Full Update Flow

```python
# Rule: UWSM_UPDATE_PIPELINE_v1
def update_uwsm(
    uwsm: UWSMv1,
    events: list[AgentEventV1],
    now: datetime,
) -> tuple[UWSMv1, list[UpdateRecord]]:
    """Full UWSM update pipeline."""
    records = []

    # 1. Apply decay to all dimensions
    for dim in PreferenceDimension:
        state = uwsm.dimensions[dim]
        days_elapsed = (now - state.last_updated).days if state.last_updated else 0
        half_life = HALF_LIFE_DAYS[dim]
        decayed_confidence = decay_confidence(
            state.confidence,
            days_elapsed,
            half_life,
        )
        if decayed_confidence != state.confidence:
            records.append(UpdateRecord(
                dimension=dim,
                rule_id="CONFIDENCE_DECAY_v1",
                prev_confidence=state.confidence,
                new_confidence=decayed_confidence,
            ))
            state.confidence = decayed_confidence

    # 2. Extract evidence signals from events
    signals = extract_all_signals(events, now)

    # 3. Apply each signal
    for signal in signals:
        state = uwsm.dimensions[signal.dimension]

        # Check for contradiction
        is_contradiction = (
            state.confidence >= 0.5 and
            abs(signal.direction - state.value) > 0.4
        )

        # Update confidence
        new_confidence = update_confidence(
            state.confidence,
            signal.source,
            is_contradiction,
        )

        # Apply hysteresis for value update
        new_value, new_hysteresis = apply_hysteresis(
            state.value,
            new_confidence,
            signal.direction,
            state.hysteresis,
        )

        # Record update
        if new_value != state.value or new_confidence != state.confidence:
            records.append(UpdateRecord(
                dimension=signal.dimension,
                rule_id=signal.rule_id,
                event_id=signal.event_id,
                prev_value=state.value,
                prev_confidence=state.confidence,
                new_value=new_value,
                new_confidence=new_confidence,
            ))

        # Apply update
        uwsm.dimensions[signal.dimension] = DimensionState(
            dimension=signal.dimension,
            value=new_value,
            confidence=new_confidence,
            signal_count=state.signal_count + 1,
            last_updated=now,
            hysteresis=new_hysteresis,
        )

    uwsm.last_updated = now
    return uwsm, records
```

### 4.2 Signal Extraction

```python
# Rule: EXTRACT_ALL_SIGNALS_v1
def extract_all_signals(
    events: list[AgentEventV1],
    now: datetime,
) -> list[EvidenceSignal]:
    """Extract all evidence signals from event stream."""
    signals = []

    # Guidance Density
    if sig := detect_expand_help_pattern(events):
        signals.append(sig)
    if sig := detect_dismiss_tooltips_pattern(events):
        signals.append(sig)

    # Initiative Tolerance
    if sig := detect_ignore_suggestions_pattern(events):
        signals.append(sig)
    if sig := detect_accept_suggestion_pattern(events):
        signals.append(sig)

    # Cognitive Load Sensitivity
    if sig := detect_long_idle_pattern(events, now):
        signals.append(sig)
    if sig := detect_rapid_close_pattern(events):
        signals.append(sig)
    if sig := detect_undo_sequence_pattern(events):
        signals.append(sig)

    # Exploration Style
    if sig := detect_dabble_pattern(events):
        signals.append(sig)
    if sig := detect_deep_focus_pattern(events):
        signals.append(sig)

    # Risk Posture
    if sig := detect_undo_spike_pattern(events):
        signals.append(sig)
    if sig := detect_bold_changes_pattern(events):
        signals.append(sig)

    # Explicit preferences (from USER_PREFERENCE_UPDATED events)
    for event in events:
        if event.event_type == EventType.USER_PREFERENCE_UPDATED:
            signals.extend(extract_explicit_signals(event))

    return signals
```

---

## 5. Audit Trail

### 5.1 Update Record Format

```json
{
  "record_id": "uwsm_update_abc123",
  "timestamp": "2026-02-06T12:00:00Z",
  "dimension": "cognitive_load_sensitivity",
  "rule_id": "CLS_BEHAVIOR_LONG_IDLE_v1",
  "event_id": "evt_xyz789",
  "prev": {
    "value": 0.5,
    "confidence": 0.45
  },
  "next": {
    "value": 0.5,
    "confidence": 0.50
  },
  "signal": {
    "direction": 0.7,
    "strength": 0.4,
    "source": "behavioral"
  }
}
```

### 5.2 Audit Log Storage

```python
# UWSM audit records are stored in the same event log
# Privacy: Layer 0 (local-only, never synced)

def emit_uwsm_update_record(record: UpdateRecord) -> AgentEventV1:
    return AgentEventV1(
        event_id=f"uwsm_{uuid.uuid4().hex[:12]}",
        event_type=EventType.USER_PREFERENCE_UPDATED,
        source=EventSource(
            repo="luthiers-toolbox",
            component="uwsm_updater",
        ),
        payload={
            "update_record": record.to_dict(),
        },
        privacy_layer=0,  # Local-only
    )
```

---

## 6. Test Cases

### 6.1 Confidence Update Tests

```python
def test_explicit_signal_increases_confidence():
    state = DimensionState(value=0.5, confidence=0.4)
    signal = EvidenceSignal(source="explicit", direction=0.8)

    new_conf = update_confidence(state.confidence, signal.source, False)
    assert new_conf == 0.6  # +0.20

def test_behavioral_signal_capped_at_080():
    state = DimensionState(value=0.5, confidence=0.75)
    signal = EvidenceSignal(source="behavioral", direction=0.7)

    new_conf = update_confidence(state.confidence, signal.source, False)
    assert new_conf == 0.80  # Capped

def test_contradiction_decreases_confidence():
    state = DimensionState(value=0.2, confidence=0.7)
    signal = EvidenceSignal(source="explicit", direction=0.9)  # Big jump

    new_conf = update_confidence(state.confidence, signal.source, True)
    assert new_conf == 0.55  # -0.15
```

### 6.2 Hysteresis Tests

```python
def test_hysteresis_requires_two_windows():
    state = DimensionState(value=0.5, confidence=0.7)
    hysteresis = HysteresisState(pending_value=0.8, pending_count=1)

    # First evidence toward 0.8
    new_val, new_hyst = apply_hysteresis(0.5, 0.7, 0.8, hysteresis)
    assert new_val == 0.5  # Not changed yet
    assert new_hyst.pending_count == 2

    # Second evidence toward 0.8
    new_val, new_hyst = apply_hysteresis(0.5, 0.7, 0.8, new_hyst)
    assert new_val == 0.8  # Now changed
    assert new_hyst.pending_count == 3

def test_hysteresis_resets_on_direction_change():
    hysteresis = HysteresisState(pending_value=0.8, pending_count=2)

    # Evidence in different direction
    new_val, new_hyst = apply_hysteresis(0.5, 0.7, 0.3, hysteresis)
    assert new_val == 0.5  # No change
    assert new_hyst.pending_value == 0.3
    assert new_hyst.pending_count == 1  # Reset
```

### 6.3 Decay Tests

```python
def test_decay_after_half_life():
    conf = decay_confidence(
        confidence=0.8,
        days_elapsed=14,  # Equal to half-life
        half_life_days=14,
    )
    assert abs(conf - 0.4) < 0.01  # Halved

def test_decay_respects_floor():
    conf = decay_confidence(
        confidence=0.2,
        days_elapsed=100,
        half_life_days=7,
        floor=0.10,
    )
    assert conf == 0.10  # Floor
```

### 6.4 Pattern Detection Tests

```python
def test_detect_long_idle():
    events = [
        AgentEventV1(
            event_type=EventType.ANALYSIS_COMPLETED,
            occurred_at=datetime(2026, 2, 6, 12, 0, 0),
        ),
    ]
    now = datetime(2026, 2, 6, 12, 0, 10)  # 10 seconds later

    signal = detect_long_idle_pattern(events, now)
    assert signal is not None
    assert signal.dimension == PreferenceDimension.COGNITIVE_LOAD_SENSITIVITY
    assert signal.direction == 0.7

def test_detect_ignore_suggestions():
    events = [
        AgentEventV1(event_type=EventType.ATTENTION_REQUESTED, payload={"directive": {"directive_id": "1"}}),
        AgentEventV1(event_type=EventType.ATTENTION_REQUESTED, payload={"directive": {"directive_id": "2"}}),
        AgentEventV1(event_type=EventType.ATTENTION_REQUESTED, payload={"directive": {"directive_id": "3"}}),
        # No ATTENTION_ACKNOWLEDGED events
    ]

    signal = detect_ignore_suggestions_pattern(events)
    assert signal is not None
    assert signal.dimension == PreferenceDimension.INITIATIVE_TOLERANCE
    assert signal.direction == 0.2  # Shift to user_led
```

---

## 7. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-02-06 | Initial release |
| 1.1.0 | TBD | Add `representation_preference` dimension |

---

**Document Version:** 1.0.0
**Last Updated:** 2026-02-06
**See Also:** [AGENT_DECISION_POLICY_V1.md](AGENT_DECISION_POLICY_V1.md), [EVENT_MOMENTS_CATALOG_V1.md](EVENT_MOMENTS_CATALOG_V1.md)
