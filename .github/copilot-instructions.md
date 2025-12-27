# Luthier's Tool Box – AI Agent Instructions

**Last Updated**: 2025-12-27  
**Build**: A_N.1 (Priority 1 Complete)

## Project Overview
This is a **CNC guitar lutherie CAD/CAM toolbox** combining:
- **Vue 3 + Vite** frontend (TypeScript) in `packages/client/` for guitar design visualization
- **FastAPI** backend (Python 3.11+) in `services/api/` for DXF/SVG export, geometry processing, and multi-post CNC workflows
- **Multi-post processor support**: GRBL, Mach4, LinuxCNC, PathPilot, MASSO, Haas, Marlin with JSON configuration files
- **Unit conversion**: Bidirectional mm ↔ inch geometry scaling (client + server)
- **RMOS (Rosette Manufacturing OS)**: Complete factory subsystem for rosette inlay design, CAM, and production tracking
- **Blueprint Import** pipeline in `services/blueprint-import/` for image-based guitar template extraction
- **SDK Architecture (H8.3)**: Typed endpoint helpers replacing raw fetch() calls (migration in progress)

**Core Mission**: Enable luthiers to design guitar components, export CAM-ready files (DXF R12 + SVG + G-code), and support multiple CNC platforms through a unified web interface.

**Repository Structure**: 
- **Active Development**: `services/api/`, `packages/client/`, `packages/shared/`, `projects/rmos/`
- **Reference Only (DO NOT MODIFY)**: `Luthiers Tool Box/`, `Guitar Design HTML app/`, `Lutherier Project/`, `Smart Guitar Build/`, `__REFERENCE__/`
- **Testing**: PowerShell-first smoke tests in `scripts/*.ps1` with bash mirrors for CI
- **Documentation**: Comprehensive guides in `docs/` with patch notes, quickrefs, and architecture diagrams
- **CI/CD**: 24 GitHub Actions workflows covering API, client, RMOS, CAM, and integration tests

---

## Architecture & Key Patterns

### 1. **Router Organization & Wave-Based Development**
- **116 working routers** organized across 22 deployment waves (see [ROUTER_MAP.md](../ROUTER_MAP.md))
- **Legacy vs Canonical lanes**: Legacy routes remain mounted for backwards compatibility with `"Legacy"` tag
  - CAM consolidated in Wave 18: `/api/cam/toolpath/*` (canonical), `/api/cam/vcarve` (legacy)
  - Compare consolidated in Wave 19: `/api/compare/*` (canonical)
  - Governance middleware tracks legacy usage via `/api/governance/stats`
- **Router registration pattern** in `services/api/app/main.py`:
  ```python
  # Core routers (always available)
  from .routers.adaptive_router import router as adaptive_router
  app.include_router(adaptive_router, prefix="/cam/pocket/adaptive", tags=["CAM"])
  
  # Optional routers with graceful degradation
  try:
      from .routers.cam_helical_v161_router import router as cam_helical_router
      app.include_router(cam_helical_router, prefix="/cam/toolpath", tags=["CAM"])
  except ImportError as e:
      print(f"Warning: Helical router not available: {e}")
  ```
- **Clean import policy** (enforced 2024-12-13): No phantom imports, all dependencies explicit
- **Endpoint governance (H4-H5)**: `/api/governance/stats` tracks legacy API usage for frontend migration planning

### 2. **RMOS (Rosette Manufacturing OS)**
- **5 interconnected domains**:
  1. **Creative Layer**: Rosette pattern design (multi-ring editor, per-ring configuration)
  2. **CAM Layer**: CNC operations (circular saw, line slicing, G-code generation)
  3. **Manufacturing Planning**: Material requirements (strip-family grouping, tile counts)
  4. **Production/Logging**: Job tracking (`saw_slice_batch`, `rosette_plan`) with yield analysis
  5. **Future Engineering**: Physics modeling (kerf, deflection), AI suggestions
- **Key endpoints**:
  - `/api/rmos/ai/*` - AI constraint search and workflow management
  - `/api/rmos/profiles/*` - Constraint profile CRUD with history/rollback
  - `/api/rmos/runs/*` - Run artifacts, attachments, metadata, diff comparison
  - `/api/rmos/saw-ops/*` - Slice preview and pipeline handoff
