<script setup lang="ts">
/**
 * MeasurementArchiveExchangeSection — Consolidated measurement archive workflow
 *
 * Dev Order 60: Groups archive export, import validation, and preview
 * into a single visible section for experimental workflow continuity.
 *
 * Does NOT persist, upload, restore, or calibrate.
 */
import type {
  MeasurementArchiveRecord,
  MeasurementArchiveValidationResult,
} from '@/types/acoustics/measurementArchive'
import MeasurementArchiveExportCard from './MeasurementArchiveExportCard.vue'
import MeasurementArchiveImportCard from './MeasurementArchiveImportCard.vue'
import MeasurementArchivePreviewCard from './MeasurementArchivePreviewCard.vue'

const props = defineProps<{
  archive: MeasurementArchiveRecord | null
  linkedSnapshotId?: string
}>()

const emit = defineEmits<{
  exported: [archive: MeasurementArchiveRecord]
  imported: [result: MeasurementArchiveValidationResult, archive: MeasurementArchiveRecord | null]
}>()

function handleExport(archive: MeasurementArchiveRecord) {
  emit('exported', archive)
}

function handleImportValidated(
  result: MeasurementArchiveValidationResult,
  archive: MeasurementArchiveRecord | null
) {
  emit('imported', result, archive)
}
</script>

<template>
  <section :class="$style.section">
    <div :class="$style.header">
      <h3 :class="$style.heading">Measurement Archive Exchange</h3>
    </div>

    <p :class="$style.description">
      Export and validate observational measurement archives locally. Archives capture
      experimental measurement state for future comparison and analysis.
    </p>
    <p :class="$style.boundary">
      No restore, upload, persistence, or calibration is performed.
    </p>

    <div :class="$style.cards">
      <!-- Export Card -->
      <MeasurementArchiveExportCard :archive="archive" @export="handleExport" />

      <!-- Import Card -->
      <MeasurementArchiveImportCard @validated="handleImportValidated" />

      <!-- Preview Card (when archive exists) -->
      <MeasurementArchivePreviewCard v-if="archive" :archive="archive" />
    </div>

    <!-- Provenance Chain -->
    <div v-if="linkedSnapshotId || archive?.measurements.some(m => m.diagnosticSnapshotReference)" :class="$style.provenance">
      <span :class="$style.provenanceLabel">Provenance Chain</span>
      <div :class="$style.provenanceList">
        <span v-if="linkedSnapshotId" :class="$style.provenanceItem">
          Linked Snapshot: {{ linkedSnapshotId }}
        </span>
        <template v-if="archive">
          <span
            v-for="m in archive.measurements.filter(m => m.diagnosticSnapshotReference?.snapshotId)"
            :key="m.measurementId"
            :class="$style.provenanceItem"
          >
            {{ m.label ?? m.measurementId }} → {{ m.diagnosticSnapshotReference?.snapshotId }}
          </span>
        </template>
      </div>
    </div>
  </section>
</template>

<style module>
.section {
  background: #0d1117;
  border: 1px solid #30363d;
  border-radius: 0.5rem;
  padding: 1rem;
}

.header {
  margin-bottom: 0.5rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #30363d;
}

.heading {
  margin: 0;
  font-size: 1.0625rem;
  font-weight: 600;
  color: #f0f6fc;
}

.description {
  margin: 0 0 0.375rem 0;
  font-size: 0.75rem;
  color: #8b949e;
  line-height: 1.5;
}

.boundary {
  margin: 0 0 0.75rem 0;
  font-size: 0.6875rem;
  color: #6b7280;
  font-style: italic;
}

.cards {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.provenance {
  margin-top: 0.75rem;
  padding: 0.5rem;
  background: rgba(99, 102, 241, 0.08);
  border-radius: 0.25rem;
}

.provenanceLabel {
  display: block;
  font-size: 0.5625rem;
  color: #a5b4fc;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.375rem;
}

.provenanceList {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.provenanceItem {
  font-size: 0.6875rem;
  color: #d1d5db;
  font-family: var(--font-mono, ui-monospace, monospace);
  padding: 0.125rem 0.25rem;
  background: rgba(55, 65, 81, 0.4);
  border-radius: 0.125rem;
}
</style>
