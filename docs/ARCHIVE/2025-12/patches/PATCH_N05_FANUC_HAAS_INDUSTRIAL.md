# Patch N.05 — Fanuc/Haas Industrial Post-Processors

**Status:** 🔜 Specification Complete (Implementation Pending)  
**Date:** November 5, 2025  
**Target:** Industrial CNC controllers (Fanuc, Haas, Mazak, Okuma)

---

## 🎯 Overview

Add support for **industrial CNC controllers** with advanced features:

- **Fanuc-style G-code** (ISO/DIN format)
- **Haas-specific extensions** (macro variables, probing, tool setters)
- **Work offset management** (G54-G59, extended offsets G54.1 P1-P99)
- **Tool change protocols** (M6 with tool length compensation)
- **Coolant control** (M7/M8/M9, through-spindle coolant)
- **Chip conveyor integration** (M31/M33)
- **Program number support** (O-codes, percent signs)
- **Modal state management** (explicit vs. implicit)

**Use Cases:**
- Production shops with Haas VF/VM series
- Industrial mills with Fanuc 0i/31i/32i controllers
- Mazak mills with Mazatrol conversational + EIA/ISO mode
- Okuma mills with OSP control

---

## 📦 New Post Configurations

### **1. Fanuc 0i/31i/32i (Generic)**

**File:** `services/api/app/data/posts/fanuc_generic.json`

```json
{
  "id": "fanuc_generic",
  "title": "Fanuc 0i/31i/32i (Generic)",
  "controller": "Fanuc",
  "dialect": "ISO/DIN",
  "header": [
    "%",
    "O{PROGRAM_NO} ({PROGRAM} - {DATE})",
    "(Tool {TOOL}: {DIAM}mm End Mill)",
    "(Material: {MATERIAL})",
    "(Work Offset: {WORK_OFFSET})",
    "G17 G21 G40 G49 G80 G90",
    "{WORK_OFFSET}",
    "G0 Z{SAFE_Z}",
    "T{TOOL} M6",
    "G43 H{TOOL}",
    "S{RPM} M3",
    "G4 P2.0"
  ],
  "footer": [
    "G0 Z{SAFE_Z}",
    "M5",
    "G91 G28 Z0",
    "G28 X0 Y0",
    "M30",
    "%"
  ],
  "tokens": {
    "PROGRAM_NO": "1001",
    "PROGRAM": "ROUGHING",
    "DATE": "2025-11-05",
    "TOOL": "1",
    "DIAM": "6.0",
    "MATERIAL": "Aluminum",
    "WORK_OFFSET": "G54",
    "SAFE_Z": "50.0",
    "RPM": "8000"
  },
  "metadata": {
    "supports_arcs": true,
    "has_tool_changer": true,
    "has_coolant": true,
    "has_chip_conveyor": false,
    "gcode_dialect": "Fanuc ISO/DIN",
    "max_spindle_rpm": 12000,
    "work_offsets": ["G54", "G55", "G56", "G57", "G58", "G59"],
    "extended_offsets": true,
    "tool_length_comp": "G43 H",
    "cutter_comp": "G41/G42 D"
  }
}
```

---

### **2. Haas VF/VM Series**

**File:** `services/api/app/data/posts/haas_vf.json`

