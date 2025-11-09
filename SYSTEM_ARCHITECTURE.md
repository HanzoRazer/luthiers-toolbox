# Luthier's ToolBox - System Architecture Diagram

**Version**: 1.0  
**Date**: November 3, 2025  
**Purpose**: Visual representation of system components and data flow

---

## High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         END USERS (Luthiers)                        │
│                    Access via Web Browser                           │
└────────────────────────────┬────────────────────────────────────────┘
                             │ HTTPS
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    FRONTEND (Vue 3 + TypeScript)                    │
│                   Served by Vite Dev / Nginx                        │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │                    Vue Components                           │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐       │   │
│  │  │   Rosette   │  │   Bridge    │  │  G-code      │  ...  │   │
│  │  │  Designer   │  │  Calculator │  │  Analyzer    │       │   │
│  │  └─────────────┘  └─────────────┘  └──────────────┘       │   │
│  │                                                             │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐       │   │
│  │  │   String    │  │    Neck     │  │   Hardware   │  ...  │   │
│  │  │  Spacing    │  │  Generator  │  │   Layout     │       │   │
│  │  └─────────────┘  └─────────────┘  └──────────────┘       │   │
│  └────────────────────────────────────────────────────────────┘   │
│                             │                                       │
│                             ▼                                       │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │              API Client Layer (utils/api.ts)                │   │
│  │  • Type-safe API calls                                      │   │
│  │  • Error handling                                           │   │
│  │  • File upload/download                                     │   │
│  └────────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────────┘
                             │ REST API (JSON)
                             │ POST /api/<pipeline>/calculate
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI + Python)                       │
│                         Port 8000                                   │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │                    FastAPI Application                      │   │
│  │                        (app.py)                             │   │
│  │  ┌──────────────────────────────────────────────────┐      │   │
│  │  │         API Endpoints                             │      │   │
│  │  │  /api/rosette/calculate                           │      │   │
│  │  │  /api/bridge/calculate                            │      │   │
│  │  │  /api/string-spacing/calculate                    │      │   │
│  │  │  /api/gcode/analyze                               │      │   │
│  │  │  /api/neck/generate                               │      │   │
│  │  │  /api/hardware/layout                             │      │   │
│  │  └──────────────────────────────────────────────────┘      │   │
│  │                        │                                    │   │
│  │                        ▼                                    │   │
│  │  ┌──────────────────────────────────────────────────┐      │   │
│  │  │         Pydantic Validation Layer                 │      │   │
│  │  │  • Request validation                             │      │   │
│  │  │  • Type checking                                  │      │   │
│  │  │  • Unit enforcement (mm only)                     │      │   │
│  │  └──────────────────────────────────────────────────┘      │   │
│  └────────────────────────────────────────────────────────────┘   │
│                             │                                       │
│                             ▼                                       │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │              Pipeline Orchestration Layer                   │   │
│  │  • Route to correct pipeline                                │   │
│  │  • Handle file uploads                                      │   │
│  │  • Coordinate multi-step operations                         │   │
│  └────────────────────────────────────────────────────────────┘   │
│                             │                                       │
│                             ▼                                       │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │                    Pipeline Modules                         │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐            │   │
│  │  │  Rosette   │  │   Bridge   │  │  G-code    │   ...      │   │
│  │  │  Pipeline  │  │  Pipeline  │  │  Explainer │            │   │
│  │  └────────────┘  └────────────┘  └────────────┘            │   │
│  │         │               │               │                   │   │
│  │         ▼               ▼               ▼                   │   │
│  │  [  Calculations  ] [  Geometry  ] [  Parsing  ]           │   │
│  │         │               │               │                   │   │
│  │         ▼               ▼               ▼                   │   │
│  │  [  DXF Export  ] [ DXF Export ] [ JSON Export ]           │   │
│  │         │               │               │                   │   │
│  │         ▼               ▼               ▼                   │   │
│  │  [ G-code Gen ] [  Validation ] [  Analysis  ]             │   │
│  └────────────────────────────────────────────────────────────┘   │
│                             │                                       │
│                             ▼                                       │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │                 Utility Libraries                           │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │   │
│  │  │ DXF Helpers  │  │   Geometry   │  │  Validation  │     │   │
│  │  │  (ezdxf)     │  │  (shapely)   │  │   Helpers    │     │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘     │   │
│  └────────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        OUTPUT FILES                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │  DXF Files   │  │  G-code      │  │  JSON        │             │
│  │  (R12 CAM)   │  │  (CNC)       │  │  (Summary)   │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
│         │                 │                 │                       │
│         ▼                 ▼                 ▼                       │
│  [ Fusion 360 ]    [ Mach4 CNC ]     [ Archive ]                  │
│  [ VCarve Pro ]    [ LinuxCNC  ]                                   │
│  [ CAMotics   ]    [ Masso G3  ]                                   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Pipeline Module Architecture

