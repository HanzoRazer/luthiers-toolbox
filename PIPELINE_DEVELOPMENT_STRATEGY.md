# Luthier's ToolBox - Pipeline Development Strategy

**Document Version**: 1.0  
**Date**: November 3, 2025  
**Status**: Ready for Developer Handoff  
**Project**: CNC Guitar Lutherie CAD/CAM System

---

## Executive Summary

This document provides a unified product development strategy for integrating specialized lutherie calculation pipelines into the Luthier's ToolBox web application. The goal is to create a cohesive system where luthiers can design guitar components, calculate structural properties, generate CAM-ready DXF files, and integrate with CNC workflows.

**Architecture**: Vue 3 + TypeScript frontend → FastAPI + Python backend → Pipeline modules → DXF/G-code export

---

## Project Structure Tree

```
Luthiers ToolBox/
│
├── 📁 client/                          # Vue 3 + Vite Frontend
│   ├── src/
│   │   ├── App.vue                     # Main application component
│   │   ├── main.ts                     # Application entry point
│   │   │
│   │   ├── components/
│   │   │   ├── toolbox/
│   │   │   │   ├── CadCanvas.vue       # [MISSING] CAD design canvas
│   │   │   │   ├── LuthierCalculator.vue # [MISSING] String spacing calculator
│   │   │   │   ├── RosetteDesigner.vue # [EXISTS] Rosette design interface
│   │   │   │   ├── BridgeCalculator.vue # [MISSING] Bridge calculator
│   │   │   │   ├── NeckGenerator.vue   # [MISSING] Neck profile generator
│   │   │   │   ├── FretCalculator.vue  # [MISSING] BenchMuse/FretFind integration
│   │   │   │   ├── GcodeAnalyzer.vue   # [TO CREATE] G-code analysis UI
│   │   │   │   └── HardwareLayout.vue  # [EXISTS] Electronics cavity layout
│   │   │   │
│   │   │   └── common/
│   │   │       ├── FileUpload.vue      # Reusable file upload component
│   │   │       ├── ExportControls.vue  # DXF/JSON export controls
│   │   │       └── ValidationWarnings.vue # Display warnings/errors
│   │   │
│   │   ├── utils/
│   │   │   ├── api.ts                  # TypeScript SDK for backend API
│   │   │   ├── geometry.ts             # Geometry utilities (mm conversions)
│   │   │   └── validators.ts           # Input validation functions
│   │   │
│   │   └── types/
│   │       ├── pipeline.types.ts       # Pipeline request/response types
│   │       ├── geometry.types.ts       # Geometry data structures
│   │       └── gcode.types.ts          # G-code analysis types
│   │
│   ├── package.json                    # Node dependencies
│   ├── vite.config.ts                  # Vite configuration
│   └── tsconfig.json                   # TypeScript configuration
│
├── 📁 server/                          # FastAPI Backend
│   ├── app.py                          # Main FastAPI application
│   ├── requirements.txt                # Python dependencies
│   │
│   ├── pipelines/                      # Specialized calculation modules
│   │   │
│   │   ├── 📁 rosette/                 # [MEDIUM PRIORITY]
│   │   │   ├── rosette_calc.py         # Parametric rosette calculator
│   │   │   ├── rosette_to_dxf.py       # DXF export (R12 format)
│   │   │   ├── rosette_make_gcode.py   # G-code toolpath generation
│   │   │   └── README.md               # Rosette pipeline documentation
│   │   │
│   │   ├── 📁 bracing/                 # [LOW PRIORITY]
│   │   │   ├── bracing_calc.py         # Structural mass estimation
│   │   │   ├── glue_area.py            # Glue surface area calculation
│   │   │   └── README.md               # Bracing pipeline documentation
│   │   │
│   │   ├── 📁 hardware/                # [MEDIUM PRIORITY]
│   │   │   ├── hardware_layout.py      # Electronics cavity calculator
│   │   │   ├── hardware_to_dxf.py      # DXF export for routing
│   │   │   └── README.md               # Hardware pipeline documentation
│   │   │
│   │   ├── 📁 gcode_explainer/         # [HIGH PRIORITY - READY]
│   │   │   ├── gcode_reader.py         # ✅ Enhanced G-code parser
│   │   │   ├── analyze_gcode.py        # [TO CREATE] FastAPI wrapper
│   │   │   ├── explain_gcode_ai.py     # [EXISTS] AI-powered explanations
│   │   │   └── README.md               # G-code pipeline documentation
│   │   │
│   │   ├── 📁 string_spacing/          # [CRITICAL PRIORITY - MISSING]
│   │   │   ├── benchmuse_spacer.py     # BenchMuse StringSpacer port
│   │   │   ├── fretfind_calc.py        # FretFind fret position calculator
│   │   │   ├── string_to_dxf.py        # Export nut/bridge/fret layouts
│   │   │   └── README.md               # String spacing documentation
│   │   │
│   │   ├── 📁 bridge/                  # [HIGH PRIORITY - MISSING]
│   │   │   ├── bridge_calc.py          # Bridge geometry calculator
│   │   │   ├── bridge_to_dxf.py        # DXF export for bridge routing
│   │   │   └── README.md               # Bridge pipeline documentation
│   │   │
│   │   ├── 📁 neck/                    # [MEDIUM PRIORITY - MISSING]
│   │   │   ├── neck_profile.py         # Neck profile generator
│   │   │   ├── neck_to_dxf.py          # Side/top view DXF export
│   │   │   └── README.md               # Neck pipeline documentation
│   │   │
│   │   └── 📁 cad_canvas/              # [LOW PRIORITY - MISSING]
│   │       ├── canvas_processor.py     # Process CAD canvas drawings
│   │       ├── canvas_to_dxf.py        # Generic DXF export
│   │       └── README.md               # CAD canvas documentation
│   │
│   ├── models/                         # Pydantic data models
│   │   ├── pipeline_models.py          # Request/response schemas
│   │   ├── geometry_models.py          # Geometry data structures
│   │   └── export_models.py            # Export format models
│   │
│   ├── utils/
│   │   ├── dxf_helpers.py              # Common DXF operations (ezdxf)
│   │   ├── geometry_helpers.py         # Shapely geometry operations
│   │   └── validation.py               # Input validation utilities
│   │
│   └── poller.py                       # Windows hot-folder monitor
│
├── 📁 configs/                         # Configuration files
│   └── examples/
│       ├── rosette/
│       │   └── example_params.json     # Rosette parameter examples
│       ├── bridge/
│       │   └── example_params.json     # Bridge parameter examples
│       └── string_spacing/
│           └── example_params.json     # String spacing examples
│
├── 📁 docs/                            # Documentation
│   ├── API.md                          # API endpoint documentation
│   ├── PIPELINES.md                    # Pipeline architecture guide
│   ├── DXF_EXPORT.md                   # DXF format specifications
│   └── DEVELOPER_GUIDE.md              # Developer onboarding guide
│
├── 📁 tests/                           # Test files
│   ├── test_gcode_reader.py            # G-code parser tests
│   ├── test_rosette_calc.py            # Rosette calculator tests
│   ├── test_api_endpoints.py           # API integration tests
│   └── fixtures/
│       ├── sample.nc                   # Test G-code files
│       └── sample.dxf                  # Test DXF files
│
├── 📁 MVP Build_10-11-2025/            # [REFERENCE ONLY - DO NOT MODIFY]
│   └── (Feature libraries - extract features from here)
│
├── 📁 MVP Build_1012-2025/             # [REFERENCE ONLY - DO NOT MODIFY]
│   └── (Feature libraries - extract features from here)
│
├── 📁 Lutherier Project/               # [DESIGN ARCHIVES]
│   └── Les Paul_Project/
│       ├── clean_cam_ready_dxf_windows_all_layers.py  # DXF cleaning script
│       └── 09252025/
│           └── FusionSetup_Base_LP_Mach4.json  # Fusion 360 setup
│
├── .github/
│   └── workflows/
│       └── ci.yml                      # CI/CD pipeline
│
├── docker-compose.yml                  # Full stack deployment
├── .gitignore                          # Git ignore rules
└── README.md                           # Project overview

```

