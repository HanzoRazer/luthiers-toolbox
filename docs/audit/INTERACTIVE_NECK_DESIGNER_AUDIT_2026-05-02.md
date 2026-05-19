# Interactive Neck Designer & Setup Platform Component Inventory

**Audit Date:** 2026-05-02  
**Auditor:** Claude Code Opus 4.5  
**Purpose:** Comprehensive inventory of files related to full string-bearing geometry and setup workflow  
**Scope:** Neck region, string-bearing geometry, bridge region, setup specifications, hardware affecting setup, player-facing parameters

---

## 1. Backend — Python

### 1a. Schemas / Pydantic Models

| Path | Type | Purpose | Status | Direct Dependencies | Direct Consumers |
|------|------|---------|--------|---------------------|------------------|
| ✅ `services/api/app/instrument_geometry/neck/fretboard_ecosphere.py` | Pydantic model | Canonical fretboard geometry document (FretboardEcosphere) — fret positions, string paths, outline, multiscale support | Complete, shipping | `alternative_temperaments.py` | `api_v1/fretboard.py`, `fret_slots_from_ecosphere.py`, tests |
| ✅ `services/api/app/calculators/string_tension.py:StringSpec`, `TensionResult`, `SetTensionResult` | Dataclasses | String tension calculation input/output models | Complete, shipping | None | `routers/instrument_geometry/string_tension_router.py` |
| ✅ `services/api/app/calculators/setup_cascade.py:SetupState`, `SetupIssue`, `SetupCascadeResult` | Dataclasses | Setup evaluation state and results | Complete, shipping | `neck_angle.py` | `routers/instrument_geometry/setup_router.py` |
| ✅ `services/api/app/calculators/saddle_compensation.py` | Pydantic models | Design and setup mode saddle compensation schemas | Complete, shipping | None | `routers/saddle_compensation_router.py` |
| ✅ `services/api/app/instrument_geometry/bridge/electric_bridges.py:ElectricBridgeSpec` | Dataclass | Complete spec for electric bridge types | Complete, shipping | None | Bridge presets router |
| ✅ `services/api/app/instrument_geometry/bridge/floyd_rose_tremolo.py` | Dataclasses | Floyd Rose Original schematic-derived dimensions | Complete, shipping | None | Bridge presets router |
| ✅ `services/api/app/calculators/nut_slot_calc.py:NutSlotSpec` | Dataclass | Nut slot depth calculation result | Complete, shipping | None | Nut/fret router |
| ✅ `services/api/app/calculators/tuning_machine_calc.py:TuningMachineSpec` | Dataclass | Tuner post height and string tree selection | Complete, shipping | None | Tuning machine router |
| ✅ `services/api/app/routers/instrument_geometry/setup_router.py` | Pydantic models | API request/response schemas for setup evaluation | Complete, shipping | `setup_cascade.py` | Frontend |

### 1b. Math Kernels (Geometry, Position Computation, Tension Calculation)

| Path | Type | Purpose | Status | Direct Dependencies | Direct Consumers |
|------|------|---------|--------|---------------------|------------------|
| ✅ `services/api/app/instrument_geometry/neck/fret_math.py` | Python module | Core fret position computation (12-TET and arbitrary temperaments) | Complete, shipping | None | `fretboard_ecosphere.py`, `neck_angle.py` |
| ✅ `services/api/app/calculators/alternative_temperaments.py` | Python module | Temperament ratios (19-TET, 24-TET, 31-TET, Pythagorean, Just, Meantone) | Complete, shipping | None | `fretboard_ecosphere.py` |
| ✅ `services/api/app/calculators/string_tension.py` | Python module | String tension physics: T = (2×f×L)² × μ | Complete, shipping | None | Bracing calc, bridge plate sizing |
| ✅ `services/api/app/instrument_geometry/neck/neck_angle.py` | Python module | Neck angle from geometry, inverse solver for target action | Complete, shipping | `fret_math.py` | `setup_cascade.py` |
| ✅ `services/api/app/calculators/saddle_compensation.py` | Python module | Per-string compensation from physical parameters and cents error | Complete, shipping | None | Saddle compensation router |
| ✅ `services/api/app/calculators/headstock_break_angle.py` | Python module | Headstock break angle calculation | Complete, shipping | None | Headstock routers |
| ✅ `services/api/app/calculators/tuning_machine_calc.py` | Python module | Break angle, post height, string tree selection, wrap count | Complete, shipping | None | Tuning machine router |
| ✅ `services/api/app/instrument_geometry/neck_taper/taper_math.py` | Python module | Neck taper geometry calculations | Complete, shipping | None | Neck outline generator |
| ✅ `services/api/app/instrument_geometry/spacing.py` | Python module | String spacing calculations | Complete, shipping | None | Multiple consumers |
| ✅ `services/api/app/instrument_geometry/bridge/compensation.py` | Python module | Bridge compensation geometry | Complete, shipping | None | Bridge calculators |
| ✅ `services/api/app/calculators/nut_compensation_physics.py` | Python module | Nut compensation physics | Complete, shipping | None | Nut calculators |
| ✅ `services/api/app/calculators/fret_wire_physics.py` | Python module | Fret wire physics calculations | Complete, shipping | None | Fret calculators |

