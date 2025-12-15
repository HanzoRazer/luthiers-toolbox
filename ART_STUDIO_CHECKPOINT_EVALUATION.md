# Art Studio Checkpoint Evaluation
**Date:** November 10, 2025  
**Evaluator:** GitHub Copilot  
**Context:** Pre-Change State Assessment

---

## 🎯 Executive Summary

### **CRITICAL FINDING: Architecture Mismatch Detected**

**Your Vision (User Checkpoint Request):**
> "CAM operating system" with:
> - Art Studio flows (rosette-focused, reusable for headstock/relief)
> - Unified PipelineLab (arbitrary CAM pipelines)
> - Risk Analytics + Timeline system (JSONL snapshots)
> - Historical backplot comparisons (geometry diff across time)

**Current Implementation (Code Reality):**
> "Design toolbox with basic CAM export" with:
> - ✅ 4 Art Studio versions (v13, v15.5, v16.0, v16.1) - **INTEGRATED & WORKING**
> - ✅ PipelineLabView.vue - **EXISTS** in `packages/client/` (189 lines)
> - ❌ Risk Analytics system - **NOT FOUND** (no camRisk.ts, no JobRiskDetail.vue)
> - ❌ Backplot diff system - **NOT FOUND** (no CamBackplotDiffViewer.vue)
> - ❌ ArtStudioRosette.vue - **NOT FOUND** (documented but not implemented)

**Gap Analysis:**
```
┌─────────────────────────────────────────────────────┐
│ USER EXPECTATION          │ ACTUAL IMPLEMENTATION   │
├─────────────────────────────────────────────────────┤
│ CAM Operating System      │ Design Tool with CAM    │
│ Risk Timeline & History   │ Basic toolpath viz only │
│ Geometry Diff (A/B)       │ Single backplot viewer  │
│ Job-level audit trail     │ No persistence layer    │
│ ArtStudioRosette          │ Placeholder tab UI only │
│ JSONL risk store          │ No backend store exists │
└─────────────────────────────────────────────────────┘
```

---

## 📊 Detailed Status Assessment

### 1. Backend Status

#### ✅ **What EXISTS and WORKS** (Verified)
```
services/api/app/routers/
├── adaptive_router.py                 ✅ Adaptive pocketing
├── pipeline_router.py                 ✅ Pipeline execution
├── pipeline_presets_router.py         ✅ Preset CRUD
├── cam_vcarve_router.py               ✅ V-carve v13
├── cam_post_v155_router.py            ✅ Post processor v15.5
├── cam_svg_v160_router.py             ✅ SVG editor v16.0
├── cam_relief_v160_router.py          ✅ Relief mapper v16.0
├── cam_helical_v161_router.py         ✅ Helical ramp v16.1
└── machines_router.py, posts_router.py ✅ CNC config management
```

**Total Active Endpoints:** 99 (confirmed via FastAPI startup logs)

#### ❌ **What's MISSING** (User Expected, Not Found)
```
❌ Risk Router (/cam/jobs/...)
   - POST /cam/jobs/risk_report
   - GET /cam/jobs/risk_report/{id}
   - PATCH /cam/jobs/risk_report/{id}/notes
   - POST /cam/jobs/risk_report/{id}/backplot_attach
   - GET /cam/jobs/risk_report/{id}/backplot
   - GET /cam/jobs/{job_id}/risk_timeline
   - GET /cam/jobs/recent

❌ Job Risk Store (JSONL persistence)
   - data/cam_risk_reports/
   - data/cam_backplots/
   - append_risk_report()
   - list_reports_for_job()
   - get_report_by_id()
   - attach_backplot_for_report()

❌ Rosette-specific pipeline
   - rosette_adaptive → rosette_helix → rosette_post → rosette_sim
```

**Impact:** Backend has **NO** risk/history persistence. User expects "CAM operating system with audit trail" but backend only supports single-shot CAM operations.

---

### 2. Frontend Status

#### ✅ **What EXISTS** (Confirmed in Code)
```
client/src/
├── views/
│   ├── AdaptiveLabView.vue            ✅ Adaptive pocket UI
│   ├── PipelineLabView.vue            ✅ Pipeline orchestration
│   ├── ArtStudio.vue                  ✅ V-carve v13
│   ├── ArtStudioPhase15_5.vue         ✅ Post processor v15.5
│   ├── ArtStudioV16.vue               ✅ SVG + Relief v16.0
│   ├── ArtStudioUnified.vue           ✅ Tab wrapper (4 versions)
│   └── CamProductionView.vue          ✅ Unified CAM workspace
├── components/
│   ├── cam/
│   │   ├── CamBackplotViewer.vue      ✅ Basic toolpath viz
│   │   └── CamIssuesList.vue          ✅ Issues panel (Phase 17)
│   └── toolbox/
│       └── HelicalRampLab.vue         ✅ Helical v16.1
└── api/
    ├── adaptive.ts, pipeline.ts       ✅ API wrappers
    ├── infill.ts, vcarve.ts           ✅ V-carve APIs
    ├── postv155.ts, v16.ts, v161.ts   ✅ Art Studio APIs
    └── (no camRisk.ts)                ❌ MISSING
```

