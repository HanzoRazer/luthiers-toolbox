# Module M.3: Energy & Heat Model — Complete Implementation

**Status:** ✅ Production Ready  
**Date:** November 2025  
**Integration:** AdaptivePocketLab.vue + FastAPI Backend

---

## 🎯 Overview

Module M.3 delivers **material-aware energy modeling** and **thermal analysis** for adaptive pocketing operations. This enables:

- ✅ **Energy Calculation**: Volume-based energy estimation using Specific Cutting Energy (SCE)
- ✅ **Heat Partitioning**: Thermal distribution into chip, tool, and workpiece
- ✅ **Power Timeseries**: Heat generation over time (W) for thermal planning
- ✅ **Material Database**: 4 preset materials (hardwoods, softwoods, aluminum)
- ✅ **CSV Exports**: Per-segment energy and bottleneck data
- ✅ **Bottleneck Visualization**: Pie chart showing feed/accel/jerk limits
- ✅ **Chipload Enforcement**: Integrated optimizer controls

---

## 📦 What's New

### **Core Features**

1. **Material Database** (`material_db.json`)
   - 4 preset materials with SCE (J/mm³) and heat partition ratios
   - maple_hard: 0.55 J/mm³ (70% chip, 20% tool, 10% work)
   - mahogany: 0.45 J/mm³ (70% chip, 20% tool, 10% work)
   - al_6061: 0.35 J/mm³ (60% chip, 25% tool, 15% work)
   - custom: 0.50 J/mm³ (70% chip, 20% tool, 10% work)

2. **Energy Model** (`energy_model.py`)
   - Volume proxy: length × (stepover × tool_d) × stepdown × engagement_factor
   - Energy = volume × SCE (J/mm³)
   - Per-segment energy tracking with cumulative totals

3. **Heat Timeseries** (`heat_timeseries.py`)
   - Power (J/s) calculation over time bins
   - Jerk-aware time estimation for accurate binning
   - Heat partition: chip/tool/work power arrays

4. **CSV Exports**
   - Energy CSV: idx, code, len_mm, vol_mm3, energy_j, cum_energy_j
   - Bottleneck CSV: idx, code, x, y, len_mm, limit (feed_cap/accel/jerk/none)

5. **UI Integration** (`AdaptivePocketLab.vue`)
   - Energy & Heat panel with material selector
   - Cumulative energy SVG chart
   - Heat partition stacked bar (chip/tool/work)
   - Heat over time SVG strip chart (3 polylines)
   - Bottleneck pie chart (donut visualization)
   - Export CSV buttons for energy and bottlenecks
   - Chipload enforcement checkbox + tolerance input

---

## 🏗️ Architecture

### **Backend Stack** (`services/api/app/`)

```
routers/
├── material_router.py        # Material CRUD (list, get, upsert)
├── cam_metrics_router.py     # Metrics API (energy, heat_timeseries, CSV exports)
└── machine_router.py          # Machine profiles (reused from M.1)

cam/
├── energy_model.py            # Energy calculation with volume proxy
└── heat_timeseries.py         # Power over time with jerk-aware binning

assets/
└── material_db.json           # Material database with SCE and heat partition
```

### **Frontend Stack** (`packages/client/src/components/`)

```
AdaptivePocketLab.vue          # Main UI with 3 new sections:
                               # 1. Energy & Heat panel
                               # 2. Heat over time card
                               # 3. Bottleneck enhancements (pie + CSV)

CompareSettings.vue            # Side-by-side NC comparison modal
```

### **CI/CD** (`.github/workflows/`)

```
adaptive_pocket.yml            # 5 comprehensive M.3 tests
```

---

## 🔌 API Endpoints

### **Materials**

**GET `/api/material/list`** - List all materials
```json
{
  "materials": [
    {
      "id": "maple_hard",
      "name": "Hard Maple",
      "sce_j_per_mm3": 0.55,
      "heat_partition": {"chip": 0.7, "tool": 0.2, "work": 0.1}
    },
    ...
  ]
}
```

**GET `/api/material/get/{mid}`** - Get specific material
```json
{
  "id": "maple_hard",
  "name": "Hard Maple",
  "sce_j_per_mm3": 0.55,
  "heat_partition": {"chip": 0.7, "tool": 0.2, "work": 0.1}
}
```

