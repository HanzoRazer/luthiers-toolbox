# CU-A1 — SoundholeRosetteShell Consolidation Plan

**Status:** Plan only (not implemented).  
**Purpose:** Single workspace for rosette designer, soundhole, purfling, and binding — same pattern as InlayWorkspaceShell (INLAY-06).

**Target:** `SoundholeRosetteShell.vue` at `/art-studio/soundhole-rosette-workspace` (or equivalent) with 4 tabs: (1) Rosette Designer — RosetteWheelView; (2) Soundhole — SoundholeDesignerView; (3) Purfling — PurflingDesignerView; (4) Binding — BindingDesignerView. Route and Art Studio nav entry. Optionally deprecate or redirect existing per-view routes.

---

## 1. Current State Summary

### 1.1 Views and Routes

| Route | Component | API / state | Purpose |
|-------|-----------|-------------|---------|
| `/art-studio/rosette-designer` | **RosetteWheelView.vue** (~1240 lines) | `useRosetteWheelStore` (Pinia), `@/types/rosetteDesigner` | 5-ring wheel, 19 tiles, symmetry, drag-drop, BOM, MFG checks, .rsd save/load, dual SVG export |
| `/art-studio/soundhole` | **SoundholeDesignerView.vue** (~371 lines) | Local refs only; planned: `/api/art-studio/soundhole/*` | Soundhole shapes (round/oval/f-hole/d-hole), rosette options, templates |
| `/art-studio/purfling` | **PurflingDesignerView.vue** (~343 lines) | Local refs only; planned: `/api/art-studio/purfling/*` | Purfling channels (body-edge, soundhole, custom), strip layers |
| `/art-studio/binding` | **BindingDesignerView.vue** (~371 lines) | Local refs only; planned: `/api/art-studio/binding/*` | Binding channel dimensions, strip stack, presets |

All four have their **own route** today.

### 1.2 Components and Composables

- **RosetteWheelView.vue:** Uses **useRosetteWheelStore** (Pinia) and types from `@/types/rosetteDesigner`. No other shared composables with Soundhole/Purfling/Binding views.
- **SoundholeDesignerView.vue:** Only local `ref()` state; comments reference planned endpoints (templates, rosette-patterns, preview, export-dxf). No store, no shared composable.
- **PurflingDesignerView.vue:** Only local `ref()` state; planned endpoints (patterns, preview, export-dxf). No store, no shared composable.
- **BindingDesignerView.vue:** Only local `ref()` state and one `computed` (totalStackHeight); planned endpoints (presets, materials, preview, export-dxf). No store, no shared composable.

**Other rosette/soundhole/purfling/binding usage in codebase:**  
`useRosetteDesignerState.ts` (toolbox), `RosetteParametersPanel.vue`, `RosetteCanvas.vue`, `ModernPanel.vue`, `PlacementControlsPanel.vue` use `soundholeDiameter` / purfling materials in a **different** flow (e.g. GuitarDesignHub / parametric rosette). They are **not** used by the four views above. No conflict.

### 1.3 Do the Four Views Share Any State Today?

**No.** They are fully independent:

- **RosetteWheelView** uses only `useRosetteWheelStore` and local refs; no import of Soundhole/Purfling/Binding views or their state.
- **SoundholeDesignerView**, **PurflingDesignerView**, and **BindingDesignerView** use only local `ref()`/`computed`; no Pinia store, no shared composable, no cross-import.

So: **no shared state, no shared canvas, no shared coordinate system** between the four views.

---

## 2. Composables: Shared vs Stage-Specific

| Composable / store | Used by today | Proposed scope in unified shell |
|--------------------|----------------|---------------------------------|
| **useRosetteWheelStore** | RosetteWheelView only | **Stage 1 only** (Rosette Designer). Ring defs, tiles, symmetry, BOM, MFG, export. |
| **(none)** | SoundholeDesignerView | **Stage 2 only** — keep local state inside SoundholeDesignerView. |
| **(none)** | PurflingDesignerView | **Stage 3 only** — keep local state inside PurflingDesignerView. |
| **(none)** | BindingDesignerView | **Stage 4 only** — keep local state inside BindingDesignerView. |

**Shared across stages (to introduce):**  
None required. Same as INLAY-06: shell only **orchestrates** which stage is visible; each stage keeps its own state. Optional later: workspace-level “project name” or “last export path” if product needs it.

---

## 3. Is a Shared Canvas Coordinate System Needed?

**No.** Tabs are sufficient.

- **Rosette Designer** has its own wheel SVG and coordinate system (CX, CY, ring radii, segment angles).
- **Soundhole** has its own preview/template UI and (when implemented) backend preview.
- **Purfling** and **Binding** have their own form-driven previews and (when implemented) backend preview/DXF.

A single unified canvas would require backend and product support for combined rosette/soundhole/purfling/binding geometry. For CU-A1, a **tabbed shell** is sufficient; each stage keeps its own preview and coordinates.