- **Testing**: `scripts/Test-RMOS-*.ps1` suite (Sandbox, SlicePreview, PipelineHandoff, ArtStudio)
- **Documentation**: `projects/rmos/README.md`, implementation guide, API reference, technical audit

### 3. **Multi-Post CAM Export System**
- **7+ CNC post-processors** with JSON configs in `services/api/app/data/posts/`:
  - Core: `grbl.json`, `mach4.json`, `linuxcnc.json`, `pathpilot.json`, `masso.json`
  - Industrial: `haas.json` (R-mode arcs, G4 S dwell in seconds)
  - Hobby: `marlin.json` (3D printer CNC conversions)
  - Each defines `header` and `footer` arrays for machine-specific G-code wrapping
- **Post presets**: `services/api/app/utils/post_presets.py` provides machine-specific arc modes and dwell syntax
- **Geometry format**: Canonical JSON with `paths` array of `line` and `arc` segments
- **Units**: Bidirectional mm ↔ inch conversion via `services/api/app/util/units.py`
- **Export endpoints**:
  - `/api/geometry/export` – Single DXF or SVG with post metadata
  - `/api/geometry/export_gcode` – G-code with post headers/footers
  - `/api/geometry/export_bundle` – ZIP with DXF + SVG + NC for one post
  - `/api/geometry/export_bundle_multi` – ZIP with DXF + SVG + N × NC files (one per post)

**Example**: Multi-post bundle request
```json
{
  "geometry": {"units":"mm", "paths":[{"type":"line","x1":0,"y1":0,"x2":60,"y2":0}]},
  "gcode": "G90\nG1 X60 Y0 F1200\nM30\n",
  "post_ids": ["GRBL", "Mach4", "LinuxCNC", "PathPilot", "MASSO"],
  "target_units": "inch"  // Optional: converts geometry before export
}
```

### 4. **Unit Conversion System**
- **Server-side**: `scale_geom_units(geom, target_units)` in `services/api/app/util/units.py`
  - Scales `x1`, `y1`, `x2`, `y2`, `cx`, `cy`, `r` fields in paths
  - Conversion factors: `IN_PER_MM = 0.03937007874015748`, `MM_PER_IN = 25.4`
- **Client-side**: `scaleGeomClient(g, target)` in `packages/client/src/components/GeometryOverlay.vue`
  - Real-time geometry rescaling when toggling mm/inch units
  - Updates geometry values, not just labels
- **G-code units**: `G21` for mm, `G20` for inches (auto-injected in post headers)

### 5. **Client-Server Communication**
- **API Base**: Vite dev proxy `/api` → `http://localhost:8000` (FastAPI server)
- **Production**: Nginx proxy in `docker/nginx/` routes `/api` to backend container
- **Client stack**: Vue 3 Composition API (`<script setup>`) + TypeScript in `packages/client/src/`
- **Geometry component**: `GeometryOverlay.vue` – parity checking, export buttons, canvas rendering
- **Request ID Tracking**: All requests include `X-Request-Id` header for correlation (see `RequestIdMiddleware` in `main.py`)

### 6. **DXF/SVG Export Rules**
### 6. **DXF/SVG Export Rules**
- **DXF format**: Always R12 (AC1009) for maximum CAM compatibility
- **SVG format**: Inline paths with metadata comments
- **Metadata injection**: `(POST=<post_id>;UNITS=<units>;DATE=<timestamp>)` in all exports
- **Closed paths**: CNC operations require closed LWPolylines (use cleaning scripts for legacy files)

### 7. **Adaptive Pocketing Engine (Module L)**
- **Current Version**: L.3 (Trochoidal Insertion + Jerk-Aware Time)
- **Core Algorithm**: Pyclipper-based polygon offsetting with integer-safe operations
- **Island Handling**: Automatic keepout zones around holes/islands (L.1)
- **Smoothing**: Rounded joins with configurable arc tolerance (0.05-1.0 mm)
- **True Spiral**: Nearest-point ring stitching for continuous toolpaths (L.2)
- **Adaptive Stepover**: Curvature-based respacing for uniform engagement (L.2)
- **Trochoids**: G2/G3 loop insertion in high-engagement zones (L.3)
- **Jerk-Aware Time**: S-curve acceleration model for realistic estimates (L.3)
- **API Endpoints**:
  - `/api/cam/pocket/adaptive/plan` – Generate toolpath from boundary loops
  - `/api/cam/pocket/adaptive/gcode` – Export with post-processor headers
  - `/api/cam/pocket/adaptive/sim` – Simulate without full G-code generation
  - `/api/cam/pocket/adaptive/batch_export` – Multi-post bundle generation
