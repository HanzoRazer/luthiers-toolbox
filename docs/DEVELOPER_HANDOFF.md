# Developer Handoff: Luthiers-ToolBox Repository

**Version:** 1.9.0
**Date:** 2026-01-16
**Purpose:** Guide a developer into assuming work on the ToolBox repository

---

## Table of Contents

1. [Repository Overview](#1-repository-overview)
2. [Architecture Summary](#2-architecture-summary)
3. [Governance & Contracts](#3-governance--contracts)
4. [Cost Attribution System](#4-cost-attribution-system)
5. [Calculator Suite](#5-calculator-suite)
6. [CI/CD Pipeline](#6-cicd-pipeline)
7. [Key File Reference](#7-key-file-reference)
8. [Quick Start Commands](#8-quick-start-commands)
9. [Gaps & Future Work](#9-gaps--future-work)
10. [CAM System Analysis](#10-cam-system-analysis)
11. [Wave 18 Migration - Duplicate Paths](#11-wave-18-migration---duplicate-paths)
12. [Path to MVP](#12-path-to-mvp)
13. [Art Studio System Analysis](#13-art-studio-system-analysis)
14. [Blueprint Reader System Analysis](#14-blueprint-reader-system-analysis)
15. [RMOS System Analysis](#15-rmos-system-analysis)
16. [CNC Saw Lab System Analysis](#16-cnc-saw-lab-system-analysis)
17. [AI System Analysis](#17-ai-system-analysis)

---

## 1. Repository Overview

**Luthiers-ToolBox** is a monorepo containing:
- **API Service** (`services/api/`) - FastAPI backend for CAM operations, calculators, telemetry
- **Client** (`client/` and `packages/client/`) - Vue.js 3D visualization frontend
- **Contracts** (`contracts/`) - JSON schemas for cross-repo governance
- **Scripts** (`scripts/`) - CI gates, validation, and automation

### Related Repositories

| Repository | Purpose | Relationship |
|------------|---------|--------------|
| `luthiers-toolbox` | Manufacturing operations | Primary (this repo) |
| `sg-spec` | Smart Guitar consumer spec | Receives safe exports, sends telemetry |

---

## 2. Architecture Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                        LUTHIERS-TOOLBOX                         │
├─────────────────────────────────────────────────────────────────┤
│  Frontend (Vue.js)                                              │
│  ├── 3D Viewer (Three.js)                                       │
│  ├── Calculator UI                                              │
│  └── CAM Operation Interface                                    │
├─────────────────────────────────────────────────────────────────┤
│  API (FastAPI)                                                  │
│  ├── /api/calculators/* - Math & business calculators           │
│  ├── /api/telemetry/*   - Smart Guitar telemetry ingestion      │
│  ├── /api/cost/*        - Cost attribution summaries            │
│  ├── /api/cam/*         - CAM operations & toolpaths            │
│  └── /api/geometry/*    - Geometry parity checking              │
├─────────────────────────────────────────────────────────────────┤
│  Contracts (JSON Schema)                                        │
│  ├── Telemetry contract (SG → ToolBox)                          │
│  ├── Safe export contract (ToolBox → SG)                        │
│  └── Internal policies (cost attribution, viewer pack)          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Governance & Contracts

### Overview

Cross-repository governance ensures:
- **Manufacturing secrets** stay in luthiers-toolbox
- **Consumer-safe content** flows to sg-spec
- **Telemetry** flows from sg-spec without player/pedagogy data

### Key Documents

| Document | Location | Purpose |
|----------|----------|---------|
| Governance Summary | `docs/GOVERNANCE_EXECUTIVE_SUMMARY.md` | Master governance doc (v1.4.0) |
| Telemetry Audit | `docs/TELEMETRY_SYSTEM_AUDIT.md` | SG → ToolBox data flow |
| Safe Export Audit | `docs/SAFE_EXPORT_SYSTEM_AUDIT.md` | ToolBox → SG data flow |

### Contracts Structure

```
contracts/
├── smart_guitar_toolbox_telemetry_v1.schema.json    # Telemetry ingest
├── smart_guitar_toolbox_telemetry_v1.schema.sha256
├── toolbox_smart_guitar_safe_export_v1.schema.json  # Safe export
├── toolbox_smart_guitar_safe_export_v1.schema.sha256
├── telemetry_cost_mapping_policy_v1.json            # Cost attribution
├── viewer_pack_v1.schema.json                       # Viewer pack format
├── viewer_pack_v1.schema.sha256
├── CONTRACTS_VERSION.json                           # Immutability sentinel
└── CHANGELOG.md                                     # Required for changes
```

### Telemetry Contract - Forbidden Fields (22)

These fields are **blocked** from flowing SG → ToolBox:

| Category | Forbidden Fields |
|----------|------------------|
| Player Data | player_id, player_profile, player_preferences |
| Lesson Data | lesson_id, lesson_progress, lesson_score |
| Practice Data | practice_session_id, practice_duration, practice_notes |
| Performance Data | accuracy_percent, timing_deviation_ms, chord_accuracy |
| Recording Data | audio_recording, midi_recording, recording_metadata |
| Coach Data | coach_feedback, coach_prompt, coach_response |
| Pedagogical Data | skill_level, learning_path, achievement_badges |

### Safe Export Contract - Forbidden Content

| Type | Forbidden Values |
|------|------------------|
| Extensions (17) | .nc, .gcode, .tap, .ngc, .cnc, .iso, .mpf, .dnc, .eia, etc. |
| Kinds (7) | cam_toolpath, machine_config, post_processor, etc. |

### Governance CI Gate

The **Scenario B Gate** enforces changelog documentation for contract changes:

```bash
# CI runs this on every PR
python scripts/ci/check_contracts_governance.py --base-ref origin/main
```

Key behaviors:
- Scans only **added lines** in CHANGELOG.md (not deleted)
- Uses **regex word boundaries** to prevent partial matches
- Requires explicit documentation of any schema changes

---

## 4. Cost Attribution System

### Purpose

Maps validated telemetry to manufacturing cost dimensions for internal analysis.

### Data Flow

```
Telemetry Ingest → Cost Mapper → Cost Store → Summary API
       │                │              │            │
       │                │              │            └── GET /api/cost/summary
       │                │              └── JSONL by date
       │                └── telemetry_cost_mapping_policy_v1.json
       └── POST /api/telemetry/ingest
```

### Cost Dimensions

| Dimension | Source Metric | Unit |
|-----------|---------------|------|
| compute_cost_hours | hardware_performance.cpu_hours | hours |
| energy_amp_hours | hardware_performance.amp_draw_avg | amp-hours |
| thermal_stress_c | hardware_performance.temp_c_max | celsius |
| wear_cycles | lifecycle.power_cycles | count |

### Module Structure

```
services/api/app/cost_attribution/
├── __init__.py     # Public exports
├── models.py       # CostFact dataclass, CostDimension literal
├── policy.py       # Load/cache mapping policy
├── mapper.py       # telemetry_to_cost_facts()
├── store.py        # JSONL storage, summarize functions
└── api.py          # FastAPI router (/api/cost/*)
```

### Key Integration Point

Cost attribution hooks into telemetry ingestion at `services/api/app/smart_guitar_telemetry/api.py`:

```python
# Lines 191-211 - Non-fatal cost attribution hook
try:
    cost_facts, cost_warnings = telemetry_to_cost_facts(_repo_root(), payload_dict)
    if cost_facts:
        append_cost_facts(_repo_root(), cost_facts)
except Exception as e:
    _log.warning("Cost attribution failed (non-fatal): %s", e)
```

---

## 5. Calculator Suite

### Categories

| Category | Modules | Status |
|----------|---------|--------|
| **General Purpose** | basic, scientific, fraction, financial | Production |
| **Woodworking** | board feet, wedge, miter, dovetail | Production |
| **Instrument Construction** | fret, radius, bracing, rosette, inlay | Production |
| **CAM/Machining** | chipload, heat, deflection, saw adapters | Production |
| **Business** | ROI, amortization, throughput | Backend Only |
| **Electronics** | wiring | Development |

**Overall Readiness: 85% Production-Ready**

### File Structure

```
services/api/app/calculators/
├── service.py                    # Main CalculatorService facade (590 lines)
├── bracing_calc.py               # Guitar brace physics
├── rosette_calc.py               # Sound hole patterns
├── inlay_calc.py                 # Fretboard inlay patterns
├── alternative_temperaments.py   # Non-equal tuning systems
├── fret_slots_cam.py             # Fret slot toolpaths (31KB)
├── suite/
│   ├── basic_calculator.py
│   ├── scientific_calculator.py
│   ├── fraction_calculator.py
│   ├── financial_calculator.py
│   └── luthier_calculator.py
├── business/                     # NOT exposed via REST API
│   ├── roi.py
│   ├── amortization.py
│   └── machine_throughput.py
└── saw/                          # Saw blade physics adapters
```

### API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /api/calculators/evaluate` | Math expression evaluation |
| `POST /api/calculators/tvm` | Time Value of Money solver |
| `POST /api/calculators/fret-positions` | Fret slot positions |
| `POST /api/calculators/board-feet` | Lumber volume calculation |
| `POST /api/calculators/string-tension` | String physics |
| `POST /calculators/evaluate` | CAM cut operation evaluation |

### Gap: Business Calculators

The business calculators (`roi.py`, `amortization.py`, `machine_throughput.py`) are:
- Fully implemented with business logic
- Have unit tests
- **NOT exposed via REST API**

This is a potential enhancement opportunity.

---

## 6. CI/CD Pipeline

### Primary Workflow: `.github/workflows/core_ci.yml`

```yaml
jobs:
  api-tests:
    - Art Studio Scope Gate
    - Viewer Pack Schema Parity Gate
    - CONTRACTS_GOVERNANCE_SCENARIO_B_GATE    # Key governance gate
    - Governance Unit Tests (stem_mentioned)  # 25 tests
    - Cost Attribution Unit Tests             # 10 tests
    - Boot API + pytest

  geometry-parity:
    - Geometry parity check (G-code vs paths)

  containers-smoke:
    - Docker build (API, Client, Nginx)
    - Stack health check via proxy
```

### Key CI Scripts

| Script | Purpose |
|--------|---------|
| `scripts/ci/check_contracts_governance.py` | Scenario B gate |
| `scripts/ci/test_check_contracts_governance.py` | 25 stem tests |
| `scripts/ci/check_art_studio_scope.py` | Art studio boundary |
| `scripts/validate/check_viewer_pack_schema_parity.py` | Schema parity |

### Running Tests Locally

```bash
# Governance unit tests (25 tests)
python -m pytest scripts/ci/test_check_contracts_governance.py -v

# Cost attribution tests (10 tests)
cd services/api
python -m pytest tests/test_cost_attribution_mapper_unit.py -v

# Full API test suite
cd services/api
python -m pytest -q

# Business calculator tests
python -m pytest services/api/app/tests/calculators/test_business.py -v
```

---

## 7. Key File Reference

### Governance & Contracts

| File | Purpose |
|------|---------|
| `docs/GOVERNANCE_EXECUTIVE_SUMMARY.md` | Master governance doc |
| `docs/TELEMETRY_SYSTEM_AUDIT.md` | Telemetry deep dive |
| `docs/SAFE_EXPORT_SYSTEM_AUDIT.md` | Safe export deep dive |
| `contracts/CONTRACTS_VERSION.json` | Schema immutability sentinel |
| `contracts/CHANGELOG.md` | Required for schema changes |

### Cost Attribution

| File | Purpose |
|------|---------|
| `contracts/telemetry_cost_mapping_policy_v1.json` | Mapping policy |
| `services/api/app/cost_attribution/models.py` | CostFact dataclass |
| `services/api/app/cost_attribution/mapper.py` | Mapping logic |
| `services/api/app/cost_attribution/api.py` | REST endpoints |
| `services/api/tests/test_cost_attribution_mapper_unit.py` | 10 unit tests |

### CI/CD

| File | Purpose |
|------|---------|
| `.github/workflows/core_ci.yml` | Main CI workflow |
| `scripts/ci/check_contracts_governance.py` | Scenario B gate |
| `scripts/ci/test_check_contracts_governance.py` | Stem tests |

### Calculator Suite

| File | Purpose |
|------|---------|
| `services/api/app/calculators/service.py` | Main facade |
| `services/api/app/routers/ltb_calculator_router.py` | REST routes |
| `services/api/app/calculators/business/` | Business calcs (no API) |

---

## 8. Quick Start Commands

### Environment Setup

```bash
# Clone repository
git clone https://github.com/HanzoRazer/luthiers-toolbox
cd luthiers-toolbox

# Python environment
python -m venv .venv
.venv/Scripts/activate  # Windows
source .venv/bin/activate  # Linux/Mac
pip install -r services/api/requirements.txt

# Start API
cd services/api
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Docker Stack

```bash
# Create .env file
cat > .env <<EOF
SERVER_PORT=8000
CLIENT_PORT=8080
FRONT_PORT=8088
CORS_ORIGINS=http://localhost:8088
COMPOSE_PROJECT_NAME=toolbox
EOF

# Build and start
docker compose --profile proxy up -d

# Health check
curl http://127.0.0.1:8088/api/health
```

### SHA256 Verification

```bash
# PowerShell
Get-ChildItem contracts/*.schema.json | ForEach-Object {
  $hash = (Get-FileHash $_ -Algorithm SHA256).Hash.ToLower()
  $expected = Get-Content ($_.FullName -replace '\.json$','.sha256')
  if ($hash -eq $expected) { "OK: $($_.Name)" } else { "FAIL: $($_.Name)" }
}

# Bash
for f in contracts/*.schema.json; do
  sha=$(sha256sum "$f" | cut -d' ' -f1)
  expected=$(cat "${f%.json}.sha256")
  [ "$sha" = "$expected" ] && echo "OK: $f" || echo "FAIL: $f"
done
```

---

## 9. Gaps & Future Work

### Identified Gaps

| Gap | Severity | Effort |
|-----|----------|--------|
| Business calculators not exposed via REST | Medium | 2-3 hours |
| Electronics/wiring calculator incomplete | Low | TBD |
| No dedicated calculator suite documentation | Low | 1-2 hours |

### Potential Enhancements

1. **Expose Business Calculators via REST API**
   - Create `services/api/app/routers/business_calculator_router.py`
   - Add endpoints for ROI, amortization, throughput
   - Register router in `main.py`

2. **Complete Electronics Calculator**
   - Finish wiring resistance calculations
   - Add pickup configuration analysis

3. **Calculator Suite Documentation**
   - Create `docs/CALCULATOR_SUITE_AUDIT.md`
   - Document all calculator APIs
   - Add usage examples

---

## Recent Commits Reference

| Commit | Description |
|--------|-------------|
| `3ef0c3d` | Stem check tightening (added lines only, word boundaries) |
| `81967dd` | 25 unit tests for stem_mentioned regex |
| `fe48e9c` | Cost attribution bundle (695 lines) |
| `72da081` | Cost attribution tests added to CI |
| `c276e2c` | Cost attribution docs in governance summary |

---

## 10. CAM System Analysis

### Overall Status: ~62% Functional

The CAM system has solid infrastructure but lacks critical supporting systems for production use.

**Full audit document with implementation code:** `docs/CAM_SYSTEM_AUDIT.md`

The CAM audit includes:
- Complete code examples for implementing feeds & speeds calculator
- Collision detection module with working Python code
- Job persistence enhancement patterns
- Tool library importer implementations
- Test file templates
- File-by-file implementation checklist

### What's Working Well

| Component | Coverage | Notes |
|-----------|----------|-------|
| Geometry Router | 73% | DXF/SVG import, export, parity |
| Drilling Operations | Complete | G81/G83 cycles work |
| Roughing/Biarc/VCarve | 65-100% | Core toolpath generation |
| Adaptive Pocketing | 65% | L.1 implementation |
| G-code Simulation | 80% | Parsing, thermal analysis |
| Post-processors | 80% | GRBL, LinuxCNC, Mach3, Fanuc, Heidenhain |

### Critical MVP Gaps (Ranked by Impact)

| Gap | Status | Why Critical | Effort |
|-----|--------|--------------|--------|
| **Feed & Speed Calculator** | STUB ONLY | Users can't generate safe cutting params | 4 days |
| **3D Toolpath Visualization** | MISSING | Only 2D backplot exists; can't verify clearances | 5 days |
| **Job Persistence** | MISSING | Work lost on refresh; no save/load | 4 days |
| **Collision Detection** | MISSING | No warning before spindle/table crashes | 3 days |
| **Tool & Material Libraries** | HARDCODED | Not scalable; defaults only | 3 days |

### Backend Files Requiring Work

```
services/api/app/cam_core/feeds_speeds/
├── calculator.py         [STUB] - returns placeholders
├── materials.py          [INCOMPLETE] - basic profiles only
├── presets.py            [SKELETON] - no actual values
└── chipload_db.py        [MISSING] - needs creation

services/api/app/models/
└── cam_job.py            [MISSING] - no persistence layer

services/api/app/routers/
└── cam_jobs_router.py    [MISSING] - no CRUD endpoints
```

### Frontend Files Requiring Work

```
client/src/components/cam/
├── CamBackplotViewer.vue  [2D ONLY] - needs Three.js 3D integration
├── Cam3DPreview.vue       [MISSING]
└── (existing components are monitoring only)

client/src/views/cam/
├── JobCreate.vue          [MISSING]
└── JobList.vue            [MISSING]

client/src/api/
├── feeds.ts               [MISSING]
├── tools.ts               [MISSING]
└── materials.ts           [MISSING]
```

### Missing API Endpoints

```
POST /api/cam/jobs/               # Create job
GET  /api/cam/jobs/{job_id}       # Fetch job
GET  /api/cam/tools/              # Tool library
POST /api/cam/materials/lookup    # Material properties
POST /api/cam/utility/feed-lookup # Feed/speed calculation
```

### Recommended MVP Focus (~25 hours)

| Task | Hours | Files |
|------|-------|-------|
| Implement feed/speed calculator | 8h | `cam_core/feeds_speeds/` |
| Add Three.js 3D preview | 8h | `CamBackplotViewer.vue` |
| Create job persistence layer | 4h | `models/cam_job.py`, router |
| Add job create/list UI | 4h | Vue views |
| Basic collision detection | 3h | `sim_validate.py` |

---

## 11. Wave 18 Migration - Duplicate Paths

### Overview

The codebase has a **Wave 18 migration in progress** where CAM endpoints are being consolidated from legacy flat paths to a hierarchical structure. During this transition, some endpoints exist at **both** old and new paths.

### Duplicate Path Summary

| Operation | Legacy Path | Consolidated Path | Status |
|-----------|-------------|-------------------|--------|
| V-Carve | `/api/cam/vcarve/*` | `/api/cam/toolpath/vcarve/*` | **DUPLICATE** |
| Helical | `/api/cam/helical/*` | `/api/cam/toolpath/helical_entry` | **DUPLICATE** |
| Relief | `/api/cam/relief/*` | `/api/cam/relief/*` (proxy) | **PROXY** |
| Roughing | `/api/cam/roughing/*` | `/api/cam/toolpath/roughing/*` | **DUPLICATE** |
| Fret Slots | `/api/cam/fret_slots/*` | `/api/cam/fret_slots/*` (proxy) | **PROXY** |
| SVG Export | `/api/cam/svg/*` | `/api/cam/export/*` | **DUPLICATE** |
| Backplot | `/api/cam/backplot/*` | (none) | Legacy only |
| Post | `/api/cam/post/*` | (none) | Legacy only |
| Smoke | `/api/cam/smoke/*` | (none) | Legacy only |

### Key Code Locations

#### Location 1: Legacy Imports (`main.py:160-171`)

```python
from .routers.cam_vcarve_router import router as cam_vcarve_router
from .routers.cam_post_v155_router import router as cam_post_v155_router
from .routers.cam_relief_v160_router import router as cam_relief_router
from .routers.cam_helical_v161_router import router as cam_helical_router
```

#### Location 2: Legacy Registration (`main.py:700-726`)

```python
# CAM Subsystem (8) - Legacy routes, consolidated equivalents in Wave 18
app.include_router(
    cam_vcarve_router, prefix="/api/cam/vcarve", tags=["V-Carve", "Legacy"]
)  # → /api/cam/toolpath/vcarve
app.include_router(
    cam_relief_router, prefix="/api/cam/relief", tags=["Relief Carving", "Legacy"]
)  # → /api/cam/relief (proxy)
app.include_router(
    cam_helical_router, prefix="/api/cam/helical", tags=["Helical Ramping", "Legacy"]
)  # → /api/cam/toolpath/helical
```

#### Location 3: Wave 18 Consolidated Registration (`main.py:1029-1034`)

```python
# Wave 18: CAM Router Consolidation (Phase 5+6)
# Categories: drilling, fret_slots, relief, risk, rosette, simulation, toolpath,
#             export, monitoring, pipeline, utility
if cam_router:
    app.include_router(cam_router, prefix="/api/cam", tags=["CAM Consolidated"])
```

#### Location 4: Aggregator Definition (`app/cam/routers/aggregator.py:94-129`)

```python
cam_router = APIRouter()

if drilling_router:
    cam_router.include_router(drilling_router, prefix="/drilling")
if toolpath_router:
    cam_router.include_router(toolpath_router, prefix="/toolpath")
if relief_router:
    cam_router.include_router(relief_router, prefix="/relief")
# ... etc
```

#### Location 5: Toolpath Category (`app/cam/routers/toolpath/__init__.py`)

```python
# Migrated from:
#   - routers/cam_roughing_router.py     → roughing_router.py
#   - routers/cam_helical_v161_router.py → helical_router.py
#   - routers/cam_vcarve_router.py       → vcarve_router.py

router = APIRouter()
router.include_router(roughing_router, prefix="/roughing")
router.include_router(helical_router)
router.include_router(vcarve_router, prefix="/vcarve")
```

#### Location 6: Relief Proxy Pattern (`app/cam/routers/relief/__init__.py`)

```python
# Proxy imports from existing routers (transitional)
from ....routers.cam_relief_router import router as toolpath_router
from ....routers.cam_relief_v160_router import router as preview_router

router = APIRouter()
if toolpath_router:
    router.include_router(toolpath_router)
```

### Migration Notes

- **Proxy pattern**: Some consolidated routes (relief, fret_slots) import the SAME legacy router, meaning both paths hit identical code
- **True duplicates**: V-Carve, Helical, Roughing have separate implementations in both legacy and consolidated locations
- **Resolution needed**: Decide whether to keep legacy paths (with deprecation warnings) or remove them entirely
- **Client impact**: Frontend API calls in `client/src/api/` may need updating when legacy paths are removed

---

## 12. Path to MVP

### Summary of Findings

#### What Exists (Working Infrastructure)

The luthiers-toolbox repository has **solid architectural foundations**:

- **CAM Core**: Toolpath generation works (drilling, roughing, biarc, v-carve, adaptive pocketing) at 65-100% coverage
- **G-code Pipeline**: Parsing, simulation, thermal analysis, and 5+ post-processor dialects (GRBL, LinuxCNC, Mach3, Fanuc, Heidenhain)
- **Geometry Processing**: DXF/SVG import/export, parity checking, unit conversion
- **Governance**: Cross-repo contracts enforced via CI gates with SHA256 verification
- **Calculator Suite**: 85% production-ready across general, woodworking, instrument, and CAM categories
- **API Structure**: FastAPI with ~50+ routers organized by domain

#### What's Missing (Critical Gaps)

The system lacks the **supporting infrastructure** that transforms algorithms into a usable product:

| Gap | Impact |
|-----|--------|
| **Feed & Speed Calculator** | Users must manually enter cutting parameters - dangerous for CNC |
| **3D Toolpath Visualization** | Only 2D backplot exists; can't verify Z-clearances or collisions |
| **Job Persistence** | Work lost on page refresh; no save/load workflow |
| **Tool & Material Libraries** | Hardcoded defaults; not scalable |
| **Collision Detection** | No warning before spindle crashes into stock or table |

#### Technical Debt

- **Wave 18 Migration Incomplete**: Duplicate endpoints at legacy (`/api/cam/vcarve`) and consolidated (`/api/cam/toolpath/vcarve`) paths
- **9 Router Categories Untested**: drilling, simulation, utility, relief, risk, fret_slots, monitoring lack dedicated tests
- **Frontend Test Coverage**: Zero Vue component or E2E tests

---

### Definitive Path to MVP

**The core CAM algorithms are done. The gap is user-facing infrastructure.**

#### Phase 1: Safety & Usability (2 weeks, ~50 hours)

| Priority | Task | Hours | Outcome |
|----------|------|-------|---------|
| 1 | Implement Feed & Speed Calculator | 8h | Safe cutting parameters |
| 2 | Add Three.js 3D Preview | 10h | Visual verification before cutting |
| 3 | Job Persistence Layer | 6h | Save/load workflows |
| 4 | Basic Collision Detection | 4h | Crash prevention warnings |
| 5 | Tool Library API | 4h | Selectable tool definitions |
| 6 | Material Lookup API | 4h | Wood/metal properties database |
| 7 | Job Create/List UI | 8h | User workflow forms |
| 8 | Complete Wave 18 Migration | 6h | Remove duplicate paths |

#### Phase 2: Polish & Test (1 week, ~20 hours)

- Add tests for 9 untested router categories
- Frontend component tests for CAM views
- Documentation for calculator and CAM APIs

---

### The Definitive Statement

**Luthiers-ToolBox is 62% of the way to MVP. The remaining 38% is not algorithmic complexity—it's user experience infrastructure.**

The toolpath math works. The G-code generation works. The post-processors work. What's missing is the wrapper that lets a human safely use these systems:

1. **They can't calculate safe feeds/speeds** → implement `chipload_db.py`
2. **They can't see what they're about to cut** → add Three.js 3D preview
3. **They can't save their work** → add job persistence
4. **They won't know if they'll crash** → add collision detection

**50 focused hours of development on these 4 systems transforms this from a collection of working algorithms into a shippable MVP.**

The path is clear. The scope is bounded. The infrastructure exists to support these additions. This is not a rewrite—it's completion.

---

## 13. Art Studio System Analysis

### Overall Status: ~85% Production-Ready (Core), ~60% Experimental Features

The Art Studio is **substantially more complete** than the CAM system. Core design workflows are production-ready.

**Full audit document:** `docs/ART_STUDIO_SYSTEM_AUDIT.md`

### Architecture (Design-First Principle)

Art Studio is the **design authority only**. It does NOT generate G-code or CAM artifacts.

```
Art Studio (Design) → Workflow (Governance) → CAM (Execution)
```

### What's Working (Production-Ready)

| Component | Status | Features |
|-----------|--------|----------|
| **Rosette Calculator** | Complete | Channel math, SVG preview, DXF export |
| **Bracing Calculator** | Complete | 4 profiles, mass calculation, DXF export |
| **Inlay Generator** | Complete | Dots, diamonds, blocks, side dots |
| **Snapshot Management** | Complete | Save/load/export with feasibility |
| **Pattern Library** | Complete | CRUD, filtering, versioned generators |
| **Feasibility Scoring** | Complete | RMOS integration, risk bucketing |
| **DXF Export** | Complete | R12-R18 version support |
| **Test Coverage** | Good | 7+ dedicated test modules |

### What's Incomplete

| Component | Status | Gap |
|-----------|--------|-----|
| **Workflow State Machine** | 80% | Some endpoints not fully wired |
| **AI-Powered SVG** | Exploratory | Integration incomplete |
| **CAM Promotion Path** | Not exposed | Manual handoff required |
| **Frontend Components** | Multiple versions | Consolidation needed |

### Backend Structure

```
services/api/app/art_studio/
├── api/                    # 10 route modules (Bundle 31.0+)
├── schemas/                # 8 Pydantic models
├── services/               # 8 business logic modules
│   └── generators/         # 2 parametric generators
├── svg/                    # AI-powered SVG (experimental)
└── routers/                # Classic calculators (rosette, bracing, inlay)
```

### API Endpoints Summary

| Category | Endpoints | Status |
|----------|-----------|--------|
| Generators | 2 | ✅ Functional |
| Pattern Library | 5 CRUD | ✅ Functional |
| Snapshots | 6 CRUD | ✅ Functional |
| Workflow | 12 | ⚠️ 80% wired |
| Rosette Jobs | 4 | ✅ Functional |
| Rosette Compare | 4 | ✅ Functional |
| Classic Calculators | 10+ | ✅ Functional |

**Total: ~50 endpoints, ~90% functional**

### Path to Full Completion (~30 hours)

| Phase | Tasks | Hours |
|-------|-------|-------|
| **Phase 1: Core** | Workflow binding, CAM promotion, frontend consolidation | 15h |
| **Phase 2: Experimental** | AI integration, custom generator UI, E2E tests | 15h |

### Comparison: Art Studio vs CAM

| Aspect | Art Studio | CAM System |
|--------|------------|------------|
| Core Algorithms | ✅ Complete | ✅ Complete |
| Persistence | ✅ Complete | ❌ Missing |
| User Infrastructure | ✅ 85% | ❌ 62% |
| Test Coverage | ✅ Good | ⚠️ Gaps |
| Hours to MVP | ~30h | ~50h |

**Art Studio is closer to MVP than CAM. The remaining work is integration polish, not fundamental infrastructure.**

---

## 14. Blueprint Reader System Analysis

### Overall Status: ~93% Production-Ready

The Blueprint Reader is the **most complete subsystem** in the repository. All core phases are operational with excellent graceful degradation architecture.

**Full audit document:** `docs/BLUEPRINT_READER_SYSTEM_AUDIT.md`

### Phase Pipeline

```
[Upload] → [Phase 1: AI] → [Phase 2: OpenCV] → [Phase 3: CAM]
   │            │               │                    │
 PDF/PNG    Claude API     Edge Detection      Adaptive
 JPG        Dimensions     Contours            Pocketing
            Extraction     DXF Export          Toolpaths
```

### What's Working (Production-Ready)

| Phase | Component | Status | Description |
|-------|-----------|--------|-------------|
| **1** | AI Analysis | ✅ Complete | Claude Sonnet 4 dimension extraction |
| **1** | SVG Export | ✅ Complete | Dimension annotations (501 in Docker) |
| **2** | Vectorization | ✅ Complete | OpenCV edge detection + contours |
| **2** | DXF Export | ✅ Complete | DXF R12 with LWPOLYLINE |
| **2.5** | CAM Bridge | ✅ Complete | Blueprint → adaptive pocketing |
| **3.1** | Contour Reconstruction | ✅ Complete | LINE/SPLINE → closed loops |
| **3.2** | DXF Preflight | ✅ Complete | 6-stage validation pipeline |

### API Endpoints (8/9 Functional)

| Endpoint | Status |
|----------|--------|
| `POST /api/blueprint/analyze` | ✅ Functional |
| `POST /api/blueprint/vectorize-geometry` | ✅ Functional |
| `POST /api/blueprint/cam/reconstruct-contours` | ✅ Functional |
| `POST /api/blueprint/cam/preflight` | ✅ Functional |
| `POST /api/blueprint/cam/to-adaptive` | ✅ Functional |
| `GET /api/blueprint/health` | ✅ Functional |
| `POST /api/blueprint/to-dxf` | ❌ Planned |

### Backend Structure

```
services/api/app/routers/
├── blueprint_router.py           # 1,315 lines (Phase 1 & 2)
└── blueprint_cam_bridge.py       # 965 lines (Phase 2.5 & 3)

services/api/app/cam/
├── contour_reconstructor.py      # 23KB - LINE/SPLINE → loops
├── dxf_preflight.py              # 28KB - 6-stage validation
└── adaptive_core_l1.py           # 25KB - Adaptive pocketing
```

### Frontend

| Component | Status |
|-----------|--------|
| BlueprintLab.vue | ✅ Complete |
| Upload zone (drag-and-drop) | ✅ Working |
| Phase 1 UI (AI analysis) | ✅ Working |
| Phase 2 UI (vectorization) | ✅ Working |
| Phase 3 UI ("Send to Adaptive") | 🟡 Disabled |

### Graceful Degradation

| Missing Dependency | Behavior |
|--------------------|----------|
| Claude API key | `/analyze` returns 503 |
| OpenCV | `/vectorize-geometry` returns 501 |
| pdf2image | PDF upload returns 503 |

### What's Incomplete

| Gap | Status | Effort |
|-----|--------|--------|
| **RMOS Integration** | Missing | 8h |
| **Multi-page PDF** | Not supported | 4h |
| **Frontend CAM Button** | Disabled | 2h |
| **Phase 3 CI Tests** | Partial | 4h |

### Path to Full Completion (~24 hours)

| Priority | Tasks | Hours |
|----------|-------|-------|
| **Critical** | RMOS bridge, Docker SVG | 10h |
| **Important** | Multi-page PDF, CI tests, CAM button | 10h |
| **Enhancement** | Art Studio integration | 4h |

### Comparison: All Systems

| Aspect | Blueprint | Art Studio | CAM |
|--------|-----------|------------|-----|
| Core Algorithms | ✅ Complete | ✅ Complete | ✅ Complete |
| API Endpoints | ✅ 93% | ✅ 90% | ⚠️ 65% |
| Persistence | ✅ Complete | ✅ Complete | ❌ Missing |
| User Infrastructure | ✅ 93% | ✅ 85% | ❌ 62% |
| Graceful Degradation | ✅ Excellent | ✅ Good | ⚠️ Partial |
| Hours to MVP | ~24h | ~30h | ~50h |

**Blueprint Reader is the closest system to production. 24 focused hours completes it.**

---

## 15. RMOS System Analysis

### Overall Status: ~80% Production-Ready

The **Rosette Manufacturing Orchestration System (RMOS)** is the governance backbone of luthiers-toolbox, managing run lifecycles, feasibility scoring, safety policies, and manufacturing workflow state.

**Full audit document:** `docs/RMOS_SYSTEM_AUDIT.md`

### Architecture (Governance Backbone)

RMOS ensures that manufacturing operations are tracked, assessed, gated, and orchestrated:

```
┌─────────────────────────────────────────────────────────────────┐
│  Run Artifacts (Immutable)  →  Feasibility Engines  →  Safety   │
│       date-partitioned           Baseline V1            Policy   │
│       SHA256 hashing             CAM stubs              Gate     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
              Workflow State Machine (10 states, 3 modes)
```

### What's Working (Production-Ready)

| Component | Status | Features |
|-----------|--------|----------|
| **Run Artifact Store** | Complete | Immutable JSON, date partitioning, SHA256 |
| **Baseline V1 Engine** | Complete | Weighted scoring (0-100), risk bucketing |
| **Safety Policy** | Complete | Environment gating, RED/UNKNOWN blocking |
| **Workflow FSM** | Complete | 10 states, 3 modes, session management |
| **Saw Operations** | Complete | Batch processing, comparison |
| **API Endpoints** | 95% | 50+ endpoints across 4 routers |
| **Frontend Components** | Complete | 47 Vue components |
| **Feasibility Phase 1** | ✅ Shipped | Pre-CAM validation, deterministic hashing |

### Feasibility Phase 1 (Shipped 2026-01-16)

The MVP wrapper now includes a **deterministic feasibility check before CAM**:

- **Pre-CAM validation**: Runs before plan generation, not after
- **Deterministic hashing**: Same input → same `feasibility_sha256`
- **Rule-based decisions**: RED (blocking), YELLOW (warnings), GREEN (pass)
- **Persisted artifacts**: `feasibility.json` in run attachments + operator pack

**Key files:**
- `services/api/app/rmos/feasibility/` - Engine, schemas, rules
- `services/api/app/rmos/mvp_wrapper.py` - Wrapper integration
- `services/api/tests/test_feasibility_engine.py` - 24 unit tests
- `services/api/tests/test_rmos_wrapper_feasibility_phase1.py` - 10 integration tests

### What's Incomplete

| Component | Status | Gap |
|-----------|--------|-----|
| **Test Coverage** | 20% | Only 3 of 15+ modules tested |
| **CAM Feasibility Engines** | Stubs | 6 modes return GREEN by default |
| **FANUC Scheduling** | Planned | Not implemented |
| **Blueprint RMOS Bridge** | Planned | Blueprint analysis ungoverned |

### Backend Structure

```
services/api/app/rmos/
├── runs_v2/                    # Immutable run artifacts
│   ├── store.py                # Date-partitioned JSON storage
│   ├── api_runs.py             # 15+ endpoints
│   └── schemas.py              # Governance-compliant models
├── engines/
│   ├── feasibility_baseline_v1.py  # Production engine
│   └── cam_feasibility.py          # 6 CAM mode stubs
├── policies/
│   └── safety_policy.py        # Central safety gate
├── workflow/
│   └── state_machine.py        # 10-state FSM
└── api/                        # 4 router modules
```

### Risk Bucketing

| Score Range | Bucket | Safety Decision |
|-------------|--------|-----------------|
| ≥80 | GREEN | ✅ ALLOW |
| 50-79 | YELLOW | ⚠️ WARN (override available) |
| <50 | RED | ❌ BLOCK |
| Unknown | UNKNOWN | ❌ BLOCK (normalized to RED) |

### Workflow States

```
DRAFT → PENDING_REVIEW → IN_REVIEW → APPROVED → SCHEDULED →
    IN_PROGRESS → COMPLETED → ARCHIVED

Alternative: IN_REVIEW → REJECTED | REVISION_REQUESTED → DRAFT
```

### Path to Full Completion (~48 hours)

| Phase | Tasks | Hours |
|-------|-------|-------|
| **Phase 1: Testing** | Workflow FSM, Session, CAM, Saw, API tests | 20h |
| **Phase 2: CAM Engines** | 6 real feasibility engines | 24h |
| **Phase 3: Features** | Blueprint bridge, Intent completion, FANUC stub | 8h |

### Comparison: All Systems

| Aspect | RMOS | Blueprint | Art Studio | CAM |
|--------|------|-----------|------------|-----|
| Core Algorithms | ✅ Complete | ✅ Complete | ✅ Complete | ✅ Complete |
| API Endpoints | ✅ 95% | ✅ 93% | ✅ 90% | ⚠️ 65% |
| Persistence | ✅ Complete | ✅ Complete | ✅ Complete | ❌ Missing |
| Test Coverage | ⚠️ 20% | ⚠️ Partial | ✅ Good | ⚠️ Gaps |
| Hours to MVP | ~48h | ~24h | ~30h | ~50h |

**RMOS provides the governance foundation all other systems depend on. Its completion enables safe manufacturing operations across the entire platform.**

---

## 16. CNC Saw Lab System Analysis

### Overall Status: ~75-80% Production-Ready

The CNC Saw Lab is a **substantially complete manufacturing subsystem** with robust safety validation, comprehensive RMOS integration, and excellent test coverage (11,030 lines across 132 test files).

**Full audit document:** `docs/SAW_LAB_SYSTEM_AUDIT.md`

### Architecture (Safety-First Manufacturing)

```
┌─────────────────────────────────────────────────────────────────┐
│  Blade Registry  →  5 Safety Calculators  →  RMOS Safety Gate   │
│   CRUD + PDF         rim/bite/heat/          Policy blocking     │
│   import             deflection/kickback     RED/UNKNOWN         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
              G-Code Generation (multi-pass, 3 operation types)
                              ↓
              Learning System (automatic override application)
```

### What's Working (Production-Ready)

| Component | Status | Features |
|-----------|--------|----------|
| **Blade Registry** | Complete | CRUD, validation, PDF import, search |
| **5 Safety Calculators** | Complete | Rim speed, bite load, heat, deflection, kickback |
| **G-Code Generator** | Complete | Multi-pass depth, 3 operation types |
| **Safety Validation** | Complete | 5 endpoints, material-specific limits |
| **Telemetry System** | Complete | 3-factor real-time risk scoring |
| **RMOS Integration** | Complete | Safety policy gating, 5 CAM guards |
| **Learning System** | Complete | Automatic override application |
| **Test Coverage** | Excellent | 11,030 lines across 132 files |

### Five Core Safety Calculators

| Calculator | Formula/Check | Material Limits |
|------------|---------------|-----------------|
| **Rim Speed** | π × D × RPM / 60000 | 40-80 m/s by material |
| **Bite Load** | feed / (RPM × teeth) | 0.03-0.15 mm/tooth |
| **Heat Index** | speed × feed × dust | 500mm cut threshold |
| **Deflection** | max = 40% × diameter | D/kerf ratio checks |
| **Kickback** | 6-factor weighted | Material-dependent |

### Backend Structure

```
services/api/app/
├── saw_lab/                    # 788 lines - Core calculators
│   └── calculators/            # 5 safety calculators (27KB)
├── services/                   # 4,548 lines - 31 service files
│   ├── saw_lab_batch_*.py      # Batch workflows
│   ├── saw_lab_learning_*.py   # Learning integration
│   └── saw_lab_decision_service.py
├── routers/                    # 1,244 lines - 5 routers
│   ├── saw_blade_router.py     # CRUD (241 lines)
│   ├── saw_gcode_router.py     # G-code (132 lines)
│   ├── saw_validate_router.py  # Validation (230 lines)
│   └── saw_telemetry_router.py # Telemetry (498 lines)
├── cam_core/saw_lab/           # Blade registry (34KB)
└── rmos/
    ├── saw_safety_gate.py      # 84 lines
    └── saw_cam_guard.py        # 286 lines - 5 guards
```

### What's Incomplete

| Component | Status | Gap |
|-----------|--------|-----|
| **Frontend Stubs** | 2 components | DiffPanel, QueuePanel not implemented |
| **CAM Core Router** | Placeholder | 22 lines, needs delegation |
| **Path Planner 2.1** | Future | Skeleton for optimization |

### Path to Completion

| Target | Hours | Tasks |
|--------|-------|-------|
| **90% Ready** | ~75h | Frontend stubs, CAM router, docs |
| **95% Ready** | ~120h | + anomaly handling, path planning |
| **98% Ready** | ~185h | + Path Planner 2.1, blade selection UI |

### Comparison: All Systems

| Aspect | Saw Lab | Blueprint | Art Studio | RMOS | CAM |
|--------|---------|-----------|------------|------|-----|
| Core Algorithms | ✅ Complete | ✅ Complete | ✅ Complete | ✅ Complete | ✅ Complete |
| API Endpoints | ✅ 95% | ✅ 93% | ✅ 90% | ✅ 95% | ⚠️ 65% |
| Test Coverage | ✅ Excellent | ⚠️ Partial | ✅ Good | ⚠️ 20% | ⚠️ Gaps |
| RMOS Integration | ✅ Complete | ⚠️ Planned | ✅ Complete | N/A | ⚠️ Stubs |
| Hours to MVP | ~75h | ~24h | ~30h | ~48h | ~50h |

**The Saw Lab is mature and production-ready for operator use. It represents one of the most complete subsystems with the strongest test coverage and safety infrastructure.**

---

## 17. AI System Analysis

### Overall Status: ~65-70% Production-Ready

The AI System is a **multi-layered platform** with approximately **26,878 lines of AI-related backend code**. Core infrastructure is production-ready; domain integrations are at various stages.

**Full audit document:** `docs/AI_SYSTEM_AUDIT.md`

### Architecture (Multi-Layer Design)

```
┌─────────────────────────────────────────────────────────────────┐
│  Canonical AI Platform (app/ai/)                                 │
│  ├── Transport Layer    - Multi-provider LLM + Image clients    │
│  ├── Cost Estimation    - Token pricing tables                  │
│  ├── Safety Policy      - Content filtering framework           │
│  └── Availability Gate  - Graceful 503 degradation              │
├─────────────────────────────────────────────────────────────────┤
│  Domain Integrations                                             │
│  ├── Blueprint Reader   - Claude Sonnet 4 vision ✅              │
│  ├── RMOS AI Search     - Constraint-first design ✅             │
│  ├── AI Graphics        - Rosette suggestions ⚠️                 │
│  └── G-code Explainer   - CNC analysis ❌                        │
└─────────────────────────────────────────────────────────────────┘
```

### What's Working (Production-Ready)

| Component | Lines | Status | Features |
|-----------|-------|--------|----------|
| **Canonical AI Platform** | 2,924 | ✅ 95% | Multi-provider transport, safety, cost |
| **Blueprint Reader Phase 1** | 1,177 | ✅ 100% | Claude Sonnet 4 vision, PDF→PNG |
| **Blueprint Reader Phase 2** | 730 | ✅ 100% | OpenCV vectorization, DXF export |
| **RMOS AI Search** | 2,080+ | ✅ 90% | Constraint-first design, feasibility scoring |
| **Availability Gate** | 147 | ✅ 100% | Graceful 503 degradation |

### What's Incomplete

| Component | Lines | Status | Gap |
|-----------|-------|--------|-----|
| **AI Graphics** | 6,647+ | ⚠️ 50% | Works API-side, no Vue UI |
| **Cost Tracking** | 215 | ⚠️ 60% | Not persisted |
| **G-code Explainer** | 115 | ❌ 20% | Parsing only, no LLM |

### Provider Configuration

| Provider | Env Variable | Required | Use Case |
|----------|-------------|----------|----------|
| **Anthropic (Claude)** | `ANTHROPIC_API_KEY` | ✅ Yes | Blueprint, RMOS |
| OpenAI | `OPENAI_API_KEY` | No | Image generation |
| Ollama | `OLLAMA_URL` | No | Local LLM fallback |

### API Endpoints

| Endpoint | Status | Description |
|----------|--------|-------------|
| `POST /api/blueprint/analyze` | ✅ | Claude vision extraction |
| `POST /api/rmos/ai/constraint-search` | ✅ | LLM-guided design |
| `POST /api/rmos/ai/quick-check` | ✅ | Fast feasibility |
| `GET /api/rmos/ai/health` | ✅ | AI availability |
| `POST /api/ai/graphics/suggest` | ⚠️ | Experimental |
| `POST /api/gcode/explain` | ❌ | Stub only |

### Path to Completion (~65 hours)

| Phase | Tasks | Hours |
|-------|-------|-------|
| **Phase 1: Core** | AI Graphics UI, cost tracking, refinement loop | 35h |
| **Phase 2: Polish** | Provider tests, G-code LLM, dashboard | 30h |

### Comparison: All Systems

| Aspect | AI | Saw Lab | Blueprint | Art Studio | RMOS | CAM |
|--------|-----|---------|-----------|------------|------|-----|
| Core Algorithms | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| API Endpoints | ⚠️ 80% | ✅ 95% | ✅ 93% | ✅ 90% | ✅ 95% | ⚠️ 65% |
| Frontend UI | ⚠️ 30% | ⚠️ 70% | ✅ 90% | ✅ 85% | ✅ 100% | ⚠️ 60% |
| Test Coverage | ⚠️ 70% | ✅ Excellent | ⚠️ Partial | ✅ Good | ⚠️ 20% | ⚠️ Gaps |
| Hours to MVP | ~65h | ~75h | ~24h | ~30h | ~48h | ~50h |

**The AI System provides the foundation for intelligent features across the platform. Core infrastructure is solid; remaining work focuses on UI integration and operational visibility.**

---

## Contact & Resources

- **GitHub Issues**: https://github.com/HanzoRazer/luthiers-toolbox/issues
- **sg-spec Repository**: https://github.com/HanzoRazer/sg-spec
- **CI Status**: Check `.github/workflows/core_ci.yml` runs

---

*This handoff document was generated to facilitate developer onboarding. For detailed technical specifications, refer to the linked documentation files.*
