<script setup lang="ts">
/**
 * InlayDetailsTable - Individual inlay positions table
 * Extracted from ArtStudioInlay.vue
 */

interface Inlay {
  fret: number
  center_x_mm: number
  center_y_mm: number
  is_double: boolean
}

defineProps<{
  inlays: Inlay[]
}>()
</script>

<template>
  <div class="bg-white border rounded-lg p-4 max-h-[300px] overflow-y-auto">
    <h3 class="font-semibold text-gray-800 mb-3">
      Inlay Details
    </h3>

    <table class="w-full text-xs">
      <thead class="bg-gray-50 sticky top-0">
        <tr>
          <th class="py-1 px-2 text-left">
            Fret
          </th>
          <th class="py-1 px-2 text-right">
            X (mm)
          </th>
          <th class="py-1 px-2 text-right">
            Y (mm)
          </th>
          <th class="py-1 px-2 text-center">
            Double
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="(inlay, idx) in inlays"
          :key="idx"
          class="border-b"
        >
          <td class="py-1 px-2">
            {{ inlay.fret }}
          </td>
          <td class="py-1 px-2 text-right font-mono">
            {{ inlay.center_x_mm.toFixed(2) }}
          </td>
          <td class="py-1 px-2 text-right font-mono">
            {{ inlay.center_y_mm.toFixed(2) }}
          </td>
          <td class="py-1 px-2 text-center">
            {{ inlay.is_double ? "●●" : "●" }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
