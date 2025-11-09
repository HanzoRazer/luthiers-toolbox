# Patch W: Design → CAM Workflow Enhancement

**Status:** 🔄 In Progress  
**Date:** November 7, 2025  
**Purpose:** Bridge toolbox design tools with Art Studio CAM features for seamless geometry handoff

---

## 🎯 Overview

**Patch W** introduces a **unified geometry workflow system** that connects the 18 Luthier's Toolbox design calculators with Art Studio CAM tools. This enables one-click design → CAM workflows without manual DXF export/import cycles.

### **Key Features**

1. ✅ **Pinia Geometry Store** - Centralized geometry state management
2. ✅ **Geometry Toolbar** - Floating toolbar with "Send to CAM" actions
3. ✅ **CAM Integration Composable** - Reusable hooks for design tools
4. ✅ **Clipboard Support** - Copy/paste geometry JSON between tools
5. ✅ **Session Storage Handoff** - Persist geometry across route changes
6. ✅ **Multi-CAM Target Support** - Send to Helical, Adaptive, V-Carve, Relief, SVG Editor

---

## 📦 Files Created (4 New Files)

### **1. Geometry Store** (`packages/client/src/stores/geometry.ts`)
**Purpose:** Centralized state management for geometry data  
**Size:** ~350 lines  

**Key Interfaces:**
```typescript
interface GeometryData {
  units: 'mm' | 'inch'
  paths: GeometryPath[]
  metadata?: {
    source?: string         // e.g., 'BridgeCalculator'
    timestamp?: string
    boundingBox?: { minX, minY, maxX, maxY }
  }
}

interface CAMTarget {
  tool: 'helical' | 'adaptive' | 'vcarve' | 'relief' | 'svg-editor'
  label: string
  icon: string
  route: string
}
```

**Key Functions:**
- `setGeometry(geometry)` - Store geometry from design tool
- `sendToCAM(tool)` - Send to specific CAM target
- `copyToClipboard()` - Copy geometry JSON
- `pasteFromClipboard()` - Import geometry JSON
- `receivePendingCAMGeometry()` - Retrieve geometry sent to CAM tool

**State Management:**
- `currentGeometry` - Active geometry
- `geometryHistory` - Last 10 geometries (undo/redo support)
- `camTargets` - Available CAM tools

**Computed Properties:**
- `hasGeometry` - Boolean check
- `geometrySummary` - Width/height/path count
- `boundingBox` - Auto-calculated min/max bounds

---

### **2. Geometry Toolbar** (`packages/client/src/components/GeometryToolbar.vue`)
**Purpose:** Floating toolbar for geometry actions  
**Size:** ~250 lines  

**UI Components:**
- **Geometry Info Panel** - Source, path count, dimensions
- **Copy Button** - Copy to clipboard (📋)
- **Send to CAM Dropdown** - 5 CAM tool targets (🔧)
- **DXF Export Button** - Direct DXF export (📄)
- **Clear Button** - Remove geometry (✕)
- **Status Messages** - Success/error feedback

**Features:**
- **Auto-show/hide** - Only visible when `hasGeometry === true`
- **Fixed positioning** - Bottom-right corner (z-index: 1000)
- **Responsive** - Adapts to viewport width
- **Toast notifications** - 3-second auto-dismiss

**Integration:**
```vue
<!-- Add to main App.vue layout -->
<template>
  <div class="app">
    <!-- ... existing nav and content ... -->
    <GeometryToolbar />  <!-- Floats over all views -->
  </div>
</template>
```

---

### **3. CAM Integration Composable** (`packages/client/src/composables/useCAMIntegration.ts`)
**Purpose:** Reusable hook for design tools  
**Size:** ~150 lines  

