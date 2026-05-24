# CAM Dev Order 8E: Governed Review Queue Routing

## Status: COMPLETE

**Date:** 2026-05-23  
**Depends on:** CAM Dev Order 8C (Review UX Contracts), 8D (CI Enforcement)  
**Transition:** Architecture remediation → Governed platform evolution

---

## Summary

Dev Order 8E turns 8C/8D review UX contracts into a governed human review queue. It introduces:

1. **ReviewQueueItem** — queue items for human review routing
2. **ReviewDecisionRecord** — decision audit trail
3. **Review Queue Registry** — storage and query operations
4. **Review Queue CI** — CI summary for queue state visibility
5. **Router endpoints** — REST API for queue operations

---

## Core Principle

```
Review routing may organize human decisions.
Review routing may not make human decisions.
```

8E routes human attention. It does not:
- Authorize implementation
- Authorize execution
- Invoke serializers
- Mutate geometry
- Generate machine output
- Auto-approve anything

---

## 8E Invariants (Model-Enforced)

### ReviewQueueItem

- `human_review_required`: always True
- `decision_authorized`: always False
- `implementation_authorized`: always False
- `execution_authorized`: always False
- `machine_output_allowed`: always False

### ReviewDecisionRecord

- `human_review_recorded`: always True
- `implementation_authorized`: always False
- `execution_authorized`: always False
- `machine_output_allowed`: always False

### ReviewQueueCISummary

- `implementation_authorized`: always False
- `execution_authorized`: always False
- `machine_output_allowed`: always False

---

## Core Models

### ReviewQueueItem

```python
class ReviewQueueItem(BaseModel):
    queue_item_id: str
    panel_id: Optional[str]
    priority_id: Optional[str]
    provenance_explanation_id: Optional[str]

    source_layer: ReviewSourceLayer  # 8 options
    review_priority: ReviewPriority  # low/medium/high/critical
    review_status: ReviewStatus  # queued/in_review/needs_more_evidence/reviewed/deferred/rejected

    assigned_role: Optional[str]
    review_reason: str
    blocking_issues: List[str]
    warnings: List[str]

    # 8E invariants
    human_review_required: bool = True
    decision_authorized: bool = False
    implementation_authorized: bool = False
    execution_authorized: bool = False
    machine_output_allowed: bool = False

    deterministic_queue_hash: str
```

### ReviewDecisionRecord

```python
class ReviewDecisionRecord(BaseModel):
    decision_id: str
    queue_item_id: str

    decision_type: DecisionType  # acknowledge/request_more_evidence/defer/reject/mark_reviewed
    decision_rationale: str
    reviewer_ref: Optional[str]
    resulting_review_status: ReviewStatus

    # 8E invariants
    human_review_recorded: bool = True
    implementation_authorized: bool = False
    execution_authorized: bool = False
    machine_output_allowed: bool = False

    deterministic_decision_hash: str
```

---

## Decision-to-Status Mapping

| Decision Type | Resulting Status |
|--------------|------------------|
| acknowledge | in_review |
| request_more_evidence | needs_more_evidence |
| defer | deferred |
| reject | rejected |
| mark_reviewed | reviewed |

---

## Source Layers

Queue items can originate from:

- `manufacturing_cognition`
- `geometry_authority`
- `strategy_export`
- `fixture_topology`
- `manufacturing_replay`
- `federation`
- `review_ux`
- `post_freeze`

---

## Registry Operations

### Queue Items

```python
register_review_queue_item(item) -> (success, error)
get_review_queue_item(queue_item_id) -> Optional[ReviewQueueItem]
list_review_queue_items() -> List[ReviewQueueItem]
list_review_queue_by_status(status) -> List[ReviewQueueItem]
list_review_queue_by_priority(priority) -> List[ReviewQueueItem]
```

### Decision Records

```python
register_review_decision_record(record) -> (success, error)
list_decisions_for_queue_item(queue_item_id) -> List[ReviewDecisionRecord]
record_review_decision(queue_item_id, decision_type, ...) -> (record, success, error)
```

### Utilities

