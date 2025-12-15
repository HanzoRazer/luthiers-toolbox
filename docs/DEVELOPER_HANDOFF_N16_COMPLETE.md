# Developer Handoff Document — N16 Phase Complete + Active Workstreams

**Purpose:** This document allows any developer or AI agent to immediately reconstruct the state of the Luthier's Tool Box repository and continue development without needing the original conversation history.

**Last Updated:** December 1, 2025  
**Repository:** luthiers-toolbox (HanzoRazer)  
**Branch:** main

---

## 1. Executive Summary

### **Completed Work (Ready for Testing)**

**N16 Phase — CNC Rosette Export Enhancement (7 Bundles)**
- N16.0: Ring arc geometry with polar-to-cartesian conversion ✅
- N16.1: Z-depth computation from ring width ✅
- N16.2: Multi-pass Z stepping (≤0.6mm per pass) ✅
- N16.3: G-code skeleton generator ✅
- N16.4: Material-specific spindle/feed presets ✅
- N16.5: Machine profile variants (GRBL/FANUC) ✅
- N16.6: Query parameter support for profiles/tools ✅
- N16.7: Hardware-tuned machine configs (BCM 2030CA, Fanuc Demo) ✅

**Bundle B41 — UnifiedPresets Backend Skeleton**
- JSON-based preset store with CRUD operations ✅
- FastAPI router at `/api/presets` ✅
- Support for cam/export/neck/combo preset kinds ✅

**Bundle #13 Extended — CNC History + Job Detail**
- Row-level risk tinting in history view ✅
- Click-through navigation to job detail ✅
- Markdown → HTML rendering in operator reports ✅

### **Active Workstreams (Not Yet Started)**

**CompareLab B22.8**
- Dual-SVG comparison with overlay/delta-only fallback
- Need: autoscale, Reset View, skeleton state, toast hints

**CAM Offset N.17b**
- Pyclipper polygon offset with G2/G3 arc emission
- Need: CI PowerShell smoke test, router verification

---

## 2. Repository Structure (Critical Paths)

```
luthiers-toolbox/
├── services/api/app/               # FastAPI backend
│   ├── main.py                     # Router registration
│   ├── api/routes/                 # API endpoints
│   │   ├── rmos_rosette_api.py     # RMOS CNC export (N16.x)
│   │   └── presets_router.py       # Unified presets (B41) 🆕
│   ├── cam/rosette/                # Rosette CNC core
│   │   ├── cnc/                    # CNC toolchain modules
│   │   │   ├── cnc_ring_toolpath.py       # N16.0/N16.2 arc geometry
│   │   │   ├── cnc_gcode_exporter.py      # N16.3/N16.5 G-code gen
│   │   │   ├── cnc_materials.py           # N16.4 material presets 🆕
│   │   │   └── cnc_machine_profiles.py    # N16.7 machine configs 🆕
│   │   └── rosette_cnc_wiring.py   # N16.1/N16.2/N16.4 integration
│   ├── util/
│   │   └── presets_store.py        # B41 JSON preset CRUD 🆕
│   └── data/
│       └── presets.json            # B41 preset storage 🆕
├── packages/client/src/            # Vue 3 frontend
│   ├── views/
│   │   ├── RMOSCncHistoryView.vue  # Bundle #13 history with row tints
│   │   └── RMOSCncJobDetailView.vue # Bundle #13 job detail with MD→HTML
│   └── components/
│       └── compare/
│           └── DualSvgDisplay.vue   # CompareLab B22.x (needs polish)
├── scripts/                        # PowerShell test suites
│   ├── test_adaptive_l1.ps1        # L.1 island tests
│   ├── test_adaptive_l2.ps1        # L.2 spiralizer tests
│   └── smoke_v161_helical.ps1      # v16.1 helical ramping
├── docs/                           # Architecture & patch notes
│   ├── .github/copilot-instructions.md  # Primary AI guidance
│   ├── AGENTS.md                   # Codex agent rules
│   ├── ADAPTIVE_POCKETING_MODULE_L.md   # Module L overview
│   ├── PATCH_L*_SUMMARY.md         # L.1/L.2/L.3 implementation docs
│   └── MACHINE_PROFILES_MODULE_M.md     # Module M overview
└── .github/workflows/              # CI/CD pipelines
    ├── adaptive_pocket.yml         # Module L tests
    └── proxy_parity.yml            # Full stack integration tests
```