**Usage in Design Tools:**
```typescript
// In BridgeCalculator.vue, RosetteDesigner.vue, etc.
import { useCAMIntegration, convertToGeometryData } from '@/composables/useCAMIntegration'

const { sendToGeometryStore, sendToCAMTool } = useCAMIntegration({
  toolName: 'BridgeCalculator'
})

function exportToCAM() {
  const geometry = convertToGeometryData(
    bridgePaths.value,  // Your design tool's path data
    'mm',               // Units
    'BridgeCalculator'  // Source name
  )
  
  sendToGeometryStore(geometry)
  // Geometry Toolbar now shows "Send to CAM" button
}

function quickSendToHelical() {
  const geometry = convertToGeometryData(bridgePaths.value, 'mm')
  sendToCAMTool(geometry, 'helical', 'BridgeCalculator')
  // Auto-navigates to /lab/helical with geometry loaded
}
```

**Usage in CAM Tools:**
```typescript
// In HelicalRampLab.vue, AdaptivePocketLab.vue, etc.
import { useCAMIntegration } from '@/composables/useCAMIntegration'

const { pendingGeometry, receivePendingGeometry } = useCAMIntegration({
  autoReceive: true  // Auto-load geometry on mount
})

onMounted(() => {
  if (pendingGeometry.value) {
    // Pre-populate form with received geometry
    centerX.value = calculateCenter(pendingGeometry.value).x
    centerY.value = calculateCenter(pendingGeometry.value).y
  }
})
```

**Helper Functions:**
- `convertToGeometryData()` - Convert design tool formats to standard GeometryData
- `geometryUpdateHandler` - Event listener for real-time updates
- `geometryClearedHandler` - Cleanup on geometry clear

---

### **4. Documentation** (`PATCH_W_DESIGN_CAM_WORKFLOW.md`)
**This file** - Comprehensive integration guide

---

## 🔌 Integration Steps

### **Step 1: Install Pinia** (if not already installed)
```bash
cd packages/client
npm install pinia
```

### **Step 2: Register Pinia Store**
**File:** `packages/client/src/main.ts`

```typescript
import { createApp } from 'vue'
import { createPinia } from 'pinia'  // ADD THIS
import App from './App.vue'

const app = createApp(App)
const pinia = createPinia()          // ADD THIS

app.use(pinia)                       // ADD THIS
app.mount('#app')
```

### **Step 3: Add Geometry Toolbar to App.vue**
**File:** `client/src/App.vue`

```vue
<script setup lang="ts">
import { ref } from 'vue'
// ... existing imports ...
import GeometryToolbar from '../packages/client/src/components/GeometryToolbar.vue'  // ADD THIS
</script>

<template>
  <div class="app">
    <header>...</header>
    <nav>...</nav>
    <main>...</main>
    <footer>...</footer>
    
    <!-- ADD THIS: Floating geometry toolbar -->
    <GeometryToolbar />
  </div>
</template>
```

### **Step 4: Add "Send to CAM" Button to Design Tools**

**Example: BridgeCalculator.vue**

```vue
<script setup lang="ts">
import { useCAMIntegration, convertToGeometryData } from '@/composables/useCAMIntegration'

// ... existing code ...

const { sendToGeometryStore } = useCAMIntegration({
  toolName: 'BridgeCalculator'
})

// Add new function
function sendToCAM() {
  if (!saddlePoints.value || saddlePoints.value.length === 0) {
    alert('Generate bridge geometry first')
    return
  }
  
  const geometry = convertToGeometryData(
    [saddlePoints.value],  // Bridge outline path
    currentUnits.value,    // 'mm' or 'inch'
    'BridgeCalculator'
  )
  
  sendToGeometryStore(geometry)
  alert('Geometry loaded! Click "Send to CAM" in the toolbar below.')
}
</script>

<template>
  <div class="bridge-calculator">
    <!-- ... existing form ... -->
    
    <div class="export-actions">
      <button @click="exportDXF">📄 Export DXF</button>
      <button @click="exportJSON">📋 Export JSON</button>
      <button @click="sendToCAM" class="btn-cam">🔧 Send to CAM</button>  <!-- NEW -->
    </div>
  </div>
</template>

<style scoped>
.btn-cam {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-weight: 600;
}
</style>
```

