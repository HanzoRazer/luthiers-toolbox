# Phase 1 Module Classification

**Date:** 2026-05-04  
**Status:** Complete  
**Scope:** Classify experimental and snapshot modules for future cleanup decisions

---

## Summary

Reviewed **7 modules** (2 interactive + 5 snapshots). All are **detached from the main app** — none are imported by `packages/client/src/` or required for build/runtime. Several contain prototype code that was later absorbed into the main app in refined form.

**Key finding:** The main app already has production versions of headstock designer, CAM panels, DXF import/export, and spiral soundhole. The experimental modules are historical snapshots, not active dependencies.

---

## Classification Matrix

| Module | Classification | Evidence | Recommendation |
|--------|----------------|----------|----------------|
| `Interactive_Headstock_Generator/` | Detached Prototype | No imports from main app; main app has separate `HeadstockDesignerView.vue` | Archive or delete |
| `Interactive_Neck and Cam _Modules/` | Detached Prototype | No imports from main app; main app has `cam/neck/` components | Archive or delete |
| `files - 2026-03-31T002554.594/` | Archive / Reference Only | Spiral soundhole prototype; absorbed into main app | Delete |
| `files - 2026-04-14T102549.923/` | Archive / Reference Only | Body side arc data; referenced in comments only | Delete |
| `files - 2026-04-16T160551.956/` | Archive / Reference Only | Guitar spec JSONs; likely staging data | Delete |
| `files - 2026-04-16T161657.416/` | Archive / Reference Only | Guitar spec JSONs; likely staging data | Delete |
| `files - 2026-04-23T090806.069/` | Archive / Reference Only | DXF conversion script + output + sprint prompt | Delete |

---

## Module Details

### Interactive_Headstock_Generator/

#### Structure
```
Interactive_Headstock_Generator/
├── files - 2026-03-17T035340.928/    # DXF integration docs + client
├── files - 2026-03-17T091407.113/    # ImportView, WorkspaceView, package.json
├── files - 2026-03-17T092736.563/    # App.vue, main.ts, index.html (runnable)
├── files - 2026-03-17T095439.331/    # WoodGrainPanel, useWoodGrain
├── headstock-designer.html           # Standalone HTML demo
├── ps-import-normalize.html          # Standalone HTML demo
├── ps-parametric.html                # Standalone HTML demo
└── ps-suite.html                     # Standalone HTML demo
```

**File count:** 23 files across 4 timestamped subdirs + 4 HTML demos

#### Entry Points
- `files - 2026-03-17T092736.563/index.html` + `main.ts` + `App.vue` — standalone Vue app
- `files - 2026-03-17T091407.113/package.json` + `vite.config.ts` — build system

#### Build System
- Separate `package.json` in subfolder (not linked to main app)
- Separate `vite.config.ts` with proxy to `localhost:8000`

#### Imports Into Main App
**NONE FOUND**

Evidence:
```bash
$ grep -RIn "Interactive_Headstock_Generator" packages/client/src services/api/app
# No output
```

The main app router references a different file:
```
packages/client/src/router/index.ts:283:
  path: "/art-studio/headstock",
  component: () => import("@/views/art-studio/HeadstockDesignerView.vue"),
```

#### API Usage
Calls `/api/dxf/spline/evaluate`, `/api/dxf/parse-and-normalize` — these endpoints exist in main backend.

Evidence:
```
files - 2026-03-17T091407.113/useDxfImport.ts:106:
  const res=await fetch(`${API_BASE}/spline/evaluate`, ...)
```

#### Shared Config / Env Usage
Uses `@/` path aliases and references `@/stores/headstock`, `@/composables/useKonvaCanvas` — but these are internal to the prototype, not shared with main app.

#### Runtime Notes
- Can run standalone with its own `npm run dev`
- Not required by main app build or runtime

#### Classification
**Detached Prototype**

#### Recommendation
**Archive or delete.** The main app has its own `HeadstockDesignerView.vue` (11KB, dated Mar 16) that uses different APIs (`/api/instruments/guitar/headstock-inlay/*`). The prototype code was not directly integrated.

#### Open Questions
None — classification is clear.

---

### Interactive_Neck and Cam _Modules/