---

## Pipeline Priority Matrix

| Priority | Pipeline | Status | Complexity | Dependencies | Deliverables |
|----------|----------|--------|------------|--------------|--------------|
| **CRITICAL** | String Spacing (BenchMuse) | Missing | Medium | None | `benchmuse_spacer.py`, `fretfind_calc.py`, API endpoint, Vue component |
| **HIGH** | G-code Analyzer | 90% Done | Low | None | `analyze_gcode.py` wrapper, `GcodeAnalyzer.vue` |
| **HIGH** | Bridge Calculator | Missing | Medium | String spacing | `bridge_calc.py`, `bridge_to_dxf.py`, API endpoint, Vue component |
| **MEDIUM** | Rosette Designer | Partial | Medium | DXF helpers | Complete integration, test G-code generation |
| **MEDIUM** | Hardware Layout | Partial | Low | DXF helpers | Complete integration, test DXF export |
| **MEDIUM** | Neck Generator | Missing | High | String spacing | `neck_profile.py`, `neck_to_dxf.py`, API endpoint, Vue component |
| **LOW** | CAD Canvas | Missing | High | DXF helpers | `canvas_processor.py`, generic drawing tools |
| **LOW** | Bracing Calculator | Missing | Low | None | `bracing_calc.py`, mass/area calculations |

