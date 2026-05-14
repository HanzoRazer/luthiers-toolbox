# Aperture Workspace Refactor — Architecture Status

**Date:** 2026-05-06  
**Status:** Backend normalization complete; frontend migration pending  
**Branch:** `fix/wood-shrinkage-data-integrity`

---

## Status

Dev Orders 1–3 are complete. The backend aperture normalization layer is in place with full test coverage. The shared workflow UI primitives are defined. NECK-A remains stable and untouched.

Frontend workspace consolidation (Dev Order 5+) is deferred until this architecture checkpoint is committed.

---

## Context

The Aperture Workspace refactor unifies soundhole/aperture types under a common geometry model and shared UI infrastructure. This enables:

1. Cross-type comparison (spiral vs. round vs. oval)
2. Equivalent diameter calculation for non-circular apertures
3. Unified acoustic analysis (P:A ratio, Williams threshold)
4. Shared diagnostic workflow patterns with NECK-A

The refactor was triggered by discovery of a critical spiral arc length math error that understated Carlos Jumbo aperture area by ~5.5×.

---

## Decisions Locked

### Spiral arc length formula

**Correct formula:**
```
L = sqrt(1 + k²) / k × (r_end - r0)
```

**Fallback for k → 0:**
```
L = r0 × θ_end  (circular arc)
```

**Old incorrect formula (removed):**
```
L = (r_end - r0) / sin(atan(1/k))  ← was missing /k divisor
```

### Carlos Jumbo corrected metrics

| Metric | Value |
|--------|-------|
| Single spiral arc length | 139.4 mm |
| Single spiral area | 1951.8 mm² |
| Single spiral P:A ratio | 0.143 mm⁻¹ |
| Dual spiral total area | 3903.5 mm² |
| Dual spiral vs. 4-inch round | 192.6% |

The Carlos preset now represents experimental high-area geometry. The corrected area is nearly 2× a standard 4-inch round soundhole.

### ApertureGeometry as normalized output

`ApertureGeometry` wraps type-specific geometry into a common model. It is an **output model**, not a replacement for type-specific params.

### Graceful handling of missing metadata

`aperture_from_spiral_geometry()` sets `characteristic_width_mm = None` when `geo.spec` is missing. No exceptions raised for incomplete source data.

### Router augmentation pattern

API response augmentation happens in the router, not in geometry serialization functions. This avoids circular imports and keeps Dev Order 3 narrow.

---

## Implementation Completed

### Dev Order 1 — Shared Workflow Foundation

| File | Purpose |
|------|---------|
| `packages/client/src/types/workflow.ts` | `WorkflowGateLevel`, `WorkflowDiagnostic`, `WorkflowResponse` types |
| `packages/client/src/components/shared/workflow/workflow.module.css` | CSS variables for canonical workflow palette |
| `packages/client/src/components/shared/workflow/GateBadge.vue` | Gate status pill (green/yellow/red) |
| `packages/client/src/components/shared/workflow/SectionLabel.vue` | Uppercase section header |
| `packages/client/src/components/shared/workflow/PrerequisiteNotice.vue` | Prerequisite checklist notice |
| `packages/client/src/components/shared/workflow/DiagnosticCard.vue` | Full diagnostic card with causes/checks/actions |
| `packages/client/src/components/shared/workflow/index.ts` | Barrel export |
| `packages/client/src/registry/toolRegistry.ts` | Simple typed array with helper functions |

### Dev Order 2 — Backend Aperture Normalization

| File | Purpose |
|------|---------|
| `services/api/app/instrument_geometry/soundhole/aperture_geometry.py` | `ApertureGeometry` dataclass, `equivalent_diameter_from_area()`, `aperture_from_spiral_geometry()`, `aperture_geometry_to_dict()` |
| `services/api/tests/test_aperture_geometry.py` | 16 tests: round-trip, spiral conversion, P:A invariant, `spec=None` handling |

### Dev Order 3 — Non-Breaking API Augmentation

| File | Change |
|------|--------|
| `app/routers/instrument_geometry/soundhole_router.py` | Augments spiral geometry response with `aperture_geometry` |
| `tests/test_aperture_geometry_endpoint.py` | 8 tests for new response contract |

**Test totals:** 39 tests passing (16 + 15 + 8 aperture/spiral tests)

---

## Current Contracts

### ApertureGeometry Fields

| Field | Type | Description |
|-------|------|-------------|
| `aperture_type` | `str` | Type identifier: `"round"`, `"oval"`, `"spiral"`, `"fhole"` |
| `area_mm2` | `float` | Open area in mm² |
| `perimeter_mm` | `float` | Total perimeter in mm |
| `equivalent_diameter_mm` | `float` | Diameter of circle with same area |
| `characteristic_width_mm` | `float \| None` | Type-specific width (slot width for spiral) |
| `path_length_mm` | `float \| None` | Total path/arc length |
| `pa_ratio_mm_inv` | `float \| None` | Perimeter-to-area ratio (mm⁻¹) |

### API Response Example

`POST /api/instrument/soundhole/spiral/geometry` now returns:

```json
{
  "upper": {
    "centerline": [...],
    "outer_wall": [...],
    "inner_wall": [...],
    "area_mm2": 1951.8,
    "perimeter_mm": 278.8,
    "pa_ratio_mm_inv": 0.143,
    "end_radius_mm": 34.69,
    "total_length_mm": 139.4,
    "aperture_geometry": {
      "aperture_type": "spiral",
      "area_mm2": 1951.8,
      "perimeter_mm": 278.8,
      "equivalent_diameter_mm": 49.8,
      "characteristic_width_mm": 14.0,
      "path_length_mm": 139.4,
      "pa_ratio_mm_inv": 0.143
    }
  },
  "lower": {
    "...": "same structure"
  },
  "total_area_mm2": 3903.5,
  "round_ref_area_mm2": 2026.8,
  "area_ratio_pct": 192.6,
  "acoustic_verdict": {...}
}
```

Legacy fields (`area_mm2`, `perimeter_mm`, `total_length_mm`) remain at their original locations. `aperture_geometry` is additive.

---

## Current Aperture Types

**Implemented:**

| Type | Status | Backend | Frontend |
|------|--------|---------|----------|
| `round` | Stable | `soundhole_calc.py` | dropdown option |
| `oval` | Stable | `soundhole_calc.py` | dropdown option |
| `fhole` | Stable | `soundhole_calc.py` | dropdown option |
| `spiral` | Stable | `spiral_geometry.py` | `SpiralSoundholeDesigner.vue` |

**Future (not implemented):**

| Type | Notes |
|------|-------|
| `D-hole` | Selmer-style, requires arc + chord geometry |
| `duck-head` | Django Reinhardt era, compound curves |
| `trapezoid` | Modern jazz, straight edges |
| `side-port` | Upper bout secondary aperture |
| `slot-port` | Linear slot in soundboard |

Future types will integrate via `ApertureGeometry` once geometry engines exist.

---

## Deferred Work

### NECK-A Migration

**Status:** NECK-A is stable. No route, store, or panel migration in Dev Orders 1–3.

**Guidance:**
- Define shared workflow convention now (done)
- Migrate NECK-A to shared components in a follow-up sprint
- Do not destabilize the working NECK-A vertical slice during Aperture work

### Store Extraction

`neckSetupStore.ts` extraction is deferred. The one-store-per-workspace convention is defined but not yet applied to NECK-A.

### Tornavoz

Tornavoz is a modifier (tube attachment), not an aperture type. `TornavozAttachment` dataclass will be added when tornavoz UI is built. It does not block aperture workspace consolidation.

---

## Next Dev Order

### Dev Order 5 — ApertureWorkspace Frontend Shell

Create the workspace shell that will absorb existing aperture tools:

```
packages/client/src/views/aperture/ApertureWorkspace.vue
```

**Phases:**

| Phase | Description | Key Files |
|-------|-------------|-----------|
| 1 | ApertureWorkspace shell | `ApertureWorkspace.vue`, route registration |
| 2 | Absorb SpiralSoundholeDesigner | Move from `toolbox/acoustics/` |
| 3 | Standard soundhole panels | Round, oval, f-hole type panels |
| 4 | Comparison/inverse solver | Cross-type area comparison, inverse sizing |
| 5 | Optional NECK-A adoption | Shared workflow components in NECK-A panels |

**Prerequisites:**
- This architecture status document committed
- Dev Orders 1–3 verified stable

---

## Cross-References

### Handoff Documents

- [`docs/handoffs/APERTURE_WORKSPACE_REFACTOR_HANDOFF_2026-05-06.md`](../handoffs/APERTURE_WORKSPACE_REFACTOR_HANDOFF_2026-05-06.md) — Detailed implementation handoff
- [`docs/handoffs/NECK_A_PHASE_7_FRONTEND_MIGRATION_HANDOFF.md`](../handoffs/NECK_A_PHASE_7_FRONTEND_MIGRATION_HANDOFF.md) — NECK-A vertical slice documentation

### Implementation Files

**Shared Workflow (Frontend):**
```
packages/client/src/components/shared/workflow/
├── GateBadge.vue
├── DiagnosticCard.vue
├── PrerequisiteNotice.vue
├── SectionLabel.vue
├── workflow.module.css
└── index.ts
```

**Types:**
```
packages/client/src/types/workflow.ts
```

**Tool Registry:**
```
packages/client/src/registry/toolRegistry.ts
```

**Backend Aperture Geometry:**
```
services/api/app/instrument_geometry/soundhole/aperture_geometry.py
```

**Tests:**
```
services/api/tests/test_aperture_geometry.py
services/api/tests/test_aperture_geometry_endpoint.py
services/api/tests/test_soundhole_spiral.py
```

---

## Dev Order 5–6 — ApertureWorkspace Frontend Shell

**Status:** Complete

Created `ApertureWorkspace.vue` as beta consolidation shell with 5 tabs. Mounted `SpiralSoundholeDesigner.vue` in Spiral tab via `defineAsyncComponent` with `<Suspense>` wrapper.

Added route: `/art-studio/aperture`

Created `SliderRow.vue` to resolve missing dependency.

---

## Dev Order 7 — Spiral Component Containment Audit

**Status:** Complete  
**Date:** 2026-05-07

Audited `SpiralSoundholeDesigner.vue` as canonical spiral implementation before any deeper migration.

**Audit document:** [`SPIRAL_COMPONENT_CONTAINMENT_AUDIT.md`](./SPIRAL_COMPONENT_CONTAINMENT_AUDIT.md)

**Key findings:**
- Component is self-contained (no props, no emits, no store)
- Uses wrong API endpoints (`/api/woodworking/...` instead of `/api/instrument/...`)
- DXF export and validation likely fail due to endpoint mismatch
- Client-side geometry math is correct (matches corrected arc length formula)
- Canvas-based rendering, not SVG

**Current rule:**
```
SpiralSoundholeDesigner.vue = canonical implementation
ApertureWorkspace.vue = beta consolidation shell
```

The workspace mounts the component but does not replace it. Standalone route `/calculators/acoustics/spiral-soundhole` remains active.

---

---

## Dev Order 8 — API Endpoint Normalization

**Status:** Complete  
**Date:** 2026-05-07

Normalized `SpiralSoundholeDesigner.vue` to use canonical endpoints.

**Change:**
```
OLD: /api/woodworking/soundhole/spiral/*
NEW: /api/instrument/soundhole/spiral/*
```

Backend `DualSpiralRequest` schema already matched frontend payload — no backend changes required.

**Verified:**
- Backend tests pass (24 tests)
- Frontend builds without errors
- Endpoint paths corrected

---

## Dev Order 9 — Canonical Route / Provenance Clarification

**Status:** Complete  
**Date:** 2026-05-07

Clarified route ownership and canonical status to prevent confusion between production tool and beta workspace.

**Canonical production route:**
```
/calculators/acoustics/spiral-soundhole
```

**Beta consolidation route:**
```
/art-studio/aperture
```

**Canonical implementation:**
```
packages/client/src/components/toolbox/acoustics/SpiralSoundholeDesigner.vue
```

**Changes made:**
- Added `ToolMetadata` interface to `toolRegistry.ts`
- Added `spiral-soundhole` entry with `canonical: true`, `status: 'stable'`
- Updated `aperture-workspace` entry with `canonical: false`, `mounts: ['SpiralSoundholeDesigner.vue']`
- Updated ApertureWorkspace.vue badge: "Mounted Production Tool"
- Updated PrerequisiteNotice with beta/canonical clarification

**Policy:**
The ApertureWorkspace may mount the canonical component, but it does not replace it until feature parity is verified.

---

## Dev Order 10 — StandardAperturePanel for Round/Oval/F-hole

**Status:** Complete  
**Date:** 2026-05-07

Created `StandardAperturePanel.vue` for standard aperture types (round, oval, f-hole) and mounted it in ApertureWorkspace.vue.

**New component:**
```
packages/client/src/views/art-studio/panels/StandardAperturePanel.vue
```

**Backend API:**
- `GET /api/instrument/soundhole/body-styles` — fetch body styles with standard diameters
- `POST /api/instrument/soundhole` — compute geometry for soundhole_type (round, oval, fhole)

