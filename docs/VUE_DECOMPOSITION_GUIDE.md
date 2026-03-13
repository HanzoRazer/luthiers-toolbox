# Vue Component Decomposition Guide

**Last Updated:** February 2026

This guide documents the strategy for decomposing large Vue components ("god objects") in The Production Shop.

---

## Current Status

### Large Components (>500 LOC) - Updated Feb 2026

| Component | LOC | Type | Status |
|-----------|-----|------|--------|
| EngineeringEstimatorView.vue | 530 | View | ✅ Extracted options + inputs + WBS + Materials (-36%) |
| GeometryToolbar.vue | 614 | UI | Well-documented, no extraction needed |
| ManufacturingCandidateList.vue | 602 | RMOS | Has child components |
| ArtStudioCalculatorDebugPanel.vue | 393 | Debug | ✅ Extracted CalculatorResultCards (-35%) |
| CurveLabModal.vue | 183 | Modal | ✅ Extracted InlineGeometryReport + DxfValidationPanel (-69%) |
| AdvisoryReviewPanel.vue | 483 | AI | ✅ Extracted AssetList + RejectModal + AttachModal (-17%) |
| ManufacturingCandidateListV2.vue | 578 | RMOS | Needs review |
| PlacementPreviewPanel.vue | 429 | Rosette | ✅ Extracted PlacementControlsPanel (-25%) |
| ArtStudioInlay.vue | 467 | Art Studio | ✅ Extracted FretPositionTable + InlaySummary + InlayDetails (-18%) |

**Previously decomposed (now under threshold):**
- ScientificCalculator.vue: 1562 → 219 LOC ✅
- DesignFirstWorkflowPanel.vue: 1548 → 322 LOC ✅
- PipelineLabView.vue: 1466 → 195 LOC ✅
- DxfToGcodeView.vue: 1503 → ~500 LOC ✅
- RiskDashboardCrossLab.vue: 948 → ~400 LOC ✅
- CurveLabModal.vue: 590 → 183 LOC ✅
- ArtStudioInlay.vue: 569 → 467 LOC ✅
- CamPipelineRunner.vue: 524 → 449 LOC ✅
- AdvisoryReviewPanel.vue: 580 → 483 LOC ✅
- CAMEssentialsLab.vue: 510 → 243 LOC ✅
- VisionAttachToRunWidget.vue: 477 → 305 LOC ✅
- AiImageGallery.vue: 496 → 454 LOC ✅
- ArtStudioCalculatorDebugPanel.vue: 603 → 393 LOC ✅
- CurveLab.vue: 447 → 339 LOC ✅
- AdaptivePoly.vue: 463 → 412 LOC ✅
- DualSvgDisplay.vue: 453 → 274 LOC ✅
- MixedMaterialStripFamilyEditor.vue: 409 → 287 LOC ✅
- PolygonOffsetLab.vue: 506 → 397 LOC ✅
- AdaptiveBenchLab.vue: 563 → 489 LOC ✅
- RmosOperationE2EPanel.vue: 501 → 412 LOC ✅
- CompareOpenPanel.vue: 548 → 495 LOC ✅
- JobIntHistoryPanel.vue: 516 → 410 LOC ✅
- BlueprintPresetPanel.vue: 554 → 505 LOC ✅
- LiveMonitor.vue: 535 → 440 LOC ✅
- ArtStudioSidebar.vue: 564 → 359 LOC ✅
- RosetteEditorView.vue: 540 → 455 LOC ✅
- GuitarDesignHub.vue: 462 → 321 LOC ✅
- FinishingDesigner.vue: 471 → 371 LOC ✅
- AiImageProperties.vue: 463 → 373 LOC ✅
- VariantReviewPanel.vue: 445 → 273 LOC ✅
- ArtPresetCompareAB.vue: 449 → 189 LOC ✅
- PlacementPreviewPanel.vue: 574 → 429 LOC ✅
- RmosAiLogViewer.vue: 379 → 173 LOC ✅
- Phase2VectorizationPanel.vue: 404 → 88 LOC ✅
- Phase3CamPanel.vue: 398 → 85 LOC ✅
- SawSlicePanel.vue: 559 → 244 LOC ✅

