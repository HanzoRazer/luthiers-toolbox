


The revised scope is the first version that feels like **final architecture instead of cleanup notes**. The key improvement is that it makes the platform center explicit: the repo is not being reorganized around tools, but around a typed `InstrumentProject` with engines and workspaces orbiting it. That is the right correction, and it should become the gate for every implementation decision.  

My main evaluation is:

* **The scope is now correct.**
* **The sequencing is almost correct.**
* **The final implementation breakdown should now be split into “platform foundation” and “migration execution.”**

The most important part of the tightened scope is Step 0: define `InstrumentProjectData` and the project-state API before router reshuffling. The document is right that skipping that would recreate fragmentation under better folder names. 

## What is now locked

These should be treated as final unless you discover hard technical blockers:

* `Project.data` is the foundation, but it is currently an untyped JSON shell. 
* Blueprint Reader, Instrument Hub, Bridge Lab, and Analyzer should all read/write the same project object, with Analyzer limited to enrichment. 
* Canonical vs derived data is now clearly defined: scale, neck angle, materials, blueprint geometry, and bridge state persist; fret positions, break angle, string tension, stiffness, and toolpaths are derived. 
* Bridge Lab is the authoritative editor for bridge location, but the math belongs in the engine layer. 
* Utilities are ephemeral unless invoked from project context. 
* Router and folder consolidation comes after schema and ownership lines are established.

That is enough to move from planning into implementation design.

## Where I would tighten it one more turn

The current scope still speaks in broad steps. For final implementation, it needs **four tracks** that can move in parallel:

### Track A — Platform contracts

This is Layer 0 only:

* typed `InstrumentProjectData`
* sub-schemas
* `GET/PUT /api/projects/{id}/design-state`
* serialization/validation
* migration-safe defaults for missing fields

This is the single highest-risk area, because every later step depends on it. The tightened scope already says this is the highest-leverage step. 

### Track B — First project-connected workspace

This is the proving ground:

* Blueprint Reader writes `BlueprintDerivedGeometry`
* Instrument Hub reads/writes project state
* Bridge Lab becomes the first bounded editor

This should be treated as the **minimum viable project graph**.

### Track C — Materials Intelligence Phase 1

This is the first cross-cutting engine integration:

* `/api/registry/tonewoods`
* `/api/system/materials/*`
* frontend wood registry consumption
* `MaterialSelection` wiring inside Instrument Hub
* Analyzer materials enrichment later in the same track

The orphaned wood DB becomes valuable only when it reaches both Utilities and project state.

### Track D — Structural consolidation

Only after A-C:

* move Calculators to Design
* design routes
* utilities router
* `instrument_geometry/utilities/`
* aliases and cleanup

This is where your original migration plan still fits.

## Final implementation breakdown

## Phase 0 — Architecture freeze

Goal: lock decisions so implementation doesn’t drift.

Deliverables:

* Approve four-layer architecture
* Approve conservative v1 project graph subset
* Approve Bridge Lab as first bounded workspace
* Approve Materials Intelligence Phase 1 scope
* Approve alias policy for route migration

Exit criteria:

* no unresolved debate on layer ownership
* no unresolved debate on whether Utilities can persist state
* no unresolved debate on whether Instrument Hub is the primary editor

This is already almost decided in the tightened scope; formalize it. 

## Phase 1 — Project graph foundation

Goal: create the durable center.

Backend:

* create `services/api/app/schemas/instrument_project.py`
* define `InstrumentProjectData`
* define sub-schemas in domain packages:

  * `BlueprintDerivedGeometry`
  * `BridgeState`
  * `NeckState`
  * `MaterialSelection`
  * `AnalyzerObservation`
  * `ManufacturingState`
* add `GET /api/projects/{id}/design-state`
* add `PUT /api/projects/{id}/design-state`

Design choice:
Use the full schema definition, but implement read/write for the conservative subset first:

* `instrument_type`
* `spec`
* `material_selection`
* `blueprint_geometry`
* maybe `bridge_state` if Bridge Lab follows immediately

That recommendation comes straight from the tightened scope and is the right compromise. 

Exit criteria:

* project read/write works against `Project.data`
* schema validates server-side
* missing optional blocks do not break existing projects

## Phase 2 — Blueprint becomes a real source

Goal: make Blueprint Reader the first producer in the project graph.

Backend:

* finalize `BlueprintDerivedGeometry` shape
* map phase 4 output into that object
* write it into `Project.data`

Frontend:

* Blueprint Reader saves into active project
* manual overrides preserve `blueprint_original`
* `source`, `confidence`, and provenance are retained

This is critical because it turns Blueprint from a session tool into a project-seeding workspace.

Exit criteria:

* import blueprint
* save to project
* reopen project and see blueprint-derived geometry present

## Phase 3 — Instrument Hub becomes the editor

