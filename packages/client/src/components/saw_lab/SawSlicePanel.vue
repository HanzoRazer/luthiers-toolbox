<template>
  <div :class="styles.sawSlicePanel">
    <div :class="styles.panelHeader">
      <h2>Saw Slice Operation</h2>
      <p :class="styles.subtitle">
        Kerf-aware straight cuts with multi-pass depth control
      </p>
    </div>

    <div :class="styles.panelContent">
      <!-- Left Column: Parameters -->
      <div :class="styles.parametersSection">
        <h3>Cut Parameters</h3>

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
              {{ blade.vendor }} {{ blade.model_code }} ({{
                blade.diameter_mm
              }}mm)
            </option>
          </select>
          <div
            v-if="selectedBlade"
            :class="styles.bladeInfo"
          >
            Kerf: {{ selectedBlade.kerf_mm }}mm | Teeth:
            {{ selectedBlade.teeth }}
          </div>
        </div>

        <!-- Machine Profile -->
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

        <!-- Material -->
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

        <!-- Geometry -->
        <div :class="styles.formGroup">
          <label>Start X (mm)</label>
          <input
            v-model.number="startX"
            type="number"
            step="0.1"
          >
        </div>

        <div :class="styles.formGroup">
          <label>Start Y (mm)</label>
          <input
            v-model.number="startY"
            type="number"
            step="0.1"
          >
        </div>

        <div :class="styles.formGroup">
          <label>End X (mm)</label>
          <input
            v-model.number="endX"
            type="number"
            step="0.1"
          >
        </div>

        <div :class="styles.formGroup">
          <label>End Y (mm)</label>
          <input
            v-model.number="endY"
            type="number"
            step="0.1"
          >
        </div>

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
            @click="validateOperation"
          >
            Validate Parameters
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
        <!-- Validation Results -->
        <div
          v-if="validationResult"
          :class="styles.validationResults"
        >
          <h3>Validation Results</h3>
          <div
            :class="validationResult.overall_result.toLowerCase() === 'ok' ? styles.validationBadgeOk : validationResult.overall_result.toLowerCase() === 'warn' ? styles.validationBadgeWarn : styles.validationBadgeError"
          >
            {{ validationResult.overall_result }}
          </div>
          <div :class="styles.validationChecks">
            <div
              v-for="(check, key) in validationResult.checks"
              :key="key"
              :class="check.result.toLowerCase() === 'ok' ? styles.checkItemOk : check.result.toLowerCase() === 'warn' ? styles.checkItemWarn : styles.checkItemError"
            >
              <span :class="styles.checkIcon">{{
                check.result === "OK"
                  ? "✓"
                  : check.result === "WARN"
                    ? "⚠"
                    : "✗"
              }}</span>
              <span :class="styles.checkName">{{ formatCheckName(String(key)) }}</span>
              <span :class="styles.checkMessage">{{ check.message }}</span>
            </div>
          </div>
        </div>

        <!-- Learned Parameters -->
        <div
          v-if="mergedParams"
          :class="styles.learnedParams"
        >
          <h3>Learned Parameters Applied</h3>
          <div :class="styles.paramComparison">
            <div :class="styles.paramRow">
              <span :class="styles.paramLabel">RPM:</span>
              <span :class="styles.paramBaseline">{{ rpm }}</span>
              <span :class="styles.paramArrow">→</span>
              <span :class="styles.paramMerged">{{
                mergedParams.rpm?.toFixed(0) || rpm
              }}</span>
            </div>
            <div :class="styles.paramRow">
              <span :class="styles.paramLabel">Feed:</span>
              <span :class="styles.paramBaseline">{{ feedIpm }}</span>
              <span :class="styles.paramArrow">→</span>
              <span :class="styles.paramMerged">{{
                mergedParams.feed_ipm?.toFixed(1) || feedIpm
              }}</span>
            </div>
            <div :class="styles.paramRow">
              <span :class="styles.paramLabel">DOC:</span>
              <span :class="styles.paramBaseline">{{ depthPerPass }}</span>
              <span :class="styles.paramArrow">→</span>
              <span :class="styles.paramMerged">{{
                mergedParams.doc_mm?.toFixed(1) || depthPerPass
              }}</span>
            </div>
          </div>
          <div :class="styles.laneInfo">
            Lane scale: {{ mergedParams.lane_scale?.toFixed(2) || "1.00" }}
          </div>
        </div>

        <!-- G-code Preview -->
        <div
          v-if="gcode"
          :class="styles.gcodePreview"
        >
          <h3>G-code Preview</h3>
          <div :class="styles.previewStats">
            <div :class="styles.stat">
              <span :class="styles.statLabel">Total Length:</span>
              <span :class="styles.statValue">{{ totalLengthMm.toFixed(1) }} mm</span>
            </div>
            <div :class="styles.stat">
              <span :class="styles.statLabel">Depth Passes:</span>
              <span :class="styles.statValue">{{ depthPasses }}</span>
            </div>
            <div :class="styles.stat">
              <span :class="styles.statLabel">Est. Time:</span>
              <span :class="styles.statValue">{{ estimatedTimeSec.toFixed(0) }}s</span>
            </div>
          </div>
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
          <p>
            Job logged with Run ID: <code>{{ runId }}</code>
          </p>
          <router-link
            :to="`/rmos/runs?run_id=${runId}`"
            :class="styles.btnPrimary"
          >
            View Run Artifact
          </router-link>
        </div>

        <!-- SVG Preview -->
        <div :class="styles.svgPreview">
          <h3>Path Preview</h3>
          <svg
            :viewBox="svgViewBox"
            width="400"
            height="300"
            :class="styles.previewCanvas"
          >
            <!-- Grid -->
            <defs>
              <pattern
                id="grid"
                width="10"
                height="10"
                patternUnits="userSpaceOnUse"
              >
                <path
                  d="M 10 0 L 0 0 0 10"
                  fill="none"
                  stroke="#e0e0e0"
                  stroke-width="0.5"
                />
              </pattern>
            </defs>
            <rect
              width="100%"
              height="100%"
              fill="url(#grid)"
            />

            <!-- Cut path -->
            <line
              v-if="startX !== null && endX !== null"
              :x1="startX"
              :y1="startY"
              :x2="endX"
              :y2="endY"
              stroke="#2196F3"
              stroke-width="2"
            />

            <!-- Kerf width visualization -->
            <line
              v-if="startX !== null && endX !== null && selectedBlade"
              :x1="startX"
              :y1="startY + selectedBlade.kerf_mm / 2"
              :x2="endX"
              :y2="endY + selectedBlade.kerf_mm / 2"
              stroke="#FF9800"
              stroke-width="1"
              stroke-dasharray="2,2"
            />
            <line
              v-if="startX !== null && endX !== null && selectedBlade"
              :x1="startX"
              :y1="startY - selectedBlade.kerf_mm / 2"
              :x2="endX"
              :y2="endY - selectedBlade.kerf_mm / 2"
              stroke="#FF9800"
              stroke-width="1"
              stroke-dasharray="2,2"
            />

            <!-- Start/End markers -->
            <circle
              v-if="startX !== null"
              :cx="startX"
              :cy="startY"
              r="2"
              fill="#4CAF50"
            />
            <circle
              v-if="endX !== null"
              :cx="endX"
              :cy="endY"
              r="2"
              fill="#F44336"
            />
          </svg>
          <div :class="styles.legend">
            <span><span
              :class="styles.colorBox"
              style="background: #2196f3"
            /> Cut
              path</span>
            <span><span
              :class="styles.colorBox"
              style="background: #ff9800"
            /> Kerf
              boundary</span>
            <span><span
              :class="styles.colorBox"
              style="background: #4caf50"
            />
              Start</span>
            <span><span
              :class="styles.colorBox"
              style="background: #f44336"
            />
              End</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * SawSlicePanel.vue - Kerf-aware straight cuts with multi-pass depth control
 *
 * REFACTORED: Uses composables for cleaner separation:
 * - useSawBladeRegistry: Blade loading and selection
 * - useSawSliceGcode: G-code generation, preview, statistics
 * - useSawSliceApi: Validation, learned params, job log
 */
