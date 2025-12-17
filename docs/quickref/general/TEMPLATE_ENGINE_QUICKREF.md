# Filename Template Token Engine - Quick Reference

**Status:** ✅ Complete  
**Module:** Unified Preset System  
**Files:**
- `services/api/app/util/template_engine.py` (380 lines)
- `services/api/app/routers/unified_presets_router.py` (Extended)
- `test_template_engine.ps1` (Test suite)

---

## 🎯 Overview

Dynamic filename generation for CAM exports with contextual token replacement. Supports 12 tokens with intelligent defaults and automatic sanitization.

---

## 📋 Supported Tokens

| Token | Description | Example Value |
|-------|-------------|---------------|
| `{preset}` | Preset name | `Strat_Roughing` |
| `{machine}` | Machine ID | `CNC_Router_01` |
| `{post}` | Post-processor ID | `GRBL`, `Mach4` |
| `{operation}` | Operation type | `adaptive`, `roughing`, `drilling` |
| `{material}` | Material name | `Maple`, `Mahogany` |
| `{neck_profile}` | Neck profile name | `Fender_Modern_C` |
| `{neck_section}` | Neck section/fret | `Fret_5`, `Nut`, `Heel` |
| `{compare_mode}` | Compare identifier | `baseline`, `variant_A` |
| `{date}` | Date (YYYY-MM-DD) | `2025-11-28` |
| `{timestamp}` | Full timestamp | `2025-11-28_14-30-45` |
| `{job_id}` | Job Intelligence ID | `job_12345` |
| `{raw}` | Raw geometry source | `body_outline`, `pickup_cavity` |

---

## 🔧 Token Resolution Rules

1. **Missing context** → Token remains literal (e.g., `{neck_profile}` if unavailable)
2. **Empty/None values** → Token removed from output
3. **Case-insensitive** → `{Preset}` = `{preset}`
4. **Unknown tokens** → Remain literal (forward compatibility)
5. **Special characters** → Auto-sanitized:
   - Spaces → underscores
   - Slashes → removed
   - Colons → hyphens
   - Multiple underscores → collapsed

---

## 🚀 API Endpoints

### **POST /api/presets/validate-template**
Validate a filename template and preview example output.

**Request:**
```json
{
  "template": "{preset}__{neck_profile}__{date}.nc"
}
```

**Response:**
```json
{
  "valid": true,
  "tokens": ["preset", "neck_profile", "date"],
  "unknown_tokens": [],
  "warnings": [],
  "example": "Example_Preset__Fender_Modern_C__2025-11-28.nc"
}
```

### **POST /api/presets/resolve-filename**
Resolve a template with provided context data.

**Request:**
```json
{
  "preset_name": "Strat Pocket",
  "post_id": "GRBL",
  "extension": "gcode"
}
```

**Response:**
```json
{
  "filename": "Strat_Pocket__GRBL__2025-11-28.gcode",
  "template_used": "{preset}__{post}__{date}"
}
```

---

## 📐 Template Examples

### **Simple CAM Export**
```
Template: {preset}_{post}_{date}.nc
Output:   J45_Pocket_GRBL_2025-11-28.nc
```

### **Neck Operation**
```
Template: {preset}__{neck_profile}__{neck_section}.gcode
Output:   Neck_Rough__Fender_Modern_C__Fret_5.gcode
```

### **Compare Mode**
```
Template: {preset}__{compare_mode}__{post}.nc
Output:   Rosette_Test__baseline__LinuxCNC.nc
```

### **Full Context**
```
Template: {preset}__{machine}__{material}__{timestamp}.gcode
Output:   Adaptive_Test__CNC_Router_01__Maple__2025-11-28_14-30-45.gcode
```

---

## 🧪 Testing

### **Run Test Suite**
```powershell
# Start API server
cd services/api
uvicorn app.main:app --reload

# Run tests (separate terminal)
cd ../..
.\test_template_engine.ps1
```

