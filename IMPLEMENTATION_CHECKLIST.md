# Pipeline Implementation Checklist

**Project**: Luthier's ToolBox  
**Purpose**: Step-by-step implementation guide for developers  
**Version**: 1.0 - November 3, 2025

---

## Quick Start Commands

```powershell
# Clone and setup
git clone <repo-url>
cd "Luthiers ToolBox"

# Server setup
cd server
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app:app --reload --port 8000

# Client setup (separate terminal)
cd client
npm install
npm run dev  # Runs on http://localhost:5173
```

---

## Phase 0: CNC ROI Financial Calculator (COMPLETE)
**Status**: 95% Complete ✅ | **Est. Time**: 30 min remaining | **Developer**: AI Agent

### Backend Tasks ✅
- [x] ✅ Created `server/pipelines/financial/cnc_roi_calculator.py` (450 lines)
  - 6 dataclass models (Equipment, Operating, Labor, Materials, Revenue, ROI)
  - Complete financial calculations (NPV, payback, ROI%, cash flow)
  - CLI interface with JSON input/output
  - **TESTED**: 4-month payback, 1361% ROI, $99K annual benefit

- [x] ✅ Created `server/configs/examples/financial/cnc_roi_example.json`
  - Realistic defaults ($34K investment, 50 guitars/year)
  - All parameters documented with comments

- [x] ✅ Added endpoint to `server/app.py`
  ```python
  from pipelines.financial import cnc_roi_calculator
  
  @app.post("/api/pipelines/financial/cnc-roi")
  async def calculate_cnc_roi(params: dict):
      result = cnc_roi_calculator.calculate_roi(params)
      return JSONResponse(content=result)
  ```

### Frontend Tasks ✅
- [x] ✅ Created `client/src/components/toolbox/CNCROICalculator.vue` (580 lines)
  - 5-tab interface: Equipment, Operating, Labor, Results, Charts
  - Real-time calculations with reactive forms
  - Export to JSON functionality
  - Reset to defaults button
  - Break-even highlighting in year-by-year table

### Integration Tasks ⏳
- [ ] Add `calculateCNCROI()` to `client/src/utils/api.ts` (~15 min)
  ```typescript
  export async function calculateCNCROI(params: any): Promise<any> {
    const res = await fetch('/api/pipelines/financial/cnc-roi', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    })
    return res.json()
  }
  ```

- [ ] Update `client/src/App.vue` navigation (~5 min)
  ```vue
  <button @click="active='cnc-roi'">💰 CNC ROI Calculator</button>
  <CNCROICalculator v-else-if="active==='cnc-roi'" />
  ```

- [ ] Update CNCROICalculator.vue to call API instead of local calculation (~10 min)

### Testing ✅
- [x] ✅ CLI test: `python cnc_roi_calculator.py --json-in example.json`
- [x] ✅ Validation: Payback 0.34 years, NPV $362K, ROI 1361%
- [ ] API test: `Invoke-RestMethod http://localhost:8000/api/pipelines/financial/cnc-roi`
- [ ] End-to-end: Navigate to calculator in UI, enter params, calculate, export

### Documentation ✅
- [x] ✅ `CNC_ROI_CALCULATOR_INTEGRATION.md` (900 lines)
- [x] ✅ `API_INTEGRATION_CHECKLIST_FINANCIAL_CALCULATOR.md` (400 lines)
- [x] ✅ `CNC_ROI_CALCULATOR_QUICK_SUMMARY.md` (350 lines)
- [x] ✅ `TESTING_CNC_ROI_CALCULATOR_NOW.md` (400 lines)

### Success Criteria ✅
- [x] Backend produces realistic ROI calculations
- [x] CLI interface works with JSON files
- [x] API endpoint integrated into server
- [x] Vue component UI complete with 5 tabs
- [ ] End-to-end test passes (client → API → results display)

**Next Action**: Complete client-side integration (30 minutes)

---

## Phase 1: G-code Analyzer (HIGH PRIORITY)
**Status**: 90% Complete | **Est. Time**: 1-2 days | **Developer**: TBD

