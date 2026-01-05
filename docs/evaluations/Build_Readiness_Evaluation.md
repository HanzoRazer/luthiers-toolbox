# Luthiers Toolbox Build Readiness Evaluation

**Evaluated:** January 4, 2026
**Repository:** `luthiers-toolbox` (main branch)
**Last Commit:** `019475b` - docs: add test gaps bookmark for future session
**Status:** Development - Not Production Ready

---

## Executive Summary

The Luthiers Toolbox is a full-stack application for guitar luthiers providing CAM processing, geometry exports, and design tools. The codebase has a mature architecture with governance compliance (RMOS), but has significant test coverage gaps and unimplemented features.

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Test Pass Rate | 74.5% (412/555) | 95%+ | ⚠️ BELOW TARGET |
| Tests Passing | 412 | - | ✅ |
| Tests Failing | 140 | 0 | ❌ |
| Tests Skipped | 3 | 0 | ⚠️ |
| CI Workflows | 35 | - | ✅ |
| Docker Services | 3 | - | ✅ |

**Verdict:** NOT ready for production deployment. Requires completion of unimplemented endpoints and test fixes.

---

## 1. Architecture Overview

### 1.1 Stack

```
┌─────────────────────────────────────────────────────┐
│                    NGINX PROXY                       │
│                   (Port 8088)                        │
└─────────────────┬───────────────────────────────────┘
                  │
    ┌─────────────┴─────────────┐
    ▼                           ▼
┌────────────────┐      ┌────────────────┐
│  Vue 3 Client  │      │  FastAPI API   │
│   (Port 8080)  │      │   (Port 8000)  │
│  Vite + Node20 │      │  Python 3.11+  │
└────────────────┘      └────────────────┘
```

### 1.2 Core Components

| Component | Location | Status |
|-----------|----------|--------|
| API Server | `services/api/` | ✅ Operational |
| Vue Client | `client/` | ✅ Operational |
| Docker Stack | `docker-compose.yml` | ✅ Configured |
| CI/CD | `.github/workflows/` | ✅ 35 workflows |
| RMOS (Runs v2) | `app/rmos/` | ✅ Governance-compliant |
| Saw Lab | `app/saw_lab/` | ⚠️ Partially complete |
| Art Studio | `app/routers/art_*` | ❌ Not mounted |
| Bridge Calculator | `app/routers/bridge_router.py` | ⚠️ URL mismatch |

### 1.3 Key Dependencies

```
# Core Framework
fastapi, uvicorn, pydantic, sqlalchemy

# CAM Processing
pyclipper==1.3.0.post5, numpy==2.2.6, shapely==2.1.2

# Export/PDF
weasyprint>=60.0, reportlab>=4.0.0, markdown>=3.4.0

# Testing
pytest>=7.4.0, pytest-cov>=4.1.0, httpx>=0.24.0
```

---

## 2. Test Coverage Analysis

### 2.1 Current State

```
Total:   555 tests
Passed:  412 (74.2%)
Failed:  140 (25.2%)
Skipped:   3 (0.5%)
```

### 2.2 Failure Categories

| Category | Count | Root Cause |
|----------|-------|------------|
| Saw Batch Query Endpoints | ~25 | Endpoints not implemented |
| Learning System | ~10 | Endpoints not implemented |
| Metrics Rollup | ~8 | Endpoints not implemented |
| Bridge Router | 12 | URL path mismatch |
| Art Studio | 35+ | Routers not mounted |
| Helical Router | 14 | Endpoints not implemented |
| Runs V2 / RMOS | ~10 | Schema mismatches |
| Other | ~26 | Various |

### 2.3 Gap Documentation

Full gap analysis: [`BOOKMARK_TEST_GAPS.md`](../../BOOKMARK_TEST_GAPS.md)

---

## 3. Feature Readiness

### 3.1 Production Ready ✅

| Feature | Endpoint | Tests |
|---------|----------|-------|
| Health Check | `GET /health` | ✅ |
| Adaptive Pocket | `POST /api/cam/pocket/adaptive/*` | ✅ |
| Polygon Offset | `POST /polygon_offset.nc` | ✅ |
| RMOS Runs v2 | `GET/POST /api/rmos/runs/*` | ✅ |
| Saw Batch Spec | `POST /api/saw/batch/spec` | ✅ |
| Saw Batch Plan | `POST /api/saw/batch/plan` | ✅ |
| Saw Batch Approve | `POST /api/saw/batch/approve` | ✅ |
| Saw Batch Toolpaths | `POST /api/saw/batch/toolpaths` | ✅ |
| Saw G-code Export | `GET /api/saw/batch/executions/{id}/gcode` | ✅ |

### 3.2 Partially Implemented ⚠️

| Feature | Issue | Action Needed |
|---------|-------|---------------|
| Bridge Calculator | Mounted at `/api/cam/bridge/*` but tests expect `/cam/bridge/*` | Fix URL or tests |
| Saw Job Log | Core endpoint works, rollup hooks incomplete | Implement rollup hooks |
| Saw Batch Queries | `/executions` exists but missing filter params | Add query params |

### 3.3 Not Implemented ❌

| Feature | Missing Endpoints |
|---------|-------------------|
| Saw Batch Aliases | `/executions/by-decision`, `/decisions/by-plan`, `/decisions/by-spec` |
| Learning System | `/learning-overrides/apply`, `/learning-overrides/resolve` |
| Metrics Rollup | `/metrics/rollup/by-execution`, `/metrics/rollup/alias` |
| Art Studio Bracing | All preview/export/preset endpoints |
| Art Studio Inlay | All preview/export/preset endpoints |
| Helical Entry | All helical toolpath endpoints |

