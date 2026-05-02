# Developer Handoff — Feature Implementation Guide

**Date:** 2026-03-16
**Status:** Active development bundles ready for integration
**Platform:** The Production Shop (luthiers-toolbox)

---

## Executive Summary

This document provides implementation guidance for 14 feature bundles staged in working folders. Each bundle contains production-ready code with schemas, composables, and components that need integration into the main codebase.

**Architecture:** All features follow the 4-layer model defined in `PLATFORM_ARCHITECTURE.md`:
- **Layer 0:** Instrument Project Graph (single source of design truth)
- **Layer 1:** Engines (pure computation, no UI)
- **Layer 2:** Workspaces (editing environments)
- **Layer 3:** Utilities (stateless tools)

---

## Part 1: Feature Bundles Overview

### Active Bundles (11)

| # | Folder | Feature | Target Layer | Priority |
|---|--------|---------|--------------|----------|
| 1 | `files - 2026-03-15T003501.238/` | String Tension Calculator | Layer 3 (Utility) | HIGH |
| 2 | `files - 2026-03-15T010734.117/` | Lutherie Geometry Panel | Layer 3 (Utility) | HIGH |
| 3 | `files - 2026-03-15T065003.210/` | Stiffness Index Panel | Layer 3 (Utility) | HIGH |
| 4 | `files - 2026-03-15T182348.417/` | Instrument Project Graph | Layer 0 (Core) | CRITICAL |
| 5 | `files - 2026-03-15T183010.895/` | Blueprint Save Feature | Layer 2 (Workspace) | MEDIUM |
| 6 | `files - 2026-03-15T184511.509/` | Instrument Hub Shell | Layer 2 (Workspace) | HIGH |
| 7 | `files - 2026-03-15T185317.088/` | Bridge Lab Workspace | Layer 2 (Workspace) | HIGH |
| 8 | `files - 2026-03-15T190701.210/` | Tonewood Materials System | Layer 1 (Engine) | HIGH |
| 9 | `files - 2026-03-15T193643.776/` | Calculator Panel Revisions | Layer 3 (Utility) | MEDIUM |
| 10 | `files - 2026-03-15T195528.162/` | Router Wiring Final | Layer 0/2 | MEDIUM |
| 11 | `files - 2026-03-14T032048.923/` | Rosette/Inlay Design Tools | Layer 2 (Art Studio) | LOW |

### Superseded Bundles (4) — Do Not Integrate

| Folder | Content | Status |
|--------|---------|--------|
| `files - 2026-03-14T091530.552/` | Vectorizer patches 01-03 | Superseded |
| `files - 2026-03-14T114707.020/` | Vectorizer patches 05-06 | Superseded |
| `files - 2026-03-14T134741.895/` | Vectorizer patches 08-12 | Superseded |
| `files - 2026-03-14T160945.705/` | Vectorizer patches 11-16 | Superseded |
| `patch_04_real_photo_fixes.py` | Vectorizer patch 04 | Superseded |

---

## Part 2: Implementation Order (Recommended)

```
Phase 1 — Foundation (Critical Path)
  └── Bundle 4: Instrument Project Graph (Layer 0)
       ├── instrument_project.py → services/api/app/schemas/
       ├── project_service.py → services/api/app/projects/
       └── project_router.py → services/api/app/routers/design/

Phase 2 — Materials Engine
  └── Bundle 8: Tonewood Materials System (Layer 1)
       ├── materials_schemas.py → services/api/app/materials/
       ├── materials_router.py → services/api/app/materials/
       ├── materials_tonewoods.py → services/api/app/materials/
       └── useTonewoods.ts → packages/client/src/composables/

Phase 3 — Calculator Utilities
  ├── Bundle 1: String Tension Calculator
  ├── Bundle 2: Lutherie Geometry Panel
  ├── Bundle 3: Stiffness Index Panel
  └── Bundle 9: Calculator Panel Revisions

Phase 4 — Workspaces
  ├── Bundle 6: Instrument Hub Shell
  ├── Bundle 7: Bridge Lab Workspace
  └── Bundle 5: Blueprint Save Feature

Phase 5 — Art Studio (Deferred)
  └── Bundle 11: Rosette/Inlay Design Tools
```

---

## Part 3: Bundle Details with Code References

### Bundle 4: Instrument Project Graph (CRITICAL)

**Purpose:** Single source of design truth for all instrument builds.

