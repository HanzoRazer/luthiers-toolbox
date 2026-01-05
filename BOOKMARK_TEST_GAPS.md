# Test Gaps Bookmark - Session 2026-01-04

Status: 140 failed, 412 passed, 3 skipped (as of commit `af8cc21`)

---

## Category 1: Saw Batch Query/Alias Endpoints (NOT IMPLEMENTED)

Tests expect these endpoints that don't exist in `app/saw_lab/batch_router.py`:

| Endpoint | Test File(s) |
|----------|--------------|
| `GET /api/saw/batch/executions` (with query params) | `test_saw_batch_execution_toolpaths.py` |
| `GET /api/saw/batch/executions/by-decision` | `test_saw_batch_execution_list_by_decision_alias.py` |
| `GET /api/saw/batch/execution` (lookup alias) | `test_saw_batch_execution_lookup_alias.py` |
| `GET /api/saw/batch/decisions/by-plan` | `test_saw_batch_alias_decisions_and_executions_by_plan_and_spec.py` |
| `GET /api/saw/batch/decisions/by-spec` | `test_saw_batch_alias_decisions_and_executions_by_plan_and_spec.py` |
| `GET /api/saw/batch/executions/by-plan` | `test_saw_batch_alias_decisions_and_executions_by_plan_and_spec.py` |
| `GET /api/saw/batch/executions/by-spec` | `test_saw_batch_alias_decisions_and_executions_by_plan_and_spec.py` |
| `GET /api/saw/batch/links` | `test_saw_batch_links_endpoint.py` |
| `GET /api/saw/batch/op-toolpaths/by-decision` | `test_saw_batch_op_toolpaths_aliases.py` |
| `GET /api/saw/batch/op-toolpaths/by-execution` | `test_saw_batch_op_toolpaths_aliases.py` |
| `GET /api/saw/batch/job-log/by-execution` | `test_saw_batch_job_log.py` |
| `POST /api/saw/batch/execution/retry` | `test_saw_batch_execution_retry_endpoint.py` |

---

## Category 2: Learning System Endpoints (NOT IMPLEMENTED)

| Endpoint | Test File(s) |
|----------|--------------|
| `POST /api/saw/batch/learning-overrides/apply` | `test_saw_learning_apply_preview_endpoint.py` |
| `POST /api/saw/batch/learning-overrides/resolve` | `test_saw_learning_decision_and_resolve_overrides.py` |
| `GET /api/saw/batch/learning-events/by-execution` | `test_saw_learning_hook_autowire_from_job_log.py` |

Related tests:
- `test_saw_learning_hook_disabled_does_not_emit.py`
- `test_saw_execution_with_learning_applied_true_when_enabled.py`
- `test_saw_batch_execution_applies_learning_when_enabled.py`
- `test_saw_batch_execution_does_not_apply_learning_when_disabled.py`

---

## Category 3: Metrics Rollup Endpoints (NOT IMPLEMENTED)

| Endpoint | Test File(s) |
|----------|--------------|
| `GET /api/saw/batch/metrics/rollup/by-execution` | `test_saw_execution_metrics_rollup_end_to_end.py` |
| `GET /api/saw/batch/metrics/rollup/alias` | `test_saw_rollup_latest_endpoints_return_found_false_when_none.py` |
| `GET /api/saw/batch/executions/metrics-rollup/by-execution` | `test_saw_batch_metrics_rollup_from_job_logs.py` |
| Rollup history/diff | `test_saw_rollup_history_and_diff_end_to_end.py` |
| Decision metrics rollup | `test_saw_decision_metrics_rollup_end_to_end.py` |

---

## Category 4: CSV Export Endpoints (NOT IMPLEMENTED)

| Endpoint | Test File(s) |
|----------|--------------|
| Job logs CSV export | `test_saw_csv_exports_end_to_end.py` |
| Execution rollups CSV export | `test_saw_csv_exports_end_to_end.py` |

---

## Category 5: Bridge Router (URL MISMATCH)

**Problem**: Tests use `/cam/bridge/*` but router is mounted at `/api/cam/bridge/*`

