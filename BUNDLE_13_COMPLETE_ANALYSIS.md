# Bundle 13 Complete Analysis - "Project Spine"

**Date:** November 19, 2025  
**Source:** Bundle 13 — PipelineLab_QueryBootstrap.txt (10,898 lines)  
**Status:** 🔴 **CRITICAL** - Contains 17 interconnected bundles forming project architecture spine

---

## 🚨 **Critical Discovery**

The file "Bundle 13 — PipelineLab_QueryBootstrap.txt" is **NOT just one bundle** - it contains **17 major feature bundles** (B2-B21) that form the **architectural spine** of the CAM/Job Intelligence system.

**What we integrated:**
- ✅ Bundle #13 only (PipelineLab Query Bootstrap) - 200 lines

**What remains:**
- 🔴 Bundles #14-21 (Job Intelligence ecosystem) - ~4,000 lines
- 🔴 Bundles B2-B11 (Bridge/Pipeline integration) - ~6,000 lines

---

## 📦 **Bundle Inventory**

### **Job Intelligence Ecosystem** (Bundles #14-21)

| Bundle | Component | Lines | Priority | Status |
|--------|-----------|-------|----------|--------|
| **#14** | Stats Header | ~200 | ⭐⭐⭐⭐⭐ | 🔴 Missing |
| **#15** | Favorites Hook | ~400 | ⭐⭐⭐⭐⭐ | 🔴 Missing |
| **#16** | Favorites Filter | ~200 | ⭐⭐⭐⭐ | 🔴 Missing |
| **#17** | Favorite Chips + Quick Filters | ~300 | ⭐⭐⭐ | 🔴 Missing |
| **#18** | Compare Runs Panel | ~500 | ⭐⭐⭐⭐ | 🔴 Missing |
| **#19** | Preset Auto-Rank | ~600 | ⭐⭐⭐ | 🔴 Missing |
| **#20** | Preset Recommendations | ~800 | ⭐⭐⭐ | 🔴 Missing |
| **#21** | Machine Self-Calibration | ~1000 | ⭐⭐⭐⭐⭐ | 🔴 Missing |

**Total:** ~4,000 lines, 8 bundles

### **Bridge/Pipeline Integration** (Bundles B2-B11)

| Bundle | Component | Lines | Priority | Status |
|--------|-----------|-------|----------|--------|
| **B2** | Bridge Preflight JSON | ~400 | ⭐⭐⭐⭐⭐ | 🔴 Missing |
| **B3** | Bridge Pipeline Gate | ~500 | ⭐⭐⭐⭐⭐ | 🔴 Missing |
| **B5** | Bridge Export Hook | ~600 | ⭐⭐⭐⭐ | 🔴 Missing |
| **B7** | G-code Download | ~400 | ⭐⭐⭐⭐ | 🔴 Missing |
| **B8** | Sim Summary | ~500 | ⭐⭐⭐⭐⭐ | 🔴 Missing |
| **B9** | Sim Issues Stub | ~600 | ⭐⭐⭐⭐⭐ | 🔴 Missing |
| **B10** | SimIssues → Backplot | ~700 | ⭐⭐⭐⭐⭐ | 🔴 Missing |
| **B11** | SimIssues → JobInt | ~800 | ⭐⭐⭐⭐⭐ | 🔴 Missing |

**Total:** ~4,500 lines, 8 bundles

---

## 🎯 **Why These Are "Spine" Components**

### **Job Intelligence (B14-B21) - User-Facing Intelligence**
Creates a complete job analytics and optimization system:
- **Stats Header (B14)**: Real-time metrics dashboard
- **Favorites (B15-B17)**: Job bookmarking and filtering
- **Compare Runs (B18)**: Side-by-side job analysis
- **Preset Ranking (B19-B20)**: AI-driven parameter optimization
- **Calibration (B21)**: Machine accuracy tracking

**Impact:** Transforms raw job logs into actionable intelligence