**POST `/api/material/upsert`** - Create/update material
```json
{
  "id": "custom_walnut",
  "name": "Black Walnut",
  "sce_j_per_mm3": 0.48,
  "heat_partition": {"chip": 0.7, "tool": 0.2, "work": 0.1}
}
```

---

### **Energy Metrics**

**POST `/api/cam/metrics/energy`** - Calculate energy breakdown
```json
{
  "moves": [...],
  "material_id": "maple_hard",
  "tool_d": 6.0,
  "stepover": 0.45,
  "stepdown": 1.5
}
```

**Response:**
```json
{
  "totals": {
    "volume_mm3": 6000.0,
    "energy_j": 3300.0,
    "chip_j": 2310.0,
    "tool_j": 660.0,
    "work_j": 330.0
  },
  "segments": [
    {
      "idx": 0,
      "code": "G1",
      "len_mm": 97.0,
      "vol_mm3": 390.6,
      "energy_j": 214.8,
      "chip_j": 150.4,
      "tool_j": 43.0,
      "work_j": 21.5
    },
    ...
  ],
  "material": "maple_hard"
}
```

---

**POST `/api/cam/metrics/energy_csv`** - Export energy CSV
```json
{
  "moves": [...],
  "material_id": "maple_hard",
  "tool_d": 6.0,
  "stepover": 0.45,
  "stepdown": 1.5,
  "job_name": "pocket"
}
```

**Response:** CSV file download with headers:
```csv
idx,code,len_mm,vol_mm3,energy_j,cum_energy_j
0,G1,97.0000,390.6000,214.8300,214.8300
1,G1,54.0000,217.4000,119.5700,334.4000
...
```

---

### **Heat Timeseries**

**POST `/api/cam/metrics/heat_timeseries`** - Calculate power over time
```json
{
  "moves": [...],
  "machine_profile_id": "default",
  "material_id": "maple_hard",
  "tool_d": 6.0,
  "stepover": 0.45,
  "stepdown": 1.5,
  "bins": 120
}
```

**Response:**
```json
{
  "t": [0.0, 0.5, 1.0, 1.5, ...],           // time axis (s)
  "p_chip": [12.3, 15.6, 13.2, ...],        // chip power (W)
  "p_tool": [3.5, 4.5, 3.8, ...],           // tool power (W)
  "p_work": [1.8, 2.2, 1.9, ...],           // work power (W)
  "total_s": 120.5,                         // total time (s)
  "material": "maple_hard",
  "machine_profile_id": "default"
}
```

---

### **Bottleneck Analysis**

**POST `/api/cam/metrics/bottleneck_csv`** - Export bottleneck CSV
```json
{
  "moves": [...],
  "machine_profile_id": "default",
  "job_name": "pocket"
}
```

**Response:** CSV file download with headers:
```csv
idx,code,x,y,len_mm,limit
0,G1,97.0000,3.0000,94.0000,none
1,G1,97.0000,6.7000,3.7000,accel
2,G1,94.3000,6.7000,2.7000,jerk
...
```

---

## 🎨 UI Components

### **Energy & Heat Panel**

Located in `AdaptivePocketLab.vue` left column:

```vue
<div class="border rounded-lg p-4 bg-white shadow-sm">
  <h2>Energy & Heat</h2>
  
  <!-- Material Selector -->
  <select v-model="materialId">
    <option value="maple_hard">Hard Maple</option>
    <option value="mahogany">Mahogany</option>
    <option value="al_6061">Aluminum 6061</option>
    <option value="custom">Custom</option>
  </select>
  
  <!-- Compute Button -->
  <button @click="runEnergy">Compute</button>
  <button @click="exportEnergyCsv">Export CSV</button>
  
  <!-- Totals Card -->
  <div v-if="energyOut">
    <div>Volume: {{ energyOut.totals.volume_mm3 }} mm³</div>
    <div>Energy: {{ energyOut.totals.energy_j }} J</div>
    <div>Chip heat: {{ energyOut.totals.chip_j }} J</div>
    <div>Tool heat: {{ energyOut.totals.tool_j }} J</div>
    <div>Work heat: {{ energyOut.totals.work_j }} J</div>
  </div>
  
  <!-- Heat Partition Bar (stacked) -->
  <div class="w-full h-6 flex rounded overflow-hidden">
    <div class="bg-amber-400" :style="{width: chipPct + '%'}"></div>
    <div class="bg-rose-400" :style="{width: toolPct + '%'}"></div>
    <div class="bg-emerald-400" :style="{width: workPct + '%'}"></div>
  </div>
  
  <!-- Cumulative Energy Chart (SVG polyline) -->
  <svg viewBox="0 0 300 120">
    <polyline :points="energyPolyline" fill="none" stroke="currentColor"/>
  </svg>
</div>
```

