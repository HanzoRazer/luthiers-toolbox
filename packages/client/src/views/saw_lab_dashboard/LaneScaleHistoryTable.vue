<template>
  <div class="bg-purple-50 rounded-lg p-4">
    <h3 class="text-lg font-semibold text-gray-900 mb-3">
      Lane Scale History
    </h3>
    <div class="overflow-x-auto">
      <table class="min-w-full divide-y divide-gray-300">
        <thead>
          <tr class="bg-white">
            <th class="px-3 py-2 text-left text-xs font-semibold text-gray-900">
              Timestamp
            </th>
            <th class="px-3 py-2 text-left text-xs font-semibold text-gray-900">
              Scale
            </th>
            <th class="px-3 py-2 text-left text-xs font-semibold text-gray-900">
              Source
            </th>
            <th class="px-3 py-2 text-left text-xs font-semibold text-gray-900">
              Reason
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200 bg-white">
          <tr
            v-for="(hist, idx) in history"
            :key="idx"
          >
            <td class="px-3 py-2 text-sm text-gray-900">
              {{ formatDateTime((hist as any).timestamp || hist.ts) }}
            </td>
            <td class="px-3 py-2 text-sm font-semibold text-gray-900">
              {{ hist.lane_scale.toFixed(2) }}
            </td>
            <td class="px-3 py-2 text-sm text-gray-600">
              {{ hist.source || 'N/A' }}
            </td>
            <td class="px-3 py-2 text-sm text-gray-600">
              {{ (hist as any).meta?.reason || 'N/A' }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
interface LaneScaleHistoryItem {
  timestamp?: string
  ts?: string
  lane_scale: number
  source?: string
  meta?: { reason?: string }
}

defineProps<{
  history: LaneScaleHistoryItem[]
}>()

function formatDateTime(isoString: string): string {
  const date = new Date(isoString)
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>
