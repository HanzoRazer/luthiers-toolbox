# Patch W: Quick Reference Guide

**Purpose:** Design → CAM Workflow Enhancement  
**Status:** ✅ Core files created, manual integration pending  
**Files:** 4 new files (geometry store, toolbar, composable, docs)

---

## 🚀 Quick Start (5 Minutes)

### **Step 1: Install Pinia**
```powershell
cd packages/client
npm install pinia
```

### **Step 2: Register Pinia Store**
**File:** `packages/client/src/main.ts`

```typescript
import { createPinia } from 'pinia'  // ADD THIS

const pinia = createPinia()          // ADD THIS
app.use(pinia)                       // ADD THIS BEFORE app.mount()
```

### **Step 3: Add Geometry Toolbar**
**File:** `client/src/App.vue`

```vue
<script setup lang="ts">
import GeometryToolbar from '../packages/client/src/components/GeometryToolbar.vue'  // ADD THIS
</script>

<template>
  <div class="app">
    <!-- ... existing content ... -->
    <GeometryToolbar />  <!-- ADD THIS BEFORE </div> -->
  </div>
</template>
```

### **Step 4: Test Workflow**
```powershell
# Terminal 1: API
cd services/api
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000

# Terminal 2: Client
cd packages/client
npm run dev

# Browser: http://localhost:5173
# 1. Open Bridge Calculator
# 2. Generate bridge
# 3. Click "Send to CAM" (after adding button)
# 4. Verify toolbar appears
# 5. Click "Send to CAM" → "Helical Ramping"
# 6. Verify geometry loaded
```

---

## 📝 Add "Send to CAM" to Design Tools

**Template for any design tool:**

```vue
<script setup lang="ts">
import { useCAMIntegration, convertToGeometryData } from '@/composables/useCAMIntegration'

const { sendToGeometryStore } = useCAMIntegration({
  toolName: 'YourToolName'  // e.g., 'BridgeCalculator'
})

function sendToCAM() {
  if (!yourGeometryData.value) {
    alert('Generate geometry first')
    return
  }
  
  const geometry = convertToGeometryData(
    yourPaths.value,         // Array of paths or polylines
    currentUnits.value,      // 'mm' or 'inch'
    'YourToolName'
  )
  
  sendToGeometryStore(geometry)
  alert('✅ Geometry loaded! Use toolbar to send to CAM.')
}
</script>

<template>
  <button @click="sendToCAM" class="btn-cam">
    🔧 Send to CAM
  </button>
</template>

<style scoped>
.btn-cam {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
}
</style>
```

---

## 🔧 Update CAM Tools to Receive Geometry

**Template for CAM tools:**

```vue
<script setup lang="ts">
import { useCAMIntegration } from '@/composables/useCAMIntegration'

const { pendingGeometry, receivePendingGeometry } = useCAMIntegration({
  autoReceive: true
})

onMounted(() => {
  const received = receivePendingGeometry()
  if (received) {
    console.log('📐 Received:', received.metadata?.source)
    
    // Auto-populate your form fields from received.paths
    // Example: Extract center point from first path
    if (received.paths[0]?.cx !== undefined) {
      centerX.value = received.paths[0].cx
      centerY.value = received.paths[0].cy
    }
  }
})
</script>

<template>
  <div v-if="pendingGeometry" class="received-banner">
    ✅ Geometry from {{ pendingGeometry.metadata?.source }}
  </div>
</template>

<style scoped>
.received-banner {
  background: #d1fae5;
  color: #065f46;
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 16px;
}
</style>
```

---

## 📊 What You Get

### **Geometry Store Features**
- ✅ Centralized geometry state (Pinia)
- ✅ Copy/paste to clipboard (JSON)
- ✅ History (last 10 designs)
- ✅ Bounding box auto-calculation
- ✅ SessionStorage persistence
- ✅ Custom events for real-time sync

### **Geometry Toolbar Features**
- ✅ Floating bottom-right widget
- ✅ "Send to CAM" dropdown (5 tools)
- ✅ Copy to clipboard button
- ✅ DXF export button
- ✅ Clear geometry button
- ✅ Status messages (success/error)

### **CAM Integration Composable**
- ✅ Reusable hooks for all tools
- ✅ Auto-receive on mount
- ✅ Format conversion utilities
- ✅ Event listeners for updates

---

## 🎯 Supported Workflows

| Design Tool | → | CAM Tool | Use Case |
|-------------|---|----------|----------|
| Bridge Calculator | → | Helical Ramping | Pocket entry for bridge saddle |
| Rosette Designer | → | Adaptive Pocketing | Multi-ring rosette clearing |
| Archtop Calculator | → | Relief Mapping | 3D carving toolpaths |
| Neck Generator | → | V-Carve | Truss rod channel |
| Hardware Layout | → | SVG Editor | Cavity trace editing |

---

## 🐛 Troubleshooting

**Q: Geometry Toolbar not showing?**  
A: Check:
1. Pinia registered in `main.ts`?
2. `<GeometryToolbar />` in `App.vue`?
3. Called `sendToGeometryStore()` from design tool?

**Q: "Cannot find module 'pinia'"?**  
A: Run `npm install pinia` in `packages/client`

**Q: CAM tool not receiving geometry?**  
A: Check browser console for `"Received geometry from: ..."` message. Verify `receivePendingCAMGeometry()` called in `onMounted()`.

---

## 📚 Full Documentation

See **PATCH_W_DESIGN_CAM_WORKFLOW.md** for:
- Complete API reference
- User workflow examples
- Technical architecture diagrams
- Testing checklist
- Rollout plan (4 phases)

---

## ✅ Checklist

**Installation:**
- [ ] Pinia installed (`npm install pinia`)
- [ ] Pinia registered in `main.ts`
- [ ] GeometryToolbar in `App.vue`

**Design Tools (Add "Send to CAM" button):**
- [ ] BridgeCalculator.vue
- [ ] RosetteDesigner.vue
- [ ] LesPaulNeckGenerator.vue
- [ ] ArchtopCalculator.vue
- [ ] EnhancedRadiusDish.vue
- [ ] HardwareLayout.vue

**CAM Tools (Add geometry receiver):**
- [ ] HelicalRampLab.vue (v16.1)
- [ ] AdaptivePocketLab.vue (Module L)
- [ ] ArtStudioV16.vue (v16.0)

**Testing:**
- [ ] Bridge → Helical workflow
- [ ] Rosette → Adaptive workflow
- [ ] Clipboard copy/paste
- [ ] History navigation

---

**Status:** ✅ Ready for integration  
**Next:** Run `.\integrate_patch_w.ps1` or follow manual steps  
**Est. Time:** 15-30 minutes for full integration