---

## 3. N16 Phase — Technical Deep Dive

### **N16.0 — Ring Arc Geometry Core**

**File:** `services/api/app/cam/rosette/cnc/cnc_ring_toolpath.py`

**Key Functions:**
- `_polar_to_cartesian()`: Converts (radius, theta_deg) → (x, y) with jig rotation
- `build_ring_arc_toolpaths()`: Single-pass chord segments
- `build_ring_arc_toolpaths_multipass()`: Multi-pass variant (N16.2)

**Geometry:**
```python
# Polar → Cartesian with jig alignment
total_deg = theta_deg + rotation_deg
theta_rad = radians(total_deg)
x = origin_x_mm + radius_mm * cos(theta_rad)
y = origin_y_mm + radius_mm * sin(theta_rad)
```

**Example:** 24 slices × 3 Z-passes = 72 total segments

### **N16.1 — Z-Depth Integration**

**File:** `services/api/app/cam/rosette/rosette_cnc_wiring.py`

**Key Functions:**
- `_compute_cut_depth_mm()`: Z-depth = min(width_mm * 0.5, 2.0mm)
- Metadata enrichment: `origin`, `segment_count`

**Examples:**
- 3mm ring width → -1.5mm target depth
- 5mm ring width → -2.0mm (clamped)

### **N16.2 — Multi-pass Z Stepping**

**Key Functions:**
- `_compute_z_passes_mm()`: Distributes depth into 2-4 passes
- Algorithm: `num_passes = ceil(depth / max_step)`

**Examples:**
- target=-1.5mm, max_step=0.6mm → 3 passes: [-0.5, -1.0, -1.5]
- target=-1.8mm, max_step=0.6mm → 3 passes: [-0.6, -1.2, -1.8]

### **N16.3 — G-code Skeleton Generator**

**File:** `services/api/app/cam/rosette/cnc/cnc_gcode_exporter.py`

**Key Types:**
- `MachineProfile`: "grbl" | "fanuc"
- `GCodePostConfig`: profile, program_number, safe_z, spindle_rpm, tool_id

**Output Format:**
```gcode
( RMOS Studio Rosette Ring 1 )
G21  ; mm
G90  ; absolute
T1 M6  ; tool change
G0 Z5.000
M3 S16000
[toolpath moves]
M5        ; spindle stop
G0 X0 Y0  ; return home
M30       ; program end
```

### **N16.4 — Material Presets**

**File:** `services/api/app/cam/rosette/cnc/cnc_materials.py`

**Material Profiles:**
```python
HARDWOOD:  feed=800, spindle=16000, max_z_step=0.5mm
SOFTWOOD:  feed=900, spindle=17000, max_z_step=0.6mm
COMPOSITE: feed=600, spindle=14000, max_z_step=0.4mm
```

**Integration:** `rosette_cnc_wiring.py` uses `select_material_feed_rule()`

### **N16.5 — Machine Profile Variants**

**GRBL vs FANUC:**
- **GRBL**: Semicolon comments, `M3 S{rpm}` format
- **FANUC**: O-number programs, `S{rpm} M3` format, no semicolons

**Tool Changes:** Both emit `Tn M6` at program start

### **N16.7 — Hardware-Tuned Configs**

**File:** `services/api/app/cam/rosette/cnc/cnc_machine_profiles.py`

**Pre-configured Machines:**
1. **BCM 2030CA Router** (`bcm_2030ca`)
   - Profile: GRBL, Safe Z: 10mm, Tool: T1
2. **Fanuc Demo Mill** (`fanuc_demo`)
   - Profile: FANUC, Safe Z: 5mm, Tool: T1, Program: O1001

**API Usage:**
```bash
POST /api/rmos/rosette/export-gcode?machine_id=bcm_2030ca
# → Uses 10mm safe Z, GRBL format, T1
```

---

## 4. Bundle B41 — UnifiedPresets Backend

### **Architecture**

**Store:** `services/api/app/util/presets_store.py`
- JSON-based CRUD with UUID generation
- Fail-soft: Returns `[]` on corruption
- Filtering: By `kind` and `tag`

**Router:** `services/api/app/api/routes/presets_router.py`
- Endpoint: `/api/presets`
- Methods: GET (list/get), POST (create), PATCH (update), DELETE

