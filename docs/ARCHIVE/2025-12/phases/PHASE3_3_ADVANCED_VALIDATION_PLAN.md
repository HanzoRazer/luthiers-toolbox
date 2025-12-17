# Phase 3.3: Advanced DXF Validation Features

**Status:** Planning → Implementation  
**Date:** November 8, 2025  
**Builds On:** Phase 3.2 (DXF Preflight + Contour Reconstruction)

---

## 🎯 Overview

Phase 3.3 adds **advanced geometric validation** capabilities to the DXF preflight system, focusing on:

1. **Self-Intersection Detection** - Topology validation using Shapely
2. **Dimension Accuracy Validation** - Reconstruction deviation analysis
3. **Material Removal Volume** - Pocket volume calculations
4. **Multi-Contour Classification** - Guitar component detection
5. **Performance Optimization** - Large file handling (>10MB)

**Key Technologies:**
- **Shapely 2.1+** - Polygon operations (`is_valid`, `buffer`, `unary_union`)
- **NumPy** - Fast geometric calculations
- **ezdxf** - DXF entity extraction
- **SciPy** (optional) - Advanced curve fitting for accuracy metrics

---

## 📦 Architecture

### **Backend Enhancements**

```
services/api/app/cam/
├── dxf_preflight.py               # Existing (600 lines)
├── dxf_advanced_validation.py     # NEW - Phase 3.3 validators (400 lines)
├── contour_reconstructor.py       # Existing (500 lines)
├── volume_calculator.py           # NEW - Material removal (200 lines)
└── contour_classifier.py          # NEW - Guitar component detection (300 lines)

services/api/app/routers/
└── blueprint_cam_bridge.py        # Update with Phase 3.3 endpoints
```

### **New Endpoints**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/cam/blueprint/validate-topology` | POST | Self-intersection detection |
| `/cam/blueprint/validate-accuracy` | POST | Dimension deviation analysis |
| `/cam/blueprint/calculate-volume` | POST | Pocket volume estimation |
| `/cam/blueprint/classify-contours` | POST | Guitar component detection |
| `/cam/blueprint/validate-advanced` | POST | All-in-one advanced validation |

---

## 🔬 Feature 1: Self-Intersection Detection

### **Goal**
Detect and visualize topology errors:
- Crossing contours (figure-8 paths)
- Overlapping segments
- Self-touching vertices
- Degenerate polygons

### **Implementation**

**File:** `services/api/app/cam/dxf_advanced_validation.py`

```python
from shapely.geometry import Polygon, LineString
from shapely.validation import explain_validity

class TopologyValidator:
    """Validate geometric topology using Shapely"""
    
    def __init__(self, dxf_bytes: bytes):
        self.doc = ezdxf.readfile(io.BytesIO(dxf_bytes))
        self.issues = []
    
    def check_self_intersections(self) -> List[TopologyIssue]:
        """Detect self-intersecting paths"""
        for entity in self.doc.modelspace().query('LWPOLYLINE'):
            points = [(p[0], p[1]) for p in entity.get_points('xy')]
            
            # Create Shapely polygon
            try:
                poly = Polygon(points)
                
                # Check validity
                if not poly.is_valid:
                    reason = explain_validity(poly)
                    self.issues.append(TopologyIssue(
                        severity=Severity.ERROR,
                        message=f"Self-intersecting polygon on layer '{entity.dxf.layer}'",
                        category="topology",
                        layer=entity.dxf.layer,
                        entity_handle=entity.dxf.handle,
                        topology_error=reason,
                        repair_suggestion=self._suggest_repair(poly)
                    ))
            except Exception as e:
                self.issues.append(TopologyIssue(
                    severity=Severity.ERROR,
                    message=f"Invalid geometry: {str(e)}",
                    category="topology"
                ))
        
        return self.issues
    
    def _suggest_repair(self, poly: Polygon) -> str:
        """Generate repair suggestion for invalid polygon"""
        try:
            # Try buffer(0) repair
            fixed = poly.buffer(0)
            if fixed.is_valid:
                return "Use buffer(0) to auto-repair (removes self-intersections)"
            else:
                return "Manual repair required in CAD software"
        except:
            return "Manual repair required in CAD software"
```