### Backend Tasks
- [x] ✅ Enhanced gcode_reader.py with validation
- [ ] Create `server/pipelines/gcode_explainer/analyze_gcode.py`
  ```python
  from pathlib import Path
  from .gcode_reader import parse_gcode
  
  async def analyze_uploaded_gcode(file_content: bytes, filename: str, validate: bool = True):
      # Save to temp file, parse, return results
      pass
  ```

- [ ] Add endpoint to `server/app.py`
  ```python
  from pipelines.gcode_explainer.analyze_gcode import analyze_uploaded_gcode
  
  @app.post("/api/gcode/analyze")
  async def analyze_gcode(file: UploadFile, validate: bool = True):
      content = await file.read()
      result = await analyze_uploaded_gcode(content, file.filename, validate)
      return {"success": True, "summary": result}
  ```

### Frontend Tasks
- [ ] Create `client/src/types/gcode.types.ts`
  ```typescript
  export interface GcodeSummary {
    units: string
    absolute: boolean
    line_count: number
    motion_count: number
    bbox_min: [number, number, number]
    bbox_max: [number, number, number]
    warnings: string[]
    errors: string[]
  }
  ```

- [ ] Create `client/src/components/toolbox/GcodeAnalyzer.vue`
  - File upload component
  - Summary display with formatted output
  - Warnings/errors section
  - Export JSON/CSV buttons

- [ ] Add API function to `client/src/utils/api.ts`
  ```typescript
  export async function analyzeGcode(file: File, validate: boolean = true): Promise<GcodeSummary> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('validate', String(validate))
    
    const response = await fetch('/api/gcode/analyze', {
      method: 'POST',
      body: formData
    })
    
    return response.json()
  }
  ```

### Testing
- [ ] Test with `test_sample.nc` file
- [ ] Test with large G-code file (>1MB)
- [ ] Test validation warnings display
- [ ] Test JSON export download

### Success Criteria
- [ ] Upload G-code file through UI
- [ ] Display parsed summary with bbox, travel, time
- [ ] Show warnings (Z below zero, high speeds, etc.)
- [ ] Download JSON/CSV exports
- [ ] Response time < 2 seconds for typical files

---

## Phase 2: BenchMuse StringSpacer (CRITICAL PRIORITY)
**Status**: Not Started | **Est. Time**: 3-5 days | **Developer**: TBD

### Research & Planning
- [ ] Locate BenchMuse StringSpacer code in MVP builds
  - Check: `MVP Build_10-11-2025/`
  - Check: `MVP Build_1012-2025/`
  - Extract algorithm, understand parameters

- [ ] Locate FretFind integration code
  - Check: MVP builds for fret calculation
  - Document fret position formulas

- [ ] Define API contract
  ```typescript
  interface StringSpacingRequest {
    scale_length_mm: number
    string_count: number
    nut_width_mm: number
    bridge_width_mm: number
    spacing_type: "even" | "tapered"
    fret_count: number
  }
  ```

### Backend Implementation
- [ ] Create `server/pipelines/string_spacing/`
- [ ] Port `benchmuse_spacer.py` from MVP
  ```python
  @dataclass
  class StringSpacingParams:
      scale_length_mm: float
      string_count: int
      nut_width_mm: float
      bridge_width_mm: float
      spacing_type: str  # "even" or "tapered"
  
  def calculate_string_positions(params: StringSpacingParams) -> List[float]:
      # BenchMuse algorithm
      pass
  ```

- [ ] Port `fretfind_calc.py`
  ```python
  def calculate_fret_positions(
      scale_length_mm: float,
      fret_count: int = 24,
      compensation_mm: float = 0.0
  ) -> List[float]:
      # FretFind algorithm (12-TET)
      # Distance from nut: scale_length - (scale_length / (2^(n/12)))
      pass
  ```

- [ ] Create `string_to_dxf.py`
  - Export nut template (string positions, slot depth)
  - Export bridge template (string positions, saddles)
  - Export fretboard (fret slot positions)
  - All as separate layers in one DXF

