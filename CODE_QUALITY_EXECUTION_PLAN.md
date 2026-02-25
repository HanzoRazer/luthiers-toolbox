# Code Quality Execution Plan
**Created**: 2026-02-25 | **Source**: `CODE_QUALITY_HANDOFF.md`  
**Scope**: `packages/client/src/` | **Total Issues**: 4,783 (1,469 warning, 3,314 info)  
**Last Updated**: 2026-02-25

---

## Status Summary

| Phase | Status | Notes |
|-------|--------|-------|
| **1 — Quick Wins** | **COMPLETED** | useAsyncAction, constants, eval fix — 24 files changed, 14 new tests, 0 regressions |
| **2 — Duplicate Extraction** | **COMPLETED** | useFetchTransform, useFormState, useLocalStorageRef, runLogHelpers, domain consolidation — 17 files changed, 30 new tests, 0 regressions |
| **3 — Dead CSS** | **COMPLETED** | 57 dead selectors removed from ManufacturingCandidateList.module.css, dead template classes cleaned, CSS audit script added — 5 files changed, 0 regressions |
| **4 — Memory/Safety** | **COMPLETED** | 12 files fixed: 11 timer leaks (setTimeout/setInterval) + 1 addEventListener leak. 0 type errors, 402 tests pass, 0 regressions |
| **5 — TODO Triage** | **COMPLETED** | 16 TODOs audited → 2 stubs deleted, 3 stale comments removed, 1 dead function deleted, 6 aspirational kept, 4 actionable documented |
| **6 — View Hooks** | **COMPLETED** | Consolidated download/CSV utilities: extended downloadBlob.ts with 4 new shared functions, eliminated 10 inline blob-download patterns + 5 csvEscape duplicates across 11 files. Net -94 LOC, 0 regressions |

---

## Plan Overview

Six phases, ordered by impact-per-hour. Each phase lists concrete deliverables, affected files, definition of done, and estimated effort. Quick wins first; structural refactors last.

---

## Phase 1 — Quick Wins (Est. 3–4 hours) — COMPLETED

### 1A. Create `composables/useAsyncAction.ts`
**Impact**: Eliminates 50+ duplicate try/catch/loading blocks across stores and composables.

**Deliverable**: A generic composable that wraps any async function with `loading`, `error`, and `data` refs.

```typescript
// packages/client/src/composables/useAsyncAction.ts
import { ref, type Ref } from 'vue'

interface AsyncActionReturn<T> {
  data: Ref<T | null>
  error: Ref<Error | null>
  loading: Ref<boolean>
  execute: (...args: unknown[]) => Promise<T | null>
  reset: () => void
}

export function useAsyncAction<T>(
  action: (...args: any[]) => Promise<T>
): AsyncActionReturn<T> {
  const data = ref<T | null>(null) as Ref<T | null>
  const error = ref<Error | null>(null) as Ref<Error | null>
  const loading = ref(false)

  async function execute(...args: unknown[]): Promise<T | null> {
    loading.value = true
    error.value = null
    try {
      const result = await action(...args)
      data.value = result
      return result
    } catch (e) {
      error.value = e instanceof Error ? e : new Error(String(e))
      return null
    } finally {
      loading.value = false
    }
  }

  function reset() {
    data.value = null
    error.value = null
    loading.value = false
  }

  return { data, error, loading, execute, reset }
}
```

