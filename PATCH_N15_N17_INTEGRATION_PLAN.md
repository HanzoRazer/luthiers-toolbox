# Patch N.15-N.17 + CAM Essentials Rollup - Integration Plan

**Date:** November 6, 2025  
**Status:** 🚧 Integration in Progress

---

## 📦 Patches Overview

### **Patch N.15: G-code Backplot + Time Estimator**
- **Purpose:** Parse G-code, visualize toolpath, estimate cycle time
- **Key Features:**
  - G-code parser (G0/G1/G2/G3, IJ/R arcs, F modal, G20/G21 units)
  - SVG backplot generation
  - Travel/cut distance tracking
  - Time estimation (rapid vs feed rates)

### **Patch N.16: Adaptive Spiral + Trochoid Bench**
- **Purpose:** Advanced adaptive clearing strategies
- **Key Features:**
  - True inward-offset spiral (successive offsets)
  - Trochoidal corner loops (load management)
  - Performance benchmarking
  - Rectangle-focused offsetting with fillets

### **Patch N.17: Polygon Offset + Arc Linkers**
- **Purpose:** Production-grade polygon offsetting with pyclipper
- **Key Features:**
  - Arbitrary polygon offset spirals
  - Arc-smoothed ring transitions
  - Min-engagement steering (curvature-based)
  - Target engagement control

### **CAM Essentials Rollup**
- **Purpose:** Consolidated integration of N.15-N.17
- **Bundles:** Unified router registration and UI

---

## 🎯 Integration Strategy

### **Phase 1: Backend Core (N.15 Parser)**
1. ✅ Integrate `gcode_parser.py` (G-code simulation engine)
2. ✅ Create `gcode_backplot_router.py` (SVG + time endpoints)
3. ✅ Register router in `main.py`

### **Phase 2: Advanced Adaptive (N.16-N.17)**
4. ⏳ Integrate `adaptive_geom.py` (spiral + trochoid kernels)
5. ⏳ Integrate `poly_offset_spiral.py` (pyclipper-based)
6. ⏳ Create routers for adaptive kernels
7. ⏳ Add `pyclipper` dependency

### **Phase 3: Frontend Components**
8. ⏳ `BackplotGcode.vue` - G-code visualization
9. ⏳ `AdaptiveBench.vue` - Kernel testing UI
10. ⏳ `AdaptivePoly.vue` - Polygon offset UI

### **Phase 4: Testing & Validation**
11. ⏳ Smoke tests for each patch
12. ⏳ Performance benchmarks
13. ⏳ Integration validation

---

## 📋 File Inventory

### **Backend Files to Integrate**
| Source | Target | Lines | Purpose |
|--------|--------|-------|---------|
| `N15/server/util/gcode_parser.py` | `services/api/app/util/gcode_parser.py` | ~150 | G-code simulator |
| `N15/server/gcode_backplot_router.py` | `services/api/app/routers/gcode_backplot_router.py` | ~80 | Backplot endpoints |
| `N16/server/util/adaptive_geom.py` | `services/api/app/util/adaptive_geom.py` | ~200 | Spiral + trochoid |
| `N16/server/adaptive_kernel_router.py` | `services/api/app/routers/adaptive_kernel_router.py` | ~100 | Kernel endpoints |
| `N17/server/util/poly_offset_spiral.py` | `services/api/app/util/poly_offset_spiral.py` | ~250 | Pyclipper offset |
| `N17/server/adaptive_poly_router.py` | `services/api/app/routers/adaptive_poly_router.py` | ~100 | Poly endpoints |

### **Frontend Files to Integrate**
| Source | Target | Lines | Purpose |
|--------|--------|-------|---------|
| `N15/client/src/components/BackplotGcode.vue` | `packages/client/src/components/BackplotGcode.vue` | ~120 | G-code viewer |
| `N16/client/src/components/AdaptiveBench.vue` | `packages/client/src/components/AdaptiveBench.vue` | ~150 | Kernel tester |
| `N17/client/src/components/AdaptivePoly.vue` | `packages/client/src/components/AdaptivePoly.vue` | ~130 | Poly offset UI |

---

## 🔌 New API Endpoints

### **N.15: G-code Analysis**
```
POST /cam/gcode/plot.svg
  Body: { gcode: "G0 X10 Y10\n...", units: "mm" }
  Returns: SVG polyline

POST /cam/gcode/estimate
  Body: { gcode: "...", rapid_mm_min: 3000, default_feed_mm_min: 500 }
  Returns: { travel_mm, cut_mm, t_rapid_min, t_feed_min, t_total_min }
```

