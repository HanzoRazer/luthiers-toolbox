# Post Injection Helpers — Quick Reference

**File:** `services/api/app/post_injection_helpers.py`  
**Status:** ✅ Production Ready  
**Dependencies:** `post_injection_dropin.py`

---

## 🎯 Overview

Convenience utilities for working with the post injection drop-in system. Provides:

- **Quick context builders** (basic, standard, rich)
- **Automatic response builders** (1-line post integration)
- **Validation helpers** (post existence, compatibility)
- **Post information queries** (list posts, get tokens)
- **Filename generators** (standard naming, Content-Disposition)
- **Schema mixins** (PostMixin, PostRichMixin)
- **Testing utilities** (mock context, verification)
- **Decorator support** (`@with_post_injection`)

---

## 📦 Installation

```python
# services/api/app/main.py
from .post_injection_dropin import install_post_middleware
from .post_injection_helpers import *  # Optional: import helpers

install_post_middleware(app)
```

**Note:** Helpers are **optional** — drop-in works standalone.

---

## 🚀 Quick Start Patterns

### **Pattern 1: Auto Context (1 Line)**

```python
from .post_injection_helpers import build_post_response

@router.post("/operation_gcode")
def export_operation(body: OperationIn):
    gcode = generate_moves(body)
    return build_post_response(gcode, body, "standard")
```

**Result:** Automatic context extraction + header setting (0 router logic)

---

### **Pattern 2: Validation + Export**

```python
from .post_injection_helpers import validate_post_exists, build_post_response
from fastapi import HTTPException

@router.post("/operation_gcode")
def export_operation(body: OperationIn):
    # Validate post
    exists, error = validate_post_exists(body.post)
    if not exists:
        raise HTTPException(404, error)
    
    gcode = generate_moves(body)
    return build_post_response(gcode, body, "standard")
```

---

### **Pattern 3: Custom Filename**

```python
from .post_injection_helpers import build_post_response, build_content_disposition

@router.post("/operation_gcode")
def export_operation(body: OperationIn):
    gcode = generate_moves(body)
    resp = build_post_response(gcode, body, "standard")
    resp.headers["Content-Disposition"] = build_content_disposition(
        "roughing", body.post, body.units
    )
    return resp
```

**Result:** File downloads as `roughing_grbl_mm.nc`

---

### **Pattern 4: Decorator (Zero Boilerplate)**

```python
from .post_injection_helpers import with_post_injection

@router.post("/operation_gcode")
@with_post_injection("standard")
def export_operation(body: OperationIn):
    gcode = generate_moves(body)
    return gcode  # Decorator handles Response + context
```

---

### **Pattern 5: Schema with Mixin**

```python
from .post_injection_helpers import PostRichMixin

class RoughingIn(PostRichMixin):
    tool_d: float
    feed_xy: float
    paths: List[Dict]
    # Inherits: post, post_mode, units, tool_number, spindle_rpm, safe_z, etc.
```

---

## 📚 Function Reference

### **Context Builders**

#### `quick_context_basic(body: BaseModel) -> Dict`
Extract basic context (post, units, tool_d, feed_xy).

```python
ctx = quick_context_basic(body)
set_post_headers(resp, ctx)
```

**Fields extracted:**
- `post` → `ctx['post']`
- `units` → `ctx['units']`
- `tool_d` or `tool_diameter` → `ctx['DIAM']`
- `feed_xy` → `ctx['FEED_XY']`

---

#### `quick_context_standard(body: BaseModel) -> Dict`
Extract standard context (tool, feeds, RPM, safe Z).

```python
ctx = quick_context_standard(body)
set_post_headers(resp, ctx)
```

**Fields extracted:**
- Basic fields (post, units, tool_d, feed_xy)
- `feed_z` → `ctx['FEED_Z']`
- `spindle_rpm` or `rpm` → `ctx['RPM']`
- `safe_z` → `ctx['SAFE_Z']` (default 5.0)
- `post_mode` → `ctx['post_mode']` (default 'auto')

---

