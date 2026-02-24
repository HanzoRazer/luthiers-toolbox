<!--
================================================================================
CAM Pipeline Runner Component
================================================================================

PURPOSE:
--------
Main UI component for executing end-to-end CAM pipelines from DXF upload through
toolpath generation, post-processing, and G-code simulation. Provides preset
management, machine/post profile selection, and real-time operation tracking.

KEY ALGORITHMS:
--------------
1. Pipeline Specification Building:
   - Constructs operation sequence: dxf_preflight → adaptive_plan → adaptive_plan_run → export_post → simulate_gcode
   - Injects per-operation parameters (profile, layer prefix, endpoints, post/machine IDs)
   - Supports auto-scaling and unit conversion

2. Event Emission System:
   - adaptive-plan-ready: Fires after adaptive_plan_run with moves, stats, overlays
   - sim-result-ready: Fires after simulate_gcode with issues, moves, summary
   - Enables parent components to react to pipeline stages (e.g., update backplot)

3. Preset Management:
   - Load presets from /cam/pipeline/presets on mount
   - Apply preset: updates units, machine_id, post_id from saved config
   - Save preset: validates name uniqueness, persists to backend
   - LocalStorage sync for selected preset ID (optional enhancement)

4. Inspector System:
   - Fetches machine profile from /cam/machines/{id} on change
   - Fetches post profile from /cam/posts/{id} on change
   - Displays key parameters (feed rates, accel, jerk, safe Z, dialect)
   - Helps users verify configuration before pipeline run

SAFETY RULES:
------------
1. File validation: Only .dxf files accepted via accept attribute
2. Button disabled during loading to prevent duplicate runs
3. Error handling: All fetch() calls wrapped in try-catch
4. Payload size management: JSON preview limited to 48 lines with scroll
5. Form data construction: Always includes file + pipeline JSON

INTEGRATION POINTS:
------------------
**API Endpoints (Required):**
- POST /cam/pipeline/run - Main pipeline execution (FormData: file, pipeline JSON)
- GET /cam/pipeline/presets - List saved presets
- POST /cam/pipeline/presets - Create new preset
- GET /cam/machines/{id} - Fetch machine profile
- GET /cam/posts/{id} - Fetch post profile

**Child Components:**
- CamPipelineGraph.vue - Visual pipeline state display (op status cards)

**Parent Components:**
- PipelineLabView.vue - Mounts this runner + CamBackplotViewer
- Wires events: @adaptive-plan-ready, @sim-result-ready

**Event Payloads:**
- adaptive-plan-ready: { moves: any[], stats: any, overlays?: any[] }
- sim-result-ready: { issues: any[], moves: any[], summary: any }

DEPENDENCIES:
------------
- Vue 3 Composition API (ref, computed, onMounted, watch)
- CamPipelineGraph.vue component
- Backend: pipeline_router.py, pipeline_presets_router.py, machine_router.py, posts_router.py
- Tailwind CSS for styling

TYPICAL WORKFLOW:
----------------
1. User selects DXF file via file input
2. User configures: tool diameter, units, machine ID, post ID, bridge profile
3. (Optional) User selects preset → auto-fills machine/post/units
4. User clicks "Run Pipeline" → buildPipelineSpec() constructs operation graph
5. FormData sent to /cam/pipeline/run → backend executes 5 operations
6. Results displayed: per-op cards with OK/FAIL status, payload JSON
7. Events emitted: adaptive-plan-ready (moves for backplot), sim-result-ready (issues)
8. (Optional) User saves current config as preset for reuse

UI SECTIONS:
-----------
- **Header:** Title + route breadcrumb
- **Main Controls:** File input, tool ⌀, units, machine ID, post ID, bridge toggle, run button
- **Presets Row:** Preset dropdown + apply, new preset name/desc + save button
- **Inspector:** Machine profile card (feeds, accel, jerk), Post profile card (dialect, mode, line numbers)
- **Results:** CamPipelineGraph + per-op cards with payload JSON toggle
- **Error Display:** Red text for API/validation errors

FUTURE ENHANCEMENTS:
-------------------
- Drag-and-drop file upload (replace <input type="file">)
- Real-time progress bar during pipeline execution
- WebSocket support for long-running pipelines
- Preset editing (currently create-only)
- Machine/Post dropdowns (fetch from /cam/machines, /cam/posts lists)
- Operation reordering UI (drag-and-drop op cards)
- Export pipeline spec as JSON file
- Import pipeline spec from JSON file
================================================================================
-->

