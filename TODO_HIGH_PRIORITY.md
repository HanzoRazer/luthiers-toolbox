# High Priority TODO List

## Analytics Endpoint Mismatch Bug

**Date Identified:** 2026-02-06  
**Priority:** HIGH  
**Status:** Open

### Issue Description

The `analytics_router` is mounted at `/api` prefix in `main.py`, but the router defines endpoints like:
- `/patterns/complexity`
- `/materials/distribution`
- `/materials/consumption`
- `/materials/efficiency`
- `/jobs/duration`
- `/jobs/status`
- `/jobs/failures`

This results in actual paths like:
- `/api/patterns/complexity`
- `/api/materials/distribution`
- `/api/jobs/duration`

**However**, the frontend (`AnalyticsDashboard.vue`) calls:
- `/api/analytics/pattern/complexity`
- `/api/analytics/material/efficiency`
- `/api/analytics/job/status_distribution`
- `/api/analytics/job/success_trends`
- `/api/analytics/advanced/correlation`
- `/api/analytics/advanced/anomalies/durations`
- `/api/analytics/advanced/anomalies/success`
- `/api/analytics/advanced/predict`

### Root Cause

The router is missing the `/analytics` prefix. Either:
1. The router should be mounted at `/api/analytics` instead of `/api`, OR
2. The frontend is calling incorrect paths

### Impact

- **8 frontend API calls in `AnalyticsDashboard.vue` are broken**
- Users see no data in the Analytics Dashboard
- No error reported because frontend silently handles fetch failures

### Files Affected

- `services/api/app/main.py` (line ~936-937)
- `services/api/app/routers/analytics_router.py`
- `packages/client/src/components/rmos/AnalyticsDashboard.vue` (lines 338-345)

### Proposed Fix

Option A (Backend fix - Recommended):
```python
# In main.py, change:
if analytics_router:
    app.include_router(analytics_router, prefix="/api/analytics", tags=["Analytics"])
```

Option B (Frontend fix):
Update all fetch calls in `AnalyticsDashboard.vue` to use correct paths.

### Related Context

Discovered during WP-2 Phase 2 route reduction task (727 → <300 routes).

---

## Route Reduction Progress

**Current:** 643 routes  
**Target:** <300 routes  
**Reduction needed:** ~343 more routes

### Routers Disabled (No Frontend Usage)

| Router | Routes | Prefix |
|--------|--------|--------|
| learn_router | 2 | /api/learn |
| dashboard_router | 2 | /api/dashboard |
| sg_telemetry_router | 8 | /api/telemetry |
| music_router | 9 | /api/music |
| cad_dxf_router | 7 | /api/cad |
| material_router | 3 | /api/material |

### Pending Investigation

- `/api/probe` (7 routes) - check frontend usage
- More RMOS/CAM route consolidation opportunities