**Key Functions:**
```typescript
async function runEnergy() {
  // Call /api/cam/metrics/energy
  // Update energyOut.value
}

async function exportEnergyCsv() {
  // Call /api/cam/metrics/energy_csv
  // Download blob as energy_{job}.csv
}

const energyPolyline = computed(() => {
  // Map segments cumulative energy to SVG polyline points
  // 300×120 viewBox scaling
})
```

---

### **Heat over Time Card**

Located in `AdaptivePocketLab.vue` left column:

```vue
<div class="border rounded-lg p-4 bg-white shadow-sm">
  <h2>Heat over Time</h2>
  
  <!-- Compute Button -->
  <button @click="runHeatTS">Compute</button>
  
  <div v-if="heatTS">
    <!-- Summary -->
    <div>Total Time: {{ heatTS.total_s }} s</div>
    <div>Peak Chip Power: {{ Math.max(...heatTS.p_chip) }} W</div>
    <div>Peak Tool Power: {{ Math.max(...heatTS.p_tool) }} W</div>
    
    <!-- Power Chart (3 polylines) -->
    <svg viewBox="0 0 300 120">
      <polyline :points="tsPolyline('p_chip')" stroke="#f59e0b"/>
      <polyline :points="tsPolyline('p_tool')" stroke="#ef4444"/>
      <polyline :points="tsPolyline('p_work')" stroke="#14b8a6"/>
    </svg>
  </div>
</div>
```

**Key Functions:**
```typescript
async function runHeatTS() {
  // Call /api/cam/metrics/heat_timeseries
  // Update heatTS.value with t, p_chip, p_tool, p_work arrays
}

function tsPolyline(field: 'p_chip' | 'p_tool' | 'p_work'): string {
  // Map (t, power) arrays to SVG polyline points
  // Normalize to 300×120 viewBox
}
```

---

### **Bottleneck Enhancements**

Located in `AdaptivePocketLab.vue` right column:

```vue
<!-- Export CSV Button -->
<button @click="exportBottleneckCsv">Export CSV</button>

<!-- Bottleneck Pie Chart -->
<div v-if="showBottleneckMap && planOut?.stats?.caps">
  <svg viewBox="0 0 120 120">
    <g transform="translate(60,60)">
      <path v-for="(s, i) in capsPie" :d="arcPath(i)" :fill="s.color"/>
      <circle cx="0" cy="0" r="26" fill="#fff"/>
    </g>
  </svg>
  <div class="legend">
    <span v-for="s in capsPie">{{ s.label }} {{ Math.round(s.pct*100) }}%</span>
  </div>
</div>
```

**Key Functions:**
```typescript
async function exportBottleneckCsv() {
  // Call /api/cam/metrics/bottleneck_csv
  // Download blob as bottleneck_{job}.csv
}

const capsPie = computed(() => {
  // Read planOut.value?.stats?.caps {feed_cap, accel, jerk, none}
  // Normalize to percentages, map to colors
})

function arcPath(index: number): string {
  // Calculate cumulative angles from previous slices
  // Generate SVG arc path: M0,0 L{x0},{y0} A{R},{R} 0 {large} 1 {x1},{y1} Z
}
```

---

### **Chipload Enforcement Controls**

Located in `AdaptivePocketLab.vue` Optimize panel:

```vue
<label>
  <input type="checkbox" v-model="enforceChip"> Enforce chipload
</label>
<input
  type="number"
  v-model.number="chipTol"
  :disabled="!enforceChip"
  placeholder="Tolerance (mm/tooth)"
  step="0.01"
>
```

