# CAM 7W — Observational Manufacturing Replay Intelligence Handoff

**Date:** 2026-05-21  
**Status:** Complete  
**Branch:** `fix/wood-shrinkage-data-integrity`

---

## Overview

CAM Dev Order 7W introduces observational manufacturing replay intelligence — a framework for recording, reconstructing, and reviewing manufacturing cognition continuity without replaying execution.

7W builds on:
- **7S** — Manufacturing cognition
- **7T** — Geometry authority governance
- **7U** — Strategy/export interoperability
- **7V** — Fixture/topology cognition

---

## Core Principle

```text
Manufacturing replay is observational.
Manufacturing replay is not execution replay.
```

Review intelligence records reasoning continuity.
Review intelligence does not authorize machine behavior.

---

## What 7W Introduces

### 1. Manufacturing Review Observations

Structured observations capturing:
- Topology warnings
- Fixture warnings
- Export review notes
- Geometry authority notes
- Manufacturing strategy notes
- Review rationale
- Provenance warnings
- Continuity observations

### 2. Manufacturing Replay Sessions

Replayable review sessions collecting:
- Observation IDs
- Topology evaluation IDs
- Fixture package IDs
- Export package IDs
- Continuity state tracking

### 3. Review Intelligence Timelines

Ordered progression tracking:
- Observation sequences
- Review state progression
- Topology risk progression
- Fixture warning progression

### 4. Replay-Safe Review Packages

Immutable bundles preserving:
- Session references
- Observation references
- Timeline references
- Provenance chains
- Review summaries

---

## File Summary

### New Files

| File | Purpose |
|------|---------|
| `app/cam/manufacturing_review_observation.py` | Review observation model and helpers |
| `app/cam/manufacturing_replay_session.py` | Replay session model and helpers |
| `app/cam/review_intelligence_timeline.py` | Timeline model and helpers |
| `app/cam/replay_safe_review_package.py` | Immutable package model and helpers |
| `app/cam/manufacturing_replay_registry.py` | In-memory registry with indexes |
| `app/routers/cam/manufacturing_replay_router.py` | HTTP endpoints |
| `tests/cam/test_manufacturing_replay_intelligence.py` | 90+ tests |

### Modified Files

| File | Change |
|------|--------|
| `app/cam/review_safe_fixture_package.py` | Added `replay_session_refs` field |
| `app/cam/review_safe_export_package.py` | Added `replay_session_refs` field |
| `app/router_registry/manifests/cam_manifest.py` | Registered manufacturing replay router |

---

## 7W Invariants

All 7W models enforce these invariants via Pydantic validators:

| Model | Invariant | Value |
|-------|-----------|-------|
| ManufacturingReviewObservation | execution_authorized | False |
| ManufacturingReviewObservation | machine_output_allowed | False |
| ManufacturingReviewObservation | modifies_geometry_authority | False |
| ManufacturingReplaySession | replay_execution_present | False |
| ManufacturingReplaySession | execution_authorized | False |
| ManufacturingReplaySession | machine_output_allowed | False |
| ReviewIntelligenceTimeline | execution_authorized | False |
| ReviewIntelligenceTimeline | machine_output_allowed | False |
| ReplaySafeReviewPackage | immutable | True |
| ReplaySafeReviewPackage | replay_execution_present | False |
| ReplaySafeReviewPackage | execution_authorized | False |
| ReplaySafeReviewPackage | machine_output_allowed | False |

Attempting to create a model with any of these invariants violated raises `ValueError`.

---

## ID Prefixes

| Model | Prefix |
|-------|--------|
| ManufacturingReviewObservation | `mro-` |
| ManufacturingReplaySession | `mrs-` |
| ReviewIntelligenceTimeline | `rit-` |
| ReplaySafeReviewPackage | `rsrp-` |

---

## Observation Categories

```python
ReviewObservationCategory = Literal[
    "topology_warning",
    "fixture_warning",
    "export_review_note",
    "geometry_authority_note",
    "manufacturing_strategy_note",
    "review_rationale",
    "provenance_warning",
    "continuity_observation",
]
```

---

## Replay Continuity States

```python
ReplayContinuityState = Literal[
    "complete",
    "partial",
    "fragmented",
    "invalid",
]
```

A replay is **fragmented** when:
- Referenced observation IDs are missing from the index
- Referenced fixture/export packages cannot be resolved
- Expected linkage between observation and context is incomplete

---

## API Endpoints

Base path: `/api/cam/manufacturing-replay`

### Observations
- `POST /observations` — Create observation
- `GET /observations` — List observations
- `GET /observations/{id}` — Get observation
- `GET /observations/by-workspace/{id}` — List by workspace
- `GET /observations/by-strategy/{id}` — List by strategy
- `GET /observations/by-category/{cat}` — List by category
- `GET /observations/by-severity/{sev}` — List by severity
- `POST /observations/{id}/validate` — Validate observation

