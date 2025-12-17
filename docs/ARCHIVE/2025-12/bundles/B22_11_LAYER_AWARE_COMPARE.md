# B22.11: Layer-Aware Compare (Per-Layer Toggles + Presence Detection)

**Status:** ✅ Complete  
**Date:** December 3, 2025  
**Dependencies:** B22.8 (State Machine), B22.9 (Autoscale), B22.10 (Compare Modes)

---

## 🎯 Overview

B22.11 adds **layer-aware comparison** to CompareLab, enabling users to:

1. **See layer presence** - Which layers exist in left vs right
2. **Toggle visibility per side** - Show/hide individual layers on left or right
3. **Filter by mismatch** - Focus on layers that differ between sides
4. **Non-destructive CSS hiding** - No SVG rewriting, just CSS injection

**Key Design:** Uses CSS `display: none` targeting `<g id="...">` or `<g data-layer-id="...">` elements, preserving original SVG structure.

---

## 📦 Files Added (7 files)

### Core Logic
```
client/src/components/compare/
├── compareLayers.ts                      # Layer model + utilities (140 lines)
├── compareLayers.spec.ts                 # Layer utilities tests (180 lines)
├── compareLayerVisibility.ts             # Visibility composable (60 lines)
├── compareLayerVisibility.spec.ts        # Visibility tests (120 lines)
└── compareLayerPanel.vue                 # Layer panel UI component (200 lines)
```

### Documentation
```
docs/
└── B22_11_LAYER_AWARE_COMPARE.md         # This file (400+ lines)
```

---

## 🔌 API Reference

### Layer Data Model

```typescript
// compareLayers.ts

export type LayerId = string;

export type LayerInfo = {
  id: LayerId;           // Unique layer identifier (matches SVG g@id)
  label: string;         // Human-readable name

  inLeft: boolean;       // Exists in left SVG
  inRight: boolean;      // Exists in right SVG

  visibleLeft: boolean;  // User toggle for left visibility
  visibleRight: boolean; // User toggle for right visibility
};

export type LayerDiffSummary = {
  addedLeftOnly: LayerId[];   // Layers only in left
  addedRightOnly: LayerId[];  // Layers only in right
  common: LayerId[];          // Layers in both
};
```

### Utility Functions

```typescript
// Build layer diff summary
export function buildLayerDiffSummary(layers: LayerInfo[]): LayerDiffSummary;

// Check if layer is mismatched (presence or visibility differs)
export function isLayerMismatched(layer: LayerInfo): boolean;

// CSS escape layer ID for selectors
export function cssEscapeLayerId(id: string): string;

// Build CSS to hide layers by ID
export function buildHiddenLayerCss(hiddenLayerIds: Set<LayerId>): string;

// Normalize layer data from backend
export function normalizeLayerInfo(layer: Partial<LayerInfo>): LayerInfo;
```

### Visibility Composable

```typescript
// compareLayerVisibility.ts

export function useLayerVisibility(layers: Ref<LayerInfo[]>): {
  hiddenLeftLayers: Ref<Set<LayerId>>;
  hiddenRightLayers: Ref<Set<LayerId>>;
  leftLayerCss: Ref<string>;
  rightLayerCss: Ref<string>;
};

export function createLayerStyleElement(css: string): string;
```

---

## 🔧 Integration Guide

### Step 1: Extend Backend Response Type

```typescript
// DualSvgDisplay.vue or types file

import type { LayerInfo } from "./compareLayers";

type CompareDiffResponse = {
  // Existing fields
  fullBBox: BBox;
  diffBBox: BBox | null;

  // B22.11: Layer data (optional)
  layers?: LayerInfo[];
};
```

**Backend response example:**
```json
{
  "fullBBox": { "minX": 0, "minY": 0, "maxX": 200, "maxY": 150 },
  "diffBBox": { "minX": 50, "minY": 30, "maxX": 180, "maxY": 120 },
  "layers": [
    {
      "id": "body",
      "label": "Body",
      "inLeft": true,
      "inRight": true,
      "visibleLeft": true,
      "visibleRight": true
    },
    {
      "id": "inlay",
      "label": "Decorative Inlay",
      "inLeft": false,
      "inRight": true,
      "visibleLeft": false,
      "visibleRight": true
    }
  ]
}
```

### Step 2: Add Layer State in DualSvgDisplay.vue

```typescript
import { ref, computed } from "vue";
import type { LayerInfo } from "./compareLayers";
import { normalizeLayerInfo } from "./compareLayers";
import { useLayerVisibility } from "./compareLayerVisibility";

// Layer state
const layers = ref<LayerInfo[]>([]);

// Derived visibility state
const { hiddenLeftLayers, hiddenRightLayers, leftLayerCss, rightLayerCss } =
  useLayerVisibility(layers);

// Computed flags
const hasLayerData = computed(() => layers.value.length > 0);
```

