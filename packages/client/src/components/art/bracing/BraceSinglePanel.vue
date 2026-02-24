<script setup lang="ts">
/**
 * BraceSinglePanel.vue
 * Single brace calculator panel with profile selection, dimensions, and results.
 */
import { COMMON_WOODS, type BracingPreviewResponse, type BracingPresetInfo } from '@/api/art-studio'
import type { ProfileTypeInfo } from './bracingTypes'

defineProps<{
  profileType: string
  width: number
  height: number
  length: number
  density: number
  selectedWood: string | null
  singleResult: BracingPreviewResponse | null
  profileTypes: ProfileTypeInfo[]
  presets: BracingPresetInfo[]
}>()

const emit = defineEmits<{
  'update:profileType': [value: string]
  'update:width': [value: number]
  'update:height': [value: number]
  'update:length': [value: number]
  'update:density': [value: number]
  setWood: [value: string | null]
  applyPreset: [preset: BracingPresetInfo]
  addToBatch: []
}>()
</script>

<template>
  <div class="space-y-4">
    <h2 class="text-lg font-semibold text-gray-800">
      Single Brace Calculator
    </h2>

    <!-- Preset Quick-Apply -->
    <div class="bg-gray-50 rounded-lg p-4">
      <label class="block text-sm font-medium text-gray-700 mb-2">Quick Presets</label>
      <div class="flex flex-wrap gap-2">
        <button
          v-for="p in presets"
          :key="p.name"
          class="text-xs px-2 py-1 bg-white border rounded hover:bg-gray-100"
          :title="p.description"
          @click="emit('applyPreset', p)"
        >
          {{ p.name }}
        </button>
      </div>
    </div>

    <!-- Profile Type -->
    <div class="bg-white border rounded-lg p-4">
      <h3 class="font-semibold text-gray-800 mb-3">
        Profile Type
      </h3>
      <div class="grid grid-cols-2 gap-2">
        <button
          v-for="pt in profileTypes"
          :key="pt.value"
          class="p-3 rounded-lg border-2 text-left transition-all"
          :class="
            profileType === pt.value
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-200 hover:border-gray-400'
          "
          @click="emit('update:profileType', pt.value)"
        >
          <div class="font-medium text-sm">
            {{ pt.label }}
          </div>
          <div class="text-xs text-gray-500">
            {{ pt.desc }}
          </div>
        </button>
      </div>
    </div>

    <!-- Dimensions -->
    <div class="bg-white border rounded-lg p-4 space-y-3">
      <h3 class="font-semibold text-gray-800">
        Dimensions
      </h3>

      <div>
        <label class="block text-xs text-gray-600 mb-1">Width (mm)</label>
        <input
          :value="width"
          type="range"
          min="5"
          max="30"
          step="0.5"
          class="w-full"
          @input="emit('update:width', Number(($event.target as HTMLInputElement).value))"
        >
        <div class="text-sm text-gray-700 text-right">
          {{ width.toFixed(1) }} mm
        </div>
      </div>

      <div>
        <label class="block text-xs text-gray-600 mb-1">Height (mm)</label>
        <input
          :value="height"
          type="range"
          min="3"
          max="20"
          step="0.5"
          class="w-full"
          @input="emit('update:height', Number(($event.target as HTMLInputElement).value))"
        >
        <div class="text-sm text-gray-700 text-right">
          {{ height.toFixed(1) }} mm
        </div>
      </div>

      <div>
        <label class="block text-xs text-gray-600 mb-1">Length (mm)</label>
        <input
          :value="length"
          type="range"
          min="50"
          max="500"
          step="5"
          class="w-full"
          @input="emit('update:length', Number(($event.target as HTMLInputElement).value))"
        >
        <div class="text-sm text-gray-700 text-right">
          {{ length.toFixed(0) }} mm
        </div>
      </div>
    </div>

    <!-- Wood Selection -->
    <div class="bg-white border rounded-lg p-4 space-y-3">
      <h3 class="font-semibold text-gray-800">
        Wood Type
      </h3>

      <select
        :value="selectedWood"
        class="w-full border rounded px-3 py-2 text-sm"
        @change="emit('setWood', ($event.target as HTMLSelectElement).value || null)"
      >
        <option :value="null">
          Custom
        </option>
        <option
          v-for="w in COMMON_WOODS"
          :key="w.name"
          :value="w.name"
        >
          {{ w.name }} ({{ w.density }} kg/m³)
        </option>
      </select>

      <div>
        <label class="block text-xs text-gray-600 mb-1">Density (kg/m³)</label>
        <input
          :value="density"
          type="number"
          min="200"
          max="1200"
          step="10"
          class="w-full border rounded px-3 py-2 text-sm"
          @input="emit('update:density', Number(($event.target as HTMLInputElement).value))"
        >
      </div>
    </div>

    <!-- Single Brace Results -->
    <div
      v-if="singleResult"
      class="bg-white border rounded-lg p-4"
    >
      <h3 class="font-semibold text-gray-800 mb-3">
        Section Properties
      </h3>

      <table class="w-full text-sm">
        <tbody>
          <tr class="border-b">
            <td class="py-2 text-gray-600">
              Cross-Section Area
            </td>
            <td class="py-2 text-right font-mono">
              {{ singleResult.section.area_mm2.toFixed(2) }} mm²
            </td>
          </tr>
          <tr class="border-b">
            <td class="py-2 text-gray-600">
              Centroid Height
            </td>
            <td class="py-2 text-right font-mono">
              {{ singleResult.section.centroid_y_mm.toFixed(2) }} mm
            </td>
          </tr>
          <tr class="border-b">
            <td class="py-2 text-gray-600">
              Moment of Inertia
            </td>
            <td class="py-2 text-right font-mono">
              {{ singleResult.section.inertia_mm4.toFixed(1) }} mm⁴
            </td>
          </tr>
          <tr class="border-b">
            <td class="py-2 text-gray-600">
              Section Modulus
            </td>
            <td class="py-2 text-right font-mono">
              {{ singleResult.section.section_modulus_mm3.toFixed(1) }} mm³
            </td>
          </tr>
          <tr class="border-b bg-amber-50">
            <td class="py-2 text-gray-700 font-medium">
              Mass
            </td>
            <td class="py-2 text-right font-mono font-bold">
              {{ singleResult.mass_grams.toFixed(2) }} g
            </td>
          </tr>
          <tr
            v-if="singleResult.stiffness_estimate"
            class="bg-blue-50"
          >
            <td class="py-2 text-gray-700 font-medium">
              Stiffness Index
            </td>
            <td class="py-2 text-right font-mono font-bold">
              {{ singleResult.stiffness_estimate.toFixed(0) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Add to Batch Button -->
    <button
      class="w-full px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600"
      @click="emit('addToBatch')"
    >
      + Add to Batch
    </button>
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
