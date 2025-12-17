# CurveLab Enhancement Quick Reference

## 🎯 Objective
Add DXF export buttons and bi-arc overlay visualization to CurveLab.vue

---

## 📝 Implementation Checklist

### Step 1: Add Imports
```typescript
// At top of <script setup>
import { downloadOffsetDXF, downloadBiarcDXF } from '@/utils/curvemath_dxf'
import { biarcEntitiesTS } from '@/utils/curvemath'
```

### Step 2: Add Reactive State
```typescript
// Add near other refs
const showBiarcOverlay = ref(false)
const lastBiarcEntities = ref<BiarcEntity[]>([])
```

### Step 3: Add Export Handlers
```typescript
async function exportDXFPolyline() {
  if (pts.value.length < 2) {
    alert('Need at least 2 points to export')
    return
  }
  
  try {
    const points: [number, number][] = pts.value.map(p => [p.x, p.y])
    await downloadOffsetDXF(points, 'CURVE')
  } catch (err) {
    console.error('DXF export failed:', err)
    alert('Export failed. Check console for details.')
  }
}

async function exportDXFBiarc() {
  if (!cPick.value || !cPick.value.p0 || !cPick.value.t0 || !cPick.value.p1 || !cPick.value.t1) {
    alert('Pick a clothoid/bi-arc first')
    return
  }
  
  try {
    await downloadBiarcDXF(
      cPick.value.p0,
      cPick.value.t0,
      cPick.value.p1,
      cPick.value.t1,
      'ARC'
    )
  } catch (err) {
    console.error('Bi-arc DXF export failed:', err)
    alert('Export failed. Check console for details.')
  }
}
```

### Step 4: Compute Bi-arc When Clothoid Picked
```typescript
// In function that handles clothoid picking (wherever cPick.value is set)
watch(cPick, (newPick) => {
  if (newPick && newPick.p0 && newPick.t0 && newPick.p1 && newPick.t1) {
    lastBiarcEntities.value = biarcEntitiesTS(
      newPick.p0,
      newPick.t0,
      newPick.p1,
      newPick.t1
    )
  } else {
    lastBiarcEntities.value = []
  }
})
```

### Step 5: Add UI Controls (Template)
```vue
<template>
  <!-- Existing controls... -->
  
  <!-- DXF Export Section -->
  <div class="dxf-export-section">
    <h3>DXF Export</h3>
    <div class="button-group">
      <button 
        @click="exportDXFPolyline" 
        :disabled="pts.length < 2"
        class="export-btn"
      >
        📄 Export Polyline DXF
      </button>
      
      <button 
        @click="exportDXFBiarc"
        :disabled="!cPick"
        class="export-btn"
      >
        🔄 Export Bi-arc DXF
      </button>
    </div>
  </div>
  
  <!-- Overlay Toggle -->
  <div class="overlay-controls">
    <label class="checkbox-label">
      <input 
        type="checkbox" 
        v-model="showBiarcOverlay"
      />
      Show bi-arc centers (R=...)
    </label>
  </div>
</template>
```

### Step 6: Add Overlay Rendering (Canvas Draw Function)
```typescript
// In your canvas draw/render function, after drawing the main curve:

if (showBiarcOverlay.value && lastBiarcEntities.value.length > 0) {
  for (const entity of lastBiarcEntities.value) {
    if (entity.type === 'arc') {
      // Save current style
      const prevFill = ctx.fillStyle
      const prevStroke = ctx.strokeStyle
      
      // Draw center dot (green)
      ctx.fillStyle = '#00ff00'
      ctx.beginPath()
      ctx.arc(entity.center[0], entity.center[1], 3, 0, 2 * Math.PI)
      ctx.fill()
      
      // Draw R= label
      ctx.font = '12px monospace'
      ctx.fillText(
        `R=${entity.radius.toFixed(1)}mm`,
        entity.center[0] + 5,
        entity.center[1] - 5
      )
      
      // Draw radius line (center → arc start)
      ctx.strokeStyle = 'rgba(0, 255, 0, 0.5)'  // 50% opacity
      ctx.lineWidth = 1
      ctx.beginPath()
      ctx.moveTo(entity.center[0], entity.center[1])
      
      // Calculate arc start point
      const a0 = (entity.start_angle * Math.PI) / 180
      const arcStartX = entity.center[0] + entity.radius * Math.cos(a0)
      const arcStartY = entity.center[1] + entity.radius * Math.sin(a0)
      ctx.lineTo(arcStartX, arcStartY)
      ctx.stroke()
      
      // Restore style
      ctx.fillStyle = prevFill
      ctx.strokeStyle = prevStroke
    }
  }
}
```

