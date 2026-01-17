<!--
================================================================================
Pipeline Lab View
================================================================================

PURPOSE:
--------
Full-screen view combining CamPipelineRunner and CamBackplotViewer for 
end-to-end CAM workflow. Orchestrates event flow between pipeline execution
(runner) and toolpath visualization (backplot). Primary user interface for
DXF → Preflight → Adaptive Planning → Post Export → Simulation workflow.

KEY ALGORITHMS:
--------------
1. Event Orchestration:
   CamPipelineRunner emits 'adaptive-plan-ready' → onAdaptivePlanReady() stores
   moves/stats/overlays → plotMoves computed updates → CamBackplotViewer renders

2. Progressive Enhancement:
   - Initial state: adaptiveMoves empty, backplot shows "Upload DXF to begin"
   - After adaptive_plan_run: adaptiveMoves populated, backplot shows toolpath
   - After simulate_gcode: simMoves populated, backplot switches to sim result
   - Computed plotMoves prefers sim over adaptive (sim takes precedence)

3. State Management:
   - Separate storage for adaptive result vs sim result
   - adaptiveMoves/Stats/Overlays: From 'adaptive-plan-ready' event
   - simMoves/Stats/Issues: From 'sim-result-ready' event
   - Computed plotMoves: simMoves.length ? simMoves : adaptiveMoves
   - Computed plotStats: simStats || adaptiveStats (sim takes precedence)

SAFETY RULES:
------------
1. Null-safe defaults: overlays ?? [], issues ?? [], moves ?? []
2. Defensive computed: simStats || adaptiveStats handles null
3. Event payload validation: Check existence before accessing properties
4. Empty state handling: CamBackplotViewer displays message when moves=[]

INTEGRATION POINTS:
------------------
**Child Components:**
- CamPipelineRunner.vue - Emits @adaptive-plan-ready, @sim-result-ready
- CamBackplotViewer.vue - Accepts :moves, :stats, :overlays, :sim-issues

**Route:**
- Path: /lab/pipeline
- Name: PipelineLab
- Lazy load: () => import('@/views/PipelineLabView.vue')

**Backend APIs (via CamPipelineRunner):**
- POST /cam/pipeline/run (5-operation execution)
- GET /cam/pipeline/presets (load saved configs)
- POST /cam/pipeline/presets (save new configs)
- GET /cam/machines/{id} (fetch machine profiles)
- GET /cam/posts/{id} (fetch post profiles)

**Event Flow:**
User uploads DXF in CamPipelineRunner → 
clicks "Run Pipeline" → 
POST /cam/pipeline/run → 
adaptive_plan_run completes → 
@adaptive-plan-ready emits {moves, stats, overlays} → 
onAdaptivePlanReady stores data → 
plotMoves computed updates → 
CamBackplotViewer re-renders with toolpath + overlays →
simulate_gcode completes → 
@sim-result-ready emits {issues, moves, summary} → 
onSimResultReady stores data → 
plotMoves switches to simMoves → 
CamBackplotViewer re-renders with severity coloring

DEPENDENCIES:
------------
- Vue 3 Composition API (ref, computed)
- CamPipelineRunner.vue (pipeline execution UI)
- CamBackplotViewer.vue (canvas toolpath visualization)
- Vue Router (registered route /lab/pipeline)

UI STRUCTURE:
------------
┌─ Pipeline Lab (/lab/pipeline) ─────────────────────────┐
│ DXF → Preflight → Plan → Run → Export → Simulate       │
├─────────────────────────────────────────────────────────┤
│ CamPipelineRunner                                       │
│ ┌─ Upload DXF ────────────────────────────────────────┐│
│ │ [Choose File] tool⌀ units machine post [Run]        ││
│ │ [Presets] [Inspector] [Results]                      ││
│ └──────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────┤
│ CamBackplotViewer                                       │
│ ┌─ Toolpath Preview ──────────────────────────────────┐│
│ │ Canvas (800×600)                                     ││
│ │ - Adaptive toolpath (blue lines + overlays)          ││
│ │ - Sim issues (severity colors: red/yellow/gray)      ││
│ │ Stats: length, time, volume                          ││
│ └──────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘

TYPICAL WORKFLOW:
----------------
1. User navigates to /lab/pipeline route
2. User uploads DXF file in CamPipelineRunner
3. User selects tool diameter, units, machine ID, post ID
4. (Optional) User loads preset config
5. User clicks "Run Pipeline" button
6. CamPipelineRunner executes 5 operations:
   a. dxf_preflight: Validate DXF, extract layers
   b. adaptive_plan: Extract boundary loops from DXF
   c. adaptive_plan_run: Generate adaptive toolpath
   d. export_post: Wrap G-code with post-processor headers
   e. simulate_gcode: Run motion simulation
7. After adaptive_plan_run completes:
   - @adaptive-plan-ready event fires
   - adaptiveMoves/Stats/Overlays updated
   - CamBackplotViewer renders toolpath with overlays
8. After simulate_gcode completes:
   - @sim-result-ready event fires
   - simMoves/Stats/Issues updated
   - CamBackplotViewer switches to sim visualization
   - Severity coloring applied (red=error, yellow=warning, gray=info)

FUTURE ENHANCEMENTS:
-------------------
- Split view: Adaptive toolpath (left) + Sim result (right)
- Diff view: Highlight differences between adaptive and sim paths
- Export button: Download G-code directly from view
- Permalink: Share pipeline config via URL query params
- History: Store recent runs in localStorage
- Comparison mode: Compare multiple presets side-by-side
================================================================================
-->

<template>
  <div class="p-4 space-y-4">
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-sm font-semibold">Pipeline Lab</h2>
        <p class="text-[11px] text-gray-500">
          DXF → Preflight → Plan → Run → Export → Simulate
        </p>
      </div>
      <span class="text-[10px] text-gray-400">/lab/pipeline</span>
    </div>

    <CamPipelineRunner
      @adaptive-plan-ready="onAdaptivePlanReady"
      @sim-result-ready="onSimResultReady"
    />

    <CamBackplotViewer
      :loops="[]"
      :moves="plotMoves"
      :stats="plotStats"
      :overlays="adaptiveOverlays"
      :sim-issues="simIssues"
    />

    <!-- CAM Backup Panel (N18 System 2) -->
    <CamBackupPanel />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import CamPipelineRunner from '@/components/cam/CamPipelineRunner.vue'
import CamBackplotViewer from '@/components/cam/CamBackplotViewer.vue'
import CamBackupPanel from '@/components/CamBackupPanel.vue'

const adaptiveMoves = ref<any[]>([])
const adaptiveStats = ref<any | null>(null)
const adaptiveOverlays = ref<any[] | null>(null)

const simMoves = ref<any[]>([])
const simStats = ref<any | null>(null)
const simIssues = ref<any[] | null>(null)

function onAdaptivePlanReady (payload: { moves: any[]; stats: any; overlays?: any[] }) {
  adaptiveMoves.value = payload.moves
  adaptiveStats.value = payload.stats
  adaptiveOverlays.value = payload.overlays ?? []
}

function onSimResultReady (payload: { issues: any[]; moves: any[]; summary: any }) {
  simIssues.value = payload.issues ?? []
  simMoves.value = payload.moves ?? []
  simStats.value = payload.summary ?? null
}

const plotMoves = computed(() =>
  simMoves.value.length ? simMoves.value : adaptiveMoves.value
)
const plotStats = computed(() => simStats.value || adaptiveStats.value)
</script>