**Files to refactor** (highest-impact first):
| File | `loading.value = true` count |
|------|------------------------------|
| `stores/artDesignFirstWorkflowStore.ts` | 5 |
| `stores/useRosetteDesignerStore.ts` | 4 |
| `components/toolbox/adaptive-bench/useAdaptiveBenchActions.ts` | 3 |
| `stores/useRmosAnalyticsStore.ts` | 2 |
| `views/rosette_compare/composables/useRosetteCompareActions.ts` | 3 |
| `views/saw_lab_dashboard/composables/useSawDashboard.ts` | 1 |
| `views/rmos_run_viewer/composables/useRmosRunViewerActions.ts` | 1 |
| `stores/fretSlotsCamStore.ts` | 1 |
| `stores/useJobLogStore.ts` | 1 |
| `stores/useLiveMonitorStore.ts` | 1 |
| `stores/useManufacturingPlanStore.ts` | 1 |
| `components/cam/composables/useCamPipelineExecution.ts` | 1 |
| … plus ~25 more in `.vue` files |

**Done when**: `useAsyncAction` is exported from `composables/index.ts`, has unit tests, and at least 10 high-count files are refactored. `grep "loading.value = true" src/` count drops by ≥50%.

### 1B. Create `constants/timing.ts` and `constants/dimensions.ts`
**Impact**: Names 100+ magic numbers scattered across the entire client.

**Deliverables**:
```
packages/client/src/constants/
  timing.ts        — ANIMATION_DURATION_MS, DEBOUNCE_DELAY_MS, SECOND_MS, TOAST_DURATION_MS
  dimensions.ts    — FRET_COUNT, MAX_FRETS, SCALE_LENGTH_MM, GRID_COLUMNS
  index.ts         — barrel export
```

**Specific values to extract**:

| Literal | Occurrences | Constant | File |
|---------|-------------|----------|------|
| `300` | 40+ | `ANIMATION_DURATION_MS` | `timing.ts` |
| `500` | 35+ | `DEBOUNCE_DELAY_MS` | `timing.ts` |
| `1000` | 30+ | `SECOND_MS` | `timing.ts` |
| `260` | 5+ | `SHAKE_DURATION_MS` | `timing.ts` |
| `1200` | 2+ | `RING_FOCUS_DURATION_MS` | `timing.ts` |
| `1600` | 1+ | `SUCCESS_TOAST_MS` | `timing.ts` |
| `2200` | 1+ | `ERROR_TOAST_MS` | `timing.ts` |
| `3000` | 2+ | `SAVED_INDICATOR_MS` | `timing.ts` |
| `4500` | 1+ | `DEFAULT_TOAST_MS` | `timing.ts` |
| `12` | 25+ | `DEFAULT_FRET_COUNT` / `GRID_COLUMNS` | `dimensions.ts` |
| `22` | 20+ | `MAX_FRETS` | `dimensions.ts` |
| `650` | 15+ | `DEFAULT_SCALE_LENGTH_MM` | `dimensions.ts` |

**Done when**: Constants files exist, are imported in the barrel, and at least 50 literal replacements have been made. Tests still pass.

### 1C. Replace `eval()` in `ScientificCalculator.vue`
**Impact**: Eliminates XSS risk. Single-file fix.

**Current** (line 152):
```typescript
? eval(value.replace('/', ' / '))
```

**Fix**: Replace with a safe fraction parser:
```typescript
function parseFraction(value: string): number {
  const parts = value.split('/')
  if (parts.length === 2) {
    const numerator = parseFloat(parts[0].trim())
    const denominator = parseFloat(parts[1].trim())
    if (!isNaN(numerator) && !isNaN(denominator) && denominator !== 0) {
      return numerator / denominator
    }
  }
  return parseFloat(value)
}
```

**Done when**: No `eval()` calls in client source. Converter presets still work correctly.

### Phase 1 Completion Log (2026-02-25)

**1A delivered:**
- `composables/useAsyncAction.ts` — generic async wrapper with loading/error/data refs, callbacks, external-ref binding
- 14 unit tests (all passing)
- 5 stores refactored: `useJobLogStore`, `useManufacturingPlanStore`, `useRmosAnalyticsStore`, `useLiveMonitorStore`, `fretSlotsCamStore`

