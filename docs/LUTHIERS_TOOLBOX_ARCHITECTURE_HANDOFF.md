# Luthiers Toolbox Architecture Handoff

**Date:** 2026-05-09  
**Audit Scope:** Full repository  
**Purpose:** Baseline for major architectural reconstruction

---

## 1. Executive Summary

**Luthiers Toolbox** is a CAD/CAM platform for guitar builders. It provides design tools, manufacturing workflows, and CNC G-code generation for stringed instrument construction.

### What the System Does
- Design instrument geometry (bodies, necks, soundholes, bridges, fretboards)
- Generate CAM toolpaths for CNC machining
- Validate manufacturing feasibility via RMOS (Rosette Manufacturing Operations System)
- Export DXF files for CAD software and G-code for CNC machines
- Vectorize blueprint images into usable geometry

### Why Reconstruction is Needed
1. **Fragmented architecture**: 1,405 Python files across 444 directories with overlapping responsibilities
2. **False completions**: 5+ frontend views claim functionality but use `setTimeout()` mocks
3. **Dead code**: Scaffolded systems (FeedbackSystem, TrainingDataCollector, AGE) never called
4. **Duplicate systems**: Two `simulation_consolidated_router.py` files with different content
5. **DXF standard violations**: 83% of DXF generators bypass the `dxf_compat` layer
6. **Missing backend wiring**: 28 G-code generators exist, only 4 frontend views are wired

### Key Numbers

| Metric | Count |
|--------|-------|
| Python files (backend) | 1,405 |
| TypeScript/Vue files (frontend) | 1,395 |
| API routers | 64-70 |
| G-code generators | 28 |
| Frontend views | 183 |
| Pinia stores | 33 |
| Test files | 389 |
| Coverage threshold | 20% |

---

## 2. Repository Map

```
luthiers-toolbox/
├── packages/
│   └── client/                      # Vue 3 + TypeScript frontend
│       └── src/
│           ├── views/               # 183 page views (28 subdirectories)
│           ├── components/          # 480 components (30 subdirectories)
│           ├── composables/         # 42 Vue composition functions
│           ├── stores/              # 33 Pinia state stores
│           ├── sdk/                 # Typed API client layer
│           ├── router/              # 85 routes with lazy loading
│           ├── api/                 # 28 domain API clients
│           └── registry/            # Tool metadata registry
│
├── services/
│   ├── api/                         # FastAPI backend
│   │   └── app/
│   │       ├── routers/             # 45 endpoint handlers
│   │       ├── cam/                 # 45 CAM/toolpath modules
│   │       ├── calculators/         # 66 calculation modules
│   │       ├── generators/          # 16 instrument generators
│   │       ├── rmos/                # 29 manufacturing governance modules
│   │       ├── services/            # 60 business logic services
│   │       ├── schemas/             # 22 Pydantic models
│   │       ├── models/              # 5 SQLAlchemy ORM models
│   │       ├── ai/                  # LLM/Vision integrations
│   │       ├── vision/              # Image segmentation
│   │       ├── art_studio/          # Rosette/inlay generators
│   │       ├── router_registry/     # Manifest-driven router loading
│   │       ├── api_v1/              # Curated stable API (10 modules)
│   │       └── db/                  # Database sessions, migrations
│   │
│   └── blueprint-import/            # Vectorizer service
│       ├── vectorizer_phase3.py     # Main extraction pipeline
│       ├── calibration_integration.py
│       └── phase4/                  # Dimension linking (scaffolded)
│
├── docs/
│   ├── audits/                      # Architecture audits
│   ├── handoffs/                    # Developer handoffs
│   ├── reference/                   # CIRAD wood data, FPL tables
│   └── architecture/                # Design documents
│
├── tests/                           # Agentic contract tests
├── docker-compose.yml               # Development stack
├── CLAUDE.md                        # AI assistant instructions
└── .github/workflows/               # CI/CD pipelines
```

### Key File Annotations

