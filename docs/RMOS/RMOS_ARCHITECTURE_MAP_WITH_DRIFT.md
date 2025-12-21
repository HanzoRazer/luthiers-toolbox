# RMOS System Architecture Map — With Drift Analysis

**Date:** December 19, 2025
**Purpose:** Developer reference with implementation status and drift tracking
**Scope:** RMOS subsystem architecture — what's documented vs. what exists

---

## Drift Legend

| Symbol | Meaning |
|--------|---------|
| `[IMPLEMENTED]` | Documented AND exists |
| `[DRIFT:MISSING]` | Documented but does NOT exist |
| `[DRIFT:UNDOCUMENTED]` | Exists but NOT documented |
| `[DRIFT:LOCATION]` | Exists but at different path than documented |
| `[DRIFT:SIGNATURE]` | Exists but API differs from documentation |

---

## 1. Feasibility Engine System

### 1.1 Engine Registry Pattern

| Component | Documented Path | Actual Status |
|-----------|-----------------|---------------|
| `FeasibilityEngine` base class | `rmos/engines/base.py` | `[IMPLEMENTED]` |
| `BaselineFeasibilityEngineV1` | `rmos/engines/feasibility_baseline_v1.py` | `[IMPLEMENTED]` |
| `StubFeasibilityEngine` | `rmos/engines/feasibility_stub.py` | `[IMPLEMENTED]` |
| `EngineRegistry` | `rmos/engines/registry.py` | `[IMPLEMENTED]` |

### 1.2 Feasibility Evaluation

| Component | Documented Path | Actual Status |
|-----------|-----------------|---------------|
| `evaluate_feasibility()` | `rmos/feasibility_fusion.py` | `[IMPLEMENTED]` |
| `feasibility_router.py` | `rmos/feasibility_router.py` | `[IMPLEMENTED]` |
| `feasibility_scorer.py` | `rmos/feasibility_scorer.py` | `[IMPLEMENTED]` |

### 1.3 Drift Notes — Feasibility

```
[DRIFT:SIGNATURE] FeasibilityResponse
  - DOCUMENTED: Basic response fields
  - ACTUAL: Now includes `request_id` and `compute_ms` fields (added Dec 19)
```

---

## 2. Run Artifacts System

### 2.1 v1 (Legacy) — `rmos/runs/`

| Component | Documented Path | Actual Status |
|-----------|-----------------|---------------|
| `runs/__init__.py` | `rmos/runs/__init__.py` | `[DRIFT:MISSING]` — Exports reference missing files |
| `runs/schemas.py` | `rmos/runs/schemas.py` | `[DRIFT:MISSING]` — v1 not implemented |
| `runs/store.py` | `rmos/runs/store.py` | `[DRIFT:MISSING]` — v1 not implemented |
| `runs/hashing.py` | `rmos/runs/hashing.py` | `[DRIFT:MISSING]` — v1 not implemented |

### 2.2 v2 (Governance-Compliant) — `rmos/runs_v2/`

| Component | Path | Status |
|-----------|------|--------|
| `RunArtifact` schema | `rmos/runs_v2/schemas.py` | `[IMPLEMENTED]` Pydantic, immutable |
| `RunStoreV2` | `rmos/runs_v2/store.py` | `[IMPLEMENTED]` Date-partitioned |
| `api_runs.py` | `rmos/runs_v2/api_runs.py` | `[IMPLEMENTED]` Full REST API |
| `hashing.py` | `rmos/runs_v2/hashing.py` | `[IMPLEMENTED]` SHA256 utilities |
| `attachments.py` | `rmos/runs_v2/attachments.py` | `[IMPLEMENTED]` Content-addressed |
| `diff.py` | `rmos/runs_v2/diff.py` | `[IMPLEMENTED]` Run comparison |
| `compat.py` | `rmos/runs_v2/compat.py` | `[DRIFT:UNDOCUMENTED]` v1→v2 migration |
| `cli_migrate.py` | `rmos/runs_v2/cli_migrate.py` | `[DRIFT:UNDOCUMENTED]` CLI migration tool |
| `migration_utils.py` | `rmos/runs_v2/migration_utils.py` | `[DRIFT:UNDOCUMENTED]` Migration helpers |

