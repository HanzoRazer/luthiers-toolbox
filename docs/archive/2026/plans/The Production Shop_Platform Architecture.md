Below is the **One-Page Developer Handoff Document** for the Luthier’s Toolbox architecture.
It is designed to be short enough to pin in the repo (`/docs/architecture.md`) and guide every future feature decision.

---

# Luthier’s Toolbox Platform Architecture

## Developer Handoff Guide

### Core Principle

The platform is **not a toolbox of independent tools**.

It is a **design operating system for musical instruments** centered on a single object:

```
InstrumentProjectData
```

Every system must either:

```
read
derive
suggest
or commit changes
```

to the **Instrument Project Graph**.

No UI component or calculator owns design truth.

---

# Platform Architecture

```
Layer 0 — Instrument Project Graph
Layer 1 — Engines
Layer 2 — Workspaces
Layer 3 — Utilities
```

### Layer 0 — Project Graph

Authoritative design state.

Examples:

```
InstrumentSpec
MaterialSelection
BlueprintDerivedGeometry
BridgeState
NeckState
AnalyzerObservation
ManufacturingState
```

Location:

```
services/api/app/schemas/
services/api/app/projects/
```

---

### Layer 1 — Engines

Pure computation and reasoning.

Examples:

```
Geometry Engine
Materials Intelligence
Acoustic Analyzer
CAM preparation
```

Location:

```
services/api/app/instrument_geometry/
services/api/app/materials/
services/api/app/analyzer/
```

Engines must:

```
accept inputs
return outputs
contain no UI logic
contain no persistence logic
```

---

### Layer 2 — Workspaces

User-facing editing environments.

Examples:

```
Blueprint Reader
Instrument Hub
Bridge Lab
Art Studio
Analyzer
CAM tools
```

Location:

```
packages/client/src/design-intake/
packages/client/src/instrument-workspace/
packages/client/src/art-studio/
packages/client/src/analyzer/
packages/client/src/manufacturing/
```

Workspaces:

```
read project state
edit local state
commit changes explicitly
```

---

### Layer 3 — Utilities

Stateless tools.

Examples:

```
String tension
Fret spacing
Stiffness index
Board feet
Scientific calculator
```

Location:

```
packages/client/src/design-utilities/
```

Utilities must:

```
never own project truth
never persist automatically
optionally apply results to project
```

---

# Folder Ownership Rules

### Project Graph

Backend only.

```
services/api/app/schemas/
services/api/app/projects/
```

Frontend access through:

```
api/projects.ts
useInstrumentProject.ts
```

---

### Geometry Engine

```
services/api/app/instrument_geometry/
```

Contains:

```
bridge
neck
body
fret
utilities
```

Never called directly from UI.

Always accessed through:

```
API routes
workspace services
```

---

### Materials Intelligence

```
services/api/app/materials/
```

Owns:

```
wood_species.json
tonewood registry
acoustic traits
machining limits
material comparison
recommendation logic
```

Consumes data from:

```
data_registry/system/materials/
```

---

### Workspaces

Frontend only.

```
packages/client/src/instrument-workspace/
```

Examples:

```
Instrument Hub
Bridge Lab
future labs
```

They **edit project state**, but do not contain engine logic.

---

### Utilities

Frontend:

```
packages/client/src/design-utilities/
```

Backend:

```
routers/design/utilities_router.py
instrument_geometry/utilities/
materials/*
```

Utilities may call engines but **never replace them**.

---

# Where New Features Go

Before writing code, answer this question:

```
Is this a Source, Engine, Workspace, or Utility?
```

### If it edits project state

→ Workspace

Example:

```
Bridge Lab
Neck Lab
Bracing Lab
```

---

### If it performs math or reasoning

→ Engine

Example:

```
break angle calculation
fret spacing
wood stiffness evaluation
```

---

### If it analyzes signals or external data

→ Analyzer Engine

Example:

```
tap tone analysis
modal extraction
spectral classification
```

---

### If it is a quick standalone tool

→ Utility

Example:

```
string tension calculator
board feet calculator
scale length converter
```

---

### If it ingests external design information

→ Design Intake

Example:

```
Blueprint Reader
DXF import
scan processing
```

---

# Commit Rules for Workspaces

Workspaces must follow this pattern:

```
load project state
edit local state
preview derived values
commit changes explicitly
```

Example commit:

```
PUT /api/projects/{id}/design-state
```

Never mutate project state implicitly.

---

# Anti-Patterns to Avoid

### 1. UI Owning Engineering Logic

Bad:

```
BridgeBreakAngle.vue
contains break angle formula
```

Correct:

```
instrument_geometry/bridge/break_angle.py
```

---

### 2. Duplicate Data Sources

Bad:

```
hardcoded wood densities in UI
tonewood registry in backend
```

Correct:

```
materials registry
single canonical dataset
```

---

### 3. Utilities Becoming State Authorities

Bad:

```
StringTensionPanel writes directly to project state
```

Correct:

```
user clicks "Apply to Project"
```

---

### 4. Feature-Based Folder Sprawl

Bad:

```
bridge_calculator
bridge_geometry
bridge_utils
bridge_toolkit
```