---

## 4. Proposed Shell: SoundholeRosetteShell.vue

### 4.1 Structure

- **Single route,** e.g. `/art-studio/soundhole-rosette-workspace` (or `/art-studio/rosette-workspace`).
- **Shell component:** `SoundholeRosetteShell.vue` (same pattern as `InlayWorkspaceShell.vue`):
  - **Stage/tab strip:** Rosette Designer | Soundhole | Purfling | Binding.
  - **Content area:** One of four stage contents (lazy-loaded with `defineAsyncComponent` + `Suspense`).
  - **Optional:** Persist active tab in `sessionStorage` or query (`?stage=soundhole`).

### 4.2 Stage Contents

| Stage | Content source | Composables / state | API |
|-------|----------------|---------------------|-----|
| **1. Rosette Designer** | **RosetteWheelView.vue** | useRosetteWheelStore, existing types | Existing .rsd, SVG export, BOM/MFG (no change) |
| **2. Soundhole** | **SoundholeDesignerView.vue** | Local refs (unchanged) | Planned: `/api/art-studio/soundhole/*` |
| **3. Purfling** | **PurflingDesignerView.vue** | Local refs (unchanged) | Planned: `/api/art-studio/purfling/*` |
| **4. Binding** | **BindingDesignerView.vue** | Local refs (unchanged) | Planned: `/api/art-studio/binding/*` |

No extraction into “Stage” wrappers required; embed the existing views as-is (same as InlayWorkspaceShell embeds InlayPatternView, ArtStudioInlay, HeadstockDesignerView).

### 4.3 Data Flow Between Stages

No mandatory data flow for v1. Each stage is self-contained. Optional later: e.g. “soundhole diameter” from Stage 2 could inform Stage 1 or 3; not in scope for initial shell.

### 4.4 Router and Nav

- Add route for `SoundholeRosetteShell.vue` (e.g. `/art-studio/soundhole-rosette-workspace`).
- Art Studio nav: one entry “Soundhole & Rosette” (or “Rosette Workspace”) → shell.
- Existing routes (`/art-studio/rosette-designer`, `/art-studio/soundhole`, `/art-studio/purfling`, `/art-studio/binding`) can remain and redirect to the shell with `?stage=…`, or be deprecated in nav only (links point to shell; old routes kept for bookmarks until product decision).

---

## 5. Summary Table

| Question | Answer |
|----------|--------|
| Do the four views share state today? | **No.** Completely independent. |
| Which composables are shared? | **None.** RosetteWheelView uses useRosetteWheelStore; the other three use only local state. |
| Which composables are stage-specific? | **Stage 1:** useRosetteWheelStore, rosette types. **Stages 2–4:** local state only. |
| Shared canvas coordinate system? | **Not required.** Tabs sufficient; each stage keeps its own preview/coordinates. |
| Single shell component? | **SoundholeRosetteShell.vue** with four stages: Rosette Designer → Soundhole → Purfling → Binding. |

---

## 6. Implementation Order (when implementing)

1. Add **SoundholeRosetteShell.vue** in `views/art-studio/` with:
   - Stage type: `"rosette" \| "soundhole" \| "purfling" \| "binding"`.
   - Tab strip and `activeStage` ref; `setStage(id)`.
   - Four `defineAsyncComponent` imports for RosetteWheelView, SoundholeDesignerView, PurflingDesignerView, BindingDesignerView.
   - Four `v-show` panels with `<Suspense>` and fallback “Loading…” (mirror InlayWorkspaceShell).
   - Same CSS pattern as InlayWorkspaceShell (shell-header, stage-tabs, stage-tab, stage-content, stage-panel, stage-loading).
2. Add route (e.g. `/art-studio/soundhole-rosette-workspace`) → SoundholeRosetteShell.vue.
3. Update Art Studio nav in AppDashboardView.vue: add “Soundhole & Rosette” (or “Rosette Workspace”) → new route; optionally remove or keep existing per-view links (rosette-designer, soundhole, purfling, binding).
4. Optional: redirect old routes to shell with query param (e.g. `/art-studio/soundhole` → shell with `?stage=soundhole`); or leave old routes as-is and only change nav.
5. Run build and smoke-test all four stages load without errors.

---

## 7. File Locations (reference)

| Item | Path |
|------|------|
| Shell (to create) | `packages/client/src/views/art-studio/SoundholeRosetteShell.vue` |
| Stage 1 | `packages/client/src/views/art-studio/RosetteWheelView.vue` |
| Stage 2 | `packages/client/src/views/art-studio/SoundholeDesignerView.vue` |
| Stage 3 | `packages/client/src/views/art-studio/PurflingDesignerView.vue` |
| Stage 4 | `packages/client/src/views/art-studio/BindingDesignerView.vue` |
| Router | `packages/client/src/router/index.ts` |
| Nav | `packages/client/src/views/AppDashboardView.vue` (Art Studio section) |