- [ ] Add API endpoint
  ```python
  @app.post("/api/string-spacing/calculate")
  async def calculate_string_spacing(request: StringSpacingRequest):
      # Calculate positions
      # Generate DXF
      # Return results + file
      pass
  ```

### Frontend Implementation
- [ ] Create `client/src/components/toolbox/FretCalculator.vue`
  - Input form (scale length, string count, nut/bridge width)
  - Spacing type selector (even/tapered radio buttons)
  - Fret count slider (0-27)
  - Real-time preview canvas
  - Export DXF button

- [ ] Add preview visualization
  - Draw nut with string positions
  - Draw bridge with string positions
  - Draw fretboard with fret lines
  - Scale to fit canvas
  - Show measurements

### Testing
- [ ] Test 6-string standard (648mm scale, 43mm nut, 54mm bridge)
- [ ] Test 7-string extended range
- [ ] Test 12-string (doubled strings)
- [ ] Test classical (52mm nut, even spacing)
- [ ] Verify fret positions match FretFind reference
- [ ] Import DXF into Fusion 360, verify dimensions

### Success Criteria
- [ ] Calculate string positions accurately
- [ ] Generate fret positions (12-TET)
- [ ] Export DXF with nut/bridge/fret templates
- [ ] DXF imports cleanly into CAM software
- [ ] All dimensions within ±0.01mm of reference

---

## Phase 3: Bridge Calculator (HIGH PRIORITY)
**Status**: Not Started | **Est. Time**: 2-3 days | **Developer**: TBD

### Research & Planning
- [ ] Extract BridgeCalculator.vue (371 lines) from MVP
- [ ] Document saddle compensation algorithms
- [ ] Define integration with string spacing

### Backend Implementation
- [ ] Create `server/pipelines/bridge/bridge_calc.py`
  ```python
  @dataclass
  class BridgeParams:
      string_spacing: List[float]  # From string_spacing pipeline
      scale_length_mm: float
      compensation_per_string_mm: List[float]  # Optional overrides
      bridge_thickness_mm: float
      saddle_slot_width_mm: float
  
  def calculate_bridge_geometry(params: BridgeParams) -> BridgeResult:
      # Calculate saddle positions with compensation
      # Calculate string holes
      # Generate outline geometry
      pass
  ```

- [ ] Create `bridge_to_dxf.py`
  - Bridge outline
  - Saddle slot (with compensation)
  - String holes
  - Mounting holes (optional)

- [ ] Add API endpoint
  ```python
  @app.post("/api/bridge/calculate")
  async def calculate_bridge(request: BridgeRequest):
      # Calculate geometry
      # Generate DXF
      # Return results
      pass
  ```

### Frontend Implementation
- [ ] Update BridgeCalculator.vue for integration
- [ ] Add string spacing import
- [ ] Add compensation adjustment UI
- [ ] Add preview with saddle positions

### Testing
- [ ] Test with standard Tune-o-matic geometry
- [ ] Test with acoustic bridge
- [ ] Test with Floyd Rose dimensions
- [ ] Verify compensation calculations
- [ ] Import DXF, verify pocket routes correctly

### Success Criteria
- [ ] Integrate with string spacing calculator
- [ ] Calculate accurate saddle compensation
- [ ] Export CNC-ready DXF
- [ ] Preview shows correct geometry

---

## Phase 4: Rosette & Hardware (MEDIUM PRIORITY)
**Status**: Partial | **Est. Time**: 2-3 days | **Developer**: TBD

### Rosette Pipeline
- [ ] Complete rosette calculation integration
- [ ] Test rosette_to_dxf.py exports
- [ ] Test rosette_make_gcode.py toolpaths
- [ ] Verify G-code runs on CNC without errors
- [ ] Document soundhole diameter ranges

### Hardware Pipeline
- [ ] Complete hardware layout integration
- [ ] Add pickup cavity templates (humbucker, P90, single-coil)
- [ ] Add control cavity templates
- [ ] Add jack hole templates
- [ ] Export multi-layer DXF (pockets, through-holes)