```python
build_review_queue_from_panel(panel_id, ...) -> (item, success, error)
sort_queue_items_by_priority(items) -> List[ReviewQueueItem]
detect_unassigned_critical_reviews() -> List[ReviewQueueItem]
detect_stale_review_items(max_age_days=7) -> List[ReviewQueueItem]
get_open_review_items() -> List[ReviewQueueItem]
```

---

## REST API Endpoints

All endpoints at `/api/cam/review-queue/`:

### Queue Items

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/items` | Create queue item |
| GET | `/items` | List all items (sorted by priority) |
| GET | `/items/{queue_item_id}` | Get item by ID |
| POST | `/items/from-panel/{panel_id}` | Create from 8C panel |

### Decisions

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/decisions` | Record decision (updates item status) |
| GET | `/items/{queue_item_id}/decisions` | Get decision history |

### Filters

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/by-status/{status}` | Filter by status |
| GET | `/by-priority/{priority}` | Filter by priority |

### CI

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/ci` | Get CI summary |

---

## CI Classification

### FAIL Conditions

Any authorization violation:
- `decision_authorized = True`
- `implementation_authorized = True`
- `execution_authorized = True`
- `machine_output_allowed = True`

### WARN Conditions

- `critical_open_count > 0`
- `high_open_count > 0`
- `missing_assignment_count > 0`
- `needs_more_evidence_count > 0`
- `blocking_issue_count > 0`

### PASS Conditions

- No FAIL conditions
- No WARN conditions

---

## Panel-to-Queue Integration

`build_review_queue_from_panel(panel_id)` performs shallow registry lookup:

1. Looks up panel in 8C registry
2. Finds associated `ReviewAttentionPriority` if exists
3. Uses priority level from the priority record
4. Creates queue item with default review_reason
5. Registers the queue item

Does NOT deep-query provenance, replay, federation, or topology registries.

---

## Queue Item Mutability

- `review_status` updated only via `record_review_decision()`
- `assigned_role` set only at creation time
- No direct PATCH endpoint in 8E
- Decision records form audit trail

---

## File Inventory

### Models

- `services/api/app/cam/review_queue_item.py`
- `services/api/app/cam/review_decision_record.py`
- `services/api/app/cam/review_queue_ci.py`

### Registry

- `services/api/app/cam/review_queue_registry.py`

### Router

- `services/api/app/routers/cam/review_queue_router.py`

### Tests

- `services/api/tests/cam/test_review_queue_routing.py` (70+ tests)

### Manifest

- `services/api/app/router_registry/manifests/cam_manifest.py`

---

## Governance Stack Position

```
8A (Post-Freeze Gate)
    ↓
8C (Review UX Contracts)
    ↓
8D (CI Enforcement)
    ↓
8E (Review Queue Routing) ← YOU ARE HERE
```

8E consumes 8C/8D artifacts by reference only. It routes human attention without authorizing implementation or execution.

---

## Operational Constraints (8E Scope Boundaries)

### Storage is Ephemeral

- Queue state is **in-memory only**
- API restart loses all queue items and decision records
- This is intentional: 8E is a governed review-routing contract layer, not an operational production queue
- **Persistence deferred** to a later operationalization order

### No Auth/User Integration

- `assigned_role` is a plain string, not linked to user accounts
- Review routing semantics must stabilize before binding to identity/auth
- User integration deferred to future order

### Stale Detection is Future-Ready

- `detect_stale_review_items(max_age_days=7)` exists in registry
- Timestamp-backed stale detection deferred until standard timestamp pattern established
- Function signature is stable for future implementation

### No Notifications

- Queue changes do not trigger webhooks or events
- Notifications belong to a later operational workflow order
- Queue semantics and persistence must settle first

---

## Future Work

- **8F**: Frontend review dashboard integration
- Database persistence for queue state
- User account/role integration for `assigned_role`
- Timestamp tracking for stale detection
- Notification system for queue updates
- Escalation workflows (via explicit future governance order)
- Direct reassignment endpoint

---

## Guardrail

```
8E routes human review attention.
It does not approve implementation, authorize execution,
invoke serializers, mutate geometry, or generate machine output.
```
