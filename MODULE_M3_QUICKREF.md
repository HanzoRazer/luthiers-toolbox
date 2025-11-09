# Module M.3: Energy & Heat Model — Quick Reference

**Status:** ✅ Production Ready  
**Version:** 1.0.0  
**Date:** November 2025

---

## 🎯 Overview

Module M.3 adds **material-aware energy modeling** and **thermal analysis** to adaptive pocketing:
- Energy calculation (J) using Specific Cutting Energy (SCE)
- Heat partitioning into chip/tool/work
- Power timeseries (W) over time
- CSV exports for analysis
- Bottleneck visualization

---

## 📦 Files Changed

### **Backend** (`services/api/app/`)
```
routers/
├── material_router.py        # NEW: Material CRUD (90 lines)
├── cam_metrics_router.py     # NEW: Metrics API (260+ lines)
└── machine_router.py          # Reused from M.1

cam/
├── energy_model.py            # NEW: Energy calculation (170 lines)
└── heat_timeseries.py         # NEW: Power over time (220 lines)

assets/
└── material_db.json           # NEW: 4 material presets

main.py                        # MODIFIED: Added material_router, cam_metrics_router
```

### **Frontend** (`packages/client/src/components/`)
```
AdaptivePocketLab.vue          # EXTENSIVELY MODIFIED: +250 lines
                               # - Energy & Heat panel
                               # - Heat over Time card
                               # - Bottleneck pie chart
                               # - CSV export buttons
                               # - Chipload enforcement controls

CompareSettings.vue            # NEW: Side-by-side NC comparison (75 lines)
```

### **CI/CD** (`.github/workflows/`)
```
adaptive_pocket.yml            # EXTENDED: +5 comprehensive tests (~300 lines)
```

---

## 🔌 API Endpoints

### **Materials**
```
GET  /api/material/list         # List all materials
GET  /api/material/get/{mid}    # Get specific material
POST /api/material/upsert       # Create/update material
```

### **Energy Metrics**
```
POST /api/cam/metrics/energy          # Calculate energy breakdown
POST /api/cam/metrics/energy_csv      # Export energy CSV
POST /api/cam/metrics/heat_timeseries # Power over time
POST /api/cam/metrics/bottleneck_csv  # Export bottleneck CSV
```

---

## 🧮 Key Algorithms

### **Energy Calculation**
```python
volume = length × (stepover × tool_d) × stepdown × engagement_factor
energy = volume × sce_j_per_mm³
heat_chip = energy × 0.7
heat_tool = energy × 0.2
heat_work = energy × 0.1
```

### **Heat Timeseries**
```python
# Per-segment power
power = energy / jerk_aware_time

# Bin into timeline
for bin in timeline:
    power_chip[bin] += power × 0.7
    power_tool[bin] += power × 0.2
    power_work[bin] += power × 0.1
```

---

## 🎨 UI Components

### **Energy & Heat Panel**
- Material selector (4 presets)
- Compute button → calls `/api/cam/metrics/energy`
- Export CSV button → downloads `energy_{job}.csv`
- Totals card: volume, energy, chip/tool/work heat
- Heat partition stacked bar (amber/rose/emerald)
- Cumulative energy SVG polyline

### **Heat over Time Card**
- Compute button → calls `/api/cam/metrics/heat_timeseries`
- Summary: total time, peak chip/tool power
- SVG strip chart: 3 polylines (chip/tool/work)
- Legend: color-coded heat types

### **Bottleneck Enhancements**
- Export CSV button → downloads `bottleneck_{job}.csv`
- Pie chart: donut showing feed_cap/accel/jerk/none distribution
- Legend: percentage breakdown

### **Chipload Enforcement**
- Checkbox: "Enforce chipload" (default: true)
- Input: "Tolerance (mm/tooth)" (default: 0.02)
- Wiring: adds `tolerance_chip_mm` to optimizer body when enabled

---

## 🧪 Testing

### **Local Test**
```powershell
# Start API
cd services/api
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000

# Start Client
cd packages/client
npm run dev

# Test Flow:
# 1. Open AdaptivePocketLab.vue
# 2. Click "Plan"
# 3. Select material (Hard Maple)
# 4. Click "Compute" in Energy & Heat panel
# 5. Click "Export CSV"
# 6. Click "Compute" in Heat over Time card
# 7. Enable "Bottleneck Map"
# 8. Click "Export CSV" in bottleneck section
```

### **CI Tests** (5 tests)
```bash
# GitHub Actions automatically runs:
# 1. Energy endpoint validation
# 2. Energy CSV export validation
# 3. Chipload enforcement validation
# 4. Heat timeseries validation
# 5. Bottleneck CSV export validation
```

---

## 📊 Material Database