```json
{
  "id": "haas_vf",
  "title": "Haas VF/VM Series",
  "controller": "Haas",
  "dialect": "Haas NGC",
  "header": [
    "%",
    "O{PROGRAM_NO} ({PROGRAM} - {DATE})",
    "(T{TOOL} {DIAM}MM FLAT ENDMILL - H{TOOL} - D{TOOL})",
    "(MATERIAL: {MATERIAL})",
    "(WORK OFFSET: {WORK_OFFSET})",
    "G00 G17 G40 G49 G80 G90",
    "G20 (INCH MODE - CONVERTED FROM {UNITS})",
    "{WORK_OFFSET}",
    "T{TOOL} M06",
    "G00 G90 G54 X0. Y0. S{RPM} M03",
    "G43 H{TOOL} Z{SAFE_Z}",
    "M08 (COOLANT ON)",
    "G04 P1."
  ],
  "footer": [
    "M09 (COOLANT OFF)",
    "M05 (SPINDLE OFF)",
    "G00 G91 G28 Z0. (Z HOME)",
    "G28 X0. Y0. (XY HOME)",
    "G90",
    "M30 (PROGRAM END)",
    "%"
  ],
  "tokens": {
    "PROGRAM_NO": "1001",
    "PROGRAM": "ROUGHING",
    "DATE": "2025-11-05",
    "TOOL": "1",
    "DIAM": "6.0",
    "MATERIAL": "6061 ALUMINUM",
    "WORK_OFFSET": "G54",
    "SAFE_Z": "2.0",
    "RPM": "8000",
    "UNITS": "mm"
  },
  "metadata": {
    "supports_arcs": true,
    "has_tool_changer": true,
    "has_coolant": true,
    "has_tsc": true,
    "has_chip_conveyor": true,
    "has_vps": true,
    "gcode_dialect": "Haas NGC",
    "max_spindle_rpm": 10000,
    "work_offsets": ["G54", "G55", "G56", "G57", "G58", "G59"],
    "extended_offsets": true,
    "extended_offset_range": "G154 P1-P99",
    "tool_length_comp": "G43 H",
    "cutter_comp": "G41/G42 D",
    "coolant_codes": {
      "flood": "M08",
      "mist": "M07",
      "tsc": "M88",
      "off": "M09"
    },
    "chip_conveyor": {
      "forward": "M31",
      "reverse": "M33",
      "off": "M35"
    }
  }
}
```

---

### **3. Haas Mini Mill (Compact)**

**File:** `services/api/app/data/posts/haas_mini.json`

```json
{
  "id": "haas_mini",
  "title": "Haas Mini Mill",
  "controller": "Haas",
  "dialect": "Haas NGC",
  "header": [
    "%",
    "O{PROGRAM_NO}",
    "(T{TOOL} D={DIAM}MM)",
    "G00 G17 G40 G80 G90",
    "G20",
    "{WORK_OFFSET}",
    "T{TOOL} M06",
    "S{RPM} M03",
    "G43 H{TOOL}",
    "M08"
  ],
  "footer": [
    "M09",
    "M05",
    "G00 G53 Z0.",
    "G53 X0. Y0.",
    "M30",
    "%"
  ],
  "tokens": {
    "PROGRAM_NO": "1000",
    "TOOL": "1",
    "DIAM": "6.0",
    "WORK_OFFSET": "G54",
    "RPM": "6000"
  },
  "metadata": {
    "supports_arcs": true,
    "has_tool_changer": false,
    "has_coolant": true,
    "has_tsc": false,
    "has_chip_conveyor": false,
    "gcode_dialect": "Haas NGC",
    "max_spindle_rpm": 6000,
    "work_offsets": ["G54", "G55", "G56"]
  }
}
```

---

### **4. Mazak (ISO Mode)**

**File:** `services/api/app/data/posts/mazak_iso.json`

```json
{
  "id": "mazak_iso",
  "title": "Mazak (EIA/ISO Mode)",
  "controller": "Mazak",
  "dialect": "ISO",
  "header": [
    "%",
    "O{PROGRAM_NO}",
    "(TOOL {TOOL} - {DIAM}MM)",
    "(WORK OFFSET: {WORK_OFFSET})",
    "G17 G21 G40 G49 G80 G90 G94",
    "{WORK_OFFSET}",
    "M06 T{TOOL}",
    "G43 H{TOOL} Z{SAFE_Z}",
    "S{RPM} M03",
    "M08"
  ],
  "footer": [
    "M09",
    "M05",
    "G91 G28 Z0",
    "G28 X0 Y0",
    "G90",
    "M30",
    "%"
  ],
  "tokens": {
    "PROGRAM_NO": "0001",
    "TOOL": "1",
    "DIAM": "6.0",
    "WORK_OFFSET": "G54",
    "SAFE_Z": "100.0",
    "RPM": "8000"
  },
  "metadata": {
    "supports_arcs": true,
    "has_tool_changer": true,
    "has_coolant": true,
    "gcode_dialect": "ISO",
    "work_offsets": ["G54", "G55", "G56", "G57", "G58", "G59"]
  }
}
```

