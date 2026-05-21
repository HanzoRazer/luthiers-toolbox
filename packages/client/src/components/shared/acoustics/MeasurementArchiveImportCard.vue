<script setup lang="ts">
/**
 * MeasurementArchiveImportCard — Import and validate measurement archive
 *
 * Dev Order 60: Imports measurement archive from JSON file with validation.
 * Dev Order 64: Added duplicate detection via existingArchiveIds prop.
 * Structural validation only — does not apply, calibrate, or predict.
 */
import { ref, computed } from 'vue'
import { GateBadge, SectionLabel } from '@/components/shared/workflow'
import type {
  MeasurementArchiveRecord,
  MeasurementArchiveValidationResult,
} from '@/types/acoustics/measurementArchive'
import {
  validateMeasurementArchive,
  formatArchiveTimestamp,
} from '@/utils/acoustics/measurementArchive'

const props = defineProps<{
  existingArchiveIds?: string[]
}>()

const emit = defineEmits<{
  imported: [result: MeasurementArchiveValidationResult, archive: MeasurementArchiveRecord | null]
}>()

const importedArchive = ref<MeasurementArchiveRecord | null>(null)
const validationResult = ref<MeasurementArchiveValidationResult | null>(null)
const fileInputRef = ref<HTMLInputElement | null>(null)

const existingIdsSet = computed(() => new Set(props.existingArchiveIds ?? []))

function handleFileSelect(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]

  if (!file) return

  const reader = new FileReader()
  reader.onload = (e) => {
    const content = e.target?.result as string

    // Parse JSON first
    let data: unknown
    try {
      data = JSON.parse(content)
    } catch (err) {
      const validation: MeasurementArchiveValidationResult = {
        valid: false,
        errors: [`JSON parse error: ${err instanceof Error ? err.message : 'Unknown error'}`],
        warnings: [],
      }
      importedArchive.value = null
      validationResult.value = validation
      emit('imported', validation, null)
      return
    }

    // Validate with duplicate detection
    const validation = validateMeasurementArchive(data, existingIdsSet.value)

    const archive = validation.valid ? (data as MeasurementArchiveRecord) : null
    importedArchive.value = archive
    validationResult.value = validation

    emit('imported', validation, archive)
  }
  reader.readAsText(file)
}

function handleClear() {
  importedArchive.value = null
  validationResult.value = null
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
}

function getGateLevel(): 'green' | 'yellow' | 'red' {
  if (!validationResult.value) return 'yellow'
  if (!validationResult.value.valid) return 'red'
  if (validationResult.value.warnings.length > 0) return 'yellow'
  return 'green'
}

function getGateLabel(): string {
  if (!validationResult.value) return 'No File'
  if (!validationResult.value.valid) return 'Invalid'
  if (validationResult.value.warnings.length > 0) return 'Valid (warnings)'
  return 'Valid'
}
</script>

<template>
  <div :class="$style.card">
    <div :class="$style.header">
      <SectionLabel text="Import Archive" />
      <GateBadge :gate="getGateLevel()" :label="getGateLabel()" />
    </div>

    <!-- File Input -->
    <div :class="$style.inputRow">
      <input
        ref="fileInputRef"
        type="file"
        accept=".json"
        :class="$style.fileInput"
        @change="handleFileSelect"
      />
      <button
        v-if="validationResult"
        :class="$style.clearButton"
        @click="handleClear"
      >
        Clear
      </button>
    </div>

    <!-- Validation Result -->
    <div v-if="validationResult" :class="$style.result">
      <!-- Metadata -->
      <div v-if="validationResult.metadata" :class="$style.metadata">
        <div v-if="validationResult.metadata.schemaVersion" :class="$style.metaItem">
          <span :class="$style.metaLabel">Schema</span>
          <span :class="$style.metaValue">{{ validationResult.metadata.schemaVersion }}</span>
        </div>
        <div v-if="validationResult.metadata.sectionCount !== undefined" :class="$style.metaItem">
          <span :class="$style.metaLabel">Sections</span>
          <span :class="$style.metaValue">{{ validationResult.metadata.sectionCount }}</span>
        </div>
        <div v-if="validationResult.metadata.createdAtIso" :class="$style.metaItem">
          <span :class="$style.metaLabel">Created</span>
          <span :class="$style.metaValue">{{ formatArchiveTimestamp(validationResult.metadata.createdAtIso) }}</span>
        </div>
      </div>

      <!-- Errors -->
      <div v-if="validationResult.errors.length > 0" :class="$style.errors">
        <span :class="$style.errorsLabel">Errors</span>
        <ul :class="$style.errorsList">
          <li v-for="(error, idx) in validationResult.errors" :key="idx">{{ error }}</li>
        </ul>
      </div>

      <!-- Warnings -->
      <div v-if="validationResult.warnings.length > 0" :class="$style.warnings">
        <span :class="$style.warningsLabel">Warnings</span>
        <ul :class="$style.warningsList">
          <li v-for="(warning, idx) in validationResult.warnings" :key="idx">{{ warning }}</li>
        </ul>
      </div>

      <!-- Status Message -->
      <div :class="$style.status">
        <span v-if="validationResult.valid" :class="$style.statusValid">
          Archive is valid for review.
        </span>
        <span v-else :class="$style.statusInvalid">
          Archive cannot be used.
        </span>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else :class="$style.emptyState">
      <p>Select a measurement archive JSON file to import.</p>
    </div>

    <div :class="$style.notice">
      Import validation checks structure only. It does not restore or apply archive data.
    </div>
  </div>
