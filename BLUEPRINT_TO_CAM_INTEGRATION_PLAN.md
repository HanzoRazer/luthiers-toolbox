# Blueprint → CAM Integration Plan

**Status:** 🎯 Strategic Integration Roadmap  
**Date:** November 8, 2025  
**Goal:** Unify Blueprint Import (Phase 2) with existing CAM/Art Studio workflows

---

## 🔍 Analysis Summary

Based on the data dump, I've identified **3 critical integration points** between Blueprint development and the CAM/Art Studio ecosystem:

### **Existing CAM Infrastructure:**
1. **N17 Polygon Offset Router** - Arc-based toolpath generation with pyclipper
2. **Adaptive Pocket (Module L)** - L.3 with trochoids + jerk-aware time
3. **DXF Preflight System** - Layer extraction and validation
4. **Bridge Pocket Workflow** - Lutherie-specific pocket operations
5. **Helical Smoke + Badges** - CI/CD testing with controller presets

### **Blueprint Phase 2 Output:**
- **DXF R2000** with `GEOMETRY` layer (closed LWPOLYLINE contours)
- Compatible with **ezdxf** library (same as existing system)
- Ready for pyclipper offset operations

---

## 🎯 Integration Strategy

### **Phase 2.5: Blueprint → CAM Bridge** (Immediate Priority)

Create seamless pipeline: **Blueprint Image → AI Analysis → Geometry Detection → CAM Toolpath**

#### **1. DXF → Adaptive Pocket Bridge**

**Endpoint:** `POST /api/cam/blueprint/to-adaptive`

**Request:**
```json
{
  "dxf_path": "/tmp/blueprint_phase2_xxx/geometry.dxf",
  "analysis_data": { /* AI dimensions from /blueprint/analyze */ },
  "tool_d": 6.0,
  "stepover": 0.45,
  "stepdown": 2.0,
  "strategy": "Spiral",
  "margin": 0.5,
  // All adaptive pocket parameters from PlanIn model
  "corner_radius_min": 1.0,
  "use_trochoids": false,
  "jerk_aware": true
}
```

**Response:**
```json
{
  "moves": [ /* G-code moves */ ],
  "stats": {
    "length_mm": 547.3,
    "time_s": 32.1,
    "time_jerk_s": 35.2
  },
  "overlays": [ /* HUD markers */ ],
  "gcode_url": "/api/cam/blueprint/download/xxx.nc"
}
```

