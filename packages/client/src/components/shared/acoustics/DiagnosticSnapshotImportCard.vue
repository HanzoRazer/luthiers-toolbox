<script setup lang="ts">
/**
 * DiagnosticSnapshotImportCard — Import validation for diagnostic snapshots
 *
 * Dev Order 39: Validates exported diagnostic snapshot JSON files
 * without restoring them into application state.
 *
 * Validation only — does NOT mutate state, restore sessions, or perform calibration.
 */
import { ref, computed } from 'vue'
import { GateBadge } from '@/components/shared/workflow'
import type { DiagnosticSnapshotImportValidation } from '@/types/diagnosticSnapshotImport'
import {
  validateDiagnosticSnapshotJsonImport,
  getImportGateColor,
  getImportGateLabel,
} from '@/utils/acoustics/diagnosticSnapshotImport'

const emit = defineEmits<{
  validated: [validation: DiagnosticSnapshotImportValidation]
}>()

const fileInput = ref<HTMLInputElement | null>(null)
const selectedFileName = ref<string | null>(null)
const parseError = ref<string | null>(null)
const validation = ref<DiagnosticSnapshotImportValidation | null>(null)

const hasValidation = computed(() => validation.value !== null)

function handleFileSelect(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]

  if (!file) {
    reset()
    return
  }

  selectedFileName.value = file.name
  parseError.value = null
  validation.value = null

  const reader = new FileReader()

  reader.onload = (e) => {
    const text = e.target?.result as string

    try {
      const parsed = JSON.parse(text)
      const result = validateDiagnosticSnapshotJsonImport(parsed)
      validation.value = result
      emit('validated', result)
    } catch (err) {
      parseError.value = 'Failed to parse JSON file.'
      validation.value = null
    }
  }

  reader.onerror = () => {
    parseError.value = 'Failed to read file.'
    validation.value = null
  }

  reader.readAsText(file)
}

function reset() {
  selectedFileName.value = null
  parseError.value = null
  validation.value = null
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

function formatTimestamp(iso: string): string {
  const date = new Date(iso)
  if (isNaN(date.getTime())) return 'Invalid'
  return date.toLocaleString()
}
</script>

<template>
  <div :class="$style.card">
    <div :class="$style.header">
      <span :class="$style.label">Import Validation</span>
      <GateBadge
        v-if="validation"
        :gate="getImportGateColor(validation.overallGate)"
        :label="getImportGateLabel(validation.overallGate)"
      />
    </div>

    <!-- Empty State Guidance -->
    <p v-if="!hasValidation && !parseError" :class="$style.guidance">
      Select a diagnostic snapshot JSON file to validate schema compatibility.
    </p>

    <!-- File Input -->
    <div :class="$style.fileSection">
      <input
        ref="fileInput"
        type="file"
        accept=".json"
        :class="$style.fileInput"
        @change="handleFileSelect"
      />
      <span v-if="selectedFileName" :class="$style.fileName">{{ selectedFileName }}</span>
    </div>

    <!-- Parse Error -->
    <div v-if="parseError" :class="$style.error">
      {{ parseError }}
    </div>

    <!-- Validation Result -->
    <template v-if="validation">
      <!-- Metadata -->
      <div :class="$style.metadata">
        <div :class="$style.metaItem">
          <span :class="$style.metaLabel">Schema</span>
          <span :class="$style.metaValue">{{ validation.schemaVersion ?? 'Unknown' }}</span>
        </div>
        <div :class="$style.metaItem">
          <span :class="$style.metaLabel">Kind</span>
          <span :class="$style.metaValue">{{ validation.kind ?? 'Unknown' }}</span>
        </div>
        <div :class="$style.metaItem">
          <span :class="$style.metaLabel">Sections</span>
          <span :class="$style.metaValue">{{ validation.sectionCount ?? 0 }}</span>
        </div>
        <div v-if="validation.createdAtIso" :class="$style.metaItem">
          <span :class="$style.metaLabel">Created</span>
          <span :class="$style.metaValue">{{ formatTimestamp(validation.createdAtIso) }}</span>
        </div>
      </div>

      <!-- Status Message -->
      <div :class="[$style.statusMessage, validation.valid ? $style.statusValid : $style.statusInvalid]">
        <template v-if="validation.valid">
          Snapshot schema is valid for diagnostic review.
        </template>
        <template v-else>
          Snapshot schema does not match expected workspace format.
        </template>
      </div>

      <!-- Diagnostics -->
      <div v-if="validation.diagnostics.length > 0" :class="$style.diagnostics">
        <span :class="$style.diagnosticsLabel">Diagnostics</span>
        <div
          v-for="diag in validation.diagnostics"
          :key="diag.id"
          :class="[$style.diagnostic, $style[`diag-${diag.gate}`]]"
        >
          <span :class="$style.diagMessage">{{ diag.message }}</span>
          <span v-if="diag.recommendedAction" :class="$style.diagAction">
            {{ diag.recommendedAction }}
          </span>
        </div>
      </div>

      <!-- Clear Button -->
      <button :class="$style.clearButton" @click="reset">Clear</button>
    </template>

    <!-- Warning Notice -->
    <div :class="$style.notice">
      Import validation checks exported snapshot structure only. It does not restore or apply
      snapshot data.
    </div>
  </div>
</template>

<style module>
.card {
  background: #111827;
  border: 1px solid #30363d;
  border-radius: 0.375rem;
  padding: 0.75rem;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.5rem;
  padding-bottom: 0.375rem;
  border-bottom: 1px solid #30363d;
}

.label {
  font-size: 0.8125rem;
  font-weight: 500;
  color: #d1d5db;
}

.guidance {
  margin: 0 0 0.5rem 0;
  padding: 0.5rem;
  background: rgba(99, 102, 241, 0.08);
  border-radius: 0.25rem;
  font-size: 0.6875rem;
  color: #a5b4fc;
}

.fileSection {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  padding: 0.5rem;
  background: #1f2937;
  border-radius: 0.25rem;
}

.fileInput {
  font-size: 0.75rem;
  color: #d1d5db;
}

.fileInput:focus-visible {
  outline: none;
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.5);
  border-radius: 0.25rem;
}