### 1c. CAM Modules (Toolpath Generation, G-code, DXF Projection)

| Path | Type | Purpose | Status | Direct Dependencies | Direct Consumers |
|------|------|---------|--------|---------------------|------------------|
| ✅ `services/api/app/cam/fret_slots_from_ecosphere.py` | Python module | Extract CAM geometry from FretboardEcosphere | Complete, shipping | `fretboard_ecosphere.py` | Fret slot CAM generators |
| ✅ `services/api/app/calculators/fret_slots_cam.py` | Python module | Standard fret slot toolpath generation | Complete, shipping | None | Fret slots router |
| ✅ `services/api/app/calculators/fret_slots_fan_cam.py` | Python module | Fan-fret (multiscale) slot toolpath generation | Complete, shipping | None | Fret slots router |
| ✅ `services/api/app/cam/neck/truss_rod_channel.py` | Python module | Truss rod channel G-code generation | Complete, shipping | `config.py`, `post_processor.py` | Neck CAM orchestrator |
| ✅ `services/api/app/cam/neck/fret_slots.py` | Python module | Fret slot CAM for neck workflow | Complete, shipping | None | Neck CAM orchestrator |
| ✅ `services/api/app/cam/neck/profile_carving.py` | Python module | Neck back profile carving | Complete, shipping | None | Neck CAM orchestrator |
| ✅ `services/api/app/cam/neck/orchestrator.py` | Python module | Neck CAM workflow orchestration | Complete, shipping | All neck CAM modules | Neck G-code router |
| ✅ `services/api/app/instrument_geometry/neck_taper/dxf_exporter.py` | Python module | Neck outline DXF export | Complete, shipping | `neck_outline_generator.py` | Neck export router |
| ✅ `services/api/app/instrument_geometry/bridge/floyd_rose_tremolo.py:floyd_rose_routing_gcode()` | Python function | Floyd Rose body routing G-code | Complete, shipping | None | Bridge CAM router |
| ✅ `services/api/app/cam/archtop_bridge_generator.py` | Python module | Archtop bridge CAM generation | Complete, shipping | None | Bridge export router |
| ✅ `services/api/app/cam/archtop_saddle_generator.py` | Python module | Archtop saddle CAM generation | Complete, shipping | None | Bridge export router |

### 1d. FastAPI Routers and Endpoints

| Path | Type | Purpose | Status | Direct Dependencies | Direct Consumers |
|------|------|---------|--------|---------------------|------------------|
| ✅ `services/api/app/api_v1/fretboard.py` | FastAPI router | Fretboard Ecosphere API: compute, dxf, scala, presets | Complete, shipping | `fretboard_ecosphere.py`, `fretboard_presets.py` | Frontend |
| ✅ `services/api/app/routers/instrument_geometry/setup_router.py` | FastAPI router | Setup cascade evaluation endpoint | Complete, shipping | `setup_cascade.py` | Frontend |
| ✅ `services/api/app/routers/instrument_geometry/string_tension_router.py` | FastAPI router | String tension calculation endpoints | Complete, shipping | `string_tension.py` | Frontend |
| ✅ `services/api/app/routers/instrument_geometry/nut_fret_router.py` | FastAPI router | Nut slot and fret wire endpoints | Complete, shipping | `nut_slot_calc.py`, `fret_wire_calc.py` | Frontend |
| ✅ `services/api/app/routers/instrument_geometry/tuning_machine_router.py` | FastAPI router | Tuning machine calculator endpoints | Complete, shipping | `tuning_machine_calc.py` | Frontend |
| ✅ `services/api/app/routers/instrument_geometry/bridge_router.py` | FastAPI router | Bridge geometry and presets | Complete, shipping | Bridge modules | Frontend |
| ✅ `services/api/app/routers/saddle_compensation_router.py` | FastAPI router | Saddle compensation calculator | Complete, shipping | `saddle_compensation.py` | Frontend |
| ✅ `services/api/app/routers/neck_router.py` | FastAPI router | Neck profile and geometry | Complete, shipping | Neck modules | Frontend |
| ✅ `services/api/app/routers/neck/gcode_router.py` | FastAPI router | Neck G-code generation | Complete, shipping | `orchestrator.py` | Frontend |
| ✅ `services/api/app/routers/cam/routers/fret_slots_router.py` | FastAPI router | Fret slot CAM preview and export | Complete, shipping | Fret slot CAM modules | Frontend |
| ✅ `services/api/app/cam/routers/bridge_export_router.py` | FastAPI router | Bridge CAM export | Complete, shipping | Bridge CAM modules | Frontend |

