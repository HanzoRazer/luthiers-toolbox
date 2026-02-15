<!--
Luthier's Tool Box - CNC Guitar Lutherie CAD/CAM Toolbox
Bridge Lab View - Complete DXF → CAM Workflow

Enhanced in Phase 24.5: Machine Envelope Integration
Repository: HanzoRazer/luthiers-toolbox
Updated: January 2025

Features:
- Multi-stage DXF preflight, adaptive planning, export, and simulation workflow
- Machine-aware CAM defaults auto-fill from envelope panel
- Per-machine state persistence
- Over-travel detection and envelope visualization
-->

<template>
  <div class="bridge-lab-view">
    <div class="lab-header">
      <h1>🌉 Bridge Lab</h1>
      <p class="subtitle">
        Complete DXF → Preflight → Adaptive → Export → Simulate Workflow
      </p>
    </div>

    <div class="workflow-container">
      <!-- Stage 0: Bridge Calculator -->
      <div class="workflow-stage">
        <div class="stage-header">
          <h2>Stage 0: Bridge Calculator</h2>
          <span class="stage-badge">0</span>
        </div>

        <BridgeCalculatorPanel @dxf-generated="onCalculatorDxfGenerated" />

        <p
          v-if="calculatorStatus"
          class="calculator-status"
        >
          {{ calculatorStatus }}
        </p>
      </div>

      <!-- Stage 1: DXF Preflight -->
      <div class="workflow-stage">
        <div class="stage-header">
          <h2>Stage 1: DXF Preflight</h2>
          <span
            class="stage-badge"
            :class="{ active: currentStage === 1 }"
          >1</span>
        </div>
        
        <CamBridgePreflightPanel 
          ref="preflightPanelRef"
          @preflight-result="onPreflightResult"
          @dxf-file-changed="onDxfFileChanged"
        />

        <!-- Machine Envelope Selection -->
        <div class="mt-3">
          <CamMachineEnvelopePanel
            @machine-selected="onMachineSelected"
            @limits-changed="onLimitsChanged"
            @cam-defaults-changed="onCamDefaultsChanged"
          />
        </div>

        <!-- Pipeline Preset Save Panel (Phase 25.0) -->
        <div class="mt-3">
          <CamBridgeToPipelinePanel
            :machine="machine as any"
            :adaptive-units="adaptiveParams.units"
            :tool-d="adaptiveParams.tool_d"
            :stepover-pct="adaptiveParams.stepover * 100"
            :stepdown="adaptiveParams.stepdown"
            :feed-x-y="adaptiveParams.feed_xy"
            :geometry-layer="adaptiveParams.geometry_layer"
            :selected-post-id="selectedPostId"
            @preset-saved="(id) => console.log('Preset saved:', id)"
            @preset-run-result="(result) => console.log('Pipeline result:', result)"
          />
        </div>
      </div>

      <!-- Stage 2: Send to Adaptive -->
      <div
        v-if="preflightPassed"
        class="workflow-stage"
      >
        <div class="stage-header">
          <h2>Stage 2: Generate Toolpath</h2>
          <span
            class="stage-badge"
            :class="{ active: currentStage === 2 }"
          >2</span>
        </div>
        
        <div class="adaptive-panel">
          <h3>Adaptive Pocket Parameters</h3>
          
          <div class="param-grid">
            <div class="param-field">
              <label>Tool Diameter</label>
              <input
                v-model.number="adaptiveParams.tool_d"
                type="number"
                step="0.1"
              >
              <span class="unit">{{ adaptiveParams.units }}</span>
            </div>
            
            <div class="param-field">
              <label>Units</label>
              <select v-model="adaptiveParams.units">
                <option value="mm">
                  Millimeters
                </option>
                <option value="inch">
                  Inches
                </option>
              </select>
            </div>
            
            <div class="param-field">
              <label>Geometry Layer</label>
              <input
                v-model="adaptiveParams.geometry_layer"
                type="text"
              >
            </div>
            
            <div class="param-field">
              <label>Stepover</label>
              <input
                v-model.number="adaptiveParams.stepover"
                type="number"
                step="0.05"
                min="0.1"
                max="1.0"
              >
              <span class="unit">% of tool_d</span>
            </div>
            
            <div class="param-field">
              <label>Stepdown</label>
              <input
                v-model.number="adaptiveParams.stepdown"
                type="number"
                step="0.1"
              >
              <span class="unit">{{ adaptiveParams.units }}</span>
            </div>
            
            <div class="param-field">
              <label>Margin</label>
              <input
                v-model.number="adaptiveParams.margin"
                type="number"
                step="0.1"
              >
              <span class="unit">{{ adaptiveParams.units }}</span>
            </div>
            
            <div class="param-field">
              <label>Strategy</label>
              <select v-model="adaptiveParams.strategy">
                <option value="Spiral">
                  Spiral
                </option>
                <option value="Lanes">
                  Lanes
                </option>
              </select>
            </div>
            
            <div class="param-field">
              <label>Feed XY</label>
              <input
                v-model.number="adaptiveParams.feed_xy"
                type="number"
                step="100"
              >
              <span class="unit">{{ adaptiveParams.units }}/min</span>
            </div>
            
            <div class="param-field">
              <label>Safe Z</label>
              <input
                v-model.number="adaptiveParams.safe_z"
                type="number"
                step="0.5"
              >
              <span class="unit">{{ adaptiveParams.units }}</span>
            </div>
            
            <div class="param-field">
              <label>Z Rough</label>
              <input
                v-model.number="adaptiveParams.z_rough"
                type="number"
                step="0.5"
              >
              <span class="unit">{{ adaptiveParams.units }}</span>
            </div>
          </div>
          
          <button 
            class="btn-primary" 
            :disabled="!dxfFile || adaptiveRunning"
            @click="sendToAdaptive"
          >
            {{ adaptiveRunning ? 'Generating Toolpath...' : '🔄 Generate Adaptive Toolpath' }}
          </button>
          
          <!-- Toolpath Results -->
          <div
            v-if="toolpathResult"
            class="toolpath-results"
          >
            <h4>Toolpath Generated</h4>
            <div class="stats-grid">
              <div class="stat-item">
                <span class="label">Moves:</span>
                <span class="value">{{ toolpathResult.stats?.move_count || 0 }}</span>
              </div>
              <div class="stat-item">
                <span class="label">Length:</span>
                <span class="value">{{ (toolpathResult.stats?.length_mm || 0).toFixed(1) }} mm</span>
              </div>
              <div class="stat-item">
                <span class="label">Time:</span>
                <span class="value">{{ (toolpathResult.stats?.time_s || 0).toFixed(1) }} s</span>
              </div>
              <div class="stat-item">
                <span class="label">Area:</span>
                <span class="value">{{ (toolpathResult.stats?.area_mm2 || 0).toFixed(1) }} mm²</span>
              </div>
            </div>
            
            <!-- Backplot Viewer -->
            <div class="backplot-container">
              <CamBackplotViewer 
                :moves="toolpathResult.moves || []"
                :stats="toolpathResult.stats"
                :units="adaptiveParams.units"
                :machine-limits="machineLimits"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Stage 3: Export G-code -->
      <div
        v-if="toolpathResult"
        class="workflow-stage"
      >
        <div class="stage-header">
          <h2>Stage 3: Export G-code</h2>
          <span
            class="stage-badge"
            :class="{ active: currentStage === 3 }"
          >3</span>
        </div>
        
        <div class="export-panel">
          <h3>Post-Processor Selection</h3>
          
          <div class="post-selector">
            <label>Select Post-Processor</label>
            <select v-model="selectedPostId">
              <option
                v-for="post in availablePosts"
                :key="post.id"
                :value="post.id"
              >
                {{ post.name || post.id }}
              </option>
            </select>
          </div>
          
          <div class="post-mode-selector">
            <label>Export Mode</label>
            <select v-model="postMode">
              <option value="standard">
                Standard (Full G-code)
              </option>
              <option value="dry_run">
                Dry Run (Rapid only)
              </option>
            </select>
          </div>
          
          <button 
            class="btn-primary" 
            :disabled="exportRunning || !selectedPostId"
            @click="exportGcode"
          >
            {{ exportRunning ? 'Exporting...' : '📤 Export G-code' }}
          </button>
          
          <p
            v-if="exportedFilename"
            class="success-message"
          >
            ✅ Exported: {{ exportedFilename }}
          </p>
        </div>
      </div>

      <!-- Stage 4: Simulate G-code -->
      <div
        v-if="exportedGcode"
        class="workflow-stage"
      >
        <div class="stage-header">
          <h2>Stage 4: Simulate G-code</h2>
          <span
            class="stage-badge"
            :class="{ active: currentStage === 4 }"
          >4</span>
        </div>
        
        <div class="simulate-panel">
          <h3>G-code Simulation</h3>
          
          <p class="help-text">
            Upload exported G-code file to verify toolpath
          </p>
          
          <div class="file-upload">
            <label class="upload-button">
              📁 Select G-code File
              <input
                type="file"
                accept=".nc,.gcode,.ngc"
                hidden
                @change="onGcodeFileChange"
              >
            </label>
            <span
              v-if="gcodeFile"
              class="file-name"
            >{{ gcodeFile.name }}</span>
          </div>
          
          <button 
            class="btn-primary" 
            :disabled="!gcodeFile || simRunning"
            @click="simulateGcode"
          >
            {{ simRunning ? 'Simulating...' : '▶️ Run Simulation' }}
          </button>
          
          <!-- Simulation Results -->
          <div
            v-if="simResult"
            class="sim-results"
          >
            <h4>Simulation Results</h4>
            <div class="stats-grid">
              <div class="stat-item">
                <span class="label">Moves:</span>
                <span class="value">{{ simResult.move_count || 0 }}</span>
              </div>
              <div class="stat-item">
                <span class="label">Length:</span>
                <span class="value">{{ (simResult.length_mm || 0).toFixed(1) }} mm</span>
              </div>
              <div class="stat-item">
                <span class="label">Time:</span>
                <span class="value">{{ (simResult.time_s || 0).toFixed(1) }} s</span>
              </div>
              <div class="stat-item">
                <span class="label">Units:</span>
                <span class="value">{{ simResult.units }}</span>
              </div>
            </div>
            
            <!-- Simulation Backplot -->
            <div class="backplot-container">
              <CamBackplotViewer 
                :moves="simResult.moves || []"
                :stats="{ move_count: simResult.move_count, time_s: simResult.time_s }"
                :sim-issues="simResult.issues"
                :units="simResult.units || 'mm'"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { api } from '@/services/apiBase';
