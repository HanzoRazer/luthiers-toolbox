✅ Document 1: REPO_LAYOUT.md

(Place at repo root)

# Luthier’s ToolBox – Repository Layout Guide
This document defines the authoritative directory structure for the Luthier’s ToolBox project as of the RMOS 2.0 + Saw Lab 2.0 architecture changeover.

It exists to:
- Reduce repo clutter
- Prevent subsystem fragmentation
- Give developers a stable map of where code *must* live
- Establish conventions for adding new modules or sandboxes

---

## 1. High-Level Structure



/
├── services/
│ └── api/
│ └── app/
│ ├── rmos/
│ ├── saw_lab/
│ ├── toolpath/
│ ├── calculators/
│ ├── art_studio/
│ ├── data/
│ └── tests/
│
├── docs/
│ ├── RMOS/
│ ├── SawLab/
│ ├── ArtStudio/
│ └── General/
│
├── ARCHIVE/
│ ├── build_bundles/
│ ├── patch_bundles/
│ ├── server_legacy/
│ └── legacy_subsystems/
│
└── README.md
REPO_LAYOUT.md
LEGACY_ARCHIVE_POLICY.md


---

## 2. Location Rules

### 2.1 All active Python backend code lives in:



services/api/app/


**Subsystem placement:**

- `rmos/`  
  RMOS 2.0 kernel, API contracts, feasibility, workflows, geometry engine selector.

- `saw_lab/`  
  Saw Lab 2.0: physics calculators, path planner, multi-board planner, debug router, toolpath builder.

- `toolpath/`  
  Geometry → machine operations: M/L converter, Shapely engine, post-processors, G-code emitters.

- `calculators/`  
  Core, global calculator services that apply across subsystems (heat, deflection, chipload, BOM, etc.).

- `art_studio/`  
  UI schema models, API adapters, graphics/LLM hooks, generation modes, inspector modules.

- `data/`  
  JSON/YAML resources:
  - Blade libraries
  - Material libraries
  - Machine profiles
  - Presets (feeds, speeds, safety envelopes)

- `tests/`  
  The **canonical test suite** for the entire API.  
  No tests outside this tree should be considered “live”.

---

## 3. Sandbox & Experimental Code

All experiments, prototypes, LLM-generated concept drops, or partial subsystems must live under:



sandbox/<name>/


Rules:

- Names must be **date- or feature-based**, e.g.:
  - `sandbox/2025_shapely_experiment`
  - `sandbox/sawlab_thermal_model_test`
- Sandboxes must **not** be imported by production modules.
- When a sandbox becomes real:
  1. Extract its stable code into the correct directory under `services/api/app/`
  2. Move the sandbox into `__ARCHIVE__/sandbox_history/`

No sandbox stays “live” indefinitely.

---

## 4. Archive Structure (See `LEGACY_ARCHIVE_POLICY.md`)



ARCHIVE/
build_bundles/ # Past bundle drops that are now applied
patch_bundles/ # Deprecated patch sets
server_legacy/ # Pre-RMOS backend experiments
legacy_subsystems/ # Old CNC Saw Lab, ToolBox_* directories, obsolete Art Studio code
sandbox_history/ # Retired experimental sandboxes


Everything moved here is *out of the active project lifecycle* but preserved for provenance and recovery.

---

## 5. Tests

All active tests must live inside:



services/api/app/tests/


Test types:

- Unit tests (calculators, planners, physics)
- Integration tests (RMOS ↔ Saw Lab)
- API router tests
- Geometry engine tests
- Art Studio schema tests

No test belongs at the repo root or inside subsystem directories (except temporary local-only experiments).

---

## 6. Adding New Features

Whenever introducing a new feature, apply these rules:

1. **Backend logic** → goes under the appropriate subsystem in `services/api/app/`.
2. **Shared utilities** → go under `services/api/app/calculators/` or `services/api/app/common/`.
3. **Docs** → stored under `docs/<SubsystemName>/`.
4. **Tests** → always added under `services/api/app/tests/`.
5. **Never** add top-level directories for “one-off” features.  
   They must be a sandbox or part of the canonical tree.

---

## 7. Governance

This document is the official layout specification.  
Any structural changes require updating:

- This `REPO_LAYOUT.md`
- `LEGACY_ARCHIVE_POLICY.md`
- The affected folder placeholders inside `__ARCHIVE__/`

Future contributors must maintain this as the map of record.