</template>

<style module>
.card {
  background: #0d1117;
  border: 1px solid #30363d;
  border-radius: 0.5rem;
  padding: 1rem;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #30363d;
}

.inputRow {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.fileInput {
  flex: 1;
  padding: 0.375rem;
  background: #1f2937;
  border: 1px solid #374151;
  border-radius: 0.25rem;
  color: #d1d5db;
  font-size: 0.75rem;
}

.fileInput::file-selector-button {
  padding: 0.25rem 0.5rem;
  background: #374151;
  border: 1px solid #4b5563;
  border-radius: 0.25rem;
  color: #d1d5db;
  font-size: 0.6875rem;
  cursor: pointer;
  margin-right: 0.5rem;
}

.clearButton {
  padding: 0.375rem 0.75rem;
  background: transparent;
  border: 1px solid #374151;
  border-radius: 0.25rem;
  color: #9ca3af;
  font-size: 0.6875rem;
  cursor: pointer;
}

.clearButton:hover {
  background: #374151;
  color: #f9fafb;
}

.result {
  margin-bottom: 0.75rem;
}

.metadata {
  display: flex;
  gap: 1rem;
  margin-bottom: 0.5rem;
  padding: 0.5rem;
  background: #1f2937;
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
  font-size: 0.75rem;
  color: #d1d5db;
}

.errors {
  padding: 0.5rem;
  background: rgba(239, 68, 68, 0.08);
  border-radius: 0.25rem;
  margin-bottom: 0.5rem;
}

.errorsLabel {
  display: block;
  font-size: 0.5625rem;
  color: #ef4444;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.25rem;
}

.errorsList {
  margin: 0;
  padding-left: 1rem;
  font-size: 0.6875rem;
  color: #ef4444;
}

.warnings {
  padding: 0.5rem;
  background: rgba(251, 191, 36, 0.08);
  border-radius: 0.25rem;
  margin-bottom: 0.5rem;
}

.warningsLabel {
  display: block;
  font-size: 0.5625rem;
  color: #fbbf24;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.25rem;
}

.warningsList {
  margin: 0;
  padding-left: 1rem;
  font-size: 0.6875rem;
  color: #fbbf24;
}

.status {
  padding: 0.5rem;
  background: #1f2937;
  border-radius: 0.25rem;
  text-align: center;
}

.statusValid {
  color: #10b981;
  font-size: 0.75rem;
}

.statusInvalid {
  color: #ef4444;
  font-size: 0.75rem;
}

.emptyState {
  padding: 1rem;
  background: rgba(107, 114, 128, 0.08);
  border-radius: 0.25rem;
  text-align: center;
  margin-bottom: 0.75rem;
}

.emptyState p {
  margin: 0;
  font-size: 0.75rem;
  color: #9ca3af;
}

.notice {
  font-size: 0.625rem;
  color: #6b7280;
  text-align: center;
}
</style>
