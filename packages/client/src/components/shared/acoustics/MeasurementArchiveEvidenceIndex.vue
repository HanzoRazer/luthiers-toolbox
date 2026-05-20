<script setup lang="ts">
/**
 * MeasurementArchiveEvidenceIndex — Evidence organization for measurement archives
 *
 * Dev Order 62: Displays created and imported archives as a coherent experimental
 * history. Supports chronological and grouped review with provenance visibility.
 *
 * Feels like: experimental lab notebook index
 * NOT: scoring dashboard or calibration authority
 *
 * Local-only — no persistence, database, or upload.
 */
import { ref, computed } from 'vue'
import { GateBadge } from '@/components/shared/workflow'
import type { MeasurementArchiveRecord } from '@/types/acoustics/measurementArchive'
import {
  sortMeasurementArchivesByTimestamp,
  groupMeasurementArchivesByMethod,
  groupMeasurementArchivesByExperimentTag,
  createEvidenceSummary,
  formatArchiveTimestamp,
  type ArchiveSortOrder,
  type MeasurementArchiveEvidenceSummary,
} from '@/utils/acoustics/measurementArchive'

const props = defineProps<{
  archives: MeasurementArchiveRecord[]
}>()

const emit = defineEmits<{
  select: [archive: MeasurementArchiveRecord]
}>()

type ViewMode = 'chronological' | 'by-method' | 'by-experiment'

const viewMode = ref<ViewMode>('chronological')
const sortOrder = ref<ArchiveSortOrder>('newest')

const sortedArchives = computed(() =>
  sortMeasurementArchivesByTimestamp(props.archives, sortOrder.value)
)

const methodGroups = computed(() =>
  groupMeasurementArchivesByMethod(props.archives)
)

const experimentGroups = computed(() =>
  groupMeasurementArchivesByExperimentTag(props.archives)
)

const summaries = computed(() => {
  const map = new Map<string, MeasurementArchiveEvidenceSummary>()
  for (const archive of props.archives) {
    map.set(archive.archiveId, createEvidenceSummary(archive))
  }
  return map
})

function getSummary(archiveId: string): MeasurementArchiveEvidenceSummary | undefined {
  return summaries.value.get(archiveId)
}

function handleSelect(archive: MeasurementArchiveRecord) {
  emit('select', archive)
}

function getMethodLabel(method: string): string {
  const labels: Record<string, string> = {
    fft_peak_detection: 'FFT Peak Detection',
    swept_sine: 'Swept Sine',
    impulse_response: 'Impulse Response',
    manual_reading: 'Manual Reading',
    unknown: 'Unknown Method',
  }
  return labels[method] ?? method
}

function toggleSort() {
  sortOrder.value = sortOrder.value === 'newest' ? 'oldest' : 'newest'
}
</script>