#### Structure
```
Interactive_Neck and Cam _Modules/
├── CAM_SURVEY.md                     # Survey document
├── files - 2026-03-17T035340.928/    # DXF integration (duplicate of headstock)
├── files - 2026-03-17T091407.113/    # Import/Workspace views
├── files - 2026-03-17T092736.563/    # App shell, ParametricView
├── files - 2026-03-17T095439.331/    # WoodGrainPanel
├── files - 2026-03-17T140231.201/    # CamSpecPanel, useCamSpec
├── files - 2026-03-17T141923.090/    # fretboard_export.py, useFretboard
├── files - 2026-03-17T144112.077/    # neck_profile_export.py, useNeckProfile
├── files - 2026-03-17T153916.645/    # CamSpecPanel (revised), useNeckTaper
├── files - 2026-03-17T155948.549/    # useHeadstockTransition
├── files - 2026-03-17T160258.346/    # useHeadstockTransition (revised)
├── files - 2026-03-17T160517.587/    # useHeadstockTransition (revised)
├── files - 2026-03-17T171011.806/    # Full panel set: Fretboard, NeckProfile, etc.
├── files - 2026-03-17T172741.143/    # VariantLibraryPanel, variants.ts
├── files - 2026-03-17T181515.994/    # photo_vectorizer_router.py
├── files - 2026-03-17T182228.919/    # ConfiguratorView
├── files - 2026-03-17T223828.607/    # CamWorkspaceView, GcodePreviewPanel
├── files - 2026-03-17T223900.242/    # CamWorkspaceView (duplicate)
├── files - 2026-03-17T224205.344/    # CamWorkspaceView (duplicate)
├── temp_cam_workspace/               # CAM workspace prototype
├── temp_cam_workspace2/              # CAM workspace prototype (copy)
├── replay_result.txt                 # Test output
├── test_core.txt                     # Test output
├── test_replay.txt                   # Test output
├── test_run_output.txt               # Test output
├── test_run_output2.txt              # Test output
└── test_run_pv.txt                   # Test output
```

**File count:** 95 files across 18 timestamped subdirs + 2 temp dirs + 6 test outputs

#### Entry Points
- Multiple `AppShell.vue` + `main.ts` + `index.html` across timestamped dirs
- No unified entry point — appears to be iterative prototype snapshots

#### Build System
- `package.json` + `vite.config.ts` in `files - 2026-03-17T091407.113/`
- Separate from main app build

#### Imports Into Main App
**NONE FOUND**

Evidence:
```bash
$ grep -RIn "Interactive_Neck" packages/client/src services/api/app
# No output
```

The main app has its own CAM panels at:
```
packages/client/src/components/cam/neck/
├── CamSpecPanel.vue
├── FretboardPanel.vue
├── HeadstockTransitionPanel.vue
├── NeckProfilePanel.vue
└── NeckTaperPanel.vue
```

#### API Usage
Calls `/api/dxf/*` endpoints (same as headstock module).

#### Shared Config / Env Usage
Uses `@/` imports internally — not shared with main app.

#### Runtime Notes
- Contains iterative development snapshots (many duplicate/revised versions)
- Main app has refined production versions of these panels
- Test output files (*.txt) are logs, not source

#### Classification
**Detached Prototype**

#### Recommendation
**Archive or delete.** The main app has production `cam/neck/` components and composables (`useDxfImport.ts`, `useExportDxf.ts`) that supersede this prototype work. The timestamped folders represent development history, not active code.

#### Open Questions
None — classification is clear.

---

### files - 2026-03-31T002554.594/

#### Structure
```
files - 2026-03-31T002554.594/
├── soundhole_spiral.py
├── SpiralSoundholeDesigner.vue
└── spiral_soundhole_router.py
```

**File count:** 3 files

#### Entry Points
None — individual source files, no build system

#### Build System
None

#### Imports Into Main App
**ABSORBED** — main app has production version

Evidence:
```
packages/client/src/components/toolbox/acoustics/SpiralSoundholeDesigner.vue
packages/client/src/router/index.ts:164:
  component: () => import("@/components/toolbox/acoustics/SpiralSoundholeDesigner.vue")
services/api/app/routers/instrument_geometry/soundhole_router.py:421:
  prefix="spiral_soundhole_"
```

#### Classification
**Archive / Reference Only**

#### Recommendation
**Delete.** The code was absorbed into the main app at:
- `packages/client/src/components/toolbox/acoustics/SpiralSoundholeDesigner.vue`
- `services/api/app/routers/instrument_geometry/soundhole_router.py`

The snapshot is historical only.

---

### files - 2026-04-14T102549.923/

#### Structure
```
files - 2026-04-14T102549.923/
├── body_side_arc_solver.py
├── carlos_jumbo_side_contour.csv
└── dreadnought_side_contour.csv
```

**File count:** 3 files

#### Entry Points
None — Python script + CSV data

#### Imports Into Main App
**REFERENCED IN COMMENTS ONLY**

Evidence:
```
services/api/app/instrument_geometry/body/ibg/arc_reconstructor.py:1161:
  # Known values from body_side_arc_solver.py verification
```

This is a comment reference, not a runtime import.

#### Classification
**Archive / Reference Only**

