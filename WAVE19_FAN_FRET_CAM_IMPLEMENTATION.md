# Wave 19: Fan-Fret CAM Implementation

**Status:** 🟡 Ready to Start  
**Date:** December 9, 2025  
**Branch:** `feature/client-migration`  
**Builds On:** Waves 15-18 (Instrument Geometry + Fretboard CAM)

---

## 🎯 Overview

Implement complete fan-fret (multi-scale) CAM generation for fretboard slot cutting. This wave extends the existing fretboard CAM system (`fret_slots_cam.py`) to support:

1. **Fan-fret geometry calculation** (perpendicular fret, angled slots)
2. **Multi-scale toolpath generation** (treble vs bass scale lengths)
3. **Per-fret risk diagnostics** (chipload/heat/deflection per fret)
4. **Enhanced UI controls** (already partially implemented in `InstrumentGeometryPanel.vue`)

---

## 📋 Current State Analysis

### ✅ What's Already Done (Waves 15-18)
- ✅ Standard fretboard CAM generation (`fret_slots_cam.py`)
- ✅ DXF R12 export with LINE entities
- ✅ G-code generation (GRBL, Mach4)
- ✅ Material-aware feedrates
- ✅ Compound radius support
- ✅ Feasibility scoring system
- ✅ Frontend UI with model selection

### 🔶 What's Partially Done
- 🔶 Fan-fret UI controls (exists but disabled with warning)
- 🔶 Multi-scale spec in `InstrumentModelId` enum
- 🔶 Fan-fret geometry types defined

### ❌ What's Missing (Wave 19 Scope)
- ❌ Fan-fret geometry calculation algorithm
- ❌ Angled slot toolpath generation
- ❌ Perpendicular fret calculation
- ❌ Per-fret feasibility metrics
- ❌ Backend fan-fret mode support

---

## 🏗️ Architecture

### Backend Components

```
services/api/app/
├── calculators/
│   └── fret_slots_cam.py          # Extend with fan-fret mode
│
├── instrument_geometry/
│   ├── neck/
│   │   └── fret_math.py           # Add multi-scale calculations
│   └── body/
│       └── fretboard_geometry.py  # Add fan-fret geometry helpers
│
└── rmos/
    └── feasibility_fusion.py      # Add per-fret risk analysis
```

### Frontend Components

```
packages/client/src/
├── stores/
│   └── instrumentGeometryStore.ts  # Enable fan-fret controls
│
└── components/
    ├── InstrumentGeometryPanel.vue # Remove warning banner
    └── FretboardPreviewSvg.vue     # Add per-fret risk coloring
```

---

## 📝 Implementation Tasks

### Phase A: Fan-Fret Geometry Math (Backend)

**File:** `services/api/app/instrument_geometry/neck/fret_math.py`

**New Functions:**
```python
def compute_fan_fret_positions(
    treble_scale_mm: float,
    bass_scale_mm: float,
    num_frets: int,
    perpendicular_fret: int = 7,
    nut_width_mm: float = 42.0,
    heel_width_mm: float = 52.0
) -> List[FanFretPoint]:
    """
    Calculate fan-fret geometry with angled slots.
    
    Returns:
        List of FanFretPoint with:
        - fret number
        - treble_x, bass_x positions
        - angle (radians)
        - perpendicular flag
    """
    pass

def calculate_perpendicular_fret(
    treble_scale_mm: float,
    bass_scale_mm: float,
    target_fret: int = 7
) -> Tuple[float, float]:
    """
    Calculate the intersection point where the specified fret
    should be perpendicular to the centerline.
    """
    pass
```

**Tests:** `Test-Wave19-FanFretMath.ps1` (8 tests)
- Test perpendicular fret calculation
- Test angled slot geometry
- Test boundary cases (perpendicular at nut/heel)
- Test scale convergence

---

### Phase B: Fan-Fret CAM Generation (Backend)

**File:** `services/api/app/calculators/fret_slots_cam.py`

