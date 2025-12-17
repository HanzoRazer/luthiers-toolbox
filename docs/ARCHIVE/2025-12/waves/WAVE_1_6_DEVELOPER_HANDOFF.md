# Wave 1-6 Structural Refactoring — Developer Handoff

**Date:** December 6, 2025  
**Branch:** `feature/rmos-2-0-skeleton`  
**Status:** ✅ Implementation Complete (274 tests passing)

---

## 🎯 Executive Summary

Waves 1-6 represent a major architectural refactoring to eliminate "spaghetti code" by introducing:

1. **MLPath** — A unified geometry spine class for all toolpath operations
2. **Layered Architecture** — Clear separation between routers, geometry engines, and physics adapters
3. **Version-Aware DXF Export** — Support for R12/R14/R18 CAD compatibility
4. **Saw Lab Bridge** — Physics adapter connecting Art Studio to Saw Lab calculators
5. **Tool/Material Profiles** — JSON-driven configuration with intelligent defaults

---

## 📁 New File Inventory

### Wave 1: Art Studio Core

| File | Purpose |
|------|---------|
| `services/api/app/toolpath/__init__.py` | **MLPath class** — Core geometry spine with `Point2D` type alias |
| `services/api/app/toolpath/vcarve_toolpath.py` | SVG → MLPaths → G-code conversion |
| `services/api/app/art_studio/svg_ingest_service.py` | SVG parsing to polylines with stats |
| `services/api/app/art_studio/vcarve_router.py` | FastAPI endpoints: `/preview`, `/gcode` |

### Wave 2: DXF Import/Export

| File | Purpose |
|------|---------|
| `services/api/app/toolpath/dxf_io_legacy.py` | DXF R12 reading and writing |
| `services/api/app/toolpath/dxf_exporter.py` | Version-aware export (R12/R14/R18) with `DXFVersion` enum |

### Wave 3: Rosette/Relief Geometry

| File | Purpose |
|------|---------|
| `services/api/app/toolpath/rosette_geometry.py` | `RosetteDesignSpec` and ring generation |
| `services/api/app/toolpath/relief_geometry.py` | `ReliefDesignSpec` and polyline handling |
| `services/api/app/art_studio/relief_router.py` | Endpoints: `/preview`, `/preview-feasibility`, `/export-dxf` |

### Wave 4-5: Calculators & Saw Bridge

| File | Purpose |
|------|---------|
| `services/api/app/calculators/__init__.py` | Package init with resilient imports |
| `services/api/app/calculators/saw_bridge.py` | Physics adapter: `evaluate_operation_feasibility()` |
| `services/api/app/calculators/tool_profiles.py` | Profile resolution: `resolve_flute_count()`, `resolve_chipload_band()` |

### Wave 6: Tool/Material Data Layer

| File | Purpose |
|------|---------|
| `services/api/app/data/__init__.py` | Data package init |
| `services/api/app/data/tool_library.py` | JSON loader: `ToolProfile`, `MaterialProfile`, `load_tool_library()` |

### Test Files Created