---

## Code Organization Standards

### 1. Pipeline Module Structure

Each pipeline follows this standard structure:

```
pipelines/<pipeline_name>/
├── <name>_calc.py          # Core calculation logic (pure Python)
├── <name>_to_dxf.py        # DXF export functionality
├── <name>_make_gcode.py    # G-code generation (optional)
├── api_wrapper.py          # FastAPI endpoint wrapper
├── __init__.py             # Package initialization
└── README.md               # Pipeline-specific documentation
```

### 2. Naming Conventions

**Python Files**:
- `snake_case` for all Python files and functions
- Descriptive names: `calculate_fret_positions()` not `calc_fp()`
- Prefix exports: `rosette_to_dxf()`, `bridge_to_dxf()`

**Vue Components**:
- `PascalCase` for component files: `RosetteDesigner.vue`
- Prefix with category: `toolbox/`, `common/`

**API Endpoints**:
- REST-style: `/api/<resource>/<action>`
- Example: `/api/rosette/calculate`, `/api/gcode/analyze`

**Units**:
- **ALL geometry in millimeters (mm)** internally
- Convert at API boundary only if supporting imperial

### 3. Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CLIENT (Vue 3)                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │ User Input   │ -> │ Vue Component│ -> │  API Client  │  │
│  │ (Form/Canvas)│    │ (Validation) │    │  (utils/api) │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
└────────────────────────────────┬────────────────────────────┘
                                 │ HTTP POST /api/<endpoint>
                                 │ Content-Type: application/json
                                 ▼
┌─────────────────────────────────────────────────────────────┐
│                    SERVER (FastAPI)                         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │ API Endpoint │ -> │ Pydantic     │ -> │  Pipeline    │  │
│  │ (app.py)     │    │ Validation   │    │  Module      │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│                                                 │            │
│                                                 ▼            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Pipeline Processing                     │   │
│  │  1. Calculate geometry (pure Python)                 │   │
│  │  2. Generate DXF (ezdxf R12 format)                  │   │
│  │  3. Optional: Generate G-code                        │   │
│  │  4. Return JSON response + file downloads            │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────────────┬────────────────────────────┘
                                 │ JSON Response + Files
                                 ▼
┌─────────────────────────────────────────────────────────────┐
│                     CLIENT (Vue 3)                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │ Display      │ <- │ Process      │ <- │  Response    │  │
│  │ Results      │    │ Response     │    │  Handler     │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## API Endpoint Specifications

### Standard Request/Response Format

**Request Structure**:
```typescript
interface PipelineRequest {
  params: {
    // Pipeline-specific parameters
    [key: string]: number | string | boolean;
  };
  units: "mm" | "inch";  // Always "mm" for internal processing
  export_format?: "dxf" | "json" | "gcode" | "all";
  validate?: boolean;     // Run validation checks
}
```

**Response Structure**:
```typescript
interface PipelineResponse {
  success: boolean;
  data: {
    // Calculated results
    [key: string]: any;
  };
  files?: {
    dxf?: string;      // Base64-encoded DXF file
    gcode?: string;    // Base64-encoded G-code file
    json?: string;     // JSON summary
  };
  warnings?: string[];  // Non-critical issues
  errors?: string[];    // Critical issues
  metadata: {
    pipeline: string;
    version: string;
    timestamp: string;
    processing_time_ms: number;
  };
}
```

### Example API Endpoints