**Repeat for:**
- RosetteDesigner.vue
- HardwareLayout.vue
- LesPaulNeckGenerator.vue
- ArchtopCalculator.vue
- EnhancedRadiusDish.vue
- FretboardCompoundRadius.vue
- BracingCalculator.vue (if geometry-based)

### **Step 5: Update CAM Tools to Receive Geometry**

**Example: HelicalRampLab.vue**

```vue
<script setup lang="ts">
import { useCAMIntegration } from '@/composables/useCAMIntegration'

// ... existing code ...

const { pendingGeometry, receivePendingGeometry } = useCAMIntegration({
  autoReceive: true
})

onMounted(() => {
  // Check for pending geometry from design tools
  const received = receivePendingGeometry()
  if (received) {
    console.log('Received geometry from:', received.metadata?.source)
    
    // Auto-populate form with received geometry
    if (received.paths.length > 0) {
      const firstPath = received.paths[0]
      
      // Extract center from circular/arc geometry
      if (firstPath.cx !== undefined && firstPath.cy !== undefined) {
        cx.value = firstPath.cx
        cy.value = firstPath.cy
        radius.value = firstPath.r || 10
      }
      
      // Or calculate center from polyline bounds
      else if (firstPath.points) {
        const bounds = calculateBounds(firstPath.points)
        cx.value = (bounds.minX + bounds.maxX) / 2
        cy.value = (bounds.minY + bounds.maxY) / 2
        radius.value = Math.min(
          (bounds.maxX - bounds.minX) / 4,
          (bounds.maxY - bounds.minY) / 4
        )
      }
    }
    
    alert(`Geometry loaded from ${received.metadata?.source}!`)
  }
})

function calculateBounds(points: number[][]) {
  const xs = points.map(p => p[0])
  const ys = points.map(p => p[1])
  return {
    minX: Math.min(...xs),
    maxX: Math.max(...xs),
    minY: Math.min(...ys),
    maxY: Math.max(...ys)
  }
}
</script>

<template>
  <div class="helical-ramp-lab">
    <!-- Show received geometry info -->
    <div v-if="pendingGeometry" class="received-geometry-banner">
      ✅ Geometry received from <strong>{{ pendingGeometry.metadata?.source }}</strong>
      <button @click="pendingGeometry = null">✕ Clear</button>
    </div>
    
    <!-- ... existing form ... -->
  </div>
</template>

<style scoped>
.received-geometry-banner {
  background: #d1fae5;
  color: #065f46;
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
```

**Repeat for:**
- AdaptivePocketLab.vue (Module L)
- ArtStudioPhase15_5.vue (v15.5 Post-processor)
- ArtStudioV16.vue (v16.0 SVG Editor + Relief)

---

## 🎨 User Workflow Examples

### **Example 1: Bridge Calculator → Helical Ramping**

**User Actions:**
1. Open **Bridge Calculator** (`🌉 Bridge`)
2. Configure: family=Steel String, scale=25.4", compensation=1.6mm
3. Click **"Generate Bridge"** → See saddle positions
4. Click **"🔧 Send to CAM"** → Geometry Toolbar appears bottom-right
5. Click **"🔧 Send to CAM ▼"** → Dropdown shows 5 CAM tools
6. Click **"🌀 Helical Ramping"** → Auto-navigate to HelicalRampLab
7. Form auto-populates: CX/CY from bridge center, radius from width/4
8. Adjust Z params, pitch, feeds → Click **"Generate Helical Entry"**
9. Download G-code with GRBL/Mach4/LinuxCNC headers

**Time Saved:** 2 minutes (no DXF export/import, no manual coordinate entry)

---

### **Example 2: Rosette Designer → Adaptive Pocketing**