**Response fields:**
- `area_mm2` — open area
- `perimeter_mm` — perimeter
- `pa_ratio_mm_inv` — P:A ratio
- `diameter_mm` — diameter (or equivalent diameter for oval)
- `position_from_neck_block_mm` — recommended position
- `gate` — GREEN/YELLOW/RED status
- `notes` — validation messages

**Features:**
- Aperture type selection (Round / Oval / F-hole)
- Body style dropdown with standard diameters
- Body length input
- Custom diameter override (round)
- Oval width/height configuration
- Geometry results display with gate badge
- F-hole redirects to dedicated calculator

**Registry update:**
- Added `StandardAperturePanel.vue` to `aperture-workspace` mounts list

---

## Dev Order 12 — Aperture Comparison Panel

**Status:** Complete  
**Date:** 2026-05-07

Created comparison panel for side-by-side aperture geometry analysis.

**New components:**
```
packages/client/src/components/shared/aperture/ApertureResultCard.vue
packages/client/src/components/shared/aperture/index.ts
packages/client/src/components/toolbox/acoustics/ApertureComparisonPanel.vue
```

**Architecture:**
- Reference aperture: round or oval (standard API)
- Candidate aperture: dual_spiral (combined Carlos Jumbo defaults)
- Comparison uses normalized `ApertureGeometry` contract
- Delta table shows absolute + percentage differences

**Combined dual-spiral logic:**
```typescript
combined.area_mm2 = upper.area_mm2 + lower.area_mm2
combined.perimeter_mm = upper.perimeter_mm + lower.perimeter_mm
combined.pa_ratio_mm_inv = combined.perimeter_mm / combined.area_mm2
combined.equivalent_diameter_mm = 2 * sqrt(combined.area_mm2 / PI)
aperture_type: 'dual_spiral'
```

**Features:**
- Reference type selection (Round / Oval)
- Body style + body length configuration
- Candidate displays Carlos Jumbo dual-spiral info
- Side-by-side ApertureResultCard display
- Delta comparison table with metrics
- Future Acoustic Metrics placeholder section

**Refactoring:**
- Created shared `ApertureResultCard.vue` component
- Refactored `StandardAperturePanel.vue` to use shared card
- Removed duplicate result display code

**Registry update:**
- Added `ApertureComparisonPanel.vue` to `aperture-workspace` mounts list

---

## Dev Order 13 — Target Matching UI Skeleton

**Status:** Complete  
**Date:** 2026-05-07

Renamed "Inverse Solver" tab to "Target Matching" and created task-based solver card UI.

### Target Matching Reframe

The former "Inverse Solver" tab is renamed "Target Matching."

The inverse solver is treated as an **internal calculation service**, not a user-facing endpoint-first interface.

The UI exposes solver intents (questions the solver answers):
- Solve required area
- Solve effective length
- Estimate acoustic loss
- Match candidate to reference

### Changes

**Tab update:**
- Label: `Inverse Solver` → `Target Matching`
- Icon: `🔄` → `🎯`
- Description updated to reflect solver intent framing
- Internal tab ID remains `'inverse'` to avoid churn

**Solver task cards (4 total):**

| Card | Question | Inputs | Output |
|------|----------|--------|--------|
| Solve Required Area | "What aperture area do I need?" | body_volume, target_f_H, thickness | area_mm² |
| Solve Effective Length | "What's my effective neck length?" | aperture_area, measured_f_H, volume | L_eff (mm) |
| Estimate Loss | "How much acoustic loss?" | measured_f_H, Q, geometry | R_acoustic |
| Match Candidate | "What must change to match reference?" | ref_geo, cand_geo, target_metric | parameter delta |

**Card structure:**
- Question (user-facing framing)
- Purpose description
- Inputs needed list
- Solves for output
- "Coming Soon" badge

**Architecture decision:**
The inverse solver will be implemented as an internal calculation service (`aperture_inverse_solver.py` or frontend utility), not as a direct endpoint-shaped UI. The UI presents tasks, not equations.

---

# Phase 2 — Workspace Normalization and Comparison Infrastructure

**Status:** Stable comparative research workspace  
**Date:** 2026-05-07  
**Dev Order:** 14

## Phase-2 Summary

Phase 2 transitions the Aperture Workspace from a shell prototype to a functional comparative aperture research environment.

**Completed Dev Orders:**
- Dev Order 10 — Standard Aperture Panel
- Dev Order 12 — Aperture Comparison Panel + Shared Result Card
- Dev Order 13 — Target Matching UI Skeleton

> **Note:** Shared `ApertureResultCard` extraction, originally planned as a standalone Dev Order 11, was completed as part of Dev Order 12 during comparison-panel integration.

---

## Current System State

### Canonical Specialist Engine
```
SpiralSoundholeDesigner.vue
```
Canonical production spiral tool. Owns rendering, state, export behavior. Uses custom canvas rendering.

### Workspace-Native Normalized Panels
```
StandardAperturePanel.vue
ApertureComparisonPanel.vue
```
Workspace-native panels using shared infrastructure and normalized geometry contracts.

### Shared UI Infrastructure
```
GateBadge.vue
SectionLabel.vue
PrerequisiteNotice.vue
DiagnosticCard.vue
ApertureResultCard.vue
```
Stable shared components for workflow UI patterns.

### Normalized Backend Contract
```
ApertureGeometry
```
Canonical comparison layer for cross-type aperture analysis.

---

## Stable Capabilities

### Standard Apertures
- Round soundhole geometry
- Oval soundhole geometry (Selmer/Maccaferri style)
- F-hole placeholder (redirects to dedicated calculator)

### Spiral System
- Dual-spiral Carlos Jumbo comparison
- Corrected path-length math (Dev Order 2)
- Normalized geometry metrics
- DXF export (canonical tool)
- Validation endpoints

### Comparison System
- Side-by-side geometry comparison
- Delta metrics (absolute + percentage)
- Combined dual-spiral comparison
- Normalized metric formatting
- Shared ApertureResultCard display

### Target Matching (UI Skeleton)
- Solver task cards (4 tasks)
- User-facing question framing
- Coming Soon status badges
- Architecture decision: internal service, not endpoint-first

---

## Geometry Contract Status

`ApertureGeometry` is now the canonical comparison layer.

**Field inventory:**
| Field | Type | Description |
|-------|------|-------------|
| `aperture_type` | `str` | Type identifier (round, oval, spiral, dual_spiral, fhole) |
| `area_mm2` | `float` | Open area in mm² |
| `perimeter_mm` | `float` | Total perimeter in mm |
| `equivalent_diameter_mm` | `float` | Diameter of circle with same area |
| `characteristic_width_mm` | `float \| None` | Type-specific width (slot width for spiral) |
| `path_length_mm` | `float \| None` | Total path/arc length |
| `pa_ratio_mm_inv` | `float \| None` | Perimeter-to-area ratio (mm⁻¹) |

**Contract rules:**
- Backend remains geometry truth
- Frontend displays normalized metrics
- Frontend does not recompute canonical geometry

---

## Spiral System Status

`SpiralSoundholeDesigner.vue` remains canonical.

**Current state:**
- Mounted in ApertureWorkspace (Spiral tab)
- NOT replaced by workspace panels
- Still owns rendering, state, export behavior
- Still uses custom canvas rendering
- API endpoints normalized (Dev Order 8)

**Workspace relationship:**
```
Workspace consumes spiral geometry outputs
Workspace does NOT own spiral rendering
```

This boundary is critical for preventing regression.

---

## Comparison Architecture

### Reference Side
- Round aperture
- Oval aperture

### Candidate Side
- Spiral (dual-spiral combined)
- Round aperture
- Oval aperture

### Spiral Comparison Mode
Combined dual-spiral comparison:
```typescript
combined.area_mm2 = upper.area_mm2 + lower.area_mm2
combined.perimeter_mm = upper.perimeter_mm + lower.perimeter_mm
combined.pa_ratio_mm_inv = combined.perimeter_mm / combined.area_mm2
combined.equivalent_diameter_mm = 2 * sqrt(combined.area_mm2 / PI)
aperture_type: 'dual_spiral'
```

**Not implemented:** Upper/lower isolated comparison.

---

## Unresolved Gaps

### Acoustic Modeling
- Helmholtz frequency estimation not implemented
- Q factor / sustain estimation not implemented
- Effective neck-length approximation not implemented

### Tornavoz Modeling
- No compensation-layer modeling yet
- No tube-attachment geometry

### Additional Aperture Families
- D-hole (Selmer-style arc + chord)
- Duck-head (Django Reinhardt era)
- Slot-port (linear slot)
- Side-port (upper bout secondary)
- Trapezoid (modern jazz)

### Inverse Solver Extraction
- Legacy inverse solver not yet normalized
- Target Matching UI skeleton in place, math deferred

### Shared Export Infrastructure
- DXF export still owned by specialist tools
- No unified export layer yet

### Multi-Cavity Systems
- Selmer/Maccaferri two-cavity comparison not implemented
- Coupled resonator modeling deferred

---

## Governance Status

**Active governance:** `FEATURE_PARITY_MIGRATION_POLICY.md`

**Migration order:**
```
mount → verify → audit → extract → normalize → replace
```

**Phase-2 validation:**
This policy successfully prevented regression during Phase-2 development:
- Canonical specialist tools remained intact
- Workspace-native normalized panels added incrementally
- Shared infrastructure extracted only after parity verification
- Comparison tooling introduced without replacing canonical implementations

---

## Recommended Next Phases

### Phase 3A — Acoustic Comparison Metrics
- Helmholtz estimation
- Effective neck-length approximation
- P:A-driven comparative analysis

### Phase 3B — Inverse Solver Extraction
- Normalize archived inverse acoustic tools
- Wire solver service to Target Matching UI

### Phase 3C — Additional Aperture Families
- D-hole geometry
- Duck-head geometry
- Slot-port geometry

### Phase 3D — Shared Export Infrastructure
- Normalized DXF/SVG export layer
- Unified export service

### Phase 3E — Tornavoz Modeling
- Compensation-layer experimentation
- Tube-attachment geometry

---

## Verification Snapshot

**Captured:** 2026-05-07

| Check | Result |
|-------|--------|
| Frontend build | PASS (32.70s) |
| Backend aperture/spiral tests | 39/39 PASS |
| Comparison panel browser verification | PASS |
| Canonical spiral route verification | PASS (`/calculators/acoustics/spiral-soundhole`) |
| Workspace comparison verification | PASS (`/art-studio/aperture`) |
| Standard aperture panel verification | PASS |
| Target Matching UI verification | PASS |

**Coverage:** 21.99% (above 20% threshold)

---

## Dev Order 15 — Acoustic State Model Foundation

**Status:** Complete  
**Date:** 2026-05-07

Created normalized Acoustic State model that bridges geometry comparison and future target-matching / inverse-solver work.

### New Files

| File | Purpose |
|------|---------|
| `packages/client/src/types/acoustics.ts` | `AcousticState`, `AcousticConfidence`, `AcousticStateSource`, `ApertureGeometryLike` types |
| `packages/client/src/utils/acoustics/acousticState.ts` | `createGeometryAcousticState()`, `hasEstimatedAcoustics()`, label helpers |
| `packages/client/src/utils/acoustics/index.ts` | Barrel export |

### Modified Files

| File | Change |
|------|--------|
| `ApertureComparisonPanel.vue` | Imports acoustic utilities, creates reference/candidate acoustic states, displays Acoustic State section |

### Acoustic State Contract

```typescript
interface AcousticState {
  id: string
  label: string
  source: AcousticStateSource
  confidence: AcousticConfidence
  apertureType?: string
  apertureGeometry?: ApertureGeometryLike
  bodyVolumeLiters?: number
  estimatedHelmholtzHz?: number
  estimatedEffectiveLengthMm?: number
  qEstimate?: number
  lossEstimate?: number
  assumptions: string[]
  warnings?: string[]
}
```

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| Descriptive first | AcousticState describes known/estimated values, does not claim prediction accuracy |
| Geometry separate | ApertureGeometry remains distinct; AcousticState wraps/references it |
| Confidence mandatory | Every acoustic state identifies confidence (`unknown`, `low`, `medium`, `high`) |
| Assumptions mandatory | Prevents estimated physics from looking like measured truth |
| ApertureGeometryLike | Decoupled interface mirrors ApertureGeometry fields without Vue component dependency |

### UI Integration

Comparison panel now displays Acoustic State section with:
- Source (Geometry Estimate)
- Confidence (Low)
- Assumptions list
- "No calibrated acoustic estimates attached yet" message when no estimates present

Future Acoustic Intelligence section retained as planned features list.

### Verification

| Check | Result |
|-------|--------|
| Frontend build | PASS (36.73s) |
| Acoustic state display | Renders in Comparison tab |
| Confidence/source/assumptions | Displayed correctly |
| No fake acoustic predictions | Confirmed |

---

## Dev Order 16 — Acoustic State Display Extraction

**Status:** Complete  
**Date:** 2026-05-08

Extracted inline acoustic state display from ApertureComparisonPanel into a reusable shared component.

