<script setup lang="ts">
/**
 * SnapshotExchangeSection — Consolidated snapshot exchange workflow
 *
 * Dev Order 42: Groups snapshot, export metadata, and import validation
 * into a single visible section.
 *
 * Does NOT forward emits, persist, restore, or upload.
 */
import type { DiagnosticSnapshot, DiagnosticSnapshotExportMetadata } from '@/types/diagnosticSnapshot'
import DiagnosticSnapshotCard from './DiagnosticSnapshotCard.vue'
import DiagnosticSnapshotExportMetadataCard from './DiagnosticSnapshotExportMetadataCard.vue'
import DiagnosticSnapshotImportCard from './DiagnosticSnapshotImportCard.vue'

defineProps<{
  snapshot: DiagnosticSnapshot
  exportMetadata: DiagnosticSnapshotExportMetadata
}>()
</script>

<template>
  <section :class="$style.section">
    <div :class="$style.header">
      <h3 :class="$style.heading">Snapshot Exchange</h3>
    </div>

    <p :class="$style.description">
      Export and validate observational diagnostic snapshots locally. Snapshots may contain
      partial or sparse diagnostic state depending on available measurements and estimates.
    </p>
    <p :class="$style.boundary">
      No restore, upload, persistence, or calibration is performed.
    </p>

    <div :class="$style.cards">
      <DiagnosticSnapshotCard :snapshot="snapshot" />

      <DiagnosticSnapshotExportMetadataCard
        :metadata="exportMetadata"
        :warnings="snapshot.exportWarnings"
      />

      <DiagnosticSnapshotImportCard />
    </div>
  </section>
</template>

<style module>
.section {
  background: #0d1117;
  border: 1px solid #30363d;
  border-radius: 0.5rem;
  padding: 0.75rem;
}

.header {
  margin-bottom: 0.5rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #30363d;
}

.heading {
  margin: 0;
  font-size: 0.9375rem;
  font-weight: 600;
  color: #f0f6fc;
}

.description {
  margin: 0 0 0.5rem 0;
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
  gap: 0.625rem;
}
</style>
