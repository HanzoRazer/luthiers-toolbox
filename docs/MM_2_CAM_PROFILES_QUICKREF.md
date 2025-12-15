# MM-2: CAM Profiles for Mixed Materials — Quick Reference

**Status:** ✅ Implemented  
**Date:** November 29, 2025  
**Module:** Rosette Manufacturing OS (RMOS)  
**Depends On:** MM-0 (Strip Families)

---

## 🎯 Overview

MM-2 adds **CAM profiles** to RMOS mixed-material system, mapping material types to specific machining parameters (feeds, speeds, depth of cut, cut direction, fragility).

**Key Features:**
- ✅ **7 Curated Profiles**: wood, metal, shell, paper, charred, burn line, resin
- ✅ **Per-Material Settings**: spindle RPM, feed rate, plunge rate, stepdown, cut direction, coolant
- ✅ **Fragility Scoring**: 0.0 (robust) to 1.0 (extremely fragile) for risk assessment
- ✅ **Profile Registry**: Load, lookup, and infer CAM profiles from strip family materials
- ✅ **G-code Integration**: Helper functions to apply profiles to segment emission
- ✅ **Pipeline Metadata**: Automatic CAM summary in job handoffs with fragility flags

---

## 📁 Architecture

### **Backend Components**
```
data/rmos/
└── cam_profiles.json                    # 7 curated CAM profiles

services/api/app/
├── schemas/cam_profile.py               # CamProfile, MaterialType, CutDirection, LaneHint
├── core/cam_profile_registry.py         # load, get, infer, summarize functions
├── core/rmos_cam_materials.py           # build_segment_cam_params helper
├── core/rmos_gcode_materials.py         # Reference G-code emitter with CAM profiles
└── core/pipeline_handoff.py             # Patched to include CAM summary + fragility flags
```

---

## 📊 CAM Profile Schema

### **CamProfile Model**
```python
{
  "id": str,                          # Unique profile ID
  "name": str,                        # Human-readable name
  "material_type": MaterialType,      # wood | metal | shell | paper | foil | charred | resin | composite
  "recommended_tool": str,            # Tool spec (e.g., "vbit_60deg", "endmill_1mm_carbide")
  "spindle_rpm": int,                 # Spindle speed in RPM
  "feed_rate_mm_min": int,            # Cutting feed rate in mm/min
  "plunge_rate_mm_min": int,          # Plunge/drilling feed rate in mm/min
  "stepdown_mm": float,               # Maximum depth of cut per pass in mm
  "cut_direction": CutDirection,      # climb | conventional | manual | mixed
  "coolant": str,                     # Coolant/lubrication (none, mist, flood)
  "fragility_score": float,           # 0.0 (robust) to 1.0 (extremely fragile)
  "priority_lane_hint": LaneHint?,    # Suggested quality lane (safe, tuned_v1, tuned_v2, experimental, archived)
  "notes": str?                       # Additional machining notes
}
```

---

## 🗂️ Curated CAM Profiles

### **1. wood_standard** (Hardwood Rosette Channels)
```json
{
  "id": "wood_standard",
  "material_type": "wood",
  "spindle_rpm": 18000,
  "feed_rate_mm_min": 1200,
  "stepdown_mm": 0.6,
  "cut_direction": "climb",
  "fragility_score": 0.2,
  "priority_lane_hint": "tuned_v1"
}
```

### **2. metal_inlay** (Copper/Brass/Aluminum)
```json
{
  "id": "metal_inlay",
  "material_type": "metal",
  "spindle_rpm": 12000,
  "feed_rate_mm_min": 300,
  "stepdown_mm": 0.15,
  "cut_direction": "climb",
  "coolant": "mist",
  "fragility_score": 0.7,
  "priority_lane_hint": "experimental",
  "notes": "Slow feed, shallow DOC to avoid chatter and burrs."
}
```

