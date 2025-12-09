# RMOS 2.0 Implementation Quick Reference

**Status:** ✅ Architecturally Complete (Untested)  
**Branch:** `feature/rmos-2-0-skeleton`  
**Date:** December 4, 2025

---

## 📦 What Was Built

### **Core Architecture Files**

```
services/api/app/
├── rmos/
│   ├── __init__.py              # Public API facade
│   ├── api_contracts.py         # Factory pattern, type definitions
│   ├── api_routes.py            # FastAPI endpoints
│   └── feasibility_scorer.py    # Aggregation logic
├── calculators/
│   └── service.py               # Unified calculator facade
└── toolpath/
    ├── geometry_engine.py       # Shapely/ML selector
    └── service.py               # Toolpath planning
```

### **Router Registration**

Updated `services/api/app/main.py`:
- Import: `from .rmos import rmos_router`
- Registration: `app.include_router(rmos_router, prefix="/api/rmos", tags=["RMOS"])`

---

## 🎯 API Endpoints

### **POST /api/rmos/feasibility**
Check manufacturing feasibility for rosette design.

**Request:**
```json
{
  "design": {
    "outer_diameter_mm": 100.0,
    "inner_diameter_mm": 20.0,
    "ring_count": 3,
    "pattern_type": "herringbone"
  },
  "context": {
    "material_id": "maple",
    "tool_id": "end_mill_6mm",
    "use_shapely_geometry": true
  }
}
```

**Response:**
```json
{
  "score": 85.5,
  "risk_bucket": "GREEN",
  "warnings": [],
  "efficiency": 89.2,
  "estimated_cut_time_seconds": 245.3,
  "calculator_results": {
    "chipload": {"score": 100, "chipload_mm": 0.0333},
    "heat": {"score": 100, "heat_index": 4.5},
    "deflection": {"score": 100, "deflection_mm": 0.0012},
    "rim_speed": {"score": 100, "rim_speed_m_per_min": 56.5},
    "geometry": {"score": 80, "complexity_index": 4.5}
  }
}
```

### **POST /api/rmos/bom**
Generate Bill of Materials for rosette design.

**Request:**
```json
{
  "design": {
    "outer_diameter_mm": 100.0,
    "inner_diameter_mm": 20.0,
    "ring_count": 3,
    "pattern_type": "herringbone"
  }
}
```

**Response:**
```json
{
  "material_required_mm2": 7853.98,
  "tool_ids": ["end_mill_6mm", "v_bit_60deg"],
  "estimated_waste_percent": 4.0,
  "notes": [
    "Material: 7853.98 mm²",
    "Waste: 4.0%",
    "Tools required: 2"
  ]
}
```

### **POST /api/rmos/toolpaths**
Generate toolpath plan for rosette design.

**Request:**
```json
{
  "design": {
    "outer_diameter_mm": 100.0,
    "inner_diameter_mm": 20.0,
    "ring_count": 3,
    "pattern_type": "herringbone"
  },
  "context": {
    "use_shapely_geometry": true
  }
}
```

**Response:**
```json
{
  "toolpaths": [
    {"operation": "rapid", "code": "G0", "z": 5.0},
    {"operation": "rapid", "code": "G0", "x": 50.0, "y": 0.0},
    {"operation": "plunge", "code": "G1", "z": -1.5, "f": 300},
    {"operation": "cut", "code": "G1", "x": 49.9, "y": 0.5, "f": 1200}
  ],
  "total_length_mm": 942.5,
  "estimated_time_seconds": 62.3,
  "warnings": []
}
```

### **GET /api/rmos/health**
Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "module": "RMOS 2.0",
  "version": "2.0.0",
  "endpoints": ["/feasibility", "/bom", "/toolpaths"]
}
```

---

## 🏗️ Architecture Patterns

### **1. Factory Pattern (RmosServices)**
Lazy-loaded service instantiation to prevent circular dependencies.

```python
from .api_contracts import RmosServices

# Get feasibility scorer
scorer = RmosServices.get_feasibility_scorer()
result = scorer(design, ctx)

# Get calculator service
calc_service = RmosServices.get_calculator_service()
bom = calc_service.compute_bom(design, ctx)

# Get geometry engine (strategy pattern)
engine = RmosServices.get_geometry_engine(ctx)
paths = engine.generate_rosette_paths(design, ctx)
```

### **2. Strategy Pattern (Geometry Engine)**
Selector chooses ML vs Shapely based on context flag.

```python
from toolpath.geometry_engine import get_geometry_engine