- **Key Files**:
  - `services/api/app/cam/adaptive_core_l1.py` – L.1 robust offsetting engine
  - `services/api/app/cam/adaptive_core_l2.py` – L.2 spiralizer + adaptive features
  - `services/api/app/cam/trochoid_l3.py` – L.3 trochoidal insertion
  - `services/api/app/cam/feedtime_l3.py` – L.3 jerk-aware time estimator
  - `services/api/app/cam/feedtime.py` – Classic time estimation utilities
  - `services/api/app/cam/stock_ops.py` – Material removal calculations
  - `services/api/app/routers/adaptive_router.py` – FastAPI endpoints
  - `packages/client/src/components/AdaptivePocketLab.vue` – Interactive UI
- **Testing**: `test_adaptive_l1.ps1`, `test_adaptive_l2.ps1` for validation
- **Documentation**: See [docs/ARCHIVE/2025-12/misc/ADAPTIVE_POCKETING_MODULE_L.md](../docs/ARCHIVE/2025-12/misc/ADAPTIVE_POCKETING_MODULE_L.md) and patch notes in `docs/ARCHIVE/2025-12/patches/`

**Example**: Pocket with island
```json
{
  "loops": [
    {"pts": [[0,0], [120,0], [120,80], [0,80]]},           // outer boundary
    {"pts": [[40,20], [80,20], [80,60], [40,60]]}          // island (hole)
  ],
  "tool_d": 6.0,
  "stepover": 0.45,      // 45% of tool diameter
  "margin": 0.8,         // mm clearance from boundaries
  "strategy": "Spiral",  // or "Lanes"
  "smoothing": 0.3,      // arc tolerance in mm
  "feed_xy": 1200
}
```

### 8. **Endpoint Governance & Migration Tracking**
- **Purpose**: Track legacy endpoint usage during Wave 18-19 consolidation
- **Implementation**: `EndpointGovernanceMiddleware` in `services/api/app/governance/endpoint_middleware.py`
- **Router tagging**: Legacy routes include `"Legacy"` in their tags array
- **Metrics endpoint**: `/api/governance/stats` returns usage counts per legacy endpoint
- **Migration workflow**:
  1. Consolidate endpoints into canonical routes (e.g., `/api/cam/toolpath/*`)
  2. Keep legacy routes mounted with `"Legacy"` tag
  3. Monitor usage via governance stats
  4. Update frontend to use canonical routes
  5. Remove legacy mounts when usage drops to zero
- **Truth map**: `docs/ENDPOINT_TRUTH_MAP.md` documents complete API surface
- **Router map**: `ROUTER_MAP.md` tracks 116 routers across 22 deployment waves

---

## Critical Developer Workflows

### **Running the Full Stack**
```bash
# Server (Linux/macOS/WSL)
cd services/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Client (separate terminal)
cd packages/client
npm install
npm run dev  # Runs on http://localhost:5173 with /api proxy

# Docker Compose (production-like)
docker compose up --build  # Runs API:8000, Client:8080, Proxy:8088

# Using Makefile (shortcuts)
make start-api     # Start FastAPI dev server
make start-client  # Start Vue dev client
make test-api      # Run pytest suite
make smoke-helix-posts  # Test all post-processor presets
```

### **Testing Strategy**
The project uses **PowerShell test scripts** for Windows-first development:
```powershell
# Test patterns: test_<feature>.ps1 or Test-<Feature>.ps1
.\test_adaptive_l1.ps1           # L.1 island handling
.\test_adaptive_l2.ps1           # L.2 spiralizer + HUD overlays
.\test_api.ps1                   # Core API smoke tests
.\smoke_v161_helical.ps1         # Helical ramping smoke tests
.\scripts\Test-RMOS-Sandbox.ps1  # RMOS pattern creation
.\scripts\Test-RMOS-SlicePreview.ps1  # RMOS slice preview
.\scripts\Test-RMOS-PipelineHandoff.ps1  # RMOS pipeline integration
```

