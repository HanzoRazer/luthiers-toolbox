<template>
  <div class="p-4 space-y-4">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold">
        Stratocaster Neck Generator
      </h1>

      <!-- Preset Selector -->
      <div class="flex items-center gap-3">
        <label class="flex items-center gap-2">
          <span class="text-sm font-medium">Load Preset:</span>
          <select
            v-model="selectedPresetId"
            class="border rounded px-3 py-2 text-sm"
            @change="loadPresetParams"
          >
            <option value="">-- Select Preset --</option>
            <option
              v-for="preset in neckPresets"
              :key="preset.id"
              :value="preset.id"
            >
              {{ preset.name }}
            </option>
          </select>
        </label>
        <button
          v-if="selectedPresetId"
          class="text-xs px-2 py-1 border rounded hover:bg-gray-50"
          title="Clear preset selection"
          @click="clearPreset"
        >
          Clear
        </button>
      </div>
    </div>

    <!-- Quick Preset Buttons -->
    <div class="flex gap-2">
      <button
        class="px-3 py-1 text-sm border rounded hover:bg-blue-50"
        @click="loadDefaults"
      >
        Modern C (Standard)
      </button>
      <button
        class="px-3 py-1 text-sm border rounded hover:bg-amber-50"
        @click="loadVintagePreset"
      >
        Vintage V (50s/60s)
      </button>
      <button
        class="px-3 py-1 text-sm border rounded hover:bg-purple-50"
        @click="load24FretPreset"
      >
        24-Fret Shred
      </button>
    </div>

    <!-- Preset Feedback -->
    <div
      v-if="presetLoadedMessage"
      class="p-3 bg-blue-50 border border-blue-200 rounded text-sm"
    >
      {{ presetLoadedMessage }}
    </div>

    <!-- Validation Warnings -->
    <div
      v-if="validationWarnings.length > 0"
      class="p-3 bg-yellow-50 border border-yellow-300 rounded text-sm"
    >
      <p class="font-semibold mb-2">
        Parameter Warnings:
      </p>
      <ul class="list-disc list-inside space-y-1">
        <li
          v-for="warning in validationWarnings"
          :key="warning.field"
          :class="{
            'text-red-600': warning.severity === 'error',
            'text-yellow-700': warning.severity === 'warning'
          }"
        >
          {{ warning.message }}
        </li>
      </ul>
    </div>

    <!-- Modified Indicator -->
    <div
      v-if="isModifiedFromPreset"
      class="p-3 bg-purple-50 border border-purple-200 rounded text-sm flex items-center justify-between"
    >
      <span>Modified from preset</span>
      <button
        :disabled="!selectedPresetId"
        class="px-3 py-1 bg-purple-600 text-white rounded hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed text-xs"
        @click="revertToPreset"
      >
        Revert to Original
      </button>
    </div>

    <div class="grid md:grid-cols-3 gap-4">
      <!-- Parameter Form -->
      <div class="md:col-span-2 space-y-4">
        <!-- Blank Dimensions -->
        <div class="p-4 border rounded">
          <h3 class="font-semibold text-lg mb-3">
            Blank Dimensions
          </h3>
          <div class="grid grid-cols-3 gap-3">
            <label class="flex flex-col">
              <span class="text-sm font-medium mb-1">Length (in)</span>
              <input
                v-model.number="form.blank_length"
                type="number"
                step="0.125"
                class="border p-2 rounded"
              >
            </label>
            <label class="flex flex-col">
              <span class="text-sm font-medium mb-1">Width (in)</span>
              <input
                v-model.number="form.blank_width"
                type="number"
                step="0.125"
                class="border p-2 rounded"
              >
            </label>
            <label class="flex flex-col">
              <span class="text-sm font-medium mb-1">Thickness (in)</span>
              <input
                v-model.number="form.blank_thickness"
                type="number"
                step="0.0625"
                class="border p-2 rounded"
              >
            </label>
          </div>
        </div>

        <!-- Scale & Dimensions -->
        <div class="p-4 border rounded">
          <h3 class="font-semibold text-lg mb-3">
            Scale & Dimensions
          </h3>
          <div class="grid grid-cols-2 gap-3">
            <label class="flex flex-col">
              <span class="text-sm font-medium mb-1">Scale Length (in)</span>
              <input
                v-model.number="form.scale_length"
                type="number"
                step="0.125"
                class="border p-2 rounded"
              >
              <span class="text-xs text-gray-500 mt-1">Standard Fender: 25.5"</span>
            </label>
            <label class="flex flex-col">
              <span class="text-sm font-medium mb-1">Neck Length (in)</span>
              <input
                v-model.number="form.neck_length"
                type="number"
                step="0.125"
                class="border p-2 rounded"
              >
            </label>
            <label class="flex flex-col">
              <span class="text-sm font-medium mb-1">Nut Width (in)</span>
              <input
                v-model.number="form.nut_width"
                type="number"
                step="0.001"
                class="border p-2 rounded"
              >
              <span class="text-xs text-gray-500 mt-1">1.65" standard, 1.875" wide</span>
            </label>
            <label class="flex flex-col">
              <span class="text-sm font-medium mb-1">Heel Width (in)</span>
              <input
                v-model.number="form.heel_width"
                type="number"
                step="0.125"
                class="border p-2 rounded"
              >
            </label>
          </div>
        </div>

        <!-- Fretboard -->
        <div class="p-4 border rounded">
          <h3 class="font-semibold text-lg mb-3">
            Fretboard
          </h3>
          <div class="grid grid-cols-2 gap-3">
            <label class="flex flex-col">
              <span class="text-sm font-medium mb-1">Fretboard Radius (in)</span>
              <input
                v-model.number="form.fretboard_radius"
                type="number"
                step="0.25"
                class="border p-2 rounded"
              >
              <span class="text-xs text-gray-500 mt-1">7.25" vintage, 9.5" modern</span>
            </label>
            <label class="flex flex-col">
              <span class="text-sm font-medium mb-1">Fret Count</span>
              <select
                v-model.number="form.fret_count"
                class="border p-2 rounded"
              >
                <option :value="21">21 (Vintage)</option>
                <option :value="22">22 (Standard)</option>
                <option :value="24">24 (Extended)</option>
              </select>
            </label>
            <label class="flex items-center gap-2 col-span-2">
              <input
                v-model="form.compound_radius"
                type="checkbox"
                class="form-checkbox"
              >
              <span class="text-sm">Compound Radius</span>
            </label>
            <label
              v-if="form.compound_radius"
              class="flex flex-col col-span-2"
            >
              <span class="text-sm font-medium mb-1">Heel Radius (in)</span>
              <input
                v-model.number="form.fretboard_radius_heel"
                type="number"
                step="0.5"
                class="border p-2 rounded"
              >
              <span class="text-xs text-gray-500 mt-1">Typically 12"-16" at heel</span>
            </label>
          </div>
        </div>

        <!-- Profile Shape -->
        <div class="p-4 border rounded">
          <h3 class="font-semibold text-lg mb-3">
            Profile Shape
          </h3>
          <div class="grid grid-cols-2 gap-3">
            <label class="flex flex-col">
              <span class="text-sm font-medium mb-1">Profile Type</span>
              <select
                v-model="form.profile_type"
                class="border p-2 rounded"
              >
                <option value="C">C (Classic rounded)</option>
                <option value="modern_C">Modern C (Slightly flat)</option>
                <option value="V">V (Angular, 50s style)</option>
                <option value="soft_V">Soft V (Rounded V)</option>
                <option value="D">D (Flat back)</option>
              </select>
            </label>
            <label
              v-if="form.profile_type === 'V' || form.profile_type === 'soft_V'"
              class="flex flex-col"
            >
              <span class="text-sm font-medium mb-1">Shoulder Width</span>
              <input
                v-model.number="form.shoulder_width"
                type="number"
                step="0.05"
                min="0.3"
                max="1.0"
                class="border p-2 rounded"
              >
              <span class="text-xs text-gray-500 mt-1">0.3 (soft) to 1.0 (sharp)</span>
            </label>
            <label class="flex flex-col">
              <span class="text-sm font-medium mb-1">Thickness @ 1st Fret (in)</span>
              <input
                v-model.number="form.thickness_1st_fret"
                type="number"
                step="0.01"
                class="border p-2 rounded"
              >
            </label>
            <label class="flex flex-col">
              <span class="text-sm font-medium mb-1">Thickness @ 12th Fret (in)</span>
              <input
                v-model.number="form.thickness_12th_fret"
                type="number"
                step="0.01"
                class="border p-2 rounded"
              >
            </label>
          </div>
        </div>

        <!-- Headstock (Flat, 6-in-line) -->
        <div class="p-4 border rounded">
          <h3 class="font-semibold text-lg mb-3">
            Headstock (Flat, 6-in-line)
          </h3>
          <div class="grid grid-cols-3 gap-3">
            <label class="flex flex-col">
              <span class="text-sm font-medium mb-1">Length (in)</span>
              <input
                v-model.number="form.headstock_length"
                type="number"
                step="0.125"
                class="border p-2 rounded"
              >
            </label>
            <label class="flex flex-col">
              <span class="text-sm font-medium mb-1">Thickness (in)</span>
              <input
                v-model.number="form.headstock_thickness"
                type="number"
                step="0.0625"
                class="border p-2 rounded"
              >
            </label>
            <label class="flex flex-col">
              <span class="text-sm font-medium mb-1">Taper (in)</span>
              <input
                v-model.number="form.headstock_taper"
                type="number"
                step="0.125"
                class="border p-2 rounded"
              >
            </label>
            <label class="flex flex-col">
              <span class="text-sm font-medium mb-1">Tuner Spacing (in)</span>
              <input
                v-model.number="form.tuner_spacing"
                type="number"
                step="0.0625"
                class="border p-2 rounded"
              >
            </label>
            <label class="flex flex-col">
              <span class="text-sm font-medium mb-1">Tuner Hole Diameter (in)</span>
              <input
                v-model.number="form.tuner_diameter"
                type="number"
                step="0.0625"
                class="border p-2 rounded"
              >
            </label>
          </div>
        </div>

        <!-- Truss Rod -->
        <div class="p-4 border rounded">
          <h3 class="font-semibold text-lg mb-3">
            Truss Rod
          </h3>
          <div class="grid grid-cols-3 gap-3">
            <label class="flex flex-col">
              <span class="text-sm font-medium mb-1">Channel Width (in)</span>
              <input
                v-model.number="form.truss_rod_channel_width"
                type="number"
                step="0.0625"
                class="border p-2 rounded"
              >
            </label>
            <label class="flex flex-col">
              <span class="text-sm font-medium mb-1">Channel Depth (in)</span>
              <input
                v-model.number="form.truss_rod_channel_depth"
                type="number"
                step="0.0625"
                class="border p-2 rounded"
              >
            </label>
            <label class="flex flex-col">
              <span class="text-sm font-medium mb-1">Access</span>
              <select
                v-model="form.truss_rod_access"
                class="border p-2 rounded"
              >
                <option value="headstock">Headstock (Vintage)</option>
                <option value="heel">Heel (Modern)</option>
              </select>
            </label>
          </div>
        </div>

        <!-- Options -->
        <div class="p-4 border rounded">
          <h3 class="font-semibold text-lg mb-3">
            Options
          </h3>
          <div class="space-y-2">
            <label class="flex items-center gap-2">
              <input
                v-model="form.include_fretboard"
                type="checkbox"
                class="form-checkbox"
              >
              <span class="text-sm">Include Fretboard Geometry</span>
            </label>
            <label class="flex items-center gap-2">
              <input
                v-model="form.alignment_pin_holes"
                type="checkbox"
                class="form-checkbox"
              >
              <span class="text-sm">Add Alignment Pin Holes</span>
            </label>
            <label class="flex items-center gap-2">
              <input
                v-model="form.skunk_stripe"
                type="checkbox"
                class="form-checkbox"
              >
              <span class="text-sm">Skunk Stripe (One-piece maple)</span>
            </label>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="flex gap-2">
          <button
            class="px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700 transition-colors"
            @click="generateNeck"
          >
            Generate Neck
          </button>
          <button
            class="px-4 py-2 rounded border hover:bg-gray-50 transition-colors"
            @click="exportJSON"
          >
            Export JSON
          </button>
          <button
            :disabled="!generatedGeometry"
            class="px-4 py-2 rounded bg-green-600 text-white hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            @click="exportDXF"
          >
            Export DXF
          </button>
        </div>
      </div>

      <!-- Info Panel -->
      <div class="space-y-4">
        <div class="p-4 border rounded bg-gray-50">
          <h3 class="font-semibold mb-2">
            About Stratocaster Necks
          </h3>
          <p class="text-sm opacity-80">
            Stratocaster necks feature a flat headstock with 6-in-line tuners.
            The 25.5" scale length provides more string tension than Gibson's 24.75".
            Profile options range from the vintage V to the modern C shape.
          </p>
        </div>

        <div class="p-4 border rounded bg-blue-50">
          <h3 class="font-semibold mb-2">
            Standard Fender Specs
          </h3>
          <ul class="text-sm space-y-1 opacity-80">
            <li><strong>Scale:</strong> 25.5"</li>
            <li><strong>Nut Width:</strong> 1.65" (42mm)</li>
            <li><strong>Headstock:</strong> Flat (no angle)</li>
            <li><strong>Fretboard Radius:</strong> 9.5" (modern) / 7.25" (vintage)</li>
            <li><strong>Tuners:</strong> 6-in-line</li>
          </ul>
        </div>

        <div
          v-if="generatedGeometry"
          class="p-4 border rounded bg-green-50"
        >
          <h3 class="font-semibold mb-2">
            Geometry Generated
          </h3>
          <ul class="text-sm space-y-1">
            <li>Profile points: {{ generatedGeometry.profile.length }}</li>
            <li>Headstock points: {{ generatedGeometry.headstock.length }}</li>
            <li>Tuner holes: {{ generatedGeometry.tuner_holes.length }}</li>
            <li>Fret slots: {{ generatedGeometry.fret_slots.length }}</li>
            <li v-if="generatedGeometry.fretboard">
              Fretboard points: {{ generatedGeometry.fretboard.length }}
            </li>
            <li>Truss rod channel: {{ generatedGeometry.truss_rod_channel.length }} points</li>
          </ul>
          <p class="text-xs opacity-70 mt-2">
            Ready for CAM export or 3D modeling.
          </p>
        </div>

        <div class="p-4 border rounded bg-yellow-50">
          <h3 class="font-semibold mb-2">
            CNC Notes
          </h3>
          <ul class="text-xs space-y-1 opacity-80">
            <li>Profile carving requires 4-axis or duplicator</li>
            <li>Flat headstock simplifies CNC operations</li>
            <li>String trees may require additional drilling</li>
            <li>Skunk stripe requires walnut inlay operation</li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute } from 'vue-router'