### 2.3 Run Artifacts API Endpoints

| Endpoint | Documented | Actual Status |
|----------|------------|---------------|
| `GET /api/runs` | Yes | `[IMPLEMENTED]` |
| `GET /api/runs/{run_id}` | Yes | `[IMPLEMENTED]` |
| `POST /api/runs` | No | `[DRIFT:UNDOCUMENTED]` Creates immutable artifact |
| `POST /api/runs/{run_id}/attach-advisory` | No | `[DRIFT:UNDOCUMENTED]` Append-only advisory |
| `GET /api/runs/{run_id}/advisories` | No | `[DRIFT:UNDOCUMENTED]` List advisories |
| `POST /api/runs/{run_id}/suggest-and-attach` | No | `[DRIFT:UNDOCUMENTED]` Generate & attach explanation |
| `GET /api/runs/{run_id}/attachments` | No | `[DRIFT:UNDOCUMENTED]` List attachments |
| `GET /api/runs/{run_id}/attachments/{sha256}` | No | `[DRIFT:UNDOCUMENTED]` Download blob |
| `GET /api/runs/{run_id}/attachments/verify` | No | `[DRIFT:UNDOCUMENTED]` Integrity check |
| `GET /api/runs/diff` | No | `[DRIFT:UNDOCUMENTED]` Compare two runs |

### 2.4 Drift Notes — Run Artifacts

```
[DRIFT:LOCATION] Run Artifacts Implementation
  - DOCUMENTED: rmos/runs/
  - ACTUAL: rmos/runs_v2/ (governance-compliant rewrite)
  - REASON: v2 uses Pydantic + date-partitioned storage per contract

[DRIFT:UNDOCUMENTED] RunArtifact Schema Fields
  - `request_id` field added for audit trail
  - `advisory_inputs` list for append-only references
  - `explanation_status` / `explanation_summary` for AI explanations
```

---

## 3. Advisory Assets System (AI-Generated Content)

### 3.1 Core Advisory Infrastructure

| Component | Documented Path | Actual Status |
|-----------|-----------------|---------------|
| `AdvisoryAsset` schema | `_experimental/ai_graphics/schemas/advisory_schemas.py` | `[IMPLEMENTED]` |
| `AdvisoryAssetStore` | `_experimental/ai_graphics/advisory_store.py` | `[IMPLEMENTED]` |
| `advisory_routes.py` | `_experimental/ai_graphics/api/advisory_routes.py` | `[DRIFT:UNDOCUMENTED]` |

### 3.2 Teaching Loop (LoRA Training Export)

| Component | Path | Status |
|-----------|------|--------|
| `TeachingLoopExporter` | `_experimental/ai_graphics/services/teaching_loop.py` | `[DRIFT:UNDOCUMENTED]` |
| `teaching_routes.py` | `_experimental/ai_graphics/api/teaching_routes.py` | `[DRIFT:UNDOCUMENTED]` |

### 3.3 Image Generation

| Component | Documented Path | Actual Status |
|-----------|-----------------|---------------|
| `GuitarVisionEngine` | `_experimental/ai_graphics/image_providers.py` | `[IMPLEMENTED]` |
| `OpenAIImageTransport` | `_experimental/ai_graphics/image_transport.py` | `[IMPLEMENTED]` |
| `prompt_engine.py` | `_experimental/ai_graphics/prompt_engine.py` | `[IMPLEMENTED]` |

### 3.4 Advisory API Endpoints