### Step 3: Update handleDiffResponse

```typescript
async function handleDiffResponse(resp: CompareDiffResponse) {
  fullBBox.value = resp.fullBBox;
  diffBBox.value = resp.diffBBox;
  hasDiffBBox.value = !!resp.diffBBox;

  // B22.11: Hydrate layers if present
  if (resp.layers && resp.layers.length > 0) {
    layers.value = resp.layers.map(normalizeLayerInfo);
  } else {
    layers.value = [];
  }

  await autoscaleToFullBBox();
}
```

### Step 4: Add Layer Panel Component

```vue
<script setup lang="ts">
import CompareLayerPanel from "./compareLayerPanel.vue";
</script>

<template>
  <div class="compare-layout">
    <!-- B22.11: Layer panel (left sidebar) -->
    <CompareLayerPanel
      :layers="layers"
      :disabled="isComputingDiff"
    />

    <!-- Existing panes wrapper -->
    <div class="compare-layout__panes">
      <!-- Your existing panes -->
    </div>
  </div>
</template>

<style scoped>
.compare-layout {
  display: grid;
  grid-template-columns: 200px minmax(0, 1fr);
  gap: 0.75rem;
}

.compare-layout__panes {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
}
</style>
```

### Step 5: Inject Layer CSS into SVG

**Option A: Inline SVG with `<defs>`**

```vue
<svg
  xmlns="http://www.w3.org/2000/svg"
  :style="{
    transform: `translate(${leftPanZoom.tx}px, ${leftPanZoom.ty}px) scale(${leftPanZoom.scale})`,
    transformOrigin: '0 0'
  }"
>
  <!-- B22.11: Layer visibility CSS -->
  <defs v-if="leftLayerCss">
    <style type="text/css">{{ leftLayerCss }}</style>
  </defs>

  <!-- Your SVG content with <g id="..."> groups -->
  <g id="body">
    <!-- Body geometry -->
  </g>
  <g id="neck">
    <!-- Neck geometry -->
  </g>
  <g id="inlay">
    <!-- Inlay geometry -->
  </g>
</svg>
```

**Option B: v-html injection**

```vue
<div class="svg-wrapper">
  <svg
    xmlns="http://www.w3.org/2000/svg"
    :style="{
      transform: `translate(${leftPanZoom.tx}px, ${leftPanZoom.ty}px) scale(${leftPanZoom.scale})`,
      transformOrigin: '0 0'
    }"
  >
    <defs v-if="leftLayerCss">
      <style type="text/css">{{ leftLayerCss }}</style>
    </defs>
    <g v-html="leftSvgInnerHtml" />
  </svg>
</div>
```

**CSS Output Example:**
```css
/* When body and inlay layers are hidden on left */
g#body, g[data-layer-id="body"], g#inlay, g[data-layer-id="inlay"] {
  display: none !important;
}
```

---

## 🎨 Layer Panel Component

### Props

```typescript
interface Props {
  layers: LayerInfo[];
  disabled?: boolean;  // Disables toggles during computation
}
```

### Features

1. **Layer List**
   - Shows all layers with toggles
   - Left (L) and Right (R) checkboxes per layer
   - Disabled checkboxes for layers not present on that side

2. **Presence Badges**
   - "Left only" badge (blue) for layers unique to left
   - "Right only" badge (purple) for layers unique to right

3. **Mismatch Filter**
   - "Only mismatched" checkbox
   - Filters to show only layers with presence or visibility differences

4. **Summary Footer**
   - Shows count of common layers
   - Shows count of left-only layers (if any)
   - Shows count of right-only layers (if any)

### Visual States

```
┌─────────────────────────────┐
│ Layers     ☑ Only mismatched│
├─────────────────────────────┤
│ Body                  [✓] L │
│                       [✓] R │
├─────────────────────────────┤
│ Neck                  [✓] L │
│                       [✓] R │
├─────────────────────────────┤
│ Inlay            Right only │
│                       [ ] L │
│                       [✓] R │
├─────────────────────────────┤
│ 2 common  1 right only      │
└─────────────────────────────┘
```

---

## 🧪 Unit Tests

### Layer Utilities Tests
**File:** `compareLayers.spec.ts`

**buildLayerDiffSummary:**
- ✅ Identifies layers present only in left
- ✅ Identifies layers present only in right
- ✅ Identifies common layers
- ✅ Handles layers absent from both sides
- ✅ Handles empty layer list

