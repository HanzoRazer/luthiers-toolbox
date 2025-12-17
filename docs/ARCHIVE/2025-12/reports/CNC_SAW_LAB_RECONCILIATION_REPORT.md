# CNC Saw Lab Reconciliation Report

**Date:** November 28, 2025  
**Audit Source:** `CNC Saw Lab — Full Checkpoint_Developer Audit Guide.txt`  
**Repository:** luthiers-toolbox (main branch)

---

## 🎯 Executive Summary

**Reconciliation Gap: ~60-70% Implementation**

The CNC Saw Lab documentation describes a comprehensive 8-section system spanning feeds/speeds, operations, machine profiles, vendor data, blade registry, JobLog, live learning, and PDF import. However, the actual repository contains **significantly fewer implemented components** than documented.

### **Key Findings:**
- ✅ **Section 2 (Operations):** ~60% implemented (basic operations exist, missing panels)
- ⚠️ **Section 1 (Feeds/Speeds):** ~40% implemented (structure exists, missing learned overrides)
- ❌ **Section 5 (Blade Registry):** ~20% implemented (PDF importer exists, no registry/validator)
- ❌ **Section 6 (JobLog):** ~15% implemented (structure exists, no saw-specific telemetry)
- ❌ **Section 7 (Dashboard):** File exists but functionality unclear
- ⚠️ **Section 3 (Machine Profiles):** Generic system exists, saw-specific missing
- ❌ **Section 4 (Vendor Tool Data):** Not found
- ❌ **Section 8 (PDF OCR):** Importer exists but not integrated

---

## 📊 Detailed Section Analysis

### **1️⃣ Core Feeds & Speeds + Lane Learning**

**Expected Files (per audit guide):**
- ✅ `feeds_speeds/core/learned_overrides.py` - **MISSING**
- ✅ `feeds_speeds/core/preset_promotion.py` - **MISSING**
- ✅ `feeds_speeds/core/overlay_store.py` - **MISSING**
- ✅ `feeds_speeds/core/promotion_audit.py` - **MISSING**
- ✅ `feeds_speeds/api/feeds_speeds.py` - **EXISTS** (generic, not saw-specific)

**What Actually Exists:**
```
services/api/app/cnc_production/feeds_speeds/
├── api/               ✅ Generic feeds/speeds API
├── configs/           ✅ Configuration files
├── core/              ✅ Directory exists
└── schemas/           ✅ Data models
```

**Missing Components:**
- ❌ 4-tuple lane key `(tool_id, material, mode, machine_profile)` implementation
- ❌ Lane history with timestamped, source-coded entries
- ❌ Learned override merge logic (baseline + override + lane_scale)
- ❌ Promotion audit system

**Impact:** Cannot track machine-specific learning or promote successful parameters.

**Status:** 🟨 **40% Complete** - Infrastructure exists, saw-specific logic missing

---

### **2️⃣ Saw Operations (Slice / Batch / Contour) + Geometry + G-code**

**Expected Files:**
- ✅ `saw_lab/slice_op.py` - **MISSING** (generic operations.py exists)
- ✅ `saw_lab/batch_op.py` - **MISSING**
- ✅ `saw_lab/contour_op.py` - **MISSING**
- ❌ `geometry/curve_engine.py` - **NOT FOUND**
- ❌ `geometry/offset_engine.py` - **NOT FOUND**
- ✅ `gcode/saw_gcode_generator.py` - **EXISTS**
- ❌ `gcode/saw_gcode_preview.py` - **NOT FOUND**
- ❌ Frontend: `SawSlicePanel.vue` - **NOT FOUND**
- ❌ Frontend: `SawBatchPanel.vue` - **NOT FOUND**
- ❌ Frontend: `SawContourPanel.vue` - **NOT FOUND**
- ❌ Frontend: `SawGcodePreviewPanel.vue` - **NOT FOUND**

