# Wave 17: Instrument Geometry Integration - TODO & Follow-up Tasks

**Date Created:** December 8, 2025  
**Status:** ✅ Wave 17 Complete | 🟩 Phase B Complete (Wave 17→18)  
**Current Phase:** Phase B (RmosContext) Delivered — Ready for Phase C

---

## 🟩 Phase B: RmosContext System (Wave 17→18) — COMPLETE

### Delivered Components
- [x] `rmos/context.py` — Authoritative `RmosContext` dataclass (532 lines)
  - Core dataclasses: `RmosContext`, `MaterialProfile`, `SafetyConstraints`, `CutOperation`, `ToolpathData`
  - Enums: `CutType`, `WoodSpecies` (11 species with density/hardness data)
  - Factory methods: `from_model_id()`, `from_dict()`
  - Serialization: `to_dict()`, `validate()`
  
- [x] `rmos/context_adapter.py` — Context transformation layer (329 lines)
  - `build_rmos_context_for_model()` — Main entry point
  - Material database helpers (11 wood species with physical properties)
  - Default cut generation (5 typical operations: saw, route, drill)
  - Context summary and export utilities
  
- [x] `rmos/context_router.py` — FastAPI endpoints (262 lines)
  - `GET /api/rmos/models` — List available instrument models
  - `GET /api/rmos/context/{model_id}` — Retrieve context for model
  - `POST /api/rmos/context` — Create custom context
  - `POST /api/rmos/context/validate` — Validate context payload
  - `GET /api/rmos/context/{model_id}/summary` — Quick summary endpoint
  
- [x] `main.py` — Router registration with graceful degradation
- [x] `test_phase_b_context.ps1` — Comprehensive test script (150 lines)

### Key Features
✅ **11 Wood Species Database:**
- Maple, Mahogany, Rosewood, Ebony, Spruce, Cedar, Walnut, Ash, Alder, Koa, Basswood
- Each with density (kg/m³) and Janka hardness (N)

✅ **Type-Safe Context Passing:**
- Dataclass-based (no dict guessing)
- Validation at boundaries
- Round-trip serialization (to_dict → from_dict)

✅ **Cross-Module Integration:**
- Instrument Geometry → RmosContext
- RmosContext → Feasibility Scoring (Phase D)
- RmosContext → Constraint Optimization (future)

### Test Coverage
```powershell
# Run Phase B tests:
.\test_phase_b_context.ps1

# Expected output:
# ✓ RmosContext import successful
# ✓ Factory (from_model_id) works
# ✓ Context adapter builds contexts
# ✓ Serialization round-trip validated
# ✓ FastAPI endpoints operational (if server running)
```

### Documentation Reference
- See: [WAVE17_18_INTEGRATION_AUTHORITY.md](./WAVE17_18_INTEGRATION_AUTHORITY.md) — Authoritative integration decisions
- Phase B completion unblocks: Phase C (Fretboard Geometry), Phase D (Feasibility), Phase E (CAM Preview)

---

## ✅ Completed Tasks

### Phase 1: Neck Taper Suite
- [x] Add `StringSpec` and `ScaleProfile` dataclasses to `models.py`
- [x] Create `neck_taper/taper_math.py` (mathematical engine)
- [x] Create `neck_taper/neck_outline_generator.py` (polyline generation)
- [x] Create `neck_taper/dxf_exporter.py` (R12 DXF export)
- [x] Create `neck_taper/api_router.py` (2 POST endpoints)
- [x] Create `neck_taper/__init__.py` (package exports)

### Phase 2: DXF Registry & Assets
- [x] Create `dxf_registry.py` (central asset registry with 4 presets)
- [x] Create `dxf_loader.py` (asset resolution and loading)
- [x] Create `assets/instrument_templates/` directory structure (strat/, lp/, acoustic/)

### Phase 3: GuitarModelSpec Layer
- [x] Create `model_spec.py` with complete specification system
- [x] Implement `STANDARD_SCALE_PROFILES` dict (6 profiles)
- [x] Create `NeckTaperSpec`, `StringSpacingSpec`, `GuitarModelSpec` dataclasses
- [x] Add `STRAT_25_5_MODEL` and `LP_24_75_MODEL` preset instances
- [x] Implement `guitar_model_to_instrument_spec()` factory function

### Phase 4: Integration & Documentation
- [x] Register `neck_taper_router` in `main.py`
- [x] Create `Neck_Taper_Theory.md` (16KB - mathematical foundations & CNC workflows)
- [x] Create `Neck_Taper_DXF_Export.md` (15KB - technical DXF format guide)
- [x] Create `Instrument_DXF_Mapping.md` (14KB - asset registry guide)