### Testing
- [ ] Rosette: 88mm soundhole (standard classical)
- [ ] Hardware: Les Paul layout (2 humbucker, 2 volume, 2 tone)
- [ ] Hardware: Stratocaster layout (3 single-coil, 1 volume, 2 tone)
- [ ] Import into VCarve, generate toolpaths

---

## Phase 5: Neck Generator & CAD Canvas (LOW PRIORITY)
**Status**: Not Started | **Est. Time**: 5-7 days | **Developer**: TBD

### Neck Generator
- [ ] Research neck profile shapes (C, D, V, U)
- [ ] Implement parametric profile generator
- [ ] Integrate fret positions from string_spacing
- [ ] Export side view DXF
- [ ] Export top view DXF (fingerboard)
- [ ] Add truss rod channel option

### CAD Canvas
- [ ] Create drawing tools (line, arc, circle, rectangle)
- [ ] Add dimension constraints
- [ ] Add grid snap
- [ ] Export to DXF
- [ ] Add layer management

---

## Common Utilities to Create

### DXF Helpers (`server/utils/dxf_helpers.py`)
```python
def create_r12_dxf(filename: str) -> ezdxf.Drawing:
    """Create R12 DXF with standard setup."""
    doc = ezdxf.new("R12")
    # Add standard layers
    doc.layers.new("GEOMETRY", dxfattribs={"color": 7})
    doc.layers.new("DIMENSIONS", dxfattribs={"color": 3})
    doc.layers.new("TEXT", dxfattribs={"color": 2})
    return doc

def add_closed_polyline(msp, points: List[Tuple[float, float]], layer: str = "GEOMETRY"):
    """Add closed polyline (required for CAM)."""
    if len(points) >= 2:
        closed_points = points + [points[0]]
        msp.add_lwpolyline(closed_points, dxfattribs={"layer": layer, "closed": True})

def add_dimension_line(msp, start, end, text: str, layer: str = "DIMENSIONS"):
    """Add dimension line with text."""
    # Implementation
    pass
```

### Geometry Helpers (`server/utils/geometry_helpers.py`)
```python
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union

def chain_segments(segments: List, tolerance: float = 0.12) -> List[Polygon]:
    """Chain line/arc segments into closed polygons."""
    # Implementation
    pass

def calculate_bbox(points: List[Tuple[float, float]]) -> dict:
    """Calculate bounding box."""
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return {
        "min": (min(xs), min(ys)),
        "max": (max(xs), max(ys)),
        "width": max(xs) - min(xs),
        "height": max(ys) - min(ys)
    }
```

### API Client (`client/src/utils/api.ts`)
```typescript
const API_BASE = import.meta.env.DEV ? 'http://localhost:8000' : ''

export async function apiPost<T>(endpoint: string, data: any): Promise<T> {
  const response = await fetch(`${API_BASE}/api${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  })
  
  if (!response.ok) {
    throw new Error(`API Error: ${response.statusText}`)
  }
  
  return response.json()
}

