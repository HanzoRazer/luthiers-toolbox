<script setup lang="ts">
/**
 * MeasuredResponseCard — Display and edit measured acoustic response
 *
 * Dev Order 19: Measured response is separate from AcousticState.
 * Dev Order 20: Added manual entry controls.
 *
 * - AcousticState = estimated/descriptive (geometry-derived)
 * - MeasuredResponse = observed/measured (actual measurements)
 */
import { computed, ref } from 'vue'
import { GateBadge } from '@/components/shared/workflow'
import type { MeasuredResponse } from '@/types/measurements'
import {
  hasMeasuredResponseData,
  getMeasurementSourceLabel,
  getMeasurementMethodLabel,
} from '@/utils/acoustics/measuredResponse'

const props = withDefaults(
  defineProps<{
    response: MeasuredResponse
    editable?: boolean
  }>(),
  {
    editable: true,
  }
)

const emit = defineEmits<{
  (e: 'update:response', value: MeasuredResponse): void
}>()

const hasData = computed(() => hasMeasuredResponseData(props.response))

const isEditing = ref(false)

const localHelmholtz = ref<number | null>(null)
const localQ = ref<number | null>(null)
const localPeak = ref<number | null>(null)
const localNote = ref('')

function startEditing() {
  localHelmholtz.value = props.response.measuredHelmholtzHz ?? null
  localQ.value = props.response.measuredQ ?? null
  localPeak.value = props.response.dominantPeakHz ?? null
  localNote.value = ''
  isEditing.value = true
}

function cancelEditing() {
  isEditing.value = false
}

function saveChanges() {
  const updated: MeasuredResponse = {
    ...props.response,
    source: 'manual',
    method: 'manual_observation',
  }

  if (localHelmholtz.value !== null && localHelmholtz.value > 0) {
    updated.measuredHelmholtzHz = localHelmholtz.value
  } else {
    updated.measuredHelmholtzHz = undefined
  }

  if (localQ.value !== null && localQ.value > 0) {
    updated.measuredQ = localQ.value
  } else {
    updated.measuredQ = undefined
  }

  if (localPeak.value !== null && localPeak.value > 0) {
    updated.dominantPeakHz = localPeak.value
  } else {
    updated.dominantPeakHz = undefined
  }

  if (localNote.value.trim()) {
    updated.notes = [...(props.response.notes ?? []), localNote.value.trim()]
  }

  emit('update:response', updated)
  isEditing.value = false
}
</script>

