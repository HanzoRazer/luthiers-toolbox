<script setup lang="ts">
/**
 * MeasurementArchivePreviewCard — Display archive contents
 *
 * Dev Order 60: Renders archive metadata and measurement summary.
 * Read-only preview — no mutation or application.
 */
import { computed } from 'vue'
import { GateBadge, SectionLabel } from '@/components/shared/workflow'
import type { MeasurementArchiveRecord } from '@/types/acoustics/measurementArchive'
import { formatArchiveTimestamp } from '@/utils/acoustics/measurementArchive'

const props = defineProps<{
  archive: MeasurementArchiveRecord
}>()

const label = computed(() =>
  props.archive.context.referenceLabel ?? props.archive.context.candidateLabel ?? 'Untitled'
)

const measurementCount = computed(() =>
  props.archive.sections.reduce((sum, s) => sum + s.measurements.length, 0)
)
</script>

<template>
  <div :class="$style.card">
    <div :class="$style.header">
      <SectionLabel :text="label" />
      <GateBadge gate="green" label="Archive" />
    </div>

    <!-- Metadata -->
    <div :class="$style.metadata">
      <div :class="$style.metaItem">
        <span :class="$style.metaLabel">Created</span>
        <span :class="$style.metaValue">{{ formatArchiveTimestamp(archive.metadata.createdAtIso) }}</span>
      </div>
      <div :class="$style.metaItem">
        <span :class="$style.metaLabel">Sections</span>
        <span :class="$style.metaValue">{{ archive.sections.length }}</span>
      </div>
      <div :class="$style.metaItem">
        <span :class="$style.metaLabel">Measurements</span>
        <span :class="$style.metaValue">{{ measurementCount }}</span>
      </div>
    </div>

    <!-- Context -->
    <div v-if="archive.context.sessionContext || archive.context.operator" :class="$style.context">
      <span v-if="archive.context.sessionContext" :class="$style.contextItem">
        {{ archive.context.sessionContext }}
      </span>
      <span v-if="archive.context.operator" :class="$style.contextItem">
        Operator: {{ archive.context.operator }}
      </span>
    </div>

    <!-- Sections -->
    <div :class="$style.sections">
      <div v-for="section in archive.sections" :key="section.sectionId" :class="$style.section">
        <div :class="$style.sectionHeader">
          <span :class="$style.sectionLabel">{{ section.label }}</span>
          <span :class="$style.sectionCount">{{ section.measurements.length }}</span>
        </div>
        <div :class="$style.measurements">
          <div v-for="m in section.measurements" :key="m.property" :class="$style.measurement">
            <span :class="$style.measurementProperty">{{ m.property }}</span>
            <span :class="$style.measurementValue">{{ m.value }} {{ m.unit }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Tags -->
    <div v-if="archive.metadata.tags?.length || archive.metadata.experimentTags?.length" :class="$style.tags">
      <span v-for="tag in archive.metadata.tags" :key="tag" :class="$style.tag">{{ tag }}</span>
      <span v-for="tag in archive.metadata.experimentTags" :key="tag" :class="[$style.tag, $style.experimentTag]">{{ tag }}</span>
    </div>

    <!-- Notes -->
    <div v-if="archive.metadata.notes" :class="$style.notes">
      <span :class="$style.notesLabel">Notes</span>
      <p :class="$style.notesText">{{ archive.metadata.notes }}</p>
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

.metadata {
  display: flex;
  gap: 1rem;
  margin-bottom: 0.75rem;
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

.context {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  margin-bottom: 0.75rem;
  padding: 0.5rem;
  background: rgba(99, 102, 241, 0.08);
  border-radius: 0.25rem;
}

.contextItem {
  font-size: 0.6875rem;
  color: #a5b4fc;
}

.sections {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.section {
  background: #1f2937;
  border: 1px solid #374151;
  border-radius: 0.25rem;
  overflow: hidden;
}

.sectionHeader {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.375rem 0.5rem;
  background: #111827;
  border-bottom: 1px solid #374151;
}

.sectionLabel {
  font-size: 0.6875rem;
  color: #9ca3af;
  font-weight: 500;
}

.sectionCount {
  font-size: 0.625rem;
  color: #6b7280;
}

.measurements {
  padding: 0.25rem 0.5rem;
}

.measurement {
  display: flex;
  justify-content: space-between;
  padding: 0.25rem 0;
  border-bottom: 1px solid #30363d;
}

.measurement:last-child {
  border-bottom: none;
}

.measurementProperty {
  font-size: 0.6875rem;
  color: #9ca3af;
}

.measurementValue {
  font-size: 0.6875rem;
  color: #d1d5db;
  font-family: var(--font-mono, ui-monospace, monospace);
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  margin-bottom: 0.75rem;
}

.tag {
  padding: 0.125rem 0.375rem;
  background: #374151;
  border-radius: 0.25rem;
  font-size: 0.625rem;
  color: #9ca3af;
}

.experimentTag {
  background: rgba(99, 102, 241, 0.2);
  color: #a5b4fc;
}

.notes {
  padding: 0.5rem;
  background: rgba(107, 114, 128, 0.08);
  border-radius: 0.25rem;
}

.notesLabel {
  display: block;
  font-size: 0.5625rem;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.25rem;
}

.notesText {
  margin: 0;
  font-size: 0.6875rem;
  color: #9ca3af;
  line-height: 1.5;
}
</style>