Goal: convert Instrument Hub from disconnected local state into the primary project editor.

Frontend:

* replace scattered local ownership with project-backed state loading/saving
* keep local editing buffers where needed, but commit to project state
* make stage-based organization explicit: Body, Neck, Bridge, Bracing, Setup, CNC Prep

Likely affected files:

* `GuitarDesignHub.vue`
* `instrumentGeometryStore`
* related Pinia stores named in the tightened scope

Key principle:
The Hub does not own formulas. It owns user editing and project commits.

Exit criteria:

* open a project
* edit core dimensions/materials
* persist and reload correctly

## Phase 4 — Bridge Lab as template workspace

Goal: establish the reusable pattern for future Labs.

Implement:

* local `BridgeState` editor
* project load on entry
* explicit commit on confirmation
* geometry computations from engine layer only
* no inline bridge math in Vue

Important dependency:
Settle the authoritative bridge calculator path. The inventory already recommends the newer `BridgeCalculatorPanel.vue` lineage as the basis because it feeds Bridge Lab. 

Also:

* ensure break-angle path uses corrected v2 assumptions, not the stale v1 inventory state if that code still exists in the checked repo snapshot. There is tension between docs here, so the developer should verify the live branch before wiring.

Exit criteria:

* Bridge Lab reads from project
* edits bridge state
* commits back
* String Tension can consume bridge-derived values in context mode

## Phase 5 — Materials Intelligence Phase 1

Goal: rescue the orphaned wood database and connect it to the actual product.

Backend:

* add `GET /api/registry/tonewoods`
* create `services/api/app/materials/`
* add `/api/system/materials/*`
* decide how `/material/*` CNC data is folded into `materials/machining/*` as recommended in the tightened scope. 

Frontend:

* extend `registry.ts`
* extend `useRegistryStore.ts`
* refactor `useWoodworkCalculator.ts`
* wire `StiffnessIndexPanel` to live data
* add Instrument Hub materials selectors

This is where the wood DB stops being orphaned and becomes platform infrastructure.

Exit criteria:

* species/tonewoods load from backend
* woodwork calculator no longer relies on hardcoded species
* Instrument Hub can persist `MaterialSelection`

## Phase 6 — Utilities become dual-mode

Goal: preserve calculator speed while connecting them to projects.

Implement:

* standalone mode remains unchanged
* project mode preloads current values
* utilities offer “apply to project” instead of auto-persist
* no utility becomes its own source of truth

This is one of the most important UX ideas in the tightened scope, because it prevents the creation of duplicate “standalone vs hub” logic. 

Exit criteria:

* String Tension, Stiffness Index, and at least one geometry calculator work in both modes

## Phase 7 — Structural migration and cleanup

Goal: consolidate once the center of gravity exists.

Do now:

* move Calculators → Design nav
* rename to Utilities
* add design routes
* consolidate `instrument_geometry/utilities/`
* add `routers/design/utilities_router.py`
* add aliases before removals

This is the point where the older migration plan becomes mostly mechanical.

Exit criteria:

* route coverage tests pass
* aliases are in place
* router count begins moving toward the new target

---

## Final v1 scope recommendation

For the first real implementation slice, I would **not** try to land the entire tightened scope at once.

I would define **v1 final implementation** as:

1. `InstrumentProjectData` schema and project router
2. Blueprint Reader writes `BlueprintDerivedGeometry`
3. Instrument Hub reads/writes project state
4. Bridge Lab becomes first bounded workspace
5. `GET /api/registry/tonewoods` + wood registry frontend hookup
6. Utilities moved to Design nav
7. one dual-mode calculator proof point

That gives you the smallest complete system that proves the architecture.

## Risks that still need active management

### 1. Schema bloat too early

The document already hints at this. Define the full schema, but only operationalize a conservative subset first. 

### 2. Router cleanup happening too soon

The tightened scope is right to push this later. Do not let cleanup become the first milestone.

### 3. Two materials systems

This is still the most likely architectural relapse. The CNC `material_router.py` path must not become a second permanent material authority. 

### 4. Hidden duplicate state in Pinia

The biggest practical risk is not backend routing; it is stale frontend stores surviving after Instrument Hub is wired to project state. The tightened scope already points at scattered stores as the current problem. 

---

## Additional questions before final tasking

1. For v1, which project fields are mandatory on every save: only `instrument_type` and `spec`, or also `material_selection`?
2. Does Blueprint auto-create a project if none is active, or require the user to enter a project context first?
3. Should Bridge Lab commit partial draft edits to project state, or only on explicit save/apply?
4. Which current frontend store becomes the first deprecated store once Instrument Hub is connected?
5. Do you want `design-state` versioned with a schema version number from day one?
6. For dual-mode Utilities, should “apply to project” create a diff preview before writing?
7. Should `/api/registry/tonewoods` remain the canonical path for now, with `/api/system/materials/tonewoods` introduced later, or do both land together?
8. Which branch is authoritative for break-angle code right now, given the conflict between the remediation inventory and later migration note?