**Files:**
```
files - 2026-03-15T182348.417/
├── instrument_project.py      # 23KB — Core schema
├── project_service.py         # 6KB  — CRUD service
├── project_router.py          # 9KB  — API endpoints
├── ADR-002-instrument-project-graph.md
└── PLATFORM_ARCHITECTURE.md   # 16KB — Master architecture doc
```

**Key Schema (instrument_project.py:41-51):**
```python
class InstrumentProjectData(BaseModel):
    schema_version: str                              # "1.0"
    instrument_type: str                             # "acoustic_guitar" | "electric_guitar" | ...
    spec: InstrumentSpec                             # scale, frets, nut/heel widths, neck angle
    blueprint_geometry: Optional[BlueprintDerivedGeometry]
    bridge_state: Optional[BridgeState]
    neck_state: Optional[NeckState]
    material_selection: Optional[MaterialSelection]
    analyzer_observations: List[AnalyzerObservation]
    manufacturing_state: Optional[ManufacturingStatus]
```

**API Endpoints:**
```
GET  /api/projects/{id}/design-state
PUT  /api/projects/{id}/design-state
```

**Integration Target:**
- Schema: `services/api/app/schemas/instrument_project.py`
- Service: `services/api/app/projects/service.py`
- Router: `services/api/app/routers/design/instrument_router.py`

---

### Bundle 8: Tonewood Materials System

**Purpose:** Wood species registry with acoustic indices and machining data.

**Files:**
```
files - 2026-03-15T190701.210/
├── materials_schemas.py       # 10KB — TonewoodEntry, MachiningNotes, compare/recommend
├── materials_router.py        # 8KB  — API endpoints
├── materials_scorer.py        # 7KB  — Role suitability scoring
├── materials_tonewoods.py     # 7KB  — Registry loader
├── InstrumentMaterialSelector.vue  # 14KB — UI component
└── useTonewoods.ts            # 7KB  — Frontend composable
```

**Key Schema (materials_schemas.py:77-204):**
```python
class TonewoodEntry(BaseModel):
    id: str
    name: str
    density_kg_m3: Optional[float]
    modulus_of_elasticity_gpa: Optional[float]
    typical_uses: List[str]

    # Computed acoustic indices (never stored)
    @computed_field
    def radiation_ratio(self) -> Optional[float]:
        """Schelleng c/ρ — primary soundboard quality index."""

    @computed_field
    def specific_moe(self) -> Optional[float]:
        """E/ρ — stiffness per unit mass."""

    @computed_field
    def ashby_index(self) -> Optional[float]:
        """E^(1/3)/ρ — plate bending index."""

    @computed_field
    def acoustic_impedance_mrayl(self) -> Optional[float]:
        """ρ×c — energy transfer at joints."""
```

**Integration Target:**
- Backend: `services/api/app/materials/` (new domain)
- Frontend: `packages/client/src/composables/useTonewoods.ts`

---

### Bundle 1: String Tension Calculator

**Purpose:** String tension physics with balance scoring and set analysis.

**Files:**
```
files - 2026-03-15T003501.238/
├── useTension.ts              # 10KB — Core physics composable
├── StringTensionPanel.vue     # 32KB — UI panel
├── CalculatorHub.vue          # 8KB  — Container shell
├── presets.ts                 # 16KB — String set presets (D'Addario, Elixir, etc.)
├── types.ts                   # 9KB  — TypeScript interfaces
├── useBreakAngle.ts           # 6KB  — Break angle computation
└── uwTable.ts                 # 5KB  — Unit weight lookup table
```

**Core Physics (useTension.ts:63-65):**
```typescript
/**
 * String tension: T = UW × (2LF)² / 386.4
 */
export function calcTension(unitWeightLbIn: number, scaleLengthIn: number, frequencyHz: number): number {
  return unitWeightLbIn * Math.pow(2 * scaleLengthIn * frequencyHz, 2) / G
}
```

**Balance Score (useTension.ts:71-79):**
```typescript
/**
 * Balance: 1.0 = perfectly matched, 0.0 = unbalanced.
 * Based on coefficient of variation, penalized at 2.5×.
 */
export function calcBalanceScore(tensionsLbs: number[]): number {
  const cv = stdDev / mean
  return Math.max(0, Math.min(1, 1 - cv * 2.5))
}
```