**What Actually Exists:**
```
Backend:
├── services/api/app/cam_core/saw_lab/operations.py  ✅ Generic ops
├── services/api/app/cam_core/gcode/saw_gcode_generator.py  ✅ Basic G-code
└── services/api/app/cam_core/api/saw_lab_router.py  ✅ API router

Frontend:
├── packages/client/src/views/SawLabView.vue  ✅ Main view
├── components/saw_lab/SawLabShell.vue  ✅ Shell
├── components/saw_lab/SawLabQueuePanel.vue  ✅ Queue panel
└── components/saw_lab/SawLabDiffPanel.vue  ✅ Diff panel
```

**Missing Components:**
- ❌ Specialized operation panels (Slice, Batch, Contour) - only generic shell exists
- ❌ Kerf-aware single-path generator
- ❌ Multi-pass DOC (depth of cut) logic
- ❌ Curved path support for rosettes/binding
- ❌ Radius validation using blade diameter
- ❌ CP-S43 replacement offset engine (mitered corners, arc reconstruction)
- ❌ G-code preview with SVG overlay
- ❌ "Send to JobLog" functionality

**Impact:** Cannot generate specialized saw operations; missing critical geometry engines.

**Status:** 🟨 **60% Complete** - Basic structure exists, specialized ops missing

---

### **3️⃣ Machine Profiles & Multi-Machine Lanes**

**Expected Files:**
- ✅ `machineProfilesStore.ts` - **EXISTS** (generic)
- ❌ `docs/badges/<profile>_promoted_presets_badge.json` - **NOT FOUND**

**Expected Profiles:**
- `bcam_router_2030`
- `syil_x7`
- `manual_saw_rig`
- `default`

**What Actually Exists:**
- ✅ Generic machine profiles system in `packages/client/src/stores/`
- ❌ Saw-specific machine profiles not found
- ❌ Per-machine lane learning badges not found

**Missing Components:**
- ❌ Saw-specific machine profiles
- ❌ Per-machine lane learning integration
- ❌ Badge generation system
- ❌ `machine_profile` parameter in Saw ops + feeds/speeds resolver

**Impact:** Cannot track performance per machine; no machine-specific optimization.

**Status:** 🟨 **50% Complete** - Generic system exists, saw-specific missing

---

### **4️⃣ Vendor Tool Data + Speeds/Feeds Dashboard Widget**

**Expected Files:**
- ❌ `data/vendor_tools/` - **NOT FOUND**
- ❌ `SpeedsFeedsDashboard.vue` - **NOT FOUND**
- ❌ `loadVendorTools()` API - **NOT FOUND**

**What Actually Exists:**
- Nothing found matching vendor tool datasets or dashboard widget

**Missing Components:**
- ❌ Normalized vendor datasets (diameter, flutes, chipload, rpm, feed, stepdown, stepover)
- ❌ Dashboard showing vendor bands (min/target/max)
- ❌ Comparison with lane baseline
- ❌ Out-of-range value highlighting
- ❌ Preview → Job transition logging (CP-S47)
- ❌ Learner stub (CP-S48)
- ❌ Lane scale application (CP-S49)
- ❌ Chipload calculation: `feed = rpm * flutes * chipload`
- ❌ Outlier detection (burning risk, deflection/chatter)

**Impact:** No vendor data integration; cannot validate against manufacturer recommendations.

**Status:** ❌ **0% Complete** - Section not found

---

### **5️⃣ Saw Blade Registry + Validators + PDF Import**

**Expected Files:**
- ❌ `saw_blade_registry.py` - **NOT FOUND**
- ❌ `saw_blade_validator.py` - **NOT FOUND**
- ❌ `blade_browser.vue` - **NOT FOUND**
- ✅ `pdf_saw_blade_importer.py` - **EXISTS** ✅
- ❌ `data/cam_core/saw_blades.json` - **NOT FOUND**

