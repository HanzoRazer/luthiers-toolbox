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
| RiskDashboardCrossLab.vue | 2062 | Dashboard | Composable ready (see below) |
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

### RiskDashboardCrossLab.vue (2062 LOC) - READY TO WIRE

**Completed:**
- ✅ `useSavedViews` composable created (~400 LOC of logic)
- ✅ `SavedViewsPanel` component created (~300 LOC of template)

**Blocker:** Existing user data uses legacy format (lane, preset, jobHint, since, until
as top-level fields). New composable uses generic `filters: Record<string, string>`.
Data migration strategy needed before wiring.

**Remaining extractions:**
- `FiltersBar.vue` - Lane/preset/date filters (~125 lines)
- `BucketsTable.vue` - Risk buckets with sparklines (~120 lines)
- `BucketDetailsPanel.vue` - Selected bucket drill-down (~120 lines)

**Commit:** `1be2d8c` - Composable + component ready

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
