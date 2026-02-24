<script setup lang="ts">
/**
 * ArtStudioRosette.vue
 *
 * Interactive rosette channel calculator for classical guitars.
 * Orchestrates child panels for parameters and preview.
 */
import { ref, watch, onMounted } from 'vue'
import {
  previewRosette,
  exportRosetteDXF,
  listRosettePresets,
  getRosettePreset,
  downloadBlob,
  type RosettePreviewResponse,
  type RosettePresetInfo,
  type PurflingBand,
} from '@/api/art-studio'
import { RosetteParametersPanel, RosettePreviewPanel } from './rosette'

// State
const loading = ref(false)
const error = ref<string | null>(null)
const previewResult = ref<RosettePreviewResponse | null>(null)
const presets = ref<RosettePresetInfo[]>([])
const selectedPreset = ref<string | null>(null)

// Form inputs
const soundholeDiameter = ref(100.0)
const centralBand = ref(3.0)
const channelDepth = ref(1.5)
const centerX = ref(0.0)
const centerY = ref(0.0)
const includePurflingRings = ref(true)

// Purfling configuration
const innerPurfling = ref<PurflingBand[]>([{ material: 'bwb', width_mm: 1.5 }])
const outerPurfling = ref<PurflingBand[]>([{ material: 'bwb', width_mm: 1.5 }])

// Methods
async function loadPresets() {
  try {
    presets.value = await listRosettePresets()
  } catch (e: unknown) {
    console.warn('Failed to load presets:', e)
  }
}

async function applyPreset() {
  if (!selectedPreset.value) return
  try {
    const preset = await getRosettePreset(selectedPreset.value)
    soundholeDiameter.value = preset.soundhole_diameter_mm
    centralBand.value = preset.central_band_mm
    channelDepth.value = preset.channel_depth_mm
    innerPurfling.value = [...preset.inner_purfling]
    outerPurfling.value = [...preset.outer_purfling]
    await refreshPreview()
  } catch (e: unknown) {
    error.value = `Failed to load preset: ${(e as Error).message}`
  }
}

async function refreshPreview() {
  loading.value = true
  error.value = null
  try {
    previewResult.value = await previewRosette({
      soundhole_diameter_mm: soundholeDiameter.value,
      central_band_mm: centralBand.value,
      inner_purfling: innerPurfling.value,
      outer_purfling: outerPurfling.value,
      channel_depth_mm: channelDepth.value,
    })
  } catch (e: unknown) {
    error.value = (e as Error).message || 'Preview failed'
  } finally {
    loading.value = false
  }
}

async function exportDXF() {
  loading.value = true
  error.value = null
  try {
    const blob = await exportRosetteDXF({
      soundhole_diameter_mm: soundholeDiameter.value,
      central_band_mm: centralBand.value,
      inner_purfling: innerPurfling.value,
      outer_purfling: outerPurfling.value,
      channel_depth_mm: channelDepth.value,
      center_x_mm: centerX.value,
      center_y_mm: centerY.value,
      include_purfling_rings: includePurflingRings.value,
    })
    downloadBlob(blob, `rosette_${soundholeDiameter.value}mm.dxf`)
  } catch (e: unknown) {
    error.value = (e as Error).message || 'Export failed'
  } finally {
    loading.value = false
  }
}

function addPurflingBand(side: 'inner' | 'outer') {
  const band: PurflingBand = { material: 'bwb', width_mm: 1.5 }
  if (side === 'inner') {
    innerPurfling.value.push(band)
  } else {
    outerPurfling.value.push(band)
  }
}

function removePurflingBand(side: 'inner' | 'outer', index: number) {
  if (side === 'inner') {
    innerPurfling.value.splice(index, 1)
  } else {
    outerPurfling.value.splice(index, 1)
  }
}

function updatePurflingBand(side: 'inner' | 'outer', index: number, band: PurflingBand) {
  if (side === 'inner') {
    innerPurfling.value[index] = band
  } else {
    outerPurfling.value[index] = band
  }
}

// Auto-preview on significant changes
watch([soundholeDiameter, centralBand, channelDepth], () => refreshPreview(), {
  debounce: 300,
} as any)

onMounted(() => {
  loadPresets()
  refreshPreview()
})
</script>

<template>
  <div class="p-4 max-w-5xl mx-auto">
    <h1 class="text-2xl font-bold mb-4 flex items-center gap-2">
      <span class="text-3xl">🎸</span>
      Rosette Channel Calculator
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

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Left Panel: Parameters -->
      <RosetteParametersPanel
        v-model:selected-preset="selectedPreset"
        v-model:soundhole-diameter="soundholeDiameter"
        v-model:central-band="centralBand"
        v-model:channel-depth="channelDepth"
        v-model:center-x="centerX"
        v-model:center-y="centerY"
        v-model:include-purfling-rings="includePurflingRings"
        :presets="presets"
        :inner-purfling="innerPurfling"
        :outer-purfling="outerPurfling"
        :loading="loading"
        :has-preview="!!previewResult"
        @apply-preset="applyPreset"
        @add-purfling-band="addPurflingBand"
        @remove-purfling-band="removePurflingBand"
        @update-purfling-band="updatePurflingBand"
        @refresh-preview="refreshPreview"
        @export-d-x-f="exportDXF"
      />

      <!-- Right Panel: Preview -->
      <RosettePreviewPanel :preview-result="previewResult" />
    </div>
  </div>
</template>
