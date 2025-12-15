-LEARNED_DB: Dict[Tuple[str, str, str], LearnedOverride] = {}
+LEARNED_DB: Dict[Tuple[str, str, str, str], LearnedOverride] = {}

-def get_learned(tool_id: str, material: str, mode: str):
-    return LEARNED_DB.get((tool_id, material, mode))
+def get_learned(tool_id: str, material: str, mode: str, machine_profile: str):
+    return LEARNED_DB.get((tool_id, material, mode, machine_profile))# Compare Mode Bundle Roadmap (B20–B36 + Supporting Features)

**Date:** November 24, 2025  
**Status:** Active Development  
**Lead Module:** Compare Lab & CNC Production Integration

---

## 🎯 Overview

This roadmap tracks the **Compare Mode** feature set across 17 primary bundles (B20–B36) plus supporting enhancements for CurveLab and OffsetLab. Compare Mode enables side-by-side toolpath analysis, diff visualization, and preset-based workflow optimization for CNC guitar lutherie.

---

## 📦 Priority-Ordered Bundle Sequence

### **Phase 1: Foundation (B20–B22)** ✅ → 🚧

#### **B20 – PresetSourceTooltip / JobInt Schema + Preset Manager** ✅
**Status:** Landed (2025-11-23)  
**Effort:** 3-4 hours  
**Value:** Schema prerequisite for all compare features

**Delivered:**
- Extended JobInt JSONL schema with optional artifacts:
  - `geometry_loops` – Original boundary/island data
  - `plan_request` – Full adaptive pocket request payload
  - `moves` / `moves_path` – Toolpath move arrays
  - `baseline_id` – Lineage tracking for comparison runs
- JSON-backed preset store at `data/presets/presets.json`
- CRUD API: `/api/cnc/presets/*` (GET, POST, PATCH, DELETE)
- `PresetManagerPanel.vue` in CNC Production hub
- Lineage tooltips showing job source, machine, material, stats
- "Open in Adaptive Lab" link with `preset_id` query parameter
- Router redirect preserves query strings for lab navigation

**Files:**
- `services/api/app/services/job_int_log.py` – Schema extension
- `services/api/app/services/jobint_artifacts.py` – Artifact extraction helpers
- `services/api/app/services/preset_store.py` – JSON persistence
- `services/api/app/routers/cnc_production/presets_router.py` – API endpoints
- `client/src/cnc_production/PresetManagerPanel.vue` – UI component
- `client/src/views/CamProductionView.vue` – Integration mount point

**Smoke Test:** ✅ Verified (2025-11-24)
```powershell
# API validation
Invoke-RestMethod -Method Get http://localhost:8000/api/cnc/presets
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/cnc/presets -Body '{"name":"J45"}' -ContentType 'application/json'

# UI verification
# Visit http://localhost:5173/cam → Preset Manager shows created presets
```

**Documentation:** `docs/CNC_PRESET_MANAGER_B20.md`

---

#### **B21 – CompareRunsPanel** 🚧
**Status:** Planned (Next)  
**Effort:** 5-6 hours  
**Dependencies:** B20 (preset storage, JobInt artifacts)  
**Value:** Unlocks compare analytics in CNC Production hub

**Features:**
- Multi-select jobs (2-4 runs) via checkboxes in job history
- Side-by-side comparison table:
  - Machine profiles, materials, post-processors
  - Predicted vs actual time (when available)
  - Issue counts (errors/warnings breakdown)
  - Review gate pass rates
  - Parameter diffs (stepover, feed, depth)
- Diff highlighting (green ↑ improvement, red ↓ regression)
- "Set as Baseline" action to mark golden run
- Export comparison as CSV report

**Use Case:**
> Luthier tests 3 stepover values (40%, 50%, 60%) on same geometry. CompareRunsPanel shows 50% had fastest time AND fewest errors, proving optimal parameters with data.

**API Endpoints:**
- `GET /api/cnc/jobs/compare?ids=<id1>,<id2>,<id3>` – Fetch jobs for comparison
- Response includes full artifacts (loops, moves, stats) for diff computation

**UI Component:**
- `client/src/cnc_production/CompareRunsPanel.vue`
- Mounted in `CamProductionView.vue` below Preset Manager
- Table layout with metric rows × job columns
- Winner badge per metric (fastest time, fewest errors, etc.)