**Validation Checks:**
- ✅ Shapely `is_valid()` - General topology validation
- ✅ `explain_validity()` - Human-readable error descriptions
- ✅ `buffer(0)` - Auto-repair suggestion for simple cases
- ✅ Crossing detection - Find intersection points
- ✅ Degenerate polygon detection - Zero-area or collapsed paths

**Output Example:**
```json
{
  "topology_valid": false,
  "issues": [
    {
      "severity": "ERROR",
      "category": "topology",
      "message": "Self-intersecting polygon on layer 'CONTOURS'",
      "topology_error": "Ring Self-intersection[50.0, 30.0]",
      "intersection_point": [50.0, 30.0],
      "repair_suggestion": "Use buffer(0) to auto-repair",
      "entity_handle": "A3F"
    }
  ]
}
```

---

## 📏 Feature 2: Dimension Accuracy Validation

### **Goal**
Compare reconstructed contours against original DXF geometry to detect:
- Reconstruction errors (±0.1mm tolerance)
- Scale inconsistencies
- Missing segments
- Vertex drift

### **Implementation**

**File:** `services/api/app/cam/dxf_advanced_validation.py`

```python
import numpy as np
from scipy.spatial.distance import cdist

class AccuracyValidator:
    """Compare reconstructed geometry vs original DXF"""
    
    def __init__(self, original_dxf: bytes, reconstructed_contours: List[Dict]):
        self.original = ezdxf.readfile(io.BytesIO(original_dxf))
        self.reconstructed = reconstructed_contours
        self.tolerance_mm = 0.1  # Guitar lutherie precision
    
    def validate_accuracy(self) -> AccuracyReport:
        """Calculate deviation metrics"""
        # Extract original vertices
        original_vertices = self._extract_vertices(self.original)
        
        # Extract reconstructed vertices
        reconstructed_vertices = []
        for contour in self.reconstructed:
            for point in contour["points"]:
                reconstructed_vertices.append([point["x"], point["y"]])
        
        # Calculate pairwise distances (Hausdorff distance)
        distances = cdist(original_vertices, reconstructed_vertices)
        
        # Metrics
        max_error = np.max(np.min(distances, axis=1))
        mean_error = np.mean(np.min(distances, axis=1))
        rms_error = np.sqrt(np.mean(np.min(distances, axis=1)**2))
        
        # Identify problem areas
        problem_vertices = []
        for i, vertex in enumerate(original_vertices):
            min_dist = np.min(distances[i])
            if min_dist > self.tolerance_mm:
                problem_vertices.append({
                    "original": vertex.tolist(),
                    "deviation_mm": float(min_dist),
                    "severity": "ERROR" if min_dist > 0.5 else "WARNING"
                })
        
        return AccuracyReport(
            max_error_mm=float(max_error),
            mean_error_mm=float(mean_error),
            rms_error_mm=float(rms_error),
            tolerance_mm=self.tolerance_mm,
            passed=max_error <= self.tolerance_mm,
            problem_vertices=problem_vertices,
            vertex_count_original=len(original_vertices),
            vertex_count_reconstructed=len(reconstructed_vertices)
        )
```

**Validation Metrics:**
- **Max Error** - Largest deviation (flag if > 0.1mm)
- **RMS Error** - Root-mean-square deviation
- **Mean Error** - Average deviation
- **Hausdorff Distance** - Worst-case vertex matching

**Output Example:**
```json
{
  "accuracy_passed": false,
  "max_error_mm": 0.237,
  "mean_error_mm": 0.042,
  "rms_error_mm": 0.089,
  "tolerance_mm": 0.1,
  "problem_vertices": [
    {
      "original": [50.5, 30.2],
      "deviation_mm": 0.237,
      "severity": "ERROR"
    }
  ],
  "vertex_count": {
    "original": 148,
    "reconstructed": 142
  }
}
```

---

## 🧊 Feature 3: Material Removal Volume Calculator

### **Goal**
Calculate pocket volumes for CAM planning:
- Single pocket volume (area × depth)
- Multi-loop pockets with islands
- Total material removal estimation
- Weight reduction calculations (with density)

### **Implementation**

**File:** `services/api/app/cam/volume_calculator.py`