---

### **5. Okuma OSP**

**File:** `services/api/app/data/posts/okuma_osp.json`

```json
{
  "id": "okuma_osp",
  "title": "Okuma OSP Control",
  "controller": "Okuma",
  "dialect": "OSP",
  "header": [
    "%",
    "O{PROGRAM_NO} ({PROGRAM})",
    "(TOOL {TOOL}: {DIAM}MM)",
    "G17 G21 G40 G49 G80 G90",
    "G15 H01",
    "T{TOOL} M06",
    "G43 Z{SAFE_Z} H{TOOL}",
    "S{RPM} M03",
    "M08"
  ],
  "footer": [
    "M09",
    "M05",
    "G91 G30 Z0",
    "G30 X0 Y0",
    "G90",
    "M02",
    "%"
  ],
  "tokens": {
    "PROGRAM_NO": "1001",
    "PROGRAM": "ROUGHING",
    "TOOL": "1",
    "DIAM": "6.0",
    "SAFE_Z": "100.0",
    "RPM": "8000"
  },
  "metadata": {
    "supports_arcs": true,
    "has_tool_changer": true,
    "has_coolant": true,
    "gcode_dialect": "Okuma OSP",
    "work_offsets": ["G15 H01", "G15 H02", "G15 H03"]
  }
}
```

---

## 🆕 Enhanced Token System

### **New Tokens for Industrial Posts**

| Token | Example | Description |
|-------|---------|-------------|
| `{PROGRAM_NO}` | 1001 | Program number (O-code) |
| `{MATERIAL}` | 6061 ALUMINUM | Material specification |
| `{WORK_OFFSET}` | G54 | Work coordinate system |
| `{TOOL}` | 1 | Tool number |
| `{TOOL_DESC}` | 6MM FLAT ENDMILL | Tool description |
| `{DIAM}` | 6.0 | Tool diameter |
| `{FLUTES}` | 4 | Number of flutes |
| `{RPM}` | 8000 | Spindle speed |
| `{SAFE_Z}` | 50.0 | Safe retract height |
| `{COOLANT}` | M08 | Coolant on code |
| `{COOLANT_OFF}` | M09 | Coolant off code |
| `{CHIP_FWD}` | M31 | Chip conveyor forward |
| `{CHIP_OFF}` | M35 | Chip conveyor off |
| `{TSC_ON}` | M88 | Through-spindle coolant on (Haas) |

---

## 🔧 Implementation Tasks

### **Phase 1: Post Configurations (30 minutes)**

```powershell
# Create post config files
cd services/api/app/data/posts

# Create each JSON file (copy from above)
New-Item -ItemType File -Path fanuc_generic.json
New-Item -ItemType File -Path haas_vf.json
New-Item -ItemType File -Path haas_mini.json
New-Item -ItemType File -Path mazak_iso.json
New-Item -ItemType File -Path okuma_osp.json

# Or append to posts.json
```

---

### **Phase 2: Schema Updates (20 minutes)**

**File:** `services/api/app/post_injection_helpers.py`

Add new mixin:

```python
class PostIndustrialMixin(BaseModel):
    """
    Mixin for industrial post-processor fields.
    Extends PostRichMixin with additional metadata.
    """
    post: Optional[str] = None
    post_mode: str = "auto"
    units: str = "mm"
    
    # Tool information
    tool_number: Optional[str] = "1"
    tool_desc: Optional[str] = None
    tool_flutes: Optional[int] = 4
    tool_d: float  # Required
    
    # Speeds and feeds
    spindle_rpm: Optional[float] = None
    feed_xy: float
    feed_z: Optional[float] = None
    
    # Work coordinates
    safe_z: float = 50.0
    work_offset: str = "G54"
    program_no: Optional[str] = "1001"
    
    # Material
    material: Optional[str] = None
    
    # Coolant/chip control
    coolant_mode: Optional[str] = "flood"  # flood | mist | tsc | off
    chip_conveyor: bool = False
    
    # Machine ID (optional)
    machine_id: Optional[str] = None
```

---

### **Phase 3: Enhanced Context Builder (15 minutes)**

**File:** `services/api/app/post_injection_helpers.py`

Add industrial context builder:

```python
def quick_context_industrial(body: BaseModel) -> Dict[str, Any]:
    """
    Extract industrial post context from Pydantic model.
    Includes all PostIndustrialMixin fields.
    
    Usage:
        ctx = quick_context_industrial(body)
        set_post_headers(resp, ctx)
    """
    # Get material with fallback
    material = getattr(body, 'material', None)
    if not material:
        material = "UNKNOWN MATERIAL"
    
    # Get coolant codes based on controller
    post_id = getattr(body, 'post', None)
    coolant_mode = getattr(body, 'coolant_mode', 'flood')
    coolant_on = "M08"  # Default flood
    if coolant_mode == "mist":
        coolant_on = "M07"
    elif coolant_mode == "tsc":
        coolant_on = "M88"  # Haas through-spindle
    elif coolant_mode == "off":
        coolant_on = ""
    
    return build_post_context(
        post=post_id,
        post_mode=getattr(body, 'post_mode', 'auto'),
        units=getattr(body, 'units', 'mm'),
        
        # Tool
        TOOL=getattr(body, 'tool_number', "1"),
        TOOL_DESC=getattr(body, 'tool_desc', None),
        FLUTES=getattr(body, 'tool_flutes', 4),
        DIAM=getattr(body, 'tool_d', None),
        
        # Speeds/feeds
        RPM=getattr(body, 'spindle_rpm', None),
        FEED_XY=getattr(body, 'feed_xy', None),
        FEED_Z=getattr(body, 'feed_z', None),
        
        # Work coordinates
        SAFE_Z=getattr(body, 'safe_z', 50.0),
        WORK_OFFSET=getattr(body, 'work_offset', 'G54'),
        PROGRAM_NO=getattr(body, 'program_no', '1001'),
        
        # Material
        MATERIAL=material,
        
        # Coolant/chip
        COOLANT=coolant_on,
        COOLANT_OFF="M09",
        CHIP_FWD="M31" if getattr(body, 'chip_conveyor', False) else "",
        CHIP_OFF="M35" if getattr(body, 'chip_conveyor', False) else "",
        TSC_ON="M88" if coolant_mode == "tsc" else "",
        
        # Machine
        machine_id=getattr(body, 'machine_id', None)
    )
```

---

### **Phase 4: Router Integration Example (10 minutes)**

**File:** `services/api/app/routers/roughing_router.py` (example)

```python
from ..post_injection_helpers import PostIndustrialMixin, quick_context_industrial

class RoughingIndustrialIn(PostIndustrialMixin):
    """Schema for roughing with industrial posts."""
    paths: List[Dict]
    stepover: float = 0.5
    # Inherits all PostIndustrialMixin fields

@router.post("/roughing_industrial_gcode")
def export_roughing_industrial(body: RoughingIndustrialIn):
    """
    Export roughing G-code with industrial post support.
    Supports: Fanuc, Haas, Mazak, Okuma
    """
    # Validate post compatibility
    exists, error = validate_post_exists(body.post)
    if not exists:
        raise HTTPException(404, error)
    
    # Generate moves
    gcode = generate_roughing_moves(body)
    
    # Build industrial context
    ctx = quick_context_industrial(body)
    resp = Response(content=gcode, media_type="text/plain")
    set_post_headers(resp, ctx)
    
    # Set filename
    resp.headers["Content-Disposition"] = build_content_disposition(
        "roughing_industrial", body.post, body.units
    )
    
    return resp
```