| Path | Purpose |
|------|---------|
| `services/api/app/main.py` | FastAPI entry point, middleware stack, router registration |
| `services/api/app/router_registry/manifest.py` | Declarative router specifications |
| `services/api/app/rmos/mvp_router.py` | Canonical DXF→G-code endpoint |
| `services/api/app/cam/adaptive_core.py` | Core adaptive pocketing algorithm |
| `services/api/app/dxf_compat.py` | Central DXF compatibility layer |
| `packages/client/src/router/index.ts` | Frontend route definitions |
| `packages/client/src/sdk/core/apiFetch.ts` | API fetch wrapper with request ID |
| `CLAUDE.md` | Project conventions and architecture decisions |

---

## 3. System Architecture

### 3.1 Frontend (Vue 3 + TypeScript)

**Technology**: Vue 3.4, Pinia 2.1, Vite 5, TypeScript, Tailwind CSS

**Organization**: Domain-driven (art-studio, cam, rmos, calculators, instruments)

**Key Patterns**:
- Composition API everywhere (`<script setup>`)
- Lazy-loaded routes for code splitting
- Request ID correlation on all API calls
- Pinia stores as single source of truth
- Tool registry for migration tracking

**Entry Points**:
- `main.ts` — App bootstrap, fetch interceptor, auth init
- `App.vue` — Layout shell, CoachBubble, CommandPalette

### 3.2 Backend (FastAPI)

**Technology**: FastAPI, Pydantic, SQLAlchemy, ezdxf, numpy

**Organization**: Functional domains (routers, services, calculators, cam, rmos)

**Key Patterns**:
- Manifest-driven router loading
- Service layer for business logic
- Store pattern for file-based persistence
- Middleware stack for cross-cutting concerns

**Entry Point**: `main.py` (254 lines)
```python
# Startup sequence:
# 1. Load environment
# 2. Create FastAPI app
# 3. Add middleware (RequestId, CORS, Deprecation, Governance)
# 4. Register exception handlers
# 5. Run startup events (safety validation, migrations, observability)
# 6. Load routers via manifest
# 7. Mount API v1 and WebSocket endpoints
```

### 3.3 Vectorizer Pipeline

**Location**: `services/blueprint-import/`

**Purpose**: Convert blueprint images/PDFs to DXF geometry

**Components**:
- `vectorizer_phase3.py` — Main extraction (3,500+ lines)
- `calibration_integration.py` — Scale calibration
- `phase4/dimension_linker.py` — Dimension linking (standalone, not integrated)

**Status**: Partially complete. FeedbackSystem and TrainingDataCollector scaffolded but never called.

### 3.4 RMOS (Manufacturing Governance)

**Location**: `services/api/app/rmos/`

**Purpose**: Manufacturing feasibility, safety gates, audit trail

**Components**:
- `feasibility_scorer.py` — Design score engine (0-100)
- `constraint_profiles.py` — Declarative design rules
- `runs_v2/` — V2 governance-compliant run management
- `safety_router.py` — Manufacturing safety gates

### 3.5 CAM Engine

**Location**: `services/api/app/cam/`

**Purpose**: Generate CNC toolpaths and G-code

**Subsystems**:
- `adaptive_core.py` — Trochoid pocketing
- `binding/` — Binding channel toolpaths
- `drilling/` — Peck cycle generation
- `profiling/` — Perimeter cutting
- `vcarve/` — V-carve engraving
- `neck/` — Neck profile carving

---

## 4. End-to-End Workflow

### Primary Manufacturing Path (Verified Working)

```
User uploads DXF
      ↓
DxfUploadZone (drag-drop, validation)
      ↓
CamParametersForm (tool, feeds, depths)
      ↓
POST /api/rmos/wrap/mvp/dxf-to-grbl
      ↓
ezdxf parsing → LWPOLYLINE extraction
      ↓
adaptive_core.compute_plan() → toolpath generation
      ↓
RMOS artifact creation (run_id, attachments)
      ↓
ToolpathPlayer simulation (DxfToGcodeView only)
      ↓
RiskBadge / WhyPanel (GREEN/YELLOW/RED gates)
      ↓
G-code download (Blob)
```

### Workflow Status Matrix