#### Recommendation
**Delete.** The algorithm was integrated into `arc_reconstructor.py`. The CSV data files are verification inputs, not production data.

---

### files - 2026-04-16T160551.956/

#### Structure
```
files - 2026-04-16T160551.956/
├── acoustic_00_spec.json
├── gibson_l0_spec.json
└── om_acoustic_spec.json
```

**File count:** 3 files (all JSON specs)

#### Imports Into Main App
**NONE FOUND**

#### Classification
**Archive / Reference Only**

#### Recommendation
**Delete.** These appear to be staging data for instrument specs. If the data is needed, it should be in `services/api/app/instrument_geometry/specs/` — not in a timestamped root folder.

---

### files - 2026-04-16T161657.416/

#### Structure
```
files - 2026-04-16T161657.416/
├── jumbo_fesselier_spec.json
└── selmer_maccaferri_d_hole_spec.json
```

**File count:** 2 files (all JSON specs)

#### Imports Into Main App
**NONE FOUND**

#### Classification
**Archive / Reference Only**

#### Recommendation
**Delete.** Same as above — staging data that should be in the proper specs directory if needed.

---

### files - 2026-04-23T090806.069/

#### Structure
```
files - 2026-04-23T090806.069/
├── json_to_dxf_r12.py
├── smart_guitar_body_outline_r12.dxf
└── SPRINT_3_EXPANSION_ENGINEER_PROMPT.md
```

**File count:** 3 files

#### Imports Into Main App
**NONE FOUND**

#### Classification
**Archive / Reference Only**

#### Recommendation
**Delete.** Contains:
- A one-off conversion script
- A generated DXF output file
- A sprint planning prompt

None are production dependencies.

---

## Deletion Candidates

All 7 modules are deletion candidates pending human approval:

| Module | Rationale |
|--------|-----------|
| `Interactive_Headstock_Generator/` | Superseded by `HeadstockDesignerView.vue` in main app |
| `Interactive_Neck and Cam _Modules/` | Superseded by `cam/neck/` components in main app |
| `files - 2026-03-31T002554.594/` | Absorbed into `SpiralSoundholeDesigner.vue` |
| `files - 2026-04-14T102549.923/` | Algorithm integrated into `arc_reconstructor.py` |
| `files - 2026-04-16T160551.956/` | Staging data, not in production |
| `files - 2026-04-16T161657.416/` | Staging data, not in production |
| `files - 2026-04-23T090806.069/` | One-off script + output + prompt |

---

## Absorption Candidates

**None.** All useful code has already been absorbed into the main app:

| Snapshot | Absorbed Into |
|----------|---------------|
| Spiral soundhole | `packages/client/src/components/toolbox/acoustics/SpiralSoundholeDesigner.vue` |
| Body side arc solver | `services/api/app/instrument_geometry/body/ibg/arc_reconstructor.py` |
| CAM panels | `packages/client/src/components/cam/neck/*.vue` |
| DXF import/export | `packages/client/src/composables/useDxfImport.ts`, `useExportDxf.ts` |
| Headstock designer | `packages/client/src/views/art-studio/HeadstockDesignerView.vue` |

---

## Preserve / Archive Candidates

If deletion is deferred, these could be archived to `archive/experimental/2026-03/`:

- `Interactive_Headstock_Generator/` — historical reference for headstock design approach
- `Interactive_Neck and Cam _Modules/CAM_SURVEY.md` — potentially useful survey document

---

## Follow-Up Tasks

1. **Human approval required** before any deletion
2. **Verify no hidden imports** — run full build after deletion to confirm no breakage
3. **Archive vs delete decision** — determine if historical snapshots have reference value
4. **Clean .gitignore** — these folders are tracked; after deletion, no cleanup needed

---

## Evidence Summary

### Search Commands Used
```bash
# Main app references
grep -RIn "Interactive_Headstock_Generator" packages/client/src services/api/app
grep -RIn "Interactive_Neck" packages/client/src services/api/app
grep -RIn "files - 2026" packages/client/src services/api/app

# Router references
grep -RIn "headstock" packages/client/src/router

# API usage
grep -RInE "fetch\(|/api/" "Interactive_Headstock_Generator"
grep -RInE "fetch\(|/api/" "Interactive_Neck and Cam _Modules"

# Shared imports
grep -RInE "@/|instrumentGeometryStore" "Interactive_Headstock_Generator"
```

### Key Evidence Files
- `packages/client/src/router/index.ts:283` — headstock route uses main app component, not experimental
- `packages/client/src/components/cam/neck/` — production CAM panels exist
- `packages/client/src/composables/useDxfImport.ts` — production DXF composable exists
- `services/api/app/routers/instrument_geometry/soundhole_router.py` — spiral soundhole integrated

---

*End of classification report*