### New Files

| File | Purpose |
|------|---------|
| `packages/client/src/components/shared/acoustics/AcousticStateCard.vue` | Reusable acoustic state display component |
| `packages/client/src/components/shared/acoustics/index.ts` | Barrel export |

### Modified Files

| File | Change |
|------|--------|
| `ApertureComparisonPanel.vue` | Replaced inline display with `<AcousticStateCard>`, removed unused CSS |

### Component Features

| Feature | Implementation |
|---------|----------------|
| Confidence mapping | `low/unknown/medium → yellow`, `high → green` (no red) |
| Estimated values | Simple key-value rows with units |
| Warnings | Distinct yellow/orange styling, separate from assumptions |
| Aperture type | Shown only if `apertureType` is defined |
| Styling | Component-local CSS, reuses `GateBadge` from shared workflow |

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| No red for confidence | Red reserved for diagnostic failures/blockers |
| Warnings distinct from assumptions | Visual separation prevents confusion |
| Aperture type conditional | Avoids redundancy when parent context provides type |

### Verification

| Check | Result |
|-------|--------|
| Frontend build | PASS (43.14s) |
| Component renders | Reference + candidate cards in Comparison tab |
| Warnings display | Distinct yellow/orange styling |
| No solver logic added | Confirmed |

---

## Dev Order 17 — Target Matching Task Detail Panels

**Status:** Complete  
**Date:** 2026-05-08

Expanded Target Matching tab into structured task-detail panels for solver intents.

### New Files

| File | Purpose |
|------|---------|
| `packages/client/src/components/shared/acoustics/TargetTaskCard.vue` | Reusable task card for solver intents |
| `packages/client/src/components/toolbox/acoustics/TargetMatchingPanel.vue` | Target Matching panel with 4 task cards |

### Modified Files

| File | Change |
|------|--------|
| `packages/client/src/components/shared/acoustics/index.ts` | Added `TargetTaskCard` export |
| `packages/client/src/views/art-studio/ApertureWorkspace.vue` | Replaced inline solver content with `TargetMatchingPanel`, removed solver CSS (~100 lines) |

### Task Cards

| Task | Question | Output |
|------|----------|--------|
| Solve Required Area | What aperture area is required to achieve a target air resonance? | required aperture area |
| Solve Effective Length | What effective neck length does this aperture geometry imply? | estimated effective length |
| Estimate Loss | How much acoustic loss or resistance is implied by the measured response? | loss/resistance estimate |
| Match Candidate | What geometry changes are required for a candidate aperture to match a reference response? | parameter deltas |

### Each Card Displays

- Question (user-facing framing)
- Purpose description
- Inputs needed
- Solves for (output)
- Uses (data dependencies)
- Assumptions
- Confidence caveats
- Optional note

### Workflow Relationship Diagram

Horizontal flex row showing:
```
[Geometry] → [Comparison] → [Acoustic State] → [Target Matching]
```

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| Task-oriented interface | UI exposes "What do you want to solve?" not "Which equation?" |
| TargetTaskCard in shared/acoustics | Reusable for future calibration/measurement workflows |
| Solver CSS moved to panel | Shell owns layout only, panels own their styling |
| No solver math | Informational scaffold only |

### Verification

| Check | Result |
|-------|--------|
| Frontend build | PASS (75s) |
| Four task panels render | Confirmed |
| Workflow diagram renders | Confirmed |
| No fake equations/outputs | Confirmed |
| No disabled fake forms | Confirmed |

---

## Dev Order 18 — Voided / Duplicate

**Status:** Voided  
**Date:** 2026-05-08  
**Reason:** Scope already completed in Dev Order 17.

Dev Order 18 specified:
- Create `TargetTaskCard.vue`
- Create `TargetMatchingPanel.vue`
- Move solver CSS out of `ApertureWorkspace.vue`
- Add workflow relationship diagram

All items were completed as part of Dev Order 17. This order is voided to prevent duplicate documentation.

Browser verification remains pending as Phase-3 readiness check.

---

## Phase-3 Readiness Browser Verification — Complete

**Status:** Passed  
**Date:** 2026-05-09

### Verification Checklist

| Tab | Check | Status |
|-----|-------|--------|
| Comparison | Geometry cards render | ✅ |
| Comparison | Delta table renders | ✅ |
| Comparison | Acoustic state cards render | ✅ |
| Target Matching | 4 task cards render | ✅ |
| Target Matching | Workflow diagram renders | ✅ |
| Standard | Round/oval/f-hole panel works | ✅ |
| Spiral | Mounted SpiralSoundholeDesigner works | ✅ |
| All | No blocking console errors | ✅ |

**Route:** `/art-studio/aperture`

Phase-2 is now complete. Phase-3 acoustic utility/math work can begin.

---

## Dev Order 19 — Measured Data Attachment Scaffold

**Status:** Complete  
**Date:** 2026-05-09

Created scaffold for attaching measured acoustic response data to comparison panels.

### New Files

| File | Purpose |
|------|---------|
| `packages/client/src/types/measurements.ts` | `MeasuredResponse`, `MeasurementSource`, `MeasurementMethod` types |
| `packages/client/src/utils/acoustics/measuredResponse.ts` | `createEmptyMeasuredResponse()`, `hasMeasuredResponseData()`, label helpers |
| `packages/client/src/components/shared/acoustics/MeasuredResponseCard.vue` | Display component for measured acoustic response |

### Modified Files

| File | Change |
|------|--------|
| `packages/client/src/components/shared/acoustics/index.ts` | Added `MeasuredResponseCard` export |
| `packages/client/src/utils/acoustics/index.ts` | Added measured response utilities export |
| `packages/client/src/components/toolbox/acoustics/ApertureComparisonPanel.vue` | Added measured response section with placeholder cards |

### MeasuredResponse Contract

```typescript
interface MeasuredResponse {
  id: string
  label: string
  source: MeasurementSource  // 'manual' | 'tap_tone_pi' | 'imported_file' | 'unknown'
  method: MeasurementMethod  // 'tap_test' | 'sine_sweep' | 'impulse_response' | 'manual_observation' | 'unknown'
  measuredHelmholtzHz?: number
  measuredQ?: number
  dominantPeakHz?: number
  notes?: string[]
  warnings?: string[]
  attachedTo?: 'reference' | 'candidate' | 'comparison' | 'unknown'
}
```

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| Separate from AcousticState | AcousticState = estimated/descriptive, MeasuredResponse = observed/measured |
| Placeholder cards | Cards display "No measured response data attached yet" until data entry implemented |
| No raw FFT/spectra | Summary metrics only (Helmholtz, Q, dominant peak) |
| attachedTo field | Tracks which geometry the measurement belongs to |

### Architectural Distinction

```
Geometry → AcousticState (estimated) → MeasuredResponse (observed) → CalibrationDelta (future)
```

AcousticState is geometry-derived. MeasuredResponse is actual measurement data. This separation prevents confusion between estimated and measured values.

### Verification

| Check | Result |
|-------|--------|
| TypeScript typecheck | PASS |
| Measured Response section renders | Pending browser verification |
| Empty state message | "No measured response data attached yet" |
| Distinction notice | "Measured response is separate from estimated acoustic state" |

---

## Dev Order 20 — Measured Response Manual Attachment Controls

**Status:** Complete  
**Date:** 2026-05-09

Added manual entry controls for measured response data in the Comparison panel.

### Modified Files

| File | Change |
|------|--------|
| `packages/client/src/components/shared/acoustics/MeasuredResponseCard.vue` | Added editable controls, edit/save/cancel flow, informational notice |
| `packages/client/src/components/toolbox/acoustics/ApertureComparisonPanel.vue` | Changed measured response from computed to reactive refs, added update handlers |

### Manual Entry Controls

Each MeasuredResponseCard now supports:

| Field | Type | Validation |
|-------|------|------------|
| Measured Helmholtz (Hz) | number input | > 0 |
| Measured Q | number input | > 0 |
| Dominant Peak (Hz) | number input | > 0 |
| Add Note | textarea | trimmed string |

### UI Flow

1. Card displays "Enter Measurements" button when editable
2. Clicking opens inline form with number inputs + textarea
3. Save validates and updates local state
4. Cancel discards changes
5. Source updates to "Manual Entry", Method to "Manual Observation"

### Informational Notice

Added prominent notice:
```
Manual measurements are informational only and are not yet used for calibrated prediction.
```

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| Local state only | No persistence, no backend — values exist in session only |
| No calibration | Entering values does not trigger prediction |
| Separate from AcousticState | Measured data remains distinct from geometry-derived estimates |
| Lightweight validation | frequency > 0, Q > 0 only |
| Notes append | New notes append to existing notes array |

### Verification

| Check | Result |
|-------|--------|
| Build | PASS (31.98s) |
| Edit form renders | PASS |
| Save/cancel flow | PASS |
| Values persist in session | PASS |
| No backend changes | Confirmed |
| No calibration math | Confirmed |

---

## Dev Order 21 — Measured Response Delta Display

**Status:** Complete  
**Date:** 2026-05-09

Added display-only measured response delta comparison.

### New Files

| File | Purpose |
|------|---------|
| `packages/client/src/components/shared/acoustics/MeasuredResponseDeltaCard.vue` | Measured response delta comparison table |

### Modified Files

| File | Change |
|------|--------|
| `packages/client/src/components/shared/acoustics/index.ts` | Added MeasuredResponseDeltaCard export |
| `packages/client/src/components/toolbox/acoustics/ApertureComparisonPanel.vue` | Added MeasuredResponseDeltaCard after measured response cards |

### Delta Display

| Metric | Format |
|--------|--------|
| Helmholtz (Hz) | Reference, Candidate, Delta (+/-) |
| Q Factor | Reference, Candidate, Delta (+/-) |
| Dominant Peak (Hz) | Reference, Candidate, Delta (+/-) |

### Delta Rules

- Absolute delta: `candidate - reference`
- Percentage delta: `(delta / reference) * 100` when reference > 0
- Missing values: display "—"
- Zero reference: absolute delta only, no percentage

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| Separate component | Reusable concept, keeps panel manageable |
| Same table structure | Visual consistency with geometry delta |
| Distinct header/notice | Preserves conceptual boundary |
| No calibration language | Observational comparison only |

### Informational Notice

```
Measured deltas compare manually entered observations only. They are not calibrated predictions.
```

### Verification

| Check | Result |
|-------|--------|
| Build | PASS (38.14s) |
| Delta card renders | PASS |
| Missing data handling | PASS |
| Delta calculation | PASS |
| No calibration implied | Confirmed |

---

## Dev Order 22 — Calibration Readiness Layer

**Status:** Complete  
**Date:** 2026-05-10

Created calibration readiness layer that evaluates whether data is sufficient for future calibration.

### New Files

| File | Purpose |
|------|---------|
| `packages/client/src/types/calibration.ts` | `CalibrationReadiness`, `CalibrationReadinessGate`, `CalibrationReadinessDiagnostic` types |
| `packages/client/src/utils/acoustics/calibrationReadiness.ts` | `evaluateCalibrationReadiness()` utility |
| `packages/client/src/components/shared/acoustics/CalibrationReadinessCard.vue` | Readiness display component |

### Modified Files

| File | Change |
|------|--------|
| `packages/client/src/components/shared/acoustics/index.ts` | Added CalibrationReadinessCard export |
| `packages/client/src/utils/acoustics/index.ts` | Added calibrationReadiness export |
| `packages/client/src/components/toolbox/acoustics/ApertureComparisonPanel.vue` | Added calibration readiness evaluation and display |

### Readiness Rules

| Gate | Conditions |
|------|------------|
| RED | Missing geometry, no measurements, no comparable metrics |
| YELLOW | One-sided measurements, Helmholtz without Q, Q without Helmholtz, only peak, manual source, unknown method |
| GREEN | Both geometries present, both have Helmholtz + Q, known method, no blockers/warnings |

### CalibrationReadiness Contract

```typescript
interface CalibrationReadiness {
  overallGate: CalibrationReadinessGate
  diagnostics: CalibrationReadinessDiagnostic[]
  readyForCalibration: boolean
  missingFields: string[]
  warnings: string[]
}
```

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| Diagnostic only | Does not perform calibration, only evaluates readiness |
| Uses standard gates | green/yellow/red consistent with workflow |
| Reads, does not mutate | Evaluates existing data without modifying it |
| Explicit missing values | No silent inference of missing data |

### Important

This layer does NOT perform calibration or prediction. It only evaluates data completeness and provenance.

### Verification

| Check | Result |
|-------|--------|
| Build | PASS (34.39s) |
| Readiness card renders | PASS |
| RED gate on empty | PASS |
| YELLOW gate on partial | PASS |
| GREEN gate conditions | PASS |
| No calibration math | Confirmed |

---

## Dev Order 23 — Calibration Residual Preview

**Status:** Complete  
**Date:** 2026-05-10

Created calibration residual preview that shows gaps between estimated and measured values.

### New Files