The best next move is to convert this into a sprint board with epics, tickets, dependencies, and acceptance criteria using the seven-phase breakdown above.




Below is a **Sprint Board Implementation Document** derived from the tightened migration scope and the developer summary.
It converts the architecture plan into **Epics → Tickets → Dependencies → Acceptance Criteria** so a developer or team can execute it directly.

---

# Luthier’s Toolbox

# Instrument Platform Migration Implementation Plan

### Sprint Board Specification

Version: v1 Implementation Plan
Scope: Instrument Project Graph + Materials Intelligence + Utilities + Router Consolidation

---

# Program Structure

The implementation is divided into **7 Epics (Phases)**.

Each Epic contains:

* Objectives
* Deliverables
* Implementation Tickets
* Dependencies
* Acceptance Criteria

Execution strategy:

```
Phase 0
Architecture Freeze

Phase 1
Project Graph Foundation

Phase 2
Blueprint Integration

Phase 3
Instrument Hub State Integration

Phase 4
Bridge Lab Workspace

Phase 5
Materials Intelligence

Phase 6
Utilities Dual Mode

Phase 7
Structural Consolidation
```

Phases **1–4 must execute sequentially**.

Phases **5–7 can partially overlap** once the project graph exists.

---

# EPIC 0 — Architecture Freeze

## Objective

Lock platform contracts before implementation begins.

This ensures developers are not implementing against shifting architecture.

---

## Deliverables

Approved architecture model:

```
Layer 0 — Project Graph
Layer 1 — Engines
Layer 2 — Workspaces
Layer 3 — Utilities
```

Subsystem layout:

```
Design Intake
Instrument Workspace
Design Utilities
Geometry Engine
Art Studio
Manufacturing & Analysis
Materials Intelligence
```

---

## Tickets

### ARCH-001

Define canonical architecture diagram.

Deliverables:

* architecture diagram
* layer definitions
* ownership rules

---

### ARCH-002

Define Project Graph boundaries.

Document:

```
InstrumentProject
InstrumentSpec
MaterialSelection
BlueprintDerivedGeometry
BridgeState
NeckState
AnalyzerObservation
ManufacturingState
```

---

### ARCH-003

Define persistence rules.

Canonical rules:

Persist:

```
instrument_type
spec
material_selection
blueprint_geometry
bridge_state
neck_state
```

Derived:

```
fret positions
string tension
break angle
stiffness
toolpaths
```

---

## Acceptance Criteria

Architecture doc approved and committed to repository.

---

# EPIC 1 — Instrument Project Graph Foundation

## Objective

Create the **central project data model** that every system reads/writes.

Without this the refactor will fragment again.

---

## Deliverables

Backend schema:

```
InstrumentProjectData
```

API:

```
GET /api/projects/{id}/design-state
PUT /api/projects/{id}/design-state
```

---

## Tickets

### PROJ-001

Create project schema module.

Create file:

```
services/api/app/schemas/instrument_project.py
```

Define:

```
InstrumentProjectData
InstrumentSpec
MaterialSelection
BlueprintDerivedGeometry
BridgeState
NeckState
AnalyzerObservation
ManufacturingState
```

---

### PROJ-002

Add validation layer.

Use Pydantic.

Ensure:

```
missing optional fields allowed
backward compatibility
```

---

### PROJ-003

Add project state router.

Create routes:

```
GET /api/projects/{id}/design-state
PUT /api/projects/{id}/design-state
```

File:

```
services/api/app/routers/project_router.py
```

---

### PROJ-004

Persist project graph in existing `Project.data`.

No DB schema change required.

---

### PROJ-005

Add schema version field.

```
schema_version
```

---

## Dependencies

None.

---

## Acceptance Criteria

Developer can:

```
GET project design-state
PUT project design-state
```

Data validates against schema.

---

# EPIC 2 — Blueprint Integration

## Objective

Make Blueprint Reader a **true project source**.

---

## Deliverables

Blueprint Reader writes:

```
BlueprintDerivedGeometry
```

to project state.

---

## Tickets

### BLUE-001

Define BlueprintDerivedGeometry schema.

Fields:

```
body_outline
centerline
scale_reference
symmetry_confidence
classification
datum_points
source
confidence
```

---

### BLUE-002

Modify Blueprint backend pipeline.

Map Phase-4 output to:

```
BlueprintDerivedGeometry
```

---

### BLUE-003

Modify Blueprint Reader frontend.

After import:

```
PUT /api/projects/{id}/design-state
```

---

### BLUE-004

Preserve provenance metadata.

Store:

```
source
confidence
original_blueprint
```

