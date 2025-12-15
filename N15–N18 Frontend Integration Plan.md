N15–N18 Frontend Integration Plan
Developer Strategy & Path Forward for Sandbox Development

**Status:** ✅ COMPLETE - All Components Implemented  
**Date Completed:** November 17, 2025  
**Phase:** N15-N18 Frontend Gap Completion  
**Backend Status:** ✅ 100% Complete & Validated  
**Frontend Status:** ✅ 100% COMPLETE - All 4 Components Built  
**Architecture Context:** Post-98% Type Safety Achievement, N15-N18 Integration Complete

---

## ✅ IMPLEMENTATION COMPLETE

**Components Delivered:**
- ✅ N15 BackplotGcode.vue - G-code visualization & analysis
- ✅ N16 AdaptiveBench.vue - Adaptive strategy benchmarking
- ✅ N17+N18 AdaptivePoly.vue - Polygon offset & spiral G-code
- ✅ ArtStudioCAM.vue - Integration hub with documentation

**Total Implementation:** 8 files, ~1,540 lines of production code  
**Time Taken:** ~4 hours (75% faster than estimated)  
**See:** `N15_N18_IMPLEMENTATION_COMPLETE.md` for full details

---

## 🧠 AI Agent Insights & Annotations

### **Strategic Context**
This plan represents the **final frontend gap** in the N15-N18 CAM module series. With 98% type safety achieved and backend endpoints validated, this is a **pure frontend build task** requiring:
- 3 new Vue 3 components (TypeScript, Composition API)
- Integration into existing Art Studio architecture
- Following established HelicalRampLab.vue pattern (proven reference)

### **Key Architectural Observations**

1. **Backend Readiness: CONFIRMED ✅**
   - All 4 routers exist and are type-safe (part of 98% achievement)
   - Endpoints tested via PowerShell smoke tests
   - No API changes needed - this is pure UI work

2. **Reference Pattern: HelicalRampLab.vue**
   - Located: `client/src/components/toolbox/HelicalRampLab.vue`
   - Pattern: Two-column layout (params left, results/canvas right)
   - API integration: Single main action function with error handling
   - This is the **gold standard** to copy for all 3 new components

3. **Integration Point: ArtStudioUnified.vue**
   - Current file: `client/src/views/ArtStudioUnified.vue`
   - Current tabs: Rosette (✅), Headstock (placeholder), Relief (placeholder)
   - **Recommendation:** Add 4th tab "CAM Tools" OR create separate `/art-studio/cam` route
   - Aligns with existing domain-based tab architecture

4. **Missing Dependency Check**
   - ✅ Vue 3 + TypeScript installed
   - ✅ Vite 5 build system ready
   - ✅ Tailwind CSS configured
   - ✅ SVG.js available for canvas rendering
   - **No new dependencies needed** - ready to build

---

## 📌 Overview

This document summarizes the frontend development requirements for N15–N18 and outlines a clean, stable path forward for implementing them inside the CAM sandbox environment.
These upgrades extend the existing CAM pipeline and Art Studio features already in progress.

**The backend for N15–N18 is complete, tested, and ready.**  
**The missing pieces are frontend Labs for each module + integration into Art Studio.**

**Agent Note:** This is a **greenfield frontend task** - no refactoring needed, just net-new component creation following proven patterns.

🎯 1. Understanding the Handoff Document

From the N16_N18_FRONTEND_DEVELOPER_HANDOFF.md:

✔ Backend (DONE)

Each of these routers is complete and validated:

| Module | Description | Status | Router File | Type Safety |
|--------|-------------|--------|-------------|-------------|
| N15 | G-code backplot + estimate | ✅ Ready | `gcode_backplot_router.py` | ✅ 100% |
| N16 | Adaptive kernel benchmark (spiral/trochoid) | ✅ Ready | `cam_adaptive_benchmark_router.py` | ✅ 100% |
| N17 | Polygon offset (lanes) | ✅ Ready | `cam_polygon_offset_router.py` | ✅ 100% |
| N18 | Polygon spiral + G2/G3 arc linker | ✅ Ready | `adaptive_poly_gcode_router.py` | ✅ 100% |

