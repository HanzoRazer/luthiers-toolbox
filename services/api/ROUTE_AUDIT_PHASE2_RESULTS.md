# Route Audit Phase 2 — Frontend Usage Results

**Audited:** 2026-02-06
**Method:** Grep search across `packages/client/src/**/*.{ts,vue}`
**Starting Route Count:** 530
**Current Route Count:** 414
**Target:** <300
**Reduction Achieved:** 116 routes (22%)

---

## DISABLED (Zero Frontend Usage) - 25 Routers

### Batch 1 (Commit b140dbb) - 5 routers, -37 routes
| Router | Prefix | Status |
|--------|--------|--------|
| `rmos_ai_router` | `/api/rmos` | DISABLED |
| `rmos_profiles_router` | `/api/rmos` | DISABLED |
| `rmos_history_router` | `/api/rmos` | DISABLED |
| `saw_debug_router` | `/api/saw/debug` | DISABLED |
| `calculators_consolidated_router` | `/api/calculators` | DISABLED |

### Batch 2 (Commit 35e4972) - 14 routers, -68 routes
| Router | Prefix | Status |
|--------|--------|--------|
| `probe_router` | `/api` (Touch-off) | DISABLED |
| `rosette_photo_router` | `/api` (Photo Import) | DISABLED |
| `job_risk_router` | `/api` (Jobs Risk) | DISABLED |
| `job_intelligence_router` | `/api` (Jobs Intelligence) | DISABLED |
| `job_insights_router` | `/api/cam/job_log` | DISABLED |
| `cnc_compare_jobs_router` | `/api/cnc/compare` | DISABLED |
| `pipeline_preset_router` | `/api` (Pipeline Presets) | DISABLED |
| `health_router_ext` | `/api/system` | DISABLED |
| `parametric_guitar_router` | `/api` (Guitar Parametric) | DISABLED |
| `fret_router` | `/api` (Fret Design) | DISABLED |
| `bridge_router` | `/api` (Bridge Calculator) | DISABLED |
| `unified_presets_router` | `/api` (Presets Unified) | DISABLED |
| `cam_roughing_intent_router` | `/api` (CAM Intent) | DISABLED |
| `blueprint_cam_bridge_router` | `/api/blueprint/cam` | DISABLED |

### Batch 3 (Commit 2e8f65a) - 6 routers, -8 routes
| Router | Prefix | Status |
|--------|--------|--------|
| `art_preview_router` | `/api/art` | DISABLED |
| `rmos_feasibility_router` | `/api/rmos` | DISABLED |
| `rmos_toolpaths_router` | `/api/rmos` | DISABLED |
| `art_feasibility_router` | `/api/art` | DISABLED |
| `rmos_mvp_wrapper_router` | `/api/rmos` | DISABLED |
| `governance_router` | `/api` | DISABLED |

### Batch 4 (Commit 45107ed) - 2 subrouters, -3 routes
| Router | Prefix | Status |
|--------|--------|--------|
| `simulation_router` (CAM) | `/api/cam/simulation` | DISABLED |
| `automation_router` (Compare) | `/api/compare/automation` | DISABLED |

---

## Previously Disabled (WP-2 earlier work)
| Router | Prefix | Status |
|--------|--------|--------|
| `material_router` | `/api/material` | DISABLED |
| `learn_router` | `/api/learn` | DISABLED |
| `cad_dxf_router` | `/api/cad` | DISABLED |
| `rmos_patterns_router` | `/api/rmos/patterns` | DISABLED |

---

## KEEP (Active Frontend Usage)

These routers have confirmed frontend usage and must be retained:

| Router | Prefix | Frontend Hits | Files |
|--------|--------|---------------|-------|
| `feeds_router` | `/api/feeds` | 3 | SawSlicePanel, SawContourPanel, SawBatchPanel |
| `geometry_router` | `/api/geometry` | 16 | GeometryUpload, GeometryOverlay, CompareLab |
| `tooling_router` | `/api/tooling` | 2 | PostPreviewDrawer, PostChooser |
| `registry_router` | `/api/registry` | 4 | registry.ts, useRegistryStore, useEdition |
| `posts_consolidated_router` | `/api/posts` | 3 | post.ts, PostTemplatesEditor |
| `neck_router` | `/api/neck` | 1 | LesPaulNeckGenerator |
| `analytics_router` | `/api/analytics` | 8 | AnalyticsDashboard |
| `joblog_router` | `/api/joblog` | 1 | useJobLogStore |
| `simulation_router` | `/api/cam/sim` | 5 | BridgeLabView, SimLab, GeometryOverlay |
| `cam_opt_router` | `/api/cam/opt` | 1 | AdaptivePocketLab |
| `cam_metrics_router` | `/api/cam/metrics` | 6 | AdaptivePocketLab |
| `cam_logs_router` | `/api/cam/logs` | 1 | AdaptivePocketLab |
| `cam_learn_router` | `/api/cam/learn` | 1 | AdaptivePocketLab |
| `ai_cam_router` | `/api/ai-cam` | 3 | camAdvisorStore |
| `vision_router` | `/api/vision` | 28 | ai_images feature |
| `rmos_router` | `/api/rmos` | 40+ | Core RMOS |
| `cam_router` | `/api/cam` | 80+ | CAM consolidated |
| `compare_router` | `/api/compare` | 20+ | Compare consolidated |

---

## HIGH-USAGE CLUSTERS (Keep All)

| Cluster | Prefix | Frontend Hits | Status |
|---------|--------|---------------|--------|
| CAM Core | `/api/cam/*` | 80+ | KEEP |
| RMOS | `/api/rmos/*` | 40+ | KEEP |
| Art Studio | `/api/art/*` | 50+ | KEEP |
| Compare | `/api/compare/*` | 20+ | KEEP |
| Saw Lab | `/api/saw/*` | 10+ | KEEP |

---

## Next Steps to Reach <300

Current: 414 routes
Target: <300
Gap: ~114 routes

### Option A: Deep Endpoint Audit
Audit individual endpoints within high-usage routers (RMOS, CAM, Art Studio) to find:
- Duplicate endpoints
- Legacy endpoints superseded by new implementations
- Rarely-used endpoints that can be consolidated

### Option B: Consolidate Remaining Legacy Routers
Several routers still have duplicate functionality:
- Legacy `simulation_router` vs new CAM simulation in aggregator
- Multiple art_studio routers with overlapping functionality

### Option C: Feature Flag Low-Usage Endpoints
Keep endpoints but gate them behind feature flags for gradual deprecation.

---

## Verification Commands

```bash
# Re-count routes after changes
cd services/api && python -c "from app.main import app; print(len(app.routes))"

# Verify no frontend breakage
cd packages/client && npm run type-check
```

---

## Summary

| Phase | Routers Disabled | Routes Removed |
|-------|------------------|----------------|
| Batch 1 | 5 | 37 |
| Batch 2 | 14 | 68 |
| Batch 3 | 6 | 8 |
| Batch 4 | 2 | 3 |
| **Total** | **27** | **116** |

**Route Reduction: 530 → 414 (22% reduction)**
