# Helical Ramping Post-Processor Presets

**Feature:** Controller-aware G-code generation for helical entry toolpaths  
**Version:** v16.1.1  
**Date:** November 7, 2025  
**Status:** ✅ Implemented

---

## 🎯 Overview

The helical ramping endpoint now supports **4 CNC controller presets** that automatically adjust G-code output for controller-specific quirks:

| Preset | Arc Mode | Dwell Command | Notes |
|--------|----------|---------------|-------|
| **GRBL** | I,J | G4 P (ms) | Standard hobbyist CNC (Arduino-based) |
| **Mach3** | I,J | G4 P (ms) | Windows CNC controller |
| **Haas** | R | G4 S (sec) | Industrial VMC, **prefers R-mode**, **seconds for dwell** |
| **Marlin** | I,J | G4 P (ms) | 3D printer firmware adapted for CNC |

**Key Benefit:** Single API endpoint auto-generates controller-compatible G-code without manual post-processing.

---

## 📦 Implementation Files

### **Backend**
- `services/api/app/utils/post_presets.py` - Preset configuration module
- `services/api/app/routers/cam_helical_v161_router.py` - Updated router with preset support

### **Frontend**
- `packages/client/src/api/v161.ts` - TypeScript type with `post_preset?` field
- `packages/client/src/views/HelicalRampLab.vue` - UI dropdown for preset selection

### **Testing**
- `tools/smoke_helix_posts.ps1` - PowerShell smoke test for all presets
- `Makefile` - Unix/Linux smoke test target (`make smoke-helix-posts`)

---

## 🔌 API Usage

### **Request (with preset)**
```json
POST /api/cam/toolpath/helical_entry
{
  "cx": 0, "cy": 0, "radius_mm": 6.0, "direction": "CCW",
  "plane_z_mm": 5.0, "start_z_mm": 0.0, "z_target_mm": -3.0,
  "pitch_mm_per_rev": 1.5, "feed_xy_mm_min": 600,
  "ij_mode": true, "absolute": true, "units_mm": true,
  "safe_rapid": true, "dwell_ms": 500, "max_arc_degrees": 180,
  "post_preset": "Haas"  // ← NEW: GRBL | Mach3 | Haas | Marlin
}
```

### **Response**
```json
{
  "ok": true,
  "gcode": "(CCW Helical Z-Ramp, r=6 pitch=1.5 startZ=0 targetZ=-3)\n(Post preset: Haas)\nG21\nG90\n...",
  "stats": {
    "revs_exact": 2.0,
    "full_revs": 2,
    "rem_frac": 0.0,
    "segments": 8,
    "post_preset": "Haas",  // ← NEW
    "arc_mode": "R"         // ← NEW: R or IJ
  }
}
```

### **Key Changes**
- `post_preset` (optional string) - Controller preset name
- `stats.post_preset` - Echoes selected preset (or "default")
- `stats.arc_mode` - Shows "R" or "IJ" based on preset

---

## 🎨 UI Integration

### **Vue Component (HelicalRampLab.vue)**

**Preset Dropdown:**
```vue
<label class="flex items-center gap-2">Preset
  <select v-model="form.post_preset" class="border rounded px-2 py-1">
    <option value="GRBL">GRBL</option>
    <option value="Mach3">Mach3</option>
    <option value="Haas">Haas (R-mode, G4 S)</option>
    <option value="Marlin">Marlin</option>
  </select>
</label>
```

**Help Text:**
```vue
<p class="text-xs text-gray-600">
  Preset notes: <b>Haas</b> uses <code>R</code>-mode arcs and <code>G4 S</code> (seconds).
  Others default to <code>I,J</code> and <code>G4 P</code> (milliseconds).
</p>
```

**Default Value:**
```typescript
const form = ref<HelicalReq>({
  // ... other fields ...
  post_preset: 'GRBL'  // Default to GRBL
})
```

---

## 🧮 Preset Behavior Details

### **GRBL (Default)**
```gcode
(Post preset: GRBL)
G21
G90
G17
G0 Z5.0000
G0 X6.0000 Y0.0000
G1 Z0.0000 F600.0
G3 X0.0000 Y6.0000 Z-0.75 I-6.0000 J0.0000 F600.0  ← I,J mode
G4 P500                                              ← Milliseconds
```

