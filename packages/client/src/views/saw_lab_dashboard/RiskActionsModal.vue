<template>
  <Teleport to="body">
    <div
      v-if="run"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
      @click.self="$emit('close')"
    >
      <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <!-- Modal Header -->
        <div class="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <div>
            <h2 class="text-2xl font-bold text-gray-900">
              Risk Actions
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
          <!-- Current Status -->
          <div class="bg-gray-50 rounded-lg p-4">
            <h3 class="text-lg font-semibold text-gray-900 mb-3">
              Current Status
            </h3>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <div class="text-sm text-gray-600">
                  Risk Level
                </div>
                <span
                  class="inline-block px-3 py-1 rounded-full text-sm font-semibold mt-1"
                  :class="riskBadgeClass(run.risk_bucket.id)"
                >
                  {{ run.risk_bucket.label }}
                </span>
              </div>
              <div>
                <div class="text-sm text-gray-600">
                  Risk Score
                </div>
                <div
                  class="text-2xl font-bold mt-1"
                  :class="riskScoreColor(run.risk_score)"
                >
                  {{ run.risk_score.toFixed(3) }}
                </div>
              </div>
            </div>
          </div>

          <!-- Recommended Actions -->
          <div class="bg-blue-50 rounded-lg p-4">
            <h3 class="text-lg font-semibold text-gray-900 mb-3">
              Recommended Actions
            </h3>
            <div class="space-y-3">
              <div
                v-for="(action, idx) in computedActions"
                :key="idx"
                class="bg-white rounded-lg p-4 border-l-4"
                :class="action.severity === 'critical' ? 'border-rose-500' : action.severity === 'warning' ? 'border-amber-500' : 'border-blue-500'"
              >
                <div class="flex items-start justify-between">
                  <div class="flex-1">
                    <div class="font-semibold text-gray-900 mb-1">
                      {{ action.title }}
                    </div>
                    <p class="text-sm text-gray-600 mb-2">
                      {{ action.description }}
                    </p>
                    <div
                      v-if="action.suggested_override"
                      class="text-xs font-mono bg-gray-100 px-2 py-1 rounded"
                    >
                      Suggested: {{ action.suggested_override }}
                    </div>
                  </div>
                  <button
                    v-if="action.action_type === 'apply_override'"
                    class="ml-3 px-3 py-1 text-sm bg-purple-600 text-white rounded hover:bg-purple-700 transition-colors"
                    @click="$emit('applyOverride', action)"
                  >
                    Apply
                  </button>
                </div>
              </div>
              <div
                v-if="computedActions.length === 0"
                class="text-center py-4 text-gray-500"
              >
                No actions required - operation within safe parameters
              </div>
            </div>
          </div>

          <!-- Override Confirmation -->
          <div
            v-if="pendingOverride"
            class="bg-amber-50 border border-amber-300 rounded-lg p-4"
          >
            <h3 class="text-lg font-semibold text-amber-900 mb-2">
              Confirm Override
            </h3>
            <p class="text-sm text-amber-800 mb-3">
              Apply {{ pendingOverride.suggested_override }} to future operations with similar conditions?
            </p>
            <div class="flex gap-3">
              <button
                class="flex-1 px-4 py-2 bg-amber-600 text-white rounded hover:bg-amber-700 transition-colors"
                @click="$emit('confirmOverride')"
              >
                Confirm
              </button>
              <button
                class="flex-1 px-4 py-2 bg-gray-300 text-gray-800 rounded hover:bg-gray-400 transition-colors"
                @click="$emit('cancelOverride')"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>

        <!-- Modal Footer -->
        <div class="sticky bottom-0 bg-gray-50 border-t border-gray-200 px-6 py-4 flex justify-end">
          <button
            class="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300 transition-colors"
            @click="$emit('close')"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { riskBadgeClass, riskScoreColor, type RiskAction, type PendingOverride } from './composables'

defineProps<{
  run: {
    run_id: string
    risk_bucket: { id: string; label: string }
    risk_score: number
  } | null
  computedActions: RiskAction[]
  pendingOverride: PendingOverride | null
}>()

defineEmits<{
  (e: 'close'): void
  (e: 'applyOverride', action: RiskAction): void
  (e: 'confirmOverride'): void
  (e: 'cancelOverride'): void
}>()
</script>
