# Designer Product Source File Map

> Maps Golden Master (`luthiers-toolbox`) source files to each standalone designer product.
>
> **Generated:** 2026-01-25

---

## Overview

Each designer product is extracted from specific modules in the Golden Master. This document identifies the source files for AI agents and developers performing feature extraction.

---

## 🎸 Neck Designer (`ltb-neck-designer`)

**Description:** Parametric neck profiles with Fender/Gibson presets, C/D/V shapes, fretboard geometry.

### Core Backend Files

| Source Path | Purpose | Priority |
|-------------|---------|----------|
| `services/api/app/routers/neck_router.py` | API endpoints (473 lines) | ⭐ Essential |
| `services/api/app/routers/neck_generator_router.py` | G-code generation endpoints | ⭐ Essential |
| `services/api/app/generators/neck_headstock_generator.py` | CNC generator (799 lines) | ⭐ Essential |
| `services/api/app/instrument_geometry/neck/neck_profiles.py` | Profile dataclasses (338 lines) | ⭐ Essential |
| `services/api/app/instrument_geometry/neck/fret_math.py` | Fret position math (687 lines) | ⭐ Essential |
| `services/api/app/instrument_geometry/neck/radius_profiles.py` | Radius curve math | ⭐ Essential |
| `services/api/app/instrument_geometry/neck_taper/neck_outline_generator.py` | Neck outline generation | ⭐ Essential |
| `services/api/app/instrument_geometry/body/fretboard_geometry.py` | Fretboard outline (254 lines) | Required |
| `services/api/app/calculators/fret_slots_cam.py` | Fret slot CAM (935 lines) | Optional |

### Schemas/Models

| Source Path | Purpose |
|-------------|---------|
| `services/api/app/instrument_geometry/models.py` | Core instrument models |
| `services/api/app/instrument_geometry/model_spec.py` | Model specifications |

### Key Dependencies

```python
# Core math (copy these)
from instrument_geometry.neck.fret_math import compute_fret_positions_mm
from instrument_geometry.neck.neck_profiles import FretboardSpec, InstrumentSpec
```

### Endpoints to Expose

| Endpoint | Purpose |
|----------|---------|
| `POST /neck/generate` | Generate neck geometry |
| `POST /neck/export/dxf` | Export DXF |
| `GET /neck/presets` | List preset profiles |
| `GET /health` | Edition tag |

---

## 🎵 Headstock Designer (`ltb-headstock-designer`)

**Description:** Headstock outline, tuner layout, angle calculation.

### Core Backend Files

| Source Path | Purpose | Priority |
|-------------|---------|----------|
| `services/api/app/generators/neck_headstock_generator.py` | Headstock geometry (lines 76-200+) | ⭐ Essential |
| `services/api/app/routers/neck_router.py` | Headstock params in NeckParameters | ⭐ Essential |
| `services/api/app/instrument_geometry/dxf_registry.py` | HEADSTOCK enum layer | Required |

### Key Classes to Extract

```python
# From neck_headstock_generator.py
class HeadstockStyle(str, Enum):
    GIBSON_OPEN = "gibson_open"
    GIBSON_SOLID = "gibson_solid"
    FENDER_STRAT = "fender_strat"
    FENDER_TELE = "fender_tele"
    PRS = "prs"
    CLASSICAL = "classical"
    PADDLE = "paddle"

# From neck_router.py - Headstock parameters
headstock_angle: float = Field(14.0, description="Headstock angle (degrees)")
headstock_length: float = Field(7.0, description="Headstock length (in)")
headstock_thickness: float = Field(0.625, description="Headstock thickness (in)")
tuner_layout: float = Field(2.5, description="Tuner spacing (in)")
tuner_diameter: float = Field(0.375, description="Tuner hole diameter (in)")
```

### Endpoints to Expose

| Endpoint | Purpose |
|----------|---------|
| `POST /headstock/generate` | Generate headstock outline |
| `POST /headstock/tuner-holes` | Generate tuner hole positions |
| `GET /headstock/styles` | List available styles |
| `GET /health` | Edition tag |

---

## 🎹 Fingerboard Designer (`ltb-fingerboard-designer`)

