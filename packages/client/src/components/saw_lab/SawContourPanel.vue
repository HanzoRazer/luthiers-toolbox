<template>
  <div :class="styles.sawContourPanel">
    <div :class="styles.panelHeader">
      <h2>Saw Contour Operation</h2>
      <p :class="styles.subtitle">
        Curved paths for rosettes and binding with radius validation
      </p>
    </div>

    <div :class="styles.panelContent">
      <!-- Left Column: Parameters -->
      <div :class="styles.parametersSection">
        <h3>Contour Parameters</h3>

        <!-- Blade Selection -->
        <div :class="styles.formGroup">
          <label>Saw Blade</label>
          <select
            v-model="selectedBladeId"
            @change="onBladeChange"
          >
            <option value="">
              Select blade...
            </option>
            <option
              v-for="blade in blades"
              :key="blade.blade_id"
              :value="blade.blade_id"
            >
              {{ blade.vendor }} {{ blade.model_code }} ({{ blade.diameter_mm }}mm)
            </option>
          </select>
          <div
            v-if="selectedBlade"
            :class="styles.bladeInfo"
          >
            Min radius: {{ (selectedBlade.diameter_mm / 2).toFixed(1) }}mm | Kerf: {{ selectedBlade.kerf_mm }}mm
          </div>
        </div>

        <!-- Machine & Material -->
        <div :class="styles.formGroup">
          <label>Machine Profile</label>
          <select v-model="machineProfile">
            <option value="bcam_router_2030">
              BCAM Router 2030
            </option>
            <option value="syil_x7">
              SYIL X7
            </option>
            <option value="tormach_1100mx">
              Tormach 1100MX
            </option>
          </select>
        </div>

        <div :class="styles.formGroup">
          <label>Material Family</label>
          <select v-model="materialFamily">
            <option value="hardwood">
              Hardwood
            </option>
            <option value="softwood">
              Softwood
            </option>
            <option value="plywood">
              Plywood
            </option>
            <option value="mdf">
              MDF
            </option>
          </select>
        </div>

        <!-- Contour Type -->
        <div :class="styles.formGroup">
          <label>Contour Type</label>
          <select
            v-model="contourType"
            @change="onContourTypeChange"
          >
            <option value="arc">
              Arc Segment
            </option>
            <option value="circle">
              Full Circle
            </option>
            <option value="rosette">
              Rosette Pattern
            </option>
          </select>
        </div>

        <!-- Arc Parameters -->
        <ContourArcParams
          v-if="contourType === 'arc'"
          v-model:centerX="centerX"
          v-model:centerY="centerY"
          v-model:radius="radius"
          v-model:startAngle="startAngle"
          v-model:endAngle="endAngle"
          :radius-validation="radiusValidation"
          @update:centerX="onParamChange"
          @update:centerY="onParamChange"
          @update:radius="onParamChange"
          @update:startAngle="onParamChange"
          @update:endAngle="onParamChange"
        />

        <!-- Circle Parameters -->
        <ContourCircleParams
          v-if="contourType === 'circle'"
          v-model:centerX="centerX"
          v-model:centerY="centerY"
          v-model:radius="radius"
          :radius-validation="radiusValidation"
          @update:centerX="onParamChange"
          @update:centerY="onParamChange"
          @update:radius="onParamChange"
        />

        <!-- Rosette Parameters -->
        <ContourRosetteParams
          v-if="contourType === 'rosette'"
          v-model:centerX="centerX"
          v-model:centerY="centerY"
          v-model:outerRadius="outerRadius"
          v-model:innerRadius="innerRadius"
          v-model:petalCount="petalCount"
          :radius-validation="radiusValidation"
          @update:centerX="onParamChange"
          @update:centerY="onParamChange"
          @update:outerRadius="onParamChange"
          @update:innerRadius="onParamChange"
          @update:petalCount="onParamChange"
        />

        <!-- Depth Parameters -->
        <div :class="styles.formGroup">
          <label>Total Depth (mm)</label>
          <input
            v-model.number="totalDepth"
            type="number"
            step="0.5"
            min="0.5"
          >
        </div>

        <div :class="styles.formGroup">
          <label>Depth Per Pass (mm)</label>
          <input
            v-model.number="depthPerPass"
            type="number"
            step="0.5"
            min="0.5"
          >
        </div>

        <!-- Feeds & Speeds -->
        <div :class="styles.formGroup">
          <label>RPM</label>
          <input
            v-model.number="rpm"
            type="number"
            step="100"
            min="2000"
            max="6000"
          >
        </div>

        <div :class="styles.formGroup">
          <label>Feed Rate (IPM)</label>
          <input
            v-model.number="feedIpm"
            type="number"
            step="5"
            min="10"
            max="300"
          >
        </div>

        <div :class="styles.formGroup">
          <label>Safe Z (mm)</label>
          <input
            v-model.number="safeZ"
            type="number"
            step="0.5"
            min="1"
          >
        </div>

        <!-- Actions -->
        <div :class="styles.actions">
          <button
            :disabled="!canValidate"
            :class="styles.btnPrimary"
            @click="validateContour"
          >
            Validate Contour
          </button>
          <button
            :disabled="!canMerge"
            :class="styles.btnSecondary"
            @click="mergeLearnedParams"
          >
            Apply Learned Overrides
          </button>
          <button
            :disabled="!isValid"
            :class="styles.btnPrimary"
            @click="generateGcode"
          >
            Generate G-code
          </button>
          <button
            :disabled="!hasGcode"
            :class="styles.btnSuccess"
            @click="sendToJobLog"
          >
            Send to JobLog
          </button>
        </div>
      </div>

      <!-- Right Column: Preview & Validation -->
      <div :class="styles.previewSection">
        <!-- Radius Validation -->
        <ContourRadiusValidation
          v-if="radiusValidation"
          :status="radiusValidation.status"
          :min-radius="radiusValidation.min_radius"
          :requested-radius="radiusValidation.requested_radius"
          :safety-margin="radiusValidation.safety_margin"
          :message="radiusValidation.message"
        />

        <!-- Validation Results -->
        <ContourValidationResults
          v-if="validationResult"
          :overall-result="validationResult.overall_result"
          :checks="validationResult.checks"
        />

        <!-- Learned Parameters -->
        <ContourLearnedParams
          v-if="mergedParams"
          :baseline-rpm="rpm"
          :baseline-feed-ipm="feedIpm"
          :baseline-depth-per-pass="depthPerPass"
          :merged-rpm="mergedParams.rpm"
          :merged-feed-ipm="mergedParams.feed_ipm"
          :merged-doc-mm="mergedParams.doc_mm"
        />

        <!-- Path Statistics -->
        <ContourPathStats
          v-if="pathStats"
          :path-length-mm="pathStats.length_mm"
          :depth-passes="depthPasses"
          :total-length-mm="totalLengthMm"
          :estimated-time-sec="estimatedTimeSec"
        />

        <!-- SVG Preview -->
        <ContourSvgPreview
          :svg-view-box="svgViewBox"
          :contour-path="contourPath"
          :center-x="centerX"
          :center-y="centerY"
          :contour-type="contourType"
          :radius="radius"
        />

        <!-- G-code Preview -->
        <div
          v-if="gcode"
          :class="styles.gcodePreview"
        >
          <h3>G-code Preview</h3>
          <pre :class="styles.gcodeText">{{ gcodePreview }}</pre>
          <button
            :class="styles.btnSecondary"
            @click="downloadGcode"
          >
            Download G-code
          </button>
        </div>

        <!-- Run Artifact Link -->
        <div
          v-if="runId"
          :class="styles.runArtifactLink"
        >
          <h3>Run Artifact</h3>
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
import { ref, computed, onMounted } from 'vue'
import { api } from '@/services/apiBase'
import styles from './SawContourPanel.module.css'
import ContourArcParams from './ContourArcParams.vue'
import ContourCircleParams from './ContourCircleParams.vue'
import ContourRosetteParams from './ContourRosetteParams.vue'
import ContourSvgPreview from './ContourSvgPreview.vue'
import ContourRadiusValidation from './ContourRadiusValidation.vue'
import ContourValidationResults from './ContourValidationResults.vue'
import ContourLearnedParams from './ContourLearnedParams.vue'
import ContourPathStats from './ContourPathStats.vue'
import {
  useSawContourPath,
  useSawContourGcode,
  useSawContourApi,
  useSawBladeRegistry,
  type SawBlade,
} from './composables'