| Material | SCE (J/mm³) | Heat Partition (chip/tool/work) |
|----------|-------------|----------------------------------|
| maple_hard | 0.55 | 70% / 20% / 10% |
| mahogany | 0.45 | 70% / 20% / 10% |
| al_6061 | 0.35 | 60% / 25% / 15% |
| custom | 0.50 | 70% / 20% / 10% |

---

## 🚀 Usage Examples

### **Energy Calculation**
```typescript
// Call energy endpoint
const r = await fetch('/api/cam/metrics/energy', {
  method: 'POST',
  body: JSON.stringify({
    moves: planOut.value.moves,
    material_id: 'maple_hard',
    tool_d: 6.0,
    stepover: 0.45,
    stepdown: 1.5
  })
})

const data = await r.json()
// data.totals: {volume_mm3, energy_j, chip_j, tool_j, work_j}
// data.segments: [{idx, code, len_mm, vol_mm3, energy_j, cum_energy_j, ...}, ...]
```

### **Heat Timeseries**
```typescript
// Call heat_timeseries endpoint
const r = await fetch('/api/cam/metrics/heat_timeseries', {
  method: 'POST',
  body: JSON.stringify({
    moves: planOut.value.moves,
    machine_profile_id: 'default',
    material_id: 'maple_hard',
    tool_d: 6.0,
    stepover: 0.45,
    stepdown: 1.5,
    bins: 120
  })
})

const data = await r.json()
// data.t: [0.0, 0.5, 1.0, ...]
// data.p_chip: [12.3, 15.6, ...]
// data.p_tool: [3.5, 4.5, ...]
// data.p_work: [1.8, 2.2, ...]
// data.total_s: 120.5
```

### **CSV Export**
```typescript
// Export energy CSV
const r = await fetch('/api/cam/metrics/energy_csv', {
  method: 'POST',
  body: JSON.stringify({
    moves: planOut.value.moves,
    material_id: 'maple_hard',
    tool_d: 6.0,
    stepover: 0.45,
    stepdown: 1.5,
    job_name: 'pocket'
  })
})

const blob = await r.blob()
const a = document.createElement('a')
a.href = URL.createObjectURL(blob)
a.download = ''
a.click()
// Downloads: energy_pocket.csv
```

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Energy totals are zero | Check moves array has G1/G2/G3, stepover/stepdown > 0 |
| Heat timeseries shows no power | Verify material_id and machine_profile_id are valid |
| CSV filename is generic | Ensure job_name parameter is provided |
| Pie chart shows 100% "none" | Run plan with machine profile (accel/jerk limits) |

---

## 📋 Integration Checklist

**Backend:**
- [x] material_db.json (4 presets)
- [x] material_router.py (CRUD)
- [x] energy_model.py (volume proxy)
- [x] heat_timeseries.py (power binning)
- [x] cam_metrics_router.py (4 endpoints)
- [x] Register routers in main.py

**Frontend:**
- [x] Energy & Heat panel
- [x] Heat over Time card
- [x] Bottleneck pie chart
- [x] CSV export buttons
- [x] Chipload controls
- [x] CompareSettings modal

**CI/CD:**
- [x] 5 comprehensive tests

---

## 🎯 Key Features Summary

| Feature | Description | Endpoint |
|---------|-------------|----------|
| Energy Calculation | Volume × SCE → J | `/cam/metrics/energy` |
| Heat Partition | 70% chip, 20% tool, 10% work | (embedded) |
| Power Timeseries | Heat rate (W) over time | `/cam/metrics/heat_timeseries` |
| Energy CSV | Per-segment energy export | `/cam/metrics/energy_csv` |
| Bottleneck CSV | Per-segment limit tracking | `/cam/metrics/bottleneck_csv` |
| Material Database | 4 presets with SCE | `/material/*` |
| Chipload Enforcement | Optimizer constraint | (UI toggle) |

---

## 📚 See Also

- [MODULE_M3_COMPLETE.md](./MODULE_M3_COMPLETE.md) - Full documentation
- [ADAPTIVE_POCKETING_MODULE_L.md](./ADAPTIVE_POCKETING_MODULE_L.md) - Core toolpath system
- [MACHINE_PROFILES_MODULE_M.md](./MACHINE_PROFILES_MODULE_M.md) - Machine-aware physics
- [MODULE_M1_1_IMPLEMENTATION_SUMMARY.md](./MODULE_M1_1_IMPLEMENTATION_SUMMARY.md) - Bottleneck map
- [PATCH_L3_SUMMARY.md](./PATCH_L3_SUMMARY.md) - Jerk-aware time + optimizer

---

**Status:** ✅ Module M.3 Complete  
**Next:** Module M.4 (Thermal Cooling Strategies)