### Sessions
- `POST /session` — Create session
- `GET /sessions` — List sessions
- `GET /session/{id}` — Get session
- `GET /sessions/by-workspace/{id}` — List by workspace
- `GET /sessions/by-strategy/{id}` — List by strategy
- `GET /sessions/by-continuity-state/{state}` — List by state
- `POST /session/{id}/observations` — Add observation
- `POST /session/{id}/validate` — Validate session
- `GET /session/{id}/summary` — Get summary
- `GET /session/{id}/replay` — Get observational replay

### Timelines
- `POST /timeline` — Create timeline
- `POST /session/{id}/build-timeline` — Build from session
- `GET /timelines` — List timelines
- `GET /timeline/{id}` — Get timeline
- `GET /timelines/by-session/{id}` — List by session
- `POST /timeline/{id}/validate` — Validate timeline
- `GET /timeline/{id}/summary` — Get summary

### Packages
- `POST /package` — Create package
- `GET /packages` — List packages
- `GET /package/{id}` — Get package
- `GET /packages/by-session/{id}` — List by session
- `POST /package/{id}/validate` — Validate package
- `GET /package/{id}/summary` — Get summary

### CI
- `GET /ci` — CI health summary

---

## CI Summary

The CI endpoint returns:

```json
{
  "total_observations": 10,
  "total_sessions": 3,
  "total_timelines": 2,
  "total_packages": 1,
  "critical_observation_count": 0,
  "warning_observation_count": 2,
  "info_observation_count": 8,
  "complete_session_count": 1,
  "partial_session_count": 2,
  "fragmented_session_count": 0,
  "invalid_session_count": 0,
  "missing_ref_count": 0,
  "status": "warn"
}
```

Status:
- **fail** — Critical observations or invalid sessions
- **warn** — Warning observations or fragmented sessions
- **pass** — All info observations and complete sessions

---

## What 7W Does NOT Do

7W explicitly does not:

- Replay execution
- Replay motion
- Invoke serializers
- Generate G-code
- Generate DXF
- Authorize machine output
- Modify geometry authority
- Approve exports automatically
- Override governance gates
- Recreate toolpaths

---

## Usage Pattern

### Recording Review Observations

```python
from app.cam.manufacturing_review_observation import create_topology_warning
from app.cam.manufacturing_replay_registry import register_review_observation

obs = create_topology_warning(
    observation_text="Undercut detected in body contour",
    workspace_id="ws-123",
    fixture_package_id="fix-pkg-456",
)
register_review_observation(obs)
```

### Creating Replay Sessions

```python
from app.cam.manufacturing_replay_session import create_replay_session
from app.cam.manufacturing_replay_registry import register_replay_session

session = create_replay_session(
    workspace_id="ws-123",
    observation_ids=[obs.observation_id],
    fixture_package_ids=["fix-pkg-456"],
)
register_replay_session(session)
```

### Building Timelines

```python
from app.cam.manufacturing_replay_registry import build_review_timeline

timeline = build_review_timeline(session)
```

### Validating Continuity

```python
from app.cam.manufacturing_replay_registry import validate_replay_continuity

is_valid, issues = validate_replay_continuity(session)
```

---

## Testing

Run the 7W test suite:

```bash
pytest tests/cam/test_manufacturing_replay_intelligence.py -v
```

Target: 90+ tests covering:
- Observation model and helpers (15 tests)
- Observation invariants (5 tests)
- Session model and helpers (15 tests)
- Session invariants (5 tests)
- Timeline model and helpers (12 tests)
- Package model and helpers (10 tests)
- Package invariants (5 tests)
- Registry operations (10 tests)
- Continuity validation (8 tests)
- CI summary (5 tests)
- Router endpoints (10 tests)

---

## Future Evolution Candidates

7W intentionally defers:

1. **Persistence** — Currently in-memory only. Database persistence could be added without changing the model interface.

2. **Cross-workspace replay** — Timelines currently track single workspace. Multi-workspace replay could be added.

3. **Diff comparison** — Comparing two replay sessions to identify divergence points.

4. **Automated fragmentation repair** — Currently only detects fragmentation; repair could be added.

5. **Replay visualization** — UI components for timeline visualization.

---

## Guardrail

```text
7W introduces observational manufacturing replay intelligence.
It does not replay execution, invoke serializers,
generate machine output, recreate toolpaths,
or authorize runtime behavior.
```

---

## Verification Checklist

| Check | Status |
|-------|--------|
| Observation model with invariants | ✓ |
| Session model with invariants | ✓ |
| Timeline model with invariants | ✓ |
| Package model with invariants | ✓ |
| Registry with indexes | ✓ |
| Continuity validation | ✓ |
| Fragmentation detection | ✓ |
| Router endpoints | ✓ |
| CI summary | ✓ |
| 90+ tests | ✓ |
| Fixture package replay linkage | ✓ |
| Export package replay linkage | ✓ |
| Router registered in manifest | ✓ |
| No execution authorization | ✓ |
| No machine output | ✓ |
| Handoff document | ✓ |
