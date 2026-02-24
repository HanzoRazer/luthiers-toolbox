<script setup lang="ts">
/**
 * RosetteParametersPanel.vue
 * Left panel for rosette parameters, purfling config, and export options.
 */
import { PURFLING_MATERIALS, type PurflingBand, type RosettePresetInfo } from '@/api/art-studio'

defineProps<{
  presets: RosettePresetInfo[]
  selectedPreset: string | null
  soundholeDiameter: number
  centralBand: number
  channelDepth: number
  innerPurfling: PurflingBand[]
  outerPurfling: PurflingBand[]
  centerX: number
  centerY: number
  includePurflingRings: boolean
  loading: boolean
  hasPreview: boolean
}>()

const emit = defineEmits<{
  'update:selectedPreset': [value: string | null]
  'update:soundholeDiameter': [value: number]
  'update:centralBand': [value: number]
  'update:channelDepth': [value: number]
  'update:centerX': [value: number]
  'update:centerY': [value: number]
  'update:includePurflingRings': [value: boolean]
  applyPreset: []
  addPurflingBand: [side: 'inner' | 'outer']
  removePurflingBand: [side: 'inner' | 'outer', index: number]
  updatePurflingBand: [side: 'inner' | 'outer', index: number, band: PurflingBand]
  refreshPreview: []
  exportDXF: []
}>()

const purflingMaterials = PURFLING_MATERIALS
</script>

