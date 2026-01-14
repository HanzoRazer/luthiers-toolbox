# Art Studio System Audit

**Version:** 1.0.0
**Date:** 2026-01-13
**Status:** ~85% Production-Ready (Core), ~60% Experimental Features

---

## Executive Summary

The Art Studio system is **substantially complete** for its primary mission of parametric design generation. Core workflows (rosette, bracing, inlay) are production-ready with good test coverage. The remaining gaps are workflow integration polish and experimental AI-powered features.

---

## 1. Architecture Overview

### Design-First Principle (Critical Constraint)

Art Studio is the **design authority only**. It does NOT generate G-code or CAM artifacts.

```
┌─────────────────────────────────────────┐
│         Art Studio (Design)              │
│  - Pattern generation                    │
│  - Feasibility preview                   │
│  - Snapshot management                   │
└────────────┬────────────────────────────┘
             │ RosetteParamSpec (canonical)
             ▼
┌─────────────────────────────────────────┐
│    Workflow State Machine (Governance)   │
│  - Session management                    │
│  - Approval workflow                     │
│  - Risk assessment (RMOS)                │
└────────────┬────────────────────────────┘
             │ Approved design
             ▼
┌─────────────────────────────────────────┐
│        CAM Layer (Execution)             │
│  - G-code generation                     │
│  - Toolpath optimization                 │
└─────────────────────────────────────────┘
```

### Separation of Concerns

| Layer | Responsibility | NOT Responsible For |
|-------|----------------|---------------------|
| Art Studio | Design entry, preview, snapshots | G-code, machine execution |
| Workflow | Approval, risk assessment | Design creation |
| CAM | Toolpath generation, G-code | Design decisions |

---

## 2. Backend Structure

### Directory Layout

```
services/api/app/art_studio/
├── __init__.py
├── api/                              # Route layer (Bundle 31.0+)
│   ├── generator_routes.py           ✅ Complete
│   ├── pattern_routes.py             ✅ Complete
│   ├── preview_routes.py             ✅ Complete
│   ├── snapshot_routes.py            ✅ Complete
│   ├── workflow_routes.py            ⚠️ Partial wiring
│   ├── rosette_jobs_routes.py        ✅ Complete
│   ├── rosette_compare_routes.py     ✅ Complete
│   ├── rosette_pattern_routes.py     ✅ Complete
│   └── rosette_feasibility_routes.py ✅ Complete
├── schemas/                          # Pydantic models
│   ├── design_snapshot.py
│   ├── generator_requests.py
│   ├── pattern_library.py
│   ├── preview.py
│   ├── rosette_feasibility.py
│   ├── rosette_params.py             # Canonical RosetteParamSpec
│   ├── rosette_snapshot.py
│   └── snapshot_meta.py
├── services/                         # Business logic
│   ├── design_snapshot_store.py      ✅ JSON persistence
│   ├── pattern_store.py              ✅ Pattern library CRUD
│   ├── rosette_feasibility_scorer.py ✅ RMOS integration
│   ├── rosette_preview_renderer.py   ✅ SVG rendering
│   ├── rosette_snapshot_store.py     ✅ Snapshot persistence
│   ├── workflow_integration.py       ⚠️ Partial
│   └── generators/
│       ├── registry.py               ✅ Generator dispatch
│       ├── basic_rings.py            ✅ v1 generator
│       └── mosaic_band.py            ✅ v1 generator
├── svg/                              # AI-powered SVG (experimental)
│   ├── generator.py                  ⚠️ Incomplete
│   └── styles.py
├── routers/                          # Classic calculators
│   ├── rosette_router.py             ✅ Complete
│   ├── bracing_router.py             ✅ Complete
│   ├── inlay_router.py               ✅ Complete
│   ├── vcarve_router.py              🟡 Preview only
│   └── relief_router.py              🟡 Preview only
└── prompts/                          # CNC design system
    ├── modes.py
    ├── validators.py
    └── cnc_prompt_pack.json
```

---

## 3. Component Status

### Tier 1: Production-Ready

