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
        
        <AdaptiveParamsPanel
          :params="adaptiveParams"
          :can-generate="!!dxfFile"
          :running="adaptiveRunning"
          :toolpath-result="toolpathResult"
          :machine-limits="machineLimits"
          @update:params="handleParamsUpdate"
          @generate="sendToAdaptive"
        />
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
        
        <SimulatePanel
          :gcode-file="gcodeFile"
          :running="simRunning"
          :sim-result="simResult"
          @file-change="onGcodeFileChange"
          @simulate="simulateGcode"
        />
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
import AdaptiveParamsPanel from './bridge_lab/AdaptiveParamsPanel.vue'
import GcodeExportPanel from './bridge_lab/GcodeExportPanel.vue'
import SimulatePanel from './bridge_lab/SimulatePanel.vue'
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

// Params update handler for AdaptiveParamsPanel
function handleParamsUpdate(newParams: typeof adaptiveParams.value): void {
  Object.assign(adaptiveParams.value, newParams)
}

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

.mt-3 {
  margin-top: 1rem;
}
</style>
