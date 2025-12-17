# Projects On Hold - Inventory

**Generated:** November 25, 2025  
**Purpose:** Comprehensive list of all deferred/pending projects for future reference

---

## 📊 Summary

| Category | Count | Combined Status |
|----------|-------|-----------------|
| **Clone/Segmentation Projects** | 1 | Analysis Complete, Awaiting Q1 2026 |
| **Neck Profile Integration** | 1 | Analysis Complete, Awaiting Decision |
| **Compare Mode Integration** | 1 | On Hold Until December 2025 |
| **Art Studio Bundle 5 Frontend** | 1 | Backend Complete, Frontend Pending |
| **Total Projects On Hold** | **4** | Ready When Priorities Allow |

---

## 🗂️ Detailed Project List

### **1. Clone Project - Repository Segmentation**

**Document:** `docs/CLONE_PROJECT_DEVELOPER_HANDOFF.md`  
**Status:** 📋 Planning & Design Complete → Ready for Implementation  
**Date Added to Hold:** November 25, 2025  
**Estimated Timeline:** 12-24 weeks for full ecosystem

**What It Is:**
- Segment monorepo into 3 commercial products (Express, Pro, Enterprise)
- Create 4 standalone digital products for Etsy/Gumroad
- Product diversification strategy to pre-empt market copycats

**Products Planned:**

| Product | Target Market | Price | Repo Name |
|---------|--------------|-------|-----------|
| Express Edition | Hobbyists | $49-$79 | luthiers-toolbox-express |
| Pro Edition | Luthiers/CNC Shops | $299-$399 | luthiers-toolbox-pro |
| Enterprise Edition | Guitar Companies | $899-$1299 | luthiers-toolbox-enterprise |
| Parametric Guitar Designer | Etsy/Gumroad | $39-$59 | parametric-guitar-designer |
| Guitar Neck Templates | Etsy/Gumroad | $14.95-$79 | guitar-neck-templates |
| Blueprint Reader | Construction | $59-$99 | blueprint-reader-designer |

**Why On Hold:**
- Strategic timing: "may not likely be actually needed until 2nd quarter 2026"
- Current priorities: Core platform features (B26, Compare Mode, etc.)
- Resource allocation: Solo development requires focus

**Next Actions When Ready:**
1. Create GitHub/GitLab repos for each product
2. Tag golden master snapshot (v0.8.0-core)
3. Clone and prune first repository (Express Edition)
4. Launch Etsy digital products (Neck Templates, Parametric Designer)

**Revenue Potential:** $116-212K/year across all products

**Related Documents:**
- `docs/CLONE_PROJECT_DEVELOPER_HANDOFF.md` (full handoff guide)
- `Clone_Project.txt` (original 2145-line chat history)

---

### **2. Neck Profile Integration**

**Documents:** 
- `docs/NECK_PROFILE_BUNDLE_ANALYSIS.md` (800+ lines)
- `docs/NECK_PROFILE_QUICKSTART.md` (350+ lines)

**Status:** 📋 Analysis Complete → Ready to Integrate When Priorities Allow  
**Date Added to Hold:** November 25, 2025  
**Estimated Timeline:** 5-8 hours for full integration

**What It Is:**
- Complete neck profile generation system for Strat/Tele/Les Paul necks
- Generate DXF cross-sections for Fusion 360 import
- Interactive NeckLab UI with SVG preview
- Compare Mode integration for side-by-side neck comparisons
- Persistent diff tracking (thickness/width deltas)

**4 Integration Phases:**

| Phase | Components | Time | Status |
|-------|-----------|------|--------|
| Phase 1: Backend Core | 5 Python files, 3 JSON configs | 1-2 hrs | Ready |
| Phase 2: NeckLab UI | 1 Vue file, router registration | 2-3 hrs | Ready |
| Phase 3: Compare Bridge | CompareLabView updates | 1-2 hrs | Ready |
| Phase 4: Diff Tracking | 2 Python JSONL files | 1 hr | Ready |

**Profiles Included:**
- 3 guitar configs: Strat Modern C, Tele Modern C/U, Les Paul '59 Round
- Profile types: C (ellipse), V (sharp bottom), U (flat bottom)

**Why On Hold:**
- User decision: "Wait and integrate later after other priorities"
- Core platform takes precedence