- Router file: `app/routers/bridge_router.py` has `prefix="/cam/bridge"`
- Mounted in `main.py` line 698: `app.include_router(bridge_router, prefix="/api", ...)`
- Full path becomes `/api/cam/bridge/*`

**Fix options**:
1. Change test URLs to `/api/cam/bridge/*`
2. Mount router without `/api` prefix
3. Remove `/cam/bridge` prefix from router and mount at `/cam/bridge`

Affected tests: `test_bridge_router.py` (12 tests)

---

## Category 6: Art Studio Features (ROUTERS NOT MOUNTED OR INCOMPLETE)

### Bracing (`test_art_studio_bracing.py` - 19 tests)
- Preview endpoints (parabolic, rectangular, triangular)
- Presets endpoint
- Batch calculation
- DXF export (multiple versions)

### Inlay (`test_art_studio_inlay.py` - 16 tests)
- Preview endpoints
- DXF export
- Presets
- Pattern types
- Fret positions

### Art Presets (`test_art_presets.py`, `test_art_presets_delete.py`)
- List presets
- Create preset
- Delete preset

### Art Job Detail (`test_art_job_detail.py`)
- Job detail endpoint

---

## Category 7: Helical Router (ENDPOINTS NOT IMPLEMENTED)

File: `test_helical_router.py` (14 tests)

Missing endpoints for:
- Helical entry (basic, statistics, multi-revolution, shallow cut)
- Arc interpolation (CW, CCW, center offsets)
- Feed rates
- Validation
- Geometry calculations
- Integration workflow

---

## Category 8: Runs V2 / RMOS Issues

### Import Errors
- `query_runs` function import errors in some tests

### Schema Mismatches
- Pydantic validation errors for missing fields: `decision`, `hashes`, `risk_bucket`, `score`

Affected tests:
- `test_rmos_runs_e2e.py`
- `test_runs_v2_split_store.py`
- `test_runs_v2_cli_audit_tail.py`
- `test_runs_filter_*.py`

---

## Category 9: Other Failing Tests

| Test File | Issue |
|-----------|-------|
| `test_blueprint_phase3_ci.py` | Health check, preflight, contour reconstruction |
| `test_cam_compare_diff_router.py` | Compare diff endpoint |
| `test_cam_intent_normalize.py` | Type coercion |
| `test_cam_intent_strict_reject_logs_request_id.py` | Request ID logging |
| `test_curve_preflight_router.py` | Preflight endpoints |
| `test_dxf_security_patch.py` | Security validation |
| `test_feature_hunt_smoke.py` | CLI JSON output |
| `test_legacy_endpoint_usage_gate_smoke.py` | Gate smoke test |
| `test_roughing_gcode_intent_metrics.py` | Metrics counters |
| `test_spec_contract_matrix.py` | Contract matrix validation |
| `test_toolpaths_lookup_alias.py` | Toolpaths lookup |

---

## Category 10: Skipped Tests (3)

Run `pytest --collect-only -q` to identify which tests are skipped and why.

---

## Recently Completed (This Session)

- Created `app/saw_lab/store.py` - pluggable artifact store
- Updated `saw_lab_gcode_emit_service.py` with `ArtifactReader` pattern
- Added G-code export endpoints to `batch_router.py`:
  - `GET /api/saw/batch/executions/{id}/gcode`
  - `GET /api/saw/batch/op-toolpaths/{id}/gcode`
- All 3 gcode export tests now pass

---

## Next Steps (Priority Order)

1. **Quick wins**: Fix bridge router URL mismatch
2. **Core batch queries**: Implement `GET /executions` with filters
3. **Alias endpoints**: decisions/executions by-plan, by-spec, by-decision
4. **Learning system**: Apply/resolve overrides
5. **Metrics rollup**: Execution and decision rollups
6. **Art studio**: Mount and complete routers

---

## Commands

```bash
# Run all tests
cd services/api && python -m pytest tests -v

# Run specific category
python -m pytest tests/test_saw_batch_*.py -v
python -m pytest tests/test_bridge_router.py -v

# Run with failure details
python -m pytest tests --tb=short -x
```
