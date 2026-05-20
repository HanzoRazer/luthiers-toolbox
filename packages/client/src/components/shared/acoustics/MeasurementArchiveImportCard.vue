<script setup lang="ts">
/**
 * MeasurementArchiveImportCard — Import validation for measurement archives
 *
 * Dev Order 60: Validates exported measurement archive JSON files
 * without restoring them into application state.
 * Dev Order 61: Uses parseMeasurementArchiveJson helper.
 *
 * Validation only — does NOT mutate state, restore sessions, or perform calibration.
 */
import { ref, computed } from 'vue'
import { GateBadge } from '@/components/shared/workflow'
import type {
  MeasurementArchiveRecord,
  MeasurementArchiveValidationResult,
} from '@/types/acoustics/measurementArchive'
import {
  parseMeasurementArchiveJson,
  formatArchiveTimestamp,
} from '@/utils/acoustics/measurementArchive'

const emit = defineEmits<{
  validated: [result: MeasurementArchiveValidationResult, archive: MeasurementArchiveRecord | null]
}>()

const fileInput = ref<HTMLInputElement | null>(null)
const selectedFileName = ref<string | null>(null)
const parseError = ref<string | null>(null)
const validation = ref<MeasurementArchiveValidationResult | null>(null)
const importedArchive = ref<MeasurementArchiveRecord | null>(null)

const hasValidation = computed(() => validation.value !== null)

function getGateColor(valid: boolean): 'green' | 'red' {
  return valid ? 'green' : 'red'
}

function getGateLabel(valid: boolean): string {
  return valid ? 'Valid' : 'Invalid'
}

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
  importedArchive.value = null

  const reader = new FileReader()

  reader.onload = (e) => {
    const text = e.target?.result as string
    const result = parseMeasurementArchiveJson(text)

    if (result.parseError) {
      parseError.value = result.parseError
      validation.value = null
      importedArchive.value = null
      return
    }

    validation.value = result.validation
    importedArchive.value = result.archive

    if (result.validation) {
      emit('validated', result.validation, result.archive)
    }
  }

  reader.onerror = () => {
    parseError.value = 'Failed to read file.'
    validation.value = null
    importedArchive.value = null
  }

  reader.readAsText(file)
}

function reset() {
  selectedFileName.value = null
  parseError.value = null
  validation.value = null
  importedArchive.value = null
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}
</script>

<template>
  <div :class="$style.card">
    <div :class="$style.header">
      <span :class="$style.label">Archive Import</span>
      <GateBadge
        v-if="validation"
        :gate="getGateColor(validation.valid)"
        :label="getGateLabel(validation.valid)"
      />
    </div>

    <!-- Empty State Guidance -->
    <p v-if="!hasValidation && !parseError" :class="$style.guidance">
      Select a measurement archive JSON file to validate schema compatibility.
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
      <!-- Schema Info -->
      <div :class="$style.metaGroup">
        <span :class="$style.groupLabel">Schema</span>
        <div :class="$style.metadata">
          <div :class="$style.metaItem">
            <span :class="$style.metaLabel">Version</span>
            <span :class="$style.metaValue">{{ validation.schemaVersion ?? 'Unknown' }}</span>
          </div>
          <div :class="$style.metaItem">
            <span :class="$style.metaLabel">Measurements</span>
            <span :class="$style.metaValue">{{ validation.measurementCount ?? 0 }}</span>
          </div>
        </div>
      </div>

      <!-- Archive Details (if valid) -->
      <div v-if="importedArchive" :class="$style.metaGroup">
        <span :class="$style.groupLabel">Archive</span>
        <div :class="$style.metadata">
          <div :class="$style.metaItem">
            <span :class="$style.metaLabel">ID</span>
            <span :class="$style.metaValue">{{ importedArchive.archiveId }}</span>
          </div>
          <div :class="$style.metaItem">
            <span :class="$style.metaLabel">Created</span>
            <span :class="$style.metaValue">{{ formatArchiveTimestamp(importedArchive.metadata.createdAtIso) }}</span>
          </div>
        </div>
      </div>

      <!-- Status Message -->
      <div :class="[$style.statusMessage, validation.valid ? $style.statusValid : $style.statusInvalid]">
        <template v-if="validation.valid">
          Archive schema is valid for experimental review.
        </template>
        <template v-else>
          Archive schema does not match expected format.
        </template>
      </div>

      <!-- Errors -->
      <div v-if="validation.errors.length > 0" :class="$style.diagnostics">
        <span :class="$style.diagnosticsLabel">Errors</span>
        <div
          v-for="(error, idx) in validation.errors"
          :key="idx"
          :class="[$style.diagnostic, $style.diagError]"
        >
          <span :class="$style.diagMessage">{{ error }}</span>
        </div>
      </div>

      <!-- Warnings -->
      <div v-if="validation.warnings.length > 0" :class="$style.diagnostics">
        <span :class="$style.diagnosticsLabel">Warnings</span>
        <div
          v-for="(warning, idx) in validation.warnings"
          :key="idx"
          :class="[$style.diagnostic, $style.diagWarning]"
        >
          <span :class="$style.diagMessage">{{ warning }}</span>
        </div>
      </div>

      <!-- Clear Button -->
      <button :class="$style.clearButton" @click="reset">Clear</button>
    </template>

    <!-- Notice -->
    <div :class="$style.notice">
      Import validation checks archive structure only. It does not restore or apply archive data.
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
  padding: 0.375rem 0.5rem;
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
  transition: background-color 0.15s ease, box-shadow 0.15s ease;
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
  background: rgba(239, 68, 68, 0.08);
  border-radius: 0.25rem;
  font-size: 0.6875rem;
  color: #ef4444;
}

.metaGroup {
  margin-bottom: 0.5rem;
}

.groupLabel {
  display: block;
  font-size: 0.5rem;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.25rem;
}

.metadata {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.375rem;
  padding: 0.375rem 0.5rem;
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
  word-break: break-all;
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
  background: rgba(107, 114, 128, 0.08);
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
  margin-bottom: 0.125rem;
  border-radius: 0.125rem;
  border-left: 2px solid;
}

.diagnostic:last-child {
  margin-bottom: 0;
}

.diagError {
  background: rgba(239, 68, 68, 0.05);
  border-left-color: #ef4444;
}

.diagWarning {
  background: rgba(251, 191, 36, 0.05);
  border-left-color: #fbbf24;
}

.diagMessage {
  display: block;
  font-size: 0.625rem;
  color: #d1d5db;
}

.clearButton {
  padding: 0.25rem 0.5rem;
  background: #374151;
  color: #d1d5db;
  border: 1px solid #4b5563;
  border-radius: 0.25rem;
  font-size: 0.6875rem;
  cursor: pointer;
  margin-top: 0.375rem;
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
  margin-top: 0.25rem;
  padding: 0.375rem 0.5rem;
  background: rgba(251, 191, 36, 0.08);
  border-radius: 0.25rem;
  font-size: 0.6875rem;
  color: #fbbf24;
}
</style>
