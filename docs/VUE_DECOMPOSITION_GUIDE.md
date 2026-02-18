# Vue Component Decomposition Guide

**Last Updated:** February 2026

This guide documents the strategy for decomposing large Vue components ("god objects") in Luthier's ToolBox.

---

## Current Status

### Large Components (>800 LOC)

| Component | LOC | Type | Status |
|-----------|-----|------|--------|
| AdaptivePocketLab.vue | 2424 | Lab | Needs decomposition |
| ManufacturingCandidateList.vue | 2319 | RMOS | Has child components |
| RiskDashboardCrossLab.vue | 1209 | Dashboard | ✅ Wired SavedViewsPanel + FiltersBar (-41% LOC) |
| ScaleLengthDesigner.vue | 1892 | Toolbox | CSS-heavy, well-structured |
| DxfToGcodeView.vue | 1503 | View | ✅ Wired components (-344 LOC) |
| ScientificCalculator.vue | 1562 | Toolbox | Needs review |
| DesignFirstWorkflowPanel.vue | 1548 | Art Studio | Needs review |
| PipelineLab.vue | 1466 | Lab | Needs decomposition |
| BlueprintLab.vue | 1459 | Lab | Needs decomposition |

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
- `FiltersBar.vue` - Lane/preset/date/quick-range filters (new)

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

### AdaptivePocketLab.vue (2424 LOC)

**Suggested splits:**
1. `ToolParametersPanel.vue` - Tool Ø, stepover, stepdown inputs
2. `MachineSelector.vue` - Machine profile dropdown + editor
3. `OptimizerPanel.vue` - Feed/stepover optimizer
4. `EnergyHeatPanel.vue` - M.3 energy & heat display
5. `BottleneckChart.vue` - Capacitance pie chart

**Blockers:**
- Complex state sharing between panels
- Multiple modals with cross-dependencies
- Already uses `usePocketSettings` composable

### DxfToGcodeView.vue (1503 LOC) ✅ WIRED

**Completed:**
- ✅ `DxfUploadZone.vue` - Wired (46 lines removed)
- ✅ `CamParametersForm.vue` - Wired (92 lines removed)
- ✅ `RunCompareCard.vue` - Wired (176 lines removed)

**Remaining:**
- `RunResultPanel.vue` - Result display with risk badge
- `OverrideModal.vue` - Override submission

**Commit:** `8c552bd` - Reduced from 1847 → 1503 LOC (-19%)

### RiskDashboardCrossLab.vue (1209 LOC) ✅ WIRED

**Completed:**
- ✅ `useSavedViews` composable created (~450 LOC of logic with legacy migration)
- ✅ `SavedViewsPanel` component created (~370 LOC of template)
- ✅ `FiltersBar` component created (~230 LOC)
- ✅ Wired both components into dashboard
- ✅ Removed ~287 lines of inline saved views template
- ✅ Removed ~370 lines of saved views helper functions
- ✅ Removed ~125 lines of inline filters template

**Legacy Migration:** Composable auto-converts old format (`{lane, preset, jobHint, since, until}`)
to new format (`{filters: Record<string, string>}`) on load.

**Remaining extractions:**
- `BucketsTable.vue` - Risk buckets with sparklines (~120 lines)
- `BucketDetailsPanel.vue` - Selected bucket drill-down (~120 lines)

**Commits:**
- `1be2d8c` - Composable + component created
- `35baec8` - Wired SavedViewsPanel, reduced 2062 → 1345 LOC (-35%)
- `14d7d51` - Wired FiltersBar, reduced 1345 → 1209 LOC (-41% total)

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

## Success Metrics

| Metric | Before | Target |
|--------|--------|--------|
| Files >800 LOC | 33 | <15 |
| Files >1500 LOC | 9 | 0 |
| Average god object LOC | ~1800 | <600 |

---

*This document guides Phase 3 of the remediation plan.*