```python
from shapely.geometry import Polygon
from shapely.ops import unary_union

class VolumeCalculator:
    """Calculate material removal volumes"""
    
    def calculate_pocket_volume(
        self,
        outer_loop: List[Tuple[float, float]],
        islands: List[List[Tuple[float, float]]],
        depth_mm: float
    ) -> VolumeReport:
        """
        Calculate volume for pocket with islands.
        
        Args:
            outer_loop: Boundary vertices [(x,y), ...]
            islands: List of island loops [[(x,y), ...], ...]
            depth_mm: Pocket depth (positive = material removed)
        
        Returns:
            VolumeReport with area, volume, weight estimates
        """
        # Create outer polygon
        outer_poly = Polygon(outer_loop)
        
        # Create island polygons
        island_polys = [Polygon(island) for island in islands]
        
        # Subtract islands from outer
        effective_area = outer_poly
        for island in island_polys:
            effective_area = effective_area.difference(island)
        
        # Calculate volume
        area_mm2 = effective_area.area
        volume_mm3 = area_mm2 * depth_mm
        volume_cm3 = volume_mm3 / 1000.0
        
        # Material weight estimates (common lutherie woods)
        densities = {
            "spruce": 0.42,     # g/cm³
            "mahogany": 0.56,
            "maple": 0.63,
            "rosewood": 0.85
        }
        
        weight_estimates = {
            wood: volume_cm3 * density
            for wood, density in densities.items()
        }
        
        return VolumeReport(
            area_mm2=float(area_mm2),
            depth_mm=depth_mm,
            volume_mm3=float(volume_mm3),
            volume_cm3=float(volume_cm3),
            weight_estimates_grams=weight_estimates,
            island_count=len(islands)
        )
```

**Use Cases:**
- ✅ Pocket planning (depth selection)
- ✅ Material cost estimation
- ✅ CNC cycle time prediction
- ✅ Weight reduction analysis (acoustic guitars)

**Output Example:**
```json
{
  "area_mm2": 15750.5,
  "depth_mm": 3.0,
  "volume_mm3": 47251.5,
  "volume_cm3": 47.25,
  "weight_estimates_grams": {
    "spruce": 19.85,
    "mahogany": 26.46,
    "maple": 29.77,
    "rosewood": 40.16
  },
  "island_count": 2
}
```

---

## 🎸 Feature 4: Multi-Contour Classification

### **Goal**
Automatically detect and classify guitar components:
- Body outline (largest closed contour)
- Soundhole (circular, centered, ~85mm diameter)
- Bracing pockets (rectangular, top plate area)
- Binding channels (parallel to body outline, offset ~3mm)
- Neck pocket (rectangular, upper bout)

### **Implementation**

**File:** `services/api/app/cam/contour_classifier.py`

```python
from shapely.geometry import Polygon, Point
import math

class ContourClassifier:
    """Classify DXF contours by guitar component type"""
    
    # OM-28 Standard Dimensions (reference)
    SOUNDHOLE_DIAMETER_MM = 88.9  # 3.5"
    SCALE_LENGTH_MM = 645.0       # 25.4"
    BODY_LENGTH_MM = 495.0        # ~19.5"
    BODY_WIDTH_MM = 394.0         # ~15.5"
    
    def classify_contour(self, contour: List[Tuple[float, float]]) -> ContourType:
        """
        Classify a single contour.
        
        Args:
            contour: Vertices [(x, y), ...]
        
        Returns:
            ContourType enum (BODY, SOUNDHOLE, BRACING, BINDING, NECK_POCKET, UNKNOWN)
        """
        poly = Polygon(contour)
        
        # Extract features
        area = poly.area
        perimeter = poly.length
        bbox = poly.bounds  # (minx, miny, maxx, maxy)
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        centroid = poly.centroid
        
        # Circularity (4π × area / perimeter²)
        circularity = (4 * math.pi * area) / (perimeter ** 2)
        
        # Classification heuristics
        
        # Body outline (largest, low circularity, guitar-shaped aspect ratio)
        if area > 100000 and circularity < 0.7 and 1.2 < width/height < 1.4:
            return ContourType.BODY
        
        # Soundhole (circular, ~88mm diameter, near center)
        if 0.85 < circularity < 1.0 and 80 < width < 100:
            return ContourType.SOUNDHOLE
        
        # Bracing pockets (small rectangles, low circularity)
        if area < 5000 and circularity < 0.7 and 2 < width/height < 8:
            return ContourType.BRACING
        
        # Binding channels (thin, parallel to body)
        if area < 1000 and height > 100 and width < 10:
            return ContourType.BINDING
        
        # Neck pocket (rectangular, upper bout)
        if area < 20000 and 0.7 < circularity < 0.9 and width > 40:
            return ContourType.NECK_POCKET
        
        return ContourType.UNKNOWN
    
    def classify_all(self, contours: List[List[Tuple]]) -> ClassificationReport:
        """Classify all contours and generate report"""
        classifications = []
        
        for i, contour in enumerate(contours):
            ctype = self.classify_contour(contour)
            poly = Polygon(contour)
            
            classifications.append({
                "index": i,
                "type": ctype.value,
                "confidence": self._calculate_confidence(contour, ctype),
                "area_mm2": float(poly.area),
                "bbox": poly.bounds,
                "vertex_count": len(contour)
            })
        
        return ClassificationReport(
            total_contours=len(contours),
            classifications=classifications,
            summary={
                ctype.value: sum(1 for c in classifications if c["type"] == ctype.value)
                for ctype in ContourType
            }
        )
```

