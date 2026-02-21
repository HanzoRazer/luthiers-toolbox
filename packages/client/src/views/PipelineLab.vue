<template>
  <div :class="styles.pipelineLab">
    <div :class="styles.header">
      <h1>🔧 Pipeline Lab</h1>
      <p :class="styles.subtitle">
        Blueprint → CAM Complete Workflow (Phase 3.2)
      </p>
    </div>

    <!-- Stage Progress Tracker -->
    <div :class="styles.stageProgress">
      <div
        v-for="(stage, idx) in stages"
        :key="idx"
        :class="stageItemClass(idx, currentStage)"
      >
        <div :class="styles.stageNumber">
          {{ idx + 1 }}
        </div>
        <div :class="styles.stageLabel">
          {{ stage }}
        </div>
      </div>
    </div>

    <!-- Stage 1: DXF Upload -->
    <Stage1UploadPanel
      v-if="currentStage === 0"
      v-model="dxfFile"
      :loading="preflightRunning"
      @submit="runPreflight"
      @clear="clearFile"
    />

    <!-- Stage 2: Preflight Results -->
    <Stage2PreflightPanel
      v-if="currentStage === 1"
      :report="preflightReport"
      @download="downloadHTMLReport"
      @continue="goToStage(2)"
    />

    <!-- Stage 3: Contour Reconstruction -->
    <Stage3ReconstructionPanel
      v-if="currentStage === 2"
      :params="reconstructionParams"
      :result="reconstructionResult"
      :loading="reconstructionRunning"
      @update:params="params => Object.assign(reconstructionParams, params)"
      @submit="runReconstruction"
      @continue="goToStage(3)"
    />

    <!-- Stage 4: Adaptive Pocket Parameters -->
    <Stage4ToolpathPanel
      v-if="currentStage === 3"
      :params="adaptiveParams"
      :result="toolpathResult"
      :loading="toolpathRunning"
      @update:params="params => Object.assign(adaptiveParams, params)"
      @submit="generateToolpath"
      @download-json="downloadJSON"
      @export-gcode="exportGCode"
    />

    <!-- Navigation -->
    <div :class="styles.navigationButtons">
      <button
        v-if="currentStage > 0"
        :class="buttons.btnSecondary"
        @click="prevStage()"
      >
        ⬅️ Previous Stage
      </button>
      <button
        :class="buttons.btnSecondary"
        @click="resetPipeline"
      >
        🔄 Reset Pipeline
      </button>
    </div>

    <!-- Blueprint → Adaptive Preset (Phase 27.0) -->
    <BlueprintPresetPanel
      :config="blueprintCfg"
      @update:config="cfg => Object.assign(blueprintCfg, cfg)"
    />
  </div>
</template>

<script setup lang="ts">
import { api } from '@/services/apiBase';
import { ref, computed } from 'vue'
import { usePipelineLabWorkflow } from '@/composables/usePipelineWorkflow'
import Stage1UploadPanel from '@/components/pipeline/Stage1UploadPanel.vue'
import Stage2PreflightPanel from '@/components/pipeline/Stage2PreflightPanel.vue'
import Stage3ReconstructionPanel from '@/components/pipeline/Stage3ReconstructionPanel.vue'
import Stage4ToolpathPanel from '@/components/pipeline/Stage4ToolpathPanel.vue'
import BlueprintPresetPanel from '@/components/pipeline/BlueprintPresetPanel.vue'
import styles from './PipelineLab.module.css'
import { buttons } from '@/styles/shared'

// CSS Module class helpers
function stageItemClass(idx: number, currentStage: number): string {
  if (currentStage === idx) return styles.stageItemActive
  if (currentStage > idx) return styles.stageItemCompleted
  return styles.stageItem
}

// Stage workflow (extracted composable)
const {
  currentStage,
  stages,
  canAdvance,
  next: nextStage,
  back: prevStage,
  goTo,
  reset: resetWorkflow,
  setStageCompleted,
  setStageLoading,
} = usePipelineLabWorkflow()

// Helper: go to stage and mark previous as complete
function goToStage(stageIndex: number) {
  for (let i = 0; i < stageIndex; i++) {
    setStageCompleted(i, true)
  }
  goTo(stageIndex)
}

// File handling
const dxfFile = ref<File | null>(null)

// Preflight
const preflightRunning = ref(false)
const preflightReport = ref<any>(null)

// Reconstruction
const reconstructionRunning = ref(false)
const reconstructionResult = ref<any>(null)
const reconstructionParams = ref({
  layer_name: 'Contours',
  tolerance: 0.1,
  min_loop_points: 3
})

