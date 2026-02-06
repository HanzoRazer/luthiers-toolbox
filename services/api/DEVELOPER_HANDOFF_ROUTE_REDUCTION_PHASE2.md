# Luthier's ToolBox – Route Reduction & Decomposition Handoff

**Last Updated:** 2026-02-06

---

## 1. Context & Objective

- **Goal:** Reduce FastAPI route count from 727 to <300 (WP-2, API Surface Reduction).
- **Current State:** Route count at **530** after systematic disabling of unused/duplicate routers and legacy lanes.
- **Scope:** Focused on backend (FastAPI, Python 3.11+), with frontend usage checks (Vue 3, Pinia, TypeScript) to ensure no breakage.

---

## 2. Work Completed (Phase 2A–2E)

### Approach

1. **Cluster Analysis:** Identified large route clusters (CAM aggregator, RMOS, Art Studio, Compare, Saw Lab, Workflow Sessions, Runs v2).
2. **Frontend Usage Audit:** Used `grep_search` against `packages/client/src/**` to confirm which API prefixes are actively consumed by the frontend.
3. **Disabling Pattern:** For unused routers, set `router = None` and wrap registration in `if router:` check in [main.py](app/main.py) (search for `WP-2` comments).
4. **Duplicate/Legacy Cleanup:** Removed or disabled legacy routers, duplicate subrouters, and double-prefix bugs in [cam/routers/aggregator.py](app/cam/routers/aggregator.py).
5. **Batch Commits:** Changes committed in phases (2A–2E), with route count and distribution tracked after each batch.

### Routers Disabled (with WP-2 tags)

| Router | Location in main.py | Routes Removed | Reason |
|--------|---------------------|---------------|--------|
| `material_router` | L144-145 | 3 | No frontend usage |
| `rmos_ai_router` | L158-161 | ~10 | No frontend usage |
| `rmos_profiles_router` | L159-162 | ~7 | No frontend usage |
| `rmos_history_router` | L160-163 | ~5 | No frontend usage |
| `instrument_geometry_router` | L222-223 | 5 | No frontend usage |
| `saw_debug_router` | L235-236 | ~3 | No frontend usage |
| `body_generator_router` | L252-254 | ~8 | No frontend usage |
| `neck_generator_router` | L253-255 | ~8 | No frontend usage |
| `cad_dxf_router` | L261-262 | 7 | No frontend usage |
| `art_studio_bracing_router` | L274-275 | 5 | No frontend usage |
| `art_studio_inlay_router` | L277-278 | 7 | No frontend usage |
| `music_router` | L285-286 | 9 | No frontend usage |
| `calculators_consolidated_router` | L297-298 | ~10 | No frontend usage |
| `pipeline_presets_router` | L185-186 | 4 | No frontend usage, double-prefix bug |
| `rmos_patterns_router` | L310-311 | 5 | No frontend usage |
| `rmos_saw_ops_router` | L313-314 | 2 | No frontend usage |
| `learn_router` | L361-365 | ~5 | No frontend usage |
| `dashboard_router` | L378-383 | ~5 | No frontend usage |
| `art_workflow_router` | L510-516 | ~8 | Superseded by RMOS workflow |
| `design_first_workflow_router` | L522-527 | ~10 | No frontend usage |
| `art_cam_promotion_router` | L534-539 | ~3 | Superseded |
| CAM `monitoring_router` | aggregator.py | ~5 | Duplicate of cam_metrics/cam_logs |
| CAM `utility_router` | aggregator.py | ~5 | Duplicate of cam_settings/cam_backup |
| CAM `export_router` | aggregator.py | ~5 | Duplicate of cam_svg legacy |

### Route Count Progress

| Phase | Routes | Delta | Cumulative Reduction |
|-------|--------|-------|---------------------|
| Baseline (Jan 2026) | 727 | — | — |
| Phase 2A–2C | 572 | -155 | 21% |
| Phase 2D | 537 | -35 | 26% |
| Phase 2E | 530 | -7 | 27% |
| **Current** | **530** | — | **27%** |
| **Target** | **<300** | — | **>59%** |

---

## 3. Blocker Analysis (for Chief Engineer)

**Primary Blocker:** Uncertainty about which remaining routes are safe to disable.

- Remaining large clusters (RMOS workflow ~17, runs v2 ~17, Saw Lab batch ~27, Art Studio ~30, CAM aggregator ~30) all have **some** frontend usage.
- Disabling entire clusters risks breaking active features.
- Further reduction requires **granular per-endpoint frontend audit** within each cluster, not just per-prefix checks.

**Not Blocked By:**
- No backend errors from disabled routers.
- Route count is verified and stable at 530.

---

## 4. Phase 3: God-Object Decomposition (Parallel Track)

### Status: PLANNING (paused for coordination)

**Top candidate:** [main.py](app/main.py) (1,385 lines) — central FastAPI app with all router imports, registration, middleware, and config.

### Decomposition Plan

| Module | Responsibility | Target File | Status |
|--------|---------------|-------------|--------|
| Router Registration | All `include_router()` calls | `app/routers_registry.py` | Stub created |
| App Factory | `FastAPI()` creation, CORS, config | `app/app_factory.py` | Not started |
| Middleware | RequestIdMiddleware, Deprecation, Governance | `app/middleware/` | Partially exists |
| Startup/Shutdown | Event handlers | `app/events.py` | Not started |

### ⚠️ Coordination Risk

Router reduction work is happening in a **separate session** that also modifies [main.py](app/main.py) and [aggregator.py](app/cam/routers/aggregator.py). Both sessions touch the same files.

**Recommendation:** Complete router reduction first, then extract router registration to `routers_registry.py` in a clean pass. This avoids merge conflicts on the largest file in the codebase.

---

## 5. Pending Actions (Priority Order)

| # | Action | Priority | Status | Reference |
|---|--------|----------|--------|-----------|
| 1 | Continue route reduction (530 → <300) | P0 | **In progress (other session)** | This doc, Section 3 |
| 2 | Extract router registration from main.py | P1 | **Paused** (waiting on #1) | `app/routers_registry.py` |
| 3 | Analytics endpoint bug fix | P1 | Not started | [TODO_HIGH_PRIORITY.md](TODO_HIGH_PRIORITY.md) |
| 4 | Exception audit (278 `except Exception`) | P1 | Not started | [copilot-instructions.md](../../.github/copilot-instructions.md) |
| 5 | App factory + middleware extraction | P2 | Not started | This doc, Section 4 |

---

## 6. Reference Materials

| Document | Purpose |
|----------|---------|
| [ROUTER_MAP.md](../../ROUTER_MAP.md) | Full router breakdown and consolidation status |
| [FENCE_REGISTRY.json](../../FENCE_REGISTRY.json) | Architectural boundary enforcement |
| [copilot-instructions.md](../../.github/copilot-instructions.md) | AI agent and codebase operation patterns |
| [TODO_HIGH_PRIORITY.md](TODO_HIGH_PRIORITY.md) | High-priority bug tracking |
| [main.py](app/main.py) | Central router registration (1,385 lines) |
| [cam/routers/aggregator.py](app/cam/routers/aggregator.py) | CAM router aggregator and subrouter state |
| [tests/README.md](tests/README.md) | Golden snapshot policy |
| [routers_registry.py](app/routers_registry.py) | New module stub for router extraction |

---

**Status:** Paused. Waiting for router reduction session to complete before continuing decomposition.
**Next action:** Resume after route reduction merges, then extract router imports/registration into `routers_registry.py`.