---

## 🔥 Critical Follow-up Tasks

### 1. Add Real DXF Template Files
**Priority:** HIGH  
**Reason:** Current registry has placeholder paths; physical files don't exist yet

**Tasks:**
- [ ] Source or create Stratocaster body DXF (`strat/body_standard.dxf`)
- [ ] Source or create Les Paul body DXF (`lp/body_standard.dxf`)
- [ ] Source or create OM acoustic body DXF (`acoustic/om_body.dxf`)
- [ ] Source or create Dreadnought body DXF (`acoustic/dreadnought_body.dxf`)
- [ ] Verify all DXF files are R12 format (AC1009)
- [ ] Validate coordinates are in millimeters
- [ ] Test CAM import in Fusion 360 and VCarve

**Files to Create:**
```
services/api/app/assets/instrument_templates/
├── strat/body_standard.dxf
├── lp/body_standard.dxf
├── acoustic/om_body.dxf
└── acoustic/dreadnought_body.dxf
```

**Validation Script:**
```python
from instrument_geometry.dxf_registry import DXF_ASSETS
for asset_id, asset in DXF_ASSETS.items():
    if not asset.path.exists():
        print(f"❌ Missing: {asset_id} -> {asset.path}")
    else:
        print(f"✅ Found: {asset_id}")
```

---

### 2. Create Pytest Test Suite
**Priority:** MEDIUM  
**Reason:** Automated validation ensures code stability across changes

**Test Files to Create:**

#### `tests/test_neck_taper.py`
```python
"""Tests for neck taper mathematical engine."""
import pytest
from instrument_geometry.neck_taper import (
    TaperInputs, fret_distance, width_at_fret, 
    compute_taper_table, reference_length
)

def test_reference_length_calculation():
    """Test reference length formula (12th fret position)."""
    L = reference_length(scale_length_mm=648.0, fret_num=12)
    assert abs(L - 324.0) < 0.1, "12th fret should be at half scale length"

def test_fret_distance_monotonic():
    """Test fret distances increase monotonically."""
    inputs = TaperInputs(42.0, 57.0, 16.0, 648.0)
    distances = [fret_distance(f, inputs.scale_length_mm) for f in range(23)]
    
    for i in range(len(distances) - 1):
        assert distances[i] < distances[i+1], f"Fret {i} distance not monotonic"

def test_width_at_fret_boundaries():
    """Test width at nut and heel boundaries."""
    inputs = TaperInputs(nut_width_mm=42.0, heel_width_mm=57.0, 
                        taper_length_in=16.0, scale_length_mm=648.0)
    
    w0 = width_at_fret(0, inputs)
    assert abs(w0 - 42.0) < 0.01, "Fret 0 width should equal nut width"
    
    # Fret 22 is beyond typical taper length, but should not exceed heel width
    w22 = width_at_fret(22, inputs)
    assert w22 <= inputs.heel_width_mm + 1.0, "Width should not exceed heel by much"

def test_compute_taper_table_structure():
    """Test taper table has correct structure."""
    inputs = TaperInputs(42.0, 57.0, 16.0, 648.0)
    table = compute_taper_table(22, inputs)
    
    assert len(table) == 23, "Should have 23 rows (frets 0-22)"
    assert table[0].fret_num == 0
    assert table[22].fret_num == 22
    assert all(row.width_mm > 0 for row in table)
```

#### `tests/test_neck_taper_dxf_export.py`
```python
"""Tests for DXF export functionality."""
import pytest
from pathlib import Path
from instrument_geometry.neck_taper import (
    TaperInputs, export_neck_outline_to_dxf,
    build_r12_polyline_dxf, Point
)

def test_build_r12_polyline_dxf_minimal():
    """Test DXF generation with minimal 3-point outline."""
    outline = [Point(0.0, 10.0), Point(100.0, 15.0), Point(0.0, 10.0)]
    dxf = build_r12_polyline_dxf(outline, "TEST_LAYER")
    
    assert "AC1009" in dxf, "Should be R12 format"
    assert "TEST_LAYER" in dxf
    assert "POLYLINE" in dxf
    assert "VERTEX" in dxf
    assert "SEQEND" in dxf
    assert dxf.count("VERTEX") == 3

def test_export_neck_outline_to_dxf_file(tmp_path):
    """Test complete DXF file export workflow."""
    inputs = TaperInputs(42.0, 57.0, 16.0, 648.0)
    output_file = tmp_path / "test_neck.dxf"
    
    export_neck_outline_to_dxf(output_file, inputs, num_frets=22)
    
    assert output_file.exists()
    assert output_file.stat().st_size > 1000  # Should be >1KB
    
    # Verify content
    content = output_file.read_text()
    assert "AC1009" in content
    assert "NECK_OUTLINE" in content
    # 23 frets × 2 sides = 46 vertices
    assert content.count("VERTEX") == 46

def test_dxf_coordinate_precision():
    """Test that coordinates are written with proper precision."""
    outline = [Point(1.23456789, 9.87654321), Point(1.23456789, 9.87654321)]
    dxf = build_r12_polyline_dxf(outline)
    
    # Should round to 4 decimal places
    assert "1.2346" in dxf
    assert "9.8765" in dxf
    assert "1.23456789" not in dxf  # Too much precision

def test_dxf_closure_flag():
    """Test that polyline closure flag is set correctly."""
    outline = [Point(0.0, 10.0), Point(100.0, 10.0), Point(0.0, 10.0)]
    dxf = build_r12_polyline_dxf(outline)
    
    # Group code 70 = polyline flags, value 1 = closed
    assert "  70\n1\n" in dxf, "Polyline should have closed flag set"
```