**Classification Rules:**

| Component | Area (mm²) | Circularity | Aspect Ratio | Location |
|-----------|------------|-------------|--------------|----------|
| Body | >100,000 | <0.7 | 1.2-1.4 | N/A |
| Soundhole | 6,000-8,000 | 0.85-1.0 | 0.9-1.1 | Centered |
| Bracing | <5,000 | <0.7 | 2:1-8:1 | Top plate |
| Binding | <1,000 | <0.5 | >10:1 | Perimeter |
| Neck Pocket | <20,000 | 0.7-0.9 | 1.5-3.0 | Upper bout |

**Output Example:**
```json
{
  "total_contours": 15,
  "summary": {
    "BODY": 1,
    "SOUNDHOLE": 1,
    "BRACING": 7,
    "BINDING": 4,
    "NECK_POCKET": 1,
    "UNKNOWN": 1
  },
  "classifications": [
    {
      "index": 0,
      "type": "BODY",
      "confidence": 0.95,
      "area_mm2": 145760.3,
      "bbox": [0, 0, 394.0, 495.0],
      "vertex_count": 128
    },
    {
      "index": 1,
      "type": "SOUNDHOLE",
      "confidence": 0.98,
      "area_mm2": 6200.5,
      "bbox": [153.0, 320.0, 241.0, 408.0],
      "vertex_count": 64
    }
  ]
}
```

---

## ⚡ Feature 5: Performance Optimization

### **Goal**
Handle large DXF files (>10MB) efficiently:
- Streaming DXF parsing
- Async validation (non-blocking)
- Progress indicators (WebSocket)
- Result caching

### **Implementation**

**Streaming Parser:**
```python
from ezdxf.addons import streaming

async def validate_large_dxf(file_path: str, progress_callback):
    """Stream large DXF files"""
    with streaming.read(file_path) as stream:
        total_entities = stream.modelspace_count()
        processed = 0
        
        async for entity in stream.modelspace():
            # Validate entity
            validate_entity(entity)
            
            # Update progress
            processed += 1
            if processed % 100 == 0:
                await progress_callback(processed / total_entities)
```

**Caching:**
```python
import hashlib
from functools import lru_cache

def cache_validation_result(dxf_bytes: bytes) -> str:
    """Generate cache key from DXF hash"""
    return hashlib.sha256(dxf_bytes).hexdigest()

@lru_cache(maxsize=128)
def get_cached_validation(cache_key: str) -> Optional[PreflightReport]:
    """Retrieve cached validation result"""
    # Check Redis/SQLite cache
    return cache.get(cache_key)
```

---

## 🧪 Testing Strategy

### **Test Suite: `test_advanced_validation.ps1`**

```powershell
# Test 1: Self-Intersection Detection
$dxf_self_intersect = Create-FigureEightDXF
Test-Endpoint "/cam/blueprint/validate-topology" `
    -ExpectError "Self-intersecting polygon" `
    -ExpectRepairSuggestion "buffer(0)"

# Test 2: Dimension Accuracy
$original = Get-Item "Gibson_L00_Original.dxf"
$reconstructed = Invoke-API "/cam/blueprint/reconstruct-contours" -DXF $original
Test-Endpoint "/cam/blueprint/validate-accuracy" `
    -Original $original `
    -Reconstructed $reconstructed `
    -ExpectMaxError "<0.1mm"

