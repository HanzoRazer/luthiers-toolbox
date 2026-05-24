# CAM Dev Order 8D: Review UX CI Integration & Baseline Ergonomics

## Status: COMPLETE

**Date:** 2026-05-23  
**Depends on:** CAM Dev Order 8C (Provenance-Aware Review UX Contracts)  
**Transition:** Architecture remediation → Governed platform evolution

---

## Summary

Dev Order 8D makes the review UX contracts from 8C CI-visible. It introduces:

1. **ReviewUXBaseline** — threshold definitions for acceptable counts
2. **ReviewUXCIEnforcementSummary** — CI check results with pass/warn/fail
3. **Pure counting helpers** — testable, registry-decoupled functions
4. **Baseline comparison** — threshold enforcement
5. **CI classification** — status determination logic
6. **Registry layer** — baseline and summary storage
7. **Router endpoints** — REST API for CI integration

---

## 8D Invariants (Model-Enforced)

All 8D models enforce these invariants via Pydantic validators:

- `execution_authorized`: always False — 8D does not authorize execution
- `machine_output_allowed`: always False — 8D does not allow machine output
- `auto_approval_allowed`: always False — 8D does not allow auto-approval

Attempting to set any of these to True raises `ValueError`.

---

## Core Models

### ReviewUXBaseline

Defines thresholds for CI enforcement:

```python
class ReviewUXBaseline(BaseModel):
    baseline_id: str
    baseline_name: str
    required_panel_count: Optional[int]  # None = not checked
    allowed_missing_provenance_count: int = 0
    allowed_federation_visibility_gap_count: int = 0
    allowed_fragmented_replay_count: int = 0
    allowed_review_overload_count: int = 0
    execution_authorized: bool = False  # 8D invariant
    machine_output_allowed: bool = False  # 8D invariant
    auto_approval_allowed: bool = False  # 8D invariant
    deterministic_baseline_hash: str
```

### ReviewUXCIEnforcementSummary

CI check results:

```python
class ReviewUXCIEnforcementSummary(BaseModel):
    summary_id: str
    baseline_id: Optional[str]
    panel_count: int
    missing_provenance_count: int
    federation_visibility_gap_count: int
    fragmented_replay_count: int
    review_overload_count: int
    baseline_exceeded: bool
    exceeded_fields: List[str]
    status: ReviewUXCIStatus  # "pass" | "warn" | "fail"
    blocking_issues: List[str]
    warnings: List[str]
    execution_authorized: bool = False  # 8D invariant
    machine_output_allowed: bool = False  # 8D invariant
    auto_approval_allowed: bool = False  # 8D invariant
```

---

## Pure Counting Helpers

Decoupled from registries for testability:

```python
def count_missing_provenance(
    panels: List[ManufacturingReviewPanel],
    explanations: List[ProvenanceExplanationArtifact],
) -> int

def count_federation_visibility_gaps(
    panels: List[ManufacturingReviewPanel],
) -> int

def count_fragmented_replay(
    panels: List[ManufacturingReviewPanel],
) -> int

def count_review_overload(
    priorities: List[ReviewAttentionPriority],
    threshold: float = 0.85,
) -> int
```

---

## CI Classification Logic

### Status Determination

```
FAIL conditions:
  - baseline_exceeded = True
  - review_overload_count > 0

WARN conditions:
  - missing_provenance_count > 0 (without exceeding baseline)
  - federation_visibility_gap_count > 0 (without exceeding baseline)
  - fragmented_replay_count > 0 (without exceeding baseline)

PASS:
  - No FAIL or WARN conditions
```

### Baseline Comparison

```python
def compare_review_ux_to_baseline(
    missing_provenance_count: int,
    federation_visibility_gap_count: int,
    fragmented_replay_count: int,
    review_overload_count: int,
    panel_count: int,
    baseline: Optional[ReviewUXBaseline],
) -> Dict[str, Any]:
    """
    Returns:
      - baseline_exceeded: bool
      - exceeded_fields: List[str]
      - comparison_details: Dict
    """
```

