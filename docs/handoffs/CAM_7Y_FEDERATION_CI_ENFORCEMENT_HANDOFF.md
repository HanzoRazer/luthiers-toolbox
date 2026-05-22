# CAM Dev Order 7Y: Federation CI Enforcement & Drift Baseline

**Status**: Complete
**Date**: 2026-05-22
**Depends on**: 7X (Federated Manufacturing Semantics)

## Overview

7Y provides CI-visible drift baselines and enforcement summaries that make federation health measurable. It builds on 7X's cross-domain federation layer to enable automated CI evaluation of federation integrity.

## Core Invariants

7Y enforces these invariants at the model level:

1. **execution_authorized**: Always False — 7Y does not authorize execution
2. **machine_output_allowed**: Always False — 7Y does not allow machine output
3. **Baselines are immutable**: Once registered, baselines cannot be modified
4. **CI summaries are historical records**: Summaries capture point-in-time state

## Files Created

### Core Models

**`services/api/app/cam/federation_drift_baseline.py`**
- `FederationDriftBaseline` model with expected counts and allowed thresholds
- `create_federation_drift_baseline()` factory
- `validate_federation_drift_baseline()` validation
- Deterministic hash computation for baseline integrity

**`services/api/app/cam/federation_ci_enforcement.py`**
- `FederationCIEnforcementSummary` model with CI metrics
- `FederationCIStatus` literal: "pass" | "warn" | "fail"
- `classify_federation_ci_status()` status classification
- `compare_federation_to_baseline()` baseline comparison
- `build_federation_ci_summary()` summary builder

### Registry

**`services/api/app/cam/federation_ci_registry.py`**
- `FEDERATION_DRIFT_BASELINE_INDEX` — baseline storage
- `FEDERATION_CI_SUMMARY_INDEX` — summary history
- Registration, retrieval, and query helpers
- CI status aggregation

### Router

**`services/api/app/routers/cam/federation_ci_router.py`**

Endpoints:
- `POST /api/cam/federation-ci/baselines` — Create baseline
- `GET /api/cam/federation-ci/baselines` — List baselines
- `GET /api/cam/federation-ci/baselines/{baseline_id}` — Get baseline
- `POST /api/cam/federation-ci/evaluate` — Evaluate federation (optionally against baseline)
- `GET /api/cam/federation-ci/summary/latest` — Get latest CI summary
- `GET /api/cam/federation-ci/status` — Get aggregated CI status
- `GET /api/cam/federation-ci/summaries` — List all summaries
- `GET /api/cam/federation-ci/summaries/{summary_id}` — Get specific summary

### Tests

**`services/api/tests/cam/test_federation_ci_enforcement.py`**
- 86 tests covering models, classification, comparison, registry, and router

## CI Status Classification

### FAIL Conditions

Any of these causes immediate FAIL:
- `authority_override_count > 0`
- `ontology_mutation_attempt_count > 0`
- `invalid_continuity_count > 0`
- `blocking_issue_count > 0`
- `execution_authorized == True`
- `machine_output_allowed == True`

### WARN Conditions

If no FAIL, these cause WARN:
- `fragmented_federation_count > allowed_fragmented_federation_count`
- `warning_count > allowed_warning_count`
- `baseline_mismatch_detected == True`

### PASS

No FAIL conditions and no WARN conditions above thresholds.

## Baseline Comparison

When evaluating against a baseline:

1. Compare `total_federation_refs` to `expected_federation_ref_count` (if set)
2. Compare `total_continuity_records` to `expected_continuity_record_count` (if set)
3. Compare `total_federated_packages` to `expected_package_count` (if set)

Any mismatch sets `baseline_mismatch_detected = True`, resulting in WARN status (not FAIL).

## Usage Examples

### Create a Baseline

```python
from app.cam.federation_drift_baseline import create_federation_drift_baseline
from app.cam.federation_ci_registry import register_federation_drift_baseline

baseline = create_federation_drift_baseline(
    baseline_name="release-v1.0",
    expected_federation_ref_count=50,
    expected_continuity_record_count=25,
    expected_package_count=10,
    allowed_warning_count=2,
    allowed_fragmented_federation_count=1,
)
success, error = register_federation_drift_baseline(baseline)
```

### Evaluate Federation

```python
from app.cam.federation_ci_enforcement import build_federation_ci_summary
from app.cam.federation_ci_registry import (
    get_federation_drift_baseline,
    register_federation_ci_summary,
)

# Without baseline
summary = build_federation_ci_summary()
register_federation_ci_summary(summary)

# With baseline
baseline = get_federation_drift_baseline("fdb-abc123")
summary = build_federation_ci_summary(baseline=baseline)
register_federation_ci_summary(summary)

print(f"Status: {summary.status}")  # pass, warn, or fail
```

### Query CI Status

```python
from app.cam.federation_ci_registry import (
    get_latest_federation_ci_summary,
    get_ci_status_summary,
)

latest = get_latest_federation_ci_summary()
if latest:
    print(f"Latest: {latest.status}")

status = get_ci_status_summary()
print(f"Pass: {status['passing_count']}, Warn: {status['warning_count']}, Fail: {status['failing_count']}")
```

## Integration Points

### 7X Integration

7Y reads from 7X's federated semantic registry via `build_cross_domain_summary()`:
- `total_federation_refs` — count of federated semantic references
- `total_continuity_records` — count of cross-domain continuity records
- `total_federated_packages` — count of federated review packages
- `authority_override_count` — authority boundary violations
- `ontology_mutation_attempt_count` — ontology mutation attempts
- `fragmented_federation_count` — fragmented federation relationships
- `invalid_continuity_count` — invalid continuity records
- `warning_count` — total warnings
- `blocking_issue_count` — blocking issues

### 7Z Integration

7Z (Governance Baseline Freeze) will use 7Y's CI summaries to determine release readiness. A FAIL status from 7Y blocks release authorization.

## Governance Guardrail

7Y measures federation drift against baselines. It does NOT:
- Mutate federation state
- Repair drift
- Authorize release
- Authorize execution
- Enable machine output

All observational, no execution.

## Files Modified

**`services/api/app/router_registry/manifests/cam_manifest.py`**
- Added RouterSpec for federation_ci_router

## Verification

```bash
cd services/api
pytest tests/cam/test_federation_ci_enforcement.py -v
```

All 86 tests should pass.