<template>
  <div class="p-4 border rounded-xl space-y-4 bg-white">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h3 class="text-sm font-semibold">
          Pipeline Lab
        </h3>
        <p class="text-[11px] text-gray-500">
          DXF → Preflight → Plan → Run → Export → Simulate
        </p>
      </div>
      <span class="text-[10px] text-gray-400">
        /lab/pipeline
      </span>
    </div>

    <!-- Main controls -->
    <div class="flex flex-wrap items-center gap-3">
      <input
        type="file"
        accept=".dxf"
        class="text-xs"
        @change="onFileChange"
      >

      <label class="inline-flex items-center space-x-1 text-xs">
        <span>Tool ⌀</span>
        <input
          v-model.number="toolDia"
          type="number"
          step="0.1"
          min="0.1"
          class="w-16 border rounded px-1 py-0.5 text-[11px]"
        >
        <span>mm</span>
      </label>

      <select
        v-model="units"
        class="border rounded px-2 py-1 text-xs"
      >
        <option value="mm">
          mm
        </option>
        <option value="inch">
          inch
        </option>
      </select>

      <input
        v-model="machineId"
        placeholder="machine_id"
        class="border rounded px-2 py-1 text-[11px] w-32"
      >

      <input
        v-model="postId"
        placeholder="post_id"
        class="border rounded px-2 py-1 text-[11px] w-32"
      >

      <label class="inline-flex items-center space-x-1 text-xs">
        <input
          v-model="bridgeProfile"
          type="checkbox"
        >
        <span>Bridge profile</span>
      </label>

      <button
        class="btn"
        :disabled="!file || loading"
        @click="runPipeline"
      >
        <span v-if="!loading">Run Pipeline</span>
        <span v-else>Running…</span>
      </button>

      <span
        v-if="summary"
        class="text-[11px] text-gray-600"
      >
        {{ summaryLabel }}
      </span>
    </div>

    <!-- H7.2: optional strict mode -->
    <div class="flex items-center gap-3 text-xs mt-1">
      <label class="inline-flex items-center gap-2">
        <input
          v-model="strictNormalize"
          type="checkbox"
        >
        <span>Strict CAM intent normalize</span>
      </label>
      <span
        v-if="normalizationIssues.length"
        class="text-[11px] text-amber-600"
      >
        Normalize issues: {{ normalizationIssues.length }}
      </span>
    </div>

    <!-- H7.2: show issues (non-breaking) -->
    <NormalizationIssuesPanel :issues="normalizationIssues" />

    <!-- Presets row -->
    <div class="flex flex-wrap items-center gap-2 text-[11px] mt-1">
      <div class="flex items-center gap-1">
        <span class="font-semibold">Preset:</span>
        <select
          v-model="selectedPresetId"
          class="border rounded px-2 py-1 text-[11px] min-w-[140px]"
          @change="selectedPresetId && applyPreset(selectedPresetId)"
        >
          <option :value="null">
            None
          </option>
          <option
            v-for="preset in presets"
            :key="preset.id"
            :value="preset.id"
          >
            {{ preset.name }}
          </option>
        </select>
        <span
          v-if="selectedPreset"
          class="text-gray-500"
        >
          ({{ selectedPreset.units }},
          {{ selectedPreset.machine_id || 'no machine' }},
          {{ selectedPreset.post_id || 'no post' }})
        </span>
      </div>

      <div class="flex items-center gap-1">
        <input
          v-model="newPresetName"
          placeholder="New preset name"
          class="border rounded px-2 py-1 text-[11px] w-40"
        >
        <input
          v-model="newPresetDesc"
          placeholder="Description (optional)"
          class="border rounded px-2 py-1 text-[11px] w-48"
        >
        <button
          class="px-2 py-1 rounded bg-gray-800 text-white text-[11px]"
          @click="savePreset"
        >
          Save preset
        </button>
      </div>
    </div>

    <!-- Preset inspector -->
    <div class="mt-2 grid md:grid-cols-2 gap-3 text-[11px]">
      <div
        v-if="inspectorMachine"
        class="border rounded-lg p-2 bg-white"
      >
        <div class="flex items-center justify-between mb-1">
          <span class="font-semibold text-gray-700">Machine</span>
          <span class="text-[10px] text-gray-400">{{ inspectorMachine.id }}</span>
        </div>
        <p class="text-gray-800">
          {{ inspectorMachine.name }}
        </p>
        <ul class="mt-1 space-y-0.5 text-gray-600">
          <li v-if="inspectorMachine.max_feed_xy">
            max feed XY: {{ inspectorMachine.max_feed_xy }}
          </li>
          <li v-if="inspectorMachine.rapid">
            rapid: {{ inspectorMachine.rapid }}
          </li>
          <li v-if="inspectorMachine.accel">
            accel: {{ inspectorMachine.accel }}
          </li>
          <li v-if="inspectorMachine.jerk">
            jerk: {{ inspectorMachine.jerk }}
          </li>
          <li v-if="inspectorMachine.safe_z_default">
            safe Z: {{ inspectorMachine.safe_z_default }}
          </li>
        </ul>
      </div>

      <div
        v-if="inspectorPost"
        class="border rounded-lg p-2 bg-white"
      >
        <div class="flex items-center justify-between mb-1">
          <span class="font-semibold text-gray-700">Post</span>
          <span class="text-[10px] text-gray-400">{{ inspectorPost.id }}</span>
        </div>
        <p class="text-gray-800">
          {{ inspectorPost.name }}
        </p>
        <ul class="mt-1 space-y-0.5 text-gray-600">
          <li v-if="inspectorPost.post">
            dialect: {{ inspectorPost.post }}
          </li>
          <li v-if="inspectorPost.post_mode">
            mode: {{ inspectorPost.post_mode }}
          </li>
          <li v-if="inspectorPost.line_numbers !== undefined">
            line numbers: {{ inspectorPost.line_numbers ? 'on' : 'off' }}
          </li>
        </ul>
      </div>
    </div>

    <!-- Error -->
    <p
      v-if="error"
      class="text-xs text-red-600"
    >
      {{ error }}
    </p>

    <!-- Results + graph -->
    <div
      v-if="results && results.length"
      class="space-y-3 mt-2"
    >
      <CamPipelineGraph :results="results" />

      <!-- Per-op cards -->
      <PipelineResultsCards
        :results="results"
        :open-payload-index="openPayloadIndex"
        @toggle-payload="togglePayload"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, watch } from 'vue'