**Key testing conventions:**
- Test scripts make direct HTTP calls to `http://localhost:8000` (server must be running)
- Use `Invoke-RestMethod` for JSON APIs, `curl` for file downloads
- Validate response structure, statistics, and G-code metadata
- Check for specific patterns: `G21` (mm), `G20` (inch), `(POST=<id>` metadata comments
- Each test script is self-contained and reports ✓/✗ with colored output

**Python tests**:
```bash
# Backend unit tests
cd services/api
pytest tests/ -v

# Test coverage (P3.1 goal: 80%)
pytest --cov=app --cov-report=html tests/

# Frontend tests (Vitest)
cd packages/client
npm run test              # Run all tests
npm run test:watch        # Watch mode
npm run test:request-id   # Test request ID tracking
```

**CI/CD workflows** (`.github/workflows/*.yml`):
- `api_health_check.yml` - API health and smoke tests
- `proxy_parity.yml` - Multi-post export and parity validation
- `adaptive_pocket.yml` - Module L adaptive pocketing tests
- `helical_badges.yml` - Helical ramping with post presets
- `rmos_ci.yml` - RMOS subsystem integration tests
- `comparelab-tests.yml` - Compare Lab golden file validation
- `client_lint_build.yml` - Vue build and TypeScript checks

### **Testing Multi-Post Exports**
```powershell
# Test single-post bundle
curl -X POST http://localhost:8000/geometry/export_bundle \
  -H 'Content-Type: application/json' \
  -d '{"geometry":{"units":"mm","paths":[{"type":"line","x1":0,"y1":0,"x2":60,"y2":0}]}, "gcode":"G90\nM30\n", "post_id":"GRBL"}' \
  -o bundle.zip

# Test multi-post bundle with unit conversion
curl -X POST http://localhost:8000/geometry/export_bundle_multi \
  -H 'Content-Type: application/json' \
  -d '{"geometry":{"units":"mm","paths":[{"type":"line","x1":0,"y1":0,"x2":25.4,"y2":0}]}, "gcode":"G90\nM30\n", "post_ids":["GRBL","Mach4","LinuxCNC"], "target_units":"inch"}' \
  -o multi_bundle.zip

# Verify exports
unzip -l multi_bundle.zip  # Should show program_GRBL.nc, program_Mach4.nc, program_LinuxCNC.nc
unzip -p multi_bundle.zip program_GRBL.nc | head -n 10  # Check for G20, (POST=GRBL
```

### **Adding New Post Processors**
1. Create JSON config in `services/api/app/data/posts/<name>.json`:
```json
{
  "header": ["G90", "G17", "(Custom header comment)"],
  "footer": ["M30", "(End of program)"]
}
```
2. (Optional) Add post preset in `services/api/app/utils/post_presets.py` for arc mode/dwell syntax
3. Test with export endpoint using `post_id="<name>"`
4. Add to CI test in `.github/workflows/proxy_parity.yml`

### **Module Versioning Pattern**
The project uses **patch-based versioning** for major features:
- **L-series**: Adaptive pocketing (L.1 → L.2 → L.3)
- **M-series**: Machine profiles and optimization (M.1 → M.2 → M.3 → M.4)
- **N-series**: Post-processor enhancements (N.0 → N.18)
- **Patch letters**: Single-file fixes (Patch A-D, Patch W)

**Key pattern**: Each version builds on previous, never breaks backward compatibility. Router code uses versioned imports:
```python
from ..cam.adaptive_core_l3 import plan_adaptive_l3  # Latest
from ..cam.adaptive_core_l2 import plan_adaptive_l2  # Still available
from ..cam.adaptive_core_l1 import plan_adaptive_l1  # Still available
```

**Documentation**: Each module has 3 docs - `MODULE_X.md` (overview), `PATCH_X_SUMMARY.md` (implementation), `PATCH_X_QUICKREF.md` (quick reference)

---

## Project-Specific Conventions

### **Geometry & Units**
- **Internal storage**: All geometry MUST be in mm. Use `units` field to track current state.
- **Unit conversion**: Use `scale_geom_units()` server-side or `scaleGeomClient()` client-side
- **DXF format**: Always export R12 (AC1009) for maximum CAM compatibility
- **Closed paths**: CNC operations require closed LWPolylines (use cleaning scripts for legacy files)