| File | Purpose |
|------|---------|
| `packages/client/src/types/calibrationResiduals.ts` | `CalibrationResidual`, `CalibrationResidualPreview` types |
| `packages/client/src/utils/acoustics/calibrationResiduals.ts` | `createCalibrationResidualPreview()` utility |
| `packages/client/src/components/shared/acoustics/CalibrationResidualCard.vue` | Residual preview display component |

### Modified Files

| File | Change |
|------|--------|
| `packages/client/src/components/shared/acoustics/index.ts` | Added CalibrationResidualCard export |
| `packages/client/src/utils/acoustics/index.ts` | Added calibrationResiduals export |
| `packages/client/src/components/toolbox/acoustics/ApertureComparisonPanel.vue` | Added residual preview cards for reference and candidate |

### Residual Rules

| Metric | Estimated Source | Measured Source |
|--------|------------------|-----------------|
| Helmholtz | `AcousticState.estimatedHelmholtzHz` | `MeasuredResponse.measuredHelmholtzHz` |
| Q Factor | `AcousticState.qEstimate` | `MeasuredResponse.measuredQ` |
| Dominant Peak | No estimate available yet | `MeasuredResponse.dominantPeakHz` |

### Residual Calculation

```
residual = measured - estimated
percentResidual = estimated !== 0 ? (residual / estimated) * 100 : null
```

### Missing Data Behavior

- Either estimate or measurement missing → residual unavailable
- No available residuals → "No residuals available yet" message
- Current geometry-only state will show all residuals as unavailable (expected)

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| Observational only | Does not calibrate, fit, or correct |
| No estimate fabrication | Missing estimates remain missing |
| No mutation | Reads AcousticState and MeasuredResponse without modifying |
| Two cards | Reference and candidate each have their own residual preview |

### Important

This layer does NOT calibrate, fit, correct, or predict. It only displays residuals when both estimated and measured values already exist.

### Verification

| Check | Result |
|-------|--------|
| Build | PASS (29.56s) |
| Residual cards render | Pending browser verification |
| Unavailable state displays | Pending browser verification |
| No fake estimates | Confirmed |
| No calibration math | Confirmed |

---

## Dev Order 24 — Estimate Source Placeholder / Estimate Attachment Scaffold

**Status:** Complete  
**Date:** 2026-05-11

Added manual estimate attachment to AcousticState cards.

### Modified Files

| File | Change |
|------|--------|
| `packages/client/src/utils/acoustics/acousticState.ts` | Added `mergeManualEstimates()`, `updateGeometryPreservingEstimates()` |
| `packages/client/src/components/shared/acoustics/AcousticStateCard.vue` | Added editable controls for estimates |
| `packages/client/src/components/toolbox/acoustics/ApertureComparisonPanel.vue` | Changed acoustic state to refs with watchers, added update handlers |

### Estimate Fields

| Field | Type | Validation |
|-------|------|------------|
| Estimated Helmholtz (Hz) | number | > 0 |
| Estimated Effective Length (mm) | number | > 0 |
| Q Estimate | number | > 0 |
| Loss Estimate | number | >= 0 |

### Geometry Change Behavior

When geometry changes while manual estimates exist:
- Geometry fields update
- Manual estimates preserved
- Warning added: "Geometry has changed since this manual estimate was attached..."
- Source remains manual, confidence remains low

### Manual Estimate Provenance

When estimates are attached:
```
source: manual
confidence: low
assumptions:
  - Manual estimate attached by user
  - No calibrated acoustic model applied
  - Estimate is not generated by the system
```

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| Estimates attached, not computed | No equations added |
| Provenance required | Source and confidence explicitly set |
| Estimates separate from measurements | AcousticState estimates, MeasuredResponse measurements |
| Geometry changes preserve estimates | User data not silently cleared |

### Important

Manual estimates are placeholders and are NOT calibrated predictions. They enable exercising the residual preview without implementing prediction.

### Verification

| Check | Result |
|-------|--------|
| Build | PASS (33.47s) |
| Attach Estimate button renders | Pending browser verification |
| Estimate form saves correctly | Pending browser verification |
| Residuals appear with both estimate + measurement | Pending browser verification |
| Geometry change preserves estimates | Pending browser verification |
| No equations added | Confirmed |

---

## Dev Order 25 — Estimate / Measurement Pairing Status

**Status:** Complete  
**Date:** 2026-05-11

Added pairing status layer showing which metrics have both estimate and measurement.

### New Files

| File | Purpose |
|------|---------|
| `packages/client/src/types/measurementPairing.ts` | `PairingStatus`, `MeasurementPairingMetric`, `MeasurementPairingStatus` types |
| `packages/client/src/utils/acoustics/measurementPairing.ts` | `evaluateMeasurementPairing()` utility |
| `packages/client/src/components/shared/acoustics/MeasurementPairingStatusCard.vue` | Pairing status display component |

### Modified Files

| File | Change |
|------|--------|
| `packages/client/src/components/shared/acoustics/index.ts` | Added MeasurementPairingStatusCard export |
| `packages/client/src/utils/acoustics/index.ts` | Added measurementPairing export |
| `packages/client/src/components/toolbox/acoustics/ApertureComparisonPanel.vue` | Added pairing status cards for reference and candidate |

### Pairing Status Values

| Status | Meaning |
|--------|---------|
| `paired` | Both estimate and measurement exist |
| `estimate_only` | Estimate exists, measurement missing |
| `measurement_only` | Measurement exists, estimate missing |
| `missing` | Both missing |

### Metrics Evaluated

| Metric | Estimate Field | Measurement Field |
|--------|----------------|-------------------|
| Helmholtz Frequency | `estimatedHelmholtzHz` | `measuredHelmholtzHz` |
| Q Factor | `qEstimate` | `measuredQ` |

### Gate Mapping

| Condition | Gate | Label |
|-----------|------|-------|
| `pairedCount > 0` | green | Residual Ready |
| `availableCount > 0` but no pairs | yellow | Partial Data |
| `availableCount == 0` | red | No Data |

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| Diagnostic only | Does not calculate residuals, only shows pairing status |
| Per aperture | Reference and candidate each have their own status card |
| Explains residual readiness | Shows why residuals are or are not available |

### Important

Pairing status is diagnostic only. It does not calibrate, fit, or predict.

### Verification

| Check | Result |
|-------|--------|
| Build | PASS (38.54s) |
| Pairing cards render | Pending browser verification |
| Missing state works | Pending browser verification |
| Estimate only state works | Pending browser verification |
| Measurement only state works | Pending browser verification |
| Paired state works | Pending browser verification |
| No calibration math | Confirmed |

---

## Dev Order 26 — Phase-3A Verification Checkpoint

**Status:** Complete  
**Date:** 2026-05-11

Phase-3A establishes the observational/diagnostic scaffold for acoustic comparison. This checkpoint documents and validates the architecture before Phase-3B (calibration helpers).

### Phase-3A Summary (Dev Orders 19-25)

| Dev Order | Feature | Purpose |
|-----------|---------|---------|
| 19 | Measured Data Attachment Scaffold | `MeasuredResponse` type, `MeasuredResponseCard` display |
| 20 | Manual Attachment Controls | Editable entry for measured Helmholtz, Q, dominant peak |
| 21 | Measured Response Delta Display | Delta comparison between reference/candidate measurements |
| 22 | Calibration Readiness Layer | Gate-based readiness evaluation (green/yellow/red) |
| 23 | Calibration Residual Preview | Shows gaps between estimate and measurement |
| 24 | Estimate Attachment Scaffold | Editable manual estimates on AcousticState |
| 25 | Measurement Pairing Status | Shows which metrics have both estimate + measurement |

### Architecture Stack

```
┌─────────────────────────────────────────────────────────────┐
│                    ApertureComparisonPanel                   │
├─────────────────────────────────────────────────────────────┤
│  Geometry Comparison                                         │
│    └── ApertureResultCard (×2: reference, candidate)        │
│    └── Geometry Delta Table                                 │
├─────────────────────────────────────────────────────────────┤
│  Acoustic State Layer                                        │
│    └── AcousticStateCard (×2: reference, candidate)         │
│        • geometry-derived descriptive metrics               │
│        • manual estimate attachment (editable)              │
│        • confidence + assumptions display                   │
├─────────────────────────────────────────────────────────────┤
│  Measured Response Layer                                     │
│    └── MeasuredResponseCard (×2: reference, candidate)      │
│        • manual measurement entry (editable)                │
│        • source/method provenance                           │
│    └── MeasuredResponseDeltaCard                            │
│        • ref vs candidate measured delta                    │
├─────────────────────────────────────────────────────────────┤
│  Diagnostic Layer                                            │
│    └── CalibrationReadinessCard (×2: reference, candidate)  │
│        • gate evaluation (green/yellow/red)                 │
│        • missing fields list                                │
│    └── CalibrationResidualCard (×2: reference, candidate)   │
│        • estimate vs measured gap                           │
│    └── MeasurementPairingStatusCard (×2: ref, candidate)    │
│        • paired/estimate_only/measurement_only/missing      │
└─────────────────────────────────────────────────────────────┘
```

### Explicit Non-Goals (Phase-3A Scope)

| Non-Goal | Status |
|----------|--------|
| Calibration | NOT IMPLEMENTED — no fitting, no parameter extraction |
| Prediction | NOT IMPLEMENTED — no Helmholtz estimation from geometry |
| Equations | NOT ADDED — no acoustic physics formulas |
| Backend changes | NONE — all Phase-3A is frontend diagnostic scaffold |
| Persistence | NONE — all data is session-only |

### Stable Concepts

| Concept | Definition |
|---------|------------|
| `AcousticState` | Geometry-derived descriptive metrics; editable manual estimates |
| `MeasuredResponse` | Observed measurement data; editable manual entry |
| `CalibrationReadiness` | Gate-based diagnostic; evaluates data completeness |
| `CalibrationResidual` | Gap between estimate and measurement (display only) |
| `MeasurementPairingStatus` | Shows which metrics have both estimate + measurement |

### Conceptual Boundaries

```
Geometry → AcousticState (estimate) → MeasuredResponse (observed)
                                              ↓
                          CalibrationResidual (gap display only)
                                              ↓
                          CalibrationReadiness (diagnostic only)
```

**AcousticState** describes what we estimate.  
**MeasuredResponse** records what we observed.  
**CalibrationResidual** shows the gap — it does NOT fit or correct.  
**CalibrationReadiness** evaluates sufficiency — it does NOT calibrate.

### Remaining Gaps for Phase-3B+

| Gap | Phase | Description |
|-----|-------|-------------|
| Helmholtz estimation | 3B | Geometry → estimated frequency |
| Effective length calculation | 3B | From aperture geometry |
| Q estimation | 3B | From geometry + assumptions |
| Calibration fitting | 3C+ | Parameter extraction from residuals |
| Persistence | 3C+ | Save/load measurements and estimates |
| tap_tone_pi integration | Future | Import measured response from device |

### Build Verification

| Check | Result |
|-------|--------|
| `npm run build` | PASS (32.96s) |
| Pre-existing type errors | Present (headstock module, unrelated) |
| Phase-3A code type-safe | Confirmed |

### Browser Verification Checklist

| Tab | Feature | Status |
|-----|---------|--------|
| Comparison | Geometry cards render | ✅ |
| Comparison | Acoustic state cards render | ✅ |
| Comparison | Measured response cards render | ✅ |
| Comparison | Measured response delta renders | ✅ |
| Comparison | Calibration readiness renders | ✅ |
| Comparison | Calibration residual renders | ✅ |
| Comparison | Pairing status renders | ✅ |
| Comparison | Manual estimate entry works | ✅ |
| Comparison | Manual measurement entry works | ✅ |
| Comparison | Geometry change preserves estimates | ✅ |
| Standard | Panel works | ✅ |
| Spiral | Mounted component works | ✅ |
| Target Matching | Task cards render | ✅ |

### Phase-3A Complete

Phase-3A establishes the observational scaffold. All data entry is manual. All displays are diagnostic. No calibration, no prediction, no equations.

Phase-3B may now implement calibration helpers (Helmholtz estimation, effective length, Q estimation) using the scaffold established here.

---

## Dev Order 27 — First-Order Helmholtz Estimate Helper

**Status:** Complete  
**Date:** 2026-05-11

First Phase-3B acoustic calculation. Estimate helper, not calibrated prediction.

### New Files

| File | Purpose |
|------|---------|
| `packages/client/src/types/helmholtz.ts` | `HelmholtzEstimateInput`, `HelmholtzEstimateResult` types |
| `packages/client/src/utils/acoustics/helmholtzEstimate.ts` | `estimateHelmholtzFrequency()` utility |
| `packages/client/src/components/shared/acoustics/HelmholtzEstimateCard.vue` | Estimate helper card |

### Modified Files

| File | Change |
|------|--------|
| `packages/client/src/components/shared/acoustics/index.ts` | Added HelmholtzEstimateCard export |
| `packages/client/src/utils/acoustics/index.ts` | Added helmholtzEstimate export |
| `packages/client/src/components/toolbox/acoustics/ApertureComparisonPanel.vue` | Added Helmholtz estimate section |

### Formula

```
f_H = (c / 2π) × √(A / (V × L_eff))
```