import {
  useStratNeckState,
  useStratNeckPresets,
  useStratNeckActions
} from './strat_neck/composables'

const route = useRoute()

// State
const {
  form,
  generatedGeometry,
  neckPresets,
  selectedPresetId,
  presetLoadedMessage,
  originalPresetParams,
  validationWarnings
} = useStratNeckState()

// Presets
const {
  isModifiedFromPreset,
  fetchNeckPresets,
  loadPresetParams,
  clearPreset,
  revertToPreset
} = useStratNeckPresets(
  form,
  generatedGeometry,
  neckPresets,
  selectedPresetId,
  presetLoadedMessage,
  originalPresetParams,
  validationWarnings
)

// Actions
const {
  generateNeck,
  loadDefaults,
  loadVintagePreset,
  load24FretPreset,
  exportJSON,
  exportDXF
} = useStratNeckActions(form, generatedGeometry)

// Lifecycle - fetch presets and check for query parameter
onMounted(async () => {
  await fetchNeckPresets()

  // Check if preset_id was passed via query parameter (from PresetHub)
  const presetIdFromQuery = route.query.preset_id as string
  if (presetIdFromQuery) {
    selectedPresetId.value = presetIdFromQuery
    await loadPresetParams()
  }
})
</script>

<style scoped>
/* Component-specific styles */
</style>
