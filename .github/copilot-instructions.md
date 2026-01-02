# Luthier's Tool Box – AI Agent Instructions

> CNC guitar lutherie platform: Vue 3 + FastAPI. **All geometry in mm. DXF R12 (AC1009).**

## ⚡ Quick Start

```bash
# Backend (FastAPI on :8000)
cd services/api && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000

# Frontend (Vue on :5173, proxies /api → :8000)
cd packages/client && npm run dev

# Key Tests
cd services/api && pytest tests/ -v                    # Backend unit tests
cd packages/client && npm run test                     # Frontend (Vitest)
cd services/api && python -m app.ci.check_boundary_imports --profile toolbox  # Boundary guard (CI-enforced)
make smoke-helix-posts                                 # Integration smoke test

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
6. **Boundary**: Never import `tap_tone.*` or `modes.*` – ToolBox interprets, Analyzer measures
7. **Request IDs**: All API responses MUST include `X-Request-Id` header for correlation

## 📁 Key Paths

| Area | Path |
|------|------|
| API Entry | `services/api/app/main.py` – ~116 routers |
| CAM Algorithms | `services/api/app/cam/` – pocketing, helical, biarc |
| RMOS Orchestration | `services/api/app/rmos/` – workflow, CAM intent |
| CAM Intent Schema | `services/api/app/rmos/cam/schemas_intent.py` |
| Frontend SDK | `packages/client/src/sdk/endpoints/` – typed helpers |
| Post Configs | `services/api/app/data/posts/*.json` – grbl, mach4, etc. |
| CI Guards | `services/api/app/ci/` – boundary checks, schema drift |

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
import { ApiError } from "@/sdk/core/errors";

const { gcode, summary, requestId } = await cam.roughingGcode(payload);
// SDK handles headers, errors, request-id correlation
```

### CAM Intent (H7.1)
```python
from app.rmos.cam import CamIntentV1, normalize_cam_intent_v1
intent = CamIntentV1(mode="roughing", units="mm", design={...})
normalized, issues = normalize_cam_intent_v1(intent)
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

## 📚 References

- [ROUTER_MAP.md](../ROUTER_MAP.md) – Router organization
- [docs/ENDPOINT_TRUTH_MAP.md](../docs/ENDPOINT_TRUTH_MAP.md) – API surface
- [docs/BOUNDARY_RULES.md](../docs/BOUNDARY_RULES.md) – Import boundaries
- [packages/client/src/sdk/endpoints/README.md](../packages/client/src/sdk/endpoints/README.md) – SDK patterns
