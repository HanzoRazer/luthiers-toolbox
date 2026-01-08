# Luthier's Tool Box – AI Agent Instructions

> CNC guitar lutherie platform: Vue 3 + FastAPI. **All geometry in mm. DXF R12 (AC1009).**
> **Last Updated:** 2026-01-08

## ⚡ Quick Start

```bash
# Backend (FastAPI on :8000)
cd services/api && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000

# Frontend (Vue on :5173, proxies /api → :8000)
cd packages/client && npm run dev

# Docker (full stack)
docker compose up --build              # Development
docker compose -f docker-compose.production.yml up -d  # Production

# Key Tests
cd services/api && pytest tests/ -v -m cam            # CAM tests only (markers: unit, integration, smoke, cam)
cd packages/client && npm run test                     # Frontend (Vitest)
cd packages/client && npm run test:request-id          # Request-ID validation
make smoke-helix-posts                                 # Integration smoke test
make check-boundaries                                  # All architectural fence checks

# Start Both (for full stack dev)
make start-api    # Terminal 1
make start-client # Terminal 2
```

## 🔑 Critical Rules

1. **Units**: Always mm internally – convert only at API boundaries (`util/units.py`)
2. **DXF**: R12 format (AC1009) with closed LWPolylines – never newer versions
3. **SDK**: Use typed helpers (`import { cam } from "@/sdk/endpoints"`) – never raw `fetch()`
4. **CAM Intent**: Use `CamIntentV1` envelope (`app.rmos.cam.CamIntentV1`) – don't create alternatives
5. **DO NOT MODIFY**: `__REFERENCE__/` directory (read-only reference data)
6. **Request IDs**: All API responses MUST include `X-Request-Id` header for correlation
7. **Machine Profiles**: Use valid IDs from `machine_profiles.json` (`GRBL_3018_Default`, `Mach4_Router_4x8`, `LinuxCNC_KneeMill`)
8. **Error Handling**: Use `ApiError` class with `.is()`, `.isClientError()`, `.isServerError()` – never raw status checks
9. **Python Modules**: Run as modules (`python -m app.ci.check_boundary_imports`) not scripts
10. **Docker Ports**: API=8000, Client=8080, Proxy=8088 (hardcoded in docker-compose.yml)
11. **Architectural Fences**: Check [FENCE_REGISTRY.json](../FENCE_REGISTRY.json) before importing across domains (RMOS↔CAM, AI sandbox, etc.) – CI-enforced

## 📁 Key Paths

| Area | Path |
|------|------|
| API Entry | `services/api/app/main.py` – ~116 routers |
| CAM Algorithms | `services/api/app/cam/` – pocketing, helical, biarc |
| RMOS Orchestration | `services/api/app/rmos/` – workflow, CAM intent |
| Saw Lab (Reference) | `services/api/app/saw_lab/` – governed operation pattern |
| CAM Intent Schema | `services/api/app/rmos/cam/schemas_intent.py` |
| Frontend SDK | `packages/client/src/sdk/endpoints/` – typed helpers |
| Post Configs | `services/api/app/data/posts/*.json` – grbl, mach4, etc. |
| CI Workflows | `.github/workflows/` – 38 workflow files |

## 🏗️ Architecture: Operation Lanes

Machine-executing endpoints follow **Operation Lane Governance**:

| Lane | Description | Example |
|------|-------------|---------|
| **OPERATION** | Full governance: artifacts, feasibility gate, audit trail | `/api/saw/batch/*` |
| **UTILITY** | Stateless/preview, no artifacts | `/api/cam/roughing/gcode` |

**Reference Implementation**: CNC Saw Lab (`services/api/app/saw_lab/batch_router.py`)
- Stage sequence: SPEC → PLAN → DECISION → EXECUTE → EXPORT → FEEDBACK
- Artifacts persisted per stage for audit/replay

## 🔗 Cross-Boundary Integration Patterns

**Never import directly across domains.** Use these three patterns:

### Pattern 1: Artifact Contract
When Domain A needs Domain B's output **without code dependency**:
```python
# Producer (e.g., Analyzer)
def perform_measurement():
    result = {"frequency_hz": 440, "mode": "fundamental"}
    write_json_artifact("measurement_001.json", result, sha256=True)
    log_to_manifest("measurement_001.json")

# Consumer (e.g., ToolBox)
def interpret_measurement():
    artifacts = list_artifacts_from_manifest()
    data = load_json(artifacts[0])
    validate_schema(data)  # Check JSON schema
    return generate_advisory(data)
```