**Integration:**
```typescript
const enforceChip = ref(true)
const chipTol = ref(0.02)

async function runWhatIf() {
  const body = { ... }
  if (enforceChip.value) {
    body.tolerance_chip_mm = chipTol.value
  }
  // Call /api/cam/whatif/opt
}
```

---

## 🧮 Algorithms

### **1. Energy Calculation**

```python
# energy_model.py

def _vol_removed_for_move(m, prev, tool_d_mm, stepover, stepdown):
    """Calculate volume removed per move."""
    dx = m.x - prev.x
    dy = m.y - prev.y
    length_mm = sqrt(dx**2 + dy**2)
    
    width_mm = stepover * tool_d_mm
    engagement_factor = 0.9 if m.code in ('G2', 'G3') else 1.0
    
    vol = length_mm * width_mm * stepdown * engagement_factor
    return vol, length_mm

def energy_breakdown(moves, sce_j_per_mm3, tool_d_mm, stepover, stepdown, heat_partition):
    """Calculate per-segment and total energy."""
    segments = []
    cum_energy = 0.0
    
    for i, m in enumerate(moves):
        vol, length = _vol_removed_for_move(m, moves[i-1], tool_d_mm, stepover, stepdown)
        energy = vol * sce_j_per_mm3
        cum_energy += energy
        
        chip_j = energy * heat_partition['chip']
        tool_j = energy * heat_partition['tool']
        work_j = energy * heat_partition['work']
        
        segments.append({
            'idx': i,
            'code': m.code,
            'len_mm': length,
            'vol_mm3': vol,
            'energy_j': energy,
            'cum_energy_j': cum_energy,
            'chip_j': chip_j,
            'tool_j': tool_j,
            'work_j': work_j
        })
    
    totals = {
        'volume_mm3': sum(s['vol_mm3'] for s in segments),
        'energy_j': cum_energy,
        'chip_j': sum(s['chip_j'] for s in segments),
        'tool_j': sum(s['tool_j'] for s in segments),
        'work_j': sum(s['work_j'] for s in segments)
    }
    
    return {'totals': totals, 'segments': segments}
```

---

### **2. Heat Timeseries**

```python
# heat_timeseries.py

def _seg_time_mm(m, accel, jerk, rapid_mm_s, feed_cap_mm_min):
    """Jerk-aware time estimation per segment."""
    dx = m.x - prev.x
    dy = m.y - prev.y
    d = sqrt(dx**2 + dy**2)
    
    if m.code == 'G0':  # Rapid
        v = rapid_mm_s
    else:  # Cutting
        v = min(m.f / 60.0, feed_cap_mm_min / 60.0)
    
    # Jerk-limited accel time
    t_a = accel / jerk
    s_a = 0.5 * accel * t_a**2
    
    if d < 2 * s_a:
        # Very short: pure jerk phase
        return 2 * sqrt(d / accel)
    else:
        # Accel + cruise + decel
        v_reach = sqrt(2 * accel * (d - 2 * s_a))
        if v_reach < v * 0.9:
            return 2 * sqrt(d / accel)
        else:
            s_cruise = d - 2 * s_a
            return 2 * t_a + s_cruise / v

def heat_timeseries(moves, profile, tool_d_mm, stepover, stepdown, sce_j_per_mm3, heat_partition, bins=120):
    """Calculate power over time."""
    # Step 1: Calculate per-segment energy and time
    seg_e = []  # energy (J) per segment
    seg_t = []  # time (s) per segment
    
    for i, m in enumerate(moves):
        vol, length = _vol_removed_for_move(m, moves[i-1], tool_d_mm, stepover, stepdown)
        energy = vol * sce_j_per_mm3
        time = _seg_time_mm(m, profile.accel, profile.jerk, profile.rapid, profile.feed_xy)
        
        seg_e.append(energy)
        seg_t.append(time)
    
    # Step 2: Build timeline bins
    T = sum(seg_t)
    B = max(10, min(bins, 2000))
    dt = T / B
    
    p_raw = [0.0] * B
    cumulative_t = 0.0
    
    for i, (e, t) in enumerate(zip(seg_e, seg_t)):
        if t <= 0:
            continue
        
        power = e / t  # J/s = W
        
        # Map segment to bins
        start_bin = int((cumulative_t / T) * B)
        end_bin = int(((cumulative_t + t) / T) * B)
        
        for b in range(start_bin, min(end_bin + 1, B)):
            p_raw[b] += power
        
        cumulative_t += t
    
    # Step 3: Partition heat
    p_chip = [p * heat_partition['chip'] for p in p_raw]
    p_tool = [p * heat_partition['tool'] for p in p_raw]
    p_work = [p * heat_partition['work'] for p in p_raw]
    
    t_axis = [i * dt for i in range(B)]
    
    return {
        't': t_axis,
        'p_chip': p_chip,
        'p_tool': p_tool,
        'p_work': p_work,
        'total_s': T
    }
```

