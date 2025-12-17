# Module M.1.1 Quick Reference

**Machine Editor + Compare + Bottleneck Map**

---

## 🎯 Quick Start

### **1. Edit a Machine Profile**
```typescript
// Click "Edit Machine" button in AdaptivePocketLab
// Modal opens with JSON editor
// Modify values → Click "Save"
// Or click "Clone As..." to create new profile
```

### **2. Compare 3 Machines**
```typescript
// Plan a pocket first (click "Plan" button)
// Click "Compare Machines" button
// Select different machine in each slot (A, B, C)
// Click "Run" in each slot
// View side-by-side comparison of times and bottlenecks
```

### **3. View Bottleneck Map**
```typescript
// Plan pocket with machine profile selected
// Enable "Bottleneck Map" checkbox (default: ON)
// Canvas shows color-coded segments:
//   🟧 Orange = feed cap limited
//   🟦 Teal = accel limited
//   🟪 Pink = jerk limited
```

---

## 🔌 API Endpoints

### **Clone Machine Profile**
```bash
POST /api/machine/profiles/clone/{src_id}?new_id=X&new_title=Y

# Example
curl -X POST "http://localhost:8000/machine/profiles/clone/GRBL_3018_Default?new_id=GRBL_Custom&new_title=My%20GRBL"

# Response
{"status": "cloned", "id": "GRBL_Custom"}
```

### **Plan with Bottleneck Tags**
```bash
POST /api/cam/pocket/adaptive/plan
{
  "loops": [...],
  "machine_profile_id": "GRBL_3018_Default",
  ...
}

# Response includes:
{
  "moves": [
    {"code": "G1", "x": 10, "y": 20, "meta": {"limit": "accel"}},
    ...
  ],
  "stats": {
    "caps": {
      "feed_cap": 12,
      "accel": 45,
      "jerk": 23,
      "none": 76
    },
    ...
  }
}
```

---

## 🎨 UI Components

### **MachineEditorModal**
```vue
<MachineEditorModal 
  v-model="editorOpen" 
  :profile="currentMachine" 
  @saved="handleSave"
/>
```

**Features:**
- JSON editor (textarea)
- ID/Title fields (synced with JSON)
- **Save** button (POST to `/api/machine/profiles`)
- **Clone As...** button (calls clone endpoint)
- **Format JSON** button (pretty-print)

### **CompareMachines**
```vue
<CompareMachines 
  v-model="compareOpen" 
  :machines="machineList" 
  :body="planRequestBody"
/>
```

**Features:**
- 3-column grid (slots A, B, C)
- Each slot has:
  - Machine dropdown
  - Run button
  - Stats (classic time, jerk time, speedup, caps)
- Caps histogram with color indicators

### **AdaptivePocketLab Integration**
```vue
<!-- State -->
const machineEditorOpen = ref(false)
const compareMachinesOpen = ref(false)
const showBottleneckMap = ref(true)

<!-- Buttons -->
<button @click="openMachineEditor" :disabled="!selMachine">Edit Machine</button>
<button @click="compareMachinesFunc" :disabled="!moves.length">Compare Machines</button>

<!-- Toggle -->
<input type="checkbox" v-model="showBottleneckMap"> Bottleneck Map

<!-- Modals -->
<MachineEditorModal v-model="machineEditorOpen" :profile="selMachine" @saved="onMachineSaved"/>
<CompareMachines v-model="compareMachinesOpen" :machines="machines" :body="buildBaseExportBody()"/>
```

---

## 🧮 Bottleneck Tagging Algorithm

### **Helper Function**
```python
def _tri_time_and_limit(d, v_target, accel, jerk):
    """Returns (time_s, limiter) where limiter ∈ {"accel", "jerk", "none"}"""
    if d <= 1e-9 or v_target <= 1e-9:
        return 0.0, "none"
    
    a = max(1.0, accel)
    j = max(1.0, jerk)
    t_a = a / j  # jerk-limited ramp time
    s_a = 0.5 * a * (t_a ** 2)  # distance during accel
    
    v_reach = math.sqrt(max(0.0, 2 * a * max(0.0, d - 2 * s_a)))
    
    if v_reach < v_target * 0.9:
        # Can't reach target speed → short move
        lim = "jerk" if j < a * 2 else "accel"
        return 2.0 * math.sqrt(d / max(1e-6, a)), lim
    
    s_cruise = max(0.0, d - 2 * s_a)
    t_cruise = s_cruise / max(1e-6, v_target)
    return (2 * t_a) + t_cruise, "none"
```

### **Main Tagging Function**
```python
def jerk_aware_time_with_profile_and_tags(moves, profile):
    """Returns (time_s, tagged_moves, caps_histogram)"""
    limits = profile.get("limits", {})
    accel = float(limits.get("accel", 800))
    jerk = float(limits.get("jerk", 2000))
    feed_cap = float(limits.get("feed_xy", 1200))
    
    caps = {"feed_cap": 0, "accel": 0, "jerk": 0, "none": 0}
    tagged = []
    
    for m in moves:
        mm = dict(m)
        mm.setdefault("meta", {})
        
        if mm.get("code") in ("G1", "G2", "G3"):
            v_req_mm_min = effective_feed_for_segment(mm, ...)
            
            # Check feed cap first
            feed_limited = v_req_mm_min > feed_cap
            v_eff = min(v_req_mm_min, feed_cap) / 60.0
            
            # Calculate time and identify constraint
            d = calculate_distance(mm, prev)
            dt, lim = _tri_time_and_limit(d, v_eff, accel, jerk)
            
            # Tag with limiter
            mm["meta"]["limit"] = "feed_cap" if feed_limited else lim
            caps[mm["meta"]["limit"]] += 1
        
        tagged.append(mm)
    
    return total_time, tagged, caps
```