---

## Decomposition Strategy

### 1. Analyze Before Refactoring

Not all large files need decomposition:
- **CSS-heavy files** (like ScaleLengthDesigner) may be fine
- **Check for existing composables** before creating new ones
- **Template vs script ratio** matters more than raw LOC

### 2. Extract Shared Patterns First

Created components in `components/ui/`:
- `LabeledInput.vue` - Replaces repetitive input+label patterns
- `CardPanel.vue` - Collapsible card containers
- `ActionButton.vue` - Buttons with loading states
- `RiskBadge.vue` - Risk level display
- `RmosTooltip.vue` - Educational tooltips
- `SavedViewsPanel.vue` - Saved filter views panel (new)

Created components in `components/dxf/`:
- `DxfUploadZone.vue` - Drag/drop upload zone
- `CamParametersForm.vue` - CAM parameter inputs
- `RunCompareCard.vue` - Run comparison display

Created components in `components/dashboard/`:
- `FiltersBar.vue` - Lane/preset/date/quick-range filters
- `BucketsTable.vue` - Risk buckets table with sparklines
- `BucketDetailsPanel.vue` - Bucket drill-down details panel

Created components in `components/pocket/`:
- `EnergyHeatPanel.vue` - Energy totals, heat partition, cumulative chart
- `HeatTimeSeriesPanel.vue` - Power chart, live learn controls
- `BottleneckMapPanel.vue` - Bottleneck toggle, legend, pie chart
- `ToolParametersPanel.vue` - Tool Ø, stepover, stepdown, margin, etc.
- `ActionButtonsBar.vue` - Plan, Preview NC, Compare, Export buttons
- `ExportConfigPanel.vue` - Job name, export modes, batch export

Created components in `components/toolbox/cam-essentials/`:
- `PatternOperationCard.vue` - Drill pattern configuration (grid/circle/line)
- `ProbeOperationCard.vue` - Touch probe work offset routines
- `RetractOperationCard.vue` - Safe retract strategies

Created components in `features/ai_images/vision_attach/`:
- `GeneratedAssetsSection.vue` - Asset grid with selection
- `RunSelectionSection.vue` - Run dropdown with search/create
- `AttachActionSection.vue` - Final attach action summary

Created components in `features/ai_images/components/`:
- `AssetQuickOpsPanel.vue` - Quick reject/promote/undo operations
- `ImageActionsPanel.vue` - Attach, download, regenerate, delete buttons
- `ImageSessionStats.vue` - Session count, total cost, provider stats

Created components in `components/artstudio/calculator-debug/`:
- `CalculatorResultCards.vue` - Calculator output cards grid

Created components in `components/curvelab/mode-panels/`:
- `OffsetModePanel.vue` - Offset distance + join type controls
- `FilletModePanel.vue` - Fillet radius control
- `FairModePanel.vue` - Lambda + preserve endpoints controls
- `ClothoidModePanel.vue` - Reset + blend buttons

Created components in `components/toolbox/adaptive-poly/`:
- `PreviewLinkModePanel.vue` - N17 arc/linear link mode toggle
- `SpiralParamsPanel.vue` - N18 feed rate and cutting depth inputs

Created components in `components/compare/dual-svg/`:
- `DiffSkeletonLoader.vue` - Loading skeleton with shimmer animation
- `LayersPanel.vue` - Layer toggle controls with diff/missing badges

Created components in `components/rmos/strip-family/`:
- `MaterialEditorCard.vue` - Single material editor with visual properties

Created components in `components/toolbox/polygon-offset/`:
- `GcodeOutputPanel.vue` - G-code preview with download/copy actions

