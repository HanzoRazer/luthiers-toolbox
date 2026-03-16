# INLAY-06 — Unified Inlay Workspace Consolidation Plan

**Status:** Plan only (no implementation).  
**Purpose:** Single workspace for pattern library, fretboard placement, headstock placement, and BOM/export.

---

## 1. Current State Summary

### 1.1 Views and Routes

| Route | Component | API base | Purpose |
|-------|-----------|----------|---------|
| `/art-studio/inlay` | **InlayDesignerView.vue** (773 lines) | `/api/art-studio/inlay` | Fretboard inlay: presets, pattern types, fret positions, preview SVG, DXF export |
| `/art-studio/inlay-patterns` | **InlayPatternView.vue** (548 lines) | `/api/art/inlay-patterns` | Marquetry pattern library: generators, params, materials, SVG/DXF export, BOM |
| `/art-studio/headstock` | **HeadstockDesignerView.vue** | `/api/instruments/guitar/headstock-inlay` | Headstock templates, prompt generation (post INLAY-02) |

### 1.2 Components and Composables

- **ArtStudioInlay.vue** (component, not routed): Uses composables `useInlayState`, `useInlayPresets`, `useInlayPreview`, `useInlayFrets`; calls `@/api/art-studio` (getFretPositions, listInlayPresets, getInlayPreset, previewInlay, exportInlayDXF). **Not used by the router** — router points at InlayDesignerView.vue instead.
- **art_studio_inlay/composables:**  
  `useInlayState`, `useInlayFrets`, `useInlayPresets`, `useInlayPreview` — all **fretboard-inlay only**; depend on art-studio inlay API and types.
- **useInlayHistoryStore.ts** (Pinia): Snapshot type is **pattern-library only** (shape, params, materials, bgMaterial, offsets). Used **only by InlayPatternView.vue** for undo/redo.
- **InlayBomPanel.vue**, **InlayMeasurePanel.vue**: Live under `components/art/inlay_patterns/`; used **only by InlayPatternView.vue**.

### 1.3 Do the Two Main Views Share Any State Today?

**No.** They are fully independent:

- **InlayDesignerView.vue** uses only local `ref()` state and direct `fetch()` to `/api/art-studio/inlay`. It does **not** import any of the art_studio_inlay composables or the history store.
- **InlayPatternView.vue** uses `useInlayHistoryStore` and local state; no use of useInlayState/useInlayFrets/useInlayPresets/useInlayPreview.
- **HeadstockDesignerView.vue** is self-contained with its own API client; no shared state with the other two.

So: **no shared state, no shared canvas, no shared coordinate system** between pattern library, fretboard designer, and headstock designer.

---

## 2. Composables: Shared vs Stage-Specific

| Composable / store | Used by today | Proposed scope in unified shell |
|--------------------|----------------|---------------------------------|
| **useInlayState** | ArtStudioInlay.vue only (not routed) | **Stage 2 only** (fretboard placement). Holds patternType, scaleLength, selectedFrets, presets, previewResult, fretData, dxfVersion, etc. |
| **useInlayFrets** | ArtStudioInlay.vue only | **Stage 2 only** — fret selection and fret position API. |
| **useInlayPresets** | ArtStudioInlay.vue only | **Stage 2 only** — art-studio inlay presets. |
| **useInlayPreview** | ArtStudioInlay.vue only | **Stage 2 only** — preview + DXF export for fretboard inlay. |
| **useInlayHistoryStore** | InlayPatternView.vue only | **Stage 1 only** — undo/redo for pattern-library (marquetry) params. Snapshot shape is pattern-specific, not fretboard/headstock. |
| **InlayBomPanel** | InlayPatternView.vue | **Stage 1 + Stage 4** — pattern BOM in Stage 1; optionally aggregated BOM in Stage 4. |
| **InlayMeasurePanel** | InlayPatternView.vue | **Stage 1** (pattern preview measurements). Optionally reuse in Stage 4 for “measure overall” if a shared preview exists. |

**Shared across stages (to introduce):**

- **Workspace-level state (optional):** e.g. “current project name”, “last export path”, or “selected instrument” — only if product needs it; not required for a tab-based shell.
- **No existing composable is shared** between the two current views; the plan does not require making the existing composables shared, only that the shell **orchestrates** which stage uses which composable.

---

## 3. Is a Shared Canvas Coordinate System Needed?

**Recommendation: No for v1. Tabs are sufficient.**

- **Fretboard inlay** uses 12-TET math and backend-generated SVG from `/api/art-studio/inlay`; coordinates are in “fretboard mm” (scale length, nut/body width).
- **Pattern library** uses generator-specific coordinates (e.g. repeat_mm, width_mm, height_mm) and SVG from `/api/art/inlay-patterns`; no common origin with the fretboard.
- **Headstock** uses template/prompt-based flow; no geometric canvas in the same sense.

A single “unified canvas” in one coordinate space would require:

- Backend support for a combined neck + headstock + pattern geometry model,
- Or client-side composition of multiple SVGs with a shared transform/origin.

That is a larger product/backend change. For INLAY-06, a **tabbed (or stepped) shell** keeps:

- **Stage 1:** Pattern library (current InlayPatternView content) — own preview and coordinates.
- **Stage 2:** Fretboard placement (current InlayDesignerView or ArtStudioInlay content) — own preview and coordinates.
- **Stage 3:** Headstock placement (HeadstockDesignerView content) — own UI and prompt output.
- **Stage 4:** BOM and export — aggregate from Stage 1 (and optionally 2/3 if those expose counts/areas).

So: **tabs (or linear stages) are sufficient**; no shared canvas coordinate system is required for the consolidation plan. A shared canvas can be a later enhancement once/if backend supports unified geometry.

---

## 4. Proposed Shell: InlayWorkspaceShell.vue

### 4.1 Structure

- **Single route,** e.g. `/art-studio/inlay-workspace` (or replace `/art-studio/inlay` and redirect inlay-patterns and headstock into the same shell with a default stage).
- **Shell component:** `InlayWorkspaceShell.vue`:
  - **Stage/tab strip:** Pattern Library | Fretboard | Headstock | BOM & Export.
  - **Content area:** One of four stage contents (see below).
  - **Optional:** Simple “project” or “session” state (e.g. persist active tab in query or localStorage).

### 4.2 Stage Contents (no full implementation here)

| Stage | Content source | Composables / panels | API |
|-------|----------------|----------------------|-----|
| **1. Pattern library** | Current **InlayPatternView.vue** content (or extract body into `InlayPatternStage.vue`) | useInlayHistoryStore, InlayMeasurePanel, InlayBomPanel | GET/POST `/api/art/inlay-patterns` |
| **2. Fretboard placement** | Current **InlayDesignerView.vue** or **ArtStudioInlay.vue** content (or extract into `InlayFretboardStage.vue`) | useInlayState, useInlayFrets, useInlayPresets, useInlayPreview (+ FretPositionTable, InlaySummaryPanel, InlayDetailsTable as needed) | `/api/art-studio/inlay` |
| **3. Headstock placement** | Current **HeadstockDesignerView.vue** content (or extract into `InlayHeadstockStage.vue`) | None beyond existing view logic | `/api/instruments/guitar/headstock-inlay` |
| **4. BOM and export** | New lightweight **InlayBomExportStage.vue** | Reuse InlayBomPanel for pattern BOM; optionally show “Export fretboard DXF” / “Export headstock prompt” links or buttons that delegate to Stage 2 / Stage 3 logic or re-call their APIs | Aggregates existing endpoints |

### 4.3 Data Flow Between Stages (optional, for Stage 4)

- **Pattern library (Stage 1):** Already has BOM; Stage 4 can show the same InlayBomPanel and export actions (or link “back to Stage 1 to export”).
- **Fretboard (Stage 2):** Export DXF from Stage 2; Stage 4 can either embed the same export button or show a summary + “Export from Fretboard tab”.
- **Headstock (Stage 3):** Copy prompt / export from Stage 3; Stage 4 can summarize and link to Stage 3.
- No mandatory “single export bundle” in v1 — each stage can keep its own export; Stage 4 is a **dashboard** of what’s available and shortcuts to each export.

### 4.4 Router and Nav

- Add route for `InlayWorkspaceShell.vue` (e.g. `/art-studio/inlay-workspace`).
- Art Studio nav: one entry “Inlay” → shell; optionally deprecate or redirect `/art-studio/inlay`, `/art-studio/inlay-patterns`, `/art-studio/headstock` to the shell with `?stage=…` or default stage.

---

## 5. Summary Table

| Question | Answer |
|----------|--------|
| Do InlayDesignerView and InlayPatternView share state today? | **No.** Completely independent. |
| Which composables are shared? | **None** today. In the plan: **none** shared; each stage uses its own (useInlayHistoryStore for Stage 1; useInlayState/useInlayFrets/useInlayPresets/useInlayPreview for Stage 2). |
| Which composables are stage-specific? | **Stage 1:** useInlayHistoryStore, InlayBomPanel, InlayMeasurePanel. **Stage 2:** useInlayState, useInlayFrets, useInlayPresets, useInlayPreview (and ArtStudioInlay’s table/summary components if used). **Stage 3:** HeadstockDesigner’s existing logic. **Stage 4:** InlayBomPanel (and optional aggregation). |
| Shared canvas coordinate system? | **Not required.** Tabs/stages are sufficient; each stage keeps its own preview and coordinates. |
| Single shell component? | **InlayWorkspaceShell.vue** with four stages: Pattern library → Fretboard → Headstock → BOM & Export. |

---

## 6. Implementation Order (when implementing)

1. Add **InlayWorkspaceShell.vue** with tab/stage UI and placeholder content for each stage.
2. Extract or reuse **Stage 1** from InlayPatternView (pattern library + history + measure + BOM).
3. Extract or reuse **Stage 2** from InlayDesignerView or ArtStudioInlay (fretboard + composables).
4. Embed or reuse **Stage 3** from HeadstockDesignerView.
5. Add **Stage 4** (BOM & export dashboard).
6. Wire router and nav; add redirects from old routes if desired.
7. Run tests for inlay and headstock; adjust any that assume old routes.