### **FastAPI Endpoints**
```python
# Geometry endpoints accept both mm and inch, converting when needed
from ..util.units import scale_geom_units

@router.post("/export_bundle_multi")
def export_bundle_multi(body: ExportBundleMultiIn):
    geom_src = body.geometry.dict()
    geom = scale_geom_units(geom_src, body.target_units or body.geometry.units)
    # ... export using converted geometry
```

### **Router Registration Pattern**
Routers are dynamically imported in `services/api/app/main.py` with try/except for optional features:
```python
# Core features (always available)
from .routers.adaptive_router import router as adaptive_router
app.include_router(adaptive_router, prefix="/cam/pocket/adaptive", tags=["CAM"])

# Optional features (graceful degradation)
try:
    from .routers.cam_helical_v161_router import router as cam_helical_v161_router
    app.include_router(cam_helical_v161_router, prefix="/cam/toolpath", tags=["CAM"])
except Exception as e:
    print(f"Warning: Helical router not available: {e}")
    cam_helical_v161_router = None
```
**Why**: Allows progressive feature rollout without breaking existing deployments.

### **Error Handling Pattern**
```python
# Validation errors → 400 Bad Request
if tool_d <= 0:
    raise HTTPException(status_code=400, detail="Tool diameter must be positive")

# Conservative fallbacks (don't crash on bad config)
try:
    smoothing = max(0.05, min(1.0, body.smoothing))
except Exception:
    smoothing = 0.3  # Safe default

# Geometry validation with detailed messages
if not loops or len(loops) < 1:
    raise HTTPException(400, detail="At least one boundary loop required")
```

### **Vue Component Structure**
- `packages/client/src/components/GeometryOverlay.vue` – Parity checking, unit toggle, export buttons, post chooser integration
- `packages/client/src/components/PostChooser.vue` – Multi-select checkbox grid for post-processor selection (localStorage persistence)
- `packages/client/src/components/PostPreviewDrawer.vue` – Side drawer showing post headers/footers and 20-line NC preview
- `packages/client/src/components/GeometryUpload.vue` – DXF/SVG file import
- Use `<script setup lang="ts">` for all new components
- Real-time unit conversion: Toggle triggers `scaleGeomClient()` to update geometry values

**Post Chooser Pattern**:
```typescript
// Selected posts persist to localStorage('toolbox.selectedPosts')
const selectedPosts = ref<string[]>(JSON.parse(localStorage.getItem('toolbox.selectedPosts') || '["GRBL"]'))

// Multi-post export uses selected posts
async function exportMultiPostBundle(){
  const posts = selectedPosts.value?.length ? selectedPosts.value : ['GRBL']
  // ... fetch with post_ids: posts
}
```

### **SDK Endpoint Helpers (H8.3)**
Use **typed, per-endpoint helpers** instead of ad-hoc `fetch()` calls:

```typescript
// ✅ DO: Use typed helpers from sdk/endpoints
import { cam } from "@/sdk/endpoints";

const { gcode, summary, requestId } = await cam.roughingGcode({
  entities: [/* boundary */],
  tool_diameter: 6.0,
  depth_per_pass: 2.0,
  // ... typed payload
});

// ❌ DON'T: Raw fetch() in components
const response = await fetch("/api/cam/roughing_gcode", {
  method: "POST",
  body: JSON.stringify(payload),
});
```

**Key Benefits:**
- Type-safe payloads and responses
- Automatic header parsing (e.g., `X-CAM-Summary`)
- Request-id propagation for tracing
- Consistent error handling with `ApiError`
- All helpers return `{...result, requestId}` shape

**Available Helpers:**
- `cam.roughingGcode(payload)` – Legacy entity-based roughing
- `cam.roughingGcodeIntent(intent, strict?)` – Intent-native with optional strict mode
- `cam.runPipeline(formData)` – FormData pipeline submission

**Migration Status (H8.3):**
- Foundation: ✅ Complete (6/6 tests passing)
- Component Migration: 🚧 In Progress (6 legacy usages identified)
- CI Gate: ✅ Integrated (`legacy_usage_gate.py` in rmos_ci.yml)
- Budget: 10 during transition, target 0 when complete

See [packages/client/src/sdk/endpoints/README.md](../packages/client/src/sdk/endpoints/README.md) for full documentation.

