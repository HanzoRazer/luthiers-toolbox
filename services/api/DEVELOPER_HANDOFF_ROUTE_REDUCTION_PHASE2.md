# Luthier's ToolBox – Route Reduction & Decomposition Handoff

**Last Updated:** 2026-02-06 (Phase 2 Complete)

---

## 1. Context & Objective

- **Goal:** Reduce FastAPI route count from 727 to <300 (WP-2, API Surface Reduction).
- **Final State:** Route count at **259** — **TARGET ACHIEVED** (41 under target).
- **Scope:** Focused on backend (FastAPI, Python 3.11+), with frontend usage checks (Vue 3, Pinia, TypeScript) to ensure no breakage.

---

## 2. Work Completed (Phase 2A–2F)

### Approach

1. **Cluster Analysis:** Identified large route clusters (CAM aggregator, RMOS, Art Studio, Compare, Saw Lab, Workflow Sessions, Runs v2).
2. **Frontend Usage Audit:** Used grep against packages/client/src/**/*.{ts,vue} to confirm which API prefixes are actively consumed by the frontend.
3. **Disabling Pattern:** For unused routers, set router = None and wrap registration in if router: check in main.py (search for WP-2 comments).
4. **Duplicate/Legacy Cleanup:** Removed or disabled legacy routers, duplicate subrouters, and double-prefix bugs.
5. **Batch Commits:** Changes committed in 19 batches, with route count and distribution tracked after each batch.

### Routers Disabled (62 total, with WP-2 tags)

| Category | Routers Disabled | Routes Removed |
|----------|------------------|----------------|
| RMOS | AI, profiles, history, feasibility, toolpaths, workflow, MVP wrapper, AI advisory | ~50 |
| Saw Lab | batch (14 subrouters), debug, compare, decision intelligence | ~65 |
| CAM | post v155, smoke, backplot, adaptive preview, polygon offset, benchmark | ~25 |
| Art Studio | bracing, inlay, preview, workflow, design-first, CAM promotion, rosette patterns v2 | ~35 |
| Calculators/Jobs | calculators consolidated, job risk/intelligence/insights, bridge, fret | ~30 |
| Infrastructure | governance, dashboard, cost, AI context adapter, feeds tooling, telemetry | ~40 |
| Other | probe, presets, live monitor, acoustics, validation, run logs | ~26 |

**Full audit trail:** See [ROUTE_AUDIT_PHASE2_RESULTS.md](ROUTE_AUDIT_PHASE2_RESULTS.md)

### Route Count Progress

| Phase | Routes | Delta | Cumulative Reduction |
|-------|--------|-------|---------------------|
| Baseline (Jan 2026) | 727 | — | — |
| Phase 2A–2C | 572 | -155 | 21% |
| Phase 2D | 537 | -35 | 26% |
| Phase 2E | 530 | -7 | 27% |
| Phase 2F (Final) | **259** | -271 | **64%** |
| **Target** | **<300** | — | **ACHIEVED** |

---

## 3. Blocker Analysis (RESOLVED)

### Original Blocker (Now Resolved)
> Uncertainty about which remaining routes are safe to disable.

**Resolution:** Systematic per-endpoint frontend audit across all clusters. Each disabled router verified to have zero frontend usage via grep search.

### Key Insight: Router Files Cannot Be Deleted

**Attempted:** Deletion of 49 disabled router files to reduce codebase size.

**Result:** Rolled back. Many router files contain shared utility functions imported by active modules:

| File | Shared Function | Used By |
|------|-----------------|---------|
| machine_router.py | get_profile() | 4 active routers |
| material_router.py | get_material() | cam_metrics_router |
| rmos_feasibility_router.py | compute_feasibility_internal() | 9 active routers |
| blueprint_cam_bridge.py | extract_loops_from_dxf() | dxf_plan_router |
| api_ai_routes.py | Re-exported in rmos/__init__.py | rmos package |

**Correct Approach:** Keep all router files in place. Disable via router = None pattern in main.py. Files remain available for their shared utility functions.

**Future Cleanup:** If router files are to be deleted, their utility functions must first be refactored to separate modules (e.g., app/utils/machine_utils.py).

---

## 4. Phase 3: God-Object Decomposition (Ready to Resume)

### Status: READY (route reduction complete)

**Top candidate:** main.py (~1,400 lines) — central FastAPI app with all router imports, registration, middleware, and config.

### Decomposition Plan

| Module | Responsibility | Target File | Status |
|--------|---------------|-------------|--------|
| Router Registration | All include_router() calls | app/routers_registry.py | Stub created |
| App Factory | FastAPI() creation, CORS, config | app/app_factory.py | Not started |
| Middleware | RequestIdMiddleware, Deprecation, Governance | app/middleware/ | Partially exists |
| Startup/Shutdown | Event handlers | app/events.py | Not started |

### Recommended Approach

1. Extract router imports and registration to routers_registry.py
2. Keep router = None disabled patterns in place
3. Consider grouping disabled routers in a # DISABLED ROUTERS section for clarity

---

## 5. Pending Actions (Priority Order)

| # | Action | Priority | Status | Reference |
|---|--------|----------|--------|-----------|
| 1 | Route reduction (727 → <300) | P0 | **COMPLETE** (259 routes) | This doc |
| 2 | Extract router registration from main.py | P1 | Ready to start | app/routers_registry.py |
| 3 | Refactor shared utilities out of router files | P2 | Not started | Section 3 above |
| 4 | Exception audit (278 except Exception) | P1 | Not started | copilot-instructions.md |
| 5 | App factory + middleware extraction | P2 | Not started | This doc, Section 4 |

---

## 6. Test Suite Status

| Metric | Count |
|--------|-------|
| **Passed** | 982 |
| **Skipped** | 7 |
| **Failed** | 0 |
| **Errors** | 0 |

All tests pass. Disabled router tests are expected to fail if run against disabled endpoints, but the test suite is configured to skip or handle these gracefully.

---

## 7. Reference Materials

| Document | Purpose |
|----------|---------|
| ROUTE_AUDIT_PHASE2_RESULTS.md | Full audit trail with per-batch details |
| ROUTER_MAP.md | Full router breakdown and consolidation status |
| FENCE_REGISTRY.json | Architectural boundary enforcement |
| copilot-instructions.md | AI agent and codebase operation patterns |
| main.py | Central router registration (~1,400 lines) |
| cam/routers/aggregator.py | CAM router aggregator and subrouter state |
| routers_registry.py | New module stub for router extraction |

---

## 8. Summary

**WP-2 Route Reduction: COMPLETE**

- Started: 727 routes
- Target: <300 routes
- Final: **259 routes** (64% reduction, 41 under target)
- Routers disabled: 62
- Tests passing: 982/982
- Frontend breakage: None

**Next Phase:** God-object decomposition of main.py (P1 priority, ready to start).
