<template>
  <div class="saw-batch-panel">
    <div class="panel-header">
      <h2>Saw Batch Operation</h2>
      <p class="subtitle">
        Schedule multiple slices with batch-level optimization
      </p>
    </div>

    <div class="panel-content">
      <!-- Left Column: Batch Setup -->
      <div class="batch-setup-section">
        <h3>Batch Configuration</h3>

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
              {{ blade.vendor }} {{ blade.model_code }} ({{ blade.diameter_mm }}mm)
            </option>
          </select>
        </div>

        <!-- Machine & Material -->
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

        <!-- Batch Parameters -->
        <div class="form-group">
          <label>Number of Slices</label>
          <input
            v-model.number="numSlices"
            type="number"
            min="1"
            max="50"
            step="1"
          >
        </div>

        <div class="form-group">
          <label>Slice Spacing (mm)</label>
          <input
            v-model.number="sliceSpacing"
            type="number"
            step="1"
            min="1"
          >
          <div class="help-text">
            Distance between slice start points
          </div>
        </div>

        <div class="form-group">
          <label>Slice Length (mm)</label>
          <input
            v-model.number="sliceLength"
            type="number"
            step="1"
            min="10"
          >
        </div>

        <div class="form-group">
          <label>Start Position X (mm)</label>
          <input
            v-model.number="startX"
            type="number"
            step="0.1"
          >
        </div>

        <div class="form-group">
          <label>Start Position Y (mm)</label>
          <input
            v-model.number="startY"
            type="number"
            step="0.1"
          >
        </div>

        <div class="form-group">
          <label>Slice Orientation</label>
          <select v-model="orientation">
            <option value="horizontal">
              Horizontal (along X)
            </option>
            <option value="vertical">
              Vertical (along Y)
            </option>
          </select>
        </div>

        <!-- Depth Parameters -->
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
            @click="validateBatch"
          >
            Validate Batch
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
            @click="generateBatchGcode"
          >
            Generate Batch G-code
          </button>
          <button
            :disabled="!hasGcode"
            class="btn-success"
            @click="sendToJobLog"
          >
            Send Batch to JobLog
          </button>
        </div>
      </div>

      <!-- Right Column: Batch Preview & Stats -->
      <div class="batch-preview-section">
        <!-- Batch Statistics -->
        <div class="batch-stats">
          <h3>Batch Statistics</h3>
          <div class="stats-grid">
            <div class="stat-card">
              <div class="stat-label">
                Total Slices
              </div>
              <div class="stat-value">
                {{ numSlices }}
              </div>
            </div>
            <div class="stat-card">
              <div class="stat-label">
                Total Length
              </div>
              <div class="stat-value">
                {{ totalLengthMm.toFixed(0) }} mm
              </div>
            </div>
            <div class="stat-card">
              <div class="stat-label">
                Total Passes
              </div>
              <div class="stat-value">
                {{ totalPasses }}
              </div>
            </div>
            <div class="stat-card">
              <div class="stat-label">
                Est. Time
              </div>
              <div class="stat-value">
                {{ formatTime(estimatedTimeSec) }}
              </div>
            </div>
            <div class="stat-card">
              <div class="stat-label">
                Total Volume
              </div>
              <div class="stat-value">
                {{ totalVolumeMm3.toFixed(0) }} mm³
              </div>
            </div>
            <div class="stat-card">
              <div class="stat-label">
                Kerf Loss
              </div>
              <div class="stat-value">
                {{ kerfLossMm3.toFixed(0) }} mm³
              </div>
            </div>
          </div>
        </div>

        <!-- Validation Results -->
        <div
          v-if="validationResult"
          class="validation-results"
        >
          <h3>Validation Results</h3>
          <div :class="['validation-badge', validationResult.overall_result.toLowerCase()]">
            {{ validationResult.overall_result }}
          </div>
          <div class="validation-summary">
            {{ validationResult.checks ? Object.keys(validationResult.checks).length : 0 }} checks performed
          </div>
        </div>

        <!-- Learned Parameters -->
        <div
          v-if="mergedParams"
          class="learned-params"
        >
          <h3>Learned Parameters Applied</h3>
          <div class="param-grid">
            <div class="param-item">
              <span class="label">RPM:</span>
              <span class="values">
                <span class="baseline">{{ rpm }}</span>
                <span class="arrow">→</span>
                <span class="merged">{{ mergedParams.rpm?.toFixed(0) || rpm }}</span>
              </span>
            </div>
            <div class="param-item">
              <span class="label">Feed:</span>
              <span class="values">
                <span class="baseline">{{ feedIpm }}</span>
                <span class="arrow">→</span>
                <span class="merged">{{ mergedParams.feed_ipm?.toFixed(1) || feedIpm }}</span>
              </span>
            </div>
            <div class="param-item">
              <span class="label">DOC:</span>
              <span class="values">
                <span class="baseline">{{ depthPerPass }}</span>
                <span class="arrow">→</span>
                <span class="merged">{{ mergedParams.doc_mm?.toFixed(1) || depthPerPass }}</span>
              </span>
            </div>
          </div>
        </div>

        <!-- SVG Preview -->
        <div class="svg-preview">
          <h3>Batch Path Preview</h3>
          <svg
            :viewBox="svgViewBox"
            width="100%"
            height="400"
            class="preview-canvas"
          >
            <!-- Grid -->
            <defs>
              <pattern
                id="batch-grid"
                width="20"
                height="20"
                patternUnits="userSpaceOnUse"
              >
                <path
                  d="M 20 0 L 0 0 0 20"
                  fill="none"
                  stroke="#e0e0e0"
                  stroke-width="0.5"
                />
              </pattern>
            </defs>
            <rect
              width="100%"
              height="100%"
              fill="url(#batch-grid)"
            />
            
            <!-- Slice paths -->
            <g
              v-for="(slice, i) in slicePaths"
              :key="i"
            >
              <line
                :x1="slice.x1"
                :y1="slice.y1"
                :x2="slice.x2"
                :y2="slice.y2"
                :stroke="i === 0 ? '#2196F3' : '#64B5F6'"
                stroke-width="2"
              />
              <text
                :x="slice.x1 - 10"
                :y="slice.y1"
                font-size="10"
                fill="#666"
              >{{ i + 1 }}</text>
            </g>
            
            <!-- Kerf boundaries (first slice) -->
            <line
              v-if="slicePaths.length > 0 && selectedBlade"
              :x1="slicePaths[0].x1"
              :y1="slicePaths[0].y1 + (selectedBlade.kerf_mm / 2)"
              :x2="slicePaths[0].x2"
              :y2="slicePaths[0].y2 + (selectedBlade.kerf_mm / 2)"
              stroke="#FF9800"
              stroke-width="1"
              stroke-dasharray="2,2"
            />
            <line
              v-if="slicePaths.length > 0 && selectedBlade"
              :x1="slicePaths[0].x1"
              :y1="slicePaths[0].y1 - (selectedBlade.kerf_mm / 2)"
              :x2="slicePaths[0].x2"
              :y2="slicePaths[0].y2 - (selectedBlade.kerf_mm / 2)"
              stroke="#FF9800"
              stroke-width="1"
              stroke-dasharray="2,2"
            />
          </svg>
          <div class="legend">
            <span><span
              class="color-box"
              style="background: #2196F3;"
            /> First slice</span>
            <span><span
              class="color-box"
              style="background: #64B5F6;"
            /> Other slices</span>
            <span><span
              class="color-box"
              style="background: #FF9800;"
            /> Kerf boundary</span>
          </div>
        </div>

        <!-- G-code Preview -->
        <div
          v-if="gcode"
          class="gcode-preview"
        >
          <h3>G-code Preview (First 20 / Last 5 lines)</h3>
          <pre class="gcode-text">{{ gcodePreview }}</pre>
          <button
            class="btn-secondary"
            @click="downloadGcode"
          >
            Download Batch G-code
          </button>
        </div>

        <!-- Run Artifact Link -->
        <div
          v-if="runId"
          class="run-artifact-link"
        >
          <h3>Run Artifact</h3>
          <p>Job logged with Run ID: <code>{{ runId }}</code></p>
          <router-link
            :to="`/rmos/runs?run_id=${runId}`"
            class="btn-primary"
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
  return selectedBladeId.value && numSlices.value > 0
})

