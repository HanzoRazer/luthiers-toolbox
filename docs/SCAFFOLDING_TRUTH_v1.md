# Scaffolding Truth Document v1

> **Last Updated:** 2026-01-01  
> **Status:** Authoritative source for code placement, routing, and boundaries  
> **Audience:** AI agents, contributors shipping bundles

---

## 1) Repo Topology Truth

### Root Structure

```
luthiers-toolbox/
├── services/
│   └── api/                      # 🎯 BACKEND ROOT
│       ├── app/                  #    FastAPI application
│       │   ├── main.py           #    ⭐ ENTRYPOINT - all router mounts
│       │   ├── routers/          #    Individual route modules
│       │   ├── rmos/             #    RMOS domain (orchestration)
│       │   ├── art_studio/       #    Art Studio domain
│       │   ├── cam/              #    CAM consolidated (Wave 18)
│       │   ├── compare/          #    Compare consolidated (Wave 19)
│       │   ├── saw_lab/          #    CNC Saw Lab domain
│       │   ├── workflow/         #    Workflow sessions (SQLite)
│       │   ├── _experimental/    #    ⚠️ SANDBOX - optional routers
│       │   ├── schemas/          #    Pydantic models
│       │   ├── services/         #    Business logic
│       │   ├── data/             #    Static data files (posts, machines)
│       │   └── ...
│       ├── tests/                #    Backend tests
│       ├── data/                 #    Runtime data storage
│       └── .venv/                #    Python virtual environment
│
├── packages/
│   ├── client/                   # 🎯 FRONTEND ROOT (Vue 3 + Vite)
│   │   └── src/
│   │       ├── main.ts           #    Vue entrypoint
│   │       ├── App.vue           #    Root component
│   │       ├── router/           #    Vue Router config
│   │       ├── stores/           #    Pinia stores
│   │       ├── api/              #    Legacy API clients (being migrated)
│   │       ├── sdk/              #    ⭐ NEW: Typed SDK (H8.3)
│   │       ├── components/       #    Vue components
│   │       ├── views/            #    Route views
│   │       ├── types/            #    TypeScript types
│   │       └── ...
│   │
│   └── shared/                   #    Shared utilities (minimal)
│
├── docs/                         #    Documentation
├── __REFERENCE__/                #    🔒 READ-ONLY reference data
└── __ARCHIVE__/                  #    Historical/deprecated code
```

### Key Paths Summary

| Area | Canonical Path | Notes |
|------|----------------|-------|
| **API App Root** | `services/api/app/` | FastAPI application |
| **API Entrypoint** | `services/api/app/main.py` | Router mounting |
| **API Tests** | `services/api/tests/` | pytest |
| **Frontend Root** | `packages/client/` | Vue 3 + Vite |
| **Frontend Source** | `packages/client/src/` | TypeScript/Vue |
| **SDK (typed helpers)** | `packages/client/src/sdk/` | H8.3 pattern |
| **Shared Libs** | `packages/shared/` | Minimal usage |
| **Reference Data** | `__REFERENCE__/` | 🔒 IMMUTABLE |

---

## 2) Router Mount Truth

### Entrypoint: `services/api/app/main.py`

**Total Routers:** ~116 working  
**Pattern:** Import at top, mount in middle, optional routers use `try/except`

### Router Categories & Prefixes

| Category | Prefix | Example Endpoints |
|----------|--------|-------------------|
| **Core CAM** | `/api/sim`, `/api/feeds`, `/api/geometry`, etc. | 11 routers |
| **RMOS** | `/api/rmos` | `/api/rmos/runs`, `/api/rmos/profiles` |
| **CAM Consolidated** (Wave 18) | `/api/cam` | `/api/cam/toolpath/*`, `/api/cam/drilling/*` |
| **Compare Consolidated** (Wave 19) | `/api/compare` | `/api/compare/baselines/*` |
| **Art Studio** | `/api/art` | `/api/art/patterns`, `/api/art/rosette/*` |
| **Saw Lab** | `/api/saw` | `/api/saw/batch/*`, `/api/saw/compare/*` |
| **Guitar Specialty** | `/api/guitar/{type}` | `/api/guitar/archtop`, `/api/guitar/om` |

### Feature Flags

| Flag | Default | Controls |
|------|---------|----------|
| `RMOS_RUNS_V2_ENABLED` | `"true"` | v2 (date-partitioned) vs v1 (legacy) runs |
| `RUN_MIGRATIONS_ON_STARTUP` | `"false"` | SQLite migrations |

