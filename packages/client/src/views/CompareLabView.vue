<template>
  <div :class="styles.compareLab">
    <header :class="styles.labHeader">
      <div>
        <h1>Compare Lab</h1>
        <p :class="styles.hint">
          Load Adaptive geometry, capture baselines, and inspect SVG diffs.
        </p>
      </div>
      <div :class="styles.headerActions">
        <input
          ref="fileInput"
          type="file"
          :class="styles.hidden"
          accept="application/json"
          @change="handleFile"
        >
        <button
          :class="styles.ghost"
          @click="triggerFileDialog"
        >
          Import Geometry JSON
        </button>
        <button
          :class="styles.primary"
          :disabled="!hasStoredGeometry"
          @click="loadPersistedGeometry"
        >
          Load From Adaptive Lab
        </button>
        <button
          :class="styles.secondary"
          :disabled="!diffResult"
          title="Export comparison as SVG, PNG, or CSV"
          @click="showExportDialog = true"
        >
          Export Diff
        </button>
        <button
          :class="styles.primary"
          :disabled="!diffResult || !filenameTemplate"
          title="Save current comparison configuration as preset"
          @click="showSavePresetModal = true"
        >
          💾 Save as Preset
        </button>
      </div>
    </header>

    <section :class="styles.labGrid">
      <CompareBaselinePicker
        :current-geometry="currentGeometry"
        @diff-computed="(payload: any) => (diffResult = payload)"
      />

      <CompareSvgDualViewer
        :class="styles.middle"
        :diff="diffResult as any"
      />

      <CompareDiffViewer
        :diff="diffResult as any"
        :current-geometry="currentGeometry"
      />
    </section>

    <!-- B23: Export Dialog -->
    <ExportDialog
      v-if="showExportDialog"
      :styles="styles"
      :export-presets="exportPresets"
      :selected-preset-id="selectedPresetId"
      :filename-template="filenameTemplate"
      :extension-mismatch="extensionMismatch"
      :template-validation="templateValidation"
      :neck-profile-context="neckProfileContext"
      :neck-section-context="neckSectionContext"
      :export-format="exportFormat"
      :export-filename="exportFilename"
      :export-in-progress="exportInProgress"
      @close="showExportDialog = false"
      @update:selected-preset-id="(v) => { selectedPresetId = v; loadPresetTemplate() }"
      @update:filename-template="filenameTemplate = $event"
      @update:export-format="exportFormat = $event"
      @validate-template="validateTemplate"
      @fix-template-extension="fixTemplateExtension"
      @fix-export-format="fixExportFormat"
      @export="executeExport"
    />

    <!-- CompareLab: Save as Preset Modal -->
    <SavePresetModal
      v-if="showSavePresetModal"
      :styles="styles"
      :preset-form="presetForm"
      :filename-template="filenameTemplate"
      :export-format="exportFormat"
      :neck-profile-context="neckProfileContext"
      :neck-section-context="neckSectionContext"
      :diff-result-mode="diffResult?.mode || 'neck_diff'"
      :preset-save-message="presetSaveMessage"
      :preset-save-in-progress="presetSaveInProgress"
      @close="showSavePresetModal = false"
      @update:preset-form="presetForm = $event"
      @save="saveAsPreset"
    />
  </div>
</template>

<script setup lang="ts">
import { watch, onMounted, toRef } from 'vue'
import { useRoute } from 'vue-router'
import CompareBaselinePicker from '@/components/compare/CompareBaselinePicker.vue'
import CompareDiffViewer from '@/components/compare/CompareDiffViewer.vue'
import CompareSvgDualViewer from '@/components/compare/CompareSvgDualViewer.vue'
import ExportDialog from './compare_lab/ExportDialog.vue'
import SavePresetModal from './compare_lab/SavePresetModal.vue'
import styles from './CompareLabView.module.css'

import {
  useCompareLabState,
  useCompareLabStorage,
  useCompareLabExport,
  useCompareLabPresets,
  useCompareLabHelpers
} from './compare_lab/composables'

const route = useRoute()

// State
const {
  fileInput,
  currentGeometry,
  diffResult,
  hasStoredGeometry,
  showExportDialog,
  exportFormat,
  exportInProgress,
  exportPrefix,
  exportPresets,
  selectedPresetId,
  filenameTemplate,
  templateValidation,
  neckProfileContext,
  neckSectionContext,
  extensionMismatch,
  showSavePresetModal,
  presetSaveInProgress,
  presetSaveMessage,
  presetForm,
  exportFilename
} = useCompareLabState()

// Storage
const {
  persistGeometry,
  loadPersistedGeometry,
  extractNeckContext,
  handleFile,
  triggerFileDialog,
  loadExportState,
  saveExportState
} = useCompareLabStorage(
  route,
  fileInput,
  currentGeometry,
  neckProfileContext,
  neckSectionContext,
  selectedPresetId,
  filenameTemplate,
  exportFormat
)

// Export
const {
  executeExport,
  exportSvg,
  exportPng,
  exportCsv,
  downloadFile
} = useCompareLabExport(
  diffResult,
  exportFormat,
  exportInProgress,
  exportPrefix,
  exportFilename,
  showExportDialog
)

// Presets
const {
  loadExportPresets,
  loadPresetTemplate,
  validateTemplate,
  saveAsPreset
} = useCompareLabPresets(
  exportPresets,
  selectedPresetId,
  filenameTemplate,
  templateValidation,
  exportFormat,
  neckProfileContext,
  neckSectionContext,
  diffResult,
  showSavePresetModal,
  presetSaveInProgress,
  presetSaveMessage,
  presetForm
)

// Helpers
const {
  fixTemplateExtension,
  fixExportFormat,
  sanitizePrefix
} = useCompareLabHelpers(
  filenameTemplate,
  exportFormat,
  exportPrefix,
  toRef(() => extensionMismatch.value)
)

// Watchers
watch(
  currentGeometry,
  (value) => {
    if (value) {
      persistGeometry(value)
      extractNeckContext()
    } else {
      diffResult.value = null
    }
  },
  { deep: true }
)

// Reload presets and refresh neck context when export dialog opens
watch(showExportDialog, (isOpen) => {
  if (isOpen) {
    loadExportPresets()
    extractNeckContext()
  }
})

// Watch for export state changes and persist
watch([selectedPresetId, filenameTemplate, exportFormat], () => {
  saveExportState()
})

onMounted(() => {
  loadPersistedGeometry()
  loadExportState()
  loadExportPresets()
  extractNeckContext()
})
</script>
