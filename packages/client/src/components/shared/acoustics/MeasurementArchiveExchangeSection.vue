<script setup lang="ts">
/**
 * MeasurementArchiveExchangeSection — Consolidated archive exchange workflow
 *
 * Dev Order 60: Composes export, import, and preview into single section.
 * Dev Order 64: Added existingArchives prop for duplicate detection.
 * Ephemeral workflow — no server persistence, local-only.
 */
import { ref, computed } from 'vue'
import { SectionLabel } from '@/components/shared/workflow'
import MeasurementArchiveExportCard from './MeasurementArchiveExportCard.vue'
import MeasurementArchiveImportCard from './MeasurementArchiveImportCard.vue'
import MeasurementArchivePreviewCard from './MeasurementArchivePreviewCard.vue'
import type {
  MeasurementArchiveRecord,
  MeasurementArchiveValidationResult,
} from '@/types/acoustics/measurementArchive'

const props = defineProps<{
  archive: MeasurementArchiveRecord | null
  existingArchives?: MeasurementArchiveRecord[]
}>()

const emit = defineEmits<{
  exported: [archive: MeasurementArchiveRecord]
  imported: [result: MeasurementArchiveValidationResult, archive: MeasurementArchiveRecord | null]
}>()

const importedArchive = ref<MeasurementArchiveRecord | null>(null)

const previewArchive = computed(() => importedArchive.value ?? props.archive)

const existingArchiveIds = computed(() =>
  (props.existingArchives ?? []).map((a) => a.archiveId)
)

function handleExported(archive: MeasurementArchiveRecord) {
  emit('exported', archive)
}

function handleImported(result: MeasurementArchiveValidationResult, archive: MeasurementArchiveRecord | null) {
  importedArchive.value = archive
  emit('imported', result, archive)
}
</script>

<template>
  <div :class="$style.section">
    <div :class="$style.header">
      <SectionLabel text="Archive Exchange" />
    </div>

    <p :class="$style.description">
      Archives are local observational records. Export files to preserve them outside this session.
    </p>

    <div :class="$style.cards">
      <MeasurementArchiveExportCard
        :archive="archive"
        @exported="handleExported"
      />
      <MeasurementArchiveImportCard
        :existing-archive-ids="existingArchiveIds"
        @imported="handleImported"
      />
    </div>

    <!-- Preview imported or current archive -->
    <MeasurementArchivePreviewCard
      v-if="previewArchive"
      :archive="previewArchive"
    />

    <div :class="$style.notice">
      Archive exchange is observational only. No calibration, prediction, or canonical authority.
    </div>
  </div>
</template>

<style module>
.section {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.header {
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #30363d;
}

.description {
  margin: 0;
  font-size: 0.75rem;
  color: #8b949e;
  line-height: 1.5;
}

.cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
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