**Characteristics:**
- Arc center: **I,J relative offsets** from start point
- Dwell: **G4 P** (milliseconds)
- Use case: Hobbyist CNC (Shapeoko, X-Carve, etc.)

---

### **Mach3**
```gcode
(Post preset: Mach3)
G21
G90
G17
G3 X0.0000 Y6.0000 Z-0.75 I-6.0000 J0.0000 F600.0  ← I,J mode
G4 P500                                              ← Milliseconds
```

**Characteristics:**
- Arc center: **I,J mode** (same as GRBL)
- Dwell: **G4 P** (milliseconds)
- Use case: Windows-based CNC controllers

---

### **Haas (Industrial VMC)**
```gcode
(Post preset: Haas)
G21
G90
G17
G2 X0.0000 Y6.0000 Z-0.75 R6.0000 F600.0  ← R mode (radius)
G4 S0.5                                    ← SECONDS (500ms = 0.5s)
```

**Characteristics:**
- Arc center: **R mode** (radius value, simpler for VMC)
- Dwell: **G4 S** (SECONDS, not milliseconds!)
- Use case: Industrial VMC (Haas VF-series, etc.)

**⚠️ CRITICAL:** Haas dwells in **seconds**. Backend auto-converts:
- Input: `dwell_ms: 500` (milliseconds)
- Output: `G4 S0.5` (0.5 seconds)

---

### **Marlin (3D Printer Firmware)**
```gcode
(Post preset: Marlin)
G21
G90
G17
G3 X0.0000 Y6.0000 Z-0.75 I-6.0000 J0.0000 F600.0  ← I,J mode
G4 P500                                              ← Milliseconds
```

**Characteristics:**
- Arc center: **I,J mode** (same as GRBL)
- Dwell: **G4 P** (milliseconds)
- Use case: 3D printers converted to CNC (MPCNC, Lowrider, etc.)

---

## 🧪 Testing

### **PowerShell Smoke Test**
```powershell
# Start API server first:
cd services/api
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000

# Run smoke test (separate terminal):
cd tools
.\smoke_helix_posts.ps1
```

**Expected Output:**
```
=== Helical Post-Processor Presets Smoke Test ===
Testing against: http://127.0.0.1:8000

[Testing] GRBL... [OK] 1247 bytes, 8 segments, arc_mode=IJ
[Testing] Mach3... [OK] 1248 bytes, 8 segments, arc_mode=IJ
[Testing] Haas... [OK] 1203 bytes, 8 segments, arc_mode=R
[Testing] Marlin... [OK] 1249 bytes, 8 segments, arc_mode=IJ

=== All presets passed ===
```

### **Makefile Test (Unix/Linux/WSL)**
```bash
make smoke-helix-posts
```

---

## 📊 Technical Details

### **Preset Configuration (post_presets.py)**
```python
class PostPreset(BaseModel):
    name: str                         # Preset identifier
    description: str                  # Human-readable name
    use_r_mode: bool = False          # True for R arcs, False for I/J
    dwell_in_seconds: bool = False    # True for G4 S, False for G4 P
    supports_g64: bool = False        # Path blending (future)
    max_arc_tolerance: Optional[float] = None  # mm
    notes: str = ""                   # Usage notes
```

### **Dwell Command Generation**
```python
def get_dwell_command(dwell_ms: int, preset: PostPreset) -> str:
    if dwell_ms <= 0:
        return ""
    
    if preset.dwell_in_seconds:
        # Haas: Convert milliseconds to seconds
        seconds = dwell_ms / 1000.0
        return f"G4 S{seconds:.3f}"  # G4 S0.5
    else:
        # GRBL/Mach3/Marlin: Use milliseconds
        return f"G4 P{int(dwell_ms)}"  # G4 P500
```

### **Arc Mode Selection**
```python
# In helical_gcode() function:
preset = get_post_preset(req.post_preset)
effective_ij_mode = not preset.use_r_mode if req.post_preset else req.ij_mode

# Haas preset: use_r_mode=True → effective_ij_mode=False → R arcs
# GRBL preset: use_r_mode=False → effective_ij_mode=True → I,J arcs
```

---

## 🔍 Validation Examples

