# Machine Envelope System – Quick Reference

**Status:** ✅ Complete  
**Bundle:** Phase 24.5  
**Components:** CamMachineEnvelopePanel, CamBackplotViewer (updated), BridgeLabView (updated)

---

## 🚀 Quick Start

### **1. Add to Bridge Lab**

```vue
<template>
  <CamMachineEnvelopePanel
    @machine-selected="onMachineSelected"
    @limits-changed="onLimitsChanged"
    @cam-defaults-changed="onCamDefaultsChanged"
  />
  
  <CamBackplotViewer
    :moves="moves"
    :stats="stats"
    :machine-limits="machineLimits"
  />
</template>

<script setup>
const machineLimits = ref(null)

function onLimitsChanged(limits) {
  machineLimits.value = limits
}

function onCamDefaultsChanged(defaults) {
  // Auto-fill your CAM params
  if (defaults?.tool_d) toolD.value = defaults.tool_d
  if (defaults?.stepover) stepover.value = defaults.stepover
}
</script>
```

---

## 📦 Backend Requirements

### **Endpoint: GET `/cam/machines`**

```json
[
  {
    "id": "machine_1",
    "name": "Shapeoko Pro XL",
    "controller": "GRBL",
    "units": "mm",
    "limits": {
      "min_x": 0.0,
      "max_x": 660.0,
      "min_y": 0.0,
      "max_y": 457.0,
      "min_z": -127.0,
      "max_z": 10.0
    },
    "feed_xy": 3000.0,
    "camDefaults": {
      "tool_d": 6.35,
      "stepover": 0.45,
      "stepdown": 2.0,
      "feed_xy": 1200.0,
      "safe_z": 5.0,
      "z_rough": -1.5
    }
  }
]
```

---

## 🎨 Visual Design

### **Backplot Colors**

| Status | Envelope Color | Badge | Meaning |
|--------|---------------|-------|---------|
| ✅ Within | Green (`#22c55e`) | Green dot + "Within envelope" | Toolpath fits |
| ⚠️ Over-travel | Red (`#ef4444`) | Red dot + "Over-travel" | Toolpath exceeds |

### **Overlay Styles**

```
Machine Envelope: Dashed 4-4 stroke (green or red)
Toolpath Bounds:  Dashed 3-3 stroke (gray)
```

---

## 🔧 Event Handlers

### **machine-selected**
```typescript
function onMachineSelected(machine: Machine | null) {
  console.log('Selected machine:', machine?.name)
}
```

### **limits-changed**
```typescript
function onLimitsChanged(limits: MachineLimits | null) {
  // Pass to backplot viewer
  machineLimits.value = limits
}
```

### **cam-defaults-changed**
```typescript
function onCamDefaultsChanged(defaults: MachineCamDefaults | null) {
  if (!defaults) return
  
  // Auto-fill adaptive params
  toolD.value = defaults.tool_d ?? 6.0
  stepover.value = defaults.stepover ?? 0.45
  stepdown.value = defaults.stepdown ?? 2.0
  feedXY.value = defaults.feed_xy ?? 1200
  safeZ.value = defaults.safe_z ?? 5.0
  zRough.value = defaults.z_rough ?? -1.5
}
```

---

## 📐 TypeScript Interfaces

```typescript
interface MachineLimits {
  min_x?: number | null
  max_x?: number | null
  min_y?: number | null
  max_y?: number | null
  min_z?: number | null
  max_z?: number | null
}

interface MachineCamDefaults {
  tool_d?: number | null
  stepover?: number | null       // 0.45 = 45%
  stepdown?: number | null
  feed_xy?: number | null
  safe_z?: number | null
  z_rough?: number | null
}

interface Machine {
  id: string
  name: string
  controller?: string | null
  units?: 'mm' | 'inch' | string | null
  limits?: MachineLimits | null
  feed_xy?: number | null
  camDefaults?: MachineCamDefaults | null
}
```

---

## 🐛 Common Issues

### **Machine dropdown empty**
- Check `/cam/machines` returns JSON array
- Verify backend serving endpoint

### **CAM defaults not auto-filling**
- Ensure `camDefaults` object in machine JSON
- Check event handler wired in parent component

### **Over-travel false positive**
- Verify units match (mm vs inch)
- Check all 4 limits (min_x, max_x, min_y, max_y) non-null

---

## 📊 File Locations

```
packages/client/src/
├── components/
│   ├── CamMachineEnvelopePanel.vue  (NEW - 176 lines)
│   └── CamBackplotViewer.vue        (UPDATED - +40 lines)
└── views/
    └── BridgeLabView.vue            (UPDATED - +65 lines)
```

---

## 🎯 Integration Checklist

- [x] CamMachineEnvelopePanel component created
- [x] CamBackplotViewer updated with machineLimits prop
- [x] BridgeLabView wired with event handlers
- [x] Auto-fill CAM params from machine defaults
- [x] Over-travel detection implemented
- [x] Status badge (green/red) rendering

---

## 📚 See Also

- [PHASE_24_5_MACHINE_ENVELOPE_INTEGRATION.md](./PHASE_24_5_MACHINE_ENVELOPE_INTEGRATION.md) - Full documentation
- [CAM_BRIDGE_PREFLIGHT_COMPLETE.md](./CAM_BRIDGE_PREFLIGHT_COMPLETE.md) - DXF validation
- [DXF_ADAPTIVE_ROUTER_INTEGRATION.md](./DXF_ADAPTIVE_ROUTER_INTEGRATION.md) - Adaptive toolpath

---

**Quick Tip:** For testing without backend, mock `/cam/machines` response:
```typescript
const mockMachines = [
  {
    id: 'test_1',
    name: 'Test Machine',
    controller: 'GRBL',
    units: 'mm',
    limits: { min_x: 0, max_x: 600, min_y: 0, max_y: 400, min_z: -100, max_z: 10 },
    camDefaults: { tool_d: 6, stepover: 0.45, stepdown: 2, feed_xy: 1200 }
  }
]
```