import CamPipelineGraph from '@/components/cam/CamPipelineGraph.vue'
import NormalizationIssuesPanel from '@/components/cam/NormalizationIssuesPanel.vue'
import PipelineResultsCards from '@/components/cam/PipelineResultsCards.vue'
import {
  useCamPipelineState,
  useCamPipelineNormalize,
  useCamPipelineInspector,
  useCamPipelinePresets,
  useCamPipelineExecution,
  useCamPipelineHelpers,
  type CamPipelineEmits
} from './composables'

// Emits
const emit = defineEmits<CamPipelineEmits>()

// State
const {
  file,
  loading,
  error,
  toolDia,
  units,
  bridgeProfile,
  machineId,
  postId,
  results,
  summary,
  openPayloadIndex,
  presets,
  selectedPresetId,
  newPresetName,
  newPresetDesc,
  inspectorMachine,
  inspectorPost,
  strictNormalize,
  normalizationIssues,
  selectedPreset,
  summaryLabel
} = useCamPipelineState()

// Normalize
const { normalizePipelineSpecDeep } = useCamPipelineNormalize()

// Inspector
const { refreshInspector } = useCamPipelineInspector(
  machineId,
  postId,
  inspectorMachine,
  inspectorPost
)

// Presets
const { loadPresets, applyPreset, savePreset } = useCamPipelinePresets(
  presets,
  selectedPresetId,
  newPresetName,
  newPresetDesc,
  units,
  machineId,
  postId,
  error,
  refreshInspector
)

// Execution
const { runPipeline } = useCamPipelineExecution(
  file,
  loading,
  error,
  results,
  summary,
  openPayloadIndex,
  toolDia,
  units,
  bridgeProfile,
  machineId,
  postId,
  strictNormalize,
  normalizationIssues,
  normalizePipelineSpecDeep,
  emit
)

// Helpers
const { onFileChange, formatPayload, togglePayload } = useCamPipelineHelpers(
  file,
  openPayloadIndex
)

// Lifecycle
onMounted(() => {
  loadPresets()
})

watch([machineId, postId], () => {
  refreshInspector()
})
</script>

<style scoped>
.btn {
  @apply bg-gray-900 text-white rounded-lg px-3 py-2 text-xs disabled:opacity-50;
}
</style>