### Pattern 2: HTTP API Contract
When Domain A needs to **invoke** Domain B's behavior:
```python
# Client (RMOS)
from app.rmos.cam import CamIntentV1

intent = CamIntentV1(mode="roughing", design={"entities": [...]})
response = requests.post("/api/cam/toolpath/roughing/gcode", json=intent.dict())
gcode = response.json()["gcode"]
persist_result(gcode)

# Server (CAM)
@router.post("/toolpath/roughing/gcode")
def generate_roughing(intent: CamIntentV1):
    # Stateless: accept intent, compute, return result
    toolpaths = generate_toolpaths(intent.design)
    return {"gcode": post_process(toolpaths)}
```

### Pattern 3: SDK Adapter
When **frontend** needs type-safe API access:
```typescript
// ✅ CORRECT: Typed SDK helper
import { cam } from "@/sdk/endpoints";
const { gcode, summary, requestId } = await cam.roughingGcode(payload);

// ❌ WRONG: Raw fetch bypasses type safety and header parsing
const response = await fetch("/api/cam/roughing/gcode", {
  method: "POST",
  body: JSON.stringify(payload),
});
```

**Key Principle**: Artifact schemas, HTTP APIs, or SDK adapters – never direct imports.

## 🧪 Essential Patterns

### Backend: New Router
```python
# services/api/app/routers/my_feature_router.py
from fastapi import APIRouter
router = APIRouter()

@router.post("/do-thing")
def do_thing(req: MyRequest) -> MyResponse: ...

# Register in main.py with try/except for optional routers
app.include_router(my_feature_router, prefix="/api/my-feature", tags=["MyFeature"])
```

### Frontend: SDK Usage (H8.3)
```typescript
import { cam } from "@/sdk/endpoints";
import { ApiError, formatApiErrorForUi } from "@/sdk/core/errors";

try {
  const { gcode, summary, requestId } = await cam.roughingGcode(payload);
  // SDK handles headers, errors, request-id correlation
} catch (err) {
  if (err instanceof ApiError) {
    if (err.is(422)) {
      // Validation error - show to user
      errorMsg.value = formatApiErrorForUi(err);
    } else if (err.isServerError()) {
      // 5xx error - show retry option
      showRetryDialog(err.requestId);
    }
  }
}
```

### CAM Intent (H7.1)
```python
from app.rmos.cam import CamIntentV1, normalize_cam_intent_v1
intent = CamIntentV1(mode="roughing", units="mm", design={...})
normalized, issues = normalize_cam_intent_v1(intent)

# CI validation: python -m app.ci.check_cam_intent_schema_hash
```

### Testing Pattern
```python
# Backend (pytest with markers)
import pytest

@pytest.mark.cam
@pytest.mark.smoke
def test_roughing_gcode_generation():
    response = client.post("/api/cam/roughing/gcode", json=payload)
    assert response.status_code == 200
    assert "X-Request-Id" in response.headers  # Required for all endpoints
```

```typescript
// Frontend (Vitest)
import { describe, it, expect, vi } from "vitest";
import { cam } from "@/sdk/endpoints";

describe("roughingGcode", () => {
  it("returns gcode + requestId", async () => {
    const result = await cam.roughingGcode(mockPayload);
    expect(result.requestId).toBeDefined();
    expect(result.gcode).toContain("G21"); // mm mode
  });
});
```

## 🗺️ API Surface

- **Canonical**: `/api/cam/toolpath/*`, `/api/cam/drilling/*`, `/api/rmos/*`, `/api/art/*`
- **Legacy**: Tagged `"Legacy"` – check `/api/governance/stats` before removal
- See [ROUTER_MAP.md](../ROUTER_MAP.md) for 116-router organization

## ⚠️ Common Pitfalls

| Issue | Fix |
|-------|-----|
| DXF not recognized | Export R12 (AC1009) with closed LWPolylines |
| Missing request headers | Use SDK helpers, not raw fetch |
| Post config not found | Check `app/data/posts/<name>.json` (lowercase) |
| Schema drift | Run `python -m app.ci.check_cam_intent_schema_hash` |
| SQLite `limit` keyword | Quote as `"limit"` in SQL statements |
| CSV line ending issues | Use `splitlines()` not `split('\n')` |
| Import boundary violation | Check [FENCE_REGISTRY.json](../FENCE_REGISTRY.json) – use artifacts/HTTP, never direct imports |
| Module-level `os.makedirs()` | Use lazy directory creation (Docker container crashes) |
| RMOS importing CAM toolpaths | Use CAM Intent envelope + HTTP API |
| CAM importing RMOS workflow | Accept intent, return data – no orchestration |
| AI sandbox creating artifacts | Return advisory data only – humans decide |
| Direct `RunArtifact()` construction | Use `validate_and_persist()` from `app.rmos.runs_v2.store` |
| Frontend raw `fetch()` calls | Import from `@/sdk/endpoints` – provides types, headers, request-id |

## 🛠️ Essential CLI Commands

