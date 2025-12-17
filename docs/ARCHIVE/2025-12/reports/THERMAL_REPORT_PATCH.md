# Thermal Report (Markdown) Patch — Implementation Summary

**Status:** ✅ Complete  
**Date:** November 2025  
**Type:** Drop-in Enhancement

---

## 🎯 Overview

Added **Markdown thermal report export** with ASCII sparklines, budget compliance tracking, and comprehensive job context. This provides a human-readable summary of energy/heat metrics suitable for documentation and sharing.

---

## 📦 What Was Added

### **1. Server Endpoint** (`cam_metrics_router.py`)

**New Endpoint:** `POST /api/cam/metrics/thermal_report_md`

**Features:**
- Material and machine context
- Energy totals (volume, energy, time)
- Heat partition table with budget compliance (OK/WARN/OVER)
- ASCII sparklines for chip/tool/work power over time
- Bottleneck distribution counts
- Safe filename generation

**Helper Functions:**
- `_sparkline(values, width=60)` - Generates ASCII sparkline using ▁▂▃▄▅▆▇█ characters
- `_state(val, lim)` - Budget state: OK (<85%), WARN (85-100%), OVER (>100%)

**Models:**
```python
class ThermalBudget(BaseModel):
    chip_j: float = 500.0
    tool_j: float = 150.0
    work_j: float = 100.0

class ThermalReportIn(BaseModel):
    moves: List[Dict[str, Any]]
    machine_profile_id: str = "Mach4_Router_4x8"
    material_id: str = "maple_hard"
    tool_d: float
    stepover: float          # 0..1
    stepdown: float
    bins: int = 200          # 10-5000
    job_name: Optional[str] = None
    budgets: ThermalBudget = ThermalBudget()
```

---

### **2. Client Button** (`AdaptivePocketLab.vue`)

**Location:** Heat over Time card (next to "Compute" button)

**Button:** "Export Report (MD)"
- Purple outline styling (matches theme)
- Disabled when no moves available
- Tooltip: "Export Thermal Report (Markdown)"

**Function:** `exportThermalReport()`
- Validates plan exists
- Builds request body with budgets (500J chip, 150J tool, 100J work)
- Downloads blob as `thermal_report_{job_name}.md`

---

### **3. CI Test** (`adaptive_pocket.yml`)

**Test:** "M.3 - Thermal report (Markdown) renders and names file"

**Validation Steps:**
1. Generate plan with moves
2. Call `/thermal_report_md` with budgets
3. Validate Content-Disposition filename (`LP_test.md`)
4. Validate Markdown sections present:
   - `# Thermal Report`
   - `## Totals`
   - `Power (J/s) sparklines`
   - `## Context`
   - `Heat partition`
   - `Bottleneck share`
5. Validate sparkline characters (▁-█) present

---

## 📄 Example Report Output

```markdown
# Thermal Report — LP_test

_Generated: 2025-11-05 14:32:15Z_

## Context
- **Machine**: `Mach4_Router_4x8`  
- **Material**: `Hard Maple` (`maple_hard`)  
- **Tool Ø**: 6.000 mm  
- **Step-over**: 45.0%  
- **Step-down**: 1.500 mm  
- **Bins**: 120  

## Totals
- **Volume removed**: 6000 mm³  
- **Total energy**: 3300.0 J  
- **Time (est.)**: 32.5 s  

### Heat partition
| Sink | Joules | Budget | Status |
|---|---:|---:|:--:|
| Chip | 2310.0 | 500.0 | OVER |
| Tool | 660.0 | 150.0 | OVER |
| Work | 330.0 | 100.0 | OVER |

## Power (J/s) sparklines
```
Chip: ▂▃▄▅▆▇█▇▆▅▄▃▂▁▂▃▄▅▆▇▇▆▅▄▃▂▁▂▃▄▅▆▇▇▆▅▄▃▂▁
Tool: ▁▂▂▃▃▄▄▄▃▃▂▂▁▁▂▂▃▃▄▄▄▃▃▂▂▁▁▂▂▃▃▄▄▄▃▃▂▂▁
Work: ▁▁▂▂▂▃▃▃▂▂▂▁▁▁▁▂▂▂▃▃▃▂▂▂▁▁▁▁▂▂▂▃▃▃▂▂▂▁▁
```

## Bottleneck share (counts)
- feed_cap: 45, accel: 23, jerk: 12, none: 78

> Notes: Sparklines are ASCII summaries of power over normalized time. Use the CSV exports for exact values.
```

---

## 🧮 Key Algorithms