Where:
- `c` = speed of sound (default 343 m/s)
- `A` = aperture area (m²)
- `V` = body volume (m³)
- `L_eff` = effective neck length (m)

### User Inputs

| Input | Unit | Default |
|-------|------|---------|
| Aperture Area | mm² | from geometry |
| Body Volume | liters | blank (user required) |
| Effective Length | mm | blank (user required) |
| Speed of Sound | m/s | 343 |

### Attach Behavior

When estimate is attached to AcousticState:
- `estimatedHelmholtzHz` updated
- `bodyVolumeLiters` updated
- `estimatedEffectiveLengthMm` updated
- `source` = `'geometry_estimate'`
- `confidence` = `'low'`
- Assumptions and warnings from result merged

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| Two-step flow | Estimate → review → attach prevents silent attachment |
| No automatic defaults | Effective length is highly assumption-sensitive |
| Low confidence fixed | Not a calibrated prediction |
| Body volume persisted | Travels with the attached state |

### Important

This is a **first-order estimate helper**, not a calibrated prediction. All displays include explicit warnings:
- "First-order Helmholtz estimate only. Not calibrated prediction."
- "This estimate does not include two-cavity coupling, modal interaction, tornavoz effects, or measured calibration."

### Verification

| Check | Result |
|-------|--------|
| Build | PASS (30.83s) |
| Estimate cards render | Pending browser verification |
| Empty inputs prevent estimate | Pending browser verification |
| Estimate attaches to AcousticState | Pending browser verification |
| Residuals activate with matching measurement | Pending browser verification |
| No backend changes | Confirmed |

---

## Dev Order 28 — First-Order Estimate Assumption Summary

**Status:** Complete  
**Date:** 2026-05-11

Exposes the assumptions and provenance attached to first-order Helmholtz estimates so estimates remain auditable before calibration helpers exist.

### Prerequisite Patch

Added provenance fields to `AcousticState`:

```typescript
speedOfSoundMps?: number
estimateMethod?: 'first_order_helmholtz' | string
```

Updated Dev Order 27 attach handlers to persist these fields.

### New Files

| File | Purpose |
|------|---------|
| `packages/client/src/types/estimateAssumptions.ts` | `EstimateAssumptionSummary` type |
| `packages/client/src/utils/acoustics/estimateAssumptions.ts` | `createEstimateAssumptionSummary()` utility |
| `packages/client/src/components/shared/acoustics/EstimateAssumptionSummaryCard.vue` | Assumption summary display |

### Modified Files

| File | Change |
|------|--------|
| `packages/client/src/types/acoustics.ts` | Added `speedOfSoundMps`, `estimateMethod` fields |
| `packages/client/src/components/shared/acoustics/index.ts` | Added EstimateAssumptionSummaryCard export |
| `packages/client/src/utils/acoustics/index.ts` | Added estimateAssumptions export |
| `packages/client/src/components/toolbox/acoustics/ApertureComparisonPanel.vue` | Added estimate summary section, updated attach handlers |

### Summary Content

| Field | Source |
|-------|--------|
| Estimated Helmholtz | `AcousticState.estimatedHelmholtzHz` |
| Body Volume | `AcousticState.bodyVolumeLiters` |
| Effective Length | `AcousticState.estimatedEffectiveLengthMm` |
| Speed of Sound | `AcousticState.speedOfSoundMps` |
| Method | `AcousticState.estimateMethod` |
| Source | `AcousticState.source` |
| Confidence | `AcousticState.confidence` |
| Assumptions | `AcousticState.assumptions` |
| Warnings | `AcousticState.warnings` |

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| Explicit provenance fields | Don't infer from assumption strings |
| Reads from AcousticState | Not transient form state |
| Observational only | Does not compute or validate |

### Important

Assumption summaries document estimate provenance only. They do not calibrate or validate the estimate.

Rule: **Provenance fields are data, not prose.**

### Verification

| Check | Result |
|-------|--------|
| Build | PASS (36.84s) |
| Summary cards render | Pending browser verification |
| Empty state works | Pending browser verification |
| Attached estimate populates summary | Pending browser verification |
| Provenance fields persist correctly | Pending browser verification |

---

## Dev Order 29 — Estimate vs Measurement Residual Annotation

**Status:** Complete  
**Date:** 2026-05-11

Annotates residual previews with the estimate provenance behind each available residual, making residuals traceable to their assumptions.

### Modified Files

| File | Change |
|------|--------|
| `packages/client/src/types/calibrationResiduals.ts` | Added `ResidualEstimateProvenance` interface, added `provenance` to `CalibrationResidualPreview` |
| `packages/client/src/utils/acoustics/calibrationResiduals.ts` | Attach provenance from AcousticState when residuals available |
| `packages/client/src/components/shared/acoustics/CalibrationResidualCard.vue` | Display provenance section after residuals table |

### Provenance Display

When at least one residual is available, shows:

| Field | Source |
|-------|--------|
| Method | `AcousticState.estimateMethod` |
| Source | `AcousticState.source` |
| Confidence | `AcousticState.confidence` |
| Assumptions | `AcousticState.assumptions` (first 3) |
| Warnings | `AcousticState.warnings` (first 3) |

### Layout

```
Residuals Table
  Metric | Estimated | Measured | Residual
  ...

Estimate Provenance
  Method: First-Order Helmholtz
  Source: Geometry Estimate
  Confidence: Low
  Assumptions:
    - First-order Helmholtz estimate
    - Body volume supplied by user
    - ...
  Warnings:
    - Not calibrated prediction
    - ...
```

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| Provenance once per card | All residuals share same AcousticState |
| Only when residuals available | No provenance to show if no residuals |
| First 3 assumptions/warnings | Keep display compact |
| Reads explicit fields | Does not parse assumption strings |

### Important

Residual annotations explain where the estimate came from. They do not calibrate, correct, fit, or validate the model.

### Verification

| Check | Result |
|-------|--------|
| Build | PASS (31.71s) |
| Provenance displays when residuals available | Pending browser verification |
| Provenance hidden when no residuals | Pending browser verification |
| Method/source/confidence display correctly | Pending browser verification |
| Assumptions/warnings display | Pending browser verification |

---

## Dev Order 30 — Residual Interpretation Helper

**Status:** Complete  
**Date:** 2026-05-11

Provides qualitative residual magnitude labels for available residuals. Interpretive guidance only — does NOT calibrate, correct, or validate.

### New Files

| File | Purpose |
|------|---------|
| `packages/client/src/types/residualInterpretation.ts` | `ResidualInterpretationLevel`, `ResidualInterpretationItem`, `ResidualInterpretationSummary` types |
| `packages/client/src/utils/acoustics/residualInterpretation.ts` | `interpretResidualPreview()`, helper functions |
| `packages/client/src/components/shared/acoustics/ResidualInterpretationCard.vue` | Interpretation display component |

### Modified Files

| File | Change |
|------|--------|
| `packages/client/src/components/shared/acoustics/index.ts` | Added ResidualInterpretationCard export |
| `packages/client/src/utils/acoustics/index.ts` | Added residualInterpretation export |
| `packages/client/src/components/toolbox/acoustics/ApertureComparisonPanel.vue` | Added interpretation section after residuals |

### Interpretation Levels

| Level | Threshold | Gate Color |
|-------|-----------|------------|
| `insufficient_data` | No residual | yellow |
| `small` | 0–5% | green |
| `moderate` | >5–15% | yellow |
| `large` | >15% | red |

### Threshold Note

Thresholds are provisional UI guidance, not validated acoustic standards.

### Display Content

Per-item:
- Level badge
- Residual value and percent
- Message explaining interpretation
- Caution text for context

Per-card:
- Overall level (worst wins)
- Notes about provisional thresholds
- Notice: "Residual interpretation is qualitative guidance only"

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| Absolute percent | Negative residuals interpreted by magnitude |
| Worst wins | Overall level reflects most concerning residual |
| No pass/fail | Interpretation is guidance, not acceptance criteria |
| Provisional thresholds | Clear that values are not calibrated standards |

### Important

Residual interpretation is qualitative guidance only. It does not calibrate, correct, fit, or validate the acoustic model.

### Verification

| Check | Result |
|-------|--------|
| Build | PASS (30.04s) |
| Interpretation cards render | Pending browser verification |
| Level badges display correctly | Pending browser verification |
| Small/moderate/large thresholds work | Pending browser verification |
| Caution text displays | Pending browser verification |

---

## Dev Order 31 — Residual Consistency Trend Indicators

**Status:** Complete  
**Date:** 2026-05-11

Summarizes whether available residuals consistently indicate estimates are high, low, mixed, or insufficient. Observational only — does NOT calibrate, correct, or recommend changes.

### New Files

| File | Purpose |
|------|---------|
| `packages/client/src/types/residualTrend.ts` | `ResidualTrendDirection`, `ResidualTrendSummary` types |
| `packages/client/src/utils/acoustics/residualTrend.ts` | `summarizeResidualTrend()`, `getTrendDirectionLabel()` |
| `packages/client/src/components/shared/acoustics/ResidualTrendCard.vue` | Trend display component |

### Modified Files

| File | Change |
|------|--------|
| `packages/client/src/components/shared/acoustics/index.ts` | Added ResidualTrendCard export |
| `packages/client/src/utils/acoustics/index.ts` | Added residualTrend export |
| `packages/client/src/components/toolbox/acoustics/ApertureComparisonPanel.vue` | Added trend section after interpretation |

### Trend Directions

| Direction | Condition | Message |
|-----------|-----------|---------|
| `insufficient_data` | No available residuals | No paired residuals available |
| `estimate_low` | All positive residuals | Measurements higher than estimates |
| `estimate_high` | All negative residuals | Measurements lower than estimates |
| `mixed` | Mixed signs or zero-only | Residual directions mixed |

### Sign Interpretation

```
residual = measured - estimated
positive residual: measured > estimated → estimate is low
negative residual: measured < estimated → estimate is high
```

### Display Content

- Trend badge (all yellow — not pass/fail)
- Message explaining direction
- Counts: available, positive, negative, zero
- Sign explanation
- Caution: "Trend indicators are observational only and do not recommend corrections"

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| All yellow badges | Trend is not pass/fail |
| No correction recommendations | Observational only |
| Count breakdown | Shows what drove the classification |
| Sign explanation | Helps user understand interpretation |

### Important

Trend indicators are observational only. They do not calibrate, correct, fit, or recommend parameter changes.

### Verification

| Check | Result |
|-------|--------|
| Build | PASS (35.55s) |
| Trend cards render | Pending browser verification |
| Direction badges display | Pending browser verification |
| Counts display correctly | Pending browser verification |
| No correction suggestions | Confirmed |

---

## Dev Order 32 — Residual Stability Classification

**Status:** Complete  
**Date:** 2026-05-11

Classifies whether residual patterns appear insufficient, sparse, stable, or volatile using existing interpretation and trend layers. Qualitative and observational only — does NOT validate, calibrate, or correct.

### New Files

| File | Purpose |
|------|---------|
| `packages/client/src/types/residualStability.ts` | `ResidualStabilityLevel`, `ResidualStabilitySummary` types |
| `packages/client/src/utils/acoustics/residualStability.ts` | `classifyResidualStability()`, helper functions |
| `packages/client/src/components/shared/acoustics/ResidualStabilityCard.vue` | Stability display component |

### Modified Files

| File | Change |
|------|--------|
| `packages/client/src/components/shared/acoustics/index.ts` | Added ResidualStabilityCard export |
| `packages/client/src/utils/acoustics/index.ts` | Added residualStability export |
| `packages/client/src/components/toolbox/acoustics/ApertureComparisonPanel.vue` | Added stability section after trend |

### Stability Levels

| Level | Condition | Gate Color |
|-------|-----------|------------|
| `insufficient` | No residuals available | yellow |
| `sparse` | Only one residual | yellow |
| `stable` | Directionally consistent, no large | green |
| `volatile` | Mixed direction or large residuals | red |

### Classification Logic

```
insufficient: availableResidualCount === 0
sparse: availableResidualCount === 1
volatile: any large residuals OR mixed trend direction
stable: all others (directionally consistent, no large)
```

### Display Content

- Stability badge (green/yellow/red)
- Message explaining classification
- Counts: available, small, moderate, large
- Trend direction reference
- Caution: "Stable does not mean correct"

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| Uses existing layers | Builds on interpretation + trend |
| Stable ≠ correct | Explicit caution prevents overconfidence |
| No statistical claims | Qualitative only |

### Important

Stability classification is qualitative and observational only. It does not validate, calibrate, correct, or recommend parameter changes.

### Verification

| Check | Result |
|-------|--------|
| Build | PASS (35.83s) |
| Stability cards render | Pending browser verification |
| Level badges display | Pending browser verification |
| Stable caution displays | Pending browser verification |
| Counts display correctly | Pending browser verification |

---

## Dev Order 33 — Residual Coherence Summary Layer

**Status:** Complete  
**Date:** 2026-05-11

Synthesizes residual interpretation, trend, and stability into a consolidated observational coherence summary. Descriptive only — does NOT calibrate, validate, fit, or correct the model.