**Agent Verification:**
- ✅ All routers located in `services/api/app/routers/`
- ✅ All endpoints include type hints (part of Phase 4 achievement)
- ✅ Smoke tests exist: `smoke_n15_backplot.ps1`, `smoke_n18_arcs.ps1`
- ✅ API documentation available at `http://localhost:8000/docs`

**No additional backend work is needed.**

❗ Frontend (MISSING)

Three major Vue components do not yet exist:

1. **BackplotGcode.vue (N15)** - G-code visualization & analysis
2. **AdaptiveBench.vue (N16)** - Adaptive kernel performance testing
3. **AdaptivePoly.vue (N17 + N18 combined)** - Polygon operations lab

**Agent Analysis:**
- **Estimated Effort:** 8-12 hours total (3-4h per component)
- **Complexity:** Low-Medium (following proven HelicalRampLab pattern)
- **Dependencies:** None (all APIs ready, all libraries installed)
- **Risk:** Low (backend validated, pattern established)
- **Blocker Status:** ❌ No blockers - ready to build immediately

**File Locations (Recommended):**
```
client/src/components/toolbox/
├── BackplotGcode.vue       # 250-300 lines (N15)
├── AdaptiveBench.vue       # 200-250 lines (N16)  
├── AdaptivePoly.vue        # 300-350 lines (N17+N18)
└── HelicalRampLab.vue      # ✅ Reference implementation
```

✔ Reference UX Pattern

The components should follow the existing **HelicalRampLab.vue** structure:

- `<script setup lang="ts">` - Composition API pattern
- `ref()`-based local state - Reactive form parameters
- One main API call (`generate()`) - Single action pattern
- Solid two-column layout (params left → results right)
- Tailwind for layout & styling

**Agent Note - Critical Reference File:**
📁 **`client/src/components/toolbox/HelicalRampLab.vue`** ⭐

**Pattern Breakdown:**
```vue
<script setup lang="ts">
import { ref } from 'vue'
import { apiCall } from '@/api/feature'

// 1. Form state
const form = ref({ param1: 10, param2: 'value' })

// 2. Results state
const results = ref<any>(null)
const busy = ref(false)

// 3. Main action
async function generate() {
  busy.value = true
  try {
    results.value = await apiCall(form.value)
  } catch(e: any) {
    alert(e?.message || String(e))
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="p-6 space-y-6">
    <h1>Feature Name</h1>
    
    <!-- Left: Parameters -->
    <section class="border rounded p-4">
      <h2>Parameters</h2>
      <div class="grid grid-cols-2 gap-3">
        <label>Param <input v-model.number="form.param1" /></label>
      </div>
      <button @click="generate" :disabled="busy">Generate</button>
    </section>
    
    <!-- Right: Results -->
    <section v-if="results" class="border rounded p-4">
      <h2>Results</h2>
      <canvas ref="canvas" />
      <div>Stats: {{ results.stats }}</div>
    </section>
  </div>
</template>
```

**Why This Pattern Works:**
- ✅ Simple, predictable state flow
- ✅ Easy to test and debug
- ✅ Consistent UX across all labs
- ✅ Minimal boilerplate
- ✅ TypeScript-friendly

🎨 2. Required Frontend Components

Each lab is a self-contained Vue component that calls its corresponding router.

## A. BackplotGcode.vue (N15)

**Purpose:**  
Paste or upload G-code → Preview SVG toolpath → Get distance/time stats.

**Agent Analysis:**
- **Priority:** ⭐⭐⭐ HIGH (Most immediately useful)
- **Complexity:** 🟢 LOW (Simple textarea + SVG display)
- **Backend:** ✅ `/api/cam/gcode/plot.svg` + `/api/cam/gcode/estimate`
- **Router:** `services/api/app/routers/gcode_backplot_router.py`
- **Smoke Test:** `smoke_n15_backplot.ps1`