### **3. shell_inlay** (Abalone/Mother-of-Pearl)
```json
{
  "id": "shell_inlay",
  "material_type": "shell",
  "spindle_rpm": 15000,
  "feed_rate_mm_min": 250,
  "stepdown_mm": 0.1,
  "cut_direction": "conventional",
  "coolant": "mist",
  "fragility_score": 0.85,
  "priority_lane_hint": "experimental",
  "notes": "Very shallow passes, high fragility; shell is brittle."
}
```

### **4. paper_marquetry** (Printed/Decorative Paper)
```json
{
  "id": "paper_marquetry",
  "material_type": "paper",
  "spindle_rpm": 10000,
  "feed_rate_mm_min": 500,
  "stepdown_mm": 0.2,
  "cut_direction": "climb",
  "fragility_score": 0.6,
  "notes": "Sharp tool, downcut to avoid tearing printed fiber."
}
```

### **5. charred_wood** (Rosette Rim / Burn Band)
```json
{
  "id": "charred_wood",
  "material_type": "charred",
  "spindle_rpm": 16000,
  "feed_rate_mm_min": 800,
  "stepdown_mm": 0.4,
  "fragility_score": 0.55,
  "notes": "Charred layer can crumble; reduce feed and DOC slightly."
}
```

### **6. char_line** (Burn Wire Operation)
```json
{
  "id": "char_line",
  "material_type": "charred",
  "spindle_rpm": 0,
  "cut_direction": "manual",
  "fragility_score": 0.5,
  "notes": "Not a cutting profile; indicates manual burn-wire operation."
}
```

### **7. resin_infill** (Channel Cutting)
```json
{
  "id": "resin_infill",
  "material_type": "resin",
  "spindle_rpm": 16000,
  "feed_rate_mm_min": 800,
  "stepdown_mm": 0.3,
  "fragility_score": 0.4,
  "notes": "Standard resin channels; avoid excessive heat."
}
```

---

## 🔌 Core Functions

### **1. Load Profiles**
```python
from app.core.cam_profile_registry import _load_profiles_raw

profiles = _load_profiles_raw()  # Returns List[CamProfile]
```

### **2. Get Profile by ID**
```python
from app.core.cam_profile_registry import get_cam_profile

profile = get_cam_profile("wood_standard")  # Returns CamProfile | None
```

### **3. Infer Profile from Material**
```python
from app.core.cam_profile_registry import infer_profile_for_material
from app.schemas.strip_family import MaterialSpec

material = MaterialSpec(
    key="mat_rosewood",
    type="wood",
    species="Indian Rosewood",
    thickness_mm=1.2,
    cam_profile="wood_standard"  # Optional explicit override
)

profile = infer_profile_for_material(material)  # Returns CamProfile | None
```

**Inference Logic:**
1. If `material.cam_profile` is set, use that profile ID
2. Otherwise, use hard-coded favorites per material type:
   - `wood` → `wood_standard`
   - `metal` → `metal_inlay`
   - `shell` → `shell_inlay`
   - `paper` → `paper_marquetry`
   - `charred` → `charred_wood`
   - `resin` → `resin_infill`
3. Fallback to first profile matching `material.type`

### **4. Summarize Profiles for Strip Family**
```python
from app.core.cam_profile_registry import summarize_profiles_for_family

strip_family = {
    "id": "sf_mixed_01",
    "materials": [
        {"key": "mat_wood", "type": "wood", "species": "Maple"},
        {"key": "mat_shell", "type": "shell", "species": "Abalone"},
        {"key": "mat_metal", "type": "metal", "species": "Copper"}
    ]
}

summary = summarize_profiles_for_family(strip_family)
# Returns:
# {
#     "profile_ids": ["wood_standard", "shell_inlay", "metal_inlay"],
#     "min_feed_rate_mm_min": 250,
#     "max_feed_rate_mm_min": 1200,
#     "worst_fragility_score": 0.85,
#     "dominant_lane_hint": "experimental"
# }
```

