# Luthier's Tool Box – AI Agent Instructions

> CNC guitar lutherie platform: Vue 3 + FastAPI. **All geometry in mm. DXF R12 (AC1009).** > **Last Updated:** 2026-01-11

## ⚡ Quick Start

```bash
# Backend (FastAPI on :8000)
cd services/api && uvicorn app.main:app --reload --port 8000

# Frontend (Vue on :5173, proxies /api → :8000)
cd packages/client && npm run dev

# Docker (full stack) – recommended for integration testing
docker compose up --build

# Key Tests
cd services/api && pytest tests/ -v                      # All backend tests
cd services/api && pytest tests/ -v -m cam               # By marker: cam, unit, integration, smoke, slow
cd services/api && pytest tests/ -v -m "cam or helical"  # Multiple markers
cd packages/client && npm run test                       # Vitest unit tests
make smoke-helix-posts                                   # Helical post-processor smoke test
make check-boundaries                                    # All architectural fence checks (run before PR)
```

### Pytest Markers (from `services/api/pytest.ini`)

`unit` `integration` `smoke` `slow` `router` `geometry` `adaptive` `bridge` `helical` `cam` `export`

## 🔑 Critical Rules

1. **Units**: Always mm internally – convert only at API boundaries
2. **DXF**: R12 format (AC1009) with closed LWPolylines – never newer versions
3. **SDK**: Use typed helpers (`import { cam } from "@/sdk/endpoints"`) – never raw `fetch()`
4. **CAM Intent**: Use `CamIntentV1` envelope (`app.rmos.cam.CamIntentV1`) – don't create alternatives
5. **DO NOT MODIFY**: `__REFERENCE__/` directory, legacy archives (`Guitar Design HTML app/`, `ToolBox_*`)
6. **Request IDs**: All API responses MUST include `X-Request-Id` header
7. **Machine Profiles**: Use IDs from `machine_profiles.json` (`GRBL_3018_Default`, `Mach4_Router_4x8`, `LinuxCNC_KneeMill`)
8. **Python Modules**: Run as modules (`python -m app.ci.check_boundary_imports`) not scripts
9. **Architectural Fences**: Check [FENCE_REGISTRY.json](../FENCE_REGISTRY.json) before cross-domain imports – CI-enforced
10. **Vue Components**: Use `<script setup lang="ts">` – state in Pinia stores (`packages/client/src/stores/`)

## 📁 Key Paths

| Area                | Path                                                     |
| ------------------- | -------------------------------------------------------- |
| API Entry           | `services/api/app/main.py` – ~116 routers                |
| CAM Algorithms      | `services/api/app/cam/` – pocketing, helical, biarc      |
| RMOS Orchestration  | `services/api/app/rmos/` – workflow, CAM intent          |
| Saw Lab (Reference) | `services/api/app/saw_lab/` – governed operation pattern |
| CAM Intent Schema   | `services/api/app/rmos/cam/schemas_intent.py`            |
| Frontend SDK        | `packages/client/src/sdk/endpoints/` – typed helpers     |
| Post Configs        | `services/api/app/data/posts/*.json` – grbl, mach4, etc. |
| CI Workflows        | `.github/workflows/` – 40 workflow files                 |
| Pinia Stores        | `packages/client/src/stores/` – frontend state           |
| Shared Utils        | `packages/shared/` – cross-package types/utilities       |
| CI Boundary Checks  | `services/api/app/ci/` – boundary enforcement scripts    |

## 🏛️ Architecture Overview

**Monorepo Structure:**

- `services/api/` – FastAPI backend (~116 routers in `app/main.py`)
- `packages/client/` – Vue 3 SPA with Pinia stores
- `packages/shared/` – Cross-package types/utilities
- `projects/rmos/` – Rosette Manufacturing OS documentation

**Data Flow:** Frontend SDK → FastAPI → CAM/RMOS modules → JSON artifacts or G-code

## 🏗️ Architecture: Operation Lanes

Machine-executing endpoints follow **Operation Lane Governance**:

| Lane          | Description                                               | Example                   |
| ------------- | --------------------------------------------------------- | ------------------------- |
| **OPERATION** | Full governance: artifacts, feasibility gate, audit trail | `/api/saw/batch/*`        |
| **UTILITY**   | Stateless/preview, no artifacts                           | `/api/cam/roughing/gcode` |

**Reference Implementation**: CNC Saw Lab (`services/api/app/saw_lab/batch_router.py`)

- Stage sequence: SPEC → PLAN → DECISION → EXECUTE → EXPORT → FEEDBACK
- **Decision Intelligence**: Plan responses include `plan_auto_suggest` for UI tuning recommendations
  - `override_state`: `"CHOSEN"` | `"CLEARED"` | `None`
  - `applied_override`: Active operator override (when CHOSEN)
  - `recommended_latest_approved`: Suggested tuning (only when CLEARED)

## 🔗 Cross-Boundary Patterns

**Never import directly across domains.** Use these patterns:

### Pattern 1: Artifact Contract (Domain A needs B's output)

```python
# Producer writes JSON artifact with SHA256
write_json_artifact("measurement.json", result, sha256=True)
# Consumer reads without code dependency
data = load_json(artifact_path); validate_schema(data)
```

### Pattern 2: HTTP API Contract (Domain A invokes B)

```python
from app.rmos.cam import CamIntentV1
intent = CamIntentV1(mode="roughing", design={"entities": [...]})
response = requests.post("/api/cam/toolpath/roughing/gcode", json=intent.dict())
```

### Pattern 3: SDK Adapter (Frontend → API)

```typescript
// ✅ CORRECT: Typed SDK helper
import { cam } from "@/sdk/endpoints";
const { gcode, summary, requestId } = await cam.roughingGcode(payload);

// ❌ WRONG: Raw fetch bypasses type safety
const response = await fetch("/api/cam/roughing/gcode", {...});
```

## 🧪 Essential Patterns

### Backend: New Router

```python
# services/api/app/routers/my_feature_router.py
from fastapi import APIRouter
router = APIRouter()

@router.post("/do-thing")
def do_thing(req: MyRequest) -> MyResponse: ...

# Register in main.py
app.include_router(my_feature_router, prefix="/api/my-feature", tags=["MyFeature"])
```

### Frontend: SDK Usage

```typescript
import { cam } from "@/sdk/endpoints";
import { ApiError } from "@/sdk/core/errors";

try {
  const { gcode, summary, requestId } = await cam.roughingGcode(payload);
} catch (err) {
  if (err instanceof ApiError && err.is(422)) {
    errorMsg.value = err.details?.message;
  }
}
```

### CAM Intent Envelope

```python
from app.rmos.cam import CamIntentV1
intent = CamIntentV1(mode="roughing", units="mm", design={...})
# CI validation: python -m app.ci.check_cam_intent_schema_hash
```

### Testing

```python
# Backend (pytest markers from pytest.ini)
@pytest.mark.cam
def test_roughing():
    response = client.post("/api/cam/roughing/gcode", json=payload)
    assert "X-Request-Id" in response.headers

# Run by marker
# pytest tests/ -v -m cam           # CAM toolpath tests
# pytest tests/ -v -m integration   # API endpoint tests
# pytest tests/ -v -m smoke         # Quick validation tests
# pytest tests/ -v -m "cam or helical"  # Multiple markers
```

### Feature Flags

```python
# Environment-based feature flags (default shown)
RMOS_RUNS_V2_ENABLED=true                    # Runs v2 implementation
SAW_LEARNING_HOOK_ENABLED=false              # Feedback loop learning
SAW_METRICS_ROLLUP_HOOK_ENABLED=false        # Metrics rollup persistence
SAW_LAB_APPLY_APPROVED_TUNING_ON_PLAN=false  # Decision Intelligence: apply approved tuning to plans
```

## 🗺️ API Surface

- **Canonical**: `/api/cam/toolpath/*`, `/api/cam/drilling/*`, `/api/rmos/*`, `/api/art/*`
- **Legacy** (tagged `"Legacy"`): Check `/api/governance/stats` before removal
- See [ROUTER_MAP.md](../ROUTER_MAP.md) for 116-router organization

