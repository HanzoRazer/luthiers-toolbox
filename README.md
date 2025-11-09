# Luthier's Tool Box 🎸

> A comprehensive CNC guitar lutherie platform combining parametric design, structural analysis, CAM workflows, and Smart Guitar integration.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub](https://img.shields.io/badge/Deploy-GitHub-blue)](https://pages.github.com/)

---

## 🎯 Project Vision

The Luthier's Tool Box is a **web-based CAD/CAM platform** designed for guitar makers, combining:

- **Parametric Design Tools** – Rosettes, bracing, hardware layout calculators
- **CNC Workflows** – DXF export (R12 format), G-code generation and analysis
- **Multi-CAM Support** – Fusion 360, Mach4, VCarve, LinuxCNC (EMC2), Masso controller
- **GitHub Deployment** – Web service accessible from any device
- **Smart Guitar Project** – Integrated IoT/embedded lutherie (Raspberry Pi 5, Bluetooth)

**Core Philosophy**: Millimeter-first design, CAM-compatible geometry, and modular pipeline architecture for specialized lutherie calculations.

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
- **Python 3.11+** (for backend/pipelines)
- **Node.js 20+** (for Vue 3 frontend)
- **Git** (version control)

### **Option 1: Local Development**

```powershell
# Clone the repository
git clone https://github.com/<your-username>/luthiers-toolbox.git
cd luthiers-toolbox

# Server setup
cd server
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app:app --reload --port 8000

# Client setup (separate terminal)
cd client
npm install
npm run dev
```

Access the app at `http://localhost:5173`

### **Option 2: Docker Compose**

```powershell
docker compose up --build
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

| Platform | Post-Processor | G-code Dialect | Status |
|----------|----------------|----------------|--------|
| **Fusion 360** | JSON setup files | Fanuc/Haas | ✅ Primary |
| **Mach4** | Safety macros, auto-variables | Mach3/4 | ✅ Supported |
| **VCarve** | Standard post | Mach3 compatible | ✅ Supported |
| **LinuxCNC (EMC2)** | Custom post | RS274/NGC | 🔄 Placeholder |
| **Masso Controller** | G-code adapter | Masso G3 | 🔄 Placeholder |

**Configuration Files**:
- `Lutherier Project*/Les Paul_Project/09252025/Base_LP_Fusion_Package/FusionSetup_Base_LP_Mach4.json`
- `plugins/gibson/nc_lint_autovars.py` (Mach4 safety checks)

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design, data flows, integration patterns |
| [.github/copilot-instructions.md](.github/copilot-instructions.md) | AI agent development guide |
| [DEPLOYMENT.md](DEPLOYMENT.md) | GitHub Pages, Railway, Docker deployment |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Code style, PR process, feature integration |

---

## 🤝 Contributing

We welcome contributions! The MVP builds in `Luthiers Tool Box/` are **feature libraries**. To integrate a feature:

1. **Extract** the relevant pipeline from an MVP build
2. **Test** it standalone with example JSON configs
3. **Integrate** into the main `server/pipelines/` directory
4. **Document** in `ARCHITECTURE.md` feature catalog
5. **Submit PR** with tests and usage examples

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

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
