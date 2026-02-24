<!--
================================================================================
Adaptive Lab View
================================================================================

PURPOSE:
--------
Standalone adaptive pocketing test environment. Allows users to:
1. Import DXF files and extract boundary loops
2. Edit loops JSON directly
3. Configure adaptive parameters (tool, stepover, strategy)
4. Run adaptive kernel and preview toolpath
5. Send configuration to PipelineLab for full G-code export

KEY ALGORITHMS:
--------------
1. DXF Import Workflow:
   - POST /cam/plan_from_dxf with FormData (file + units + tool_d + geometry_layer)
   - Backend extracts loops from DXF layer
   - Returns {plan: {loops, tool_d, stepover, ...}, debug: {...}}
   - Populate loops JSON editor + adaptive params from plan

2. Adaptive Execution:
   - Parse loops JSON (validate array of {pts: [[x,y], ...]})
   - POST /api/cam/pocket/adaptive/plan with {loops, units, tool_d, ...}
   - Receive {moves, stats, overlays}
   - Pass to CamBackplotViewer for visualization

3. Demo Loops:
   - Hardcoded 100×60mm rectangle for quick testing
   - Loads into loops JSON editor on button click

SAFETY RULES:
------------
1. JSON validation: Try/catch parse loops, show error if invalid
2. File validation: Check dxfFile exists before POST
3. Loading states: Disable buttons during API calls
4. Error display: Show dxfError, adaptiveError in red text
5. Null-safe props: CamBackplotViewer receives null simIssues (no sim in this view)

INTEGRATION POINTS:
------------------
**Child Components:**
- CamBackplotViewer.vue - Displays adaptive moves + overlays (no sim)

**Backend APIs:**
- POST /cam/plan_from_dxf - DXF → loops extraction
- POST /api/cam/pocket/adaptive/plan - Adaptive toolpath generation

**Router:**
- Route: /lab/adaptive
- Name: AdaptiveLab
- Link: router.push('/lab/pipeline') for Send to PipelineLab

**Data Flow:**
DXF file → /cam/plan_from_dxf → loops JSON → edit params → 
/api/cam/pocket/adaptive/plan → moves → CamBackplotViewer renders

DEPENDENCIES:
------------
- Vue 3 Composition API (ref, useRouter)
- Vue Router (router.push)
- CamBackplotViewer.vue (toolpath visualization)
- Tailwind CSS (responsive grid, form styling)

TYPICAL WORKFLOW:
----------------
1. User clicks "Choose File" and uploads DXF
2. Selects units (mm or inch)
3. (Optional) Enters geometry layer name
4. Clicks "Import DXF → Loops"
5. Backend extracts loops, returns JSON
6. Loops populate in JSON editor
7. Adaptive params populate from DXF metadata
8. User adjusts tool ⌀, stepover, strategy, feeds
9. Clicks "Run Adaptive Kernel"
10. Backend generates toolpath
11. CamBackplotViewer displays blue toolpath with overlays
12. User clicks "Open PipelineLab" to export G-code

UI STRUCTURE:
------------
┌─ Adaptive Lab (/lab/adaptive) ──────────────────────┐
│ Loops → Adaptive kernel → Toolpath preview          │
├──────────────────────────────────────────────────────┤
│ ┌─ Left Panel ─────────┐ ┌─ Right Panel ──────────┐│
│ │ DXF → Loops          │ │ CamBackplotViewer      ││
│ │ [File] [Units] [Import] │                        ││
│ │                        │ │ [SVG canvas with      ││
│ │ Adaptive Parameters  │ │  blue toolpath +       ││
│ │ [Tool ⌀] [Stepover]  │ │  overlays]             ││
│ │ [Strategy] [Feeds]   │ │                        ││
│ │ [Run Adaptive Kernel]│ │ Stats: time, moves    ││
│ │                        │ └────────────────────────┘│
│ │ Loops JSON           │ │                          │
│ │ [Textarea editor]    │ │                          │
│ │ [Load demo loops]    │ │                          │
│ │                        │ │                          │
│ │ Send to PipelineLab  │ │                          │
│ │ [Open PipelineLab]   │ │                          │
│ └──────────────────────┘ └────────────────────────┘│
└──────────────────────────────────────────────────────┘