**Success Criteria:**
- ✅ Compare up to 4 jobs simultaneously
- ✅ Auto-detect winner per metric
- ✅ Export as CSV with timestamps
- ✅ Works across different machines/materials

---

#### **B22 – CompareMode_SvgDiffDualDisplay** 🎯 HIGH IMPACT
**Status:** Planned  
**Effort:** 8-10 hours  
**Dependencies:** B21 (job selection), B20 (artifact storage)  
**Value:** Core visual diff lab for side-by-side toolpath analysis

**Features:**
- Dedicated `/lab/compare` route with `CompareLab.vue` component
- Dual SVG canvas layout (split-screen):
  - **Left pane:** Baseline run (blue toolpath)
  - **Right pane:** Comparison run (orange toolpath)
- Overlay toggle: Show both paths on single canvas (diff mode)
- Color-coded delta highlights:
  - Green zones: Improved engagement/fewer retracts
  - Red zones: Increased load/collisions
- Zoom/pan synchronized across both panes
- Metric overlays: Time delta, length delta, retract count delta

**Router Integration:**
```typescript
// Navigate from CompareRunsPanel or Preset Manager
router.push({
  name: 'CompareLab',
  query: {
    baseline_id: 'uuid-baseline',
    compare_id: 'uuid-compare'
  }
})
```

**API Endpoint:**
- `GET /api/cam/compare/diff?baseline=<id>&compare=<id>`
- Returns diff payload with overlay annotations and statistics

**UI Component:**
- `client/src/views/labs/CompareLab.vue`
- `client/src/components/compare/DualSvgDisplay.vue`
- `client/src/components/compare/DeltaOverlays.vue`

**Success Criteria:**
- ✅ Dual canvas renders in <2 seconds for 500-move toolpaths
- ✅ Overlay mode highlights diffs with color coding
- ✅ Synchronized zoom/pan across both panes
- ✅ Export diff view as annotated SVG

---

### **Phase 2: Export & Naming (B23–B26)**

#### **B23 – CompareMode_ExportOverlays**
**Status:** Planned  
**Effort:** 3-4 hours  
**Dependencies:** B22 (CompareLab dual canvas)  
**Value:** Export functionality for production documentation

**Features:**
- "Export Diff" button in CompareLab toolbar
- Export formats:
  - **SVG:** Dual-pane layout with delta annotations
  - **PNG:** Rasterized screenshot at 300 DPI
  - **CSV:** Delta metrics table (time, length, retracts, collisions)
- Filename convention: `compare_<baseline>_vs_<compare>_<timestamp>.svg`
- Auto-inject metadata comments in SVG exports

**Success Criteria:**
- ✅ Export completes in <3 seconds
- ✅ SVG imports cleanly into Inkscape/Illustrator
- ✅ CSV opens in Excel with proper column headers

---

#### **B24 – CompareMode_ExportNamingAware**
**Status:** Planned  
**Effort:** 2-3 hours  
**Dependencies:** B23 (export infrastructure)  
**Value:** Traceable filenames for production archives

**Features:**
- User-friendly naming options in export dialog:
  - Preset names (if derived from presets)
  - Job IDs (fallback)
  - Custom prefix field
- Default pattern: `<prefix>_baseline-<name>_vs_<name>_<date>.ext`
- Example: `J45_baseline-aggressive_vs_conservative_20251124.svg`

**Success Criteria:**
- ✅ Preset names appear in export dialog
- ✅ Custom prefix persists to localStorage
- ✅ Filenames avoid special characters (sanitized)

---

#### **B25 – CompareMode_ExportPresetsAndFilenameOverride**
**Status:** Planned  
**Effort:** 3-4 hours  
**Dependencies:** B24 (naming system)  
**Value:** Preset-based export templates

**Features:**
- Save export settings as preset:
  - Format (SVG/PNG/CSV)
  - Filename template
  - Overlay toggles
  - Color scheme
- "Export Preset Manager" in CompareLab settings
- Apply preset on export: One-click export with saved config

**Success Criteria:**
- ✅ Export presets stored in `data/export_presets.json`
- ✅ Apply preset auto-fills export dialog
- ✅ Supports multiple export presets per user

---

#### **B26 – CompareMode_ExportPresetTemplateEditor**
**Status:** Planned  
**Effort:** 4-5 hours  
**Dependencies:** B25 (preset storage)  
**Value:** Advanced template customization