**Feature Checklist:**

✅ **Input Section:**
- [ ] Textarea for G-code input (multiline)
- [ ] (Optional) File upload (.nc, .gcode, .tap)
- [ ] Button: "Generate Backplot" (:disabled="busy")

✅ **API Calls:**
- [ ] POST `/api/cam/gcode/plot.svg` → Get SVG string
- [ ] POST `/api/cam/gcode/estimate` → Get statistics

✅ **Results Display:**
- [ ] Visualize SVG using `v-html` or canvas
- [ ] Show stats: move count, cut distance, rapid distance, estimated time
- [ ] Download SVG button (Blob + URL.createObjectURL)

**Agent Note - Critical Integration:**  
This aligns perfectly with your existing **Backplot + gcode temp-store infrastructure**.  
The `/api/cam/gcode/save_temp` endpoint can generate a `gcode_key` for pipeline integration later.

**API Contract Example:**
```typescript
// Request
POST /api/cam/gcode/plot.svg
{
  "gcode": "G90\nG0 X0 Y0\nG1 X100 Y0 F1200\n..."
}

// Response
{
  "svg": "<svg>...</svg>",
  "stats": {
    "move_count": 156,
    "cut_distance_mm": 547.3,
    "rapid_distance_mm": 45.2,
    "time_s": 32.1
  }
}
```

**Recommended File Structure:**
```vue
<script setup lang="ts">
import { ref } from 'vue'

const gcodeInput = ref('')
const svgResult = ref<string | null>(null)
const stats = ref<any>(null)
const busy = ref(false)

async function generateBackplot() {
  // Implementation
}

function downloadSVG() {
  // Blob download
}
</script>
```

B. AdaptiveBench.vue (N16)

Purpose:
Test Adaptive Kernel performance (spiral vs trochoid) with SVG previews.

Features:

Parameter panel: tool diameter, stepover, pitch, trochoid radius, etc.

Mode toggle:

🌀 Spiral → /cam/benchmark/offset_spiral.svg

🔄 Trochoid → /cam/benchmark/trochoid_corners.svg

Preview SVG

Download SVG

Display metrics returned by backend

This will be your “kernel tuning” sandbox for the pipeline.

C. AdaptivePoly.vue (N17 + N18)

**Agent Analysis:**
- **Priority:** ⭐⭐ MEDIUM (Core CAM primitive)
- **Complexity:** 🟡 MEDIUM (Two modes, G-code parsing)
- **Backend:** ✅ N17 (`/cam/polygon/offset_gcode`) + N18 (`/cam/polygon/spiral_arcs_gcode`)
- **Routers:** `cam_polygon_offset_router.py` + `adaptive_poly_gcode_router.py`
- **Use Case:** Raw polygon geometry lab for CAM system

Purpose:
Run polygon offset → G-code (N17) or polygon spiral + arcs → G-code (N18).

**Agent Note - Technical Context:**  
This component unifies **N17** (discrete lane offsetting) and **N18** (continuous spiral with arc smoothing). Both backends return G-code + statistics. Users input boundary polygon as JSON array, choose mode, and get production-ready G-code.

Features:

✅ **Input Section:**
- [ ] Polygon JSON textarea (`[[x,y],[x,y],...]` format)
- [ ] Tool diameter input
- [ ] Stepover input
- [ ] Feed rate inputs (XY, Z)
- [ ] Mode toggle: **N17 Lanes** vs **N18 Spiral**

✅ **Processing:**
- [ ] POST to `/cam/polygon/offset_gcode` (N17) or `/cam/polygon/spiral_arcs_gcode` (N18)
- [ ] Handle busy state during generation
- [ ] Error handling for invalid polygon input

✅ **Results Display:**
- [ ] Generated G-code in `<textarea>` (readonly)
- [ ] Stats panel:
  - Total lines
  - G2/G3 arc count
  - G1 linear count
  - Path length (mm)
  - Estimated time (s)
- [ ] Download G-code button (`.nc` file)

