# CompareLab State Machine README

**useCompareState — Canonical Compare State Controller**  
(B22.8 and forward)

---

## Overview

`useCompareState.ts` is the official state machine for all CompareLab "compute diff" operations.

It centralizes four critical concerns:

### 1. **Skeleton state** (`isComputingDiff`)
- Tracks whether CompareLab is actively running a diff job
- Powers the animated loading stripes over the SVG panes
- Prevents accidental double-executes (double-clicks, rapid key presses)

### 2. **Disable/Error state** (`diffDisabledReason`)
- Holds backend/validation errors or "overlay not valid" messages
- Automatically disables all overlay-related UI controls
- Displays a toast (B22.8) whenever a new disable reason surfaces

### 3. **Overlay availability** (`overlayDisabled`)
- Derived boolean computed from `isComputingDiff + diffDisabledReason`
- All overlay toggles, color switches, and opacity sliders MUST bind to it

### 4. **Request wrapper** (`runWithCompareSkeleton`)
- Wraps any async diff-compute call
- Enforces skeleton state → run → finalize
- Ensures consistent behavior for all compare entry points

### 5. **Layer System** (B22.8 Skeleton) 🆕
- Tracks layer visibility and diff status
- Supports "show only mismatched layers" filtering
- Provides bounding box data for zoom-to-diff functionality

---

## Why This File Exists

CompareLab previously allowed multiple fragments of logic inside `DualSvgDisplay.vue` to manipulate:
- Loading indicators
- Overlay toggles
- Pan/zoom resets
- Failure messages

This caused drift and inconsistent UI behavior.

**`useCompareState.ts` standardizes all this into a single, predictable, testable module** with clean unit tests (`useCompareState.spec.ts`).

---

## Rules for Development (DO / DO NOT)

> **⚠️ CRITICAL GUARDRAILS:**  
> Violations of these rules will cause state inconsistencies, race conditions, and unpredictable UI behavior.  
> All CompareLab components MUST follow these patterns without exception.

### ✅ DO

**Import and use the composable at the top of your view/component:**

```typescript
import { useCompareState } from '@/composables/useCompareState'

const compareState = useCompareState()
```

**Wrap every compare API operation with:**

```typescript
await compareState.runWithCompareSkeleton(async () => {
  const response = await fetch('/api/compare/run', {...})
  return await response.json()
})
```

**Bind every overlay control with:**

```vue
<button :disabled="compareState.overlayDisabled.value">
  Toggle Overlay
</button>
```

**Allow the component template to reflect state instead of manually toggling controls.**

### ❌ DO NOT

> **🚫 VIOLATION DETECTION:**  
> Code reviews MUST reject any PR that violates these guardrails.  
> ESLint rules may be added in future to enforce these patterns automatically.