#### `quick_context_rich(body: BaseModel) -> Dict`
Extract rich context (all tokens).

```python
ctx = quick_context_rich(body)
set_post_headers(resp, ctx)
```

**Fields extracted:**
- Standard fields (above)
- `tool_number` or `tool` → `ctx['TOOL']`
- `work_offset` → `ctx['WORK_OFFSET']`
- `program_no` → `ctx['PROGRAM_NO']`
- `machine_id` → `ctx['machine_id']`

---

### **Response Builders**

#### `build_post_response(gcode: str, body: BaseModel, context_level: str = "standard") -> Response`
Build Response with automatic context extraction.

```python
gcode = generate_moves(body)
return build_post_response(gcode, body, "standard")
```

**Levels:**
- `"basic"` → Uses `quick_context_basic()`
- `"standard"` → Uses `quick_context_standard()`
- `"rich"` → Uses `quick_context_rich()`

---

#### `build_post_response_custom(gcode: str, **context_fields) -> Response`
Build Response with explicit context.

```python
return build_post_response_custom(
    gcode,
    post="grbl",
    units="mm",
    DIAM=6.0,
    FEED_XY=1200,
    RPM=18000
)
```

---

### **Validation Helpers**

#### `validate_post_exists(post_id: Optional[str]) -> Tuple[bool, Optional[str]]`
Check if post-processor exists.

```python
exists, error = validate_post_exists(body.post)
if not exists:
    raise HTTPException(404, error)
```

**Returns:**
- `(True, None)` if post exists or no post specified
- `(False, "Post 'xyz' not found")` if post not found

---

#### `validate_post_compatible(post_id: Optional[str], requires_arcs: bool = False, requires_tool_changer: bool = False) -> Tuple[bool, List[str]]`
Check post compatibility with operation requirements.

```python
ok, warnings = validate_post_compatible(body.post, requires_arcs=True)
if not ok:
    raise HTTPException(400, f"Incompatible post: {warnings}")
```

**Returns:**
- `(True, [])` if compatible
- `(False, ["Post 'xyz' may not support G2/G3 arcs"])` if incompatible

---

### **Post Information**

#### `list_available_posts() -> List[Dict]`
Get all available post-processors.

```python
posts = list_available_posts()
# [{'id': 'grbl', 'title': 'GRBL 1.1', 'controller': 'GRBL'}, ...]
```

---

#### `get_post_info(post_id: str) -> Optional[Dict]`
Get detailed post configuration.

```python
info = get_post_info("grbl")
if info:
    print(f"Controller: {info['controller']}")
    print(f"Header: {info['header']}")
```

---

#### `get_post_tokens(post_id: str) -> List[str]`
Extract all token placeholders from post config.

```python
tokens = get_post_tokens("grbl")
# ['DATE', 'UNITS', 'DIAM', 'FEED_XY', 'RPM']
```

---

### **Filename Helpers**

#### `build_gcode_filename(operation: str, post_id: Optional[str] = None, units: str = "mm", extension: str = "nc") -> str`
Generate standard G-code filename.

```python
filename = build_gcode_filename("roughing", "grbl", "mm")
# Returns: "roughing_grbl_mm.nc"
```

---

#### `build_content_disposition(operation: str, post_id: Optional[str] = None, units: str = "mm") -> str`
Generate Content-Disposition header.

```python
headers = {
    "Content-Disposition": build_content_disposition("roughing", "grbl", "mm")
}
return Response(content=gcode, headers=headers, media_type="text/plain")
```

---

### **Schema Mixins**

#### `PostMixin` (Basic)
Adds `post` and `units` fields.

```python
class OperationIn(PostMixin):
    tool_d: float
    feed_xy: float
    # Inherits: post, units
```

---

#### `PostRichMixin` (Rich)
Adds all post-related fields.

```python
class OperationIn(PostRichMixin):
    tool_d: float
    feed_xy: float
    # Inherits: post, post_mode, units, tool_number, spindle_rpm,
    #           safe_z, work_offset, program_no, machine_id
```

---

### **Testing Helpers**