Each pipeline follows this internal structure:

```
pipelines/<pipeline_name>/
│
├── <name>_calc.py              # Core Calculation Logic
│   ┌─────────────────────────────────────────────┐
│   │  Input: Parameters (Pydantic model)         │
│   │         - All values in mm                  │
│   │         - Validated ranges                  │
│   ├─────────────────────────────────────────────┤
│   │  Process:                                   │
│   │    1. Validate parameters                   │
│   │    2. Perform calculations                  │
│   │    3. Generate coordinates                  │
│   │    4. Calculate metadata                    │
│   ├─────────────────────────────────────────────┤
│   │  Output: Results (dataclass)                │
│   │         - Calculated values                 │
│   │         - Coordinate arrays                 │
│   │         - Warnings list                     │
│   │         - Metadata dict                     │
│   └─────────────────────────────────────────────┘
│                     │
│                     ▼
├── <name>_to_dxf.py            # DXF Export
│   ┌─────────────────────────────────────────────┐
│   │  Input: Calculation results                 │
│   ├─────────────────────────────────────────────┤
│   │  Process:                                   │
│   │    1. Create R12 DXF document               │
│   │    2. Add layers (GEOMETRY, TEXT, etc.)     │
│   │    3. Create closed polylines               │
│   │    4. Add dimensions/labels                 │
│   │    5. Optimize for CAM                      │
│   ├─────────────────────────────────────────────┤
│   │  Output: DXF file (R12 format)              │
│   │         - Closed polylines only             │
│   │         - Organized layers                  │
│   │         - CAM-ready geometry                │
│   └─────────────────────────────────────────────┘
│                     │
│                     ▼
├── <name>_make_gcode.py        # G-code Generation (Optional)
│   ┌─────────────────────────────────────────────┐
│   │  Input: DXF file or coordinates             │
│   ├─────────────────────────────────────────────┤
│   │  Process:                                   │
│   │    1. Parse geometry                        │
│   │    2. Generate toolpaths                    │
│   │    3. Apply feeds/speeds                    │
│   │    4. Add safety moves                      │
│   │    5. Optimize path order                   │
│   ├─────────────────────────────────────────────┤
│   │  Output: G-code file (.nc)                  │
│   │         - Fanuc dialect                     │
│   │         - Safety validated                  │
│   │         - CNC-ready                         │
│   └─────────────────────────────────────────────┘
│                     │
│                     ▼
└── api_wrapper.py              # FastAPI Integration
    ┌─────────────────────────────────────────────┐
    │  1. Receive HTTP POST request               │
    │  2. Validate with Pydantic                  │
    │  3. Call calculation module                 │
    │  4. Generate exports (DXF/G-code)           │
    │  5. Return JSON response + files            │
    └─────────────────────────────────────────────┘
```

---

## Data Flow Diagram

### Example: String Spacing Calculation