### Optional Router Pattern

Routers in `_experimental/` and specialty modules use:

```python
try:
    from .routers.archtop_router import router as archtop_router
except ImportError as e:
    archtop_router = None
    _log.warning("Optional router archtop_router not available: %s", e)

# Later:
if archtop_router:
    app.include_router(archtop_router, prefix="/api/guitar/archtop", tags=["Guitar"])
```

### Middleware Stack (Order Matters)

1. `RequestIdMiddleware` — Correlation IDs (FIRST)
2. `CORSMiddleware` — CORS headers
3. `DeprecationHeadersMiddleware` — Legacy lane warnings
4. `EndpointGovernanceMiddleware` — Usage tracking (H4)

---

## 3) Domain Boundaries & Ownership Rules

### 🔒 IMMUTABLE (Do Not Modify)

| Path | Reason |
|------|--------|
| `__REFERENCE__/` | Reference data, DXFs, tool databases |
| `services/api/app/geometry/` | Core geometry algorithms |
| `services/api/app/cam_core/` | CAM algorithms |
| `services/api/app/calculators/` | Calculation engines |
| `services/api/app/ci/` | CI gates (unless fixing gates) |

### ⚠️ SANDBOX-ONLY

| Path | Notes |
|------|-------|
| `services/api/app/_experimental/` | Optional imports, safe to fail |
| `services/api/app/sandboxes/` | Experimental features |

### ✅ ALLOWED TO MODIFY

| Path | Scope |
|------|-------|
| `services/api/app/art_studio/` | Art Studio bundles |
| `services/api/app/rmos/` | RMOS orchestration |
| `services/api/app/saw_lab/` | CNC Saw Lab |
| `services/api/app/routers/` | New endpoints |
| `services/api/app/workflow/` | Workflow sessions |
| `packages/client/src/` | Frontend features |

### Import Boundaries (CI-Enforced)

**ToolBox CANNOT import:**
- `tap_tone.*` (Analyzer core)
- `modes.*` (Modal analysis)

See: [BOUNDARY_RULES.md](./BOUNDARY_RULES.md)

### Naming Conventions

| Item | Convention | Example |
|------|------------|---------|
| Router files | `{domain}_{feature}_router.py` | `cam_roughing_router.py` |
| API prefix | `/api/{domain}/{operation}` | `/api/cam/toolpath/roughing` |
| Pinia stores | `use{Domain}Store.ts` | `useRmosRunsStore.ts` |
| SDK endpoints | `sdk/endpoints/{domain}/` | `sdk/endpoints/cam/` |
| Test files | `test_{feature}.py` | `test_runs_filter_batch_label.py` |

---

## 4) Canonical Service Layer Structure

### Backend (FastAPI + Pydantic V2)

```
services/api/app/
├── main.py                    # Entrypoint, middleware, router mounts
├── routers/                   # API route handlers
│   └── {feature}_router.py   # Each returns FastAPI `APIRouter`
├── schemas/                   # Pydantic V2 models (request/response)
│   └── {domain}_schemas.py
├── services/                  # Business logic layer
│   └── {domain}_service.py
├── {domain}/                  # Domain modules (RMOS, art_studio, etc.)
│   ├── api/                   # Domain-specific routers
│   │   └── {feature}_routes.py
│   ├── schemas*.py            # Domain schemas
│   ├── *_service.py           # Domain services
│   └── store.py               # Storage adapters
└── data/                      # Static data (posts, machines, tools)
```

### Frontend (Vue 3 + TypeScript)

```
packages/client/src/
├── main.ts                    # Vue entrypoint
├── router/                    # Vue Router
│   └── index.ts
├── stores/                    # Pinia stores
│   └── use{Domain}Store.ts
├── sdk/                       # ⭐ Typed API helpers (H8.3)
│   ├── core/                  # Transport layer
│   │   ├── apiFetch.ts        # Simple (returns data)
│   │   └── apiFetchRaw.ts     # Raw (returns {data, response})
│   └── endpoints/             # Per-domain helpers
│       ├── index.ts           # Aggregated exports
│       └── cam/               # CAM endpoints
│           ├── cam.ts
│           ├── types.ts
│           └── roughing.ts
├── api/                       # ⚠️ LEGACY - migrate to sdk/
├── views/                     # Route components
├── components/                # Reusable components
└── types/                     # TypeScript definitions
```

