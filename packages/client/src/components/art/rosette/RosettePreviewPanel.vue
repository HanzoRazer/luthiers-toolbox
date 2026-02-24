<script setup lang="ts">
/**
 * RosettePreviewPanel.vue
 * Right panel for rosette preview and results display.
 */
import type { RosettePreviewResponse } from '@/api/art-studio'

defineProps<{
  previewResult: RosettePreviewResponse | null
}>()
</script>

<template>
  <div class="space-y-4">
    <!-- SVG Preview -->
    <div class="bg-white border rounded-lg p-4">
      <h3 class="font-semibold text-gray-800 mb-3">
        Preview
      </h3>

      <div
        v-if="previewResult?.preview_svg"
        class="bg-gray-100 rounded p-4 flex items-center justify-center min-h-[300px]"
        v-html="previewResult.preview_svg"
      />
      <div
        v-else
        class="bg-gray-100 rounded p-4 flex items-center justify-center min-h-[300px] text-gray-400"
      >
        Click Preview to generate
      </div>
    </div>

    <!-- Results Table -->
    <div
      v-if="previewResult"
      class="bg-white border rounded-lg p-4"
    >
      <h3 class="font-semibold text-gray-800 mb-3">
        Channel Dimensions
      </h3>

      <table class="w-full text-sm">
        <tbody>
          <tr class="border-b">
            <td class="py-2 text-gray-600">
              Soundhole Radius
            </td>
            <td class="py-2 text-right font-mono">
              {{ previewResult.result.soundhole_radius_mm.toFixed(2) }} mm
            </td>
          </tr>
          <tr class="border-b">
            <td class="py-2 text-gray-600">
              Channel Inner Radius
            </td>
            <td class="py-2 text-right font-mono">
              {{ previewResult.result.channel_inner_radius_mm.toFixed(2) }} mm
            </td>
          </tr>
          <tr class="border-b">
            <td class="py-2 text-gray-600">
              Channel Outer Radius
            </td>
            <td class="py-2 text-right font-mono">
              {{ previewResult.result.channel_outer_radius_mm.toFixed(2) }} mm
            </td>
          </tr>
          <tr class="border-b">
            <td class="py-2 text-gray-600">
              Channel Width
            </td>
            <td class="py-2 text-right font-mono font-bold">
              {{ previewResult.result.channel_width_mm.toFixed(2) }} mm
            </td>
          </tr>
          <tr>
            <td class="py-2 text-gray-600">
              Channel Depth
            </td>
            <td class="py-2 text-right font-mono">
              {{ previewResult.result.channel_depth_mm.toFixed(2) }} mm
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Stack Breakdown -->
    <div
      v-if="previewResult?.result.stack?.length"
      class="bg-white border rounded-lg p-4"
    >
      <h3 class="font-semibold text-gray-800 mb-3">
        Stack Breakdown
      </h3>

      <div class="space-y-2">
        <div
          v-for="(item, idx) in previewResult.result.stack"
          :key="idx"
          class="flex justify-between items-center py-1 px-2 rounded"
          :class="item.label.includes('Central') ? 'bg-amber-50' : 'bg-gray-50'"
        >
          <span class="text-sm">{{ item.label }}</span>
          <span class="text-xs font-mono text-gray-600">
            {{ item.width_mm.toFixed(1) }} mm
            ({{ item.inner_radius_mm.toFixed(1) }} → {{ item.outer_radius_mm.toFixed(1) }})
          </span>
        </div>
      </div>
    </div>
  </div>
</template>