- ❌ **NEVER** set overlay controls' `disabled` state manually (bind to `overlayDisabled` only)
- ❌ **NEVER** bypass `runWithCompareSkeleton()` for new diff compute triggers
- ❌ **NEVER** mutate `isComputingDiff` directly (use wrapper or composable actions only)
- ❌ **NEVER** create local copies of state refs (use the composable's refs directly)
- ❌ **NEVER** call backend `/compare/*` endpoints outside the composable
- ❌ **NEVER** implement your own loading/skeleton logic (use existing state)
- ❌ **NEVER** catch and suppress errors from `computeDiff()` without checking `diffDisabledReason`
- ❌ **NEVER** modify layer state directly (use `setLayerEnabled()` action only)

---

## State Machine Interface

### Core State

```typescript
interface CompareState {
  // Refs
  isComputingDiff: Ref<boolean>
  diffDisabledReason: Ref<string | null>
  currentMode: Ref<CompareMode>
  compareResult: Ref<DiffResult | null>
  
  // Layer system (B22.8 Skeleton)
  layers: Ref<CompareLayerInfo[]>
  showOnlyMismatchedLayers: Ref<boolean>
  
  // Computed
  overlayDisabled: ComputedRef<boolean>
  visibleLayers: ComputedRef<CompareLayerInfo[]>
  activeBBox: ComputedRef<CompareResultBBox | null>
  hasResult: ComputedRef<boolean>
  
  // Actions
  computeDiff: (baselineId: string, currentGeometry: CanonicalGeometry) => Promise<void>
  setMode: (mode: CompareMode) => void
  reset: () => void
  runWithCompareSkeleton: <T>(fn: () => Promise<T>) => Promise<T | undefined>
  setLayerEnabled: (id: string, enabled: boolean) => void
  setShowOnlyMismatched: (enabled: boolean) => void
}
```

### State Transitions

```
[Idle State]
  isComputingDiff: false
  diffDisabledReason: null
  overlayDisabled: true (no result)
  compareResult: null
  
       ↓ User triggers computeDiff()
       
[Computing State]
  isComputingDiff: true
  diffDisabledReason: null (cleared)
  overlayDisabled: true (computing)
  compareResult: null (old result)
  
       ↓ Success
       
[Result State]
  isComputingDiff: false
  diffDisabledReason: null
  overlayDisabled: false (ready)
  compareResult: {...}
  layers: [...]
  
       ↓ Error
       
[Error State]
  isComputingDiff: false
  diffDisabledReason: "Error message"
  overlayDisabled: true (error)
  compareResult: null
  layers: []
```

---

## Usage Examples

### Basic Setup in View Component

```typescript
// CompareLabView.vue
<script setup lang="ts">
import { useCompareState } from '@/composables/useCompareState'
import { ref } from 'vue'

const compareState = useCompareState()
const currentGeometry = ref<CanonicalGeometry | null>(null)

async function handleRequestDiff(baselineId: string) {
  if (!currentGeometry.value) {
    console.warn('No geometry loaded')
    return
  }
  
  await compareState.computeDiff(baselineId, currentGeometry.value)
}
</script>

<template>
  <CompareBaselinePicker
    :is-computing-diff="compareState.isComputingDiff.value"
    @request-diff="handleRequestDiff"
  />
  
  <DualSvgDisplay
    :is-computing-diff="compareState.isComputingDiff.value"
    :overlay-disabled="compareState.overlayDisabled.value"
    :diff-disabled-reason="compareState.diffDisabledReason.value"
    :layers="compareState.visibleLayers.value"
    @toggle-layer="compareState.setLayerEnabled"
  />
</template>
```

### Using runWithCompareSkeleton for Custom Operations

```typescript
// Custom diff trigger with transformation
async function computeTransformedDiff(baselineId: string) {
  const result = await compareState.runWithCompareSkeleton(async () => {
    // Transform geometry before sending
    const transformed = applyTransform(currentGeometry.value)
    
    const response = await fetch('/api/compare/lab/diff', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        baseline_id: baselineId,
        current_geometry: transformed
      })
    })
    
    if (!response.ok) {
      throw new Error(`Diff failed: ${response.status}`)
    }
    
    return await response.json()
  })
  
  // result is undefined if operation blocked or errored
  if (result) {
    console.log('Diff successful:', result)
  }
}
```

### Layer Management

```typescript
// Toggle specific layer
compareState.setLayerEnabled('Body', false)

// Show only layers with differences
compareState.setShowOnlyMismatched(true)

// Get visible layers (respects filter)
const visible = compareState.visibleLayers.value

// Get bounding box for zoom
const bbox = compareState.activeBBox.value
if (bbox) {
  zoomToRect(bbox.minX, bbox.minY, bbox.maxX, bbox.maxY)
}
```

---

## Component Integration Pattern

### Data Flow

```
CompareLabView.vue (owns state machine instance)
  ↓ props: state refs (isComputingDiff, overlayDisabled, etc.)
  ↓ events: state actions (@request-diff → computeDiff)
  
CompareSvgDualViewer.vue (pass-through)
  ↓ props: forwards state refs
  ↓ events: forwards events
  
DualSvgDisplay.vue (presentation)
  ↓ renders UI based on props
  ↑ emits events (toggle-layer, mode-change)
```

### Props Pattern

**Parent passes state refs:**
```vue
:is-computing-diff="compareState.isComputingDiff.value"
:overlay-disabled="compareState.overlayDisabled.value"
:diff-disabled-reason="compareState.diffDisabledReason.value"
:layers="compareState.visibleLayers.value"
```

**Child emits requests:**
```vue
@request-diff="compareState.computeDiff"
@toggle-layer="compareState.setLayerEnabled"
@mode-change="compareState.setMode"
```

---

## When to Update This Module

Add or extend this module when:

- ✨ New diff modes are added (overlay, delta, blink, x-ray, etc.)
- 🔧 Compare job parameters change (new filters, transforms)
- ⌨️ You add keyboard shortcuts or programmatic triggers
- 🐛 You need to adjust failure handling or skeleton transitions
- 📊 New metadata fields required in diff results
- 🎨 Layer system enhancements (filtering, grouping)

---

## Testing

### Unit Tests

**Location:** `client/src/composables/useCompareState.spec.ts`

**Coverage:** 40+ tests across 8 describe blocks

**Key Test Areas:**
- Initial state validation
- `overlayDisabled` computed logic (3 conditions)
- `runWithCompareSkeleton` success/error paths
- Double-click protection (concurrent operation blocking)
- `computeDiff` action validation
- `setMode` action with overlay disabled guard
- `reset` action state clearing
- Integration tests (full state transitions)

**Run Tests:**
```bash
cd client
npm run test useCompareState
```

**Coverage Report:**
```bash
npm run test:coverage
# Open client/coverage/index.html
```

### Manual Testing Checklist

See: `docs/COMPARELAB_DEV_CHECKLIST.md`

---

## Protocol Compliance

### B22.8 Protocol Requirements

All CompareLab implementations **MUST** comply with the following protocol:

#### Protocol Rule 1: Single Source of Truth
- **Requirement:** `useCompareState` is the ONLY place that mutates `isComputingDiff`, `diffDisabledReason`, and `overlayDisabled`
- **Enforcement:** Code review verification
- **Rationale:** Prevents state drift and race conditions
- **Violation Example:**
  ```typescript
  // ❌ WRONG - Manual state mutation
  const isLoading = ref(false)
  isLoading.value = true
  
  // ✅ RIGHT - Use composable state
  compareState.isComputingDiff.value  // Read-only
  ```

#### Protocol Rule 2: Wrapper Enforcement
- **Requirement:** ALL async diff operations MUST use `runWithCompareSkeleton()`
- **Enforcement:** Code review + future ESLint rule
- **Rationale:** Ensures consistent skeleton display and double-click protection
- **Violation Example:**
  ```typescript
  // ❌ WRONG - Direct API call
  const result = await fetch('/api/compare/run', {...})
  
  // ✅ RIGHT - Use wrapper
  const result = await compareState.runWithCompareSkeleton(async () => {
    return await fetch('/api/compare/run', {...})
  })
  ```

#### Protocol Rule 3: Disabled State Binding
- **Requirement:** ALL overlay controls MUST bind `:disabled` to `overlayDisabled.value`
- **Enforcement:** Code review verification
- **Rationale:** Consistent UX across all controls
- **Violation Example:**
  ```vue
  <!-- ❌ WRONG - Local disabled logic -->
  <button :disabled="!hasResult || isProcessing">
  
  <!-- ✅ RIGHT - Bind to composable -->
  <button :disabled="compareState.overlayDisabled.value">
  ```

#### Protocol Rule 4: Props-Down / Events-Up
- **Requirement:** State flows down via props, mutations flow up via events
- **Enforcement:** Architecture review
- **Rationale:** Unidirectional data flow, testable components
- **Pattern:**
  ```
  CompareLabView (state owner)
    ↓ props: state.isComputingDiff.value
    ↑ events: @request-diff
  DualSvgDisplay (presenter)
    ↓ receives props
    ↑ emits events
  ```

#### Protocol Rule 5: Error Handling
- **Requirement:** Errors MUST be captured in `diffDisabledReason`, not thrown or logged silently
- **Enforcement:** Test coverage verification
- **Rationale:** User-visible error messages, debuggable failures
- **Pattern:**
  ```typescript
  // ✅ Errors auto-captured by runWithCompareSkeleton
  await compareState.runWithCompareSkeleton(async () => {
    // This error becomes diffDisabledReason
    throw new Error('Backend failed')
  })
  
  // Check error state
  if (compareState.diffDisabledReason.value) {
    console.error('Diff failed:', compareState.diffDisabledReason.value)
  }
  ```

### Protocol Audit Checklist

Before merging any CompareLab changes, verify:

- [ ] **Rule 1:** No manual mutation of `isComputingDiff`, `diffDisabledReason`, `overlayDisabled`
- [ ] **Rule 2:** All async diff calls wrapped in `runWithCompareSkeleton()`
- [ ] **Rule 3:** All overlay controls bind `:disabled="overlayDisabled.value"`
- [ ] **Rule 4:** State owner pattern maintained (view owns composable, children receive props)
- [ ] **Rule 5:** Errors visible in `diffDisabledReason` (not silently caught)
- [ ] **Tests:** Unit tests pass with 95%+ coverage
- [ ] **Manual:** Checklist completed (`COMPARELAB_DEV_CHECKLIST.md`)
- [ ] **Docs:** README updated if new patterns added

## Version Control

This module is part of the **B22.8 CompareLab polish phase** (see developer notes inside `DualSvgDisplay.vue`).

### Version History

- **B22.8 Core:** State machine with skeleton, disable reason, overlay control
- **B22.8 Tests:** Unit test suite with 40+ tests (100% coverage target)
- **B22.8 Skeleton:** Layer system, bounding boxes, enhanced types

### Compatibility Promise

Any future refactor (B22.9, B23.x) **MUST maintain backward compatibility** unless explicitly marked in patch notes.

**Backward Compatibility Guarantees:**

1. **Interface Stability:** Existing `CompareState` properties/methods won't be removed
2. **Additive Changes:** New features added as optional properties (with `?` in TypeScript)
3. **Deprecation Warnings:** 1 protocol version notice before breaking changes
4. **Migration Guides:** Breaking changes documented in `docs/B<version>_MIGRATION.md`

**Example of Acceptable Change (B22.9):**
```typescript
// ✅ ALLOWED - Adding optional field
export interface DiffResult {
  // ... existing fields
  metadata?: { timestamp: string }  // New optional field
}
```

**Example of Breaking Change (B23.0):**
```typescript
// ❌ REQUIRES MIGRATION GUIDE
export interface DiffResult {
  // ⚠️ BREAKING: Renamed field
  summary_stats: DiffSummary  // Was: summary
}
```

### Breaking Change Protocol

If a breaking change is required:

1. **Increment Protocol Version:** Major bump (e.g., B22.x → B23.0)
2. **Document Migration Path:** Create `docs/B23_MIGRATION.md` with:
   - What changed (before/after code)
   - Why it changed (rationale)
   - How to migrate (step-by-step)
   - Automated migration script (if possible)
3. **Provide Deprecation Shims:** Keep old API working for 1 protocol version with console warnings
4. **Update All Consumers:** Same commit must update all components using old API
5. **Update Tests:** All test suites must pass with new API
6. **Team Notification:** Announce breaking change in team chat/email with migration timeline

**Example Migration Guide Structure:**
```markdown
# B23.0 Migration Guide

## Breaking Changes

### 1. Renamed `summary` to `summary_stats`

**Before (B22.x):**
```typescript
const { summary } = compareState.compareResult.value
```

**After (B23.0):**
```typescript
const { summary_stats } = compareState.compareResult.value
```

**Migration Script:**
```bash
# Run automated migration
npm run migrate:b23
```

### 2. Deprecated: `computeDiff()` now requires options object

**Timeline:** 
- B23.0: Old signature works with warning
- B23.1: Old signature throws error
- B24.0: Old signature removed

**Migration:**
```typescript
// Before
await computeDiff(baselineId, geometry)

// After
await computeDiff({ baselineId, geometry, options: {} })
```
```

---

## Architecture Decisions

### Why Composable Instead of Pinia Store?

**Decision:** Use Vue composable pattern over Pinia store

**Rationale:**
- CompareLab state is **view-scoped** (not global)
- Single instance per view (no cross-component sharing)
- Simpler testing (no store mocking required)
- Clearer ownership (view owns instance)

**When to Use Pinia:** Global settings, user preferences, cross-lab state

### Why `runWithCompareSkeleton` Instead of Middleware?

**Decision:** Explicit wrapper function over implicit middleware

**Rationale:**
- **Visibility:** Clear where skeleton logic applies
- **Control:** Caller can check result (undefined on error)
- **Simplicity:** No framework-level hooks needed
- **Testability:** Easy to mock and verify behavior

### Why Computed `overlayDisabled` Instead of Ref?

**Decision:** Computed property derived from 3 conditions

**Rationale:**
- **Single source of truth:** Derived from other refs
- **Consistency:** Can't get out of sync
- **Clarity:** Logic visible in one place
- **Reactive:** Auto-updates when dependencies change

---

## Common Patterns

### Pattern 1: Button Disabled Binding

```vue
<button
  :disabled="compareState.overlayDisabled.value"
  :title="compareState.diffDisabledReason.value || 'Toggle overlay mode'"
  @click="compareState.setMode('overlay')"
>
  Overlay Mode
</button>
```

### Pattern 2: Conditional Rendering

```vue
<!-- Show skeleton while computing -->
<div v-if="compareState.isComputingDiff.value" class="skeleton">
  <div class="shimmer"></div>
  <p>Computing diff...</p>
</div>

<!-- Show error banner when disabled -->
<div v-else-if="compareState.diffDisabledReason.value" class="error-banner">
  ⚠ {{ compareState.diffDisabledReason.value }}
</div>

<!-- Show normal content -->
<div v-else class="content">
  <!-- Diff results -->
</div>
```

### Pattern 3: Error Handling in Actions

```typescript
async function customDiffOperation() {
  try {
    const result = await compareState.computeDiff(baselineId, geometry)
    // Success path
    console.log('Diff complete')
  } catch (error) {
    // Error already captured in diffDisabledReason
    console.error('Diff failed:', compareState.diffDisabledReason.value)
  }
}
```

---

## Troubleshooting

### Issue: Overlay controls not disabling during computation

**Check:**
```vue
<!-- Wrong: local disabled logic -->
<button :disabled="localLoading || !hasResult">

<!-- Right: bind to state machine -->
<button :disabled="compareState.overlayDisabled.value">
```

### Issue: Double-click still triggers duplicate requests

**Check:**
```typescript
// Wrong: direct call
await fetch('/api/compare/run', {...})

// Right: use wrapper
await compareState.runWithCompareSkeleton(async () => {
  return await fetch('/api/compare/run', {...})
})
```

### Issue: Error messages not showing

**Check:**
1. Is `diffDisabledReason` bound to UI?
2. Is error banner conditional on `diffDisabledReason`?
3. Does backend return proper error format?

```typescript
// Backend should return:
{ detail: "User-friendly error message" }

// State machine will extract from:
err?.response?.data?.detail || err?.message || "Default message"
```

### Issue: Layer toggles not working

**Check:**
1. Are layers passed to child component?
2. Is `@toggle-layer` event wired?
3. Does backend return `layers` array?

```vue
<!-- Parent -->
:layers="compareState.visibleLayers.value"
@toggle-layer="compareState.setLayerEnabled"

<!-- Child -->
emit('toggle-layer', layer.id, !layer.enabled)
```

---

## Related Documentation

- **Implementation Summary:** `docs/B22_8_IMPLEMENTATION_SUMMARY.md`
- **Skeleton Integration:** `docs/B22_8_SKELETON_INTEGRATION.md`
- **Test Setup Guide:** `docs/B22_8_TEST_SETUP.md`
- **Manual Test Checklist:** `docs/COMPARELAB_DEV_CHECKLIST.md`
- **Unit Tests:** `client/src/composables/useCompareState.spec.ts`

---

## Quick Reference Card

```typescript
// Import
import { useCompareState } from '@/composables/useCompareState'

// Initialize
const compareState = useCompareState()

// Core State
compareState.isComputingDiff.value       // boolean
compareState.overlayDisabled.value       // boolean (computed)
compareState.diffDisabledReason.value    // string | null
compareState.compareResult.value         // DiffResult | null

// Layer State
compareState.layers.value                // CompareLayerInfo[]
compareState.visibleLayers.value         // CompareLayerInfo[] (filtered)
compareState.activeBBox.value            // CompareResultBBox | null

// Actions
await compareState.computeDiff(baselineId, geometry)
compareState.setMode('overlay' | 'delta' | 'blink' | 'x-ray')
compareState.setLayerEnabled(layerId, true)
compareState.setShowOnlyMismatched(true)
compareState.reset()

// Wrapper
await compareState.runWithCompareSkeleton(async () => {...})
```

---

**Status:** ✅ Production Ready (B22.8)  
**Test Coverage:** 100% target for state machine core  
**Backward Compatible:** Yes (all enhancements additive)  
**Next Protocol:** B22.9 (awaiting specification)