```bash
# CI Gates (run before commit)
python -m app.ci.check_boundary_imports --profile toolbox          # External boundaries
python -m app.ci.check_domain_boundaries --profile rmos_cam        # Internal boundaries
python -m app.ci.check_cam_intent_schema_hash                      # Schema validation
python -m app.ci.check_endpoint_governance                         # Endpoint governance
python -m app.ci.legacy_usage_gate --roots "../../packages/client/src" --budget 10  # Legacy usage
python -m app.ci.check_operation_lane_compliance                   # Operation lane
python ci/ai_sandbox/check_ai_import_boundaries.py                 # AI sandbox

# Run all boundary checks
make check-boundaries

# RMOS Management (from services/api/)
python -m app.rmos.runs_v2.cli_audit tail -n 50        # View run logs
python -m app.rmos.runs_v2.cli_audit count --mode soft  # Count runs
python -m app.rmos.runs_v2.cli_delete run_abc123 --reason "cleanup" --dry-run
python -m app.rmos.runs_v2.cli_migrate status           # Check migration status

# Package Scripts (from packages/client/)
npm run dev                    # Start dev server (:5173)
npm run build                  # Production build
npm run test                   # Run all Vitest tests
npm run test:watch             # Watch mode
npm run test:request-id        # Request-ID specific tests
npm run lint                   # ESLint check (max-warnings=0)
npm run type-check             # Vue TypeScript check
```

## 🔒 CBSP21 Completeness Protocol

When making large changes, create `.cbsp21/patch_input.json` manifest declaring:
- `files_expected_to_change` – explicit file list
- `diff_articulation.what_changed` – 5-15 bullet summary
- `behavior_change` – `none|compatible|breaking`
- `diff_range` – base/head for changed files verification

CI enforces ≥95% coverage verification for governed areas. See [CBSP21.md](../CBSP21.md).

**Critical**: Never declare patches "redundant" without proving equivalence via `git diff` or validation commands.

**Example manifest**:
```json
{
  "schema": "cbsp21_patch_input_v1",
  "patch_id": "FIX_409",
  "title": "Fix helical ramping arc mode",
  "intent": "Ensure post-processors use correct arc mode",
  "change_type": "code",
  "behavior_change": "compatible",
  "risk_level": "medium",
  "scope": {
    "paths_in_scope": ["services/api/app/cam/"],
    "files_expected_to_change": ["services/api/app/cam/helical.py"]
  },
  "diff_articulation": {
    "what_changed": [
      "Fixed IJ vs R arc mode selection",
      "Added post-processor validation"
    ],
    "why_not_redundant": "Previous code defaulted to IJ for all posts"
  },
  "verification": {
    "commands_run": ["pytest tests/cam/test_helical.py -v"]
  }
}
```

## � Red Flags for AI Agents

**Immediate rejection** – these patterns violate architectural fences:

```python
# ❌ RMOS importing CAM execution
from app.cam.toolpath.roughing import generate_roughing_toolpath

# ❌ CAM importing RMOS orchestration
from app.rmos.workflow import approve_workflow

# ❌ AI sandbox creating artifacts
from app.rmos.runs.store import create_run_artifact

# ❌ Direct RunArtifact construction
from app.rmos.runs_v2.schemas import RunArtifact
artifact = RunArtifact(run_id="xyz", ...)  # Bypasses validation!

# ❌ External repo import
from tap_tone.measurement import perform_analysis

# ❌ Frontend raw fetch
const response = await fetch("/api/cam/roughing/gcode", {...});
```

**Before importing across domains:**
1. Check `FENCE_REGISTRY.json` for allowed imports
2. If forbidden, use artifact contract, HTTP API, or SDK adapter
3. Run `make check-boundaries` before commit

## �📚 References

- [FENCE_REGISTRY.json](../FENCE_REGISTRY.json) – Architectural boundary registry (8 fence profiles)
- [docs/governance/FENCE_ARCHITECTURE.md](../docs/governance/FENCE_ARCHITECTURE.md) – Complete fence documentation
- [ROUTER_MAP.md](../ROUTER_MAP.md) – Router organization (~116 routers by wave)
- [docs/ENDPOINT_TRUTH_MAP.md](../docs/ENDPOINT_TRUTH_MAP.md) – API surface + lane classifications
- [docs/BOUNDARY_RULES.md](../docs/BOUNDARY_RULES.md) – Import boundaries (CI-enforced)
- [docs/AI_CODE_BUNDLE_LOCK_POINTS_v1.md](../docs/AI_CODE_BUNDLE_LOCK_POINTS_v1.md) – Authoritative router prefixes
- [packages/client/src/sdk/endpoints/README.md](../packages/client/src/sdk/endpoints/README.md) – SDK patterns
- [CBSP21.md](../CBSP21.md) – Completeness protocol for large changes