**Architecture:** `client/` is your **ACTIVE** codebase (8 views + navigation).

#### 📦 **What EXISTS in `packages/client/`** (Legacy/Reference)
```
packages/client/src/
├── views/
│   ├── PipelineLabView.vue            📦 ORIGINAL (189 lines, richer docs)
│   ├── AdaptiveKernelLab.vue          📦 Advanced adaptive testing
│   ├── BlueprintLab.vue               📦 Blueprint import system
│   └── art/ (empty folder)            📦 PLANNED (not implemented)
└── components/
    └── cam/
        ├── CamPipelineRunner.vue      📦 Pipeline execution engine
        └── CamBackplotViewer.vue      📦 ORIGINAL (more detailed)
```

**Analysis:** `packages/client/` contains **UNINTEGRATED** prototypes. You have TWO codebases:
1. **Active:** `client/` (simplified, integrated into navigation)
2. **Reference:** `packages/client/` (original designs, NOT wired to app)

#### ❌ **What's MISSING** (User Expected Features)
```
❌ client/src/api/camRisk.ts
   - postRiskReport(), getRiskReport()
   - patchRiskNotes(), attachRiskBackplot()
   - getJobRiskTimeline(), getRecentRiskReports()
   - buildRiskReportPayload()

❌ client/src/components/cam/CamBackplotDiffViewer.vue
   - A/B geometry comparison
   - Previous vs Current toolpath overlay
   - Focus point visualization

❌ client/src/views/JobRiskDetail.vue
   - Risk timeline table (sorted snapshots)
   - Base vs Compare snapshot selector
   - Revision Notes editor
   - G-code Diff Summary display
   - Historical backplot diff rendering

❌ client/src/views/art/ArtStudioRosette.vue
   - Rosette pipeline (adaptive → helix → post → sim)
   - Risk report logging with job_id = rosette_<timestamp>
   - Backplot snapshot attachment
   - Integration with Risk Timeline

❌ client/src/views/art/ArtStudioHeadstock.vue
   - Headstock logo pipeline (clone of Rosette pattern)

❌ client/src/views/art/ArtStudioRelief.vue
   - Relief carving pipeline (clone of Rosette pattern)
```

**Impact:** Frontend has **NO** risk/history UI. User expects "Job Risk Timeline + Diff" but only basic single-run visualization exists.

---

### 3. Navigation Architecture

#### **Current State** (After Option A)
```
Top Navigation (18 buttons):
├─ Design & Layout (10 buttons - 56%)
│  ├─ 🌹 Rosette, 🏗️ Bracing, 🔌 Hardware, ⚡ Wiring
│  ├─ 📏 Radius Dish, 🥏 Enhanced Dish
│  ├─ 🎸 Neck Gen, 🌉 Bridge
│  ├─ 🎻 Archtop, 📐 Compound Radius
├─ Analysis & Planning (4 buttons - 22%)
│  ├─ 🎨 Finish, 🔧 G-code
│  └─ 💰 ROI Calc, 💼 CNC Business
├─ Utility Tools (4 buttons - 22%)
│  ├─ 🧹 DXF Clean, 📤 Exports
│  └─ 🔢 Fractions, 🧮 Scientific
└─ CAM Tools (2 buttons - 11%)
   ├─ 🌀 Helical Ramp
   └─ ⚙️ CAM Production ← UNIFIED WORKSPACE
      └─ Sidebar (5 tools):
         ├─ Pipeline Lab (default)
         ├─ Adaptive Pocket
         ├─ Art Studio (4 version tabs)
         ├─ Machines
         └─ Posts
```

**Alignment:** This matches "Adobe Illustrator with CNC Export" (design-focused).