#### `mock_post_context(post: str = "grbl", units: str = "mm", **overrides) -> Dict`
Create mock context for testing.

```python
ctx = mock_post_context("linuxcnc", DIAM=6.0, FEED_XY=1200, RPM=18000)
```

---

#### `verify_post_injection(gcode: str, post_id: str) -> bool`
Verify G-code has been post-processed.

```python
def test_export_with_post():
    body = OperationIn(tool_d=6.0, feed_xy=1200, post="grbl")
    result = export_operation(body)
    gcode = result.body.decode()
    assert verify_post_injection(gcode, "grbl")
```

---

## 🧪 Testing Examples

### **Test 1: Basic Response Builder**

```powershell
# Terminal
cd services/api
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000

# Another terminal
$body = @{
    paths = @(@{type="line"; x1=0; y1=0; x2=100; y2=0})
    tool_d = 6.0
    feed_xy = 1200
    post = "grbl"
    units = "mm"
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Uri "http://localhost:8000/api/cam/roughing_gcode" `
    -Method POST -ContentType "application/json" -Body $body -OutFile "test_basic.nc"

# Verify
Get-Content test_basic.nc | Select-Object -First 10
# Should show: G21, G90, G17, (POST=GRBL;...), etc.
```

---

### **Test 2: Validation**

```python
# services/api/app/routers/roughing_router.py
from ..post_injection_helpers import validate_post_exists, build_post_response
from fastapi import HTTPException

@router.post("/roughing_gcode")
def export_roughing(body: RoughingIn):
    # Validate post
    exists, error = validate_post_exists(body.post)
    if not exists:
        raise HTTPException(404, error)
    
    gcode = generate_roughing_moves(body)
    return build_post_response(gcode, body, "standard")
