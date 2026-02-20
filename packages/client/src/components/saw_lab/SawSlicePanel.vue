<template>
  <div class="saw-slice-panel">
    <div class="panel-header">
      <h2>Saw Slice Operation</h2>
      <p class="subtitle">
        Kerf-aware straight cuts with multi-pass depth control
      </p>
    </div>

    <div class="panel-content">
      <!-- Left Column: Parameters -->
      <div class="parameters-section">
        <h3>Cut Parameters</h3>

        <!-- Blade Selection -->
        <div class="form-group">
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
            class="blade-info"
          >
            Kerf: {{ selectedBlade.kerf_mm }}mm | Teeth:
            {{ selectedBlade.teeth }}
          </div>
        </div>

        <!-- Machine Profile -->
        <div class="form-group">
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
        <div class="form-group">
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
        <div class="form-group">
          <label>Start X (mm)</label>
          <input
            v-model.number="startX"
            type="number"
            step="0.1"
          >
        </div>

        <div class="form-group">
          <label>Start Y (mm)</label>
          <input
            v-model.number="startY"
            type="number"
            step="0.1"
          >
        </div>

        <div class="form-group">
          <label>End X (mm)</label>
          <input
            v-model.number="endX"
            type="number"
            step="0.1"
          >
        </div>

        <div class="form-group">
          <label>End Y (mm)</label>
          <input
            v-model.number="endY"
            type="number"
            step="0.1"
          >
        </div>

        <div class="form-group">
          <label>Total Depth (mm)</label>
          <input
            v-model.number="totalDepth"
            type="number"
            step="0.5"
            min="0.5"
          >
        </div>

        <div class="form-group">
          <label>Depth Per Pass (mm)</label>
          <input
            v-model.number="depthPerPass"
            type="number"
            step="0.5"
            min="0.5"
          >
        </div>

        <!-- Feeds & Speeds -->
        <div class="form-group">
          <label>RPM</label>
          <input
            v-model.number="rpm"
            type="number"
            step="100"
            min="2000"
            max="6000"
          >
        </div>

        <div class="form-group">
          <label>Feed Rate (IPM)</label>
          <input
            v-model.number="feedIpm"
            type="number"
            step="5"
            min="10"
            max="300"
          >
        </div>

        <div class="form-group">
          <label>Safe Z (mm)</label>
          <input
            v-model.number="safeZ"
            type="number"
            step="0.5"
            min="1"
          >
        </div>

        <!-- Actions -->
        <div class="actions">
          <button
            :disabled="!canValidate"
            class="btn-primary"
            @click="validateOperation"
          >
            Validate Parameters
          </button>
          <button
            :disabled="!canMerge"
            class="btn-secondary"
            @click="mergeLearnedParams"
          >
            Apply Learned Overrides
          </button>
          <button
            :disabled="!isValid"
            class="btn-primary"
            @click="generateGcode"
          >
            Generate G-code
          </button>
          <button
            :disabled="!hasGcode"
            class="btn-success"
            @click="sendToJobLog"
          >
            Send to JobLog
          </button>
        </div>
      </div>

      <!-- Right Column: Preview & Validation -->
      <div class="preview-section">
        <!-- Validation Results -->
        <div
          v-if="validationResult"
          class="validation-results"
        >
          <h3>Validation Results</h3>
          <div
            :class="[
              'validation-badge',
              validationResult.overall_result.toLowerCase(),
            ]"
          >
            {{ validationResult.overall_result }}
          </div>
          <div class="validation-checks">
            <div
              v-for="(check, key) in validationResult.checks"
              :key="key"
              :class="['check-item', check.result.toLowerCase()]"
            >
              <span class="check-icon">{{
                check.result === "OK"
                  ? "✓"
                  : check.result === "WARN"
                    ? "⚠"
                    : "✗"
              }}</span>
              <span class="check-name">{{ formatCheckName(String(key)) }}</span>
              <span class="check-message">{{ check.message }}</span>
            </div>
          </div>
        </div>

        <!-- Learned Parameters -->
        <div
          v-if="mergedParams"
          class="learned-params"
        >
          <h3>Learned Parameters Applied</h3>
          <div class="param-comparison">
            <div class="param-row">
              <span class="label">RPM:</span>
              <span class="baseline">{{ rpm }}</span>
              <span class="arrow">→</span>
              <span class="merged">{{
                mergedParams.rpm?.toFixed(0) || rpm
              }}</span>
            </div>
            <div class="param-row">
              <span class="label">Feed:</span>
              <span class="baseline">{{ feedIpm }}</span>
              <span class="arrow">→</span>
              <span class="merged">{{
                mergedParams.feed_ipm?.toFixed(1) || feedIpm
              }}</span>
            </div>
            <div class="param-row">
              <span class="label">DOC:</span>
              <span class="baseline">{{ depthPerPass }}</span>
              <span class="arrow">→</span>
              <span class="merged">{{
                mergedParams.doc_mm?.toFixed(1) || depthPerPass
              }}</span>
            </div>
          </div>
          <div class="lane-info">
            Lane scale: {{ mergedParams.lane_scale?.toFixed(2) || "1.00" }}
          </div>
        </div>

        <!-- G-code Preview -->
        <div
          v-if="gcode"
          class="gcode-preview"
        >
          <h3>G-code Preview</h3>
          <div class="preview-stats">
            <div class="stat">
              <span class="label">Total Length:</span>
              <span class="value">{{ totalLengthMm.toFixed(1) }} mm</span>
            </div>
            <div class="stat">
              <span class="label">Depth Passes:</span>
              <span class="value">{{ depthPasses }}</span>
            </div>
            <div class="stat">
              <span class="label">Est. Time:</span>
              <span class="value">{{ estimatedTimeSec.toFixed(0) }}s</span>
            </div>
          </div>
          <pre class="gcode-text">{{ gcodePreview }}</pre>
          <button
            class="btn-secondary"
            @click="downloadGcode"
          >
            Download G-code
          </button>
        </div>

        <!-- Run Artifact Link -->
        <div
          v-if="runId"
          class="run-artifact-link"
        >
          <h3>Run Artifact</h3>
          <p>
            Job logged with Run ID: <code>{{ runId }}</code>
          </p>
          <router-link
            :to="`/rmos/runs?run_id=${runId}`"
            class="btn-primary"
          >
            View Run Artifact
          </router-link>
        </div>

        <!-- SVG Preview -->
        <div class="svg-preview">
          <h3>Path Preview</h3>
          <svg
            :viewBox="svgViewBox"
            width="400"
            height="300"
            class="preview-canvas"
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
          <div class="legend">
            <span><span
              class="color-box"
              style="background: #2196f3"
            /> Cut
              path</span>
            <span><span
              class="color-box"
              style="background: #ff9800"
            /> Kerf
              boundary</span>
            <span><span
              class="color-box"
              style="background: #4caf50"
            />
              Start</span>
            <span><span
              class="color-box"
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

