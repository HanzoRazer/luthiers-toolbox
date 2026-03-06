<template>
  <section class="workflow-section calibration">
    <div class="section-header">
      <h2>
        <span class="step-number">1.5</span>
        Pixel Calibration
      </h2>
      <span
        v-if="calibration"
        :class="['confidence-badge', `confidence-${confidenceLevel}`]"
      >
        {{ confidenceLevel }} confidence
      </span>
    </div>

    <!-- Pre-Calibration Action Card -->
    <div
      v-if="!calibration"
      class="action-card"
    >
      <p class="hint">
        Calibrate the blueprint to get accurate real-world dimensions.
        Select a known scale length or let the system auto-detect.
      </p>

      <!-- Known Scale Length Selector -->
      <div class="scale-selector">
        <label for="scale-brand">Known Scale Length:</label>
        <div class="select-row">
          <select
            id="scale-brand"
            v-model="selectedBrand"
            @change="onBrandChange"
          >
            <option value="">Select brand...</option>
            <option value="fender">Fender</option>
            <option value="gibson">Gibson</option>
            <option value="prs">PRS</option>
            <option value="other">Other</option>
          </select>
          <select
            v-if="selectedBrand && modelOptions.length > 0"
            v-model="selectedModel"
            @change="onModelChange"
          >
            <option value="">Select model...</option>
            <option
              v-for="(scale, model) in modelOptions"
              :key="model"
              :value="model"
            >
              {{ formatModelName(model) }} ({{ scale }}")
            </option>
          </select>
          <input
            v-if="selectedBrand === 'custom'"
            v-model.number="customScaleLength"
            type="number"
            step="0.25"
            min="20"
            max="40"
            placeholder="Scale length (inches)"
            class="custom-scale-input"
          >
        </div>
      </div>

      <!-- Paper Size Selector -->
      <div class="paper-selector">
        <label>Assumed Paper Size:</label>
        <div class="radio-group">
          <label>
            <input
              v-model="paperSize"
              type="radio"
              value="letter"
            >
            Letter (8.5x11")
          </label>
          <label>
            <input
              v-model="paperSize"
              type="radio"
              value="a4"
            >
            A4
          </label>
          <label>
            <input
              v-model="paperSize"
              type="radio"
              value="tabloid"
            >
            Tabloid (11x17")
          </label>
        </div>
      </div>

      <button
        :disabled="isCalibrating"
        class="btn-primary"
        @click="emit('calibrate', { knownScaleLength, paperSize })"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z"
          />
        </svg>
        {{ isCalibrating ? 'Calibrating...' : 'Auto-Calibrate' }}
      </button>

      <button
        class="btn-secondary manual-btn"
        @click="showManualMode = true"
      >
        Manual Calibration (Two-Point)
      </button>
    </div>

    <!-- Manual Calibration Mode -->
    <div
      v-if="showManualMode && !calibration"
      class="manual-calibration-card"
    >
      <h3>Manual Two-Point Calibration</h3>
      <p class="hint">
        Click two points on a known dimension in the blueprint, then enter the real measurement.
      </p>

      <div class="manual-inputs">
        <div class="point-row">
          <label>Point 1:</label>
          <input
            v-model.number="manualPoint1X"
            type="number"
            placeholder="X"
          >
          <input
            v-model.number="manualPoint1Y"
            type="number"
            placeholder="Y"
          >
        </div>
        <div class="point-row">
          <label>Point 2:</label>
          <input
            v-model.number="manualPoint2X"
            type="number"
            placeholder="X"
          >
          <input
            v-model.number="manualPoint2Y"
            type="number"
            placeholder="Y"
          >
        </div>
        <div class="dimension-row">
          <label>Real Dimension:</label>
          <input
            v-model.number="manualDimension"
            type="number"
            step="0.125"
            placeholder="Inches"
          >
          <span class="unit">inches</span>
        </div>
        <div class="name-row">
          <label>Reference Name:</label>
          <select v-model="manualDimensionName">
            <option value="scale_length">Scale Length</option>
            <option value="body_width">Body Width</option>
            <option value="body_length">Body Length</option>
            <option value="nut_width">Nut Width</option>
            <option value="user_reference">Other</option>
          </select>
        </div>
      </div>

      <div class="manual-actions">
        <button
          class="btn-secondary"
          @click="showManualMode = false"
        >
          Cancel
        </button>
        <button
          :disabled="!canSubmitManual"
          class="btn-primary"
          @click="submitManualCalibration"
        >
          Apply Manual Calibration
        </button>
      </div>
    </div>

    <!-- Calibration Results -->
    <div
      v-if="calibration"
      class="results-card"
    >
      <div class="calibration-grid">
        <div class="info-card">
          <span class="label">Resolution:</span>
          <span class="value">{{ calibration.ppi.toFixed(1) }} PPI</span>
          <span class="subvalue">({{ calibration.ppmm.toFixed(2) }} px/mm)</span>
        </div>
        <div class="info-card">
          <span class="label">Method:</span>
          <span class="value method-badge">{{ formatMethod(calibration.method) }}</span>
        </div>
        <div
          v-if="calibration.reference_name"
          class="info-card"
        >
          <span class="label">Reference:</span>
          <span class="value">{{ calibration.reference_name }}</span>
          <span
            v-if="calibration.reference_value_inches"
            class="subvalue"
          >
            {{ calibration.reference_value_inches }}"
          </span>
        </div>
        <div class="info-card">
          <span class="label">Confidence:</span>
          <span :class="['value', `confidence-text-${confidenceLevel}`]">
            {{ (calibration.confidence * 100).toFixed(0) }}%
          </span>
        </div>
      </div>

      <!-- Notes -->
      <div
        v-if="calibration.notes && calibration.notes.length > 0"
        class="notes-section"
      >
        <strong>Notes:</strong>
        <ul>
          <li
            v-for="(note, idx) in calibration.notes"
            :key="idx"
          >
            {{ note }}
          </li>
        </ul>
      </div>

      <!-- Low Confidence Warning -->
      <div
        v-if="calibration.confidence < 0.5"
        class="warning-box"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          />
        </svg>
        <div>
          <strong>Low confidence calibration.</strong>
          Consider using manual two-point calibration for better accuracy.
        </div>
      </div>

      <!-- Actions -->
      <div class="action-row">
        <button
          class="btn-secondary"
          @click="emit('recalibrate')"
        >
          Re-calibrate
        </button>
        <button
          v-if="!props.accepted"
          class="btn-primary"
          @click="emit('accept')"
        >
          Accept & Continue to Vectorization
        </button>
        <span
          v-else
          class="accepted-badge"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M5 13l4 4L19 7"
            />
          </svg>
          Calibration Accepted
        </span>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'

// Types
export interface CalibrationResult {
  calibration_id: string
  method: string
  ppi: number
  ppmm: number
  confidence: number
  reference_name?: string
  reference_value_inches?: number
  reference_pixels?: number
  notes: string[]
}

export interface ManualCalibrationData {
  point1_x: number
  point1_y: number
  point2_x: number
  point2_y: number
  real_dimension: number
  dimension_name: string
}

// Known scale lengths database
const SCALE_LENGTHS: Record<string, Record<string, number>> = {
  fender: {
    stratocaster: 25.5,
    telecaster: 25.5,
    jazzmaster: 25.5,
    jaguar: 24.0,
    mustang: 24.0,
    jazz_bass: 34.0,
    precision_bass: 34.0,
  },
  gibson: {
    les_paul: 24.75,
    sg: 24.75,
    es_335: 24.75,
    explorer: 24.75,
    flying_v: 24.75,
    firebird: 24.75,
    thunderbird_bass: 34.0,
  },
  prs: {
    custom_24: 25.0,
    custom_22: 25.0,
    mccarty: 25.0,
    se: 25.0,
  },
  other: {
    rickenbacker: 24.75,
    gretsch: 24.6,
    danelectro: 25.0,
    steinberger: 25.5,
    strandberg: 25.5,
  },
}

// Props
interface Props {
  calibration: CalibrationResult | null
  isCalibrating: boolean
  accepted?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  accepted: false,
})

// Emits
const emit = defineEmits<{
  calibrate: [options: { knownScaleLength: number | null; paperSize: string }]
  'manual-calibrate': [data: ManualCalibrationData]
  recalibrate: []
  accept: []
}>()

// State
const selectedBrand = ref<string>('')
const selectedModel = ref<string>('')
const customScaleLength = ref<number | null>(null)
const paperSize = ref<string>('letter')
const showManualMode = ref(false)

// Manual calibration state
const manualPoint1X = ref<number | null>(null)
const manualPoint1Y = ref<number | null>(null)
const manualPoint2X = ref<number | null>(null)
const manualPoint2Y = ref<number | null>(null)
const manualDimension = ref<number | null>(null)
const manualDimensionName = ref<string>('scale_length')

// Computed
const modelOptions = computed(() => {
  if (!selectedBrand.value || selectedBrand.value === 'custom') {
    return {}
  }
  return SCALE_LENGTHS[selectedBrand.value] || {}
})

const knownScaleLength = computed<number | null>(() => {
  if (selectedBrand.value === 'custom' && customScaleLength.value) {
    return customScaleLength.value
  }
  if (selectedBrand.value && selectedModel.value) {
    return SCALE_LENGTHS[selectedBrand.value]?.[selectedModel.value] || null
  }
  return null
})

const confidenceLevel = computed<string>(() => {
  if (!props.calibration) return 'unknown'
  const conf = props.calibration.confidence
  if (conf >= 0.8) return 'high'
  if (conf >= 0.5) return 'medium'
  return 'low'
})

const canSubmitManual = computed<boolean>(() => {
  return (
    manualPoint1X.value !== null &&
    manualPoint1Y.value !== null &&
    manualPoint2X.value !== null &&
    manualPoint2Y.value !== null &&
    manualDimension.value !== null &&
    manualDimension.value > 0
  )
})

// Watchers
watch(selectedBrand, () => {
  selectedModel.value = ''
})

// Methods
function onBrandChange() {
  selectedModel.value = ''
}

function onModelChange() {
  // Model selected, knownScaleLength will update via computed
}

function formatModelName(model: string): string {
  return model
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

function formatMethod(method: string): string {
  const methodNames: Record<string, string> = {
    scale_length: 'Scale Length',
    paper_size: 'Paper Size',
    body_heuristic: 'Body Heuristic',
    ruler: 'Ruler Detection',
    manual: 'Manual',
    auto: 'Auto',
  }
  return methodNames[method] || method
}

function submitManualCalibration() {
  if (!canSubmitManual.value) return

  emit('manual-calibrate', {
    point1_x: manualPoint1X.value!,
    point1_y: manualPoint1Y.value!,
    point2_x: manualPoint2X.value!,
    point2_y: manualPoint2Y.value!,
    real_dimension: manualDimension.value!,
    dimension_name: manualDimensionName.value,
  })

  showManualMode.value = false
}
</script>

<style scoped>
.workflow-section {
  border: 2px solid #e5e7eb;
  border-radius: 1rem;
  padding: 1.5rem;
  background: white;
}

.workflow-section.calibration {
  border-color: #f59e0b;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.section-header h2 {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin: 0;
  font-size: 1.25rem;
}

.step-number {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #f59e0b;
  color: white;
  font-weight: bold;
  font-size: 0.875rem;
}

.confidence-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.875rem;
  font-weight: 600;
}

.confidence-high {
  background: #d1fae5;
  color: #065f46;
}

.confidence-medium {
  background: #fef3c7;
  color: #92400e;
}

.confidence-low {
  background: #fee2e2;
  color: #991b1b;
}

.action-card {
  background: #fffbeb;
  border-radius: 0.75rem;
  padding: 1.5rem;
  text-align: center;
}

.hint {
  color: #6b7280;
  margin-bottom: 1rem;
}

.scale-selector,
.paper-selector {
  margin-bottom: 1.25rem;
  text-align: left;
}

.scale-selector label,
.paper-selector label {
  display: block;
  font-weight: 500;
  margin-bottom: 0.5rem;
  color: #374151;
}

.select-row {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.select-row select,
.custom-scale-input {
  padding: 0.5rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  min-width: 150px;
}

.custom-scale-input {
  width: 140px;
}

.radio-group {
  display: flex;
  gap: 1.5rem;
  flex-wrap: wrap;
}

.radio-group label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: normal;
  cursor: pointer;
}

.manual-btn {
  margin-top: 0.75rem;
}

/* Manual Calibration Card */
.manual-calibration-card {
  background: #f3f4f6;
  border-radius: 0.75rem;
  padding: 1.5rem;
  margin-top: 1rem;
}

.manual-calibration-card h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1rem;
}

.manual-inputs {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin: 1rem 0;
}

.point-row,
.dimension-row,
.name-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.point-row label,
.dimension-row label,
.name-row label {
  width: 100px;
  font-weight: 500;
  font-size: 0.875rem;
}

.point-row input,
.dimension-row input {
  width: 80px;
  padding: 0.375rem 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 0.25rem;
}

.name-row select {
  padding: 0.375rem 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 0.25rem;
}

.unit {
  color: #6b7280;
  font-size: 0.875rem;
}

.manual-actions {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
}

/* Results Card */
.results-card {
  background: #fffbeb;
  border-radius: 0.75rem;
  padding: 1.5rem;
}

.calibration-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
  margin-bottom: 1rem;
}

