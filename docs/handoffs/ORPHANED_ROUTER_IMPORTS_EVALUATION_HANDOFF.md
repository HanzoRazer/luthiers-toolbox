# Orphaned Router Imports Evaluation Handoff

**Date**: 2026-05-19  
**Author**: Claude Code (automated archaeology)  
**Status**: RESOLVED  
**Priority**: Was BLOCKING — fixed by restoring registry-based main.py  
**Branch**: fix/wood-shrinkage-data-integrity

---

## Resolution Applied (2026-05-19)

**Root cause re-evaluated**: This was NOT about 4 missing routers. Commit `06ae26ca` (merge) re-introduced an old monolithic 1377-line `main.py` with direct imports to deleted modules, bypassing the working router registry system.

**Fix applied**: Restored registry-based `main.py` from commit `352ba5e2` (287 lines).

```bash
git checkout 352ba5e2 -- services/api/app/main.py
```

**Verification**:
- 134 routers loaded via `load_all_routers()`
- 1043 routes exposed
- `/api/_meta/routing-truth` exists (CI gate will pass)
- `/api/blueprint/vectorize` exists (morphology harvest works)

**Do NOT restore the 4 deleted router files**. They were intentionally consolidated:
| Deleted Router | Replacement |
|----------------|-------------|
| `router_truth_routes.py` | `governance_consolidated_router.py` → `/api/_meta/routing-truth` |
| `governance_router.py` | Orphaned, no active consumers |
| `metrics_router.py` | `governance_consolidated_router.py` → `/api/_meta/metrics` |
| `cam_sim_router.py` | `simulation_consolidated_router.py` → `/api/cam/sim/*` |

---

## Original Analysis (preserved for reference)

---

## Executive Summary

Four router imports in `services/api/app/main.py` reference modules that were deleted in commit `545fccad` (2026-02-10) but the import statements were not removed. This prevents the API server from starting.

| Import Statement | Deleted Module | Line |
|-----------------|----------------|------|
| `from .meta.router_truth_routes import router as routing_truth_router` | `app/meta/router_truth_routes.py` | 55 |
| `from .governance.governance_router import router as governance_router` | `app/governance/governance_router.py` | 59 |
| `from .governance.metrics_router import router as metrics_router` | `app/governance/metrics_router.py` | 60 |
| `from .routers.cam_sim_router import router as sim_router` | `app/routers/cam_sim_router.py` | 136 |

**Root Cause**: Commit `545fccad` deleted 25 router files as "orphaned" but did not update `main.py` to remove the corresponding imports.

---

## Timeline

| Date | Commit | Action |
|------|--------|--------|
| 2025-12-25 | `ae45a7fb` | `router_truth_routes.py` created (H4 endpoint canonicalization) |
| 2026-01-XX | `bda8fdf8` | `governance_router.py` created (H5.1 endpoint stats) |
| 2026-02-10 | `545fccad` | **DELETION** — 25 router files removed, imports NOT updated |

---

## Router-by-Router Analysis

### 1. `router_truth_routes.py` (71 lines)

**Purpose**: Runtime route table introspection for deployment verification.

**Endpoint**: `GET /api/_meta/routing-truth`

**Functionality**:
- Dumps all mounted routes at runtime
- Flags deprecated paths (legacy art studio, transitional rosette lanes)
- Returns structured JSON with route paths, methods, and deprecation status

**Original Code** (deleted):
```python
@router.get("/routing-truth")
async def routing_truth(request: Request) -> Dict[str, Any]:
    """
    "Routing Truth" Audit endpoint.
    Returns the concrete runtime route table as seen by FastAPI.
    """
    app = request.app
    items: List[Dict[str, Any]] = []

    for r in app.routes:
        if not isinstance(r, Route):
            continue
        path = getattr(r, "path", "")
        methods = sorted(list(getattr(r, "methods", []) or []))
        name = getattr(r, "name", None)
        deprecated_reason = _is_deprecated_path(path)
        items.append({
            "path": path,
            "methods": methods,
            "name": name,
            "deprecated": bool(deprecated_reason),
            "deprecated_reason": deprecated_reason,
        })

    items.sort(key=lambda x: (x["path"], ",".join(x["methods"])))
    return {
        "count": len(items),
        "deprecated_count": sum(1 for x in items if x["deprecated"]),
        "routes": items,
    }
```

**Dependencies**: None (self-contained FastAPI introspection)

**Active Consumers**:
| Consumer | Path | Status |
|----------|------|--------|
| `.github/workflows/routing_truth.yml` | CI workflow | **WILL FAIL** |
| `.github/workflows/artifact_linkage_gate.yml` | CI workflow | References endpoint |
| `services/api/scripts/check_routing_truth.py` | Governance script | **WILL FAIL** |

**EVALUATION VERDICT**: 
- [ ] **RESTORE** — CI workflows depend on this endpoint
- [ ] **REMOVE** — Delete CI workflows and import simultaneously
- [ ] **DEFER** — CI already broken, can address later