**isLayerMismatched:**
- ✅ Returns true for presence mismatch (left only)
- ✅ Returns true for presence mismatch (right only)
- ✅ Returns true for visibility mismatch (left hidden)
- ✅ Returns true for visibility mismatch (right hidden)
- ✅ Returns false when present and visible on both

**cssEscapeLayerId:**
- ✅ Escapes backslashes
- ✅ Escapes double quotes
- ✅ Escapes single quotes
- ✅ Escapes newlines
- ✅ Handles normal IDs without changes

**buildHiddenLayerCss:**
- ✅ Returns empty string for no hidden layers
- ✅ Builds CSS for single hidden layer
- ✅ Builds CSS for multiple hidden layers
- ✅ Escapes special characters in layer IDs

**normalizeLayerInfo:**
- ✅ Sets default label from id
- ✅ Uses provided label
- ✅ Defaults inLeft/inRight to false
- ✅ Defaults visibility to match presence
- ✅ Respects explicit visibility flags
- ✅ Handles empty id with fallback label

### Visibility Composable Tests
**File:** `compareLayerVisibility.spec.ts`

**useLayerVisibility:**
- ✅ Computes empty hidden sets when all visible
- ✅ Identifies hidden left layers
- ✅ Identifies hidden right layers
- ✅ Builds CSS for hidden layers
- ✅ Updates reactively when visibility changes
- ✅ Handles empty layer list
- ✅ Handles multiple hidden layers on same side

**createLayerStyleElement:**
- ✅ Wraps CSS in style element
- ✅ Returns empty string for empty CSS
- ✅ Preserves complex CSS

### Run All Tests

```bash
cd client
npm run test -- compare
```

**Expected output:**
```
✓ compareLayers.spec.ts (26 tests)
✓ compareLayerVisibility.spec.ts (10 tests)
✓ compareModes.spec.ts (7 tests)
✓ compareBlinkBehavior.spec.ts (8 tests)
✓ compareXrayBehavior.spec.ts (9 tests)

Test Files  5 passed (5)
     Tests  60 passed (60)
```

---

## 🎬 UX Behavior

### Layer Presence Detection

**Scenario: Layer exists in both**
- Both L and R toggles enabled
- No presence badge shown
- Default: both visible

**Scenario: Layer exists only in left**
- L toggle enabled, R toggle disabled (grayed out)
- "Left only" badge (blue) displayed
- Default: visible on left

**Scenario: Layer exists only in right**
- L toggle disabled, R toggle enabled
- "Right only" badge (purple) displayed
- Default: visible on right

### Visibility Toggles

**Toggle left visibility:**
- Unchecking L hides layer in left pane
- CSS injected: `g#layerId { display: none !important; }`
- Does not affect right pane

**Toggle right visibility:**
- Unchecking R hides layer in right pane
- Independent of left visibility state

### Mismatch Filter

**When "Only mismatched" is checked:**
- Shows layers where `inLeft !== inRight` (presence mismatch)
- Shows layers where visibility differs from default
- Hides layers present and visible on both sides

**Use case:** Focus attention on differences, hide common structure

---

## 🔍 Edge Cases Handled

1. **No layer data from backend** - Panel not rendered, no behavior change
2. **Layer ID escaping** - Special characters (quotes, backslashes) escaped in CSS selectors
3. **Both selectors** - Targets `g#id` and `g[data-layer-id="id"]` for flexibility
4. **Empty layer list** - Gracefully handles no layers (no CSS injected)
5. **Disabled state** - All toggles disabled during `isComputingDiff`
6. **Reactivity** - CSS updates automatically when toggles change
7. **Non-destructive** - Original SVG markup unchanged, only CSS added

---

## 📊 Performance Characteristics

- **Layer panel render:** O(n) where n = number of layers
- **CSS generation:** O(h) where h = number of hidden layers
- **CSS application:** Browser-native (GPU-accelerated display:none)
- **Memory:** ~100 bytes per LayerInfo, ~50 bytes per CSS rule
- **Reactivity overhead:** Negligible (computed refs)

**No performance concerns for typical guitar designs (5-20 layers).**

---

## 🚀 Backend Integration

### Required Response Fields

```typescript
{
  layers?: [
    {
      id: string;           // Required: matches SVG g@id
      label?: string;       // Optional: human-readable name (defaults to id)
      inLeft: boolean;      // Required: layer exists in left SVG
      inRight: boolean;     // Required: layer exists in right SVG
      visibleLeft?: boolean;  // Optional: defaults to inLeft
      visibleRight?: boolean; // Optional: defaults to inRight
    }
  ]
}
```

### SVG Structure Requirements