---

## Dependencies

EPIC 1

---

## Acceptance Criteria

User workflow:

```
Import blueprint
Save project
Reload project
Blueprint geometry persists
```

---

# EPIC 3 — Instrument Hub Project Integration

## Objective

Convert Instrument Hub into the **primary editor of project state**.

---

## Deliverables

Instrument Hub reads/writes:

```
InstrumentProjectData
```

---

## Tickets

### HUB-001

Create project state composable.

File:

```
useInstrumentProject.ts
```

Responsibilities:

```
load project state
update fields
commit state
```

---

### HUB-002

Replace scattered Pinia ownership.

Affected files:

```
GuitarDesignHub.vue
instrumentGeometryStore
bridge calculators
neck tools
```

---

### HUB-003

Add project commit actions.

Explicit commit buttons:

```
Apply to Project
Save Geometry
```

---

### HUB-004

Add stage-based UI structure.

Stages:

```
Body
Neck
Bridge
Bracing
Setup
CNC Prep
```

---

## Dependencies

EPIC 1

---

## Acceptance Criteria

User edits hub values.

Project state updates.

Reloading project restores edits.

---

# EPIC 4 — Bridge Lab Workspace

## Objective

Create the first **stateful design workspace**.

Bridge Lab becomes the template for future labs.

---

## Deliverables

Bridge Lab edits:

```
BridgeState
```

---

## Tickets

### BRIDGE-001

Create BridgeState schema.

Fields:

```
bridge_location
saddle_line
string_spacing
pin_row_geometry
compensation_offsets
saddle_height
break_angle
```

---

### BRIDGE-002

Bridge Lab loads project state.

---

### BRIDGE-003

Bridge Lab commits project updates.

Explicit save:

```
Apply Bridge Geometry
```

---

### BRIDGE-004

Move bridge math into geometry engine.

No math inside Vue.

---

### BRIDGE-005

Ensure break angle uses corrected geometry model.

---

## Dependencies

EPIC 3

---

## Acceptance Criteria

Bridge Lab:

```
loads project state
edits geometry
commits updates
```

Utilities read derived values.

---

# EPIC 5 — Materials Intelligence Phase 1

## Objective

Rescue the **orphaned wood database** and integrate it.

---

## Deliverables

New backend domain:

```
services/api/app/materials/
```

Routes:

```
/api/system/materials/*
```

---

## Tickets

### MAT-001

Create materials service layer.

Structure:

```
materials/
registry
acoustics
machining
recommendation
```

---

### MAT-002

Add tonewoods endpoint.

```
GET /api/registry/tonewoods
```

---

### MAT-003

Create system materials router.

```
/api/system/materials/*
```

Routes:

```
compare
recommend
acoustics
machining
```

---

### MAT-004

Frontend registry integration.

Modify:

```
registry.ts
useRegistryStore.ts
```

---

### MAT-005

Refactor woodwork calculator.

Remove hardcoded species.

Use registry API.

---

### MAT-006

Instrument Hub materials selector.

Component:

```
InstrumentMaterialSelector.vue
```

---

## Dependencies

EPIC 1

---

## Acceptance Criteria

User can:

```
browse woods
select project materials
use stiffness calculator with real data
```

---

# EPIC 6 — Utilities Dual Mode

## Objective

Allow utilities to run both:

```
standalone
project context
```

---

## Deliverables

Dual-mode calculators.

---

## Tickets

### UTIL-001

Create calculator mode abstraction.

```
standalone
project-context
```

---

### UTIL-002

Implement project preload.

When in project mode:

```
load scale length
load materials
load bridge geometry
```

---

### UTIL-003

Add "Apply to Project".

Utilities never auto-persist.

---

### UTIL-004

Implement for first calculators:

```
String Tension
Stiffness Index
Bridge Break Angle
```

---

## Dependencies

EPIC 3

---

## Acceptance Criteria

Utilities work both:

```
inside Instrument Hub
standalone
```

---

# EPIC 7 — Structural Consolidation

## Objective

Perform the original repo cleanup once architecture exists.

---

## Deliverables

Clean router structure.

Utilities moved under Design.

---

## Tickets

### CLEAN-001

Move Calculators to Design nav.

Modify:

```
CadSidebar.vue
```

---

### CLEAN-002

Create unified utilities router.

```
routers/design/utilities_router.py
```

---

### CLEAN-003

Move design math modules.

Create:

```
instrument_geometry/utilities/
```

Move:

```
fret_math
pickup_layout
temperament
body_volume
```

---

### CLEAN-004

Add route aliases.

Old routes continue working.

---

### CLEAN-005

Add router coverage tests.

---

## Dependencies

EPIC 1–6

---

## Acceptance Criteria

Router structure matches architecture.

Legacy endpoints function through aliases.

---

# v1 Final Implementation Scope