# Test 3: Volume Calculation
$pocket = @{
    outer_loop = @(@(0,0), @(100,0), @(100,60), @(0,60))
    islands = @(@(@(30,20), @(70,20), @(70,40), @(30,40)))
    depth_mm = 3.0
}
Test-Endpoint "/cam/blueprint/calculate-volume" `
    -Pocket $pocket `
    -ExpectVolume "~16200 mm³"

# Test 4: Contour Classification
$gibson_l00 = Get-Item "Gibson_L00_Spec.dxf"
Test-Endpoint "/cam/blueprint/classify-contours" `
    -DXF $gibson_l00 `
    -ExpectTypes @("BODY", "SOUNDHOLE", "BRACING")
```

---

## 📊 Implementation Timeline

### **Week 1: Self-Intersection Detection**
- [ ] Day 1-2: Implement `TopologyValidator` class
- [ ] Day 3: Add Shapely validation hooks
- [ ] Day 4: Create repair suggestions
- [ ] Day 5: Write tests

### **Week 2: Accuracy & Volume**
- [ ] Day 1-2: Implement `AccuracyValidator`
- [ ] Day 3-4: Implement `VolumeCalculator`
- [ ] Day 5: Integration tests

### **Week 3: Classification & Performance**
- [ ] Day 1-3: Implement `ContourClassifier`
- [ ] Day 4: Add streaming parser
- [ ] Day 5: Caching system

### **Week 4: UI & Documentation**
- [ ] Day 1-2: Update PipelineLab.vue
- [ ] Day 3: Add visualization components
- [ ] Day 4-5: Documentation and CI/CD

---

## 🎨 UI Enhancements (PipelineLab.vue)

### **Advanced Validation Panel**

```vue
<template>
  <div class="advanced-validation">
    <!-- Topology Status -->
    <div class="validation-card">
      <h3>🔍 Topology Validation</h3>
      <div v-if="topology.valid" class="status-ok">
        ✅ No self-intersections detected
      </div>
      <div v-else class="status-error">
        ❌ {{ topology.issues.length }} topology errors found
        <ul>
          <li v-for="issue in topology.issues" :key="issue.handle">
            {{ issue.message }}
            <button @click="highlightEntity(issue.handle)">Show</button>
            <button @click="applyRepair(issue)">{{ issue.repair_suggestion }}</button>
          </li>
        </ul>
      </div>
    </div>
    
    <!-- Accuracy Metrics -->
    <div class="validation-card">
      <h3>📏 Dimension Accuracy</h3>
      <div class="accuracy-metrics">
        <div class="metric">
          <span>Max Error:</span>
          <span :class="accuracy.max_error_mm > 0.1 ? 'error' : 'ok'">
            {{ accuracy.max_error_mm.toFixed(3) }} mm
          </span>
        </div>
        <div class="metric">
          <span>RMS Error:</span>
          <span>{{ accuracy.rms_error_mm.toFixed(3) }} mm</span>
        </div>
        <!-- Deviation heatmap canvas -->
        <canvas ref="deviationCanvas" width="400" height="300"></canvas>
      </div>
    </div>
    
    <!-- Volume Estimates -->
    <div class="validation-card">
      <h3>🧊 Material Removal</h3>
      <div class="volume-info">
        <div>Area: {{ volume.area_mm2.toFixed(1) }} mm²</div>
        <div>Depth: {{ volume.depth_mm }} mm</div>
        <div>Volume: {{ volume.volume_cm3.toFixed(2) }} cm³</div>
        <div>Weight Removed (spruce): {{ volume.weight_estimates_grams.spruce.toFixed(1) }}g</div>
      </div>
    </div>
    
    <!-- Contour Classification -->
    <div class="validation-card">
      <h3>🎸 Component Detection</h3>
      <div class="classification-grid">
        <div v-for="cls in classification.classifications" :key="cls.index"
             class="component-badge"
             :class="cls.type.toLowerCase()">
          {{ cls.type }} ({{ (cls.confidence * 100).toFixed(0) }}%)
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const topology = ref({ valid: true, issues: [] })
const accuracy = ref({ max_error_mm: 0, rms_error_mm: 0 })
const volume = ref({ area_mm2: 0, depth_mm: 0, volume_cm3: 0, weight_estimates_grams: {} })
const classification = ref({ total_contours: 0, classifications: [] })

