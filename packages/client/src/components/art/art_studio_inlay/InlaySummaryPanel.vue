<script setup lang="ts">
/**
 * InlaySummaryPanel - Inlay generation summary
 * Extracted from ArtStudioInlay.vue
 */

interface InlayResult {
  inlays: unknown[]
  scale_length_mm: number
  num_frets: number
}

defineProps<{
  result: InlayResult
  patternType: string
}>()
</script>

<template>
  <div class="bg-white border rounded-lg p-4">
    <h3 class="font-semibold text-gray-800 mb-3">
      Inlay Summary
    </h3>

    <div class="grid grid-cols-2 gap-4 text-sm">
      <div>
        <span class="text-gray-600">Total Inlays:</span>
        <span class="ml-2 font-bold">{{ result.inlays.length }}</span>
      </div>
      <div>
        <span class="text-gray-600">Pattern:</span>
        <span class="ml-2 font-bold capitalize">{{ patternType }}</span>
      </div>
      <div>
        <span class="text-gray-600">Scale Length:</span>
        <span class="ml-2 font-mono">{{ result.scale_length_mm.toFixed(1) }} mm</span>
      </div>
      <div>
        <span class="text-gray-600">Frets:</span>
        <span class="ml-2">{{ result.num_frets }}</span>
      </div>
    </div>
  </div>
</template>