### **5. Build Segment CAM Parameters**
```python
from app.core.rmos_cam_materials import build_segment_cam_params
from app.schemas.strip_family import MaterialSpec

material = MaterialSpec(key="mat_shell", type="shell", species="Abalone")
machine_defaults = {
    "spindle_rpm": 18000,
    "feed_rate_mm_min": 1000
}

params = build_segment_cam_params(material, machine_defaults)
# Returns:
# {
#     "cam_profile_id": "shell_inlay",
#     "spindle_rpm": 15000,           # Overridden by profile
#     "feed_rate_mm_min": 250,        # Overridden by profile
#     "plunge_rate_mm_min": 120,
#     "stepdown_mm": 0.1,
#     "cut_direction": "conventional",
#     "coolant": "mist",
#     "fragility_score": 0.85,
#     "recommended_tool": "endmill_0_8mm_carbide",
#     "notes": "Very shallow passes, high fragility; shell is brittle."
# }
```

---

## 🛠️ Integration Patterns

### **Pattern 1: G-code Emission with CAM Profiles**

**Reference Implementation:** `services/api/app/core/rmos_gcode_materials.py`

```python
from app.core.rmos_gcode_materials import emit_rosette_gcode_with_materials

plan = {
    "segments": [
        {
            "type": "line",
            "x1": 0, "y1": 0, "x2": 10, "y2": 0,
            "material_index": 0  # References materials[0] in strip_family
        },
        {
            "type": "arc",
            "x1": 10, "y1": 0, "x2": 10, "y2": 10,
            "cx": 10, "cy": 5, "r": 5,
            "material_index": 1  # References materials[1]
        }
    ]
}

strip_family = {
    "materials": [
        {"key": "mat_wood", "type": "wood", "species": "Maple"},
        {"key": "mat_shell", "type": "shell", "species": "Abalone"}
    ]
}

machine_defaults = {
    "spindle_rpm": 18000,
    "feed_rate_mm_min": 1000
}

gcode = emit_rosette_gcode_with_materials(plan, strip_family, machine_defaults)
```

**Generated G-code:**
```gcode
(RMOS Rosette with MM-2 CAM Profiles)
G21 (mm)
G90 (absolute)

(Segment 0: Maple)
(CAM: wood_standard, Fragility: 0.20)
M3 S18000 (Spindle on)
G1 X10.0000 Y0.0000 F1200

(Segment 1: Abalone)
(CAM: shell_inlay, Fragility: 0.85)
M3 S15000 (Spindle on)
G3 X10.0000 Y10.0000 I0.0000 J5.0000 F250
(Very shallow passes, high fragility; shell is brittle.)

M30 (End)
```

### **Pattern 2: Pipeline Handoff with CAM Metadata**

**Automatically Applied:** `services/api/app/core/pipeline_handoff.py`

When `build_pipeline_payload()` is called with a strip family:

```python
from app.core.pipeline_handoff import build_pipeline_payload
from app.schemas.pipeline_handoff import PipelineHandoffRequest

req = PipelineHandoffRequest(
    lane="tuned_v1",
    machine_profile="cnc_01",
    batch_op={
        "strip_family": {
            "id": "sf_mixed_01",
            "materials": [
                {"key": "mat_wood", "type": "wood"},
                {"key": "mat_shell", "type": "shell"}
            ]
        }
    }
)

payload = build_pipeline_payload(req)
```

**Payload Includes:**
```json
{
  "job_type": "rmos_rosette_saw_batch",
  "lane": "tuned_v1",
  "metadata": {
    "cam_profile_summary": {
      "profile_ids": ["wood_standard", "shell_inlay"],
      "min_feed_rate_mm_min": 250,
      "max_feed_rate_mm_min": 1200,
      "worst_fragility_score": 0.85,
      "dominant_lane_hint": "experimental"
    },
    "materials": [
      {"key": "mat_wood", "type": "wood"},
      {"key": "mat_shell", "type": "shell"}
    ],
    "fragile_job": true,
    "fragility_reason": "Worst material fragility: 0.85"
  }
}
```

**Auto-Flagging Rules:**
- If `worst_fragility_score >= 0.75` → `fragile_job: true`
- If `req.lane` is empty and `dominant_lane_hint` exists → `suggested_lane` added

---