**Data Format:**
```json
{
  "id": "uuid",
  "kind": "cam" | "export" | "neck" | "combo",
  "name": "string",
  "tags": ["production", "rosette"],
  "machine_id": "bcm_2030ca",
  "cam_params": { ... },
  "export_params": { ... },
  "neck_params": { ... }
}
```

### **API Examples**

```bash
# List all CAM presets
GET /api/presets/?kind=cam

# Create new preset
POST /api/presets/
{
  "kind": "cam",
  "name": "Rosette Standard",
  "cam_params": {
    "stepover": 0.45,
    "strategy": "Spiral",
    "feed_xy": 1200
  }
}

# Update preset
PATCH /api/presets/{id}
{"tags": ["production", "verified"]}

# Delete preset
DELETE /api/presets/{id}
```

---

## 5. Active Workstreams (Not Yet Implemented)

### **CompareLab B22.8 — Dual-SVG Compare Polish**

**Status:** Partial implementation exists, needs completion

**What Exists:**
- `DualSvgDisplay.vue` with overlay mode
- Opacity/color controls
- Delta-only fallback
- Validation fail-soft
- Pan/zoom sync

**What's Needed:**
1. Autoscale and Reset View button
2. Full wiring of `isComputingDiff` skeleton state
3. Toast helper for user hints
4. Bind `diffDisabledReason` to UI

**Files Involved:**
- `packages/client/src/components/compare/DualSvgDisplay.vue`
- `services/api/app/routers/cam_compare_diff_router.py` (already exists)

### **CAM Offset N.17b — Polygon Offset CI Parity**

**Status:** Router exists, needs CI integration

**What Exists:**
- `polygon_offset_router.py` with `/cam/polygon_offset` (JSON)
- Pyclipper-based offset generation

**What's Needed:**
1. Verify `/cam/polygon_offset.nc` route (G-code export)
2. Add PowerShell CI smoke test (Ubuntu pwsh)
3. Fix stale test message (100×60 → 40×30)

**CI Requirements:**
- POST 40×30 rectangle to `/cam/polygon_offset.nc`
- Assert: non-empty, G21/G90/G17, M3/M5, arcCount > 4

**Files Involved:**
- `services/api/app/routers/polygon_offset_router.py`
- `services/api/app/main.py` (router inclusion)
- `.github/workflows/polygon_offset.yml` (new CI file)

---

## 6. Pre-Development Checklist

Before starting new work, verify:

### **Backend (FastAPI)**
- [ ] Server starts: `uvicorn app.main:app --reload --port 8000`
- [ ] N16 endpoints respond: `/api/rmos/rosette/export-gcode`
- [ ] B41 endpoints respond: `/api/presets`
- [ ] Machine configs accessible: `get_machine_config("bcm_2030ca")`

### **Frontend (Vue 3)**
- [ ] Client starts: `npm run dev` (port 5173)
- [ ] RMOS history view shows row tints
- [ ] Job detail view renders Markdown reports
- [ ] `/api` proxy to backend works

### **CI/CD**
- [ ] GitHub Actions run on push
- [ ] Adaptive pocket tests pass
- [ ] PowerShell scripts executable on Ubuntu

### **Documentation**
- [ ] `.github/copilot-instructions.md` is current
- [ ] Patch notes exist for N16.0-N16.7
- [ ] AGENTS.md reflects current module structure

---

## 7. Seed Prompt — Clone Chat and Continue Development

**Use this exact text to start a new ChatGPT/Copilot thread:**

---

### **SEED PROMPT — N16 Phase Complete + Active Workstreams**

**Title:** Luthier's Tool Box — Continue N16 Polish + CompareLab B22.8 + CAM Offset N.17b

**Context Recap:**

**N16 Phase (COMPLETE — Ready for Testing):**
- N16.0-N16.7: Rosette CNC export with arc geometry, multi-pass Z stepping, material presets, machine profiles (GRBL/FANUC), and hardware configs (BCM 2030CA, Fanuc Demo)
- All backend code implemented in `services/api/app/cam/rosette/`
- Endpoints: `/api/rmos/rosette/export-gcode` with `?machine_id=`, `?profile=`, `?tool_id=`
- Files: `cnc_ring_toolpath.py`, `cnc_gcode_exporter.py`, `cnc_materials.py`, `cnc_machine_profiles.py`, `rosette_cnc_wiring.py`