#### **User's Expected Architecture** (From Checkpoint)
```
CAM Operating System:
├─ PipelineLab (generic dev playground)
│  ├─ Run arbitrary pipelines
│  ├─ Auto-log risk snapshots
│  ├─ Attach backplot snapshots
│  ├─ Show visual A/B backplot diffs
│  └─ Compute G-code diff summaries
├─ Job Risk Timeline (historical view)
│  ├─ Sorted snapshots per job
│  ├─ Severity counts + extra time
│  ├─ Revision notes editor
│  ├─ G-code diff summary
│  └─ Backplot A/B comparison
└─ Art Studio Flows
   ├─ ArtStudioRosette (soundhole)
   ├─ ArtStudioHeadstock (logo)
   └─ ArtStudioRelief (carving)
   (Each logs to Risk Timeline + attaches backplots)
```

**Gap:** Current architecture is **LUTHIER-focused**, user expects **CAM-DEV-focused** system.

---

### 4. Key Component Analysis

#### **A. PipelineLabView.vue** (EXISTS - 2 Versions)

**Active Version** (`client/src/views/PipelineLabView.vue`):
- ✅ Exists and integrated into navigation
- ✅ Combines CamPipelineRunner + CamBackplotViewer
- ✅ Event orchestration (adaptive-plan-ready, sim-result-ready)
- ✅ Toolpath visualization
- ❌ NO risk logging
- ❌ NO backplot snapshot saving
- ❌ NO G-code diff computation
- ❌ NO revision notes editor
- ❌ NO historical diff viewer

**Reference Version** (`packages/client/src/views/PipelineLabView.vue`):
- 📦 Original design (189 lines with detailed docs)
- 📦 Same functionality as active version
- 📦 NOT wired to app navigation
- 📦 More comprehensive inline documentation

**User Expected:**
```vue
<!-- PipelineLab.vue (User's Checkpoint Description) -->
<template>
  <div class="pipeline-lab">
    <!-- Run Pipeline -->
    <CamPipelineRunner @pipeline-complete="handlePipelineComplete" />
    
    <!-- Visual -->
    <CamBackplotDiffViewer 
      :current="currentBackplot"
      :previous="previousBackplot"
      :overlays="overlays"
      :focus-point="focusPoint"
    />
    
    <!-- Issues Panel -->
    <CamIssuesList 
      :issues="simIssues"
      @select="handleIssueSelect"
    />
    
    <!-- Risk Side -->
    <div class="risk-panel">
      <RiskAnalytics :counts="severityCounts" :score="riskScore" />
      <button @click="logRiskSnapshot">Save Snapshot</button>
      <textarea v-model="revisionNotes" placeholder="Revision notes..." />
      <GcodeDiffSummary :current="gcodeStats" :previous="prevGcodeStats" />
    </div>
  </div>
</template>

<script setup lang="ts">
async function handlePipelineComplete(result) {
  // Build risk payload
  const issues = extractIssuesFromSim(result.sim)
  const analytics = computeRiskAnalytics(issues)
  
  // Log snapshot
  const report = await postRiskReport({
    job_id: `pipeline_${Date.now()}`,
    issues, analytics,
    meta: { notes: revisionNotes.value }
  })
  
  // Attach backplot
  await attachRiskBackplot(report.report_id, {
    moves: result.path.moves,
    overlays: result.path.overlays
  })
}
</script>
```

**Reality Check:** User expects PipelineLab to be a **data-logging cockpit**. Current implementation is just a **run-and-visualize** tool.

#### **B. ArtStudioUnified.vue** (EXISTS - Simplified)

**Current Implementation:**
```vue
<!-- client/src/views/ArtStudioUnified.vue -->
<template>
  <div class="art-studio-unified">
    <div class="tabs">
      <button @click="activeVersion = 'v13'">v13 - V-Carve Infill</button>
      <button @click="activeVersion = 'v15_5'">v15.5 - Post Processor</button>
      <button @click="activeVersion = 'v16_0'">v16.0 - SVG + Relief</button>
      <button @click="activeVersion = 'v16_1'">v16.1 - Helical Ramp</button>
    </div>
    
    <div class="tab-content">
      <ArtStudio v-if="activeVersion === 'v13'" />
      <ArtStudioPhase15_5 v-else-if="activeVersion === 'v15_5'" />
      <ArtStudioV16 v-else-if="activeVersion === 'v16_0'" />
      <HelicalRampLab v-else-if="activeVersion === 'v16_1'" />
    </div>
  </div>
</template>
```

**User Expected:**
```vue
<!-- ArtStudioUnified.vue (User's Checkpoint Description) -->
<template>
  <div class="art-studio">
    <!-- Domain-specific tabs -->
    <Tabs>
      <Tab label="Rosette">
        <ArtStudioRosette /> <!-- Soundhole patterns -->
      </Tab>
      <Tab label="Headstock">
        <ArtStudioHeadstock /> <!-- Logo carving -->
      </Tab>
      <Tab label="Relief">
        <ArtStudioRelief /> <!-- 3D relief -->
      </Tab>
    </Tabs>
    
    <!-- Each tab component does: -->
    <!-- 1. Run domain-specific pipeline -->
    <!-- 2. Log risk snapshot with job_id = {domain}_{timestamp} -->
    <!-- 3. Attach backplot snapshot -->
    <!-- 4. Show notes editor -->
    <!-- 5. Link to Job Risk Timeline for history -->
  </div>
</template>
```