---

### 2. `governance_router.py` (27 lines)

**Purpose**: Endpoint governance hit counters for measuring legacy/shadow usage before deletions.

**Endpoints**:
- `GET /governance/endpoints/stats` — Return endpoint hit counters
- `POST /governance/endpoints/stats/reset` — Reset in-memory counters

**Functionality**:
```python
@router.get("/stats")
def get_endpoint_stats():
    """
    Return endpoint governance hit counters + recent hit log.
    Used to measure legacy/shadow usage before deletions.
    """
    return snapshot()

@router.post("/stats/reset")
def reset_endpoint_stats():
    """
    Reset in-memory counters (does NOT truncate JSONL log file).
    """
    reset()
    return {"ok": True}
```

**Dependencies**:
- `app/governance/endpoint_stats.py` — **EXISTS** (dependency is intact)

**Active Consumers**:
| Consumer | Status |
|----------|--------|
| Frontend | No direct references found |
| CI | No direct references found |
| Governance middleware | `EndpointGovernanceMiddleware` still imported but may not use these endpoints |

**EVALUATION VERDICT**:
- [ ] **RESTORE** — Governance metrics needed for endpoint deprecation workflow
- [ ] **REMOVE** — No active consumers, dependency can be accessed directly
- [ ] **DEFER** — Low priority, governance workflow not currently active

---

### 3. `metrics_router.py` (42 lines)

**Purpose**: Prometheus metrics exposition endpoint aggregating endpoint stats and RMOS CAM metrics.

**Endpoint**: `GET /metrics`

**Functionality**:
```python
@router.get("/metrics", response_class=PlainTextResponse)
def metrics():
    """
    Prometheus exposition endpoint.
    Env:
      ENDPOINT_METRICS_ENABLED=true|false
      RMOS_METRICS_ENABLED=true|false
    """
    if not _enabled():
        return PlainTextResponse("# metrics disabled\n", status_code=404)

    parts = [snapshot_prometheus_text()]
    if _rmos_metrics_enabled():
        parts.append(render_rmos_cam_metrics())

    return PlainTextResponse("".join(parts), media_type="text/plain; version=0.0.4")
```

**Dependencies**:
- `app/governance/endpoint_stats.py` — **EXISTS**
- `app/observability/metrics.py` — **EXISTS**

**Active Consumers**:
| Consumer | Path | Status |
|----------|------|--------|
| `packages/client/src/views/rmos/QualityControlView.vue` | Frontend | References `/metrics` |
| `packages/client/src/sdk/core/auth.ts` | SDK | May reference metrics |
| `packages/client/src/components/cam/CamBackplot3D.vue` | Frontend | May reference metrics |
| `packages/client/src/components/adaptive/composables/useEnergyMetrics.ts` | Frontend | May reference metrics |
| Prometheus scraper | External | **WILL FAIL** if configured |

**EVALUATION VERDICT**:
- [ ] **RESTORE** — Frontend and potential Prometheus integration depend on this
- [ ] **REMOVE** — No Prometheus in production, frontend can adapt
- [ ] **DEFER** — Investigate frontend usage depth first

---

### 4. `cam_sim_router.py` (34 lines)

**Purpose**: G-code simulation endpoint (JSON body input).

**Endpoint**: `POST /cam/simulate_gcode`

**Original Functionality**:
```python
class SimInput(BaseModel):
    gcode: str = Field(..., description="Raw G-code to simulate")
    as_csv: Optional[bool] = False
    accel: Optional[float] = DEFAULT_ACCEL
    clearance_z: Optional[float] = DEFAULT_CLEAR_Z
    envelope: Optional[Dict[str, tuple]] = DEFAULT_ENVELOPE

@router.post("/simulate_gcode")
def simulate_gcode(body: SimInput) -> Response:
    sim = simulate(body.gcode, accel=body.accel or DEFAULT_ACCEL,
                   clearance_z=body.clearance_z or DEFAULT_CLEAR_Z,
                   env=body.envelope or DEFAULT_ENVELOPE)
    if body.as_csv:
        data = csv_export(sim)
        return Response(content=data, media_type="text/csv")
    return Response(content=json.dumps({'issues': sim['issues'], 'moves': sim['moves']}),
                    media_type="application/json")
```

**Dependencies**:
- `app/routers/sim_validate.py` — **RELOCATED** to `app/util/sim_validate.py`

**Superseded By**: `app/routers/simulation_consolidated_router.py`
- New endpoint: `POST /sim/gcode` (different path)
- Uses same underlying `sim_validate.py` (now at `app/util/`)

**Frontend SDK Endpoint**: `POST /api/cam/gcode/simulate` (in `packages/client/src/sdk/endpoints/cam/simulate.ts`)
- **NOTE**: Frontend uses `/api/cam/gcode/simulate`, NOT `/cam/simulate_gcode`
- The deleted router was NOT serving the frontend

