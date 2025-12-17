# B21: Route Registration Guide – Multi-Run Comparison

**Component:** `packages/client/src/views/MultiRunComparisonView.vue`  
**Target Route:** `/lab/compare-runs`  
**Status:** Manual setup required

---

## 🎯 Overview

The Multi-Run Comparison component (`MultiRunComparisonView.vue`) is complete but needs route registration. This project uses a **dynamic routing pattern** where routes are not centrally configured.

**Architecture Pattern:**
- No centralized `router/index.ts` in `packages/client/`
- Components imported on-demand via navigation actions
- Routes referenced directly in navigation links (stores, components)

---

## 📋 Registration Options

### **Option 1: Add to Geometry Store (Recommended)**

If Multi-Run Comparison is a CAM tool, add to `packages/client/src/stores/geometry.ts`:

```typescript
// File: packages/client/src/stores/geometry.ts
// Around line 153 (existing tool definitions)

const camTools = [
  { tool: 'helical', label: 'Helical Ramping', icon: '🌀', route: '/lab/helical' },
  { tool: 'adaptive', label: 'Adaptive Pocketing', icon: '⚡', route: '/lab/adaptive' },
  { tool: 'vcarve', label: 'V-Carve', icon: '🎨', route: '/lab/vcarve' },
  { tool: 'relief', label: 'Relief Mapping', icon: '🗺️', route: '/lab/relief' },
  { tool: 'svg-editor', label: 'SVG Editor', icon: '✏️', route: '/lab/svg-editor' },
  { tool: 'compare-runs', label: 'Multi-Run Comparison', icon: '📊', route: '/lab/compare-runs' }  // 🆕
]
```

**Usage:**
```typescript
import { useGeometryStore } from '@/stores/geometry'

const geometryStore = useGeometryStore()
geometryStore.sendToCAM('compare-runs')  // Routes to /lab/compare-runs
```

---

### **Option 2: Add to Navigation Component**

If you have a sidebar/toolbar navigation component, add direct link:

```vue
<!-- Example: Sidebar.vue or Toolbar.vue -->
<template>
  <nav>
    <!-- Existing links -->
    <router-link to="/lab/pipeline">Pipeline</router-link>
    <router-link to="/lab/risk">Risk Dashboard</router-link>
    
    <!-- New link -->
    <router-link to="/lab/compare-runs">
      <span class="icon">📊</span>
      <span>Multi-Run Comparison</span>
    </router-link>
  </nav>
</template>
```

---

### **Option 3: Add to Preset Hub View**

Add "Compare Selected" button to `packages/client/src/views/PresetHubView.vue`:

```vue
<!-- File: packages/client/src/views/PresetHubView.vue -->
<!-- Add to header action buttons section -->

<button
  v-if="selectedPresets.length >= 2"
  @click="compareSelectedPresets"
  class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
>
  📊 Compare Selected ({{ selectedPresets.length }})
</button>

<script setup lang="ts">
import { useRouter } from 'vue-router'
const router = useRouter()

function compareSelectedPresets() {
  // Store selected preset IDs in localStorage
  localStorage.setItem('multirun.selectedPresets', JSON.stringify(selectedPresets.value))
  
  // Navigate to comparison view
  router.push('/lab/compare-runs')
}
</script>
```

Then update `MultiRunComparisonView.vue` to read from localStorage:

```typescript
// In MultiRunComparisonView.vue onMounted()
const preselectedIds = localStorage.getItem('multirun.selectedPresets')
if (preselectedIds) {
  selectedPresetIds.value = JSON.parse(preselectedIds)
  localStorage.removeItem('multirun.selectedPresets')  // Clear after loading
  
  // Auto-run comparison if 2+ presets
  if (selectedPresetIds.value.length >= 2) {
    await runComparison()
  }
}
```

---

### **Option 4: Add to Art Studio Suite**

If part of Art Studio workflow, add to `packages/client/src/views/art/RiskDashboardCrossLab.vue`:

