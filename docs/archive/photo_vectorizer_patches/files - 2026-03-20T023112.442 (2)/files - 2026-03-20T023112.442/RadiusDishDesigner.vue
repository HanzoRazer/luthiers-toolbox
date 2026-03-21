<template>
  <div class="p-4 space-y-4">
    <div class="flex items-center justify-between gap-4">
      <h1 class="text-2xl font-bold">Radius Dish Designer</h1>
      <div class="flex items-center gap-2 text-sm">
        <span class="opacity-70">Guides:</span>
        <a class="underline" href="/radius_dish/Acoustic_Guitar_Radius_Explained.pdf"
          target="_blank" rel="noopener">Radius Explained</a>
        <span>·</span>
        <a class="underline" href="/radius_dish/Router_Trammel_Radius_Dish_Guide.pdf"
          target="_blank" rel="noopener">Trammel Guide</a>
      </div>
    </div>

    <div class="flex gap-2 flex-wrap">
      <button
        v-for="t in tabs" :key="t"
        class="px-3 py-1 rounded border transition-colors"
        :class="tab === t ? 'bg-blue-100 border-blue-500' : 'hover:bg-gray-50'"
        @click="tab = t"
      >{{ t }}</button>
    </div>

    <RadiusDishDesign
      v-if="tab === 'Design'"
      :selected-radius="selectedRadius"
      @update:selected-radius="selectedRadius = $event"
    />

    <RadiusDishCalculator v-else-if="tab === 'Calculator'" />

    <RadiusDishCncSetup
      v-else-if="tab === 'CNC Setup'"
      :selected-radius="selectedRadius"
      :ball-nose-mm="12.7"
      :stepover-mm="3.0"
      :feed-mm-min="2500"
      :spindle-rpm="18000"
      @download-gcode="downloadGcode"
    />

    <RadiusDishDocs v-else-if="tab === 'Docs'" />
  </div>
</template>

<script setup lang="ts">
/**
 * RadiusDishDesigner.vue — root component
 *
 * selectedRadius is now a number (feet, any value)
 * rather than the old '15ft' | '25ft' literal union.
 */
import { ref } from 'vue'
import {
  RadiusDishDesign,
  RadiusDishCalculator,
  RadiusDishCncSetup,
  RadiusDishDocs,
} from './radius-dish'
import { generateGcode, downloadBlob } from '@/api/radius-dish'

const tabs = ['Design', 'Calculator', 'CNC Setup', 'Docs']
const tab  = ref('Design')

const selectedRadius = ref<number>(20)   // feet — any value

async function downloadGcode() {
  try {
    const { blob, filename } = await generateGcode({ radius_ft: selectedRadius.value })
    downloadBlob(blob, filename)
  } catch (e: any) {
    console.error('G-code download failed:', e.message)
  }
}
</script>