| Component | Location | Features |
|-----------|----------|----------|
| **Rosette Calculator** | `routers/rosette_router.py` | Channel math, SVG preview, DXF export |
| **Bracing Calculator** | `routers/bracing_router.py` | 4 profiles (rectangular, triangular, parabolic, scalloped), mass calc |
| **Inlay Generator** | `routers/inlay_router.py` | Dots, diamonds, blocks, side dots, 12th fret doubles |
| **Snapshot Management** | `api/snapshot_routes.py` | Save/load/export/import with feasibility |
| **Pattern Library** | `api/pattern_routes.py` | CRUD, filtering, tagging |
| **Generator Registry** | `services/generators/registry.py` | Versioned generators, extensible |
| **Feasibility Scoring** | `services/rosette_feasibility_scorer.py` | RMOS integration, batch evaluation |
| **DXF Export** | Multiple routers | R12-R18 version support |
| **Rosette Jobs** | `api/rosette_jobs_routes.py` | SQLite persistence, comparison |

### Tier 2: Functional with Gaps

| Component | Status | Gap |
|-----------|--------|-----|
| **Workflow Integration** | 80% | State machine binding incomplete |
| **Rosette Pattern Engine** | 90% | Graceful degradation if generator unavailable |
| **CNC Prompt System** | 70% | Prompt→SVG experimental |

### Tier 3: Preview-Only (By Design)

| Component | Status | Rationale |
|-----------|--------|-----------|
| **VCarve Router** | Preview only | G-code generation in CAM layer |
| **Relief Router** | Preview only | DXF export in CAM layer |

### Tier 4: Experimental

| Component | Status | Notes |
|-----------|--------|-------|
| **AI-Powered SVG** | Exploratory | Architecture exists, integration incomplete |

---

## 4. API Endpoints

### Generators (`/api/art/generators`)

| Endpoint | Method | Status |
|----------|--------|--------|
| `/` | GET | ✅ List generators with param hints |
| `/{generator_key}/generate` | POST | ✅ Generate RosetteParamSpec |

**Available Generators:**
- `basic_rings@1` - Concentric rings with auto-fill
- `mosaic_band@1` - Banded mosaic with accent rings

### Pattern Library (`/api/art/patterns`)

| Endpoint | Method | Status |
|----------|--------|--------|
| `/` | GET | ✅ List patterns (q, tag, generator_key filters) |
| `/` | POST | ✅ Create pattern |
| `/{pattern_id}` | GET | ✅ Get pattern |
| `/{pattern_id}` | PUT | ✅ Update pattern |
| `/{pattern_id}` | DELETE | ✅ Delete pattern |

### Snapshots (`/api/art/snapshots`)

| Endpoint | Method | Status |
|----------|--------|--------|
| `/` | POST | ✅ Create snapshot |
| `/recent` | GET | ✅ List recent with filtering |
| `/{snapshot_id}` | GET | ✅ Get snapshot |
| `/{snapshot_id}` | PUT | ✅ Update snapshot |
| `/{snapshot_id}` | DELETE | ✅ Delete snapshot |
| `/{snapshot_id}/baseline` | POST | ✅ Mark as baseline |

### Workflow (`/api/art-studio/workflow`)

| Endpoint | Method | Status |
|----------|--------|--------|
| `/from-pattern` | POST | ⚠️ Partial |
| `/from-generator` | POST | ⚠️ Partial |
| `/from-snapshot` | POST | ⚠️ Partial |
| `/sessions` | GET | ⚠️ Partial |
| `/sessions/{id}` | GET | ⚠️ Partial |
| `/sessions/{id}/design` | PUT | ⚠️ Partial |
| `/sessions/{id}/feasibility` | POST | ⚠️ Partial |
| `/sessions/{id}/approve` | POST | ⚠️ Partial |
| `/sessions/{id}/reject` | POST | ⚠️ Partial |
| `/sessions/{id}/request-revision` | POST | ⚠️ Partial |
| `/sessions/{id}/save-snapshot` | POST | ⚠️ Partial |
| `/generators` | GET | ⚠️ Partial |

### Rosette Jobs (`/api/art/rosette`)

| Endpoint | Method | Status |
|----------|--------|--------|
| `/preview` | POST | ✅ Generate geometry preview |
| `/save` | POST | ✅ Save job |
| `/jobs` | GET | ✅ List saved jobs |
| `/presets` | GET | ✅ List presets |

