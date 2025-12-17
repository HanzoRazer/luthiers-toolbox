# Helical v16.1 Production Upgrade Plan

**Status:** 🟡 Functional but needs production overhaul  
**Date:** November 13, 2025  
**Priority:** High (before Phase 3 integration)

---

## 🎯 Current State

**Works:** ✅ Core helical generation functional in testing  
**Issue:** ⚠️ Not production-ready - needs significant refactoring

### **What Works**
- ✅ Basic helical plunge generation
- ✅ G2/G3 arc commands
- ✅ CW/CCW direction support
- ✅ Post-processor presets (GRBL, Mach3, Haas, Marlin)
- ✅ IJ mode vs R mode
- ✅ Frontend form inputs
- ✅ API endpoints respond

### **Critical Issues for Production**

#### **1. Backend Architecture Issues**

**a) Monolithic Router (185 lines)**
- ❌ Business logic mixed with API layer
- ❌ No separation of concerns
- ❌ Hard to test individual components
- ❌ Arc generation inline in endpoint

**b) Missing Core CAM Module**
- ❌ No `cam/helical.py` module (should match Module L pattern)
- ❌ Arc math not reusable
- ❌ No unit tests for helical algorithm
- ❌ No integration with Module L adaptive pocketing

**c) Limited Error Handling**
- ❌ Basic validation only
- ❌ No chipload warnings (thin-wall risk)
- ❌ No radius vs pitch sanity checks
- ❌ No feed rate limits per material

**d) Missing Machine Profile Integration**
- ❌ Hard-coded feed rates (not from Module M)
- ❌ No acceleration limits
- ❌ No rapid feed awareness
- ❌ No jerk-aware time estimation (L.3 pattern)

**e) Statistics Incomplete**
- ❌ Basic length/time only
- ❌ No engagement angle calculation
- ❌ No chipload display
- ❌ No comparison to straight plunge

#### **2. Frontend Issues**

**a) Component Structure (90 lines)**
- ❌ No TypeScript interfaces for stats
- ❌ Minimal validation
- ❌ No real-time parameter preview
- ❌ No visual feedback (canvas preview missing)

**b) User Experience Gaps**
- ❌ No parameter presets (hardwood vs softwood)
- ❌ No tooltips explaining parameters
- ❌ No visual helix preview (2D/3D)
- ❌ No comparison mode (helical vs straight)

**c) Missing Integration**
- ❌ Not connected to geometry upload pipeline
- ❌ Can't apply to existing drill points
- ❌ No batch helical generation
- ❌ No export to DXF/SVG workflow

#### **3. API Design Issues**

**a) Request Model (HelicalReq)**
- ❌ Too many optional fields (unclear defaults)
- ❌ No validation ranges (radius > pitch?)
- ❌ No material-aware presets
- ❌ Missing safety checks

**b) Response Format**
- ❌ Minimal stats object
- ❌ No warnings array
- ❌ No toolpath metadata
- ❌ No visualization data (arc points)

**c) Endpoint Design**
- ❌ Only `/helical_entry` (no batch, no preview)
- ❌ No `/helical_plan` for simulation
- ❌ No `/helical_multi` for drilling patterns
- ❌ No websocket for large operations

#### **4. Missing Production Features**

**a) Safety & Validation**
- ❌ No thin-wall detection (helix too close to boundary)
- ❌ No stepover warning (radius too small for pitch)
- ❌ No feed rate capping (exceed machine limits?)
- ❌ No collision detection

**b) Integration with Existing Modules**
- ❌ No Module L integration (adaptive pockets need helical entry)
- ❌ No Module M profiles (hard-coded feeds)
- ❌ No Module N post system (using old preset pattern)
- ❌ No Blueprint Lab integration (drill points from images)

**c) Documentation Gaps**
- ❌ No inline API docs (FastAPI auto-docs incomplete)
- ❌ No algorithm documentation
- ❌ No chipload calculation formulas
- ❌ No material-specific guidelines

**d) Testing Coverage**
- ❌ No unit tests for helical algorithm
- ❌ No integration tests for API
- ❌ No E2E tests for component
- ❌ No performance benchmarks

---

## 🔧 Production Upgrade Roadmap

### **Phase A: Core Module Extraction** (Priority 1)