### Step 7: Add Styling (Scoped CSS)
```vue
<style scoped>
.dxf-export-section {
  margin: 1rem 0;
  padding: 1rem;
  border: 1px solid #ccc;
  border-radius: 4px;
}

.dxf-export-section h3 {
  margin-top: 0;
  font-size: 1rem;
  font-weight: 600;
}

.button-group {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.export-btn {
  padding: 0.5rem 1rem;
  background: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
}

.export-btn:hover:not(:disabled) {
  background: #45a049;
}

.export-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.overlay-controls {
  margin: 0.5rem 0;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  user-select: none;
}

.checkbox-label input[type="checkbox"] {
  cursor: pointer;
  width: 16px;
  height: 16px;
}
</style>
```

---

## 🧪 Testing Steps

### 1. Test Polyline Export
1. Draw a curve with 5-10 points in CurveLab
2. Click "Export Polyline DXF"
3. Verify file downloads as `polycurve.dxf`
4. Open in Fusion 360 / VCarve / text editor
5. Check for ENTITIES section

### 2. Test Bi-arc Export
1. Pick a clothoid/bi-arc (set p0, t0, p1, t1)
2. Click "Export Bi-arc DXF"
3. Verify file downloads as `biarc.dxf`
4. Open in CAM software
5. Check for ARC entities

### 3. Test Overlay Visualization
1. Pick a clothoid/bi-arc
2. Enable "Show bi-arc centers (R=...)" checkbox
3. Verify green dots appear at arc centers
4. Verify R=...mm labels show radius values
5. Verify faint green lines show radius vectors
6. Toggle checkbox on/off to verify hiding works

### 4. Test Error Handling
1. Try exporting polyline with 0 points → Should show alert
2. Try exporting bi-arc without picking → Should show alert
3. Stop server and try exporting → Should show console error

---

## 🐛 Common Issues & Fixes

### Issue: "Import ... could not be resolved"
**Fix**: Restart TypeScript server in VS Code (Ctrl+Shift+P → "TypeScript: Restart TS Server")

### Issue: Canvas overlay not showing
**Check**:
```typescript
console.log('Overlay enabled:', showBiarcOverlay.value)
console.log('Bi-arc entities:', lastBiarcEntities.value)
```
**Fix**: Ensure `watch(cPick, ...)` is calling `biarcEntitiesTS()` correctly

### Issue: DXF file not downloading
**Check browser console for errors**:
- Network error? → Server not running
- CORS error? → Check CORS middleware in app.py
- 404 error? → Router not included in app.py

**Fix**: Verify server is running at `http://localhost:8000`

### Issue: Buttons disabled
**Check**:
- Polyline button: `pts.value.length >= 2`?
- Bi-arc button: `cPick.value` populated?

**Fix**: Draw more points or pick clothoid

---

## 📊 Expected Outcomes

✅ **Polyline Export**:
- Button enabled when 2+ points drawn
- Click → `polycurve.dxf` downloads immediately
- File contains POLYLINE + VERTEX entities
- Opens cleanly in CAM software

✅ **Bi-arc Export**:
- Button enabled when clothoid picked
- Click → `biarc.dxf` downloads immediately
- File contains 2 ARC entities (or 1 POLYLINE if degenerate)
- Opens cleanly in CAM software

✅ **Overlay Visualization**:
- Checkbox toggle shows/hides overlay
- Green center dots at arc origins (3px radius)
- R= labels show radius in mm (12px monospace font)
- Faint green lines show radius vectors (50% opacity)
- Overlay updates when clothoid re-picked

---

## 🔗 Related Files

- **DXF Utilities**: `client/src/utils/curvemath_dxf.ts`
- **Bi-arc Math**: `client/src/utils/curvemath.ts` (line 172+)
- **Server Endpoints**: `server/dxf_exports_router.py`
- **Tests**: `server/tests/test_curvemath_dxf.py`
- **Integration Guide**: `CURVEMATH_DXF_INTEGRATION_COMPLETE.md`

---

## 📞 Need Help?

**Stuck?** Check the integration guide:
```
cat CURVEMATH_DXF_INTEGRATION_COMPLETE.md
```

**Server issues?** Test endpoints directly:
```powershell
curl http://localhost:8000/exports/dxf/health
```

**Client errors?** Check browser console (F12)

---

**Last Updated**: January 2025  
**Status**: Backend ✅ Complete | UI 🔜 Pending Implementation
