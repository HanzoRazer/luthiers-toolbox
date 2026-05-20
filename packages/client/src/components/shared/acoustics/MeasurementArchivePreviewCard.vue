<script setup lang="ts">
/**
 * MeasurementArchivePreviewCard — Read-only archive preview
 *
 * Dev Order 54: Minimal visual verification surface for measurement archives.
 *
 * Shows:
 * - Archive ID
 * - Schema version
 * - Created timestamp
 * - Measurement count
 * - Observational-only notice
 *
 * Does NOT provide archive management, mutation, or browser UI.
 */
import type { MeasurementArchiveRecord } from '@/types/acoustics/measurementArchive'
import { formatArchiveTimestamp } from '@/utils/acoustics/measurementArchive'

defineProps<{
  archive: MeasurementArchiveRecord
}>()
</script>

<template>
  <div :class="$style.card">
    <div :class="$style.header">
      <span :class="$style.label">Measurement Archive</span>
      <span :class="$style.badge">Preview</span>
    </div>

    <!-- Metadata Group -->
    <div :class="$style.metaGroup">
      <span :class="$style.groupLabel">Archive</span>
      <div :class="$style.metadata">
        <div :class="$style.metaItem">
          <span :class="$style.metaLabel">ID</span>
          <span :class="$style.metaValue">{{ archive.archiveId }}</span>
        </div>
        <div :class="$style.metaItem">
          <span :class="$style.metaLabel">Schema</span>
          <span :class="$style.metaValue">{{ archive.metadata.schemaVersion }}</span>
        </div>
        <div :class="$style.metaItem">
          <span :class="$style.metaLabel">Created</span>
          <span :class="$style.metaValue">{{ formatArchiveTimestamp(archive.metadata.createdAtIso) }}</span>
        </div>
        <div :class="$style.metaItem">
          <span :class="$style.metaLabel">Measurements</span>
          <span :class="$style.metaValue">{{ archive.measurements.length }}</span>
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

    <!-- Tags -->
    <div v-if="archive.tags && archive.tags.length > 0" :class="$style.tags">
      <span v-for="tag in archive.tags" :key="tag" :class="$style.tag">{{ tag }}</span>
    </div>

    <!-- Observational Notice -->
    <div :class="$style.notice">
      {{ archive.provenanceReminder }}
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
  background: rgba(99, 102, 241, 0.15);
  color: #a5b4fc;
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

.notice {
  margin-top: 0.25rem;
  padding: 0.375rem 0.5rem;
  background: rgba(251, 191, 36, 0.08);
  border-radius: 0.25rem;
  font-size: 0.6875rem;
  color: #fbbf24;
}
</style>