**User Actions:**
1. Open **Rosette Designer** (`🌹 Rosette`)
2. Configure: rings=5, pattern=Herringbone, outer diameter=100mm
3. Click **"Generate Rosette"** → See pattern preview
4. Click **"🔧 Send to CAM"**
5. Toolbar: Click **"🔧 Send to CAM ▼"** → **"⚡ Adaptive Pocketing"**
6. AdaptivePocketLab opens with rosette geometry as boundary loop
7. Configure: tool=6mm, stepover=45%, strategy=Spiral
8. Click **"Generate Toolpath"** → See offset rings
9. Export multi-post bundle (GRBL + Mach4 + LinuxCNC G-code)

**Time Saved:** 5 minutes (complex geometry, island handling automatic)

---

### **Example 3: Archtop Calculator → Relief Mapping**

**User Actions:**
1. Open **Archtop Calculator** (`🎻 Archtop`)
2. Configure: top radius=20ft, back radius=15ft, dimensions
3. Click **"Calculate Carving"** → See SVG preview
4. Click **"🔧 Send to CAM"** → **"🗺️ Relief Mapping"**
5. Relief Mapper opens with archtop profile as height map
6. Configure: Z range=-10mm to 0mm, mesh resolution=1mm
7. Generate 3D toolpath with climb milling
8. Export with PathPilot post-processor for Tormach mill

**Time Saved:** 10 minutes (3D geometry, no manual mesh creation)

---

## 📊 Technical Architecture

### **Data Flow Diagram**

```
┌─────────────────────────────────────────────────────────────┐
│              Design Tools (18 components)                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │ Bridge   │ │ Rosette  │ │ Archtop  │ │ Neck Gen │ ...  │
│  │ Calc     │ │ Designer │ │ Calc     │ │          │      │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘      │
│       │            │            │            │              │
│       └────────────┴────────────┴────────────┘              │
│                    │                                        │
│                    ▼                                        │
│         useCAMIntegration() composable                      │
│                    │                                        │
│                    ▼                                        │
│         convertToGeometryData()                             │
│                    │                                        │
│                    ▼                                        │
└────────────────────┼────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                Pinia Geometry Store                         │
│  ┌──────────────────────────────────────────────────┐      │
│  │  State:                                          │      │
│  │  - currentGeometry: GeometryData | null          │      │
│  │  - geometryHistory: GeometryData[]               │      │
│  │                                                   │      │
│  │  Actions:                                        │      │
│  │  - setGeometry(geometry)                         │      │
│  │  - sendToCAM(tool)                               │      │
│  │  - copyToClipboard()                             │      │
│  │  - receivePendingCAMGeometry()                   │      │
│  └──────────────────────────────────────────────────┘      │
│                    │                                        │
└────────────────────┼────────────────────────────────────────┘
                     │
      ┌──────────────┼──────────────┐
      │              │              │
      ▼              ▼              ▼
┌──────────┐  ┌──────────┐  ┌──────────┐
│ Geometry │  │ Session  │  │ Custom   │
│ Toolbar  │  │ Storage  │  │ Events   │
│ (Vue)    │  │ (Browser)│  │ (Window) │
└────┬─────┘  └────┬─────┘  └────┬─────┘
     │            │            │
     └────────────┴────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│              CAM Tools (Art Studio)                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │ Helical  │ │ Adaptive │ │ V-Carve  │ │ Relief   │ ...  │
│  │ Ramp     │ │ Pocket   │ │          │ │ Mapper   │      │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘      │
│       │            │            │            │              │
│       └────────────┴────────────┴────────────┘              │
│                    │                                        │
│                    ▼                                        │
│         receivePendingCAMGeometry()                         │
│                    │                                        │
│                    ▼                                        │
│         Auto-populate form inputs                           │
│                    │                                        │
│                    ▼                                        │
│         Generate G-code with post-processors                │
└─────────────────────────────────────────────────────────────┘
```

---

## 🧪 Testing Checklist

