# Moment Detection Tests — v1.0

These tests validate `EVENT_MOMENTS_CATALOG_V1.md` moment detectors.
Format is Given/When/Then with minimal synthetic `AgentEventV1` events.

## Conventions
- `t+Ns` means seconds after session start.
- Event JSON is illustrative; only fields required by the detector are shown.
- Where your implementation differs (e.g., `occurred_at` vs `timestamp`), map accordingly.

---

## FIRST_SIGNAL

### FIRST_SIGNAL_001 — First analysis completion triggers FIRST_SIGNAL
**Given**
- Session starts, no prior signal events.

**When** the following events arrive:
```json
[
  {"event_id":"e1","event_type":"analysis_started","occurred_at":"t+1s"},
  {"event_id":"e2","event_type":"analysis_completed","occurred_at":"t+30s","payload":{"artifacts_created":["ods_snapshot_v1"]}}
]
```

**Then**
- Detected moments include: `FIRST_SIGNAL`
- `trigger_events` includes `e2`

---

### FIRST_SIGNAL_002 — First view rendered triggers FIRST_SIGNAL (preferred if present)

**When**
```json
[
  {"event_id":"e1","event_type":"analysis_completed","occurred_at":"t+10s"},
  {"event_id":"e2","event_type":"user_action","occurred_at":"t+12s","payload":{"action":"view_rendered","panel_id":"spectrum","trace_id":"main"}}
]
```

**Then**
- `FIRST_SIGNAL` triggers with `e2` as primary trigger event

---

### FIRST_SIGNAL_003 — Subsequent signals do not re-trigger FIRST_SIGNAL

**When**
```json
[
  {"event_id":"e1","event_type":"analysis_completed","occurred_at":"t+10s"},
  {"event_id":"e2","event_type":"analysis_completed","occurred_at":"t+60s"}
]
```

**Then**
- Only one `FIRST_SIGNAL` moment fires, referencing `e1`

---

## HESITATION

### HESITATION_001 — Idle after tool render triggers HESITATION

**Given**
- A tool view is rendered.

**When**
```json
[
  {"event_id":"e1","event_type":"user_action","occurred_at":"t+5s","payload":{"action":"view_rendered","panel_id":"spectrum"}},
  {"event_id":"e2","event_type":"idle_timeout","occurred_at":"t+14s","payload":{"idle_seconds":9}}
]
```

**Then**
- `HESITATION` moment fires
- `trigger_events` includes `e2`

---

### HESITATION_002 — Repeated hover with no action triggers HESITATION

**When**
```json
[
  {"event_id":"e1","event_type":"user_action","occurred_at":"t+5s","payload":{"action":"hover","target":"trace_panel","duration_ms":3200}},
  {"event_id":"e2","event_type":"user_action","occurred_at":"t+9s","payload":{"action":"hover","target":"trace_panel","duration_ms":3400}}
]
```

**Then**
- `HESITATION` moment fires
- Confidence is > 0.5 (implementation-specific threshold)

---

### HESITATION_003 — No HESITATION if parameter change occurs promptly

**When**
```json
[
  {"event_id":"e1","event_type":"user_action","occurred_at":"t+5s","payload":{"action":"view_rendered","panel_id":"spectrum"}},
  {"event_id":"e2","event_type":"user_action","occurred_at":"t+7s","payload":{"action":"parameter_changed","param":"brightness","value":0.6}}
]
```

**Then**
- No `HESITATION` moment is emitted

---

## OVERLOAD

### OVERLOAD_001 — Explicit "too much" feedback triggers OVERLOAD

**When**
```json
[
  {"event_id":"e1","event_type":"user_feedback","occurred_at":"t+20s","payload":{"feedback":"too_much"}}
]
```

**Then**
- `OVERLOAD` moment fires with trigger `e1`

---

### OVERLOAD_002 — Undo spike triggers OVERLOAD

