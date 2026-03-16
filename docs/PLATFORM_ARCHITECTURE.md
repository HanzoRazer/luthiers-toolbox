# The Production Shop — Platform Architecture
## Developer Guide

**Version:** 1.0  
**Status:** Active — supersedes all prior architecture docs  
**Location:** `/docs/PLATFORM_ARCHITECTURE.md`

---

## What This Platform Is

The Production Shop is **not a toolbox of independent features**.

It is a **design operating system for musical instruments** — a system where every feature orbits a single authoritative object: the `InstrumentProject`.

That distinction matters for every decision you will make here. When you are unsure where a new feature belongs, where a calculation should live, or why a folder is structured the way it is, come back to this document.

---

## The Four Layers

```
Layer 0 — Instrument Project Graph     ← the center of gravity
Layer 1 — Engines                       ← geometry math, materials reasoning
Layer 2 — Workspaces                    ← where builders spend their time
Layer 3 — Utilities                     ← quick stateless tools
```

Understanding these four layers is the only thing you need to navigate this codebase correctly.

---

## Layer 0 — Instrument Project Graph

**The single source of design truth.**

Every instrument build lives in one object:

```python
# services/api/app/schemas/instrument_project.py
class InstrumentProjectData(BaseModel):
    schema_version: str                              # "1.0" — increment on breaking changes
    instrument_type: str                             # "acoustic_guitar" | "electric_guitar" | "bass" | ...
    spec: InstrumentSpec                             # scale, frets, nut/heel widths, neck angle
    blueprint_geometry: Optional[BlueprintDerivedGeometry]  # from Blueprint Reader
    bridge_state: Optional[BridgeState]             # saddle, compensation, break angle
    neck_state: Optional[NeckState]                 # profile, angle, taper
    material_selection: Optional[MaterialSelection] # top, back/sides, neck, fretboard, bridge, bracing
    analyzer_observations: List[AnalyzerObservation] # acoustic measurements — advisory only
    manufacturing_state: Optional[ManufacturingState] # CAM approval state
```

**What belongs here (persisted):**
- Instrument type and spec (scale length, fret count, neck angle, string count, nut width)
- Blueprint-derived geometry with provenance
- Bridge geometry state (saddle location, compensation offsets, break angle)
- Neck geometry state
- Material selections per component role
- Analyzer observations as advisory enrichment

**What does NOT belong here (derived — never store):**
- Fret positions (always compute from `spec.scale_length_mm`)
- String tension values (compute from gauges + tuning + scale)
- Break angle (compute from `bridge_state` inputs via Geometry Engine)
- Saddle compensation offsets (compute from string gauges + scale length)
- Stiffness indices (compute from `material_selection` + Materials Engine)
- CAM toolpaths (generate from validated project state on demand)

**Database location:**  
The project schema is stored in `Project.data` (JSONB) in the existing `projects` table — no additional database tables required.

**API surface:**
```
GET  /api/projects/{id}/design-state
PUT  /api/projects/{id}/design-state
```

**Frontend access:**
```typescript
// packages/client/src/instrument-workspace/shared-state/useInstrumentProject.ts
// Never access project state directly from UI components — always through this composable
```

---

## Layer 1 — Engines

**Pure computation and reasoning. No UI. No persistence.**

Engines accept inputs and return outputs. They are tested in isolation. They have no knowledge of Vue, no imports from Pinia, and no calls to the database.

### Geometry Engine

**Location:** `services/api/app/instrument_geometry/`

Responsible for:
- Fret spacing and fretboard geometry
- Bridge placement and saddle line computation
- Break angle calculation (v2 corrected model — see `docs/BRIDGE_BREAK_ANGLE_DERIVATION.md`)
- Pickup cavity placement and centerline computation
- Body volume, overhang channel geometry
- Neck taper and profile math
- Alternative temperament fret deviations

**Sub-packages:**
```
instrument_geometry/
├── bridge/        ← placement.py, compensation.py, break_angle.py
├── neck/          ← fret_math.py, neck_profiles.py, radius_profiles.py
├── body/          ← centerline.py, outlines.py, parametric.py
├── pickup/        ← cavity_placement.py
├── neck_taper/    ← taper_math.py, neck_outline_generator.py
└── utilities/     ← shared math modules (consolidation target)
```

### Materials Intelligence Engine

**Location:** `services/api/app/materials/`

Responsible for:
- Wood species registry (473 species)
- Curated tonewood reference (71 species with acoustic properties)
- Acoustic property reasoning (radiation ratio, stiffness-to-weight, impedance)
- Machining guidance per species (feed/speed limits, burn risk, tearout, dust hazard)
- Material comparison and recommendation logic

**Sub-packages:**
```
materials/
├── registry/      ← wood_species.py, tonewoods.py, normalization.py, queries.py
├── acoustics/     ← wood_acoustics.py, reference_matching.py
├── machining/     ← wood_limits.py, recommendation.py, hazards.py
├── recommendation/ ← compare.py, suggest.py
└── schemas.py
```

**Raw data lives at:** `data_registry/system/materials/` (wood_species.json, luthier_tonewood_reference.json)  
Do not read raw JSON from routers or UI — always go through the `materials/` service layer.