| Workflow | Entry Point | Real Backend | Simulation | RMOS | Status |
|----------|-------------|--------------|------------|------|--------|
| DxfToGcodeView | `/cam/dxf-to-gcode` | YES | YES | YES | **CANONICAL** |
| QuickCutView | `/quick-cut` | YES | NO | YES | **WORKING** |
| VCarveView | `/art-studio/vcarve` | YES | YES | NO | **WORKING** |
| PocketClearingView | `/cam/pocket` | NO | NO | NO | **FAKE** |
| ContourCuttingView | `/cam/contour` | NO | NO | NO | **FAKE** |
| DrillingView | `/cam/drilling` | NO | NO | NO | **FAKE** |

---

## 5. Core Data Models and Schemas

### Backend Schemas (Pydantic)

| Schema | Location | Purpose |
|--------|----------|---------|
| `PlanIn` | `schemas/adaptive_schemas.py` | Adaptive pocketing input |
| `InstrumentProject` | `schemas/instrument_project.py` | Complete instrument definition |
| `SmartGuitarCam` | `schemas/smart_guitar_cam.py` | Electric guitar CAM specs |
| `RosetteProject` | `schemas/rosette_project.py` | Soundhole design |
| `CamFretSlots` | `schemas/cam_fret_slots.py` | Fret slot specifications |
| `Relief` | `schemas/relief.py` | Relief carving parameters |

### Frontend Types

| Type | Location | Purpose |
|------|----------|---------|
| `ToolEntry` | `registry/toolRegistry.ts` | Tool metadata and status |
| `ApiError` | `sdk/core/apiFetch.ts` | API error wrapper |
| `RunAttachment` | `types/rmos.ts` | RMOS run artifacts |

### File Formats

| Format | Purpose | Generator |
|--------|---------|-----------|
| DXF R12 | Free tier export | `dxf_compat.py` (LINE only) |
| DXF R2000 | Pro tier export | `dxf_compat.py` (LWPOLYLINE) |
| G-code | CNC machine input | Various in `cam/` |
| SVG | Preview rendering | `layered_dxf_writer.py` |

---

## 6. Vectorizer and Geometry Pipeline

### Vectorizer Location

`services/blueprint-import/vectorizer_phase3.py` (3,500+ lines)

### Pipeline Stages

1. **Image preprocessing** — Contrast enhancement, noise reduction
2. **Edge detection** — Canny + dual-pass strategy
3. **Contour extraction** — cv2.findContours()
4. **Classification** — Body, soundhole, bridge, neck regions
5. **Gap closing** — Morphological operations
6. **Scale calibration** — Reference object detection
7. **DXF export** — via ezdxf

### Contour Classification

**Location**: `vectorizer_phase3.py:1181` (FeedbackSystem class)

**Categories**:
- `BODY_OUTLINE` — Main instrument perimeter
- `SOUNDHOLE` — Sound hole aperture
- `BRIDGE` — Bridge placement region
- `NECK` — Neck pocket/tenon
- `BINDING` — Binding channel
- `UNKNOWN` — Unclassified contours

### Radius/Curvature Tools

| Tool | Location | Purpose |
|------|----------|---------|
| `biarc_math.py` | `cam/biarc_math.py` | Circular arc approximation |
| `curvature_profiler.py` | `services/curvature_profiler.py` | Archtop surface profiling |
| `contour_reconstructor.py` | `cam/contour_reconstructor.py` | Repair damaged outlines |
| `outline_reconstructor.py` | `services/outline_reconstructor.py` | DXF outline repair |

### Scaffolded (Not Integrated)

| System | Location | Status |
|--------|----------|--------|
| FeedbackSystem | `vectorizer_phase3.py:1181` | Defined, `submit_correction()` never called |
| TrainingDataCollector | `vectorizer_phase3.py:1273` | Defined, never instantiated |
| AGE Integration | CLAUDE.md documented | 0 lines implemented |
| Phase 4 Dimension Linking | `phase4/dimension_linker.py` | Standalone, not integrated |

---

## 7. Tests and Validation

### Test Locations

