# Luthier's Tool Box – Architecture

> System design, data flows, and integration patterns for the CNC guitar lutherie platform.

**Last Updated**: November 3, 2025  
**Version**: Multi-project mono-repo architecture

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Repository Organization](#repository-organization)
3. [Core Application Architecture](#core-application-architecture)
4. [Pipeline System](#pipeline-system)
5. [Feature Catalog](#feature-catalog)
6. [Data Flows](#data-flows)
7. [CAM Integration](#cam-integration)
8. [Smart Guitar Project](#smart-guitar-project)
9. [Extension Points](#extension-points)
10. [Design Decisions](#design-decisions)

---

## System Overview

### **High-Level Architecture**

```
┌─────────────────────────────────────────────────────────────┐
│                    BROWSER CLIENT                           │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Vue 3 + Vite (TypeScript)                         │    │
│  │  ├── CadCanvas.vue      (Design interface)         │    │
│  │  ├── LuthierCalculator  (String spacing, etc.)     │    │
│  │  └── ExportView         (DXF queue management)     │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                          │ HTTP/WS
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    FASTAPI SERVER                           │
│  ┌────────────────────────────────────────────────────┐    │
│  │  app.py (FastAPI application)                      │    │
│  │  ├── /projects, /documents, /versions             │    │
│  │  ├── /boolean (Shapely operations)                │    │
│  │  ├── /exports/queue (DXF generation)              │    │
│  │  └── WebSocket (real-time presence)               │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                 PIPELINE ECOSYSTEM                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  Rosette    │  │  Bracing    │  │  Hardware   │        │
│  │  Calculator │  │  Analysis   │  │  Layout     │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  G-code     │  │  DXF        │  │  Export     │        │
│  │  Explainer  │  │  Cleaner    │  │  Queue      │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   CAM SOFTWARE                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │ Fusion   │ │  Mach4   │ │  VCarve  │ │ LinuxCNC │      │
│  │  360     │ │          │ │          │ │  (EMC2)  │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
│  ┌──────────┐                                               │
│  │  Masso   │  (Hot Folder: C:\CAM\HotFolder)             │
│  └──────────┘                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Repository Organization

### **Mono-Repo Structure**

The repository contains **three types of projects**:

#### **1. Core Application** (Active Development)
- **Path**: Extracted from MVP builds → `server/`, `client/`
- **Purpose**: Web-based CAD/CAM interface
- **Status**: Under active integration

#### **2. Feature Libraries** (MVP Builds)
- **Paths**: `Luthiers Tool Box/MVP Build_10-11-2025/`, `MVP Build_1012-2025/`
- **Purpose**: Reference implementations for cherry-picking features
- **Structure**:
  ```
  MVP Build_*/
  ├── MVP_scaffold_bracing_hardware/     # Bracing + hardware tools
  ├── MVP_GCode_Explainer_Addon/         # G-code analysis
  ├── rosette_pack/                      # Rosette calculator
  ├── qrm_pack/                          # Mesh retopology presets
  └── Luthiers_Tool_Box_Full_GitHubReady_Plus_Integrated_Rosette_Queue/
  ```

#### **3. Design Archives**
- **Paths**: `Lutherier Project/`, `Guitar Design HTML app/`
- **Purpose**: CAD files, Fusion 360 setups, DXF templates
- **Contents**:
  - Les Paul / J-45 project files
  - DXF cleaning scripts
  - Fusion 360 tool libraries and post-processors

#### **4. Smart Guitar Project** (Separate)
- **Path**: `Smart Guitar Build/`
- **Purpose**: IoT/embedded guitar with Raspberry Pi 5
- **Tech Stack**: Python, MIDI, Bluetooth, GPIO
- **Integration**: Rear cavity DXF templates for CNC machining

---

## Core Application Architecture

### **Technology Stack**

#### **Frontend (Client)**
- **Framework**: Vue 3.4+ with Composition API (`<script setup>`)
- **Build Tool**: Vite 5.0+
- **Language**: TypeScript
- **Key Libraries**: None (vanilla Vue + native Canvas API)

#### **Backend (Server)**
- **Framework**: FastAPI (Python 3.11+)
- **Validation**: Pydantic models
- **Geometry**: Shapely (boolean operations)
- **DXF**: ezdxf (R12/AC1009 format)
- **Server**: Uvicorn (ASGI)

#### **Deployment**
- **Primary**: GitHub Pages (static) + GitHub Actions
- **Alternative**: Docker Compose, Railway, Vercel
- **Storage**: File-based (JSON + DXF files in `server/storage/`)

### **API Endpoints**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/projects` | POST | Create project container |
| `/documents` | POST | Create document within project |
| `/versions/save` | POST | Save snapshot with geometry (mm units) |
| `/versions/{doc_id}` | GET | List all versions |
| `/boolean` | POST | Shapely union/intersect operations |
| `/exports/queue` | POST | Queue DXF export job |
| `/exports/list` | GET | List queued/ready exports |
| `/files/{export_id}` | GET | Download generated DXF |
| `/ws` | WebSocket | Real-time presence updates |

### **Data Models**

#### **Project → Document → Version Hierarchy**
```python
Project {
  id: str (UUID)
  name: str
  created_at: datetime
}

Document {
  id: str (UUID)
  project_id: str
  name: str
  head_version: int
}

Version {
  version_no: int
  is_snapshot: bool
  payload_json: {
    units: "mm"
    polylines: [[[x,y], [x,y], ...]]
    metadata: {...}
  }
  author: str
  created_at: datetime
}
```

---

## Pipeline System

### **Design Pattern**

Each pipeline is a **standalone CLI tool** that:
1. Reads JSON configuration
2. Performs calculations
3. Outputs JSON report + artifact (DXF/SVG/G-code)
4. Updates `queue.json` for UI integration

### **Pipeline Template**

```python
# pipelines/<tool>/<tool>_calc.py
import argparse, json, pathlib

def compute(params: dict) -> dict:
    """Core calculation logic"""
    # Extract params
    # Perform math
    # Return results
    pass

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("json_in")
    ap.add_argument("--out-dir", default="out")
    args = ap.parse_args()
    
    params = json.loads(pathlib.Path(args.json_in).read_text())
    result = compute(params)
    
    out_dir = pathlib.Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "result.json").write_text(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
```

---

## Feature Catalog

### **Integration Status Matrix**

| Feature | MVP Build | Status | Priority | Notes |
|---------|-----------|--------|----------|-------|
| **Rosette Calculator** | 10-11-2025, 1012-2025 | 🔄 Integrating | Medium | DXF + G-code generation ready |
| **Bracing Analysis** | 10-11-2025 | 📦 Available | Low | Mass/glue area calculations |
| **Hardware Layout** | 10-11-2025 | 📦 Available | Low | Electronics cavity planning |
| **G-code Explainer** | 10-11-2025 | 📦 Available | Medium | Web UI + CLI tool |
| **DXF Cleaner** | Lutherier Project/ | ✅ Complete | High | CAM prep utility |
| **Export Queue** | 1012-2025 | 🔄 Integrating | High | Unified export management |
| **WiringWorkbench** | Integration_Patch_v1 | 🔜 Planned | Low | Electronics wiring diagrams |
| **FinishPlanner** | Integration_Patch_v1 | 🔜 Planned | Low | Finishing schedule calculator |
| **QRM Retopology** | 10-11-2025 | 📦 Available | Low | Blender mesh retopology |
| **Smart Guitar** | Smart Guitar Build/ | 🔀 Separate Project | N/A | IoT integration |

**Legend**: ✅ Complete | 🔄 In Progress | 📦 Available in MVP | 🔜 Planned | 🔀 Separate

---

## Data Flows

### **1. Design → Export Workflow**

```
User creates geometry in CadCanvas.vue
  ↓
POST /versions/save { polylines: [...], units: "mm" }
  ↓
Server stores version with head_version++
  ↓
User clicks "Export DXF"
  ↓
POST /exports/queue { document_id, version_no, kind: "dxf" }
  ↓
Server generates R12 DXF with closed LWPolylines
  ↓
Export status → "ready"
  ↓
GET /files/{export_id} → Download DXF
  ↓
(Optional) poller.py copies to C:\CAM\HotFolder
```

### **2. Pipeline Execution Workflow**

```
User prepares JSON config (example_params.json)
  ↓
python pipeline_tool.py example_params.json --out-dir out/
  ↓
Tool computes results (rosette channels, brace mass, etc.)
  ↓
Outputs:
  - out/result.json (numeric results)
  - out/artifact.dxf (CAM-ready geometry)
  - out/queue.json (export queue metadata)
  ↓
UI reads queue.json → displays "Ready Exports"
```

### **3. CAM Integration Workflow**

```
DXF file (R12, closed LWPolylines, mm units)
  ↓
Import into Fusion 360 / VCarve / Mach4
  ↓
Apply tool library (FusionSetup_Base_LP_Mach4.json)
  ↓
Generate toolpaths (profile, pocket, drill)
  ↓
Post-process to G-code
  ↓
(Optional) G-code Explainer for validation
  ↓
Send to CNC controller
```

---

## CAM Integration

### **Supported Platforms**

#### **1. Fusion 360** (Primary)
- **Setup Files**: `Lutherier Project/Les Paul_Project/09252025/Base_LP_Fusion_Package/`
- **Tool Library**: `FusionSetup_Base_LP_Mach4.json`
- **Post-Processor**: Generic Fanuc/Haas → Mach4 compatible
- **Workflow**: DXF import → CAM operations → G-code export

#### **2. Mach4**
- **Safety Macros**: `plugins/gibson/nc_lint_autovars.py`
- **Features**: Auto-variable validation, stepdown checks
- **G-code Dialect**: Mach3/4 compatible (G0/G1, M3/M5)

#### **3. VCarve**
- **Post-Processor**: Standard Mach3-compatible
- **Features**: Profile, pocket, V-carve toolpaths
- **DXF Import**: Native support for R12 format

#### **4. LinuxCNC (EMC2)** [Placeholder]
- **G-code Dialect**: RS274/NGC (NIST standard)
- **Status**: Post-processor TBD
- **Integration**: Custom tool table and axis configuration

#### **5. Masso Controller** [Placeholder]
- **G-code Dialect**: Masso G3 variant
- **Status**: Adapter script TBD
- **Integration**: Direct USB/Ethernet connection

### **DXF Requirements for CAM**

All DXF exports MUST follow these rules:

1. **Format**: R12 (AC1009) – maximum compatibility
2. **Units**: Millimeters (INSUNITS=4)
3. **Geometry**: Closed LWPOLYLINEs (no open paths)
4. **Tolerance**: ±0.12mm for segment chaining
5. **Layers**: Named by operation (PROFILE, POCKET, DRILL)

**Why R12?** Legacy CAM software (Mach4, VCarve) has inconsistent support for newer DXF versions (R13+). R12 guarantees universal import.

---

## Smart Guitar Project

### **Separation Rationale**

The Smart Guitar is a **separate hardware project** with its own:
- **Tech Stack**: Python + Raspberry Pi GPIO, MIDI libraries
- **Hardware**: Pi 5, 4×18650 batteries, BMS, cooling fan
- **Integration Point**: Rear cavity DXF template for CNC machining

### **Architecture**

```
┌─────────────────────────────────────────────┐
│        Smart Guitar Electronics Bay         │
│  ┌────────────────────────────────────┐    │
│  │  Raspberry Pi 5                    │    │
│  │  ├── MIDI I/O (USB)                │    │
│  │  ├── Bluetooth 5.0                 │    │
│  │  ├── Audio processing (ALSA/JACK)  │    │
│  │  └── Web UI (Flask/FastAPI)        │    │
│  └────────────────────────────────────┘    │
│  ┌────────────────────────────────────┐    │
│  │  Power System                      │    │
│  │  ├── 4×18650 batteries (2×2)       │    │
│  │  ├── BMS (battery management)      │    │
│  │  └── 5V/3A regulator              │    │
│  └────────────────────────────────────┘    │
└─────────────────────────────────────────────┘
```

### **DXF Template**

**File**: `smart_guitar_rear_cavity_template.dxf`

**Layers**:
- `COVER_OUTLINE` – Plastic cover profile (180×110mm)
- `CAVITY_REBATE` – Ledge for cover (3mm inset)
- `POCKETS` – Pi bay (100×70mm), battery bay (45.2×73mm), BMS (60×25mm)
- `HOLES` – Fan mount (Ø50mm), screws (Ø3mm)
- `GUIDES` – Cable channels (8mm wide)

### **Integration with Main Project**

The Smart Guitar DXF template is **generated by the main Luthier's Tool Box** hardware layout pipeline, then used for CNC routing of the guitar body.

---

## Extension Points

### **Adding a New Pipeline**

1. **Create directory**: `server/pipelines/<tool>/`
2. **Implement CLI tool**: `<tool>_calc.py` (see template above)
3. **Add config examples**: `server/configs/examples/<tool>/`
4. **Update queue**: Append to `exports/queue.json`
5. **Document**: Add to `ARCHITECTURE.md` feature catalog

### **Adding a New CAM Platform**

1. **Create post-processor**: `plugins/<platform>/post_<platform>.py`
2. **Add G-code dialect**: Document special commands (e.g., Masso `G38.2`)
3. **Test with DXF**: Verify closed-path import
4. **Update docs**: Add to CAM Integration section

### **Adding a Vue Component**

1. **Create component**: `client/src/components/toolbox/<Feature>.vue`
2. **Add to App.vue**: Register in navigation
3. **Connect to API**: Use `utils/api.ts` SDK functions
4. **Test**: Verify units are always `mm`

---

## Design Decisions

### **1. Why Millimeters Only?**

**Decision**: All internal storage and calculations use millimeters.

**Rationale**:
- CNC machines operate in metric (mm or µm)
- Avoids floating-point errors from unit conversions
- Fusion 360 / Mach4 default to mm
- Inches can be added as UI-only display layer

**Future**: Add inch display with fractional notation (e.g., `1 3/16"`)

### **2. Why R12 DXF Format?**

**Decision**: Always export DXF R12 (AC1009), never R13+.

**Rationale**:
- Maximum compatibility with legacy CAM software
- VCarve / Mach4 have parsing bugs with R13+ features (splines, hatches)
- R12 only supports basic entities (LINE, ARC, CIRCLE, POLYLINE) – perfect for CAM

**Trade-off**: No advanced features (blocks, xrefs), but CAM doesn't need them.

### **3. Why Closed LWPolylines?**

**Decision**: All geometry is converted to closed LWPOLYLINE entities.

**Rationale**:
- CNC operations require closed paths for toolpath generation
- Open paths cause "unsafe cut" errors in CAM software
- Shapely `unify_and_close()` function ensures valid polygons

**Implementation**: DXF cleaning scripts chain segments with 0.12mm tolerance.

### **4. Why Pipeline Pattern?**

**Decision**: Each tool is a standalone CLI script, not integrated into FastAPI.

**Rationale**:
- Easier to test in isolation
- Users can run pipelines without web server
- Parallel development by multiple contributors
- Future: Add FastAPI wrappers for web UI

**Trade-off**: Less tight integration, but more modularity.

### **5. Why Feature Library Model?**

**Decision**: MVP builds are "libraries" to cherry-pick from, not active code.

**Rationale**:
- Allows experimentation without breaking main codebase
- Each MVP build is a frozen snapshot of working features
- Clear separation between "reference" and "production"

**Process**: Extract → Test → Integrate → Document

---

## Next Steps

### **Near-Term (v1.0)**
- [ ] Integrate rosette calculator into main app
- [ ] Add export queue UI component
- [ ] Deploy to GitHub Pages
- [ ] Add LinuxCNC post-processor

### **Mid-Term (v2.0)**
- [ ] Inch/fractional display in UI
- [ ] Database backend (PostgreSQL)
- [ ] Multi-user collaboration (WebSocket sync)
- [ ] Blender add-on integration

### **Long-Term (v3.0)**
- [ ] Smart Guitar web interface
- [ ] Real-time toolpath simulation
- [ ] AI-assisted brace design
- [ ] Mobile app (React Native)

---

**Document Maintained By**: AI Agent + Human Collaborator  
**Last Review**: November 3, 2025