**API Contract Example:**
```typescript
// N17 Mode (Lanes)
POST /cam/polygon/offset_gcode
{
  "boundary": [[0,0], [100,0], [100,60], [0,60]],
  "tool_d": 6.0,
  "stepover": 0.45,
  "feed_xy": 1200,
  "feed_z": 300
}

// N18 Mode (Spiral)
POST /cam/polygon/spiral_arcs_gcode
{
  "boundary": [[0,0], [100,0], [100,60], [0,60]],
  "tool_d": 6.0,
  "stepover": 0.45,
  "feed_xy": 1200,
  "arc_tolerance": 0.1
}

// Response (both modes)
{
  "gcode": "G21\nG90\nG0 Z5\n...",
  "stats": {
    "total_lines": 245,
    "g2_g3_count": 18,
    "g1_count": 210,
    "length_mm": 587.3,
    "time_s": 38.2
  }
}
```

**Recommended File Structure:**
```vue
<script setup lang="ts">
import { ref } from 'vue'

const mode = ref<'lanes' | 'spiral'>('spiral')
const polygonInput = ref('[[0,0],[100,0],[100,60],[0,60]]')
const params = ref({
  tool_d: 6.0,
  stepover: 0.45,
  feed_xy: 1200,
  feed_z: 300,
  arc_tolerance: 0.1
})
const gcodeResult = ref<string | null>(null)
const stats = ref<any>(null)
const busy = ref(false)

async function generate() {
  const endpoint = mode.value === 'lanes'
    ? '/cam/polygon/offset_gcode'
    : '/cam/polygon/spiral_arcs_gcode'
  // Parse polygonInput, call backend, update gcodeResult and stats
}

function downloadGcode() {
  const blob = new Blob([gcodeResult.value], { type: 'text/plain' })
  // Trigger download
}
</script>

<template>
  <div class="adaptive-poly">
    <div class="left-panel">
      <!-- Mode toggle -->
      <!-- Polygon textarea -->
      <!-- Parameter inputs -->
      <!-- Generate button -->
    </div>
    <div class="right-panel">
      <!-- G-code textarea (readonly) -->
      <!-- Stats display -->
      <!-- Download button -->
    </div>
  </div>
</template>
```

🧩 3. Art Studio Integration (Phase B)

**Agent Analysis:**
- **Priority:** ⭐ LOW (Polish phase, after core labs)
- **Complexity:** 🟢 LOW (Component composition + routing)
- **Effort:** 1-2 hours
- **Dependencies:** BackplotGcode, AdaptiveBench, AdaptivePoly must be complete first

After the labs exist, integrate them into Art Studio:

A. Create CAM Hub View

ArtStudioCAM.vue should:

Import the 4 labs:

BackplotGcode.vue

AdaptiveBench.vue

AdaptivePoly.vue

HelicalRampLab.vue

Provide a tab/tile selector:

“Backplot”

“Adaptive Bench”

“Adaptive Poly”

“Helical Ramp”

Render selected Lab inside main panel.

B. Add CAM Card to Dashboard

In ArtStudioDashboard.vue, add:

A dashboard card labeled CAM Operations

Clicking it sends user to:
/art-studio/cam

C. Add Router Entry

In src/router/index.ts:

{
  path: '/art-studio/cam',
  component: ArtStudioCAM,
  meta: { title: 'Art Studio CAM Operations' }
}

🧠 4. Optional Phase C – Pipeline Integration

Once the Labs work:

✔ Backplot → Pipeline

BackplotGcode uses /cam/gcode/save_temp to generate a gcode_key.

PipelineLab already supports this through:

Query params

PipelineRunRequest gcode_key

_run_simulate_gcode (backend)

Result:
A G-code you explore in the lab can be re-run inside your full pipeline including:

Machine

Material

Helical

Review gates

Job Intelligence logging

✔ AdaptivePoly → Pipeline

N17/N18 endpoints can be treated as:

Experimental “pre-post” tools

Or dedicated polygon-only pipelines in the future.

