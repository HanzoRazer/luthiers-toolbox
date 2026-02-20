<template>
  <div class="pipeline-lab">
    <div class="header">
      <h1>🔧 Pipeline Lab</h1>
      <p class="subtitle">
        Blueprint → CAM Complete Workflow (Phase 3.2)
      </p>
    </div>

    <!-- Stage Progress Tracker -->
    <div class="stage-progress">
      <div 
        v-for="(stage, idx) in stages" 
        :key="idx" 
        class="stage-item"
        :class="{ active: currentStage === idx, completed: currentStage > idx }"
      >
        <div class="stage-number">
          {{ idx + 1 }}
        </div>
        <div class="stage-label">
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
    <div class="navigation-buttons">
      <button
        v-if="currentStage > 0"
        class="btn btn-secondary"
        @click="prevStage()"
      >
        ⬅️ Previous Stage
      </button>
      <button
        class="btn btn-secondary"
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

<style scoped>
.pipeline-lab {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.header {
  text-align: center;
  margin-bottom: 40px;
}

.header h1 {
  font-size: 2.5em;
  margin: 0;
}

.subtitle {
  color: #666;
  margin-top: 10px;
}

/* Stage Progress */
.stage-progress {
  display: flex;
  gap: 10px;
  margin-bottom: 40px;
  justify-content: center;
}

.stage-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 20px;
  background: #f5f5f5;
  border-radius: 8px;
  opacity: 0.5;
}

.stage-item.active {
  background: #2196F3;
  color: white;
  opacity: 1;
}

.stage-item.completed {
  background: #4CAF50;
  color: white;
  opacity: 1;
}

.stage-number {
  width: 30px;
  height: 30px;
  background: white;
  color: #333;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
}

.stage-item.active .stage-number,
.stage-item.completed .stage-number {
  background: rgba(255,255,255,0.3);
  color: white;
}

/* Drop Zone */
.drop-zone {
  border: 3px dashed #ccc;
  border-radius: 12px;
  padding: 60px;
  text-align: center;
  transition: all 0.3s;
  background: #fafafa;
}

.drop-zone.dragging {
  border-color: #2196F3;
  background: #e3f2fd;
}

.upload-icon {
  font-size: 4em;
  margin-bottom: 20px;
}

.or-text {
  color: #999;
  margin: 20px 0;
}

.upload-button {
  display: inline-block;
  padding: 12px 24px;
  background: #2196F3;
  color: white;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.3s;
}

.upload-button:hover {
  background: #1976D2;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 20px;
  background: white;
  padding: 20px;
  border-radius: 8px;
}

.file-icon {
  font-size: 3em;
}

.clear-button {
  margin-left: auto;
  padding: 10px 15px;
  background: #f44336;
  color: white;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  font-size: 1.2em;
}

/* Status Badges */
.status-badge {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 15px 20px;
  border-radius: 8px;
  margin-bottom: 20px;
  font-size: 1.2em;
  font-weight: bold;
}

.status-badge.passed {
  background: #4CAF50;
  color: white;
}

.status-badge.failed {
  background: #f44336;
  color: white;
}

/* Summary Grid */
.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 15px;
  margin: 20px 0;
}

.stat-card {
  padding: 20px;
  border-radius: 8px;
  text-align: center;
  background: #f5f5f5;
}

.stat-card.error { border-left: 4px solid #f44336; }
.stat-card.warning { border-left: 4px solid #ff9800; }
.stat-card.info { border-left: 4px solid #2196F3; }
.stat-card.neutral { border-left: 4px solid #9e9e9e; }

.stat-value {
  font-size: 2.5em;
  font-weight: bold;
  margin-bottom: 5px;
}

.stat-label {
  color: #666;
  font-size: 0.9em;
}

/* Issues */
.issue-item {
  border-left: 4px solid #ccc;
  padding: 15px;
  margin: 10px 0;
  background: #f5f5f5;
  border-radius: 4px;
}

.issue-item.error { border-left-color: #f44336; }
.issue-item.warning { border-left-color: #ff9800; }
.issue-item.info { border-left-color: #2196F3; }

.issue-badge {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 0.85em;
  font-weight: bold;
  color: white;
  background: #666;
}

.issue-item.error .issue-badge { background: #f44336; }
.issue-item.warning .issue-badge { background: #ff9800; }
.issue-item.info .issue-badge { background: #2196F3; }

.issue-category {
  color: #666;
  font-size: 0.9em;
  margin-left: 10px;
}

.issue-suggestion {
  margin-top: 10px;
  color: #666;
  font-size: 0.95em;
}

/* Controls */
.control-group {
  margin: 15px 0;
}

.control-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
  color: #333;
}

.control-group input,
.control-group select {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 1em;
}

.control-group small {
  display: block;
  margin-top: 5px;
  color: #666;
}

.params-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
  margin: 20px 0;
}

/* Buttons */
.action-buttons {
  display: flex;
  gap: 15px;
  margin: 30px 0;
  justify-content: center;
}

.btn {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 1em;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-primary {
  background: #2196F3;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #1976D2;
}

.btn-secondary {
  background: #9e9e9e;
  color: white;
}

.btn-secondary:hover {
  background: #757575;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.navigation-buttons {
  display: flex;
  gap: 15px;
  justify-content: center;
  margin-top: 40px;
  padding-top: 20px;
  border-top: 1px solid #ddd;
}

/* Entity Chips */
.entity-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.entity-chip {
  display: flex;
  gap: 10px;
  padding: 8px 15px;
  background: #e3f2fd;
  border-radius: 20px;
  font-size: 0.9em;
}

.entity-type {
  font-weight: 500;
}

.entity-count {
  color: #666;
}

/* Loop Cards */
.loop-card {
  padding: 15px;
  background: #f5f5f5;
  border-radius: 8px;
  margin: 10px 0;
}

.loop-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 5px;
}

.badge-outer {
  padding: 3px 8px;
  background: #4CAF50;
  color: white;
  border-radius: 4px;
  font-size: 0.85em;
}

.badge-island {
  padding: 3px 8px;
  background: #ff9800;
  color: white;
  border-radius: 4px;
  font-size: 0.85em;
}

.stage-panel {
  animation: fadeIn 0.3s;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