// Adaptive pocket
const toolpathRunning = ref(false)
const toolpathResult = ref<any>(null)
const adaptiveParams = ref({
  tool_d: 6.0,
  stepover: 0.45,
  stepdown: 2.0,
  margin: 0.5,
  strategy: 'Spiral',
  feed_xy: 1200,
  feed_z: 600,
  safe_z: 5.0,
  z_rough: -1.5
})

const stepoverPercent = computed({
  get: () => adaptiveParams.value.stepover * 100,
  set: (val: number) => { adaptiveParams.value.stepover = val / 100 }
})

// Blueprint → Adaptive Preset Config (state managed by component)
const blueprintCfg = ref({
  tool_d: 6.0,
  stepover: 0.45,
  stepdown: 2.0,
  margin: 0.5,
  safe_z: 5.0,
  z_rough: -1.5,
  feed_xy: 1200.0
})

function clearFile() {
  dxfFile.value = null
  preflightReport.value = null
  reconstructionResult.value = null
  toolpathResult.value = null
  resetWorkflow()
}

// Preflight
async function runPreflight() {
  if (!dxfFile.value) return
  
  preflightRunning.value = true
  try {
    const formData = new FormData()
    formData.append('file', dxfFile.value)
    formData.append('format', 'json')
    
    const response = await api('/api/cam/blueprint/preflight', {
      method: 'POST',
      body: formData
    })
    
    if (!response.ok) throw new Error('Preflight failed')
    
    preflightReport.value = await response.json()
    setStageCompleted(0, true); goToStage(1)
  } catch (error) {
    alert('Preflight check failed: ' + error)
  } finally {
    preflightRunning.value = false
  }
}

async function downloadHTMLReport() {
  if (!dxfFile.value) return
  
  const formData = new FormData()
  formData.append('file', dxfFile.value)
  formData.append('format', 'html')
  
  const response = await api('/api/cam/blueprint/preflight', {
    method: 'POST',
    body: formData
  })
  
  const blob = await response.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'dxf_preflight_report.html'
  a.click()
  URL.revokeObjectURL(url)
}

// Reconstruction
async function runReconstruction() {
  if (!dxfFile.value) return
  
  reconstructionRunning.value = true
  try {
    const formData = new FormData()
    formData.append('file', dxfFile.value)
    formData.append('layer_name', reconstructionParams.value.layer_name)
    formData.append('tolerance', reconstructionParams.value.tolerance.toString())
    formData.append('min_loop_points', reconstructionParams.value.min_loop_points.toString())
    
    const response = await api('/api/cam/blueprint/reconstruct-contours', {
      method: 'POST',
      body: formData
    })
    
    if (!response.ok) throw new Error('Reconstruction failed')
    
    reconstructionResult.value = await response.json()
  } catch (error) {
    alert('Contour reconstruction failed: ' + error)
  } finally {
    reconstructionRunning.value = false
  }
}

// Adaptive pocket
async function generateToolpath() {
  if (!dxfFile.value) return
  
  toolpathRunning.value = true
  try {
    const formData = new FormData()
    formData.append('file', dxfFile.value)
    Object.entries(adaptiveParams.value).forEach(([key, value]) => {
      formData.append(key, String(value))
    })
    
    const response = await api('/api/cam/blueprint/to-adaptive', {
      method: 'POST',
      body: formData
    })
    
    if (!response.ok) throw new Error('Toolpath generation failed')
    
    toolpathResult.value = await response.json()
  } catch (error) {
    alert('Toolpath generation failed: ' + error)
  } finally {
    toolpathRunning.value = false
  }
}

function downloadJSON() {
  if (!toolpathResult.value) return
  
  const blob = new Blob([JSON.stringify(toolpathResult.value, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'toolpath.json'
  a.click()
  URL.revokeObjectURL(url)
}

function exportGCode() {
  if (!toolpathResult.value) return
  
  // Convert moves to G-code
  const lines = ['G21', 'G90', 'G17']
  toolpathResult.value.moves.forEach((move: any) => {
    let line = move.code
    if (move.x !== undefined) line += ` X${move.x.toFixed(4)}`
    if (move.y !== undefined) line += ` Y${move.y.toFixed(4)}`
    if (move.z !== undefined) line += ` Z${move.z.toFixed(4)}`
    if (move.f !== undefined) line += ` F${move.f.toFixed(1)}`
    lines.push(line)
  })
  lines.push('M30')
  
  const blob = new Blob([lines.join('\n')], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'toolpath.nc'
  a.click()
  URL.revokeObjectURL(url)
}

function resetPipeline() {
  if (confirm('Reset pipeline? This will clear all progress.')) {
    clearFile()
  }
}

</script>