**Features:**
- Visual template editor in CompareLab settings:
  - Drag-and-drop filename tokens (`{baseline}`, `{compare}`, `{date}`)
  - Live preview of generated filename
  - Color picker for overlay annotations
  - Font size controls for SVG text labels
- Preset import/export (JSON file)
- Share presets across team via Git

**Success Criteria:**
- ✅ Template changes update live preview instantly
- ✅ Export presets importable via JSON file upload
- ✅ Backward compatible with B25 presets

---

### **Phase 3: UX Polish & Persistence (B27–B36)**

#### **B27–B36 – Compare Export UX Polish Sequence**
**Status:** Planned (Sequential Implementation)  
**Effort:** ~2-3 hours per bundle (avg)  
**Value:** Production-grade user experience

**Bundle Breakdown:**
- **B27:** Export progress indicator (spinner + ETA)
- **B28:** Batch export (select multiple diffs, export as ZIP)
- **B29:** Export history panel (recent exports with re-download)
- **B30:** Export notifications (toast on success/failure)
- **B31:** Export queue (handle multiple concurrent exports)
- **B32:** Auto-export on preset save (optional toggle)
- **B33:** Export size warnings (large SVG/PNG alert)
- **B34:** Export format validation (check DXF/SVG structure)
- **B35:** Export compression (ZIP bundle for multi-file exports)
- **B36:** Export metadata injection (preserve lineage in file headers)

**Dependencies:** Each bundle depends on previous (B27 → B28 → ... → B36)

**Success Criteria Per Bundle:**
- ✅ Feature tested in isolation
- ✅ No regressions in previous bundles
- ✅ User-facing docs updated

---

## 🎨 Supporting Features (Parallel Development)

### **Bundle CL-B: CurveLab Modal + DXF Preflight Integration**
**Status:** Planned (Independent)  
**Effort:** 6-8 hours  
**Value:** Separate feature, active in project todo

**Features:**
- Modal overlay for curve-based geometry editing
- DXF preflight validator integration (checks before CAM)
- Curve smoothing tools (arc fitting, corner rounding)
- Export cleaned geometry back to CAM pipeline

**Component:**
- `client/src/views/labs/CurveLab.vue`
- `client/src/components/toolbox/DxfPreflightValidator.vue` (existing)

**Success Criteria:**
- ✅ Modal opens from CAM Production or Art Studio
- ✅ DXF validation runs before CAM operations
- ✅ Cleaned geometry exports to adaptive pocket planner

---

### **Patch N.18 + N18.1–N18.6: OffsetLab Visual Enhancements**
**Status:** Planned (Post-CurveLab)  
**Effort:** ~2-3 hours per patch  
**Value:** Independent visual improvements for OffsetLab

**Patch Series:**
- **N.18:** Base offset visualization overhaul
- **N18.1:** Color-coded offset rings (depth gradient)
- **N18.2:** Island highlight mode (red keepout zones)
- **N18.3:** Smoothing preview (real-time arc tolerance slider)
- **N18.4:** Offset statistics HUD (ring count, area coverage)
- **N18.5:** Export offset stack as multi-layer DXF
- **N18.6:** Offset animation (ring-by-ring playback)

**Component:**
- `client/src/views/labs/OffsetLab.vue` (future)

**Success Criteria:**
- ✅ Each patch ships independently
- ✅ No breaking changes to adaptive pocket engine
- ✅ Visual enhancements improve operator clarity

---

## 🔄 Integration Points

### **Cross-Module Dependencies**

```
B20 (Preset Manager)
  ↓
B21 (CompareRunsPanel) → Uses presets for job selection
  ↓
B22 (CompareLab Dual Display) → Core visual diff engine
  ↓
B23–B26 (Export Infrastructure) → Production documentation
  ↓
B27–B36 (UX Polish) → Incremental refinements
```

### **Supporting Features (Parallel Tracks)**
```
CL-B (CurveLab) → Independent modal, integrates with CAM Production
N.18 Series (OffsetLab) → Visual enhancements, no dependencies on Compare Mode
```

---

## 📋 Implementation Checklist