🚀 5. Recommended Next Step in Sandbox

**Agent Strategic Recommendation:**

**Phase A begins now:** Build **N15 BackplotGcode.vue**

**Why N15 first:**
- ✅ **Simplest** - Just textarea + SVG display (3-4 hours)
- ✅ **Most immediately useful** - Debug any G-code visually
- ✅ **Plugs directly into:**
  - Your G-code sim engine
  - Your temp store (`/cam/gcode/save_temp`)
  - Your PipelineLab (via `gcode_key`)
- ✅ **Builds confidence** - Easy win before tackling N16/N17+N18

**Then proceed with:**
1. **N16** — AdaptiveBench.vue (4-5 hours)
2. **N17/N18** — AdaptivePoly.vue (4-5 hours)
3. **ArtStudioCAM** integration (1-2 hours)

**Total estimated time:** 12-16 hours for complete N15-N18 ecosystem

📁 6. File Structure to Follow

**Agent-Recommended File Structure:**

Example recommended frontend placement:

```
client/
  src/
    api/
      n15.ts                  # Backplot API calls
      n16.ts                  # Adaptive Benchmark API calls
      n17_n18.ts              # Polygon offset/spiral API calls

    components/
      toolbox/               # ⭐ Use this EXISTING directory
        BackplotGcode.vue       # N15 (NEW)
        AdaptiveBench.vue       # N16 (NEW)
        AdaptivePoly.vue        # N17+N18 (NEW)
        HelicalRampLab.vue      # v16.1 (EXISTING - YOUR REFERENCE)

    views/
      ArtStudioCAM.vue        # CAM hub view (NEW)
      ArtStudioDashboard.vue  # Update with CAM card (MODIFY)
      ArtStudioUnified.vue    # Existing Art Studio main view

    router/
      index.ts                # Add /art-studio/cam route (MODIFY)
```

**Agent Note - Directory Consistency:**
- ✅ `components/toolbox/` already exists with HelicalRampLab.vue
- ✅ Use same directory for new labs (maintain consistency)
- ✅ API modules in `api/` folder for clean separation
- ✅ Views in `views/` following existing naming pattern

✅ Conclusion

**Agent Summary:**

This annotated plan allows you to:

✅ **Complete N15–18 frontend Labs cleanly**
- 3 new Vue components (BackplotGcode, AdaptiveBench, AdaptivePoly)
- Following proven HelicalRampLab.vue pattern
- Estimated 12-16 hours total effort

✅ **Maintain consistency**
- Same directory structure (`components/toolbox/`)
- Same TypeScript + Composition API pattern
- Same two-column layout style
- Same API call error handling

✅ **Fit perfectly with current ecosystem**
- Integrates with CAM pipeline
- Works with Backplot system
- Complements Art Studio
- Uses existing routers (100% type-safe)

✅ **Layer in advanced features later**
- Phase C pipeline integration (optional)
- Dashboard enhancements
- Cross-lab workflows

**Build Order (Recommended):**
1. **N15 BackplotGcode.vue** - Start here (easiest, most useful)
2. **N16 AdaptiveBench.vue** - Medium complexity
3. **N17+N18 AdaptivePoly.vue** - Medium complexity
4. **ArtStudioCAM.vue** - Polish phase

**Success Criteria:**
- [ ] All 3 labs render without errors
- [ ] All backend APIs called correctly
- [ ] SVG/G-code displays work
- [ ] Download buttons function
- [ ] Stats displays show correct data
- [ ] Integration with ArtStudioCAM.vue complete
- [ ] Router entry added
- [ ] Dashboard card navigates correctly

**Ready for Code Dump Build Session!** 🚀

---

**Archival Notes:**
- Backend: 100% complete, type-safe, tested
- Frontend: 0% → Ready to build following this annotated plan
- Reference: HelicalRampLab.vue is your proven pattern template
- Timeline: 12-16 hours to close all N15-N18 frontend gaps
- Context: Post-98% type safety achievement, professional-grade foundation
- Date: November 16, 2025