### **Unit Tests** (Future)
- [ ] Geometry store state mutations
- [ ] Clipboard copy/paste operations
- [ ] SessionStorage persistence
- [ ] Geometry format conversion
- [ ] Bounding box calculations

### **Integration Tests**
- [ ] Bridge Calculator → Helical workflow
- [ ] Rosette Designer → Adaptive Pocket workflow
- [ ] Archtop Calculator → Relief Mapper workflow
- [ ] Clipboard export → Manual paste → Import
- [ ] History navigation (undo/redo)

### **Manual Testing**
```powershell
# Terminal 1: Start API
cd services/api
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000

# Terminal 2: Start client
cd packages/client
npm install pinia  # First time only
npm run dev

# Browser: http://localhost:5173
# 1. Open Bridge Calculator
# 2. Generate bridge → Click "Send to CAM"
# 3. Verify Geometry Toolbar appears
# 4. Click "Send to CAM" → "Helical Ramping"
# 5. Verify HelicalRampLab opens with geometry
# 6. Verify CX/CY auto-populated
# 7. Generate G-code → Download → Verify valid
```

---

## 🚀 Rollout Plan

### **Phase 1: Foundation** (Week 1)
- [x] Create Pinia geometry store
- [x] Create GeometryToolbar component
- [x] Create useCAMIntegration composable
- [ ] Install Pinia in client
- [ ] Register store in main.ts
- [ ] Add GeometryToolbar to App.vue

### **Phase 2: Design Tool Integration** (Week 2)
- [ ] Add "Send to CAM" to BridgeCalculator
- [ ] Add "Send to CAM" to RosetteDesigner
- [ ] Add "Send to CAM" to LesPaulNeckGenerator
- [ ] Add "Send to CAM" to ArchtopCalculator
- [ ] Add "Send to CAM" to EnhancedRadiusDish
- [ ] Add "Send to CAM" to HardwareLayout

### **Phase 3: CAM Tool Integration** (Week 3)
- [ ] Update HelicalRampLab to receive geometry (v16.1)
- [ ] Update AdaptivePocketLab to receive geometry (Module L)
- [ ] Update ArtStudioV16 (SVG Editor + Relief Mapper)
- [ ] Update ArtStudioPhase15_5 (Post-processor)

### **Phase 4: Polish & Documentation** (Week 4)
- [ ] Add keyboard shortcuts (Ctrl+Shift+C = copy, Ctrl+Shift+V = paste)
- [ ] Add geometry history UI (sidebar with last 10 designs)
- [ ] Add geometry validation (check closed paths, units)
- [ ] Update user documentation with workflow examples
- [ ] Create video tutorial (Bridge → Helical → G-code)

---

## 📚 API Reference

### **Geometry Store API**

```typescript
// Import
import { useGeometryStore } from '@/stores/geometry'

// Usage
const store = useGeometryStore()

// State
store.currentGeometry      // GeometryData | null
store.geometryHistory      // GeometryData[]
store.camTargets           // CAMTarget[]

// Computed
store.hasGeometry          // boolean
store.geometrySource       // string
store.geometryUnits        // 'mm' | 'inch'
store.pathCount            // number
store.boundingBox          // { minX, minY, maxX, maxY } | null
store.geometrySummary      // { source, units, pathCount, width, height } | null

// Actions
store.setGeometry(geometry: GeometryData)
store.clearGeometry()
store.loadFromHistory(index: number)
store.exportToJSON(): string
store.importFromJSON(json: string): boolean
store.copyToClipboard(): Promise<boolean>
store.pasteFromClipboard(): Promise<boolean>
store.sendToCAM(tool: CAMTarget['tool'])
store.receivePendingCAMGeometry(): GeometryData | null
```

### **CAM Integration Composable API**