**Option 1: ID-based layers**
```xml
<svg xmlns="http://www.w3.org/2000/svg">
  <g id="body">
    <!-- Body paths -->
  </g>
  <g id="neck">
    <!-- Neck paths -->
  </g>
  <g id="inlay">
    <!-- Inlay paths -->
  </g>
</svg>
```

**Option 2: Data attribute layers**
```xml
<svg xmlns="http://www.w3.org/2000/svg">
  <g data-layer-id="body">
    <!-- Body paths -->
  </g>
  <g data-layer-id="neck">
    <!-- Neck paths -->
  </g>
  <g data-layer-id="inlay">
    <!-- Inlay paths -->
  </g>
</svg>
```

**Both patterns supported** - CSS targets both selectors.

### Fallback Behavior (No Backend Support)

If backend doesn't send `layers` field:
- Panel not rendered
- All existing behavior works unchanged
- No errors or warnings

**Migration path:** Add layer support incrementally without breaking existing deployments.

---

## 🔧 Advanced Patterns

### Programmatic Layer Control

```typescript
// Hide all left-only layers
const leftOnlyLayers = layers.value.filter(l => l.inLeft && !l.inRight);
leftOnlyLayers.forEach(l => l.visibleLeft = false);

// Show only common layers
layers.value.forEach(l => {
  l.visibleLeft = l.inLeft && l.inRight;
  l.visibleRight = l.inLeft && l.inRight;
});

// Reset all to visible
layers.value.forEach(l => {
  l.visibleLeft = l.inLeft;
  l.visibleRight = l.inRight;
});
```

### Custom Layer Badges

Extend `compareLayerPanel.vue` to show custom badges:

```vue
<span v-if="layer.metadata?.modified" class="layer-row__badge layer-row__badge--modified">
  Modified
</span>
```

### Layer Groups

Extend `LayerInfo` with parent/child relationships:

```typescript
export type LayerInfo = {
  // ... existing fields
  parentId?: LayerId;
  children?: LayerId[];
};
```

---

## 🐛 Troubleshooting

### Issue: Layer not hiding when toggled
**Solution:** 
- Verify SVG uses `<g id="...">` or `<g data-layer-id="...">`
- Check browser console for CSS injection
- Inspect computed `leftLayerCss` / `rightLayerCss` values

### Issue: Special characters in layer ID break CSS
**Solution:** 
- Use `cssEscapeLayerId()` (already applied)
- Alternatively, sanitize layer IDs on backend to use only `[a-zA-Z0-9_-]`

### Issue: Panel not showing even with layer data
**Solution:**
- Check `hasLayerData` computed is true
- Verify `layers.value.length > 0`
- Ensure panel not hidden by parent CSS

### Issue: Toggles disabled when they shouldn't be
**Solution:**
- Check `isComputingDiff` state (should be false after diff completes)
- Verify `layer.inLeft` / `layer.inRight` flags are correct

---

## 📋 Integration Checklist

- [ ] Add `compareLayers.ts` and tests
- [ ] Add `compareLayerVisibility.ts` and tests
- [ ] Add `compareLayerPanel.vue` component
- [ ] Extend `CompareDiffResponse` type with `layers` field
- [ ] Add `layers` ref in `DualSvgDisplay.vue`
- [ ] Initialize `useLayerVisibility` composable
- [ ] Update `handleDiffResponse` to normalize layers
- [ ] Add layer panel to template with grid layout
- [ ] Inject `leftLayerCss` into left SVG `<defs>`
- [ ] Inject `rightLayerCss` into right SVG `<defs>`
- [ ] Test with backend returning layer data
- [ ] Test with no layer data (fallback)
- [ ] Run tests: `npm run test -- compare`
- [ ] Verify layer toggles hide/show correctly
- [ ] Test mismatch filter
- [ ] Verify presence badges display correctly

---

## 🎯 Next Steps: B22.12+

With B22.11 complete, **CompareLab has full layer control:**

- ✅ B22.8: State machine + guardrails
- ✅ B22.9: Autoscale + zoom-to-diff
- ✅ B22.10: 5 compare modes (side-by-side, overlay, delta, blink, X-ray)
- ✅ B22.11: Layer-aware compare (per-layer toggles + presence detection)

**Ready for advanced features:**

- **B22.12:** Diff heatmap (color-coded change intensity on unchanged layers)
- **B22.13:** Export diff report (PDF/HTML with layer breakdown)
- **B22.14:** Diff animation (morph between states with layer transitions)
- **B22.15:** Layer history (track changes across multiple versions)

---

**Status:** ✅ B22.11 Complete - Layer-Aware Compare Ready  
**Next:** User approval to begin B22.12 (Diff Heatmap)
