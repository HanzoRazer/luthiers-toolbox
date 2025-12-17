# Luthier's ToolBox - Main System Files List

**Date**: November 3, 2025  
**Purpose**: Quick reference for core project files

---

## 🗂️ Core System Files

### 📄 Application Entry Points

**Frontend**:
```
client/src/main.ts                    # Vue 3 application entry
client/src/App.vue                    # Root Vue component
client/index.html                     # HTML entry point
```

**Backend**:
```
server/app.py                         # FastAPI application (main server)
server/requirements.txt               # Python dependencies
```

---

## 🔧 Enhanced Tools (Ready to Use)

```
gcode_reader.py                       # ✅ Enhanced G-code parser (512 lines)
                                      # - Validation system
                                      # - Safety checks
                                      # - JSON/CSV export
                                      # - 90% Phase 1 complete
```

---

## 📁 Pipeline Modules (Backend)

### ✅ Existing/Partial Pipelines:
```
server/pipelines/gcode_explainer/
├── explain_gcode_ai.py              # AI-powered G-code explanation
└── (analyze_gcode.py to be created) # Wrapper for gcode_reader

server/pipelines/rosette/
├── rosette_calc.py                  # Rosette calculations (partial)
├── rosette_to_dxf.py                # DXF export (partial)
└── rosette_make_gcode.py            # G-code generation (to complete)

server/pipelines/hardware/
├── hardware_layout.py               # Electronics layout (partial)
└── hardware_to_dxf.py               # DXF export (partial)
```

### ⏳ To Be Created (Priority Order):
```
server/pipelines/string_spacing/     # 🔴 CRITICAL - Phase 2
├── benchmuse_spacer.py              # String spacing calculator
├── fretfind_calc.py                 # Fret position calculator
├── string_to_dxf.py                 # DXF export
└── api_wrapper.py                   # API endpoint

server/pipelines/bridge/              # 🟡 HIGH - Phase 3
├── bridge_calc.py                   # Bridge geometry
├── bridge_to_dxf.py                 # DXF export
└── api_wrapper.py                   # API endpoint

server/pipelines/neck/                # 🟢 MEDIUM - Phase 5
├── neck_profile.py                  # Neck profile generator
└── neck_to_dxf.py                   # DXF export
```

---

## 🎨 Vue Components (Frontend)

### ✅ Existing Components:
```
client/src/components/toolbox/
├── RosetteDesigner.vue              # Rosette design interface
└── HardwareLayout.vue               # Electronics cavity layout
```

### ⏳ To Be Created:
```
client/src/components/toolbox/
├── GcodeAnalyzer.vue                # 🟡 HIGH - Phase 1 (to create)
├── FretCalculator.vue               # 🔴 CRITICAL - Phase 2
├── BridgeCalculator.vue             # 🟡 HIGH - Phase 3
├── NeckGenerator.vue                # 🟢 MEDIUM - Phase 5
├── CadCanvas.vue                    # ⚪ LOW - Phase 5
└── LuthierCalculator.vue            # 🟢 MEDIUM

client/src/components/common/
├── FileUpload.vue                   # Reusable file upload
├── ExportControls.vue               # DXF/JSON export buttons
└── ValidationWarnings.vue           # Display warnings/errors
```

---

## 🛠️ Utility Libraries

### Backend (Python):
```
server/utils/
├── dxf_helpers.py                   # ⏳ To create - Common DXF operations
├── geometry_helpers.py              # ⏳ To create - Shapely utilities
└── validation.py                    # ⏳ To create - Input validation
```

### Frontend (TypeScript):
```
client/src/utils/
├── api.ts                           # ✅ Exists - API client (needs expansion)
├── geometry.ts                      # ⏳ To create - Geometry utilities
└── validators.ts                    # ⏳ To create - Form validation

client/src/types/
├── pipeline.types.ts                # ⏳ To create - Pipeline types
├── geometry.types.ts                # ⏳ To create - Geometry types
└── gcode.types.ts                   # ⏳ To create - G-code types
```

---

## 📦 Configuration Files

### Build & Dependencies:
```
client/
├── package.json                     # ✅ Node dependencies
├── vite.config.ts                   # ✅ Vite configuration
└── tsconfig.json                    # ✅ TypeScript config

server/
└── requirements.txt                 # ✅ Python dependencies
```

### Deployment:
```
docker-compose.yml                   # ✅ Full stack deployment
.github/workflows/ci.yml             # ✅ CI/CD pipeline
.gitignore                           # ✅ Git ignore rules
```

---

## 🧪 Test Files

### Existing:
```
test_sample.nc                       # ✅ Test G-code file (525 bytes)
test_output.json                     # ✅ Example JSON output
```

### To Be Created:
```
tests/
├── test_gcode_reader.py             # Unit tests for G-code parser
├── test_string_spacing.py           # String spacing tests
├── test_bridge_calc.py              # Bridge calculator tests
├── test_api_endpoints.py            # API integration tests
└── fixtures/
    ├── sample.nc                    # More test G-code files
    └── sample.dxf                   # Test DXF files
```

---

## 📚 Documentation Files

