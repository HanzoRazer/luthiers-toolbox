# DXF & SVG Generation Architecture

> **Luthiers Toolbox** — Vector Graphics Export System  
> Last updated: 2026-04-23

---

## Table of Contents

1. [Overview](#overview)
2. [DXF Generation Systems](#dxf-generation-systems)
   - [Bridge Export](#1-bridge-export)
   - [Smart Guitar DXF Generator](#2-smart-guitar-dxf-generator)
   - [Edge-to-DXF Photo Vectorizer](#3-edge-to-dxf-photo-vectorizer)
   - [Inlay Pattern Export](#4-inlay-pattern-export)
   - [Blueprint Phase 2/3 Vectorizer](#5-blueprint-phase-23-vectorizer)
   - [Headstock Export](#6-headstock-export)
   - [Adaptive Pocketing Input](#7-adaptive-pocketing-dxf-input)
3. [SVG Generation Systems](#svg-generation-systems)
   - [Rosette Designer](#1-rosette-designer)
   - [Blueprint Phase 3 SVG Export](#2-blueprint-phase-3-svg-export)
   - [AI Art Studio (Prompt→SVG)](#3-ai-art-studio-promptsvg)
   - [Inlay Preview SVG](#4-inlay-preview-svg)
4. [Directory Structure](#directory-structure)
5. [Backend API Endpoint Reference](#backend-api-endpoint-reference)
6. [Frontend Components](#frontend-components)
7. [Core Libraries & Dependencies](#core-libraries--dependencies)
8. [DXF Version Support & Compatibility Layer](#dxf-version-support--compatibility-layer)
9. [Known Infrastructure Issues](#known-infrastructure-issues)

---

## Overview

The Luthiers Toolbox platform provides multiple pathways for generating DXF and SVG vector files:

| **Input Type** | **Processing System** | **Output Formats** |
|----------------|----------------------|-------------------|
| JSON Spec | Smart Guitar Generator | DXF (R2010) |
| Manual Geometry | Bridge Export | DXF (R12) |
| Photo/PDF Upload | Edge-to-DXF, Phase 2/3 Vectorizers | DXF, SVG |
| Design Parameters | Inlay Calculator, Rosette Designer | DXF, SVG |
| Text Prompt | AI Art Studio | SVG (via DALL-E + potrace/vtracer) |

All DXF generators use the **ezdxf** library. The default output format is **R12** for maximum CAM software compatibility, though R2010 is used for complex geometry requiring LWPOLYLINE entities.

---

## DXF Generation Systems

### 1. Bridge Export

**Purpose:** Generate bridge saddle geometry DXF for CNC routing.

**File:** `services/api/app/cam/routers/bridge_export_router.py`

**Endpoint:**
```
POST /api/cam/bridge/export_dxf
```

**Input Model:** `BridgeGeometryIn`
```python
class BridgeGeometryIn(BaseModel):
    units: str = "mm"
    scaleLength: float           # e.g., 648.0 (25.5")
    stringSpread: float          # String spacing at bridge
    compTreble: float            # Treble compensation (mm)
    compBass: float              # Bass compensation (mm)
    slotWidth: float             # Saddle slot width
    slotLength: float            # Saddle slot length
    angleDeg: float              # Saddle angle
    endpoints: Dict[str, Dict]   # {"treble": {x, y}, "bass": {x, y}}
    slotPolygon: List[Dict]      # 4 vertices defining slot rectangle
```

**Output Layers:**
| Layer | Entity Type | Description |
|-------|-------------|-------------|
| `SADDLE` | LINE | Centerline from treble to bass endpoint |
| `SLOT` | LINE (×4) | 4-sided closed slot rectangle |
| `REFERENCE` | LINE | Scale length reference line |

**DXF Format:** R12 (manual entity construction, no ezdxf document)

**Response:** `application/dxf` with `Content-Disposition: attachment`

---

### 2. Smart Guitar DXF Generator

**Purpose:** Generate complete electric guitar routing DXF from database spec.

**File:** `services/api/app/routers/instruments/guitar/smart_guitar_dxf_router.py`

**Endpoint:**
```
GET /api/instruments/smart-guitar/dxf
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `version` | string | `"v3"` | Spec version identifier |
| `include_cavities` | bool | `true` | Include routing cavities |
| `include_body_outline` | bool | `true` | Include body outline |

**Input Source:** JSON spec file at:
```
services/api/app/instrument_geometry/body/specs/smart_guitar_v1.json
```

**Output Layers (12 total):**
| Layer | ACI Color | Description |
|-------|-----------|-------------|
| `BODY_OUTLINE` | 7 (White) | Explorer-Klein hybrid silhouette |
| `NECK_POCKET` | 5 (Magenta) | Bolt-on pocket 76.2×55.9×15.9mm |
| `NECK_PICKUP` | 1 (Red) | Humbucker route |
| `BRIDGE_PICKUP` | 1 (Red) | Humbucker route |
| `BRIDGE_ROUTE` | 3 (Green) | Headless bridge mounting |
| `REAR_ELECTRONICS` | 4 (Cyan) | Raspberry Pi 5 cavity |
| `ARDUINO_POCKET` | 4 (Cyan) | Preamp/battery bay |
| `ANTENNA_RECESS` | 6 (Magenta) | RF window shelf |
| `CONTROL_PLATE` | 2 (Yellow) | Surface recess |
| `OUTPUT_JACK` | 30 (Orange) | Angled bore (CIRCLE entity) |
| `USB_PORT` | 30 (Orange) | Edge-routed slot |
| `BOLT_HOLES` | 8 (Gray) | 4× neck bolt positions (CIRCLE) |

**DXF Format:** R2010 via ezdxf (`ezdxf.new("R2010")`)

**Entity Types:** LWPOLYLINE (rectangles), CIRCLE (holes/jacks)

---

### 3. Edge-to-DXF Photo Vectorizer

**Purpose:** High-fidelity edge extraction from photos/PDFs to DXF. This system produced the reference `cuatro_puertoriqueno_simple.dxf` (15.5MB, 129,000 LINE entities).

**Files:**
- Router: `services/api/app/routers/blueprint/edge_to_dxf_router.py`
- Core Engine: `services/photo-vectorizer/edge_to_dxf.py`

**Endpoints:**
```
POST /blueprint/edge-to-dxf/convert      # Standard single-pass Canny
POST /blueprint/edge-to-dxf/enhanced     # Multi-scale edge fusion (archival)
GET  /blueprint/edge-to-dxf/status       # Module availability check
```

**Input:** File upload (PNG, JPG, PDF)
- PDF rendered at 300 DPI via PyMuPDF (`fitz`)

**Parameters (convert endpoint):**
| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `target_height_mm` | float | 500.0 | — | Output height in mm |
| `canny_low` | int | 50 | 1-255 | Canny low threshold |
| `canny_high` | int | 150 | 1-255 | Canny high threshold |
| `adjacency` | float | 3.0 | 1.0-10.0 | Max pixel distance to connect |
| `return_file` | bool | false | — | Direct file download vs JSON |

**Output Characteristics:**
| Mode | LINE Entities | File Size | Use Case |
|------|---------------|-----------|----------|
| Standard | 50,000-100,000 | 10-20MB | Working files |
| Enhanced | 50,000-300,000+ | 10-50MB | Archival, manual CAD tracing |

**DXF Format:** R12 (individual LINE entities for maximum compatibility)

**Response Model:** `EdgeToDXFResponse`
```python
class EdgeToDXFResponse(BaseModel):
    success: bool
    dxf_path: Optional[str]
    line_count: int
    edge_pixel_count: int
    image_size_px: list      # [width, height]
    output_size_mm: list     # [width, height]
    mm_per_px: float
    processing_time_ms: float
    file_size_mb: float
    method: str              # "standard" or "enhanced"
```

---

### 4. Inlay Pattern Export

**Purpose:** Generate fretboard inlay geometry for CNC pocket milling.

**File:** `services/api/app/art_studio/inlay_router.py`

**Endpoints:**
```
POST /art-studio/inlay/preview           # Calculate positions + SVG preview
POST /art-studio/inlay/export-dxf        # Export DXF file
POST /art-studio/inlay/export-gcode      # Generate pocket milling G-code
GET  /art-studio/inlay/presets           # List available presets
GET  /art-studio/inlay/presets/{name}    # Get specific preset
GET  /art-studio/inlay/pattern-types     # List shape types
GET  /art-studio/inlay/dxf-versions      # List supported DXF versions
```

**Input Model:** `InlayDXFRequest`
```python
class InlayDXFRequest(BaseModel):
    pattern_type: InlayPatternType = DOT  # dot, diamond, block, etc.
    fret_positions: List[int] = [3, 5, 7, 9, 12, 15, 17, 19, 21, 24]
    double_at_12: bool = True
    marker_diameter_mm: float = 6.0       # 2.0-20.0
    block_width_mm: float = 40.0
    block_height_mm: float = 8.0
    scale_length_mm: float = 648.0
    pocket_depth_mm: float = 1.5          # 0.5-5.0
    include_side_dots: bool = False
    dxf_version: str = "R12"
```

**Pattern Types (InlayPatternType enum):**
- `DOT` — Standard circular dots
- `DIAMOND` — Jazz diamond markers
- `BLOCK` — Gibson Les Paul style blocks
- `PARALLELOGRAM` — Gibson ES trapezoid style
- `SPLIT_BLOCK` — Split block inlays
- `CROWN` — Crown/fancy markers
- `SNOWFLAKE` — Decorative snowflake
- `CUSTOM` — User-defined vertices

**Output Layers:**
| Layer | Description |
|-------|-------------|
| `INLAY_OUTLINE` | Shape perimeters (CIRCLE for dots, LINE for polygons) |
| `INLAY_CENTER` | Center points for alignment |

**DXF Format:** R12 default (configurable via `dxf_version` parameter)

---

### 5. Blueprint Phase 2/3 Vectorizer

**Purpose:** Extract vector geometry from blueprint PDFs/images with ML classification.

**Files:**
- Phase 2 Router: `services/api/app/routers/blueprint/phase2_router.py`
- Phase 3 Router: `services/api/app/routers/blueprint/phase3_router.py`
- Phase 2 Core: `services/blueprint-import/vectorizer_phase2.py`
- Phase 3 Core: `services/blueprint-import/vectorizer_phase3.py`

**Endpoints:**
```
# Phase 2
POST /blueprint/to-dxf               # OpenCV-based extraction

# Phase 3
POST /blueprint/phase3/vectorize     # Full ML pipeline
POST /blueprint/phase3/quick         # Quick extraction (no ML/OCR)
GET  /blueprint/phase3/info          # Module availability
```

**Phase 3 Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `instrument_type` | string | `"electric"` | electric, acoustic, archtop, bass, ukulele, mandolin |
| `spec_name` | string | — | Known spec for validation |
| `dual_pass` | bool | `true` | Aggressive body + lighter detail extraction |
| `use_ml` | bool | `true` | Enable ML contour classification |
| `detect_primitives` | bool | `true` | Detect circles, rectangles |
| `validate` | bool | `true` | Validate against spec dimensions |
| `dpi` | int | 400 | PDF render DPI (72-1200) |
| `scale_hint_mm_per_pixel` | float | — | Override from Phase 1 AI analysis |

**Output Classification Layers:**
| Layer | Description |
|-------|-------------|
| `BODY_OUTLINE` | Main instrument silhouette |
| `PICKGUARD` | Pickguard geometry |
| `NECK_POCKET` | Neck pocket route |
| `PICKUP_ROUTE` | Pickup cavities |
| `CONTROL_CAVITY` | Electronics cavity |
| `BRIDGE_ROUTE` | Bridge mounting area |
| `JACK_ROUTE` | Output jack route |
| `SOUNDHOLE` | Acoustic soundhole |
| `ROSETTE` | Rosette decoration ring |
| `BRACING` | Internal bracing pattern |

**DXF Format:** R2010 with LWPOLYLINE (closed contours)

---

### 6. Headstock Export

**Purpose:** Generate headstock DXF with veneer and binding layers.

**File:** `services/api/app/routers/headstock/dxf_export.py`

**Endpoint:**
```
POST /api/export/headstock-dxf
```

**Output Layers:**
- Headstock outline
- Veneer layout
- Binding profile

---

### 7. Adaptive Pocketing DXF Input

**Purpose:** Accept DXF uploads for adaptive toolpath generation.

**File:** `services/api/app/routers/adaptive/dxf_router.py`

**Endpoint:**
```
POST /api/cam/adaptive/plan_from_dxf
```

**Input Requirements:**
- DXF file with `GEOMETRY` layer
- LWPOLYLINE entities (closed polylines)

**Processing:** `_dxf_to_loops_from_bytes()` extracts geometry for toolpath planning.

---

## SVG Generation Systems

### 1. Rosette Designer

**Purpose:** Interactive rosette wheel design with real-time SVG preview.

**Files:**
- Router: `services/api/app/art_studio/api/rosette_designer_routes.py`
- SVG Renderer: `services/api/app/art_studio/services/rosette/rosette_svg.py`
- Engine: `services/api/app/art_studio/services/rosette_engine.py`

**Endpoints:**
```
GET  /rosette/catalog              # Tile catalog with SVG patterns
POST /rosette/preview              # Render SVG preview
POST /rosette/export/svg           # Export downloadable SVG
POST /rosette/place-tile           # Place tile with symmetry
POST /rosette/sym-cells            # Get symmetry-affected cells
POST /rosette/bom                  # Bill of materials
POST /rosette/mfg-check            # Manufacturing validation
GET  /rosette/recipes              # 8 recipe presets
```

**Preview Request:**
```python
class PreviewRequest(BaseModel):
    num_segs: int           # Number of segments (8-36)
    grid: Dict[str, str]    # Cell → tile_id mapping
    ring_active: List[bool] # Active rings
    show_tabs: bool = True
    show_annotations: bool = False
    width: int = 400
    height: int = 400
```

**Supported Tile Materials (15+ patterns):**
- Abalone
- Mother of pearl (MOP)
- Burl
- Herringbone
- Celtic knot
- Checkerboard
- Custom patterns with gradients

**SVG Features:**
- Pattern tile definitions with SVG gradients
- Extension tabs visualization
- Guide circles and radial lines
- Color-coded material representation

---

### 2. Blueprint Phase 3 SVG Export

**Purpose:** Export classified contours to color-coded SVG for visualization.

**File:** `services/blueprint-import/export_svg.py`

**Function:**
```python
def export_to_svg(
    classified: dict,              # Category → contour list
    output_path: str,
    image_height: int,
    mm_per_px: float,
    center_on_body: bool = True,
    simplify_tolerance: float = 0.2,  # Douglas-Peucker mm
    excluded_categories: list = None,
    max_per_category: dict = None,
    scale_factor: float = 1.0
) -> Tuple[float, float]:          # (body_width_mm, body_height_mm)
```

**Layer Color Mapping:**
| Layer | Color | Hex |
|-------|-------|-----|
| BODY_OUTLINE | Red | `#FF0000` |
| PICKGUARD | Yellow | `#FFFF00` |
| NECK_POCKET | Green | `#00FF00` |
| PICKUP_ROUTE | Cyan | `#00FFFF` |
| CONTROL_CAVITY | Blue | `#0000FF` |
| BRIDGE_ROUTE | Magenta | `#FF00FF` |
| SOUNDHOLE | Red | `#FF0000` |
| ROSETTE | Yellow | `#FFFF00` |
| BRACING | Green | `#00FF00` |
| Unknown | Orange | `#FF6600` |

**Library:** `svgwrite>=1.4.0`

---

### 3. AI Art Studio (Prompt→SVG)

**Purpose:** Generate SVG from text prompts using AI image generation + vectorization.

**File:** `services/api/app/art_studio/svg/generator.py`

**Flow:**
1. Safety check via `ai.safety`
2. Image generation via `ai.transport.image_client` (DALL-E 3)
3. Vectorization to SVG (potrace, vtracer, or autotrace)
4. Audit logging via `ai.observability`

**Configuration:**
```python
@dataclass
class SVGGeneratorConfig:
    provider: str = "openai"
    model: str = "dall-e-3"
    size: str = "1024x1024"
    quality: str = "standard"
    vectorize_method: VectorizeMethod = POTRACE
    style: str = "line_art"
    
    # Potrace options
    potrace_turdsize: int = 2       # Speckle suppression
    potrace_alphamax: float = 1.0   # Corner threshold
    potrace_opttolerance: float = 0.2
    
    # Vtracer options
    vtracer_colormode: str = "binary"
    vtracer_filter_speckle: int = 4
```

**Vectorization Methods:**
| Method | Binary | Description |
|--------|--------|-------------|
| `POTRACE` | `potrace` | Classic bitmap tracer, requires PBM input |
| `VTRACER` | `vtracer` | Rust-based, better curve handling |
| `AUTOTRACE` | `autotrace` | Alternative tracer |
| `NONE` | — | Return PNG embedded in SVG |

**Output:** SVGResult with embedded metadata (RDF/DC)

---

### 4. Inlay Preview SVG

**Purpose:** Inline SVG preview of calculated inlay positions.

**File:** `services/api/app/art_studio/inlay_router.py` (function `_generate_preview_svg`)

**Features:**
- Fretboard background visualization
- Scale-to-fit rendering
- Shape-aware rendering (circles for dots, polygons for others)
- Labels showing count, pattern type, scale length, depth

---

## Directory Structure

```
services/
├── api/app/
│   ├── cam/routers/
│   │   └── bridge_export_router.py          # Bridge DXF export
│   │
│   ├── routers/
│   │   ├── blueprint/
│   │   │   ├── edge_to_dxf_router.py        # Photo→DXF high-fidelity
│   │   │   ├── phase2_router.py             # Blueprint vectorization
│   │   │   └── phase3_router.py             # ML-based vectorization
│   │   │
│   │   ├── instruments/guitar/
│   │   │   └── smart_guitar_dxf_router.py   # Smart Guitar from spec
│   │   │
│   │   ├── headstock/
│   │   │   └── dxf_export.py                # Headstock DXF
│   │   │
│   │   └── adaptive/
│   │       └── dxf_router.py                # DXF input for toolpaths
│   │
│   ├── art_studio/
│   │   ├── api/
│   │   │   └── rosette_designer_routes.py   # Rosette SVG endpoints
│   │   │
│   │   ├── services/
│   │   │   ├── rosette_engine.py            # Rosette logic + SVG render
│   │   │   └── rosette/rosette_svg.py       # SVG pattern definitions
│   │   │
│   │   ├── svg/
│   │   │   └── generator.py                 # AI prompt→SVG
│   │   │
│   │   └── inlay_router.py                  # Inlay DXF/SVG/G-code
│   │
│   ├── instrument_geometry/
│   │   ├── body/specs/
│   │   │   └── smart_guitar_v1.json         # Smart Guitar spec
│   │   └── dxf_registry.py                  # DXF asset registry
│   │
│   └── util/
│       └── dxf_compat.py                    # DXF version compatibility
│
├── photo-vectorizer/
│   ├── edge_to_dxf.py                       # High-fidelity converter
│   ├── cognitive_extraction_engine.py       # AI-assisted extraction
│   └── cognitive_extractor.py               # Claude Sonnet integration
│
└── blueprint-import/
    ├── vectorizer_phase2.py                 # OpenCV vectorizer
    ├── vectorizer_phase3.py                 # ML classification
    ├── export_svg.py                        # Phase 3 SVG export
    ├── dxf_postprocessor.py                 # DXF cleanup
    └── dxf_compat.py                        # Version handling

packages/client/src/components/
├── dxf/
│   ├── index.ts                             # DXF component exports
│   ├── DxfUploadZone.vue                    # File upload UI
│   ├── CamParametersForm.vue                # CAM settings
│   ├── GcodeResultPanel.vue                 # G-code output display
│   ├── OverrideModal.vue                    # Parameter overrides
│   ├── RunCompareCard.vue                   # Run comparison
│   └── useDxfToGcode.ts                     # DXF→G-code hook
│
└── compare/dual-svg/                        # SVG comparison viewer
```

---

## Backend API Endpoint Reference

### DXF Endpoints

| Endpoint | Method | Input | Output |
|----------|--------|-------|--------|
| `/api/cam/bridge/export_dxf` | POST | BridgeGeometryIn JSON | DXF R12 |
| `/api/instruments/smart-guitar/dxf` | GET | Query params | DXF R2010 |
| `/blueprint/edge-to-dxf/convert` | POST | File + params | DXF R12 |
| `/blueprint/edge-to-dxf/enhanced` | POST | File | DXF R12 |
| `/blueprint/edge-to-dxf/status` | GET | — | JSON status |
| `/art-studio/inlay/export-dxf` | POST | InlayDXFRequest | DXF R12 |
| `/blueprint/to-dxf` | POST | File + scale | DXF |
| `/blueprint/phase3/vectorize` | POST | File + params | DXF/SVG |
| `/api/export/headstock-dxf` | POST | Geometry spec | DXF |
| `/api/cam/adaptive/plan_from_dxf` | POST | DXF file | Toolpath JSON |

### SVG Endpoints

| Endpoint | Method | Input | Output |
|----------|--------|-------|--------|
| `/rosette/preview` | POST | PreviewRequest | SVG string in JSON |
| `/rosette/export/svg` | POST | ExportSvgRequest | SVG file |
| `/rosette/catalog` | GET | — | Catalog with SVG patterns |
| `/art-studio/inlay/preview` | POST | InlayPreviewRequest | JSON with `preview_svg` |
| `/blueprint/phase3/vectorize` | POST | File (return_svg=true) | SVG file |

---

## Frontend Components

### DXF Components (`packages/client/src/components/dxf/`)

| Component | Purpose |
|-----------|---------|
| `DxfUploadZone.vue` | Drag-and-drop DXF file upload interface |
| `CamParametersForm.vue` | CAM parameter configuration (feeds, speeds, depths) |
| `GcodeResultPanel.vue` | Display generated G-code with syntax highlighting |
| `OverrideModal.vue` | Override default parameters modal |
| `RunCompareCard.vue` | Compare multiple toolpath runs |
| `useDxfToGcode.ts` | Composable hook for DXF→G-code conversion |
| `index.ts` | Component exports |

### SVG Components

| Component | Purpose |
|-----------|---------|
| `compare/dual-svg/` | Side-by-side SVG comparison viewer |

### Utilities

| File | Purpose |
|------|---------|
| `utils/curvemath_dxf.ts` | DXF curve mathematics |
| `models/rmos_dxf.ts` | DXF data models (TypeScript types) |

---

## Core Libraries & Dependencies

### Python

| Library | Version | Purpose |
|---------|---------|---------|
| **ezdxf** | ≥1.0 | Primary DXF generation |
| **svgwrite** | ≥1.4.0 | SVG generation |
| **PyMuPDF (fitz)** | — | PDF rendering to image |
| **OpenCV (cv2)** | — | Edge detection, contour extraction |
| **numpy** | — | Geometry calculations |
| **Pillow** | — | Image format conversion (for potrace) |

### External Binaries (optional)

| Binary | Purpose |
|--------|---------|
| `potrace` | Bitmap→SVG vectorization |
| `vtracer` | Rust-based vectorization (better curves) |
| `autotrace` | Alternative vectorization |
| `svgo` | SVG optimization |
| `magick` (ImageMagick) | Image format conversion fallback |

---

## DXF Version Support & Compatibility Layer

**File:** `services/api/app/util/dxf_compat.py`

The compatibility layer provides version-aware DXF entity creation:

### Supported Versions

| Version | AC Code | LWPOLYLINE | Notes |
|---------|---------|------------|-------|
| R12 | AC1009 | ❌ | Maximum CAM compatibility ("the genesis") |
| R13 | AC1012 | ✓ | |
| R14 | AC1014 | ✓ | |
| R2000 (R15) | AC1015 | ✓ | |
| R2004 (R16) | AC1018 | ✓ | |
| R2007 (R17) | AC1021 | ✓ | |
| R2010 (R18) | AC1024 | ✓ | Complex geometry support |

### Key Functions

```python
def validate_version(version: str) -> DxfVersion:
    """Validate and normalize version string (e.g., "R15" → "R2000")."""

def supports_lwpolyline(version: DxfVersion) -> bool:
    """Check if version supports LWPOLYLINE entity."""

def create_document(version: DxfVersion = 'R12', setup: bool = False) -> Drawing:
    """Create new DXF document with specified version."""

def add_polyline(msp, points, layer='0', closed=False, version='R12'):
    """Add polyline using version-appropriate entity.
    
    R12: Uses LINE segments
    R13+: Uses LWPOLYLINE
    """

def add_rectangle(msp, x1, y1, x2, y2, layer='0', version='R12'):
    """Add rectangle using version-appropriate entity."""
```

### Usage Pattern

```python
from app.util.dxf_compat import create_document, add_polyline, validate_version

version = validate_version(user_version)
doc = create_document(version)
msp = doc.modelspace()

points = [(0, 0), (100, 0), (100, 50), (0, 50)]
add_polyline(msp, points, layer='BODY', closed=True, version=version)
```

---

## Known Infrastructure Issues

### BLOCKING: DXF Output Standard

> ⚠️ **Status: NOT STARTED**  
> **Priority: Blocking — ranks equal to Smart Guitar first article**

**Problem:** Every DXF generator calls ezdxf directly with inconsistent settings. This caused Fusion 360 to freeze and require a hard reset on `smart_guitar_front_v3.dxf`.

**Required:** Create `services/api/app/cam/dxf_writer.py` — a single central DXF writer that ALL generators call.

**Standards to Enforce:**
| Setting | Value | Reason |
|---------|-------|--------|
| Format | R12 (AC1009) | Maximum CAM compatibility |
| Entities | LINE only | No LWPOLYLINE (Fusion 360 freeze) |
| Headers | Sentinel EXTMIN/EXTMAX (1e+20) | Avoid header population issues |
| Precision | ≤3dp coordinates | Prevent floating-point drift |
| Units | INSUNITS=4 (mm), MEASUREMENT=1 | Metric consistency |
| Layers | Named layers only | No geometry on layer 0 |

**Generators Requiring Refactor:**
- `app/instrument_geometry/bridge/archtop_floating_bridge.py`
- `app/instrument_geometry/soundhole/spiral_geometry.py`
- All body outline and CAM generators using ezdxf directly

**Rule:** No new DXF generator may be built until `dxf_writer.py` exists and existing generators are refactored to use it.

---

## Version History

| Date | Version | Changes |
|------|---------|---------|
| 2026-04-23 | 1.0.0 | Initial documentation |
