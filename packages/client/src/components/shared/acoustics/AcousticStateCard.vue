<script setup lang="ts">
/**
 * AcousticStateCard — Reusable display and edit for AcousticState
 *
 * Dev Order 16: Extracted from ApertureComparisonPanel inline display.
 * Dev Order 24: Added manual estimate attachment controls.
 * Displays acoustic state metadata without prediction logic.
 */
import { computed, ref } from 'vue'
import { GateBadge } from '@/components/shared/workflow'
import type { AcousticState, AcousticConfidence } from '@/types/acoustics'
import {
  hasEstimatedAcoustics,
  getConfidenceLabel,
  getSourceLabel,
  mergeManualEstimates,
} from '@/utils/acoustics'

const props = withDefaults(
  defineProps<{
    state: AcousticState
    editable?: boolean
  }>(),
  {
    editable: false,
  }
)

const emit = defineEmits<{
  (e: 'update:state', value: AcousticState): void
}>()

/**
 * Map confidence to gate color.
 * low/unknown/medium → yellow, high → green
 * No red — red is reserved for diagnostic failures.
 */
function confidenceToGate(confidence: AcousticConfidence): 'green' | 'yellow' {
  return confidence === 'high' ? 'green' : 'yellow'
}

const hasEstimates = computed(() => hasEstimatedAcoustics(props.state))
const gateColor = computed(() => confidenceToGate(props.state.confidence))
const isManualSource = computed(() => props.state.source === 'manual')

// Edit mode state
const isEditing = ref(false)
const localHelmholtz = ref<number | null>(null)
const localEffectiveLength = ref<number | null>(null)
const localQ = ref<number | null>(null)
const localLoss = ref<number | null>(null)

function startEditing() {
  localHelmholtz.value = props.state.estimatedHelmholtzHz ?? null
  localEffectiveLength.value = props.state.estimatedEffectiveLengthMm ?? null
  localQ.value = props.state.qEstimate ?? null
  localLoss.value = props.state.lossEstimate ?? null
  isEditing.value = true
}

function cancelEditing() {
  isEditing.value = false
}

function saveEstimates() {
  const estimates: {
    estimatedHelmholtzHz?: number
    estimatedEffectiveLengthMm?: number
    qEstimate?: number
    lossEstimate?: number
  } = {}

  if (localHelmholtz.value !== null && localHelmholtz.value > 0) {
    estimates.estimatedHelmholtzHz = localHelmholtz.value
  }
  if (localEffectiveLength.value !== null && localEffectiveLength.value > 0) {
    estimates.estimatedEffectiveLengthMm = localEffectiveLength.value
  }
  if (localQ.value !== null && localQ.value > 0) {
    estimates.qEstimate = localQ.value
  }
  if (localLoss.value !== null && localLoss.value >= 0) {
    estimates.lossEstimate = localLoss.value
  }

  const updated = mergeManualEstimates(props.state, estimates)
  emit('update:state', updated)
  isEditing.value = false
}
</script>

<template>
  <div :class="$style.card">
    <!-- Header -->
    <div :class="$style.header">
      <span :class="$style.label">{{ state.label }}</span>
      <GateBadge :gate="gateColor" :label="getConfidenceLabel(state.confidence)" />
    </div>

    <!-- Metadata -->
    <div :class="$style.meta">
      <div :class="$style.row">
        <span :class="$style.key">Source:</span>
        <span :class="$style.value">{{ getSourceLabel(state.source) }}</span>
      </div>
      <div :class="$style.row">
        <span :class="$style.key">Confidence:</span>
        <span :class="$style.value">{{ getConfidenceLabel(state.confidence) }}</span>
      </div>
      <div v-if="state.apertureType" :class="$style.row">
        <span :class="$style.key">Type:</span>
        <span :class="$style.value">{{ state.apertureType }}</span>
      </div>
    </div>

    <!-- Editing Form -->
    <div v-if="isEditing" :class="$style.editForm">
      <div :class="$style.field">
        <label :class="$style.fieldLabel">Estimated Helmholtz (Hz)</label>
        <input
          v-model.number="localHelmholtz"
          type="number"
          :class="$style.input"
          min="0"
          step="0.1"
          placeholder="e.g., 98.5"
        />
      </div>
      <div :class="$style.field">
        <label :class="$style.fieldLabel">Estimated Effective Length (mm)</label>
        <input
          v-model.number="localEffectiveLength"
          type="number"
          :class="$style.input"
          min="0"
          step="0.1"
          placeholder="e.g., 12.4"
        />
      </div>
      <div :class="$style.field">
        <label :class="$style.fieldLabel">Q Estimate</label>
        <input
          v-model.number="localQ"
          type="number"
          :class="$style.input"
          min="0"
          step="0.1"
          placeholder="e.g., 7.2"
        />
      </div>
      <div :class="$style.field">
        <label :class="$style.fieldLabel">Loss Estimate</label>
        <input
          v-model.number="localLoss"
          type="number"
          :class="$style.input"
          min="0"
          step="0.01"
          placeholder="e.g., 0.18"
        />
      </div>
      <div :class="$style.editActions">
        <button :class="$style.btnCancel" @click="cancelEditing">Cancel</button>
        <button :class="$style.btnSave" @click="saveEstimates">Save</button>
      </div>
    </div>

    <!-- Display mode -->
    <template v-else>
      <!-- Estimated Values -->
      <div v-if="hasEstimates" :class="$style.estimates">
        <div v-if="state.estimatedHelmholtzHz !== undefined" :class="$style.row">
          <span :class="$style.key">Helmholtz:</span>
          <span :class="$style.value">{{ state.estimatedHelmholtzHz.toFixed(1) }} Hz</span>
        </div>
        <div v-if="state.estimatedEffectiveLengthMm !== undefined" :class="$style.row">
          <span :class="$style.key">Effective length:</span>
          <span :class="$style.value">{{ state.estimatedEffectiveLengthMm.toFixed(1) }} mm</span>
        </div>
        <div v-if="state.qEstimate !== undefined" :class="$style.row">
          <span :class="$style.key">Q estimate:</span>
          <span :class="$style.value">{{ state.qEstimate.toFixed(1) }}</span>
        </div>
        <div v-if="state.lossEstimate !== undefined" :class="$style.row">
          <span :class="$style.key">Loss estimate:</span>
          <span :class="$style.value">{{ state.lossEstimate.toFixed(2) }}</span>
        </div>
      </div>

      <!-- No Estimates Message -->
      <div v-else :class="$style.noEstimates">
        No calibrated acoustic estimates attached.
      </div>

      <!-- Edit Button -->
      <button v-if="editable" :class="$style.editBtn" @click="startEditing">
        Attach Estimate
      </button>
    </template>

    <!-- Manual estimate notice -->
    <div v-if="isManualSource && hasEstimates" :class="$style.manualNotice">
      Manual estimates are placeholders and are not calibrated predictions.
    </div>

    <!-- Warnings -->
    <div v-if="state.warnings?.length" :class="$style.warnings">
      <span :class="$style.warningsLabel">Warnings:</span>
      <ul>
        <li v-for="(warning, i) in state.warnings" :key="i">
          {{ warning }}
        </li>
      </ul>
    </div>

    <!-- Assumptions -->
    <div v-if="state.assumptions.length" :class="$style.assumptions">
      <span :class="$style.assumptionsLabel">Assumptions:</span>
      <ul>
        <li v-for="(assumption, i) in state.assumptions" :key="i">
          {{ assumption }}
        </li>
      </ul>
    </div>
  </div>
