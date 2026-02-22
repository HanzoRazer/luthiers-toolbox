<template>
  <div class="p-3 space-y-3 border rounded">
    <h3 class="text-lg font-semibold">
      Adaptive Pocket Lab
    </h3>

    <div class="grid md:grid-cols-3 gap-3">
      <div class="space-y-2">
        <!-- Tool Parameters (extracted component) -->
        <ToolParametersPanel
          v-model:tool-d="toolD"
          v-model:stepover-pct="stepoverPct"
          v-model:stepdown="stepdown"
          v-model:margin="margin"
          v-model:strategy="strategy"
          v-model:corner-radius-min="cornerRadiusMin"
          v-model:slowdown-feed-pct="slowdownFeedPct"
          v-model:climb="climb"
          v-model:feed-x-y="feedXY"
          v-model:units="units"
        />

        <!-- M.1 Machine Selector (extracted component) -->
        <MachineSelector
          v-model="machineId"
          :machines="machines"
          :disabled="false"
          @edit="openMachineEditor"
          @compare="compareMachinesFunc"
        />
        
        <!-- Post-Processor & Adaptive Feed (extracted component) -->
        <PostProcessorConfig
          v-model:post-id="postId"
          v-model:af-mode="afMode"
          v-model:af-inline-min-f="afInlineMinF"
          v-model:af-m-start="afMStart"
          v-model:af-m-end="afMEnd"
          :posts="posts"
          :disabled="false"
          @save-preset="savePresetForPost(postId)"
          @load-preset="loadPresetForPost(postId)"
          @reset-preset="resetPresetForPost(postId)"
        />
        
        <!-- Action Buttons (extracted component) -->
        <ActionButtonsBar
          :has-moves="moves.length > 0"
          :job-name="jobName"
          @plan="plan"
          @preview-nc="previewNc"
          @compare="openCompare"
          @export="exportProgram"
        />

        <!-- Export Config (extracted component) -->
        <ExportConfigPanel
          v-model:job-name="jobName"
          v-model:export-modes="exportModes"
          :has-moves="moves.length > 0"
          @batch-export="batchExport"
        />
        
        <!-- HUD Overlays (extracted component) -->
        <HudOverlayControls
          v-model:show-tight="showTight"
          v-model:show-slow="showSlow"
          v-model:show-fillets="showFillets"
          :disabled="false"
        />
        
        <!-- Trochoid Settings (extracted component) -->
        <TrochoidSettings
          v-model:use-trochoids="useTrochoids"
          v-model:trochoid-radius="trochoidRadius"
          v-model:trochoid-pitch="trochoidPitch"
          :disabled="false"
        />
        
        <!-- Jerk-Aware Settings (extracted component) -->
        <JerkAwareSettings
          v-model:jerk-aware="jerkAware"
          v-model:machine-accel="machineAccel"
          v-model:machine-jerk="machineJerk"
          v-model:corner-tol="cornerTol"
          :disabled="false"
        />
        
        <!-- M.2: Optimize for Machine (extracted component) -->
        <OptimizeForMachinePanel
          :opt-out="optOut"
          :has-toolpath="moves.length > 0"
          :has-machine="!!machineId"
          v-model:opt-feed-lo="optFeedLo"
          v-model:opt-feed-hi="optFeedHi"
          v-model:opt-stp-lo="optStpLo"
          v-model:opt-stp-hi="optStpHi"
          v-model:opt-rpm-lo="optRpmLo"
          v-model:opt-rpm-hi="optRpmHi"
          v-model:opt-flutes="optFlutes"
          v-model:opt-chip="optChip"
          v-model:opt-grid-f="optGridF"
          v-model:opt-grid-s="optGridS"
          v-model:enforce-chip="enforceChip"
          v-model:chip-tol="chipTol"
          :disabled="false"
          @run-what-if="runWhatIf"
          @compare-settings="openCompareSettings"
          @apply-recommendation="applyRecommendation"
        />

        <!-- M.3: Energy & Heat (extracted component) -->
        <EnergyHeatPanel
          v-model:material-id="materialId"
          :has-toolpath="moves.length > 0"
          :energy-out="energyOut"
          :chip-pct="chipPct"
          :tool-pct="toolPct"
          :work-pct="workPct"
          :energy-polyline="energyPolyline"
          @run-energy="runEnergy"
          @export-csv="exportEnergyCsv"
        />
      </div>

      <!-- M.3 Heat over Time Card (extracted component) -->
      <HeatTimeSeriesPanel
        :has-moves="!!planOut?.moves"
        :material-id="materialId"
        :profile-id="profileId"
        :heat-ts="heatTS"
        v-model:include-csv-links="includeCsvLinks"
        v-model:adopt-overrides="adoptOverrides"
        v-model:live-learn-applied="liveLearnApplied"
        v-model:measured-seconds="measuredSeconds"
        :session-override-factor="sessionOverrideFactor"
        @run-heat-ts="runHeatTS"
        @export-report="exportThermalReport"
        @export-bundle="exportThermalBundle"
        @log-run="logCurrentRun"
        @train-overrides="trainOverrides"
        @reset-live-learn="() => { liveLearnApplied = false; sessionOverrideFactor = null; measuredSeconds = null }"
      />

      <div class="md:col-span-2">
        <!-- M.1.1 Bottleneck Map Toggle (extracted component) -->
        <BottleneckMapPanel
          v-model:show-map="showBottleneckMap"
          :has-moves="!!planOut?.moves"
          :stats="(planOut?.stats as any)"
          @export-csv="exportBottleneckCsv"
        />

        <canvas
          ref="cv"
          class="w-full h-[420px] border rounded bg-gray-50"
        />
        <!-- Toolpath Stats (extracted component) -->
        <ToolpathStatsPanel :stats="(stats as any)" />
      </div>
    </div>
    
    <!-- NC Preview Drawer -->
    <PreviewNcDrawer
      :open="ncOpen"
      :gcode-text="ncText"
      @close="ncOpen = false"
    />
    <CompareAfModes
      v-model="compareOpen"
      :request-body="buildBaseExportBody()"
      @make-default="handleMakeDefault"
    />
  
    <!-- M.1.1 Machine Editor & Compare Modals -->
    <MachineEditorModal
      v-model="machineEditorOpen"
      :profile="selMachine"
      @saved="onMachineSaved"
    />
    <CompareMachines
      v-model="compareMachinesOpen"
      :machines="machines"
      :body="buildBaseExportBody()"
    />
  
    <!-- M.3 Compare Settings Modal -->
    <CompareSettings 
      v-model="compareSettingsOpen" 
      :baseline-nc="compareData.baselineNc" 
      :opt-nc="compareData.optNc" 
      :baseline-time="compareData.tb" 
      :opt-time="compareData.topt" 
    />
  </div>