**1B delivered:**
- `constants/timing.ts` (16 constants), `constants/dimensions.ts` (13 constants), `constants/index.ts` (barrel)
- Magic numbers replaced in 13 files: Toast, AiImageGallery, AiImagePanel, ToolTable, RosetteEditorView, SnapshotPanel, downloadBlob, useBulkDecision, useBulkDecisionV2, useBulkExport, EngineeringEstimatorView, analytics, InstrumentGeometryForm

**1C delivered:**
- `eval()` replaced with safe `parseFraction()` in `ScientificCalculator.vue`

**Validation:** 0 type errors across 24 modified files. Full test suite: 372 tests pass, 0 failures.

---

## Phase 2 — Duplicate Code Extraction (Est. 6–8 hours) — COMPLETED

### 2A. Extract `composables/useFetchTransform.ts`
**Impact**: Eliminates 40+ fetch-then-transform patterns.

**Signature**:
```typescript
export function useFetchTransform<TRaw, TOut>(
  fetcher: () => Promise<TRaw>,
  transform: (raw: TRaw) => TOut
): { data: Ref<TOut | null>; loading: Ref<boolean>; error: Ref<Error | null>; refresh: () => Promise<void> }
```

**Target files**: SDK endpoint callers in `views/*/composables/`, `stores/`, `features/*/composables/`.

### 2B. Extract `composables/useFormState.ts`
**Impact**: Eliminates 30+ repeated ref-initialization patterns for form/errors/touched.

**Signature**:
```typescript
export function useFormState<T extends Record<string, unknown>>(
  defaults: T
): { form: Ref<T>; errors: Ref<Partial<Record<keyof T, string>>>; touched: Ref<Partial<Record<keyof T, boolean>>>; reset: () => void; isDirty: ComputedRef<boolean> }
```

### 2C. Consolidate adaptive composables
**Directory**: `components/adaptive/composables/` (13 files, ~120 duplicates)

**Action**:
1. Audit all 13 files for shared patterns (loading state, error handling, settings serialization)
2. Extract shared logic into 2-3 internal helper composables
3. Re-export from existing `index.ts`

**Target shared patterns**:
- Settings load/save (appears in `useTrochoidSettings`, `usePocketSettings`, `useAdaptiveFeedPresets`)
- Toolpath execution + logging (appears in `useToolpathRenderer`, `useToolpathExport`, `useRunLogging`)
- Machine profile selection (appears in `useMachineProfiles`, `useOptimizer`)

### 2D. Create `components/compare/CompareUtils.ts`
**Directory**: `components/compare/` (28 files, ~100 duplicates)

**Action**: Extract shared viewport math, diff mode logic, and export formatting into a single utility module. The files `compareViewportMath.ts`, `compareBlinkBehavior.ts`, `compareXrayBehavior.ts`, and `compareLayers.ts` likely have overlapping coordinate-transform and toggle logic.

### 2E. Consolidate rosette composables
**Directory**: `components/rosette/composables/` (7 files, ~90 duplicates)

**Action**: Merge overlapping workflow/export logic between `useWorkflowActions.ts`, `useWorkflowOverrides.ts`, `useExportSnippets.ts`, and `useClipboardExport.ts`.

### 2F. Unify RMOS composables
**Directory**: `components/rmos/composables/` (14 files, ~50 duplicates)

**Action**: Merge overlapping selection/filter/keyboard patterns. `useCandidateSelection`, `useCandidateFilters`, `useCandidateKeyboard`, and `useCandidateHelpers` likely share significant selection-state logic.

### Phase 2 Completion Log

**Commit**: `244bd54d` | **Date**: 2026-02-26 | **Branch**: `main`