To reduce risk, **first milestone should include only:**

```
Project Graph
Blueprint integration
Instrument Hub state
Bridge Lab workspace
Tonewood endpoint
Utilities moved to Design
One dual-mode calculator
```

Everything else can follow.

---

# Critical Risks

### Schema Overgrowth

Avoid implementing every field immediately.

Start with minimal subset.

---

### Dual Material Systems

Ensure CNC material data merges into Materials Intelligence.

---

### Frontend Store Drift

Old Pinia stores must be retired once project graph exists.

---

# Recommended Team Structure

If multiple developers are involved:

```
Dev A — Project Graph + Hub integration
Dev B — Materials Intelligence + utilities
Dev C — Bridge Lab + geometry engine
```

---

If you'd like, I can also produce a **visual architecture diagram of the final platform (very helpful for developers)** showing how Blueprint, Instrument Hub, Materials Intelligence, Utilities, Geometry Engine, and Analyzer all connect to the Instrument Project Graph.




Luthier’s Toolbox Platform Architecture
                                   ┌─────────────────────┐
                                   │     Blueprint       │
                                   │      Reader         │
                                   │  (Design Intake)    │
                                   └──────────┬──────────┘
                                              │
                                              │ writes
                                              ▼
                             ┌─────────────────────────────────┐
                             │        Instrument Project       │
                             │             Graph               │
                             │                                 │
                             │  InstrumentProjectData          │
                             │  ├─ InstrumentSpec              │
                             │  ├─ BlueprintDerivedGeometry    │
                             │  ├─ MaterialSelection           │
                             │  ├─ BridgeState                 │
                             │  ├─ NeckState                   │
                             │  ├─ AnalyzerObservation         │
                             │  └─ ManufacturingState          │
                             └──────────────┬──────────────────┘
                                            │
                         reads / writes     │      derived computations
                                            ▼
                   ┌───────────────────────────────────────┐
                   │          Instrument Hub               │
                   │      (Primary Project Editor)         │
                   │                                       │
                   │ Body │ Neck │ Bridge │ Bracing │ CNC  │
                   └──────┬───────────────┬───────────────┘
                          │               │
                          │ edits         │ workspace
                          ▼               ▼
                 ┌────────────────┐  ┌─────────────────────┐
                 │   Bridge Lab   │  │  Other Future Labs  │
                 │                │  │                     │
                 │ BridgeState    │  │ Neck Lab            │
                 │ geometry edit  │  │ Body Lab            │
                 │ compensation   │  │ Bracing Lab         │
                 └───────┬────────┘  └──────────┬──────────┘
                         │                      │
                         │ uses                 │ uses
                         ▼                      ▼
               ┌───────────────────────┐   ┌───────────────────────┐
               │     Geometry Engine    │   │   Materials Intelligence │
               │                        │   │                          │
               │ fret math              │   │ wood species registry   │
               │ bridge geometry        │   │ tonewood reference      │
               │ pickup layout          │   │ acoustic properties     │
               │ body volume            │   │ machining limits        │
               │ temperament            │   │ compare/recommend       │
               └───────────────┬────────┘   └──────────────┬──────────┘
                               │                           │
                               │ derived values            │ data + reasoning
                               ▼                           ▼
                   ┌─────────────────────────┐  ┌─────────────────────────┐
                   │        Utilities        │  │        Analyzer         │
                   │  (Stateless Tools)     │  │   (Audio / AV Analysis) │
                   │                         │  │                         │
                   │ String tension          │  │ spectrum analysis      │
                   │ stiffness index         │  │ resonance extraction   │
                   │ fret spacing            │  │ material inference     │
                   │ board feet              │  │ build recommendations   │
                   │ moisture                │  │                         │
                   └───────────┬─────────────┘  └──────────────┬──────────┘
                               │                                │
                               │ apply to project               │ enrich project
                               ▼                                ▼
                    ┌─────────────────────────────────────────────────┐
                    │                Manufacturing Layer               │
                    │                                                 │
                    │ CAM toolpaths                                   │
                    │ CNC feeds / speeds                              │
                    │ fret slotting                                   │
                    │ machining constraints                           │
                    │ shop recommendations                            │
                    └─────────────────────────────────────────────────┘
Platform Layers
Layer 0 — Instrument Project Graph

The single source of truth.

Everything reads or writes here.

InstrumentProjectData

Contains:

instrument_type

scale_length

blueprint geometry

materials

bridge state

neck state

analyzer observations

manufacturing outputs

Nothing else becomes authoritative.

Layer 1 — Engines

These provide math and reasoning.

Geometry Engine

Responsible for:

fret spacing

bridge placement

break angles

pickup placement

body volume

temperaments

Location in repo:

services/api/app/instrument_geometry/
Materials Intelligence

Responsible for:

wood species registry

