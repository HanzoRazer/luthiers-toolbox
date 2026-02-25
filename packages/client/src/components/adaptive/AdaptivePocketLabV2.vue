<template>
  <div class="p-3 space-y-3 border rounded">
    <h3 class="text-lg font-semibold">Adaptive Pocket Lab</h3>

    <div class="grid md:grid-cols-3 gap-3">
      <div class="space-y-2">
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

        <MachineSelector
          v-model="machineId"
          :machines="machines"
          :disabled="false"
          @edit="machineEditorOpen = true"
          @compare="compareMachinesOpen = true"
        />

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

        <ActionButtonsBar
          :has-moves="moves.length > 0"
          :job-name="jobName"
          @plan="plan"
          @preview-nc="handlePreviewNc"
          @compare="compareOpen = true"
          @export="handleExport"
        />

        <ExportConfigPanel
          v-model:job-name="jobName"
          v-model:export-modes="exportModes"
          :has-moves="moves.length > 0"
          @batch-export="handleBatchExport"
        />

        <HudOverlayControls
          v-model:show-tight="showTight"
          v-model:show-slow="showSlow"
          v-model:show-fillets="showFillets"
          :disabled="false"
        />

        <TrochoidSettings
          v-model:use-trochoids="useTrochoids"
          v-model:trochoid-radius="trochoidRadius"
          v-model:trochoid-pitch="trochoidPitch"
          :disabled="false"
        />

        <JerkAwareSettings
          v-model:jerk-aware="jerkAware"
          v-model:machine-accel="machineAccel"
          v-model:machine-jerk="machineJerk"
          v-model:corner-tol="cornerTol"
          :disabled="false"
        />

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

        <EnergyHeatPanel
          v-model:material-id="materialId"
          :has-toolpath="moves.length > 0"
          :energy-out="energyOut"
          :chip-pct="chipPct"
          :tool-pct="toolPct"
          :work-pct="workPct"
          :energy-polyline="energyPolyline"
          @run-energy="handleRunEnergy"
          @export-csv="handleExportEnergyCsv"
        />
      </div>

      <HeatTimeSeriesPanel
        :has-moves="moves.length > 0"
        :material-id="materialId"
        :profile-id="machineId"
        :heat-ts="heatTS"
        v-model:include-csv-links="includeCsvLinks"
        v-model:adopt-overrides="adoptOverrides"
        v-model:live-learn-applied="liveLearnApplied"
        v-model:measured-seconds="measuredSeconds"
        :session-override-factor="sessionOverrideFactor"
        @run-heat-ts="handleRunHeatTS"
        @export-report="handleExportThermalReport"
        @export-bundle="handleExportThermalBundle"
        @log-run="handleLogRun"
        @train-overrides="handleTrainOverrides"
        @reset-live-learn="resetLiveLearning"
      />

      <div class="md:col-span-2">
        <BottleneckMapPanel
          v-model:show-map="showBottleneckMap"
          :has-moves="moves.length > 0"
          :stats="stats"
          @export-csv="handleExportBottleneckCsv"
        />

        <canvas ref="cv" class="w-full h-[420px] border rounded bg-gray-50" />
        <ToolpathStatsPanel :stats="stats" />
      </div>
    </div>

    <PreviewNcDrawer :open="ncOpen" :gcode-text="ncText" @close="ncOpen = false" />
    <CompareAfModes v-model="compareOpen" :request-body="buildBaseExportBody()" @make-default="handleMakeDefault" />
    <MachineEditorModal v-model="machineEditorOpen" :profile="selMachine" @saved="onMachineSaved" />
    <CompareMachines v-model="compareMachinesOpen" :machines="machines" :body="buildBaseExportBody()" />
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
import { api } from '@/services/apiBase'
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
} from './composables'

import PreviewNcDrawer from '@/components/PreviewNcDrawer.vue'
import CompareAfModes from '@/components/compare/CompareAfModes.vue'
import MachineEditorModal from '@/components/MachineEditorModal.vue'
import CompareMachines from '@/components/compare/CompareMachines.vue'
import CompareSettings from '@/components/compare/CompareSettings.vue'
import {
  MachineSelector,
  PostProcessorConfig,
  TrochoidSettings,
  JerkAwareSettings,
  HudOverlayControls,
  OptimizeForMachinePanel,
  ToolpathStatsPanel,
} from '.'
import EnergyHeatPanel from '@/components/pocket/EnergyHeatPanel.vue'
import HeatTimeSeriesPanel from '@/components/pocket/HeatTimeSeriesPanel.vue'
import BottleneckMapPanel from '@/components/pocket/BottleneckMapPanel.vue'
import ToolParametersPanel from '@/components/pocket/ToolParametersPanel.vue'
import ActionButtonsBar from '@/components/pocket/ActionButtonsBar.vue'
import ExportConfigPanel from '@/components/pocket/ExportConfigPanel.vue'

// Canvas ref
const cv = ref<HTMLCanvasElement | null>(null)

// Pocket settings composable
const { toolD, stepoverPct, stepdown, margin, strategy, climb, cornerRadiusMin, slowdownFeedPct, feedXY, units } =
  usePocketSettings()

// Adaptive feed presets composable
const {
  afMode,
  afInlineMinF,
  afMStart,
  afMEnd,
  savePresetForPost,
  loadPresetForPost,
  resetPresetForPost,
  loadPrefs: loadAfPrefs,
  buildAdaptiveOverride,
} = useAdaptiveFeedPresets()