import { ref, computed, onMounted } from 'vue'
import BridgeCalculatorPanel from '@/components/BridgeCalculatorPanel.vue'
import CamBridgePreflightPanel from '@/components/CamBridgePreflightPanel.vue'
import CamBackplotViewer from '@/components/CamBackplotViewer.vue'
import CamMachineEnvelopePanel from '@/components/CamMachineEnvelopePanel.vue'
import CamBridgeToPipelinePanel from '@/components/cam/CamBridgeToPipelinePanel.vue'

interface MachineLimits {
  min_x?: number | null
  max_x?: number | null
  min_y?: number | null
  max_y?: number | null
  min_z?: number | null
  max_z?: number | null
}

interface MachineCamDefaults {
  tool_d?: number | null
  stepover?: number | null
  stepdown?: number | null
  feed_xy?: number | null
  safe_z?: number | null
  z_rough?: number | null
}

interface Machine {
  id: string
  name: string
  controller?: string | null
  units?: string | null
  limits?: MachineLimits | null
  camDefaults?: MachineCamDefaults | null
}

// State
const currentStage = ref(1)
const dxfFile = ref<File | null>(null)
const preflightResult = ref<any>(null)
const toolpathResult = ref<any>(null)
const exportedGcode = ref<string | null>(null)
const exportedFilename = ref<string | null>(null)
const gcodeFile = ref<File | null>(null)
const simResult = ref<any>(null)
const calculatorStatus = ref<string | null>(null)
const preflightPanelRef = ref<{ loadExternalFile: (file: File | null) => void } | null>(null)