**Goal:** Separate business logic from API layer

**Tasks:**
1. Create `services/api/app/cam/helical_core.py` (200+ lines)
   - `helical_plunge()` - Core algorithm
   - `helical_stats()` - Calculate length/time/chipload
   - `helical_validate()` - Safety checks
   - `helical_preview_points()` - Return arc sample points for viz

2. Create `services/api/app/cam/helical_safety.py` (150+ lines)
   - `check_thin_wall()` - Radius vs boundary clearance
   - `check_chipload()` - Feed vs RPM vs pitch validation
   - `check_engagement()` - Radial engagement warnings
   - `check_machine_limits()` - Feed/accel caps

3. Update router to use core modules:
   ```python
   from ..cam.helical_core import helical_plunge, helical_stats
   from ..cam.helical_safety import helical_validate
   
   @router.post("/helical_entry")
   def helical_entry(body: HelicalReq):
       # Validate safety
       warnings = helical_validate(body, machine_profile)
       
       # Generate toolpath
       moves = helical_plunge(body)
       
       # Calculate stats
       stats = helical_stats(moves, body)
       
       return {"gcode": to_gcode(moves), "stats": stats, "warnings": warnings}
   ```

**Estimated:** 6-8 hours

---

### **Phase B: Module Integration** (Priority 2)

**Goal:** Connect helical to existing production modules

**Tasks:**
1. **Module M Integration:**
   - Pull feed rates from machine profiles
   - Use acceleration limits for time estimation
   - Apply rapid feed for clearance moves

2. **Module L Integration:**
   - Add `helical_entry=True` flag to adaptive pocketing
   - Replace straight plunge with helical ramp
   - Inherit tool diameter and stepdown from pocket plan

3. **Module N Integration:**
   - Migrate from `post_presets.py` to full N-series post system
   - Use post JSON configs (already exist for GRBL, Mach4, etc.)
   - Add post-specific arc formatting (IJ vs R vs IJK)

4. **Feedtime L.3 Integration:**
   - Use jerk-aware estimator for helical time
   - Account for arc penalties (10% slower)
   - Display both classic and jerk-aware estimates

**Estimated:** 4-6 hours

---

### **Phase C: Enhanced Validation** (Priority 2)

**Goal:** Production-grade safety checks

**Tasks:**
1. **Geometric Validation:**
   ```python
   # Thin-wall check
   if radius_mm < 2 * tool_diameter:
       warnings.append("Helix radius < 2× tool diameter - risk of tool breakage")
   
   # Pitch vs radius ratio
   if pitch_mm_per_rev > radius_mm * 0.5:
       warnings.append("Pitch too aggressive for radius - reduce to < 50% of radius")
   
   # Boundary clearance
   if min_distance_to_boundary < tool_diameter / 2:
       raise HTTPException(400, "Helix collides with boundary")
   ```

2. **Chipload Validation:**
   ```python
   # Calculate chipload per tooth
   chipload = feed_xy_mm_min / (rpm * num_flutes)
   
   # Material-specific ranges
   if material == "hardwood" and chipload > 0.15:
       warnings.append(f"Chipload {chipload:.3f}mm too high for hardwood (max 0.15mm)")
   ```

3. **Machine Limit Checks:**
   ```python
   # Compare to machine profile
   if feed_xy_mm_min > machine.max_feed_xy:
       raise HTTPException(400, f"Feed {feed_xy_mm_min} exceeds machine limit {machine.max_feed_xy}")
   ```

**Estimated:** 3-4 hours

---

### **Phase D: Frontend Overhaul** (Priority 3)

**Goal:** Production-quality UX

**Tasks:**
1. **Canvas Preview:**
   ```vue
   <canvas ref="preview" width="400" height="400" class="border"/>
   ```
   - Draw helix spiral (top view)
   - Show start point, end point, arc segments
   - Highlight engagement zones
   - Display radius, pitch visually

2. **Parameter Presets:**
   ```typescript
   const presets = {
     hardwood_finish: { pitch: 1.0, feed: 400 },
     hardwood_rough: { pitch: 1.5, feed: 600 },
     softwood_finish: { pitch: 1.5, feed: 800 },
     softwood_rough: { pitch: 2.0, feed: 1200 }
   }
   ```