### New Files

| File | Purpose |
|------|---------|
| `packages/client/src/types/residualCoherence.ts` | `ResidualCoherenceLevel`, `ResidualCoherenceSummary` types |
| `packages/client/src/utils/acoustics/residualCoherence.ts` | `summarizeResidualCoherence()`, helper functions |
| `packages/client/src/components/shared/acoustics/ResidualCoherenceCard.vue` | Coherence summary display component |

### Modified Files

| File | Change |
|------|--------|
| `packages/client/src/components/shared/acoustics/index.ts` | Added ResidualCoherenceCard export |
| `packages/client/src/utils/acoustics/index.ts` | Added residualCoherence export |
| `packages/client/src/components/toolbox/acoustics/ApertureComparisonPanel.vue` | Added coherence section after stability |

### Coherence Levels

| Level | Condition | Gate Color |
|-------|-----------|------------|
| `insufficient` | stability.level === 'insufficient' | yellow |
| `sparse` | stability.level === 'sparse' | yellow |
| `coherent` | stable + non-mixed trend + no large residuals | green |
| `mixed` | volatile OR mixed trend OR large residuals | red |

### Classification Logic

```
insufficient: stability.level === 'insufficient'
sparse: stability.level === 'sparse'
mixed: stability.level === 'volatile' OR trend.direction === 'mixed' OR largeResidualCount > 0
coherent: all others (stable, consistent direction, no large)
```

### Display Content

- Coherence badge (green/yellow/red)
- Summary message
- Linked diagnostic metadata (interpretation level, trend direction, stability level)
- Caution: "Coherent does not imply calibrated accuracy"
- Notes explaining observational nature

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| Combines three layers | Single readable diagnostic overview |
| Coherent ≠ correct | Explicit caution prevents validation claims |
| No new acoustic math | Uses existing outputs only |
| Descriptive labels | "Coherent Pattern" vs. "Mixed Pattern" |

### Important

Residual coherence summarizes observational diagnostic layers only. It does not calibrate, validate, or correct the model.

### Verification

| Check | Result |
|-------|--------|
| Build | PASS (36.98s) |
| Coherence cards render | Pending browser verification |
| Level badges display | Pending browser verification |
| Coherent caution displays | Pending browser verification |
| Diagnostic metadata displays | Pending browser verification |

---

## Dev Order 34 — Diagnostic Narrative Summary

**Status:** Complete  
**Date:** 2026-05-11

Generates deterministic human-readable summaries from residual interpretation, trend, stability, and coherence layers. Rule-based templates only — does NOT calibrate, validate, optimize, or predict.

### New Files

| File | Purpose |
|------|---------|
| `packages/client/src/types/diagnosticNarrative.ts` | `DiagnosticNarrativeTone`, `DiagnosticNarrativeSummary` types |
| `packages/client/src/utils/acoustics/diagnosticNarrative.ts` | `generateDiagnosticNarrative()`, helper functions |
| `packages/client/src/components/shared/acoustics/DiagnosticNarrativeCard.vue` | Narrative display component |

### Modified Files

| File | Change |
|------|--------|
| `packages/client/src/components/shared/acoustics/index.ts` | Added DiagnosticNarrativeCard export |
| `packages/client/src/utils/acoustics/index.ts` | Added diagnosticNarrative export |
| `packages/client/src/components/toolbox/acoustics/ApertureComparisonPanel.vue` | Added narrative section after coherence |

### Narrative Tones

| Tone | Condition | Gate Color |
|------|-----------|------------|
| `insufficient` | coherence.level === 'insufficient' | yellow |
| `sparse` | coherence.level === 'sparse' | yellow |
| `coherent` | coherence.level === 'coherent' | green |
| `mixed` | coherence.level === 'mixed' | red |

### Narrative Templates

| Tone | Narrative |
|------|-----------|
| insufficient | "Insufficient paired residual observations are available to summarize diagnostic behavior." |
| sparse | "Residual observations remain sparse under current assumptions..." |
| coherent | "Residual observations appear internally coherent under current assumptions..." |
| mixed | "Residual observations appear mixed or divergent under current assumptions..." |

### Display Content

- Tone badge (green/yellow/red)
- Narrative text block
- Supporting observations list (conditional based on actual state)
- Provenance reminder (always present)
- Caution: "Diagnostic narratives summarize existing observational layers only..."

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| Tone from coherence | Direct mapping, no additional classification |
| Rule-based templates | Deterministic, no AI generation |
| Conditional observations | Only show true conditions for mixed tone |
| Trend-specific additions | Coherent narratives add trend direction context |

### Important

Diagnostic narratives summarize observational diagnostics only. They do not calibrate, validate, optimize, or predict acoustic behavior.

### Verification

| Check | Result |
|-------|--------|
| Build | PASS (32.78s) |
| Narrative cards render | Pending browser verification |
| Tone badges display | Pending browser verification |
| Supporting observations populate | Pending browser verification |
| Provenance reminder always appears | Pending browser verification |

---

## Dev Order 35 — Phase-3B Diagnostic Stack Checkpoint

**Status:** Complete  
**Date:** 2026-05-11

Phase-3B diagnostic stack checkpoint. Verifies the full diagnostic helper stack from first-order estimate helper through diagnostic narrative. No feature changes made.

### Build Status

| Check | Result |
|-------|--------|
| Build | PASS (27.52s) |
| Typecheck | FAIL — pre-existing unrelated headstock errors |
| Browser verification | PASS (manual) |

**Note:** Typecheck failure is unrelated to Dev Orders 27–34 and originates in the headstock module. The diagnostic stack code compiles and builds successfully.

### Verified Layers

| Layer | Dev Order | Status |
|-------|-----------|--------|
| First-order Helmholtz estimate helper | 27 | Implemented |
| Estimate assumption summary | 28 | Implemented |
| Residual preview | 23 | Implemented |
| Residual provenance | 29 | Implemented |
| Residual interpretation | 30 | Implemented |
| Residual trend | 31 | Implemented |
| Residual stability | 32 | Implemented |
| Residual coherence | 33 | Implemented |
| Diagnostic narrative | 34 | Implemented |
| Calibration readiness | 22 | Implemented |

### Browser Verification Route

```
/art-studio/aperture → Comparison tab
```

Spot-check tabs:
- Standard tab
- Spiral tab
- Target Matching tab

### Browser Verification Scenarios

#### Scenario A — Empty State

| Check | Expected | Result |
|-------|----------|--------|
| Acoustic State cards show no calibrated estimates | No fake values | PASS |
| Estimate summaries show empty state | Empty | PASS |
| Measured Response cards show no measured data | Empty | PASS |
| Pairing status shows no data | No data | PASS |
| Residual preview shows unavailable | Unavailable | PASS |
| Interpretation shows insufficient data | Insufficient | PASS |
| Trend shows insufficient data | Insufficient | PASS |
| Stability shows insufficient | Insufficient | PASS |
| Coherence shows insufficient | Insufficient | PASS |
| Narrative shows insufficient | Insufficient | PASS |
| Readiness is not green | Not green | PASS |

#### Scenario B — Estimate Only

| Check | Expected | Result |
|-------|----------|--------|
| Estimate appears in AcousticState | Visible | PASS |
| Source/provenance displays | Visible | PASS |
| Confidence is low | Low | PASS |
| Estimate assumption summary populates | Populated | PASS |
| Pairing status shows estimate only | Estimate only | PASS |
| Residual preview remains unavailable | Unavailable | PASS |
| Narrative does not imply calibration | No calibration language | PASS |

#### Scenario C — Measurement Only

| Check | Expected | Result |
|-------|----------|--------|
| Measurement appears | Visible | PASS |
| Source becomes manual entry | Manual | PASS |
| Pairing status shows measurement only | Measurement only | PASS |
| Residual preview remains unavailable | Unavailable | PASS |
| Narrative does not imply calibration | No calibration language | PASS |

#### Scenario D — Paired Helmholtz Residual

| Check | Expected | Result |
|-------|----------|--------|
| Pairing status becomes paired / residual ready | Paired | PASS |
| Residual preview appears | Visible | PASS |
| Residual provenance appears | Visible | PASS |
| Interpretation classifies small/moderate/large | Classified | PASS |
| Trend classifies direction | Classified | PASS |
| Stability handles sparse state | Sparse | PASS |
| Coherence handles sparse state | Sparse | PASS |
| Narrative handles sparse state | Sparse narrative | PASS |
| Readiness updates | Updated | PASS |

#### Scenario E — Multi-Metric Residual Pattern

| Check | Expected | Result |
|-------|----------|--------|
| Two residuals appear | Two visible | PASS |
| Trend counts update | Updated | PASS |
| Stability moves beyond sparse | Stable or volatile | PASS |
| Coherence updates | Coherent or mixed | PASS |
| Narrative updates | Updated | PASS |
| No correction recommendation appears | No corrections | PASS |

#### Scenario F — Candidate Side

| Check | Expected | Result |
|-------|----------|--------|
| Candidate stack behaves independently | Independent | PASS |
| Reference state does not mutate | Unchanged | PASS |
| Candidate narrative updates independently | Independent | PASS |

### Language Audit

**Disallowed language** (must not appear):
- calibrated prediction
- validated model
- corrected estimate
- recommended correction
- optimize aperture
- prediction accuracy confirmed
- model fit complete

**Allowed language** (may appear):
- first-order estimate
- manual estimate
- observational
- provisional
- not calibrated
- not prediction-grade
- under current assumptions

| Audit | Result |
|-------|--------|
| Disallowed language check | PASS |
| Allowed language present | PASS |

### Important

All diagnostics remain observational. No calibration, correction, optimization, or validated prediction is implemented.

### Recommended Next Phase Candidates

- Report/export summary
- Diagnostic session snapshot
- Measurement import scaffold
- Calibration helper design

No selection made. Phase-3C scope TBD.

---

## Dev Order 36 — Diagnostic Session Snapshot Scaffold

**Status:** Complete  
**Date:** 2026-05-11

Creates a structured observational diagnostic snapshot scaffold for future export workflows. Captures current diagnostic state without persistence or prediction.

### New Files

| File | Purpose |
|------|---------|
| `packages/client/src/types/diagnosticSnapshot.ts` | `DiagnosticSnapshot`, `DiagnosticSnapshotSection` types |
| `packages/client/src/utils/acoustics/diagnosticSnapshot.ts` | `createDiagnosticSnapshot()`, helper functions |
| `packages/client/src/components/shared/acoustics/DiagnosticSnapshotCard.vue` | Snapshot display component |

### Modified Files

| File | Change |
|------|--------|
| `packages/client/src/components/shared/acoustics/index.ts` | Added DiagnosticSnapshotCard export |
| `packages/client/src/utils/acoustics/index.ts` | Added diagnosticSnapshot export |
| `packages/client/src/components/toolbox/acoustics/ApertureComparisonPanel.vue` | Added snapshot card after narrative |

### Snapshot Contents

| Section | Source |
|---------|--------|
| Reference Diagnostic Narrative | referenceDiagnosticNarrative |
| Candidate Diagnostic Narrative | candidateDiagnosticNarrative |
| Reference Residual Coherence | referenceResidualCoherence |
| Candidate Residual Coherence | candidateResidualCoherence |
| Calibration Readiness | calibrationReadiness |

### Display Content

- Timestamp (ISO format, localized display)
- Available section count
- Narrative summary (combined reference/candidate tones)
- Section summaries with availability status
- Provenance reminder
- Observational-only notice

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| Single snapshot card | Consolidates both sides |
| No export button yet | Scaffold only, export in future order |
| observationalOnly: true | Enforces type-level constraint |
| Section availability tracking | Supports sparse/incomplete states |

### Important

Snapshots preserve observational state only. They do not persist, calibrate, validate, or predict acoustic behavior.

### Verification

| Check | Result |
|-------|--------|
| Build | PASS (32.55s) |
| Snapshot card renders | PASS |
| Timestamp appears | PASS |
| Sections populate correctly | PASS |
| Observational notice appears | PASS |

---

## Dev Order 37 — Diagnostic Snapshot Export Preparation

**Status:** Complete  
**Date:** 2026-05-11

Prepares diagnostic snapshots for future export/report workflows by adding schema versioning, export readiness metadata, and JSON-safe normalization. Does NOT implement export, download, or persistence.

### Modified Files

| File | Change |
|------|--------|
| `packages/client/src/types/diagnosticSnapshot.ts` | Added schemaVersion, kind, exportReady, exportWarnings, DiagnosticSnapshotExportMetadata |
| `packages/client/src/utils/acoustics/diagnosticSnapshot.ts` | Added normalizeDiagnosticSnapshotForExport(), createDiagnosticSnapshotExportMetadata() |
| `packages/client/src/components/shared/acoustics/DiagnosticSnapshotCard.vue` | Display schema version, kind, export readiness, warnings |
| `packages/client/src/components/toolbox/acoustics/ApertureComparisonPanel.vue` | Wrapped snapshot creation with normalization |

### Schema Fields Added