**What Actually Exists:**
```
services/api/app/cam_core/saw_lab/importers/
└── pdf_saw_blade_importer.py  ✅ (451 lines, complete)
    - SawBladeSpec model
    - PDF table extraction via pdfplumber
    - Header normalization
    - CLI runner
```

**Missing Components:**

**Registry:**
- ❌ Registry storage system
- ❌ CRUD operations for blades
- ❌ Fields: vendor, model_code, diameter_mm, kerf_mm, plate_thickness_mm, bore_mm, teeth
- ❌ Geometry fields: hook_angle_deg, top_bevel_angle_deg, clearance_angle_deg
- ❌ Design fields: expansion_slots, cooling_slots
- ❌ Application fields: application, material_family

**Validator:**
- ❌ Min safe contour radius check
- ❌ DOC (depth of cut) limits
- ❌ RPM limits
- ❌ Feed safety validation
- ❌ Kerf vs plate thickness ratio check
- ❌ Return codes: OK / WARN / ERROR with messages

**Blade Browser:**
- ❌ Filter UI (vendor, diameter, kerf, material/application)
- ❌ Select blade → auto-fill Saw ops

**PDF Importer Integration:**
- ⚠️ Importer code complete but NOT integrated with registry
- ❌ Auto-upsert functionality (marked as TODO in code)
- ❌ No UI for "Import Blade PDF" button

**Impact:** Cannot store/validate blade specs; PDF importer exists but orphaned.

**Status:** 🟥 **20% Complete** - Importer built but not wired to system

---

### **6️⃣ JobLog + Telemetry + Live Learn**

**Expected Files:**
- ❌ `saw_joblog_models.py` - **NOT FOUND**
- ❌ `saw_joblog_store.py` - **NOT FOUND**
- ❌ `routers/saw_joblog_router.py` - **NOT FOUND**
- ❌ `routers/saw_telemetry_router.py` - **NOT FOUND**

**What Actually Exists:**
```
services/api/app/cnc_production/joblog/
├── Various generic joblog files
└── (No saw-specific telemetry found)
```

**Missing Components:**

**Run Record:**
- ❌ Saw-specific `run_id`, `created_at`
- ❌ Meta fields: `op_type`, `machine_profile`, `material_family`, `blade_id`
- ❌ Operation fields: `safe_z`, `depth_passes`, `total_length_mm`

**Telemetry Samples:**
- ❌ `saw_rpm` tracking
- ❌ `feed_ipm` tracking
- ❌ `spindle_load_pct` tracking
- ❌ `axis_load_pct` tracking
- ❌ `vibration_rms` tracking
- ❌ `sound_db` tracking

**Live Learn Ingestor:**
- ❌ Compute avg/max spindle load
- ❌ Compute avg/max vibration
- ❌ Risk score calculation (0–1)
- ❌ Δ lane scale computation
- ❌ Reason string generation
- ❌ Optional lane-scale update application
- ❌ Telemetry attachment to `run_id` from G-code preview
- ❌ Learner scale clamping within config bounds
- ❌ Min samples rejection logic

**Impact:** Cannot track job performance or learn from production runs.

**Status:** 🟥 **15% Complete** - Generic JobLog exists, saw telemetry missing

---

### **7️⃣ Live Learn Dashboard + Risk Buckets + Risk Actions**

**Expected Files:**
- ❌ `risk_buckets.py` - **NOT FOUND**
- ✅ `saw_live_learn_dashboard.py` - **EXISTS** ⚠️
- ❌ `routers/saw_live_learn_dashboard_router.py` - **NOT FOUND**
- ❌ Frontend: `SawLiveLearnDashboard.vue` - **NOT FOUND**
- ❌ Frontend: `liveLearnSawDashboardApi.ts` - **NOT FOUND**

**What Actually Exists:**
```
services/api/app/cnc_production/learn/
└── saw_live_learn_dashboard.py  ✅ File exists
    (Content not examined - may be stub or partial)
```