FUTURE ENHANCEMENTS:
-------------------
- Save/load presets (persist params to localStorage)
- Export loops JSON as file
- Import loops JSON from file
- Multi-layer DXF support (select layer from dropdown)
- Auto-detect units from DXF
- Visual loop editor (click points to create loops)
- Island support UI (mark loops as outer vs islands)
- Smoothing parameter control (arc tolerance)
================================================================================
-->

<template>
  <div class="p-4 space-y-4">
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-sm font-semibold">
          Adaptive Lab
        </h2>
        <p class="text-[11px] text-gray-500">
          Loops → Adaptive kernel → Toolpath preview
        </p>
      </div>
      <span class="text-[10px] text-gray-400">/lab/adaptive</span>
    </div>

    <div class="grid md:grid-cols-[1.1fr,1.3fr] gap-4">
      <div class="space-y-3">
        <!-- DXF import -->
        <DxfImportPanel
          v-model:units="dxfUnits"
          v-model:geometry-layer="dxfGeometryLayer"
          :has-file="!!dxfFile"
          :loading="loadingDxf"
          :error="dxfError"
          :debug="dxfDebug"
          @file-change="dxfFile = $event"
          @import="importFromDxf"
        />

        <!-- Adaptive params + run -->
        <AdaptiveParamsForm
          :params="adaptiveParamsObject"
          :running="runningAdaptive"
          :error="adaptiveError"
          @update:params="handleParamsUpdate"
          @run="runAdaptive"
        />

        <!-- Loops JSON editor -->
        <LoopsJsonEditor
          v-model="loopsJson"
          @load-demo="loadDemoLoops"
        />

        <!-- Send to pipeline -->
        <PipelineActions
          @open-compare="openCompareLab"
          @open-pipeline="sendToPipeline"
        />
      </div>

      <CamBackplotViewer
        :loops="[]"
        :moves="moves"
        :stats="stats"
        :overlays="overlays"
        :sim-issues="null"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { api } from '@/services/apiBase';
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import CamBackplotViewer from '@/components/cam/CamBackplotViewer.vue'
import DxfImportPanel from './adaptive_lab/DxfImportPanel.vue'
import AdaptiveParamsForm, { type AdaptiveParams } from './adaptive_lab/AdaptiveParamsForm.vue'
import LoopsJsonEditor from './adaptive_lab/LoopsJsonEditor.vue'
import PipelineActions from './adaptive_lab/PipelineActions.vue'
import { loopsToGeometry } from '@/utils/geometry'

const router = useRouter()
const COMPARE_STORAGE_KEY = 'toolbox.compare.currentGeometry'

const dxfFile = ref<File | null>(null)
const dxfUnits = ref<'mm' | 'inch'>('mm')
const dxfGeometryLayer = ref<string>('')
const dxfError = ref<string | null>(null)
const dxfDebug = ref<string | null>(null)
const loadingDxf = ref(false)

const toolD = ref(6.0)
const stepover = ref(0.45)
const stepdown = ref(2.0)
const margin = ref(0.5)
const strategy = ref<'Spiral' | 'Lanes'>('Spiral')
const feedXY = ref(1200.0)
const safeZ = ref(5.0)
const zRough = ref(-1.5)
const adaptiveError = ref<string | null>(null)
const runningAdaptive = ref(false)

const loopsJson = ref<string>('')
const moves = ref<any[]>([])
const stats = ref<any | null>(null)
const overlays = ref<any[] | null>(null)

function persistCompareSnapshot (loops: any[], units: 'mm' | 'inch' = 'mm') {
  try {
    const geometry = loopsToGeometry(Array.isArray(loops) ? loops : [], units)
    localStorage.setItem(COMPARE_STORAGE_KEY, JSON.stringify(geometry))
  } catch (error) {
    console.warn('Unable to persist compare snapshot', error)
  }
}

