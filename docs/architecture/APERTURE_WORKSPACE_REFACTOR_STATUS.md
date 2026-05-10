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
| Edit form renders | Pending browser verification |
| Save/cancel flow | Pending browser verification |
| Values persist in session | Pending browser verification |
| No backend changes | Confirmed |
| No calibration math | Confirmed |

---

## Revision History

| Date | Change |
|------|--------|
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
