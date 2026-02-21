<template>
  <section class="border rounded p-4 bg-white space-y-4">
    <h2 class="font-semibold text-lg">
      Kernel Output
    </h2>
    <div class="grid gap-4 md:grid-cols-2 text-xs">
      <div class="space-y-1">
        <h3 class="font-semibold text-sm">
          Stats
        </h3>
        <p v-if="result.stats.length_mm != null">
          <b>Length:</b> {{ formatStat(result.stats.length_mm) }} mm
        </p>
        <p v-if="result.stats.area_mm2 != null">
          <b>Area:</b> {{ formatStat(result.stats.area_mm2) }} mm²
        </p>
        <p v-if="result.stats.time_s != null">
          <b>Time:</b> {{ formatStat(result.stats.time_s) }} s
        </p>
        <p v-if="result.stats.time_jerk_s != null">
          <b>Time (jerk-aware):</b> {{ formatStat(result.stats.time_jerk_s) }} s
        </p>
        <p v-if="result.stats.volume_mm3 != null">
          <b>Volume:</b> {{ formatStat(result.stats.volume_mm3) }} mm³
        </p>
        <p v-if="result.stats.move_count != null">
          <b>Moves:</b> {{ result.stats.move_count }}
        </p>
        <p v-if="result.stats.tight_count != null">
          <b>Tight segments:</b> {{ result.stats.tight_count }}
        </p>
        <p v-if="result.stats.trochoid_count != null">
          <b>Trochoid arcs:</b> {{ result.stats.trochoid_count }}
        </p>
      </div>
      <div>
        <details>
          <summary class="cursor-pointer text-sm font-semibold">
            Raw Output JSON
          </summary>
          <pre class="bg-gray-50 p-2 rounded mt-2 whitespace-pre-wrap text-[10px]">{{ JSON.stringify(result, null, 2) }}</pre>
        </details>
        <details v-if="lastRequest">
          <summary class="cursor-pointer text-sm font-semibold mt-2">
            Last Request JSON
          </summary>
          <pre class="bg-gray-50 p-2 rounded mt-2 whitespace-pre-wrap text-[10px]">{{ JSON.stringify(lastRequest, null, 2) }}</pre>
        </details>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
interface AdaptiveStats {
  length_mm?: number
  area_mm2?: number
  time_s?: number
  time_jerk_s?: number
  volume_mm3?: number
  move_count?: number
  tight_count?: number
  trochoid_count?: number
}

interface AdaptivePlanOut {
  stats: AdaptiveStats
  moves?: unknown[]
  overlays?: unknown[]
}

defineProps<{
  result: AdaptivePlanOut
  lastRequest: unknown | null
}>()

function formatStat(value: number | undefined): string {
  if (value == null) return ''
  return typeof value.toFixed === 'function' ? value.toFixed(1) : String(value)
}
</script>