export async function downloadFile(base64: string, filename: string) {
  const blob = base64ToBlob(base64)
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
```

---

## Integration Checklist (For Each Pipeline)

**Before Starting**:
- [ ] Read pipeline documentation
- [ ] Review reference implementation (MVP builds)
- [ ] Define API contract (request/response types)
- [ ] Write example usage

**Backend**:
- [ ] Create pipeline directory structure
- [ ] Implement calculation module
- [ ] Write unit tests (pytest)
- [ ] Implement DXF export
- [ ] Test DXF imports in CAM software
- [ ] Create API wrapper
- [ ] Add endpoint to app.py
- [ ] Test API with Postman/curl
- [ ] Document endpoint in API.md

**Frontend**:
- [ ] Create TypeScript types
- [ ] Create Vue component
- [ ] Add API client functions
- [ ] Implement form validation
- [ ] Add preview visualization
- [ ] Add export functionality
- [ ] Write component tests
- [ ] Test in browser (Chrome, Firefox, Safari)
- [ ] Document component usage

**Integration Testing**:
- [ ] Test full workflow (input → calculate → export → import to CAM)
- [ ] Test error handling (invalid inputs, network errors)
- [ ] Test with various parameter combinations
- [ ] Performance test (response times)
- [ ] Test on Windows + Linux

**Documentation**:
- [ ] Update PIPELINE_DEVELOPMENT_STRATEGY.md
- [ ] Add pipeline to API.md
- [ ] Add usage examples
- [ ] Record demo video

---

## Developer Daily Workflow

### Morning Routine
1. Pull latest changes: `git pull origin main`
2. Check issue tracker for assigned tasks
3. Review any overnight PR feedback
4. Start development server: `uvicorn app:app --reload`
5. Start client dev server: `npm run dev`

### Development Cycle
1. Create feature branch: `git checkout -b feature/<pipeline-name>`
2. Write failing test first (TDD)
3. Implement feature
4. Make test pass
5. Refactor code
6. Commit with descriptive message: `git commit -m "feat: add string spacing calculator"`
7. Push to GitHub: `git push origin feature/<pipeline-name>`
8. Create Pull Request
9. Address review comments
10. Merge when approved

### Evening Routine
1. Commit all work (even if incomplete)
2. Update task checklist in this document
3. Add notes for tomorrow in issue comments
4. Push to GitHub

---

## Code Review Checklist

**Reviewer checks**:
- [ ] Code follows naming conventions
- [ ] All units are in millimeters
- [ ] Functions have docstrings
- [ ] Tests are included and pass
- [ ] No hardcoded paths (use Path objects)
- [ ] Error handling is comprehensive
- [ ] DXF exports are R12 format
- [ ] API responses include warnings/errors
- [ ] Vue components are responsive
- [ ] TypeScript types are accurate
- [ ] No console.log() in production code
- [ ] Performance is acceptable (<500ms API response)

---

## Troubleshooting Guide

### DXF won't import to Fusion 360
- **Check**: Is it R12 format? (`ezdxf.new("R12")`)
- **Check**: Are polylines closed? (add first point at end)
- **Check**: Are all coordinates finite? (no NaN/Infinity)
- **Solution**: Use `clean_cam_ready_dxf_windows_all_layers.py`

### API endpoint returns 422
- **Cause**: Pydantic validation error
- **Solution**: Check request JSON matches model exactly
- **Debug**: Look at FastAPI docs page (`/docs`) for schema

### Vue component not reactive
- **Cause**: Not using `ref()` or `reactive()`
- **Solution**: Wrap state in `ref()` for primitives
- **Debug**: Check Vue DevTools for reactivity

### Tests failing in CI but passing locally
- **Cause**: Different Python/Node versions
- **Solution**: Use exact versions from CI config
- **Check**: `.github/workflows/ci.yml` for versions

---

## Resources for Developers

### Documentation
- **FastAPI**: https://fastapi.tiangolo.com/
- **Vue 3**: https://vuejs.org/guide/introduction.html
- **ezdxf**: https://ezdxf.readthedocs.io/
- **Shapely**: https://shapely.readthedocs.io/
- **Pydantic**: https://docs.pydantic.dev/

### Internal Docs
- `PIPELINE_DEVELOPMENT_STRATEGY.md` - Architecture overview
- `API.md` - API endpoint documentation
- `DXF_EXPORT.md` - DXF format specifications
- `DEVELOPER_GUIDE.md` - Onboarding guide

### Tools
- **VS Code Extensions**: Python, Vue, ESLint, Pylance
- **API Testing**: Postman, Thunder Client (VS Code)
- **DXF Viewing**: LibreCAD, DraftSight (free), Fusion 360
- **G-code Simulation**: CAMotics, NCViewer

---

## Questions & Support

**Have questions?**
- Check documentation first (this file + linked docs)
- Search GitHub Issues for similar problems
- Ask in #luthiers-toolbox Slack channel
- Create GitHub Discussion for architecture questions
- Create GitHub Issue for bugs

**Need help?**
- Tag `@lead-developer` in Slack
- Schedule pair programming session
- Request code review early and often

---

**Document Status**: ✅ Ready for Use  
**Last Updated**: November 3, 2025  
**Next Review**: After Phase 1 completion