**Bundle B41 (COMPLETE):**
- UnifiedPresets backend skeleton at `/api/presets`
- JSON store with kind/tag filtering
- CRUD operations: GET/POST/PATCH/DELETE
- Files: `presets_store.py`, `presets_router.py`, `data/presets.json`

**CompareLab B22.8 (PARTIAL — Needs Polish):**
- DualSvgDisplay.vue exists with overlay, pan/zoom sync, fail-soft
- Need: autoscale, Reset View, full skeleton state wiring, toast hints

**CAM Offset N.17b (EXISTS — Needs CI):**
- polygon_offset_router.py exists
- Need: CI PowerShell smoke test, `/cam/polygon_offset.nc` verification, message fix (40×30)

**Do Now:**

1. **Test N16 Phase:**
   - Start backend: `uvicorn app.main:app --reload --port 8000`
   - Test endpoint: `POST /api/rmos/rosette/export-gcode?machine_id=bcm_2030ca`
   - Verify G-code output: 10mm safe Z, GRBL format, material-specific spindle RPM

2. **Complete CompareLab B22.8:**
   - Generate Vue patch for `DualSvgDisplay.vue`
   - Wire `isComputingDiff` skeleton state
   - Add Reset View button and toast helper
   - Bind `diffDisabledReason` to UI

3. **Lock CAM Offset N.17b:**
   - Verify `/cam/polygon_offset.nc` route in `polygon_offset_router.py`
   - Add PowerShell CI test: POST 40×30, assert G21/G90/G17, M3/M5, arcCount>4
   - Fix stale test message (100×60 → 40×30)

4. **Optional UI Enhancement:**
   - Add machine profile dropdown to CNC export panel (replace generic profile selector with machine_id chooser)

**Constraints:**
- Keep all public API contracts unchanged
- No breaking changes to N16 endpoints
- Maintain backward compatibility with existing callers

**References:**
- Primary guidance: `.github/copilot-instructions.md`
- Agent rules: `AGENTS.md`
- Module docs: `ADAPTIVE_POCKETING_MODULE_L.md`, `MACHINE_PROFILES_MODULE_M.md`
- Patch notes: `PATCH_L*_SUMMARY.md`

---

## 8. Testing Quick Reference

### **N16 Backend Testing**

```powershell
# Start API server
cd services/api
uvicorn app.main:app --reload --port 8000

# Test N16.3 G-code export (generic)
curl -X POST http://localhost:8000/api/rmos/rosette/export-gcode `
  -H "Content-Type: application/json" `
  -d @test_payload.json `
  -o test_output.gcode

# Test N16.7 machine config
curl -X POST "http://localhost:8000/api/rmos/rosette/export-gcode?machine_id=bcm_2030ca" `
  -H "Content-Type: application/json" `
  -d @test_payload.json `
  -o bcm_output.gcode

# Verify G-code structure
Select-String -Path bcm_output.gcode -Pattern "G21|G90|M3|M5|T1"
```

### **B41 Presets Testing**

```powershell
# List all presets
curl http://localhost:8000/api/presets/

# Create CAM preset
curl -X POST http://localhost:8000/api/presets/ `
  -H "Content-Type: application/json" `
  -d '{"kind":"cam","name":"Test","cam_params":{"stepover":0.45}}'

# Filter by kind
curl "http://localhost:8000/api/presets/?kind=cam"
```

### **Frontend Testing**

```bash
cd packages/client
npm run dev  # Runs on http://localhost:5173

# Test RMOS history view
# Navigate to /rmos/cnc-history
# Verify row tints (red/amber/green/gray)
# Click row → should navigate to /rmos/cnc-job/{job_id}
# Verify Markdown rendering in operator report
```

---

## 9. Key Files Reference

### **Backend Critical Files**

| File | Purpose | Lines |
|------|---------|-------|
| `services/api/app/main.py` | Router registration | ~917 |
| `services/api/app/api/routes/rmos_rosette_api.py` | RMOS CNC API | ~1066 |
| `services/api/app/cam/rosette/cnc/cnc_ring_toolpath.py` | N16.0/N16.2 geometry | 237 |
| `services/api/app/cam/rosette/cnc/cnc_gcode_exporter.py` | N16.3/N16.5 G-code | 133 |
| `services/api/app/cam/rosette/cnc/cnc_materials.py` | N16.4 materials | 83 |
| `services/api/app/cam/rosette/cnc/cnc_machine_profiles.py` | N16.7 machines | 91 |
| `services/api/app/cam/rosette/rosette_cnc_wiring.py` | N16 integration | 245 |
| `services/api/app/util/presets_store.py` | B41 store | 136 |
| `services/api/app/api/routes/presets_router.py` | B41 API | 211 |

