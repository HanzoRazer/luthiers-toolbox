# Luthier's Tool Box – AI Agent Instructions

## Project Overview
**CNC guitar lutherie CAD/CAM platform** - Design guitar components -> export CAM-ready files (DXF R12 + SVG + G-code) -> support 5 CNC platforms.

| Stack | Location | Tech |
|-------|----------|------|
| Backend | `services/api/` | FastAPI (Python 3.11+), 100+ routers organized in Waves 1-20 |
| Frontend | `packages/client/` | Vue 3 + Vite (TypeScript), Pinia stores |
| RMOS | `services/api/app/rmos/` | Rosette Manufacturing Orchestration System |
| Tests | `services/api/tests/`, `services/api/app/tests/` | pytest with markers |

**DO NOT MODIFY**: `__ARCHIVE__/`, `__REFERENCE__/`, `Guitar Design HTML app/` (historical archives)

---

## Architecture Patterns

### Backend Router Organization (`main.py`)
Routers are organized in **Waves 1-20**. Many routers in `routers/` are imported conditionally:
```python
# Core routers (always loaded)
from .routers.geometry_router import router as geometry_router

# Feature-flagged (Wave 14)
if os.getenv("RMOS_RUNS_V2_ENABLED", "true").lower() == "true":
    from .rmos.runs_v2.api_runs import router as rmos_runs_router

# Wave 18-19: Consolidated routers (cam/routers/, compare/routers/)
# Wave 20: Canonical API axes (/api/instruments/, /api/cam/guitar/)
```
**Before adding endpoints**: Check if a router for that domain exists; add to existing router when possible. Recent consolidations:
- **Wave 18**: CAM routers consolidated into `cam/routers/` (63 routes)
- **Wave 19**: Compare routers consolidated into `compare/routers/` (14 routes)
- **Wave 20**: Option C API restructuring with canonical axes

### RMOS Feasibility Engine (`rmos/feasibility_fusion.py`)
```python
# AUTHORITATIVE signature - use exactly these parameter names
def evaluate_feasibility(
    design: Dict[str, Any],  # NOT "spec"
    context: RmosContext,    # NOT "ctx"
) -> FeasibilityReport:      # Pydantic dataclass with is_feasible() method
```
Key endpoints:
- `/api/rmos/feasibility/evaluate` - Risk analysis
- `/api/rmos/ai/search` - AI pattern search
- `/api/rmos/runs` - Immutable run artifacts (v2, date-partitioned)

### Run Artifacts v2 (`rmos/runs_v2/`)
Governance-compliant, immutable storage with **required fields**:
```python
class RunArtifact(BaseModel):
    run_id: str
    status: Literal["OK", "BLOCKED", "ERROR"]
    decision: RunDecision        # risk_level REQUIRED
    hashes: Hashes               # feasibility_sha256 REQUIRED (64 char)
```

### CAM Intent Schema (H7.1)
Use `app.rmos.cam.CamIntentV1` as the canonical request envelope. Mode-specific payloads go in `design` field.

### Multi-Post CAM Export
Posts in `services/api/app/data/posts/*.json` (`grbl.json`, `linuxcnc.json`, `mach4.json`, `masso.json`, `pathpilot.json`).
- `/api/geometry/export_bundle` - ZIP: DXF + SVG + NC
- `/api/geometry/export_bundle_multi` - Multi-platform bundle

---

## Developer Workflows

### Start Services
```bash
# Backend (from repo root)
cd services/api && uvicorn app.main:app --reload --port 8000

# Frontend (Vue on :5173, proxies /api → :8000)
cd packages/client && npm run dev

# Docker full stack
docker compose up --build  # API:8000, Client:8080

# Makefile shortcuts (preferred)
make start-api            # Start FastAPI dev server (port 8000)
make start-client         # Start Vue dev client
make test-api             # Run API pytest tests
make smoke-helix-posts    # Test helical ramping with all post-processor presets
```

### Testing
```bash
# API tests (from services/api/ directory - CRITICAL: pytest must run from here)
cd services/api && pytest tests/ -v

# Run specific marker
pytest -m "cam" -v           # CAM tests only
pytest -m "integration" -v   # Integration tests
pytest -m "router" -v        # Router endpoint tests

# Frontend tests
cd packages/client && npm run test
```

**Test markers**: `unit`, `integration`, `smoke`, `slow`, `router`, `cam`, `geometry`, `adaptive`, `bridge`, `helical`, `export`, `allow_missing_request_id`

### CI Workflows (`.github/workflows/`)
- `api_pytest.yml` - Core API tests
- `rmos_ci.yml` - RMOS integration tests
- `cam_essentials.yml` - CAM toolpath tests
- `comparelab-tests.yml` - CompareMode validation
- `cam_gcode_smoke.yml` - G-code generation smoke tests

---

## Critical Rules

1. **Units**: Always mm internally – convert only at API boundaries (`util/units.py`)
2. **DXF**: R12 format (AC1009) with closed LWPolylines – never newer versions
3. **SDK**: Use typed helpers (`import { cam } from "@/sdk/endpoints"`) – never raw `fetch()`
4. **CAM Intent**: Use `CamIntentV1` envelope (`app.rmos.cam.CamIntentV1`) – don't create alternatives
5. **DO NOT MODIFY**: `__REFERENCE__/` directory (read-only reference data)
6. **Boundary**: Never import `tap_tone.*` or `modes.*` – ToolBox interprets, Analyzer measures
7. **Request IDs**: All API responses MUST include `X-Request-Id` header for correlation