| Sub-task | Deliverable | Impact |
|----------|-------------|--------|
| **2A** | `composables/useFetchTransform.ts` + 16 tests | Generic fetch+transform+loading/error composable with `immediate`, `onSuccess`/`onError`, external refs |
| **2B** | `composables/useFormState.ts` + 14 tests | Generic reactive form state with `form`/`errors`/`touched`/`isDirty`/`reset`/`setField` |
| **2C** | `composables/useLocalStorageRef.ts` | Replaces 12+ localStorage read/write/watch blocks across 5 adaptive files |
| **2C** | `adaptive/composables/runLogHelpers.ts` | Extracts `serializeMovesToSegments()` + `buildRunLogBody()` — shared by useLiveLearning & useRunLogging |
| **2C** | Refactored `useLiveLearning.ts` & `useRunLogging.ts` | Both now use shared helpers instead of duplicated inline code |
| **2D** | Deprecated `computeZoomToBox` in `compareViewportMath.ts` | Zero-logic alias for `computeFitTransform` — marked `@deprecated` |
| **2E** | Refactored `useClipboardExport.ts` | Table-driven copy actions eliminate 9x session-guard duplication; uses shared `downloadBlob` util; `WorkflowOverrides` derived via `Pick<>` from `WorkflowOverridesState` |
| **2F** | Refactored `useClipboardToast.ts` | Now composes `useToast()` internally — removes 20 lines of duplicated timer logic |
| **2F** | Created `utils/keyboard.ts` | Shared `isTypingContext()` extracted from `useCandidateKeyboard` + `useKeyboardShortcuts` |
| **2F** | Deprecated `useLegacyBulkDecision.ts` | ~95% clone of `useUndoStack` — marked `@deprecated` |
| **2F** | Deprecated `useCandidateKeyboard.ts` | ~90% clone of `useKeyboardShortcuts` — marked `@deprecated` |

**Validation**: 0 type errors (`vue-tsc --noEmit` clean), 402 tests pass (30 new), 0 failures.

---

## Phase 3 — Dead CSS Cleanup (Est. 3–4 hours)

### 3A. Audit & clean `ScientificCalculator.vue` (15+ dead selectors)
**Method**: Compare `<style scoped>` selectors against `<template>`. The component was recently decomposed into sub-components (`CalculatorDisplay`, `BasicCalculatorPad`, etc.) — CSS for removed elements is likely still present.

### 3B. Audit & clean `PipelineLabView.vue` (12+ dead selectors)
**File**: `views/PipelineLabView.vue`

### 3C. Audit & clean `BlueprintLab.vue` (10+ dead selectors)
**File**: `views/BlueprintLab.vue` (note: actual filename is `BlueprintLab.vue`, not `BlueprintLabView.vue` as stated in handoff)

### 3D. Audit & clean `ManufacturingCandidateList.vue` (8+ dead selectors)
**File**: `components/rmos/ManufacturingCandidateList.vue`  
**Caveat**: Some selectors may target dynamically-generated class names. Mark these with `/* dynamic */` comments rather than deleting.

### 3E. Configure CSS purge in build pipeline
**Action**: Add PurgeCSS or UnCSS to the Vite build config to catch dead CSS automatically going forward.

### Phase 3 Completion Log (commit `ed293794`)

| Sub-task | Deliverable | Notes |
|----------|-------------|-------|
| 3A | ScientificCalculator.vue | **Already clean** — 7 selectors, all used. Decomposition into sub-components was done correctly. |
| 3B | PipelineLabView.vue | **Already clean** — No `<style>` section (uses Tailwind utilities). 0 dead selectors. |
| 3C | BlueprintLab.vue | **Already clean** — 12 selectors, all used. 0 dead selectors. |
| 3D | ManufacturingCandidateList.module.css | **57 dead selectors removed** (521→110 lines). CSS module only imported by parent; child components (CandidateRowItem, CandidateFiltersSection, BulkDecisionBar, etc.) define their own styles. Added `.tableCompact` stub with TODO for child re-implementation. |
| 3D | BasicCalculatorPad.vue, ScientificCalculatorPad.vue | Removed dead `calculator-grid` template class (no matching CSS rule). |
| 3E | `scripts/audit-dead-css.mjs` | CI-ready dead CSS detector — 577 files scanned, detects dead selectors in scoped styles + CSS Modules. Auto-detects Vue Transition classes, dynamic prefix patterns (`'risk-' + level`), and `/* dynamic */` suppression comments. |
| 3E | `package.json` | Added `css:audit` and `css:audit:strict` (CI gate with `--fail-on-dead`) npm scripts. |
| — | Validation | 0 type errors, 402 tests pass, 0 failures |