**Description:** Radius, scale, multiscale/fan-fret calculator, fret positions.

### Core Backend Files

| Source Path | Purpose | Priority |
|-------------|---------|----------|
| `services/api/app/instrument_geometry/neck/fret_math.py` | Core fret math (687 lines) | ⭐ Essential |
| `services/api/app/instrument_geometry/body/fretboard_geometry.py` | Outline/taper (254 lines) | ⭐ Essential |
| `services/api/app/routers/music/temperament_router.py` | Temperament systems (374 lines) | ⭐ Essential |
| `services/api/app/routers/fret_router.py` | Fret design endpoints | ⭐ Essential |
| `services/api/app/calculators/alternative_temperaments.py` | Temperament math | ⭐ Essential |
| `services/api/app/calculators/fret_slots_export.py` | Fret slot export | Required |
| `services/api/app/instrument_geometry/neck/radius_profiles.py` | Radius curves | Required |
| `services/api/app/instrument_geometry/fan_fret_guard.py` | Fan-fret validation | Optional |

### Key Functions to Extract

```python
# From fret_math.py
SEMITONE_RATIO = 2.0 ** (1.0 / 12.0)  # ≈ 1.05946

def compute_fret_positions_mm(scale_length_mm: float, fret_count: int) -> List[float]:
    """Compute equal-temperament fret positions."""
    
def compute_fan_fret_positions(
    bass_scale_mm: float,
    treble_scale_mm: float,
    string_count: int,
    fret_count: int,
    perpendicular_fret: int = 7,
) -> List[FanFretPoint]:
    """Compute multiscale fret geometry."""

# From fretboard_geometry.py
def compute_fretboard_outline(
    nut_width_mm: float,
    heel_width_mm: float,
    scale_length_mm: float,
    fret_count: int,
) -> List[Tuple[float, float]]:
    """Compute fretboard 2D outline."""
```

### Temperament Systems

```python
# From alternative_temperaments.py
class TemperamentSystem(str, Enum):
    EQUAL = "equal"
    JUST_MAJOR = "just_major"
    JUST_MINOR = "just_minor"
    PYTHAGOREAN = "pythagorean"
    MEANTONE_QUARTER = "meantone_quarter"
```

### Endpoints to Expose

| Endpoint | Purpose |
|----------|---------|
| `POST /fingerboard/calculate` | Calculate fret positions |
| `POST /fingerboard/fan-fret` | Multiscale calculation |
| `GET /temperaments/systems` | List temperament systems |
| `POST /temperaments/compare` | Compare to 12-TET |
| `GET /health` | Edition tag |

---

## 🌉 Bridge Designer (`ltb-bridge-designer`)

**Description:** Bridge geometry, string spacing, saddle compensation.

### Core Backend Files

| Source Path | Purpose | Priority |
|-------------|---------|----------|
| `services/api/app/routers/bridge_router.py` | API endpoints (367 lines) | ⭐ Essential |
| `services/api/app/instrument_geometry/bridge/geometry.py` | Bridge math (221 lines) | ⭐ Essential |
| `services/api/app/instrument_geometry/bridge/compensation.py` | Intonation (133 lines) | ⭐ Essential |
| `services/api/app/instrument_geometry/bridge/placement.py` | Bridge placement | Required |
| `services/api/app/pipelines/bridge/bridge_to_dxf.py` | DXF export | Required |

### Key Classes to Extract

```python
# From bridge_router.py
class BridgeGeometry(BaseModel):
    units: str
    scaleLength: float
    stringSpread: float  # E-to-E at bridge
    compTreble: float    # Compensation offset
    compBass: float
    slotWidth: float
    slotLength: float
    angleDeg: Optional[float]
    endpoints: BridgeEndpoints
    slotPolygon: List[Point]

# From geometry.py
def compute_saddle_positions_mm(
    scale_length_mm: float,
    compensations_mm: Dict[str, float],
) -> Dict[str, float]:
    """Compute actual saddle position per string."""

# From compensation.py
STANDARD_6_STRING_COMPENSATION = {
    "E6": 2.5, "A5": 2.0, "D4": 1.5, 
    "G3": 1.0, "B2": 1.5, "E1": 2.0
}
```