**When**
```json
[
  {"event_id":"e1","event_type":"user_action","occurred_at":"t+21s","payload":{"action":"undo"}},
  {"event_id":"e2","event_type":"user_action","occurred_at":"t+22s","payload":{"action":"undo"}},
  {"event_id":"e3","event_type":"user_action","occurred_at":"t+23s","payload":{"action":"undo"}}
]
```

**Then**
- `OVERLOAD` moment fires
- Confidence reflects spike heuristic (e.g., >= 0.6)

---

### OVERLOAD_003 — Rapid open/close cycles trigger OVERLOAD

**When**
```json
[
  {"event_id":"e1","event_type":"tool_rendered","occurred_at":"t+5s","payload":{"tool_id":"tap_tone_analyzer"}},
  {"event_id":"e2","event_type":"tool_closed","occurred_at":"t+7s","payload":{"tool_id":"tap_tone_analyzer"}},
  {"event_id":"e3","event_type":"tool_rendered","occurred_at":"t+9s","payload":{"tool_id":"tap_tone_analyzer"}},
  {"event_id":"e4","event_type":"tool_closed","occurred_at":"t+11s","payload":{"tool_id":"tap_tone_analyzer"}}
]
```

**Then**
- `OVERLOAD` moment fires

---

## DECISION_REQUIRED

### DECISION_REQUIRED_001 — Tool emits DECISION_REQUIRED

**When**
```json
[
  {"event_id":"e1","event_type":"decision_required","occurred_at":"t+40s","payload":{"decision_id":"d1","options":["A","B"]}}
]
```

**Then**
- `DECISION_REQUIRED` moment fires with `e1`

---

### DECISION_REQUIRED_002 — Suppressed by ERROR if both present

**When**
```json
[
  {"event_id":"e1","event_type":"decision_required","occurred_at":"t+40s"},
  {"event_id":"e2","event_type":"system_error","occurred_at":"t+41s","payload":{"code":"E_IO"}}
]
```

**Then**
- Only `ERROR` moment fires (priority rule)
- `DECISION_REQUIRED` is suppressed

---

## FINDING

### FINDING_001 — Attention candidate available triggers FINDING

**When**
```json
[
  {"event_id":"e1","event_type":"artifact_created","occurred_at":"t+35s","payload":{"schema":"wolf_candidates_v1","confidence_max":0.87}},
  {"event_id":"e2","event_type":"attention_requested","occurred_at":"t+36s","payload":{"directive_id":"attn_1"}}
]
```

**Then**
- `FINDING` moment fires using `e2` (preferred) or `e1` (fallback)

---

### FINDING_002 — Low confidence candidate does not trigger FINDING

**When**
```json
[
  {"event_id":"e1","event_type":"artifact_created","occurred_at":"t+35s","payload":{"schema":"wolf_candidates_v1","confidence_max":0.42}}
]
```

**Then**
- No `FINDING` moment (assuming threshold > 0.6)

---

## ERROR

### ERROR_001 — analysis_failed triggers ERROR

**When**
```json
[
  {"event_id":"e1","event_type":"analysis_failed","occurred_at":"t+25s","payload":{"message":"file not found"}}
]
```

**Then**
- `ERROR` moment fires with `e1`

---

### ERROR_002 — system_error triggers ERROR

**When**
```json
[
  {"event_id":"e1","event_type":"system_error","occurred_at":"t+25s","payload":{"code":"E_TIMEOUT"}}
]
```

**Then**
- `ERROR` moment fires with `e1`

---

## Priority Rules

### PRIORITY_001 — ERROR suppresses OVERLOAD and others

**When**
```json
[
  {"event_id":"e1","event_type":"user_feedback","occurred_at":"t+20s","payload":{"feedback":"too_much"}},
  {"event_id":"e2","event_type":"analysis_failed","occurred_at":"t+21s"}
]
```

**Then**
- Only `ERROR` moment fires
- `OVERLOAD` is suppressed