| Field | Value |
|-------|-------|
| `schemaVersion` | 'diagnostic-snapshot.v1' |
| `kind` | 'aperture-diagnostic-snapshot' |
| `exportReady` | boolean |
| `exportWarnings` | string[] |

### Export Readiness Rules

| Condition | exportReady |
|-----------|-------------|
| All required fields present | true |
| Missing schemaVersion/kind/id/createdAtIso | false |
| observationalOnly !== true | false |

### Export Warnings

- Unavailable sections count
- "Snapshot is observational only"
- "No persistence/export has been performed"

### Display Updates

- Schema version display
- Kind display
- Export readiness indicator (green/red)
- Export warnings list
- "Snapshot is prepared for future export but no file has been generated"

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| No download button | Export preparation only, not export |
| Deterministic output | Same input produces same structure (except timestamp) |
| JSON-safe removal | Strips undefined values for serialization |
| Warnings always present | Communicates observational status |

### Important

This does not implement export, download, persistence, or report generation. Schema preparation only.

### Verification

| Check | Result |
|-------|--------|
| Build | PASS (39.61s) |
| Schema version appears | PASS |
| Kind appears | PASS |
| Export readiness appears | PASS |
| Export warnings appear | PASS |
| Download button added (Dev Order 38) | PASS |

---

## Dev Order 38 — Diagnostic Snapshot JSON Export

**Status:** Complete  
**Date:** 2026-05-11

Enables client-side JSON export of normalized diagnostic snapshots. First actual export action in the snapshot workflow. Does NOT persist to backend, generate reports, or import sessions.

### New Files

| File | Purpose |
|------|---------|
| `packages/client/src/utils/acoustics/diagnosticSnapshotExport.ts` | Export utilities: canExportDiagnosticSnapshot(), createDiagnosticSnapshotJsonExport(), downloadDiagnosticSnapshotJson() |

### Modified Files

| File | Change |
|------|--------|
| `packages/client/src/types/diagnosticSnapshot.ts` | Added DiagnosticSnapshotExportStatus, DiagnosticSnapshotJsonExport |
| `packages/client/src/utils/acoustics/index.ts` | Added diagnosticSnapshotExport export |
| `packages/client/src/components/shared/acoustics/DiagnosticSnapshotCard.vue` | Added Download JSON Snapshot button |

### Export Payload Structure

```json
{
  "exportMetadata": {
    "schemaVersion": "diagnostic-snapshot.v1",
    "kind": "aperture-diagnostic-snapshot",
    "generatedBy": "aperture-workspace",
    "exportPreparedAtIso": "...",
    "exportStatus": "exported_json"
  },
  "snapshot": { ... }
}
```

### Export Status Values

| Status | Meaning |
|--------|---------|
| `prepared_not_exported` | Schema ready, no download performed |
| `exported_json` | JSON file has been downloaded |

### UI Updates

- "Download JSON Snapshot" button
- Disabled when `exportReady !== true`
- Shows "Snapshot is not export-ready." when disabled
- Export notice: "JSON export preserves observational diagnostic state only..."

### Filename Format

```
aperture-diagnostic-snapshot-YYYYMMDD-HHmmss.json
```

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| Client-side only | No backend endpoint required |
| Blob download | Standard browser download behavior |
| Export guard | Prevents download of invalid snapshots |
| Observational notice | Clarifies export does not include predictions |

### Important

JSON export is observational only. It does not persist to backend, generate reports, import sessions, or export calibrated predictions.

### Verification

| Check | Result |
|-------|--------|
| Build | PASS (48.32s) |
| Download button appears | PASS |
| Button disabled when not ready | PASS |
| JSON file downloads | PASS |
| JSON includes exportMetadata | PASS |
| JSON includes snapshot | PASS |
| No backend calls | PASS |

---

## Dev Order 40 — Snapshot Export / Import Roundtrip Verification

**Status:** Complete  
**Date:** 2026-05-13

Verifies that diagnostic snapshots exported as JSON can be re-imported through the validation card and accepted by the schema validator.

### Code Review

Schema compatibility verified between export and import:

| Field | Export | Import Check | Compatible |
|-------|--------|--------------|------------|
| `exportMetadata` | object | must exist | ✓ |
| `snapshot` | object | must exist | ✓ |
| `snapshot.schemaVersion` | `'diagnostic-snapshot.v1'` | exact match | ✓ |
| `snapshot.kind` | `'aperture-diagnostic-snapshot'` | exact match | ✓ |
| `snapshot.observationalOnly` | `true` | === true | ✓ |
| `snapshot.sections` | array | Array.isArray() | ✓ |

Constants match across files:
- `diagnosticSnapshot.ts:20` — `SCHEMA_VERSION = 'diagnostic-snapshot.v1'`
- `diagnosticSnapshotExport.ts:17` — `SCHEMA_VERSION = 'diagnostic-snapshot.v1'`
- `diagnosticSnapshotImport.ts:16` — `EXPECTED_SCHEMA_VERSION = 'diagnostic-snapshot.v1'`

### Browser Verification

| Step | Expected | Result |
|------|----------|--------|
| Navigate to `/art-studio/aperture` | Route loads | ✅ PASS |
| Click "Download JSON Snapshot" | JSON file downloads | ✅ PASS |
| File opens as valid JSON | Well-formed JSON | ✅ PASS |
| JSON contains `exportMetadata` | Present | ✅ PASS |
| JSON contains `snapshot.schemaVersion` | `'diagnostic-snapshot.v1'` | ✅ PASS |
| JSON contains `snapshot.kind` | `'aperture-diagnostic-snapshot'` | ✅ PASS |
| JSON contains `snapshot.observationalOnly` | `true` | ✅ PASS |
| Select exported file in import validation | File selected | ✅ PASS |
| Import validation gate | green or yellow | ✅ PASS |
| Current UI state unchanged after import | No mutation | ✅ PASS |
| No backend calls observed | Network tab clean | ✅ PASS |

### State Mutation Check

Import validation must NOT mutate:
- Geometry comparison state
- Acoustic state cards
- Measured response data
- Residual diagnostics
- Calibration readiness

Result: ✅ All remain unchanged after file selection.

### Build Status

| Check | Result |
|-------|--------|
| `npm run build` | ✅ PASS |
| Schema compatibility | ✅ PASS (code review) |
| Browser roundtrip | ✅ PASS |

### Important

This order verifies roundtrip compatibility only. It does NOT:
- Restore snapshot state
- Persist to backend
- Generate reports
- Implement schema migration

---

## Dev Order 45 — Snapshot Exchange Visual State Hierarchy

**Status:** Complete  
**Date:** 2026-05-14

Improves visual hierarchy and layout organization for Snapshot Exchange while preserving all existing snapshot/export/import behavior.

### Modified Files

| File | Change |
|------|--------|
| `packages/client/src/components/shared/acoustics/DiagnosticSnapshotCard.vue` | Added accent border-left, larger heading, stronger spacing (primary emphasis) |
| `packages/client/src/components/shared/acoustics/DiagnosticSnapshotExportMetadataCard.vue` | Smaller heading, compact spacing, muted border (secondary emphasis) |
| `packages/client/src/components/shared/acoustics/DiagnosticSnapshotImportCard.vue` | Smaller heading, compact spacing, muted border (utility emphasis) |
| `packages/client/src/components/shared/acoustics/SnapshotExchangeSection.vue` | Increased card gap for visual breathing room |

### Visual Hierarchy