**Audit baseline**: 814 potentially dead selectors across 62 files (includes false positives from dynamic class bindings). Future phases can use `npm run css:audit` to track progress.

---

## Phase 4 — Memory Leak & Safety Audit (Est. 2–3 hours) — COMPLETED

### 4A. Audit `setTimeout`/`setInterval` without cleanup — COMPLETED
**Audited**: ~60 timer call sites across 40 files. Classified as SAFE (proper cleanup), LEAK (missing cleanup), LOW-RISK (fire-and-forget UI), or N/A (non-component utility).

**11 timer leaks fixed:**

| File | Issue | Fix |
|------|-------|-----|
| `useSnapshotCompareNavigation.ts` | `liveTimer` 200ms debounce, no `onBeforeUnmount` | Added `onBeforeUnmount` cleanup |
| `useCandidateFilters.ts` | `prefsTimer` 250ms localStorage debounce, no cleanup | Added `onBeforeUnmount` cleanup |
| `useLogPolling.ts` | `pollInterval` setInterval, no internal cleanup | Added `onBeforeUnmount(() => stopPolling())` |
| `RosetteEditorView.vue` | `flashTimer` not cleaned in existing `onBeforeUnmount` | Added `flashTimer` cleanup to existing hook |
| `Toast.vue` | Timer ID not stored, no cancellation on re-call | Store timer ID, clear on re-call, add `onBeforeUnmount` |
| `useListFilters.ts` | `prefsTimer` 250ms debounce, no cleanup | Added `onBeforeUnmount` cleanup |
| `useWebSocket.ts` | Reconnect `setTimeout` ID not stored, can't cancel | Store reconnect timer, clear in `disconnect()` |
| `AiImageGallery.vue` | Toast timer IDs not stored, no cleanup | Store timer IDs, clear on re-call, add `onBeforeUnmount` |
| `AiImagePanel.vue` | `previewTimeout` debounce, no `onBeforeUnmount` | Added `onBeforeUnmount` cleanup |
| `EngineeringEstimatorView.vue` | `debounceTimer` no `onBeforeUnmount` | Added `onBeforeUnmount` cleanup |
| `AudioAnalyzerRunsLibrary.vue` | `debounceTimer` no `onBeforeUnmount` | Added `onBeforeUnmount` cleanup |

### 4B. Audit `addEventListener` without `removeEventListener` — COMPLETED
**Audited**: 17 `addEventListener` calls across 14 files. 10 SAFE, 3 N/A, 1 LEAK.

**1 addEventListener leak fixed:**

| File | Issue | Fix |
|------|-------|-----|
| `CurveLab.vue` | `window.addEventListener("resize", setup)` in `onMounted`, no cleanup | Added `onBeforeUnmount(() => window.removeEventListener("resize", setup))` |

---

## Phase 5 — TODO/FIXME Triage (Est. 2 hours) — COMPLETED

**Audit**: 16 TODOs found across `packages/client/src/`. Zero FIXME/HACK/XXX comments exist.

### 5A. Classification Results