**Modifications:**
```python
def generate_fret_slot_cam(
    model: InstrumentSpec,
    material_id: str = "rosewood",
    tool_diameter_mm: float = 1.5,
    mode: Literal["standard", "fan"] = "standard",  # NEW
    treble_scale_mm: Optional[float] = None,        # NEW
    bass_scale_mm: Optional[float] = None,          # NEW
    perpendicular_fret: Optional[int] = None,       # NEW
    post_processor: str = "GRBL",
    units: str = "mm"
) -> FretSlotCamResult:
    """
    Extended to support fan-fret mode.
    """
    if mode == "fan":
        return _generate_fan_fret_cam(...)
    else:
        return _generate_standard_cam(...)

def _generate_fan_fret_cam(
    treble_scale_mm: float,
    bass_scale_mm: float,
    perpendicular_fret: int,
    num_frets: int,
    nut_width_mm: float,
    heel_width_mm: float,
    tool_diameter_mm: float,
    slot_depth_mm: float,
    material: MaterialProfile
) -> FretSlotCamResult:
    """
    Generate toolpaths for angled fan-fret slots.
    
    Key differences from standard:
    - Each slot has unique angle
    - Perpendicular fret is straight
    - DXF layer: FRET_SLOTS_FAN
    """
    pass
```

**DXF Changes:**
- New layer: `FRET_SLOTS_FAN`
- LINE entities with rotation metadata
- Slot angle annotations

**G-code Changes:**
- Rotated slot cutting paths
- Tool compensation for angled cuts
- Optional spiral entry for angled slots

**Tests:** `Test-Wave19-FanFretCAM.ps1` (10 tests)
- Test fan-fret DXF export
- Test angled slot G-code
- Test perpendicular fret (should be straight)
- Test material-aware feeds with fan-fret
- Test compound radius with fan-fret

---

### Phase C: Per-Fret Risk Analysis (Backend)

**File:** `services/api/app/rmos/feasibility_fusion.py`

**New Functions:**
```python
def evaluate_per_fret_feasibility(
    fret_toolpaths: List[FretToolpath],
    material: MaterialProfile,
    tool_diameter_mm: float
) -> List[PerFretRisk]:
    """
    Calculate risk metrics for each individual fret slot.
    
    Returns:
        List of PerFretRisk with:
        - fret number
        - chipload_risk (GREEN/YELLOW/RED)
        - heat_risk
        - deflection_risk
        - rim_speed_risk
    """
    pass

@dataclass
class PerFretRisk:
    fret: int
    chipload_risk: RiskLevel
    heat_risk: RiskLevel
    deflection_risk: RiskLevel
    rim_speed_risk: RiskLevel
    recommendations: List[str]
```

**Router Extension:**
```python
# In cam_preview_router.py
class FretSlotsPreviewResponse(BaseModel):
    # ... existing fields ...
    per_fret_metrics: Optional[List[PerFretRisk]] = None  # NEW
```

**Tests:** `Test-Wave19-PerFretRisk.ps1` (6 tests)
- Test per-fret risk calculation
- Test risk aggregation across frets
- Test worst-case fret identification
- Test risk recommendations per fret

---

### Phase D: Frontend Integration

**File:** `packages/client/src/stores/instrumentGeometryStore.ts`

**Changes:**
```typescript
export const useInstrumentGeometryStore = defineStore('instrumentGeometry', {
  state: () => ({
    // ... existing state ...
    fanFretEnabled: false,
    trebleScaleLength: 648.0,  // mm (25.5")
    bassScaleLength: 660.0,    // mm (26.0")
    perpendicularFret: 7,
    perFretDiagnostics: [] as PerFretDiagnostic[]
  }),

  actions: {
    async generatePreview() {
      const payload = {
        model_id: this.selectedModelId,
        mode: this.fanFretEnabled ? 'fan' : 'standard',
        // ... existing fields ...
        treble_scale_mm: this.fanFretEnabled ? this.trebleScaleLength : undefined,
        bass_scale_mm: this.fanFretEnabled ? this.bassScaleLength : undefined,
        perpendicular_fret: this.fanFretEnabled ? this.perpendicularFret : undefined
      }
      
      const response = await fetch('/api/cam/fret_slots/preview', {
        method: 'POST',
        body: JSON.stringify(payload)
      })
      
      const data = await response.json()
      this.previewResponse = data
      
      // NEW: Store per-fret diagnostics if available
      if (data.per_fret_metrics) {
        this.perFretDiagnostics = data.per_fret_metrics.map(normalizeFretRisk)
      }
    }
  }
})
```