---

## Essential Patterns

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
from app.rmos.cam import CamIntentV1
intent = CamIntentV1(mode="router_3axis", units="mm", design={...})
# CI guard prevents schema drift: python -m app.ci.check_cam_intent_schema_hash
```

### Units - Millimeters Everywhere
- **Internal storage**: Always mm
- **API boundary**: Convert via `app/util/units.py`
- **Conversion factors**: `MM_PER_IN = 25.4` (NIST exact)
```python
from app.util.units import convert_geometry
geometry_inch = convert_geometry(geometry_mm, "mm", "inch")
```

### DXF Export
- **Format**: R12 (AC1009) only - CAM software compatibility
- **Geometry**: Closed LWPolylines required
- **Validation**: Use `app/cam/dxf_preflight.py` before export

### Post-Processor Configuration
Posts in `services/api/app/data/posts/*.json`:
- IDs are **case-sensitive**
- Custom posts: Add to `custom_posts.json`

### Vue Components
- Always `<script setup lang="ts">`
- State in Pinia stores (`packages/client/src/stores/`)
- Follow existing store patterns (see `useRmosRunsStore.ts`)

### Error Handling
- Backend: Return `HTTPException` with descriptive messages
- Never crash on bad config data - use conservative fallbacks
- Request ID correlation: `X-Request-Id` header auto-generated by middleware

---

## API Surface

- **Canonical**: `/api/cam/toolpath/*`, `/api/cam/drilling/*`, `/api/rmos/*`, `/api/art/*`
- **Legacy**: Tagged `"Legacy"` – check `/api/governance/stats` before removal
- **Governance**: `/api/governance/stats` tracks legacy route hit counts
- See [ROUTER_MAP.md](../ROUTER_MAP.md) for router organization

---

## CI Gates (must pass before merge)

| Gate | Command | What it checks |
|------|---------|----------------|
| Endpoint Truth | `python -m app.ci.endpoint_truth_gate check` | Routes match ENDPOINT_TRUTH_MAP.md |
| CAM Schema | `python -m app.ci.check_cam_intent_schema_hash` | CamIntentV1 hasn't drifted |
| AI Sandbox | `python -m app.ci.ban_experimental_ai_core_imports` | No deprecated ai_core imports |
| Legacy Usage | `python -m app.ci.legacy_usage_gate` | Frontend not calling legacy APIs |

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `services/api/app/main.py` | FastAPI app, all router registrations |
| `services/api/app/rmos/feasibility_fusion.py` | Feasibility scoring engine |
| `services/api/app/rmos/runs_v2/schemas.py` | Governance-compliant artifact schemas |
| `services/api/app/rmos/context.py` | RmosContext - unified manufacturing context |
| `services/api/app/cam/adaptive_core_l*.py` | Adaptive pocketing algorithms |
| `services/api/app/cam/polygon_offset_n17.py` | Polygon offset with arc linkers |
| `services/api/app/util/units.py` | MM↔Inch conversion (boundary only) |
| `services/api/app/data/` | JSON configs (posts, machines, tools) |
| `services/api/pytest.ini` | Test configuration and markers |
| `packages/client/src/stores/` | Pinia state management |
| `docker-compose.yml` | Full-stack deployment config |

---

## Common Pitfalls

| Issue | Solution |
|-------|----------|
| Router not working | Check if imported in `main.py` - conditionals may skip it |
| RMOS import fails | Use `design` not `spec`; import from `rmos.context` |
| DXF rejected by CAM software | Must be R12 format with closed polylines |
| Units mismatch | All internal data in mm; convert only at API boundary |
| Post not found | IDs are case-sensitive; check `data/posts/*.json` |
| Test can't find app | Run pytest from `services/api/` directory |
| Missing X-Request-Id | Add `@pytest.mark.allow_missing_request_id` marker |
| Schema drift | Run `python -m app.ci.check_cam_intent_schema_hash` |
| Legacy API in frontend | Check ENDPOINT_TRUTH_MAP.md for canonical path |

---

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `RMOS_RUNS_V2_ENABLED` | `true` | Use v2 governance-compliant runs |
| `RMOS_RUNS_DIR` | `data/runs/rmos` | Run artifact storage path |
| `SERVER_PORT` | `8000` | API server port |
| `CLIENT_PORT` | `8080` | Frontend dev server port |
| `CORS_ORIGINS` | `http://localhost:8080` | Allowed frontend origins |

---

## Adding New Features

1. **New endpoint**: Add to existing router in `routers/` matching domain, or create new router following Wave pattern
2. **New RMOS feature**: Use `RmosContext` from `rmos/context.py`; emit `RunArtifact` for audit trail
3. **New CAM operation**: Add to `cam/` module; include unit tests with `@pytest.mark.cam`
4. **New Pinia store**: Follow `useRmosRunsStore.ts` pattern; keep API calls in store actions
5. **New Vue component**: Use `<script setup lang="ts">`; emit typed events

---

## References

- [ROUTER_MAP.md](../ROUTER_MAP.md) – Router organization (Waves 0-22)
- [docs/ENDPOINT_TRUTH_MAP.md](../docs/ENDPOINT_TRUTH_MAP.md) – API surface + legacy mapping
- [docs/BOUNDARY_RULES.md](../docs/BOUNDARY_RULES.md) – Import boundaries
- [packages/client/src/sdk/endpoints/README.md](../packages/client/src/sdk/endpoints/README.md) – SDK patterns
