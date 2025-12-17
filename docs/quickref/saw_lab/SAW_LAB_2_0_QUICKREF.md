# Saw Lab 2.0 — RMOS Integration Module

**Status:** ✅ Production Ready  
**Date:** December 4, 2025  
**Module:** Saw Lab 2.0

---

## 🎯 Overview

Saw Lab 2.0 integrates CNC saw blade operations as a first-class mode within the RMOS orchestration system. When a tool_id starts with `saw:`, all feasibility calculations and toolpath generation automatically switch to saw-specific algorithms.

### Key Features

- **5 Saw-Specific Calculators**: Heat, Deflection, Rim Speed, Bite Load, Kickback
- **Automatic Mode Detection**: `saw:` prefix triggers saw mode
- **Blade Parameter Parsing**: Tool ID encodes blade diameter, tooth count, kerf
- **Safety-First Design**: Kickback risk evaluation, rim speed limits
- **RMOS Compatible**: Seamless integration with existing endpoints

---

## 📁 Module Structure

```
services/api/app/saw_lab/
├── __init__.py              # SawLabService facade
├── models.py                # Pydantic models (SawContext, SawDesign, etc.)
├── geometry.py              # Blade arc calculations, tooth engagement
├── path_planner.py          # Cut sequence planning
├── toolpath_builder.py      # G-code generation
├── risk_evaluator.py        # Safety risk assessment
└── calculators/
    ├── __init__.py          # FeasibilityCalculatorBundle
    ├── saw_heat.py          # Heat buildup calculator
    ├── saw_deflection.py    # Blade deflection calculator
    ├── saw_rimspeed.py      # Rim speed safety calculator
    ├── saw_bite_load.py     # Tooth bite load calculator
    └── saw_kickback.py      # Kickback risk calculator
```

---

## 🔧 Tool ID Format

Saw tools use a prefixed ID format:

```
saw:<diameter_inches>_<tooth_count>_<kerf_mm>
```

### Examples

| Tool ID | Blade Diameter | Teeth | Kerf |
|---------|---------------|-------|------|
| `saw:10_24_3.0` | 10" (254mm) | 24 | 3.0mm |
| `saw:8_40_2.5` | 8" (203mm) | 40 | 2.5mm |
| `saw:12_60_3.5` | 12" (305mm) | 60 | 3.5mm |

### Default Values