| Endpoint | Status |
|----------|--------|
| `POST /api/advisory/generate/image` | `[DRIFT:UNDOCUMENTED]` DALL-E generation |
| `GET /api/advisory/assets` | `[DRIFT:UNDOCUMENTED]` List assets |
| `GET /api/advisory/assets/{id}` | `[DRIFT:UNDOCUMENTED]` Get asset |
| `GET /api/advisory/assets/{id}/content` | `[DRIFT:UNDOCUMENTED]` Download binary |
| `POST /api/advisory/assets/{id}/review` | `[DRIFT:UNDOCUMENTED]` Human approval |
| `GET /api/advisory/pending` | `[DRIFT:UNDOCUMENTED]` Pending review |
| `GET /api/advisory/stats` | `[DRIFT:UNDOCUMENTED]` Statistics |

### 3.5 Teaching Loop API Endpoints

| Endpoint | Status |
|----------|--------|
| `POST /api/teaching/export` | `[DRIFT:UNDOCUMENTED]` Export to Kohya |
| `GET /api/teaching/stats` | `[DRIFT:UNDOCUMENTED]` Export statistics |
| `GET /api/teaching/ready` | `[DRIFT:UNDOCUMENTED]` Training readiness |
| `GET /api/teaching/workflow` | `[DRIFT:UNDOCUMENTED]` Current stage |

### 3.6 Drift Notes — Advisory System

```
[DRIFT:UNDOCUMENTED] Complete Advisory Layer
  - advisory_routes.py with 7 endpoints
  - teaching_loop.py for LoRA training export
  - teaching_routes.py with 4 endpoints
  - Human-in-the-loop approval workflow
  - Date-partitioned asset storage
```

---

## 4. Request Infrastructure

### 4.1 Request ID Middleware

| Component | Path | Status |
|-----------|------|--------|
| `RequestIdMiddleware` | `app/main.py` | `[DRIFT:UNDOCUMENTED]` |
| `request_context.py` | `app/util/request_context.py` | `[DRIFT:UNDOCUMENTED]` |
| `request_utils.py` | `app/util/request_utils.py` | `[DRIFT:UNDOCUMENTED]` |
| `logging_request_id.py` | `app/util/logging_request_id.py` | `[DRIFT:UNDOCUMENTED]` |

### 4.2 Drift Notes — Request Infrastructure

```
[DRIFT:UNDOCUMENTED] Full Request Correlation
  - X-Request-Id header auto-generated or echoed
  - ContextVar propagation for deep logging
  - RequestIdFilter for automatic log injection
  - Test fixtures auto-inject request IDs
```

---

## 5. Database & Persistence Layer

### 5.1 SQLite Infrastructure

| Component | Documented Path | Actual Status |
|-----------|-----------------|---------------|
| `RMOSDatabase` | `core/rmos_db.py` | `[IMPLEMENTED]` |
| `SQLiteStoreBase` | `stores/sqlite_base.py` | `[IMPLEMENTED]` |
| `sqlite_pattern_store.py` | `stores/sqlite_pattern_store.py` | `[IMPLEMENTED]` |
| `sqlite_joblog_store.py` | `stores/sqlite_joblog_store.py` | `[IMPLEMENTED]` |

### 5.2 Migrations

| Component | Documented Path | Actual Status |
|-----------|-----------------|---------------|
| `app/db/migrations/` | `app/db/migrations/` | `[DRIFT:MISSING]` — Directory not created |
| `0001_init_workflow_sessions.sql` | `app/db/migrations/` | `[DRIFT:MISSING]` |

### 5.3 `.gitignore` Issue

```
[DRIFT:CONFIG] .gitignore line 110
  - DOCUMENTED: Should allow app/db/migrations/
  - ACTUAL: "migrations/" unanchored — blocks ALL migrations/ directories
  - FIX: Change to "/migrations/" (anchored to root)
```

---

## 6. Documentation Drift Summary

### 6.1 Files That Exist But Are Undocumented