// Toolpath renderer composable
const { overlays, showTight, showSlow, showFillets, showBottleneckMap, draw } = useToolpathRenderer()

// Toolpath export composable
const exporter = useToolpathExport()
const { ncOpen, ncText, jobName, exportModes, selectedModes } = exporter

// Energy metrics composable
const energyMetrics = useEnergyMetrics()
const {
  materialId,
  energyOut,
  heatTS,
  includeCsvLinks,
  chipPct,
  toolPct,
  workPct,
  energyPolyline,
  runEnergy: metricsRunEnergy,
  exportEnergyCsv: metricsExportEnergyCsv,
  runHeatTS: metricsRunHeatTS,
  exportBottleneckCsv: metricsExportBottleneckCsv,
  exportThermalReport: metricsExportThermalReport,
  exportThermalBundle: metricsExportThermalBundle,
} = energyMetrics

// Live learning composable
const learning = useLiveLearning()
const {
  adoptOverrides,
  sessionOverrideFactor,
  liveLearnApplied,
  measuredSeconds,
  patchBodyWithSessionOverride,
  resetLiveLearning,
  computeLiveLearnFactor,
} = learning

// Trochoid & jerk settings composable
const { useTrochoids, trochoidRadius, trochoidPitch, jerkAware, machineAccel, machineJerk, cornerTol } =
  useTrochoidSettings()

// Machine profiles composable
const postId = ref('GRBL')
const posts = ref(['GRBL', 'Mach4', 'LinuxCNC', 'PathPilot', 'MASSO'])
const { machines, machineId, selMachine, machineEditorOpen, compareMachinesOpen, onMachineSaved, loadMachines } =
  useMachineProfiles({ onPostIdChange: (pid) => { postId.value = pid } })

// Compare modal composable
const { compareOpen, handleMakeDefault } = useCompareModal({ postId }, { afMode, savePresetForPost })

// Pocket planning composable (plan + export handlers)
const pocketPlanning = usePocketPlanning(
  {
    toolD, stepoverPct, stepdown, margin, strategy, cornerRadiusMin,
    slowdownFeedPct, climb, feedXY, units,
    useTrochoids, trochoidRadius, trochoidPitch,
    jerkAware, machineAccel, machineJerk, cornerTol,
    postId, machineId, jobName,
  },
  {
    buildAdaptiveOverride,
    patchBodyWithSessionOverride,
    ncText, ncOpen,
    selectedModes,
    overlays,
    onPlanComplete: () => cv.value && draw(cv.value, moves.value, { minx: 0, miny: 0, maxx: 100, maxy: 60 }),
  }
)
const { loops, moves, stats, plan, previewNc, exportProgram, batchExport, buildBaseExportBody } = pocketPlanning

// Optimizer composable
const optimizer = useOptimizer(
  {
    toolD, stepoverPct, stepdown, feedXY, units,
    cornerRadiusMin, slowdownFeedPct, margin, strategy, climb,
    useTrochoids, trochoidRadius, trochoidPitch,
    jerkAware, machineAccel, machineJerk, cornerTol,
    postId, machineId, jobName,
  },
  { moves, loops, plan, buildAdaptiveOverride }
)
const {
  optFeedLo, optFeedHi, optStpLo, optStpHi, optRpmLo, optRpmHi,
  optFlutes, optChip, optGridF, optGridS, optOut,
  enforceChip, chipTol, compareSettingsOpen, compareData,
  runWhatIf, applyRecommendation, openCompareSettings,
} = optimizer

// Run logging composable
const { logCurrentRun, trainOverrides } = useRunLogging(
  { toolD, stepoverPct, stepdown, feedXY, machineId },
  { moves, stats, plan, materialId, computeLiveLearnFactor, sessionOverrideFactor, liveLearnApplied }
)

// Auto-load preset when post changes
watch(postId, (pid) => pid && loadPresetForPost(pid))

// Energy/heat thin handlers — delegate to composable methods with local state
async function handleRunEnergy() {
  if (!moves.value.length) await plan()
  await metricsRunEnergy(moves.value, toolD.value, stepoverPct.value, stepdown.value, jobName.value)
}
async function handleExportEnergyCsv() {
  await metricsExportEnergyCsv(moves.value, toolD.value, stepoverPct.value, stepdown.value, jobName.value)
}
async function handleRunHeatTS() {
  await metricsRunHeatTS(moves.value, machineId.value, toolD.value, stepoverPct.value, stepdown.value)
}
async function handleExportBottleneckCsv() {
  await metricsExportBottleneckCsv(moves.value, machineId.value, jobName.value)
}
async function handleExportThermalReport() {
  await metricsExportThermalReport(moves.value, machineId.value, toolD.value, stepoverPct.value, stepdown.value)
}
async function handleExportThermalBundle() {
  await metricsExportThermalBundle(moves.value, machineId.value, toolD.value, stepoverPct.value, stepdown.value)
}

// Handlers — plan/export/logging use composable-provided functions directly
function handlePreviewNc() { previewNc() }
function handleExport() { exportProgram(postId.value, strategy.value) }
function handleBatchExport() { batchExport(postId.value) }
async function handleLogRun(actualSeconds?: number) {
  if (!moves.value.length) await plan()
  await logCurrentRun(actualSeconds)
}
async function handleTrainOverrides() { await trainOverrides() }

onMounted(async () => {
  loadAfPrefs()
  await loadMachines()
  setTimeout(() => cv.value && draw(cv.value, moves.value, { minx: 0, miny: 0, maxx: 100, maxy: 60 }), 100)
})
</script>