### 1e. Calculators (Fret Wire, Fret Physics, String Tension, Intonation)

| Path | Type | Purpose | Status | Direct Dependencies | Direct Consumers |
|------|------|---------|--------|---------------------|------------------|
| ✅ `services/api/app/calculators/string_tension.py` | Calculator | String tension from gauge, tuning, scale length | Complete, shipping | None | Multiple consumers |
| ✅ `services/api/app/calculators/fret_wire_calc.py` | Calculator | Fret wire dimensions and selection | Complete, shipping | None | Nut/fret router |
| ✅ `services/api/app/calculators/fret_wire_physics.py` | Calculator | Fret wire physics (crown height, tang width) | Complete, shipping | None | Fret calculators |
| ✅ `services/api/app/calculators/fret_leveling_calc.py` | Calculator | Fret leveling specifications | Complete, shipping | None | Fretwork router |
| ✅ `services/api/app/calculators/nut_slot_calc.py` | Calculator | Nut slot depth from gauge and fret type | Complete, shipping | None | Nut/fret router |
| ✅ `services/api/app/calculators/nut_compensation_calc.py` | Calculator | Nut compensation calculations | Complete, shipping | None | Nut router |
| ✅ `services/api/app/calculators/saddle_compensation.py` | Calculator | Design and setup mode saddle compensation | Complete, shipping | None | Saddle compensation router |
| ✅ `services/api/app/calculators/saddle_compensation_calc.py` | Calculator | Additional saddle compensation logic | Complete, shipping | None | Saddle compensation router |
| ✅ `services/api/app/calculators/bridge_calc.py` | Calculator | Bridge geometry calculations | Complete, shipping | None | Bridge routers |
| ✅ `services/api/app/calculators/bridge_break_angle.py` | Calculator | Bridge break angle calculation | Complete, shipping | None | Setup cascade |
| ✅ `services/api/app/calculators/headstock_break_angle.py` | Calculator | Headstock break angle | Complete, shipping | None | Headstock routers |
| ✅ `services/api/app/calculators/tuning_machine_calc.py` | Calculator | Tuner post height, break angle, string trees | Complete, shipping | None | Tuning machine router |

### 1f. Setup-Related Modules (Relief, Action, Nut Height, Intonation)

| Path | Type | Purpose | Status | Direct Dependencies | Direct Consumers |
|------|------|---------|--------|---------------------|------------------|
| ✅ `services/api/app/calculators/setup_cascade.py` | Calculator | Setup parameter cascade evaluation with gates | Complete, shipping | `neck_angle.py` | Setup router |
| ✅ `services/api/app/instrument_geometry/neck/neck_angle.py` | Calculator | Neck angle from geometry, solve for target action | Complete, shipping | `fret_math.py` | `setup_cascade.py` |
| 🟡 `services/api/app/routers/instrument_geometry/setup_router.py` | Router | POST /setup/evaluate endpoint | Complete, shipping | `setup_cascade.py` | Frontend |

### 1g. Data Files (JSON Specs, Presets, Reference Data, Tuning Tables, Gauge Tables)