// Machine envelope state
const machine = ref<Machine | null>(null)
const machineLimits = ref<MachineLimits | null>(null)
const machineCamDefaults = ref<MachineCamDefaults | null>(null)

// Adaptive parameters
const adaptiveParams = ref({
  tool_d: 6.0,
  units: 'mm' as 'mm' | 'inch',
  geometry_layer: 'GEOMETRY',
  stepover: 0.45,
  stepdown: 2.0,
  margin: 0.5,
  strategy: 'Spiral' as 'Spiral' | 'Lanes',
  feed_xy: 1200,
  safe_z: 5.0,
  z_rough: -1.5
})

// Post processor
const availablePosts = ref<any[]>([])
const selectedPostId = ref('GRBL')
const postMode = ref('standard')

// Loading states
const adaptiveRunning = ref(false)
const exportRunning = ref(false)
const simRunning = ref(false)

// Computed
const preflightPassed = computed(() => {
  return preflightResult.value?.passed === true
})

// Lifecycle
onMounted(async () => {
  await loadPosts()
})

// Event handlers
function onDxfFileChanged(file: File | null) {
  dxfFile.value = file
  toolpathResult.value = null
  exportedGcode.value = null
  exportedFilename.value = null
  gcodeFile.value = null
  simResult.value = null
  currentStage.value = 1
  if (!file) {
    calculatorStatus.value = null
  }
}

