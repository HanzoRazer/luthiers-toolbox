<template>
  <div class="text-xs border rounded p-3 space-y-1">
    <h2 class="font-bold text-sm mb-2">
      Relief Sim Bridge Results (Risk: {{ simBridgeOut.risk_score.toFixed(2) }})
    </h2>
    <div class="grid grid-cols-2 gap-x-4 gap-y-1">
      <div>
        <span class="text-gray-500">Floor:</span>
        avg {{ simBridgeOut.stats.avg_floor_thickness.toFixed(2) }} mm,
        min {{ simBridgeOut.stats.min_floor_thickness.toFixed(2) }} mm
      </div>
      <div>
        <span class="text-gray-500">Load:</span>
        max {{ simBridgeOut.stats.max_load_index.toFixed(2) }},
        avg {{ simBridgeOut.stats.avg_load_index.toFixed(2) }}
      </div>
      <div>
        <span class="text-gray-500">Removed:</span>
        {{ simBridgeOut.stats.total_removed_volume.toFixed(1) }} mm³
      </div>
      <div>
        <span class="text-gray-500">Grid cells:</span>
        {{ simBridgeOut.stats.cell_count }}
      </div>
      <div class="col-span-2">
        <span class="text-gray-500">Issues:</span>
        {{ simBridgeOut.issues.length }} (thin floors + high loads)
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface SimBridgeStats {
  avg_floor_thickness: number
  min_floor_thickness: number
  max_load_index: number
  avg_load_index: number
  total_removed_volume: number
  cell_count: number
}

interface SimBridgeIssue {
  type: string
  severity: string
  x: number
  y: number
  z?: number
  extra_time_s?: number
  note?: string
  meta?: Record<string, any>
}

interface SimBridgeOutput {
  issues: SimBridgeIssue[]
  stats: SimBridgeStats
  risk_score: number
  meta?: Record<string, any>
}

defineProps<{
  simBridgeOut: SimBridgeOutput
}>()
</script>