**Implementation:**
```python
# services/api/app/routers/blueprint_cam_bridge.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Tuple, Dict, Any, Optional
import ezdxf

from ..routers.adaptive_router import PlanIn, PlanOut, plan
from .blueprint_router import VectorizeResponse

router = APIRouter(prefix="/cam/blueprint", tags=["cam", "blueprint"])

class BlueprintToAdaptiveRequest(BaseModel):
    """Bridge: DXF geometry → Adaptive pocket toolpath"""
    dxf_path: str
    analysis_data: Dict[str, Any]
    
    # Inherit all adaptive pocket parameters
    tool_d: float
    stepover: float = 0.45
    stepdown: float = 2.0
    margin: float = 0.5
    strategy: str = "Spiral"
    smoothing: float = 0.5
    climb: bool = True
    feed_xy: float = 1200.0
    safe_z: float = 5.0
    z_rough: float = -1.5
    corner_radius_min: float = 1.0
    target_stepover: float = 0.45
    slowdown_feed_pct: float = 60.0
    use_trochoids: bool = False
    trochoid_radius: float = 1.5
    trochoid_pitch: float = 3.0
    jerk_aware: bool = False
    machine_feed_xy: float = 1200.0
    machine_rapid: float = 3000.0
    machine_accel: float = 800.0
    machine_jerk: float = 2000.0
    corner_tol_mm: float = 0.2

@router.post("/to-adaptive", response_model=PlanOut)
def blueprint_to_adaptive(req: BlueprintToAdaptiveRequest):
    """
    Bridge endpoint: Blueprint DXF → Adaptive pocket toolpath
    
    Workflow:
    1. Load DXF from Phase 2 vectorization
    2. Extract GEOMETRY layer (closed polylines)
    3. Convert to adaptive pocket loops format
    4. Generate toolpath with L.3 features
    """
    try:
        # Load DXF
        doc = ezdxf.readfile(req.dxf_path)
        msp = doc.modelspace()
        
        # Extract closed polylines from GEOMETRY layer
        loops = []
        for entity in msp.query('LWPOLYLINE[layer=="GEOMETRY"]'):
            if entity.closed:
                points = [(p[0], p[1]) for p in entity.get_points()]
                loops.append({"pts": points})
        
        if not loops:
            raise HTTPException(
                status_code=400,
                detail="No closed polylines found on GEOMETRY layer"
            )
        
        # Build adaptive pocket request
        adaptive_req = PlanIn(
            loops=loops,
            units="mm",
            tool_d=req.tool_d,
            stepover=req.stepover,
            stepdown=req.stepdown,
            margin=req.margin,
            strategy=req.strategy,
            smoothing=req.smoothing,
            climb=req.climb,
            feed_xy=req.feed_xy,
            safe_z=req.safe_z,
            z_rough=req.z_rough,
            corner_radius_min=req.corner_radius_min,
            target_stepover=req.target_stepover,
            slowdown_feed_pct=req.slowdown_feed_pct,
            use_trochoids=req.use_trochoids,
            trochoid_radius=req.trochoid_radius,
            trochoid_pitch=req.trochoid_pitch,
            jerk_aware=req.jerk_aware,
            machine_feed_xy=req.machine_feed_xy,
            machine_rapid=req.machine_rapid,
            machine_accel=req.machine_accel,
            machine_jerk=req.machine_jerk,
            corner_tol_mm=req.corner_tol_mm
        )
        
        # Generate adaptive toolpath
        result = plan(adaptive_req)
        
        return result
    
    except ezdxf.DXFError as e:
        raise HTTPException(status_code=400, detail=f"DXF error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
```

---

#### **2. DXF → N17 Polygon Offset Bridge**

**Endpoint:** `POST /api/cam/blueprint/to-offset`

**Use Case:** Blueprint → Offset toolpath with arc linking (alternative to adaptive)

**Request:**
```json
{
  "dxf_path": "/tmp/blueprint_phase2_xxx/geometry.dxf",
  "tool_dia": 6.0,
  "stepover": 2.4,
  "inward": true,
  "z": -1.5,
  "safe_z": 5.0,
  "feed": 600.0,
  "feed_arc": 500.0,
  "feed_floor": 300.0,
  "join_type": "round",
  "arc_tolerance": 0.15,
  "link_mode": "arc",
  "link_radius": 1.0
}
```

**Implementation:**
```python
@router.post("/to-offset")
def blueprint_to_offset(req: PolygonOffsetRequest):
    """
    Bridge endpoint: Blueprint DXF → N17 polygon offset with arcs
    
    Uses N17 utilities:
    - toolpath_offsets (pyclipper-based)
    - emit_xy_with_arcs (G2/G3 linking)
    """
    # Same DXF extraction as above
    doc = ezdxf.readfile(req.dxf_path)
    # ... extract first closed polyline from GEOMETRY layer
    
    # Generate offset paths
    from server.util.polygon_offset_n17 import toolpath_offsets
    from server.util.gcode_emit_advanced import emit_xy_with_arcs
    
    paths = toolpath_offsets(
        polygon,
        req.tool_dia,
        req.stepover,
        inward=req.inward,
        join_type=req.join_type,
        arc_tolerance=req.arc_tolerance
    )
    
    nc = emit_xy_with_arcs(
        paths,
        z=req.z,
        safe_z=req.safe_z,
        units=req.units,
        feed=req.feed,
        feed_arc=req.feed_arc,
        feed_floor=req.feed_floor,
        link_radius=req.link_radius
    )
    
    return Response(content=nc, media_type="text/plain")
```

---

#### **3. Unified Blueprint → CAM Endpoint**

**Endpoint:** `POST /api/cam/blueprint/process` (One-Stop Shop)

