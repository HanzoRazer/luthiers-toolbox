# Wave 19: Fan-Fret CAM Quick Reference

**Status:** ✅ Production Ready  
**Version:** 1.0  
**Test Coverage:** 47/49 (96%)

---

## 🎯 Quick Start (5 Minutes)

### 1. Enable Fan-Fret Mode
1. Navigate to **Instrument Geometry** panel
2. Check ☑️ **Fan-Fret (Multi-Scale)** checkbox
3. Configure scales:
   - **Treble Scale:** 647.7 mm (25.5")
   - **Bass Scale:** 660.4 mm (26")
   - **Perpendicular Fret:** 7

### 2. Generate CAM
1. Click **🚀 Generate CAM Preview**
2. Wait 2-3 seconds for calculation
3. Verify angled fret lines in preview
4. Download DXF or G-code

---

## 📐 Common Configurations

### 7-String Extended Range
- **Treble:** 647.7 mm (25.5")
- **Bass:** 685.8 mm (27")
- **Perpendicular:** 7 or 8
- **Use Case:** Drop-tuned metal, extended-range guitars

### Benedetto-Style Jazz
- **Treble:** 635 mm (25")
- **Bass:** 660.4 mm (26")
- **Perpendicular:** 9 or 10
- **Use Case:** Archtop jazz guitars, ergonomic feel

### Strandberg Aggressive
- **Treble:** 635 mm (25")
- **Bass:** 698.5 mm (27.5")
- **Perpendicular:** 7
- **Use Case:** Maximum ergonomics, heavy drop tunings

---

## 🎨 UI Components

### Fan-Fret Controls (When Enabled)
```
☑️ Fan-Fret (Multi-Scale)

  Treble Scale: [647.7] mm
  Bass Scale:   [660.4] mm
  Perpendicular Fret: [7] fret #

  ℹ️ Fan-fret CAM with per-fret risk analysis (Wave 19)
```

### Risk Color Codes (Future: Wave 20)
- 🟢 **GREEN:** Standard parameters OK
- 🟡 **YELLOW:** Reduce feed 10-15%
- 🔴 **RED:** Slow feed 25%, add coolant

---

## 🔧 API Integration

### POST /api/cam/fret_slots/preview

**Fan-Fret Request:**
```json
{
  "model_id": "lp_24_75",
  "mode": "fan",
  "treble_scale_mm": 647.7,
  "bass_scale_mm": 660.4,
  "perpendicular_fret": 7,
  "fret_count": 22,
  "nut_width_mm": 43.0,
  "heel_width_mm": 56.0,
  "slot_width_mm": 0.6,
  "slot_depth_mm": 3.0,
  "post_id": "GRBL"
}
```

**Standard Request (Comparison):**
```json
{
  "model_id": "lp_24_75",
  "mode": "standard",
  "scale_length_mm": 628.65,
  "fret_count": 22,
  "nut_width_mm": 43.0,
  "heel_width_mm": 56.0,
  "slot_width_mm": 0.6,
  "slot_depth_mm": 3.0,
  "post_id": "GRBL"
}
```

**Response:**
```json
{
  "toolpaths": [{"fret_number": 1, "bass_point": [x,y], "treble_point": [x,y], "angle_rad": 0.091}],
  "per_fret_risks": [{"fret_number": 1, "overall_risk": "GREEN", "angle_deg": 5.2}],
  "risk_summary": {"green_count": 18, "yellow_count": 3, "red_count": 1},
  "dxf_content": "...",
  "gcode_content": "...",
  "statistics": {"total_length_mm": 946.0, "estimated_time_s": 85.14}
}
```

---

## 📊 Risk Analysis

### Chipload Risk Thresholds
| Angle | Risk | Action |
|-------|------|--------|
| 0-15° | 🟢 GREEN | Standard feed |
| 15-25° | 🟡 YELLOW | Reduce feed 10-15% |
| 25+° | 🔴 RED | Reduce feed 25%, coolant |

### Heat Risk Factors
- **Tool engagement length:** Longer slots = more heat
- **Angle:** Steeper = longer engagement
- **Material:** Ebony > Rosewood > Maple

### Overall Risk
- Takes **worst** of chipload + heat
- Single RED = overall RED
- Two YELLOW = overall YELLOW
- Otherwise GREEN

---

## 🧪 Testing

### Run All Tests
```powershell
.\Test-Wave19-FanFretGeometry.ps1  # Phase A: 9/9
.\Test-Wave19-FanFretCAM.ps1       # Phase B: 17/19
.\Test-Wave19-PerFretRisk.ps1      # Phase C: 14/14
.\Test-Wave19-PhaseD-Frontend.ps1  # Phase D: 7/7
```

### Quick Smoke Test
```powershell
$body = @{
  model_id = "lp_24_75"
  mode = "fan"
  treble_scale_mm = 647.7
  bass_scale_mm = 660.4
  perpendicular_fret = 7
  fret_count = 22
  nut_width_mm = 43.0
  heel_width_mm = 56.0
  slot_width_mm = 0.6
  slot_depth_mm = 3.0
  post_id = "GRBL"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/cam/fret_slots/preview" `
  -Method Post -ContentType "application/json" -Body $body
```

---

## 🐛 Troubleshooting

### Issue: Button Still Disabled
**Cause:** Old browser cache  
**Fix:** Hard refresh (Ctrl+Shift+R)

### Issue: Frets Not Angled
**Cause:** API receiving mode=standard  
**Fix:** Verify fan-fret checkbox is checked

### Issue: Perpendicular Fret Wrong
**Cause:** Input value out of range  
**Fix:** Set between 0 and fret_count

### Issue: API Error "model_id not found"
**Cause:** Invalid model ID  
**Fix:** Use "lp_24_75" or "strat_25_5"

### Issue: Risk Data Missing
**Cause:** Backend Phase C not deployed  
**Fix:** Verify `cam_fret_slots_router.py` registered

---

## 📦 File Locations

### Backend
- **Geometry:** `services/api/app/calculators/fret_math.py`
- **CAM:** `services/api/app/calculators/fret_slots_cam.py`
- **Risk:** `services/api/app/calculators/feasibility_fusion.py`
- **API:** `services/api/app/routers/cam_fret_slots_router.py`

### Frontend
- **UI:** `packages/client/src/components/InstrumentGeometryPanel.vue`
- **Store:** `packages/client/src/stores/instrumentGeometryStore.ts`

### Tests
- `Test-Wave19-FanFretGeometry.ps1` (Phase A)
- `Test-Wave19-FanFretCAM.ps1` (Phase B)
- `Test-Wave19-PerFretRisk.ps1` (Phase C)
- `Test-Wave19-PhaseD-Frontend.ps1` (Phase D)

---

## 🚀 Next Steps

### User Testing
1. Enable fan-fret mode
2. Test 3+ scale configurations
3. Verify DXF/G-code downloads
4. Report visual issues

### Future Enhancements (Wave 20)
1. Color-coded fret lines by risk
2. Tooltips with angle/risk data
3. Risk legend in preview panel
4. Export button for per-fret report

---

## 📚 See Also

- [Wave 19 Complete Summary](./WAVE19_COMPLETE_SUMMARY.md)
- [Adaptive Pocketing Module L](./ADAPTIVE_POCKETING_MODULE_L.md)
- [Machine Profiles Module M](./MACHINE_PROFILES_MODULE_M.md)
- [Copilot Instructions](./.github/copilot-instructions.md)

---

**Status:** ✅ Production Ready (47/49 tests passing)  
**Last Updated:** December 2024