### What Changed (Delta Notes)

| Change | Old | New |
|--------|-----|-----|
| CAM routes | Scattered in `routers/cam_*.py` | Consolidated in `cam/routers/` (Wave 18) |
| Compare routes | Scattered | Consolidated in `compare/routers/` (Wave 19) |
| RMOS runs | `rmos/runs/` (v1 legacy) | `rmos/runs_v2/` (date-partitioned) |
| Frontend API | `api/*.ts` clients | `sdk/endpoints/` typed helpers |
| Request IDs | Per-call | Global middleware + ContextVar |

---

## 5) Storage & Environment Variables

### Canonical Data Roots

| Purpose | Default Path | Env Var |
|---------|--------------|---------|
| **RMOS Runs v2** | `services/api/data/runs/rmos/` | `RMOS_RUNS_DIR` |
| **Run Attachments** | `services/api/data/attachments/` | `RMOS_RUN_ATTACHMENTS_DIR` |
| **Run Artifacts** | `data/run_artifacts/` | `RMOS_ARTIFACT_ROOT` |
| **Variant State** | `services/api/data/variant_state/` | `RMOS_RUN_VARIANT_STATE_DIR` |
| **Compare Baselines** | `services/api/app/data/compare/baselines/` | (hardcoded) |
| **CNC Production** | `app/data/cnc_production/` | (hardcoded) |
| **Workflow Sessions DB** | (auto) | `RMOS_DB_PATH` |
| **Profile YAML** | (auto) | `RMOS_PROFILE_YAML_PATH` |
| **Profile History** | (auto) | `RMOS_PROFILE_HISTORY_PATH` |

### All RMOS Environment Variables

```bash
# Core Storage
RMOS_RUNS_DIR                          # Runs v2 store root
RMOS_RUN_ATTACHMENTS_DIR               # Binary attachments
RMOS_ARTIFACT_ROOT                     # Run artifacts
RMOS_RUN_VARIANT_STATE_DIR             # Advisory variant state
RMOS_DB_PATH                           # SQLite database path
RMOS_PROFILE_YAML_PATH                 # Constraint profiles
RMOS_PROFILE_HISTORY_PATH              # Profile history

# Feature Flags
RMOS_RUNS_V2_ENABLED=true              # Use v2 runs (date-partitioned)
RMOS_REPLAY_GATE_MODE=block            # block|warn|off
RMOS_REPLAY_GATE_REQUIRE_NOTE=true     # Require note on replay

# Rate Limiting & Security
RMOS_DELETE_RATE_LIMIT_MAX=10          # Max deletes per window
RMOS_DELETE_RATE_LIMIT_WINDOW=60       # Window in seconds
RMOS_MAX_ATTACHMENT_BYTES              # Max upload size
RMOS_ACOUSTICS_STREAM_TOKEN            # Stream auth token
RMOS_SIGNED_URL_SECRET                 # URL signing secret
RMOS_ACOUSTICS_ZIP_MAX_ITEMS           # Max items in ZIP
RMOS_ACOUSTICS_ZIP_MAX_TOTAL_INPUT_BYTES
RMOS_ACOUSTICS_ZIP_MAX_OUTPUT_BYTES
RMOS_ACOUSTICS_SIGNED_BATCH_MAX_ITEMS

# Database
RUN_MIGRATIONS_ON_STARTUP=false
MIGRATIONS_DRY_RUN=false
MIGRATIONS_FAIL_HARD=true
```

### File-Based Storage (Dev)

**Yes, file-based storage is allowed for dev:**
- Runs v2: JSON files in date-partitioned dirs
- Attachments: SHA256-named blobs
- Baselines: JSON files
- Index: `_index.json` for fast queries

---

## 6) Frontend Conventions

### Path Aliases

**`vite.config.ts`:**
```typescript
resolve: {
  alias: {
    '@': fileURLToPath(new URL('./src', import.meta.url))
  }
}
```

