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
    <div
      v-if="currentStage === 0"
      class="stage-panel"
    >
      <h2>📁 Stage 1: Upload DXF Blueprint</h2>
      
      <div 
        class="drop-zone"
        :class="{ dragging: isDragging }"
        @dragover.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false"
        @drop.prevent="handleDrop"
      >
        <div v-if="!dxfFile">
          <div class="upload-icon">
            📄
          </div>
          <p>Drag & drop DXF file here</p>
          <p class="or-text">
            or
          </p>
          <label class="upload-button">
            Browse Files
            <input
              type="file"
              accept=".dxf"
              hidden
              @change="handleFileSelect"
            >
          </label>
        </div>
        <div
          v-else
          class="file-info"
        >
          <div class="file-icon">
            ✅
          </div>
          <div>
            <h3>{{ dxfFile.name }}</h3>
            <p>{{ formatFileSize(dxfFile.size) }}</p>
          </div>
          <button
            class="clear-button"
            @click="clearFile"
          >
            ✕
          </button>
        </div>
      </div>

      <div
        v-if="dxfFile"
        class="action-buttons"
      >
        <button
          class="btn btn-primary"
          :disabled="preflightRunning"
          @click="runPreflight"
        >
          {{ preflightRunning ? '⏳ Checking...' : '🔍 Run Preflight Check' }}
        </button>
      </div>
    </div>

    <!-- Stage 2: Preflight Results -->
    <div
      v-if="currentStage === 1"
      class="stage-panel"
    >
      <h2>🔍 Stage 2: Preflight Validation</h2>
      
      <div
        v-if="preflightReport"
        class="preflight-results"
      >
        <!-- Status Badge -->
        <div
          class="status-badge"
          :class="preflightReport.passed ? 'passed' : 'failed'"
        >
          <span class="status-icon">{{ preflightReport.passed ? '✅' : '❌' }}</span>
          <span class="status-text">{{ preflightReport.passed ? 'PASSED' : 'FAILED' }}</span>
        </div>

        <!-- Summary Stats -->
        <div class="summary-grid">
          <div class="stat-card error">
            <div class="stat-value">
              {{ preflightReport.summary.errors }}
            </div>
            <div class="stat-label">
              ERRORS
            </div>
          </div>
          <div class="stat-card warning">
            <div class="stat-value">
              {{ preflightReport.summary.warnings }}
            </div>
            <div class="stat-label">
              WARNINGS
            </div>
          </div>
          <div class="stat-card info">
            <div class="stat-value">
              {{ preflightReport.summary.info }}
            </div>
            <div class="stat-label">
              INFO
            </div>
          </div>
          <div class="stat-card neutral">
            <div class="stat-value">
              {{ preflightReport.total_entities }}
            </div>
            <div class="stat-label">
              ENTITIES
            </div>
          </div>
        </div>

        <!-- Issues List -->
        <div
          v-if="preflightReport.issues.length > 0"
          class="issues-section"
        >
          <h3>Issues ({{ preflightReport.issues.length }})</h3>
          <div 
            v-for="(issue, idx) in preflightReport.issues" 
            :key="idx" 
            class="issue-item"
            :class="issue.severity.toLowerCase()"
          >
            <div class="issue-header">
              <span class="issue-badge">{{ issue.severity }}</span>
              <span class="issue-category">[{{ issue.category }}]</span>
              <span
                v-if="issue.layer"
                class="issue-layer"
              >Layer: {{ issue.layer }}</span>
            </div>
            <div class="issue-message">
              {{ issue.message }}
            </div>
            <div
              v-if="issue.suggestion"
              class="issue-suggestion"
            >
              💡 {{ issue.suggestion }}
            </div>
          </div>
        </div>

        <!-- Entity Stats -->
        <div
          v-if="preflightReport.stats.entity_types"
          class="entity-stats"
        >
          <h3>Entity Types</h3>
          <div class="entity-grid">
            <div 
              v-for="(count, type) in preflightReport.stats.entity_types" 
              :key="type" 
              class="entity-chip"
            >
              <span class="entity-type">{{ type }}</span>
              <span class="entity-count">{{ count }}</span>
            </div>
          </div>
        </div>

        <!-- Actions -->
        <div class="action-buttons">
          <button
            class="btn btn-secondary"
            @click="downloadHTMLReport"
          >
            📄 Download HTML Report
          </button>
          <button 
            class="btn btn-primary" 
            :disabled="preflightReport.summary.errors > 0"
            @click="currentStage = 2"
          >
            {{ preflightReport.summary.errors > 0 ? '❌ Fix Errors First' : '➡️ Continue to Reconstruction' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Stage 3: Contour Reconstruction -->
    <div
      v-if="currentStage === 2"
      class="stage-panel"
    >
      <h2>🔗 Stage 3: Contour Reconstruction</h2>
      
      <div class="reconstruction-controls">
        <div class="control-group">
          <label>Layer Name</label>
          <input
            v-model="reconstructionParams.layer_name"
            type="text"
            placeholder="Contours"
          >
        </div>
        <div class="control-group">
          <label>Tolerance (mm)</label>
          <input
            v-model.number="reconstructionParams.tolerance"
            type="number"
            step="0.05"
            min="0.05"
            max="1.0"
          >
        </div>
        <div class="control-group">
          <label>Min Loop Points</label>
          <input
            v-model.number="reconstructionParams.min_loop_points"
            type="number"
            min="3"
          >
        </div>
      </div>

      <div class="action-buttons">
        <button
          class="btn btn-primary"
          :disabled="reconstructionRunning"
          @click="runReconstruction"
        >
          {{ reconstructionRunning ? '⏳ Reconstructing...' : '🔗 Reconstruct Contours' }}
        </button>
      </div>

      <!-- Reconstruction Results -->
      <div
        v-if="reconstructionResult"
        class="reconstruction-results"
      >
        <div class="status-badge passed">
          <span class="status-icon">✅</span>
          <span class="status-text">{{ reconstructionResult.message }}</span>
        </div>

        <div class="summary-grid">
          <div class="stat-card neutral">
            <div class="stat-value">
              {{ reconstructionResult.loops.length }}
            </div>
            <div class="stat-label">
              LOOPS FOUND
            </div>
          </div>
          <div class="stat-card info">
            <div class="stat-value">
              {{ reconstructionResult.stats.lines_found }}
            </div>
            <div class="stat-label">
              LINES
            </div>
          </div>
          <div class="stat-card info">
            <div class="stat-value">
              {{ reconstructionResult.stats.splines_found }}
            </div>
            <div class="stat-label">
              SPLINES
            </div>
          </div>
          <div class="stat-card info">
            <div class="stat-value">
              {{ reconstructionResult.stats.edges_built }}
            </div>
            <div class="stat-label">
              EDGES
            </div>
          </div>
        </div>

        <!-- Warnings -->
        <div
          v-if="reconstructionResult.warnings.length > 0"
          class="warnings-section"
        >
          <h3>⚠️ Warnings</h3>
          <ul>
            <li
              v-for="(warning, idx) in reconstructionResult.warnings"
              :key="idx"
            >
              {{ warning }}
            </li>
          </ul>
        </div>

        <!-- Loop Info -->
        <div class="loops-section">
          <h3>Extracted Loops</h3>
          <div
            v-for="(loop, idx) in reconstructionResult.loops"
            :key="idx"
            class="loop-card"
          >
            <div class="loop-header">
              <strong>Loop {{ idx + 1 }}</strong>
              <span
                v-if="idx === reconstructionResult.outer_loop_idx"
                class="badge-outer"
              >OUTER</span>
              <span
                v-else
                class="badge-island"
              >ISLAND</span>
            </div>
            <div class="loop-info">
              Points: {{ loop.pts.length }}
            </div>
          </div>
        </div>

        <div class="action-buttons">
          <button
            class="btn btn-primary"
            @click="currentStage = 3"
          >
            ➡️ Continue to Adaptive Pocket
          </button>
        </div>
      </div>
    </div>

    <!-- Stage 4: Adaptive Pocket Parameters -->
    <div
      v-if="currentStage === 3"
      class="stage-panel"
    >
      <h2>⚙️ Stage 4: Adaptive Pocket Toolpath</h2>
      
      <div class="params-grid">
        <div class="control-group">
          <label>Tool Diameter (mm)</label>
          <input
            v-model.number="adaptiveParams.tool_d"
            type="number"
            step="0.5"
            min="1"
          >
        </div>
        <div class="control-group">
          <label>Stepover (%)</label>
          <input
            v-model.number="stepoverPercent"
            type="number"
            step="5"
            min="10"
            max="100"
          >
          <small>{{ adaptiveParams.stepover.toFixed(2) }} of tool diameter</small>
        </div>
        <div class="control-group">
          <label>Stepdown (mm)</label>
          <input
            v-model.number="adaptiveParams.stepdown"
            type="number"
            step="0.5"
            min="0.5"
          >
        </div>
        <div class="control-group">
          <label>Margin (mm)</label>
          <input
            v-model.number="adaptiveParams.margin"
            type="number"
            step="0.1"
            min="0"
          >
        </div>
        <div class="control-group">
          <label>Strategy</label>
          <select v-model="adaptiveParams.strategy">
            <option>Spiral</option>
            <option>Lanes</option>
          </select>
        </div>
        <div class="control-group">
          <label>Feed XY (mm/min)</label>
          <input
            v-model.number="adaptiveParams.feed_xy"
            type="number"
            step="100"
            min="100"
          >
        </div>
      </div>

      <div class="action-buttons">
        <button
          class="btn btn-primary"
          :disabled="toolpathRunning"
          @click="generateToolpath"
        >
          {{ toolpathRunning ? '⏳ Generating...' : '⚡ Generate Toolpath' }}
        </button>
      </div>

      <!-- Toolpath Results -->
      <div
        v-if="toolpathResult"
        class="toolpath-results"
      >
        <div class="status-badge passed">
          <span class="status-icon">✅</span>
          <span class="status-text">Toolpath Generated</span>
        </div>

        <div class="summary-grid">
          <div class="stat-card neutral">
            <div class="stat-value">
              {{ toolpathResult.stats.length_mm.toFixed(1) }}
            </div>
            <div class="stat-label">
              LENGTH (mm)
            </div>
          </div>
          <div class="stat-card info">
            <div class="stat-value">
              {{ toolpathResult.stats.time_min.toFixed(2) }}
            </div>
            <div class="stat-label">
              TIME (min)
            </div>
          </div>
          <div class="stat-card info">
            <div class="stat-value">
              {{ toolpathResult.moves.length }}
            </div>
            <div class="stat-label">
              MOVES
            </div>
          </div>
          <div class="stat-card info">
            <div class="stat-value">
              {{ (toolpathResult.stats.volume_mm3 / 1000).toFixed(1) }}
            </div>
            <div class="stat-label">
              VOLUME (cm³)
            </div>
          </div>
        </div>

        <div class="action-buttons">
          <button
            class="btn btn-secondary"
            @click="downloadJSON"
          >
            📥 Download JSON
          </button>
          <button
            class="btn btn-primary"
            @click="exportGCode"
          >
            📄 Export G-code
          </button>
        </div>
      </div>
    </div>

    <!-- Navigation -->
    <div class="navigation-buttons">
      <button
        v-if="currentStage > 0"
        class="btn btn-secondary"
        @click="currentStage--"
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
    <div
      class="stage-panel"
      style="margin-top: 40px; border: 2px solid #9C27B0;"
    >
      <h2>🎨 Blueprint → Adaptive Preset (Phase 27.0)</h2>
      <p class="stage-description">
        Upload a blueprint image and run one-click Blueprint → Adaptive pipeline directly.
        Generate toolpath preview and send to Art Studio for refinement.
      </p>

      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-top: 20px;">
        <!-- File Upload -->
        <div>
          <h3 style="font-size: 1.1em; margin-bottom: 10px;">
            📄 Blueprint Image
          </h3>
          <input
            type="file"
            accept="image/*"
            style="display: block; width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px;"
            @change="onBlueprintPresetFileChange"
          >
          <div
            v-if="blueprintPresetFile"
            style="margin-top: 10px; color: #4CAF50;"
          >
            ✅ {{ blueprintPresetFile.name }}
          </div>
        </div>

        <!-- Tool Configuration -->
        <div>
          <h3 style="font-size: 1.1em; margin-bottom: 10px;">
            🔧 Tool Configuration
          </h3>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
            <label style="display: flex; flex-direction: column;">
              <span style="font-size: 0.9em; color: #666;">Tool Ø (mm)</span>
              <input
                v-model.number="blueprintCfg.tool_d"
                type="number"
                step="0.1"
                style="padding: 8px; border: 1px solid #ddd; border-radius: 4px;"
              >
            </label>
            <label style="display: flex; flex-direction: column;">
              <span style="font-size: 0.9em; color: #666;">Stepover</span>
              <input
                v-model.number="blueprintCfg.stepover"
                type="number"
                step="0.05"
                style="padding: 8px; border: 1px solid #ddd; border-radius: 4px;"
              >
            </label>
            <label style="display: flex; flex-direction: column;">
              <span style="font-size: 0.9em; color: #666;">Stepdown</span>
              <input
                v-model.number="blueprintCfg.stepdown"
                type="number"
                step="0.1"
                style="padding: 8px; border: 1px solid #ddd; border-radius: 4px;"
              >
            </label>
            <label style="display: flex; flex-direction: column;">
              <span style="font-size: 0.9em; color: #666;">Margin</span>
              <input
                v-model.number="blueprintCfg.margin"
                type="number"
                step="0.1"
                style="padding: 8px; border: 1px solid #ddd; border-radius: 4px;"
              >
            </label>
            <label style="display: flex; flex-direction: column;">
              <span style="font-size: 0.9em; color: #666;">Safe Z</span>
              <input
                v-model.number="blueprintCfg.safe_z"
                type="number"
                step="0.1"
                style="padding: 8px; border: 1px solid #ddd; border-radius: 4px;"
              >
            </label>
            <label style="display: flex; flex-direction: column;">
              <span style="font-size: 0.9em; color: #666;">Z Rough</span>
              <input
                v-model.number="blueprintCfg.z_rough"
                type="number"
                step="0.1"
                style="padding: 8px; border: 1px solid #ddd; border-radius: 4px;"
              >
            </label>
            <label style="display: flex; flex-direction: column; grid-column: span 2;">
              <span style="font-size: 0.9em; color: #666;">Feed XY</span>
              <input
                v-model.number="blueprintCfg.feed_xy"
                type="number"
                step="10"
                style="padding: 8px; border: 1px solid #ddd; border-radius: 4px;"
              >
            </label>
          </div>
        </div>

        <!-- Actions -->
        <div>
          <h3 style="font-size: 1.1em; margin-bottom: 10px;">
            ⚡ Actions
          </h3>
          <div style="display: flex; flex-direction: column; gap: 10px;">
            <button
              class="btn btn-primary"
              :disabled="!blueprintPresetFile || runningBlueprintPipeline"
              style="width: 100%;"
              @click="runBlueprintPresetPipeline"
            >
              {{ runningBlueprintPipeline ? '⏳ Running...' : '🚀 Run Blueprint → Adaptive' }}
            </button>
            <button
              class="btn"
              :disabled="!blueprintPipelineResponse"
              style="width: 100%; background: #9C27B0; color: white;"
              @click="sendToArtStudio"
            >
              🎨 Send to Art Studio
            </button>
          </div>
          <div
            v-if="lastArtStudioExport"
            style="margin-top: 10px; font-size: 0.9em; color: #4CAF50;"
          >
            ✅ Sent {{ lastArtStudioExport }}
          </div>
          <div
            v-if="blueprintPresetError"
            style="margin-top: 10px; padding: 10px; background: #ffebee; border-radius: 4px; color: #c62828; font-size: 0.9em;"
          >
            ❌ {{ blueprintPresetError }}
          </div>
        </div>

        <!-- Stats -->
        <div v-if="blueprintPipelineStats">
          <h3 style="font-size: 1.1em; margin-bottom: 10px;">
            📊 Stats
          </h3>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 0.9em;">
            <div style="padding: 10px; background: #f5f5f5; border-radius: 4px;">
              <span style="color: #666;">Moves:</span>
              <strong style="display: block; font-size: 1.2em; margin-top: 5px;">{{ blueprintPipelineStats.move_count }}</strong>
            </div>
            <div
              v-if="blueprintPipelineStats.length_mm"
              style="padding: 10px; background: #f5f5f5; border-radius: 4px;"
            >
              <span style="color: #666;">Length:</span>
              <strong style="display: block; font-size: 1.2em; margin-top: 5px;">{{ blueprintPipelineStats.length_mm }} mm</strong>
            </div>
            <div
              v-if="blueprintPipelineStats.area_mm2"
              style="padding: 10px; background: #f5f5f5; border-radius: 4px;"
            >
              <span style="color: #666;">Area:</span>
              <strong style="display: block; font-size: 1.2em; margin-top: 5px;">{{ blueprintPipelineStats.area_mm2 }} mm²</strong>
            </div>
            <div
              v-if="blueprintPipelineStats.time_s"
              style="padding: 10px; background: #f5f5f5; border-radius: 4px;"
            >
              <span style="color: #666;">Time:</span>
              <strong style="display: block; font-size: 1.2em; margin-top: 5px;">{{ blueprintPipelineStats.time_s }} s</strong>
            </div>
          </div>
        </div>

        <!-- Toolpath Preview -->
        <div style="grid-column: span 2;">
          <h3 style="font-size: 1.1em; margin-bottom: 10px;">
            🔍 Toolpath Preview
          </h3>
          <div style="width: 100%; height: 300px; background: #1a1a1a; border-radius: 8px; position: relative; overflow: hidden;">
            <svg
              v-if="previewSegments.length"
              viewBox="0 0 100 100"
              preserveAspectRatio="xMidYMid meet"
              style="width: 100%; height: 100%;"
            >
              <polyline
                v-for="(seg, idx) in previewSegments"
                :key="idx"
                :points="segToPoints(seg)"
                fill="none"
                stroke="lime"
                stroke-width="0.4"
              />
            </svg>
            <div
              v-else
              style="position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; color: #666; font-size: 0.9em;"
            >
              Run Blueprint → Adaptive to see toolpath
            </div>
          </div>
          <div
            v-if="previewSegments.length"
            style="margin-top: 10px; text-align: center; font-size: 0.9em; color: #666;"
          >
            {{ previewSegments.length }} segments
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const ARTSTUDIO_ADAPTIVE_KEY = 'ltb:artstudio:lastAdaptiveRequest'

// Stage definitions
const stages = [
  'Upload DXF',
  'Preflight Check',
  'Reconstruct Contours',
  'Adaptive Pocket'
]

const currentStage = ref(0)
const isDragging = ref(false)

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

// Blueprint → Adaptive Preset State
type Segment = { x1: number; y1: number; x2: number; y2: number }

const blueprintPresetFile = ref<File | null>(null)
const blueprintCfg = ref({
  tool_d: 6.0,
  stepover: 0.45,
  stepdown: 2.0,
  margin: 0.5,
  safe_z: 5.0,
  z_rough: -1.5,
  feed_xy: 1200.0
})

const runningBlueprintPipeline = ref(false)
const blueprintPresetError = ref<string | null>(null)
const blueprintPipelineResponse = ref<any | null>(null)
const blueprintPipelineStats = ref<any | null>(null)
const previewSegments = ref<Segment[]>([])
const lastArtStudioExport = ref<string | null>(null)

// File handling
function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement
  if (target.files && target.files[0]) {
    dxfFile.value = target.files[0]
  }
}

function handleDrop(event: DragEvent) {
  isDragging.value = false
  if (event.dataTransfer?.files && event.dataTransfer.files[0]) {
    const file = event.dataTransfer.files[0]
    if (file.name.toLowerCase().endsWith('.dxf')) {
      dxfFile.value = file
    } else {
      alert('Please upload a .dxf file')
    }
  }
}

function clearFile() {
  dxfFile.value = null
  preflightReport.value = null
  reconstructionResult.value = null
  toolpathResult.value = null
  currentStage.value = 0
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

// Preflight
async function runPreflight() {
  if (!dxfFile.value) return
  
  preflightRunning.value = true
  try {
    const formData = new FormData()
    formData.append('file', dxfFile.value)
    formData.append('format', 'json')
    
    const response = await fetch('/api/cam/blueprint/preflight', {
      method: 'POST',
      body: formData
    })
    
    if (!response.ok) throw new Error('Preflight failed')
    
    preflightReport.value = await response.json()
    currentStage.value = 1
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
  
  const response = await fetch('/api/cam/blueprint/preflight', {
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
    
    const response = await fetch('/api/cam/blueprint/reconstruct-contours', {
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
    
    const response = await fetch('/api/cam/blueprint/to-adaptive', {
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

// Blueprint → Adaptive Preset Handlers (Phase 27.0)
function onBlueprintPresetFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  blueprintPresetFile.value = input.files?.[0] || null
  blueprintPresetError.value = null
}

async function runBlueprintPresetPipeline() {
  if (!blueprintPresetFile.value) {
    blueprintPresetError.value = 'Select a blueprint file first.'
    return
  }
  runningBlueprintPipeline.value = true
  blueprintPresetError.value = null
  blueprintPipelineResponse.value = null
  blueprintPipelineStats.value = null
  previewSegments.value = []

  try {
    const form = new FormData()
    form.append('file', blueprintPresetFile.value)
    form.append('tool_d', String(blueprintCfg.value.tool_d))
    form.append('stepover', String(blueprintCfg.value.stepover))
    form.append('stepdown', String(blueprintCfg.value.stepdown))
    form.append('margin', String(blueprintCfg.value.margin))
    form.append('safe_z', String(blueprintCfg.value.safe_z))
    form.append('z_rough', String(blueprintCfg.value.z_rough))
    form.append('feed_xy', String(blueprintCfg.value.feed_xy))

    const res = await fetch('/api/pipeline/blueprint_to_adaptive', {
      method: 'POST',
      body: form
    })

    if (!res.ok) throw new Error('Blueprint → Adaptive failed')

    const data = await res.json()
    blueprintPipelineResponse.value = data
    blueprintPipelineStats.value = data.plan?.stats || null

    const segs = movesToSegments(data.plan?.moves || [])
    previewSegments.value = normalizeSegments(segs)
  } catch (err: any) {
    console.error('Blueprint → Adaptive pipeline error', err)
    blueprintPresetError.value = err?.message || String(err)
  } finally {
    runningBlueprintPipeline.value = false
  }
}

function sendToArtStudio() {
  const source = blueprintPipelineResponse.value?.adaptive_request || null

  if (!source) {
    blueprintPresetError.value = 'No Adaptive request available. Run Blueprint → Adaptive first.'
    return
  }

  try {
    localStorage.setItem(ARTSTUDIO_ADAPTIVE_KEY, JSON.stringify(source))
    const ts = new Date().toLocaleTimeString()
    lastArtStudioExport.value = `at ${ts}`
    window.location.href = '/art-studio'
  } catch (err) {
    console.error('Failed to export to Art Studio', err)
    blueprintPresetError.value = 'Failed to save Adaptive request for Art Studio.'
  }
}

// Toolpath Preview Helpers
function movesToSegments(moves: any[]): Segment[] {
  const segs: Segment[] = []
  let last = { x: 0, y: 0, has: false }

  for (const m of moves) {
    const x = typeof m.x === 'number' ? m.x : last.x
    const y = typeof m.y === 'number' ? m.y : last.y
    if (last.has) {
      segs.push({ x1: last.x, y1: last.y, x2: x, y2: y })
    }
    last = { x, y, has: true }
  }
  return segs
}

function normalizeSegments(segs: Segment[]): Segment[] {
  if (!segs.length) return []
  let minX = segs[0].x1, maxX = segs[0].x1
  let minY = segs[0].y1, maxY = segs[0].y1

  for (const s of segs) {
    minX = Math.min(minX, s.x1, s.x2)
    maxX = Math.max(maxX, s.x1, s.x2)
    minY = Math.min(minY, s.y1, s.y2)
    maxY = Math.max(maxY, s.y1, s.y2)
  }

  const dx = maxX - minX || 1
  const dy = maxY - minY || 1
  const scale = 90 / Math.max(dx, dy)
  const offsetX = (100 - dx * scale) / 2
  const offsetY = (100 - dy * scale) / 2

  return segs.map((s) => ({
    x1: (s.x1 - minX) * scale + offsetX,
    y1: 100 - ((s.y1 - minY) * scale + offsetY),
    x2: (s.x2 - minX) * scale + offsetX,
    y2: 100 - ((s.y2 - minY) * scale + offsetY)
  }))
}

function segToPoints(seg: Segment): string {
  return `${seg.x1},${seg.y1} ${seg.x2},${seg.y2}`
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