**Expected Output:**
```
1. Testing POST /api/presets/validate-template (simple)
  ✓ Validation successful:
    Valid: True
    Tokens: preset, date
    Example: Example_Preset_2025-11-28.nc

2. Testing POST /api/presets/validate-template (neck)
  ✓ Validation successful:
    Valid: True
    Tokens: preset, neck_profile, neck_section, date
    Example: Example_Preset__Fender_Modern_C__Fret_5__2025-11-28.gcode

...

=== All Template Engine Tests Completed ===
```

---

## 💡 Intelligent Defaults

If no template is provided, the system chooses based on context:

| Context | Default Template |
|---------|-----------------|
| Neck data present | `{preset}__{neck_profile}__{neck_section}__{date}` |
| Compare mode | `{preset}__{compare_mode}__{post}__{date}` |
| Operation type | `{preset}__{operation}__{post}__{date}` |
| Generic | `{preset}__{post}__{date}` |

---

## 🔍 Python Usage

### **Direct Template Resolution**
```python
from app.util.template_engine import resolve_template

result = resolve_template(
    "{preset}__{post}.nc",
    {"preset": "Test", "post": "GRBL"}
)
# Output: "Test__GRBL.nc"
```

### **Export Filename Generation**
```python
from app.util.template_engine import resolve_export_filename

filename = resolve_export_filename(
    preset_name="Strat Pocket",
    neck_profile="Fender Modern C",
    neck_section="Fret 5",
    extension="gcode"
)
# Output: "Strat_Pocket__Fender_Modern_C__Fret_5__2025-11-28.gcode"
```

### **Template Validation**
```python
from app.util.template_engine import validate_template

validation = validate_template("{preset}__{unknown}__{post}.nc")
# Returns:
# {
#   "valid": True,
#   "tokens": ["preset", "unknown", "post"],
#   "unknown_tokens": ["unknown"],
#   "warnings": ["Unknown token: {unknown}"]
# }
```

---

## 🛠️ Integration Points

### **Export Params Schema**
```python
class ExportParams(BaseModel):
    filename_template: Optional[str] = Field(
        None,
        description="Template with tokens: {preset}, {machine}, {neck_profile}, etc."
    )
```

### **Preset Storage**
Export presets store templates in `export_params.filename_template`:
```json
{
  "kind": "export",
  "name": "Standard Export",
  "export_params": {
    "filename_template": "{preset}__{post}__{date}.gcode",
    "default_format": "gcode"
  }
}
```

---

## 🚨 Error Handling

### **Missing Template**
```
POST /api/presets/validate-template
{"template": ""}

→ 400 Bad Request: "Template is required"
```

### **Mismatched Braces**
```
Template: {preset}_{post.nc

→ warnings: ["Mismatched braces in template"]
→ valid: false
```

### **No Tokens (Static Filename)**
```
Template: output.nc

→ warnings: ["Template contains no tokens (static filename)"]
→ valid: true
```

---

## 📊 Token Priority

When resolving filenames, tokens are evaluated in order:

1. **User-provided context** (from API request)
2. **Preset data** (from `cam_params`, `export_params`, `neck_params`)
3. **Auto-generated** (`date`, `timestamp` always available)
4. **Missing → literal** (token remains in output if no value)

---

## ✅ Validation Checklist

- [x] 12 supported tokens implemented
- [x] Case-insensitive token matching
- [x] Special character sanitization
- [x] Intelligent default templates
- [x] Unknown token handling (forward compatibility)
- [x] Validation endpoint (`/validate-template`)
- [x] Resolution endpoint (`/resolve-filename`)
- [x] Test suite with 7 scenarios
- [x] Integration with unified presets router
- [x] Python API (`resolve_template`, `resolve_export_filename`, `validate_template`)

---

## 🎯 Next Steps

**Immediate:**
- Task 6: Create `PresetHubView.vue` frontend component
- Wire template validation into preset creation UI
- Add filename preview in export dialogs

**Future Enhancements:**
- Token autocomplete in template editor
- Template library with common patterns
- Custom token plugins for user-defined fields

---

**Status:** ✅ Task 5 Complete (5/6 Phase 1 Backend Foundation)  
**Test Coverage:** 7 API endpoint tests via PowerShell  
**Next:** PresetHubView.vue frontend component
