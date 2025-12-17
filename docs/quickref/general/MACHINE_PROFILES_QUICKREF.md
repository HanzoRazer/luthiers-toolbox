# Module M.1 Quick Reference

**Machine Profiles + Predictive Feed Model**

---

## 🚀 Quick Start

### **1. List Available Machines**
```bash
curl http://localhost:8000/api/machine/profiles | jq '.[].title'
# Output:
# "GRBL 3018 (hobby)"
# "Mach4 Router 4x8 (pro)"
# "LinuxCNC Knee Mill"
```

### **2. Plan with Machine Profile**
```bash
curl -X POST http://localhost:8000/cam/pocket/adaptive/plan \
  -H 'Content-Type: application/json' \
  -d '{
    "loops": [{"pts": [[0,0],[100,0],[100,60],[0,60]]}],
    "tool_d": 6.0,
    "stepover": 0.45,
    "strategy": "Spiral",
    "machine_profile_id": "Mach4_Router_4x8"
  }' | jq '.stats.time_s_jerk'
```

### **3. Use in UI**
```vue
<!-- Select machine in AdaptivePocketLab -->
<select v-model="machineId">
  <option value="GRBL_3018_Default">GRBL 3018 (hobby)</option>
  <option value="Mach4_Router_4x8">Mach4 Router 4x8 (pro)</option>
  <option value="">Custom from knobs</option>
</select>

<!-- Machine stats auto-display -->
<div v-if="selMachine">
  Feed {{ selMachine.limits.feed_xy }} mm/min · 
  Accel {{ selMachine.limits.accel }} mm/s²
</div>
```

---

## 📋 Default Profiles

| ID | Title | Feed | Accel | Jerk | Post |
|----|-------|------|-------|------|------|
| `GRBL_3018_Default` | GRBL 3018 (hobby) | 1200 | 600 | 1500 | GRBL |
| `Mach4_Router_4x8` | Mach4 Router 4x8 (pro) | 15000 | 1800 | 4000 | Mach4 |
| `LinuxCNC_KneeMill` | LinuxCNC Knee Mill | 6000 | 900 | 2500 | LinuxCNC |

---

## 🔌 API Endpoints

### **Machine Management**
```bash
# List profiles
GET /api/machine/profiles

# Get specific profile
GET /api/machine/profiles/{id}

# Create/update profile
POST /api/machine/profiles
Body: {id, title, controller, axes, limits, ...}

# Delete profile
DELETE /api/machine/profiles/{id}
```

### **Planning with Profile**
```bash
POST /api/cam/pocket/adaptive/plan
Body: {
  ...standard params...,
  "machine_profile_id": "Mach4_Router_4x8"  # 🆕 New parameter
}

Response: {
  "stats": {
    "time_s_jerk": 22.8,              # 🆕 Profile-based time
    "machine_profile_id": "Mach4..."  # 🆕 Echo selected profile
  }
}
```

---

## 🎨 UI Integration

### **Machine Selector (AdaptivePocketLab.vue)**

```typescript
// State
const machines = ref<any[]>([])
const machineId = ref<string>(localStorage.getItem('toolbox.machine') || 'Mach4_Router_4x8')
const selMachine = computed(() => machines.value.find(m => m.id === machineId.value))

// Load on mount
onMounted(async () => {
  const r = await fetch('/api/machine/profiles')
  machines.value = await r.json()
})

// Auto-select post
watch(machineId, (v: string) => {
  localStorage.setItem('toolbox.machine', v || '')
  if (selMachine.value?.post_id_default) {
    postId.value = selMachine.value.post_id_default
  }
})

// Include in plan request
async function plan() {
  const body = {
    // ... existing params
    machine_profile_id: machineId.value || undefined
  }
}
```

---

## 🧮 Profile Schema

```json
{
  "id": "Mach4_Router_4x8",
  "title": "Mach4 Router 4x8 (pro)",
  "controller": "Mach4",
  "axes": {"travel_mm": [2440, 1220, 150]},
  "limits": {
    "feed_xy": 15000,       // mm/min - max cutting feed
    "rapid": 24000,         // mm/min - max rapid
    "accel": 1800,          // mm/s² - acceleration
    "jerk": 4000,           // mm/s³ - jerk limit
    "corner_tol_mm": 0.30   // mm - corner blending
  },
  "spindle": {"max_rpm": 24000},
  "feed_override": {"min": 0.5, "max": 1.5},
  "post_id_default": "Mach4"
}
```