const canMerge = computed(() => {
  return selectedBladeId.value && machineProfile.value && materialFamily.value
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

<style scoped>
.saw-batch-panel {
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
  grid-template-columns: 380px 1fr;
  gap: 30px;
}

h3 {
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

.help-text {
  margin-top: 3px;
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

.batch-stats,
.validation-results,
.learned-params,
.svg-preview,
.gcode-preview {
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  padding: 15px;
  margin-bottom: 20px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;
}

.stat-card {
  background: white;
  padding: 12px;
  border-radius: 4px;
  border: 1px solid #dee2e6;
  text-align: center;
}

.stat-label {
  font-size: 11px;
  color: #7f8c8d;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 5px;
}

.stat-value {
  font-size: 20px;
  font-weight: 700;
  color: #2c3e50;
}

.validation-badge {
  display: inline-block;
  padding: 5px 15px;
  border-radius: 4px;
  font-weight: 600;
  margin-bottom: 10px;
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

.validation-summary {
  font-size: 13px;
  color: #7f8c8d;
}

.param-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;
}

.param-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
  font-size: 13px;
}

.param-item .label {
  font-weight: 600;
  color: #2c3e50;
}

.param-item .values {
  display: flex;
  align-items: center;
  gap: 5px;
}

.baseline {
  color: #7f8c8d;
}

.arrow {
  color: #3498db;
}

.merged {
  color: #27ae60;
  font-weight: 600;
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

.gcode-text {
  background: #2c3e50;
  color: #ecf0f1;
  padding: 15px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.5;
  overflow-x: auto;
  margin-bottom: 10px;
  max-height: 300px;
  overflow-y: auto;
}

.run-artifact-link {
  background: #e8f5e9;
  border: 1px solid #4caf50;
  border-radius: 4px;
  padding: 15px;
  margin-top: 15px;
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