**File:** `packages/client/src/components/InstrumentGeometryPanel.vue`

**Changes:**
```vue
<!-- Remove warning banner -->
<div v-if="store.fanFretEnabled" class="fan-fret-controls">
  <!-- Existing controls remain -->
  
  <!-- Add perpendicular fret control -->
  <div class="input-group">
    <label>Perpendicular Fret</label>
    <input
      type="number"
      v-model.number="store.perpendicularFret"
      step="1"
      min="0"
      :max="store.fretboardSpec.num_frets"
      class="number-input"
    />
  </div>
  
  <!-- REMOVE this warning: -->
  <!-- <div class="info-banner warning">
    ⚠️ Fan-fret CAM generation not yet implemented
  </div> -->
</div>
```

**File:** `packages/client/src/components/FretboardPreviewSvg.vue`

**Enhancement:** Add per-fret risk coloring
```vue
<template>
  <svg :viewBox="`0 0 ${width} ${length}`">
    <!-- Fretboard outline -->
    <path :d="fretboardPath" fill="#e8d4b8" stroke="#8b7355" stroke-width="2"/>
    
    <!-- Fret slots with risk-based coloring -->
    <g v-for="fret in frets" :key="fret.fret">
      <line
        :x1="fret.treble_x_mm"
        :y1="fret.from_bridge_mm"
        :x2="fret.bass_x_mm"
        :y2="fret.from_bridge_mm"
        :stroke="getFretRiskColor(fret.fret)"
        stroke-width="2"
        :transform="getFretTransform(fret)"
      />
      
      <!-- Tooltip on hover -->
      <title>
        Fret {{ fret.fret }}
        Angle: {{ (fret.angle_rad * 180 / Math.PI).toFixed(2) }}°
        Risk: {{ getFretRiskLevel(fret.fret) }}
      </title>
    </g>
    
    <!-- Risk legend -->
    <g class="risk-legend">
      <rect x="10" y="10" width="15" height="3" fill="#10b981"/> <!-- Green -->
      <text x="30" y="15" font-size="12">Safe</text>
      
      <rect x="10" y="20" width="15" height="3" fill="#f59e0b"/> <!-- Yellow -->
      <text x="30" y="25" font-size="12">Caution</text>
      
      <rect x="10" y="30" width="15" height="3" fill="#ef4444"/> <!-- Red -->
      <text x="30" y="35" font-size="12">Danger</text>
    </g>
  </svg>
</template>

<script setup lang="ts">
const getFretRiskColor = (fretNum: number): string => {
  const diagnostic = store.perFretDiagnostics.find(d => d.fret === fretNum)
  if (!diagnostic) return '#6b7280' // gray for unknown
  
  // Worst-case color across all risk categories
  const risks = [
    diagnostic.chipload_risk,
    diagnostic.heat_risk,
    diagnostic.deflection_risk
  ]
  
  if (risks.includes('danger')) return '#ef4444'  // red
  if (risks.includes('warning')) return '#f59e0b' // yellow
  return '#10b981' // green
}

const getFretTransform = (fret: FretGeometry): string => {
  if (Math.abs(fret.angle_rad) < 0.001) return '' // straight fret
  
  const centerX = (fret.treble_x_mm + fret.bass_x_mm) / 2
  const centerY = fret.from_bridge_mm
  const angleDeg = fret.angle_rad * 180 / Math.PI
  
  return `rotate(${angleDeg}, ${centerX}, ${centerY})`
}
</script>
```

**Tests:** `Test-Wave19-Frontend.ps1` (7 tests)
- Test fan-fret controls enabled
- Test perpendicular fret selector
- Test API payload with fan-fret params
- Test per-fret risk color mapping
- Test SVG rotation transforms