3. **Real-time Validation:**
   - Show warnings inline (yellow background)
   - Show errors (red border, disable button)
   - Show success criteria (green checkmarks)

4. **Enhanced Stats Display:**
   ```vue
   <div class="stats-grid">
     <div>Length: {{ stats.length_mm }}mm</div>
     <div>Time: {{ stats.time_classic_s }}s ({{ stats.time_jerk_s }}s realistic)</div>
     <div>Revolutions: {{ stats.revolutions }}</div>
     <div>Chipload: {{ stats.chipload_mm }} mm/tooth</div>
     <div>Engagement: {{ stats.engagement_angle }}° avg</div>
     <div>Material Removal: {{ stats.volume_mm3 }} mm³</div>
   </div>
   ```

**Estimated:** 6-8 hours

---

### **Phase E: Extended API** (Priority 3)

**Goal:** Complete API surface

**Tasks:**
1. **Add Endpoints:**
   ```python
   @router.post("/helical_plan")  # Simulate without G-code
   @router.post("/helical_multi")  # Batch drilling pattern
   @router.post("/helical_validate")  # Validate params without generating
   ```

2. **Enhanced Response:**
   ```python
   {
     "gcode": "...",
     "stats": {
       "length_mm": 347.2,
       "time_classic_s": 41.7,
       "time_jerk_s": 52.3,
       "revolutions": 6.67,
       "chipload_mm": 0.083,
       "engagement_angle_avg": 15.2,
       "volume_mm3": 2830.5
     },
     "warnings": [
       "Chipload 0.083mm is high for hardwood (recommended < 0.10mm)",
       "Helix radius 10mm is tight for 6mm tool (recommended > 12mm)"
     ],
     "preview_points": [[x1,y1,z1], [x2,y2,z2], ...],  # For canvas
     "metadata": {
       "post": "GRBL",
       "units": "mm",
       "date": "2025-11-13T...",
       "tool_d": 6.0,
       "material": "hardwood"
     }
   }
   ```

**Estimated:** 3-4 hours

---

### **Phase F: Testing & Documentation** (Priority 4)

**Goal:** 80% test coverage, complete docs

**Tasks:**
1. **Unit Tests:**
   - `test_helical_core.py` - Algorithm tests
   - `test_helical_safety.py` - Validation tests
   - `test_helical_router.py` - API tests

2. **Integration Tests:**
   - Module L integration (adaptive pockets with helical entry)
   - Module M integration (machine profiles)
   - Module N integration (post processors)

3. **E2E Tests:**
   - `test_helical_frontend.ps1` - Component smoke tests
   - `test_helical_workflow.ps1` - Full workflow tests

4. **Documentation:**
   - `HELICAL_MODULE_H.md` - Complete module docs (like Module L docs)
   - `HELICAL_ALGORITHM_GUIDE.md` - Math and formulas
   - `HELICAL_QUICKREF.md` - Parameter guide
   - API docstrings for auto-generated FastAPI docs

**Estimated:** 6-8 hours

---

## 📊 Effort Summary

| Phase | Priority | Estimated Hours | Status |
|-------|----------|-----------------|--------|
| **A: Core Module** | 1 | 6-8 | Not started |
| **B: Module Integration** | 2 | 4-6 | Not started |
| **C: Validation** | 2 | 3-4 | Not started |
| **D: Frontend Overhaul** | 3 | 6-8 | Not started |
| **E: Extended API** | 3 | 3-4 | Not started |
| **F: Testing & Docs** | 4 | 6-8 | Not started |
| **TOTAL** | | **28-38 hours** | 🟡 Functional prototype |

**Timeline:**
- **Phases A-C (Critical):** 13-18 hours (2-3 work days)
- **Phases D-F (Polish):** 15-20 hours (2-3 work days)
- **Total Production Ready:** 4-6 work days

---

## 🎯 Recommended Approach

### **Option 1: Immediate Critical Fixes** (Recommended)
**Goal:** Make v16.1 production-safe without full rewrite

**Quick Wins (4-6 hours):**
1. Extract core algorithm to `cam/helical_core.py` (Phase A partial)
2. Add basic safety checks (Phase C critical only):
   - Radius < 2× tool diameter → error
   - Pitch > 50% radius → warning
   - Feed > 2000 mm/min → warning