</template>

<script setup lang="ts">
import { api } from '@/services/apiBase';
import { ref, onMounted, watch, computed } from 'vue'
import {
  usePocketSettings,
  useAdaptiveFeedPresets,
  useToolpathRenderer,
  useToolpathExport,
  useEnergyMetrics,
  useLiveLearning,
  usePocketPlanning,
  useMachineProfiles,
  useOptimizer,
  useRunLogging,
  useTrochoidSettings,
  useCompareModal,
  type Move,
} from './adaptive/composables'

import PreviewNcDrawer from './PreviewNcDrawer.vue'
import CompareAfModes from './CompareAfModes.vue'
import MachineEditorModal from './MachineEditorModal.vue'
import CompareMachines from './CompareMachines.vue'
import CompareSettings from './CompareSettings.vue'
import { MachineSelector, PostProcessorConfig, TrochoidSettings, JerkAwareSettings, HudOverlayControls, OptimizeForMachinePanel, ToolpathStatsPanel } from './adaptive'
import EnergyHeatPanel from './pocket/EnergyHeatPanel.vue'
import HeatTimeSeriesPanel from './pocket/HeatTimeSeriesPanel.vue'
import BottleneckMapPanel from './pocket/BottleneckMapPanel.vue'
import ToolParametersPanel from './pocket/ToolParametersPanel.vue'
import ActionButtonsBar from './pocket/ActionButtonsBar.vue'
import ExportConfigPanel from './pocket/ExportConfigPanel.vue'

const cv = ref<HTMLCanvasElement|null>(null)

// Pocket settings (from composable)
const {
  toolD,
  stepoverPct,
  stepdown,
  margin,
  strategy,
  climb,
  cornerRadiusMin,
  slowdownFeedPct,
  feedXY,
  units,
} = usePocketSettings()

// Adaptive feed presets (from composable)
const afPresets = useAdaptiveFeedPresets()
const {
  afMode,
  afInlineMinF,
  afMStart,
  afMEnd,
  savePresetForPost,
  loadPresetForPost,
  resetPresetForPost,
  buildAdaptiveOverride,
  loadPrefs: loadAfPrefs,
} = afPresets