### **Sparkline Generation**
```python
def _sparkline(values, width=60):
    # Downsample to width if needed
    if len(values) > width:
        step = len(values) / width
        vals = [values[int(i*step)] for i in range(width)]
    else:
        vals = values[:]
    
    # Normalize to 0..7 and map to spark characters
    vmax = max(vals) or 1.0
    return "".join(_SPARK[min(7, int((v / vmax) * 7))] for v in vals)
```

### **Budget State**
```python
def _state(val, lim):
    if val <= lim * 0.85: return "OK"    # <85% of limit
    if val <= lim: return "WARN"         # 85-100% of limit
    return "OVER"                        # >100% of limit
```

---

## 🧪 Testing

### **Local Test**
```powershell
# Start API
cd services/api
uvicorn app.main:app --reload --port 8000

# Test endpoint
curl -X POST http://localhost:8000/cam/metrics/thermal_report_md `
  -H 'Content-Type: application/json' `
  -d '{
    "moves": [...],
    "machine_profile_id": "Mach4_Router_4x8",
    "material_id": "maple_hard",
    "tool_d": 6.0,
    "stepover": 0.45,
    "stepdown": 1.5,
    "bins": 200,
    "job_name": "test_pocket",
    "budgets": {"chip_j": 500, "tool_j": 150, "work_j": 100}
  }' `
  -o thermal_report.md

# View report
cat thermal_report.md
```

### **CI Test**
GitHub Actions automatically validates:
- Correct filename generation
- Markdown structure completeness
- Sparkline character presence

---

## 📊 Budget Defaults

| Sink | Default Budget (J) | Typical Use |
|------|-------------------:|-------------|
| Chip | 500.0 | Evacuated with coolant/chips |
| Tool | 150.0 | Tool wear tracking threshold |
| Work | 100.0 | Workpiece heat capacity limit |

---

## 🎨 UI Integration

**Button Location:** Heat over Time card (right column)

**Styling:**
- Purple outline (`border-purple-600`)
- Hover effect (`hover:bg-purple-50`)
- Disabled state when no moves available
- Consistent with existing button theme

**User Flow:**
1. User clicks "Plan" to generate toolpath
2. User clicks "Export Report (MD)" in Heat section
3. Browser downloads `thermal_report_pocket.md`
4. User can open in any markdown viewer or text editor

---

## 🔧 Configuration

### **Customizable Parameters**

```typescript
// In exportThermalReport() function:
budgets: {
  chip_j: 500.0,    // Adjust based on material/cooling
  tool_j: 150.0,    // Adjust based on tool life targets
  work_j: 100.0     // Adjust based on workpiece size
}
bins: 200           // More bins = finer sparkline resolution (10-5000)
```

---

## 📈 Use Cases

1. **Documentation:** Attach to job sheets for production reference
2. **Analysis:** Share with team for process improvement
3. **Compliance:** Track against thermal budgets for quality control
4. **Troubleshooting:** Diagnose overheating issues with sparkline patterns
5. **Optimization:** Compare before/after reports when tuning parameters

---

## ✅ Files Modified

| File | Changes | Lines Added |
|------|---------|------------:|
| `cam_metrics_router.py` | Added endpoint + helpers | ~145 |
| `AdaptivePocketLab.vue` | Added button + function | ~50 |
| `adaptive_pocket.yml` | Added CI test | ~65 |
| **Total** | | **~260** |

---

## 🚀 Next Steps

### **Immediate Use**
- Report is ready to use in AdaptivePocketLab UI
- CI test ensures continued functionality
- No additional configuration needed

### **Future Enhancements**
- **Custom budgets UI:** Add input fields for chip_j/tool_j/work_j
- **Multi-format export:** Add PDF/HTML options
- **Chart embedding:** Convert sparklines to PNG/SVG for better reports
- **Historical tracking:** Store reports for trend analysis

---

## 🎯 Integration Checklist

- [x] Server endpoint (`/thermal_report_md`)
- [x] Sparkline helper function
- [x] Budget compliance logic
- [x] Client export button
- [x] Client download function
- [x] CI smoke test
- [x] Markdown content validation
- [x] Filename safety (safe_stem)

---

## 📚 See Also

- [MODULE_M3_COMPLETE.md](./MODULE_M3_COMPLETE.md) - Full M.3 documentation
- [MODULE_M3_QUICKREF.md](./MODULE_M3_QUICKREF.md) - Quick reference
- [cam_metrics_router.py](./services/api/app/routers/cam_metrics_router.py) - Endpoint implementation
- [AdaptivePocketLab.vue](./packages/client/src/components/AdaptivePocketLab.vue) - UI integration

---

**Status:** ✅ Thermal Report Patch Complete  
**Type:** Drop-in Enhancement (no breaking changes)  
**Ready for:** Production Use
