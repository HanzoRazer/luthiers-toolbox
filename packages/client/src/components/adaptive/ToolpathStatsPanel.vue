<script setup lang="ts">
/**
 * ToolpathStatsPanel - Toolpath statistics display
 * Extracted from AdaptivePocketLab.vue
 */

interface ToolpathStats {
  length_mm: number
  area_mm2: number
  time_s_classic: number
  time_s_jerk: number | null
  move_count: number
  volume_mm3: number
  tight_segments?: number
  trochoid_arcs?: number
}

defineProps<{
  stats: ToolpathStats | null
}>()
</script>

<template>
  <div
    v-if="stats"
    class="stats-panel text-sm mt-2 p-2 bg-slate-100 rounded"
  >
    <div class="grid grid-cols-2 gap-2">
      <div><b>Length:</b> {{ stats.length_mm }} mm</div>
      <div><b>Area:</b> {{ stats.area_mm2 }} mm²</div>
      <div>
        <b>Time (Classic):</b>
        {{ stats.time_s_classic }} s ({{ (stats.time_s_classic / 60).toFixed(1) }} min)
      </div>
      <div v-if="stats.time_s_jerk !== null">
        <b>Time (Jerk):</b>
        {{ stats.time_s_jerk }} s ({{ (stats.time_s_jerk / 60).toFixed(1) }} min)
      </div>
      <div><b>Moves:</b> {{ stats.move_count }}</div>
      <div><b>Volume:</b> {{ stats.volume_mm3 }} mm³</div>
      <div><b>Tight Segments:</b> {{ stats.tight_segments || 0 }}</div>
      <div><b>Trochoid Arcs:</b> {{ stats.trochoid_arcs || 0 }}</div>
    </div>

    <div class="mt-2 flex items-center gap-3 text-xs text-gray-600">
      <span class="flex items-center gap-1">
        <span
          class="inline-block w-3 h-3 rounded"
          style="background: #0ea5e9"
        />
        Normal speed
      </span>
      <span class="flex items-center gap-1">
        <span
          class="inline-block w-3 h-3 rounded"
          style="background: #f59e0b"
        />
        Moderate slowdown
      </span>
      <span class="flex items-center gap-1">
        <span
          class="inline-block w-3 h-3 rounded"
          style="background: #ef4444"
        />
        Heavy slowdown
      </span>
      <span class="ml-4 flex items-center gap-1">
        <span
          class="inline-block w-3 h-3 rounded"
          style="background: #7c3aed"
        />
        Trochoid arcs
      </span>
    </div>
  </div>
</template>
