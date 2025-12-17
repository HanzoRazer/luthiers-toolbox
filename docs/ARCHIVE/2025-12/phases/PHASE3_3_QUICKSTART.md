# Phase 3.3 Quick Start Guide

**Goal:** Implement advanced DXF validation features in 4 weeks

---

## 📋 Implementation Checklist

### **Week 1: Self-Intersection Detection** ⏱️ 5 days

**Day 1-2: Core Topology Validator**
- [ ] Install dependencies: `pip install shapely scipy`
- [ ] Create `services/api/app/cam/dxf_advanced_validation.py`
- [ ] Implement `TopologyValidator` class
- [ ] Add `check_self_intersections()` method using Shapely `is_valid()`
- [ ] Add `explain_validity()` error descriptions
- [ ] Add `buffer(0)` repair suggestions

**Day 3: API Endpoint**
- [ ] Add `POST /cam/blueprint/validate-topology` to `blueprint_cam_bridge.py`
- [ ] Accept DXF file upload
- [ ] Return `TopologyIssue` list with severity, location, repair suggestions
- [ ] Test with figure-8 DXF (self-intersecting path)

**Day 4: Unit Tests**
- [ ] Create `test_topology_validation.py`
- [ ] Test valid polygon (no errors)
- [ ] Test self-intersecting polygon (ERROR severity)
- [ ] Test degenerate polygon (zero area)
- [ ] Test buffer(0) repair suggestion

**Day 5: Integration**
- [ ] Add topology validation to preflight workflow
- [ ] Update `PreflightReport` model to include topology issues
- [ ] Test with Gibson L-00 DXF

---

### **Week 2: Accuracy & Volume** ⏱️ 5 days

**Day 1-2: Accuracy Validator**
- [ ] Create `AccuracyValidator` class in `dxf_advanced_validation.py`
- [ ] Extract vertices from original DXF
- [ ] Extract vertices from reconstructed contours
- [ ] Calculate Hausdorff distance using `scipy.spatial.distance.cdist()`
- [ ] Compute max_error, mean_error, rms_error
- [ ] Flag vertices with deviation > 0.1mm

**Day 3-4: Volume Calculator**
- [ ] Create `services/api/app/cam/volume_calculator.py`
- [ ] Implement `VolumeCalculator` class
- [ ] Create Shapely polygons from loops
- [ ] Subtract islands using `polygon.difference(island)`
- [ ] Calculate area × depth = volume
- [ ] Add wood density estimates (spruce, mahogany, maple, rosewood)
- [ ] Add `POST /cam/blueprint/calculate-volume` endpoint

**Day 5: Tests & Integration**
- [ ] Create `test_accuracy_volume.py`
- [ ] Test accuracy with synthetic deviation data
- [ ] Test volume with pocket + island
- [ ] Test weight estimates for different woods
- [ ] Add endpoints to `blueprint_cam_bridge.py`

---

### **Week 3: Classification & Performance** ⏱️ 5 days

**Day 1-3: Contour Classifier**
- [ ] Create `services/api/app/cam/contour_classifier.py`
- [ ] Implement `ContourClassifier` class
- [ ] Add classification heuristics:
  - Body: area > 100,000 mm², circularity < 0.7, aspect 1.2-1.4
  - Soundhole: circular, diameter 80-100mm
  - Bracing: area < 5,000 mm², rectangular
  - Binding: thin channels near perimeter
  - Neck pocket: rectangular, upper bout
- [ ] Calculate confidence scores
- [ ] Add `POST /cam/blueprint/classify-contours` endpoint
- [ ] Test with Gibson L-00 DXF (expect body + soundhole + bracing)

**Day 4: Performance Optimization**
- [ ] Add streaming DXF parser using `ezdxf.addons.streaming`
- [ ] Implement progress callback for large files (>10MB)
- [ ] Add result caching with SHA256 hash keys
- [ ] Test with 15MB DXF file

**Day 5: Comprehensive Testing**
- [ ] Create `test_advanced_validation.ps1` (PowerShell)
- [ ] Test all 5 features with real DXF files
- [ ] Measure performance (time, memory)
- [ ] Document edge cases

---

### **Week 4: UI & Documentation** ⏱️ 5 days

**Day 1-2: PipelineLab UI Updates**
- [ ] Add "Advanced Validation" panel to `PipelineLab.vue`
- [ ] Add topology status card with error list
- [ ] Add accuracy metrics display (max/mean/RMS error)
- [ ] Add deviation heatmap canvas
- [ ] Add volume estimates card
- [ ] Add component classification grid with badges

**Day 3: Visualization**
- [ ] Highlight topology errors on canvas (red circles at intersection points)
- [ ] Draw deviation heatmap (color-coded by error magnitude)
- [ ] Add component type badges to contour overlay
- [ ] Implement "Show" button to zoom to problem areas

**Day 4-5: Documentation & CI/CD**
- [ ] Create `PHASE3_3_ADVANCED_VALIDATION_COMPLETE.md`
- [ ] Update API documentation with new endpoints
- [ ] Add CI/CD workflow: `.github/workflows/advanced_validation.yml`
- [ ] Test all features end-to-end
- [ ] Create video demo