### **B20 ✅ Complete**
- [x] JobInt schema extension (artifacts)
- [x] Preset store JSON persistence
- [x] CRUD API endpoints
- [x] PresetManagerPanel.vue component
- [x] Router query string preservation
- [x] Smoke test validation
- [x] Documentation (CNC_PRESET_MANAGER_B20.md)

### **B21 🚧 Next Up**
- [ ] Job comparison API endpoint
- [ ] CompareRunsPanel.vue component
- [ ] Multi-select checkbox UI in job history
- [ ] Side-by-side metric table
- [ ] CSV export functionality
- [ ] Winner badge logic per metric
- [ ] Integration tests with B20 presets

### **B22 🎯 High Priority**
- [ ] CompareLab.vue route and component
- [ ] DualSvgDisplay.vue split canvas
- [ ] Delta overlay computation
- [ ] Color-coded diff highlights
- [ ] Synchronized zoom/pan
- [ ] Export diff as SVG
- [ ] API endpoint for diff payloads

### **B23–B36 ⏸️ Queued**
- [ ] Sequential implementation post-B22
- [ ] Each bundle requires smoke test
- [ ] Docs per bundle in `docs/` folder

### **CL-B + N.18 Series ⏸️ Parallel Track**
- [ ] CurveLab modal after B22
- [ ] OffsetLab enhancements after CurveLab
- [ ] Independent testing from Compare Mode

---

## 🧪 Testing Strategy

### **Per-Bundle Smoke Tests**
Each bundle (B20–B36) requires:
1. **API validation:** PowerShell `Invoke-RestMethod` calls
2. **UI verification:** Manual browser testing at `localhost:5173`
3. **Regression check:** Ensure previous bundles still work
4. **Documentation:** Update quickref and integration docs

### **CI Integration**
- GitHub Actions workflow per major bundle (B20, B21, B22)
- Proxy tests for full stack validation
- Badge system for pass/fail status

---

## 📚 Documentation Structure

### **Bundle-Specific Docs (Created Per Bundle)**
```
docs/
├── CNC_PRESET_MANAGER_B20.md          ✅ Complete
├── COMPARE_RUNS_PANEL_B21.md          🚧 Next
├── COMPARE_LAB_DUAL_DISPLAY_B22.md    📋 Planned
├── COMPARE_EXPORT_OVERLAYS_B23.md     📋 Planned
├── ...
└── COMPARE_EXPORT_METADATA_B36.md     📋 Planned
```

### **Quickref Docs (High-Level Summaries)**
```
COMPARE_MODE_QUICKREF.md               📋 To be created after B22
COMPARE_EXPORT_QUICKREF.md             📋 To be created after B26
```

---

## 🎯 Success Metrics

### **Phase 1 Complete (B20–B22)**
- ✅ Preset Manager operational with job lineage
- ✅ Job comparison table shows side-by-side metrics
- ✅ CompareLab renders dual-canvas diff view
- ✅ Export baseline: SVG diff with annotations

### **Phase 2 Complete (B23–B26)**
- ✅ Export infrastructure supports SVG/PNG/CSV
- ✅ Filename templates use preset names
- ✅ Export presets stored and reusable
- ✅ Template editor allows customization

### **Phase 3 Complete (B27–B36)**
- ✅ Production-grade UX with progress indicators
- ✅ Batch export and queue system
- ✅ Export history panel for re-downloads
- ✅ Metadata injection preserves lineage

### **Supporting Features Complete**
- ✅ CurveLab modal integrated with CAM Production
- ✅ OffsetLab visual enhancements complete (N.18–N18.6)

---

## 🚀 Next Actions

**Immediate (Week of 2025-11-24):**
1. ✅ Complete B20 smoke test validation
2. 🚧 Implement B21 CompareRunsPanel API endpoint
3. 🚧 Build CompareRunsPanel.vue component
4. 🚧 Test multi-job selection and metric diff table

**Short-Term (Next 2 Weeks):**
1. 📋 Implement B22 CompareLab with dual canvas
2. 📋 Test SVG diff export functionality
3. 📋 Document B21 and B22 in quickref format

**Long-Term (Next Month):**
1. 📋 Complete B23–B26 export infrastructure
2. 📋 Begin B27–B36 UX polish sequence
3. 📋 Integrate CurveLab and OffsetLab enhancements

---

**Roadmap Status:** 🟢 Active  
**Lead Developer:** [Your Team]  
**Last Updated:** November 24, 2025
