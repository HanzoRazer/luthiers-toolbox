# Patch N.04: Router Integration Snippets for Post Injection

**Status:** ✅ Copy-Paste Ready  
**Date:** November 5, 2025  
**Dependencies:** Post Injection Drop-In (N.03)

---

## 🎯 Overview

Quick copy-paste snippets for integrating post injection into existing CAM routers. Three patterns: **Basic** (zero changes), **Standard** (minimal context), and **Rich** (full tokens).

---

## 📋 Pattern 1: Basic (Zero Changes)

**Use when:** Router already returns `text/plain` and you want automatic post wrapping with no code changes.

**Requirements:**
- Endpoint returns `text/plain` response
- Path starts with `/cam/` or `/vcarve/` or `/api/cam/` or `/api/vcarve/`
- Middleware is installed in `main.py`

**What you get:**
- Automatic header/footer injection if `post` field in request body
- Basic token expansion (DATE, UNITS)
- No code changes needed

**Example:**
```python
# Your existing router - NO CHANGES NEEDED
@router.post("/roughing_gcode")
def export_roughing(body: RoughingIn):
    gcode = generate_roughing_moves(body)
    return Response(content=gcode, media_type="text/plain")
```

**Client request:**
```json
{
  "paths": [...],
  "tool_d": 6.0,
  "feed_xy": 1200,
  "post": "grbl",  // <-- Middleware detects this
  "units": "mm"
}
```

**Middleware automatically wraps output:**
```gcode
(ToolBox)
(Date 2025-11-05)
G21 ; units MM
G90
G0 Z5.0000
...
M30
```

---

## 📋 Pattern 2: Standard (Minimal Context)

**Use when:** You want basic token expansion (tool diameter, feeds) with minimal code.

**Add to router:**
```python
from starlette.responses import Response
from ..post_injection_dropin import build_post_context, set_post_headers

@router.post("/roughing_gcode")
def export_roughing(body: RoughingIn):
    # 1. Generate G-code (unchanged)
    gcode = generate_roughing_moves(body)
    
    # 2. Build minimal context (3 lines)
    ctx = build_post_context(
        post=getattr(body, 'post', None),
        units=getattr(body, 'units', 'mm'),
        DIAM=getattr(body, 'tool_d', None),
        FEED_XY=getattr(body, 'feed_xy', None)
    )
    
    # 3. Set context header (2 lines)
    resp = Response(content=gcode, media_type="text/plain")
    set_post_headers(resp, ctx)
    return resp
```

**What you get:**
- Tool diameter in header: `(Tool 6.0mm)`
- Feed rate in header: `(Feed XY: 1200 mm/min)`
- Units command: `G21` or `G20`

---

## 📋 Pattern 3: Rich (Full Tokens)

**Use when:** You want complete token expansion for professional G-code comments.

**Add to router:**
```python
from starlette.responses import Response
from ..post_injection_dropin import build_post_context, set_post_headers

@router.post("/finishing_gcode")
def export_finishing(body: FinishingIn):
    # 1. Generate G-code (unchanged)
    gcode = generate_finishing_moves(body)
    
    # 2. Build rich context (10+ lines)
    ctx = build_post_context(
        post=getattr(body, 'post', None),
        post_mode=getattr(body, 'post_mode', 'auto'),
        units=getattr(body, 'units', 'mm'),
        TOOL=getattr(body, 'tool_number', None),
        DIAM=getattr(body, 'tool_d', None),
        FEED_XY=getattr(body, 'feed_xy', None),
        RPM=getattr(body, 'spindle_rpm', None),
        SAFE_Z=getattr(body, 'safe_z', 5.0),
        WORK_OFFSET=getattr(body, 'work_offset', 'G54'),
        PROGRAM_NO=getattr(body, 'program_no', None),
        machine_id=getattr(body, 'machine_id', None)
    )
    
    # 3. Set context header (2 lines)
    resp = Response(content=gcode, media_type="text/plain")
    set_post_headers(resp, ctx)
    return resp
```

**What you get:**
```gcode
(ToolBox)
(Date 2025-11-05)
(Tool T1 - Diameter 6.0mm)
(Feed XY: 1200 mm/min)
(Spindle: 18000 RPM)
G21
G90
G54
...
M5
G0 Z5.0
M30
```

---

## 🔧 Schema Updates

### **Add Post Fields to Pydantic Models**

```python
from pydantic import BaseModel, Field
from typing import Optional

class RoughingIn(BaseModel):
    """Roughing operation input"""
    # Existing fields
    paths: List[Dict[str, Any]]
    tool_d: float = Field(..., gt=0)
    feed_xy: float = Field(..., gt=0)
    feed_z: float = Field(..., gt=0)
    
    # NEW: Post-processor fields (optional)
    post: Optional[str] = Field(None, description="Post-processor ID (grbl, linuxcnc, etc.)")
    post_mode: Optional[str] = Field("auto", pattern="^(auto|off|force)$")
    units: str = Field(default="mm", pattern="^(mm|inch)$")
    
    # NEW: Rich token fields (optional)
    tool_number: Optional[str] = Field(None, description="Tool number (T1, T2, etc.)")
    spindle_rpm: Optional[float] = Field(None, description="Spindle speed")
    safe_z: float = Field(default=5.0, description="Safe Z retract height")
    work_offset: Optional[str] = Field(None, description="Work coordinate system (G54, G55, etc.)")
    program_no: Optional[str] = Field(None, description="Program number (O1000, etc.)")
    machine_id: Optional[str] = Field(None, description="Machine profile ID")
```

