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
          <ToolpathResultsPanel
            :toolpath-result="toolpathResult"
            :units="adaptiveParams.units"
            :machine-limits="machineLimits"
          />
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
        
        <GcodeExportPanel
          v-model:selected-post-id="selectedPostId"
          v-model:post-mode="postMode"
          :available-posts="availablePosts"
          :export-running="exportRunning"
          :exported-filename="exportedFilename"
          @export="exportGcode"
        />
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
          <SimulationResultsPanel :sim-result="simResult" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import BridgeCalculatorPanel from '@/components/bridge_calculator_panel/BridgeCalculatorPanel.vue'
import CamBridgePreflightPanel from '@/components/cam/CamBridgePreflightPanel.vue'
import CamMachineEnvelopePanel from '@/components/cam/CamMachineEnvelopePanel.vue'
import CamBridgeToPipelinePanel from '@/components/cam/CamBridgeToPipelinePanel.vue'
import ToolpathResultsPanel from './bridge_lab/ToolpathResultsPanel.vue'
import GcodeExportPanel from './bridge_lab/GcodeExportPanel.vue'
import SimulationResultsPanel from './bridge_lab/SimulationResultsPanel.vue'
import {
  useBridgeLabWorkflow,
  useMachineEnvelope,
  useAdaptiveToolpath,
  useGcodeExport,
  useGcodeSimulation
} from './bridge_lab/composables'

// Workflow state
const {
  currentStage,
  dxfFile,
  toolpathResult,
  exportedGcode,
  exportedFilename,
  gcodeFile,
  simResult,
  calculatorStatus,
  preflightPassed,
  onDxfFileChanged,
  onPreflightResult
} = useBridgeLabWorkflow()

// Adaptive toolpath
const { adaptiveParams, adaptiveRunning, sendToAdaptive } = useAdaptiveToolpath(
  dxfFile,
  currentStage,
  toolpathResult
)

// Machine envelope
const { machine, machineLimits, onMachineSelected, onLimitsChanged, onCamDefaultsChanged } =
  useMachineEnvelope(adaptiveParams)

// G-code export
const { availablePosts, selectedPostId, postMode, exportRunning, loadPosts, exportGcode } =
  useGcodeExport(toolpathResult, adaptiveParams, currentStage, exportedGcode, exportedFilename)

// G-code simulation
const { simRunning, onGcodeFileChange, simulateGcode } = useGcodeSimulation(
  gcodeFile,
  simResult,
  adaptiveParams,
  currentStage
)

// Preflight panel ref
const preflightPanelRef = ref<{ loadExternalFile: (file: File | null) => void } | null>(null)

// Calculator DXF generated handler
function onCalculatorDxfGenerated(file: File): void {
  calculatorStatus.value = `DXF generated: ${file.name}`
  currentStage.value = 1
  if (preflightPanelRef.value?.loadExternalFile) {
    preflightPanelRef.value.loadExternalFile(file)
  } else {
    dxfFile.value = file
  }
}

// Lifecycle
onMounted(async () => {
  await loadPosts()
})
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