### Acoustic Analyzer Engine

**Location:** `services/api/app/analyzer/`

Responsible for:
- Interpreting tap-tone measurements from tap-tone-pi (hard boundary — we consume `viewer_pack` only, never import tap-tone-pi code)
- Modal visualization and Chladni pattern classification
- Wolf tone risk assessment (WSI — Wolf Susceptibility Index)
- Design recommendations from measured acoustic behavior
- Reference instrument cohort matching

Analyzer outputs feed `AnalyzerObservation` in the project graph — advisory only. The analyzer enriches project state. It does not override `material_selection`, `bridge_state`, or `spec`.

---

## Layer 2 — Workspaces

**User-facing editing environments.**

Workspaces are where builders spend their time. They read project state, support local editing, and commit changes explicitly. They do not contain engine math. They do not own design truth.

### The commit pattern (required for all workspaces):

```
1. Load project state on entry
2. Edit local state (component-level reactivity)
3. Show derived values (calling engines via API)
4. On user confirmation → PUT /api/projects/{id}/design-state
```

Never mutate project state implicitly. Never auto-save derived values.

### Current workspaces:

| Workspace | Frontend location | What it edits |
|-----------|-------------------|---------------|
| Blueprint Reader | `design-intake/blueprint/` | `blueprint_geometry` |
| Instrument Hub | `instrument-workspace/hub/` | Full project — primary editor |
| Bridge Lab | `instrument-workspace/acoustic/bridge/` | `bridge_state` |
| Art Studio | `art-studio/` | Decorative/pattern geometry |
| Analyzer | `analyzer/` | Writes `analyzer_observations` only |
| CAM tools | `manufacturing/` | Reads validated project state |

### Future workspace pattern (Bridge Lab is the template):

When adding **Neck Lab**, **Body Lab**, or **Bracing Lab**, follow the Bridge Lab pattern exactly:
- Bounded local state in the workspace composable
- Loads from project on entry
- Calls Geometry Engine for math (never inline)
- Commits to project on explicit user action

---

## Layer 3 — Utilities

**Stateless tools. Never own project truth.**

Utilities are calculators. They compute values. They do not save anything unless the user explicitly chooses "Apply to Project." The same calculator works identically in standalone mode and in project context — the only difference is that project context pre-fills inputs from the active project.

### Two modes (required for all utilities):

**Standalone mode** — tool runs independently, no project required.

**Project context mode** — when an active project exists, inputs are pre-filled from project state. Results can be applied back via explicit action. Never auto-applied.

### Utility locations:

**Frontend:** `packages/client/src/design-utilities/`
```
design-utilities/
├── lutherie/          ← fret spacing, neck angle, break angles, string tension, pickup layout
├── wood-intelligence/ ← species browser, stiffness index, compare, board feet, moisture
└── scientific/        ← general calculator
```

**Backend:** `routers/design/utilities_router.py`  
All utility endpoints live under `/api/design/utilities/*` — one router, one prefix.

**Nav location:** Under **Design** in the sidebar, labeled **Utilities** — not under Business.

---

## Where New Features Go

**Before writing any code, answer this question:**

> Is this a Source, Engine, Workspace, or Utility?

```
Does it ingest external design data?  →  DESIGN INTAKE (Layer 2 / Blueprint)
Does it edit instrument design state? →  WORKSPACE    (Layer 2)
Does it perform math or reasoning?    →  ENGINE       (Layer 1)
Does it analyze signals/sensors?      →  ANALYZER ENGINE (Layer 1)
Is it a quick standalone tool?        →  UTILITY      (Layer 3)
```

If a feature fits more than one category, it is probably trying to do too much. Split it.

### Decision tree:

```
New feature request
       │
       ▼
Does it modify or create InstrumentProjectData?
       │
   YES │                              NO
       ▼                              ▼
  Is it the entry           Does it compute values?
  point (intake)?                     │
       │                    YES       │       NO
   YES │                    ▼         │       ▼
       ▼                  ENGINE   Is it purely
  DESIGN INTAKE       (Layer 1)    presentation/
  Blueprint Reader    No state     interaction?
  DXF import         No UI            │
                                  YES │
                                      ▼
                                   UTILITY
                                  (Layer 3)
                                  Stateless
```

---

## Folder Ownership Reference

| What | Backend location | Frontend location |
|------|-----------------|-------------------|
| Project schema | `schemas/instrument_project.py` | `shared-state/project-types.ts` |
| Project persistence | `projects/service.py` | `useInstrumentProject.ts` |
| Geometry math | `instrument_geometry/` | Never — accessed via API |
| Materials data | `materials/` | `design-utilities/wood-intelligence/composables/` |
| Blueprint pipeline | `blueprint/` (phases 1–4) | `design-intake/blueprint/` |
| Bridge workspace | `routers/design/instrument_router.py` | `instrument-workspace/acoustic/bridge/` |
| Utilities API | `routers/design/utilities_router.py` | `design-utilities/` |
| Art/ornament | `art_studio/` | `art-studio/` |
| CAM/manufacturing | `cam/routers/` | `manufacturing/` |
| Analyzer | `analyzer/` | `analyzer/` |
| System/registry | `routers/system/` + `routers/registry_router.py` | `api/registry.ts` |