**Request:**
```json
{
  "blueprint_file": "guitar_body.png",  // multipart upload
  "scale_factor": 1.0,
  "cam_mode": "adaptive",  // or "offset"
  "tool_d": 6.0,
  "stepover": 0.45,
  "strategy": "Spiral",
  // ... all CAM parameters
  "export_formats": ["gcode", "dxf", "svg"],
  "post_id": "GRBL"
}
```

**Response:**
```json
{
  "analysis": { /* AI dimensions */ },
  "geometry": { /* Detected contours */ },
  "toolpath": { /* Adaptive pocket result */ },
  "exports": {
    "gcode": "/api/cam/blueprint/download/xxx_GRBL.nc",
    "dxf": "/api/cam/blueprint/download/xxx.dxf",
    "svg": "/api/cam/blueprint/download/xxx.svg"
  }
}
```

**Workflow:**
1. Upload blueprint → `/blueprint/analyze`
2. Vectorize geometry → `/blueprint/vectorize-geometry`
3. Choose CAM mode → `/cam/blueprint/to-adaptive` or `/cam/blueprint/to-offset`
4. Export with post-processor → existing G-code export system

---

## 🔄 Integration with Existing Systems

### **A. Adaptive Pocket (Module L.3)**

**Current State:**
- Request model: `PlanIn` with 30+ parameters
- Response model: `PlanOut` with moves, stats, overlays
- Features: Trochoids, jerk-aware time, adaptive stepover, min-fillet

**Integration:**
```python
# Blueprint DXF → Adaptive pocket loops
loops = extract_dxf_geometry(dxf_path, layer="GEOMETRY")

# Use existing adaptive router
adaptive_result = plan(PlanIn(
    loops=loops,
    tool_d=6.0,
    use_trochoids=True,
    jerk_aware=True,
    # ... other L.3 parameters
))
```

**Benefits:**
- Zero duplication - reuse existing L.3 implementation
- All advanced features available (trochoids, jerk, fillets)
- Consistent API for both manual and blueprint workflows

---

### **B. N17 Polygon Offset**

**Current State:**
- Request model: `PolyOffsetReq`
- Utilities: `toolpath_offsets`, `emit_xy_with_arcs`
- Features: Join types (miter/round/bevel), arc linking, feed floors

**Integration:**
```python
# Blueprint DXF → First closed polygon
polygon = extract_dxf_first_polygon(dxf_path, layer="GEOMETRY")

# Use N17 utilities
paths = toolpath_offsets(polygon, tool_dia=6.0, join_type="round")
nc = emit_xy_with_arcs(paths, link_radius=1.0, feed_floor=300.0)
```

**Benefits:**
- Simpler alternative to adaptive pocketing
- Good for single-contour operations
- Arc linking reduces G-code size

---

### **C. DXF Preflight System**

**Current State:**
- Endpoint: `/cam/dxf_preflight`
- Features: Layer analysis, unit detection, validation
- Profiles: Generic, Bridge

**Integration:**
```python
# Run preflight on Blueprint Phase 2 DXF
preflight_result = client.post(
    "/cam/dxf_preflight",
    files={"file": open("geometry.dxf", "rb")},
    params={"profile": "bridge", "cam_layer_prefix": "GEOMETRY"}
)

# Validate before CAM processing
if not preflight_result.json()["ok"]:
    # Show issues to user
    issues = preflight_result.json()["issues"]
```

**Benefits:**
- Catch DXF issues before CAM processing
- Validate closed paths, layer structure, units
- Consistent validation across manual and blueprint workflows

---

### **D. Helical Smoke + Badges CI**

**Current State:**
- GitHub Actions workflow
- Tests all controller presets (GRBL, Mach3, Haas, Marlin)
- Generates live status badges

**Integration:**
```yaml
# Add blueprint smoke test to existing workflow

jobs:
  smoke-blueprint:
    runs-on: ubuntu-latest
    steps:
      - name: Test Blueprint → Adaptive pipeline
        run: |
          python test_blueprint_to_cam.py
          # Should generate valid G-code for all presets
      
      - name: Validate DXF export
        run: |
          python test_blueprint_dxf_quality.py
          # Check closed paths, layer structure, units
```