function onCalculatorDxfGenerated(file: File) {
  calculatorStatus.value = `DXF generated: ${file.name}`
  currentStage.value = 1
  if (preflightPanelRef.value?.loadExternalFile) {
    preflightPanelRef.value.loadExternalFile(file)
  } else {
    dxfFile.value = file
  }
}

function onMachineSelected(m: Machine | null) {
  machine.value = m
}

function onLimitsChanged(limits: MachineLimits | null) {
  machineLimits.value = limits
}

function onCamDefaultsChanged(defaults: MachineCamDefaults | null) {
  machineCamDefaults.value = defaults
  if (!defaults) return

  // Auto-fill adaptive params from machine CAM defaults
  if (defaults.tool_d != null) {
    adaptiveParams.value.tool_d = defaults.tool_d
  }
  if (defaults.stepover != null) {
    adaptiveParams.value.stepover = defaults.stepover
  }
  if (defaults.stepdown != null) {
    adaptiveParams.value.stepdown = defaults.stepdown
  }
  if (defaults.feed_xy != null) {
    adaptiveParams.value.feed_xy = defaults.feed_xy
  }
  if (defaults.safe_z != null) {
    adaptiveParams.value.safe_z = defaults.safe_z
  }
  if (defaults.z_rough != null) {
    adaptiveParams.value.z_rough = defaults.z_rough
  }
}

function onPreflightResult(result: any) {
  preflightResult.value = result
  if (result.passed) {
    currentStage.value = 2
  }
}

// Stage 2: Send to Adaptive
async function sendToAdaptive() {
  if (!dxfFile.value) return
  
  adaptiveRunning.value = true
  currentStage.value = 2
  
  try {
    const formData = new FormData()
    formData.append('file', dxfFile.value)
    formData.append('units', adaptiveParams.value.units)
    formData.append('tool_d', adaptiveParams.value.tool_d.toString())
    formData.append('geometry_layer', adaptiveParams.value.geometry_layer)
    formData.append('stepover', adaptiveParams.value.stepover.toString())
    formData.append('stepdown', adaptiveParams.value.stepdown.toString())
    formData.append('margin', adaptiveParams.value.margin.toString())
    formData.append('strategy', adaptiveParams.value.strategy)
    formData.append('feed_xy', adaptiveParams.value.feed_xy.toString())
    formData.append('safe_z', adaptiveParams.value.safe_z.toString())
    formData.append('z_rough', adaptiveParams.value.z_rough.toString())
    
    const response = await api('/api/cam/dxf_adaptive_plan_run', {
      method: 'POST',
      body: formData
    })
    
    if (!response.ok) {
      throw new Error(`Adaptive planning failed: ${response.statusText}`)
    }
    
    toolpathResult.value = await response.json()
    currentStage.value = 3
  } catch (error) {
    console.error('Adaptive error:', error)
    alert(`Toolpath generation failed: ${error}`)
  } finally {
    adaptiveRunning.value = false
  }
}

// Stage 3: Export G-code
async function loadPosts() {
  try {
    const response = await api('/api/posts/')
    if (response.ok) {
      const data = await response.json()
      // /api/posts/ returns {"posts": [...]}
      availablePosts.value = data.posts || []
    } else {
      throw new Error('Failed to load posts')
    }
  } catch (error) {
    console.error('Failed to load posts:', error)
    // Fallback to default posts
    availablePosts.value = [
      { id: 'GRBL', name: 'GRBL' },
      { id: 'Mach4', name: 'Mach4' },
      { id: 'LinuxCNC', name: 'LinuxCNC' },
      { id: 'PathPilot', name: 'PathPilot' },
      { id: 'MASSO', name: 'MASSO' }
    ]
  }
}