```python
# 1. G-code Analysis (HIGH PRIORITY)
@app.post("/api/gcode/analyze")
async def analyze_gcode(
    file: UploadFile,
    validate: bool = True
) -> GcodeAnalysisResponse:
    """
    Analyze G-code file for CNC machining
    - Parse motions, speeds, coordinates
    - Calculate bounding box and travel distance
    - Run safety validation checks
    - Return JSON summary + warnings
    """
    pass

# 2. String Spacing Calculator (CRITICAL PRIORITY)
@app.post("/api/string-spacing/calculate")
async def calculate_string_spacing(
    request: StringSpacingRequest
) -> StringSpacingResponse:
    """
    Calculate string spacing for nut and bridge
    - BenchMuse algorithm for even/tapered spacing
    - Fret position calculation (FretFind integration)
    - Export DXF with nut/bridge/fret layouts
    """
    pass

# 3. Bridge Calculator (HIGH PRIORITY)
@app.post("/api/bridge/calculate")
async def calculate_bridge(
    request: BridgeRequest
) -> BridgeResponse:
    """
    Calculate bridge geometry and compensation
    - String spacing integration
    - Saddle compensation calculations
    - Export DXF for CNC routing
    """
    pass

# 4. Rosette Designer (MEDIUM PRIORITY)
@app.post("/api/rosette/calculate")
async def calculate_rosette(
    request: RosetteRequest
) -> RosetteResponse:
    """
    Design parametric soundhole rosettes
    - Channel width/depth calculations
    - Purfling ring generation
    - Export DXF + G-code for CNC inlay
    """
    pass

# 5. Neck Profile Generator (MEDIUM PRIORITY)
@app.post("/api/neck/generate")
async def generate_neck(
    request: NeckRequest
) -> NeckResponse:
    """
    Generate neck profile geometry
    - C/D/V/U shape profiles
    - Fret spacing integration
    - Export side/top view DXF
    """
    pass

# 6. Hardware Layout (MEDIUM PRIORITY)
@app.post("/api/hardware/layout")
async def layout_hardware(
    request: HardwareRequest
) -> HardwareResponse:
    """
    Layout electronics cavity geometry
    - Pickup/control/jack placement
    - Export DXF for routing
    """
    pass
```

---

## Development Workflow

### Phase 1: G-code Analyzer Integration (1-2 days)
**Status**: 90% Complete - Enhancement done, needs API wrapper

**Tasks**:
1. ✅ Enhanced `gcode_reader.py` (COMPLETE)
2. ⬜ Create `server/pipelines/gcode_explainer/analyze_gcode.py`
3. ⬜ Add API endpoint to `server/app.py`
4. ⬜ Create `client/src/components/toolbox/GcodeAnalyzer.vue`
5. ⬜ Add file upload and result display
6. ⬜ Test with sample G-code files

**Deliverables**:
- Working G-code upload interface
- Validation warnings display
- JSON/CSV export functionality
- Integration with existing `explain_gcode_ai.py`

### Phase 2: BenchMuse StringSpacer Integration (3-5 days)
**Status**: Critical Priority - Not Started

**Tasks**:
1. ⬜ Extract BenchMuse StringSpacer from MVP builds
2. ⬜ Create `server/pipelines/string_spacing/benchmuse_spacer.py`
3. ⬜ Port FretFind algorithm to `fretfind_calc.py`
4. ⬜ Create DXF export with nut/bridge/fret layouts
5. ⬜ Add API endpoint `/api/string-spacing/calculate`
6. ⬜ Create `client/src/components/toolbox/FretCalculator.vue`
7. ⬜ Test with various scale lengths and string counts

**Deliverables**:
- String spacing calculator (even/tapered)
- Fret position calculator (compensated/straight)
- DXF export with nut/bridge templates
- Vue component with real-time preview

### Phase 3: Bridge Calculator Integration (2-3 days)
**Status**: High Priority - Depends on Phase 2

**Tasks**:
1. ⬜ Extract BridgeCalculator.vue from MVP builds (371 lines)
2. ⬜ Create `server/pipelines/bridge/bridge_calc.py`
3. ⬜ Integrate with string spacing calculations
4. ⬜ Add saddle compensation algorithms
5. ⬜ Create DXF export for bridge routing
6. ⬜ Add API endpoint `/api/bridge/calculate`
7. ⬜ Update Vue component for integration

**Deliverables**:
- Bridge geometry calculator
- String spacing integration
- Saddle compensation
- DXF export for CNC routing

### Phase 4: Rosette & Hardware Completion (2-3 days)
**Status**: Medium Priority - Partial implementations exist

**Tasks**:
1. ⬜ Complete rosette pipeline integration
2. ⬜ Test rosette G-code generation
3. ⬜ Complete hardware layout integration
4. ⬜ Create unified export system
5. ⬜ Test DXF imports in Fusion 360/VCarve

**Deliverables**:
- Complete rosette designer
- Complete hardware layout tool
- Tested DXF exports
- G-code generation working

### Phase 5: Neck Generator & CAD Canvas (5-7 days)
**Status**: Medium/Low Priority - Complex features

