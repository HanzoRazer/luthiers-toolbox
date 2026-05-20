# CI Hygiene Debt Burn-Down — Patch Plan

**Issue:** #20  
**Branch:** `fix/ci-hygiene-debt-20`  
**Date:** 2026-05-20

## Summary

Three categories of pre-existing CI failures need resolution:

| Priority | Category | Status | Fix Complexity |
|----------|----------|--------|----------------|
| 1 | sg-spec credential failures | 21 workflows affected | Medium |
| 2 | CBSP21 Patch Manifest Gate | Schema field mismatch | Trivial |
| 3 | Complexity violations | Baseline exists, no NEW violations | Deferred |

---

## Priority 1: sg-spec Credential Failures

### Root Cause
Workflows configure git with `SG_SPEC_TOKEN` for private repo access:
```yaml
- name: Configure git for private repos
  run: |
    git config --global url."https://${{ secrets.SG_SPEC_TOKEN }}@github.com/".insteadOf "https://github.com/"
```

When `SG_SPEC_TOKEN` is missing/empty, the URL becomes `https://@github.com/` causing pip install to fail if any private dependencies exist.

### Affected Workflows (21 total)

**Primary (git config pattern):**
- `.github/workflows/api_tests.yml:14-16`
- `.github/workflows/geometry_parity.yml:16-18`
- `.github/workflows/core_ci.yml`
- `.github/workflows/cam_essentials.yml:26-28`
- `.github/workflows/artifact_linkage_gate.yml:44`
- `.github/workflows/api_wiring_gate.yml`
- `.github/workflows/api_health_check.yml`
- `.github/workflows/api_health_and_smoke.yml`
- `.github/workflows/run_artifact_contract_gate.yml`
- `.github/workflows/routing_truth.yml`
- `.github/workflows/rmos_ci.yml`
- `.github/workflows/mvp_golden_gate.yml`
- `.github/workflows/governance_unified.yml`
- `.github/workflows/sdk_codegen.yml`
- `.github/workflows/api_dxf_tests.yml`
- `.github/workflows/adaptive_pocket.yml`

**Docker build args:**
- `.github/workflows/containers.yml`
- `.github/workflows/proxy_parity.yml`
- `.github/workflows/proxy_adaptive.yml`

### Fix Approach

Add conditional check to skip git config when token unavailable:

```yaml
- name: Configure git for private repos
  if: ${{ secrets.SG_SPEC_TOKEN != '' }}
  run: |
    git config --global url."https://${{ secrets.SG_SPEC_TOKEN }}@github.com/".insteadOf "https://github.com/"

- name: Warn if private repo token unavailable
  if: ${{ secrets.SG_SPEC_TOKEN == '' }}
  run: |
    echo "::warning::SG_SPEC_TOKEN not configured - private dependencies will fail"
```

### Files to Modify

| File | Lines | Change |
|------|-------|--------|
| `.github/workflows/api_tests.yml` | 14-16 | Add conditional |
| `.github/workflows/geometry_parity.yml` | 16-18 | Add conditional |
| `.github/workflows/cam_essentials.yml` | 26-28 | Add conditional |
| (16 more workflows) | varies | Same pattern |

---

## Priority 2: CBSP21 Patch Manifest Gate

### Root Cause
Schema field name mismatch:
- **Manifest uses:** `"schema_version": "cbsp21_patch_input_v1"`  
- **Gate expects:** `"schema": "cbsp21_patch_input_v1"`

See `scripts/ci/check_cbsp21_gate.py:54`:
```python
if manifest.get("schema") != "cbsp21_patch_input_v1":
    print(f"❌ CBSP21 FAIL: Invalid schema...")
```

### Fix

**File:** `.cbsp21/patch_input.json`  
**Line:** 2  
**Change:** `"schema_version"` → `"schema"`

```diff
{
-  "schema_version": "cbsp21_patch_input_v1",
+  "schema": "cbsp21_patch_input_v1",
   "patch_id": "BUNDLE_32.4.18",
```

---

## Priority 3: Complexity Violations

### Current Status

**Fence checker:** PASS (0 violations)  
**Complexity check:** PASS (ratchet mode, no NEW violations above baseline)

The complexity baseline (`services/api/app/ci/complexity_baseline.json`) tracks 179 existing violations with threshold 15. The check passes because no NEW functions exceed the baseline.

### Issue #20 Named Offenders

The issue mentions three functions:
1. `process_file` (81) — **Not found** in current codebase
2. `build_dxf` (46) — Multiple instances in rosette prototypes
3. `_fallback_topology_recovery` (41) — Found at `topology_recovery.py:271`

### Actual Top Offenders (from baseline)

| Function | Complexity | Location |
|----------|------------|----------|
| `parse_dxf` | 50 | `app/art_studio/services/generators/inlay_import.py:33` |
| `run_manufacturing_checks` | 50 | `app/art_studio/services/rosette/rosette_manufacturing.py:183` |
| `tessellate_path_d` | 42 | `app/art_studio/services/generators/inlay_geometry_svg.py:131` |
| `record_operator_feedback_event` | 41 | `app/services/saw_lab_operator_feedback_learning_hook.py:49` |

### Recommendation

**Do not demote** the complexity check. The baseline ratchet mode is working correctly:
- Existing violations are tracked
- New violations would fail CI
- Gradual reduction is the path forward

**Next step:** After fixing priorities 1-2, select ONE top offender for refactoring:
- Target: `parse_dxf` or `run_manufacturing_checks` (both at 50)
- Goal: Reduce complexity below 40 via extract-method refactoring

---

## Implementation Order

1. **Fix CBSP21 schema field** (1 line change, instant fix)
2. **Add sg-spec conditionals** (21 workflow files, pattern-based)
3. **Update complexity baseline** if any refactoring done

---

## Verification Commands

```bash
# CBSP21 gate
python scripts/ci/check_cbsp21_gate.py --manifest .cbsp21/patch_input.json --changed-files ""

# Fence checker
cd services/api && python -m app.ci.fence_checker_v2

# Complexity check
cd services/api && python -m app.ci.check_complexity --baseline app/ci/complexity_baseline.json
```