**Next Actions When Ready:**
1. Implement Phase 1 (Backend Core) - Create neck_profiles utility module
2. Test backend endpoints (`/cam/neck/profiles`, `/section_dxf`)
3. Add Phase 2 (NeckLab UI) - Create NeckLabView.vue
4. Wire Compare Mode bridge for neck comparisons

**Technical Stack:**
- Backend: Python (ezdxf 1.1.0+), FastAPI routers
- Frontend: Vue 3 Composition API
- Storage: JSON configs, JSONL diff tracking
- Export: DXF/SVG in-memory generation

**Related Documents:**
- `docs/NECK_PROFILE_BUNDLE_ANALYSIS.md` (technical analysis)
- `docs/NECK_PROFILE_QUICKSTART.md` (step-by-step guide)
- `GitHub-Neck _Profile_ bundle.txt` (4449-line source bundle)

---

### **3. Compare Mode Integration**

**Document:** `.github/COMPARE_MODE_REMINDER.md`  
**Status:** 📌 ON HOLD - Awaiting Integration Planning  
**Created:** November 15, 2025  
**Next Review:** December 1, 2025 (2 weeks)  
**Priority:** MEDIUM (Unblocks Item 17)

**What It Is:**
- Universal comparison tool for baseline vs candidate analysis
- Tracks geometry/toolpath changes across iterations
- Integrates with Adaptive Lab, Relief Lab, or Blueprint pipeline

**Integration Options:**

| Option | Component | Use Case |
|--------|-----------|----------|
| Option 1 | AdaptivePocketLab.vue | Track pocket optimization iterations |
| Option 2 | ArtStudioRelief.vue | Compare relief carving strategies |
| Option 3 | Blueprint → DXF | Quality control for template validation |
| Option 4 | CompareModeLab.vue (new) | General-purpose diff viewer |

**Why On Hold:**
- Awaiting integration decision (which Lab to wire first)
- Needs architectural planning for reusable comparison engine

**Reminder Schedule:**
- ✅ Week 1 (Nov 22): Review integration options
- 🔜 Week 2 (Nov 29): Finalize architecture
- 🔜 Week 3 (Dec 6): Begin implementation if ready
- 🔜 Month 1 (Dec 15): Progress check-in
- 🔜 Month 2 (Jan 15, 2026): Final review

**Next Actions When Ready:**
1. Choose integration path (Adaptive/Relief/Blueprint/Standalone)
2. Design comparison engine interface
3. Implement baseline storage mechanism
4. Add "Save as Baseline" UI controls
5. Create diff visualization component

**Related Work Completed:**
- B26 Baseline Marking (commit 627711f) - Job tracking baseline system
- Compare jobs infrastructure already exists

**Related Documents:**
- `.github/COMPARE_MODE_REMINDER.md` (full planning doc)
- `docs/COMPARE_MODE_DEVELOPER_HANDOFF.md` (pending creation)

---

### **4. Art Studio Bundle 5 - Frontend Integration**

**Documents:**
- `ART_STUDIO_BUNDLE5_BACKEND_COMPLETE.md`
- `ART_STUDIO_BUNDLE5_QUICKREF.md`

**Status:** ✅ Backend Complete (8/8 files) | ⏸️ Frontend Pending (7 files)  
**Date Created:** November 2025  
**Estimated Timeline:** 3-5 hours for frontend wiring

**What It Is:**
- Bundle 5: Relief carving optimization system
- Backend: Complete with 8 Python modules
- Frontend: 7 Vue components awaiting integration

**Backend Components (Complete):**
1. ✅ `relief_budget.py` - Relief depth budget calculator
2. ✅ `relief_kernel_core.py` - Core relief kernel logic
3. ✅ `relief_zone_spec.py` - Zone specification schema
4. ✅ `relief_slice_engine.py` - Slice generation engine
5. ✅ `relief_viz.py` - Visualization utilities
6. ✅ `relief_optimizer.py` - Optimization algorithms
7. ✅ `relief_router.py` - FastAPI endpoints
8. ✅ `relief_schemas.py` - Pydantic models