```typescript
// Import
import { useCAMIntegration, convertToGeometryData } from '@/composables/useCAMIntegration'

// Usage in Design Tools
const { sendToGeometryStore, sendToCAMTool, geometryStore } = useCAMIntegration({
  toolName: 'BridgeCalculator'
})

sendToGeometryStore(geometry: GeometryData, source?: string)
sendToCAMTool(geometry: GeometryData, tool: CAMTarget['tool'], source?: string)

// Usage in CAM Tools
const { pendingGeometry, receivePendingGeometry } = useCAMIntegration({
  autoReceive: true
})

receivePendingGeometry(): GeometryData | null

// Utility
const geometry = convertToGeometryData(
  paths: any[],
  units: 'mm' | 'inch' = 'mm',
  source?: string
): GeometryData
```

---

## 🐛 Troubleshooting

### **Issue:** "Module not found: pinia"
**Solution:**
```bash
cd packages/client
npm install pinia
```

### **Issue:** Geometry Toolbar not showing
**Checklist:**
1. ✅ Pinia registered in `main.ts`?
2. ✅ `<GeometryToolbar />` added to `App.vue`?
3. ✅ `hasGeometry === true` (call `setGeometry()` first)?
4. ✅ Check browser console for errors

### **Issue:** "Send to CAM" not navigating
**Solution:** Verify Vue Router is installed and routes exist:
```typescript
// Check router config has CAM tool routes
const routes = [
  { path: '/lab/helical', component: HelicalRampLab },
  { path: '/lab/adaptive', component: AdaptivePocketLab },
  // ...
]
```

### **Issue:** CAM tool not receiving geometry
**Checklist:**
1. ✅ Called `sendToCAM()` before navigation?
2. ✅ CAM tool has `receivePendingCAMGeometry()` in `onMounted()`?
3. ✅ Check `sessionStorage.getItem('pending_cam_geometry')` in browser DevTools
4. ✅ Check browser console for `"Received geometry from: BridgeCalculator"`

---

## 📈 Success Metrics

### **Target Improvements**
| Metric | Before Patch W | After Patch W | Improvement |
|--------|----------------|---------------|-------------|
| Design → CAM workflow | 3-5 min (manual) | 30 sec (one-click) | **80% faster** |
| Geometry export steps | 5 steps | 2 clicks | **60% fewer** |
| User errors (wrong units) | ~15% | <2% | **87% reduction** |
| CAM form pre-fill | 0% | 80% | **80% automation** |
| Workflow documentation | 2 pages | Tutorial + tooltips | **Better UX** |

### **User Satisfaction Goals**
- ⭐⭐⭐⭐⭐ "Geometry handoff is seamless!"
- ⭐⭐⭐⭐⭐ "No more manual coordinate entry!"
- ⭐⭐⭐⭐⭐ "Design → G-code in under 2 minutes!"

---

## 🎯 Next Steps

1. **Install Pinia** (`npm install pinia`)
2. **Register store** in `main.ts`
3. **Add GeometryToolbar** to `App.vue`
4. **Test workflow** (Bridge → Helical)
5. **Add to remaining design tools** (Rosette, Neck, etc.)
6. **Update CAM tools** to receive geometry
7. **Create user tutorial** (video + docs)

---

## 📋 Related Documentation

- [Art Studio v16.1 Integration](./ART_STUDIO_V16_1_HELICAL_INTEGRATION.md) - Helical ramping CAM tool
- [Art Studio v16.0 Integration](./ART_STUDIO_V16_0_INTEGRATION_COMPLETE.md) - SVG Editor + Relief Mapper
- [Module L: Adaptive Pocketing](./ADAPTIVE_POCKETING_MODULE_L.md) - L.1-L.3 features
- [A_N Build Roadmap](./A_N_BUILD_ROADMAP.md) - Strategic plan for Alpha Nightingale
- [Integration Complete v7](./INTEGRATION_COMPLETE_V7.md) - 18 toolbox design tools

---

**Status:** ✅ Patch W Core Files Created  
**Next Action:** Install Pinia and integrate into App.vue  
**Ready for:** Phase 1 rollout (foundation setup)
