<script setup lang="ts">
/**
 * ArtStudioInlay.vue
 *
 * Fretboard inlay pattern designer.
 * Generates dot, diamond, block, and custom inlay patterns with DXF export.
 *
 * REFACTORED: Uses composables for cleaner separation of concerns.
 */
import { watch, onMounted } from 'vue'
import { COMMON_SCALE_LENGTHS } from '@/api/art-studio'
import FretPositionTable from './FretPositionTable.vue'
import InlaySummaryPanel from './InlaySummaryPanel.vue'
import InlayDetailsTable from './InlayDetailsTable.vue'
import {
  PATTERN_TYPES,
  useInlayState,
  useInlayPresets,
  useInlayPreview,
  useInlayFrets
} from './composables'

// =============================================================================
// COMPOSABLES
// =============================================================================

const {
  loading,
  error,
  previewResult,
  fretData,
  presets,
  selectedPreset,
  patternType,
  scaleLength,
  fretboardWidthNut,
  fretboardWidthBody,
  numFrets,
  inlaySize,
  doubleAt12,
  doubleSpacing,
  selectedFrets,
  dxfVersion,
  layerPrefix,
  selectedScalePreset
} = useInlayState()

const { refreshPreview, exportDXF } = useInlayPreview(
  loading,
  error,
  previewResult,
  patternType,
  selectedFrets,
  scaleLength,
  fretboardWidthNut,
  fretboardWidthBody,
  numFrets,
  inlaySize,
  doubleAt12,
  doubleSpacing,
  dxfVersion,
  layerPrefix
)

const { loadPresets, applyPreset } = useInlayPresets(
  presets,
  selectedPreset,
  error,
  patternType,
  selectedFrets,
  scaleLength,
  fretboardWidthNut,
  fretboardWidthBody,
  numFrets,
  inlaySize,
  doubleAt12,
  doubleSpacing,
  refreshPreview
)

const { loadFretPositions, toggleFret, selectStandardFrets, clearFrets } = useInlayFrets(
  fretData,
  selectedFrets,
  scaleLength,
  numFrets
)

// =============================================================================
// WATCHERS
// =============================================================================

watch([scaleLength, numFrets], () => loadFretPositions())

watch(
  [patternType, scaleLength, inlaySize, doubleAt12],
  () => refreshPreview(),
  { debounce: 300 } as any
)

// =============================================================================
// LIFECYCLE
// =============================================================================

onMounted(() => {
  loadPresets()
  loadFretPositions()
  refreshPreview()
})
</script>