---

## Anti-Patterns — Do Not Do These

### 1. Math inside Vue components

```python
# WRONG — break angle formula in BridgeCalculator.vue
angleDeg = Math.atan(saddle_h / pin_dist) * 180 / Math.PI

# CORRECT — call the engine
response = await api.post('/api/design/utilities/bridge-break-angle', {...})
```

### 2. Hardcoded species or material data in frontend

```typescript
// WRONG
const WOOD_DENSITIES = { spruce: 425, cedar: 370, mahogany: 545 }

// CORRECT — fetch from registry
const { tonewoods } = useTonewoods()
```

### 3. Utility auto-writing to project state

```typescript
// WRONG — string tension panel writes directly on compute
watchEffect(() => { project.string_tension = computeTension() })

// CORRECT — user clicks "Apply to Project"
function applyToProject() {
  projectStore.commit({ spec: { ...spec, gauges: currentGauges } })
}
```

### 4. Stale Pinia stores surviving alongside project graph

When a feature is migrated to read/write `InstrumentProjectData`, the corresponding legacy Pinia store must be deprecated and removed. Do not leave parallel state systems running.

```
// STORES SCHEDULED FOR RETIREMENT (as each phase completes):
instrumentGeometryStore  ← retire after HUB-002
geometry.ts store        ← retire after BRIDGE-002
bridge local state       ← retire after BRIDGE-003
```

### 5. Analyzer overriding project design state

```python
# WRONG — analyzer writes to bridge_state directly
project.bridge_state.compensation = analyzer.inferred_compensation

# CORRECT — analyzer writes an observation only
project.analyzer_observations.append(AnalyzerObservation(
    run_id=run_id,
    finding="compensation appears low for selected material combination",
    confidence=0.72
))
```

### 6. Two competing material authority paths

There are currently two material-related systems: `routers/registry_router.py` (wood species / tonewoods) and `routers/material_router.py` (CNC cutting energy / heat partition). These are being unified. When adding any wood/material feature, route through the new `materials/` domain — do not extend either legacy router.

---

## The Full Data Flow

```
Blueprint Reader
    ↓ writes BlueprintDerivedGeometry
Instrument Project Graph  ←──────── Analyzer (enriches with AnalyzerObservation)
    ↓ reads/writes
Instrument Hub
    ↓ contains
Bridge Lab / Neck Lab / Body Lab / Bracing Lab
    ↓ calls
Geometry Engine          Materials Intelligence
    ↓                         ↓
Derived results (not stored)  Material data (feeds Wood Intelligence UI)
    ↓
Utilities (optional quick tools, standalone or project-context)
    ↓
Manufacturing Layer (reads validated project state → CAM → CNC)
```

---

## Naming Conventions

| Thing | Convention | Example |
|-------|-----------|---------|
| Project schema field | `snake_case` | `bridge_state`, `material_selection` |
| Vue composable | `use` prefix | `useInstrumentProject`, `useBridgeWorkspace` |
| Vue panel component | `*Panel.vue` | `BridgeGeometryPanel.vue` |
| Vue workspace shell | `*Shell.vue` or `*Hub.vue` | `InstrumentHubShell.vue` |
| Backend schema | PascalCase Pydantic model | `InstrumentProjectData`, `BridgeState` |
| Backend service | `*_service.py` | `project_service.py` |
| Backend engine module | noun describing the domain | `break_angle.py`, `placement.py` |
| API route | kebab-case | `/api/design/utilities/bridge-break-angle` |
| Frontend API client | camelCase function | `getDesignState()`, `putDesignState()` |

---

## Key Documents in `/docs`

| Document | What it covers |
|----------|---------------|
| `PLATFORM_ARCHITECTURE.md` ← **this file** | Layer model, ownership rules, anti-patterns |
| `BRIDGE_BREAK_ANGLE_DERIVATION.md` | v2 corrected break angle geometry (Carruth 6° empirical) |
| `ANALYZER_BOUNDARY_SPEC.md` | Hard boundary between tap-tone-pi and this platform |
| `ROUTER_CONSOLIDATION_ROADMAP.md` | Ongoing router reduction plan |
| `REMEDIATION_STATUS_MARCH_2026.md` | Current codebase health metrics |
| `GAP_ANALYSIS_MASTER.md` | Known missing tools and PHYS gaps |
| `STORE_MIGRATION_POSTGRES.md` | SQLite ↔ PostgreSQL backend switching |
| `adr/` | Architecture Decision Records — decisions that should not be re-litigated |

---

## The Golden Rule

```
No feature should bypass the Instrument Project Graph.

Every feature must:
  read     — from project state or engines
  derive   — computed values from engine inputs
  suggest  — advisory recommendations (Analyzer, Materials)
  commit   — explicit user-confirmed writes to project state

The Project Graph is the kernel.
Engines are the compute layer.
Workspaces are the applications.
Utilities are the helper tools.
```

If you are building a feature and you cannot answer **where it commits its output**, stop and resolve that question before writing code.