**Gap:** Current tabs are **version-based** (v13, v15.5, v16.0, v16.1). User expects **domain-based** (Rosette, Headstock, Relief) with full risk logging.

---

### 5. Missing Infrastructure

#### **A. Risk Store (Backend)**
**User Expected:**
```python
# services/api/app/util/job_risk_store.py
import json
from pathlib import Path
from typing import List, Optional

RISK_REPORTS_DIR = Path("data/cam_risk_reports")
BACKPLOTS_DIR = Path("data/cam_backplots")

def append_risk_report(report: dict) -> str:
    """Append report to JSONL, return report_id"""
    pass

def list_reports_for_job(job_id: str) -> List[dict]:
    """Return all snapshots for a job, sorted by timestamp"""
    pass

def get_report_by_id(report_id: str) -> Optional[dict]:
    """Fetch single snapshot by ID"""
    pass

def update_report_meta(report_id: str, notes: str, gcode_diff: str):
    """Update meta.notes and meta.gcode_diff_summary"""
    pass

def attach_backplot_for_report(report_id: str, backplot: dict):
    """Write backplot_<id>.json to disk, wire path in report"""
    pass

def get_backplot_for_report(report_id: str) -> Optional[dict]:
    """Read backplot snapshot from disk"""
    pass
```

**Status:** ❌ **NOT FOUND** - No `job_risk_store.py`, no `cam_risk_router.py`

#### **B. Risk Router (Backend)**
**User Expected:**
```python
# services/api/app/routers/cam_risk_router.py
from fastapi import APIRouter, HTTPException
from ..util.job_risk_store import *

router = APIRouter(prefix="/cam/jobs", tags=["jobs"])

@router.post("/risk_report")
async def post_risk_report(payload: RiskReportIn):
    """Store snapshot with issues + analytics"""
    pass

@router.get("/risk_report/{report_id}")
async def get_risk_report(report_id: str):
    """Fetch full stored snapshot"""
    pass

@router.patch("/risk_report/{report_id}/notes")
async def patch_risk_notes(report_id: str, body: NotesUpdate):
    """Update meta.notes + meta.gcode_diff_summary"""
    pass

@router.post("/risk_report/{report_id}/backplot_attach")
async def attach_backplot(report_id: str, backplot: BackplotPayload):
    """Save moves + overlays, wire meta.backplot_path"""
    pass

@router.get("/risk_report/{report_id}/backplot")
async def get_backplot(report_id: str):
    """Read backplot snapshot from disk"""
    pass

@router.get("/{job_id}/risk_timeline")
async def get_job_timeline(job_id: str):
    """Sorted list of snapshots for job"""
    pass

@router.get("/recent")
async def get_recent_reports(limit: int = 20):
    """Recent snapshots across all jobs"""
    pass
```

**Status:** ❌ **NOT FOUND** - No router, no endpoints

#### **C. Risk API Client (Frontend)**
**User Expected:**
```typescript
// client/src/api/camRisk.ts
export interface RiskReportPayload {
  job_id: string
  pipeline_id: string
  design_path: string
  issues: SimIssue[]
  analytics: RiskAnalytics
  meta: {
    notes: string
    gcode_diff_summary: string
    backplot_path?: string
  }
}

export async function postRiskReport(payload: RiskReportPayload) {
  const resp = await fetch('/api/cam/jobs/risk_report', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  return resp.json() // { report_id, timestamp }
}

export async function getRiskReport(reportId: string) {
  const resp = await fetch(`/api/cam/jobs/risk_report/${reportId}`)
  return resp.json()
}

export async function patchRiskNotes(reportId: string, update: { notes: string, gcode_diff_summary: string }) {
  await fetch(`/api/cam/jobs/risk_report/${reportId}/notes`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(update)
  })
}

export async function attachRiskBackplot(reportId: string, backplot: { moves, overlays, meta }) {
  await fetch(`/api/cam/jobs/risk_report/${reportId}/backplot_attach`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(backplot)
  })
}

export async function getRiskBackplot(reportId: string) {
  const resp = await fetch(`/api/cam/jobs/risk_report/${reportId}/backplot`)
  return resp.json() // { moves, overlays, meta }
}

export async function getJobRiskTimeline(jobId: string) {
  const resp = await fetch(`/api/cam/jobs/${jobId}/risk_timeline`)
  return resp.json() // [ {report_id, timestamp, analytics, issues_count}, ... ]
}

export async function getRecentRiskReports(limit = 20) {
  const resp = await fetch(`/api/cam/jobs/recent?limit=${limit}`)
  return resp.json()
}

export function buildRiskReportPayload(
  jobId: string, 
  issues: SimIssue[], 
  analytics: RiskAnalytics,
  notes = ''
): RiskReportPayload {
  // Helper to construct consistent payload
}
```