3. Add warning display to frontend (Phase D partial)
4. Create basic unit tests (Phase F critical only)

**Defer:**
- Full Module M/L/N integration (can wait for Phase 3+)
- Canvas preview (nice-to-have, not critical)
- Extended API endpoints (future enhancement)

**Result:** Production-safe helical generation in 1 day of work

---

### **Option 2: Full Production Overhaul** (Ideal)
**Goal:** Complete all phases before Phase 3

**Timeline:** 4-6 work days (28-38 hours)

**Approach:**
- Weeks 1-2: Phases A-C (core, integration, validation)
- Week 3: Phases D-E (frontend, API)
- Week 4: Phase F (testing, docs)

**Result:** World-class helical system matching Module L quality

---

### **Option 3: Parallel Development** (Hybrid)
**Goal:** Start Phase 3 (N17) while improving v16.1

**Strategy:**
- **Now:** Quick critical fixes (Option 1 - 4-6 hours)
- **Phase 3 work:** Integrate N17 Polygon Offset
- **After Phase 3:** Full v16.1 overhaul (Option 2 - 3-4 days)

**Benefit:** Don't block Re-Forestation Plan progress
**Risk:** v16.1 stays in "functional but not polished" state longer

---

## 🚨 Critical Issues to Fix ASAP

**Before allowing production use:**

1. **Add radius validation:**
   ```python
   if radius_mm < tool_d * 2:
       raise HTTPException(400, "Helix radius must be >= 2× tool diameter")
   ```

2. **Add pitch validation:**
   ```python
   if pitch_mm_per_rev > radius_mm * 0.5:
       warnings.append("Pitch too aggressive - risk of tool breakage")
   ```

3. **Add feed rate cap:**
   ```python
   if feed_xy_mm_min > 2000:
       warnings.append("Feed rate very high - verify machine capability")
   ```

4. **Add chipload calculation:**
   ```python
   # Assume 2-flute, 18000 RPM (common router speeds)
   rpm = 18000
   num_flutes = 2
   chipload = feed_xy_mm_min / (rpm * num_flutes)
   if chipload > 0.15:
       warnings.append(f"Chipload {chipload:.3f}mm high for hardwood")
   ```

5. **Display warnings in UI:**
   ```vue
   <div v-if="warnings.length" class="bg-yellow-50 border-yellow-500 p-3">
     <h3>⚠️ Warnings</h3>
     <ul>
       <li v-for="w in warnings">{{ w }}</li>
     </ul>
   </div>
   ```

---

## 📋 Decision Point

**Recommendation:** **Option 1 (Quick Critical Fixes)** then **Option 3 (Parallel)**

**Rationale:**
- v16.1 works for testing/demos (current state is OK for Phase 2 verification)
- Critical safety checks prevent user errors (4-6 hours well spent)
- Don't block Phase 3-8 progress (Re-Forestation Plan momentum)
- Full overhaul can happen after N17/N16 integration (more context on patterns)

**Next Steps:**
1. Implement 5 critical fixes above (1-2 hours)
2. Mark Phase 2 as "Verified with caveats" (done)
3. Start Phase 3 (Integrate N17 Polygon Offset)
4. Schedule v16.1 production overhaul after Phase 3-4 complete

---

## 📚 Related Documentation

**Module Patterns to Follow:**
- `ADAPTIVE_POCKETING_MODULE_L.md` - Reference for module structure
- `PATCH_L3_SUMMARY.md` - Reference for safety validation
- `MACHINE_PROFILES_MODULE_M.md` - Reference for machine integration

**Integration Targets:**
- Module L (adaptive pocketing needs helical entry)
- Module M (machine profiles for feeds/rapids)
- Module N (post-processor system)

**Future Enhancements:**
- Blueprint Lab integration (helical at detected drill points)
- Batch processing (multi-hole drilling patterns)
- 3D visualization (interactive helix preview)

---

**Status:** 🟡 Functional but needs production upgrade  
**Priority:** High (before wider user adoption)  
**Estimated Effort:** 4-6 hours (critical fixes) or 28-38 hours (full overhaul)  
**Recommended:** Start with critical fixes, full overhaul after Phase 3-4
