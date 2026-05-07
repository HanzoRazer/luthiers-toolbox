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

## Revision History

| Date | Change |
|------|--------|
| 2026-05-07 | Dev Order 9 canonical route clarification complete |
| 2026-05-07 | Dev Order 8 endpoint normalization complete |
| 2026-05-07 | Dev Order 7 containment audit complete |
| 2026-05-06 | Initial architecture status after Dev Orders 1–3 |