**Run Tests:**
```bash
cd services/api
pytest tests/test_neck_taper.py -v
pytest tests/test_neck_taper_dxf_export.py -v
pytest tests/test_neck_taper*.py -v --cov=app.instrument_geometry.neck_taper
```

---

### 3. Update Router Registration (Missing Return Statement)
**Priority:** LOW  
**Reason:** Router is imported but not yet included in app

**Current State in `main.py`:**
```python
# Wave 17 — Instrument Geometry: Neck Taper Suite
try:
    from .instrument_geometry.neck_taper.api_router import router as neck_taper_router
except Exception as e:
    print(f"Warning: Could not load neck_taper_router: {e}")
    neck_taper_router = None
```

**Need to Add (around line 710 with other instrument routers):**
```python
# Wave 17 — Neck Taper Suite
if neck_taper_router is not None:
    app.include_router(neck_taper_router, prefix="/api/instrument/neck_taper", tags=["Instrument Geometry"])
```

**Location:** After `instrument_geometry_router` registration (line ~708)

---

## 🎯 Enhancement Tasks (Optional)

### 4. Expand GuitarModelSpec Presets
**Priority:** MEDIUM  
**Benefit:** More out-of-the-box model definitions

**Models to Add:**
- [ ] Telecaster 25.5" (`tele_25_5`)
- [ ] SG 24.75" (`sg_24_75`)
- [ ] PRS Custom 25" (`prs_custom_25`)
- [ ] Jaguar 24" (`jaguar_24`)
- [ ] Acoustic OM 25.4" (`om_acoustic`)
- [ ] Acoustic Dreadnought 25.4" (`dreadnought`)
- [ ] 7-string extended range (`extended_7string`)
- [ ] Bass Precision 34" (`pbass_34`)
- [ ] Bass Jazz 34" (`jbass_34`)

**File:** `services/api/app/instrument_geometry/model_spec.py`

**Example Pattern:**
```python
TELE_25_5_MODEL = GuitarModelSpec(
    id="tele_25_5",
    display_name="Tele-style 25.5\"",
    scale_profile_id="fender_25_5",
    num_strings=6,
    strings=STANDARD_10_46_E_STANDARD,
    nut_spacing=StringSpacingSpec(num_strings=6, e_to_e_mm=35.0, bass_edge_margin_mm=3.0, treble_edge_margin_mm=2.5),
    bridge_spacing=StringSpacingSpec(num_strings=6, e_to_e_mm=52.0),
    neck_taper=NeckTaperSpec(nut_width_mm=42.0, heel_width_mm=56.0, taper_length_in=16.0),
    body_outline_id="tele_body_v1"
)

PRESET_MODELS["tele_25_5"] = TELE_25_5_MODEL
```

---

### 5. Add DXF Validation Utility
**Priority:** MEDIUM  
**Benefit:** Catch malformed DXF files before CAM import

**Create File:** `services/api/app/instrument_geometry/dxf_validator.py`