# Use Shapely (production)
ctx = RmosContext(use_shapely_geometry=True)
engine = get_geometry_engine(ctx)  # Returns ShapelyGeometryEngine

# Use ML (legacy)
ctx = RmosContext(use_shapely_geometry=False)
engine = get_geometry_engine(ctx)  # Returns MLGeometryEngine
```

### **3. Weighted Scoring (Feasibility)**
5 calculators with weighted contributions:
- **Chipload** (30%): Feed rate / (RPM × flutes)
- **Heat** (25%): Heat dissipation based on ring count
- **Deflection** (20%): Tool deflection at cut depth
- **Rim Speed** (15%): Surface speed at outer diameter
- **Geometry** (10%): Complexity based on ring count + pattern

**Risk Bucketing:**
- Score ≥ 80 → GREEN
- Score ≥ 50 → YELLOW
- Score < 50 → RED
- Worst-case propagation: One RED = Overall RED

---

## 🔧 Calculator Service Details

### **CalculatorService Methods**

```python
from calculators.service import CalculatorService

calc = CalculatorService()

# Individual checks (return dict with 'score', 'warning', metadata)
chipload_result = calc.check_chipload_feasibility(design, ctx)
heat_result = calc.check_heat_dissipation(design, ctx)
deflection_result = calc.check_tool_deflection(design, ctx)
rim_speed_result = calc.check_rim_speed(design, ctx)
geometry_result = calc.check_geometry_complexity(design, ctx)

# BOM generation
bom = calc.compute_bom(design, ctx)  # Returns RmosBomResult
```

### **Calculator Return Structure**
```python
{
  "score": 85.0,           # 0-100 feasibility score
  "warning": "Optional warning message",
  "chipload_mm": 0.0333,   # Calculator-specific metadata
  "heat_index": 4.5,
  "deflection_mm": 0.0012,
  "rim_speed_m_per_min": 56.5,
  "complexity_index": 4.5
}
```

---

## 🛤️ Toolpath Service Details

### **ToolpathService.generate_toolpaths()**

**Process:**
1. Get geometry engine based on context flag
2. Generate rosette path geometry (concentric rings)
3. Convert to toolpath operations:
   - Rapid to safe Z (5mm)
   - Rapid to ring start
   - Plunge to cut depth (-1.5mm default)
   - Cut around ring (G1 moves)
   - Retract to safe Z
4. Accumulate path length
5. Estimate machining time (rapid/cut/plunge feed rates)
6. Apply 10% overhead for accel/decel

**Feed Rates:**
- Rapid: 5000 mm/min
- Cutting: 1200 mm/min
- Plunge: 300 mm/min

---

## 🧩 Type Definitions

### **RmosContext**
```python
class RmosContext(BaseModel):
    material_id: Optional[str] = None
    tool_id: Optional[str] = None
    machine_profile_id: Optional[str] = None
    use_shapely_geometry: bool = True  # Strategy selector
```

### **RmosFeasibilityResult**
```python
class RmosFeasibilityResult(BaseModel):
    score: float  # 0-100
    risk_bucket: RiskBucket  # GREEN/YELLOW/RED
    warnings: List[str]
    efficiency: Optional[float]
    estimated_cut_time_seconds: Optional[float]
    calculator_results: Dict[str, Any]
```

### **RmosBomResult**
```python
class RmosBomResult(BaseModel):
    material_required_mm2: float
    tool_ids: List[str]
    estimated_waste_percent: float
    notes: List[str]
```

### **RmosToolpathPlan**
```python
class RmosToolpathPlan(BaseModel):
    toolpaths: List[Dict[str, Any]]  # G-code operations
    total_length_mm: float
    estimated_time_seconds: float
    warnings: List[str]
```

---

## 🧪 Testing (Not Yet Executed)

### **Manual Test Script**
Create `test_rmos_2_0.ps1`:

```powershell
# Start server
cd "C:\Users\thepr\Downloads\Luthiers ToolBox"
cd services/api
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000

# In another terminal:
$body = @{
  design = @{
    outer_diameter_mm = 100.0
    inner_diameter_mm = 20.0
    ring_count = 3
    pattern_type = "herringbone"
  }
  context = @{
    use_shapely_geometry = $true
  }
} | ConvertTo-Json -Depth 10

# Test feasibility
Invoke-RestMethod -Uri "http://localhost:8000/api/rmos/feasibility" `
  -Method POST -Body $body -ContentType "application/json"

# Test BOM
Invoke-RestMethod -Uri "http://localhost:8000/api/rmos/bom" `
  -Method POST -Body $body -ContentType "application/json"