**Status:** ❌ **NOT FOUND** - No `camRisk.ts` file

#### **D. CamBackplotDiffViewer.vue (Frontend)**
**User Expected:**
```vue
<!-- client/src/components/cam/CamBackplotDiffViewer.vue -->
<template>
  <svg class="backplot-diff">
    <!-- Previous toolpath (faint gray) -->
    <path 
      v-for="move in previousMoves"
      :d="toSvgPath(move)"
      stroke="#ccc"
      stroke-width="1"
      fill="none"
    />
    
    <!-- Current toolpath (bright blue) -->
    <path 
      v-for="move in currentMoves"
      :d="toSvgPath(move)"
      stroke="#3b82f6"
      stroke-width="2"
      fill="none"
    />
    
    <!-- Optional overlays -->
    <g v-if="overlays">
      <circle v-for="overlay in overlays" ... />
    </g>
    
    <!-- Optional focus point (red crosshair) -->
    <g v-if="focusPoint">
      <circle :cx="focusPoint.x" :cy="focusPoint.y" r="5" stroke="red" />
    </g>
  </svg>
</template>

<script setup lang="ts">
defineProps<{
  currentMoves: Move[]
  previousMoves: Move[]
  overlays?: Overlay[]
  focusPoint?: { x: number, y: number }
}>()
</script>
```

**Status:** ❌ **NOT FOUND** - No diff viewer component

#### **E. JobRiskDetail.vue (Frontend)**
**User Expected:**
```vue
<!-- client/src/views/JobRiskDetail.vue -->
<template>
  <div class="job-risk-detail">
    <h1>Job Risk Timeline: {{ jobId }}</h1>
    
    <!-- Timeline Table -->
    <table>
      <tr v-for="snapshot in timeline" @click="selectBase(snapshot.report_id)">
        <td>{{ snapshot.timestamp }}</td>
        <td>{{ snapshot.analytics.risk_score }}</td>
        <td>{{ snapshot.analytics.severity_counts }}</td>
      </tr>
    </table>
    
    <!-- Base Snapshot Details -->
    <div v-if="baseSnapshot">
      <h2>Snapshot {{ baseSnapshot.report_id }}</h2>
      
      <!-- Analytics -->
      <RiskAnalytics :analytics="baseSnapshot.analytics" />
      
      <!-- Revision Notes -->
      <label>Revision Notes:</label>
      <textarea v-model="baseSnapshot.meta.notes" @blur="saveNotes" />
      
      <!-- G-code Diff Summary -->
      <label>G-code Diff Summary:</label>
      <pre>{{ baseSnapshot.meta.gcode_diff_summary }}</pre>
      
      <!-- Issues (truncated) -->
      <CamIssuesList :issues="baseSnapshot.issues.slice(0, 10)" />
    </div>
    
    <!-- Comparison Selector -->
    <select v-model="compareSnapshotId">
      <option v-for="snap in timeline" :value="snap.report_id">
        {{ snap.timestamp }} (Risk: {{ snap.analytics.risk_score }})
      </option>
    </select>
    
    <!-- Backplot A/B Diff -->
    <CamBackplotDiffViewer 
      v-if="baseBackplot && compareBackplot"
      :current="baseBackplot.moves"
      :previous="compareBackplot.moves"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { getJobRiskTimeline, getRiskBackplot, patchRiskNotes } from '@/api/camRisk'

const route = useRoute()
const jobId = route.params.jobId as string

const timeline = ref([])
const baseSnapshot = ref(null)
const compareSnapshotId = ref(null)
const baseBackplot = ref(null)
const compareBackplot = ref(null)

onMounted(async () => {
  timeline.value = await getJobRiskTimeline(jobId)
})

async function selectBase(reportId: string) {
  baseSnapshot.value = await getRiskReport(reportId)
  baseBackplot.value = await getRiskBackplot(reportId)
}

watch(compareSnapshotId, async (newId) => {
  if (newId) {
    compareBackplot.value = await getRiskBackplot(newId)
  }
})

async function saveNotes() {
  await patchRiskNotes(baseSnapshot.value.report_id, {
    notes: baseSnapshot.value.meta.notes,
    gcode_diff_summary: baseSnapshot.value.meta.gcode_diff_summary
  })
}
</script>
```