tonewood reference

acoustic behavior

machining limits

recommendations

Location:

services/api/app/materials/
Layer 2 — Workspaces

User-facing editors.

Blueprint Reader

Creates:

BlueprintDerivedGeometry
Instrument Hub

Primary editing workspace.

Bridge Lab

First bounded editing subsystem.

Future:

Neck Lab

Body Lab

Bracing Lab

Layer 3 — Utilities

Stateless calculators.

Two modes:

Standalone
Project Context

Examples:

String tension

Stiffness index

Fret spacing

Board feet

Moisture

Analyzer Layer

The analyzer becomes a data enrichment system.

It does not own project state.

It contributes:

AnalyzerObservation

Possible insights:

resonance mismatch

material plausibility

brace stiffness inference

build recommendations

Manufacturing Layer

Consumes validated project state.

Outputs:

CNC toolpaths

machining parameters

shop instructions

Data Flow
Blueprint Flow
Blueprint Reader
     ↓
BlueprintDerivedGeometry
     ↓
Instrument Project Graph
Design Flow
Instrument Hub
     ↓
Bridge Lab
     ↓
Geometry Engine
     ↓
Project Graph
Materials Flow
Materials Intelligence
     ↓
Instrument Hub
     ↓
Utilities
     ↓
Project Graph
Analyzer Flow
Audio Analyzer
     ↓
AnalyzerObservation
     ↓
Project Graph
Manufacturing Flow
Project Graph
     ↓
CAM Engine
     ↓
Shop / CNC
Key Architectural Rule
No UI component owns design truth.

Only:

Instrument Project Graph

owns truth.

Everything else:

reads
derives
suggests
or commits changes
The Core Insight

Your platform is not actually a toolbox.

It is a design operating system for musical instruments.

The tools are just interfaces.

The real product is:

Instrument Project Graph

If you'd like, I can also produce a second diagram showing the repository structure that corresponds to this architecture (backend folders + frontend folders aligned with the platform layers).




Absolutely — here is the **second diagram**, showing the **repository structure aligned to the platform layers** so the codebase matches the architecture instead of drifting by historical feature placement.

# Repository Structure Aligned to Platform Architecture