**Benefits:**
- Automated testing of blueprint → CAM pipeline
- Catch regressions in geometry detection
- Validate G-code output quality

---

## 📊 Data Flow Diagram

```
┌─────────────────┐
│  Blueprint PDF  │
│   or Image      │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│  /blueprint/analyze     │ ← Phase 1: AI Analysis
│  (Claude Sonnet 4)      │
└────────┬────────────────┘
         │ {dimensions, scale, confidence}
         ▼
┌─────────────────────────┐
│ /blueprint/vectorize    │ ← Phase 2: OpenCV + DXF
│  (Canny + Hough)        │
└────────┬────────────────┘
         │ geometry.dxf (GEOMETRY layer)
         │ geometry.svg
         ▼
    ┌────────────────────┐
    │  DXF Preflight     │ ← Validation
    │  (optional)        │
    └────────┬───────────┘
             │ {ok, layers, issues}
             ▼
    ┌────────────────────────────┐
    │  CAM Processing Mode       │
    └────────────────────────────┘
             │
      ┌──────┴──────┐
      │             │
      ▼             ▼
┌──────────────┐  ┌──────────────┐
│  Adaptive    │  │  N17 Offset  │
│  Pocket L.3  │  │  (Arc Link)  │
└──────┬───────┘  └──────┬───────┘
       │                 │
       └────────┬────────┘
                │ {moves, stats, overlays}
                ▼
      ┌──────────────────┐
      │  Post Processor  │ ← Existing System
      │  (5 controllers) │
      └────────┬─────────┘
               │
               ▼
      ┌──────────────────┐
      │  G-code Output   │
      │  DXF/SVG Export  │
      └──────────────────┘
```

---

## 🛠️ Implementation Checklist

### **Phase 2.5: Blueprint → CAM Bridge**

- [ ] Create `blueprint_cam_bridge.py` router
- [ ] Implement `blueprint_to_adaptive()` endpoint
- [ ] Implement `blueprint_to_offset()` endpoint
- [ ] Add DXF extraction utilities
- [ ] Integrate with existing `adaptive_router.py`
- [ ] Integrate with N17 `polygon_offset_n17.py`
- [ ] Add unit tests for DXF → loops conversion
- [ ] Add smoke tests for blueprint → CAM pipeline

### **Phase 2.5: Vue UI Integration**

- [ ] Add "Generate Toolpath" button to `BlueprintImporter.vue`
- [ ] Add CAM mode selector (Adaptive vs Offset)
- [ ] Add tool parameters form (tool_d, stepover, etc.)
- [ ] Add post-processor selector (reuse existing component)
- [ ] Add preview canvas for toolpath overlay
- [ ] Add download buttons (G-code, DXF, SVG)

### **Phase 2.5: Testing & Validation**

- [ ] Test with Les Paul body blueprint
- [ ] Test with Strat body blueprint
- [ ] Test with Tele body blueprint
- [ ] Validate DXF import in Fusion 360
- [ ] Validate G-code in CAMotics simulator
- [ ] Measure dimension accuracy (target: >70%)
- [ ] Add to CI/CD smoke tests

---

## 📚 Code Examples

### **Example 1: Blueprint → Adaptive Pocket (Full Pipeline)**

```python
from fastapi.testclient import TestClient
from app.main import app
import json

client = TestClient(app)

# Step 1: Analyze blueprint
with open("les_paul_body.png", "rb") as f:
    analysis_response = client.post(
        "/blueprint/analyze",
        files={"file": ("les_paul_body.png", f, "image/png")}
    )

analysis = analysis_response.json()["analysis"]

# Step 2: Vectorize geometry
with open("les_paul_body.png", "rb") as f:
    vectorize_response = client.post(
        "/blueprint/vectorize-geometry",
        files={"file": ("les_paul_body.png", f, "image/png")},
        data={
            "analysis_data": json.dumps(analysis),
            "scale_factor": 1.0
        }
    )

dxf_path = vectorize_response.json()["dxf_path"]

# Step 3: Generate adaptive toolpath
toolpath_response = client.post(
    "/cam/blueprint/to-adaptive",
    json={
        "dxf_path": dxf_path,
        "analysis_data": analysis,
        "tool_d": 6.0,
        "stepover": 0.45,
        "strategy": "Spiral",
        "use_trochoids": True,
        "jerk_aware": True
    }
)

result = toolpath_response.json()
print(f"Toolpath generated: {len(result['moves'])} moves")
print(f"Estimated time: {result['stats']['time_jerk_s']:.1f}s")
print(f"Contours detected: {vectorize_response.json()['contours_detected']}")
```