---

## 📊 Time Prediction Example

**Test:** 120×80mm pocket, 6mm tool, 45% stepover

```bash
# GRBL (hobby machine)
curl ... -d '{"machine_profile_id": "GRBL_3018_Default"}' | jq '.stats.time_s_jerk'
# Output: 45.2s

# Mach4 (pro machine)
curl ... -d '{"machine_profile_id": "Mach4_Router_4x8"}' | jq '.stats.time_s_jerk'
# Output: 22.8s

# Speedup: 1.98x (pro machine has higher accel/jerk)
```

---

## 🛠️ Create Custom Profile

```typescript
const newProfile = {
  id: 'My_Custom_Mill',
  title: 'Custom Mill',
  controller: 'LinuxCNC',
  axes: {travel_mm: [600, 400, 200]},
  limits: {
    feed_xy: 8000,
    rapid: 12000,
    accel: 1200,
    jerk: 3000,
    corner_tol_mm: 0.25
  },
  post_id_default: 'LinuxCNC'
}

await fetch('/api/machine/profiles', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify(newProfile)
})
```

---

## 🐛 Common Issues

### Time estimate same for all profiles
```bash
# Check request includes machine_profile_id
curl ... -d '{"machine_profile_id": "Mach4_Router_4x8", "jerk_aware": true}'

# Verify profiles have different accel/jerk
curl http://localhost:8000/api/machine/profiles | jq '.[].limits.accel'
```

### Profile not found
```bash
# List available IDs
curl http://localhost:8000/api/machine/profiles | jq '.[].id'

# Verify exact match (case-sensitive)
curl http://localhost:8000/api/machine/profiles/Mach4_Router_4x8
```

### Post doesn't auto-select
```bash
# Check profile has post_id_default
curl http://localhost:8000/api/machine/profiles/GRBL_3018_Default | jq '.post_id_default'
# Should output: "GRBL"

# Clear localStorage
localStorage.removeItem('toolbox.machine')
```

---

## 📝 Testing Commands

```powershell
# Start server
cd services/api
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000

# Test machine profiles API
curl http://localhost:8000/api/machine/profiles

# Test profile-based planning
curl -X POST http://localhost:8000/cam/pocket/adaptive/plan `
  -H 'Content-Type: application/json' `
  -d '{
    "loops": [{"pts": [[0,0],[120,0],[120,80],[0,80]]}],
    "tool_d": 6.0,
    "stepover": 0.45,
    "strategy": "Spiral",
    "machine_profile_id": "GRBL_3018_Default"
  }' | jq '.stats'

# Compare machines
$profiles = @('GRBL_3018_Default', 'Mach4_Router_4x8', 'LinuxCNC_KneeMill')
foreach ($p in $profiles) {
  $time = curl -X POST http://localhost:8000/cam/pocket/adaptive/plan `
    -H 'Content-Type: application/json' `
    -d "{`"machine_profile_id`": `"$p`", `"loops`": [{`"pts`": [[0,0],[120,0],[120,80],[0,80]]}], `"tool_d`": 6.0, `"stepover`": 0.45, `"strategy`": `"Spiral`"}" | jq '.stats.time_s_jerk'
  Write-Host "$p : $time s"
}
```

---

## 🎯 Key Features

✅ **Machine profiles**: JSON-based configs for GRBL, Mach4, LinuxCNC  
✅ **Predictive feed**: Velocity capping based on accel/jerk/curvature  
✅ **Jerk-aware time**: Realistic runtime with s-curve acceleration  
✅ **Auto-post mapping**: Machine selection auto-picks post-processor  
✅ **CRUD API**: Create, read, update, delete profiles  
✅ **UI integration**: Machine dropdown + live stats display  
✅ **CI validation**: Automated tests proving profile accuracy  

---

## 📚 See Also

- [Full Documentation](./MACHINE_PROFILES_MODULE_M.md)
- [Adaptive Pocketing Module L](./ADAPTIVE_POCKETING_MODULE_L.md)
- [Patch L.3 Summary](./PATCH_L3_SUMMARY.md)

---

**Status:** ✅ Production Ready  
**Version:** M.1  
**Date:** November 5, 2025