**Tasks**:
1. ⬜ Design neck profile algorithm (C/D/V/U shapes)
2. ⬜ Create CAD canvas with drawing tools
3. ⬜ Implement generic DXF export
4. ⬜ Add Vue components
5. ⬜ Integration testing

**Deliverables**:
- Neck profile generator
- CAD canvas with drawing tools
- Generic DXF export system

---

## Technology Stack

### Frontend
- **Framework**: Vue 3.4+ with Composition API (`<script setup>`)
- **Build Tool**: Vite 5.0+
- **Language**: TypeScript 5.0+
- **State Management**: Pinia (if needed for complex state)
- **HTTP Client**: Fetch API with typed wrappers
- **UI Components**: Native HTML5 + custom components

### Backend
- **Framework**: FastAPI 0.104+
- **Language**: Python 3.11+
- **Data Validation**: Pydantic 2.0+
- **Server**: Uvicorn (ASGI)
- **DXF Library**: ezdxf 1.1+ (R12 format)
- **Geometry**: Shapely 2.0+ (unions, intersections, polygons)

### Development Tools
- **Linting**: Ruff (Python), ESLint (TypeScript)
- **Formatting**: Black (Python), Prettier (TypeScript)
- **Testing**: Pytest (Python), Vitest (TypeScript)
- **CI/CD**: GitHub Actions

---

## Code Templates

### 1. Pipeline Calculator Module Template

```python
# server/pipelines/<pipeline_name>/<name>_calc.py
"""
<Pipeline Name> Calculator for Luthier's ToolBox

Calculates <description> for guitar lutherie applications.

Usage:
    from pipelines.<pipeline_name> import calculate_<name>
    
    result = calculate_<name>(params)
"""

from dataclasses import dataclass
from typing import List, Tuple, Optional


@dataclass
class <Name>Params:
    """Input parameters for <name> calculation."""
    # Define parameters here (all in mm)
    param1_mm: float
    param2_mm: float
    # ... more parameters


@dataclass
class <Name>Result:
    """Output results from <name> calculation."""
    # Define results here
    calculated_value: float
    coordinates: List[Tuple[float, float]]
    warnings: List[str]
    metadata: dict


def validate_params(params: <Name>Params) -> List[str]:
    """
    Validate input parameters.
    
    Returns:
        List of warning messages (empty if all valid)
    """
    warnings = []
    
    if params.param1_mm <= 0:
        warnings.append("param1 must be positive")
    
    # Add more validation
    
    return warnings


def calculate_<name>(params: <Name>Params) -> <Name>Result:
    """
    Main calculation function.
    
    Args:
        params: Input parameters (all in mm)
    
    Returns:
        Calculation results
    
    Raises:
        ValueError: If parameters are invalid
    """
    # Validate inputs
    warnings = validate_params(params)
    
    # Perform calculations (all in mm)
    # ...
    
    # Return results
    return <Name>Result(
        calculated_value=0.0,
        coordinates=[],
        warnings=warnings,
        metadata={"units": "mm"}
    )


if __name__ == "__main__":
    # CLI for standalone testing
    import sys
    import json
    
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <params.json>")
        sys.exit(1)
    
    with open(sys.argv[1]) as f:
        data = json.load(f)
    
    params = <Name>Params(**data)
    result = calculate_<name>(params)
    
    print(json.dumps({
        "value": result.calculated_value,
        "warnings": result.warnings
    }, indent=2))
```

### 2. DXF Export Module Template

```python
# server/pipelines/<pipeline_name>/<name>_to_dxf.py
"""
DXF export functionality for <Pipeline Name>

Exports calculation results to R12 DXF format for CAM software.
"""

import ezdxf
from ezdxf.enums import TextEntityAlignment
from pathlib import Path
from typing import List, Tuple


def create_dxf_from_<name>(
    coordinates: List[Tuple[float, float]],
    output_path: Path,
    layer_name: str = "GEOMETRY",
    include_labels: bool = True
) -> Path:
    """
    Create R12 DXF file from calculation results.
    
    Args:
        coordinates: List of (x, y) points in mm
        output_path: Output file path
        layer_name: DXF layer name
        include_labels: Add dimension labels
    
    Returns:
        Path to created DXF file
    """
    # Create R12 DXF (maximum compatibility)
    doc = ezdxf.new("R12")
    msp = doc.modelspace()
    
    # Create layer
    doc.layers.new(name=layer_name, dxfattribs={"color": 7})
    
    # Add closed polyline (required for CAM)
    if len(coordinates) >= 2:
        points = coordinates + [coordinates[0]]  # Close the path
        msp.add_lwpolyline(
            points,
            dxfattribs={
                "layer": layer_name,
                "closed": True
            }
        )
    
    # Add labels if requested
    if include_labels:
        # Add title
        msp.add_text(
            "Luthier's ToolBox - <Pipeline Name>",
            dxfattribs={
                "layer": layer_name,
                "height": 2.5,
                "insert": (10, 10),
            }
        )
    
    # Save DXF
    doc.saveas(output_path)
    return output_path


if __name__ == "__main__":
    # CLI for standalone testing
    import sys
    import json
    
    if len(sys.argv) < 3:
        print(f"Usage: python {sys.argv[0]} <input.json> <output.dxf>")
        sys.exit(1)
    
    with open(sys.argv[1]) as f:
        data = json.load(f)
    
    coordinates = [(p["x"], p["y"]) for p in data["coordinates"]]
    create_dxf_from_<name>(coordinates, Path(sys.argv[2]))
    print(f"✅ DXF created: {sys.argv[2]}")
```