```python
"""DXF validation utilities for asset integrity checking."""
from pathlib import Path
from typing import Dict, Any
from .dxf_registry import DXFAsset

def validate_dxf_asset(asset: DXFAsset) -> Dict[str, Any]:
    """
    Validate DXF file integrity and geometry.
    
    Returns:
        Dictionary with validation results:
        - valid: bool
        - errors: List[str]
        - warnings: List[str]
        - stats: Dict (file size, entity count, etc.)
    """
    errors = []
    warnings = []
    
    # Check 1: File exists
    if not asset.path.exists():
        errors.append(f"File not found: {asset.path}")
        return {"valid": False, "errors": errors, "warnings": warnings}
    
    # Check 2: File readable
    try:
        content = asset.path.read_text()
    except Exception as e:
        errors.append(f"Cannot read file: {e}")
        return {"valid": False, "errors": errors, "warnings": warnings}
    
    # Check 3: DXF header
    if "AC1009" not in content and asset.dxf_version == "R12":
        errors.append(f"Expected R12 (AC1009) format, not found in header")
    
    # Check 4: Entity presence
    if "POLYLINE" not in content and "LWPOLYLINE" not in content:
        errors.append("No polyline entities found")
    
    # Check 5: Proper closure
    if "SEQEND" in content and "POLYLINE" in content:
        polyline_count = content.count("POLYLINE")
        seqend_count = content.count("SEQEND")
        if polyline_count != seqend_count:
            warnings.append(f"Mismatched POLYLINE ({polyline_count}) and SEQEND ({seqend_count}) counts")
    
    # Check 6: File size sanity
    file_size_kb = asset.path.stat().st_size / 1024
    if file_size_kb < 1:
        warnings.append(f"Suspiciously small file: {file_size_kb:.1f} KB")
    elif file_size_kb > 10000:
        warnings.append(f"Very large file: {file_size_kb:.1f} KB (may be slow to load)")
    
    stats = {
        "file_size_kb": file_size_kb,
        "vertex_count": content.count("VERTEX"),
        "polyline_count": content.count("POLYLINE") + content.count("LWPOLYLINE")
    }
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "stats": stats
    }
```

**Usage:**
```python
from instrument_geometry.dxf_registry import get_dxf_asset_by_id
from instrument_geometry.dxf_validator import validate_dxf_asset

asset = get_dxf_asset_by_id("strat_body_v1")
result = validate_dxf_asset(asset)

if result["valid"]:
    print(f"✅ Valid: {result['stats']}")
else:
    print(f"❌ Errors: {result['errors']}")
if result["warnings"]:
    print(f"⚠️ Warnings: {result['warnings']}")
```

---

### 6. Create Frontend Integration (Client Side)
**Priority:** LOW  
**Benefit:** Interactive neck taper designer in Vue client

**Create File:** `packages/client/src/views/InstrumentGeometry/NeckTaperDesigner.vue`

```vue
<script setup lang="ts">
import { ref, computed } from 'vue'

const nutWidth = ref(42.0)
const heelWidth = ref(57.0)
const taperLength = ref(16.0)
const scaleLength = ref(648.0)
const numFrets = ref(22)

const isValid = computed(() => {
  return nutWidth.value > 0 && 
         heelWidth.value > nutWidth.value &&
         taperLength.value > 0 &&
         scaleLength.value > 0
})

async function generateOutline() {
  const response = await fetch('/api/instrument/neck_taper/outline', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      nut_width_mm: nutWidth.value,
      heel_width_mm: heelWidth.value,
      taper_length_in: taperLength.value,
      scale_length_mm: scaleLength.value,
      num_frets: numFrets.value
    })
  })
  
  const data = await response.json()
  // Render outline on canvas
  renderOutline(data.outline)
}

async function downloadDXF() {
  const response = await fetch('/api/instrument/neck_taper/outline.dxf', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      nut_width_mm: nutWidth.value,
      heel_width_mm: heelWidth.value,
      taper_length_in: taperLength.value,
      scale_length_mm: scaleLength.value,
      num_frets: numFrets.value
    })
  })
  
  const blob = await response.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'neck_taper.dxf'
  a.click()
}

function renderOutline(points: Array<{x: number, y: number}>) {
  // Canvas rendering logic
}
</script>

<template>
  <div class="neck-taper-designer">
    <h2>Neck Taper Designer</h2>
    
    <div class="controls">
      <label>Nut Width (mm): <input v-model.number="nutWidth" type="number" step="0.1"/></label>
      <label>Heel Width (mm): <input v-model.number="heelWidth" type="number" step="0.1"/></label>
      <label>Taper Length (in): <input v-model.number="taperLength" type="number" step="0.1"/></label>
      <label>Scale Length (mm): <input v-model.number="scaleLength" type="number" step="0.1"/></label>
      <label>Frets: <input v-model.number="numFrets" type="number" min="12" max="27"/></label>
      
      <button @click="generateOutline" :disabled="!isValid">Preview</button>
      <button @click="downloadDXF" :disabled="!isValid">Download DXF</button>
    </div>
    
    <canvas ref="canvas" width="800" height="400"></canvas>
  </div>
</template>
```