Created components in `components/toolbox/adaptive-bench/`:
- `BenchResultsPanel.vue` - Benchmark results stats grid display

Created components in `components/toolbox/guitar-design-hub/`:
- `ToolCard.vue` - Clickable tool card with icon, title, desc, badge
- `DesignPhaseSection.vue` - Phase category wrapper with slot

Created components in `components/toolbox/finishing/`:
- `FinishTypesPanel.vue` - Finish type selection cards
- `LaborInputSection.vue` - Labor calculator inputs
- `LaborResultsSection.vue` - Labor results display
- `BurstPreviewCanvas.vue` - Sunburst pattern canvas preview
- `BurstControlsPanel.vue` - Burst type, colors, params, presets, export

Created components in `components/rmos/operation-e2e/`:
- `OperationHistoryPanel.vue` - Operation history list with status badges

Created components in `components/art/snapshot_compare/components/`:
- `SnapshotCard.vue` - Unified left/right snapshot display card

Created components in `components/cam/job-int-history/`:
- `CloneToPresetForm.vue` - Clone-to-preset modal form

Created components in `components/pipeline/blueprint-preset/`:
- `PipelineStatsGrid.vue` - Pipeline run statistics display

Created components in `components/rmos/live-monitor/`:
- `EventMetadataDisplay.vue` - Fragility badge, materials list, lane hint

Created components in `components/artstudio/sidebar/`:
- `InstrumentGeometryForm.vue` - Scale length, fret count, presets, compound radius

Created components in `components/rosette/rosette-editor/`:
- `RingNudgePanel.vue` - Ring width adjustment controls with distribute
- `JumpHUD.vue` - Filter status, ring counts, hotkey tooltip

Created components in `components/rmos/variant-review/`:
- `VariantCard.vue` - Single advisory variant card for review (SVG preview, rating, notes, promote)

Created components in `components/art/preset-compare/`:
- `PresetColumn.vue` - Single preset column for A/B comparison (health badge, stats, lineage)

Created components in `components/rosette/placement-preview/`:
- `PlacementControlsPanel.vue` - Host surface (rect/circle/polygon) and placement controls (scale, rotate, offset)

Created components in `components/rmos/ai-log-viewer/`:
- `AttemptsTable.vue` - AI log attempts table with score, risk, acceptable columns
- `RunsTable.vue` - AI log runs table with attempts, success, score columns

Created components in `components/blueprint/phase2-vectorization/`:
- `VectorizationControls.vue` - Pre-vectorization params (scale, thresholds, min area)
- `VectorizationResults.vue` - Stats grid, preview, and export buttons (SVG/DXF)

Created components in `components/blueprint/phase3-cam/`:
- `CamParametersCard.vue` - Tool diameter, stepover, stepdown, feeds, and generate button
- `CamResultsCard.vue` - RMOS result stats, warnings, errors, and G-code download

### 3. Use Composables for Logic

Existing composables:
- `useDxfWorkflow` - DXF workflow state (not yet used in DxfToGcodeView)
- `usePocketSettings` - Pocket CAM settings
- `useScaleLengthCalculator` - Scale length math
- `useCandidateFilters` - RMOS candidate filtering
- `useCandidateSelection` - Batch selection
- `useSavedViews` - Saved filter views with localStorage (new)

### 4. Create Child Components

Pattern: Extract template sections into focused components that:
- Accept props from parent
- Emit events for state changes
- Have single responsibility

---

## Priority Decomposition Targets

### AdaptivePocketLab.vue (1424 LOC) ✅ IN PROGRESS

**Completed:**
- ✅ `EnergyHeatPanel.vue` (177 LOC) - M.3 energy & heat display
- ✅ `HeatTimeSeriesPanel.vue` (291 LOC) - M.3 heat over time with live learn
- ✅ `BottleneckMapPanel.vue` (169 LOC) - M.1.1 bottleneck toggle + pie chart
- ✅ `ToolParametersPanel.vue` (145 LOC) - Tool Ø, stepover, stepdown, etc.
- ✅ `ActionButtonsBar.vue` (72 LOC) - Plan, Preview NC, Compare, Export
- ✅ `ExportConfigPanel.vue` (85 LOC) - Job name, export modes, batch export