.fileInput::file-selector-button {
  padding: 0.25rem 0.5rem;
  background: #374151;
  color: #f9fafb;
  border: 1px solid #4b5563;
  border-radius: 0.25rem;
  font-size: 0.6875rem;
  cursor: pointer;
  margin-right: 0.5rem;
  transition: background-color 0.15s ease;
}

.fileInput::file-selector-button:hover {
  background: #4b5563;
}

.fileName {
  font-size: 0.75rem;
  color: #9ca3af;
  font-style: italic;
}

.error {
  margin-bottom: 0.5rem;
  padding: 0.375rem 0.5rem;
  background: rgba(239, 68, 68, 0.1);
  border-radius: 0.25rem;
  font-size: 0.6875rem;
  color: #ef4444;
}

.metadata {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  padding: 0.5rem;
  background: rgba(55, 65, 81, 0.5);
  border-radius: 0.25rem;
}

.metaItem {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}

.metaLabel {
  font-size: 0.5625rem;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.metaValue {
  font-size: 0.6875rem;
  font-weight: 500;
  color: #d1d5db;
  font-family: var(--font-mono, ui-monospace, monospace);
}

.statusMessage {
  margin-bottom: 0.5rem;
  padding: 0.375rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.6875rem;
}

.statusValid {
  background: rgba(16, 185, 129, 0.08);
  color: #10b981;
}

.statusInvalid {
  background: rgba(239, 68, 68, 0.08);
  color: #ef4444;
}

.diagnostics {
  margin-bottom: 0.5rem;
  padding: 0.375rem 0.5rem;
  background: rgba(107, 114, 128, 0.1);
  border-radius: 0.25rem;
}

.diagnosticsLabel {
  display: block;
  font-size: 0.5625rem;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.25rem;
}

.diagnostic {
  padding: 0.25rem 0.375rem;
  margin-bottom: 0.25rem;
  border-radius: 0.125rem;
  border-left: 2px solid;
}

.diagnostic:last-child {
  margin-bottom: 0;
}

.diag-red {
  background: rgba(239, 68, 68, 0.05);
  border-left-color: #ef4444;
}

.diag-yellow {
  background: rgba(251, 191, 36, 0.05);
  border-left-color: #fbbf24;
}

.diag-green {
  background: rgba(16, 185, 129, 0.05);
  border-left-color: #10b981;
}

.diagMessage {
  display: block;
  font-size: 0.625rem;
  color: #d1d5db;
}

.diagAction {
  display: block;
  font-size: 0.5625rem;
  color: #9ca3af;
  font-style: italic;
  margin-top: 0.125rem;
}

.clearButton {
  padding: 0.25rem 0.5rem;
  background: #374151;
  color: #d1d5db;
  border: 1px solid #4b5563;
  border-radius: 0.25rem;
  font-size: 0.6875rem;
  cursor: pointer;
  margin-bottom: 0.5rem;
  transition: background-color 0.15s ease, box-shadow 0.15s ease;
}

.clearButton:hover {
  background: #4b5563;
}

.clearButton:focus-visible {
  outline: none;
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.5);
}

.notice {
  padding: 0.375rem 0.5rem;
  background: rgba(251, 191, 36, 0.08);
  border-radius: 0.25rem;
  font-size: 0.6875rem;
  color: #fbbf24;
}
</style>