---

## Registry Operations

### Baseline Registry

```python
REVIEW_UX_BASELINE_INDEX: Dict[str, ReviewUXBaseline]

register_review_ux_baseline(baseline) -> (success, error)
get_review_ux_baseline(baseline_id) -> Optional[ReviewUXBaseline]
get_latest_review_ux_baseline() -> Optional[ReviewUXBaseline]
list_review_ux_baselines() -> List[ReviewUXBaseline]
```

### CI Summary Registry

```python
REVIEW_UX_CI_SUMMARY_INDEX: Dict[str, ReviewUXCIEnforcementSummary]

register_review_ux_ci_summary(summary) -> (success, error)
get_review_ux_ci_summary(summary_id) -> Optional[ReviewUXCIEnforcementSummary]
get_latest_review_ux_ci_summary() -> Optional[ReviewUXCIEnforcementSummary]
list_review_ux_ci_summaries() -> List[ReviewUXCIEnforcementSummary]
list_ci_summaries_by_status(status) -> List[ReviewUXCIEnforcementSummary]
```

### Evaluation and Reporting

```python
evaluate_current_review_ux_state(baseline=None) -> ReviewUXCIEnforcementSummary
run_review_ux_ci_check(baseline_id=None) -> (summary, success, error)
build_review_ux_ci_report() -> Dict[str, Any]
get_review_ux_ci_status_summary() -> Dict[str, Any]
```

---

## REST API Endpoints

All endpoints at `/api/cam/review-ux-ci/`:

### Baseline Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/baselines` | Create and register baseline |
| GET | `/baselines` | List all baselines |
| GET | `/baselines/latest` | Get most recent baseline |
| GET | `/baselines/{baseline_id}` | Get baseline by ID |

### CI Check Operations

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/check` | Run CI check (optional baseline_id) |
| GET | `/summaries` | List all CI summaries |
| GET | `/summaries/latest` | Get most recent summary |
| GET | `/summaries/{summary_id}` | Get summary by ID |

### Reporting

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/report` | Build full CI report |
| GET | `/status` | Get aggregated status summary |

---

## File Inventory

### Models

- `services/api/app/cam/review_ux_baseline.py` — ReviewUXBaseline model
- `services/api/app/cam/review_ux_ci_enforcement.py` — CI summary model and helpers

### Registry

- `services/api/app/cam/review_ux_ci_registry.py` — Registry operations

### Router

- `services/api/app/routers/cam/review_ux_ci_router.py` — REST endpoints

### Tests

- `services/api/tests/cam/test_review_ux_ci_enforcement.py` — 60+ tests

### Manifest

- `services/api/app/router_registry/manifests/cam_manifest.py` — Router registration

---

## Integration with 8C

8D consumes 8C artifacts via shallow reads:

```python
from .review_ux_registry import (
    list_review_panels,
    list_provenance_explanations,
    list_review_attention_priorities,
)
```

8D does NOT re-evaluate 8C logic. It accepts 8C registry state as source of truth.

---

## Test Coverage

60+ tests covering:

- ReviewUXBaseline model and validation
- 8D invariant enforcement
- Pure counting helpers
- Baseline comparison logic
- CI classification
- Registry operations (CRUD, ordering, filtering)
- Router endpoints (success and error cases)

---

## Governance Position

8D completes the review UX governance stack:

```
8A (Post-Freeze Gate)
    ↓
8C (Review UX Contracts)
    ↓
8D (CI Enforcement) ← YOU ARE HERE
```

8D makes 8C state CI-visible without authorizing execution or machine output.
All classification is for human review prioritization.

---

## Future Work

- **8E**: Review UX dashboard integration (if needed)
- **8F**: Cross-layer governance aggregation (8A + 8C + 8D unified status)
- Integration with existing CI pipelines via `/api/cam/review-ux-ci/check`