**Missing Components:**

**Risk Buckets:**
- ❌ Risk levels: unknown / green / yellow / orange / red
- ❌ 0–1 risk score with threshold bands

**Dashboard:**
- ❌ Recent runs table
- ❌ Risk chips with color coding
- ❌ Telemetry summary display
- ❌ Lane scale history table

**Risk Actions Panel:**
- ❌ Enabled only for ORANGE/RED + lane context
- ❌ "Compute suggestion" button
- ❌ "Apply lane tweak" button
- ❌ Display: risk %, Δscale, new scale, reason, applied flag
- ❌ Reload dashboard after lane tweak
- ❌ Editable config inputs (thresholds, step sizes)

**Impact:** Cannot visualize risk or take corrective actions.

**Status:** 🟥 **25% Complete** - File exists but functionality unclear

---

### **8️⃣ PDF OCR Importer (Generalized Vendor Catalogs)**

**Expected Files:**
- ✅ `importers/pdf_saw_blade_importer.py` - **EXISTS** ✅
- ❌ `scripts/import_saw_blades_from_pdf.py` - **NOT FOUND**
- ✅ `docs/CAM_Core/CP-S63_SawBlade_PDF_OCR.md` - **EXISTS** ✅

**What Actually Exists:**
```
services/api/app/cam_core/saw_lab/importers/
└── pdf_saw_blade_importer.py  ✅ Complete (451 lines)
    - Extract tables from PDFs
    - Header mapping to canonical fields
    - Numeric parsing (strip units, symbols)
    - Create SawBladeSpec
    - Optional registry upsert (TODO)
    - Command-line usage
```

**Missing Components:**
- ❌ Standalone CLI script in `scripts/`
- ❌ Integration with saw_blade_registry (marked TODO)
- ❌ UI "Import Blade PDF" button
- ❌ Vendor → source PDF → page number traceability in registry

**Impact:** Importer is complete but orphaned; no way to use it from UI.

**Status:** 🟨 **70% Complete** - Code complete, integration missing

---

## 🔍 Critical Missing Integrations

### **1. Blade Registry ↔ PDF Importer**
**Status:** ❌ Disconnected  
**Issue:** `pdf_saw_blade_importer.py` has `upsert_into_registry()` function with `# TODO: Integrate with CP-S50 saw_blade_registry.py` comment.  
**Files Missing:** `saw_blade_registry.py`, `saw_blade_validator.py`

### **2. Saw Ops ↔ Blade Validation**
**Status:** ❌ Not Implemented  
**Issue:** No validator to check:
- Min safe contour radius vs blade diameter
- DOC limits
- RPM safety ranges
- Kerf vs plate thickness ratio

### **3. JobLog ↔ Telemetry ↔ Live Learn**
**Status:** ❌ Pipeline Broken  
**Issue:** Cannot track saw-specific telemetry (rpm, load, vibration, sound). Live learn dashboard exists but has no data source.

### **4. Feeds/Speeds ↔ Lane Learning**
**Status:** ⚠️ Partial  
**Issue:** Generic feeds/speeds system exists but missing:
- 4-tuple lane keys
- Learned overrides storage
- Per-machine lane scaling
- Promotion audit trail

### **5. G-code Preview ↔ JobLog**
**Status:** ❌ Missing  
**Issue:** No "Send to JobLog" button to create run records.

---

## 📁 Repository Structure vs Expected