---

## 📊 Success Criteria

### Backend
- [ ] Fan-fret geometry calculations accurate (±0.01mm)
- [ ] Perpendicular fret calculation correct
- [ ] Angled slot DXF export valid (loads in Fusion 360)
- [ ] G-code for angled slots generated correctly
- [ ] Per-fret risk metrics calculated
- [ ] All 24 backend tests passing (8+10+6)

### Frontend
- [ ] Fan-fret controls fully functional
- [ ] Warning banner removed
- [ ] Per-fret risk coloring displayed
- [ ] SVG transforms accurate for angled frets
- [ ] All 7 frontend tests passing

### Integration
- [ ] End-to-end fan-fret workflow (UI → API → CAM)
- [ ] DXF export works for fan-fret boards
- [ ] G-code export works for fan-fret boards
- [ ] Feasibility scoring works per-fret

---

## 🔍 Testing Strategy

### Unit Tests (Backend)
```powershell
# Math validation
.\Test-Wave19-FanFretMath.ps1

# CAM generation
.\Test-Wave19-FanFretCAM.ps1

# Risk analysis
.\Test-Wave19-PerFretRisk.ps1
```

### Integration Tests
```powershell
# End-to-end fan-fret workflow
.\Test-Wave19-E2E.ps1
```

### Frontend Tests
```powershell
# UI controls and rendering
.\Test-Wave19-Frontend.ps1
```

---

## 📚 Reference Materials

### Fan-Fret Theory
- **Perpendicular Fret:** The fret where treble and bass strings intersect at 90° to centerline
- **Scale Convergence:** Treble scale < Bass scale → fan angle opens toward bridge
- **Common Configs:**
  - 7-string: 25.5" treble, 27" bass, perpendicular @ 7th fret
  - 8-string: 25.5" treble, 28" bass, perpendicular @ 8th fret

### Existing Code References
- `InstrumentModelId` enum (has multi-scale specs)
- `InstrumentGeometryPanel.vue` (fan-fret UI already exists)
- `fret_slots_cam.py` (standard CAM generation)

---

## 🚀 Implementation Order

1. **Phase A: Math** (3-4 hours)
   - Implement fan-fret geometry calculations
   - Add tests
   - Validate against known fan-fret specs

2. **Phase B: CAM** (4-5 hours)
   - Extend `generate_fret_slot_cam()` with fan mode
   - Implement angled slot toolpaths
   - DXF/G-code export for fan-fret
   - Add tests

3. **Phase C: Risk** (2-3 hours)
   - Implement per-fret risk analysis
   - Add to preview endpoint response
   - Add tests

4. **Phase D: Frontend** (2-3 hours)
   - Enable fan-fret controls
   - Add per-fret risk visualization
   - Remove warning banner
   - Add tests

**Total Estimated Time:** 11-15 hours

---

## 📝 Next Steps

1. Create feature branch: `feature/wave19-fan-fret-cam`
2. Implement Phase A (math layer)
3. Run tests and validate
4. Implement Phase B (CAM generation)
5. Implement Phase C (risk analysis)
6. Implement Phase D (frontend)
7. Integration testing
8. Merge to `feature/client-migration`

---

## 🔗 Related Documentation

- [WAVE15_18_COMPLETE_SUMMARY.md](./WAVE15_18_COMPLETE_SUMMARY.md) - Foundation
- [WAVE17_TODO.md](./WAVE17_TODO.md) - Previous wave tasks
- [Wave 16 – Fan-Fret_ Per-Fret Diagnostics UI.txt](./Wave 16 – Fan-Fret_ Per-Fret Diagnostics UI.txt) - UI design notes
- [Instrument_Geometry_Wave_16_Tier1_Real_Geometry.txt](./Instrument_Geometry_Wave_16_Tier1_Real_Geometry.txt) - Geometry specs

---

**Status:** ✅ Ready for implementation  
**Blockers:** None - all dependencies (Waves 15-18) are complete  
**Next Wave:** Wave 20 (Bridge CAM generation)