**Remaining:**
- `MachineSelector.vue` - Already extracted, needs wiring review
- `OptimizerPanel.vue` - Feed/stepover optimizer

**Commits:**
- `0013437` - Reduced from 1992 → 1570 LOC (-21%)
- `7d08eb9` - Reduced from 1570 → 1424 LOC (-10%)

### DxfToGcodeView.vue (1503 LOC) ✅ WIRED

**Completed:**
- ✅ `DxfUploadZone.vue` - Wired (46 lines removed)
- ✅ `CamParametersForm.vue` - Wired (92 lines removed)
- ✅ `RunCompareCard.vue` - Wired (176 lines removed)

**Remaining:**
- `RunResultPanel.vue` - Result display with risk badge
- `OverrideModal.vue` - Override submission

**Commit:** `8c552bd` - Reduced from 1847 → 1503 LOC (-19%)

### RiskDashboardCrossLab.vue (948 LOC) ✅ COMPLETE

**Completed:**
- ✅ `useSavedViews` composable (~450 LOC with legacy migration)
- ✅ `SavedViewsPanel` component (~370 LOC)
- ✅ `FiltersBar` component (~230 LOC)
- ✅ `BucketsTable` component (~175 LOC)
- ✅ `BucketDetailsPanel` component (~195 LOC)

**Legacy Migration:** Composable auto-converts old format (`{lane, preset, jobHint, since, until}`)
to new format (`{filters: Record<string, string>}`) on load.

**Commits:**
- `1be2d8c` - Composable + component created
- `35baec8` - Wired SavedViewsPanel (2062 → 1345, -35%)
- `14d7d51` - Wired FiltersBar (1345 → 1209, -41%)
- `822a93b` - Wired BucketsTable + BucketDetailsPanel (1209 → 948, -54%)

### ManufacturingCandidateList.vue (2319 LOC)

**Already has child components:**
- CandidateFiltersBar
- CandidateRowItem
- CandidateSummaryChips
- BulkDecisionModal

**Remaining work:**
- Extract more template sections
- Move inline styles to component styles

---

## Refactoring Rules

1. **Test before and after** - Run type-check and build
2. **One component at a time** - Don't batch risky changes
3. **Preserve behavior** - No functional changes during decomposition
4. **Commit frequently** - Small, focused commits

---

## Code Patterns

### Extracting a Section

```typescript
// Before: Inline in parent
<div class="section">
  <h3>Title</h3>
  <input v-model="value" />
  <button @click="doThing">Action</button>
</div>

// After: Child component
<SectionPanel
  :value="value"
  @update:value="value = $event"
  @action="doThing"
/>
```

### Using Composables

```typescript
// Before: Inline state
const params = ref({ tool_d: 6.0, stepover: 0.45 })

// After: Composable
const { params, updateParam, resetParams } = useCamParameters()
```

---

## Systematic Extraction Workflow (Claude Code Add-on)

This section documents the automated extraction workflow using `analyze_vue_extraction.py`.

### Quick Start

```bash
# 1. Find candidates in components over 500 lines
python scripts/analyze_vue_extraction.py packages/client/src/components --recursive --min-lines 500

# 2. Find candidates in views over 500 lines
python scripts/analyze_vue_extraction.py packages/client/src/views --recursive --min-lines 500

# 3. Choose file with most HIGH candidates, then extract
```

### v-model Pattern for Two-Way Binding

When extracting form sections, use Vue's v-model pattern:

**Child component:**
```vue
<template>
  <input
    :value="toolDiameter"
    type="number"
    @input="emit('update:toolDiameter', parseFloat(($event.target as HTMLInputElement).value))"
  >
</template>

<script setup lang="ts">
defineProps<{
  toolDiameter: number
}>()

const emit = defineEmits<{
  'update:toolDiameter': [value: number]
}>()
</script>
```

