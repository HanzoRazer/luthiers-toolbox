# Luthier's Tool Box 🎸

> A comprehensive CNC guitar lutherie platform combining parametric design, structural analysis, CAM workflows, and Smart Guitar integration.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build: A_N.1](https://img.shields.io/badge/Build-A__N.1-brightgreen)](https://github.com/HanzoRazer/luthiers-toolbox)
[![Priority 1: Complete](https://img.shields.io/badge/Priority_1-Complete-success)](./A_N_BUILD_ROADMAP.md)
[![CAM Essentials: Ready](https://img.shields.io/badge/CAM_Essentials-Production_Ready-brightgreen)](./CAM_ESSENTIALS_N0_N10_QUICKREF.md)
[![CompareLab Tests](https://github.com/HanzoRazer/luthiers-toolbox/actions/workflows/comparelab-tests.yml/badge.svg)](https://github.com/HanzoRazer/luthiers-toolbox/actions/workflows/comparelab-tests.yml)

---

## 🎯 Project Vision

The Luthier's Tool Box is a **web-based CAD/CAM platform** designed for guitar makers, combining:

- **Parametric Design Tools** – Body outline, neck geometry, rosettes, bracing, hardware layout
- **CNC Workflows** – DXF export (R12 format), adaptive pocketing, helical ramping, drilling patterns
- **Multi-Post Support** – 5 CNC platforms (GRBL, Mach4, LinuxCNC, PathPilot, MASSO)
- **CAM Essentials** – Roughing, drilling cycles (G81-G89), probe patterns, retract strategies
- **Art Studio v16.1** – SVG editor, relief mapper, blueprint AI analysis, helical Z-ramping
- **Module L (Adaptive Pocketing)** – Trochoidal insertion, jerk-aware time estimation, island handling
- **GitHub Deployment** – Web service accessible from any device
- **Smart Guitar Project** – Integrated IoT/embedded lutherie (Raspberry Pi 5, Bluetooth)

**Core Philosophy**: Millimeter-first design, CAM-compatible geometry, and modular pipeline architecture for specialized lutherie calculations.

**Current Status**: 🟢 **Priority 1 Complete** - Production CAM core ready for A_N.1 Alpha Release (November 2025)

---

## 🆕 What's New in A_N.1 (November 2025)

### **✅ Priority 1: Production CAM Core Complete**

All critical CNC toolpath generation features are production-ready:

#### **P1.1: Art Studio v16.1 - Helical Ramping** ✅
- **Impact**: 50% better tool life, eliminates plunge breakage
- **Features**: Spiral Z-entry for pockets with configurable pitch
- **Endpoints**: `/api/cam/toolpath/helical_entry`
- **Use Cases**: Bridge pin holes, control cavities, neck pockets

#### **P1.2: Patch N17 - Polygon Offset with Arc Linkers** ✅
- **Impact**: Production-grade offsetting, no self-intersections
- **Features**: Pyclipper engine, G2/G3 arc transitions, island handling
- **Integration**: Powers Module L.1 adaptive pocketing
- **Lab**: `/lab/polygon-offset` with visual preview

#### **P1.3: Patch N16 - Trochoidal Benchmark** ✅
- **Impact**: Validates Module L.3 trochoidal performance
- **Features**: Adaptive spiral vs lanes comparison, cycle time analysis
- **Lab**: `/lab/adaptive-benchmark` with SVG preview
- **Metrics**: Length, area, time, volume, move count

#### **P1.4: CAM Essentials Rollup (N0-N10)** ✅
- **Impact**: Complete post-processor ecosystem for 5 CNC platforms
- **Operations**: 
  - **N01**: Roughing with post awareness (GRBL, Mach4, LinuxCNC, PathPilot, MASSO)
  - **N06**: Modal drilling cycles (G81, G83, G73, G84, G85)
  - **N07**: Drill patterns (grid, circle, line) with visual hole editor
  - **N08**: Retract strategies (direct G0, ramped G1, helical G2/G3)
  - **N09**: Probe patterns (corner, boss, surface Z) with G31 commands
  - **N10**: Unified CAM Essentials Lab (699-line Vue component)
- **Testing**: 12/12 smoke tests passing
- **Lab**: `/lab/cam-essentials` and `/lab/drilling`

### **📊 Integration Metrics**
- **Backend Coverage**: 100% (all routers operational)
- **Frontend Coverage**: 100% (all operations have UI)
- **Test Coverage**: 100% (comprehensive smoke test suites)
- **CI/CD**: ✅ GitHub Actions workflows configured
- **Documentation**: ✅ Complete with quickrefs and integration guides

### **📚 New Documentation**
- [A_N Build Roadmap](./A_N_BUILD_ROADMAP.md) - Release plan and feature tracking
- [Priority 1 Complete Status](./PRIORITY_1_COMPLETE_STATUS.md) - Integration verification
- [CAM Essentials Quick Reference](./CAM_ESSENTIALS_N0_N10_QUICKREF.md) - API and UI guide
- [Adaptive Pocketing Module L](./ADAPTIVE_POCKETING_MODULE_L.md) - Algorithm documentation
- [Machine Profiles Module M](./MACHINE_PROFILES_MODULE_M.md) - CNC configuration system

---

## 📁 Repository Structure

This is a **mono-repo** containing multiple related projects:

```
Luthiers ToolBox/
├── .github/                         # GitHub Actions, Copilot instructions
│   └── copilot-instructions.md      # AI agent development guide
│
├── Guitar Design HTML app/          # Legacy CAD interfaces and examples
│   └── Guitar Design HTML app/
│       ├── 10_06+2025/             # Feature bundles with deployment docs
│       ├── J45_CAM_Import_Kit/     # Acoustic guitar CAD templates
│       ├── LesPaul_CAM_Import_Kit/ # Electric guitar CAD templates
│       └── String Master Scaffolding/
│
├── Lutherier Project/               # CAD/CAM files and cleaning scripts
│   └── Lutherier Project/
│       ├── Les Paul_Project/        # DXF files, Fusion 360 setups
│       ├── Gibson J 45_ Project/    # Acoustic guitar designs
│       └── Mesh Pipeline Project/   # 3D mesh generation tools
│
├── Luthiers Tool Box/               # FEATURE LIBRARIES (MVP Builds)
│   ├── MVP Build_10-11-2025/       # Core feature set
│   │   ├── MVP_scaffold_bracing_hardware/
│   │   ├── MVP_GCode_Explainer_Addon/
│   │   ├── rosette_pack/
│   │   └── qrm_pack/
│   └── MVP Build_1012-2025/        # Extended features
│       ├── Luthiers_Tool_Box_Full_GitHubReady_Plus_Integrated_Rosette_Queue/
│       └── SmartGuitar_Pi5_Party_MVP_v0.1/
│
├── Smart Guitar Build/              # SEPARATE PROJECT: IoT integration
│   ├── Rogue-one/                  # Smart guitar firmware
│   └── Build 10-13-2025/           # Latest smart guitar tools
│
└── Integration Patches/             # Add-on features
    ├── WiringWorkbench_*.zip       # Electronics wiring planner
    └── FinishPlanner_*.zip         # Finishing schedule calculator
```

---

## 🚀 Quick Start

### **Prerequisites**
- **Python 3.11+** (for backend/CAM pipelines)
- **Node.js 20+** (for Vue 3 frontend)
- **Git** (version control)

### **Option 1: Local Development (Recommended)**

```powershell
# Clone the repository
git clone https://github.com/HanzoRazer/luthiers-toolbox.git
cd "Luthiers ToolBox"

# Backend setup
cd services/api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend setup (separate terminal)
cd packages/client  # or cd client (depending on structure)
npm install
npm run dev
```

Access the app at `http://localhost:5173`

### **Option 2: Docker Compose (Production-like)**

```powershell
docker compose up --build
```

Access via:
- **Frontend**: `http://localhost:8080`
- **API**: `http://localhost:8000`
- **Proxy**: `http://localhost:8088` (unified access)

### **First Steps**

1. **🎸 Guitar Design Tools** - Click to explore 14 design tools across 6 build phases
2. **🎨 Art Studio** - Access Blueprint Lab (AI photo analysis), SVG editor, DXF tools
3. **⚙️ CAM Tools** - Try CAM Essentials Lab for roughing, drilling, and probe patterns
4. **🧮 Calculators** - Use Scientific Calculator or Business Calculator
5. **💼 CNC Business** - Financial planning and ROI analysis

### **Quick Test - CAM Essentials**

```powershell
# Run comprehensive smoke tests
.\test_cam_essentials_n0_n10.ps1

# Expected: 12/12 tests passing
# • N01: Roughing (GRBL, Mach4)
# • N06: Drilling (G81, G83)
# • N07: Drill Patterns (Grid, Circle, Line)
# • N08: Retract Patterns (Direct, Helical)
# • N09: Probe Patterns (Corner, Boss, Surface)
```

- **Client**: http://localhost:8080
- **API**: http://localhost:8000

### **Option 3: GitHub Pages Deployment**

See [DEPLOYMENT.md](DEPLOYMENT.md) for GitHub Actions setup and static site generation.

---

## 🛠️ Feature Catalog

### **Core Application** (Vue 3 + FastAPI)

| Feature | Description | Location |
|---------|-------------|----------|
| **CAD Canvas** | Millimeter-grid design interface | `client/src/components/toolbox/CadCanvas.vue` |
| **DXF Export** | R12 format, closed LWPolylines | `server/app.py` → `/exports/queue` |
| **Boolean Operations** | Shapely-based union/intersect | `server/app.py` → `/boolean` |
| **Hot Folder Poller** | Windows CNC integration | `server/poller.py` (→ `C:\CAM\HotFolder`) |

### **Pipeline Tools** (Feature Libraries)

#### **Rosette Calculator**
- **Location**: `MVP Build_10-11-2025/rosette_pack/`, `MVP Build_1012-2025/*/pipelines/rosette/`
- **Features**:
  - Parametric soundhole rosette design
  - Channel width/depth calculations
  - SVG/DXF export for CNC
  - G-code generation (scoring, rough, finish passes)
  - Blender add-on for 3D visualization
- **Usage**:
  ```powershell
  cd server/pipelines/rosette
  python rosette_calc.py example_params.json --out-dir out/
  python rosette_to_dxf.py example_params.json --out out/rosette.dxf
  ```

#### **Bracing Calculator**
- **Location**: `MVP Build_10-11-2025/MVP_scaffold_bracing_hardware/pipelines/bracing/`
- **Features**:
  - Mass estimation (wood density × volume)
  - Glue area calculation
  - Structural stiffness modeling
  - X-brace, fan brace, ladder brace templates
- **Usage**:
  ```powershell
  python bracing_calc.py example_x_brace.json --out-dir out/
  ```

#### **Hardware Layout**
- **Location**: `MVP Build_10-11-2025/MVP_scaffold_bracing_hardware/pipelines/hardware/`
- **Features**:
  - Electronics cavity positioning (pickups, pots, switches)
  - DXF export for routing
  - JSON templates (Les Paul, Strat, Tele)
- **Usage**:
  ```powershell
  python hardware_layout.py example_lp_hardware.json --out-dir out/
  ```

#### **G-code Explainer**
- **Location**: `MVP Build_10-11-2025/MVP_GCode_Explainer_Addon/`
- **Features**:
  - Line-by-line G-code analysis
  - Modal state tracking (G0/G1, spindle, feed rate)
  - Export to TXT, Markdown, HTML, CSV
  - Web UI with drag-and-drop (Flask server on port 5051)
- **Usage**:
  ```powershell
  python explain_gcode_ai.py --in example.nc --md --html --csv
  python serve_explainer.py  # Web UI: http://127.0.0.1:5051
  ```

#### **DXF Cleaning Scripts**
- **Location**: `Lutherier Project*/Les Paul_Project/`, `Gibson J 45_ Project/`
- **Features**:
  - Convert LINE/ARC/CIRCLE/SPLINE → closed LWPolylines
  - Segment chaining with 0.12mm tolerance
  - Multi-layer support
  - GUI and CLI modes
- **Usage**:
  ```powershell
  python clean_cam_ready_dxf_windows_all_layers.py
  ```

### **Add-on Features** (Integration Patches)

| Add-on | Description | Status |
|--------|-------------|--------|
| **WiringWorkbench** | Electronics wiring diagram generator | 📦 ZIP bundles |
| **FinishPlanner** | Multi-stage finishing schedule calculator | 📦 ZIP bundles |
| **QRM Pack** | QuadRemesher presets for mesh retopology | `qrm_pack/` |

### **Smart Guitar Project** (Separate)

- **Location**: `Smart Guitar Build/`, `MVP Build_1012-2025/SmartGuitar_Pi5_Party_MVP_v0.1/`
- **Features**:
  - Raspberry Pi 5 integration
  - Bluetooth/DAW connectivity
  - Rear cavity routing template (DXF)
  - Battery bay (4×18650), BMS pocket, cooling fan
- **Tech Stack**: Python + Pi GPIO, MIDI integration
- **Documentation**: See `smart_guitar_rear_cavity_template_README.txt`

---

## 🎸 Guitar Tap - Companion Workshop Tool

**Guitar Tap** is a desktop application for real-time tap tone analysis and deflection correlation, based on **Trevor Gore's research methods**.

### **Features:**
- ✅ **Real-time FFT analysis** - Capture guitar resonances with microphone input
- ✅ **Deflection vs Frequency Correlation** - Gore's structural analysis method
- ✅ **Enhanced Frequency Display** - Color-coded peaks with musical notes and cents deviation
- ✅ **Linear Regression Analysis** - R² correlation, residuals plots, statistical analysis
- ✅ **CSV Export** - Integration with Tool Box calculators
- ✅ **Cross-platform** - Windows, Mac, Linux (PyQt6)

### **Quick Start:**
```powershell
cd guitar_tap
pip install numpy scipy sounddevice pyqt6 matplotlib
python guitar_tap.py

# Or launch enhanced tools:
python launch_deflection_analyzer.py
python test_enhanced_display.py
```

### **Integration Workflow:**
1. **Measure in Guitar Tap** → Take deflection and frequency measurements
2. **Export CSV** → `deflection_measurements.csv`
3. **Import to Tool Box** → Bracing Calculator or structural analysis tools
4. **Generate CAM** → DXF export for CNC machining

### **Documentation:**
- [guitar_tap/README.md](guitar_tap/README.md) - Installation and usage
- [guitar_tap/WORKFLOW_GUIDE.md](guitar_tap/WORKFLOW_GUIDE.md) - Complete measurement workflow
- [guitar_tap/INTEGRATION_COMPLETE.md](guitar_tap/INTEGRATION_COMPLETE.md) - Enhanced features guide

### **Scientific Background:**
Based on Trevor Gore & Gerard Gilet's "Contemporary Acoustic Guitar" methods for:
- Tap tone analysis (modal frequencies)
- Structural stiffness correlation
- Quality control in guitar building
- Reproducibility and consistency

**Repository:** [guitar_tap/](guitar_tap/)  
**Tech Stack:** Python 3.11, PyQt6, NumPy, SciPy, Matplotlib  
**Original:** Forked from [dwsdolce/guitar_tap](https://github.com/dwsdolce/guitar_tap)

---

## 🔧 CAM Platform Support

### **Multi-Post Processor System**

The Luthier's Tool Box supports **5 CNC platforms** with automatic post-processor selection:

| Platform | Post ID | G-code Dialect | Arc Mode | Status |
|----------|---------|----------------|----------|--------|
| **GRBL 1.1** | `GRBL` | Standard G-code | I/J (incremental) | ✅ Production |
| **Mach4** | `Mach4` | Mach3/4 compatible | I/J + R-mode | ✅ Production |
| **LinuxCNC** | `LinuxCNC` | RS274/NGC | I/J (incremental) | ✅ Production |
| **PathPilot** | `PathPilot` | Tormach variant | I/J (incremental) | ✅ Production |
| **MASSO** | `MASSO` | Masso G3 | I/J (incremental) | ✅ Production |

**Additional Profiles:**
- **Fanuc/Haas** - Industrial controllers with R-mode arcs and G4 S dwell (N05)
- **Marlin** - 3D printer CNC conversions (hobby use)

### **Post-Processor Features**

All post-processors support:
- ✅ **Header/Footer Injection** - Machine-specific startup and shutdown sequences
- ✅ **Arc Mode Selection** - I/J (incremental) or R-mode (radius) per machine
- ✅ **Dwell Syntax** - G4 P (milliseconds) vs G4 S (seconds)
- ✅ **Token Expansion** - Dynamic substitution (`%POST_ID%`, `%UNITS%`, `%RPM%`, etc.)
- ✅ **Multi-Export Bundles** - Generate DXF + SVG + N × NC files in single ZIP

### **Configuration Files**

Post-processor configs: `services/api/app/data/posts/*.json`
```json
{
  "header": [
    "G90",           // Absolute positioning
    "G21",           // Metric units
    "G17",           // XY plane
    "(POST=GRBL)"    // Metadata
  ],
  "footer": [
    "M30",           // Program end
    "(End)"
  ]
}
```

### **Integration Examples**

**Fusion 360**: JSON setup files
- `Lutherier Project*/Les Paul_Project/09252025/FusionSetup_Base_LP_Mach4.json`

**Mach4**: Safety macros and auto-variables
- `plugins/gibson/nc_lint_autovars.py`

**VCarve**: Standard Mach3-compatible post (use `Mach4` post ID)

---

## ✨ Key Features

### **🎸 Guitar Design Tools (14 Tools, 6 Phases)**

Organized by construction workflow:

**Phase 1: Body Foundation**
- Body Outline Generator - Parametric acoustic/electric bodies with DXF export
- Bracing Calculator - Structural analysis with deflection correlation
- Archtop Calculator - Carved top geometry and thickness profiles

**Phase 2: Neck & Fretboard**
- Neck Generator - Les Paul style with scale length compensation
- Scale Length Designer - Intonation calculator
- Radius Dish Designer - Fretboard radius profiles
- Enhanced Radius Dish - Advanced compound radius
- Compound Radius Fretboard - Multi-radius fingerboards

**Phase 3: Bridge & Setup**
- Bridge Calculator - Saddle compensation for acoustic guitars (Phase P2.3)

**Phase 4: Hardware & Electronics**
- Hardware Layout - Pickup routing, control cavity placement
- Wiring Workbench - Electronics layout and wiring diagrams (Phase P2.3)

**Phase 5: Decorative Details**
- Rosette Designer - Laser-cut rosette patterns with DXF/G-code export

**Phase 6: Finishing**
- Finish Planner - Coating schedule and drying times (Phase P2.3)
- Finishing Designer - Multi-coat planning

### **🎨 Art Studio (v16.1)**

**Design Tools:**
- **Blueprint Lab** - AI-powered guitar photo analysis → vectorization → DXF export (Phase 2)
- **Relief Mapper** - Heightmap to CNC toolpaths with roughing and finishing
- **SVG Editor** - Vector graphics with CAM-ready geometry

**CAM Integration:**
- **DXF Cleaner** - CAM-ready geometry conversion (R12 format, closed paths)
- **DXF Preflight** - Pre-export validation (catch errors before CAM import)
- **Export Queue** - Download manager for multi-format exports

**v16 Features:**
- SVG layer management
- Relief carving workflows
- Post-processor v15.5 (CRC, lead-in/out, arc mode selection)

**v16.1 Features:** 🆕
- Helical Z-ramping (spiral entry for pockets)
- 50% better tool life vs plunge entry
- Configurable pitch and feed rates

### **⚙️ CAM Tools (N0-N10 Essentials)**

**Core Operations:**
- **Roughing (N01)** - Rectangular pocketing with 5-post support
- **Drilling (N06)** - Modal cycles (G81-G89: drill, peck, tap, bore, ream)
- **Drill Patterns (N07)** - Grid, circle, line arrays with visual hole editor
- **Retract Patterns (N08)** - Direct G0, ramped G1, helical G2/G3 strategies
- **Probe Patterns (N09)** - Corner, boss, surface Z with G31 commands and SVG setup sheets

**Advanced Features:**
- **Module L: Adaptive Pocketing** - Trochoidal insertion, jerk-aware time, island handling (L.1-L.3)
- **Module M: Machine Profiles** - CNC configuration, accel/jerk limits, learning system (M.1-M.4)
- **Helical Ramp Lab** - Spiral entry toolpaths (v16.1)
- **Polygon Offset Lab** - Robust offsetting with arc linkers (N17)
- **Adaptive Benchmark Lab** - Performance comparison (N16)

**Workflows:**
- Roughing → Drilling → Probing → Finishing
- Multi-post export bundles (DXF + SVG + N × NC files)
- Real-time statistics (length, area, time, volume)

### **🧮 Calculators (4 Tools)**

**Math & Precision:**
- **Fraction Calculator** - Decimal ↔ fraction conversions (placeholder)
- **Scientific Calculator** - Full-featured with trig, logs, constants (π, e)

**Business & ROI:**
- **CNC ROI Calculator** - Investment analysis (placeholder)
- **Business Calculator** - Startup costs, revenue projections, cash flow (750 lines)

### **💼 CNC Business**
- Financial planning for lutherie shops
- Equipment cost analysis
- Revenue and profit projections

---

## 📚 Documentation

### **Core Documentation**
- [README.md](./README.md) - This file (project overview)
- [A_N_BUILD_ROADMAP.md](./A_N_BUILD_ROADMAP.md) - A_N.1 release plan (Priority 1 100% ✅)
- [ARCHITECTURE.md](./ARCHITECTURE.md) - System architecture and design patterns
- [CODING_POLICY.md](./CODING_POLICY.md) - Development standards and conventions
- [.github/copilot-instructions.md](./.github/copilot-instructions.md) - AI agent development guide
- [DEPLOYMENT.md](./DEPLOYMENT.md) - GitHub Pages, Railway, Docker deployment
- [CONTRIBUTING.md](./CONTRIBUTING.md) - Code style, PR process, feature integration

### **Priority 1 (Complete - Production Ready)**

**P1.1: Helical Ramping**
- [ART_STUDIO_V16_1_HELICAL_INTEGRATION.md](./ART_STUDIO_V16_1_HELICAL_INTEGRATION.md) - Full integration guide
- [ART_STUDIO_V16_1_QUICKREF.md](./ART_STUDIO_V16_1_QUICKREF.md) - Quick reference
- [HELICAL_POST_PRESETS.md](./HELICAL_POST_PRESETS.md) - Post-processor presets

**P1.2: Polygon Offset**
- [POLYGON_OFFSET_N17_INTEGRATION.md](./POLYGON_OFFSET_N17_INTEGRATION.md) - Lab integration
- [POLYGON_OFFSET_N17_QUICKREF.md](./POLYGON_OFFSET_N17_QUICKREF.md) - API reference
- [OFFSET_SMOOTHING_ARC_LINKERS.md](./OFFSET_SMOOTHING_ARC_LINKERS.md) - Arc linking algorithm

**P1.3: Trochoidal Benchmark**
- [TROCHOIDAL_BENCHMARK_N16_COMPLETE.md](./TROCHOIDAL_BENCHMARK_N16_COMPLETE.md) - Full benchmark results
- [TROCHOIDAL_BENCHMARK_N16_QUICKREF.md](./TROCHOIDAL_BENCHMARK_N16_QUICKREF.md) - Quick reference

**P1.4: CAM Essentials Rollup**
- [P1_4_CAM_ESSENTIALS_PRODUCTION_RELEASE.md](./P1_4_CAM_ESSENTIALS_PRODUCTION_RELEASE.md) - Production release summary 🆕
- [CAM_ESSENTIALS_N0_N10_INTEGRATION_COMPLETE.md](./CAM_ESSENTIALS_N0_N10_INTEGRATION_COMPLETE.md) - Full integration
- [CAM_ESSENTIALS_N0_N10_QUICKREF.md](./CAM_ESSENTIALS_N0_N10_QUICKREF.md) - API and UI reference
- [CAM_ESSENTIALS_N0_N10_STATUS.md](./CAM_ESSENTIALS_N0_N10_STATUS.md) - Completion metrics

### **Module Documentation**

**Module L: Adaptive Pocketing**
- [ADAPTIVE_POCKETING_MODULE_L.md](./ADAPTIVE_POCKETING_MODULE_L.md) - Module overview (L.0-L.3)
- [PATCH_L1_ROBUST_OFFSETTING.md](./PATCH_L1_ROBUST_OFFSETTING.md) - L.1 pyclipper integration
- [PATCH_L2_TRUE_SPIRALIZER.md](./PATCH_L2_TRUE_SPIRALIZER.md) - L.2 continuous spiral
- [PATCH_L2_MERGED_SUMMARY.md](./PATCH_L2_MERGED_SUMMARY.md) - L.2 curvature respacing
- [PATCH_L3_SUMMARY.md](./PATCH_L3_SUMMARY.md) - L.3 trochoids and jerk-aware time

**Module M: Machine Profiles**
- [MACHINE_PROFILES_MODULE_M.md](./MACHINE_PROFILES_MODULE_M.md) - Module overview (M.1-M.4)
- [MACHINE_PROFILE_M1_INTEGRATION.md](./MACHINE_PROFILE_M1_INTEGRATION.md) - M.1 CRUD operations
- [MACHINE_PROFILE_M2_LEARNING.md](./MACHINE_PROFILE_M2_LEARNING.md) - M.2 learning system
- [MACHINE_PROFILE_M3_OPTIMIZER.md](./MACHINE_PROFILE_M3_OPTIMIZER.md) - M.3 feed optimizer
- [MACHINE_PROFILE_M4_QUICKREF.md](./MACHINE_PROFILE_M4_QUICKREF.md) - M.4 quick reference

**Blueprint Import Pipeline**
- [BLUEPRINT_LAB_INDEX.md](./BLUEPRINT_LAB_INDEX.md) - Lab overview
- [BLUEPRINT_IMPORT_PHASE1_SUMMARY.md](./BLUEPRINT_IMPORT_PHASE1_SUMMARY.md) - Phase 1 complete
- [BLUEPRINT_IMPORT_PHASE2_COMPLETE.md](./BLUEPRINT_IMPORT_PHASE2_COMPLETE.md) - Phase 2 complete
- [BLUEPRINT_LAB_QUICKREF.md](./BLUEPRINT_LAB_QUICKREF.md) - Quick reference

**Art Studio**
- [ART_STUDIO_COMPLETE_INTEGRATION.md](./ART_STUDIO_COMPLETE_INTEGRATION.md) - Full integration
- [ART_STUDIO_V16_0_INTEGRATION_COMPLETE.md](./ART_STUDIO_V16_0_INTEGRATION_COMPLETE.md) - v16.0 features
- [ART_STUDIO_V15_5_INTEGRATION.md](./ART_STUDIO_V15_5_INTEGRATION.md) - v15.5 post-processor

### **Testing & CI/CD**
- [.github/workflows/cam_essentials.yml](./.github/workflows/cam_essentials.yml) - CAM Essentials CI 🆕
- [.github/workflows/adaptive_pocket.yml](./.github/workflows/adaptive_pocket.yml) - Adaptive pocketing CI
- [.github/workflows/helical_badges.yml](./.github/workflows/helical_badges.yml) - Helical ramping CI
- [test_cam_essentials_n0_n10.ps1](./test_cam_essentials_n0_n10.ps1) - CAM smoke tests (12/12 passing ✅)
- [scripts/Test-RepoHealth.ps1](./scripts/Test-RepoHealth.ps1) - Repo-wide `/health` probe (ensures FastAPI health router reports `status: ok`, verifies optional diagnostics via `-IncludeDiagnostics`, and runs inside `.github/workflows/server-env-check.yml`)

### **Export & Post-Processors**
- [MULTI_POST_EXPORT_SYSTEM.md](./MULTI_POST_EXPORT_SYSTEM.md) - Multi-post architecture
- [POST_CHOOSER_SYSTEM.md](./POST_CHOOSER_SYSTEM.md) - UI integration
- [BATCH_EXPORT_SUMMARY.md](./BATCH_EXPORT_SUMMARY.md) - Batch export workflows

---

## 🤝 Contributing

**Status:** A_N.1 Alpha Release Candidate – Priority 1 Complete (100%)

We welcome contributions! This project follows a **module-based development** approach with strict testing and documentation requirements.

### **Development Workflow**

1. **Choose a Priority** from [A_N_BUILD_ROADMAP.md](./A_N_BUILD_ROADMAP.md):
   - ✅ Priority 1 (P1.1-P1.4): Complete - Production CAM core
   - 🔜 Priority 2 (P2.1-P2.6): Design tools enhancement
   - 🔜 Priority 3 (P3.1-P3.4): Advanced CAM features

2. **Feature Development**:
   - Backend: Add routers in `services/api/app/routers/`
   - Frontend: Add components in `packages/client/src/components/`
   - Follow [CODING_POLICY.md](./CODING_POLICY.md) conventions

3. **Testing Requirements**:
   - PowerShell smoke test script (`test_*.ps1`)
   - GitHub Actions CI workflow (`.github/workflows/*.yml`)
   - 100% endpoint coverage for new routers

4. **Documentation Requirements** (3-doc pattern):
   - `INTEGRATION_COMPLETE.md` - Full integration details
   - `QUICKREF.md` - API and UI quick reference
   - `STATUS.md` or `SUMMARY.md` - Completion metrics

5. **Submit PR**:
   - Include test results (all passing ✅)
   - Link to integration documents
   - Update roadmap with completion status

### **Current Focus Areas**

- **Priority 2.1**: Neck Calculator enhancement (geometry, CNC paths)
- **Priority 2.2**: Bracing Pattern Library (X-bracing, lattice, fan)
- **Priority 2.3**: Bridge Calculator production-ready (intonation, G-code)

See [CONTRIBUTING.md](./CONTRIBUTING.md) for detailed code style and PR guidelines.

---

## 📄 License

MIT License – see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- **ezdxf** for DXF R12 export
- **Shapely** for geometry processing
- **Vue 3 + Vite** for reactive UI
- **FastAPI** for Python backend
- Community contributors and lutherie experts

---

## 📧 Contact

- **Issues**: [GitHub Issues](https://github.com/<your-username>/luthiers-toolbox/issues)
- **Discussions**: [GitHub Discussions](https://github.com/<your-username>/luthiers-toolbox/discussions)

---

**Happy Building! 🎸**