**Frontend Components (Pending):**
1. ⏸️ `ReliefBudgetPanel.vue` - Budget configuration UI
2. ⏸️ `ReliefKernelEditor.vue` - Kernel parameter editor
3. ⏸️ `ReliefZoneDesigner.vue` - Zone drawing tool
4. ⏸️ `ReliefSlicePreview.vue` - 2D slice visualization
5. ⏸️ `Relief3DViewer.vue` - 3D relief preview (three.js)
6. ⏸️ `ReliefOptimizerPanel.vue` - Optimization controls
7. ⏸️ `ArtStudioReliefLab.vue` - Main view component

**Why On Hold:**
- Frontend requires router setup + three.js integration
- Dependencies: Vue Router configuration, 3D rendering library
- Lower priority than core CAM features

**Next Actions When Ready:**
1. Install three.js dependency (`npm install three`)
2. Create 7 Vue components in `packages/client/src/components/relief/`
3. Add route to `packages/client/src/router/index.ts`
4. Wire API calls to backend endpoints
5. Test full relief optimization workflow

**API Endpoints Available:**
- `POST /cam/relief/budget` - Calculate relief budget
- `POST /cam/relief/kernel` - Generate relief kernel
- `POST /cam/relief/zones` - Define relief zones
- `POST /cam/relief/slices` - Generate slice previews
- `POST /cam/relief/optimize` - Run optimization

**Related Documents:**
- `ART_STUDIO_BUNDLE5_BACKEND_COMPLETE.md` (complete backend docs)
- `ART_STUDIO_BUNDLE5_QUICKREF.md` (quick reference)

---

## 📅 Tentative Roadmap

### **Q4 2025 (Now - December 31)**
- Focus: Core platform features (Compare Mode, remaining bundles)
- On Hold: All 4 projects remain deferred

### **Q1 2026 (January - March)**
- **Week 1-4:** Neck Profile Integration (5-8 hours)
- **Week 5-8:** Compare Mode Integration (choose path + implement)
- **Week 9-12:** Art Studio Bundle 5 Frontend (3-5 hours)

### **Q2 2026 (April - June)**
- **Clone Project Launch:**
  - Week 1-4: Express Edition + Neck Templates (Etsy)
  - Week 5-8: Parametric Guitar Designer (Etsy)
  - Week 9-12: Pro Edition segmentation

---

## 🎯 Reactivation Criteria

**Projects can be reactivated when:**

1. **Core Platform Stable:**
   - All critical CAM features complete
   - Test suite passing
   - No blocking bugs

2. **User Decision Made:**
   - Integration path chosen (for Compare Mode)
   - Product priorities confirmed (for Clone Project)
   - Resource allocation confirmed (solo vs team)

3. **Dependencies Ready:**
   - three.js installed (for Bundle 5)
   - Router configured (for new views)
   - GitHub repos created (for Clone Project)

4. **Market Timing:**
   - Q1 2026 for neck integration (internal)
   - Q2 2026 for Clone Project (external market launch)

---

## 📝 Notes

**Decision Log:**
- **Nov 25, 2025:** User confirmed "Wait and integrate later after other priorities" for Neck Profile
- **Nov 25, 2025:** User confirmed "put this one in reserve also" for Clone Project
- **Nov 15, 2025:** Compare Mode placed on hold until December 1 review

**Strategic Rationale:**
- Focus on core platform before diversification
- Analysis/planning complete = quick activation when ready
- No code rot risk (all docs current, no partial implementations)

**Estimated Combined Value:**
- Clone Project: $116-212K/year revenue potential
- Neck Profile: Major feature for Pro/Enterprise editions
- Compare Mode: Unblocks optimization workflows
- Bundle 5: Completes Art Studio relief system

---

## ✅ Action Items

**For User:**
- [ ] Review this inventory quarterly (Dec 2025, Mar 2026, Jun 2026)
- [ ] Update priorities as core platform matures
- [ ] Decide on Q2 2026 Clone Project timing

**For Development:**
- [ ] Keep docs synchronized with main repo changes
- [ ] Test integration points remain valid
- [ ] Update roadmap when reactivating projects

---

**Total Projects On Hold:** 4  
**Total Estimated Integration Time:** 20-36 hours  
**Total Revenue Potential:** $116-212K/year (Clone Project only)  
**Next Review Date:** December 1, 2025 (Compare Mode)  
**Target Reactivation:** Q1-Q2 2026
