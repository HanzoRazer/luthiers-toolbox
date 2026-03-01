# Remediation Plan v2

**Date:** 2026-02-09
**Based on:** Snapshot 16 Design Review (6.68/10)
**Goal:** Reach 7.0+/10
**Gap:** 0.32 points

---

## Current State (Reviewer Verified)

| Metric | Snapshot 15 | Snapshot 16 | Target | Gap |
|--------|-------------|-------------|--------|-----|
| Files >500 lines | 19+ | **14** | <10 | -4 |
| Broad `except Exception` | 725 | **691** | <200 | -491 |
| API route decorators | ~992 | **994** | <500 | -494 |
| Root directory items | 38 | **33** | <25 | -8 |
| @safety_critical sites | 0 | **6** | 20+ | +14 |
| Test ratio | 12% | **12%** | 20%+ | +8% |

---

## Phase 12: Metrics Accuracy Fix (Quick Win)

**Impact:** Credibility, tracking accuracy
**Effort:** 1 hour
**Priority:** HIGH

### Actions
1. Update REVIEW_REMEDIATION_PLAN.md with accurate counts
2. Reconcile "files >500 lines" methodology (include all app/*.py)
3. Clarify route counting (decorators vs manifest entries)

---

## Phase 13: God-Object Decomposition (Continued)

**Impact:** Maintainability +1
**Effort:** 8-16 hours
**Priority:** HIGH

### Files to Decompose (14 remaining)

| File | Lines | Strategy | Priority |
|------|-------|----------|----------|
| adaptive_router.py | 1,244 | Extract 3+ sub-routers | HIGH |
| blueprint_router.py | 1,236 | Extract 3+ sub-routers | HIGH |
| geometry_router.py | 1,100 | Extract schemas done, split routes | MEDIUM |
| blueprint_cam_bridge.py | 937 | Extract schemas done, split routes | MEDIUM |
| dxf_preflight_router.py | 792 | Split validation vs reporting | MEDIUM |
| probe_router.py | 782 | Split by probe type | MEDIUM |
| fret_router.py | 696 | Split calculation vs export | LOW |
| cam_metrics_router.py | 653 | Split by metric category | LOW |
| lespaul_gcode_gen.py | 593 | Extract G-code templates | LOW |
| calculators_consolidated_router.py | 577 | Already consolidated, skip | SKIP |
| ai_context_adapter/routes.py | 538 | Split by context type | LOW |
| dxf_plan_router.py | 528 | Split planning vs execution | LOW |
| router_registry.py | 519 | Intentional manifest, skip | SKIP |
| tooling_router.py | 513 | Split by tool category | LOW |

### Approach
- Extract sub-routers by domain (e.g., adaptive_pocket_router, adaptive_contour_router)
- Move endpoint groups to separate files
- Keep parent router as thin orchestrator

---

## Phase 14: @safety_critical Expansion

**Impact:** Safety +1, Reliability +1
**Effort:** 4-8 hours
**Priority:** HIGH

### Current Coverage (6 sites)
- rmos/feasibility/engine.py
- rmos/operations/cam_adapter.py (2)
- rmos/operations/saw_adapter.py (2)
- cam/rosette/cnc/cnc_gcode_exporter.py

### Target Coverage (20+ sites)

| Module | Functions to Decorate |
|--------|----------------------|
| cam/gcode/*.py | All G-code generation functions |
| calculators/feeds_speeds.py | calculate_feeds(), calculate_speeds() |
| calculators/fret_calculator.py | calculate_fret_positions() |
| rmos/risk_bucketing.py | compute_risk_bucket() |
| rmos/decision_intelligence.py | evaluate_decision() |
| cam/toolpath/*.py | generate_toolpath() variants |

---

## Phase 15: Exception Hardening (Aggressive)

**Impact:** Reliability +1
**Effort:** 8-16 hours
**Priority:** MEDIUM

### Current: 691 broad `except Exception`
### Target: <200

### Strategy
1. **Audit safety-critical modules first** (~200 sites)
   - rmos/
   - cam/
   - calculators/
2. **Replace with specific types:**
   - `except ValueError` for parsing
   - `except FileNotFoundError` for I/O
   - `except KeyError` for dict access
   - Domain exceptions (FeasibilityError, GCodeGenerationError)
3. **Add CI gate** to block new broad exceptions

### Files with Most Broad Exceptions (audit first)
```
grep -r "except Exception" services/api/app --include="*.py" -c | sort -t: -k2 -rn | head -20
```

---

## Phase 16: Route Consolidation

**Impact:** User Fit +1, Scalability +1
**Effort:** 16-24 hours
**Priority:** MEDIUM

### Current: 994 route decorators
### Target: <500

### Classification
| Tier | Description | Action | Est. Routes |
|------|-------------|--------|-------------|
| Core | Essential API | Keep | ~150 |
| Power | Advanced features | Keep | ~150 |
| Internal | Dev/debug only | Mark internal | ~200 |
| Cull | Unused/duplicate | Delete | ~500 |

### Approach
1. Add usage telemetry to identify unused routes
2. Mark internal routes with `include_in_schema=False`
3. Deprecate duplicate routes (v1 vs v2)
4. Consolidate similar endpoints

---

## Phase 17: Root Directory Cleanup

**Impact:** Aesthetics +1
**Effort:** 1-2 hours
**Priority:** LOW

### Current: 33 items
### Target: <25

### Actions
1. Move to `docs/internal/`:
   - AGENT_SESSION_BOOKMARK.md
   - REVIEW_REMEDIATION_PLAN.md
   - REMEDIATION_PLAN_v2.md
   - FENCE_REGISTRY.json
2. Consolidate `.code-workspace` files (keep 1)
3. Move `luthiers-toolbox-16-design-review.md` to `docs/reviews/`

---

## Success Metrics

| Metric | Current | Phase | Target | Status |
|--------|---------|-------|--------|--------|
| Files >500 lines | 14 | 13 | <10 | Pending |
| @safety_critical sites | 6 | 14 | 20+ | Pending |
| except Exception | 691 | 15 | <200 | Pending |
| Route decorators | 994 | 16 | <500 | Pending |
| Root items | 33 | 17 | <25 | Pending |
| Design review score | 6.68 | All | 7.0+ | Pending |

---

## Priority Order

1. **Phase 12** - Fix metrics accuracy (1 hour) — credibility
2. **Phase 14** - Expand @safety_critical (4-8 hours) — safety gains
3. **Phase 13** - Decompose top 4 large files (8-16 hours) — maintainability
4. **Phase 15** - Exception hardening (8-16 hours) — reliability
5. **Phase 16** - Route consolidation (16-24 hours) — scalability
6. **Phase 17** - Root cleanup (1-2 hours) — aesthetics

---

## Path to 7.0+

Completing phases 12-14 should close the 0.32 point gap:
- @safety_critical expansion: Safety 7→8 (+0.2 weighted)
- God-object decomposition: Maintainability 6→7 (+0.15 weighted)
- Metrics accuracy: Credibility boost across categories

**Estimated effort to 7.0+:** 15-25 hours
