<template>
  <div class="p-4 space-y-4">
    <div class="flex items-center justify-between gap-4">
      <h1 class="text-2xl font-bold">
        Radius Dish Designer
      </h1>
      <div class="flex items-center gap-2 text-sm">
        <span class="opacity-70">Guides:</span>
        <a
          class="underline"
          href="/radius_dish/Acoustic_Guitar_Radius_Explained.pdf"
          target="_blank"
          rel="noopener"
        >
          Radius Explained (PDF)
        </a>
        <span>·</span>
        <a
          class="underline"
          href="/radius_dish/Router_Trammel_Radius_Dish_Guide.pdf"
          target="_blank"
          rel="noopener"
        >
          Router Trammel Guide (PDF)
        </a>
      </div>
    </div>

    <div class="flex gap-2 flex-wrap">
      <button
        v-for="t in tabs"
        :key="t"
        class="px-3 py-1 rounded border transition-colors"
        :class="tab === t ? 'bg-blue-100 border-blue-500' : 'hover:bg-gray-50'"
        @click="tab = t"
      >
        {{ t }}
      </button>
    </div>

    <!-- Design Tab -->
    <RadiusDishDesign
      v-if="tab === 'Design'"
      :selected-radius="selectedRadius"
      @update:selected-radius="selectedRadius = $event"
      @download-dxf="downloadDXF"
      @download-gcode="downloadGCode"
      @view-svg="viewSVG"
    />

    <!-- Calculator Tab -->
    <RadiusDishCalculator v-else-if="tab === 'Calculator'" />

    <!-- CNC Setup Tab -->
    <RadiusDishCncSetup
      v-else-if="tab === 'CNC Setup'"
      :selected-radius="selectedRadius"
      @download-gcode="downloadGCode"
    />

    <!-- Docs Tab -->
    <RadiusDishDocs v-else-if="tab === 'Docs'" />
  </div>
</template>

<script setup lang="ts">
/**
 * RadiusDishDesigner.vue
 *
 * Radius dish designer for archtop guitar construction.
 *
 * REFACTORED: Child components extracted for decomposition:
 * - RadiusDishDesign: Design tab with radius selection and preview
 * - RadiusDishCalculator: Calculator tab with depth calculator
 * - RadiusDishCncSetup: CNC Setup tab with machining instructions
 * - RadiusDishDocs: Documentation tab with theory and guides
 */
import { ref } from 'vue'
import {
  RadiusDishDesign,
  RadiusDishCalculator,
  RadiusDishCncSetup,
  RadiusDishDocs
} from './radius-dish'

const tabs = ['Design', 'Calculator', 'CNC Setup', 'Docs']
const tab = ref('Design')

// Shared state
const selectedRadius = ref<'15ft' | '25ft'>('15ft')

// Actions
function downloadDXF() {
  const url = `/radius_dish/Radius_Arc_${selectedRadius.value}.dxf`
  const link = document.createElement('a')
  link.href = url
  link.download = `Radius_Arc_${selectedRadius.value}.dxf`
  link.click()
}

function downloadGCode() {
  const radiusNum = selectedRadius.value === '15ft' ? '15ft' : '25ft'
  const url = `/radius_dish/radius_dish_${radiusNum}_grbl.nc`
  const link = document.createElement('a')
  link.href = url
  link.download = `radius_dish_${radiusNum}_grbl.nc`
  link.click()
}

function viewSVG() {
  window.open(`/radius_dish/Radius_Arc_${selectedRadius.value}.svg`, '_blank')
}
</script>

<style scoped>
/* Component-specific styles */
</style>