---

### **3. Bottleneck Detection**

```python
# cam_metrics_router.py (simplified)

def determine_bottleneck(move, prev_move, profile):
    """Classify segment limit."""
    dx = move.x - prev_move.x
    dy = move.y - prev_move.y
    len_mm = sqrt(dx**2 + dy**2)
    
    if len_mm <= 0:
        return "none"
    
    feed_f = move.f or 0.0
    feed_cap = profile.feed_xy
    accel = profile.accel
    jerk = profile.jerk
    
    # Check feed cap
    if feed_f >= feed_cap * 0.95:
        return "feed_cap"
    
    # Check accel limit (short move)
    if len_mm < (feed_f / 60.0)**2 / (2 * accel):
        return "accel"
    
    # Check jerk limit (very short move)
    if len_mm < (feed_f / 60.0)**3 / (jerk * accel):
        return "jerk"
    
    return "none"
```

---

## 🧪 Testing

### **Local Testing**

```powershell
# Start API
cd services/api
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000

# Start Client
cd packages/client
npm run dev  # http://localhost:5173

# Manual testing:
# 1. Open AdaptivePocketLab.vue
# 2. Click "Plan"
# 3. Select material (e.g., Hard Maple)
# 4. Click "Compute" in Energy & Heat panel
# 5. Verify energy totals and heat partition bar
# 6. Click "Export CSV" - download energy_pocket.csv
# 7. Click "Compute" in Heat over Time card
# 8. Verify power chart displays chip/tool/work curves
# 9. Enable "Bottleneck Map"
# 10. Click "Export CSV" - download bottleneck_pocket.csv
```

---

### **CI Tests** (`.github/workflows/adaptive_pocket.yml`)

**5 Comprehensive Tests:**

1. **Energy Endpoint** (~90 lines)
   - Validates POST /cam/metrics/energy structure
   - Checks totals: volume_mm3, energy_j, chip_j, tool_j, work_j
   - Validates segments array with per-move data
   - Verifies heat partition sum = 100%

2. **Energy CSV Export** (~45 lines)
   - Validates Content-Disposition header
   - Checks CSV structure: idx,code,len_mm,vol_mm3,energy_j,cum_energy_j
   - Verifies column count = 6
   - Validates cumulative energy increases monotonically

3. **Chipload Enforcement** (~50 lines)
   - Calls /cam/whatif/opt with tolerance_chip_mm
   - Validates RPM bounds (6000-24000)
   - Checks chipload accuracy: error <= 0.01 mm/tooth

4. **Heat Timeseries** (~70 lines)
   - Calls POST /cam/metrics/heat_timeseries
   - Validates structure: t, p_chip, p_tool, p_work, total_s
   - Checks array lengths match
   - Verifies peak power values > 0

5. **Bottleneck CSV Export** (~70 lines)
   - Calls POST /cam/metrics/bottleneck_csv
   - Validates Content-Disposition filename
   - Checks CSV structure: idx,code,x,y,len_mm,limit
   - Verifies limit values in {feed_cap, accel, jerk, none}

---

## 📊 Performance Characteristics

### **Material SCE Values**

| Material | SCE (J/mm³) | Heat Partition (chip/tool/work) |
|----------|-------------|----------------------------------|
| Hard Maple | 0.55 | 70% / 20% / 10% |
| Mahogany | 0.45 | 70% / 20% / 10% |
| Aluminum 6061 | 0.35 | 60% / 25% / 15% |
| Custom | 0.50 | 70% / 20% / 10% |