---

## 🧪 Testing

### **Test 1: Fanuc Generic**

```powershell
cd services/api
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000

# In another terminal
$body = @{
    paths = @(@{type="line"; x1=0; y1=0; x2=100; y2=0})
    tool_d = 6.0
    tool_number = "3"
    tool_desc = "6MM FLAT ENDMILL"
    spindle_rpm = 8000
    feed_xy = 1200
    feed_z = 300
    safe_z = 50.0
    work_offset = "G54"
    program_no = "1001"
    material = "6061 ALUMINUM"
    post = "fanuc_generic"
    units = "mm"
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Uri "http://localhost:8000/api/cam/roughing_industrial_gcode" `
    -Method POST -ContentType "application/json" -Body $body -OutFile "test_fanuc.nc"

# Verify Fanuc format
Get-Content test_fanuc.nc
```

**Expected Output:**
```gcode
%
O1001 (ROUGHING - 2025-11-05T14:30:00)
(Tool 3: 6.0mm End Mill)
(Material: 6061 ALUMINUM)
(Work Offset: G54)
G17 G21 G40 G49 G80 G90
G54
G0 Z50.0
T3 M6
G43 H3
S8000 M3
G4 P2.0
G1 X100.0 Y0.0 F1200.0
G0 Z50.0
M5
G91 G28 Z0
G28 X0 Y0
M30
%
```

---

### **Test 2: Haas VF Series**

```powershell
$body = @{
    paths = @(@{type="line"; x1=0; y1=0; x2=100; y2=0})
    tool_d = 6.0
    tool_number = "1"
    tool_desc = "6MM FLAT ENDMILL"
    spindle_rpm = 8000
    feed_xy = 1200
    safe_z = 2.0
    work_offset = "G54"
    program_no = "1001"
    material = "6061 ALUMINUM"
    coolant_mode = "flood"
    chip_conveyor = $true
    post = "haas_vf"
    units = "mm"
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Uri "http://localhost:8000/api/cam/roughing_industrial_gcode" `
    -Method POST -ContentType "application/json" -Body $body -OutFile "test_haas.nc"

Get-Content test_haas.nc
```

**Expected Output:**
```gcode
%
O1001 (ROUGHING - 2025-11-05T14:30:00)
(T1 6.0MM FLAT ENDMILL - H1 - D1)
(MATERIAL: 6061 ALUMINUM)
(WORK OFFSET: G54)
G00 G17 G40 G49 G80 G90
G20 (INCH MODE - CONVERTED FROM mm)
G54
T1 M06
G00 G90 G54 X0. Y0. S8000 M03
G43 H1 Z2.0
M08 (COOLANT ON)
G04 P1.
G1 X3.937 Y0. F47.244
M09 (COOLANT OFF)
M05 (SPINDLE OFF)
M31 (CHIP CONVEYOR FORWARD)
G00 G91 G28 Z0. (Z HOME)
G28 X0. Y0. (XY HOME)
M35 (CHIP CONVEYOR OFF)
G90
M30 (PROGRAM END)
%
```

---

### **Test 3: All Industrial Posts**

```powershell
# Test all 5 industrial posts
$posts = @("fanuc_generic", "haas_vf", "haas_mini", "mazak_iso", "okuma_osp")

foreach ($post in $posts) {
    $body = @{
        paths = @(@{type="line"; x1=0; y1=0; x2=100; y2=0})
        tool_d = 6.0
        tool_number = "1"
        spindle_rpm = 8000
        feed_xy = 1200
        work_offset = "G54"
        program_no = "1001"
        material = "ALUMINUM"
        post = $post
        units = "mm"
    } | ConvertTo-Json -Depth 5
    
    Invoke-RestMethod -Uri "http://localhost:8000/api/cam/roughing_industrial_gcode" `
        -Method POST -ContentType "application/json" -Body $body `
        -OutFile "test_$post.nc"
    
    Write-Host "✓ $post exported" -ForegroundColor Green
}

# Verify each file
Get-ChildItem test_*.nc | ForEach-Object {
    Write-Host "`n=== $($_.Name) ===" -ForegroundColor Cyan
    Get-Content $_.FullName | Select-Object -First 10
}
```

---

## 📊 Feature Comparison

| Feature | GRBL | LinuxCNC | Fanuc | Haas | Mazak | Okuma |
|---------|------|----------|-------|------|-------|-------|
| **Arcs (G2/G3)** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Tool Changer** | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Coolant** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Through-Spindle** | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| **Chip Conveyor** | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| **Work Offsets** | G54-G59 | G54-G59.3 | G54-G59 + Ext | G54-G59 + G154 | G54-G59 | G15 H01-H99 |
| **Program Numbers** | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| **Tool Length Comp** | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Cutter Comp** | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Max RPM** | ~30k | Variable | ~12k | ~10k | ~15k | ~12k |

---

## 🎯 Benefits for Production Shops

### **1. Professional Output**
- O-codes with program numbers
- Tool descriptions in comments
- Material specifications
- Work offset declarations
- Proper coolant control

### **2. Shop Floor Ready**
- No manual post-editing required
- Consistent format across all programs
- Proper tool change sequences
- Safe retract heights

### **3. Advanced Features**
- Through-spindle coolant (Haas)
- Chip conveyor control (Haas)
- Extended work offsets (G154 P1-P99)
- Tool length compensation (G43 H)

### **4. Multi-Machine Support**
- Single toolpath → Multiple posts
- Export for both hobby (GRBL) and industrial (Haas)
- Easy machine migration

---

## 🔧 Configuration Best Practices

### **Fanuc Generic**
```json
{
  "post": "fanuc_generic",
  "tool_number": "1",
  "spindle_rpm": 8000,
  "safe_z": 50.0,
  "work_offset": "G54",
  "program_no": "1001",
  "material": "6061 ALUMINUM"
}
```

### **Haas VF/VM**
```json
{
  "post": "haas_vf",
  "tool_number": "1",
  "tool_desc": "6MM FLAT ENDMILL",
  "spindle_rpm": 8000,
  "safe_z": 2.0,
  "work_offset": "G54",
  "program_no": "1001",
  "material": "6061 ALUMINUM",
  "coolant_mode": "flood",
  "chip_conveyor": true
}
```

### **Haas Mini Mill**
```json
{
  "post": "haas_mini",
  "tool_number": "1",
  "spindle_rpm": 6000,
  "work_offset": "G54",
  "program_no": "1000"
}
```

---

## 📚 Documentation Updates

### **Update 1: POST_INJECTION_HELPERS_QUICKREF.md**

Add industrial context section:

```markdown
### **quick_context_industrial(body: BaseModel) -> Dict**
Extract industrial post context (Fanuc, Haas, Mazak, Okuma).