| Location | Files | Tests | Purpose |
|----------|-------|-------|---------|
| `services/api/tests/` | 272 | ~4,700 | Primary API tests |
| `services/api/app/tests/` | 34 | ~900 | Unit tests for calculators |
| `services/blueprint-import/tests/` | 12 | ~400 | Vectorizer tests |
| `packages/client/src/**/*.test.ts` | 31 | ~500 | Frontend tests |

### Test Commands

```bash
# Backend tests
cd services/api
pytest tests/ -v

# Specific module
pytest tests/test_soundhole*.py

# With coverage
pytest --cov=app.rmos --cov-report=html

# Frontend tests
cd packages/client
npm run test
```

### Coverage Gaps

1. **Safety modules only**: 20% threshold covers `core.safety`, `rmos.feasibility` only
2. **No E2E workflow tests**: Design→CAM→DXF→G-code path untested end-to-end
3. **Frontend SDK only**: Component tests minimal
4. **4 xfail bugs**: RMOS/Simulation endpoints have known schema mismatches

### Xfail Protected Bugs

| Bug | Location | Issue |
|-----|----------|-------|
| `list_runs_filtered_bug` | `test_rmos_endpoint_smoke.py` | Unexpected keyword arguments |
| `metrics_production_bug` | `test_simulation_endpoint_smoke.py` | Router/schema mismatch |

---

## 8. Build, Run, and Development Commands

### Backend

```bash
cd services/api

# Install
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run dev server
uvicorn app.main:app --reload --port 8010

# Run tests
pytest tests/ -v

# Type check
mypy app/

# Lint
ruff check app/
```

### Frontend

```bash
cd packages/client

# Install
npm install

# Dev server
npm run dev

# Build
npm run build

# Type check
npm run type-check

# Lint
npm run lint

# Test
npm run test
```

### Docker

```bash
# Development
docker-compose up

# Production
docker-compose -f docker-compose.production.yml up
```

---

## 9. Dependency Graph

### Backend Internal Dependencies

```
main.py
  └── router_registry/manifest.py
        └── manifests/*.py (6 domain manifests)
              └── Individual routers
                    └── services/*.py
                          └── calculators/*.py
                          └── cam/*.py

rmos/
  └── feasibility_scorer.py
        └── constraint_profiles.py
  └── runs_v2/
        └── attachments.py
        └── api_runs.py
```

### Frontend Internal Dependencies

```
main.ts
  └── router/index.ts (85 routes)
  └── stores/*.ts (33 Pinia stores)
        └── sdk/endpoints/*.ts
              └── sdk/core/apiFetch.ts

views/*.vue
  └── composables/*.ts (42 composables)
  └── components/*.vue (480 components)
```

### External Dependencies

**Backend** (key packages):
- `fastapi>=0.109` — Web framework
- `pydantic>=2.0` — Data validation
- `ezdxf>=1.0` — DXF file handling
- `numpy>=1.24` — Numerical computation
- `opencv-python>=4.8` — Image processing
- `anthropic>=0.18` — Claude AI
- `openai>=1.12` — OpenAI API

**Frontend** (key packages):
- `vue@3.4` — UI framework
- `pinia@2.1` — State management
- `vite@5` — Build tool
- `@supabase/supabase-js` — Authentication

---

## 10. Architectural Risks and Technical Debt

### Critical Issues

| Issue | Impact | Location |
|-------|--------|----------|
| **Fake frontend views** | Users see non-functional features | `PocketClearingView`, `ContourCuttingView`, `DrillingView`, `SurfacingView` |
| **DXF standard violations** | CAD software compatibility issues | 83% of generators bypass `dxf_compat` |
| **Duplicate routers** | Conflicting endpoints | Two `simulation_consolidated_router.py` files |
| **Dead scaffolded code** | Wasted maintenance effort | FeedbackSystem, TrainingDataCollector, AGE |
| **Missing /api/teaching backend** | 404 errors | Frontend calls endpoint that doesn't exist |

### Technical Debt

| Debt | Severity | Remediation |
|------|----------|-------------|
| 28 generators, 4 wired | HIGH | Wire remaining generators to frontend |
| Vectorizer feedback loops | MEDIUM | Implement FeedbackSystem.submit_correction() |
| /api/cam/sim/metrics broken | MEDIUM | Fix schema mismatch (8 xfail tests) |
| Disabled aggregator routers | LOW | Resolve legacy path conflicts |
| No centralized UI library | LOW | Extract shared components |

