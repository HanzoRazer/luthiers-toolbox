<template>
  <div :class="styles.sawBatchPanel">
    <div :class="styles.panelHeader">
      <h2>Saw Batch Operation</h2>
      <p :class="styles.subtitle">
        Schedule multiple slices with batch-level optimization
      </p>
    </div>

    <div :class="styles.panelContent">
      <!-- Left Column: Batch Setup -->
      <BatchSetupSection
        :blades="blades"
        v-model:selected-blade-id="selectedBladeId"
        v-model:machine-profile="machineProfile"
        v-model:material-family="materialFamily"
        v-model:num-slices="numSlices"
        v-model:slice-spacing="sliceSpacing"
        v-model:slice-length="sliceLength"
        v-model:start-x="startX"
        v-model:start-y="startY"
        v-model:orientation="orientation"
        v-model:total-depth="totalDepth"
        v-model:depth-per-pass="depthPerPass"
        v-model:rpm="rpm"
        v-model:feed-ipm="feedIpm"
        v-model:safe-z="safeZ"
        :can-validate="canValidate"
        :can-merge="canMerge"
        :is-valid="isValid"
        :has-gcode="hasGcode"
        @validate="validateBatch"
        @merge-learned-params="mergeLearnedParams"
        @generate-gcode="generateBatchGcode"
        @send-to-job-log="sendToJobLog"
      />

      <!-- Right Column: Batch Preview & Stats -->
      <div :class="styles.batchPreviewSection">
        <!-- Batch Statistics -->
        <div :class="styles.batchStats">
          <h3 :class="styles.sectionTitle">Batch Statistics</h3>
          <div :class="styles.statsGrid">
            <div :class="styles.statCard">
              <div :class="styles.statLabel">
                Total Slices
              </div>
              <div :class="styles.statValue">
                {{ numSlices }}
              </div>
            </div>
            <div :class="styles.statCard">
              <div :class="styles.statLabel">
                Total Length
              </div>
              <div :class="styles.statValue">
                {{ totalLengthMm.toFixed(0) }} mm
              </div>
            </div>
            <div :class="styles.statCard">
              <div :class="styles.statLabel">
                Total Passes
              </div>
              <div :class="styles.statValue">
                {{ totalPasses }}
              </div>
            </div>
            <div :class="styles.statCard">
              <div :class="styles.statLabel">
                Est. Time
              </div>
              <div :class="styles.statValue">
                {{ formatTime(estimatedTimeSec) }}
              </div>
            </div>
            <div :class="styles.statCard">
              <div :class="styles.statLabel">
                Total Volume
              </div>
              <div :class="styles.statValue">
                {{ totalVolumeMm3.toFixed(0) }} mm³
              </div>
            </div>
            <div :class="styles.statCard">
              <div :class="styles.statLabel">
                Kerf Loss
              </div>
              <div :class="styles.statValue">
                {{ kerfLossMm3.toFixed(0) }} mm³
              </div>
            </div>
          </div>
        </div>

        <!-- Validation Results -->
        <div
          v-if="validationResult"
          :class="styles.validationResults"
        >
          <h3 :class="styles.sectionTitle">Validation Results</h3>
          <div :class="validationResult.overall_result.toLowerCase() === 'ok' ? styles.validationBadgeOk : validationResult.overall_result.toLowerCase() === 'warn' ? styles.validationBadgeWarn : styles.validationBadgeError">
            {{ validationResult.overall_result }}
          </div>
          <div :class="styles.validationSummary">
            {{ validationResult.checks ? Object.keys(validationResult.checks).length : 0 }} checks performed
          </div>
        </div>

        <!-- Learned Parameters -->
        <LearnedParamsDisplay
          v-if="mergedParams"
          :merged-params="mergedParams"
          :baseline-rpm="rpm"
          :baseline-feed-ipm="feedIpm"
          :baseline-depth-per-pass="depthPerPass"
        />

        <!-- SVG Preview -->
        <SvgPreview
          :svg-view-box="svgViewBox"
          :slice-paths="slicePaths"
          :selected-blade="selectedBlade"
        />

        <!-- G-code Preview -->
        <div
          v-if="gcode"
          :class="styles.gcodePreview"
        >
          <h3 :class="styles.sectionTitle">G-code Preview (First 20 / Last 5 lines)</h3>
          <pre :class="styles.gcodeText">{{ gcodePreview }}</pre>
          <button
            :class="styles.btnSecondary"
            @click="downloadGcode"
          >
            Download Batch G-code
          </button>
        </div>

        <!-- Run Artifact Link -->
        <div
          v-if="runId"
          :class="styles.runArtifactLink"
        >
          <h3 :class="styles.sectionTitle">Run Artifact</h3>
          <p>Job logged with Run ID: <code>{{ runId }}</code></p>
          <router-link
            :to="`/rmos/runs?run_id=${runId}`"
            :class="styles.btnPrimary"
          >
            View Run Artifact
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * SawBatchPanel.vue - Batch saw operations with optimization
 *
 * REFACTORED: Uses composables for cleaner separation:
 * - useSawBladeRegistry: Blade loading and selection
 * - useSawBatchStats: Batch statistics and slice path generation
 * - useSawBatchGcode: G-code generation and download
 */