### **Bridge/Pipeline (B2-B11) - Core CAM Integration**
Connects design → toolpath → simulation → job tracking:
- **Preflight (B2)**: Validates bridge geometry before CAM
- **Pipeline Gate (B3)**: Bridge integration checkpoint
- **Export Hook (B5)**: DXF → G-code bridge
- **Download (B7)**: G-code file management
- **Sim Summary (B8)**: Quick simulation overview
- **Sim Issues (B9-B11)**: Issue detection, visualization, logging

**Impact:** Creates end-to-end CAM workflow from bridge design to tracked jobs

---

## 🔥 **Critical Missing Components**

### **Immediate Blockers**

1. **Bundle #14 - Stats Header** ⭐⭐⭐⭐⭐
   - **Why:** Job Intelligence panel is incomplete without metrics
   - **Files:** 1 component patch
   - **Time:** 15 minutes
   - **Blocks:** User understanding of job history

2. **Bundle #15 - Favorites Hook** ⭐⭐⭐⭐⭐
   - **Why:** Core user interaction pattern
   - **Files:** 1 backend service (NEW), 2 patches
   - **Time:** 45 minutes
   - **Blocks:** B16, B17 (favorites features)

3. **Bundle B8 - Sim Summary** ⭐⭐⭐⭐⭐
   - **Why:** Pipeline results invisible without this
   - **Files:** 1 service, 1 router patch, 1 component
   - **Time:** 1 hour
   - **Blocks:** B9, B10, B11 (simulation issues)

4. **Bundle B11 - SimIssues → JobInt** ⭐⭐⭐⭐⭐
   - **Why:** Closes the loop - simulation issues feed job intelligence
   - **Files:** 1 service, 1 router, 1 component
   - **Time:** 1.5 hours
   - **Blocks:** Full CAM workflow completion

5. **Bundle #21 - Machine Calibration** ⭐⭐⭐⭐⭐
   - **Why:** Required for accurate machine profiles
   - **Files:** 1 service (NEW), 1 router (NEW), 1 API helper (NEW), 1 component (NEW), 1 test (NEW)
   - **Time:** 2 hours
   - **Blocks:** Machine accuracy tracking

### **High-Value Features**

6. **Bundle #18 - Compare Runs** ⭐⭐⭐⭐
   - **Why:** Debug why Job A succeeded vs Job B failed
   - **Files:** 1 component (NEW), 1 view (NEW), 1 router patch
   - **Time:** 1.5 hours

7. **Bundle B3 - Pipeline Gate** ⭐⭐⭐⭐⭐
   - **Why:** Bridge geometry validation before expensive CAM ops
   - **Files:** 1 service, 1 router patch, 1 test
   - **Time:** 1 hour

---

## 📋 **Recommended Integration Order**

### **Phase 1: Complete Job Intelligence Core** (3 hours)
1. Bundle #14 - Stats Header (15 min)
2. Bundle #15 - Favorites Hook (45 min)
3. Bundle #16 - Favorites Filter (30 min)
4. Bundle #17 - Favorite Chips (45 min)
5. Bundle #18 - Compare Runs (1 hour)

**Deliverable:** Fully functional Job Intelligence panel with metrics, favorites, filtering, comparison

### **Phase 2: Complete Pipeline Integration** (4 hours)
1. Bundle B2 - Bridge Preflight (1 hour)
2. Bundle B3 - Pipeline Gate (1 hour)
3. Bundle B8 - Sim Summary (1 hour)
4. Bundle B9 - Sim Issues Stub (1 hour)

**Deliverable:** End-to-end bridge → CAM → simulation workflow

### **Phase 3: Close the Loop** (3 hours)
1. Bundle B10 - SimIssues → Backplot (1.5 hours)
2. Bundle B11 - SimIssues → JobInt (1.5 hours)

**Deliverable:** Simulation issues visible in backplot and tracked in job intelligence