**Integration Target:**
- `packages/client/src/design-utilities/lutherie/string-tension/`

---

### Bundle 3: Stiffness Index Panel

**Purpose:** Tonewood acoustic index calculator (radiation ratio, specific MOE, Ashby index).

**Files:**
```
files - 2026-03-15T065003.210/
├── useStiffnessIndex.ts       # 10KB — Acoustic index composable
├── StiffnessIndexPanel.vue    # 22KB — UI panel
├── tonewoodData.ts            # 15KB — Hardcoded fallback + API loader
├── ScientificCalculator.vue   # 6KB  — General calculator
├── WoodworkPanel.vue          # 6KB  — Board feet, moisture
└── calculator-index.ts        # 555B — Export barrel
```

**Acoustic Index Functions (useStiffnessIndex.ts:60-80):**
```typescript
// Speed of sound: c = √(E/ρ)
export function calcSpeedOfSound(moeGpa: number, densityKgM3: number): number {
  return Math.sqrt((moeGpa * 1e9) / densityKgM3)
}

// Radiation ratio: c/ρ × 1000 (Schelleng index)
export function calcRadiationRatio(speedMs: number, densityKgM3: number): number {
  return (speedMs / densityKgM3) * 1000
}

// Ashby plate index: E^(1/3) / ρ
export function calcAshbyIndex(moeGpa: number, densityKgM3: number): number {
  return Math.pow(moeGpa * 1000, 1/3) / densityKgM3
}
```

**Integration Target:**
- `packages/client/src/design-utilities/wood-intelligence/stiffness/`

---

### Bundle 6: Instrument Hub Shell

**Purpose:** Primary editing environment for instrument projects.

**Files:**
```
files - 2026-03-15T184511.509/
├── InstrumentHubShell.vue     # 29KB — Main workspace shell
├── useInstrumentProject.ts    # 10KB — Project state composable
├── projects_api.ts            # 8KB  — API client
└── project-types.ts           # 5KB  — TypeScript types
```

**Project State Pattern (useInstrumentProject.ts):**
```typescript
// Load → Edit → Commit pattern (required for all workspaces)
export function useInstrumentProject() {
  const project = ref<InstrumentProjectData | null>(null)

  async function load(projectId: string) {
    project.value = await api.get(`/api/projects/${projectId}/design-state`)
  }

  async function commit() {
    await api.put(`/api/projects/${project.value.id}/design-state`, project.value)
  }

  return { project, load, commit }
}
```

**Integration Target:**
- `packages/client/src/instrument-workspace/hub/`

---

### Bundle 7: Bridge Lab Workspace

**Purpose:** Bridge geometry editing (saddle, compensation, break angle).

**Files:**
```
files - 2026-03-15T185317.088/
├── BridgeLabPanel.vue         # 16KB — Bridge workspace UI
└── useBridgeWorkspace.ts      # 9KB  — Bridge state composable
```

**Bridge State Pattern (useBridgeWorkspace.ts):**
```typescript
// Workspace edits BridgeState within the project
export function useBridgeWorkspace(project: Ref<InstrumentProjectData>) {
  const localBridge = ref<BridgeState>({ ...project.value.bridge_state })

  // Derived values from Geometry Engine (never store)
  const breakAngle = computed(() =>
    calcBreakAngle(localBridge.value.saddle_height_mm, localBridge.value.pin_distance_mm)
  )

  function applyToProject() {
    project.value.bridge_state = { ...localBridge.value }
  }

  return { localBridge, breakAngle, applyToProject }
}
```

**Integration Target:**
- `packages/client/src/instrument-workspace/acoustic/bridge/`

---

## Part 4: Key Architecture Rules

### Rule 1: Never Store Derived Values

```python
# WRONG — storing computed fret positions
class InstrumentProjectData:
    fret_positions: List[float]  # ❌ NEVER

# CORRECT — compute on demand
def get_fret_positions(scale_length_mm: float, fret_count: int) -> List[float]:
    return [scale_length_mm - (scale_length_mm / (2 ** (n / 12))) for n in range(fret_count + 1)]
```

### Rule 2: Math Lives in Engines, Not Components

```typescript
// WRONG — physics in Vue component
const breakAngle = computed(() => Math.atan(saddle / pin) * 180 / Math.PI)  // ❌

// CORRECT — call engine via API
const { data: breakAngle } = await api.post('/api/design/utilities/bridge-break-angle', {
  saddle_height_mm: saddle.value,
  pin_distance_mm: pin.value
})
```