```
┌──────────────────────────────────────────────────────────────────┐
│  USER INPUT (Vue Component)                                      │
│  ┌────────────────────────────────────────────────────────┐     │
│  │  Scale Length:      648 mm                             │     │
│  │  String Count:      6                                  │     │
│  │  Nut Width:         43 mm                              │     │
│  │  Bridge Width:      54 mm                              │     │
│  │  Spacing Type:      Tapered                            │     │
│  │  Fret Count:        22                                 │     │
│  └────────────────────────────────────────────────────────┘     │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             │ POST /api/string-spacing/calculate
                             │ { scale_length_mm: 648, ... }
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│  PYDANTIC VALIDATION                                             │
│  ┌────────────────────────────────────────────────────────┐     │
│  │  ✓ scale_length_mm > 0                                 │     │
│  │  ✓ string_count in [4, 5, 6, 7, 8, 12]                │     │
│  │  ✓ nut_width_mm < bridge_width_mm                      │     │
│  │  ✓ spacing_type in ["even", "tapered"]                │     │
│  └────────────────────────────────────────────────────────┘     │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│  BENCHMUSE SPACER CALCULATION                                    │
│  ┌────────────────────────────────────────────────────────┐     │
│  │  1. Calculate nut string positions                     │     │
│  │     - E: 3.5mm, A: 11.1mm, D: 18.7mm, ...             │     │
│  │                                                         │     │
│  │  2. Calculate bridge string positions                  │     │
│  │     - E: 4.5mm, A: 13.5mm, D: 22.5mm, ...             │     │
│  │                                                         │     │
│  │  3. Validate spacing (no overlaps)                     │     │
│  └────────────────────────────────────────────────────────┘     │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│  FRETFIND CALCULATION                                            │
│  ┌────────────────────────────────────────────────────────┐     │
│  │  For n = 0 to 22:                                      │     │
│  │    fret_distance[n] = scale_length -                   │     │
│  │                       (scale_length / 2^(n/12))        │     │
│  │                                                         │     │
│  │  Fret 1:  36.3mm from nut                              │     │
│  │  Fret 12: 324.0mm from nut (octave)                    │     │
│  │  Fret 22: 551.5mm from nut                             │     │
│  └────────────────────────────────────────────────────────┘     │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│  DXF GENERATION (ezdxf)                                          │
│  ┌────────────────────────────────────────────────────────┐     │
│  │  Layer: NUT                                            │     │
│  │    - Nut outline (43mm x 6mm)                          │     │
│  │    - String slot positions (6 lines)                   │     │
│  │                                                         │     │
│  │  Layer: BRIDGE                                         │     │
│  │    - Bridge outline (54mm x 12mm)                      │     │
│  │    - String hole positions (6 circles)                 │     │
│  │                                                         │     │
│  │  Layer: FRETS                                          │     │
│  │    - 22 fret slot lines across fingerboard             │     │
│  │    - Labeled with distances                            │     │
│  │                                                         │     │
│  │  Layer: DIMENSIONS                                     │     │
│  │    - Scale length dimension line                       │     │
│  │    - String spacing annotations                        │     │
│  └────────────────────────────────────────────────────────┘     │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│  API RESPONSE                                                    │
│  ┌────────────────────────────────────────────────────────┐     │
│  │  {                                                      │     │
│  │    "success": true,                                     │     │
│  │    "nut_positions_mm": [3.5, 11.1, 18.7, ...],         │     │
│  │    "bridge_positions_mm": [4.5, 13.5, 22.5, ...],      │     │
│  │    "fret_positions_mm": [36.3, 70.3, ..., 551.5],      │     │
│  │    "warnings": [],                                      │     │
│  │    "dxf_file": "UEsDBBQAAAAIAA...",  // Base64         │     │
│  │    "metadata": {                                        │     │
│  │      "pipeline": "string_spacing",                      │     │
│  │      "version": "1.0",                                  │     │
│  │      "processing_time_ms": 45                           │     │
│  │    }                                                    │     │
│  │  }                                                      │     │
│  └────────────────────────────────────────────────────────┘     │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│  FRONTEND DISPLAY                                                │
│  ┌────────────────────────────────────────────────────────┐     │
│  │  ✓ Calculation complete in 45ms                        │     │
│  │                                                         │     │
│  │  Nut Spacing:    3.5, 11.1, 18.7, 26.3, 33.9, 41.5mm  │     │
│  │  Bridge Spacing: 4.5, 13.5, 22.5, 31.5, 40.5, 49.5mm  │     │
│  │                                                         │     │
│  │  [Canvas Preview: Shows nut, bridge, frets]            │     │
│  │                                                         │     │
│  │  [Download DXF] [Download JSON] [Print Template]       │     │
│  └────────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────────┘
```

---

## Error Handling Flow

```
┌──────────────────────────────────────────────────────────────────┐
│  REQUEST RECEIVED                                                │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │  Valid JSON?   │
                    └───────┬────────┘
                            │
            ┌───────────────┴───────────────┐
            │ NO                            │ YES
            ▼                               ▼
    ┌───────────────┐           ┌─────────────────────┐
    │  Return 400   │           │ Pydantic Validation │
    │  Bad Request  │           └──────────┬──────────┘
    └───────────────┘                      │
                                           │
                              ┌────────────┴────────────┐
                              │ Valid Parameters?       │
                              └────────┬────────────────┘
                                       │
                       ┌───────────────┴───────────────┐
                       │ NO                            │ YES
                       ▼                               ▼
               ┌───────────────┐           ┌─────────────────────┐
               │  Return 422   │           │  Run Calculation    │
               │  Validation   │           └──────────┬──────────┘
               │  Error        │                      │
               └───────────────┘                      │
                                         ┌────────────┴────────────┐
                                         │ Calculation Success?    │
                                         └────────┬────────────────┘
                                                  │
                                  ┌───────────────┴───────────────┐
                                  │ NO                            │ YES
                                  ▼                               ▼
                          ┌───────────────┐           ┌─────────────────────┐
                          │  Return 500   │           │  Generate Exports   │
                          │  Server Error │           └──────────┬──────────┘
                          │  (with logs)  │                      │
                          └───────────────┘                      │
                                                    ┌────────────┴────────────┐
                                                    │ Export Success?         │
                                                    └────────┬────────────────┘
                                                             │
                                             ┌───────────────┴───────────────┐
                                             │ NO                            │ YES
                                             ▼                               ▼
                                     ┌───────────────┐           ┌─────────────────────┐
                                     │  Return 500   │           │  Return 200 OK      │
                                     │  Export Error │           │  + Response JSON    │
                                     └───────────────┘           │  + Files (Base64)   │
                                                                 └─────────────────────┘
```

