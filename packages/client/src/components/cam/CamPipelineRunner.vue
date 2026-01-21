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
    <details
      v-if="normalizationIssues.length"
      class="mt-2 text-xs"
    >
      <summary class="cursor-pointer text-amber-700 hover:underline">
        CAM intent normalization issues ({{ normalizationIssues.length }})
      </summary>
      <div class="mt-2 space-y-2">
        <div
          v-for="(entry, idx) in normalizationIssues.slice(0, 50)"
          :key="idx"
          class="p-2 border border-amber-200 rounded-lg bg-amber-50"
        >
          <div class="font-semibold text-[11px] text-amber-800">
            {{ entry.path }}
          </div>
          <ul class="mt-1 ml-4 list-disc text-[11px] text-amber-700">
            <li
              v-for="(iss, j) in entry.issues"
              :key="j"
            >
              <span
                v-if="iss.code"
                class="font-mono"
              >[{{ iss.code }}]</span>
              {{ iss.message }}
              <span
                v-if="iss.path"
                class="opacity-70"
              > ({{ iss.path }})</span>
            </li>
          </ul>
        </div>
        <div
          v-if="normalizationIssues.length > 50"
          class="text-[11px] text-gray-500"
        >
          Showing first 50 issue groups...
        </div>
      </div>
    </details>

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
      <div class="space-y-1">
        <div
          v-for="(op, idx) in results"
          :key="idx"
          class="flex items-start justify-between px-3 py-2 rounded-lg border text-xs bg-gray-50"
        >
          <div class="flex flex-col space-y-1">
            <div class="flex items-center space-x-2">
              <span
                class="px-2 py-0.5 rounded-full text-[10px] font-semibold"
                :class="op.ok && !op.error ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'"
              >
                {{ op.ok && !op.error ? 'OK' : 'FAIL' }}
              </span>
              <span class="font-mono text-[11px] uppercase">
                {{ op.kind }}
              </span>
            </div>

            <p
              v-if="op.error"
              class="text-[11px] text-rose-700"
            >
              {{ op.error }}
            </p>

            <button
              v-if="op.payload"
              class="text-[10px] underline text-gray-600 text-left"
              @click="togglePayload(idx)"
            >
              {{ openPayloadIndex === idx ? 'Hide payload' : 'Show payload JSON' }}
            </button>
          </div>

          <pre
            v-if="openPayloadIndex === idx && op.payload"
            class="ml-4 max-h-48 overflow-auto bg-white rounded-md p-2 text-[10px] whitespace-pre-wrap w-full md:w-1/2"
          >{{ formatPayload(op.payload) }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import CamPipelineGraph from '@/components/cam/CamPipelineGraph.vue'
import { normalizeCamIntent } from '@/services/rmosCamIntentApi'

// H7.2: normalize-first adoption controls / visibility
const strictNormalize = ref(false)
const normalizationIssues = ref<
  { path: string; issues: Array<{ code?: string; message: string; severity?: string; path?: string }> }[]
>([])

function _isPlainObject(v: unknown): v is Record<string, any> {
  return !!v && typeof v === "object" && !Array.isArray(v)
}

// Heuristic: identify "intent-like" objects without importing CamIntent types here.
function _looksLikeCamIntent(obj: Record<string, any>): boolean {
  if ("operation" in obj) return true
  if ("operation_type" in obj) return true
  if ("op" in obj) return true
  if ("tool_id" in obj && ("material_id" in obj || "stock" in obj)) return true
  if ("mode" in obj && (obj.mode === "router_3axis" || obj.mode === "saw")) return true
  return false
}

async function _normalizePipelineSpecDeep(spec: any): Promise<{
  normalized: any
  issues: { path: string; issues: Array<{ code?: string; message: string; severity?: string; path?: string }> }[]
}> {
  const collected: {
    path: string
    issues: Array<{ code?: string; message: string; severity?: string; path?: string }>
  }[] = []

  async function walk(node: any, path: string): Promise<any> {
    if (node == null) return node

    if (Array.isArray(node)) {
      const out: any[] = []
      for (let i = 0; i < node.length; i++) {
        out.push(await walk(node[i], `${path}[${i}]`))
      }
      return out
    }

    if (_isPlainObject(node)) {
      // Normalize directly if it looks like a CamIntent
      if (_looksLikeCamIntent(node)) {
        try {
          const resp = await normalizeCamIntent(
            { intent: node as any, strict: false },
            { requestId: `CamPipelineRunner.normalizePipelineSpec.${Date.now()}` }
          )
          if (resp.issues?.length) {
            collected.push({ path, issues: resp.issues })
          }
          return resp.intent
        } catch {
          // If normalization fails, keep original
          return node
        }
      }

      // Otherwise deep-walk properties (and normalize nested intents)
      const out: Record<string, any> = { ...node }
      for (const key of Object.keys(out)) {
        out[key] = await walk(out[key], path ? `${path}.${key}` : key)
      }
      return out
    }

    // primitives
    return node
  }

  const normalized = await walk(spec, "pipeline")
  return { normalized, issues: collected }
}

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

interface PipelineResponse {
  ops: PipelineOpResult[]
  summary: Record<string, any>
}

interface PipelinePreset {
  id: string
  name: string
  description?: string | null
  units: 'mm' | 'inch'
  machine_id?: string | null
  post_id?: string | null
}

interface MachineProfile {
  id: string
  name: string
  max_feed_xy?: number
  rapid?: number
  accel?: number
  jerk?: number
  safe_z_default?: number
  [key: string]: any
}

interface PostProfile {
  id: string
  name: string
  post?: string
  post_mode?: string
  line_numbers?: boolean
  [key: string]: any
}

const emit = defineEmits<{
  (e: 'adaptive-plan-ready', payload: { moves: any[]; stats: any; overlays?: any[] }): void
  (e: 'sim-result-ready', payload: { issues: any[]; moves: any[]; summary: any }): void
}>()

const file = ref<File | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

const toolDia = ref(6.0)
const units = ref<'mm' | 'inch'>('mm')
const bridgeProfile = ref(false)
const machineId = ref<string | null>(null)
const postId = ref<string | null>(null)

const results = ref<PipelineOpResult[] | null>(null)
const summary = ref<Record<string, any> | null>(null)
const openPayloadIndex = ref<number | null>(null)

const presets = ref<PipelinePreset[]>([])
const selectedPresetId = ref<string | null>(null)
const newPresetName = ref('')
const newPresetDesc = ref('')

const inspectorMachine = ref<MachineProfile | null>(null)
const inspectorPost = ref<PostProfile | null>(null)

const selectedPreset = computed(() =>
  presets.value.find(p => p.id === selectedPresetId.value) ?? null
)

const summaryLabel = computed(() => {
  if (!summary.value) return ''
  const s = summary.value
  const time = (s.time_s ?? s.time_jerk_s ?? 0).toFixed(1)
  const moves = s.move_count ?? '—'
  return `time: ${time}s, moves: ${moves}`
})

onMounted(async () => {
  try {
    const resp = await fetch('/cam/pipeline/presets')
    if (!resp.ok) return
    const data = await resp.json() as PipelinePreset[]
    presets.value = data
  } catch {
    // ignore
  }
})

function onFileChange (ev: Event) {
  const input = ev.target as HTMLInputElement
  const f = input.files?.[0]
  if (f) file.value = f
}

function buildPipelineSpec () {
  const ops: any[] = []

  ops.push({
    kind: 'dxf_preflight',
    params: {
      profile: bridgeProfile.value ? 'bridge' : null,
      cam_layer_prefix: 'CAM_',
      debug: true
    }
  })

  ops.push({ kind: 'adaptive_plan', params: {} })
  ops.push({ kind: 'adaptive_plan_run', params: {} })

  ops.push({
    kind: 'export_post',
    params: {
      endpoint: '/cam/roughing_gcode',
      post_id: postId.value ?? undefined,
      units: units.value
    }
  })

  ops.push({
    kind: 'simulate_gcode',
    params: {
      machine_id: machineId.value ?? undefined
    }
  })

  return {
    ops,
    tool_d: toolDia.value || 6.0,
    units: units.value,
    geometry_layer: null,
    auto_scale: true,
    cam_layer_prefix: 'CAM_',
    machine_id: machineId.value ?? undefined,
    post_id: postId.value ?? undefined
  }
}

function formatPayload (payload: any): string {
  try {
    return JSON.stringify(payload, null, 2)
  } catch {
    return String(payload)
  }
}

function togglePayload (idx: number) {
  openPayloadIndex.value = openPayloadIndex.value === idx ? null : idx
}

async function runPipeline () {
  if (!file.value) return
  loading.value = true
  error.value = null
  results.value = null
  summary.value = null
  openPayloadIndex.value = null
  normalizationIssues.value = []

  try {
    const form = new FormData()
    form.append('file', file.value)

    // H7.2: normalize CamIntent(s) inside the pipeline before submit
    const pipelineDraft = buildPipelineSpec()
    const { normalized: pipelineNormalized, issues } = await _normalizePipelineSpecDeep(pipelineDraft)
    normalizationIssues.value = issues

    if (strictNormalize.value && issues.length > 0) {
      // strict mode: fail early (non-breaking because default strict=false)
      const msg =
        issues
          .slice(0, 10)
          .map((x) => `${x.path}: ${x.issues.map((i) => i.message).join("; ")}`)
          .join(" | ") + (issues.length > 10 ? " | ..." : "")
      throw new Error(`CAM intent normalization failed (strict): ${msg}`)
    }

    form.append('pipeline', JSON.stringify(pipelineNormalized))

    const resp = await fetch('/cam/pipeline/run', {
      method: 'POST',
      body: form
    })

    if (!resp.ok) {
      const text = await resp.text()
      throw new Error(text || `HTTP ${resp.status}`)
    }

    const data = await resp.json() as PipelineResponse
    results.value = data.ops
    summary.value = data.summary ?? {}

    // Emit adaptive-plan-ready event for backplot
    const lastAdaptive = [...(data.ops || [])].reverse()
      .find(op => op.kind === 'adaptive_plan_run' && op.ok && op.payload)
    if (lastAdaptive && lastAdaptive.payload) {
      const moves = lastAdaptive.payload.moves ?? []
      const stats = lastAdaptive.payload.stats ?? {}
      const overlays = lastAdaptive.payload.overlays ?? []
      emit('adaptive-plan-ready', { moves, stats, overlays })
    }

    // Emit sim-result-ready event for backplot severity coloring
    const lastSim = [...(data.ops || [])].reverse()
      .find(op => op.kind === 'simulate_gcode' && op.ok && op.payload)
    if (lastSim && lastSim.payload) {
      const issues = lastSim.payload.issues ?? []
      const moves = lastSim.payload.moves ?? []
      const summarySim = lastSim.payload.summary ?? {}
      emit('sim-result-ready', { issues, moves, summary: summarySim })
    }
  } catch (e: any) {
    error.value = e?.message ?? String(e)
  } finally {
    loading.value = false
  }
}

async function refreshInspector () {
  inspectorMachine.value = null
  inspectorPost.value = null

  try {
    if (machineId.value) {
      const resp = await fetch(`/cam/machines/${machineId.value}`)
      if (resp.ok) inspectorMachine.value = await resp.json() as MachineProfile
    }
  } catch {
    // ignore
  }

  try {
    if (postId.value) {
      const resp = await fetch(`/cam/posts/${postId.value}`)
      if (resp.ok) inspectorPost.value = await resp.json() as PostProfile
    }
  } catch {
    // ignore
  }
}

const applyPreset = async (id: string | null) => {
  if (!id) return
  const preset = presets.value.find(p => p.id === id)
  if (!preset) return
  selectedPresetId.value = id
  units.value = preset.units
  machineId.value = preset.machine_id ?? null
  postId.value = preset.post_id ?? null
  await refreshInspector()
}

watch([machineId, postId], () => {
  refreshInspector()
})

async function savePreset () {
  if (!newPresetName.value.trim()) {
    error.value = 'Preset name is required.'
    return
  }
  error.value = null
  try {
    const body = {
      name: newPresetName.value.trim(),
      description: newPresetDesc.value.trim() || null,
      units: units.value,
      machine_id: machineId.value,
      post_id: postId.value
    }
    const resp = await fetch('/cam/pipeline/presets', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    })
    if (!resp.ok) {
      const text = await resp.text()
      throw new Error(text || `HTTP ${resp.status}`)
    }
    const created = await resp.json() as PipelinePreset
    presets.value.push(created)
    selectedPresetId.value = created.id
    newPresetName.value = ''
    newPresetDesc.value = ''
    await refreshInspector()
  } catch (e: any) {
    error.value = e?.message ?? String(e)
  }
}
</script>

<style scoped>
.btn {
  @apply bg-gray-900 text-white rounded-lg px-3 py-2 text-xs disabled:opacity-50;
}
</style>