### Endpoints to Expose

| Endpoint | Purpose |
|----------|---------|
| `POST /bridge/export_dxf` | Generate DXF |
| `GET /bridge/presets` | Family/gauge presets |
| `POST /bridge/calculate` | Calculate compensation |
| `GET /health` | Edition tag |

---

## 📐 Blueprint Reader (`blueprint-reader`)

**Description:** AI-powered blueprint digitization, vectorization, DXF export.

### Core Backend Files

| Source Path | Purpose | Priority |
|-------------|---------|----------|
| `services/api/app/routers/blueprint_router.py` | Main endpoints (1316 lines) | ⭐ Essential |
| `services/api/app/routers/blueprint_cam_bridge.py` | CAM integration | Required |
| `services/api/app/services/vision_service.py` | Vision processing | ⭐ Essential |

### External Service Dependencies

```
services/blueprint-import/
├── analyzer/       # Phase 1: Claude AI analysis
├── vectorizer/     # Phase 2: OpenCV vectorization
└── vectorizer_phase2/  # Enhanced geometry extraction
```

### Key Endpoints to Expose

| Endpoint | Purpose |
|----------|---------|
| `POST /blueprint/analyze` | AI dimensional analysis |
| `POST /blueprint/to-svg` | Phase 1 annotated SVG |
| `POST /blueprint/vectorize-geometry` | Phase 2 vectorization |
| `GET /blueprint/status/{id}` | Analysis status |
| `GET /health` | Edition tag |

### AI Integration (Phase 1)

```python
# Claude Sonnet 4 Vision API prompt structure
# Returns: scale, dimensions, blueprint_type, confidence scores
{
    "scale": "1:1",
    "dimensions": [
        {"value": 12.75, "unit": "inches", "label": "scale_length", "confidence": 0.95},
    ],
    "blueprint_type": "guitar",
}
```

### OpenCV Pipeline (Phase 2)

```python
# Vectorization pipeline steps:
# 1. Grayscale conversion
# 2. Gaussian blur (5×5 kernel)
# 3. Canny edge detection
# 4. Contour extraction
# 5. Hough line transforms
# 6. DXF R12 polyline export
```

---

## Shared Utilities

These files are commonly needed across multiple designers:

| Source Path | Used By |
|-------------|---------|
| `services/api/app/util/dxf_helpers.py` | All (DXF export) |
| `services/api/app/util/units.py` | All (mm/in conversion) |
| `services/api/app/schemas/*.py` | All (common Pydantic models) |
| `services/api/app/core/config.py` | All (settings) |

---

## Extraction Checklist Template

Use this checklist when extracting any designer:

```markdown
## {{PRODUCT}} Extraction Checklist

### Backend
- [ ] Copy router file(s) from `services/api/app/routers/`
- [ ] Copy instrument_geometry modules needed
- [ ] Copy calculator modules needed
- [ ] Adapt imports (remove `app.` prefix or restructure)
- [ ] Create minimal `requirements.txt`
- [ ] Add health endpoint with edition tag

### Frontend (if applicable)
- [ ] Copy Vue components from `packages/client/src/components/`
- [ ] Copy Pinia stores from `packages/client/src/stores/`
- [ ] Adapt SDK endpoints
- [ ] Create minimal `package.json`

### Testing
- [ ] Copy relevant tests from `services/api/tests/`
- [ ] Adapt test fixtures
- [ ] Add edition tag verification test
- [ ] Run tests in isolation (no Golden Master)

### Documentation
- [ ] Fill in `.github/copilot-instructions.md` template
- [ ] Update README with feature documentation
- [ ] Add API endpoint documentation
```

---

## See Also

- [MASTER_SEGMENTATION_STRATEGY.md](./MASTER_SEGMENTATION_STRATEGY.md) – Product family architecture
- [../PRODUCT_REPO_SETUP.md](../../PRODUCT_REPO_SETUP.md) – Repo creation workflow
- [templates/.github/copilot-instructions.md](../../templates/.github/copilot-instructions.md) – Spin-off instruction template