### Primary Handoff Documents (Read These First):
```
MASTER_INDEX.md                      # ✅ Start here - Complete navigation
DEVELOPER_HANDOFF.md                 # ✅ Onboarding guide (16 KB)
PIPELINE_DEVELOPMENT_STRATEGY.md     # ✅ Architecture (40 KB)
IMPLEMENTATION_CHECKLIST.md          # ✅ Daily tasks (17 KB)
SYSTEM_ARCHITECTURE.md               # ✅ Visual diagrams (54 KB)
STRUCTURAL_TREE_CODE_LIST.md         # ✅ File inventory (22 KB)
```

### Phase-Specific:
```
GCODE_READER_ENHANCED.md             # ✅ Phase 1 details (7 KB)
```

### Project Root:
```
README.md                            # ✅ Project overview (10 KB)
GETTING_STARTED.md                   # ✅ Setup guide (14 KB)
```

---

## 📂 Reference Directories

### MVP Feature Libraries (Extract Code From Here):
```
MVP Build_10-11-2025/                # Reference implementations
MVP Build_1012-2025/                 # Reference implementations
```

### Design Archives:
```
Lutherier Project/Les Paul_Project/
├── clean_cam_ready_dxf_windows_all_layers.py  # DXF cleaning script
└── 09252025/FusionSetup_Base_LP_Mach4.json    # Fusion 360 setup
```

---

## 🎯 Priority File Development Order

### Week 1 - Phase 1 (G-code Analyzer):
```
1. server/pipelines/gcode_explainer/analyze_gcode.py   (~100 lines)
2. client/src/components/toolbox/GcodeAnalyzer.vue     (~200 lines)
3. client/src/types/gcode.types.ts                     (~50 lines)
```

### Week 2-3 - Phase 2 (String Spacing - CRITICAL):
```
1. server/pipelines/string_spacing/benchmuse_spacer.py  (~300 lines)
2. server/pipelines/string_spacing/fretfind_calc.py     (~200 lines)
3. server/pipelines/string_spacing/string_to_dxf.py     (~250 lines)
4. server/pipelines/string_spacing/api_wrapper.py       (~150 lines)
5. client/src/components/toolbox/FretCalculator.vue     (~400 lines)
```

### Week 4 - Phase 3 (Bridge Calculator):
```
1. server/pipelines/bridge/bridge_calc.py               (~300 lines)
2. server/pipelines/bridge/bridge_to_dxf.py             (~200 lines)
3. server/pipelines/bridge/api_wrapper.py               (~150 lines)
4. client/src/components/toolbox/BridgeCalculator.vue   (~371 lines)
```

---

## 🔑 Critical Files Summary

**Must exist before starting development**:
- ✅ `server/app.py` - Main FastAPI server
- ✅ `client/src/main.ts` - Vue application
- ✅ `gcode_reader.py` - Enhanced G-code parser (Phase 1 - 90% done)

**Create these utilities first** (used by all pipelines):
- ⏳ `server/utils/dxf_helpers.py` - DXF R12 export functions
- ⏳ `server/utils/geometry_helpers.py` - Shapely operations
- ⏳ `client/src/utils/api.ts` - Expand with all endpoints

**Top 3 missing features** (in priority order):
1. 🔴 **String Spacing/FretFind** - CRITICAL (Phase 2)
2. 🟡 **Bridge Calculator** - HIGH (Phase 3)
3. 🟡 **G-code Analyzer UI** - HIGH (Phase 1 completion)

---

## 📊 File Count Summary

| Category | Existing | To Create | Total |
|----------|----------|-----------|-------|
| Backend Python | ~10 | ~25 | ~35 |
| Frontend Vue/TS | ~5 | ~15 | ~20 |
| Utilities | ~2 | ~8 | ~10 |
| Tests | 2 | ~10 | ~12 |
| Documentation | 18 | ~3 | ~21 |
| Configuration | ~8 | ~5 | ~13 |
| **Total** | **~45** | **~66** | **~111** |

**Current Completion**: ~40% of files exist, 10% fully complete

---

## 🚀 Quick Start Files

**To run the application**:
```powershell
# Terminal 1 (Backend)
cd server
.\.venv\Scripts\Activate.ps1
uvicorn app:app --reload --port 8000

# Terminal 2 (Frontend)
cd client
npm run dev

# Test G-code reader
python gcode_reader.py test_sample.nc --validate --pretty
```

**Key URLs**:
- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/docs
- API Base: http://localhost:8000/api

---

## 📝 Notes

- **All geometry in millimeters (mm)** - Never mix units
- **DXF format**: Always R12 (AC1009) for CAM compatibility
- **Closed paths only**: CNC requires closed LWPolylines
- **Python 3.11+** required for backend
- **Node.js 18+** required for frontend

---

**For complete file inventory with line counts, see**: `STRUCTURAL_TREE_CODE_LIST.md`  
**For development strategy, see**: `PIPELINE_DEVELOPMENT_STRATEGY.md`  
**For daily tasks, see**: `IMPLEMENTATION_CHECKLIST.md`

---

*Last Updated: November 3, 2025*  
*Status: Phase 1 at 90%, Ready for Phase 2*