async function validateAdvanced(dxfFile: File) {
  // Call all validation endpoints
  const [topo, acc, vol, cls] = await Promise.all([
    validateTopology(dxfFile),
    validateAccuracy(dxfFile),
    calculateVolume(dxfFile),
    classifyContours(dxfFile)
  ])
  
  topology.value = topo
  accuracy.value = acc
  volume.value = vol
  classification.value = cls
}
</script>

<style scoped>
.validation-card {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 15px;
  margin: 10px 0;
}

.status-ok { color: #388e3c; }
.status-error { color: #d32f2f; }

.component-badge {
  display: inline-block;
  padding: 5px 10px;
  margin: 5px;
  border-radius: 4px;
  font-size: 0.85em;
}

.component-badge.body { background: #90caf9; }
.component-badge.soundhole { background: #ffb74d; }
.component-badge.bracing { background: #a5d6a7; }
</style>
```

---

## 📚 API Documentation Updates

### **New Models**

```python
from pydantic import BaseModel
from enum import Enum

class TopologyIssue(BaseModel):
    severity: str
    message: str
    category: str = "topology"
    layer: Optional[str]
    entity_handle: Optional[str]
    topology_error: str
    intersection_point: Optional[Tuple[float, float]]
    repair_suggestion: str

class AccuracyReport(BaseModel):
    max_error_mm: float
    mean_error_mm: float
    rms_error_mm: float
    tolerance_mm: float
    passed: bool
    problem_vertices: List[Dict]
    vertex_count_original: int
    vertex_count_reconstructed: int

class VolumeReport(BaseModel):
    area_mm2: float
    depth_mm: float
    volume_mm3: float
    volume_cm3: float
    weight_estimates_grams: Dict[str, float]
    island_count: int

class ContourType(str, Enum):
    BODY = "BODY"
    SOUNDHOLE = "SOUNDHOLE"
    BRACING = "BRACING"
    BINDING = "BINDING"
    NECK_POCKET = "NECK_POCKET"
    UNKNOWN = "UNKNOWN"

class ClassificationReport(BaseModel):
    total_contours: int
    classifications: List[Dict]
    summary: Dict[str, int]
```

---

## ✅ Success Criteria

### **Phase 3.3 Complete When:**
- [x] Self-intersection detection working with Shapely
- [x] Dimension accuracy validation calculating deviation metrics
- [x] Volume calculator supporting islands
- [x] Contour classifier identifying 5+ guitar components
- [x] Performance optimization handling 10MB+ DXF files
- [x] PipelineLab UI showing advanced validation results
- [x] Test suite passing all validation scenarios
- [x] Documentation complete with examples
- [x] CI/CD testing advanced features

---

## 🚀 Getting Started

### **1. Install New Dependencies**

```powershell
cd services/api
.\.venv\Scripts\Activate.ps1
pip install shapely scipy
pip freeze > requirements.txt
```

### **2. Create Validation Modules**

```powershell
# Create new files
New-Item -Path "app/cam/dxf_advanced_validation.py" -ItemType File
New-Item -Path "app/cam/volume_calculator.py" -ItemType File
New-Item -Path "app/cam/contour_classifier.py" -ItemType File
```

### **3. Update Router**

Add endpoints to `blueprint_cam_bridge.py`:
```python
@router.post("/validate-topology")
async def validate_topology(file: UploadFile):
    """Detect self-intersections"""
    # Implementation
    
@router.post("/validate-accuracy")
async def validate_accuracy(...):
    """Compare reconstructed vs original"""
    # Implementation
```

### **4. Test Locally**

```powershell
# Start server
uvicorn app.main:app --reload --port 8000

# Run tests
.\test_advanced_validation.ps1
```

---

## 📖 Related Documentation

- [Phase 3.2: DXF Preflight Complete](./PHASE3_2_DXF_PREFLIGHT_COMPLETE.md)
- [Phase 3.1: Contour Reconstruction](./PHASE3_1_CONTOUR_RECONSTRUCTION_COMPLETE.md)
- [Adaptive Pocketing Module L](./ADAPTIVE_POCKETING_MODULE_L.md)
- [Shapely Documentation](https://shapely.readthedocs.io/)

---

**Status:** 📝 Planning Complete → Ready for Implementation  
**Estimated Effort:** 3-4 weeks  
**Priority:** High (Core CAM validation)  
**Dependencies:** Phase 3.2 (DXF Preflight) ✅ Complete
