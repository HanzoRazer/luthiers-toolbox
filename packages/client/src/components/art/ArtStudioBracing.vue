<script setup lang="ts">
/**
 * ArtStudioBracing.vue
 *
 * Guitar bracing section calculator.
 * Orchestrates child panels for single brace, batch, and export.
 */
import { ref, watch, onMounted } from 'vue'
import {
  PROFILE_TYPES,
  BraceSinglePanel,
  BraceBatchPanel,
  BraceResultsPanel,
  useSingleBrace,
  useBraceBatch,
  useBracingExport,
  useBracingPresets
} from './bracing'

// Shared state
const loading = ref(false)
const error = ref<string | null>(null)

// Single brace composable
const {
  profileType,
  width,
  height,
  length,
  density,
  singleResult,
  selectedWood,
  setSelectedWood,
  previewSingle
} = useSingleBrace(loading, error)

// Batch composable
const { braces, batchName, batchResult, addBrace, removeBrace, updateBrace, calculateBatch } =
  useBraceBatch(loading, error)

// Export composable
const { dxfVersion, includeCenterlines, includeLabels, exportDXF } =
  useBracingExport(loading, error)

// Presets composable
const { presets, loadPresets, applyPreset } = useBracingPresets(profileType, density)

// Profile types for template
const profileTypes = PROFILE_TYPES

// Helper to copy current single brace to batch
function copyCurrentToBrace(): void {
  addBrace({
    profileType: profileType.value,
    width: width.value,
    height: height.value,
    length: length.value,
    density: density.value
  })
}

// Helper to export with current braces
function handleExportDXF(): void {
  exportDXF(braces.value, batchName.value)
}

// Watchers
watch([profileType, width, height, length, density], () => previewSingle(), {
  debounce: 300
} as any)

onMounted(() => {
  loadPresets()
  previewSingle()
})
</script>

<template>
  <div class="p-4 max-w-6xl mx-auto">
    <h1 class="text-2xl font-bold mb-4 flex items-center gap-2">
      <span class="text-3xl">🪵</span>
      Bracing Calculator
    </h1>

    <!-- Error Banner -->
    <div
      v-if="error"
      class="bg-red-100 border border-red-400 text-red-700 px-4 py-2 rounded mb-4"
    >
      {{ error }}
      <button
        class="ml-2 underline"
        @click="error = null"
      >
        Dismiss
      </button>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Left Panel: Single Brace Calculator -->
      <BraceSinglePanel
        v-model:profileType="profileType"
        v-model:width="width"
        v-model:height="height"
        v-model:length="length"
        v-model:density="density"
        :selected-wood="selectedWood"
        :single-result="singleResult"
        :profile-types="profileTypes"
        :presets="presets"
        @set-wood="setSelectedWood"
        @apply-preset="applyPreset"
        @add-to-batch="copyCurrentToBrace"
      />

      <!-- Middle Panel: Batch List -->
      <BraceBatchPanel
        v-model:batch-name="batchName"
        :braces="braces"
        :loading="loading"
        :profile-types="profileTypes"
        @update:brace="updateBrace"
        @remove-brace="removeBrace"
        @calculate-batch="calculateBatch"
      />

      <!-- Right Panel: Batch Results & Export -->
      <BraceResultsPanel
        v-model:dxf-version="dxfVersion"
        v-model:include-centerlines="includeCenterlines"
        v-model:include-labels="includeLabels"
        :batch-result="batchResult"
        :brace-count="braces.length"
        :batch-name="batchName"
        :loading="loading"
        @export-d-x-f="handleExportDXF"
      />
    </div>
  </div>
</template>