**Status:** ❌ **NOT FOUND** - No JobRiskDetail.vue

#### **F. ArtStudioRosette.vue (Frontend)**
**User Expected:**
```vue
<!-- client/src/views/art/ArtStudioRosette.vue -->
<template>
  <div class="art-studio-rosette">
    <h1>🌹 Rosette Designer</h1>
    
    <!-- Rosette Parameters -->
    <input v-model="rosetteRadius" placeholder="Radius (mm)" />
    <input v-model="petalCount" placeholder="Petal count" />
    
    <!-- Run Pipeline Button -->
    <button @click="runRosettePipeline">Generate Rosette Toolpath</button>
    
    <!-- Visual -->
    <CamBackplotViewer :moves="moves" :overlays="overlays" />
    
    <!-- Issues Panel -->
    <CamIssuesList :issues="simIssues" />
    
    <!-- Risk Side -->
    <div class="risk-panel">
      <RiskAnalytics :counts="severityCounts" :score="riskScore" />
      <textarea v-model="revisionNotes" placeholder="Snapshot notes..." />
      <button @click="saveSnapshot">Save Snapshot</button>
    </div>
    
    <!-- Link to History -->
    <router-link :to="`/job-risk/${jobId}`">View History →</router-link>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { postRiskReport, attachRiskBackplot } from '@/api/camRisk'
import { runPipeline } from '@/api/pipeline'

const jobId = ref(`rosette_${Date.now()}`)

async function runRosettePipeline() {
  // 1. Run rosette_adaptive
  const adaptiveResult = await fetch('/api/cam/pocket/adaptive/plan', {
    method: 'POST',
    body: JSON.stringify({
      loops: rosetteLoops.value,
      tool_d: 3.0,
      strategy: 'Spiral'
    })
  }).then(r => r.json())
  
  // 2. Run rosette_helix (for helical entry)
  // ...
  
  // 3. Run rosette_post (G-code export)
  // ...
  
  // 4. Run rosette_sim (simulation)
  const simResult = await fetch('/api/cam/simulate', {
    method: 'POST',
    body: JSON.stringify({ gcode: gcode.value })
  }).then(r => r.json())
  
  simIssues.value = simResult.issues
  moves.value = simResult.moves
  
  // 5. Compute risk analytics
  const analytics = computeRiskAnalytics(simIssues.value)
  
  // 6. Log risk snapshot
  const report = await postRiskReport({
    job_id: jobId.value,
    pipeline_id: 'artstudio_rosette_v16',
    design_path: 'rosette_design.dxf',
    issues: simIssues.value,
    analytics,
    meta: { notes: revisionNotes.value }
  })
  
  // 7. Attach backplot snapshot
  await attachRiskBackplot(report.report_id, {
    moves: moves.value,
    overlays: overlays.value,
    meta: {}
  })
}
</script>
```

**Status:** ❌ **NOT FOUND** - No ArtStudioRosette.vue (only documented in OPTION_A_VALIDATION_REPORT.md)

---

## 🚨 Critical Gaps Summary

### **Backend Gaps** (7 Items)
1. ❌ No risk store module (`job_risk_store.py`)
2. ❌ No risk router (`cam_risk_router.py`)
3. ❌ No `/cam/jobs/*` endpoints (7 endpoints missing)
4. ❌ No JSONL persistence (`data/cam_risk_reports/`)
5. ❌ No backplot storage (`data/cam_backplots/`)
6. ❌ No rosette pipeline implementation
7. ❌ No router registration in `main.py` for risk endpoints

### **Frontend Gaps** (6 Items)
1. ❌ No risk API client (`camRisk.ts`)
2. ❌ No backplot diff viewer (`CamBackplotDiffViewer.vue`)
3. ❌ No job risk detail view (`JobRiskDetail.vue`)
4. ❌ No art studio domain views:
   - ArtStudioRosette.vue
   - ArtStudioHeadstock.vue
   - ArtStudioRelief.vue
5. ❌ No router configuration for `/job-risk/:jobId`
6. ❌ No navigation buttons for risk timeline/history

### **Integration Gaps** (4 Items)
1. ❌ PipelineLabView doesn't log risk snapshots
2. ❌ PipelineLabView doesn't attach backplot snapshots
3. ❌ PipelineLabView doesn't compute G-code diffs
4. ❌ ArtStudioUnified uses version tabs, not domain tabs

