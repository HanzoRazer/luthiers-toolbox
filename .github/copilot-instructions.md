# Luthier's Tool Box - AI Agent Instructions

## Project Overview
**CNC guitar lutherie CAD/CAM platform** - Design guitar components → export CAM-ready files (DXF R12 + SVG + G-code) → support 7 CNC platforms.

| Stack | Location | Tech |
|-------|----------|------|
| Backend | `services/api/` | FastAPI (Python 3.11+), 70+ routers in 14 waves |
| Frontend | `packages/client/` | Vue 3 + Vite (TypeScript), Pinia stores |
| RMOS | `services/api/app/rmos/` | Rosette Manufacturing OS subsystem |
| Docs | `projects/rmos/`, `docs/` | Architecture guides, specs |

**DO NOT MODIFY**: `Luthiers Tool Box/`, `Guitar Design HTML app/` (legacy archives)

---

## Architecture Quick Reference

### Backend Router Pattern (`main.py`)
Routers are organized in **waves** (1-14). Check `main.py` imports - many routers in `routers/` are stubs:
```python
# Wave 1: Core routers (always loaded)
from .routers.geometry_router import router as geometry_router

# Wave 14: Optional with feature flags
if os.getenv("RMOS_RUNS_V2_ENABLED", "true").lower() == "true":
    from .rmos.runs_v2.api_runs import router as rmos_runs_router
```

### RMOS Feasibility Engine
```python
# AUTHORITATIVE signature (rmos/feasibility_fusion.py)
def evaluate_feasibility(
    design: Dict[str, Any],  # NOT "spec"
    context: RmosContext,    # NOT "ctx"  
) -> FeasibilityReport:      # Pydantic dataclass
```
- `/api/rmos/feasibility/evaluate` - Risk analysis
- `/api/rmos/ai/search` - AI pattern search
- `/api/rmos/runs` - Immutable run artifacts (v2, date-partitioned)

### Run Artifacts (`rmos/runs_v2/`)
Governance-compliant, write-once storage:
```python
class RunArtifact(BaseModel):
    run_id: str
    status: Literal["OK", "BLOCKED", "ERROR"]
    decision: RunDecision        # risk_level REQUIRED
    hashes: Hashes               # feasibility_sha256 REQUIRED
```

### Multi-Post CAM Export
Posts in `services/api/app/data/posts/*.json`. Key endpoints:
- `/api/geometry/export_bundle` - ZIP: DXF + SVG + NC
- `/api/geometry/export_bundle_multi` - Multi-platform bundle

---

## Developer Workflows

### Start Services
```bash
# Backend
cd services/api && uvicorn app.main:app --reload --port 8000

# Frontend  
cd packages/client && npm run dev  # http://localhost:5173

# Docker (full stack)
docker compose up --build  # API:8000, Client:8080
```

### Testing
```bash
# Python tests (primary location: services/api/app/tests/)
cd services/api && pytest app/tests/ -v

# RMOS CI integration (starts server, runs tests)
python scripts/rmos_ci_test.py

# Client tests
cd packages/client && npm run test
```

CI workflows in `.github/workflows/`: `rmos_ci.yml`, `api_pytest.yml`, `cam_essentials.yml`, `comparelab-tests.yml`

---

## Critical Conventions

### Units
- **Internal**: Always mm
- **API boundary**: Convert via `util/units.py`

### DXF Export
- **Format**: R12 (AC1009) only for CAM compatibility
- **Geometry**: Closed LWPolylines required

### Vue Components
- Always `<script setup lang="ts">`
- State in Pinia stores (`packages/client/src/stores/`)

### Error Handling
- Backend: `HTTPException` with conservative fallbacks
- Never crash on bad config data

---

## Key Files

| File | Purpose |
|------|---------|
| `services/api/app/main.py` | FastAPI app, 70+ router registrations |
| `services/api/app/rmos/feasibility_fusion.py` | RMOS feasibility core |
| `services/api/app/rmos/runs_v2/schemas.py` | RunArtifact governance schemas |
| `services/api/app/cam/adaptive_core_l*.py` | Adaptive pocketing (L-series) |
| `services/api/app/data/` | Posts, machines, tools JSON configs |
| `DEVELOPER_HANDOFF_DEC19_2025.md` | Infrastructure audit & status |
| `projects/rmos/README.md` | RMOS architecture docs |

---

## Common Pitfalls

| Issue | Solution |
|-------|----------|
| Router not working | Check if imported in `main.py` - many are stubs |
| RMOS import fails | Use `design` not `spec` param; check `rmos/context.py` |
| DXF rejected by CAM | Must be R12 format with closed polylines |
| Units mismatch | All internal data in mm; convert at boundary |
| Post not found | IDs are case-sensitive; check `data/posts/` |

---

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `RMOS_RUNS_V2_ENABLED` | `true` | Use v2 governance-compliant runs |
| `RMOS_RUNS_DIR` | `data/runs/rmos` | Run artifact storage |
| `CORS_ORIGINS` | `http://localhost:8080` | Allowed frontend origins |