async function importFromDxf () {
  if (!dxfFile.value) return
  loadingDxf.value = true
  dxfError.value = null
  dxfDebug.value = null

  try {
    const form = new FormData()
    form.append('file', dxfFile.value)
    form.append('units', dxfUnits.value)
    form.append('tool_d', String(toolD.value || 6.0))
    if (dxfGeometryLayer.value.trim()) {
      form.append('geometry_layer', dxfGeometryLayer.value.trim())
    }
    form.append('auto_scale', 'true')

    const resp = await api('/api/cam/plan_from_dxf', {
      method: 'POST',
      body: form
    })

    if (!resp.ok) {
      const text = await resp.text()
      throw new Error(text || `HTTP ${resp.status}`)
    }

    const data = await resp.json() as { plan: any; debug?: any }
    const plan = data.plan || {}
    const loops = plan.loops ?? []

    loopsJson.value = JSON.stringify(loops, null, 2)
    const planUnits: 'mm' | 'inch' = plan.units === 'inch' ? 'inch' : (dxfUnits.value || 'mm')
    persistCompareSnapshot(loops, planUnits)

    if (typeof plan.tool_d === 'number') toolD.value = plan.tool_d
    if (typeof plan.stepover === 'number') stepover.value = plan.stepover
    if (typeof plan.stepdown === 'number') stepdown.value = plan.stepdown
    if (typeof plan.margin === 'number') margin.value = plan.margin
    if (typeof plan.feed_xy === 'number') feedXY.value = plan.feed_xy
    if (typeof plan.safe_z === 'number') safeZ.value = plan.safe_z
    if (typeof plan.z_rough === 'number') zRough.value = plan.z_rough
    if (typeof plan.strategy === 'string') strategy.value = plan.strategy

    if (data.debug) {
      dxfDebug.value = JSON.stringify(data.debug, null, 2)
    }
  } catch (e: any) {
    dxfError.value = e?.message ?? String(e)
  } finally {
    loadingDxf.value = false
  }
}

function loadDemoLoops () {
  const demo = [
    {
      pts: [
        [0, 0],
        [100, 0],
        [100, 60],
        [0, 60]
      ]
    }
  ]
  loopsJson.value = JSON.stringify(demo, null, 2)
  persistCompareSnapshot(demo, 'mm')
}

async function runAdaptive () {
  adaptiveError.value = null
  runningAdaptive.value = true
  moves.value = []
  stats.value = null
  overlays.value = null

  try {
    let loopsParsed: any
    try {
      loopsParsed = JSON.parse(loopsJson.value || '[]')
    } catch {
      throw new Error('Loops JSON is invalid.')
    }
    if (!Array.isArray(loopsParsed)) {
      throw new Error('Loops JSON must be an array of loops.')
    }

    persistCompareSnapshot(loopsParsed, 'mm')

    const body = {
      loops: loopsParsed,
      units: 'mm',
      tool_d: toolD.value || 6.0,
      stepover: stepover.value,
      stepdown: stepdown.value,
      margin: margin.value,
      strategy: strategy.value,
      feed_xy: feedXY.value,
      safe_z: safeZ.value,
      z_rough: zRough.value
    }

    const resp = await api('/api/cam/pocket/adaptive/plan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    })

    if (!resp.ok) {
      const text = await resp.text()
      throw new Error(text || `HTTP ${resp.status}`)
    }

    const data = await resp.json()
    moves.value = data.moves ?? []
    stats.value = data.stats ?? null
    overlays.value = data.overlays ?? null
  } catch (e: any) {
    adaptiveError.value = e?.message ?? String(e)
  } finally {
    runningAdaptive.value = false
  }
}

// Computed object for AdaptiveParamsForm
const adaptiveParamsObject = computed<AdaptiveParams>(() => ({
  toolD: toolD.value,
  stepover: stepover.value,
  stepdown: stepdown.value,
  margin: margin.value,
  strategy: strategy.value,
  feedXY: feedXY.value,
  safeZ: safeZ.value,
  zRough: zRough.value,
}))

function handleParamsUpdate(params: AdaptiveParams) {
  toolD.value = params.toolD
  stepover.value = params.stepover
  stepdown.value = params.stepdown
  margin.value = params.margin
  strategy.value = params.strategy
  feedXY.value = params.feedXY
  safeZ.value = params.safeZ
  zRough.value = params.zRough
}

function sendToPipeline () {
  router.push('/lab/pipeline')
}

function openCompareLab () {
  router.push('/lab/compare')
}
</script>
