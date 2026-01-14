# Developer Handoff: Luthiers-ToolBox Repository

**Version:** 1.2.0
**Date:** 2026-01-13
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

## Contact & Resources

- **GitHub Issues**: https://github.com/HanzoRazer/luthiers-toolbox/issues
- **sg-spec Repository**: https://github.com/HanzoRazer/sg-spec
- **CI Status**: Check `.github/workflows/core_ci.yml` runs

---

*This handoff document was generated to facilitate developer onboarding. For detailed technical specifications, refer to the linked documentation files.*