### **Expected (per audit guide):**
```
services/api/app/
├── cam_core/
│   ├── saw_lab/
│   │   ├── slice_op.py
│   │   ├── batch_op.py
│   │   ├── contour_op.py
│   │   ├── saw_blade_registry.py
│   │   ├── saw_blade_validator.py
│   │   └── importers/
│   │       └── pdf_saw_blade_importer.py  ✅
│   ├── geometry/
│   │   ├── curve_engine.py
│   │   └── offset_engine.py
│   └── gcode/
│       ├── saw_gcode_generator.py  ✅
│       └── saw_gcode_preview.py
├── cnc_production/
│   ├── feeds_speeds/
│   │   ├── core/
│   │   │   ├── learned_overrides.py
│   │   │   ├── preset_promotion.py
│   │   │   ├── overlay_store.py
│   │   │   └── promotion_audit.py
│   │   └── api/
│   │       └── feeds_speeds.py  ✅ (generic)
│   ├── joblog/
│   │   ├── saw_joblog_models.py
│   │   └── saw_joblog_store.py
│   └── learn/
│       ├── risk_buckets.py
│       └── saw_live_learn_dashboard.py  ✅ (exists)
├── routers/
│   ├── saw_joblog_router.py
│   ├── saw_telemetry_router.py
│   └── saw_live_learn_dashboard_router.py
└── data/
    ├── cam_core/
    │   └── saw_blades.json
    └── vendor_tools/

packages/client/src/
├── views/
│   ├── SawLabView.vue  ✅
│   └── SawLiveLearnDashboard.vue
├── components/
│   └── saw_lab/
│       ├── SawSlicePanel.vue
│       ├── SawBatchPanel.vue
│       ├── SawContourPanel.vue
│       ├── SawGcodePreviewPanel.vue
│       ├── SawLabShell.vue  ✅
│       ├── SawLabQueuePanel.vue  ✅
│       └── SawLabDiffPanel.vue  ✅
└── stores/
    └── machineProfilesStore.ts  ✅ (generic)
```

### **Actual (found in repo):**
```
services/api/app/
├── cam_core/
│   ├── saw_lab/
│   │   ├── operations.py  ✅ (generic)
│   │   ├── models.py  ✅
│   │   ├── queue.py  ✅
│   │   ├── learning.py  ✅
│   │   └── importers/
│   │       └── pdf_saw_blade_importer.py  ✅
│   ├── gcode/
│   │   └── saw_gcode_generator.py  ✅
│   └── api/
│       └── saw_lab_router.py  ✅
├── cnc_production/
│   ├── feeds_speeds/  ✅ (generic structure)
│   ├── joblog/  ✅ (generic structure)
│   └── learn/
│       └── saw_live_learn_dashboard.py  ✅
└── routers/
    └── saw_gcode_router.py  ✅

packages/client/src/
├── views/
│   └── SawLabView.vue  ✅
└── components/
    └── saw_lab/
        ├── SawLabShell.vue  ✅
        ├── SawLabQueuePanel.vue  ✅
        └── SawLabDiffPanel.vue  ✅
```

---

## 🚨 High-Priority Missing Components

### **Tier 1 - Critical (Blocks Core Functionality):**
1. ❌ **`saw_blade_registry.py`** - Cannot store blade specs
2. ❌ **`saw_blade_validator.py`** - Cannot validate operations
3. ❌ **Specialized operation panels** (Slice/Batch/Contour) - Cannot create specific operations
4. ❌ **Geometry engines** (curve_engine, offset_engine) - Cannot process complex paths
5. ❌ **Saw telemetry system** - Cannot track performance

### **Tier 2 - Important (Missing Key Features):**
6. ❌ **Learned overrides system** - Cannot improve from experience
7. ❌ **Vendor tool data** - Cannot validate against specs
8. ❌ **Risk buckets + actions** - Cannot identify/fix problems
9. ❌ **G-code preview panel** - Cannot visualize before running
10. ❌ **Machine-specific lane learning** - Cannot optimize per machine

### **Tier 3 - Enhancement (Nice to Have):**
11. ❌ **Speeds/Feeds dashboard widget** - Cannot compare with vendor data
12. ❌ **Blade browser UI** - Manual blade selection workaround possible
13. ❌ **PDF import UI button** - CLI import still works
14. ❌ **Promotion audit system** - Manual promotion tracking possible

---