</template>

<style module>
.card {
  background: #111827;
  border: 1px solid #374151;
  border-radius: 0.375rem;
  padding: 0.75rem;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.5rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #374151;
}

.label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #f9fafb;
}

.meta {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  margin-bottom: 0.5rem;
}

.row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.key {
  font-size: 0.6875rem;
  font-weight: 500;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.value {
  font-size: 0.8125rem;
  color: #d1d5db;
}

.estimates {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 0.5rem;
  background: rgba(34, 197, 94, 0.1);
  border-radius: 0.25rem;
  margin-bottom: 0.5rem;
}

.noEstimates {
  font-size: 0.75rem;
  color: #6b7280;
  font-style: italic;
  padding: 0.5rem;
  background: rgba(107, 114, 128, 0.1);
  border-radius: 0.25rem;
  margin-bottom: 0.5rem;
}

.editBtn {
  width: 100%;
  padding: 0.5rem;
  margin-bottom: 0.5rem;
  background: rgba(99, 102, 241, 0.2);
  border: 1px dashed #6366f1;
  border-radius: 0.25rem;
  color: #a5b4fc;
  font-size: 0.75rem;
  cursor: pointer;
  transition: background 0.15s;
}

.editBtn:hover {
  background: rgba(99, 102, 241, 0.3);
}

.editForm {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0.5rem;
  background: rgba(99, 102, 241, 0.1);
  border-radius: 0.25rem;
  margin-bottom: 0.5rem;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.fieldLabel {
  font-size: 0.6875rem;
  font-weight: 500;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.input {
  padding: 0.375rem 0.5rem;
  background: #1f2937;
  border: 1px solid #374151;
  border-radius: 0.25rem;
  color: #f9fafb;
  font-size: 0.8125rem;
  font-family: var(--font-mono, ui-monospace, monospace);
}

.input:focus {
  outline: none;
  border-color: #6366f1;
}

.editActions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
  margin-top: 0.25rem;
}

.btnCancel,
.btnSave {
  padding: 0.375rem 0.75rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s;
}

.btnCancel {
  background: transparent;
  border: 1px solid #4b5563;
  color: #9ca3af;
}

.btnCancel:hover {
  background: rgba(75, 85, 99, 0.3);
}

.btnSave {
  background: #6366f1;
  border: 1px solid #6366f1;
  color: #fff;
}

.btnSave:hover {
  background: #4f46e5;
}

.manualNotice {
  font-size: 0.6875rem;
  color: #fbbf24;
  font-style: italic;
  padding: 0.375rem 0.5rem;
  background: rgba(251, 191, 36, 0.1);
  border-radius: 0.25rem;
  margin-bottom: 0.5rem;
}

.warnings {
  font-size: 0.75rem;
  color: #f59e0b;
  margin-bottom: 0.5rem;
  padding: 0.5rem;
  background: rgba(245, 158, 11, 0.1);
  border-radius: 0.25rem;
}

.warningsLabel {
  font-weight: 500;
  display: block;
  margin-bottom: 0.25rem;
}

.warnings ul {
  margin: 0;
  padding-left: 1rem;
}

.warnings li {
  line-height: 1.5;
}

.assumptions {
  font-size: 0.75rem;
  color: #9ca3af;
}

.assumptionsLabel {
  font-weight: 500;
  color: #6b7280;
  display: block;
  margin-bottom: 0.25rem;
}

.assumptions ul {
  margin: 0;
  padding-left: 1rem;
}

.assumptions li {
  line-height: 1.5;
}
</style>