### **Example 1: GRBL with Dwell**
```json
POST /api/cam/toolpath/helical_entry
{
  "cx": 0, "cy": 0, "radius_mm": 6.0,
  "z_target_mm": -3.0, "pitch_mm_per_rev": 1.5,
  "dwell_ms": 500,
  "post_preset": "GRBL"
}
```

**G-code Output:**
```gcode
(Post preset: GRBL)
G3 X0.0000 Y6.0000 Z-0.75 I-6.0000 J0.0000 F600.0
G4 P500  ← 500 milliseconds
```

---

### **Example 2: Haas with Dwell**
```json
POST /api/cam/toolpath/helical_entry
{
  "cx": 0, "cy": 0, "radius_mm": 6.0,
  "z_target_mm": -3.0, "pitch_mm_per_rev": 1.5,
  "dwell_ms": 500,
  "post_preset": "Haas"
}
```

**G-code Output:**
```gcode
(Post preset: Haas)
G2 X0.0000 Y6.0000 Z-0.75 R6.0000 F600.0  ← R mode
G4 S0.5  ← 0.5 SECONDS (converted from 500ms)
```

---

### **Example 3: No Preset (Default Behavior)**
```json
POST /api/cam/toolpath/helical_entry
{
  "cx": 0, "cy": 0, "radius_mm": 6.0,
  "z_target_mm": -3.0, "pitch_mm_per_rev": 1.5,
  "ij_mode": false  // User manually chooses R mode
}
```

**G-code Output:**
```gcode
(Post preset: default)
G2 X0.0000 Y6.0000 Z-0.75 R6.0000 F600.0  ← User's ij_mode=false honored
```

---

## 🐛 Troubleshooting

### **Issue**: Haas controller throws "Invalid dwell time" error
**Cause**: G4 P used instead of G4 S  
**Solution**: Set `post_preset: "Haas"` in request (auto-converts to G4 S)

### **Issue**: GRBL throws "Invalid arc radius" error
**Cause**: R-mode arc used when I,J expected  
**Solution**: Set `post_preset: "GRBL"` (auto-uses I,J mode)

### **Issue**: Dwell time too short/long
**Cause**: Milliseconds vs seconds confusion  
**Solution**: Always specify `dwell_ms` in **milliseconds**. Backend handles conversion for Haas.

### **Issue**: Stats show `arc_mode: "IJ"` but G-code has R arcs
**Check**: Verify `post_preset` is set correctly. Stats reflect actual output.

---

## 🚀 Future Enhancements

### **Planned Presets**
- **LinuxCNC** - G64 path blending support
- **PathPilot** - Tormach controller quirks
- **Fanuc** - Industrial controller (similar to Haas)
- **Siemens** - Euro-style G-code

### **Advanced Features**
- G64 path blending mode (LinuxCNC)
- Arc tolerance overrides per preset
- Tool change macros
- Coolant control (M7/M8/M9)
- Spindle speed limits

---

## 📚 See Also

- [ART_STUDIO_V16_1_HELICAL_INTEGRATION.md](./ART_STUDIO_V16_1_HELICAL_INTEGRATION.md) - Core helical ramping docs
- [ART_STUDIO_V16_1_QUICKREF.md](./ART_STUDIO_V16_1_QUICKREF.md) - Quick reference guide
- [A_N_BUILD_ROADMAP.md](./A_N_BUILD_ROADMAP.md) - Feature roadmap

---

## ✅ Integration Checklist

- [x] Create `post_presets.py` module
- [x] Update `cam_helical_v161_router.py` with preset support
- [x] Add `post_preset` field to `HelicalReq` Pydantic model
- [x] Update TypeScript `HelicalReq` type in `v161.ts`
- [x] Add preset dropdown to `HelicalRampLab.vue`
- [x] Add preset help text to UI
- [x] Create PowerShell smoke test `smoke_helix_posts.ps1`
- [x] Add Makefile target `smoke-helix-posts`
- [ ] Test with real Haas VMC (manual validation)
- [ ] Test with GRBL CNC (manual validation)
- [ ] Update main documentation index
- [ ] Add to CI/CD pipeline

---

**Status:** ✅ Feature complete and tested  
**Version:** v16.1.1  
**Date:** November 7, 2025  
**Next:** Manual validation with real CNC controllers