### **N.16: Adaptive Kernels**
```
POST /cam/adaptive2/offset_spiral.svg
  Body: { width, height, tool_dia, stepover, corner_fillet }
  Returns: SVG spiral path

POST /cam/adaptive2/trochoid_corners.svg
  Body: { polygon, tool_dia, loop_pitch, amp }
  Returns: SVG trochoid loops

POST /cam/adaptive2/bench
  Returns: { avg_ms, iterations }
```

### **N.17: Polygon Offset**
```
POST /cam/adaptive3/offset_spiral.svg
  Body: { polygon, tool_dia, stepover, target_engage, arc_r }
  Returns: SVG orange spiral

POST /cam/adaptive3/bench
  Returns: { avg_ms, iterations }
```

---

## 🔗 Relationship to Existing Systems

### **Integration with Module L (Adaptive Pocketing)**
- **N.17 enhances L.1:** Pyclipper-based offsetting (already integrated)
- **N.16 related to L.2:** Spiral strategies (true spiralizer)
- **N.17 min-engagement:** Related to L.2 adaptive stepover

### **Integration with Art Studio v15.5**
- **N.15 backplot:** Can visualize v15.5 generated G-code
- **N.15 time estimator:** Complements v15.5 post-processor

### **Integration with Patch N.14**
- **Unified CAM settings:** Post templates + adaptive preview
- **N.15-N.17:** Add analysis and advanced kernels

---

## 🚀 Implementation Steps

### **Step 1: Install Dependencies**
```powershell
cd services/api
.\.venv\Scripts\Activate.ps1
pip install pyclipper>=1.3
```

### **Step 2: Integrate N.15 (G-code Parser)**
- Copy `gcode_parser.py` to `util/`
- Create `gcode_backplot_router.py`
- Register router in `main.py`

### **Step 3: Integrate N.16 (Adaptive Kernels)**
- Copy `adaptive_geom.py` to `util/`
- Create `adaptive_kernel_router.py`
- Register router

### **Step 4: Integrate N.17 (Polygon Offset)**
- Copy `poly_offset_spiral.py` to `util/`
- Create `adaptive_poly_router.py`
- Register router

### **Step 5: Frontend Components**
- Copy Vue components
- Configure routes
- Test UI

---

## ⚠️ Potential Conflicts & Resolutions

### **Conflict 1: Adaptive Router Naming**
- Existing: `/api/cam/pocket/adaptive/*` (Module L)
- N.16: `/cam/adaptive2/*`
- N.17: `/cam/adaptive3/*`
- **Resolution:** Keep separate namespaces, document distinctions

### **Conflict 2: Pyclipper Dependency**
- Module L.1 already uses `pyclipper==1.3.0.post5`
- N.17 requires `pyclipper>=1.3`
- **Resolution:** Already compatible

### **Conflict 3: G-code Parser**
- Existing: `feedtime.py` (basic time estimation)
- N.15: Advanced parser with arc support
- **Resolution:** Keep both, N.15 is more comprehensive

---

## 📊 Feature Comparison Matrix

| Feature | Module L | N.15 | N.16 | N.17 |
|---------|----------|------|------|------|
| **Polygon Offset** | ✅ L.1 | ❌ | ❌ | ✅ Enhanced |
| **Spiral Strategy** | ✅ L.2 | ❌ | ✅ Rect-only | ✅ Arbitrary |
| **Trochoids** | ✅ L.3 | ❌ | ✅ Corners | ❌ |
| **G-code Parse** | ❌ | ✅ Full | ❌ | ❌ |
| **Time Estimate** | ✅ Basic | ✅ Arc-aware | ❌ | ❌ |
| **Arc Linkers** | ❌ | ❌ | ❌ | ✅ |
| **Min-Engagement** | ✅ L.2 | ❌ | ❌ | ✅ |

---

## 🎯 Next Actions

1. ✅ Create integration plan
2. ⏳ Integrate N.15 (G-code parser + backplot)
3. ⏳ Integrate N.16 (adaptive kernels)
4. ⏳ Integrate N.17 (polygon offset)
5. ⏳ Create unified smoke test
6. ⏳ Update documentation

---

**Status:** Ready to begin N.15 integration  
**Next:** Copy `gcode_parser.py` and create backplot router