```
NEW IMPLEMENTATIONS (Dec 19, 2025):
├── app/util/
│   ├── __init__.py              [UNDOCUMENTED]
│   ├── request_context.py       [UNDOCUMENTED]
│   ├── request_utils.py         [UNDOCUMENTED]
│   └── logging_request_id.py    [UNDOCUMENTED]
├── app/rmos/runs_v2/
│   ├── compat.py                [UNDOCUMENTED]
│   ├── cli_migrate.py           [UNDOCUMENTED]
│   └── migration_utils.py       [UNDOCUMENTED]
├── app/_experimental/ai_graphics/api/
│   ├── advisory_routes.py       [UNDOCUMENTED]
│   └── teaching_routes.py       [UNDOCUMENTED]
└── app/_experimental/ai_graphics/services/
    └── teaching_loop.py         [UNDOCUMENTED]
```

### 6.2 Files Documented But Missing

```
MISSING:
├── app/rmos/runs/
│   ├── schemas.py               [DOCUMENTED BUT MISSING - superseded by runs_v2]
│   ├── store.py                 [DOCUMENTED BUT MISSING - superseded by runs_v2]
│   └── hashing.py               [DOCUMENTED BUT MISSING - superseded by runs_v2]
└── app/db/migrations/
    ├── 0001_init_workflow_sessions.sql  [DOCUMENTED BUT MISSING]
    └── 0002_add_indexes.sql             [DOCUMENTED BUT MISSING]
```

---

## 7. Recommended Documentation Updates

### Priority 1: Update RMOS_ARCHITECTURE_MAP.md

1. Change Section 2 "Run Artifacts System" to reference `runs_v2/`
2. Add Section for Request ID Middleware
3. Add Advisory API endpoints
4. Add Teaching Loop endpoints
5. Document `suggest-and-attach` endpoint

### Priority 2: Create New Documentation

1. `docs/canonical/REQUEST_ID_MIDDLEWARE.md`
2. `docs/canonical/ADVISORY_LAYER_API.md`
3. `docs/canonical/TEACHING_LOOP_WORKFLOW.md`

### Priority 3: Fix Configuration

1. `.gitignore` line 110: Change `migrations/` to `/migrations/`

---

## 8. Quick Reference: Actual File Locations

### Feasibility System
```
services/api/app/rmos/
├── engines/
│   ├── __init__.py
│   ├── base.py                  # FeasibilityEngine ABC
│   ├── feasibility_baseline_v1.py
│   ├── feasibility_stub.py
│   └── registry.py              # EngineRegistry
├── feasibility_fusion.py        # evaluate_feasibility()
├── feasibility_router.py        # /api/rmos/feasibility/*
└── feasibility_scorer.py        # Risk dimension scorers
```

### Run Artifacts (v2 — Active)
```
services/api/app/rmos/runs_v2/
├── __init__.py
├── schemas.py                   # RunArtifact, Hashes, etc.
├── store.py                     # RunStoreV2 (date-partitioned)
├── api_runs.py                  # /api/runs/* endpoints
├── hashing.py                   # SHA256 utilities
├── attachments.py               # Content-addressed blobs
├── diff.py                      # Run comparison
├── compat.py                    # v1 → v2 conversion
├── migration_utils.py           # Data migration
└── cli_migrate.py               # CLI tool
```

### Advisory System
```
services/api/app/_experimental/ai_graphics/
├── advisory_store.py            # AdvisoryAssetStore
├── schemas/
│   └── advisory_schemas.py      # AdvisoryAsset, types
├── api/
│   ├── advisory_routes.py       # /api/advisory/*
│   └── teaching_routes.py       # /api/teaching/*
├── services/
│   └── teaching_loop.py         # TeachingLoopExporter
├── image_providers.py           # GuitarVisionEngine
├── image_transport.py           # OpenAIImageTransport
└── prompt_engine.py             # Prompt construction
```

### Request Infrastructure
```
services/api/app/
├── main.py                      # RequestIdMiddleware
└── util/
    ├── __init__.py
    ├── request_context.py       # ContextVar
    ├── request_utils.py         # require_request_id()
    └── logging_request_id.py    # RequestIdFilter
```

---

**Document Version:** 2.0 (With Drift Analysis)
**Last Updated:** December 19, 2025