---

## 🎨 Canvas Rendering

### **Bottleneck Map Pass**
```typescript
if (showBottleneckMap.value) {
  let last:any=null
  for (const m of moves.value){
    if ((m.code==='G1'||m.code==='G2'||m.code==='G3') && 'x' in m && 'y' in m){
      if (last){
        const lim = m.meta?.limit || 'none'
        const col = lim==='feed_cap' ? '#f59e0b' :   // orange
                    lim==='accel'    ? '#14b8a6' :   // teal
                    lim==='jerk'     ? '#ec4899' :   // pink
                    null
        if (col) {
          ctx.strokeStyle = col
          ctx.lineWidth = 2/s
          ctx.beginPath()
          ctx.moveTo(last.x, last.y)
          ctx.lineTo(m.x, m.y)
          ctx.stroke()
        }
      }
      last = {x:m.x,y:m.y}
    } else if ('x' in m && 'y' in m){
      last = {x:m.x,y:m.y}
    }
  }
}
```

---

## 📊 Example Caps Distributions

### **GRBL CNC 3018**
```json
{
  "feed_cap": 5,     // 3% - mostly within feed limits
  "accel": 87,       // 56% - heavy accel limiting (low 800 mm/s²)
  "jerk": 45,        // 29% - significant jerk limiting
  "none": 19         // 12% - few cruise segments
}
```
**Interpretation:** Low-end machine, heavily constrained by physics

### **Mach4 Custom**
```json
{
  "feed_cap": 23,    // 15% - more feed-limited (higher feed rate)
  "accel": 45,       // 29% - moderate accel limiting
  "jerk": 12,        // 8% - minimal jerk limiting (high 5000 mm/s³)
  "none": 76         // 49% - good cruise percentage
}
```
**Interpretation:** Mid-range machine, better balance

### **LinuxCNC Industrial**
```json
{
  "feed_cap": 12,    // 8% - moderate feed limiting
  "accel": 54,       // 34% - balanced accel
  "jerk": 28,        // 18% - moderate jerk
  "none": 62         // 40% - healthy cruise
}
```
**Interpretation:** Industrial machine, optimal performance

---

## 🔍 Workflow Examples

### **Machine Tuning**
1. Plan test pocket
2. Click **Compare Machines**
3. Run current profile in slot A
4. Click **Edit Machine** → **Clone As...** → `GRBL_Tuned`
5. Increase `accel` from 800 to 1000 mm/s²
6. Save and select in slot B
7. Run both
8. Compare speedup and caps
9. Iterate until optimal

### **Machine Selection**
1. Plan target pocket
2. Click **Compare Machines**
3. Select 3 candidates (GRBL, Mach4, LinuxCNC)
4. Run all three
5. Compare:
   - Runtime (faster = higher productivity)
   - Bottlenecks (high accel/jerk = rough surface)
   - Feed cap % (high = good utilization)
6. Choose best balance

### **Bottleneck Diagnosis**
1. Plan pocket with actual profile
2. Enable **Bottleneck Map**
3. Identify dominant color:
   - Mostly orange → increase feed rate
   - Mostly teal → increase accel
   - Mostly pink → increase jerk
4. Clone profile and adjust
5. Re-plan and verify improvement

---

## 🐛 Common Issues

### **Issue:** Edit button disabled
**Cause:** No machine profile selected  
**Fix:** Select a profile from dropdown

### **Issue:** Compare button disabled
**Cause:** No toolpath planned  
**Fix:** Click "Plan" button first

### **Issue:** Bottleneck map shows all gray
**Cause:** No machine profile selected or unrealistic limits  
**Fix:** Select a profile and ensure limits are reasonable

### **Issue:** Clone returns HTTP 400
**Cause:** `new_id` already exists  
**Fix:** Choose a unique ID

---

## 📋 Quick Checklist

**Backend:**
- [x] Clone endpoint in `machine_router.py`
- [x] `_tri_time_and_limit()` helper in `feedtime_l3.py`
- [x] `jerk_aware_time_with_profile_and_tags()` in `feedtime_l3.py`
- [x] Updated `/plan` endpoint in `adaptive_router.py`

**Frontend:**
- [x] `MachineEditorModal.vue` component
- [x] `MachinePane.vue` component
- [x] `CompareMachines.vue` component
- [x] State variables in `AdaptivePocketLab.vue`
- [x] Helper functions in `AdaptivePocketLab.vue`
- [x] Buttons and modals in template
- [x] Bottleneck map toggle and rendering

**Testing:**
- [ ] CI test for bottleneck tags
- [ ] CI test for clone endpoint
- [ ] Local end-to-end testing

---

## 📚 See Also

- [Full Implementation Summary](./MODULE_M1_1_IMPLEMENTATION_SUMMARY.md)
- [Module M.1](./MACHINE_PROFILES_MODULE_M.md)
- [Module L.3](./PATCH_L3_SUMMARY.md)
- [Adaptive Pocketing](./ADAPTIVE_POCKETING_MODULE_L.md)

---

**Status:** ✅ M.1.1 Complete (CI Pending)  
**Integration:** 5 files modified, 4 files created  
**Estimated Setup:** 2-3 hours with testing
