<template>
  <div class="bg-blue-50 rounded-lg p-4">
    <h3 class="text-lg font-semibold text-gray-900 mb-3">
      Telemetry Metrics
    </h3>
    <div class="grid grid-cols-2 gap-4">
      <div class="bg-white rounded p-3">
        <div class="text-sm text-gray-600">
          Average Spindle Load
        </div>
        <div class="text-2xl font-bold text-gray-900">
          {{ formatMetric(metrics.avg_spindle_load_pct, 1) }}%
        </div>
      </div>
      <div class="bg-white rounded p-3">
        <div class="text-sm text-gray-600">
          Max Spindle Load
        </div>
        <div class="text-2xl font-bold text-gray-900">
          {{ formatMetric(metrics.max_spindle_load_pct, 1) }}%
        </div>
      </div>
      <div class="bg-white rounded p-3">
        <div class="text-sm text-gray-600">
          Average RPM
        </div>
        <div class="text-2xl font-bold text-gray-900">
          {{ formatMetric(metrics.avg_rpm, 0) }}
        </div>
      </div>
      <div class="bg-white rounded p-3">
        <div class="text-sm text-gray-600">
          Max RPM
        </div>
        <div class="text-2xl font-bold text-gray-900">
          {{ formatMetric((metrics as any).max_rpm, 0) }}
        </div>
      </div>
      <div class="bg-white rounded p-3">
        <div class="text-sm text-gray-600">
          Average Feed Rate
        </div>
        <div class="text-2xl font-bold text-gray-900">
          {{ formatMetric(metrics.avg_feed_mm_min, 0) }} mm/min
        </div>
      </div>
      <div class="bg-white rounded p-3">
        <div class="text-sm text-gray-600">
          Vibration (RMS)
        </div>
        <div class="text-2xl font-bold text-gray-900">
          {{ formatMetric(metrics.avg_vibration_rms, 2) }} mm/s
        </div>
      </div>
    </div>
    <div class="mt-3 text-sm text-gray-600">
      📊 {{ metrics.n_samples }} telemetry samples recorded
    </div>
  </div>
</template>

<script setup lang="ts">
interface RunMetrics {
  avg_spindle_load_pct?: number
  max_spindle_load_pct?: number
  avg_rpm?: number
  max_rpm?: number
  avg_feed_mm_min?: number
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