async function exportGcode() {
  if (!toolpathResult.value || !selectedPostId.value) return
  
  exportRunning.value = true
  currentStage.value = 3
  
  try {
    const response = await api('/api/cam/toolpath/roughing/gcode', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        moves: toolpathResult.value.moves,
        units: adaptiveParams.value.units,
        post: selectedPostId.value,
        post_mode: postMode.value
      })
    })
    
    if (!response.ok) {
      throw new Error(`G-code export failed: ${response.statusText}`)
    }
    
    const gcode = await response.text()
    exportedGcode.value = gcode
    
    // Download file
    const blob = new Blob([gcode], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    const filename = `bridge_${selectedPostId.value.toLowerCase()}_${Date.now()}.nc`
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
    
    exportedFilename.value = filename
    currentStage.value = 4
  } catch (error) {
    console.error('Export error:', error)
    alert(`G-code export failed: ${error}`)
  } finally {
    exportRunning.value = false
  }
}

// Stage 4: Simulate G-code
function onGcodeFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  gcodeFile.value = input.files?.[0] ?? null
  simResult.value = null
}

async function simulateGcode() {
  if (!gcodeFile.value) return
  
  simRunning.value = true
  currentStage.value = 4
  
  try {
    const formData = new FormData()
    formData.append('file', gcodeFile.value)
    formData.append('units', adaptiveParams.value.units)
    
    const response = await api('/api/cam/simulate_gcode', {
      method: 'POST',
      body: formData
    })
    
    if (!response.ok) {
      throw new Error(`Simulation failed: ${response.statusText}`)
    }
    
    simResult.value = await response.json()
  } catch (error) {
    console.error('Simulation error:', error)
    alert(`G-code simulation failed: ${error}`)
  } finally {
    simRunning.value = false
  }
}
</script>

<style scoped>
.bridge-lab-view {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.lab-header {
  margin-bottom: 2rem;
  text-align: center;
}

.lab-header h1 {
  margin: 0 0 0.5rem 0;
  font-size: 2.5rem;
  font-weight: 700;
  color: #1f2937;
}

.subtitle {
  margin: 0;
  font-size: 1.125rem;
  color: #6b7280;
}

.calculator-status {
  margin: 1rem 1.5rem 1.5rem;
  color: #047857;
  font-weight: 500;
}

.workflow-container {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.workflow-stage {
  background: white;
  border-radius: 0.75rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.stage-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.stage-header h2 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
}

.stage-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  font-size: 1.25rem;
  font-weight: 700;
}

.stage-badge.active {
  background: rgba(255, 255, 255, 0.4);
  box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.3);
}

/* Adaptive Panel */
.adaptive-panel, .export-panel, .simulate-panel {
  padding: 1.5rem;
}

.adaptive-panel h3, .export-panel h3, .simulate-panel h3 {
  margin: 0 0 1.5rem 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
}

.param-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.param-field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.param-field label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
}

.param-field input, .param-field select {
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 0.875rem;
}

.param-field .unit {
  font-size: 0.75rem;
  color: #6b7280;
  margin-top: -0.25rem;
}

.btn-primary {
  width: 100%;
  padding: 0.75rem 1.5rem;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 0.375rem;
  font-weight: 500;
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-primary:hover:not(:disabled) {
  background: #2563eb;
}

.btn-primary:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.toolpath-results, .sim-results {
  margin-top: 1.5rem;
  padding: 1.5rem;
  background: #f9fafb;
  border-radius: 0.5rem;
  border: 1px solid #e5e7eb;
}

.toolpath-results h4, .sim-results h4 {
  margin: 0 0 1rem 0;
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.stat-item {
  display: flex;
  gap: 0.5rem;
  font-size: 0.875rem;
}

.stat-item .label {
  font-weight: 500;
  color: #6b7280;
}

.stat-item .value {
  color: #1f2937;
  font-weight: 600;
}

.backplot-container {
  margin-top: 1rem;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  overflow: hidden;
}

/* Export Panel */
.post-selector, .post-mode-selector {
  margin-bottom: 1rem;
}

.post-selector label, .post-mode-selector label {
  display: block;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
}

.post-selector select, .post-mode-selector select {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 0.875rem;
}

.success-message {
  margin-top: 1rem;
  padding: 0.75rem;
  background: #d1fae5;
  color: #065f46;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  font-weight: 500;
}

/* Simulate Panel */
.help-text {
  margin-bottom: 1rem;
  color: #6b7280;
  font-size: 0.875rem;
}

.file-upload {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.upload-button {
  display: inline-block;
  padding: 0.5rem 1rem;
  background: #e5e7eb;
  color: #1f2937;
  border-radius: 0.375rem;
  cursor: pointer;
  font-weight: 500;
  transition: background 0.2s;
  font-size: 0.875rem;
}

.upload-button:hover {
  background: #d1d5db;
}

.file-name {
  font-size: 0.875rem;
  color: #6b7280;
}
</style>
