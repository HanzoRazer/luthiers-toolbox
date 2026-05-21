<script setup lang="ts">
/**
 * MeasurementArchiveEvidenceIndex — Experimental history organizer
 *
 * Dev Order 62: Displays measurement archives as experimental evidence history.
 * Supports chronological, by-method, and by-experiment views.
 * Dev Order 67: Verified safe with archives containing topology variant references.
 *
 * Evidence summaries are observational only — no ranking, recommendation, or calibration.
 */
import { ref, computed } from 'vue'
import { GateBadge, SectionLabel } from '@/components/shared/workflow'
import type { MeasurementArchiveRecord } from '@/types/acoustics/measurementArchive'
import {
  sortMeasurementArchivesByTimestamp,
  groupMeasurementArchivesByMethod,
  groupMeasurementArchivesByExperimentTag,
  createEvidenceSummary,
  formatArchiveTimestamp,
} from '@/utils/acoustics/measurementArchive'

const props = defineProps<{
  archives: MeasurementArchiveRecord[]
}>()

const emit = defineEmits<{
  select: [archive: MeasurementArchiveRecord]
}>()

type ViewMode = 'chronological' | 'by-method' | 'by-experiment'

const viewMode = ref<ViewMode>('chronological')

const sortedArchives = computed(() => sortMeasurementArchivesByTimestamp(props.archives))

const archivesByMethod = computed(() => groupMeasurementArchivesByMethod(props.archives))

const archivesByExperiment = computed(() => groupMeasurementArchivesByExperimentTag(props.archives))

const evidenceSummary = computed(() => createEvidenceSummary(props.archives))

function getArchiveLabel(archive: MeasurementArchiveRecord): string {
  return archive.context.referenceLabel ?? archive.context.candidateLabel ?? archive.archiveId
}

function isSparseArchive(archiveId: string): boolean {
  return evidenceSummary.value.sparseArchives.includes(archiveId)
}

function selectArchive(archive: MeasurementArchiveRecord) {
  emit('select', archive)
}
</script>