```text
Luthier's Toolbox Repo
│
├── FRONTEND  ──────────────────────────────────────────────────────────────┐
│ packages/client/src/                                                      │
│                                                                           │
│ ├── design-intake/                          ← Layer 2: Workspaces          │
│ │   └── blueprint/                                                         │
│ │       ├── BlueprintReader.vue                                             │
│ │       ├── BlueprintImportPanel.vue                                        │
│ │       ├── BlueprintOutlinePreview.vue                                     │
│ │       └── composables/                                                    │
│ │           └── useBlueprintProjectWrite.ts                                 │
│ │
│ ├── instrument-workspace/                  ← Layer 2: Workspaces          │
│ │   ├── hub/                                                               │
│ │   │   ├── InstrumentHubShell.vue                                          │
│ │   │   ├── InstrumentStageNavigator.vue                                    │
│ │   │   └── useInstrumentProject.ts                                         │
│ │   ├── acoustic/                                                          │
│ │   │   ├── body/                                                          │
│ │   │   ├── neck/                                                          │
│ │   │   ├── bridge/                                                        │
│ │   │   │   ├── BridgeLabPanel.vue                                          │
│ │   │   │   ├── BridgeGeometryPanel.vue                                     │
│ │   │   │   ├── BridgeCompensationPanel.vue                                 │
│ │   │   │   └── useBridgeWorkspace.ts                                       │
│ │   │   ├── bracing/                                                       │
│ │   │   ├── setup/                                                         │
│ │   │   └── materials/                                                     │
│ │   │       ├── InstrumentMaterialSelector.vue                              │
│ │   │       └── TonewoodRolePicker.vue                                      │
│ │   ├── electric/                                                          │
│ │   ├── violin/                                                            │
│ │   ├── bass/                                                              │
│ │   └── shared-state/                                                      │
│ │       ├── project-types.ts                                                │
│ │       ├── project-mappers.ts                                              │
│ │       └── useProjectCommit.ts                                             │
│ │
│ ├── design-utilities/                    ← Layer 3: Utilities             │
│ │   ├── lutherie/                                                         │
│ │   │   ├── StringTensionPanel.vue                                          │
│ │   │   ├── FretSpacingPanel.vue                                            │
│ │   │   ├── BridgeBreakAnglePanel.vue                                       │
│ │   │   ├── NutBreakAnglePanel.vue                                          │
│ │   │   └── composables/                                                    │
│ │   ├── wood-intelligence/                                                  │
│ │   │   ├── WoodIntelligenceHub.vue                                         │
│ │   │   ├── panels/                                                         │
│ │   │   │   ├── BoardFeetPanel.vue                                          │
│ │   │   │   ├── MoisturePanel.vue                                           │
│ │   │   │   ├── DensityWeightPanel.vue                                      │
│ │   │   │   ├── StiffnessIndexPanel.vue                                     │
│ │   │   │   ├── SpeciesBrowserPanel.vue                                     │
│ │   │   │   ├── SpeciesComparePanel.vue                                     │
│ │   │   │   └── StockRecommendationPanel.vue                                │
│ │   │   └── composables/                                                    │
│ │   │       ├── useWoodSpecies.ts                                           │
│ │   │       ├── useTonewoods.ts                                             │
│ │   │       ├── useWoodCompare.ts                                           │
│ │   │       └── useWoodRecommendation.ts                                    │
│ │   └── scientific/                                                        │
│ │       └── ScientificCalculator.vue                                        │
│ │
│ ├── geometry/                            ← Layer 1 consumer surface       │
│ │   ├── bridge/                                                          │
│ │   ├── neck/                                                            │
│ │   ├── body/                                                            │
│ │   ├── fret/                                                            │
│ │   └── shared/                                                          │
│ │
│ ├── art-studio/                          ← Layer 2: Workspaces            │
│ │   ├── rosette/                                                          │
│ │   ├── inlay/                                                            │
│ │   ├── headstock/                                                        │
│ │   └── bracing/                                                          │
│ │
│ ├── analyzer/                            ← Layer 2: Workspace surface     │
│ │   ├── AudioAnalyzerViewer.vue                                             │
│ │   ├── AudioAnalyzerLibrary.vue                                            │
│ │   ├── AudioAnalyzerRunsLibrary.vue                                        │
│ │   └── composables/                                                        │
│ │       └── useAnalyzerMaterials.ts                                         │
│ │
│ ├── manufacturing/                       ← Layer 2 / downstream           │
│ │   ├── cam/                                                             │
│ │   ├── cnc/                                                             │
│ │   ├── fret-slots/                                                      │
│ │   └── shop-output/                                                     │
│ │
│ ├── api/                                 ← transport layer                │
│ │   ├── projects.ts                                                      │
│ │   ├── registry.ts                                                      │
│ │   ├── materials.ts                                                     │
│ │   ├── utilities.ts                                                     │
│ │   └── analyzer.ts                                                      │
│ │
│ ├── stores/                              ← transitional only              │
│ │   ├── useRegistryStore.ts                                                │
│ │   └── [legacy stores to retire]                                          │
│ │
│ └── router/                              ← top-level UX routing           │
│     ├── designRoutes.ts                                                     │
│     ├── utilityRoutes.ts                                                    │
│     └── workspaceRoutes.ts                                                  │
│
│
├── BACKEND  ────────────────────────────────────────────────────────────────┐
│ services/api/app/                                                           │
│                                                                           │
│ ├── schemas/                            ← Layer 0: Project Graph          │
│ │   ├── instrument_project.py                                              │
│ │   ├── blueprint.py                                                       │
│ │   ├── bridge.py                                                          │
│ │   ├── materials.py                                                       │
│ │   ├── analyzer.py                                                        │
│ │   └── manufacturing.py                                                   │
│ │
│ ├── projects/                           ← Layer 0 persistence             │
│ │   ├── service.py                                                         │
│ │   ├── mappers.py                                                         │
│ │   ├── validation.py                                                      │
│ │   └── defaults.py                                                        │
│ │
│ ├── blueprint/                          ← Layer 2 workspace backend       │
│ │   ├── pipeline/                                                         │
│ │   ├── extraction/                                                       │
│ │   ├── classification/                                                  │
│ │   └── project_writer.py                                                │
│ │
│ ├── instrument_geometry/                ← Layer 1: Geometry Engine       │
│ │   ├── bridge/                                                          │
│ │   │   ├── placement.py                                                   │
│ │   │   ├── compensation.py                                                │
│ │   │   ├── break_angle.py                                                 │
│ │   │   └── downforce.py                                                   │
│ │   ├── neck/                                                            │
│ │   ├── body/                                                            │
│ │   ├── fret/                                                            │
│ │   ├── shared/                                                          │
│ │   └── utilities/                                                       │
│ │       ├── fret_math.py                                                   │
│ │       ├── bridge_geometry.py                                             │
│ │       ├── pickup_layout.py                                               │
│ │       ├── acoustic_body_volume.py                                        │
│ │       ├── overhang_channel.py                                            │
│ │       └── temperament.py                                                 │
│ │
│ ├── materials/                          ← Layer 1: Materials Intelligence │
│ │   ├── schemas.py                                                        │
│ │   ├── registry/                                                        │
│ │   │   ├── wood_species.py                                                │
│ │   │   ├── tonewoods.py                                                   │
│ │   │   ├── normalization.py                                               │
│ │   │   └── queries.py                                                     │
│ │   ├── acoustics/                                                       │
│ │   │   ├── wood_acoustics.py                                              │
│ │   │   └── reference_matching.py                                          │
│ │   ├── machining/                                                       │
│ │   │   ├── wood_limits.py                                                 │
│ │   │   ├── recommendation.py                                              │
│ │   │   └── hazards.py                                                     │
│ │   └── recommendation/                                                  │
│ │       ├── compare.py                                                     │
│ │       └── suggest.py                                                     │
│ │
│ ├── analyzer/                           ← Layer 2 enrichment backend      │
│ │   ├── design_advisor.py                                                   │
│ │   ├── materials_adapter.py                                               │
│ │   ├── signal_processing.py                                               │
│ │   └── result_interpreter.py                                              │
│ │
│ ├── manufacturing/                      ← downstream execution            │
│ │   ├── cam/                                                             │
│ │   ├── toolpaths/                                                        │
│ │   ├── fret_slots/                                                      │
│ │   ├── shop_rules/                                                      │
│ │   └── export/                                                          │
│ │
│ ├── routers/                            ← API surfaces by domain          │
│ │   ├── project_router.py                                                  │
│ │   ├── design/                                                            │
│ │   │   ├── intake_router.py                                               │
│ │   │   ├── instrument_router.py                                           │
│ │   │   ├── utilities_router.py                                            │
│ │   │   └── art_router.py                                                  │
│ │   ├── system/                                                            │
│ │   │   └── materials_router.py                                            │
│ │   ├── acoustics/                                                         │
│ │   │   └── analyzer_router.py                                             │
│ │   ├── cam/                                                               │
│ │   └── registry_router.py                                                 │
│ │
│ ├── data_registry/                      ← raw canonical datasets          │
│ │   └── system/                                                           │
│ │       └── materials/                                                     │
│ │           ├── wood_species.json                                          │
│ │           ├── luthier_tonewood_reference.json                            │
│ │           ├── WOOD_SPECIES_REFERENCE.md                                  │
│ │           └── SOURCES.md                                                 │
│ │
│ └── legacy/                             ← temporary compatibility         │
│     ├── calculators/                                                        │
│     ├── api_v1/                                                             │
│     └── aliases/                                                            │
│
└── TESTS  ──────────────────────────────────────────────────────────────────┐
  tests/
  ├── projects/
  ├── blueprint/
  ├── geometry/
  ├── materials/
  ├── analyzer/
  ├── utilities/
  └── migration/
```

