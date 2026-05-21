<script setup lang="ts">
/**
 * MeasurementArchiveExportCard — Export measurement archive to JSON
 *
 * Dev Order 60: Exports current measurement state as a portable archive.
 * Local-only, observational-only — no server persistence.
 */
import { computed } from 'vue'
import { GateBadge, SectionLabel } from '@/components/shared/workflow'
import type { MeasurementArchiveRecord } from '@/types/acoustics/measurementArchive'
import { exportMeasurementArchive, buildMeasurementArchiveFilename } from '@/utils/acoustics/measurementArchive'

const props = defineProps<{
  archive: MeasurementArchiveRecord | null
}>()

const emit = defineEmits<{
  exported: [archive: MeasurementArchiveRecord]
}>()

const canExport = computed(() => props.archive !== null)

const sectionCount = computed(() => props.archive?.sections.length ?? 0)

const measurementCount = computed(() =>
  props.archive?.sections.reduce((sum, s) => sum + s.measurements.length, 0) ?? 0
)

function handleExport() {
  if (!props.archive) return

  const json = exportMeasurementArchive(props.archive, { pretty: true })
  const filename = buildMeasurementArchiveFilename(props.archive)

  const blob = new Blob([json], { type: 'application/json' })
  const url = URL.createObjectURL(blob)

  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)

  emit('exported', props.archive)
}
</script>

<template>
  <div :class="$style.card">
    <div :class="$style.header">
      <SectionLabel text="Export Archive" />
      <GateBadge
        :gate="canExport ? 'green' : 'yellow'"
        :label="canExport ? 'Ready' : 'No Data'"
      />
    </div>

    <div v-if="canExport" :class="$style.preview">
      <div :class="$style.stat">
        <span :class="$style.statLabel">Sections</span>
        <span :class="$style.statValue">{{ sectionCount }}</span>
      </div>
      <div :class="$style.stat">
        <span :class="$style.statLabel">Measurements</span>
        <span :class="$style.statValue">{{ measurementCount }}</span>
      </div>
    </div>

    <div v-else :class="$style.emptyState">
      <p>No archive data to export.</p>
    </div>

    <button
      :class="$style.exportButton"
      :disabled="!canExport"
      @click="handleExport"
    >
      Export JSON
    </button>

    <div :class="$style.notice">
      Archives are local-only. Export preserves observational data without calibration or prediction.
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

.preview {
  display: flex;
  gap: 1rem;
  margin-bottom: 0.75rem;
}

.stat {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}

.statLabel {
  font-size: 0.625rem;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.statValue {
  font-size: 1rem;
  color: #f9fafb;
  font-weight: 600;
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

.exportButton {
  width: 100%;
  padding: 0.5rem;
  background: #374151;
  border: 1px solid #4b5563;
  border-radius: 0.25rem;
  color: #f9fafb;
  font-size: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.exportButton:hover:not(:disabled) {
  background: #4b5563;
}

.exportButton:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.notice {
  margin-top: 0.5rem;
  font-size: 0.625rem;
  color: #6b7280;
  text-align: center;
}
</style>