### Rosette Compare (`/api/art/rosette/compare`)

| Endpoint | Method | Status |
|----------|--------|--------|
| `/` | POST | ✅ Compare two jobs |
| `/snapshot` | POST | ✅ Save comparison |
| `/snapshots` | GET | ✅ List comparisons |
| `/export_csv` | GET | ✅ Export as CSV |

### Rosette Patterns (`/api/art/rosette/pattern`)

| Endpoint | Method | Status |
|----------|--------|--------|
| `/status` | GET | ✅ Generator availability |
| `/patterns` | GET | ✅ List preset patterns |
| `/patterns/{id}` | GET | ✅ Get pattern details |
| `/generate_traditional` | POST | ✅ Traditional matrix method |
| `/generate_modern` | POST | ✅ Modern parametric method |
| `/export` | POST | ✅ Export various formats |

### Classic Calculators

| Endpoint | Method | Status |
|----------|--------|--------|
| `/api/art-studio/rosette/preview` | POST | ✅ Channel calculation |
| `/api/art-studio/rosette/export-dxf` | POST | ✅ DXF export |
| `/api/art-studio/bracing/preview` | POST | ✅ Section properties |
| `/api/art-studio/bracing/batch` | POST | ✅ Batch calculation |
| `/api/art-studio/bracing/export-dxf` | POST | ✅ DXF export |
| `/api/art-studio/inlay/preview` | POST | ✅ Pattern calculation |
| `/api/art-studio/inlay/export-dxf` | POST | ✅ DXF export |

---

## 5. Data Models

### RosetteParamSpec (Canonical)

```python
class RosetteParamSpec:
    outer_diameter_mm: float
    inner_diameter_mm: float
    ring_params: List[RingParam]  # Inner → outer
```

### RingParam

```python
class RingParam:
    ring_index: int
    width_mm: float
    pattern_type: str  # SOLID, MOSAIC, HATCH, DOTS, STIPPLE
    tile_length_mm: Optional[float]
```

### DesignSnapshot

```python
class DesignSnapshot:
    snapshot_id: str
    name: str
    notes: str
    tags: List[str]
    pattern_id: Optional[str]
    context_refs: Dict  # material/tool/machine
    rosette_params: RosetteParamSpec
    feasibility: FeasibilitySummary
    created_at: datetime
    updated_at: datetime
```

### PatternRecord

```python
class PatternRecord:
    pattern_id: str
    name: str
    description: str
    generator_key: str  # "basic_rings@1"
    params: Dict
    tags: List[str]
    created_at: datetime
```

---

## 6. Integration Points

### RMOS Integration

- **Service:** `rosette_feasibility_scorer.py`
- **Function:** Wraps `rmos.feasibility_scorer.score_design_feasibility()`
- **Output:** Risk bucket (GREEN/YELLOW/RED) + warnings
- **Persistence:** RunArtifact via `art_studio_run_service.py`

### CAM Integration

- **Boundary:** Art Studio = design only, CAM = execution only
- **VCarve:** Preview in Art Studio → G-code in `/api/cam/toolpath/vcarve/gcode`
- **Relief:** Preview in Art Studio → DXF in `/api/cam/toolpath/relief/export-dxf`

### AI Platform Integration (Experimental)

- **Location:** `svg/generator.py`
- **Providers:** DALL-E, Stable Diffusion, Stub
- **Function:** Text/image → SVG via prompt engineering + vectorization

---

## 7. Test Coverage

| Test File | Components | Status |
|-----------|-----------|--------|
| `test_art_studio_rosette.py` | Rosette calc + router | ✅ Good |
| `test_art_studio_bracing.py` | Bracing calc + router | ✅ Good |
| `test_art_studio_inlay.py` | Inlay calc + router | ✅ Complete |
| `test_art_studio_scope_gate.py` | Scope boundaries | ✅ Complete |
| `test_art_studio_rosette_compare.py` | Comparison logic | ✅ Complete |
| `test_art_presets.py` | Preset CRUD | ✅ Complete |
| `test_art_namespace.py` | Namespace isolation | ✅ Complete |