### **Example 2: Blueprint → N17 Offset (Arc Linking)**

```python
# Same steps 1-2 as above

# Step 3: Generate N17 offset toolpath
nc_response = client.post(
    "/cam/blueprint/to-offset",
    json={
        "dxf_path": dxf_path,
        "tool_dia": 6.0,
        "stepover": 2.4,
        "inward": True,
        "join_type": "round",
        "arc_tolerance": 0.15,
        "link_mode": "arc",
        "link_radius": 1.0,
        "feed": 600.0,
        "feed_arc": 500.0,
        "feed_floor": 300.0
    }
)

gcode = nc_response.text
print(f"G-code size: {len(gcode)} bytes")
```

---

## 🎯 Strategic Benefits

### **1. Zero Duplication**
- Reuse existing adaptive pocket engine (L.3)
- Reuse existing N17 polygon offset utilities
- Reuse existing post-processor system
- Reuse existing DXF preflight validation

### **2. Consistent API**
- Same request/response models across manual and blueprint workflows
- Same CAM parameters (tool_d, stepover, strategy, etc.)
- Same post-processor integration
- Same G-code export format

### **3. Incremental Adoption**
- Blueprint users can opt-in to CAM generation
- Manual CAM users unaffected
- Each endpoint independent (analyze → vectorize → CAM)
- Progressive enhancement strategy

### **4. Testing Coverage**
- Add to existing Helical Smoke CI
- Reuse existing smoke test infrastructure
- Automated validation of blueprint → CAM pipeline
- Live badges for blueprint integration status

---

## 🚀 Next Steps

### **Immediate (This Sprint)**
1. ✅ Review this integration plan
2. Create `blueprint_cam_bridge.py` router
3. Implement `blueprint_to_adaptive()` endpoint
4. Test with Phase 2 DXF output

### **Short Term (Next Sprint)**
1. Implement `blueprint_to_offset()` endpoint
2. Add Vue UI controls to `BlueprintImporter.vue`
3. Add unit tests for DXF extraction
4. Test with real guitar blueprints

### **Medium Term (Month 2)**
1. Add to CI/CD smoke tests
2. Implement unified `/cam/blueprint/process` endpoint
3. Add toolpath preview overlay
4. Validate with lutherie community

---

## 🤔 Questions to Answer

1. **Priority:** Which CAM mode should we implement first?
   - Adaptive pocket (L.3 with all features)
   - N17 offset (simpler, arc linking)
   - Both in parallel

2. **DXF Layer Strategy:** Should Blueprint Phase 2 change layer naming?
   - Keep `GEOMETRY` layer (current)
   - Switch to `CAM_POCKET` layer (matches existing system)
   - Support both with configurable prefix

3. **Scale Calibration:** When should it happen?
   - During vectorization (Phase 2)
   - During CAM processing (Phase 2.5)
   - User-adjustable after both

4. **Post-Processor Integration:** How to handle post selection?
   - Add to blueprint endpoints (new parameter)
   - Use separate export endpoint (existing system)
   - Both options available

5. **Testing Strategy:** What's the validation criteria?
   - DXF imports cleanly into Fusion 360
   - G-code simulates correctly in CAMotics
   - Dimension accuracy >70% vs AI analysis
   - All controller presets generate valid output

---

**Status:** 📋 Ready for Implementation  
**Priority:** High (Phase 2.5 critical for blueprint adoption)  
**Effort:** Medium (2-3 days for core bridge endpoints)  
**Risk:** Low (leverages existing stable systems)

---

**Let me know which integration point you'd like to start with!**