---

## 📚 Complete Router Examples

### **Example 1: Roughing Router (Standard Context)**

```python
"""
Roughing G-code export with post injection support.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from starlette.responses import Response

# Import post injection helpers
from ..post_injection_dropin import build_post_context, set_post_headers

router = APIRouter(prefix="/api/cam", tags=["cam"])

class RoughingIn(BaseModel):
    paths: List[Dict[str, Any]]
    tool_d: float = Field(..., gt=0)
    feed_xy: float = Field(..., gt=0)
    feed_z: float = Field(..., gt=0)
    stepdown: float = Field(..., gt=0)
    safe_z: float = Field(default=5.0)
    
    # Post fields
    post: Optional[str] = None
    units: str = Field(default="mm")

@router.post("/roughing_gcode")
def export_roughing_gcode(body: RoughingIn):
    """Export roughing G-code with optional post-processor wrapping"""
    # Generate raw G-code moves
    moves = []
    for path in body.paths:
        # ... generate G-code from paths
        pass
    gcode = "\n".join(moves)
    
    # Build context for post injection
    ctx = build_post_context(
        post=body.post,
        units=body.units,
        DIAM=body.tool_d,
        FEED_XY=body.feed_xy,
        SAFE_Z=body.safe_z
    )
    
    # Return with context header
    resp = Response(content=gcode, media_type="text/plain")
    set_post_headers(resp, ctx)
    return resp
```

---

### **Example 2: Adaptive Pocketing (Rich Context)**

```python
"""
Adaptive pocketing G-code export with full token support.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from starlette.responses import Response

from ..post_injection_dropin import build_post_context, set_post_headers
from ..cam.adaptive_core_l3 import plan_adaptive_l3

router = APIRouter(prefix="/api/cam/pocket", tags=["pocketing"])

class AdaptivePocketIn(BaseModel):
    loops: List[Dict[str, Any]]
    tool_d: float = Field(..., gt=0)
    stepover: float = Field(..., gt=0, le=1.0)
    stepdown: float = Field(..., gt=0)
    feed_xy: float = Field(..., gt=0)
    feed_z: float = Field(..., gt=0)
    safe_z: float = Field(default=5.0)
    strategy: str = Field(default="Spiral")
    
    # Post fields
    post: Optional[str] = None
    post_mode: str = Field(default="auto")
    units: str = Field(default="mm")
    
    # Rich context
    tool_number: Optional[str] = None
    spindle_rpm: Optional[float] = None
    work_offset: Optional[str] = "G54"
    program_no: Optional[str] = None

@router.post("/adaptive/gcode")
def export_adaptive_gcode(body: AdaptivePocketIn):
    """Export adaptive pocket G-code with post-processor"""
    # Generate toolpath
    moves = plan_adaptive_l3(
        body.loops,
        body.tool_d,
        body.stepover,
        body.stepdown,
        body.strategy
    )
    
    # Convert to G-code
    gcode_lines = []
    for move in moves:
        # ... convert moves to G-code
        pass
    gcode = "\n".join(gcode_lines)
    
    # Build rich context
    ctx = build_post_context(
        post=body.post,
        post_mode=body.post_mode,
        units=body.units,
        TOOL=body.tool_number,
        DIAM=body.tool_d,
        FEED_XY=body.feed_xy,
        RPM=body.spindle_rpm,
        SAFE_Z=body.safe_z,
        WORK_OFFSET=body.work_offset,
        PROGRAM_NO=body.program_no
    )
    
    # Return with context
    resp = Response(content=gcode, media_type="text/plain")
    set_post_headers(resp, ctx)
    return resp
```

---

### **Example 3: V-Carve Router (Art Studio)**

```python
"""
V-Carve export with post injection for Art Studio.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional
from starlette.responses import Response

from ..post_injection_dropin import build_post_context, set_post_headers
from ..cam.vcarve_engine import generate_vcarve_toolpath

router = APIRouter(prefix="/api/cam_vcarve", tags=["vcarve"])

class VCarveExportIn(BaseModel):
    geometry: dict
    tool_angle: float = Field(..., gt=0, le=180)
    max_depth: float = Field(..., gt=0)
    feed_xy: float = Field(..., gt=0)
    feed_z: float = Field(..., gt=0)
    safe_z: float = Field(default=5.0)
    
    # Post fields
    post: Optional[str] = None
    units: str = Field(default="mm")
    
    # Rich context
    spindle_rpm: Optional[float] = 18000
    work_offset: Optional[str] = "G54"

@router.post("/export_gcode")
def export_vcarve_gcode(body: VCarveExportIn):
    """Export V-carve G-code with post-processor"""
    # Generate V-carve toolpath
    toolpath = generate_vcarve_toolpath(
        body.geometry,
        body.tool_angle,
        body.max_depth
    )
    
    # Convert to G-code
    gcode = toolpath_to_gcode(toolpath, body.feed_xy, body.feed_z)
    
    # Build context
    ctx = build_post_context(
        post=body.post,
        units=body.units,
        DIAM=f"V{body.tool_angle}°",  # V-bit angle
        FEED_XY=body.feed_xy,
        RPM=body.spindle_rpm,
        SAFE_Z=body.safe_z,
        WORK_OFFSET=body.work_offset
    )
    
    # Return with context
    resp = Response(content=gcode, media_type="text/plain")
    set_post_headers(resp, ctx)
    return resp
```