---

## 4. Docker Deployment

### 4.1 Configuration Files

| File | Purpose | Status |
|------|---------|--------|
| `docker-compose.yml` | Development stack | ✅ |
| `docker-compose.production.yml` | Production stack | ✅ |
| `services/api/Dockerfile` | API container | ✅ |
| `client/Dockerfile` | Client container | ✅ |

### 4.2 Services

```yaml
services:
  api:
    build: services/api
    ports: ["8000:8000"]
    healthcheck: curl -fsS http://127.0.0.1:8000/health

  client:
    build: client
    ports: ["8080:8080"]
    depends_on: [api]

  proxy:  # Optional
    image: nginx:alpine
    ports: ["8088:80"]
```

### 4.3 Deployment Commands

```bash
# Development
docker compose up --build

# Production
docker compose -f docker-compose.production.yml up -d

# Health check
curl http://localhost:8000/health
```

---

## 5. CI/CD Pipeline

### 5.1 Workflow Count: 35

| Category | Workflows | Status |
|----------|-----------|--------|
| API Tests | `api_pytest.yml`, `api_health_*.yml` | ✅ |
| CAM Tests | `cam_essentials.yml`, `cam_gcode_smoke.yml` | ✅ |
| Adaptive Pocket | `adaptive_pocket.yml` (62KB) | ✅ |
| Blueprint | `blueprint_phase3.yml` | ⚠️ |
| Gates | `artifact_linkage_gate.yml`, `cbsp21_*.yml` | ✅ |
| DXF Security | `api_dxf_tests.yml` | ✅ |
| AI Sandbox | `ai_sandbox_enforcement.yml` | ✅ |

### 5.2 Critical Workflows

```
adaptive_pocket.yml      - Core CAM processing (largest workflow)
api_health_and_smoke.yml - API startup validation
artifact_linkage_gate.yml - RMOS artifact integrity
```

---

## 6. Operational Risks

### 6.1 High Priority

| Risk | Impact | Mitigation |
|------|--------|------------|
| 140 failing tests | False confidence in deployments | Complete implementations |
| URL mismatches | 404 errors in production | Audit all router mounts |
| Missing query endpoints | Users can't filter/search | Implement alias endpoints |

### 6.2 Medium Priority

| Risk | Impact | Mitigation |
|------|--------|------------|
| Unmounted routers | Features unavailable | Mount in `main.py` |
| Schema mismatches | Pydantic validation errors | Align schemas with tests |
| Learning system gaps | No feedback loop | Implement learning hooks |

### 6.3 Low Priority

| Risk | Impact | Mitigation |
|------|--------|------------|
| 3 skipped tests | Minor coverage gap | Investigate skip reasons |
| Duplicate operation IDs | OpenAPI warnings | Rename endpoints |

---

## 7. Pre-Production Checklist

### 7.1 Critical (Must Fix)

- [ ] Implement Saw Batch query endpoints (`/executions` with filters)
- [ ] Implement alias endpoints (`by-decision`, `by-plan`, `by-spec`)
- [ ] Fix Bridge Router URL mismatch
- [ ] Mount Art Studio routers in `main.py`
- [ ] Achieve 95%+ test pass rate

### 7.2 Important (Should Fix)

- [ ] Implement Learning System endpoints
- [ ] Implement Metrics Rollup endpoints
- [ ] Implement Helical Router endpoints
- [ ] Add CSV export endpoints
- [ ] Resolve Pydantic schema mismatches

### 7.3 Nice to Have

- [ ] Resolve OpenAPI duplicate operation ID warnings
- [ ] Investigate and fix skipped tests
- [ ] Add missing test coverage for edge cases

---

## 8. Recent Changes (Last 5 Commits)

```
019475b docs: add test gaps bookmark for future session
27c1f70 feat(rmos): persist candidate list view prefs to localStorage
af8cc21 refactor(saw-lab): extract artifact store and add pluggable reader
53542cd feat(rmos): copy candidate_id/advisory_id buttons + toast
c6195c9 fix(api): repair corrupted newline escapes in router files
```

---

## 9. Recommendations

### 9.1 Immediate Actions (This Week)

1. **Fix Bridge Router URL** - Either update tests to use `/api/cam/bridge/*` or change mount point
2. **Add Saw Batch `/executions` query** - Enable filtering by `batch_label`, pagination
3. **Mount Art Studio routers** - Add to `main.py` include_router calls

### 9.2 Short-Term (2 Weeks)

1. Implement all alias endpoints (by-decision, by-plan, by-spec)
2. Implement Learning System apply/resolve endpoints
3. Target 90%+ test pass rate

### 9.3 Medium-Term (1 Month)

1. Complete Metrics Rollup system
2. Complete Helical Router
3. Target 95%+ test pass rate
4. Production deployment readiness review

---

## 10. Verdict

| Aspect | Status |
|--------|--------|
| Core API | ✅ READY |
| Docker Deployment | ✅ READY |
| CI/CD Pipeline | ✅ READY |
| Test Coverage | ❌ NOT READY (74.5%) |
| Feature Completeness | ❌ NOT READY (many unimplemented) |
| Production Deployment | ❌ NOT READY |

**Overall Status:** Development phase. The core architecture is solid, Docker and CI/CD are well-configured, but significant feature implementation work remains before production readiness.

**Estimated time to production readiness:** 2-4 weeks of focused development to implement missing endpoints and achieve 95%+ test pass rate.

---

*Generated: January 4, 2026*
*See also: [`BOOKMARK_TEST_GAPS.md`](../../BOOKMARK_TEST_GAPS.md) for detailed gap analysis*
