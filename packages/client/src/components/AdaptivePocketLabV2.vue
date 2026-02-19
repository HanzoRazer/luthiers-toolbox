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
import { ref, onMounted, watch, computed, reactive } from 'vue'
import {
  usePocketSettings,
  useAdaptiveFeedPresets,
  useToolpathRenderer,
  useToolpathExport,
  useEnergyMetrics,
  useLiveLearning,
} from './adaptive/composables'

import PreviewNcDrawer from './PreviewNcDrawer.vue'
import CompareAfModes from './CompareAfModes.vue'
import MachineEditorModal from './MachineEditorModal.vue'
import CompareMachines from './CompareMachines.vue'
import CompareSettings from './CompareSettings.vue'
import {
  MachineSelector,
  PostProcessorConfig,
  TrochoidSettings,
  JerkAwareSettings,
  HudOverlayControls,
  OptimizeForMachinePanel,
  ToolpathStatsPanel,
} from './adaptive'
import EnergyHeatPanel from './pocket/EnergyHeatPanel.vue'
import HeatTimeSeriesPanel from './pocket/HeatTimeSeriesPanel.vue'
import BottleneckMapPanel from './pocket/BottleneckMapPanel.vue'
import ToolParametersPanel from './pocket/ToolParametersPanel.vue'
import ActionButtonsBar from './pocket/ActionButtonsBar.vue'
import ExportConfigPanel from './pocket/ExportConfigPanel.vue'

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
const { ncOpen, ncText, jobName, exportModes, previewNc, exportProgram, batchExport } = useToolpathExport()

// Energy metrics composable
const {
  materialId,
  energyOut,
  heatTS,
  includeCsvLinks,
  chipPct,
  toolPct,
  workPct,
  energyPolyline,
  runEnergy,
  exportEnergyCsv,
  runHeatTS,
  exportBottleneckCsv,
  exportThermalReport,
  exportThermalBundle,
} = useEnergyMetrics()

// Live learning composable
const {
  adoptOverrides,
  sessionOverrideFactor,
  liveLearnApplied,
  measuredSeconds,
  patchBodyWithSessionOverride,
  logCurrentRun,
  trainOverrides,
  resetLiveLearning,
} = useLiveLearning()

// L.3 trochoid state
const useTrochoids = ref(false)
const trochoidRadius = ref(1.5)
const trochoidPitch = ref(3.0)

// Jerk-aware state
const jerkAware = ref(false)
const machineAccel = ref(800)
const machineJerk = ref(2000)
const cornerTol = ref(0.2)

// Machine profiles state
const machines = ref<any[]>([])
const machineId = ref<string>(localStorage.getItem('toolbox.machine') || 'Mach4_Router_4x8')
const selMachine = computed(() => machines.value.find((m) => m.id === machineId.value))
const postId = ref('GRBL')
const posts = ref(['GRBL', 'Mach4', 'LinuxCNC', 'PathPilot', 'MASSO'])

// Modal state
const compareOpen = ref(false)
const machineEditorOpen = ref(false)
const compareMachinesOpen = ref(false)
const compareSettingsOpen = ref(false)
const compareData = reactive({ baselineNc: '', optNc: '', tb: 0, topt: 0 })

// Optimizer state
const optFeedLo = ref(600)
const optFeedHi = ref(9000)
const optStpLo = ref(0.25)
const optStpHi = ref(0.85)
const optRpmLo = ref(8000)
const optRpmHi = ref(24000)
const optFlutes = ref(2)
const optChip = ref(0.05)
const optGridF = ref(6)
const optGridS = ref(6)
const optOut = ref<any>(null)
const enforceChip = ref(true)
const chipTol = ref(0.02)

// Toolpath state
const loops = ref([{ pts: [[0, 0], [100, 0], [100, 60], [0, 60]] }])
const moves = ref<any[]>([])
const stats = ref<any | null>(null)

// Watch machine change
watch(machineId, (v) => {
  localStorage.setItem('toolbox.machine', v || '')
  const m = selMachine.value
  if (m?.post_id_default) postId.value = m.post_id_default
})