.info-card {
  background: white;
  padding: 0.75rem;
  border-radius: 0.5rem;
  border: 1px solid #fcd34d;
}

.info-card .label {
  display: block;
  color: #6b7280;
  font-size: 0.75rem;
  margin-bottom: 0.25rem;
}

.info-card .value {
  display: block;
  font-weight: 600;
  font-size: 1rem;
}

.info-card .subvalue {
  display: block;
  color: #6b7280;
  font-size: 0.75rem;
}

.method-badge {
  display: inline-block;
  padding: 0.125rem 0.5rem;
  background: #fef3c7;
  border-radius: 0.25rem;
  font-size: 0.875rem;
}

.confidence-text-high {
  color: #065f46;
}

.confidence-text-medium {
  color: #92400e;
}

.confidence-text-low {
  color: #991b1b;
}

.notes-section {
  background: white;
  padding: 0.75rem;
  border-radius: 0.5rem;
  margin-bottom: 1rem;
  font-size: 0.875rem;
}

.notes-section ul {
  margin: 0.5rem 0 0 1.5rem;
  padding: 0;
}

.notes-section li {
  margin-bottom: 0.25rem;
}

.warning-box {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 0.75rem;
  background: #fef3c7;
  border: 1px solid #f59e0b;
  border-radius: 0.5rem;
  margin-bottom: 1rem;
}

.warning-box svg {
  width: 24px;
  height: 24px;
  flex-shrink: 0;
  color: #f59e0b;
}

.warning-box div {
  font-size: 0.875rem;
}

.action-row {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
}

/* Buttons */
.btn-primary,
.btn-secondary {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 0.5rem;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: #f59e0b;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #d97706;
}

.btn-secondary {
  background: #e5e7eb;
  color: #374151;
}

.btn-secondary:hover:not(:disabled) {
  background: #d1d5db;
}

.btn-primary:disabled,
.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary svg,
.btn-secondary svg {
  width: 20px;
  height: 20px;
}

.accepted-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background: #d1fae5;
  color: #065f46;
  border-radius: 0.5rem;
  font-weight: 600;
}

.accepted-badge svg {
  width: 20px;
  height: 20px;
}
</style>