---

### 7. Add CI/CD Smoke Tests
**Priority:** MEDIUM  
**Benefit:** Automated validation on every commit

**Create File:** `.github/workflows/wave17_neck_taper.yml`

```yaml
name: Wave 17 - Neck Taper Suite Tests

on:
  push:
    paths:
      - 'services/api/app/instrument_geometry/**'
      - 'tests/test_neck_taper*.py'
  pull_request:
    paths:
      - 'services/api/app/instrument_geometry/**'

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        cd services/api
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run Neck Taper Tests
      run: |
        cd services/api
        pytest tests/test_neck_taper*.py -v --cov=app.instrument_geometry.neck_taper
    
    - name: Test API Endpoints
      run: |
        cd services/api
        uvicorn app.main:app --host 0.0.0.0 --port 8000 &
        sleep 5
        
        # Test JSON endpoint
        curl -X POST http://localhost:8000/api/instrument/neck_taper/outline \
          -H 'Content-Type: application/json' \
          -d '{"nut_width_mm":42,"heel_width_mm":57,"taper_length_in":16,"scale_length_mm":648,"num_frets":22}' \
          | jq '.outline | length'
        
        # Test DXF endpoint
        curl -X POST http://localhost:8000/api/instrument/neck_taper/outline.dxf \
          -H 'Content-Type: application/json' \
          -d '{"nut_width_mm":42,"heel_width_mm":57,"taper_length_in":16,"scale_length_mm":648,"num_frets":22}' \
          -o test_neck.dxf
        
        # Verify DXF file
        grep -q "AC1009" test_neck.dxf && echo "✅ DXF format validated"
```

---

### 8. Integrate with Art Studio
**Priority:** LOW  
**Benefit:** Neck taper can feed Art Studio toolpath generation

**Task:** Add neck taper as input to Art Studio relief carving workflows

**Files to Modify:**
- `services/api/app/art_studio/relief_router.py`
- `packages/client/src/views/ArtStudio/ReliefView.vue`

**Concept:**
```python
@router.post("/relief/from_neck_taper")
async def generate_relief_from_neck_taper(
    neck_inputs: TaperInputs,
    relief_depth_mm: float = 2.0
):
    """Generate 3D relief toolpath for neck back carve."""
    # 1. Generate neck outline
    outline = generate_neck_outline(22, neck_inputs)
    
    # 2. Convert to relief boundary
    # 3. Apply thickness profile (C/V/U carve)
    # 4. Generate adaptive toolpath
    pass
```

---

## 📋 Maintenance Tasks

### 9. Code Quality & Cleanup
- [ ] Run `ruff` linter on all new files
- [ ] Add type hints to all public functions (already mostly done)
- [ ] Add docstring examples to all major functions
- [ ] Verify all imports are absolute (not relative where inappropriate)

### 10. Documentation Updates
- [ ] Add Wave 17 section to main `README.md`
- [ ] Update API documentation (Swagger/OpenAPI)
- [ ] Create video tutorial for Neck Taper Designer (optional)
- [ ] Add lutherie references (book citations, standard dimensions)

---

## 🚀 Future Expansion (Wave 18+)

### Compound Taper Curves
- [ ] Bezier curve interpolation for organic shapes
- [ ] Multi-segment tapers (faster taper near nut)
- [ ] Asymmetric bass/treble tapers

### 3D Neck Profile System
- [ ] Thickness profile integration (C/V/U back carves)
- [ ] Fretboard radius compensation
- [ ] STEP/IGES 3D solid export

### Machine Learning Enhancements
- [ ] Neck shape optimization (comfort + structural strength)
- [ ] FEA stress analysis integration
- [ ] Acoustic modeling (neck mass effects)

---

## 📞 Support & Questions

If you encounter issues or need clarification:

1. **Check Documentation:**
   - `docs/instrument/Neck_Taper_Theory.md`
   - `docs/instrument/Neck_Taper_DXF_Export.md`
   - `docs/instrument/Instrument_DXF_Mapping.md`

2. **Review Code Examples:**
   - All modules have extensive docstrings
   - Test files demonstrate usage patterns

3. **API Testing:**
   ```bash
   curl -X POST http://localhost:8000/api/instrument/neck_taper/outline \
     -H 'Content-Type: application/json' \
     -d '{"nut_width_mm":42,"heel_width_mm":57,"taper_length_in":16,"scale_length_mm":648,"num_frets":22}'
   ```

---

**Last Updated:** December 8, 2025  
**Next Review:** After real DXF assets are added (Task #1)