# Test toolpaths
Invoke-RestMethod -Uri "http://localhost:8000/api/rmos/toolpaths" `
  -Method POST -Body $body -ContentType "application/json"

# Test health
Invoke-RestMethod -Uri "http://localhost:8000/api/rmos/health"
```

### **Expected Health Check**
```json
{
  "status": "ok",
  "module": "RMOS 2.0",
  "version": "2.0.0",
  "endpoints": ["/feasibility", "/bom", "/toolpaths"]
}
```

---

## 🚨 Known Issues

### **1. RosetteParamSpec Import**
Currently using fallback stub in `api_contracts.py`:
```python
try:
    from ..art_studio.schemas import RosetteParamSpec
except ImportError:
    class RosetteParamSpec(BaseModel):  # Stub
        outer_diameter_mm: float = 100.0
        inner_diameter_mm: float = 20.0
        ring_count: int = 3
        pattern_type: str = "herringbone"
```

**Resolution:** Verify actual path to art_studio.schemas or create proper schema file.

### **2. Calculator Placeholders**
All 5 calculators use simplified heuristics:
- Real implementations need material/tool database integration
- Chipload calculation needs actual spindle/feed parameters
- Heat dissipation needs thermal modeling
- Deflection calculation needs tool stiffness data
- Rim speed needs material-specific safe ranges

### **3. Geometry Engine Stub**
MLGeometryEngine delegates to Shapely:
```python
class MLGeometryEngine(GeometryEngine):
    def __init__(self):
        self._fallback = ShapelyGeometryEngine()
```

**Future:** Load actual ML model for path prediction.

---

## 📋 Integration Checklist

- [x] Create RMOS 2.0 directory structure
- [x] Implement api_contracts.py (factory pattern)
- [x] Implement feasibility_scorer.py (weighted aggregation)
- [x] Implement calculators/service.py (5 calculators + BOM)
- [x] Implement toolpath/geometry_engine.py (strategy pattern)
- [x] Implement toolpath/service.py (toolpath planning)
- [x] Implement api_routes.py (3 FastAPI endpoints)
- [x] Create __init__.py facade
- [x] Wire router into main.py
- [ ] Test /api/rmos/health endpoint
- [ ] Test /api/rmos/feasibility with sample design
- [ ] Test /api/rmos/bom with sample design
- [ ] Test /api/rmos/toolpaths with sample design
- [ ] Validate RosetteParamSpec import path
- [ ] Replace calculator placeholders with real logic
- [ ] Integrate material/tool databases
- [ ] Add ML geometry engine implementation
- [ ] Create CI smoke tests
- [ ] Document directional workflows (Design-First, Constraint-First, AI-Assisted)
- [ ] Commit to feature branch
- [ ] Merge to main after validation

---

## 🎯 Next Steps (When Ready)

1. **Manual Validation:**
   ```powershell
   cd services/api
   .\.venv\Scripts\Activate.ps1
   uvicorn app.main:app --reload --port 8000
   # Test endpoints with Postman or curl
   ```

2. **Fix Import Path:**
   - Search for actual RosetteParamSpec location
   - Update imports in api_contracts.py, feasibility_scorer.py, etc.

3. **Database Integration:**
   - Wire calculators to material/tool databases
   - Replace hardcoded values (spindle RPM, feed rates) with profile lookups

4. **Create Smoke Tests:**
   - `test_rmos_feasibility.ps1`
   - `test_rmos_bom.ps1`
   - `test_rmos_toolpaths.ps1`

5. **Commit Changes:**
   ```powershell
   git add services/api/app/rmos/
   git add services/api/app/calculators/service.py
   git add services/api/app/toolpath/
   git add services/api/app/main.py
   git commit -m "RMOS 2.0: Implement feasibility/BOM/toolpath skeleton"
   ```

---

## 📚 References

- **Architecture Docs:** `docs/RMOS/RMOS_2_0_Spec.md`
- **Directional Workflows:** `docs/RMOS/Directional_Workflow_2_0.md`
- **Developer Onboarding:** `docs/RMOS/RMOS_Developer_Onboarding.md`
- **Adaptive Pocketing:** `ADAPTIVE_POCKETING_MODULE_L.md` (for CAM integration)
- **Machine Profiles:** `MACHINE_PROFILES_MODULE_M.md` (for feed rate overrides)

---

**Status:** ✅ Skeleton Complete | ⏸️ Testing Deferred  
**Branch:** `feature/rmos-2-0-skeleton`  
**Files Modified:** 8 new files, 1 file updated (main.py)