Fields extracted:
- Standard fields (post, units, tool_d, feed_xy, etc.)
- Tool description and flute count
- Work offset and program number
- Material specification
- Coolant mode (flood, mist, tsc)
- Chip conveyor control

Usage:
```python
ctx = quick_context_industrial(body)
set_post_headers(resp, ctx)
```

### **Update 2: PATCH_N_SERIES_ROLLUP.md**

Add industrial posts to summary table:

| Post | Type | Features |
|------|------|----------|
| GRBL | Hobby | Basic arcs |
| LinuxCNC | Open Source | Full featured |
| PathPilot | Tormach | Enhanced LinuxCNC |
| MASSO | Australian | Simple format |
| Mach4 | Windows | Legacy support |
| **Fanuc** 🆕 | **Industrial** | **O-codes, tool changer** |
| **Haas** 🆕 | **Industrial** | **TSC, chip conveyor** |
| **Mazak** 🆕 | **Industrial** | **ISO mode** |
| **Okuma** 🆕 | **Industrial** | **OSP control** |

---

## ✅ Implementation Checklist

### **Phase 1: Post Configs (30 min)**
- [ ] Create `fanuc_generic.json`
- [ ] Create `haas_vf.json`
- [ ] Create `haas_mini.json`
- [ ] Create `mazak_iso.json`
- [ ] Create `okuma_osp.json`
- [ ] Test loading posts via API

