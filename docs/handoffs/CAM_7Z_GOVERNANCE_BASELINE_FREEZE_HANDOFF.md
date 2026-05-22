# CAM Dev Order 7Z: Governance Baseline Freeze & Release Readiness

**Status**: Complete
**Date**: 2026-05-22
**Depends on**: 7Y (Federation CI Enforcement & Drift Baseline)

## Overview

7Z provides governance baseline freezes and release readiness evaluation that capture point-in-time governance state for human review. It builds on 7Y's CI enforcement to enable structured release readiness assessment.

## Core Invariants

7Z enforces these invariants at the model level:

1. **human_review_required**: Always True — 7Z always requires human review
2. **auto_release_authorized**: Always False — 7Z does not authorize auto-release
3. **release_authorized**: Always False — 7Z does not authorize release
4. **execution_authorized**: Always False — 7Z does not authorize execution
5. **machine_output_allowed**: Always False — 7Z does not allow machine output

## Files Created

### Core Models

**`services/api/app/cam/governance_baseline_freeze.py`**
- `GovernanceBaselineFreeze` model capturing point-in-time governance state
- `GovernanceFreezeStatus` literal: "pending" | "reviewed" | "approved" | "rejected"
- `create_governance_baseline_freeze()` factory
- Deterministic hash computation for integrity

**`services/api/app/cam/release_readiness_evaluation.py`**
- `ReleaseReadinessEvaluation` model assessing release readiness
- `ReleaseReadinessStatus` literal: "ready" | "not_ready" | "blocked"
- `classify_readiness_status()` status classification
- `evaluate_freeze_readiness()` evaluation builder

**`services/api/app/cam/governance_release_package.py`**
- `GovernanceReleasePackage` model bundling freeze and evaluation
- `create_governance_release_package()` factory
- Package review context for human reviewers

### Registry

**`services/api/app/cam/governance_freeze_registry.py`**
- `GOVERNANCE_FREEZE_INDEX` — freeze storage
- `RELEASE_EVALUATION_INDEX` — evaluation storage
- `GOVERNANCE_PACKAGE_INDEX` — package storage
- Registration, retrieval, and query helpers
- Status transition validation

### Router

**`services/api/app/routers/cam/governance_freeze_router.py`**

Freeze endpoints:
- `POST /api/cam/governance-freeze/freezes` — Create freeze
- `GET /api/cam/governance-freeze/freezes` — List freezes
- `GET /api/cam/governance-freeze/freezes/latest` — Get latest freeze
- `GET /api/cam/governance-freeze/freezes/{freeze_id}` — Get freeze
- `PATCH /api/cam/governance-freeze/freezes/{freeze_id}/status` — Update status

Evaluation endpoints:
- `POST /api/cam/governance-freeze/evaluate` — Evaluate freeze readiness
- `GET /api/cam/governance-freeze/evaluations` — List evaluations
- `GET /api/cam/governance-freeze/evaluations/latest` — Get latest evaluation
- `GET /api/cam/governance-freeze/evaluations/{evaluation_id}` — Get evaluation

Package endpoints:
- `POST /api/cam/governance-freeze/packages` — Create package
- `GET /api/cam/governance-freeze/packages` — List packages
- `GET /api/cam/governance-freeze/packages/latest` — Get latest package
- `GET /api/cam/governance-freeze/packages/{package_id}` — Get package

Status endpoint:
- `GET /api/cam/governance-freeze/status` — Get aggregated status

### Tests

**`services/api/tests/cam/test_governance_baseline_freeze.py`**
- 81 tests covering models, classification, registry, and router

## Release Readiness Classification

### BLOCKED Conditions

Any of these causes BLOCKED status:
- `ci_passed == False`
- `no_blocking_issues == False`

### NOT_READY Conditions

If not BLOCKED, these cause NOT_READY:
- `warnings_within_threshold == False`
- `baseline_aligned == False`
- `human_review_completed == False`

### READY

All criteria met:
- CI passed
- No blocking issues
- Warnings within threshold
- Baseline aligned
- Human review completed

## Freeze Status Transitions

Valid status transitions:
- `pending` -> `reviewed`
- `reviewed` -> `approved`
- `reviewed` -> `rejected`

Status changes trigger hash recomputation.

## Usage Examples

### Create a Freeze

```python
from app.cam.governance_baseline_freeze import create_governance_baseline_freeze
from app.cam.governance_freeze_registry import register_governance_freeze

freeze = create_governance_baseline_freeze(
    freeze_name="release-v1.0-candidate",
    baseline_id="fdb-abc123",
    ci_summary_id="fces-def456",
    ci_status_at_freeze="pass",
    blocking_issue_count=0,
    warning_count=2,
)
success, error = register_governance_freeze(freeze)
```

### Evaluate Readiness

```python
from app.cam.release_readiness_evaluation import evaluate_freeze_readiness
from app.cam.governance_freeze_registry import (
    get_governance_freeze,
    register_release_evaluation,
)

freeze = get_governance_freeze("gbf-abc123")
evaluation = evaluate_freeze_readiness(
    freeze=freeze,
    warning_threshold=5,
)
register_release_evaluation(evaluation)

print(f"Readiness: {evaluation.readiness_status}")
if evaluation.blocking_reasons:
    print(f"Blocked by: {evaluation.blocking_reasons}")
```

### Create Release Package

```python
from app.cam.governance_release_package import create_governance_release_package
from app.cam.governance_freeze_registry import (
    get_governance_freeze,
    get_release_evaluation,
    register_governance_package,
)

freeze = get_governance_freeze("gbf-abc123")
evaluation = get_release_evaluation("rre-def456")

package = create_governance_release_package(
    package_name="release-v1.0-package",
    freeze=freeze,
    evaluation=evaluation,
)
register_governance_package(package)
```

### Update Freeze Status

```python
from app.cam.governance_freeze_registry import update_freeze_status

success, error = update_freeze_status(
    freeze_id="gbf-abc123",
    new_status="reviewed",
    reviewer_note="Reviewed by engineering lead. LGTM.",
)
```

## Integration Points

### 7Y Integration

7Z reads from 7Y's CI enforcement layer:
- Uses `get_federation_drift_baseline()` for baseline reference
- Uses `get_latest_federation_ci_summary()` for CI state at freeze
- Captures CI metrics in freeze for historical record

### Governance Workflow

1. **Freeze**: Capture point-in-time governance state via 7Y CI summary
2. **Evaluate**: Assess readiness against criteria
3. **Package**: Bundle freeze and evaluation for review
4. **Review**: Human reviewer updates status (reviewed -> approved/rejected)

## Governance Guardrail

7Z freezes governance readiness for review. It does NOT:
- Mutate federation state
- Repair drift
- Authorize release
- Authorize execution
- Enable machine output

All observational, no execution.

## Files Modified

**`services/api/app/router_registry/manifests/cam_manifest.py`**
- Added RouterSpec for governance_freeze_router

## Verification

```bash
cd services/api
pytest tests/cam/test_governance_baseline_freeze.py -v
```

All 81 tests should pass.