<template>
  <div class="p-4 max-w-6xl mx-auto">
    <h1 class="text-2xl font-bold mb-4 flex items-center gap-2">
      <span class="text-3xl">◆</span>
      Fretboard Inlay Designer
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
      <!-- Left Panel: Pattern Settings -->
      <div class="space-y-4">
        <!-- Preset Selector -->
        <div class="bg-gray-50 rounded-lg p-4">
          <label class="block text-sm font-medium text-gray-700 mb-2">Load Preset</label>
          <div class="flex gap-2">
            <select
              v-model="selectedPreset"
              class="flex-1 border rounded px-3 py-2 text-sm"
            >
              <option :value="null">
                — Select preset —
              </option>
              <option
                v-for="p in presets"
                :key="p.name"
                :value="p.name"
              >
                {{ p.name }}
              </option>
            </select>
            <button
              class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
              :disabled="!selectedPreset || loading"
              @click="applyPreset"
            >
              Apply
            </button>
          </div>
        </div>

        <!-- Pattern Type -->
        <div class="bg-white border rounded-lg p-4">
          <h3 class="font-semibold text-gray-800 mb-3">
            Pattern Type
          </h3>
          <div class="grid grid-cols-5 gap-2">
            <button
              v-for="pt in PATTERN_TYPES"
              :key="pt.value"
              class="p-3 rounded-lg border-2 text-center transition-all"
              :class="
                patternType === pt.value
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-400'
              "
              @click="patternType = pt.value"
            >
              <div class="text-2xl">
                {{ pt.icon }}
              </div>
              <div class="text-xs mt-1">
                {{ pt.label }}
              </div>
            </button>
          </div>
        </div>

        <!-- Scale Length -->
        <div class="bg-white border rounded-lg p-4 space-y-3">
          <h3 class="font-semibold text-gray-800">
            Scale Length
          </h3>

          <select
            v-model="selectedScalePreset"
            class="w-full border rounded px-3 py-2 text-sm"
          >
            <option :value="null">
              Custom
            </option>
            <option
              v-for="s in COMMON_SCALE_LENGTHS"
              :key="s.name"
              :value="s.name"
            >
              {{ s.name }}
            </option>
          </select>

          <div>
            <label class="block text-xs text-gray-600 mb-1">Scale Length (mm)</label>
            <input
              v-model.number="scaleLength"
              type="number"
              min="500"
              max="800"
              step="0.1"
              class="w-full border rounded px-3 py-2 text-sm"
            >
          </div>
        </div>

        <!-- Fretboard Dimensions -->
        <div class="bg-white border rounded-lg p-4 space-y-3">
          <h3 class="font-semibold text-gray-800">
            Fretboard Dimensions
          </h3>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs text-gray-600 mb-1">Width at Nut (mm)</label>
              <input
                v-model.number="fretboardWidthNut"
                type="number"
                min="35"
                max="60"
                step="0.5"
                class="w-full border rounded px-2 py-1 text-sm"
              >
            </div>
            <div>
              <label class="block text-xs text-gray-600 mb-1">Width at Body (mm)</label>
              <input
                v-model.number="fretboardWidthBody"
                type="number"
                min="45"
                max="75"
                step="0.5"
                class="w-full border rounded px-2 py-1 text-sm"
              >
            </div>
          </div>

          <div>
            <label class="block text-xs text-gray-600 mb-1">Number of Frets</label>
            <input
              v-model.number="numFrets"
              type="range"
              min="12"
              max="27"
              class="w-full"
            >
            <div class="text-sm text-gray-700 text-right">
              {{ numFrets }} frets
            </div>
          </div>
        </div>

        <!-- Inlay Settings -->
        <div class="bg-white border rounded-lg p-4 space-y-3">
          <h3 class="font-semibold text-gray-800">
            Inlay Settings
          </h3>

          <div>
            <label class="block text-xs text-gray-600 mb-1">Inlay Size (mm)</label>
            <input
              v-model.number="inlaySize"
              type="range"
              min="3"
              max="15"
              step="0.5"
              class="w-full"
            >
            <div class="text-sm text-gray-700 text-right">
              {{ inlaySize.toFixed(1) }} mm
            </div>
          </div>

          <label class="flex items-center gap-2 text-sm">
            <input
              v-model="doubleAt12"
              type="checkbox"
            >
            Double markers at 12th fret
          </label>

          <div v-if="doubleAt12">
            <label class="block text-xs text-gray-600 mb-1">Double Spacing (mm)</label>
            <input
              v-model.number="doubleSpacing"
              type="number"
              min="4"
              max="20"
              step="0.5"
              class="w-full border rounded px-2 py-1 text-sm"
            >
          </div>
        </div>
      </div>

      <!-- Middle Panel: Fret Selection -->
      <div class="space-y-4">
        <!-- Fret Position Selector -->
        <div class="bg-white border rounded-lg p-4">
          <div class="flex justify-between items-center mb-3">
            <h3 class="font-semibold text-gray-800">
              Fret Positions
            </h3>
            <div class="flex gap-2">
              <button
                class="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
                @click="selectStandardFrets"
              >
                Standard
              </button>
              <button
                class="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                @click="clearFrets"
              >
                Clear
              </button>
            </div>
          </div>

          <div class="grid grid-cols-6 gap-2">
            <button
              v-for="fret in numFrets"
              :key="fret"
              class="p-2 text-sm rounded border-2 transition-all"
              :class="
                selectedFrets.includes(fret)
                  ? 'border-blue-500 bg-blue-100 font-bold'
                  : 'border-gray-200 hover:border-gray-400'
              "
              @click="toggleFret(fret)"
            >
              {{ fret }}
            </button>
          </div>

          <div class="mt-3 text-xs text-gray-500">
            Selected: {{ selectedFrets.join(", ") || "None" }}
          </div>
        </div>

        <!-- Fret Position Table -->
        <FretPositionTable
          v-if="fretData"
          :fret-data="fretData"
          :selected-frets="selectedFrets"
        />

        <!-- Export Options -->
        <div class="bg-white border rounded-lg p-4 space-y-3">
          <h3 class="font-semibold text-gray-800">
            Export Options
          </h3>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs text-gray-600 mb-1">DXF Version</label>
              <select
                v-model="dxfVersion"
                class="w-full border rounded px-2 py-1 text-sm"
              >
                <option value="R12">
                  R12 (Most Compatible)
                </option>
                <option value="R2000">
                  R2000
                </option>
                <option value="R2010">
                  R2010
                </option>
              </select>
            </div>
            <div>
              <label class="block text-xs text-gray-600 mb-1">Layer Prefix</label>
              <input
                v-model="layerPrefix"
                type="text"
                class="w-full border rounded px-2 py-1 text-sm"
              >
            </div>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="flex gap-3">
          <button
            class="flex-1 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
            :disabled="loading"
            @click="refreshPreview"
          >
            {{ loading ? "Generating..." : "Preview" }}
          </button>
          <button
            class="flex-1 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:opacity-50"
            :disabled="loading || !previewResult"
            @click="exportDXF"
          >
            Export DXF
          </button>
        </div>
      </div>

      <!-- Right Panel: Preview -->
      <div class="space-y-4">
        <!-- SVG Preview -->
        <div class="bg-white border rounded-lg p-4">
          <h3 class="font-semibold text-gray-800 mb-3">
            Preview
          </h3>

          <div
            v-if="previewResult?.preview_svg"
            class="bg-gray-100 rounded p-2 overflow-auto"
            style="max-height: 500px"
            v-html="previewResult.preview_svg"
          />
          <div
            v-else
            class="bg-gray-100 rounded p-4 flex items-center justify-center min-h-[300px] text-gray-400"
          >
            Click Preview to generate
          </div>
        </div>

        <!-- Inlay Summary -->
        <InlaySummaryPanel
          v-if="previewResult"
          :result="previewResult.result"
          :pattern-type="patternType"
        />

        <!-- Inlay Details -->
        <InlayDetailsTable
          v-if="previewResult?.result.inlays?.length"
          :inlays="previewResult.result.inlays"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
input[type="range"] {
  @apply h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer;
}
input[type="range"]::-webkit-slider-thumb {
  @apply appearance-none w-4 h-4 bg-blue-500 rounded-full cursor-pointer;
}
</style>