### **Phase 4: Optimization Layer** (4 hours)
1. Bundle #19 - Preset Auto-Rank (1.5 hours)
2. Bundle #20 - Preset Recommendations (1.5 hours)
3. Bundle #21 - Machine Calibration (2 hours)

**Deliverable:** AI-driven parameter optimization and machine accuracy tracking

**Total Time: 14 hours** to complete all missing components

---

## 🎨 **Phase 27.1 Status**

Phase 27.1 (Rosette Compare) appears complete in the bundle. No missing components identified.

---

## 🚀 **Next Steps**

**Option 1: Complete Job Intelligence First** (Recommended)
- Focus on B14-B18 (3 hours)
- Immediate user value
- Natural progression from current state

**Option 2: Complete Pipeline Integration First**
- Focus on B2, B3, B8, B9 (4 hours)
- Critical for CAM workflow
- Enables simulation visualization

**Option 3: Cherry-pick Critical Components**
- B14 (Stats), B15 (Favorites), B8 (Sim Summary), B11 (SimIssues → JobInt)
- 3.5 hours for maximum impact
- Gets core functionality working

---

## 📊 **Integration Complexity**

| Complexity | Bundles | Total Lines | Time |
|------------|---------|-------------|------|
| **Low** | B14, B16, B7 | ~800 | 1.5 hours |
| **Medium** | B15, B17, B2, B5, B8, B9 | ~3,300 | 5 hours |
| **High** | B18, B10, B11 | ~2,000 | 4.5 hours |
| **Very High** | B19, B20, B21 | ~2,400 | 5 hours |

---

## 🔍 **Files Currently Missing**

### **Backend (NEW files needed)**
- `server/services/job_int_favorites.py` (B15)
- `server/services/job_int_tags.py` (B17)
- `server/services/machine_calibration.py` (B21)
- `server/routers/machine_calibration_router.py` (B21)
- `services/api/app/utils/error_capture.py` (B2)
- `services/api/app/services/bridge_export.py` (B5)
- `services/api/app/services/pipeline_ops_bridge.py` (B3)
- `services/api/app/services/jobint_sim_issues_summary.py` (B11)

### **Frontend (NEW files needed)**
- `client/src/api/preset_rank.ts` (B19)
- `client/src/api/machine_calibration.ts` (B21)
- `client/src/components/cam/JobIntCompareRunsPanel.vue` (B18)
- `client/src/components/cam/PresetRankingsPanel.vue` (B19)
- `client/src/components/cam/PresetRecommendationsPanel.vue` (B20)
- `client/src/components/cam/MachineCalibrationPanel.vue` (B21)
- `client/src/components/CamJobInsightsSummaryPanel.vue` (B8)
- `client/src/components/CamJobSimIssuesHistoryChart.vue` (B11)
- `client/src/components/CamJobLogTable.vue` (B11)
- `client/src/views/JobIntCompareView.vue` (B18)
- `client/src/views/CamJobInsightsView.vue` (B11)

### **Tests (NEW files needed)**
- `server/tests/test_machine_calibration.py` (B21)
- `services/api/tests/test_bridge_error_capture.py` (B2)
- `services/api/tests/test_bridge_export_dxf_geom.py` (B5)
- `services/api/tests/test_bridge_preflight.py` (B2)
- `services/api/tests/test_pipeline_bridge_gate.py` (B3)

---

## ⚠️ **Risk Assessment**

**Without these bundles:**
- ❌ Job Intelligence incomplete (no metrics, no favorites, no comparison)
- ❌ Pipeline simulation results invisible
- ❌ Bridge geometry errors not caught early
- ❌ Simulation issues not tracked or visualized
- ❌ Machine calibration data not captured
- ❌ Preset optimization unavailable

**Impact:** Core CAM workflow is incomplete. Users can run pipelines but can't see results, track jobs, or optimize parameters.

---

**Recommendation:** Integrate in phases, starting with Job Intelligence (B14-B18) for immediate user value, then Pipeline Integration (B2-B11) for workflow completion.