// ============================================================================
// Composables
// ============================================================================

const {
  contourType,
  centerX,
  centerY,
  radius,
  startAngle,
  endAngle,
  outerRadius,
  innerRadius,
  petalCount,
  contourPath,
  pathStats,
  svgViewBox,
  updateContourPath,
  getMinRadius,
} = useSawContourPath()

const { blades, selectedBladeId, selectedBlade, loadBlades } = useSawBladeRegistry()

const {
  radiusValidation,
  validationResult,
  mergedParams,
  runId,
  validateRadius: doValidateRadius,
  validateContour: doValidateContour,
  mergeLearnedParams: doMergeLearnedParams,
  sendToJobLog: doSendToJobLog,
  clearValidation,
} = useSawContourApi()

// ============================================================================
// Local State
// ============================================================================

const machineProfile = ref('bcam_router_2030')
const materialFamily = ref('hardwood')
const totalDepth = ref(6)
const depthPerPass = ref(2)
const rpm = ref(3600)
const feedIpm = ref(100)
const safeZ = ref(5)

// ============================================================================
// G-code Composable (with getters)
// ============================================================================

const {
  gcode,
  hasGcode,
  depthPasses,
  totalLengthMm,
  estimatedTimeSec,
  gcodePreview,
  generateGcode: doGenerateGcode,
  downloadGcode,
} = useSawContourGcode(
  () => ({
    contourType: contourType.value,
    centerX: centerX.value,
    centerY: centerY.value,
    radius: radius.value,
  }),
  () => ({
    totalDepth: totalDepth.value,
    depthPerPass: depthPerPass.value,
    rpm: rpm.value,
    feedIpm: feedIpm.value,
    safeZ: safeZ.value,
  }),
  () => selectedBlade.value as SawBlade | null,
  () => pathStats.value.length_mm
)