**`tsconfig.json`:**
```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

**Usage:** `import { cam } from "@/sdk/endpoints"`

### Pinia Store Conventions

**Location:** `packages/client/src/stores/`

**Naming:** `use{Domain}Store.ts`

**Current Stores:**
- `useRmosRunsStore.ts` — RMOS run artifacts
- `useRosettePatternStore.ts` — Rosette patterns
- `useSawLearnStore.ts` — Saw learning
- `useArtStudioEngine.ts` — Art Studio state
- `useJobLogStore.ts` — Job logging
- ... (21 total)

### API Client Conventions

**SDK Pattern (H8.3 - PREFERRED):**
```typescript
// packages/client/src/sdk/endpoints/cam/roughing.ts
import { postRaw } from "@/sdk/core/apiFetchRaw";
import type { RoughingGcodeRequest, RoughingGcodeResult } from "./types";

export async function roughingGcode(
  payload: RoughingGcodeRequest
): Promise<RoughingGcodeResult> {
  const { data, response } = await postRaw<string>("/api/cam/roughing_gcode", payload);
  return {
    gcode: data,
    summary: parseCamSummary(response),
    requestId: extractRequestId(response),
  };
}
```

**Usage in components:**
```typescript
import { cam } from "@/sdk/endpoints";
const { gcode, summary, requestId } = await cam.roughingGcode(payload);
```

**Legacy Pattern (AVOID - in `api/`):**
```typescript
// packages/client/src/api/rmos.ts
export async function fetchRuns() {
  const response = await fetch("/api/rmos/runs");
  return response.json();
}
```

### Type Conventions

**Location:** `packages/client/src/types/`

**Pattern:** Domain-grouped TypeScript interfaces

---

## 7) Test Harness Expectations

### Backend Tests (pytest)

**Location:** `services/api/tests/`

**Run Commands:**
```bash
# From services/api directory
cd services/api

# Full test suite
.venv/Scripts/python.exe -m pytest tests/ -v

# Specific test file
.venv/Scripts/python.exe -m pytest tests/test_runs_filter_batch_label.py -v

# With coverage
.venv/Scripts/python.exe -m pytest tests/ --cov=app --cov-report=html

# Fast (no coverage)
.venv/Scripts/python.exe -m pytest tests/ -v --no-cov

# RMOS-specific (uses rmos_pytest.ini)
.venv/Scripts/python.exe -m pytest tests/ -c ../../rmos_pytest.ini -v
```

**Key Fixtures:**
- `rmos_global_test_isolation` — Resets run store singleton, sets temp `RMOS_RUNS_DIR`
- `client` — FastAPI TestClient

**Test Isolation:**
```python
# tests/conftest.py pattern
@pytest.fixture(autouse=True)
def rmos_global_test_isolation(tmp_path, monkeypatch):
    """Reset singleton and isolate storage per test."""
    from app.rmos.runs_v2 import store
    store._default_store = None
    monkeypatch.setenv("RMOS_RUNS_DIR", str(tmp_path / "runs"))
```

### Frontend Tests (Vitest)

**Location:** `packages/client/src/**/__tests__/`

**Run Commands:**
```bash
# From packages/client directory
cd packages/client

# Run tests
npm run test

# Watch mode
npm run test -- --watch