import { ref, computed, onMounted } from 'vue'
import {
  useSawBladeRegistry,
  useSawSliceGcode,
  useSawSliceApi,
} from './composables'
import styles from './SawSlicePanel.module.css'

// ============================================================================
// Form State (not extracted - tightly coupled to template)
// ============================================================================

const machineProfile = ref<string>('bcam_router_2030')
const materialFamily = ref<string>('hardwood')

const startX = ref<number>(0)
const startY = ref<number>(0)
const endX = ref<number>(100)
const endY = ref<number>(0)

const totalDepth = ref<number>(12)
const depthPerPass = ref<number>(3)

const rpm = ref<number>(3600)
const feedIpm = ref<number>(120)
const safeZ = ref<number>(5)

// ============================================================================
// Composables
// ============================================================================

// Blade registry
const bladeRegistry = useSawBladeRegistry(() => {
  // Clear validation when blade changes
  sliceApi.clearValidation()
})

// Convenience aliases
const { blades, selectedBladeId, selectedBlade, loadBlades, onBladeChange } = bladeRegistry

// G-code generation
const gcodeGen = useSawSliceGcode(
  () => ({ startX: startX.value, startY: startY.value, endX: endX.value, endY: endY.value }),
  () => ({
    totalDepth: totalDepth.value,
    depthPerPass: depthPerPass.value,
    rpm: rpm.value,
    feedIpm: feedIpm.value,
    safeZ: safeZ.value,
  }),
  () => selectedBlade.value,
  () => materialFamily.value
)

// Convenience aliases
const {
  gcode,
  hasGcode,
  depthPasses,
  totalLengthMm,
  estimatedTimeSec,
  gcodePreview,
  svgViewBox,
  generateGcode,
  downloadGcode,
} = gcodeGen

// API operations
const sliceApi = useSawSliceApi(
  {
    getBlade: () => selectedBlade.value,
    getBladeId: () => selectedBladeId.value,
    getMaterial: () => materialFamily.value,
    getMachine: () => machineProfile.value,
    getRpm: () => rpm.value,
    getFeedIpm: () => feedIpm.value,
    getDepthPerPass: () => depthPerPass.value,
    getSafeZ: () => safeZ.value,
    getDepthPasses: () => depthPasses.value,
    getTotalLengthMm: () => totalLengthMm.value,
    getStartX: () => startX.value,
    getStartY: () => startY.value,
    getEndX: () => endX.value,
    getEndY: () => endY.value,
  },
  (merged) => {
    // Apply merged params to form
    rpm.value = merged.rpm
    feedIpm.value = merged.feed_ipm
    depthPerPass.value = merged.doc_mm
  }
)

// Convenience aliases
const {
  validationResult,
  mergedParams,
  runId,
  isValid,
  validateOperation,
  mergeLearnedParams,
  sendToJobLog,
  formatCheckName,
} = sliceApi

// ============================================================================
// Computed (validation gates)
// ============================================================================

const canValidate = computed(() => {
  return selectedBladeId.value && startX.value !== null && endX.value !== null
})

const canMerge = computed(() => {
  return selectedBladeId.value && machineProfile.value && materialFamily.value
})

// ============================================================================
// Lifecycle
// ============================================================================

onMounted(() => {
  loadBlades()
})
</script>