**Active Consumers**:
| Consumer | Endpoint Used | Status |
|----------|---------------|--------|
| Frontend SDK | `/api/cam/gcode/simulate` | Different endpoint (unaffected) |
| Direct API calls | `/cam/simulate_gcode` | Unknown |

**EVALUATION VERDICT**:
- [ ] **RESTORE** — Unknown direct consumers may exist
- [ ] **REMOVE** — Superseded by `simulation_consolidated_router.py`, frontend uses different endpoint
- [ ] **REDIRECT** — Add redirect from old path to new path

---

## Recommended Actions

### Option A: Minimal Fix (Remove Dead Imports)

Remove the four import statements from `main.py` and associated `app.include_router()` calls.

**Pros**: Fastest path to bootable server  
**Cons**: Breaks CI workflows, may break metrics collection  

**Files to modify**:
- `services/api/app/main.py` — Remove imports and router mounts
- `.github/workflows/routing_truth.yml` — Disable or delete
- `.github/workflows/artifact_linkage_gate.yml` — Verify impact

### Option B: Restore Critical Routers

Restore `router_truth_routes.py` and `metrics_router.py` from git history, remove the others.

```bash
git show 545fccad~1:services/api/app/meta/router_truth_routes.py > services/api/app/meta/router_truth_routes.py
git show 545fccad~1:services/api/app/governance/metrics_router.py > services/api/app/governance/metrics_router.py
```

**Pros**: CI workflows continue working, metrics preserved  
**Cons**: Restoring code flagged as "orphaned" without understanding why  

**Files to modify**:
- `services/api/app/main.py` — Remove `governance_router` and `sim_router` imports only
- Restore `router_truth_routes.py` and `metrics_router.py`

### Option C: Full Audit Before Changes

1. Check if CI workflows have been running successfully since Feb 10
2. Check Prometheus/Grafana for metrics endpoint usage
3. Grep production logs for endpoint hits
4. Make informed decision per-router

---

## Git Archaeology Commands

```bash
# View deleted file content
git show 545fccad~1:services/api/app/meta/router_truth_routes.py

# View deletion commit details
git show 545fccad --stat

# View creation commit details  
git show ae45a7fb --stat

# Check if CI has been failing since Feb 10
git log --oneline --since="2026-02-10" -- .github/workflows/routing_truth.yml

# Restore a specific file from before deletion
git checkout 545fccad~1 -- services/api/app/meta/router_truth_routes.py
```

---

## Deleted Files Reference

All 25 files deleted in commit `545fccad`:

| Category | File | Lines |
|----------|------|-------|
| **Governance** | `governance_router.py` | 27 |
| **Governance** | `router_truth_routes.py` | 71 |
| **CAM Sim** | `cam_sim_router.py` | ~34 |
| Saw/CNC | `saw_telemetry_router.py` | 498 |
| Saw/CNC | `saw_blade_router.py` | 241 |
| Saw/CNC | `saw_validate_router.py` | 238 |
| Saw/CNC | `saw_gcode_router.py` | 134 |
| Saw/CNC | `rmos_saw_ops_router.py` | 143 |
| Saw/CNC | `cam_roughing_intent_router.py` | 178 |
| Saw/CNC | `adaptive_poly_gcode_router.py` | 151 |
| Saw/CNC | `feeds_router.py` | 105 |
| Jobs | `unified_presets_router.py` | 491 |
| Jobs | `dashboard_router.py` | 247 |
| Jobs | `job_insights_router.py` | 247 |
| Jobs | `job_intelligence_router.py` | 259 |
| Jobs | `job_risk_router.py` | 172 |
| Jobs | `compare_jobs_router.py` | 177 |
| Art Studio | `design_first_workflow_routes.py` | 422 |
| Art Studio | `rosette_feasibility_routes.py` | 125 |
| Art Studio | `cam_promotion_routes.py` | 35 |
| Misc | `rosette_photo_router.py` | 325 |
| Misc | `rmos_cam_intent_router.py` | 118 |
| Misc | `rmos_patterns_router.py` | 117 |
| Misc | `debug_router.py` | 358 |
| Misc | `websocket_router.py` | 77 |
| Misc | `instruments_router.py` | 126 |

**Total**: ~5,082 lines, ~60 endpoints

---

## Checklist for Evaluating Team

- [ ] Check GitHub Actions history for `routing_truth.yml` failures since 2026-02-10
- [ ] Check if Prometheus is configured to scrape `/metrics`
- [ ] Grep Railway/production logs for `/governance/endpoints/stats` hits
- [ ] Grep Railway/production logs for `/cam/simulate_gcode` hits
- [ ] Decide: restore, remove, or redirect per router
- [ ] Update `main.py` imports accordingly
- [ ] Verify server boots locally: `cd services/api && uvicorn app.main:app --reload --port 8000`
- [ ] Verify CI passes after changes

---

## Contact

For questions about this handoff, reference the git archaeology in commit `545fccad` and the creation commits listed in the Timeline section.
