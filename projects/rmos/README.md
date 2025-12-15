# 🎛️ Rosette Manufacturing OS (RMOS)

**Version:** 0.1.0-alpha  
**Status:** Sandbox Project  
**Last Updated:** November 20, 2025

---

## 🎯 Mission Statement

The **Rosette Manufacturing OS (RMOS)** is a complete factory subsystem for designing, manufacturing, and tracking **ultra-precision rosette inlay work** — from creative pattern design through CNC saw operations to production planning and job logging.

**Core Innovation:** Enable luthiers to design arbitrarily complex rosette patterns (including ultra-thin strips "thinner than a toothpick") and automatically generate CAM-ready toolpaths with manufacturing intelligence, safety guardrails, and production traceability.

---

## 📚 Quick Navigation

- **New to RMOS?** Start with [Architecture Overview](#architecture-overview)
- **Ready to implement?** See [Implementation Guide](./IMPLEMENTATION_GUIDE.md)
- **Need API docs?** Check [API Reference](./docs/API_REFERENCE.md)
- **Found a bug?** Review [Technical Audit](./docs/TECHNICAL_AUDIT.md)
- **Planning features?** Read [Roadmap](./docs/ROADMAP.md)

---

## 🏗️ Architecture Overview

RTL operates across **5 interconnected domains**:

### **1. Creative Layer** 🎨
**What:** Design rosette patterns visually  
**Components:**
- Rosette Manufacturing OS (Vue component)
- Pattern Library (save/load/edit)
- Multi-ring editor with per-ring configuration

**Key Features:**
- Concentric ring bands with arbitrary count
- Per-ring strip family assignment (wood species/color)
- Tile length overrides per ring
- Slice angle control (for angled cuts)
- Color hints for visual preview

### **2. CAM Layer** ⚙️
**What:** Convert patterns to CNC operations  
**Components:**
- Circular Saw Operations (multi-ring concentric cuts)
- Line Slicing Operations (parallel strip cuts)
- Multi-Slice Batch Engine
- G-code generation (G2/G3 arcs + linear moves)

**Key Features:**
- Circle geometry mode (concentric rings)
- Line geometry mode (parallel strips)
- Automatic radial stepping
- Tool selection + validation
- Risk analysis (rim speed, gantry span, deflection)

### **3. Manufacturing Planning Layer** 📊
**What:** Calculate material requirements  
**Components:**
- Ring Requirements Calculator
- Strip-Family Grouping Engine
- Material Planning System

**Key Features:**
- Circumference → tile count per ring
- Tile length adjustments for slice angles
- Strip-family aggregation (group by wood species)
- Total strip length calculations
- Stick count derivation (given strip dimensions)
- Configurable scrap factors

### **4. Production/Logging Layer** 📝
**What:** Track jobs and optimize processes  
**Components:**
- JobLog Integration (2 job types)
- Yield Tracking System
- Operator Notes + Best-Slice Identification

**Job Types:**
1. `saw_slice_batch` - Actual CNC cuts (line + circle modes)
2. `rosette_plan` - Pre-production manufacturing plans

**Key Features:**
- Every cut logged with metadata (tool, material, risk)
- Actual vs predicted yield tracking
- Best-slice identification per batch
- Historical performance analytics

### **5. Future Engineering Layer** 🚀
**What:** Advanced physics + AI (roadmap)  
**Planned Features:**
- Kerf + deflection physics modeling
- Arbor hardware jig library
- Glue-up recipe generator
- AI pattern suggestions
- Batch scheduling optimizer
- End-to-end traceability

---

## 🔥 The "Thinner Than a Toothpick" Problem

### **Challenge**
Luthiers create **mosaic-style rosettes** using wooden strips as thin as **0.3-0.8mm** (thinner than toothpicks). This requires:

1. **Angled Slicing** - Rotating stock to achieve desired width/length
2. **Extreme Precision** - ±0.05mm tolerance on ultra-thin cuts
3. **Safety Mechanisms** - Preventing tool deflection and strip breakage

### **Traditional Approach**
Manual setup with trial-and-error:
- Guess stick rotation angle
- Test cuts waste material
- No safety validation until cut fails
- No manufacturing planning (frequent material shortages)

### **RMOS Solution: Strip Recipe System**

**Workflow:**
```
Designer Input:
  - Desired tile geometry (rhombus, triangle, straight)
  - Tile dimensions (width, length, thickness)

RMOS Derives:
  - Source stick dimensions
  - Rotation angle (0-45°)
  - Slice thickness
  - Jig type (angle fixture or carrier block)
  - Safety validation (RED if < 0.4mm width)

CNC Output:
  - Angled slicing operation with jig setup
  - G-code with safety checks
  - Risk analysis (deflection, gantry span)
```

**Example:**
```typescript
// Designer wants: 0.5mm × 3mm × 30° rhombus tiles
StripRecipe {
  desired_cross_section: { width: 0.5, height: 3 },
  slice_angle_deg: 30,
  slice_thickness_mm: 0.5,
  
  // RMOS calculates:
  source_stick_size: { w: 6, h: 6, l: 300 },
  jig_type: "angle_fixture",
  
  // Safety checks:
  safety_checks: {
    min_strip_width: 0.4,
    requires_carrier: true,    // Too thin, use backing
    blade_kerf_ratio: 0.67,
    risk_grade: "RED"          // Warn before cutting
  }
}
```

---

## 📐 Core Data Structures

### **RosettePattern**
```typescript
{
  pattern_id: "uuid",
  name: "Celtic Knot 12-Ring",
  ring_bands: [
    {
      id: "uuid",
      index: 0,                      // Innermost ring
      strip_family_id: "ebony_black",
      color_hint: "#1a1a1a",
      tile_length_override_mm: 2.5,
      slice_angle_deg: 30
    },
    {
      id: "uuid",
      index: 1,
      strip_family_id: "maple_white",
      color_hint: "#f5f5dc",
      tile_length_override_mm: 3.0,
      slice_angle_deg: 0
    }
    // ... more rings
  ],
  created_at: "2025-11-20T14:30:00Z",
  updated_at: "2025-11-20T15:45:00Z"
}
```

### **SawSliceBatchOpCircle**
```typescript
{
  op_type: "saw_slice_batch",
  geometry_source: "circle_param",
  base_radius_mm: 20,              // Innermost ring
  num_rings: 3,
  radial_step_mm: 2.5,             // Ring spacing
  slice_thickness_mm: 0.8,
  tool_id: "thin_kerf_blade_001",
  material: "ebony",
  workholding: "vacuum",
  passes: 1
}
```

### **JobLogEntry (Rosette Plan)**
```typescript
{
  job_id: "job_20251120_143022",
  job_type: "rosette_plan",
  plan_pattern_id: "uuid",
  plan_guitars: 10,
  plan_total_tiles: 480,
  strip_plans: [
    {
      strip_family_id: "ebony_black",
      tiles_needed: 120,
      strip_length_m: 2.4,
      sticks_needed: 3,
      scrap_factor: 1.15
    },
    {
      strip_family_id: "maple_white",
      tiles_needed: 360,
      strip_length_m: 7.2,
      sticks_needed: 9,
      scrap_factor: 1.15
    }
  ],
  created_at: "2025-11-20T14:30:00Z"
}
```

---

## 🚀 Quick Start (When Ready to Implement)

### **Prerequisites**
- Python 3.11+ (backend)
- Node 18+ (frontend)
- ToolBox main repo cloned
- Familiarity with FastAPI + Vue 3

### **Step 1: Review Architecture**
```bash
cd projects/rmos
cat ARCHITECTURE.md        # Deep technical dive (30 min read)
```

### **Step 2: Review Implementation Guide**
```bash
cat IMPLEMENTATION_GUIDE.md  # Step-by-step patches (15 min read)
```

### **Step 3: Apply Patches in Order**
Patches are **cumulative** and **sequential**:
```bash
cd patches
cat PATCH_A_CORE.md        # Core infrastructure (1-2 hours)
cat PATCH_B_JOBLOG.md      # JobLog integration (1 hour)
cat PATCH_C_MULTIRING.md   # Multi-ring saw support (2 hours)
# ... continue through PATCH_O
```

### **Step 4: Test Each Patch**
```powershell
cd tests
.\test_joblog.ps1           # After Patch B
.\test_multiring_saw.ps1    # After Patch C
.\test_planner.ps1          # After Patch L
```

### **Step 5: Integrate with ToolBox**
```bash
# Link RMOS APIs to PipelineLab
# See IMPLEMENTATION_GUIDE.md § Integration Points
```

---

## 📋 Implementation Phases

### **Phase 0: Sandbox Setup** (1 week)
- ✅ Create folder structure
- ✅ Write documentation (this README, ARCHITECTURE, etc.)
- ✅ Define all 15 patches
- ⏸️ Prepare code bundles

### **Phase 1: MVP (v0.1)** (4-6 weeks)
**Goal:** Basic pattern + single-ring saw operations + JobLog

**Patches:** A, B, C, D
- Core RMOS infrastructure
- JobLog integration
- Single-ring circular saw operations
- Preview endpoints

**Deliverables:**
- Create/save/load basic rosette patterns
- Generate single-ring saw operations
- View jobs in JobLog Mini-Viewer
- Preview G-code before running

### **Phase 2: Multi-Family (v0.2)** (2-3 weeks)
**Goal:** Multi-strip-family planner + Pattern Library UI

**Patches:** E, F, G, H, I, J
- Multi-Ring OpPanel (Vue)
- Rosette Manufacturing OS
- Pattern → CAM mapper
- Pattern Library backend + frontend

**Deliverables:**
- Visual pattern editor
- Multi-family manufacturing planning
- Pattern library with search/filter
- Pattern → pipeline synchronization

### **Phase 3: Production Ready (v0.3)** (3-4 weeks)
**Goal:** Complete manufacturing planner + persistence

**Patches:** K, L, M, N, O
- Multi-family planner
- Planner → JobLog integration
- Manufacturing Plan Panel UI
- End-to-end pipeline sync
- SQLite persistence (replace in-memory)

**Deliverables:**
- Complete rosette manufacturing workflow
- Production-ready job logging
- Manufacturing plan generation
- Historical analytics

### **Phase 4: Advanced (v0.4)** (4-6 weeks)
**Goal:** Ultra-thin strip recipes + AI

**Features:**
- Strip recipe system (angled slicing)
- Jig library + recommendations
- AI pattern suggestions
- Enhanced risk modeling (kerf, deflection)

### **Phase 5: Complete Factory (v1.0)** (8-12 weeks)
**Goal:** Full production system

**Features:**
- Hardware integration (jigs, arbors)
- Batch scheduling
- Traceability system
- Multi-user support
- Production metrics dashboard

---

## 🔗 Integration with Main ToolBox

### **PipelineLab Integration**
RMOS provides pipeline nodes:
- `saw_slice_batch` (multi-ring + line modes)
- `rosette_manufacturing_plan` (planning node)

**Flow:**
```
Rosette Manufacturing OS
  ↓ emits pattern change
Pattern → CAM Mapper
  ↓ derives SawSliceBatchOp
PipelineLab Store
  ↓ updates node
Multi-Ring OpPanel
  ↓ previews G-code + risk
Run Pipeline
  ↓ executes operation
JobLog Writer
  ↓ stores job
JobLog Mini-Viewer
  ↓ displays history
```

### **JobInt Integration** (See Main Handoff Appendix A)
RMOS writes 2 job types:
1. `saw_slice_batch` - Actual cuts
2. `rosette_plan` - Manufacturing plans

Both appear in unified JobLog with filtering:
```
/joblog?job_type=rosette_plan
/joblog?tool_id=thin_kerf_blade_001
```

### **Art Studio Integration** (See Main Handoff Appendix B)
- Rosette patterns use Art Studio risk analytics
- Compare mode for pattern iterations
- Preset scorecards for manufacturing approaches

---

## 📁 Repository Structure

```
projects/rmos/
├── README.md                    # This file
├── ARCHITECTURE.md              # Complete technical design
├── IMPLEMENTATION_GUIDE.md      # Step-by-step deployment
│
├── patches/                     # 15 patch bundles (A-O)
│   ├── PATCH_A_CORE.md
│   ├── PATCH_B_JOBLOG.md
│   ├── PATCH_C_MULTIRING.md
│   ├── PATCH_D_PREVIEW.md
│   ├── PATCH_E_OPPANEL.md
│   ├── PATCH_F_JOBLOG_UI.md
│   ├── PATCH_G_TEMPLATE.md
│   ├── PATCH_H_MAPPER.md
│   ├── PATCH_I_LIBRARY_BE.md
│   ├── PATCH_J_LIBRARY_FE.md
│   ├── PATCH_K_PLANNER_1.md
│   ├── PATCH_L_PLANNER_MULTI.md
│   ├── PATCH_M_PLAN_JOBLOG.md
│   ├── PATCH_N_PLAN_UI.md
│   └── PATCH_O_SYNC.md
│
├── code_bundles/               # Ready-to-deploy code
│   ├── backend/
│   │   ├── schemas/            # Pydantic models
│   │   ├── routes/             # FastAPI routers
│   │   ├── core/               # Business logic
│   │   └── utils/              # Helper functions
│   └── frontend/
│       ├── components/         # Vue components
│       ├── models/             # TypeScript types
│       ├── utils/              # Mappers, calculators
│       └── stores/             # Pinia stores
│
├── tests/                      # PowerShell smoke tests
│   ├── test_joblog.ps1
│   ├── test_multiring_saw.ps1
│   ├── test_pattern_mapper.ps1
│   ├── test_planner.ps1
│   └── test_integration.ps1
│
└── docs/                       # Additional documentation
    ├── API_REFERENCE.md        # Complete endpoint docs
    ├── TECHNICAL_AUDIT.md      # Known issues + debt
    ├── ROADMAP.md              # v0.1 → v1.0 timeline
    ├── DESIGN_DECISIONS.md     # Architecture rationale
    └── TROUBLESHOOTING.md      # Common issues + fixes
```

---

## 🎓 Learning Path

### **For New Developers:**

1. **Read This README** (20 min)
   - Understand the "thinner than a toothpick" problem
   - Review 5-domain architecture
   - See core data structures

2. **Study ARCHITECTURE.md** (45 min)
   - Deep dive into each domain
   - Understand data flows
   - Review integration points

3. **Review First 3 Patches** (1 hour)
   - `PATCH_A_CORE.md` - Infrastructure
   - `PATCH_B_JOBLOG.md` - Logging
   - `PATCH_C_MULTIRING.md` - Multi-ring saw

4. **Try a Small Implementation** (2-3 hours)
   - Apply Patches A + B
   - Create a test pattern
   - View in JobLog
   - Verify with tests

### **For Experienced ToolBox Developers:**

1. **Skim This README** (5 min)
2. **Jump to IMPLEMENTATION_GUIDE.md** (10 min)
3. **Apply patches sequentially** (varies by phase)
4. **Refer back to ARCHITECTURE.md as needed**

---

## 🐛 Known Issues & Technical Debt

**See:** [docs/TECHNICAL_AUDIT.md](./docs/TECHNICAL_AUDIT.md) for complete list.

**High Priority Issues:**

1. **Schema Inconsistencies**
   - `JobLogEntry` forces `num_slices` for planning jobs (should be optional)
   - Need separate schemas for different job types

2. **Missing UI Fields**
   - `tile_length_override_mm` not exposed in ring editor
   - `slice_angle_deg` not wired to controls

3. **Multi-Family Conflicts**
   - Planner uses first-seen tile length when same family has different overrides
   - Need conflict resolution strategy

4. **Storage Layer**
   - In-memory dictionaries only (not production-ready)
   - Need SQLite migration for v0.3

5. **API Gaps**
   - No ring index validation
   - No pattern versioning/history
   - Missing atomic saw job + JobLog write

---

## 💡 Design Principles

1. **Creative First** - Never constrain luthier creativity
2. **Safety Always** - Flag unsafe operations before execution
3. **Intelligence Embedded** - Auto-calculate everything possible
4. **Traceability Built-In** - Log every operation with full context
5. **Modular Architecture** - Easy to extend (new shapes, jigs, etc.)
6. **Production Ready** - Not a toy, a real factory system

---

## 🤝 Contributing

### **Before You Start:**
1. Read this README + ARCHITECTURE.md
2. Review TECHNICAL_AUDIT.md for known issues
3. Check ROADMAP.md for current phase
4. Look at existing patches for code style

### **Development Workflow:**
1. Pick an unimplemented patch or bug from TECHNICAL_AUDIT.md
2. Create feature branch: `rmos/patch-X-description`
3. Apply code from `code_bundles/` or write new
4. Add tests in `tests/`
5. Update documentation if needed
6. Test locally with smoke tests
7. Submit PR with clear description

### **Code Style:**
- Backend: Follow FastAPI + Pydantic conventions
- Frontend: Vue 3 Composition API (`<script setup>`)
- TypeScript for all `.ts` files
- Document complex algorithms inline

---

## 📞 Support & Resources

### **Documentation:**
- **Main ToolBox Handoff:** `../../CAM_CAD_DEVELOPER_HANDOFF.md` (Appendix E)
- **RMOS Architecture:** `./ARCHITECTURE.md`
- **Implementation Guide:** `./IMPLEMENTATION_GUIDE.md`
- **API Reference:** `./docs/API_REFERENCE.md`

### **Testing:**
```powershell
# Run all smoke tests
cd tests
Get-ChildItem .\test_*.ps1 | ForEach-Object { & $_ }

# Run specific test
.\test_multiring_saw.ps1
```

### **Key Contacts:**
- **Repository:** https://github.com/HanzoRazer/guitar_tap
- **RMOS Lead:** TBD
- **Integration Questions:** See main ToolBox team

---

## 🎸 Vision

**RMOS represents the next evolution of Luthier's Tool Box:**

Moving beyond basic CAM operations into **domain-specific manufacturing intelligence**. The "thinner than a toothpick" problem is just the beginning.

**The same architecture supports:**
- Binding strip cutting
- Purfling channel routing
- Fret slot precision work
- Any lutherie operation requiring extreme precision + planning

**RMOS proves ToolBox can be both:**
- A general-purpose CNC CAM platform
- A specialized lutherie factory system

**Let's build the Rosette Factory! 🎛️🎸**

---

**Status:** ✅ Sandbox Complete, Ready for Phase 1 Implementation  
**Next Milestone:** Apply Patches A-D for v0.1 MVP  
**Target Date:** Q1 2026