// Auto-load preset when post changes
watch(postId, (pid) => pid && loadPresetForPost(pid))

function buildBaseExportBody() {
  return {
    loops: loops.value,
    units: units.value,
    tool_d: toolD.value,
    stepover: stepoverPct.value / 100.0,
    stepdown: stepdown.value,
    margin: margin.value,
    strategy: strategy.value,
    smoothing: 0.8,
    climb: climb.value,
    feed_xy: feedXY.value,
    safe_z: 5,
    z_rough: -stepdown.value,
    post_id: postId.value,
    use_trochoids: useTrochoids.value,
    trochoid_radius: trochoidRadius.value,
    trochoid_pitch: trochoidPitch.value,
    jerk_aware: jerkAware.value,
    machine_feed_xy: 1200,
    machine_rapid: 3000,
    machine_accel: machineAccel.value,
    machine_jerk: machineJerk.value,
    corner_tol_mm: cornerTol.value,
  }
}

function handleMakeDefault(mode: string) {
  afMode.value = mode as any
  savePresetForPost(postId.value)
  compareOpen.value = false
}

async function plan() {
  const baseBody = {
    ...buildBaseExportBody(),
    corner_radius_min: cornerRadiusMin.value,
    target_stepover: stepoverPct.value / 100.0,
    slowdown_feed_pct: slowdownFeedPct.value,
    machine_feed_xy: feedXY.value,
    machine_profile_id: machineId.value || undefined,
  }
  const body = patchBodyWithSessionOverride(baseBody)

  try {
    const r = await api('/api/cam/pocket/adaptive/plan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    const out = await r.json()
    moves.value = out.moves || []
    stats.value = out.stats || null
    overlays.value = out.overlays || []
    if (cv.value) draw(cv.value, moves.value, { minx: 0, miny: 0, maxx: 100, maxy: 60 })
  } catch (err) {
    console.error('Plan failed:', err)
    alert('Failed to plan pocket: ' + err)
  }
}

async function handlePreviewNc() {
  const body = patchBodyWithSessionOverride({
    ...buildBaseExportBody(),
    corner_radius_min: cornerRadiusMin.value,
    target_stepover: stepoverPct.value / 100.0,
    slowdown_feed_pct: slowdownFeedPct.value,
    adaptive_feed_override: buildAdaptiveOverride(),
  })
  await previewNc(body)
}

async function handleExport() {
  const body = patchBodyWithSessionOverride({
    ...buildBaseExportBody(),
    corner_radius_min: cornerRadiusMin.value,
    target_stepover: stepoverPct.value / 100.0,
    slowdown_feed_pct: slowdownFeedPct.value,
    adaptive_feed_override: buildAdaptiveOverride(),
    job_name: jobName.value || undefined,
  })
  await exportProgram(body, postId.value, strategy.value)
}

async function handleBatchExport() {
  const body = patchBodyWithSessionOverride(buildBaseExportBody())
  await batchExport(body, postId.value)
}

// Energy/heat handlers
async function handleRunEnergy() {
  if (!moves.value.length) await plan()
  await runEnergy(moves.value, toolD.value, stepoverPct.value, stepdown.value, jobName.value)
}

async function handleExportEnergyCsv() {
  await exportEnergyCsv(moves.value, toolD.value, stepoverPct.value, stepdown.value, jobName.value)
}

async function handleRunHeatTS() {
  await runHeatTS(moves.value, machineId.value, toolD.value, stepoverPct.value, stepdown.value)
}

async function handleExportBottleneckCsv() {
  await exportBottleneckCsv(moves.value, machineId.value, jobName.value)
}

async function handleExportThermalReport() {
  await exportThermalReport(moves.value, machineId.value, toolD.value, stepoverPct.value, stepdown.value)
}

async function handleExportThermalBundle() {
  await exportThermalBundle(moves.value, machineId.value, toolD.value, stepoverPct.value, stepdown.value)
}

// Live learning handlers
async function handleLogRun(actualSeconds?: number) {
  if (!moves.value.length) await plan()
  await logCurrentRun(
    moves.value,
    stats.value,
    machineId.value,
    materialId.value,
    toolD.value,
    stepoverPct.value,
    stepdown.value,
    feedXY.value,
    actualSeconds
  )
}

async function handleTrainOverrides() {
  await trainOverrides(machineId.value)
}

// Machine editor
async function onMachineSaved(id: string) {
  machineId.value = id
  try {
    const r = await api('/api/machine/profiles')
    machines.value = await r.json()
  } catch (e) {
    console.error('Failed to refresh machines:', e)
  }
}

// Optimizer
async function runWhatIf() {
  if (!moves.value.length) await plan()
  if (!moves.value.length || !machineId.value) {
    alert('Plan pocket and select machine first')
    return
  }

  try {
    const body: Record<string, any> = {
      moves: moves.value,
      machine_profile_id: machineId.value,
      z_total: -stepdown.value,
      stepdown: stepdown.value,
      safe_z: 5,
      bounds: { feed: [optFeedLo.value, optFeedHi.value], stepover: [optStpLo.value, optStpHi.value], rpm: [optRpmLo.value, optRpmHi.value] },
      tool: { flutes: optFlutes.value, chipload_target_mm: optChip.value },
      grid: [optGridF.value, optGridS.value],
    }
    if (enforceChip.value) body.tolerance_chip_mm = chipTol.value

    const r = await api('/api/cam/opt/what_if', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
    if (!r.ok) throw new Error(await r.text())
    optOut.value = await r.json()
  } catch (e) {
    alert('Optimization failed: ' + e)
  }
}

function applyRecommendation() {
  if (!optOut.value?.opt?.best) return
  const b = optOut.value.opt.best
  stepoverPct.value = Math.round(b.stepover * 100)
  feedXY.value = Math.round(b.feed_mm_min)
  alert(`Applied: Feed ${b.feed_mm_min} mm/min, Stepover ${(b.stepover * 100).toFixed(1)}%\nRe-plan to see updated toolpath.`)
}

async function openCompareSettings() {
  if (!optOut.value?.opt?.best) {
    alert('Run What-If optimizer first')
    return
  }
  try {
    const baseBody = { ...buildBaseExportBody(), corner_radius_min: cornerRadiusMin.value, target_stepover: stepoverPct.value / 100.0, slowdown_feed_pct: slowdownFeedPct.value, adaptive_feed_override: buildAdaptiveOverride(), job_name: jobName.value || undefined }
    const best = optOut.value.opt.best
    const recBody = { ...baseBody, stepover: best.stepover, feed_xy: best.feed_mm_min, target_stepover: best.stepover }

    const [baselineNc, baselinePlan, optNc, optPlan] = await Promise.all([
      api('/api/cam/pocket/adaptive/gcode', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(baseBody) }).then((r) => r.text()),
      api('/api/cam/pocket/adaptive/plan', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(baseBody) }).then((r) => r.json()),
      api('/api/cam/pocket/adaptive/gcode', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(recBody) }).then((r) => r.text()),
      api('/api/cam/pocket/adaptive/plan', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(recBody) }).then((r) => r.json()),
    ])

    compareData.baselineNc = baselineNc
    compareData.optNc = optNc
    compareData.tb = baselinePlan.stats?.time_s_jerk || baselinePlan.stats?.time_s_classic || 0
    compareData.topt = optPlan.stats?.time_s_jerk || optPlan.stats?.time_s_classic || 0
    compareSettingsOpen.value = true
  } catch (e) {
    alert('Compare settings failed: ' + e)
  }
}

onMounted(async () => {
  loadAfPrefs()
  try {
    const r = await api('/api/machine/profiles')
    machines.value = await r.json()
  } catch (e) {
    console.error('Failed to load machine profiles:', e)
  }
  setTimeout(() => cv.value && draw(cv.value, moves.value, { minx: 0, miny: 0, maxx: 100, maxy: 60 }), 100)
})
</script>