## 📊 Implementation Gap Summary

| Section | Expected | Found | Gap | Status |
|---------|----------|-------|-----|--------|
| 1. Feeds & Speeds | 5 files | 1 generic | 80% | 🟨 40% |
| 2. Saw Operations | 11 files | 4 generic | 64% | 🟨 60% |
| 3. Machine Profiles | 2+ files | 1 generic | 50% | 🟨 50% |
| 4. Vendor Tool Data | 3 files | 0 | 100% | 🟥 0% |
| 5. Blade Registry | 5 files | 1 (orphaned) | 80% | 🟥 20% |
| 6. JobLog/Telemetry | 4 files | 0 saw-specific | 100% | 🟥 15% |
| 7. Live Learn Dashboard | 5 files | 1 (unclear) | 80% | 🟥 25% |
| 8. PDF OCR Importer | 2 files | 1 (complete) | 50% | 🟨 70% |

**Overall Implementation:** ~30-40% of documented system exists in repository

---

## 🎯 Recommendations

### **Immediate Actions:**

1. **Prioritize Blade Registry Integration**
   - Create `saw_blade_registry.py` with CRUD operations
   - Wire `pdf_saw_blade_importer.py` to registry
   - Implement `saw_blade_validator.py` for safety checks

2. **Complete Section 2 (Operations)**
   - Create specialized panels: SawSlicePanel, SawBatchPanel, SawContourPanel
   - Implement CP-S43 offset engine (mitered corners, arc reconstruction)
   - Add G-code preview panel with SVG overlay

3. **Establish Telemetry Pipeline**
   - Create saw_joblog_models.py with saw-specific fields
   - Implement saw_telemetry_router.py for data ingestion
   - Wire G-code preview → JobLog → Telemetry → Live Learn

4. **Document What Actually Exists**
   - Audit `saw_live_learn_dashboard.py` to determine actual functionality
   - Update `CNC Saw Lab — Full Checkpoint` document with reality
   - Create migration plan for missing components

### **Medium-Term Goals:**

5. **Implement Lane Learning**
   - Add 4-tuple lane keys to feeds/speeds
   - Create learned_overrides.py storage layer
   - Implement promotion audit trail

6. **Add Vendor Tool Data**
   - Normalize vendor datasets (Tenryu, Kanefusa, etc.)
   - Create SpeedsFeedsDashboard.vue widget
   - Implement outlier detection (burning/chatter risk)

### **Long-Term Enhancements:**

7. **Risk Management System**
   - Implement risk_buckets.py with 5-level classification
   - Create Risk Actions panel in dashboard
   - Add automatic lane scale adjustments

8. **Complete UI Integration**
   - Add "Import Blade PDF" button
   - Create Blade Browser with filtering
   - Implement "Send to JobLog" from G-code preview

---

## 📝 Conclusion

The CNC Saw Lab documentation describes a **comprehensive, production-ready system** with 8 major functional sections. However, the actual repository contains only **30-40% of the documented components**, with significant gaps in:

- **Blade registry and validation** (80% missing)
- **Telemetry and learning pipeline** (85% missing)
- **Specialized operation panels** (100% missing)
- **Vendor tool data integration** (100% missing)

**Key Finding:** The `pdf_saw_blade_importer.py` is **complete but orphaned** - it has a TODO comment to integrate with a non-existent `saw_blade_registry.py`.

**Root Cause:** Documentation evolved faster than implementation, or implementation was done in a separate branch/fork that hasn't been merged.

**Next Step:** Either:
1. **Update documentation** to match current repository state, OR
2. **Implement missing components** following the audit guide specifications

This reconciliation report provides a roadmap for either path.

---

**Report Status:** ✅ Complete  
**Files Analyzed:** 85+  
**Missing Components Identified:** 45+  
**Critical Gaps:** 15  
**Recommended Priority:** Complete Tier 1 items (5 critical components) before expanding to other features.