### **Typical Results** (100×60mm pocket, 6mm tool, 45% stepover)

- **Volume:** ~6000 mm³
- **Energy (Maple):** ~3300 J
- **Chip Heat:** ~2310 J (70%)
- **Tool Heat:** ~660 J (20%)
- **Work Heat:** ~330 J (10%)
- **Peak Chip Power:** ~15-25 W
- **Peak Tool Power:** ~4-8 W
- **Peak Work Power:** ~2-4 W

---

## 🚀 Usage Examples

### **Example 1: Energy Calculation**

```typescript
// In AdaptivePocketLab.vue

async function runEnergy() {
  const body = {
    moves: planOut.value.moves,
    material_id: materialId.value,  // "maple_hard"
    tool_d: toolD.value,             // 6.0 mm
    stepover: stepover.value,        // 0.45
    stepdown: stepdown.value         // 1.5 mm
  }
  
  const r = await fetch('/api/cam/metrics/energy', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body)
  })
  
  energyOut.value = await r.json()
  // energyOut.totals: { volume_mm3, energy_j, chip_j, tool_j, work_j }
  // energyOut.segments: [ {idx, code, len_mm, vol_mm3, energy_j, cum_energy_j, ...}, ... ]
}
```

---

### **Example 2: Heat Timeseries**

```typescript
// In AdaptivePocketLab.vue

async function runHeatTS() {
  const body = {
    moves: planOut.value.moves,
    machine_profile_id: profileId.value,  // "default"
    material_id: materialId.value,        // "maple_hard"
    tool_d: toolD.value,                  // 6.0 mm
    stepover: stepover.value,             // 0.45
    stepdown: stepdown.value,             // 1.5 mm
    bins: 120                             // 120 time bins
  }
  
  const r = await fetch('/api/cam/metrics/heat_timeseries', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body)
  })
  
  heatTS.value = await r.json()
  // heatTS.t: [0.0, 0.5, 1.0, ...]
  // heatTS.p_chip: [12.3, 15.6, ...]
  // heatTS.p_tool: [3.5, 4.5, ...]
  // heatTS.p_work: [1.8, 2.2, ...]
  // heatTS.total_s: 120.5
}
```

---

### **Example 3: CSV Export**

```typescript
// In AdaptivePocketLab.vue

async function exportEnergyCsv() {
  const body = {
    moves: planOut.value.moves,
    material_id: materialId.value,
    tool_d: toolD.value,
    stepover: stepover.value,
    stepdown: stepdown.value,
    job_name: 'pocket'
  }
  
  const r = await fetch('/api/cam/metrics/energy_csv', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body)
  })
  
  const blob = await r.blob()
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = ''  // Server sets filename via Content-Disposition
  a.click()
  URL.revokeObjectURL(a.href)
  
  // Downloaded as: energy_pocket.csv
}
```

---

### **Example 4: Bottleneck Pie Chart**

```typescript
// In AdaptivePocketLab.vue

const capsPie = computed(() => {
  const c = planOut.value?.stats?.caps || {feed_cap:0, accel:0, jerk:0, none:0}
  const total = Math.max(1, c.feed_cap + c.accel + c.jerk + c.none)
  
  return [
    {label: 'Feed cap', v: c.feed_cap, color: '#f59e0b'},
    {label: 'Accel', v: c.accel, color: '#14b8a6'},
    {label: 'Jerk', v: c.jerk, color: '#ec4899'},
    {label: 'None', v: c.none, color: '#9ca3af'}
  ].map(s => ({...s, pct: s.v / total}))
})

function arcPath(index: number): string {
  const R = 40  // outer radius
  const cx = 60, cy = 60  // center
  
  // Calculate cumulative angle
  let angle = 0
  for (let i = 0; i < index; i++) {
    angle += capsPie.value[i].pct * 360
  }
  
  const angle0 = angle
  const angle1 = angle + capsPie.value[index].pct * 360
  
  const rad0 = angle0 * Math.PI / 180
  const rad1 = angle1 * Math.PI / 180
  
  const x0 = cx + R * Math.cos(rad0)
  const y0 = cy + R * Math.sin(rad0)
  const x1 = cx + R * Math.cos(rad1)
  const y1 = cy + R * Math.sin(rad1)
  
  const large = angle1 - angle0 > 180 ? 1 : 0
  
  return `M${cx},${cy} L${x0},${y0} A${R},${R} 0 ${large} 1 ${x1},${y1} Z`
}
```