// ============================================================================
// Computed
// ============================================================================

const canValidate = computed(() => selectedBladeId.value && radius.value > 0)
const canMerge = computed(() => selectedBladeId.value && machineProfile.value && materialFamily.value)
const isValid = computed(() => validationResult.value && validationResult.value.overall_result !== 'ERROR')

// ============================================================================
// Event Handlers
// ============================================================================

function onContourTypeChange() {
  updateContourPath()
}

function onParamChange() {
  updateContourPath()
  if (selectedBlade.value) {
    validateRadius()
  }
}

function onBladeChange() {
  clearValidation()
  updateContourPath()
  if (selectedBlade.value) {
    validateRadius()
  }
}

async function validateRadius() {
  if (!selectedBlade.value) return
  await doValidateRadius(selectedBlade.value.diameter_mm, getMinRadius())
}

async function validateContour() {
  if (!selectedBlade.value) return
  await doValidateContour(
    selectedBlade.value,
    materialFamily.value,
    rpm.value,
    feedIpm.value,
    depthPerPass.value
  )
}

async function mergeLearnedParams() {
  const laneKey = {
    tool_id: selectedBladeId.value,
    material: materialFamily.value,
    mode: 'contour',
    machine_profile: machineProfile.value,
  }
  const baseline = {
    rpm: rpm.value,
    feed_ipm: feedIpm.value,
    doc_mm: depthPerPass.value,
    safe_z: safeZ.value,
  }

  const merged = await doMergeLearnedParams(laneKey, baseline)
  if (merged) {
    rpm.value = merged.rpm
    feedIpm.value = merged.feed_ipm
    depthPerPass.value = merged.doc_mm
  }
}

function generateGcode() {
  doGenerateGcode()
}

async function sendToJobLog() {
  const payload = {
    op_type: 'contour',
    machine_profile: machineProfile.value,
    material_family: materialFamily.value,
    blade_id: selectedBladeId.value,
    safe_z: safeZ.value,
    depth_passes: depthPasses.value,
    total_length_mm: totalLengthMm.value,
    planned_rpm: rpm.value,
    planned_feed_ipm: feedIpm.value,
    planned_doc_mm: depthPerPass.value,
    operator_notes: `Contour: ${contourType.value}, radius ${radius.value}mm`,
  }

  const newRunId = await doSendToJobLog(payload)
  if (newRunId) {
    alert(`Contour sent to job log! Run ID: ${newRunId}`)
  } else {
    alert('Failed to send to job log')
  }
}

function formatCheckName(key: string): string {
  return key.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())
}

// ============================================================================
// Lifecycle
// ============================================================================

onMounted(() => {
  loadBlades()
  updateContourPath()
})
</script>