# Specific file
npm run test -- src/sdk/endpoints/cam/__tests__/cam.endpoints.test.ts
```

### CI Gates

**Backend CI Gates** (`services/api/app/ci/`):

| Gate | Command | Purpose |
|------|---------|---------|
| Endpoint Truth | `python -m app.ci.endpoint_truth_gate check` | Routes match truth map |
| CAM Schema | `python -m app.ci.check_cam_intent_schema_hash` | CamIntentV1 unchanged |
| Boundary | `python -m app.ci.check_boundary_imports --profile toolbox` | No forbidden imports |
| Legacy Usage | `python -m app.ci.legacy_usage_gate` | Frontend not calling legacy |

**Makefile Targets:**
```bash
make smoke-helix-posts   # Integration test
make test-api            # API smoke tests
make start-api           # uvicorn dev server
make start-client        # Vite dev server
```

---

## Quick Reference Card

### Adding a New Backend Endpoint

1. **Create router:** `services/api/app/routers/{feature}_router.py`
2. **Define schemas:** `services/api/app/schemas/{feature}_schemas.py`
3. **Add service:** `services/api/app/services/{feature}_service.py`
4. **Import in `main.py`**
5. **Mount:** `app.include_router(router, prefix="/api/{domain}", tags=[...])`
6. **Add test:** `services/api/tests/test_{feature}.py`

### Adding a New Frontend Feature

1. **Create store:** `packages/client/src/stores/use{Feature}Store.ts`
2. **Add SDK helper:** `packages/client/src/sdk/endpoints/{domain}/{feature}.ts`
3. **Export from index:** `packages/client/src/sdk/endpoints/{domain}/index.ts`
4. **Create view:** `packages/client/src/views/{Feature}View.vue`
5. **Add route:** `packages/client/src/router/index.ts`

### Debugging Checklist

- [ ] Router imported in `main.py`?
- [ ] Router mounted with `include_router()`?
- [ ] Prefix correct? (some routers have built-in prefix)
- [ ] Optional router check: `if router:` before mount?
- [ ] Test isolation fixture resetting singletons?
- [ ] Env var set correctly? (check `.env` and test `monkeypatch`)

---

## Art Studio Mini-Truth (Lane Stub)

**Lane:** Art Studio  
**Goal:** One-page "don't guess" reference for contributors shipping Art Studio changes.

### Canonical Locations

| Area | Path |
|------|------|
| **Backend** | `services/api/app/art_studio/` |
| **Frontend views** | `packages/client/src/views/art-studio/` |
| **Frontend SDK (preferred)** | `packages/client/src/sdk/endpoints/art/` |
| **Frontend stores** | `packages/client/src/stores/useArtStudioEngine.ts` |

### Router Mount Pattern

**Mount family:** `/api/art/*`

**Wave split in `main.py`:**

| Wave | Routers | Pattern |
|------|---------|---------|
| Wave 15 | Art Studio core completion | `art_patterns_router`, `art_generators_router`, `art_preview_router`, `art_snapshots_router`, `art_workflow_router` |
| Wave 20+ | Flatter `/api/art` family | `art_feasibility_router`, `art_snapshot_router` (v2) |

**Rule:** Every Art Studio bundle must declare which wave it targets to avoid shadow endpoints.

### Deprecated Lanes

| Lane Key | Match Prefix | Successor | Middleware |
|----------|--------------|-----------|------------|
| `legacy_art_studio_lane` | `/api/art-studio/*` | `/api/art` | `DeprecationHeadersMiddleware` |
| `transitional_no_api_prefix_lane` | `/rosette/*` | `/api/art` | `DeprecationHeadersMiddleware` |

Headers emitted on deprecated lane hits: `Deprecation`, `Sunset`, `X-Deprecated-Lane`, `Link`

### Storage Truth (Env Vars)

| Variable | Purpose | Default |
|----------|---------|---------|
| `ART_STUDIO_DATA_ROOT` | Root directory for Art Studio data | (app relative) |
| `ART_STUDIO_SNAPSHOTS_DIR` | Snapshot storage directory | (data root)/snapshots |
| `ART_STUDIO_DB_PATH` | Path to Art Studio SQLite database | `art_studio.db` |

### Test Isolation Rule

All Art Studio tests **MUST** override storage roots to a temp directory (`tmp_path`) so tests never touch developer/prod data.

```python
@pytest.fixture(autouse=True)
def art_studio_isolation(tmp_path, monkeypatch):
    monkeypatch.setenv("ART_STUDIO_DATA_ROOT", str(tmp_path / "art"))
    monkeypatch.setenv("ART_STUDIO_SNAPSHOTS_DIR", str(tmp_path / "snapshots"))
```

### Frontend Convention Truth

**Default:** Use typed SDK endpoints under:
- `packages/client/src/sdk/endpoints/art/`

Legacy direct `api/` fetch is allowed only if explicitly stated in the bundle header.

### Bundle Truth Header (Recommended)

Every Art Studio bundle PR/commit should declare:

```yaml
# BUNDLE TRUTH HEADER
wave: 20
mount_prefix: /api/art
deprecation_lanes: [legacy_art_studio_lane]
storage_env: ART_STUDIO_DATA_ROOT
sdk_path: packages/client/src/sdk/endpoints/art/
test_isolation: required
```

---

## See Also

- [ROUTER_MAP.md](../ROUTER_MAP.md) — Complete router organization by wave
- [ENDPOINT_TRUTH_MAP.md](./ENDPOINT_TRUTH_MAP.md) — API surface documentation
- [BOUNDARY_RULES.md](./BOUNDARY_RULES.md) — Import restrictions
- [ROUTING_TRUTH_CONTRACT_v1.md](./ROUTING_TRUTH_CONTRACT_v1.md) — Runtime route introspection
- [packages/client/src/sdk/endpoints/README.md](../packages/client/src/sdk/endpoints/README.md) — SDK patterns