<template>
  <div :class="$style.index">
    <div :class="$style.header">
      <span :class="$style.title">Evidence Index</span>
      <span :class="$style.count">{{ archives.length }} archive{{ archives.length !== 1 ? 's' : '' }}</span>
    </div>

    <!-- Empty State -->
    <div v-if="archives.length === 0" :class="$style.empty">
      <p :class="$style.emptyText">No archives in evidence index.</p>
      <p :class="$style.emptyHint">Create or import measurement archives to build experimental history.</p>
    </div>

    <!-- View Controls -->
    <div v-else :class="$style.controls">
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
      <button
        v-if="viewMode === 'chronological'"
        :class="$style.sortButton"
        @click="toggleSort"
      >
        {{ sortOrder === 'newest' ? 'Newest First' : 'Oldest First' }}
      </button>
    </div>

    <!-- Chronological View -->
    <div v-if="viewMode === 'chronological' && archives.length > 0" :class="$style.list">
      <div
        v-for="archive in sortedArchives"
        :key="archive.archiveId"
        :class="[$style.entry, getSummary(archive.archiveId)?.isSparse && $style.sparse]"
        @click="handleSelect(archive)"
      >
        <div :class="$style.entryHeader">
          <span :class="$style.timestamp">{{ formatArchiveTimestamp(archive.metadata.createdAtIso) }}</span>
          <GateBadge
            v-if="getSummary(archive.archiveId)?.isSparse"
            gate="yellow"
            label="Sparse"
          />
        </div>

        <div :class="$style.entryBody">
          <div :class="$style.labels">
            <span v-if="archive.context.referenceLabel" :class="$style.label">
              {{ archive.context.referenceLabel }}
            </span>
            <span v-if="archive.context.candidateLabel" :class="$style.label">
              {{ archive.context.candidateLabel }}
            </span>
          </div>
          <span :class="$style.measurementCount">
            {{ archive.measurements.length }} measurement{{ archive.measurements.length !== 1 ? 's' : '' }}
          </span>
        </div>

        <div v-if="getSummary(archive.archiveId)?.methods.length" :class="$style.methods">
          <span
            v-for="method in getSummary(archive.archiveId)?.methods"
            :key="method"
            :class="$style.methodTag"
          >
            {{ getMethodLabel(method) }}
          </span>
        </div>

        <div v-if="getSummary(archive.archiveId)?.experimentTags.length" :class="$style.tags">
          <span
            v-for="tag in getSummary(archive.archiveId)?.experimentTags"
            :key="tag"
            :class="$style.experimentTag"
          >
            {{ tag }}
          </span>
        </div>

        <div v-if="getSummary(archive.archiveId)?.hasLinkedSnapshot" :class="$style.provenance">
          Linked to diagnostic snapshot
        </div>

        <div v-if="getSummary(archive.archiveId)?.sparseWarnings.length" :class="$style.warnings">
          <span
            v-for="(warning, idx) in getSummary(archive.archiveId)?.sparseWarnings"
            :key="idx"
            :class="$style.warning"
          >
            {{ warning }}
          </span>
        </div>
      </div>
    </div>

    <!-- By Method View -->
    <div v-else-if="viewMode === 'by-method' && archives.length > 0" :class="$style.groups">
      <div v-for="group in methodGroups" :key="group.method" :class="$style.group">
        <div :class="$style.groupHeader">
          <span :class="$style.groupTitle">{{ getMethodLabel(group.method) }}</span>
          <span :class="$style.groupCount">{{ group.archives.length }}</span>
        </div>
        <div :class="$style.groupList">
          <div
            v-for="archive in group.archives"
            :key="archive.archiveId"
            :class="$style.compactEntry"
            @click="handleSelect(archive)"
          >
            <span :class="$style.compactTimestamp">
              {{ formatArchiveTimestamp(archive.metadata.createdAtIso) }}
            </span>
            <span :class="$style.compactLabels">
              {{ archive.context.referenceLabel ?? archive.context.candidateLabel ?? archive.archiveId }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- By Experiment View -->
    <div v-else-if="viewMode === 'by-experiment' && archives.length > 0" :class="$style.groups">
      <div v-for="group in experimentGroups" :key="group.tag" :class="$style.group">
        <div :class="$style.groupHeader">
          <span :class="[$style.groupTitle, group.tag === '(untagged)' && $style.untagged]">
            {{ group.tag }}
          </span>
          <span :class="$style.groupCount">{{ group.archives.length }}</span>
        </div>
        <div :class="$style.groupList">
          <div
            v-for="archive in group.archives"
            :key="archive.archiveId"
            :class="$style.compactEntry"
            @click="handleSelect(archive)"
          >
            <span :class="$style.compactTimestamp">
              {{ formatArchiveTimestamp(archive.metadata.createdAtIso) }}
            </span>
            <span :class="$style.compactLabels">
              {{ archive.context.referenceLabel ?? archive.context.candidateLabel ?? archive.archiveId }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Footer Notice -->
    <div :class="$style.notice">
      Evidence index is local-only. No persistence, scoring, or calibration authority.
    </div>
  </div>
</template>

<style module>
.index {
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

.title {
  font-size: 0.8125rem;
  font-weight: 500;
  color: #d1d5db;
}

.count {
  font-size: 0.6875rem;
  color: #6b7280;
}

.empty {
  padding: 1rem 0.5rem;
  text-align: center;
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

.controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.viewModes {
  display: flex;
  gap: 0.25rem;
}

.modeButton {
  padding: 0.25rem 0.5rem;
  background: #1f2937;
  color: #9ca3af;
  border: 1px solid #374151;
  border-radius: 0.25rem;
  font-size: 0.625rem;
  cursor: pointer;
  transition: all 0.15s ease;
}

.modeButton:hover {
  background: #374151;
  color: #d1d5db;
}

.modeButton.active {
  background: #374151;
  border-color: #6366f1;
  color: #f9fafb;
}

.sortButton {
  padding: 0.25rem 0.5rem;
  background: #1f2937;
  color: #9ca3af;
  border: 1px solid #374151;
  border-radius: 0.25rem;
  font-size: 0.625rem;
  cursor: pointer;
  transition: all 0.15s ease;
}

.sortButton:hover {
  background: #374151;
  color: #d1d5db;
}

.list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-height: 400px;
  overflow-y: auto;
}

.entry {
  padding: 0.5rem;
  background: #1f2937;
  border: 1px solid #374151;
  border-radius: 0.25rem;
  cursor: pointer;
  transition: all 0.15s ease;
}

.entry:hover {
  border-color: #6366f1;
  background: #252f3f;
}

.entry.sparse {
  border-left: 2px solid #fbbf24;
}

.entryHeader {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.25rem;
}

.timestamp {
  font-size: 0.6875rem;
  color: #9ca3af;
  font-family: var(--font-mono, ui-monospace, monospace);
}

.entryBody {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.25rem;
}

.labels {
  display: flex;
  gap: 0.375rem;
}

.label {
  font-size: 0.75rem;
  color: #d1d5db;
}

.measurementCount {
  font-size: 0.625rem;
  color: #6b7280;
}

.methods {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  margin-top: 0.25rem;
}

.methodTag {
  font-size: 0.5625rem;
  padding: 0.125rem 0.375rem;
  background: rgba(99, 102, 241, 0.15);
  border-radius: 0.25rem;
  color: #a5b4fc;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  margin-top: 0.25rem;
}

.experimentTag {
  font-size: 0.5625rem;
  padding: 0.125rem 0.375rem;
  background: rgba(16, 185, 129, 0.15);
  border-radius: 0.25rem;
  color: #6ee7b7;
}

.provenance {
  margin-top: 0.25rem;
  font-size: 0.5625rem;
  color: #a5b4fc;
  font-style: italic;
}

.warnings {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  margin-top: 0.25rem;
}

.warning {
  font-size: 0.5625rem;
  color: #fbbf24;
}

.groups {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-height: 400px;
  overflow-y: auto;
}

.group {
  background: #1f2937;
  border: 1px solid #374151;
  border-radius: 0.25rem;
  padding: 0.5rem;
}

.groupHeader {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.375rem;
  padding-bottom: 0.25rem;
  border-bottom: 1px solid #30363d;
}

.groupTitle {
  font-size: 0.75rem;
  font-weight: 500;
  color: #d1d5db;
}

.groupTitle.untagged {
  color: #6b7280;
  font-style: italic;
}

.groupCount {
  font-size: 0.625rem;
  color: #6b7280;
  padding: 0.125rem 0.375rem;
  background: #374151;
  border-radius: 0.125rem;
}

.groupList {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.compactEntry {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.25rem 0.375rem;
  background: #111827;
  border-radius: 0.125rem;
  cursor: pointer;
  transition: background 0.15s ease;
}

.compactEntry:hover {
  background: #252f3f;
}

.compactTimestamp {
  font-size: 0.5625rem;
  color: #6b7280;
  font-family: var(--font-mono, ui-monospace, monospace);
  flex-shrink: 0;
}

.compactLabels {
  font-size: 0.6875rem;
  color: #9ca3af;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.notice {
  margin-top: 0.5rem;
  padding: 0.375rem 0.5rem;
  background: rgba(107, 114, 128, 0.08);
  border-radius: 0.25rem;
  font-size: 0.625rem;
  color: #6b7280;
  text-align: center;
}
</style>
