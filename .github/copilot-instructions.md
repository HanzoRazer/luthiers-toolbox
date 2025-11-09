# Luthier's Tool Box – AI Agent Instructions

## Project Overview
This is a **CNC guitar lutherie CAD/CAM toolbox** combining:
- **Vue 3 + Vite** frontend (TypeScript) in `packages/client/` for guitar design visualization
- **FastAPI** backend (Python 3.11+) in `services/api/` for DXF/SVG export, geometry processing, and multi-post CNC workflows
- **Multi-post processor support**: GRBL, Mach4, LinuxCNC, PathPilot, MASSO with JSON configuration files
- **Unit conversion**: Bidirectional mm ↔ inch geometry scaling (client + server)
- **Smart Guitar Project** (separate) for IoT/embedded lutherie with Raspberry Pi 5

**Core Mission**: Enable luthiers to design guitar components, export CAM-ready files (DXF R12 + SVG + G-code), and support multiple CNC platforms through a unified web interface.

**Repository Structure**: Mono-repo with active development in `services/api/`, `packages/client/`, and `packages/shared/`. Legacy MVP builds and CAD archives in `Luthiers Tool Box/` are reference implementations only.

---

## Architecture & Key Patterns

### 1. **Multi-Post CAM Export System**
- **5 CNC post-processors** with JSON configs in `services/api/app/data/posts/`:
  - `grbl.json`, `mach4.json`, `linuxcnc.json`, `pathpilot.json`, `masso.json`
  - Each defines `header` and `footer` arrays for machine-specific G-code wrapping
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

### 2. **Unit Conversion System**
- **Server-side**: `scale_geom_units(geom, target_units)` in `services/api/app/util/units.py`
  - Scales `x1`, `y1`, `x2`, `y2`, `cx`, `cy`, `r` fields in paths
  - Conversion factors: `IN_PER_MM = 0.03937007874015748`, `MM_PER_IN = 25.4`
- **Client-side**: `scaleGeomClient(g, target)` in `packages/client/src/components/GeometryOverlay.vue`
  - Real-time geometry rescaling when toggling mm/inch units
  - Updates geometry values, not just labels
- **G-code units**: `G21` for mm, `G20` for inches (auto-injected in post headers)

### 3. **Client-Server Communication**
- **API Base**: Vite dev proxy `/api` → `http://localhost:8000` (FastAPI server)
- **Production**: Nginx proxy in `docker/proxy/` routes `/api` to backend container
- **Client stack**: Vue 3 Composition API (`<script setup>`) + TypeScript in `packages/client/src/`
- **Geometry component**: `GeometryOverlay.vue` – parity checking, export buttons, canvas rendering

### 4. **DXF/SVG Export Rules**
- **DXF format**: Always R12 (AC1009) for maximum CAM compatibility
- **SVG format**: Inline paths with metadata comments
- **Metadata injection**: `(POST=<post_id>;UNITS=<units>;DATE=<timestamp>)` in all exports
- **Closed paths**: CNC operations require closed LWPolylines (use cleaning scripts for legacy files)

### 5. **Adaptive Pocketing Engine (Module L)**
- **Current Version**: L.1 (Robust Offsetting + Island Subtraction)
- **Core Algorithm**: Pyclipper-based polygon offsetting with integer-safe operations
- **Island Handling**: Automatic keepout zones around holes/islands
- **Smoothing**: Rounded joins with configurable arc tolerance (0.05-1.0 mm)
- **API Endpoints**:
  - `/api/cam/pocket/adaptive/plan` – Generate toolpath from boundary loops
  - `/api/cam/pocket/adaptive/gcode` – Export with post-processor headers
  - `/api/cam/pocket/adaptive/sim` – Simulate without full G-code generation
- **Key Files**:
  - `services/api/app/cam/adaptive_core_l1.py` – L.1 robust offsetting engine
  - `services/api/app/cam/feedtime.py` – Time estimation utilities
  - `services/api/app/cam/stock_ops.py` – Material removal calculations
  - `services/api/app/routers/adaptive_router.py` – FastAPI endpoints
  - `packages/client/src/components/AdaptivePocketLab.vue` – Interactive UI
- **Testing**: `test_adaptive_l1.ps1` for island handling validation
- **Documentation**: See [ADAPTIVE_POCKETING_MODULE_L.md](../ADAPTIVE_POCKETING_MODULE_L.md) and [PATCH_L1_ROBUST_OFFSETTING.md](../PATCH_L1_ROBUST_OFFSETTING.md)

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

---

## Critical Developer Workflows

### **Running the Full Stack**
```powershell
# Server (PowerShell)
cd services/api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Client (separate terminal)
cd packages/client
npm install
npm run dev  # Runs on http://localhost:5173 with /api proxy

# Docker Compose (production-like)
docker compose up --build  # Runs API:8000, Client:8080, Proxy:8088
```

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
2. Test with export endpoint using `post_id="<name>"`
3. Add to CI test in `.github/workflows/proxy_parity.yml`

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

### **Key Python Libraries**
- **ezdxf** – DXF file read/write (R12 format)
- **shapely** – Geometry operations (union, intersect, polygon processing)
- **pyclipper** – Production-grade polygon offsetting (L.1 adaptive pocketing)
- **fastapi + pydantic** – API and validation
- **uvicorn** – ASGI server

### **Vue Stack**
- **Vue 3.4+** with `<script setup>` syntax
- **Vite 5.0+** for dev/build
- **TypeScript** for type safety (`.ts` in utils, `.vue` with `<script setup lang="ts">`)

---

## Important Files & Directories

| Path | Purpose |
|------|---------|
| `services/api/app/main.py` | FastAPI application entry point, router registration |
| `services/api/app/routers/geometry_router.py` | Geometry import/export, parity checking, multi-post bundles |
| `services/api/app/routers/tooling_router.py` | Post-processor listing and configuration management |
| `services/api/app/util/units.py` | Unit conversion utilities (mm ↔ inch) |
| `services/api/app/util/exporters.py` | DXF R12 and SVG export functions |
| `services/api/app/data/posts/*.json` | Post-processor configurations (GRBL, Mach4, etc.) |
| `packages/client/src/components/GeometryOverlay.vue` | Main geometry UI with export buttons and post chooser |
| `packages/client/src/components/PostChooser.vue` | Multi-select post-processor picker with localStorage persistence |
| `packages/client/src/components/PostPreviewDrawer.vue` | Side drawer for previewing post headers/footers and NC output |
| `packages/client/src/components/GeometryUpload.vue` | DXF/SVG file import component |
| `.github/workflows/proxy_parity.yml` | CI pipeline testing multi-post exports |
| `docker-compose.yml` | Full stack deployment (API:8000, Client:8080, Proxy:8088) |
| `docker/api/Dockerfile` | FastAPI container build |
| `docker/client/Dockerfile` | Vue client container build |
| `docker/proxy/Dockerfile` | Nginx reverse proxy configuration |

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