---

## 🐛 Troubleshooting

### **Issue:** Energy totals are zero
**Solution:** 
- Check that `planOut.value?.moves` has cutting moves (G1/G2/G3)
- Verify `stepover` and `stepdown` are > 0
- Check material SCE value is valid (> 0)

### **Issue:** Heat timeseries shows no power
**Solution:**
- Verify `material_id` and `machine_profile_id` are valid
- Check `bins` parameter is between 10-2000
- Ensure moves have length > 0

### **Issue:** CSV download filename is generic
**Solution:**
- Ensure `job_name` parameter is provided
- Check `safe_stem()` utility is working (removes unsafe chars)
- Verify Content-Disposition header in response

### **Issue:** Bottleneck pie chart shows 100% "none"
**Solution:**
- Run plan with machine profile that has accel/jerk limits
- Check `stats.caps` field exists in planOut
- Verify bottleneck map toggle is enabled

---

## 📋 Integration Checklist

**Backend:**
- [x] Create `material_db.json` with 4 presets
- [x] Create `material_router.py` (list, get, upsert)
- [x] Create `energy_model.py` (volume proxy + heat partition)
- [x] Create `heat_timeseries.py` (power binning + jerk-aware time)
- [x] Create `cam_metrics_router.py` (energy, heat_timeseries, CSV exports)
- [x] Register routers in `main.py`

**Frontend:**
- [x] Add Energy & Heat panel to AdaptivePocketLab.vue
- [x] Add Heat over Time card
- [x] Add Bottleneck pie chart
- [x] Add Export CSV buttons (energy + bottleneck)
- [x] Add Chipload enforcement controls
- [x] Add CompareSettings modal

**CI/CD:**
- [x] Add 5 comprehensive tests to adaptive_pocket.yml
- [x] Test energy endpoint structure
- [x] Test energy CSV export
- [x] Test chipload enforcement
- [x] Test heat timeseries
- [x] Test bottleneck CSV export

**Documentation:**
- [x] Update ADAPTIVE_POCKETING_MODULE_L.md with M.3 references
- [x] Create MODULE_M3_COMPLETE.md (this document)
- [x] Update .github/copilot-instructions.md with M.3 overview

---

## 🎯 Next Steps

### **Immediate Priorities:**
1. ✅ **Module M.3 Complete** - All features implemented and tested
2. 🔜 **Module M.4** (Planned) - Advanced thermal cooling strategies
3. 🔜 **Module M.5** (Planned) - Multi-operation job sequencing

### **Future Enhancements:**
- **Material Library Expansion**: Add more presets (exotic woods, plastics, composites)
- **Thermal Limits**: Implement max tool temperature warnings
- **Energy Optimization**: Minimize total energy consumption
- **Heat Dissipation Modeling**: Add coolant/air flow effects
- **CSV Batch Export**: Single button for energy + bottleneck + toolpath CSVs

---

## 📚 See Also

- [Adaptive Pocketing Module L](./ADAPTIVE_POCKETING_MODULE_L.md) - Core toolpath generation
- [Module M.1: Machine Profiles](./MACHINE_PROFILES_MODULE_M.md) - Machine-aware physics
- [Module M.1.1: Machine Editor](./MODULE_M1_1_IMPLEMENTATION_SUMMARY.md) - Profile CRUD + bottleneck map
- [Module M.2: Cycle Time Estimator](./PATCH_L3_SUMMARY.md) - Jerk-aware time + what-if optimizer
- [Multi-Post Export System](./PATCH_K_EXPORT_COMPLETE.md) - G-code post-processors
- [Unit Conversion](./services/api/app/util/units.py) - mm ↔ inch scaling

---

**Status:** ✅ Module M.3 Complete and Production-Ready  
**Version:** 1.0.0  
**Date:** November 2025  
**Next Module:** M.4 (Thermal Cooling Strategies)
