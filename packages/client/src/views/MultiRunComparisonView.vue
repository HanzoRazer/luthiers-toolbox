<template>
  <div class="p-6 space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <h1 class="text-3xl font-bold">
        Multi-Run Comparison
      </h1>
      <button
        class="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
        @click="fetchPresets"
      >
        Refresh Presets
      </button>
    </div>

    <!-- Preset Selector -->
    <div class="bg-white border rounded-lg p-4">
      <h2 class="text-xl font-semibold mb-3">
        Select Presets to Compare
      </h2>
      <p class="text-sm text-gray-600 mb-4">
        Choose at least 2 presets that were cloned from JobInt runs (B19). Only presets with job lineage can be compared.
      </p>

      <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 max-h-64 overflow-y-auto p-2">
        <label
          v-for="preset in presetsWithLineage"
          :key="preset.id"
          class="flex items-start gap-2 p-3 border rounded hover:bg-gray-50 cursor-pointer"
          :class="{'bg-blue-50 border-blue-300': selectedPresetIds.includes(preset.id)}"
        >
          <input
            v-model="selectedPresetIds"
            type="checkbox"
            :value="preset.id"
            class="mt-1"
          >
          <div class="flex-1">
            <p class="font-medium text-sm">{{ preset.name }}</p>
            <p class="text-xs text-gray-500">{{ preset.kind }}</p>
            <p
              v-if="preset.job_source_id"
              class="text-xs text-gray-400"
            >
              Job: {{ preset.job_source_id.slice(0, 8) }}...
            </p>
          </div>
        </label>
      </div>

      <div
        v-if="presetsWithLineage.length === 0"
        class="text-center py-8 text-gray-500"
      >
        <p class="mb-2">
          No presets with job lineage found
        </p>
        <p class="text-sm">
          Clone jobs as presets using B19 feature in JobInt view
        </p>
      </div>

      <div class="flex items-center gap-4 mt-4">
        <button
          :disabled="selectedPresetIds.length < 2 || loading"
          class="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          @click="runComparison"
        >
          {{ loading ? 'Analyzing...' : 'Compare Runs' }}
        </button>
        <span class="text-sm text-gray-600">
          {{ selectedPresetIds.length }} preset{{ selectedPresetIds.length !== 1 ? 's' : '' }} selected
        </span>
        <button
          v-if="selectedPresetIds.length > 0"
          class="text-sm text-gray-600 hover:text-gray-800 underline"
          @click="selectedPresetIds = []"
        >
          Clear selection
        </button>
      </div>
    </div>

    <!-- Error Message -->
    <div
      v-if="errorMessage"
      class="p-4 bg-red-50 border border-red-200 rounded text-red-700"
    >
      {{ errorMessage }}
    </div>

    <!-- Comparison Results -->
    <div
      v-if="comparisonResult"
      class="space-y-6"
    >
      <!-- Summary Stats -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div class="bg-white border rounded-lg p-4">
          <p class="text-sm text-gray-600 mb-1">Runs Compared</p>
          <p class="text-2xl font-bold">{{ comparisonResult.runs.length }}</p>
        </div>
        <div class="bg-white border rounded-lg p-4">
          <p class="text-sm text-gray-600 mb-1">Avg Time</p>
          <p class="text-2xl font-bold">{{ comparisonResult.avg_time_s ? comparisonResult.avg_time_s.toFixed(1) : 'N/A' }}s</p>
        </div>
        <div class="bg-white border rounded-lg p-4">
          <p class="text-sm text-gray-600 mb-1">Avg Energy</p>
          <p class="text-2xl font-bold">{{ comparisonResult.avg_energy_j ? comparisonResult.avg_energy_j.toFixed(0) : 'N/A' }}J</p>
        </div>
        <div class="bg-white border rounded-lg p-4">
          <p class="text-sm text-gray-600 mb-1">Avg Moves</p>
          <p class="text-2xl font-bold">{{ comparisonResult.avg_move_count || 'N/A' }}</p>
        </div>
      </div>

      <!-- Time Comparison Chart -->
      <div class="bg-white border rounded-lg p-4">
        <h3 class="text-lg font-semibold mb-3">Time Comparison</h3>
        <div v-if="chartData.labels.length > 0" class="h-64">
          <canvas ref="timeChartCanvas" />
        </div>
        <p v-else class="text-center text-gray-500 py-8">No time data available for charting</p>
      </div>

      <!-- Actions -->
      <div class="flex gap-4">
        <button class="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700" @click="exportComparisonCSV">
          Export as CSV
        </button>
        <button class="px-4 py-2 border rounded hover:bg-gray-50" @click="resetComparison">
          New Comparison
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * MultiRunComparisonView - Compare multiple CAM preset runs.
 *
 * REFACTORED: Uses composables for cleaner separation of concerns.
 */
import { onMounted, watch } from 'vue'
import {
  useMultiRunComparisonState,
  useMultiRunComparisonPersistence,
  useMultiRunComparisonApi,
  useMultiRunComparisonChart,
  useMultiRunComparisonActions
} from './multi_run_comparison/composables'

// State
const {
  allPresets,
  selectedPresetIds,
  loading,
  errorMessage,
  comparisonResult,
  timeChartCanvas
} = useMultiRunComparisonState()

// Persistence
const { loadPersistedState, savePersistedState, clearPersistedState } =
  useMultiRunComparisonPersistence(selectedPresetIds, comparisonResult)

// Chart
const { chartData, destroyChart } = useMultiRunComparisonChart(
  comparisonResult,
  timeChartCanvas
)

// Actions
const { presetsWithLineage, resetComparison, exportComparisonCSV } =
  useMultiRunComparisonActions(
    allPresets,
    selectedPresetIds,
    comparisonResult,
    errorMessage,
    destroyChart,
    clearPersistedState
  )

// API
const { fetchPresets, runComparison } = useMultiRunComparisonApi(
  allPresets,
  selectedPresetIds,
  loading,
  errorMessage,
  comparisonResult,
  savePersistedState
)

// Lifecycle
onMounted(async () => {
  loadPersistedState()
  await fetchPresets()
})

// Watch for selection changes and persist
watch(
  () => selectedPresetIds.value,
  () => {
    savePersistedState()
  },
  { deep: true }
)
</script>

<style scoped>
/* Tailwind handles most styling */
</style>