<style scoped>
.saw-slice-panel {
  padding: 20px;
}

.panel-header {
  margin-bottom: 30px;
}

.panel-header h2 {
  margin: 0 0 5px 0;
  color: #2c3e50;
}

.subtitle {
  margin: 0;
  color: #7f8c8d;
  font-size: 14px;
}

.panel-content {
  display: grid;
  grid-template-columns: 400px 1fr;
  gap: 30px;
}

.parameters-section h3,
.preview-section h3 {
  margin: 0 0 15px 0;
  color: #34495e;
  font-size: 16px;
  border-bottom: 2px solid #3498db;
  padding-bottom: 5px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
  color: #2c3e50;
  font-size: 14px;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 8px;
  border: 1px solid #bdc3c7;
  border-radius: 4px;
  font-size: 14px;
}

.blade-info {
  margin-top: 5px;
  font-size: 12px;
  color: #7f8c8d;
}

.actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 20px;
}

.btn-primary,
.btn-secondary,
.btn-success {
  padding: 12px;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: #3498db;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #2980b9;
}

.btn-secondary {
  background: #95a5a6;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background: #7f8c8d;
}

.btn-success {
  background: #27ae60;
  color: white;
}

.btn-success:hover:not(:disabled) {
  background: #229954;
}

.btn-primary:disabled,
.btn-secondary:disabled,
.btn-success:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.validation-results,
.learned-params,
.gcode-preview,
.run-artifact-link,
.svg-preview {
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  padding: 15px;
  margin-bottom: 20px;
}

.validation-badge {
  display: inline-block;
  padding: 5px 15px;
  border-radius: 4px;
  font-weight: 600;
  margin-bottom: 15px;
}

.validation-badge.ok {
  background: #d4edda;
  color: #155724;
}

.validation-badge.warn {
  background: #fff3cd;
  color: #856404;
}

.validation-badge.error {
  background: #f8d7da;
  color: #721c24;
}

.validation-checks {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.check-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px;
  border-radius: 4px;
  font-size: 13px;
}

.check-item.ok {
  background: #d4edda;
}

.check-item.warn {
  background: #fff3cd;
}

.check-item.error {
  background: #f8d7da;
}

.check-icon {
  font-weight: 700;
  font-size: 16px;
}

.check-name {
  font-weight: 600;
  min-width: 150px;
}

.param-comparison {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 10px;
}

.param-row {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
}

.param-row .label {
  font-weight: 600;
  min-width: 60px;
}

.param-row .baseline {
  color: #7f8c8d;
}

.param-row .arrow {
  color: #3498db;
}

.param-row .merged {
  color: #27ae60;
  font-weight: 600;
}

.lane-info {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #dee2e6;
  font-size: 13px;
  color: #7f8c8d;
}

.preview-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;
  margin-bottom: 15px;
}

.stat {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.stat .label {
  font-size: 12px;
  color: #7f8c8d;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stat .value {
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
}

.gcode-text {
  background: #2c3e50;
  color: #ecf0f1;
  padding: 15px;
  border-radius: 4px;
  font-family: "Courier New", monospace;
  font-size: 12px;
  line-height: 1.5;
  overflow-x: auto;
  margin-bottom: 10px;
  max-height: 300px;
  overflow-y: auto;
}

.preview-canvas {
  border: 1px solid #dee2e6;
  background: white;
  border-radius: 4px;
}

.legend {
  display: flex;
  gap: 15px;
  margin-top: 10px;
  font-size: 12px;
  color: #7f8c8d;
}

.legend span {
  display: flex;
  align-items: center;
  gap: 5px;
}

.color-box {
  display: inline-block;
  width: 16px;
  height: 16px;
  border-radius: 2px;
}

.run-artifact-link {
  background: #e8f5e9;
  border-color: #4caf50;
}

.run-artifact-link code {
  background: #c8e6c9;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 13px;
}

.run-artifact-link a {
  display: inline-block;
  margin-top: 10px;
  text-decoration: none;
}
</style>
