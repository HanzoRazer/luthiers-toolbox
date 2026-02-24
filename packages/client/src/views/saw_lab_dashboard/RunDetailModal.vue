<template>
  <Teleport to="body">
    <div
      v-if="run"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
      @click.self="$emit('close')"
    >
      <div class="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <!-- Modal Header -->
        <div class="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <div>
            <h2 class="text-2xl font-bold text-gray-900">
              Run Details
            </h2>
            <p class="text-sm text-gray-600">
              {{ run.run_id }}
            </p>
          </div>
          <button
            class="text-gray-400 hover:text-gray-600 text-2xl font-bold"
            @click="$emit('close')"
          >
            &times;
          </button>
        </div>

        <!-- Modal Body -->
        <div class="p-6 space-y-6">
          <!-- Run Info -->
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="text-sm font-semibold text-gray-600">Created At</label>
              <p class="text-gray-900">
                {{ formatDateTime(run.created_at) }}
              </p>
            </div>
            <div>
              <label class="text-sm font-semibold text-gray-600">Status</label>
              <p>
                <span
                  class="px-2 py-1 rounded text-sm"
                  :class="statusBadgeClass(run.status)"
                >
                  {{ run.status }}
                </span>
              </p>
            </div>
            <div>
              <label class="text-sm font-semibold text-gray-600">Operation</label>
              <p class="text-gray-900">
                {{ run.op_type }}
              </p>
            </div>
            <div>
              <label class="text-sm font-semibold text-gray-600">Machine</label>
              <p class="text-gray-900">
                {{ run.machine_profile }}
              </p>
            </div>
            <div>
              <label class="text-sm font-semibold text-gray-600">Material</label>
              <p class="text-gray-900">
                {{ run.material_family }}
              </p>
            </div>
            <div v-if="run.blade_id">
              <label class="text-sm font-semibold text-gray-600">Blade</label>
              <p class="text-gray-900">
                {{ run.blade_id }}
              </p>
            </div>
          </div>

          <!-- Risk Assessment -->
          <div class="bg-gray-50 rounded-lg p-4">
            <h3 class="text-lg font-semibold text-gray-900 mb-3">
              Risk Assessment
            </h3>
            <div class="space-y-3">
              <div class="flex items-center justify-between">
                <span class="text-gray-700">Risk Level</span>
                <span
                  class="px-3 py-1 rounded-full text-sm font-semibold"
                  :class="riskBadgeClass(run.risk_bucket.id)"
                >
                  {{ run.risk_bucket.label }}
                </span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-gray-700">Risk Score</span>
                <span
                  class="text-lg font-bold"
                  :class="riskScoreColor(run.risk_score)"
                >
                  {{ run.risk_score.toFixed(3) }}
                </span>
              </div>
              <div class="w-full bg-gray-200 rounded-full h-3">
                <div
                  class="h-3 rounded-full transition-all"
                  :class="riskBarClass(run.risk_bucket.id)"
                  :style="{ width: `${run.risk_score * 100}%` }"
                />
              </div>
              <p class="text-sm text-gray-600 italic">
                {{ run.risk_bucket.description }}
              </p>
            </div>
          </div>

          <!-- Telemetry Metrics -->
          <TelemetryMetricsPanel
            v-if="run.has_telemetry && run.metrics"
            :metrics="run.metrics"
          />

          <!-- Lane Scale History -->
          <LaneScaleHistoryTable
            v-if="run.lane_scale_history.length > 0"
            :history="run.lane_scale_history"
          />
        </div>

        <!-- Modal Footer -->
        <div class="sticky bottom-0 bg-gray-50 border-t border-gray-200 px-6 py-4 flex justify-end gap-3">
          <button
            class="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300 transition-colors"
            @click="$emit('close')"
          >
            Close
          </button>
          <button
            v-if="run.has_telemetry && run.metrics"
            class="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 transition-colors"
            @click="$emit('openRiskActions', run)"
          >
            Risk Actions
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import TelemetryMetricsPanel, { type RunMetrics } from './TelemetryMetricsPanel.vue'
import LaneScaleHistoryTable, { type LaneScaleHistoryItem } from './LaneScaleHistoryTable.vue'
import {
  riskBadgeClass,
  riskBarClass,
  riskScoreColor,
  statusBadgeClass,
  formatDateTime
} from './composables'

defineProps<{
  run: {
    run_id: string
    created_at: string
    status: string
    op_type: string
    machine_profile: string
    material_family: string
    blade_id?: string
    risk_bucket: { id: string; label: string; description: string }
    risk_score: number
    has_telemetry: boolean
    metrics?: RunMetrics
    lane_scale_history: LaneScaleHistoryItem[]
  } | null
}>()

defineEmits<{
  (e: 'close'): void
  (e: 'openRiskActions', run: any): void
}>()
</script>