| File | Tests |
|------|-------|
| `app/tests/test_art_studio_vcarve_router.py` | 3 tests — VCarve preview/gcode endpoints |
| `app/tests/test_dxf_r12_roundtrip.py` | 2 tests — DXF read/write roundtrip |
| `app/tests/test_dxf_exporter_versions.py` | 4 tests — R12/R14/R18 header verification |
| `app/tests/test_tool_profiles.py` | 11 tests — Tool/material profile loading |
| `app/tests/test_saw_bridge_profiles_integration.py` | 5 tests — Physics adapter integration |

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Vue 3 Frontend                              │
│  (Art Studio, Blueprint Lab, Saw Lab panels)                        │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │ HTTP/JSON
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    FastAPI Routers (Wave 1, 3)                      │
│  /api/art-studio/vcarve/*  │  /api/art-studio/relief/*              │
│  /api/art-studio/rosette/* │  /api/art-studio/bracing/*             │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   Geometry Layer (Wave 1, 2, 3)                     │
│  toolpath/              │  MLPath spine class                       │
│  ├── __init__.py        │  Point2D = tuple[float, float]            │
│  ├── vcarve_toolpath.py │  SVG → MLPaths → G-code                   │
│  ├── dxf_io_legacy.py   │  DXF R12 read/write                       │
│  ├── dxf_exporter.py    │  Version-aware export (R12/R14/R18)       │
│  ├── rosette_geometry.py│  Ring generation                          │
│  └── relief_geometry.py │  Polyline handling                        │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  Physics Adapter Layer (Wave 5)                     │
│  calculators/                                                       │
│  ├── __init__.py           │  Package init (resilient imports)      │
│  ├── saw_bridge.py         │  evaluate_operation_feasibility()      │
│  └── tool_profiles.py      │  Profile resolution helpers            │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Data Layer (Wave 6)                             │
│  data/                                                              │
│  ├── __init__.py           │  Package init                          │
│  ├── tool_library.py       │  JSON loader for profiles              │
│  └── tool_library.json     │  (existing) Tool/material definitions  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔑 Key Classes & Functions

### MLPath (Wave 1)

The **geometry spine** class unifying all toolpath operations:

```python
from app.toolpath import MLPath, Point2D

# Point2D is a type alias
Point2D = tuple[float, float]

# MLPath wraps a list of points with metadata
path = MLPath(points=[(0, 0), (10, 0), (10, 10), (0, 10)], closed=True)

# Properties
path.points      # List[Point2D]
path.closed      # bool
len(path)        # Number of points
path.bounds()    # (min_x, min_y, max_x, max_y)
path.length()    # Total path length in mm
path.centroid()  # (cx, cy)

# Transforms
path.translate(dx, dy)  # Returns new MLPath
path.scale(sx, sy)      # Returns new MLPath
path.rotate(degrees)    # Returns new MLPath (around centroid)
```

### DXF Export (Wave 2)

Version-aware export supporting R12 (CAM-safe), R14, and R18:

```python
from app.toolpath.dxf_exporter import export_mlpaths_to_dxf, DXFVersion, DXFExportOptions

# Simple export (R12 default)
dxf_content = export_mlpaths_to_dxf(paths, version=DXFVersion.R12)

# With options
opts = DXFExportOptions(
    version=DXFVersion.R14,
    layer_name="CONTOUR",
    color_index=7
)
dxf_content = export_mlpaths_to_dxf(paths, options=opts)
```

### Saw Bridge (Wave 5)

Physics adapter connecting Art Studio to Saw Lab calculators:

```python
from app.calculators.saw_bridge import evaluate_operation_feasibility, SawPhysicsResult

result: SawPhysicsResult | None = evaluate_operation_feasibility(
    tool_id="flat_6.0",
    material_id="Ebony",
    feed_rate=1200.0,
    rpm=18000,
    doc=2.0
)

if result:
    print(f"Chipload: {result.chipload}")      # mm/tooth
    print(f"Heat index: {result.heat_index}")  # 0.0-1.0
    print(f"Deflection: {result.deflection}")  # mm
    print(f"Feasible: {result.feasible}")      # bool
```

### Tool Library (Wave 6)

JSON-driven profile loading:

```python
from app.data.tool_library import load_tool_library, get_tool_profile, get_material_profile

# Load all profiles (cached after first call)
tools, materials = load_tool_library()

# Get specific profiles
tool = get_tool_profile("flat_6.0")
# Returns: ToolProfile(id="flat_6.0", type="flat", diameter=6.0, flutes=2, ...)

material = get_material_profile("Ebony")
# Returns: MaterialProfile(id="Ebony", density=1.2, heat_sensitivity="high", ...)
```

---

## 🛤️ Router Registration

Routers are registered in `services/api/app/main.py`:

```python
# Wave 1: VCarve router
from .art_studio.vcarve_router import router as art_studio_vcarve_router
app.include_router(art_studio_vcarve_router, prefix="/api/art-studio/vcarve", tags=["Art Studio"])

# Wave 3: Relief router
from .art_studio.relief_router import router as art_studio_relief_router
app.include_router(art_studio_relief_router, prefix="/api/art-studio/relief", tags=["Art Studio"])
```

### New API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/art-studio/vcarve/preview` | POST | Preview SVG as toolpath JSON |
| `/api/art-studio/vcarve/gcode` | POST | Generate G-code from SVG |
| `/api/art-studio/relief/preview` | POST | Preview relief design |
| `/api/art-studio/relief/preview-feasibility` | POST | Check relief feasibility |
| `/api/art-studio/relief/export-dxf` | POST | Export relief as DXF |

---

## 📦 Package Dependencies

### New Requirements

```txt
# Already in requirements.txt (no new external deps needed)
# Wave 1-6 use only stdlib + existing FastAPI/Pydantic
```

### Import Patterns

```python
# Wave 1: Toolpath core
from app.toolpath import MLPath, Point2D
from app.toolpath.vcarve_toolpath import svg_to_naive_gcode, VCarveToolpathParams
from app.art_studio.svg_ingest_service import parse_svg_to_polylines

# Wave 2: DXF
from app.toolpath.dxf_io_legacy import read_dxf_to_mlpaths, write_mlpaths_to_dxf_r12
from app.toolpath.dxf_exporter import export_mlpaths_to_dxf, DXFVersion

# Wave 3: Rosette/Relief
from app.toolpath.rosette_geometry import build_rosette_mlpaths, RosetteDesignSpec
from app.toolpath.relief_geometry import relief_design_to_mlpaths, ReliefDesignSpec

# Wave 5: Physics adapter
from app.calculators.saw_bridge import evaluate_operation_feasibility

# Wave 6: Profiles
from app.data.tool_library import get_tool_profile, get_material_profile
from app.calculators.tool_profiles import resolve_flute_count, resolve_chipload_band
```

---

## 🧪 Testing

### Run All Tests

```powershell
cd services/api
.\.venv\Scripts\python.exe -m pytest -v
# Expected: 274 passed, 1 skipped
```

### Run Wave-Specific Tests

```powershell
# Wave 1: VCarve router
pytest app/tests/test_art_studio_vcarve_router.py -v

# Wave 2: DXF
pytest app/tests/test_dxf_r12_roundtrip.py app/tests/test_dxf_exporter_versions.py -v

# Wave 5-6: Saw Bridge + Profiles
pytest app/tests/test_saw_bridge_profiles_integration.py app/tests/test_tool_profiles.py -v
```

### Quick Smoke Tests

```powershell
# MLPath import
python -c "from app.toolpath import MLPath; p = MLPath([(0,0),(1,1)]); print(f'OK: {p}')"

# Tool library
python -c "from app.data.tool_library import get_tool_profile; print(get_tool_profile('flat_6.0'))"

# Saw bridge
python -c "from app.calculators.saw_bridge import evaluate_operation_feasibility; print(evaluate_operation_feasibility('flat_6.0', 'Ebony', 1200, 18000, 2.0))"
```

---

## 🔄 Data Flow Examples

### Example 1: SVG → G-code (Wave 1)

```
User uploads SVG
        │
        ▼
svg_ingest_service.parse_svg_to_polylines(svg_content)
        │
        ▼
List[List[Point2D]] polylines
        │
        ▼
vcarve_toolpath.svg_to_naive_gcode(polylines, params)
        │
        ▼
G-code string with headers/footers
```

### Example 2: Relief → DXF (Wave 2 + 3)

```
ReliefDesignSpec
        │
        ▼
relief_geometry.relief_design_to_mlpaths(spec)
        │
        ▼
List[MLPath] paths
        │
        ▼
dxf_exporter.export_mlpaths_to_dxf(paths, DXFVersion.R12)
        │
        ▼
DXF R12 string (CAM-compatible)
```

### Example 3: Feasibility Check (Wave 5 + 6)

```
Operation params (tool_id, material_id, feed, rpm, doc)
        │
        ▼
saw_bridge.evaluate_operation_feasibility(...)
        │
        ├─► tool_profiles.resolve_flute_count(tool_id)
        │         │
        │         ▼
        │   data/tool_library.get_tool_profile(tool_id)
        │
        ├─► tool_profiles.resolve_chipload_band(tool_id)
        │
        └─► Physics calculations (chipload, heat, deflection)
                  │
                  ▼
            SawPhysicsResult(chipload, heat_index, deflection, feasible)
```

---

## ⚠️ Known Limitations

1. **SVG Parsing** — Currently handles basic `<rect>`, `<circle>`, `<path>` elements. Complex SVG features (gradients, transforms, text) are ignored.

2. **DXF Reading** — `dxf_io_legacy.py` uses ezdxf and may not handle all DXF variants. R2018+ files may need conversion.

3. **Saw Bridge** — Uses simplified physics model. Full Saw Lab integration requires the untracked Saw Lab files (76 files in `SAW_LAB_UNTRACKED_FILES_INVENTORY.md`).

4. **Tool Library** — Loads from existing `tool_library.json`. New tools require JSON edits (no CRUD API yet).

---

## 📋 Architectural Decisions (ADRs)

The following decisions were made during Wave 1-6 review:

### ADR-1: MLPath Scope & Evolution

**Decision:** Staged evolution, keep core simple.

| Timeframe | Approach |
|-----------|----------|
| **Short term** | MLPath stays 2D polyline-only + optional metadata (`z_level: float | None`, `tags: set[str]`) |
| **Medium term** | Introduce `Segment` concept (line/arc primitives) as parallel representation; MLPath can wrap segments or stay polyline |
| **Compensation** | Keep inside/outside/on-path at CAM operation level, not on MLPath — geometry is "shape in space," compensation is a planning decision |

**Rationale:** Avoids massive rewrite of everything expecting `list[Point2D]`. Arcs and Z-depth will be introduced through segment-level representation.

---

### ADR-2: DXF Version Strategy

**Decision:** R12 default, configurable export, deferred R2018+ read.

| Aspect | Policy |
|--------|--------|
| **Default** | R12 for all CAM exports (maximum compatibility) |
| **Configurable** | Expose `?version=R14` or `?version=R18` query param for CAD workflows |
| **Reading** | R12/R14 robust read supported; R2018+ files require external conversion (standard practice) |

**Rationale:** "R12 is king" for CAM toolchains. Newer versions are opt-in for users who need specific CAD features.

---

### ADR-3: Saw Bridge Integration Path

**Decision:** `saw_bridge.py` remains the stable façade; delegates to backends.

```python
# Future backend selector pattern
def evaluate_operation_feasibility(..., backend: str = "stub"):
    if backend == "saw_lab_v2":
        from app.saw_lab.calculators import full_physics
        return full_physics.evaluate(...)
    else:
        return _stub_physics(...)
```

**Rationale:** Art Studio, RMOS, and tests only call `evaluate_operation_feasibility()`. Backend can be swapped without breaking callers.

---

### ADR-4: Tool Library CRUD

**Decision:** Read-only JSON now; CRUD and overrides planned for Phase 2.

| Phase | Capability |
|-------|------------|
| **Phase 1 (current)** | Read-only JSON in repo |
| **Phase 2** | Admin CRUD endpoints (`POST/PATCH /api/tooling/tools`) writing to `custom_tools.json` |
| **Phase 2** | User overrides via `~/.luthiers-toolbox/custom_tools.json` merged at load time |
| **Phase 3 (Team mode)** | SQLite/Postgres for multi-user editing, audit trails, versioning |

**Rationale:** Core schema must stabilize before building CRUD; JSON is sufficient for single-user workflows.

---

### ADR-5: Rosette Router Consolidation

**Decision:** `rosette_geometry.py` is the single source of truth; `rosette_router.py` delegates to it.

**Migration plan:**
1. `rosette_geometry.py` owns all ring/petal math
2. `rosette_router.py` handles FastAPI I/O, validation, calls geometry engine
3. No duplicate geometry logic across modules

**Rationale:** Avoid maintaining two geometry engines in parallel.

---

### ADR-6: SVG Ingest Roadmap

**Decision:** Restricted subset now; transforms and groups on roadmap; text-to-path out of scope.

| Feature | Status |
|---------|--------|
| Basic shapes (rect, circle, path) | ✅ Supported |
| Transform matrices | 🔜 Next (flatten to absolute coords) |
| `<g>` group handling | 🔜 Next (recursive traversal) |
| Text-to-path | ❌ Out of scope (require user conversion in Inkscape/Illustrator) |

**Rationale:** Text rendering requires font pipeline; transforms are tractable as a preprocessing pass.

---

### ADR-7: Test Strategy

**Decision:** Flat `tests/` folder with clear naming; 60%+ coverage target for new code.

| Policy | Detail |
|--------|--------|
| **Location** | Keep flat `app/tests/` structure |
| **Naming** | Clear prefixes and docstrings (e.g., `# Wave 2: DXF`) |
| **Markers** | Optional `@pytest.mark.wave2` for selective runs |
| **Coverage** | 60%+ for new subsystems (MLPath, DXF, rosette, saw_bridge, tool_profiles) |
| **Legacy** | Whole-repo coverage can lag; new code held to higher bar |

---

### ADR-8: Breaking Change Policy

**Decision:** Explicit deprecation warnings; API versioning for HTTP routes.

**For Python APIs:**
```python
# DEPRECATED: use app.toolpath.MLPath + rosette_geometry instead
import warnings
warnings.warn("old_function is deprecated, use MLPath", DeprecationWarning)
```

**For HTTP APIs:**
- Option A: Version prefix (`/api/art-studio/v2/rosette/...`)
- Option B: Query param (`?version=2`)
- Document all breaking changes in CHANGELOG.md

**RMOS 2.0 Contract:**
- Treat RMOS 2.0 spec as "v1 contract" for directional workflows
- Breaking changes to feasibility calls require new "profile" or version

---

## 🚀 Next Steps

1. **Commit Wave Changes**
   ```powershell
   git add services/api/app/toolpath/
   git add services/api/app/art_studio/vcarve_router.py
   git add services/api/app/art_studio/relief_router.py
   git add services/api/app/calculators/
   git add services/api/app/data/
   git add services/api/app/tests/test_*.py
   git commit -m "feat: Wave 1-6 structural refactoring - MLPath spine, DXF export, Saw Bridge"
   ```

2. **Commit Saw Lab Files** (76 untracked files)
   - See `SAW_LAB_UNTRACKED_FILES_INVENTORY.md` for full list
   - These integrate with Wave 5's `saw_bridge.py`

3. **Wire UI Components**
   - Connect `SawLabView.vue` to new routers
   - Add VCarve panel to Art Studio

---

## 📚 Related Documentation

| Document | Description |
|----------|-------------|
| `AGENTS.md` | AI agent guidance for codebase navigation |
| `ADAPTIVE_POCKETING_MODULE_L.md` | Module L (L.0-L.3) pocketing system |
| `PATCH_L1_ROBUST_OFFSETTING.md` | Pyclipper-based polygon offsetting |
| `SAW_LAB_UNTRACKED_FILES_INVENTORY.md` | 76 untracked Saw Lab files |
| `ART_STUDIO_QUICKREF.md` | Art Studio component reference |

---

## ✅ Implementation Checklist

| Wave | Component | Status |
|------|-----------|--------|
| 1 | `toolpath/__init__.py` (MLPath) | ✅ |
| 1 | `toolpath/vcarve_toolpath.py` | ✅ |
| 1 | `art_studio/svg_ingest_service.py` | ✅ |
| 1 | `art_studio/vcarve_router.py` | ✅ |
| 2 | `toolpath/dxf_io_legacy.py` | ✅ |
| 2 | `toolpath/dxf_exporter.py` | ✅ |
| 3 | `toolpath/rosette_geometry.py` | ✅ |
| 3 | `toolpath/relief_geometry.py` | ✅ |
| 3 | `art_studio/relief_router.py` | ✅ |
| 4 | `calculators/__init__.py` | ✅ |
| 5 | `calculators/saw_bridge.py` | ✅ |
| 5 | `calculators/tool_profiles.py` | ✅ |
| 6 | `data/__init__.py` | ✅ |
| 6 | `data/tool_library.py` | ✅ |
| — | Router registration in `main.py` | ✅ |
| — | Test files (25 new tests) | ✅ |
| — | Full test suite passing (274) | ✅ |

---

**Author:** AI Assistant (Claude Opus 4.5)  
**Reviewed By:** [Pending]  
**Approved By:** [Pending]