<template>
  <div :class="$style.card">
    <!-- Header -->
    <div :class="$style.header">
      <span :class="$style.label">{{ response.label }}</span>
      <GateBadge gate="yellow" label="Measured" />
    </div>

    <!-- Metadata -->
    <div :class="$style.meta">
      <div :class="$style.row">
        <span :class="$style.key">Source:</span>
        <span :class="$style.value">{{ getMeasurementSourceLabel(response.source) }}</span>
      </div>
      <div :class="$style.row">
        <span :class="$style.key">Method:</span>
        <span :class="$style.value">{{ getMeasurementMethodLabel(response.method) }}</span>
      </div>
    </div>

    <!-- Editing Form -->
    <div v-if="isEditing" :class="$style.editForm">
      <div :class="$style.field">
        <label :class="$style.fieldLabel">Measured Helmholtz (Hz)</label>
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
        <label :class="$style.fieldLabel">Measured Q</label>
        <input
          v-model.number="localQ"
          type="number"
          :class="$style.input"
          min="0"
          step="0.1"
          placeholder="e.g., 12.5"
        />
      </div>
      <div :class="$style.field">
        <label :class="$style.fieldLabel">Dominant Peak (Hz)</label>
        <input
          v-model.number="localPeak"
          type="number"
          :class="$style.input"
          min="0"
          step="0.1"
          placeholder="e.g., 102.3"
        />
      </div>
      <div :class="$style.field">
        <label :class="$style.fieldLabel">Add Note</label>
        <textarea
          v-model="localNote"
          :class="$style.textarea"
          rows="2"
          placeholder="Optional measurement note..."
        />
      </div>
      <div :class="$style.editActions">
        <button :class="$style.btnCancel" @click="cancelEditing">Cancel</button>
        <button :class="$style.btnSave" @click="saveChanges">Save</button>
      </div>
    </div>

    <!-- Measured Values (display mode) -->
    <template v-else>
      <div v-if="hasData" :class="$style.measurements">
        <div v-if="response.measuredHelmholtzHz !== undefined" :class="$style.row">
          <span :class="$style.key">Helmholtz:</span>
          <span :class="$style.measureValue">{{ response.measuredHelmholtzHz.toFixed(1) }} Hz</span>
        </div>
        <div v-if="response.measuredQ !== undefined" :class="$style.row">
          <span :class="$style.key">Q Factor:</span>
          <span :class="$style.measureValue">{{ response.measuredQ.toFixed(1) }}</span>
        </div>
        <div v-if="response.dominantPeakHz !== undefined" :class="$style.row">
          <span :class="$style.key">Dominant Peak:</span>
          <span :class="$style.measureValue">{{ response.dominantPeakHz.toFixed(1) }} Hz</span>
        </div>
      </div>

      <!-- No Data Message -->
      <div v-else :class="$style.noData">
        No measured response data attached yet.
      </div>

      <!-- Edit Button -->
      <button v-if="editable" :class="$style.editBtn" @click="startEditing">
        Enter Measurements
      </button>
    </template>

    <!-- Informational Notice -->
    <div :class="$style.infoNotice">
      Manual measurements are informational only and are not yet used for calibrated prediction.
    </div>

    <!-- Distinction Notice -->
    <div :class="$style.notice">
      Measured response is separate from estimated acoustic state.
    </div>

    <!-- Warnings -->
    <div v-if="response.warnings?.length" :class="$style.warnings">
      <span :class="$style.warningsLabel">Warnings:</span>
      <ul>
        <li v-for="(warning, i) in response.warnings" :key="i">
          {{ warning }}
        </li>
      </ul>
    </div>

    <!-- Notes -->
    <div v-if="response.notes?.length" :class="$style.notes">
      <span :class="$style.notesLabel">Notes:</span>
      <ul>
        <li v-for="(note, i) in response.notes" :key="i">
          {{ note }}
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

.measurements {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 0.5rem;
  background: rgba(16, 185, 129, 0.1);
  border-radius: 0.25rem;
  margin-bottom: 0.5rem;
}

.measureValue {
  font-size: 0.875rem;
  font-weight: 600;
  color: #10b981;
  font-family: var(--font-mono, ui-monospace, monospace);
}

.noData {
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

.input,
.textarea {
  padding: 0.375rem 0.5rem;
  background: #1f2937;
  border: 1px solid #374151;
  border-radius: 0.25rem;
  color: #f9fafb;
  font-size: 0.8125rem;
  font-family: var(--font-mono, ui-monospace, monospace);
}

.input:focus,
.textarea:focus {
  outline: none;
  border-color: #6366f1;
}

.textarea {
  resize: vertical;
  min-height: 2.5rem;
  font-family: inherit;
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

.infoNotice {
  font-size: 0.6875rem;
  color: #fbbf24;
  font-style: italic;
  padding: 0.375rem 0.5rem;
  background: rgba(251, 191, 36, 0.1);
  border-radius: 0.25rem;
  margin-bottom: 0.5rem;
}

.notice {
  font-size: 0.6875rem;
  color: #9ca3af;
  font-style: italic;
  padding: 0.375rem 0.5rem;
  background: rgba(99, 102, 241, 0.1);
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

.notes {
  font-size: 0.75rem;
  color: #9ca3af;
}

.notesLabel {
  font-weight: 500;
  color: #6b7280;
  display: block;
  margin-bottom: 0.25rem;
}

.notes ul {
  margin: 0;
  padding-left: 1rem;
}

.notes li {
  line-height: 1.5;
}
</style>