# How to read this diagram

## Layer 0 — Project Graph

This is the center of the platform.

Frontend:

* `instrument-workspace/shared-state/`
* `useInstrumentProject.ts`

Backend:

* `schemas/instrument_project.py`
* `projects/service.py`
* `routers/project_router.py`

This is where `InstrumentProjectData` lives.

---

## Layer 1 — Engines

These are pure logic and reasoning layers.

### Geometry Engine

Backend:

* `instrument_geometry/*`

### Materials Intelligence

Backend:

* `materials/*`

These should not be owned by UI components.

---

## Layer 2 — Workspaces

These are the main user-facing editing surfaces.

Frontend:

* `design-intake/blueprint/`
* `instrument-workspace/`
* `art-studio/`
* `analyzer/`
* `manufacturing/`

Backend support:

* `blueprint/`
* `analyzer/`
* `manufacturing/`

---

## Layer 3 — Utilities

These are stateless tools that can run:

* standalone
* in project context

Frontend:

* `design-utilities/lutherie/`
* `design-utilities/wood-intelligence/`
* `design-utilities/scientific/`

Backend:

* `routers/design/utilities_router.py`
* `instrument_geometry/utilities/`
* `materials/*`

---

# The most important alignment rule

The repo should line up like this:

```text
UI workspace
    ↓
frontend folder
    ↓
API router domain
    ↓
engine/service domain
    ↓
project graph
```

Example:

```text
Bridge Lab
→ instrument-workspace/acoustic/bridge/
→ routers/design/instrument_router.py
→ instrument_geometry/bridge/
→ InstrumentProjectData.bridge_state
```

And for wood intelligence:

```text
Wood Intelligence UI
→ design-utilities/wood-intelligence/
→ routers/system/materials_router.py
→ materials/registry + materials/acoustics + materials/machining
→ InstrumentProjectData.material_selection
```

# The big structural change

This diagram makes one thing very clear:

**The repo is no longer centered around calculators, panels, or historical routes.**

It is centered around:

* a **project graph**
* a small number of **engines**
* a set of **workspaces**
* thin **utility interfaces**

That is the structure that will keep the codebase from becoming chaotic again.

I can also turn this into a **one-page developer handoff document** with:

* architecture principles
* folder ownership rules
* “where new features go” decision rules
* anti-patterns to avoid

