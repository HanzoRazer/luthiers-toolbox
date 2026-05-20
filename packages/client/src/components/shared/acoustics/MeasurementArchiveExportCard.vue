<script setup lang="ts">
/**
 * MeasurementArchiveExportCard — Export current measurement archive
 *
 * Dev Order 60: Displays archive metadata and provides local JSON export.
 * Dev Order 61: Uses standardized filename builder.
 *
 * Observational only — does NOT upload, persist, or calibrate.
 */
import type { MeasurementArchiveRecord } from '@/types/acoustics/measurementArchive'
import {
  formatArchiveTimestamp,
  buildMeasurementArchiveFilename,
} from '@/utils/acoustics/measurementArchive'

const props = defineProps<{
  archive: MeasurementArchiveRecord | null
}>()

const emit = defineEmits<{
  export: [archive: MeasurementArchiveRecord]
}>()

function handleExport() {
  if (!props.archive) return

  const json = JSON.stringify(props.archive, null, 2)
  const blob = new Blob([json], { type: 'application/json' })
  const url = URL.createObjectURL(blob)

  const link = document.createElement('a')
  link.href = url
  link.download = buildMeasurementArchiveFilename(props.archive)
  link.click()

  URL.revokeObjectURL(url)
  emit('export', props.archive)
}

function getMeasurementSources(): string[] {
  if (!props.archive) return []
  const sources = new Set(props.archive.measurements.map((m) => m.source))
  return Array.from(sources)
}
</script>

<template>
  <div :class="$style.card">
    <div :class="$style.header">
      <span :class="$style.label">Archive Export</span>
      <span v-if="archive" :class="$style.badge">Ready</span>
      <span v-else :class="$style.badgeEmpty">Empty</span>
    </div>

    <!-- Empty State -->
    <div v-if="!archive" :class="$style.emptyState">
      <p :class="$style.emptyText">No archive created yet.</p>
      <p :class="$style.emptyHint">Use "Archive Measurement" to capture current experimental state.</p>
    </div>

    <!-- Archive Details -->
    <template v-else>
      <div :class="$style.metaGroup">
        <span :class="$style.groupLabel">Archive</span>
        <div :class="$style.metadata">
          <div :class="$style.metaItem">
            <span :class="$style.metaLabel">ID</span>
            <span :class="$style.metaValue">{{ archive.archiveId }}</span>
          </div>
          <div :class="$style.metaItem">
            <span :class="$style.metaLabel">Created</span>
            <span :class="$style.metaValue">{{ formatArchiveTimestamp(archive.metadata.createdAtIso) }}</span>
          </div>
          <div :class="$style.metaItem">
            <span :class="$style.metaLabel">Measurements</span>
            <span :class="$style.metaValue">{{ archive.measurements.length }}</span>
          </div>
          <div :class="$style.metaItem">
            <span :class="$style.metaLabel">Schema</span>
            <span :class="$style.metaValue">{{ archive.metadata.schemaVersion }}</span>
          </div>
        </div>
      </div>

      <!-- Context Summary -->
      <div v-if="archive.context.referenceLabel || archive.context.candidateLabel" :class="$style.metaGroup">
        <span :class="$style.groupLabel">Context</span>
        <div :class="$style.metadata">
          <div v-if="archive.context.referenceLabel" :class="$style.metaItem">
            <span :class="$style.metaLabel">Reference</span>
            <span :class="$style.metaValue">{{ archive.context.referenceLabel }}</span>
          </div>
          <div v-if="archive.context.candidateLabel" :class="$style.metaItem">
            <span :class="$style.metaLabel">Candidate</span>
            <span :class="$style.metaValue">{{ archive.context.candidateLabel }}</span>
          </div>
        </div>
      </div>

      <!-- Sources -->
      <div v-if="getMeasurementSources().length > 0" :class="$style.sources">
        <span :class="$style.sourcesLabel">Sources</span>
        <div :class="$style.sourceList">
          <span v-for="source in getMeasurementSources()" :key="source" :class="$style.sourceTag">
            {{ source }}
          </span>
        </div>
      </div>

      <!-- Tags -->
      <div v-if="archive.tags && archive.tags.length > 0" :class="$style.tags">
        <span v-for="tag in archive.tags" :key="tag" :class="$style.tag">{{ tag }}</span>
      </div>

      <!-- Export Button -->
      <button :class="$style.exportButton" @click="handleExport">
        Export JSON
      </button>
    </template>

    <!-- Notice -->
    <div :class="$style.notice">
      {{ archive?.provenanceReminder ?? 'Archives contain observational measurements only.' }}
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

.badge {
  font-size: 0.5625rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
}

.badgeEmpty {
  font-size: 0.5625rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
  background: rgba(107, 114, 128, 0.15);
  color: #6b7280;
}

.emptyState {
  padding: 0.5rem;
  background: rgba(107, 114, 128, 0.08);
  border-radius: 0.25rem;
  margin-bottom: 0.5rem;
}

.emptyText {
  margin: 0 0 0.25rem 0;
  font-size: 0.75rem;
  color: #9ca3af;
}

.emptyHint {
  margin: 0;
  font-size: 0.6875rem;
  color: #6b7280;
  font-style: italic;
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
  padding: 0.375rem;
  background: rgba(55, 65, 81, 0.4);
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

.sources {
  margin-bottom: 0.5rem;
}

.sourcesLabel {
  display: block;
  font-size: 0.5rem;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.25rem;
}

.sourceList {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
}

.sourceTag {
  font-size: 0.5625rem;
  padding: 0.125rem 0.375rem;
  background: rgba(99, 102, 241, 0.15);
  border-radius: 0.25rem;
  color: #a5b4fc;
  font-family: var(--font-mono, ui-monospace, monospace);
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  margin-bottom: 0.5rem;
}

.tag {
  font-size: 0.5625rem;
  padding: 0.125rem 0.375rem;
  background: rgba(107, 114, 128, 0.2);
  border-radius: 0.25rem;
  color: #9ca3af;
}

.exportButton {
  width: 100%;
  padding: 0.5rem;
  background: #374151;
  color: #f9fafb;
  border: 1px solid #4b5563;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  margin-bottom: 0.5rem;
  transition: background-color 0.15s ease, box-shadow 0.15s ease;
}

.exportButton:hover {
  background: #4b5563;
}

.exportButton:focus-visible {
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