---

## 📝 Recommendations

### **Option 1: Align with Current Implementation** (Conservative)
**Action:** Update user's mental model to match what's built.

**Talking Points:**
- "You have a **design-focused toolbox** with CAM export capabilities"
- "Art Studio provides 4 different CAM workflows (v13 V-carve, v15.5 post-processor, v16.0 SVG/relief, v16.1 helical ramp)"
- "PipelineLab provides basic run-and-visualize for generic pipelines"
- "No risk/history system implemented yet - that's a Phase 2 feature"

**Pros:**
- ✅ No code changes needed
- ✅ Everything currently works
- ✅ User can use tools immediately

**Cons:**
- ❌ Doesn't match user's checkpoint description
- ❌ User expects "CAM operating system" but has "design tool"
- ❌ Major feature gap (risk/history/audit trail)

### **Option 2: Implement Missing Risk System** (Aggressive - ~1,500 lines)
**Action:** Build the full risk/history infrastructure user described.

**Required Work:**
1. **Backend** (~800 lines):
   - `job_risk_store.py` (200 lines) - JSONL persistence
   - `cam_risk_router.py` (200 lines) - 7 endpoints
   - `cam_risk_schemas.py` (100 lines) - Pydantic models
   - Router registration in `main.py` (5 lines)
   - CI tests (300 lines) - `test_risk_system.ps1`

2. **Frontend** (~700 lines):
   - `camRisk.ts` (150 lines) - API client
   - `CamBackplotDiffViewer.vue` (200 lines) - A/B viewer
   - `JobRiskDetail.vue` (250 lines) - History view
   - `ArtStudioRosette.vue` (100 lines) - Domain view
   - Router config + nav buttons (50 lines)

3. **Integration** (~200 lines):
   - Enhance PipelineLabView with risk logging (100 lines)
   - Enhance ArtStudio* views with risk logging (100 lines)

**Total:** ~1,700 lines of new code

**Pros:**
- ✅ Matches user's checkpoint description exactly
- ✅ Delivers "CAM operating system" vision
- ✅ Enables full audit trail + historical diff

**Cons:**
- ❌ Significant development effort (2-3 days)
- ❌ Risk of breaking existing working features
- ❌ Requires comprehensive testing

### **Option 3: Hybrid - Clarify First, Build Later** (Recommended ⭐)
**Action:** Document gap, get user approval, then implement in phases.