## 🧪 Testing

### **Test Profile Loading**
```powershell
cd services/api
.\.venv\Scripts\Activate.ps1
python -c "from app.core.cam_profile_registry import _load_profiles_raw; print(len(_load_profiles_raw()), 'profiles loaded')"
# Expected: 7 profiles loaded
```

### **Test Profile Inference**
```powershell
python -c "
from app.core.cam_profile_registry import infer_profile_for_material
from app.schemas.strip_family import MaterialSpec

mat = MaterialSpec(key='test', type='shell', species='Abalone', thickness_mm=0.8)
prof = infer_profile_for_material(mat)
print(f'{prof.id}: {prof.name} (fragility={prof.fragility_score})')
"
# Expected: shell_inlay: Shell inlay – abalone/MOP (fragility=0.85)
```

### **Test Strip Family Summary**
```powershell
python -c "
from app.core.cam_profile_registry import summarize_profiles_for_family

family = {
    'materials': [
        {'key': 'm1', 'type': 'wood', 'species': 'Maple'},
        {'key': 'm2', 'type': 'metal', 'species': 'Copper'}
    ]
}

summary = summarize_profiles_for_family(family)
print(summary)
"
# Expected: {'profile_ids': ['metal_inlay', 'wood_standard'], 'min_feed_rate_mm_min': 300, ...}
```

---

## 📋 Integration Checklist

**Backend:**
- [x] Create `data/rmos/cam_profiles.json` with 7 profiles
- [x] Create `schemas/cam_profile.py` with CamProfile model
- [x] Create `core/cam_profile_registry.py` with load/get/infer/summarize
- [x] Create `core/rmos_cam_materials.py` with build_segment_cam_params
- [x] Create `core/rmos_gcode_materials.py` reference implementation
- [x] Patch `core/pipeline_handoff.py` to include CAM summary

**Frontend (Optional):**
- [ ] Display CAM profile summary in strip family editor (MM-0 UI extension)
- [ ] Show fragility warnings when selecting materials
- [ ] Add CAM profile selector dropdown per material

**Testing:**
- [ ] Unit tests for profile loading and inference
- [ ] Integration test for pipeline handoff with CAM metadata
- [ ] G-code emission test with mixed materials

---

## 🔍 Fragility Score Guidelines

| Score Range | Interpretation | Lane Hint | Notes |
|-------------|----------------|-----------|-------|
| 0.0 - 0.3 | **Robust** | tuned_v1, tuned_v2 | Standard wood, resin |
| 0.3 - 0.6 | **Moderate** | tuned_v1, experimental | Charred wood, paper |
| 0.6 - 0.8 | **Fragile** | experimental | Thin metal, foils |
| 0.8 - 1.0 | **Extremely Fragile** | experimental | Shell, brittle inlays |

---

## 🚀 Next Steps: MM-3 and MM-4

### **MM-3: PDF Design Sheet Generator**
- Export strip family specs to PDF with material callouts
- CAM profile summary table
- Tooling requirements and setup notes

### **MM-4: Risk Model Integration**
- Per-material risk multipliers based on fragility
- Failure mode analysis (brittle shell, thin metal)
- Safety margins and tolerance recommendations
- Lane auto-selection based on risk score

---

## 🐛 Troubleshooting

### **Issue**: Profile not found for material
**Solution**: Check that `cam_profiles.json` exists and is valid JSON. Verify material type matches one of: wood, metal, shell, paper, foil, charred, resin, composite.

### **Issue**: Fragility score not in handoff metadata
**Solution**: Ensure strip_family is passed in `batch_op` payload when calling `build_pipeline_payload()`.

### **Issue**: G-code not using profile feeds/speeds
**Solution**: Verify `emit_segment_with_params()` is applying `params['feed_rate_mm_min']` and `params['spindle_rpm']` to output lines.

---

**Status:** ✅ MM-2 Implementation Complete  
**Next Module:** MM-3 (PDF Design Sheet Generator)  
**Dependencies:** MM-0 (Strip Families), MM-2 (CAM Profiles)
