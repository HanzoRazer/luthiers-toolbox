# Phase 2 Quick Reference

**Status:** ✅ Operational  
**Version:** 2.0  
**Last Updated:** November 8, 2025

---

## 🚀 Quick Start

### Test Phase 2 (No API key needed)
```powershell
cd "C:\Users\thepr\Downloads\Luthiers ToolBox"
python test_blueprint_phase2.py
```

### Expected Output
```
✓ Phase 2 vectorizer loaded successfully
✓ opencv-python 4.12.0
✓ ezdxf 1.4.2
✓ Edge detection: working
✓ Contour extraction: working
✓ DXF R2000 export: working
```

---

## 📡 API Endpoints

### `/blueprint/vectorize-geometry` (POST)
**Upload blueprint image → Get DXF + SVG**

**Parameters:**
- `file`: Image file (PNG/JPG)
- `analysis_data`: JSON string from `/blueprint/analyze`
- `scale_factor`: Float (default 1.0)

**Example (TestClient):**
```python
import json
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

with open("blueprint.png", "rb") as f:
    response = client.post(
        "/blueprint/vectorize-geometry",
        files={"file": ("blueprint.png", f, "image/png")},
        data={
            "analysis_data": json.dumps({}),
            "scale_factor": 1.0
        }
    )

result = response.json()
print(f"DXF: {result['dxf_path']}")
print(f"Contours: {result['contours_detected']}")
```

---

## 🎛️ Parameter Tuning

### Clean Blueprints
```python
low_threshold = 50
high_threshold = 150
min_area = 100.0
```

### Noisy Scans
```python
low_threshold = 70
high_threshold = 180
min_area = 200.0
```

### Hand-Drawn Sketches
```python
low_threshold = 30
high_threshold = 120
min_area = 50.0
```

---

## 🔧 Troubleshooting

### "Phase 2 not available"
```powershell
pip install opencv-python scikit-image ezdxf
```

### "Geometry flipped vertically"
- In CAM software: Use "Mirror Y" or "Flip Vertical"
- Or add `flip_y=True` parameter (coming in Phase 2.5)

### "Too many contours detected"
- Increase `min_area` to filter small contours
- Increase `epsilon_factor` to simplify contours

### "Not enough detail"
- Decrease `min_area` to capture smaller features
- Decrease `epsilon_factor` for more points per contour
- Lower `low_threshold` in edge detection

---

## 📁 Output Files

### SVG (geometry.svg)
- Blue contours (detected shapes)
- Red lines (straight segments)
- Green dimension annotations

### DXF (geometry.dxf)
- **GEOMETRY layer** (Green): Closed contours
- **LINES layer** (Red): Line segments
- **DIMENSIONS layer** (Yellow): Text annotations

**CAM Import:**
- Fusion 360: File → Insert → Insert DXF
- VCarve: File → Import → Import Vectors
- Mach4: File → Load DXF

---

## 📊 Algorithm Steps

1. **Preprocess** → Grayscale + Blur + CLAHE
2. **Detect Edges** → Canny (50, 150) + Dilate
3. **Extract Contours** → FindContours + Filter + Simplify
4. **Detect Lines** → Hough Transform
5. **Convert Coords** → Pixels → mm (300 DPI)
6. **Apply Scale** → Multiply by scale_factor
7. **Export** → SVG + DXF R2000

---

## ✅ Quick Validation

```powershell
# Test everything
python test_blueprint_phase2.py

# Should see:
# ✓ Phase 2 vectorizer loaded
# ✓ Edge detection: 1204 pixels
# ✓ Contour extraction: 2 contours
# ✓ DXF R2000 created
```

---

## 🎯 Next Steps

1. Get sample guitar blueprint (PNG/JPG)
2. Run `/blueprint/analyze` to get dimensions
3. Run `/blueprint/vectorize-geometry` to get DXF
4. Import DXF into Fusion 360/VCarve
5. Measure accuracy vs actual guitar dimensions

---

**For full details:** See `BLUEPRINT_IMPORT_PHASE2_COMPLETE.md`
