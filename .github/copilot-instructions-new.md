# Luthier's Tool Box – AI Agent Quick Guide

> CNC guitar lutherie platform: Vue 3 frontend → FastAPI backend → DXF/G-code export

## Essential Locations

| Area | Path | Notes |
|------|------|-------|
| Backend | `services/api/app/` | FastAPI routers, CAM engines, RMOS |
| Frontend | `packages/client/src/` | Vue 3 + TypeScript components |
| Tests | `scripts/*.ps1` | PowerShell smoke tests (primary) |
| Docs | `docs/`, `ROUTER_MAP.md` | Architecture, patches, API truth map |
| **DO NOT MODIFY** | `__REFERENCE__/`, `Luthiers Tool Box/` | Historical artifacts |

## Dev Commands

```bash
# Backend
cd services/api && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd packages/client && npm install && npm run dev  # :5173 → proxies /api to :8000

# Tests (PowerShell - server must be running)
./test_adaptive_l1.ps1  # CAM pocketing
./scripts/Test-RMOS-Sandbox.ps1  # RMOS subsystem
pytest tests/ -v  # Python unit tests
```

## Key Patterns

### 1. Router Registration (`main.py`)
```python
# Always use try/except for optional routers
try:
    from .routers.feature_router import router as feature_router
    app.include_router(feature_router, prefix="/api/feature", tags=["Feature"])
except ImportError as e:
    print(f"Warning: Feature router not available: {e}")
```

### 2. SDK Endpoint Helpers (H8.3) – Use instead of raw fetch()
```typescript
// ✅ DO: packages/client/src/sdk/endpoints/
import { cam } from "@/sdk/endpoints";
const { gcode, summary, requestId } = await cam.roughingGcode(payload);

// ❌ DON'T: Raw fetch() in components
```

### 3. Units – Always mm internally
- Server: `services/api/app/util/units.py` – `scale_geom_units(geom, "inch")`
- Client: `scaleGeomClient()` in GeometryOverlay.vue
- G-code: `G21` (mm) or `G20` (inch) auto-injected by post headers

### 4. DXF Export – Always R12 format for CAM compatibility
- Use `ezdxf` for R12 (AC1009) exports
- All paths must be closed LWPolylines for CNC

### 5. CAM Intent Schema (H7.1)
- Canonical envelope: `app.rmos.cam.CamIntentV1`
- Never create alternative envelopes – embed `design` shapes under this

## API Endpoint Governance

- **Legacy routes**: Tagged with `"Legacy"` for deprecation tracking
- **Metrics**: `GET /api/governance/stats` shows legacy usage counts
- **Migration**: Use canonical routes, check `docs/ENDPOINT_TRUTH_MAP.md`

## Testing Conventions

- PowerShell scripts (`.ps1`) are primary test format
- Scripts call `http://localhost:8000` directly (server must run)
- Validate G-code patterns: `G21`, `G20`, `(POST=<id>` metadata
- CI workflows in `.github/workflows/*.yml`

## Critical Files

| Purpose | File |
|---------|------|
| Router truth | [ROUTER_MAP.md](../ROUTER_MAP.md) – 116 routers, 22 waves |
| API surface | [docs/ENDPOINT_TRUTH_MAP.md](../docs/ENDPOINT_TRUTH_MAP.md) |
| CAM pocketing | `services/api/app/cam/adaptive_core_l*.py` (L.1-L.3) |
| Post configs | `services/api/app/data/posts/*.json` (GRBL, Mach4, etc.) |
| SDK helpers | `packages/client/src/sdk/endpoints/` |

## Quick Troubleshooting

| Issue | Solution |
|-------|----------|
| DXF not importing to Fusion 360 | Ensure R12 format, closed LWPolylines |
| Units mismatch | Convert at API boundary only, store in mm |
| Post not found | Check `services/api/app/data/posts/<name>.json` exists |
| Import errors | Run `python scripts/audit_phantom_imports.py` |

---

**For comprehensive documentation**, see:
- [ROUTER_MAP.md](../ROUTER_MAP.md) – Complete router organization
- [docs/ENDPOINT_TRUTH_MAP.md](../docs/ENDPOINT_TRUTH_MAP.md) – Full API surface
- [docs/H8.3_SDK_MIGRATION_TRACKING.md](../docs/H8.3_SDK_MIGRATION_TRACKING.md) – SDK migration status
- [docs/ARCHIVE/2025-12/misc/ADAPTIVE_POCKETING_MODULE_L.md](../docs/ARCHIVE/2025-12/misc/ADAPTIVE_POCKETING_MODULE_L.md) – CAM algorithms