---

## 🚀 Quick Commands

### **Setup**
```powershell
# Install dependencies
cd services/api
.\.venv\Scripts\Activate.ps1
pip install shapely scipy
pip freeze > requirements.txt

# Create new files
New-Item -Path "app/cam/dxf_advanced_validation.py" -ItemType File
New-Item -Path "app/cam/volume_calculator.py" -ItemType File
New-Item -Path "app/cam/contour_classifier.py" -ItemType File
```

### **Test Topology Validation**
```powershell
# Start server
python -m uvicorn app.main:app --reload --port 8000

# Test endpoint (separate terminal)
$form = @{
    file = Get-Item "test_figure8.dxf"
}
Invoke-RestMethod -Uri "http://localhost:8000/cam/blueprint/validate-topology" `
    -Method Post -Form $form
```

### **Test Volume Calculator**
```powershell
$body = @{
    outer_loop = @(@(0,0), @(100,0), @(100,60), @(0,60))
    islands = @(@(@(30,20), @(70,20), @(70,40), @(30,40)))
    depth_mm = 3.0
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/cam/blueprint/calculate-volume" `
    -Method Post -Body $body -ContentType "application/json"
```

### **Test Classification**
```powershell
$form = @{
    file = Get-Item "Gibson_L00_Spec.dxf"
}
$result = Invoke-RestMethod -Uri "http://localhost:8000/cam/blueprint/classify-contours" `
    -Method Post -Form $form

# Expected: BODY, SOUNDHOLE, BRACING types
$result.summary
```

---

## 📊 Progress Tracking

| Feature | Status | Lines | Tests | Docs |
|---------|--------|-------|-------|------|
| Self-Intersection Detection | ⏸️ Not Started | 0/200 | 0/4 | ❌ |
| Dimension Accuracy | ⏸️ Not Started | 0/150 | 0/3 | ❌ |
| Volume Calculator | ⏸️ Not Started | 0/200 | 0/4 | ❌ |
| Contour Classifier | ⏸️ Not Started | 0/300 | 0/5 | ❌ |
| Performance Optimization | ⏸️ Not Started | 0/150 | 0/2 | ❌ |
| PipelineLab UI | ⏸️ Not Started | 0/300 | Manual | ❌ |
| Documentation | ✅ Planning | 0/800 | N/A | ✅ |

**Total Phase 3.3:** 0/1,300 lines

---

## 🎯 Milestones

- **Week 1 End:** ✅ Topology validation working
- **Week 2 End:** ✅ Accuracy + volume endpoints live
- **Week 3 End:** ✅ Classification + performance tested
- **Week 4 End:** ✅ UI complete, documented, CI/CD added

---

## 🔗 Key Files to Create

```
services/api/app/cam/
├── dxf_advanced_validation.py  # Week 1-2
├── volume_calculator.py        # Week 2
└── contour_classifier.py       # Week 3

services/api/app/routers/
└── blueprint_cam_bridge.py     # Update with 5 new endpoints

packages/client/src/views/
└── PipelineLab.vue            # Add advanced validation panel

.github/workflows/
└── advanced_validation.yml    # CI/CD tests

Root directory/
├── test_advanced_validation.ps1       # Week 3
├── PHASE3_3_ADVANCED_VALIDATION_COMPLETE.md  # Week 4
└── PHASE3_3_QUICKSTART.md             # ✅ This file
```

---

## 💡 Tips

**Shapely Quick Reference:**
```python
from shapely.geometry import Polygon
from shapely.validation import explain_validity

poly = Polygon([(0,0), (10,0), (10,10), (5,5), (0,10)])

# Check validity
if not poly.is_valid:
    print(explain_validity(poly))  # "Ring Self-intersection[5.0, 5.0]"
    
    # Try auto-repair
    fixed = poly.buffer(0)
    if fixed.is_valid:
        print("✅ Repaired")
```

**Volume Calculation:**
```python
from shapely.geometry import Polygon

outer = Polygon([(0,0), (100,0), (100,60), (0,60)])
island = Polygon([(30,20), (70,20), (70,40), (30,40)])

pocket_area = outer.difference(island)
volume_mm3 = pocket_area.area * 3.0  # 3mm depth
volume_cm3 = volume_mm3 / 1000.0
```

**Classification Heuristics:**
```python
circularity = (4 * math.pi * area) / (perimeter ** 2)
aspect_ratio = width / height

if circularity > 0.85:
    return "SOUNDHOLE"  # circular
elif area > 100000:
    return "BODY"       # largest
elif area < 5000 and aspect_ratio > 2:
    return "BRACING"    # small rectangular
```

---

## 📚 References

- [Shapely Documentation](https://shapely.readthedocs.io/)
- [SciPy Spatial Distance](https://docs.scipy.org/doc/scipy/reference/spatial.distance.html)
- [Phase 3.3 Full Plan](./PHASE3_3_ADVANCED_VALIDATION_PLAN.md)
- [Phase 3.2 Complete](./PHASE3_2_DXF_PREFLIGHT_COMPLETE.md)

---

**Next Step:** Start Week 1 - Self-Intersection Detection 🚀