### 3. FastAPI Endpoint Template

```python
# server/pipelines/<pipeline_name>/api_wrapper.py
"""
FastAPI endpoint wrapper for <Pipeline Name>
"""

from fastapi import APIRouter, HTTPException, File, UploadFile
from pydantic import BaseModel, Field
from typing import List, Optional
import tempfile
from pathlib import Path

from .<name>_calc import calculate_<name>, <Name>Params, <Name>Result
from .<name>_to_dxf import create_dxf_from_<name>


router = APIRouter(prefix="/api/<name>", tags=["<Pipeline Name>"])


class <Name>Request(BaseModel):
    """API request model for <name> calculation."""
    param1_mm: float = Field(..., gt=0, description="Parameter 1 in millimeters")
    param2_mm: float = Field(..., gt=0, description="Parameter 2 in millimeters")
    export_dxf: bool = Field(True, description="Generate DXF export")
    validate: bool = Field(True, description="Run validation checks")


class <Name>Response(BaseModel):
    """API response model for <name> calculation."""
    success: bool
    calculated_value: float
    coordinates: List[dict]  # [{"x": float, "y": float}]
    warnings: List[str]
    dxf_file: Optional[str] = None  # Base64-encoded if requested
    metadata: dict


@router.post("/calculate", response_model=<Name>Response)
async def calculate_endpoint(request: <Name>Request):
    """
    Calculate <name> and optionally export DXF.
    
    Returns:
        Calculation results and optional DXF file
    """
    try:
        # Convert request to params
        params = <Name>Params(
            param1_mm=request.param1_mm,
            param2_mm=request.param2_mm
        )
        
        # Run calculation
        result = calculate_<name>(params)
        
        # Generate DXF if requested
        dxf_data = None
        if request.export_dxf:
            with tempfile.NamedTemporaryFile(suffix=".dxf", delete=False) as tmp:
                dxf_path = create_dxf_from_<name>(
                    result.coordinates,
                    Path(tmp.name)
                )
                # Read and encode
                with open(dxf_path, "rb") as f:
                    import base64
                    dxf_data = base64.b64encode(f.read()).decode()
                # Cleanup
                dxf_path.unlink()
        
        # Build response
        return <Name>Response(
            success=True,
            calculated_value=result.calculated_value,
            coordinates=[{"x": x, "y": y} for x, y in result.coordinates],
            warnings=result.warnings,
            dxf_file=dxf_data,
            metadata=result.metadata
        )
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### 4. Vue Component Template

```vue
<!-- client/src/components/toolbox/<Name>Calculator.vue -->
<template>
  <div class="<name>-calculator">
    <h2><Pipeline Name> Calculator</h2>
    
    <!-- Input Form -->
    <form @submit.prevent="calculate">
      <div class="form-group">
        <label for="param1">Parameter 1 (mm):</label>
        <input
          id="param1"
          v-model.number="params.param1_mm"
          type="number"
          step="0.1"
          min="0"
          required
        />
      </div>
      
      <div class="form-group">
        <label for="param2">Parameter 2 (mm):</label>
        <input
          id="param2"
          v-model.number="params.param2_mm"
          type="number"
          step="0.1"
          min="0"
          required
        />
      </div>
      
      <div class="form-actions">
        <button type="submit" :disabled="loading">
          {{ loading ? 'Calculating...' : 'Calculate' }}
        </button>
        <button type="button" @click="exportDxf" :disabled="!result">
          Export DXF
        </button>
      </div>
    </form>
    
    <!-- Results Display -->
    <div v-if="result" class="results">
      <h3>Results</h3>
      <p>Calculated Value: {{ result.calculated_value.toFixed(3) }} mm</p>
      
      <!-- Preview Canvas -->
      <canvas ref="previewCanvas" width="400" height="400"></canvas>
      
      <!-- Warnings -->
      <div v-if="result.warnings.length" class="warnings">
        <h4>⚠️ Warnings</h4>
        <ul>
          <li v-for="(warning, idx) in result.warnings" :key="idx">
            {{ warning }}
          </li>
        </ul>
      </div>
    </div>
    
    <!-- Error Display -->
    <div v-if="error" class="error">
      <strong>Error:</strong> {{ error }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { calculate<Name>, exportDxf<Name> } from '@/utils/api'

// State
const params = ref({
  param1_mm: 100,
  param2_mm: 50
})
const result = ref<any>(null)
const loading = ref(false)
const error = ref<string | null>(null)
const previewCanvas = ref<HTMLCanvasElement | null>(null)

// Calculate
async function calculate() {
  loading.value = true
  error.value = null
  
  try {
    result.value = await calculate<Name>(params.value)
    drawPreview()
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

// Draw preview
function drawPreview() {
  if (!previewCanvas.value || !result.value) return
  
  const ctx = previewCanvas.value.getContext('2d')
  if (!ctx) return
  
  // Clear canvas
  ctx.clearRect(0, 0, 400, 400)
  
  // Draw coordinates
  ctx.strokeStyle = '#0066cc'
  ctx.lineWidth = 2
  ctx.beginPath()
  
  result.value.coordinates.forEach((point: {x: number, y: number}, idx: number) => {
    const x = point.x * 2 + 50  // Scale and offset
    const y = point.y * 2 + 50
    
    if (idx === 0) {
      ctx.moveTo(x, y)
    } else {
      ctx.lineTo(x, y)
    }
  })
  
  ctx.stroke()
}

// Export DXF
async function exportDxf() {
  if (!result.value?.dxf_file) return
  
  try {
    const blob = await exportDxf<Name>(result.value.dxf_file)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = '<name>_export.dxf'
    a.click()
    URL.revokeObjectURL(url)
  } catch (e: any) {
    error.value = e.message
  }
}

onMounted(() => {
  // Auto-calculate on mount
  calculate()
})
</script>

<style scoped>
.<name>-calculator {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.form-group {
  margin-bottom: 15px;
}

label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}

input[type="number"] {
  width: 100%;
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
}

.form-actions {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}

button {
  padding: 10px 20px;
  background: #0066cc;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

button:hover:not(:disabled) {
  background: #0052a3;
}

button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.results {
  margin-top: 30px;
  padding: 20px;
  background: #f5f5f5;
  border-radius: 4px;
}

canvas {
  border: 1px solid #ccc;
  margin: 20px 0;
}

.warnings {
  margin-top: 20px;
  padding: 15px;
  background: #fff3cd;
  border-left: 4px solid #ffc107;
}

.error {
  margin-top: 20px;
  padding: 15px;
  background: #f8d7da;
  border-left: 4px solid #dc3545;
  color: #721c24;
}
</style>
```

---

## Testing Strategy

### 1. Unit Tests (Python)

```python
# tests/test_<name>_calc.py
import pytest
from server.pipelines.<name>.<name>_calc import calculate_<name>, <Name>Params


def test_basic_calculation():
    """Test basic calculation with valid params."""
    params = <Name>Params(param1_mm=100, param2_mm=50)
    result = calculate_<name>(params)
    
    assert result.calculated_value > 0
    assert len(result.warnings) == 0


def test_validation_warnings():
    """Test that validation warnings are generated."""
    params = <Name>Params(param1_mm=-10, param2_mm=50)
    result = calculate_<name>(params)
    
    assert len(result.warnings) > 0


def test_edge_cases():
    """Test edge case inputs."""
    # Zero values
    params = <Name>Params(param1_mm=0, param2_mm=50)
    result = calculate_<name>(params)
    assert "must be positive" in " ".join(result.warnings)
    
    # Very large values
    params = <Name>Params(param1_mm=10000, param2_mm=50)
    result = calculate_<name>(params)
    # Should complete without error
```

### 2. Integration Tests (API)

```python
# tests/test_api_endpoints.py
from fastapi.testclient import TestClient
from server.app import app

client = TestClient(app)


def test_<name>_calculate_endpoint():
    """Test <name> calculation API endpoint."""
    response = client.post("/api/<name>/calculate", json={
        "param1_mm": 100,
        "param2_mm": 50,
        "export_dxf": True,
        "validate": True
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "calculated_value" in data
    assert "coordinates" in data


def test_invalid_params():
    """Test API with invalid parameters."""
    response = client.post("/api/<name>/calculate", json={
        "param1_mm": -10,  # Invalid
        "param2_mm": 50
    })
    
    assert response.status_code == 422  # Validation error
```

### 3. End-to-End Tests (Vue)

```typescript
// tests/e2e/<name>_calculator.spec.ts
import { test, expect } from '@playwright/test'

test('calculate <name> and export DXF', async ({ page }) => {
  await page.goto('http://localhost:5173')
  
  // Navigate to calculator
  await page.click('text=<Pipeline Name>')
  
  // Fill form
  await page.fill('#param1', '100')
  await page.fill('#param2', '50')
  
  // Calculate
  await page.click('button:has-text("Calculate")')
  
  // Wait for results
  await expect(page.locator('.results')).toBeVisible()
  
  // Export DXF
  const downloadPromise = page.waitForEvent('download')
  await page.click('button:has-text("Export DXF")')
  const download = await downloadPromise
  
  expect(download.suggestedFilename()).toContain('.dxf')
})
```

---

## Deployment Strategy

### Development Environment

```powershell
# Setup script (setup_dev.ps1)

# Server setup
cd server
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Client setup
cd ../client
npm install

# Start services
Start-Process pwsh -ArgumentList "-NoExit", "-Command", "cd server; .\.venv\Scripts\Activate.ps1; uvicorn app:app --reload --port 8000"
Start-Process pwsh -ArgumentList "-NoExit", "-Command", "cd client; npm run dev"

Write-Host "✅ Development environment started"
Write-Host "   API:    http://localhost:8000"
Write-Host "   Client: http://localhost:5173"
```

### Production Deployment (Docker)

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build:
      context: ./server
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - PYTHONUNBUFFERED=1
      - LOG_LEVEL=info
    volumes:
      - ./server:/app
      - dxf_exports:/exports
    restart: unless-stopped

  client:
    build:
      context: ./client
      dockerfile: Dockerfile
    ports:
      - "8080:80"
    depends_on:
      - api
    restart: unless-stopped

volumes:
  dxf_exports:
```

---

## Success Metrics

### Technical Metrics
- ✅ All API endpoints respond < 500ms
- ✅ DXF exports import cleanly into Fusion 360/VCarve
- ✅ Zero runtime errors in production
- ✅ 90%+ test coverage
- ✅ All calculations accurate to 0.01mm

### User Metrics
- ✅ Luthiers can complete full guitar layout in < 30 minutes
- ✅ DXF files CNC-ready without manual cleanup
- ✅ G-code validation catches safety issues before machining
- ✅ Positive feedback from beta testers

---

## Developer Onboarding Checklist

**New Developer Setup** (Allow 2-4 hours):

- [ ] Clone repository
- [ ] Install Python 3.11+ and Node.js 18+
- [ ] Run `setup_dev.ps1` to start services
- [ ] Read `DEVELOPER_GUIDE.md`
- [ ] Review pipeline architecture (this document)
- [ ] Complete "Hello World" pipeline exercise
- [ ] Submit first PR (fix a typo or add a test)

**First Week Tasks**:
- [ ] Implement one small pipeline (e.g., bracing calculator)
- [ ] Write unit tests for new code
- [ ] Create Vue component for pipeline
- [ ] Document API endpoint
- [ ] Present work to team

---

## Support & Resources

### Documentation
- **API Docs**: http://localhost:8000/docs (FastAPI auto-generated)
- **Project Wiki**: GitHub Wiki (design decisions, tutorials)
- **Issue Tracker**: GitHub Issues (bugs, feature requests)

### Communication
- **Slack/Discord**: #luthiers-toolbox channel
- **Email**: dev@luthery-toolbox.com
- **Code Reviews**: GitHub Pull Requests

### Reference Materials
- **DXF Specification**: Autodesk DXF R12 format guide
- **G-code Reference**: Fanuc G-code programming manual
- **Lutherie Math**: Dan Erlewine's guitar building books
- **FretFind**: Ekips FretFind calculator documentation

---

## License & Credits

**License**: MIT License (open source)

**Credits**:
- BenchMuse StringSpacer algorithm
- FretFind fret calculator
- ezdxf library (Manfred Moitzi)
- FastAPI framework (Sebastián Ramírez)
- Vue.js framework (Evan You)

---

**Document End**

**Next Steps**: Review with development team, assign tasks by priority, begin Phase 1 implementation.
