# Luthier's Tool Box – AI Agent Instructions

> CNC guitar lutherie platform: Vue 3 + FastAPI. **All geometry in mm. DXF R12 (AC1009).**

## Quick Start

```bash
# Full stack dev (2 terminals)
make start-api     # FastAPI on :8000
make start-client  # Vue on :5173 (proxies /api → :8000)

# Docker
docker compose up --build

# Essential tests & checks
cd services/api && pytest tests/ -v -m cam    # CAM tests
cd packages/client && npm run test            # Frontend tests
make check-boundaries                         # MUST pass before commit
```

## Critical Rules

1. **Units**: Always mm internally – convert only at API boundaries (`app/util/units.py`)
2. **DXF**: R12 format (AC1009) with closed LWPolylines – never newer versions
3. **SDK**: Use typed helpers (`import { cam } from "@/sdk/endpoints"`) – never raw `fetch()`
4. **CAM Intent**: Use `CamIntentV1` envelope (`app.rmos.cam.CamIntentV1`) – don't create alternatives
5. **Boundaries**: Check `FENCE_REGISTRY.json` before importing across domains – CI-enforced
6. **Request IDs**: All API responses MUST include `X-Request-Id` header
7. **DO NOT MODIFY**: `__REFERENCE__/` directory (read-only reference data)

## Architecture

```
services/api/app/           # FastAPI backend (~116 routers)
├── cam/                    # CAM algorithms (pocketing, helical, biarc)
├── rmos/                   # RMOS orchestration, workflow, CAM intent
│   └── cam/schemas_intent.py  # CamIntentV1 canonical envelope
├── saw_lab/                # Reference OPERATION lane implementation
├── data/posts/*.json       # Post-processor configs (grbl, mach4, etc.)
└── main.py                 # Router registration

packages/client/src/        # Vue 3 + TypeScript frontend
├── sdk/endpoints/          # Typed API helpers (H8.3 pattern)
├── components/             # Reusable UI by domain
└── views/                  # Route-level pages
```

## Domain Boundaries (CI-Enforced)

**Never import directly across domains.** Use these patterns:

```python
# ❌ WRONG: Direct cross-domain import
from app.cam.toolpath.roughing import generate_roughing_toolpath

# ✅ CORRECT: HTTP API contract
response = requests.post("/api/cam/toolpath/roughing/gcode", json=intent.dict())
```

| Integration Pattern | When to Use |
|---------------------|-------------|
| **HTTP API** | Domain A invokes Domain B (RMOS → CAM) |
| **Artifact Contract** | Domain A reads Domain B's JSON/CSV output |
| **SDK Adapter** | Frontend calls backend |

## Operation Lanes (Machine-Executing Endpoints)

| Lane | Description | Example |
|------|-------------|---------|
| **OPERATION** | Artifacts, feasibility gate, audit trail | `/api/saw/batch/*` |
| **UTILITY** | Stateless/preview, no artifacts | `/api/cam/roughing/gcode` |

Reference implementation: `services/api/app/saw_lab/batch_router.py` (SPEC → PLAN → DECISION → EXECUTE → EXPORT → FEEDBACK)

## Code Patterns

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

### Frontend: SDK Usage (never raw fetch)
```typescript
import { cam } from "@/sdk/endpoints";
import { ApiError } from "@/sdk/core/errors";

const { gcode, summary, requestId } = await cam.roughingGcode(payload);
```

### Testing
```python
# pytest markers: unit, integration, smoke, cam
@pytest.mark.cam
def test_roughing():
    response = client.post("/api/cam/roughing/gcode", json=payload)
    assert "X-Request-Id" in response.headers
```

## Common Pitfalls

| Issue | Fix |
|-------|-----|
| DXF not recognized | Export R12 (AC1009) with closed LWPolylines |
| Post config not found | Check `app/data/posts/<name>.json` (lowercase) |
| Import boundary violation | Use artifacts/HTTP, check `FENCE_REGISTRY.json` |
| SQLite `limit` keyword | Quote as `"limit"` in SQL |
| Module-level `os.makedirs()` | Use lazy directory creation (Docker crashes) |
| Direct `RunArtifact()` construction | Use `validate_and_persist()` from store |

## CI Commands

```bash
make check-boundaries                                        # All fence checks (7 profiles)
cd services/api && python -m app.ci.check_cam_intent_schema_hash  # Schema freeze guard
make check-art-studio-scope                                  # Art Studio boundary gate
```

## Known CI Quirks (A_N.7)

Some CI failures are environment-specific and pass locally:

| CI Failure | Notes |
|------------|-------|
| Bridge Router 500s | CI-only – passes locally, investigating environment |
| DXF Security LogRecord | Logging config conflict in test isolation |

**Don't debug CI-only failures locally** – check `docs/BUILD_READINESS_EVALUATION.md` for current status.

## Art Studio Scope Rules

Art Studio is **ornament-authority only** (rosettes, inlays, mosaics). It must NOT:
- Generate machine outputs (G-code, DXF, toolpaths) → use CAM domain
- Create/persist run artifacts → use RMOS runs_v2 store
- Call Saw Lab / CAM execution APIs → use HTTP contracts

**Moved to CAM:**
- Relief DXF export: `POST /api/cam/toolpath/relief/export-dxf`
- VCarve G-code: `POST /api/cam/toolpath/vcarve/gcode`

**Inline suppression:** `# SCOPE_ALLOW: TAG` for legitimate false positives

## Key References

- `FENCE_REGISTRY.json` – Boundary definitions (8 profiles)
- `ROUTER_MAP.md` – 116 routers by deployment wave
- `docs/ENDPOINT_TRUTH_MAP.md` – API surface + lane classifications
- `docs/BUILD_READINESS_EVALUATION.md` – Current CI status & known issues
- `packages/client/src/sdk/endpoints/README.md` – SDK patterns
- `CBSP21.md` – Completeness protocol for large changes