### **Phase 2: Schema Updates (20 min)**
- [ ] Add `PostIndustrialMixin` to helpers
- [ ] Add `quick_context_industrial()` function
- [ ] Update token expansion for new fields

### **Phase 3: Router Integration (10 min)**
- [ ] Create example router endpoint (roughing_industrial)
- [ ] Test with Fanuc post
- [ ] Test with Haas post

### **Phase 4: Testing (30 min)**
- [ ] Test all 5 industrial posts
- [ ] Verify O-codes and program numbers
- [ ] Verify tool change sequences
- [ ] Verify coolant/chip conveyor codes
- [ ] Test unit conversion (mm → inch for Haas)

### **Phase 5: Documentation (20 min)**
- [ ] Update POST_INJECTION_HELPERS_QUICKREF.md
- [ ] Update PATCH_N_SERIES_ROLLUP.md
- [ ] Create example G-code outputs
- [ ] Document feature comparison table

**Total Effort:** ~2 hours

---

## 🐛 Troubleshooting

### **Issue:** Haas expects inch mode but receiving mm
**Solution:** Set `units="inch"` in request or configure auto-conversion:
```json
{
  "units": "mm",
  "post": "haas_vf"
}
```
Drop-in will auto-convert if post specifies `G20` in header.

### **Issue:** Missing O-code or percent signs
**Solution:** Verify post has `%` in header/footer and `O{PROGRAM_NO}` line.

### **Issue:** Tool change sequence incorrect
**Solution:** Check post header for proper sequence:
```
T{TOOL} M06
G43 H{TOOL}
S{RPM} M03
```

---

## 🔮 Future Enhancements

### **N.06: Sub-Program Support**
- M98 P-code calls
- Multi-tool operations
- Tool library integration

### **N.07: Probing Cycles**
- G65 macro calls (Fanuc/Haas)
- Work offset measurement
- Tool length measurement

### **N.08: Advanced Coolant**
- Programmable coolant (M88)
- High-pressure coolant
- Air blast (M83)

---

## 📞 Support

**Fanuc Resources:**
- Fanuc 0i/31i/32i Parameter Manual
- ISO G-code reference

**Haas Resources:**
- Haas Mill Operator's Manual
- Haas G-code reference (P/N 96-0232)
- VF/VM Series Quick Reference Guide

**Integration Help:**
- See POST_INJECTION_HELPERS_QUICKREF.md for context builders
- See PATCH_N04_ROUTER_SNIPPETS.md for integration patterns

---

## 🏆 Summary

Patch N.05 adds **5 industrial CNC post-processors**:

✅ **Fanuc 0i/31i/32i** - Generic ISO/DIN format  
✅ **Haas VF/VM** - Full-featured with TSC and chip conveyor  
✅ **Haas Mini Mill** - Compact format for mini mills  
✅ **Mazak ISO** - EIA/ISO mode for Mazatrol machines  
✅ **Okuma OSP** - OSP control format  

**New Features:**
- Program numbers (O-codes)
- Tool change sequences (M6 + G43)
- Coolant control (M7/M8/M9/M88)
- Chip conveyor (M31/M33/M35)
- Extended work offsets (G154 P1-P99)
- Material specifications in headers

**Implementation:** 2 hours  
**Status:** 🔜 Ready for implementation  
**Next Steps:** Create JSON configs and test with production parts