import { api } from '@/services/apiBase'
import { ref, computed, onMounted } from 'vue'
import {
  useSawBladeRegistry,
  useSawBatchStats,
  useSawBatchGcode,
} from './composables'
import styles from './SawBatchPanel.module.css'
import BatchSetupSection from './saw_batch_panel/BatchSetupSection.vue'
import SvgPreview from './saw_batch_panel/SvgPreview.vue'
import LearnedParamsDisplay from './saw_batch_panel/LearnedParamsDisplay.vue'

// ============================================================================
// Form State
// ============================================================================

const machineProfile = ref<string>('bcam_router_2030')
const materialFamily = ref<string>('hardwood')

const numSlices = ref<number>(10)
const sliceSpacing = ref<number>(25)
const sliceLength = ref<number>(150)
const startX = ref<number>(0)
const startY = ref<number>(0)
const orientation = ref<'horizontal' | 'vertical'>('horizontal')

const totalDepth = ref<number>(12)
const depthPerPass = ref<number>(3)

const rpm = ref<number>(3600)
const feedIpm = ref<number>(120)
const safeZ = ref<number>(5)

const validationResult = ref<any>(null)
const mergedParams = ref<any>(null)
const runId = ref<string>('')

// ============================================================================
// Composables
// ============================================================================

// Blade registry
const bladeRegistry = useSawBladeRegistry(() => {
  validationResult.value = null
  mergedParams.value = null
})

const { blades, selectedBladeId, selectedBlade, loadBlades, onBladeChange } = bladeRegistry

// Batch statistics
const batchStats = useSawBatchStats(
  () => ({
    numSlices: numSlices.value,
    sliceSpacing: sliceSpacing.value,
    sliceLength: sliceLength.value,
    startX: startX.value,
    startY: startY.value,
    orientation: orientation.value,
    totalDepth: totalDepth.value,
    depthPerPass: depthPerPass.value,
    feedIpm: feedIpm.value,
  }),
  () => selectedBlade.value
)

const {
  depthPasses,
  totalPasses,
  totalLengthMm,
  estimatedTimeSec,
  totalVolumeMm3,
  kerfLossMm3,
  slicePaths,
  svgViewBox,
  formatTime,
} = batchStats

// G-code generation
const gcodeGen = useSawBatchGcode(
  () => ({
    numSlices: numSlices.value,
    sliceLength: sliceLength.value,
    sliceSpacing: sliceSpacing.value,
    totalDepth: totalDepth.value,
    depthPerPass: depthPerPass.value,
    feedIpm: feedIpm.value,
    safeZ: safeZ.value,
  }),
  () => selectedBlade.value,
  () => materialFamily.value,
  () => slicePaths.value,
  () => depthPasses.value,
  () => totalLengthMm.value
)

const { gcode, hasGcode, gcodePreview, generateBatchGcode, downloadGcode } = gcodeGen

// ============================================================================
// Computed (validation gates)
// ============================================================================

const canValidate = computed(() => {
  return !!(selectedBladeId.value && numSlices.value > 0)
})

const canMerge = computed(() => {
  return !!(selectedBladeId.value && machineProfile.value && materialFamily.value)
})

const isValid = computed(() => {
  return validationResult.value && validationResult.value.overall_result !== 'ERROR'
})

// ============================================================================
// API Functions
// ============================================================================

async function validateBatch() {
  if (!selectedBlade.value) return

  const payload = {
    blade: selectedBlade.value,
    op_type: 'batch',
    material_family: materialFamily.value,
    planned_rpm: rpm.value,
    planned_feed_ipm: feedIpm.value,
    planned_doc_mm: depthPerPass.value,
  }

  try {
    const response = await api('/api/saw/validate/operation', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    validationResult.value = await response.json()
  } catch (err) {
    console.error('Validation failed:', err)
  }
}

async function mergeLearnedParams() {
  const laneKey = {
    tool_id: selectedBladeId.value,
    material: materialFamily.value,
    mode: 'batch',
    machine_profile: machineProfile.value,
  }

  const baseline = {
    rpm: rpm.value,
    feed_ipm: feedIpm.value,
    doc_mm: depthPerPass.value,
    safe_z: safeZ.value,
  }

  try {
    const response = await api('/api/feeds/learned/merge', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lane_key: laneKey, baseline }),
    })
    const result = await response.json()
    mergedParams.value = result.merged

    rpm.value = result.merged.rpm
    feedIpm.value = result.merged.feed_ipm
    depthPerPass.value = result.merged.doc_mm
  } catch (err) {
    console.error('Failed to merge learned params:', err)
  }
}

async function sendToJobLog() {
  const payload = {
    op_type: 'batch',
    machine_profile: machineProfile.value,
    material_family: materialFamily.value,
    blade_id: selectedBladeId.value,
    safe_z: safeZ.value,
    depth_passes: depthPasses.value,
    total_length_mm: totalLengthMm.value,
    planned_rpm: rpm.value,
    planned_feed_ipm: feedIpm.value,
    planned_doc_mm: depthPerPass.value,
    operator_notes: `Batch: ${numSlices.value} slices, ${sliceLength.value}mm each, ${sliceSpacing.value}mm spacing`,
  }

  try {
    const response = await api('/api/saw/joblog/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    const run = await response.json()
    runId.value = run.run_id

    alert(
      `Batch sent to job log! Run ID: ${run.run_id}\n\nSlices: ${numSlices.value}\nTotal time: ${formatTime(estimatedTimeSec.value)}`
    )
  } catch (err) {
    console.error('Failed to send to job log:', err)
    alert('Failed to send to job log')
  }
}

// ============================================================================
// Lifecycle
// ============================================================================

onMounted(() => {
  loadBlades()
})
</script>
