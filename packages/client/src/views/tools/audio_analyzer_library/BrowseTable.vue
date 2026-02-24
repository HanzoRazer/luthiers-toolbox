<template>
  <section :class="styles.cardWide">
    <h2>Browse Attachments</h2>
    <div :class="styles.filterBar">
      <span
        v-if="kindFilter || mimeFilter"
        :class="styles.activeFilters"
      >
        Filters:
        <code v-if="kindFilter">kind={{ kindFilter }}</code>
        <code v-if="mimeFilter">mime={{ mimeFilter }}</code>
        <button
          :class="styles.btnClear"
          @click="$emit('clear-filters')"
        >Clear</button>
      </span>
      <span :class="styles.browseCount">
        Showing {{ data?.count ?? 0 }} of {{ data?.total_in_index ?? 0 }}
      </span>
    </div>

    <div
      v-if="loading"
      :class="loaders.muted"
    >
      Loading...
    </div>
    <div
      v-else-if="error"
      :class="styles.importError"
    >
      {{ error }}
    </div>
    <table
      v-else
      :class="styles.tbl"
    >
      <thead>
        <tr>
          <th>Filename</th>
          <th>Kind</th>
          <th>Validation</th>
          <th>MIME</th>
          <th>Size</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="entry in data?.entries"
          :key="entry.sha256"
        >
          <td
            :class="[styles.mono, styles.filenameCell]"
            :title="entry.filename"
          >
            {{ entry.filename }}
          </td>
          <td><code :class="styles.kindBadge">{{ entry.kind }}</code></td>
          <td>
            <span
              v-if="isViewerPack(entry)"
              :class="[badges.badge, {
                [badges.badgePass]: entry.validation_passed === true,
                [badges.badgeFail]: entry.validation_passed === false,
                [badges.badgeUnknown]: entry.validation_passed === undefined
              }]"
              :title="getValidationTooltip(entry)"
            >
              {{ getValidationLabel(entry) }}
            </span>
            <span
              v-else
              :class="styles.validationNa"
            >—</span>
          </td>
          <td :class="styles.mono">
            {{ entry.mime }}
          </td>
          <td :class="styles.mono">
            {{ formatSize(entry.size_bytes) }}
          </td>
          <td :class="styles.actionsCell">
            <a
              v-if="isViewerPack(entry)"
              :class="buttons.btn"
              :href="`/tools/audio-analyzer?sha256=${entry.sha256}`"
            >
              Open
            </a>
            <a
              :class="buttons.btn"
              :href="getDownloadUrl(entry.sha256)"
              download
            >
              Download
            </a>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Pagination -->
    <div
      v-if="data"
      :class="styles.pagination"
    >
      <button
        :class="buttons.btn"
        :disabled="!data.next_cursor"
        @click="$emit('next-page')"
      >
        Next Page
      </button>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { BrowseResponse, AttachmentMetaEntry } from '@/types/rmosAcoustics'
import { getDownloadUrl, isViewerPack, formatSize } from '@/sdk/endpoints/rmosAcoustics'
import styles from '../AudioAnalyzerLibrary.module.css'
import { buttons, badges, loaders } from '@/styles/shared'

defineProps<{
  data: BrowseResponse | null
  loading: boolean
  error: string
  kindFilter: string
  mimeFilter: string
}>()

defineEmits<{
  'clear-filters': []
  'next-page': []
}>()

function getValidationLabel(entry: AttachmentMetaEntry): string {
  if (entry.validation_passed === true) return 'PASS'
  if (entry.validation_passed === false) return 'FAIL'
  return 'UNKNOWN'
}

function getValidationTooltip(entry: AttachmentMetaEntry): string {
  if (entry.validation_passed === undefined) {
    return 'No validation report (legacy pack)'
  }
  const errors = entry.validation_errors ?? 0
  const warnings = entry.validation_warnings ?? 0
  return `${entry.validation_passed ? 'Passed' : 'Failed'}: ${errors} errors, ${warnings} warnings`
}
</script>
