<!--
================================================================================
CAM Pipeline Graph Component
================================================================================

PURPOSE:
--------
Visual representation of pipeline execution state. Displays operation sequence
as circular nodes connected by lines, with color-coded status indicators.
Provides at-a-glance understanding of which stages completed successfully.

KEY ALGORITHMS:
--------------
1. Status Classification:
   - Green (emerald-500): Operation completed successfully (ok=true, no error)
   - Red (rose-500): Operation failed (ok=false or error present)
   - Gray: Operation pending/not run (default state)

2. Label Abbreviation:
   - dxf_preflight → PRE (preflight validation)
   - adaptive_plan → PLAN (loop extraction from DXF)
   - adaptive_plan_run → RUN (toolpath generation)
   - export_post → POST (post-processor wrapping)
   - simulate_gcode → SIM (motion simulation)

3. Layout Algorithm:
   - Horizontal flex layout with gap-3 spacing
   - Circular nodes (8×8, rounded-full) with abbreviated labels
   - Connecting lines (6px width) between adjacent nodes
   - Last node has no trailing line (v-if="idx < ops.length - 1")

SAFETY RULES:
------------
1. Null-safe: results prop can be null (uses computed default [])
2. Defensive rendering: v-for handles empty arrays gracefully
3. Type-safe: PipelineOpKind enum ensures valid operation types
4. CSS isolation: scoped styles prevent conflicts

INTEGRATION POINTS:
------------------
**Parent Components:**
- CamPipelineRunner.vue - Passes :results prop after pipeline execution

**Props:**
- results: PipelineOpResult[] | null - Array of operation results from pipeline

**Data Flow:**
CamPipelineRunner.vue → runPipeline() → fetch /cam/pipeline/run → 
data.ops → :results prop → CamPipelineGraph displays status

DEPENDENCIES:
------------
- Vue 3 Composition API (computed, defineProps)
- Tailwind CSS (bg-emerald-500, bg-rose-500, rounded-full, flex, gap-3)

UI STRUCTURE:
------------
┌─ Pipeline Graph ────────────────────────┐
│ 5 stage(s)                              │
│                                          │
│ ●PRE━━●PLAN━━●RUN━━●POST━━●SIM          │
│ (colored nodes + lines)                  │
│                                          │
│ Legend:                                  │
│ 🟢 OK  🔴 Failed  ⚪ Pending             │
└──────────────────────────────────────────┘

USAGE EXAMPLE:
-------------
<CamPipelineGraph :results="pipelineResults" />

Where pipelineResults is:
[
  { kind: 'dxf_preflight', ok: true, error: null, payload: {...} },
  { kind: 'adaptive_plan', ok: true, error: null, payload: {...} },
  { kind: 'adaptive_plan_run', ok: false, error: 'Timeout', payload: null }
]

Result: PRE (green), PLAN (green), RUN (red), POST (gray), SIM (gray)

FUTURE ENHANCEMENTS:
-------------------
- Click node to jump to corresponding op card in CamPipelineRunner
- Hover tooltips with op kind full name + error message
- Animated transitions (gray → green on success)
- Time badges on each node (time_s from payload)
- Vertical layout option for mobile
================================================================================
-->

<template>
  <div class="p-3 border rounded-lg space-y-2 bg-white">
    <div class="flex items-center justify-between">
      <h4 class="text-xs font-semibold text-gray-700">
        Pipeline Graph
      </h4>
      <span class="text-[10px] text-gray-500">
        {{ ops.length }} stage(s)
      </span>
    </div>

    <div class="flex items-center flex-wrap gap-3">
      <div
        v-for="(op, idx) in ops"
        :key="idx"
        class="flex items-center"
      >
        <div
          class="w-8 h-8 rounded-full flex items-center justify-center text-[9px] font-mono border"
          :class="nodeClass(op)"
        >
          {{ shortLabel(op.kind) }}
        </div>
        <div
          v-if="idx < ops.length - 1"
          class="w-6 h-px bg-gray-300 mx-1"
        />
      </div>
    </div>

    <div class="flex flex-wrap gap-3 text-[10px] text-gray-600">
      <div class="flex items-center gap-1">
        <span class="w-3 h-3 rounded-full bg-emerald-500"></span>
        <span>OK</span>
      </div>
      <div class="flex items-center gap-1">
        <span class="w-3 h-3 rounded-full bg-rose-500"></span>
        <span>Failed</span>
      </div>
      <div class="flex items-center gap-1">
        <span class="w-3 h-3 rounded-full bg-gray-300 border border-gray-400"></span>
        <span>Pending/Not run</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

type PipelineOpKind =
  | 'dxf_preflight'
  | 'adaptive_plan'
  | 'adaptive_plan_run'
  | 'export_post'
  | 'simulate_gcode'

interface PipelineOpResult {
  kind: PipelineOpKind
  ok: boolean
  error?: string | null
  payload?: any
}

const props = defineProps<{
  results: PipelineOpResult[] | null
}>()

const ops = computed(() => props.results ?? [])

function shortLabel (kind: PipelineOpKind): string {
  switch (kind) {
    case 'dxf_preflight': return 'PRE'
    case 'adaptive_plan': return 'PLAN'
    case 'adaptive_plan_run': return 'RUN'
    case 'export_post': return 'POST'
    case 'simulate_gcode': return 'SIM'
    default: return 'OP'
  }
}

function nodeClass (op: PipelineOpResult) {
  if (op.ok && !op.error) {
    return 'bg-emerald-500 text-white border-transparent'
  }
  if (!op.ok || op.error) {
    return 'bg-rose-500 text-white border-transparent'
  }
  return 'bg-gray-100 text-gray-700 border-gray-400'
}
</script>