```

```powershell
# Test with invalid post
$body = @{
    paths = @(@{type="line"; x1=0; y1=0; x2=100; y2=0})
    tool_d = 6.0
    feed_xy = 1200
    post = "invalid_post"
    units = "mm"
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Uri "http://localhost:8000/api/cam/roughing_gcode" `
    -Method POST -ContentType "application/json" -Body $body

# Should return 404: Post-processor 'invalid_post' not found
```

---

### **Test 3: Decorator**

```python
# services/api/app/routers/adaptive_router.py
from ..post_injection_helpers import with_post_injection

@router.post("/adaptive_gcode")
@with_post_injection("rich")
def export_adaptive(body: AdaptivePocketIn):
    gcode = generate_adaptive_moves(body)
    return gcode  # Decorator wraps in Response
```

```powershell
# Test
$body = @{
    loops = @(
        @{pts = @(@(0,0), @(100,0), @(100,60), @(0,60))}
    )
    tool_d = 6.0
    stepover = 0.45
    feed_xy = 1200
    post = "linuxcnc"
    units = "mm"
    tool_number = 3
    spindle_rpm = 18000
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Uri "http://localhost:8000/api/cam/pocket/adaptive/gcode" `
    -Method POST -ContentType "application/json" -Body $body -OutFile "test_decorator.nc"

# Verify rich tokens
Get-Content test_decorator.nc | Select-Object -First 15
# Should show: (Tool: 3), (Diameter: 6.0mm), (RPM: 18000), etc.
```

---

## 📊 Comparison Table

| Pattern | Lines of Code | Features | Use Case |
|---------|---------------|----------|----------|
| **Manual** | 8-10 lines | Full control | Custom logic |
| **build_post_response** | 2 lines | Auto context + header | Standard integration |
| **Decorator** | 1 line | Zero boilerplate | Simple exports |
| **Mixin** | 1 line | Schema-level | Shared fields |

---

## 🔍 Common Patterns

### **Pattern: Validation → Export → Filename**

```python
from .post_injection_helpers import (
    validate_post_exists,
    build_post_response,
    build_content_disposition
)
from fastapi import HTTPException

@router.post("/operation_gcode")
def export_operation(body: OperationIn):
    # 1. Validate
    exists, error = validate_post_exists(body.post)
    if not exists:
        raise HTTPException(404, error)
    
    # 2. Export
    gcode = generate_moves(body)
    resp = build_post_response(gcode, body, "standard")
    
    # 3. Filename
    resp.headers["Content-Disposition"] = build_content_disposition(
        "roughing", body.post, body.units
    )
    
    return resp
```

---

### **Pattern: Arc Compatibility Check**

```python
from .post_injection_helpers import validate_post_compatible
from fastapi import HTTPException

@router.post("/vcarve_gcode")
def export_vcarve(body: VCarveIn):
    # Check arc support
    ok, warnings = validate_post_compatible(body.post, requires_arcs=True)
    if not ok:
        raise HTTPException(400, f"Incompatible post: {warnings}")
    
    gcode = generate_vcarve_moves(body)
    return build_post_response(gcode, body, "rich")
```

---

### **Pattern: List Posts Endpoint**

```python
from .post_injection_helpers import list_available_posts

@router.get("/posts")
def get_posts():
    return {"posts": list_available_posts()}
```

```json
{
  "posts": [
    {"id": "grbl", "title": "GRBL 1.1", "controller": "GRBL"},
    {"id": "linuxcnc", "title": "LinuxCNC", "controller": "LinuxCNC"},
    {"id": "pathpilot", "title": "PathPilot", "controller": "PathPilot"},
    {"id": "masso", "title": "MASSO G3", "controller": "MASSO"},
    {"id": "mach4", "title": "Mach4", "controller": "Mach4"}
  ]
}
```

---

## 🐛 Troubleshooting

### **Issue:** `ImportError: cannot import name 'build_post_response'`

**Solution:**
```python
# Ensure drop-in is imported first
from .post_injection_dropin import install_post_middleware
from .post_injection_helpers import build_post_response

install_post_middleware(app)
```

---

### **Issue:** Decorator returns `None`

**Solution:** Ensure function returns a string (G-code):
```python
@with_post_injection("standard")
def export_operation(body: OperationIn):
    gcode = generate_moves(body)
    return gcode  # Must return string, not None
```

---

### **Issue:** Context fields not extracted

**Solution:** Check field names match conventions:
```python
# These work
tool_d, tool_diameter → DIAM
feed_xy → FEED_XY
spindle_rpm, rpm → RPM

# These don't work
tool_diameter_mm → Not recognized
feed_rate_xy → Not recognized
```

---

## 🎯 Migration Checklist

- [ ] Import helpers in router
- [ ] Replace manual context building with `quick_context_*()` or `build_post_response()`
- [ ] Add validation with `validate_post_exists()` (optional)
- [ ] Add filename with `build_content_disposition()` (optional)
- [ ] Update schema with `PostMixin` or `PostRichMixin` (optional)
- [ ] Test with PowerShell commands
- [ ] Verify post injection with `verify_post_injection()` (tests)

---

## 📚 See Also

- [Drop-In Quick Reference](./POST_INJECTION_DROPIN_QUICKREF.md) - Core middleware
- [Router Snippets (N.04)](./PATCH_N04_ROUTER_SNIPPETS.md) - Integration patterns
- [Roughing Integration (N.01)](./PATCH_N01_ROUGHING_POST_MIN.md) - Example
- [Standardization (N.03)](./PATCH_N03_STANDARDIZATION.md) - Framework

---

## ✅ Summary

**Helpers provide:**
- 🚀 **Quick context builders** (basic, standard, rich) — 1-line extraction
- 🎯 **Auto response builders** — Zero boilerplate
- ✅ **Validation helpers** — Post existence, compatibility
- 📋 **Post queries** — List, info, tokens
- 📁 **Filename generators** — Standard naming
- 🧬 **Schema mixins** — Shared fields
- 🧪 **Testing utilities** — Mock, verification
- 🎨 **Decorator support** — `@with_post_injection`

**Status:** ✅ Production Ready  
**Installation:** Optional (drop-in works standalone)  
**Effort:** 0-2 minutes per router (copy-paste patterns)  
**Next Steps:** Use helpers to accelerate router migration (basic → standard → rich)