// Toolpath renderer (from composable)
const renderer = useToolpathRenderer()
const { overlays, showTight, showSlow, showFillets, showBottleneckMap, draw: rendererDraw } = renderer

// Toolpath export (from composable)
const exporter = useToolpathExport()
const { ncOpen, ncText, jobName, exportModes, selectedModes } = exporter

// Energy metrics (from composable)
const energyMetrics = useEnergyMetrics()
const { 
  materialId, energyOut, heatTS, includeCsvLinks, chipPct, toolPct, workPct, energyPolyline,
  runEnergy: metricsRunEnergy,
  exportEnergyCsv: metricsExportEnergyCsv,
  runHeatTS: metricsRunHeatTS,
  exportBottleneckCsv: metricsExportBottleneckCsv,
  exportThermalReport: metricsExportThermalReport,
  exportThermalBundle: metricsExportThermalBundle,
} = energyMetrics

// Live learning (from composable)
const learning = useLiveLearning()
const { adoptOverrides, sessionOverrideFactor, liveLearnApplied, measuredSeconds, patchBodyWithSessionOverride, resetLiveLearning, computeLiveLearnFactor } = learning

// Machine profiles (from composable) - needs postId ref before definition
const postId = ref('GRBL')
const machineProfiles = useMachineProfiles({
  onPostIdChange: (pid) => { postId.value = pid }
})
const { 
  machines, machineId, selMachine, 
  machineEditorOpen, compareMachinesOpen,
  openMachineEditor, onMachineSaved, compareMachinesFunc, loadMachines 
} = machineProfiles

// Trochoid/jerk settings (from composable) - L.3
const trochoidSettings = useTrochoidSettings()
const {
  useTrochoids, trochoidRadius, trochoidPitch,
  jerkAware, machineAccel, machineJerk, cornerTol,
} = trochoidSettings

// Compare modal (from composable)
const compareModal = useCompareModal(
  { postId },
  { afMode, savePresetForPost }
)
const { compareOpen, openCompare, handleMakeDefault } = compareModal

// ==========================================================================
// Local State (remaining)
// ==========================================================================

// NOTE: compareSettingsOpen, compareData, enforceChip, chipTol, optFeedLo/Hi, optStpLo/Hi,
// optRpmLo/Hi, optFlutes, optChip, optGridF/S, optOut now from useOptimizer composable

// Pocket planning (from composable) - handles plan, preview, export
const pocketPlanning = usePocketPlanning(
  {
    // From usePocketSettings
    toolD,
    stepoverPct,
    stepdown,
    margin,
    strategy,
    cornerRadiusMin,
    slowdownFeedPct,
    climb,
    feedXY,
    units,
    // Local trochoid/jerk settings
    useTrochoids,
    trochoidRadius,
    trochoidPitch,
    jerkAware,
    machineAccel,
    machineJerk,
    cornerTol,
    // Post processor & machine
    postId,
    machineId,
    // Job name from toolpath export
    jobName,
  },
  {
    // Dependencies from other composables
    buildAdaptiveOverride,
    patchBodyWithSessionOverride,
    ncText,
    ncOpen,
    selectedModes,
    overlays,
    onPlanComplete: () => draw(),
  }
)
const { loops, moves, stats, plan, previewNc, exportProgram, batchExport, buildBaseExportBody } = pocketPlanning

// Optimizer (from composable) - M.2 What-If optimization
const optimizer = useOptimizer(
  {
    // From usePocketSettings
    toolD, stepoverPct, stepdown, feedXY, units,
    cornerRadiusMin, slowdownFeedPct, margin, strategy, climb,
    // Trochoid/jerk settings
    useTrochoids, trochoidRadius, trochoidPitch,
    jerkAware, machineAccel, machineJerk, cornerTol,
    // Post & machine
    postId, machineId,
    // Job name
    jobName,
  },
  {
    // Dependencies
    moves, loops, plan, buildAdaptiveOverride,
  }
)
const {
  optFeedLo, optFeedHi, optStpLo, optStpHi, optRpmLo, optRpmHi,
  optFlutes, optChip, optGridF, optGridS, optOut,
  enforceChip, chipTol,
  compareSettingsOpen, compareData,
  runWhatIf, applyRecommendation, openCompareSettings,
} = optimizer