## ⚠️ Common Pitfalls

| Issue                        | Fix                                                 |
| ---------------------------- | --------------------------------------------------- |
| DXF not recognized           | Export R12 (AC1009) with closed LWPolylines         |
| Missing request headers      | Use SDK helpers, not raw fetch                      |
| Post config not found        | Check `app/data/posts/<name>.json` (lowercase)      |
| Schema drift                 | Run `python -m app.ci.check_cam_intent_schema_hash` |
| SQLite `limit` keyword       | Quote as `"limit"` in SQL statements                |
| CSV line endings             | Use `splitlines()` not `split('\n')`                |
| Import boundary violation    | Use artifacts/HTTP, never direct imports            |
| Module-level `os.makedirs()` | Use lazy directory creation (Docker crashes)        |
| Direct `RunArtifact()`       | Use `validate_and_persist()` from store             |
| Frontend raw `fetch()`       | Import from `@/sdk/endpoints`                       |

## 🛠️ Essential CLI Commands

```bash
# CI Gates (run before commit)
python -m app.ci.check_boundary_imports --profile toolbox
python -m app.ci.check_cam_intent_schema_hash
make check-boundaries

# RMOS Management
python -m app.rmos.runs_v2.cli_audit tail -n 50

# Package Scripts (from packages/client/)
npm run dev          # Start dev server
npm run test         # Vitest
npm run lint         # ESLint (max-warnings=0)

# Makefile Targets (from repo root)
make smoke-helix-posts        # Test helical ramping with all post presets
make test-api                 # Run API smoke tests
make check-art-studio-scope   # Art Studio ornament-authority scope gate
make viewer-pack-gate         # Full viewer pack v1 contract gate
```

## 🎸 Module Awareness

| Module         | Scope                                                   | Key Files                                 |
| -------------- | ------------------------------------------------------- | ----------------------------------------- |
| **Module L**   | Adaptive pocketing (spiralizer, trochoids, jerk timing) | `services/api/app/cam/`                   |
| **Module M**   | Machine profiles, energy modeling, feed overrides       | `machines_router.py`, `cam_opt_router.py` |
| **Art Studio** | SVG editor, relief mapper, helical Z-ramping            | `art_studio/`, `/api/art/*` routes        |
| **Saw Lab**    | Reference implementation for governed operations        | `saw_lab/batch_router.py`                 |
| **RMOS**       | Manufacturing orchestration system                      | `rmos/`, `/api/rmos/*` routes             |

## 🚨 Red Flags (Immediate Rejection)

```python
# ❌ RMOS importing CAM execution
from app.cam.toolpath.roughing import generate_roughing_toolpath

# ❌ CAM importing RMOS orchestration
from app.rmos.workflow import approve_workflow

# ❌ Direct RunArtifact construction
artifact = RunArtifact(run_id="xyz", ...)  # Bypasses validation!

# ❌ External repo import
from tap_tone.measurement import perform_analysis
```

```typescript
// ❌ Frontend raw fetch
const response = await fetch("/api/cam/roughing/gcode", {...});
```

## 📚 References

- [FENCE_REGISTRY.json](../FENCE_REGISTRY.json) – Architectural boundaries (8 profiles)
- [ROUTER_MAP.md](../ROUTER_MAP.md) – Router organization (~116 routers)
- [docs/ENDPOINT_TRUTH_MAP.md](../docs/ENDPOINT_TRUTH_MAP.md) – API surface + lane classifications
- [docs/BOUNDARY_RULES.md](../docs/BOUNDARY_RULES.md) – Import boundaries (CI-enforced)
- [packages/client/src/sdk/endpoints/README.md](../packages/client/src/sdk/endpoints/README.md) – SDK patterns

## 📝 Task Guidelines

- **Atomic changes**: One feature/fix per request, scoped to relevant subsystem
- **Present diffs**: Don't rewrite large files without justification
- **Ask before**: Major refactors, schema changes, or API renames (external tooling depends on surfaces)
- **Test verification**: Run the smoke test closest to the subsystem you modified
- **Document features**: Update relevant `docs/` or quickref when adding functionality