### **Post Processor JSON Format**
Located in `services/api/app/data/posts/*.json`:
```json
{
  "header": [
    "G90",           // Absolute positioning
    "G17",           // XY plane selection
    "(Machine: GRBL 1.1)"
  ],
  "footer": [
    "M30",           // Program end
    "(Generated by Luthier's Tool Box)"
  ]
}
```
- `header` lines injected before G-code body (units command `G21`/`G20` auto-added first)
- `footer` lines appended after G-code body
- Metadata comment `(POST=<id>;UNITS=<units>;DATE=<timestamp>)` auto-injected

---

## Integration Points & External Dependencies

### **CAM Software Integration**
The toolbox supports **5 CAM platforms** (current placeholders):
- **Fusion 360** (Primary): JSON setup files in `Lutherier Project*/Les Paul_Project/09252025/`
  - `FusionSetup_Base_LP_Mach4.json` – Tool library and operation parameters
- **Mach4**: Safety macros and auto-variables in `plugins/gibson/nc_lint_autovars.py`
- **VCarve**: Standard Mach3-compatible post-processor
- **LinuxCNC (EMC2)**: RS274/NGC G-code dialect (placeholder, post-processor TBD)
- **Masso Controller**: Masso G3 G-code variant (placeholder, adapter script TBD)

**CRITICAL**: CAM files in `Lutherier Project*/` contain production tooling data (feeds, speeds, tool library). DO NOT modify unless updating actual shop equipment specs.

### **Key Python Libraries**
- **ezdxf** – DXF file read/write (R12 format)
- **shapely** – Geometry operations (union, intersect, polygon processing)
- **pyclipper** – Production-grade polygon offsetting (L.1 adaptive pocketing)
- **fastapi + pydantic** – API and validation
- **uvicorn** – ASGI server
- **anthropic** – Blueprint Import AI analysis (Claude API)
- **reportlab** – PDF design sheet generation
- **weasyprint** – HTML to PDF conversion for operator reports
- **sqlalchemy + alembic** – Database ORM and migrations
- **pytest + pytest-cov** – Testing framework with coverage (80% target)

### **Vue Stack**
- **Vue 3.4+** with `<script setup>` syntax
- **Vite 5.0+** for dev/build
- **TypeScript** for type safety (`.ts` in utils, `.vue` with `<script setup lang="ts">`)
- **Pinia** for state management
- **Vue Router** for navigation
- **Zod** for runtime validation
- **Chart.js** for data visualization
- **Vitest + JSDOM** for component testing

### **Docker Architecture**
The project uses **multi-stage Docker builds** for each service:
- **API Container**: Python 3.11+ with FastAPI, exposes port 8000
  - Health check: `curl -fsS http://127.0.0.1:8000/health`
  - Volume mount: `./services/api/app/data` (SQLite DB + JSON configs)
- **Client Container**: Node 20+ with Vite, exposes port 8080
  - Nginx serves static build in production
- **Proxy Container**: Nginx reverse proxy, exposes port 8088
  - Routes `/api` → API:8000, `/` → Client:8080

**Critical Docker rules** (from `docker-compose.yml`):
1. API healthcheck MUST succeed before client starts (prevents race conditions)
2. Port mappings MUST match .env defaults (8000=API, 8080=Client, 8088=Proxy)
3. Volume mounts MUST preserve data directory (SQLite DB, posts, templates)
4. CORS_ORIGINS MUST include client URL to prevent API access errors
5. All services MUST have `restart:unless-stopped` for production stability

---

## Important Files & Directories