```typescript
// Around line 1600 (existing lab links)
const labLinks = [
  { path: "/lab/adaptive", label: "Adaptive Pocketing", icon: "⚡" },
  { path: "/lab/relief", label: "Relief Mapping", icon: "🗺️" },
  { path: "/lab/pipeline", label: "Pipeline", icon: "🔄" },
  { path: "/lab/risk-dashboard", label: "Risk Dashboard", icon: "⚠️" },
  { path: "/lab/compare-runs", label: "Multi-Run Comparison", icon: "📊" }  // 🆕
]
```

---

## 🧪 Testing Route Registration

### **Test 1: Direct Navigation**
```typescript
// In browser console or component
import { useRouter } from 'vue-router'
const router = useRouter()
router.push('/lab/compare-runs')
```

**Expected:** MultiRunComparisonView.vue renders, preset selector loads

### **Test 2: Browser URL**
Navigate to: `http://localhost:5173/lab/compare-runs`

**Expected:** Component loads without 404 error

### **Test 3: Navigation Link**
Click navigation link/button you added

**Expected:** Smooth transition to comparison view

---

## 📦 Chart.js Dependency Check

**File:** `packages/client/package.json`

**Check for:**
```json
{
  "dependencies": {
    "chart.js": "^4.0.0"  // or any 4.x version
  }
}
```

**If Missing:**
```bash
cd packages/client
npm install chart.js
# or
yarn add chart.js
```

**Verify Import:**
```typescript
import { Chart, registerables } from 'chart.js'
Chart.register(...registerables)
```

---

## ✅ Verification Checklist

- [ ] Route `/lab/compare-runs` registered in navigation system
- [ ] Chart.js dependency installed (`npm list chart.js`)
- [ ] Component renders without console errors
- [ ] Preset selector loads presets with `job_source_id`
- [ ] Multi-select checkboxes work
- [ ] "Compare Runs" button enabled after 2+ selections
- [ ] Comparison API call succeeds (check Network tab)
- [ ] Summary stats display correctly
- [ ] Trend badges show with correct colors
- [ ] Recommendations panel renders
- [ ] Comparison table shows all runs
- [ ] Best/worst rows highlighted (green/red)
- [ ] Chart.js bar chart renders
- [ ] CSV export downloads file
- [ ] "New Comparison" resets state

---

## 🚀 Recommended Setup Sequence

1. **Install Chart.js** (if missing)
   ```bash
   cd packages/client
   npm install chart.js
   ```

2. **Add to Geometry Store** (Option 1)
   - Enables `sendToCAM('compare-runs')` pattern
   - Consistent with other CAM tools

3. **Add to Preset Hub** (Option 3)
   - "Compare Selected" button for multi-selection workflow
   - Auto-navigates with pre-selected presets

4. **Test Direct Navigation**
   ```typescript
   router.push('/lab/compare-runs')
   ```

5. **Run Backend Test**
   ```powershell
   .\test_multi_run_comparison.ps1
   ```

6. **Run Frontend Checklist** (15 items above)

---

## 🔧 Troubleshooting

### **Issue: Component not found (404)**
**Solution:** Ensure component imported in parent view or lazy-loaded correctly

### **Issue: Chart.js error "Chart is not a constructor"**
**Solution:** 
```bash
npm install chart.js
npm install  # Rebuild dependencies
```

### **Issue: Presets not loading**
**Solution:** Check B19 job lineage tracking - presets need `job_source_id` field

### **Issue: API call fails with 400**
**Solution:** Ensure 2+ preset IDs sent in request body

### **Issue: Chart doesn't render**
**Solution:** 
- Check `timeChartCanvas.value` is not null
- Verify Chart.js registered: `Chart.register(...registerables)`
- Check browser console for Canvas errors

---

## 📚 Related Documentation

- [B21 Multi-Run Comparison Complete](./B21_MULTI_RUN_COMPARISON_COMPLETE.md) - Full feature documentation
- [B19 Clone as Preset](./B19_CLONE_AS_PRESET_INTEGRATION.md) - Job lineage tracking
- [Unified Preset Status](./UNIFIED_PRESET_INTEGRATION_STATUS.md) - Overall progress

---

**Status:** Route registration is the **only remaining task** for B21 completion  
**Estimated Time:** 15-30 minutes (install Chart.js + add navigation link)  
**Recommended:** Option 1 (Geometry Store) + Option 3 (Preset Hub button)