| Card | Role | Visual Treatment |
|------|------|------------------|
| Diagnostic Snapshot | Primary | 3px indigo border-left, 0.9375rem heading, 600 weight, stronger spacing |
| Export Metadata | Secondary | Muted border (#30363d), 0.8125rem heading, compact spacing |
| Import Validation | Utility | Muted border (#30363d), 0.8125rem heading, compact spacing |

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| Accent border-left for primary | Clear visual anchor without background change |
| Muted borders for secondary | Subtle de-emphasis without opacity reduction |
| Compact spacing for utility | Denser layout signals supporting role |
| Same base background | Maintains cohesion, avoids disabled appearance |

### Important

This order changes presentation only. No snapshot semantics, export behavior, import validation behavior, restore logic, or persistence behavior changed.

### Build Status

| Check | Result |
|-------|--------|
| `npm run build` | ✅ PASS (30.79s) |
| Component bundle | `ApertureComparisonPanel-BDw45SIK.js 98.69 kB` |

### Browser Verification

| Step | Expected | Result |
|------|----------|--------|
| Navigate to `/art-studio/aperture` | Route loads | ✅ PASS |
| Snapshot card has indigo border-left | Primary emphasis | ✅ PASS |
| Snapshot heading larger than others | Visual hierarchy | ✅ PASS |
| Metadata card has muted border | Secondary emphasis | ✅ PASS |
| Import card has muted border | Utility emphasis | ✅ PASS |
| Spacing between cards consistent | Visual rhythm | ✅ PASS |
| JSON export still works | Behavior preserved | ✅ PASS |
| Import validation still works | Behavior preserved | ✅ PASS |
| No console errors | Clean console | ✅ PASS |

---

## Dev Order 44 — Snapshot Exchange Empty-State Refinement

**Status:** Complete  
**Date:** 2026-05-14

Improves empty-state and sparse-state messaging inside Snapshot Exchange without changing export/import behavior.

### Modified Files

| File | Change |
|------|--------|
| `packages/client/src/components/shared/acoustics/SnapshotExchangeSection.vue` | Updated description with two-paragraph layout, added boundary notice |
| `packages/client/src/components/shared/acoustics/DiagnosticSnapshotCard.vue` | Added sparse-state detection, "Minimal observational snapshot" message, changed "Unavailable" to "Pending" |
| `packages/client/src/components/shared/acoustics/DiagnosticSnapshotImportCard.vue` | Added empty-state guidance paragraph, softened status messages |
| `packages/client/src/utils/acoustics/diagnosticSnapshot.ts` | Updated warning messages to be informational |

### UX Changes

| Area | Before | After |
|------|--------|-------|
| Section description | Single paragraph | Two paragraphs (capability + boundary) |
| Sparse snapshot | No indication | "Minimal observational snapshot available" message |
| Section status | "Unavailable" | "Pending" |
| Import empty state | No guidance | "Select a diagnostic snapshot JSON file..." |
| Import valid state | "...but restore is not implemented" | "Snapshot schema is valid for diagnostic review" |
| Warnings | "Snapshot has X unavailable section(s)" | "Some diagnostic sections are currently unavailable." |

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| "Pending" vs "Unavailable" | Less alarming, implies sections may become available |
| Two-paragraph section copy | Separates capability description from architectural boundary |
| Sparse detection threshold | < 50% available triggers sparse notice |
| Informational warnings | Sparse snapshots are valid, not errors |

### Important

Sparse observational snapshots remain valid and exportable. This order changes UX copy only. It does NOT:
- Change snapshot schema
- Change export behavior
- Change import validation logic
- Add restore functionality
- Add persistence/backend calls

### Build Status

| Check | Result |
|-------|--------|
| `npm run build` | ✅ PASS (38.07s) |
| Component bundle | `ApertureComparisonPanel-DmFTaZS7.js 98.69 kB` |

### Browser Verification

| Step | Expected | Result |
|------|----------|--------|
| Navigate to `/art-studio/aperture` | Route loads | ✅ PASS |
| Section shows two-paragraph description | Capability + boundary | ✅ PASS |
| Sparse snapshot shows informational notice | Non-alarming message | ✅ PASS |
| Sections show "Pending" not "Unavailable" | Softer language | ✅ PASS |
| Import card shows guidance before selection | Instructional text | ✅ PASS |
| Valid import shows "schema is valid" | No restore language | ✅ PASS |
| Export warnings are informational | No failure language | ✅ PASS |
| JSON export still works | File downloads | ✅ PASS |
| Import validation still works | Green/yellow gate | ✅ PASS |
| No console errors | Clean console | ✅ PASS |

---

## Dev Order 43 — Snapshot Exchange Warning Display Cleanup

**Status:** Complete  
**Date:** 2026-05-13

Removes duplicate export-warning display inside the Snapshot Exchange section while preserving warning visibility.

### Modified Files

| File | Change |
|------|--------|
| `packages/client/src/components/shared/acoustics/DiagnosticSnapshotCard.vue` | Removed Export Warnings template and CSS |
| `packages/client/src/components/shared/acoustics/DiagnosticSnapshotExportMetadataCard.vue` | Renamed label from "Warnings" to "Export Warnings" |

### Warning Ownership

| Component | Before | After |
|-----------|--------|-------|
| DiagnosticSnapshotCard | Displayed export warnings | No warnings displayed |
| DiagnosticSnapshotExportMetadataCard | Displayed warnings | Sole owner of "Export Warnings" |

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| Export metadata owns warnings | Warnings describe export-prepared state, natural fit |
| Label renamed to "Export Warnings" | Clear ownership, matches removed label |
| No semantic behavior change | Only presentation changed |

### Important

This order changes presentation only. It does NOT:
- Change snapshot schema
- Change export behavior
- Change import validation
- Add restore functionality
- Add persistence/backend calls

### Build Status

| Check | Result |
|-------|--------|
| `npm run build` | ✅ PASS (44.85s) |
| Component bundle | `ApertureComparisonPanel-7K7Zmr88.js 97.86 kB` |

### Browser Verification

| Step | Expected | Result |
|------|----------|--------|
| Navigate to `/art-studio/aperture` | Route loads | Pending |
| Snapshot Exchange section renders | Section visible | Pending |
| Snapshot card renders without warnings | No "Export Warnings" block | Pending |
| Export Metadata card shows "Export Warnings" | Label visible with warnings | Pending |
| Warnings appear only once | Single location | Pending |
| JSON download still works | File downloads | Pending |
| Exported JSON validates on import | Green/yellow gate | Pending |
| No console errors | Clean console | Pending |

---

## Dev Order 42 — Snapshot Export Section Consolidation

**Status:** Complete  
**Date:** 2026-05-13

Groups Diagnostic Snapshot, Export Metadata, and Import Validation into a single Snapshot Exchange section. Layout consolidation only — no behavior changes.

### New Files

| File | Purpose |
|------|---------|
| `packages/client/src/components/shared/acoustics/SnapshotExchangeSection.vue` | Consolidated snapshot exchange container |

### Modified Files

| File | Change |
|------|--------|
| `packages/client/src/components/shared/acoustics/index.ts` | Added SnapshotExchangeSection export |
| `packages/client/src/components/toolbox/acoustics/ApertureComparisonPanel.vue` | Replaced individual cards with SnapshotExchangeSection |

### Section Structure

```text
Snapshot Exchange
├── DiagnosticSnapshotCard (snapshot summary + JSON export button)
├── DiagnosticSnapshotExportMetadataCard (export metadata)
└── DiagnosticSnapshotImportCard (import validation)
```

### Section Copy

- Heading: "Snapshot Exchange"
- Description: "Export and validate diagnostic snapshots locally. Snapshots preserve observational diagnostic state only and do not restore, persist, upload, or calibrate data."

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| Visible container card | Creates clear visual grouping for snapshot workflow |
| No emit forwarding | Consolidation only — no parent behavior needs validation result yet |
| Warnings duplication preserved | Both snapshot card and metadata card show warnings; avoids behavior changes |

### Important

This order changes layout only. It does NOT:
- Add restore behavior
- Add persistence/backend calls
- Add new export formats
- Forward import validation emits
- Consolidate warning display logic

### Build Status

| Check | Result |
|-------|--------|
| `npm run build` | ✅ PASS (1m 38s) |
| Component bundle | `ApertureComparisonPanel-dBrXEcMP.js 98.31 kB` |

### Browser Verification

| Step | Expected | Result |
|------|----------|--------|
| Navigate to `/art-studio/aperture` | Route loads | ✅ PASS |
| Comparison tab shows Snapshot Exchange section | Section with border/background renders | ✅ PASS |
| Section heading shows "Snapshot Exchange" | Heading visible | ✅ PASS |
| Section description present | Non-persistent/non-restore copy | ✅ PASS |
| DiagnosticSnapshotCard inside section | Card renders | ✅ PASS |
| Export Metadata card inside section | Card renders | ✅ PASS |
| Import Validation card inside section | Card renders | ✅ PASS |
| JSON download button works | File downloads | ✅ PASS |
| Exported JSON validates on import | Green/yellow gate | ✅ PASS |
| No console errors | Clean console | ✅ PASS |

---

## Dev Order 41 — Snapshot Export Metadata Review Card

**Status:** Complete  
**Date:** 2026-05-13

Displays diagnostic snapshot export package metadata without tracking download events or persistence state. Purely observational — shows what the export metadata structure currently IS.

### New Files

| File | Purpose |
|------|---------|
| `packages/client/src/components/shared/acoustics/DiagnosticSnapshotExportMetadataCard.vue` | Export metadata display component |

### Modified Files

| File | Change |
|------|--------|
| `packages/client/src/components/shared/acoustics/index.ts` | Added DiagnosticSnapshotExportMetadataCard export |
| `packages/client/src/components/toolbox/acoustics/ApertureComparisonPanel.vue` | Added import, computed property, and card placement |

### Metadata Fields Displayed

| Field | Source | Display |
|-------|--------|---------|
| Schema Version | `metadata.schemaVersion` | `diagnostic-snapshot.v1` |
| Kind | `metadata.kind` | `aperture-diagnostic-snapshot` |
| Generated By | `metadata.generatedBy` | `aperture-workspace` |
| Export Status | `metadata.exportStatus` | Formatted as "Prepared (not exported)" |
| Prepared At | `metadata.exportPreparedAtIso` | Localized timestamp |
| Warnings | `snapshot.exportWarnings` | List from snapshot |

### Implementation Details

| Aspect | Implementation |
|--------|----------------|
| Metadata source | `createDiagnosticSnapshotExportMetadata()` |
| Status value | Always `'prepared_not_exported'` |
| Event tracking | None — does not track download events |
| Persistence | None — does not indicate actual export occurred |
| State mutation | None — purely observational |

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| No download event tracking | Keeps implementation observational, non-stateful |
| No export lifecycle state | Card shows current metadata structure, not history |
| Warnings from snapshot | Uses existing `exportWarnings` from snapshot object |
| Required notice | "Export metadata describes the snapshot package only. It does not indicate persistence, restore, or calibration." |

### Important

This card displays what the export package metadata structure currently IS. It does NOT:
- Track whether a download actually occurred
- Persist export history
- Indicate actual export completion
- Mutate application state

### Build Status

| Check | Result |
|-------|--------|
| `npm run build` | ✅ PASS (54.24s) |
| Component bundle | `ApertureComparisonPanel-MDL4Q5ve.js 97.50 kB` |

### Browser Verification

| Step | Expected | Result |
|------|----------|--------|
| Navigate to `/art-studio/aperture` | Route loads | ✅ PASS |
| Comparison tab shows Export Metadata card | Card renders | ✅ PASS |
| Card shows Schema Version | `diagnostic-snapshot.v1` | ✅ PASS |
| Card shows Kind | `aperture-diagnostic-snapshot` | ✅ PASS |
| Card shows Generated By | `aperture-workspace` | ✅ PASS |
| Card shows Export Status | "Prepared (not exported)" | ✅ PASS |
| Card shows Prepared At timestamp | Valid localized date | ✅ PASS |
| Card shows Warnings section | Lists export warnings | ✅ PASS |
| Card shows required notice | Notice text present | ✅ PASS |

---

## Dev Order 39 — Diagnostic Snapshot Import Validation Scaffold

**Status:** Complete  
**Date:** 2026-05-12

Validates exported diagnostic snapshot JSON files without restoring them into application state. First import validation scaffold — does NOT restore sessions, mutate state, or perform calibration.

### New Files

| File | Purpose |
|------|---------|
| `packages/client/src/types/diagnosticSnapshotImport.ts` | `DiagnosticSnapshotImportGate`, `DiagnosticSnapshotImportDiagnostic`, `DiagnosticSnapshotImportValidation` types |
| `packages/client/src/utils/acoustics/diagnosticSnapshotImport.ts` | `validateDiagnosticSnapshotJsonImport()`, `getImportGateColor()`, `getImportGateLabel()` |
| `packages/client/src/components/shared/acoustics/DiagnosticSnapshotImportCard.vue` | File input with validation display |

### Modified Files

| File | Change |
|------|--------|
| `packages/client/src/components/shared/acoustics/index.ts` | Added DiagnosticSnapshotImportCard export |
| `packages/client/src/utils/acoustics/index.ts` | Added diagnosticSnapshotImport export |
| `packages/client/src/components/toolbox/acoustics/ApertureComparisonPanel.vue` | Added import card after snapshot card |

### Validation Gates

| Gate | Conditions |
|------|------------|
| RED | Missing payload/object, missing exportMetadata, missing snapshot, wrong schemaVersion, wrong kind, observationalOnly !== true, sections not array |
| YELLOW | Missing exportStatus, zero sections, has export warnings, missing/invalid timestamp |
| GREEN | All required fields valid, observationalOnly: true, correct schema/kind |

### Validation Result Contract

```typescript
interface DiagnosticSnapshotImportValidation {
  overallGate: DiagnosticSnapshotImportGate
  valid: boolean
  schemaVersion?: string
  kind?: string
  sectionCount?: number
  createdAtIso?: string
  diagnostics: DiagnosticSnapshotImportDiagnostic[]
}
```

### UI Features

- File input accepting `.json` files
- Gate badge showing validation status
- Metadata display (schema version, kind, section count, timestamp)
- Status message (valid for review / cannot be used)
- Diagnostics list with gate coloring
- Clear button to reset
- Notice: "Import validation checks exported snapshot structure only. It does not restore or apply snapshot data."

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| Validation only | Does not restore or apply imported data |
| Client-side parsing | No backend required for validation |
| Red/yellow/green gates | Consistent with existing gate system |
| Diagnostic list | Shows what specifically failed/warned |
| No emit/persist | Emits validation result only for potential future use |

### Important

Import validation is structural validation only. It does NOT restore, apply, calibrate, predict, or mutate application state.

### Verification

| Check | Result |
|-------|--------|
| Build | PASS (54.93s) |
| Import card renders | Pending browser verification |
| Invalid JSON shows parse error | Pending browser verification |
| Wrong schema shows red gate | Pending browser verification |
| Valid snapshot shows green gate | Pending browser verification |
| Clear button resets | Pending browser verification |

---

## Revision History

| Date | Change |
|------|--------|
| 2026-05-14 | **Dev Order 45 Snapshot Exchange Visual State Hierarchy complete** |
| 2026-05-14 | **Dev Order 44 Snapshot Exchange Empty-State Refinement complete** |
| 2026-05-13 | **Dev Order 43 Snapshot Exchange Warning Display Cleanup complete** |
| 2026-05-13 | **Dev Order 42 Snapshot Export Section Consolidation complete** |
| 2026-05-13 | **Dev Order 41 Snapshot Export Metadata Review Card complete** |
| 2026-05-13 | **Dev Order 40 Snapshot Export/Import Roundtrip Verification complete** |
| 2026-05-12 | **Dev Order 39 Diagnostic Snapshot Import Validation complete** |
| 2026-05-11 | **Dev Order 38 Diagnostic Snapshot JSON Export complete** |
| 2026-05-11 | **Dev Order 37 Diagnostic Snapshot Export Preparation complete** |
| 2026-05-11 | **Dev Order 36 Diagnostic Session Snapshot Scaffold complete** |
| 2026-05-11 | **Dev Order 35 Phase-3B Diagnostic Stack Checkpoint complete** |
| 2026-05-11 | **Dev Order 34 Diagnostic Narrative Summary complete** |
| 2026-05-11 | **Dev Order 33 Residual Coherence Summary Layer complete** |
| 2026-05-11 | **Dev Order 32 Residual Stability Classification complete** |
| 2026-05-11 | **Dev Order 31 Residual Consistency Trend Indicators complete** |
| 2026-05-11 | **Dev Order 30 Residual Interpretation Helper complete** |
| 2026-05-11 | **Dev Order 29 Estimate vs Measurement Residual Annotation complete** |
| 2026-05-11 | **Dev Order 28 First-Order Estimate Assumption Summary complete** |
| 2026-05-11 | **Dev Order 27 First-Order Helmholtz Estimate Helper complete** |
| 2026-05-11 | **Dev Order 26 Phase-3A Verification Checkpoint complete** |
| 2026-05-11 | **Dev Order 25 Measurement Pairing Status complete** |
| 2026-05-11 | **Dev Order 24 Estimate Attachment Scaffold complete** |
| 2026-05-10 | **Dev Order 23 Calibration Residual Preview complete** |
| 2026-05-10 | **Dev Order 22 Calibration Readiness Layer complete** |
| 2026-05-09 | **Dev Order 21 Measured Response Delta Display complete** |
| 2026-05-09 | **Dev Order 20 Measured Response Manual Attachment Controls complete** |
| 2026-05-09 | **Dev Order 19 Measured Data Attachment Scaffold complete** |
| 2026-05-09 | **Phase-3 Readiness Browser Verification passed** |
| 2026-05-08 | **Dev Order 18 voided as duplicate of Dev Order 17** |
| 2026-05-08 | **Dev Order 17 Target Matching Task Detail Panels complete** |
| 2026-05-08 | **Dev Order 16 Acoustic State Display Extraction complete** |
| 2026-05-07 | **Dev Order 15 Acoustic State Model Foundation complete** |
| 2026-05-07 | **Dev Order 14 Phase-2 checkpoint complete** |
| 2026-05-07 | Dev Order 13 Target Matching UI skeleton + reframe complete |
| 2026-05-07 | Dev Order 12 ApertureComparisonPanel + shared ApertureResultCard complete |
| 2026-05-07 | Dev Order 10 StandardAperturePanel complete |
| 2026-05-07 | Dev Order 9 canonical route clarification complete |
| 2026-05-07 | Dev Order 8 endpoint normalization complete |
| 2026-05-07 | Dev Order 7 containment audit complete |
| 2026-05-06 | Initial architecture status after Dev Orders 1–3 |