**Parent usage:**
```vue
<ToolSetup
  v-model:tool-diameter="params.toolDiameter"
  @update:tool-diameter="onParamChange"
/>
```

**Key rules:**
- Prop name: `camelCase` in defineProps (e.g., `toolDiameter`)
- v-model binding: `kebab-case` (e.g., `v-model:tool-diameter`)
- Emit name must match prop: `update:toolDiameter`

### CSS Modules Handling

When parent uses CSS Modules, pass styles object as prop:

**Child:**
```vue
<template>
  <section :class="styles.panelSection">
    <div :class="styles.formGroup">...</div>
  </section>
</template>

<script setup lang="ts">
defineProps<{
  styles: Record<string, string>
}>()
</script>
```

**Parent:**
```vue
<ChildPanel :styles="styles" />
```

### Nested Candidate Consolidation

When analyzer shows nested HIGH candidates, extract the **outermost** as one component:

```
1. [HIGH] Lines 100-250 - HistorySidebar (contains nested)
   2. [HIGH] Lines 120-160 - RiskMetrics (nested)
   3. [HIGH] Lines 170-220 - PresetScorecard (nested)
```

→ Extract lines 100-250 as `HistorySidebar.vue` containing both nested sections.

### Helper Function Migration

Move helper functions to child when **only used by that section**:

**Before (parent):**
```typescript
function formatDate(iso: string) { /* ... */ }
function riskColor(score: number) { /* ... */ }
// Used only in one section
```

**After (child):**
```typescript
// Moved from parent - only used here
function formatDate(iso: string) { /* ... */ }
function riskColor(score: number) { /* ... */ }
```

### Type Interface Co-location

Move TypeScript interfaces to child when only used there:

```vue
<script setup lang="ts">
// Interfaces moved from parent
interface Hole {
  x: number
  y: number
  enabled: boolean
}

defineProps<{
  holes: Hole[]
}>()
</script>
```

### Subdirectory Organization

Create subdirectory for multiple child extractions:

```
components/
  DrillingLab.vue              # Parent (743 → 546 lines)
  drilling/
    DrillToolSetup.vue         # Extracted
    DrillCycleType.vue         # Extracted
    DrillDepthSettings.vue     # Extracted
```

### Extraction Checklist

Before committing:
- [ ] All extracted components pass type-check
- [ ] v-model prop names match emit names
- [ ] CSS Modules styles passed if needed
- [ ] Helper functions moved to appropriate component
- [ ] Type interfaces moved to appropriate component
- [ ] Line count reduction verified

### Commit Message Template

```
refactor(ui): extract N HIGH candidates from ComponentName.vue

Extract sections into focused child components:
- ChildA.vue (XX lines): description
- ChildB.vue (XX lines): description

ComponentName.vue: XXX → YYY lines (ZZ% reduction)

All components use v-model pattern for two-way binding.
Passes type-check.
```

---

## Success Metrics

| Metric | Before | Current | Target |
|--------|--------|---------|--------|
| Files >800 LOC | 33 | 14 | 0 |
| Files >500 LOC | ~50 | ~25 | <15 |
| Files >1500 LOC | 9 | 1 | 0 |
| Largest file LOC | ~2300 | 3038 | <600 |

**Note (March 2026):** ToolpathPlayer.vue (3038 LOC) is the main remaining outlier.
It is already well-decomposed with 13 child components. The file size is dominated by:
- CSS (1555 lines) - dark theme styling for canvas/HUD
- Template (906 lines) - orchestration of 13 child components
- Script (574 lines) - tightly-coupled state management

Further decomposition requires architectural rework (composable extraction + CSS modularization).
**Deferred to Phase 4** per SCORE_7_PLAN.md.

---

*This document guides Phase 3 of the remediation plan.*