### Naming Inconsistencies

- `useRosetteStore` vs `rosetteStore` (store naming)
- `util/` vs `utils/` (both exist)
- `api_v1/` vs domain routers (endpoint organization)

---

## 11. Reconstruction Plan

### Phase 1: Inventory and Stabilization (2-3 weeks)
- [ ] Mark all fake views with "Demo" banners
- [ ] Document all 28 G-code generators with input/output contracts
- [ ] Create endpoint truth map (frontend calls vs backend existence)
- [ ] Remove or fix xfail tests (4 known bugs)

### Phase 2: Schema Normalization (2-3 weeks)
- [ ] Unify Pydantic schemas for CAM operations
- [ ] Standardize G-code generator interface (request schema → string response)
- [ ] Document RMOS run artifact schema

### Phase 3: Subsystem Separation (3-4 weeks)
- [ ] Extract CAM engine as standalone service
- [ ] Separate vectorizer from main API
- [ ] Define clear boundaries: CAM ↔ RMOS ↔ Frontend

### Phase 4: Vectorizer/Geometry Integration (2-3 weeks)
- [ ] Implement FeedbackSystem.submit_correction()
- [ ] Wire TrainingDataCollector
- [ ] Integrate phase4/dimension_linker.py
- [ ] Add scale validation gate

### Phase 5: Test Hardening (2-3 weeks)
- [ ] Add E2E workflow tests (design→CAM→DXF→G-code)
- [ ] Increase coverage beyond safety modules
- [ ] Add component tests for frontend

### Phase 6: Documentation and Handoff (1-2 weeks)
- [ ] Update CLAUDE.md with reconstruction decisions
- [ ] Create API documentation
- [ ] Write deployment runbook

---

## 12. Open Questions

1. **Which simulation router is canonical?** Two files exist with different content:
   - `routers/simulation_consolidated_router.py` (326 lines, has `/metrics`)
   - `cam/routers/simulation/simulation_consolidated_router.py` (143 lines, no `/metrics`)

2. **Should fake views be removed or completed?** PocketClearingView, ContourCuttingView, etc. have real generators available but aren't wired.

3. **What is the AGE integration timeline?** CLAUDE.md documents it as required, but 0 lines exist.

4. **Is the vectorizer FeedbackSystem still needed?** Scaffolded in 2026, never called.

5. **What is the /api/teaching endpoint supposed to do?** Frontend references it, no backend exists.

6. **Should R12 DXF remain the free tier default?** R2000 verified working 2026-04-28.

---

## Appendix A: G-Code Generator Reference

| Generator | Location | Operation | Wired |
|-----------|----------|-----------|-------|
| VCarveToolpathGenerator | `cam/vcarve/toolpath.py` | V-carve | YES |
| ProfileToolpathGenerator | `cam/profiling/profile_toolpath.py` | Perimeter | NO |
| BindingChannelGenerator | `cam/binding/channel_toolpath.py` | Binding | NO |
| DrillingPeckCycleGenerator | `cam/drilling/peck_cycle.py` | Drilling | NO |
| SurfaceCarvingGenerator | `cam/carving/surface_carving.py` | Relief | YES |
| FretSlotGenerator | `cam/neck/fret_slots.py` | Fret slots | PARTIAL |
| LesPaulGCodeGenerator | `generators/lespaul_gcode/generator.py` | Full body | NO |
| AcousticBodyGenerator | `generators/acoustic_body_generator.py` | Acoustic body | NO |

---

## Appendix B: Router Manifest Structure

```python
# router_registry/manifests/cam_manifest.py
CAM_ROUTERS = [
    RouterSpec(
        module="app.cam.routers.drilling",
        prefix="/api/cam/drilling",
        tags=["CAM", "Drilling"],
        required=True,
        category="cam"
    ),
    # ... 14 more
]
```

---

*Document generated: 2026-05-09*  
*Auditor: Claude Opus 4.5*  
*Classification: Reconstruction Baseline*