| Path | Purpose |
|------|---------|
| `services/api/app/main.py` | FastAPI application entry point, router registration |
| `services/api/app/routers/geometry_router.py` | Geometry import/export, parity checking, multi-post bundles |
| `services/api/app/routers/tooling_router.py` | Post-processor listing and configuration management |
| `services/api/app/routers/adaptive_router.py` | Adaptive pocketing endpoints (Module L) |
| `services/api/app/routers/machine_router.py` | Machine profile CRUD (Module M) |
| `services/api/app/routers/cam_helical_v161_router.py` | Helical ramping endpoint (Art Studio v16.1) |
| `services/api/app/cam/adaptive_core_l*.py` | Adaptive pocketing versions (L.1, L.2, L.3) |
| `services/api/app/cam/trochoid_l3.py` | Trochoidal insertion logic (L.3) |
| `services/api/app/cam/feedtime_l3.py` | Jerk-aware time estimation (L.3) |
| `services/api/app/util/units.py` | Unit conversion utilities (mm ↔ inch) |
| `services/api/app/util/exporters.py` | DXF R12 and SVG export functions |
| `services/api/app/utils/post_presets.py` | Post-processor presets (arc modes, dwell syntax) |
| `services/api/app/data/posts/*.json` | Post-processor configurations (GRBL, Mach4, etc.) |
| `packages/client/src/components/GeometryOverlay.vue` | Main geometry UI with export buttons and post chooser |
| `packages/client/src/components/PostChooser.vue` | Multi-select post-processor picker with localStorage persistence |
| `packages/client/src/components/PostPreviewDrawer.vue` | Side drawer for previewing post headers/footers and NC output |
| `packages/client/src/components/GeometryUpload.vue` | DXF/SVG file import component |
| `packages/client/src/components/AdaptivePocketLab.vue` | Interactive adaptive pocketing UI (Module L) |
| `.github/workflows/proxy_parity.yml` | CI pipeline testing multi-post exports |
| `.github/workflows/adaptive_pocket.yml` | CI tests for adaptive pocketing (Module L) |
| `.github/workflows/helical_badges.yml` | CI tests for helical ramping (v16.1) |
| `docker-compose.yml` | Full stack deployment (API:8000, Client:8080, Proxy:8088) |
| `docker/api/Dockerfile` | FastAPI container build |
| `docker/client/Dockerfile` | Vue client container build |
| `docker/proxy/Dockerfile` | Nginx reverse proxy configuration |
| `test_adaptive_l1.ps1`, `test_adaptive_l2.ps1` | PowerShell test scripts for Module L |
| `smoke_v161_helical.ps1` | Smoke tests for helical ramping |
| `ADAPTIVE_POCKETING_MODULE_L.md` | Module L overview |
| `PATCH_L*_SUMMARY.md` | Implementation docs for L.1, L.2, L.3 |
| `MACHINE_PROFILES_MODULE_M.md` | Module M overview (machine profiles) |
| `HELICAL_POST_PRESETS.md` | Post preset system documentation |
| `CODING_POLICY.md` | Comprehensive coding standards and patterns |

---

## Testing & CI

### **Local Testing**
```powershell
# Python lint
pip install black ruff
ruff check services/api
black --check services/api

# Client build test
cd packages/client
npm run build
```

### **CI Pipeline** (`.github/workflows/proxy_parity.yml`)
- Builds Docker containers for API, Client, and Proxy
- Tests geometry parity checking (design vs toolpath)
- Validates DXF/SVG/G-code exports with post metadata
- Tests multi-post bundle exports (5 NC files + DXF + SVG)
- Validates unit conversion (mm → inch scaling in exports)

---

## Common Pitfalls & Solutions

### **Issue**: DXF not recognized by Fusion 360
**Solution**: Ensure you're exporting **R12 format** with **closed LWPolylines**. Use cleaning scripts to convert arcs/splines.

### **Issue**: Units mismatch (inches vs mm)
**Solution**: All data MUST be in mm. If adding inch support, convert at API boundary only. Never store mixed units.

### **Issue**: Post-processor not found in exports
**Solution**: Verify post config exists in `services/api/app/data/posts/<name>.json`. Post IDs are case-sensitive (e.g., "GRBL" not "grbl").

### **Issue**: Debugging request flow across components
**Solution**: Use `X-Request-Id` header for correlation. Client includes ID in all API calls, server echoes it back, and logs include it via `RequestIdMiddleware`. Check logs with `grep <request-id>` or frontend console for end-to-end tracing.

### **Issue**: Import errors after adding routers
**Solution**: Verify all dependencies exist (2024-12-13 clean import policy). No phantom imports allowed. Add graceful degradation with try/except only for truly optional features, never to hide missing files.

### **Issue**: Frontend uses legacy API endpoints
**Solution**: Check governance stats at `/api/governance/stats` to see usage counts. Migrate components to use canonical endpoints (e.g., `/api/cam/toolpath/*` instead of `/api/cam/vcarve`). CI gate in `rmos_ci.yml` tracks frontend legacy usage via `legacy_usage_gate.py` - budget currently set to 10, target 0.

---

## H7.2: CAM Intent Implementation

> **Added 2025-12-27**: Intent-native CAM endpoints with strict mode validation.

### Overview

H7.2 introduces intent-native CAM endpoints that use the canonical `CamIntentV1` envelope. These endpoints normalize input, validate constraints, and emit Prometheus metrics.