// Run logging (from composable) - M.4 run logging & training
const runLogging = useRunLogging(
  {
    toolD, stepoverPct, stepdown, feedXY,
    machineId,
  },
  {
    moves, stats, plan,
    materialId,
    computeLiveLearnFactor, sessionOverrideFactor, liveLearnApplied,
  }
)
const { logCurrentRun, trainOverrides } = runLogging

const posts = ref<string[]>(['GRBL','Mach4','LinuxCNC','PathPilot','MASSO'])

// Computed aliases for template compatibility
const planOut = computed(() => ({
  moves: moves.value,
  stats: stats.value
}))
const profileId = computed(() => machineId.value)

// NOTE: AfPreset functions (savePresetForPost, loadPresetForPost, resetPresetForPost) 
// now from useAdaptiveFeedPresets composable

// Auto-load per-post preset when user changes post
watch(postId, (pid: string)=>{ if (!pid) return; loadPresetForPost(pid) })

// NOTE: buildBaseExportBody now from usePocketPlanning composable

// NOTE: openCompare, handleMakeDefault now from useCompareModal composable

// NOTE: selectedModes() now from useToolpathExport composable

// NOTE: batchExport now from usePocketPlanning composable

/** Wrapper for renderer.draw - delegates to useToolpathRenderer composable */
function draw() {
  if (!cv.value) return
  rendererDraw(cv.value, moves.value, { minx: 0, miny: 0, maxx: 100, maxy: 60 })
}

// NOTE: plan() now from usePocketPlanning composable

// NOTE: buildAdaptiveOverride() now from useAdaptiveFeedPresets composable

// NOTE: previewNc() now from usePocketPlanning composable

// NOTE: exportProgram() now from usePocketPlanning composable

// NOTE: loadAfPrefs() now from useAdaptiveFeedPresets composable

// NOTE: openMachineEditor, onMachineSaved, compareMachinesFunc now from useMachineProfiles composable

// NOTE: runWhatIf, applyRecommendation now from useOptimizer composable

// M.3: Compute energy & heat for current toolpath (delegates to useEnergyMetrics)
async function runEnergy() {
  if (!moves.value?.length) {
    await plan()
  }
  if (!moves.value?.length) return
  await metricsRunEnergy(moves.value, toolD.value, stepoverPct.value, stepdown.value, jobName.value)
}

// M.3: Export per-segment energy breakdown as CSV (delegates to useEnergyMetrics)
async function exportEnergyCsv() {
  if (!moves.value?.length) {
    await plan()
  }
  if (!moves.value?.length) return
  await metricsExportEnergyCsv(moves.value, toolD.value, stepoverPct.value, stepdown.value, jobName.value)
}

// M.3: Run heat timeseries (delegates to useEnergyMetrics)
async function runHeatTS() {
  if (!planOut.value?.moves) return
  await metricsRunHeatTS(planOut.value.moves, profileId.value, toolD.value, stepoverPct.value, stepdown.value)
}

// M.3: Export bottleneck CSV (delegates to useEnergyMetrics)
async function exportBottleneckCsv() {
  if (!planOut.value?.moves) return
  await metricsExportBottleneckCsv(planOut.value.moves, profileId.value, 'pocket')
}

// M.3: Export thermal report (delegates to useEnergyMetrics)
async function exportThermalReport() {
  if (!planOut.value?.moves) return
  await metricsExportThermalReport(planOut.value.moves, profileId.value, toolD.value, stepoverPct.value, stepdown.value)
}

// M.4: Export thermal bundle (delegates to useEnergyMetrics)
async function exportThermalBundle() {
  if (!planOut.value?.moves) return
  await metricsExportThermalBundle(planOut.value.moves, profileId.value, toolD.value, stepoverPct.value, stepdown.value)
}

// M.4: Compute live learn session factor from estimated vs actual time
// NOTE: computeLiveLearnFactor() and patchBodyWithSessionOverride() 
// now from useLiveLearning composable

// NOTE: logCurrentRun, trainOverrides now from useRunLogging composable

// NOTE: openCompareSettings now from useOptimizer composable

// NOTE: saveAfPrefs() now internal to useAdaptiveFeedPresets composable
// (auto-saves on change via watcher)

onMounted(async () => {
  loadAfPrefs()
  
  // M.1: Load machine profiles (from useMachineProfiles composable)
  await loadMachines()
  
  setTimeout(draw, 100)
})
</script>