### **Frontend Critical Files**

| File | Purpose | Lines |
|------|---------|-------|
| `packages/client/src/views/RMOSCncHistoryView.vue` | History with tints | ~400 |
| `packages/client/src/views/RMOSCncJobDetailView.vue` | Job detail + MD→HTML | 340 |
| `packages/client/src/components/compare/DualSvgDisplay.vue` | B22 compare (needs polish) | ~600 |

### **Documentation Files**

| File | Purpose |
|------|---------|
| `.github/copilot-instructions.md` | Primary AI agent guidance |
| `AGENTS.md` | Codex agent rules |
| `ADAPTIVE_POCKETING_MODULE_L.md` | Module L overview |
| `PATCH_L1_ROBUST_OFFSETTING.md` | L.1 implementation |
| `PATCH_L2_MERGED_SUMMARY.md` | L.2 implementation |
| `PATCH_L3_SUMMARY.md` | L.3 implementation |
| `MACHINE_PROFILES_MODULE_M.md` | Module M overview |

---

## 10. How to Use This Document

### **Scenario 1: Chat Thread Expired/Corrupted**

1. Open new ChatGPT/Copilot chat
2. Paste **Section 7 (Seed Prompt)** verbatim
3. Agent will reconstruct complete context
4. Continue development immediately

### **Scenario 2: New Developer Onboarding**

1. Read **Section 1 (Executive Summary)**
2. Review **Section 3 (N16 Technical Deep Dive)**
3. Run **Section 8 (Testing Quick Reference)**
4. Check **Section 6 (Pre-Development Checklist)**

### **Scenario 3: Feature Extension**

1. Locate relevant module in **Section 2 (Repository Structure)**
2. Read corresponding patch note (e.g., `PATCH_L2_MERGED_SUMMARY.md`)
3. Follow patterns in **Section 9 (Key Files Reference)**
4. Test with **Section 8 (Testing Quick Reference)**

---

## 11. Emergency Contact Points

### **If Backend Won't Start:**
- Check Python version: `python --version` (need 3.11+)
- Check dependencies: `pip list | grep fastapi`
- Check port: `netstat -an | findstr 8000`
- Check logs: Terminal output from `uvicorn app.main:app --reload`

### **If Frontend Won't Start:**
- Check Node version: `node --version` (need 18+)
- Check dependencies: `npm list vue`
- Check port: `netstat -an | findstr 5173`
- Clear cache: `npm run clean` (if exists) or `rm -rf node_modules && npm install`

### **If Tests Fail:**
- PowerShell version: `$PSVersionTable.PSVersion` (need 7.0+)
- API accessibility: `curl http://localhost:8000/health`
- Payload validity: Check JSON with `jq` or online validator

---

## 12. Version History

| Date | Phase | Bundles | Status |
|------|-------|---------|--------|
| 2025-12-01 | N16 | N16.0-N16.7 | ✅ Complete |
| 2025-12-01 | B41 | UnifiedPresets | ✅ Complete |
| 2025-12-01 | Bundle #13 | History + Detail | ✅ Complete |
| TBD | B22.8 | CompareLab Polish | 🔄 Partial |
| TBD | N.17b | Offset CI | 🔄 Partial |

---

## 13. Quick Win Opportunities

**If you have 15 minutes:**
- Test N16 endpoints with curl
- Verify preset creation via `/api/presets`
- Check RMOS history view row tints

**If you have 1 hour:**
- Complete CompareLab autoscale feature
- Add PowerShell CI test for polygon offset
- Document machine config extension pattern

**If you have 1 day:**
- UI for machine profile selector
- Integration tests for N16 phase
- Performance benchmarking for multi-pass toolpaths

---

**Document End — Ready for Production Use**

**Storage:** `docs/DEVELOPER_HANDOFF_N16_COMPLETE.md`  
**Maintenance:** Update after each major phase completion  
**Ownership:** Core development team + AI agents