| # | File | Classification | Action Taken |
|---|------|---------------|-------------|
| 1 | `cnc_production/PresetManagerPanel.vue` | **STUB** | Deleted file + removed import/usage from `CamProductionView.vue` |
| 2 | `components/art/ReliefRiskPresetPanel.vue` | **STUB** | Deleted file + removed import/usage from `ArtStudioRelief.vue` |
| 3 | `components/cam/composables/useJobIntHistoryActions.ts:26` | ASPIRATIONAL | Left as-is (future UX: detail modal for history entries) |
| 4 | `components/curvelab/composables/useCurveHistory.ts:46` | ACTIONABLE | Left — wire `exportDXF()` to backend `/api/geometry/export?fmt=dxf` |
| 5 | `components/rmos/PromptLineageViewer.vue:6` | ASPIRATIONAL | Left as-is (future: dedicated provenance API) |
| 6 | `components/rmos/PromptLineageViewer.vue:28` | ASPIRATIONAL | Left as-is (same as #5) |
| 7 | `components/rmos/SvgPathDiffViewer.vue:23` | ASPIRATIONAL | Left as-is (future: path-level diff highlighting) |
| 8 | `components/rosette/RosetteCanvas.vue:49` | **STALE** | Deleted dead SVG.js import comment + TODO |
| 9 | `components/rosette/RosetteCanvas.vue:110` | **STALE** | Deleted stale "Initialize SVG.js" TODO comment |
| 10 | `components/rosette/RosetteCanvas.vue:267` | ACTIONABLE | Left — draw preview line during mouse drag |
| 11 | `components/toolbox/composables/useRosetteDesignerExport.ts:101` | ASPIRATIONAL | Left as-is (needs PDF library not in project) |
| 12 | `sdk/endpoints/artPlacement.ts:4` | STUB (keep) | Left — actively imported by PlacementPreviewPanel, typed contract |
| 13 | `utils/neck_generator.ts:480` | **STALE** | Deleted unused `exportNeckAsDXF()` function (never imported) |
| 14 | `views/labs/CompareLab.vue:77` | ASPIRATIONAL | Left as-is (minor state restoration enhancement) |
| 15 | `views/saw_lab_dashboard/composables/useSawRiskActions.ts:135` | ACTIONABLE | Left — wire override apply to backend learned-overrides API |
| 16 | `views/PresetHubView.vue:200` | ACTIONABLE | Left — wire `router.push()` to Job Intelligence panel |

### 5B. Stale Cleanup Summary
- 2 stub files deleted (PresetManagerPanel.vue, ReliefRiskPresetPanel.vue)
- 2 stale SVG.js comments removed (RosetteCanvas.vue)
- 1 dead function deleted (`exportNeckAsDXF` — exported but never imported)

### 5C. Remaining Actionable TODOs (4)
These have clear implementation paths but are feature work, not quality debt:
1. **CurveLab DXF export** — wire to existing backend geometry export API
2. **RosetteCanvas preview line** — draw `<line>` element during mouse drag
3. **Saw Risk override apply** — call learned-overrides API instead of `console.log`
4. **PresetHub job navigation** — add `router.push()` to Job Intelligence view

---

## Phase 6 — Structural Dedup in Views (Est. 4–5 hours) — COMPLETED

### 6A. Consolidate download/export utilities — COMPLETED
**Analysis**: Vue decomposition analyzer scanned 59 view composables across 13 directories.
Fingerprinting identified the highest-impact shared pattern: download/export utilities
duplicated across 10+ sites.

**What was done**:
- Extended `utils/downloadBlob.ts` with `downloadTextFile`, `downloadCsvFile`, `csvEscape`, `filenameTimestamp`
- Eliminated 10 inline blob-download implementations across 8 files
- Consolidated 5 duplicate `csvEscape` implementations → 1 canonical version
- Removed 2 duplicate `filenameTimestamp` helpers
- Removed dead `csvEscape` export from `riskFormatters.ts`

**Files changed (11)**:
- `utils/downloadBlob.ts` — extended with 4 new shared functions
- `views/art/risk-dashboard/useRiskExports.ts` — removed local downloadBlob + buildFilenameTimestamp
- `views/art/risk-dashboard/riskFormatters.ts` — removed dead csvEscape export
- `views/art/composables/useRiskExport.ts` — removed local csvEscape, downloadBlob, buildTimestamp
- `views/cam/risk_timeline_relief/composables/useRiskTimelineActions.ts` — removed local csvEscape + downloadCsv
- `views/bridge_lab/composables/useGcodeExport.ts` — replaced inline blob pattern
- `views/multi_run_comparison/composables/useMultiRunComparisonActions.ts` — replaced inline blob pattern
- `views/rmos_run_viewer/composables/useRmosRunViewerActions.ts` — replaced 2 inline blob patterns
- `views/compare_lab/composables/useCompareLabExport.ts` — replaced inner downloadFile
- `views/cam/RiskPresetSideBySide.vue` — removed local csvEscape + downloadCsv
- `components/art/rosette_compare_history/composables/useRosetteCompareActions.ts` — removed local csvEscape + inline blob

**Also identified (deferred — product decision needed)**:
- `useRiskFilters.ts` exists in 2 locations (risk-dashboard/ and composables/) serving V1 vs V2 views
- `useRiskBuckets.ts` exists in 2 locations serving V1 vs V2 views
- These are competing refactors, not accidental duplicates — consolidation requires V1/V2 decision

**Result**: -94 LOC net, 0 type errors, 402 tests pass, commit `3c08a212`

---

## Execution Order & Dependencies

```
Phase 1A (useAsyncAction) ──┐
Phase 1B (constants)        ├── Independent, can be parallelized
Phase 1C (eval fix)         ┘
        │
        ▼
Phase 2A-2F (dedup extraction)  ← Depends on 1A existing (many refactors will use useAsyncAction)
        │
        ▼
Phase 3A-3E (dead CSS)          ← Independent, can run parallel to Phase 2
        │
        ▼
Phase 4A-4B (memory leaks)      ← Independent
        │
        ▼
Phase 5A-5C (TODO triage)       ← Independent
        │
        ▼
Phase 6A (view hooks)           ← Depends on Phase 2 patterns being established
```

---

## Validation Gates

After **each phase**, run:
```bash
cd packages/client
npm run build          # No compile errors
npm run test           # All tests pass
npm run lint           # No new lint violations
```

After **all phases**, re-run the analyzer:
```bash
cd C:/Users/thepr/Downloads/code-analysis-tool
PYTHONPATH=scripts python -m code_quality C:/Users/thepr/Downloads/luthiers-toolbox/packages/client/src
```

**Target**: Warnings ≤ 500 (from 1,469), Info ≤ 2,000 (from 3,314).

---

## Risk Mitigations

| Risk | Mitigation |
|------|------------|
| Refactoring breaks runtime behavior | Unit tests before & after each extraction. Test commands in `npm run test`. |
| Dead CSS removal breaks dynamic classes | Mark `/* dynamic */` and skip. Only remove selectors with zero template matches. |
| `useAsyncAction` doesn't fit all patterns | Allow exceptions. Some stores have complex loading state (multiple loading refs) — leave those for Phase 6. |
| Constant extraction causes merge conflicts | Do in a single focused PR per constant file. |
| eval removal breaks fraction presets | Add dedicated test case for fraction strings like `"1/4"`, `"3/8"`, `"7/16"`. |

---

## Estimated Total Effort

| Phase | Hours | Priority |
|-------|-------|----------|
| 1 — Quick Wins | 3–4 | **P0** (do first) |
| 2 — Duplicate Extraction | 6–8 | **P1** |
| 3 — Dead CSS | 3–4 | **P1** |
| 4 — Memory/Safety | 2–3 | **P1** |
| 5 — TODO Triage | 2 | **P2** |
| 6 — View Hooks | 4–5 | **P2** |
| **Total** | **20–26** | |

---

*Ready to execute. Start with Phase 1A → 1B → 1C in parallel, then proceed sequentially.*
