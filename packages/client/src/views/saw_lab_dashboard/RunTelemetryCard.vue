<template>
  <div class="pt-2 border-t border-gray-100">
    <div class="text-xs text-gray-600 mb-2 font-semibold">
      Telemetry Metrics
    </div>
    <div class="grid grid-cols-2 gap-2 text-xs">
      <div class="bg-gray-50 rounded p-2">
        <div class="text-gray-500">
          Avg Load
        </div>
        <div class="font-semibold text-gray-900">
          {{ formatMetric(metrics.avg_spindle_load_pct, 1) }}%
        </div>
      </div>
      <div class="bg-gray-50 rounded p-2">
        <div class="text-gray-500">
          Max Load
        </div>
        <div class="font-semibold text-gray-900">
          {{ formatMetric(metrics.max_spindle_load_pct, 1) }}%
        </div>
      </div>
      <div class="bg-gray-50 rounded p-2">
        <div class="text-gray-500">
          Avg RPM
        </div>
        <div class="font-semibold text-gray-900">
          {{ formatMetric(metrics.avg_rpm, 0) }}
        </div>
      </div>
      <div class="bg-gray-50 rounded p-2">
        <div class="text-gray-500">
          Vibration
        </div>
        <div class="font-semibold text-gray-900">
          {{ formatMetric(metrics.avg_vibration_rms, 2) }} mm/s
        </div>
      </div>
    </div>
    <div class="text-xs text-gray-500 mt-1">
      {{ metrics.n_samples }} samples
    </div>
  </div>
</template>

<script setup lang="ts">
interface RunMetrics {
  avg_spindle_load_pct?: number
  max_spindle_load_pct?: number
  avg_rpm?: number
  avg_vibration_rms?: number
  n_samples: number
}

defineProps<{
  metrics: RunMetrics
}>()

function formatMetric(value: number | undefined, decimals: number): string {
  if (value == null) return 'N/A'
  return value.toFixed(decimals)
}
</script>