**Coverage Assessment:**
- ✅ Unit tests: Good
- ✅ Integration tests: Good
- ⚠️ E2E tests: Incomplete
- ⚠️ AI/SVG tests: Missing

---

## 8. Frontend Components

| Component | Location | Status |
|-----------|----------|--------|
| ArtStudio.vue | `client/src/views/` | ✅ Exists |
| ArtStudioRosette.vue | `client/src/views/` | ✅ Exists |
| RosetteDesigner.vue | `client/src/views/` | ✅ Exists |
| BracingCalculator.vue | `client/src/views/` | ✅ Exists |
| RosetteCanvas.vue | `client/src/components/` | ✅ Exists |
| RosetteComparePanel.vue | `client/src/components/` | ✅ Exists |
| ArtPresetSelector.vue | `client/src/components/` | ✅ Exists |

**Note:** Multiple component versions exist (ArtStudioV16.vue, etc.) - consolidation recommended.

---

## 9. Identified Gaps

### Gap 1: Workflow State Machine Binding

**Issue:** `workflow_routes.py` endpoints defined but not fully wired to state machine
**Impact:** Design→approval→CAM flow incomplete
**Effort:** 6 hours
**Priority:** HIGH

### Gap 2: AI-Powered SVG Generation

**Issue:** `svg/generator.py` architecture exists but AI provider integration incomplete
**Impact:** Text→design generation not working end-to-end
**Effort:** 8-12 hours
**Priority:** MEDIUM (experimental feature)

### Gap 3: CAM Promotion Path

**Issue:** No exposed API to promote snapshots directly to CAM execution
**Impact:** Manual handoff required between design and manufacturing
**Effort:** 4 hours
**Priority:** HIGH

### Gap 4: Frontend Component Consolidation

**Issue:** Multiple Vue component versions without clear canonical choice
**Impact:** Maintenance overhead, unclear which to use
**Effort:** 4 hours
**Priority:** MEDIUM

### Gap 5: Custom Generator UI

**Issue:** Generator registry exists but no UI for creating custom generators
**Impact:** Users cannot extend pattern types without code changes
**Effort:** 6 hours
**Priority:** LOW

---

## 10. Path to Full Completion

### Phase 1: Core Completion (~15 hours)

| Task | Hours | Outcome |
|------|-------|---------|
| Complete workflow state machine binding | 6h | Full design→approval→CAM flow |
| Expose CAM promotion API | 4h | Snapshots trigger CAM execution |
| Consolidate frontend components | 3h | Single canonical ArtStudio.vue |
| Document generator extension pattern | 2h | Custom pattern creation guide |

### Phase 2: Experimental Features (~15 hours)

| Task | Hours | Outcome |
|------|-------|---------|
| Complete AI platform integration | 8h | Text→SVG generation works |
| Add custom generator UI | 5h | Users create new pattern types |
| E2E test coverage | 2h | Frontend-backend integration tests |

---

## 11. Summary

**Art Studio is 85% complete for production use.**

### What Works

- ✅ Parametric design generation (rosette, bracing, inlay)
- ✅ Feasibility preview and risk assessment (RMOS)
- ✅ Snapshot management and design history
- ✅ Pattern library with versioned generators
- ✅ Export to DXF (R12-R18)
- ✅ SVG preview rendering
- ✅ Job tracking and comparison
- ✅ Good test coverage

### What's Missing

- ⚠️ Workflow state machine completion (design→CAM bridge)
- ⚠️ AI-powered SVG generation (experimental)
- ⚠️ Custom generator UI
- ⚠️ Frontend consolidation

### Comparison to CAM System

| Aspect | Art Studio | CAM System |
|--------|------------|------------|
| Core Algorithms | ✅ Complete | ✅ Complete |
| Persistence | ✅ Complete | ❌ Missing |
| User Infrastructure | ✅ 85% | ❌ 62% |
| Test Coverage | ✅ Good | ⚠️ Gaps |
| Hours to MVP | ~30h | ~50h |

**Art Studio is closer to MVP than CAM. The remaining work is integration polish, not fundamental infrastructure.**

---

*Document generated as part of luthiers-toolbox system audit.*