---

## 🧪 Testing Snippets

### **Test 1: Basic Router (No Context)**

```powershell
# Test existing router with zero changes
$body = @{
  paths = @(@{type="line"; x1=0; y1=0; x2=100; y2=0})
  tool_d = 6.0
  feed_xy = 1200
  post = "grbl"  # Middleware auto-detects
  units = "mm"
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Uri "http://localhost:8000/api/cam/roughing_gcode" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body `
  -OutFile "test_basic.nc"

# Verify
Get-Content test_basic.nc | Select-Object -First 10
# Expected: (ToolBox), G21, G90
```

---

### **Test 2: Standard Context**

```powershell
# Test with minimal context
$body = @{
  paths = @(@{type="line"; x1=0; y1=0; x2=100; y2=0})
  tool_d = 6.5
  feed_xy = 1500
  post = "linuxcnc"
  units = "mm"
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Uri "http://localhost:8000/api/cam/roughing_gcode" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body `
  -OutFile "test_standard.nc"

# Verify
Get-Content test_standard.nc | Select-Object -First 15
# Expected: (Tool 6.5mm), (Feed XY: 1500 mm/min)
```

---

### **Test 3: Rich Context**

```powershell
# Test with full token expansion
$body = @{
  loops = @(@{pts=@(@(0,0),@(100,0),@(100,60),@(0,60))})
  tool_d = 6.0
  stepover = 0.45
  stepdown = 1.5
  feed_xy = 1200
  feed_z = 400
  post = "mach4"
  units = "mm"
  tool_number = "T1"
  spindle_rpm = 18000
  work_offset = "G54"
  program_no = "O1000"
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Uri "http://localhost:8000/api/cam/pocket/adaptive/gcode" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body `
  -OutFile "test_rich.nc"

# Verify
Get-Content test_rich.nc | Select-Object -First 20
# Expected: (Tool T1 - 6.0mm), (Spindle: 18000 RPM), G54, O1000
```

---

## 📋 Migration Checklist

For each existing router:

### **Phase 1: Schema Update (5 min)**
- [ ] Add `post: Optional[str]` field
- [ ] Add `units: str` field (if not present)
- [ ] Add `post_mode: Optional[str]` field (optional)

### **Phase 2: Basic Integration (2 min)**
- [ ] Test with existing code (zero changes)
- [ ] Verify middleware wraps output
- [ ] Confirm headers/footers present

### **Phase 3: Standard Context (5 min)**
- [ ] Import `build_post_context, set_post_headers`
- [ ] Add 3-line context builder
- [ ] Add 2-line header setter
- [ ] Test with curl/PowerShell

### **Phase 4: Rich Context (10 min)**
- [ ] Add rich token fields to schema
- [ ] Expand context builder with all tokens
- [ ] Update post configs with token placeholders
- [ ] Test token expansion
- [ ] Verify output quality

---

## 🎯 Quick Reference

### **Imports**
```python
from starlette.responses import Response
from ..post_injection_dropin import build_post_context, set_post_headers
```

### **Minimal Context (3 lines)**
```python
ctx = build_post_context(post=body.post, units=body.units, DIAM=body.tool_d)
resp = Response(content=gcode, media_type="text/plain")
set_post_headers(resp, ctx)
```

### **Rich Context (10 lines)**
```python
ctx = build_post_context(
    post=body.post, post_mode=body.post_mode, units=body.units,
    TOOL=body.tool_number, DIAM=body.tool_d, FEED_XY=body.feed_xy,
    RPM=body.spindle_rpm, SAFE_Z=body.safe_z, WORK_OFFSET=body.work_offset,
    PROGRAM_NO=body.program_no, machine_id=body.machine_id
)
resp = Response(content=gcode, media_type="text/plain")
set_post_headers(resp, ctx)
```

---

## 📚 Related Documentation

- [Post Injection Drop-In Quick Ref](./POST_INJECTION_DROPIN_QUICKREF.md)
- [Patch N.03: Standardization](./PATCH_N03_STANDARDIZATION.md)
- [Patch N.01: Roughing Integration](./PATCH_N01_ROUGHING_POST_MIN.md)
- [Patch N.0: Smart Post Configurator](./PATCH_N0_SMART_POST_SCAFFOLD.md)

---

**Status:** ✅ Copy-Paste Ready  
**Patterns:** 3 (Basic, Standard, Rich)  
**Time to Integrate:** 2-15 minutes per router  
**Breaking Changes:** None
