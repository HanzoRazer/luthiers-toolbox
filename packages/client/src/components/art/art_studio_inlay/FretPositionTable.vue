<script setup lang="ts">
/**
 * FretPositionTable - Fret positions table (12-TET)
 * Extracted from ArtStudioInlay.vue
 */

interface FretPosition {
  fret: number
  position_mm: number
  distance_from_previous_mm: number
}

interface FretData {
  positions: FretPosition[]
}

defineProps<{
  fretData: FretData
  selectedFrets: number[]
}>()
</script>

<template>
  <div class="bg-white border rounded-lg p-4 max-h-[400px] overflow-y-auto">
    <h3 class="font-semibold text-gray-800 mb-3">
      Fret Positions (12-TET)
    </h3>

    <table class="w-full text-xs">
      <thead class="bg-gray-50 sticky top-0">
        <tr>
          <th class="py-1 px-2 text-left">
            Fret
          </th>
          <th class="py-1 px-2 text-right">
            Position
          </th>
          <th class="py-1 px-2 text-right">
            Spacing
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="pos in fretData.positions"
          :key="pos.fret"
          class="border-b"
          :class="selectedFrets.includes(pos.fret) ? 'bg-blue-50' : ''"
        >
          <td class="py-1 px-2">
            {{ pos.fret }}
          </td>
          <td class="py-1 px-2 text-right font-mono">
            {{ pos.position_mm.toFixed(2) }}
          </td>
          <td class="py-1 px-2 text-right font-mono text-gray-500">
            {{ pos.distance_from_previous_mm.toFixed(2) }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