| Path | Type | Purpose | Status | Direct Dependencies | Direct Consumers |
|------|------|---------|--------|---------------------|------------------|
| ✅ `services/api/app/instrument_geometry/neck/fretboard_presets.py` | Python module | Fretboard preset configurations (Fender, Gibson, PRS, Jazz Bass, Smart Guitar Pro Fan) | Complete, shipping | `fretboard_ecosphere.py` | `api_v1/fretboard.py` |
| ✅ `services/api/app/generators/neck_headstock_presets.py` | Python module | Neck and headstock dimension presets | Complete, shipping | `neck_headstock_enums.py` | Headstock generator |
| ✅ `services/api/app/instrument_geometry/bridge/electric_bridges.py:ELECTRIC_BRIDGES` | Dict | Electric bridge database (Strat, Tele, TOM, Floyd Rose, Bigsby) | Complete, shipping | None | Bridge routers |
| ✅ `services/api/app/instrument_geometry/specs/*.json` | JSON files | Instrument specification files (Stratocaster, Les Paul, ES-335, etc.) | Complete, shipping | None | Instrument geometry routers |
| ✅ `services/api/app/calculators/nut_slot_calc.py:FRET_CROWN_HEIGHTS_MM` | Dict | Fret crown heights by type | Complete, shipping | None | Nut slot calculator |
| ✅ `services/api/app/calculators/nut_slot_calc.py:STANDARD_STRING_SETS` | Dict | Predefined string sets | Complete, shipping | None | Nut slot calculator |
| ✅ `services/api/app/calculators/string_tension.py:STANDARD_TUNING_HZ` | Dict | Standard tuning frequencies | Complete, shipping | None | String tension calculator |
| ✅ `services/api/app/calculators/string_tension.py:WOUND_UNIT_WEIGHT_KG_M` | Dict | Wound string unit weights (D'Addario specs) | Complete, shipping | None | String tension calculator |
| ✅ `services/api/app/calculators/string_tension.py:STRING_SETS` | Dict | Preset string sets (extra_light, light, medium, bluegrass, classical) | Complete, shipping | None | String tension calculator |
| ✅ `services/api/app/calculators/tuning_machine_calc.py:STANDARD_POST_HEIGHTS` | Dict | Standard tuner post heights by brand | Complete, shipping | None | Tuning machine calculator |
| ✅ `services/api/app/calculators/tuning_machine_calc.py:STRING_TREE_SPECS` | Dict | String tree specifications | Complete, shipping | None | Tuning machine calculator |
| ✅ `services/api/app/data_registry/edition/neck_designer/neck_templates.json` | JSON | Neck design templates | Exists | None | Neck designer |

### 1h. Tests

| Path | Type | Purpose | Status |
|------|------|---------|--------|
| ✅ `services/api/app/tests/integration/test_fretboard_ecosphere_roundtrip.py` | Test | FretboardEcosphere roundtrip testing | Complete |
| ✅ `services/api/app/tests/calculators/test_scala_loader.py` | Test | Scala temperament loading | Complete |
| ✅ `services/api/app/tests/calculators/test_alternative_temperaments_ntet.py` | Test | Alternative temperament tests | Complete |
| ✅ `services/api/app/tests/test_archtop_floating_bridge.py` | Test | Archtop bridge tests | Complete |
| ✅ `services/api/app/tests/test_bandsaw_physics.py` | Test | Bandsaw physics tests | Complete |

---

## 2. Frontend — Vue/TypeScript

### 2a. Vue Components (.vue files)

| Path | Type | Purpose | Status | Direct Dependencies | Direct Consumers |
|------|------|---------|--------|---------------------|------------------|
| ✅ `packages/client/src/components/FretboardPreviewSvg.vue` | Vue component | Live SVG preview of fretboard with risk coloring | Complete, shipping | `instrumentGeometryStore.ts` | InstrumentGeometryView |
| ✅ `packages/client/src/components/toolbox/FretboardCompoundRadius.vue` | Vue component | Compound radius calculator UI | Complete, shipping | None | Toolbox view |
| ✅ `packages/client/src/views/InstrumentGeometryView.vue` | Vue component | Main instrument geometry view | Complete, shipping | `instrumentGeometryStore.ts` | App router |
| 🧪 `templates/client/views/NeckDesigner.vue` | Vue component | **STUB** — Neck designer placeholder | Scaffolded only | None | Dashboard templates |
| 🧪 `templates/client/views/HeadstockDesigner.vue` | Vue component | **STUB** — Headstock designer placeholder | Scaffolded only | None | Dashboard templates |
| 🧪 `templates/client/views/BridgeDesigner.vue` | Vue component | **STUB** — Bridge designer placeholder | Scaffolded only | None | Dashboard templates |
| 🧪 `templates/client/views/FingerboardDesigner.vue` | Vue component | **STUB** — Fingerboard designer placeholder | Scaffolded only | None | Dashboard templates |
| 🧪 `templates/client/views/ParametricBodyDesigner.vue` | Vue component | **STUB** — Body designer placeholder | Scaffolded only | None | Dashboard templates |

### 2b. Composables (use*.ts files)

| Path | Type | Purpose | Status |
|------|------|---------|--------|
| ✅ `packages/client/src/composables/useCAMIntegration.ts` | Composable | CAM integration utilities | Complete, shipping |
| ✅ `packages/client/src/composables/usePresetQueryBootstrap.ts` | Composable | Preset loading bootstrap | Complete, shipping |

### 2c. Pinia Stores

| Path | Type | Purpose | Status | Direct Dependencies | Direct Consumers |
|------|------|---------|--------|---------------------|------------------|
| ✅ `packages/client/src/stores/instrumentGeometryStore.ts` | Pinia store | Fretboard geometry, CAM preview, feasibility scoring | Complete, shipping | API endpoints | `FretboardPreviewSvg.vue`, `InstrumentGeometryView.vue` |
| ✅ `packages/client/src/stores/neck.ts` | Pinia store | Neck state management | Partial | None | Neck-related views |
| ✅ `packages/client/src/stores/geometry.ts` | Pinia store | Geometry state management | Partial | None | Geometry views |
| ✅ `packages/client/src/stores/fretSlotsCamStore.ts` | Pinia store | Fret slots CAM state | Complete, shipping | API endpoints | Fret slot views |

### 2d. TypeScript Utilities and Types

| Path | Type | Purpose | Status |
|------|------|---------|--------|
| ✅ `packages/client/src/types/fretSlots.ts` | Types | Fret slot type definitions | Complete, shipping |
| ✅ `packages/client/src/stores/instrumentGeometryStore.ts` (types) | Types | FretboardSpec, ToolpathSummary, CAMStatistics, FeasibilityReport | Complete, shipping |

### 2e. API Clients

| Path | Type | Purpose | Status |
|------|------|---------|--------|
| ✅ `packages/client/src/api/v16.ts` | API client | v16 API endpoints | Complete, shipping |
| ✅ `packages/client/src/api/v161.ts` | API client | v161 API endpoints | Complete, shipping |
| ✅ `packages/client/src/services/instrumentApi.ts` | Service | Instrument model fetching | Complete, shipping |

### 2f. Setup Workflow UI Components

| Path | Type | Purpose | Status |
|------|------|---------|--------|
| ❌ | | **No dedicated setup workflow UI exists** | Not implemented |

### 2g. Tests

| Path | Type | Purpose | Status |
|------|------|---------|--------|
| ✅ `packages/client/src/components/compare/compareLayerVisibility.spec.ts` | Test | Compare layer visibility tests | Complete |
| ✅ `packages/client/src/components/compare/compareLayers.spec.ts` | Test | Compare layers tests | Complete |

---

## 3. Documentation

### 3a. Specs and Reference Docs

| Path | Type | Purpose | Status |
|------|------|---------|--------|
| ✅ `CLAUDE.md` (project root) | Markdown | Project instructions, architecture decisions | Active |
| ✅ `services/api/app/ROUTER_CONSOLIDATION_MAP.md` | Markdown | Router consolidation documentation | Active |
| ✅ `services/api/app/ROUTER_SAFETY_AUDIT.md` | Markdown | Router safety audit | Active |

### 3b. Sprint Handoffs

| Path | Type | Purpose | Status |
|------|------|---------|--------|
| ✅ `SPRINTS.md` | Markdown | Sprint tracking and history | Active |

### 3c. Architectural Decision Records

| Path | Type | Purpose | Status |
|------|------|---------|--------|
| ✅ `CLAUDE.md` — VECTORIZER ARCHITECTURE section | ADR | Vectorizer feedback loop architecture | Approved, awaiting implementation |

### 3d. Setup-Related Documentation

| Path | Type | Purpose | Status |
|------|------|---------|--------|
| ❌ | | **No dedicated setup procedure documentation** | Not implemented |

---

## 4. Sandbox / Experimental

| Path | Type | Purpose | Status |
|------|------|---------|--------|
| 🧪 `templates/client/views/NeckDesigner.vue` | Stub | Neck designer UI placeholder | Scaffolded |
| 🧪 `templates/client/views/HeadstockDesigner.vue` | Stub | Headstock designer UI placeholder | Scaffolded |
| 🧪 `templates/client/views/BridgeDesigner.vue` | Stub | Bridge designer UI placeholder | Scaffolded |
| 🧪 `templates/client/views/FingerboardDesigner.vue` | Stub | Fingerboard designer UI placeholder | Scaffolded |

---

## 5. Standalone Repos (Referenced in this repo)

Based on references in this repo's docs and CLAUDE.md:

| Repo | Relationship | Purpose |
|------|--------------|---------|
| `ltb-woodworking-studio` | Sibling project | Independent woodworking studio with own wood data, no HTTP dependency on luthiers-toolbox |
| `tap_tone_pi` | Reference pattern | AGE (Agentic Guidance Engine) pattern for vectorizer integration |

---

## Cross-References

### A. Endpoint Surface Map

#### Neck Region

| Method | Path | Module:Function | Returns | Frontend Consumer |
|--------|------|-----------------|---------|-------------------|
| POST | `/api/v1/fretboard/compute` | `api_v1/fretboard.py:post_compute` | FretboardEcosphere JSON | `instrumentGeometryStore.ts` |
| POST | `/api/v1/fretboard/dxf` | `api_v1/fretboard.py:post_dxf` | DXF bytes | Download button |
| POST | `/api/v1/fretboard/scala` | `api_v1/fretboard.py:post_scala` | Scala scale JSON or .scl file | Export button |
| GET | `/api/v1/fretboard/presets` | `api_v1/fretboard.py:get_presets` | Preset list | Preset selector |
| GET | `/api/v1/fretboard/presets/{name}` | `api_v1/fretboard.py:get_preset_by_name` | FretboardInput | Preset loader |
| GET | `/api/v1/fretboard/schema` | `api_v1/fretboard.py:get_schema` | JSON Schema | Client validation |

#### Setup Specs

| Method | Path | Module:Function | Returns | Frontend Consumer |
|--------|------|-----------------|---------|-------------------|
| POST | `/api/instrument-geometry/setup/evaluate` | `setup_router.py:evaluate_instrument_setup` | SetupCascadeResponse | Not wired |

#### String Physics

| Method | Path | Module:Function | Returns | Frontend Consumer |
|--------|------|-----------------|---------|-------------------|
| POST | `/api/instrument-geometry/string-tension/compute` | `string_tension_router.py` | SetTensionResult | Not wired |

#### Bridge Region

| Method | Path | Module:Function | Returns | Frontend Consumer |
|--------|------|-----------------|---------|-------------------|
| GET | `/api/instrument-geometry/bridges` | `bridge_router.py` | Bridge presets | Not wired |
| POST | `/api/saddle-compensation/design` | `saddle_compensation_router.py` | DesignCalculatorResult | Not wired |
| POST | `/api/saddle-compensation/setup` | `saddle_compensation_router.py` | SetupCalculatorResult | Not wired |

### B. Frontend → Backend Call Graph

| Frontend File | Endpoint Called | Notes |
|---------------|-----------------|-------|
| `instrumentGeometryStore.ts:generatePreview()` | `POST /api/cam/fret_slots/preview` | CAM preview with feasibility |
| `instrumentGeometryStore.ts:loadInstrumentModels()` | `GET /api/instrument/models` | Dynamic model loading |
| `FretboardPreviewSvg.vue` | (consumes store, no direct API) | Renders from store state |
| **GAPS:** | | |
| No frontend consumer | `POST /setup/evaluate` | Setup cascade not wired |
| No frontend consumer | `POST /string-tension/compute` | String tension not wired |
| No frontend consumer | `GET /bridges` | Bridge presets not wired |
| No frontend consumer | `POST /saddle-compensation/*` | Saddle compensation not wired |

### C. Duplication and Overlap Report

#### Duplicate: Fret Position Computation

**Canonical:** `services/api/app/instrument_geometry/neck/fretboard_ecosphere.py:_compute_fret_positions_for_temperament()`  
**Legacy:** `services/api/app/instrument_geometry/neck/fret_math.py:compute_fret_positions_mm()`

**Verdict:** `fretboard_ecosphere.py` delegates to the kernel via `alternative_temperaments.py`. Not a true duplicate — proper separation of concerns.

#### Duplicate: Neck Profile Generation

**Location 1:** `services/api/app/generators/neck_headstock_geometry.py:generate_neck_profile_points()`  
**Location 2:** `services/api/app/instrument_geometry/neck/neck_profiles.py`

**Verdict:** Need investigation — may be complementary (one for visualization, one for CAM).

#### Duplicate: Bridge Preset Data

**Location 1:** `services/api/app/instrument_geometry/bridge/electric_bridges.py:ELECTRIC_BRIDGES`  
**Location 2:** `services/api/app/instrument_geometry/bridge/floyd_rose_tremolo.py`

**Verdict:** Floyd Rose is a separate, detailed module; ELECTRIC_BRIDGES is the summary database. Floyd Rose is intentionally separate due to schematic-derived precision. NOT a duplicate.

### D. Coverage Gaps

| Feature | Exists | Partially Exists | Absent | Priority for Interactive Neck Designer |
|---------|--------|------------------|--------|----------------------------------------|
| **Nut slot CAM (toolpath for cutting nut slots)** | | | ❌ | **Definitely needed** |
| **Truss rod channel routing CAM** | ✅ | | | Already implemented |
| **String tension calculator** | ✅ | | | Already implemented |
| **Per-string saddle compensation calculator** | ✅ | | | Already implemented |
| **Neck relief specification engine** | | 🟡 Setup cascade checks ranges | | Definitely needed — extend setup_cascade |
| **Action specification engine (12th/17th fret)** | | 🟡 Setup cascade checks ranges | | Definitely needed — extend setup_cascade |
| **Pickup height specification engine** | | | ❌ | Maybe needed |
| **Intonation procedure / iterative tuner workflow** | | | ❌ | Definitely needed |
| **Buzz diagnosis logic / diagnostic tree** | | | ❌ | Definitely needed |
| **Setup history tracking / customer profile persistence** | | | ❌ | Definitely needed |
| **String gauge selection recommendation logic** | | | ❌ | Maybe needed |
| **Tuning variation handling (drop, open, alternative)** | | 🟡 DROP_D_TUNING_HZ exists | | Definitely needed — extend |
| **Bridge type abstraction (fixed/tremolo/acoustic/headless/classical)** | ✅ | | | Already implemented |
| **Headless bridge / Smart Guitar specific bridge geometry** | | | ❌ | Definitely needed |
| **Tremolo system geometry (Floyd Rose, Strat, Bigsby, Kahler)** | ✅ | | | Floyd Rose complete, others partial |
| **Acoustic bridge geometry (pin spacing, bridge plate, saddle slot)** | | 🟡 | | Definitely needed |
| **Classical tie-block bridge geometry** | | | ❌ | Maybe needed |
| **Tuner hole positioning by headstock layout (3+3/6-in-line/4+2/slotted)** | ✅ | | | Already implemented |
| **Headless tuner positioning (Smart Guitar)** | | | ❌ | Definitely needed |
| **Side dot positions on neck side** | | | ❌ | Maybe needed |
| **Fret marker / inlay positions on fretboard face** | | 🟡 FretboardPreviewSvg has hardcoded positions | | Definitely needed |
| **Headstock veneer geometry** | | | ❌ | Maybe needed |
| **Volute geometry** | | | ❌ | Maybe needed |
| **Scarf joint geometry** | | | ❌ | Maybe needed |
| **Heel transition CAM** | | 🟡 neck/orchestrator.py | | Definitely needed |
| **Neck shimming geometry / neck angle adjustment** | | | ❌ | Maybe needed |
| **Strap button position recommendations** | | | ❌ | Maybe needed |
| **Player profile data structure** | | | ❌ | Definitely needed |
| **Setup workflow guided sequence UI** | | | ❌ | **Definitely needed** |
| **Before/after measurement comparison UI** | | | ❌ | Definitely needed |

### E. Existing Interactive Components

| Component | What It Is | What It Does | API Called | State Sharing | Parameters Exposed |
|-----------|------------|--------------|------------|---------------|-------------------|
| `FretboardPreviewSvg.vue` | SVG canvas | Renders fretboard outline, fret slots with risk coloring, inlay markers | None (consumes store) | `instrumentGeometryStore` | spec, toolpaths, width, height, showLabels, showInlays, showRiskLegend, riskColoring |
| `FretboardCompoundRadius.vue` | Calculator tool | Compound radius calculations | Unknown | Isolated | Unknown |
| `InstrumentGeometryView.vue` | Main view | Orchestrates geometry UI | Via store | `instrumentGeometryStore` | Full fretboard spec |

### F. State Management Surface

| Store | State Held | Actions | Consuming Components | Persistence |
|-------|------------|---------|---------------------|-------------|
| `instrumentGeometryStore` | selectedModelId, fretboardSpec, previewResponse, fanFretEnabled, trebleScaleLength, bassScaleLength, perpendicularFret | selectModel, generatePreview, downloadDxf, downloadGcode, reset, loadInstrumentModels | `FretboardPreviewSvg.vue`, `InstrumentGeometryView.vue` | Session only |
| `neck.ts` | Unknown | Unknown | Unknown | Unknown |
| `geometry.ts` | Unknown | Unknown | Unknown | Unknown |
| `fretSlotsCamStore.ts` | Fret slot CAM state | Unknown | Fret slot views | Session only |

### G. Recommendation: Components to Keep, Retire, Extend

#### Keep (Reusable)

| Component | Rationale |
|-----------|-----------|
| `FretboardEcosphere` | Canonical doc pattern — extend to NeckEcosphere |
| `fret_math.py` | Core math kernel — production-proven |
| `alternative_temperaments.py` | Temperament support — production-proven |
| `string_tension.py` | Physics-based calculation — production-proven |
| `setup_cascade.py` | Setup evaluation logic — extend for full setup workflow |
| `saddle_compensation.py` | Both design and setup modes — production-proven |
| `electric_bridges.py` | Comprehensive bridge database |
| `floyd_rose_tremolo.py` | Schematic-derived precision — exemplar for other tremolo systems |
| `truss_rod_channel.py` | CAM generation — production-proven |
| `FretboardPreviewSvg.vue` | Live SVG preview — extend for full neck preview |
| `instrumentGeometryStore.ts` | State management pattern — extend for setup workflow |

#### Retire (Replace or Absorb)

| Component | Rationale |
|-----------|-----------|
| Template stubs (`NeckDesigner.vue`, `BridgeDesigner.vue`, etc.) | Replace with real implementations |

#### Extend

| Component | Extension Needed |
|-----------|------------------|
| `setup_cascade.py` | Add diagnostic trees, guided workflow steps, player profiles |
| `instrumentGeometryStore.ts` | Add setup workflow state, before/after comparison |
| `FretboardPreviewSvg.vue` | Add neck back profile preview, nut slots, string markers |
| `fretboard_presets.py` | Add player style presets (light touch, heavy strummer, etc.) |

### H. Schema / Canonical Doc Analysis — NeckEcosphere Field Union

Based on fields scattered across existing modules, a unified `NeckEcosphere` canonical doc would need:

```python
class NeckEcosphere:
    # === From FretboardEcosphere ===
    input_params: NeckInput
    fret_lines: List[FretLine]
    string_paths: List[StringPath]
    outline_points: List[Tuple[float, float]]
    total_length_mm: float
    max_width_mm: float
    max_fret_angle_deg: float

    # === Neck Profile (from neck_profiles.py, neck_headstock_geometry.py) ===
    profile_type: NeckProfile  # C_SHAPE, D_SHAPE, V_SHAPE, ASYMMETRIC
    depth_at_nut_mm: float
    depth_at_12th_mm: float
    depth_at_heel_mm: float
    profile_cross_sections: List[NeckCrossSection]  # At key positions

    # === Headstock (from neck_headstock_geometry.py) ===
    headstock_style: HeadstockStyle
    headstock_outline: List[Tuple[float, float]]
    headstock_angle_deg: float
    tuner_positions: List[Tuple[float, float]]
    string_tree_positions: List[StringTreeSpec]

    # === Nut (from nut_slot_calc.py) ===
    nut_width_mm: float
    nut_slot_schedule: List[NutSlotSpec]
    nut_material: Optional[str]

    # === Truss Rod (from truss_rod_channel.py) ===
    truss_rod_type: TrussRodType  # SINGLE_ACTION, DUAL_ACTION
    truss_rod_channel: TrussRodChannelSpec
    truss_rod_access: str  # HEADSTOCK, HEEL

    # === String Tension (from string_tension.py) ===
    string_set: List[StringSpec]
    string_tensions: List[TensionResult]
    total_tension_lb: float
    total_tension_n: float

    # === Scale Length (from FretboardInput) ===
    scale_type: ScaleType
    scale_length_mm: float
    bass_scale_length_mm: Optional[float]
    perpendicular_fret: int

    # === Setup State (from setup_cascade.py) ===
    setup_state: Optional[SetupState]
    setup_evaluation: Optional[SetupCascadeResult]

    # === Intonation (from saddle_compensation.py) ===
    intonation_offsets_mm: Dict[int, float]
    saddle_compensation_result: Optional[DesignCalculatorResult]

    # === Fret Markers (new) ===
    fret_marker_positions: List[int]  # [3, 5, 7, 9, 12, 15, 17, 19, 21, 24]
    fret_marker_style: str  # DOT, BLOCK, CUSTOM

    # === Bridge Reference (cross-ref to BridgeEcosphere) ===
    bridge_type: str
    bridge_reference_x_mm: float  # Distance from nut to bridge centerline
    saddle_radius_mm: Optional[float]
    string_spacing_at_bridge_mm: float

    # === Player Profile (new) ===
    player_profile: Optional[PlayerProfile]

    # === Metadata ===
    version: str
    computed_at: datetime
```

**Note:** This is the *union* of fields from scattered modules. The actual NeckEcosphere design should be done in a separate specification document after reviewing this audit.

---

## Summary

### What Exists (Strong Foundation)
- ✅ Complete `FretboardEcosphere` canonical doc with FRET-A ecosphere
- ✅ String tension physics calculator with D'Addario unit weights
- ✅ Setup cascade evaluation with GREEN/YELLOW/RED gates
- ✅ Saddle compensation (both design and setup modes)
- ✅ Electric bridge database (Fender, Gibson, Floyd Rose)
- ✅ Floyd Rose tremolo with full schematic-derived dimensions
- ✅ Neck profile geometry (C, D, V shapes)
- ✅ Headstock outline generation (Gibson, Fender, PRS, Martin, Benedetto, Classical)
- ✅ Tuning machine calculator (post height, break angle, string trees)
- ✅ Truss rod channel CAM
- ✅ Fret slot CAM (standard and fan-fret)
- ✅ Frontend store for fretboard geometry

### What's Missing (Critical Gaps for Interactive Neck Designer)
- ❌ **Nut slot CAM** — no toolpath generation for nut cutting
- ❌ **Setup workflow UI** — backend exists but no frontend
- ❌ **Player profile data structure** — no persistence
- ❌ **Buzz diagnosis tree** — no diagnostic logic
- ❌ **Intonation procedure workflow** — no iterative tuner UI
- ❌ **Setup history tracking** — no before/after comparison
- ❌ **Headless/Smart Guitar bridge geometry** — missing
- ❌ **Fret marker position system** — hardcoded in SVG component
- ❌ **Designer stubs** — NeckDesigner, BridgeDesigner, HeadstockDesigner are empty

### Recommended Next Steps
1. Design `NeckEcosphere` schema following FRET-A pattern
2. Extend `setup_cascade.py` with diagnostic trees and guided workflow
3. Build setup workflow UI consuming the setup/evaluate endpoint
4. Implement nut slot CAM using nut_slot_calc.py geometry
5. Add player profile persistence (localStorage + backend)
6. Replace template stubs with real interactive designers

---

*End of audit document*