<template>
  <div :class="$style.panel">
    <div :class="$style.header">
      <SectionLabel text="Evidence Index" />
      <GateBadge
        :gate="archives.length > 0 ? 'green' : 'yellow'"
        :label="`${archives.length} archive${archives.length !== 1 ? 's' : ''}`"
      />
    </div>

    <!-- View Mode Selector -->
    <div :class="$style.viewModes">
      <button
        :class="[$style.modeButton, viewMode === 'chronological' && $style.active]"
        @click="viewMode = 'chronological'"
      >
        Chronological
      </button>
      <button
        :class="[$style.modeButton, viewMode === 'by-method' && $style.active]"
        @click="viewMode = 'by-method'"
      >
        By Method
      </button>
      <button
        :class="[$style.modeButton, viewMode === 'by-experiment' && $style.active]"
        @click="viewMode = 'by-experiment'"
      >
        By Experiment
      </button>
    </div>

    <!-- Empty State -->
    <div v-if="archives.length === 0" :class="$style.emptyState">
      <p :class="$style.emptyText">No measurement archives in evidence index.</p>
      <p :class="$style.emptyHint">Export or import archives to build experimental history.</p>
    </div>

    <!-- Chronological View -->
    <div v-else-if="viewMode === 'chronological'" :class="$style.archiveList">
      <div
        v-for="archive in sortedArchives"
        :key="archive.archiveId"
        :class="[$style.archiveItem, isSparseArchive(archive.archiveId) && $style.sparse]"
        @click="selectArchive(archive)"
      >
        <div :class="$style.archiveMain">
          <span :class="$style.archiveLabel">{{ getArchiveLabel(archive) }}</span>
          <span :class="$style.archiveTimestamp">
            {{ formatArchiveTimestamp(archive.metadata.createdAtIso) }}
          </span>
        </div>
        <div :class="$style.archiveMeta">
          <span :class="$style.sectionCount">
            {{ archive.sections.length }} section{{ archive.sections.length !== 1 ? 's' : '' }}
          </span>
          <span v-if="isSparseArchive(archive.archiveId)" :class="$style.sparseWarning">
            Sparse
          </span>
        </div>
      </div>
    </div>

    <!-- By Method View -->
    <div v-else-if="viewMode === 'by-method'" :class="$style.groupedView">
      <div v-for="[method, methodArchives] in archivesByMethod" :key="method" :class="$style.group">
        <div :class="$style.groupHeader">
          <span :class="$style.groupLabel">{{ method }}</span>
          <span :class="$style.groupCount">{{ methodArchives.length }}</span>
        </div>
        <div :class="$style.groupItems">
          <div
            v-for="archive in methodArchives"
            :key="archive.archiveId"
            :class="[$style.archiveItem, $style.compact, isSparseArchive(archive.archiveId) && $style.sparse]"
            @click="selectArchive(archive)"
          >
            <span :class="$style.archiveLabel">{{ getArchiveLabel(archive) }}</span>
            <span :class="$style.archiveTimestamp">
              {{ formatArchiveTimestamp(archive.metadata.createdAtIso) }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- By Experiment View -->
    <div v-else-if="viewMode === 'by-experiment'" :class="$style.groupedView">
      <div v-for="[tag, tagArchives] in archivesByExperiment" :key="tag" :class="$style.group">
        <div :class="$style.groupHeader">
          <span :class="$style.groupLabel">{{ tag }}</span>
          <span :class="$style.groupCount">{{ tagArchives.length }}</span>
        </div>
        <div :class="$style.groupItems">
          <div
            v-for="archive in tagArchives"
            :key="archive.archiveId"
            :class="[$style.archiveItem, $style.compact, isSparseArchive(archive.archiveId) && $style.sparse]"
            @click="selectArchive(archive)"
          >
            <span :class="$style.archiveLabel">{{ getArchiveLabel(archive) }}</span>
            <span :class="$style.archiveTimestamp">
              {{ formatArchiveTimestamp(archive.metadata.createdAtIso) }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Evidence Summary -->
    <div v-if="archives.length > 0" :class="$style.summary">
      <span :class="$style.summaryLabel">Evidence Summary</span>
      <div :class="$style.summaryContent">
        <span v-if="evidenceSummary.dateRange">
          {{ formatArchiveTimestamp(evidenceSummary.dateRange.earliest) }} —
          {{ formatArchiveTimestamp(evidenceSummary.dateRange.latest) }}
        </span>
        <span v-if="evidenceSummary.methodsUsed.length > 0">
          Methods: {{ evidenceSummary.methodsUsed.join(', ') }}
        </span>
        <span v-if="evidenceSummary.sparseArchives.length > 0" :class="$style.sparseNotice">
          {{ evidenceSummary.sparseArchives.length }} sparse archive{{ evidenceSummary.sparseArchives.length !== 1 ? 's' : '' }}
        </span>
      </div>
    </div>

    <!-- Notice -->
    <div :class="$style.notice">
      Evidence index is observational. Archives are organized for review, not ranked or recommended.
    </div>
  </div>
</template>

<style module>
.panel {
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

.viewModes {
  display: flex;
  gap: 0.25rem;
  margin-bottom: 0.75rem;
}

.modeButton {
  padding: 0.375rem 0.75rem;
  background: transparent;
  border: 1px solid #374151;
  border-radius: 0.25rem;
  color: #9ca3af;
  font-size: 0.6875rem;
  cursor: pointer;
  transition: all 0.15s ease;
}

.modeButton:hover {
  background: #374151;
  color: #f9fafb;
}

.modeButton.active {
  background: #374151;
  border-color: #6366f1;
  color: #f9fafb;
}

.emptyState {
  padding: 1rem;
  background: rgba(107, 114, 128, 0.08);
  border-radius: 0.25rem;
  text-align: center;
  margin-bottom: 0.75rem;
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

.archiveList {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.archiveItem {
  padding: 0.5rem;
  background: #1f2937;
  border: 1px solid #374151;
  border-radius: 0.25rem;
  cursor: pointer;
  transition: all 0.15s ease;
}

.archiveItem:hover {
  background: #374151;
  border-color: #6366f1;
}

.archiveItem.sparse {
  border-left: 2px solid #fbbf24;
}

.archiveItem.compact {
  padding: 0.375rem 0.5rem;
}

.archiveMain {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.archiveLabel {
  font-size: 0.75rem;
  color: #f9fafb;
  font-weight: 500;
}

.archiveTimestamp {
  font-size: 0.625rem;
  color: #6b7280;
}

.archiveMeta {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.25rem;
}

.sectionCount {
  font-size: 0.625rem;
  color: #6b7280;
}

.sparseWarning {
  font-size: 0.5625rem;
  color: #fbbf24;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.groupedView {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.group {
  background: #1f2937;
  border: 1px solid #374151;
  border-radius: 0.25rem;
  overflow: hidden;
}

.groupHeader {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem;
  background: #111827;
  border-bottom: 1px solid #374151;
}

.groupLabel {
  font-size: 0.6875rem;
  color: #9ca3af;
  font-weight: 500;
}

.groupCount {
  font-size: 0.625rem;
  color: #6b7280;
  background: #374151;
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
}

.groupItems {
  display: flex;
  flex-direction: column;
}

.groupItems .archiveItem {
  border: none;
  border-radius: 0;
  border-bottom: 1px solid #30363d;
}

.groupItems .archiveItem:last-child {
  border-bottom: none;
}

.summary {
  padding: 0.5rem;
  background: rgba(99, 102, 241, 0.08);
  border-radius: 0.25rem;
  margin-bottom: 0.75rem;
}

.summaryLabel {
  display: block;
  font-size: 0.5625rem;
  color: #a5b4fc;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.25rem;
}

.summaryContent {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
  font-size: 0.6875rem;
  color: #d1d5db;
}

.sparseNotice {
  color: #fbbf24;
}

.notice {
  padding: 0.375rem 0.5rem;
  background: rgba(107, 114, 128, 0.08);
  border-radius: 0.25rem;
  font-size: 0.625rem;
  color: #6b7280;
  text-align: center;
}
</style>