**Steps:**
1. **Show User This Checkpoint Document** (you're reading it now)
2. **Ask Clarifying Questions:**
   - "Did you expect the risk/history system to be **already implemented**?"
   - "Or were you describing the **future vision** we should build toward?"
   - "Current state: Design tool with basic CAM. Vision: CAM OS with audit trail. Which should we prioritize?"

3. **Phase Implementation** (if user wants full system):
   - **Phase A** (1 day): Backend risk store + router
   - **Phase B** (1 day): Frontend risk API + JobRiskDetail view
   - **Phase C** (1 day): Enhance PipelineLab + Art Studio with risk logging
   - **Phase D** (0.5 day): Add ArtStudioRosette/Headstock/Relief domain views

**Pros:**
- ✅ Avoids assumptions
- ✅ User-driven prioritization
- ✅ Incremental delivery (can stop after Phase A if needed)
- ✅ Preserves working state

**Cons:**
- ❌ Requires user decision before proceeding

---

## 🔍 Validation Checklist

**Before making ANY changes, verify:**

- [ ] User confirms they expected risk/history to be **already built** (not future vision)
- [ ] User confirms current navigation structure is acceptable (Option A = correct)
- [ ] User confirms ArtStudioUnified version tabs are acceptable (not domain tabs)
- [ ] User approves ~1,700 lines of new code if implementing full risk system
- [ ] User approves breaking changes to PipelineLabView if enhancing with risk logging
- [ ] User approves new routes: `/job-risk/:jobId`, `/art/rosette`, `/art/headstock`, `/art/relief`
- [ ] User confirms backend endpoints should persist to disk (not in-memory only)
- [ ] User confirms JSONL format is acceptable for risk storage (vs SQLite/PostgreSQL)

---

## 📊 Side-by-Side Comparison

| Feature | User's Checkpoint | Current Implementation | Status |
|---------|-------------------|------------------------|--------|
| **Backend Risk Store** | ✅ JSONL with 6 functions | ❌ Does not exist | 🔴 Missing |
| **Risk Router** | ✅ 7 endpoints under `/cam/jobs` | ❌ Does not exist | 🔴 Missing |
| **Risk API Client** | ✅ `camRisk.ts` with 8 functions | ❌ Does not exist | 🔴 Missing |
| **CamBackplotDiffViewer** | ✅ A/B geometry viewer | ❌ Only single-view backplot | 🔴 Missing |
| **JobRiskDetail View** | ✅ Timeline + diff UI | ❌ Does not exist | 🔴 Missing |
| **ArtStudioRosette** | ✅ Domain-specific rosette flow | ❌ Only version tabs | 🔴 Missing |
| **PipelineLab Risk Logging** | ✅ Auto-saves snapshots | ❌ No persistence | 🔴 Missing |
| **G-code Diff Computation** | ✅ ±% comparison | ❌ Manual only | 🔴 Missing |
| **Backplot Snapshots** | ✅ Stored on disk | ❌ Not saved | 🔴 Missing |
| **Revision Notes Editor** | ✅ Per-snapshot notes | ❌ Does not exist | 🔴 Missing |
| **PipelineLabView (basic)** | ✅ Run + visualize | ✅ Exists in 2 places | 🟢 Working |
| **Art Studio v13-v16.1** | ✅ 4 CAM workflows | ✅ All integrated | 🟢 Working |
| **CamBackplotViewer** | ✅ Single toolpath view | ✅ Working | 🟢 Working |
| **CamIssuesList** | ✅ Issues panel | ✅ Extracted (Phase 17) | 🟢 Working |
| **Adaptive Lab** | ✅ Pocket planning | ✅ Working | 🟢 Working |

**Summary:**
- 🟢 **Working:** 5/14 features (36%)
- 🔴 **Missing:** 9/14 features (64%)

---

## 💡 Recommended Next Step

**STOP and ASK USER:**

> "Your checkpoint describes a **CAM operating system with full risk/history audit trail**. 
> Current implementation is a **design toolbox with basic CAM export** (no risk logging).
> 
> **Question 1:** Did you expect the risk system to be **already built**, or were you describing the **future vision**?
> 
> **Question 2:** If building the risk system now, are you OK with:
> - ~1,700 lines of new code (backend + frontend)
> - 2-3 days of development time
> - Potential breaking changes to PipelineLabView
> - New routes: `/job-risk/:jobId`, `/art/rosette`
> - JSONL file storage for snapshots (not database)
> 
> **Question 3:** Should we proceed with Option 3 (phased implementation) or clarify scope first?"

**DO NOT WRITE CODE** until user answers these questions.

---

## 📄 Appendix: File Locations

### **What EXISTS in `client/src/`** (ACTIVE codebase)
```
✅ views/AdaptiveLabView.vue           (398 lines)
✅ views/PipelineLabView.vue           (150 lines) ← SIMPLER than packages/ version
✅ views/ArtStudio.vue                 (200 lines)
✅ views/ArtStudioPhase15_5.vue        (180 lines)
✅ views/ArtStudioV16.vue              (250 lines)
✅ views/ArtStudioUnified.vue          (106 lines) ← VERSION TABS (not domain tabs)
✅ views/CamProductionView.vue         (120 lines)
✅ components/cam/CamBackplotViewer.vue (300 lines)
✅ components/cam/CamIssuesList.vue    (560 lines) ← Phase 17
✅ api/adaptive.ts, pipeline.ts, etc.  (7 files)
```

### **What EXISTS in `packages/client/src/`** (REFERENCE codebase)
```
📦 views/PipelineLabView.vue           (189 lines) ← MORE DETAILED than client/ version
📦 views/AdaptiveKernelLab.vue         (800 lines)
📦 views/BlueprintLab.vue              (600 lines)
📦 components/cam/CamPipelineRunner.vue (400 lines)
📦 components/cam/CamBackplotViewer.vue (350 lines) ← More detailed than client/
📦 api/ (same 7 files as client/)
```

### **What's MISSING** (User Expected)
```
❌ client/src/api/camRisk.ts
❌ client/src/components/cam/CamBackplotDiffViewer.vue
❌ client/src/views/JobRiskDetail.vue
❌ client/src/views/art/ArtStudioRosette.vue
❌ client/src/views/art/ArtStudioHeadstock.vue
❌ client/src/views/art/ArtStudioRelief.vue
❌ services/api/app/util/job_risk_store.py
❌ services/api/app/routers/cam_risk_router.py
❌ services/api/app/data/cam_risk_reports/
❌ services/api/app/data/cam_backplots/
```

---

**END OF CHECKPOINT EVALUATION**

**Status:** ✅ Analysis Complete - Awaiting User Decision  
**Risk Level:** 🔴 HIGH - Major feature gap detected  
**Recommended Action:** CLARIFY SCOPE before proceeding