If parsing fails, these defaults are used:
- Blade diameter: 254mm (10")
- Tooth count: 24
- Kerf: 3.0mm

---

## 📊 Calculators

### Weight Distribution

| Calculator | Weight | Description |
|------------|--------|-------------|
| Bite Load | 25% | Chip load per tooth |
| Heat | 20% | Heat buildup risk |
| Rim Speed | 20% | Peripheral velocity safety |
| Kickback | 20% | Kickback risk factors |
| Deflection | 15% | Blade deflection |

### 1. Bite Load Calculator

Calculates chip load per tooth (feed per tooth):

```
bite_load_mm = feed_rate / (RPM × tooth_count)
```

**Optimal Ranges:**
- Softwood: 0.05-0.15 mm/tooth
- Hardwood: 0.03-0.10 mm/tooth
- Plywood: 0.03-0.08 mm/tooth
- MDF: 0.05-0.12 mm/tooth

### 2. Heat Calculator

Evaluates heat buildup based on rim speed and feed rate:

```
heat_index = 100 × speed_factor × feed_factor × dust_factor
```

**Factors:**
- Rim speed: Optimal 40-60 m/s for wood
- Feed per tooth: Too low = burning, too high = overload
- Dust collection: Reduces heat accumulation

### 3. Rim Speed Calculator

Calculates peripheral blade velocity:

```
rim_speed_m_s = π × diameter × RPM / (1000 × 60)
```

**Safe Ranges (carbide-tipped):**
- Wood: 40-80 m/s
- Aluminum: 20-40 m/s
- Acrylic: 30-60 m/s

### 4. Kickback Calculator

Evaluates kickback risk based on multiple factors:

**Risk Factors:**
- Cut type (rip cuts highest risk)
- Blade exposure above stock
- Feed rate (too fast or slow)
- Bevel/miter angles
- Stock thickness

### 5. Deflection Calculator

Assesses blade deflection potential:

**Factors:**
- Blade diameter to kerf ratio
- Cut depth relative to blade diameter
- Feed pressure from feed rate

---

## 🔌 API Usage

### Saw Mode Activation

Simply use a tool_id with the `saw:` prefix:

```json
{
  "design": {
    "outer_diameter_mm": 300.0,
    "ring_count": 1,
    "pattern_type": "crosscut"
  },
  "context": {
    "material_id": "hardwood_maple",
    "tool_id": "saw:10_24_3.0"
  }
}
```

### Response Example

```json
{
  "score": 77.5,
  "risk_bucket": "YELLOW",
  "warnings": [
    "Moderate kickback risk (2 factors)"
  ],
  "efficiency": 77.5,
  "estimated_cut_time_seconds": 6.2,
  "calculator_results": {
    "heat": {
      "calculator_name": "heat",
      "score": 75.0,
      "warning": "Moderate heat risk (index: 70.0)",
      "metadata": {
        "rim_speed_m_s": 66.32,
        "heat_index": 70.0
      }
    },
    "bite_load": {
      "calculator_name": "bite_load",
      "score": 100.0,
      "warning": null,
      "metadata": {
        "bite_load_mm": 0.025,
        "optimal_range_mm": [0.03, 0.10]
      }
    }
  }
}
```

---

## 🛤️ Toolpath Generation

Saw toolpaths follow a simple pattern:

1. **Rapid** to approach position (safe Z + Y offset)
2. **Plunge** to cut depth (30% feed rate)
3. **Feed** through material (full feed rate)
4. **Retract** to safe Z

### G-code Output

```gcode
G21               ; Units: mm
G90               ; Absolute positioning
G17               ; XY plane selection
S5000             ; Spindle speed
M3                ; Spindle on CW
G0 Z40.0000       ; Move to safe height
G0 X0.0000 Y-20.0000  ; Move to cut 1 approach
G1 Z-2.0000 F900.0    ; Plunge for cut 1
G1 Y320.0000 F3000.0  ; Cut 1: crosscut
G0 Z40.0000           ; Retract after cut 1
M5                ; Spindle stop
M30               ; Program end
```

---

## ⚠️ Safety Considerations

### Risk Levels

| Score | Risk Bucket | Action |
|-------|-------------|--------|
| ≥80 | GREEN | Safe to proceed |
| 50-79 | YELLOW | Proceed with caution |
| <50 | RED | Do not proceed |

### Automatic Warnings

The system automatically generates warnings for:
- High rim speed (approaching blade limits)
- Low bite load (burning risk)
- High kickback risk (multiple factors)
- Excessive blade deflection

---

## 🧪 Testing

### Test Script

```powershell
.\scripts\test_saw_lab_2_0.ps1
```

### Manual Test

```powershell
$body = @{
    design = @{
        outer_diameter_mm = 300.0
        ring_count = 1
        pattern_type = "crosscut"
    }
    context = @{
        tool_id = "saw:10_24_3.0"
    }
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Uri "http://localhost:8010/api/rmos/feasibility" `
    -Method POST -Body $body -ContentType "application/json"
```

---

## 📚 See Also

- [RMOS 2.0 Implementation Quickref](./RMOS_2_0_IMPLEMENTATION_QUICKREF.md)
- [Material Conversion Tools](./scripts/MaterialTools.ps1)
- [Test Data](./tests/data/saw_lab_materials.csv)

---

## ✅ Integration Checklist

- [x] Create `saw_lab/` module with models, geometry, calculators
- [x] Implement 5 saw-specific calculators
- [x] Add `saw_engine.py` in toolpath module
- [x] Update `feasibility_scorer.py` to branch on saw mode
- [x] Update `toolpath/service.py` to branch on saw mode
- [x] Create test script `test_saw_lab_2_0.ps1`
- [x] Create test data fixtures
- [x] Document module

---

**Module:** Saw Lab 2.0  
**Version:** 1.0  
**Status:** ✅ Production Ready