<template>
  <div class="space-y-4">
    <!-- Preset Selector -->
    <div class="bg-gray-50 rounded-lg p-4">
      <label class="block text-sm font-medium text-gray-700 mb-2">Load Preset</label>
      <div class="flex gap-2">
        <select
          :value="selectedPreset"
          class="flex-1 border rounded px-3 py-2 text-sm"
          @change="emit('update:selectedPreset', ($event.target as HTMLSelectElement).value || null)"
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
          @click="emit('applyPreset')"
        >
          Apply
        </button>
      </div>
    </div>

    <!-- Basic Dimensions -->
    <div class="bg-white border rounded-lg p-4 space-y-3">
      <h3 class="font-semibold text-gray-800">
        Dimensions
      </h3>

      <div>
        <label class="block text-xs text-gray-600 mb-1">Soundhole Diameter (mm)</label>
        <input
          :value="soundholeDiameter"
          type="range"
          min="50"
          max="150"
          step="0.5"
          class="w-full"
          @input="emit('update:soundholeDiameter', Number(($event.target as HTMLInputElement).value))"
        >
        <div class="text-sm text-gray-700 text-right">
          {{ soundholeDiameter.toFixed(1) }} mm
        </div>
      </div>

      <div>
        <label class="block text-xs text-gray-600 mb-1">Central Band Width (mm)</label>
        <input
          :value="centralBand"
          type="range"
          min="0"
          max="20"
          step="0.5"
          class="w-full"
          @input="emit('update:centralBand', Number(($event.target as HTMLInputElement).value))"
        >
        <div class="text-sm text-gray-700 text-right">
          {{ centralBand.toFixed(1) }} mm
        </div>
      </div>

      <div>
        <label class="block text-xs text-gray-600 mb-1">Channel Depth (mm)</label>
        <input
          :value="channelDepth"
          type="range"
          min="0.5"
          max="4.0"
          step="0.1"
          class="w-full"
          @input="emit('update:channelDepth', Number(($event.target as HTMLInputElement).value))"
        >
        <div class="text-sm text-gray-700 text-right">
          {{ channelDepth.toFixed(1) }} mm
        </div>
      </div>
    </div>

    <!-- Inner Purfling -->
    <div class="bg-white border rounded-lg p-4">
      <div class="flex justify-between items-center mb-3">
        <h3 class="font-semibold text-gray-800">
          Inner Purfling
        </h3>
        <button
          class="text-xs px-2 py-1 bg-green-100 text-green-700 rounded hover:bg-green-200"
          @click="emit('addPurflingBand', 'inner')"
        >
          + Add Band
        </button>
      </div>

      <div
        v-for="(band, idx) in innerPurfling"
        :key="'inner-' + idx"
        class="flex gap-2 mb-2 items-center"
      >
        <select
          :value="band.material"
          class="flex-1 border rounded px-2 py-1 text-sm"
          @change="emit('updatePurflingBand', 'inner', idx, { ...band, material: ($event.target as HTMLSelectElement).value })"
        >
          <option
            v-for="m in purflingMaterials"
            :key="m.code"
            :value="m.code"
          >
            {{ m.name }}
          </option>
        </select>
        <input
          :value="band.width_mm"
          type="number"
          min="0.5"
          max="10"
          step="0.1"
          class="w-20 border rounded px-2 py-1 text-sm"
          @input="emit('updatePurflingBand', 'inner', idx, { ...band, width_mm: Number(($event.target as HTMLInputElement).value) })"
        >
        <span class="text-xs text-gray-500">mm</span>
        <button
          v-if="innerPurfling.length > 0"
          class="text-red-500 hover:text-red-700"
          @click="emit('removePurflingBand', 'inner', idx)"
        >
          ✕
        </button>
      </div>
      <div
        v-if="innerPurfling.length === 0"
        class="text-sm text-gray-400 italic"
      >
        No inner purfling
      </div>
    </div>

    <!-- Outer Purfling -->
    <div class="bg-white border rounded-lg p-4">
      <div class="flex justify-between items-center mb-3">
        <h3 class="font-semibold text-gray-800">
          Outer Purfling
        </h3>
        <button
          class="text-xs px-2 py-1 bg-green-100 text-green-700 rounded hover:bg-green-200"
          @click="emit('addPurflingBand', 'outer')"
        >
          + Add Band
        </button>
      </div>

      <div
        v-for="(band, idx) in outerPurfling"
        :key="'outer-' + idx"
        class="flex gap-2 mb-2 items-center"
      >
        <select
          :value="band.material"
          class="flex-1 border rounded px-2 py-1 text-sm"
          @change="emit('updatePurflingBand', 'outer', idx, { ...band, material: ($event.target as HTMLSelectElement).value })"
        >
          <option
            v-for="m in purflingMaterials"
            :key="m.code"
            :value="m.code"
          >
            {{ m.name }}
          </option>
        </select>
        <input
          :value="band.width_mm"
          type="number"
          min="0.5"
          max="10"
          step="0.1"
          class="w-20 border rounded px-2 py-1 text-sm"
          @input="emit('updatePurflingBand', 'outer', idx, { ...band, width_mm: Number(($event.target as HTMLInputElement).value) })"
        >
        <span class="text-xs text-gray-500">mm</span>
        <button
          v-if="outerPurfling.length > 0"
          class="text-red-500 hover:text-red-700"
          @click="emit('removePurflingBand', 'outer', idx)"
        >
          ✕
        </button>
      </div>
      <div
        v-if="outerPurfling.length === 0"
        class="text-sm text-gray-400 italic"
      >
        No outer purfling
      </div>
    </div>

    <!-- Export Options -->
    <div class="bg-white border rounded-lg p-4 space-y-3">
      <h3 class="font-semibold text-gray-800">
        Export Options
      </h3>

      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="block text-xs text-gray-600 mb-1">Center X (mm)</label>
          <input
            :value="centerX"
            type="number"
            step="0.1"
            class="w-full border rounded px-2 py-1 text-sm"
            @input="emit('update:centerX', Number(($event.target as HTMLInputElement).value))"
          >
        </div>
        <div>
          <label class="block text-xs text-gray-600 mb-1">Center Y (mm)</label>
          <input
            :value="centerY"
            type="number"
            step="0.1"
            class="w-full border rounded px-2 py-1 text-sm"
            @input="emit('update:centerY', Number(($event.target as HTMLInputElement).value))"
          >
        </div>
      </div>

      <label class="flex items-center gap-2 text-sm">
        <input
          :checked="includePurflingRings"
          type="checkbox"
          @change="emit('update:includePurflingRings', ($event.target as HTMLInputElement).checked)"
        >
        Include individual purfling ring circles
      </label>
    </div>

    <!-- Action Buttons -->
    <div class="flex gap-3">
      <button
        class="flex-1 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
        :disabled="loading"
        @click="emit('refreshPreview')"
      >
        {{ loading ? 'Calculating...' : 'Preview' }}
      </button>
      <button
        class="flex-1 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:opacity-50"
        :disabled="loading || !hasPreview"
        @click="emit('exportDXF')"
      >
        Export DXF
      </button>
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