---

## Technology Stack Layers

```
┌─────────────────────────────────────────────────────────────────┐
│  PRESENTATION LAYER                                             │
│  ┌───────────────────────────────────────────────────────┐     │
│  │  HTML5 + CSS3 + TypeScript                            │     │
│  │  • Vue 3 Composition API                              │     │
│  │  • Reactive data binding                              │     │
│  │  • Component-based architecture                       │     │
│  └───────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  API LAYER                                                      │
│  ┌───────────────────────────────────────────────────────┐     │
│  │  REST API (JSON over HTTPS)                           │     │
│  │  • FastAPI framework                                  │     │
│  │  • Pydantic data validation                           │     │
│  │  • Auto-generated OpenAPI docs                        │     │
│  └───────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  BUSINESS LOGIC LAYER                                           │
│  ┌───────────────────────────────────────────────────────┐     │
│  │  Pipeline Modules (Pure Python)                       │     │
│  │  • BenchMuse StringSpacer                             │     │
│  │  • FretFind Calculator                                │     │
│  │  • Bridge Calculator                                  │     │
│  │  • Rosette Designer                                   │     │
│  │  • G-code Analyzer                                    │     │
│  │  • Neck Generator                                     │     │
│  └───────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  DATA PROCESSING LAYER                                          │
│  ┌───────────────────────────────────────────────────────┐     │
│  │  Geometry & File Processing                           │     │
│  │  • ezdxf (DXF read/write)                             │     │
│  │  • Shapely (geometric operations)                     │     │
│  │  • NumPy (mathematical calculations)                  │     │
│  └───────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  OUTPUT LAYER                                                   │
│  ┌───────────────────────────────────────────────────────┐     │
│  │  File Formats                                         │     │
│  │  • DXF R12 (CAM software)                             │     │
│  │  • G-code (CNC machines)                              │     │
│  │  • JSON (data interchange)                            │     │
│  │  • CSV (motion logs)                                  │     │
│  └───────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Deployment Architecture

### Development Environment

```
┌────────────────────────────────────────────────────────────┐
│  Developer Workstation (Windows/Mac/Linux)                 │
│                                                             │
│  ┌──────────────────────┐    ┌──────────────────────┐     │
│  │  Terminal 1          │    │  Terminal 2          │     │
│  │                      │    │                      │     │
│  │  cd server           │    │  cd client           │     │
│  │  .venv/bin/activate  │    │  npm run dev         │     │
│  │  uvicorn app:app     │    │                      │     │
│  │    --reload          │    │  ➜ Local: ...5173    │     │
│  │                      │    │                      │     │
│  │  ➜ ...localhost:8000 │    │                      │     │
│  └──────────────────────┘    └──────────────────────┘     │
│                                                             │
│  Browser: http://localhost:5173 (proxies API to :8000)    │
└────────────────────────────────────────────────────────────┘
```

### Production Environment

```
┌─────────────────────────────────────────────────────────────────┐
│  Cloud Server / VPS (Ubuntu Linux)                              │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Nginx (Reverse Proxy)                                 │    │
│  │  Port 80/443                                           │    │
│  │                                                         │    │
│  │  /          → Static files (Vue build)                 │    │
│  │  /api/*     → Proxy to FastAPI (:8000)                 │    │
│  └─────────────────────┬──────────────────────────────────┘    │
│                        │                                        │
│         ┌──────────────┴──────────────┐                        │
│         │                             │                        │
│         ▼                             ▼                        │
│  ┌──────────────┐            ┌──────────────────┐             │
│  │  Vue App     │            │  FastAPI         │             │
│  │  (Static)    │            │  (uvicorn)       │             │
│  │  /var/www/   │            │  Port 8000       │             │
│  │  ltb/dist/   │            │  systemd service │             │
│  └──────────────┘            └──────────────────┘             │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  File Storage                                          │    │
│  │  /var/ltb/exports/     ← Generated DXF/G-code files    │    │
│  │  /var/ltb/uploads/     ← User-uploaded files           │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### Docker Deployment

```
┌─────────────────────────────────────────────────────────────────┐
│  Docker Host                                                     │
│                                                                  │
│  docker-compose.yml                                              │
│  │                                                               │
│  ├─> Service: api                                                │
│  │   ┌────────────────────────────────────────────────────┐    │
│  │   │  Python 3.11 Alpine                                │    │
│  │   │  FastAPI + Dependencies                            │    │
│  │   │  Port: 8000                                        │    │
│  │   │  Volume: ./server:/app                             │    │
│  │   └────────────────────────────────────────────────────┘    │
│  │                                                               │
│  └─> Service: client                                             │
│      ┌────────────────────────────────────────────────────┐    │
│      │  Nginx Alpine                                      │    │
│      │  Serves Vue build                                  │    │
│      │  Port: 8080 → 80                                   │    │
│      │  Proxy: /api → api:8000                            │    │
│      └────────────────────────────────────────────────────┘    │
│                                                                  │
│  Shared Volume: dxf_exports                                      │
└─────────────────────────────────────────────────────────────────┘

Start: docker compose up --build
Access: http://localhost:8080
```

---

## Security Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  SECURITY LAYERS                                                │
│                                                                  │
│  1. Transport Layer                                              │
│     ┌────────────────────────────────────────────────────┐     │
│     │  HTTPS/TLS 1.3                                     │     │
│     │  • Certificate validation                          │     │
│     │  • Encrypted connections                           │     │
│     └────────────────────────────────────────────────────┘     │
│                                                                  │
│  2. Input Validation                                             │
│     ┌────────────────────────────────────────────────────┐     │
│     │  Pydantic Models                                   │     │
│     │  • Type checking                                   │     │
│     │  • Range validation                                │     │
│     │  • Sanitization                                    │     │
│     └────────────────────────────────────────────────────┘     │
│                                                                  │
│  3. File Upload Limits                                           │
│     ┌────────────────────────────────────────────────────┐     │
│     │  FastAPI Settings                                  │     │
│     │  • Max file size: 100MB                            │     │
│     │  • Allowed types: .nc, .gcode, .dxf                │     │
│     │  • Virus scanning (future)                         │     │
│     └────────────────────────────────────────────────────┘     │
│                                                                  │
│  4. Rate Limiting                                                │
│     ┌────────────────────────────────────────────────────┐     │
│     │  Nginx/FastAPI Middleware                          │     │
│     │  • Max 60 requests/minute per IP                   │     │
│     │  • DDoS protection                                 │     │
│     └────────────────────────────────────────────────────┘     │
│                                                                  │
│  5. Error Handling                                               │
│     ┌────────────────────────────────────────────────────┐     │
│     │  No Sensitive Info Leakage                         │     │
│     │  • Generic error messages to users                 │     │
│     │  • Detailed logs server-side only                  │     │
│     └────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Performance Considerations

```
┌─────────────────────────────────────────────────────────────────┐
│  PERFORMANCE OPTIMIZATION STRATEGIES                            │
│                                                                  │
│  Frontend:                                                       │
│  • Component lazy loading                                       │
│  • Debounced input validation                                   │
│  • Canvas rendering optimization                                │
│  • Code splitting (Vite automatic)                              │
│                                                                  │
│  Backend:                                                        │
│  • Async/await for I/O operations                               │
│  • Connection pooling (if database added)                       │
│  • Caching of common calculations                               │
│  • Batch DXF processing                                         │
│                                                                  │
│  Pipeline Modules:                                               │
│  • NumPy vectorization for math                                 │
│  • Shapely spatial indexing                                     │
│  • Pre-computed lookup tables                                   │
│  • Minimal memory allocation                                    │
│                                                                  │
│  Target Performance:                                             │
│  • API response: < 500ms (95th percentile)                      │
│  • DXF generation: < 2 seconds                                  │
│  • G-code parsing: < 5 seconds for 100k lines                   │
│  • Frontend TTI: < 3 seconds                                    │
└─────────────────────────────────────────────────────────────────┘
```

---

**Document Status**: ✅ Complete  
**For Use By**: Developers, System Architects, DevOps Engineers  
**Next Steps**: Review with team, begin Phase 1 implementation