### Rule 3: Explicit Commit Pattern

```typescript
// WRONG — auto-saving on every change
watch(localState, () => api.put(...))  // ❌

// CORRECT — user confirms changes
function applyToProject() {
  projectStore.commit({ bridge_state: localBridge.value })
}
```

### Rule 4: Two Utility Modes

All utilities must support:
1. **Standalone mode** — runs without project context
2. **Project context mode** — pre-fills inputs from active project, offers "Apply to Project"

```typescript
function useStringTension(project?: Ref<InstrumentProjectData>) {
  // Standalone: empty defaults
  // Project context: pre-fill from project.spec.scale_length_mm
  const scaleLength = ref(project?.value?.spec?.scale_length_mm ?? 25.5)
}
```

---

## Part 5: File Placement Reference

| Component Type | Backend Location | Frontend Location |
|----------------|------------------|-------------------|
| Project schema | `schemas/instrument_project.py` | `shared-state/project-types.ts` |
| Materials engine | `materials/` | N/A (API only) |
| Geometry engine | `instrument_geometry/` | N/A (API only) |
| Calculator utilities | `routers/design/utilities_router.py` | `design-utilities/` |
| Workspaces | `routers/design/instrument_router.py` | `instrument-workspace/` |
| Art Studio | `art_studio/` | `art-studio/` |

---

## Part 6: Testing Requirements

### Backend

```bash
# Unit tests for each engine function
pytest services/api/tests/test_instrument_project.py -v
pytest services/api/tests/test_materials_engine.py -v

# API smoke tests for new endpoints
pytest services/api/tests/test_design_utilities_smoke.py -v
```

### Frontend

```bash
# Composable tests
npm run test:composables

# Component tests (Vitest)
npm run test -- --filter="StringTensionPanel"
```

---

## Part 7: Quick Reference — API Endpoints

### Project Graph

```
GET  /api/projects/{id}/design-state
PUT  /api/projects/{id}/design-state
```

### Materials

```
GET  /api/registry/tonewoods
GET  /api/registry/tonewoods/{id}
POST /api/system/materials/compare
POST /api/system/materials/recommend
```

### Design Utilities

```
POST /api/design/utilities/bridge-break-angle
POST /api/design/utilities/string-tension
POST /api/design/utilities/fret-spacing
POST /api/design/utilities/stiffness-index
```

---

## Appendix A: Bundle File Inventory

| Bundle | Files | Total Size |
|--------|-------|------------|
| 1. String Tension | 7 | 88KB |
| 2. Lutherie Geometry | 5 | 50KB |
| 3. Stiffness Index | 6 | 61KB |
| 4. Instrument Project | 5 | 60KB |
| 5. Blueprint Save | 4 | 41KB |
| 6. Instrument Hub | 4 | 54KB |
| 7. Bridge Lab | 2 | 26KB |
| 8. Materials System | 6 | 56KB |
| 9. Calculator Revisions | 4 | 49KB |
| 10. Router Wiring | 2 | 13KB |
| 11. Rosette Tools | 11 | 6.3MB |
| **Total Active** | **56 files** | **~6.8MB** |

---

## Appendix B: Superseded Technology

The following vectorizer patches are **not for integration**:

```
patch_01_scale_calibration.py      ⚪ Superseded
patch_02_multi_instrument_split.py ⚪ Superseded
patch_03_body_isolator.py          ⚪ Superseded
patch_04_real_photo_fixes.py       ⚪ Superseded
patch_05_coin_color_filter.py      ⚪ Superseded
patch_06_orientation_detector.py   ⚪ Superseded
patch_08_material_bom.py           ⚪ Superseded
patch_09_grain_visualization.py    ⚪ Superseded
patch_10_parallel_batch.py         ⚪ Superseded
patch_11_ml_classifier.py          ⚪ Superseded
patch_12_body_fixes_gcode.py       ⚪ Superseded
patch_13_two_pass_calibration.py   ⚪ Superseded
patch_14_gated_adaptive_close.py   ⚪ Superseded
patch_15_pipeline_wiring.py        ⚪ Superseded
patch_16_perspective_diagnostic.py ⚪ Superseded
```

These represent a deprecated photo vectorizer approach. The current blueprint pipeline uses a different architecture.

---

*End of Developer Handoff Document*