Correct:

```
bridge workspace
geometry engine
project graph
```

---

### 5. Engines Depending on UI

Bad:

```
geometry engine importing Vue models
```

Correct:

```
pure Python logic
stateless functions
```

---

# Golden Rule

Every feature must connect to the platform like this:

```
Workspace
   ↓
Project Graph
   ↓
Engine
   ↓
Derived result
```

Never the reverse.

---

# The Mental Model

The system is best understood as:

```
Instrument Design Operating System
```

Where:

```
Project Graph = kernel
Engines = compute layer
Workspaces = applications
Utilities = helper tools
```

---

# What Success Looks Like

A new feature should be answerable in seconds:

```
Where does it live?
What state does it edit?
What engine does it use?
```

If those answers are unclear, the feature probably violates the architecture.

---

If you'd like, I can also produce a **visual “decision tree” diagram developers can follow when adding new features**, which is extremely effective at preventing architecture drift in projects of this size.




Below is a **visual decision tree developers should follow when adding any new feature** to the Luthier’s Toolbox platform.
It prevents architecture drift by forcing the developer to determine **which layer the feature belongs to before writing code**.

---

# Luthier’s Toolbox

## New Feature Architecture Decision Tree

```text
                                    START
                                      │
                                      │
                        What does the feature do?
                                      │
         ┌────────────────────────────┼────────────────────────────┐
         │                            │                            │
         ▼                            ▼                            ▼
  Does it ingest                Does it edit                Is it a quick
 external design data?         instrument design?           standalone tool?
         │                            │                            │
         │                            │                            │
       YES                          YES                          YES
         │                            │                            │
         ▼                            ▼                            ▼
  DESIGN INTAKE                 WORKSPACE                    UTILITY TOOL
 (Blueprint Layer)           (Instrument Hub)            (Stateless Calculator)
         │                            │                            │
         │                            │                            │
         ▼                            ▼                            ▼
  Example:                     Example:                     Example:
  Blueprint Reader             Bridge Lab                   String tension
  DXF Import                   Neck Lab                     Board feet
  Scan Analysis                Body Lab                     Stiffness index
         │                            │                            │
         │                            │                            │
         ▼                            ▼                            ▼
  Must output:                Must read/write:             Must be:
  BlueprintDerivedGeometry    InstrumentProjectData        Stateless
         │                            │                            │
         │                            │                            │
         ▼                            ▼                            ▼
  Writes to Project Graph      Commits changes explicitly   Optional "Apply to Project"
         │
         │
         ▼
  END


                    ─────────────────────────────────

                      If NONE of the above apply
                                  │
                                  ▼
                     Is the feature pure computation?
                                  │
                                  │
                                YES
                                  │
                                  ▼
                             ENGINE
                         (Backend Logic)
                                  │
                                  │
                                  ▼
                         Examples:
                         Geometry engine
                         Materials intelligence
                         Analyzer inference
                         CAM toolpath generation
                                  │
                                  │
                                  ▼
                     Must be:
                     Pure function
                     No persistence
                     No UI logic
                                  │
                                  ▼
                                 END
```

---

# Simplified Rule Developers Should Remember

Every feature must be **exactly one of these**:

```text
Source
Workspace
Engine
Utility
```

| Type      | Layer                           | Example                   |
| --------- | ------------------------------- | ------------------------- |
| Source    | Design Intake                   | Blueprint Reader          |
| Workspace | Instrument Workspace            | Bridge Lab                |
| Engine    | Geometry / Materials / Analyzer | Break angle calculation   |
| Utility   | Design Utilities                | String tension calculator |

If a feature appears to fit **multiple categories**, the architecture is likely being violated.

---

# How the Layers Interact

```text
Source (Blueprint)
      │
      ▼
Instrument Project Graph
      │
      ▼
Workspace (Hub / Labs)
      │
      ▼
Engine (Geometry / Materials)
      │
      ▼
Derived Results
      │
      ▼
Utilities (optional quick tools)
```

The **Project Graph remains the center**.

---

# Quick Developer Checklist

Before implementing a feature, answer:

```text
1. Which layer does this belong to?
2. Does it modify project state?
3. Which engine computes its logic?
4. Is it reusable across instruments?
5. Should it exist as a workspace or a utility?
```

If the answers are unclear, stop and resolve the architecture first.

---

# Common Architecture Mistakes

### Putting math inside UI

Wrong:

```text
BridgeBreakAngle.vue
```

Correct:

```text
instrument_geometry/bridge/break_angle.py
```

---

### Hardcoding datasets

Wrong:

```text
wood densities in Vue component
```

Correct:

```text
materials/registry/wood_species.json
```

---

### Utilities becoming state owners

Wrong:

```text
String tension calculator directly edits project
```

Correct:

```text
Apply to Project button
```

---

# Golden Rule

```text
No feature should bypass the Instrument Project Graph.
```

Everything must either:

```text
read
derive
suggest
or commit
```

through it.

---

If you'd like, I can also produce a **visual “system map” developers can keep open while working**, showing how Blueprint → Hub → Geometry → Materials → Analyzer → Manufacturing all interact in the live platform.