### New Router

- `cam_roughing_intent_router` — Intent-native roughing G-code generation

**Prefix:** `/api/cam`
**Tags:** `CAM`, `Intent`

### Endpoints

| Method | Endpoint | Query Params | Description |
|--------|----------|--------------|-------------|
| POST | `/api/cam/roughing_gcode_intent` | `strict=bool` | Generate roughing G-code from `CamIntentV1` |

### Strict Mode (H7.2.3)

The `strict` query parameter controls validation behavior:

- `?strict=false` (default): Returns 200 with issues in response body
- `?strict=true`: Returns 422 if normalization produces any issues

```bash
# Non-strict (default) - tolerates issues
curl -X POST http://localhost:8000/api/cam/roughing_gcode_intent \
  -H "Content-Type: application/json" \
  -d '{"design": {...}}'

# Strict - rejects on issues
curl -X POST "http://localhost:8000/api/cam/roughing_gcode_intent?strict=true" \
  -H "Content-Type: application/json" \
  -d '{"design": {...}}'
```

### Prometheus Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `cam_roughing_intent_requests_total` | Counter | Total requests |
| `cam_roughing_intent_issues_total` | Counter | Requests with normalization issues |
| `cam_roughing_intent_strict_rejects_total` | Counter | Strict mode rejections |
| `cam_roughing_intent_latency_ms` | Histogram | Request latency |

### Test Coverage

- `test_cam_roughing_intent_strict.py` — Strict mode behavior tests
- `test_roughing_gcode_intent_metrics.py` — Metrics emission tests
- `test_cam_intent_strict_reject_logs_request_id.py` — Request ID logging tests

---

## Design Philosophy

This project prioritizes **CAM compatibility** over visual fidelity. DXF exports are optimized for CNC machining workflows:
- Closed paths for toolpath generation
- R12 format for legacy CAM software support
- Millimeter precision matching woodworking machinery standards
- Separation of "design" (visual) and "export" (CAM-ready) geometry

When adding features, always consider:
1. Will this DXF import cleanly into Fusion 360/VCarve/Mach4?
2. Are all dimensions in millimeters with appropriate tolerance?
3. Can the geometry be converted to closed toolpaths?

---

## Quick Reference Commands

```powershell
# Start dev stack
cd services/api && .\.venv\Scripts\Activate.ps1 && uvicorn app.main:app --reload
cd packages/client && npm run dev

# Test multi-post export
curl -X POST http://localhost:8000/geometry/export_bundle_multi `
  -H 'Content-Type: application/json' `
  -d '{"geometry":{"units":"mm","paths":[{"type":"line","x1":0,"y1":0,"x2":60,"y2":0}]}, "gcode":"G90\nM30\n", "post_ids":["GRBL","Mach4","LinuxCNC"]}' `
  -o multi_bundle.zip

# Build for production
cd packages/client && npm run build
cd services/api && docker build -f ../../docker/api/Dockerfile -t ltb-api .

# Run full stack with Docker
docker compose up --build
```

---

## Frontend Legacy Usage CI Gate

> **Added 2025-12-27**: Automated detection of legacy API usage in frontend code.

### How It Works

The `legacy_usage_gate.py` CI script:
1. Scans `packages/client/src` and `packages/sdk/src` for API paths
2. Matches paths against known legacy patterns
3. Reports usage and fails if over budget

### Configuration

In `.github/workflows/rmos_ci.yml`:

```yaml
- name: Frontend legacy usage gate
  env:
    LEGACY_USAGE_BUDGET: "10"  # Adjust as migration progresses
  run: |
    python -m app.ci.legacy_usage_gate \
      --roots "../../packages/client/src" "../../packages/sdk/src" \
      --budget ${LEGACY_USAGE_BUDGET}
```

### Reducing the Budget

As frontend migration progresses:
1. Fix legacy usages in frontend code
2. Reduce `LEGACY_USAGE_BUDGET` in CI workflow
3. Goal: Set to `0` when migration complete

### Adding New Legacy Patterns

Edit `services/api/app/ci/legacy_usage_gate.py`:

```python
LEGACY_ROUTES: List[Tuple[str, str, str]] = [
    # (regex_pattern, canonical_replacement, notes)
    (r"^/api/old/path", "/api/new/path", "Migration notes"),
]
```
