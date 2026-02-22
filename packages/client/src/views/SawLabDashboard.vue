<template>
  <div class="saw-lab-dashboard min-h-screen bg-gray-50 p-6">
    <!-- Header -->
    <div class="mb-6">
      <h1 class="text-3xl font-bold text-gray-900 mb-2">
        Saw Lab Dashboard
      </h1>
      <p class="text-gray-600">
        Real-time CNC monitoring with risk classification
      </p>
    </div>

    <!-- Summary Cards -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      <div class="bg-white rounded-lg shadow p-4 border-l-4 border-blue-500">
        <div class="text-sm text-gray-600 mb-1">
          Total Runs
        </div>
        <div class="text-2xl font-bold text-gray-900">
          {{ dashboardState.dashboard.value?.total_runs || 0 }}
        </div>
      </div>

      <div class="bg-white rounded-lg shadow p-4 border-l-4 border-green-500">
        <div class="text-sm text-gray-600 mb-1">
          Green (Safe)
        </div>
        <div class="text-2xl font-bold text-green-700">
          {{ filters.riskCounts.value.green }}
        </div>
      </div>

      <div class="bg-white rounded-lg shadow p-4 border-l-4 border-amber-500">
        <div class="text-sm text-gray-600 mb-1">
          Yellow + Orange
        </div>
        <div class="text-2xl font-bold text-amber-700">
          {{ filters.riskCounts.value.yellow + filters.riskCounts.value.orange }}
        </div>
      </div>

      <div class="bg-white rounded-lg shadow p-4 border-l-4 border-rose-500">
        <div class="text-sm text-gray-600 mb-1">
          Red (Danger)
        </div>
        <div class="text-2xl font-bold text-rose-700">
          {{ filters.riskCounts.value.red }}
        </div>
      </div>
    </div>

    <!-- Controls -->
    <div class="bg-white rounded-lg shadow p-4 mb-6">
      <div class="flex flex-wrap gap-4 items-center">
        <!-- Refresh Button -->
        <button
          :disabled="dashboardState.loading.value"
          class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          @click="dashboardState.loadDashboard"
        >
          <span v-if="dashboardState.loading.value">⏳ Loading...</span>
          <span v-else>🔄 Refresh</span>
        </button>

        <!-- Limit Selector -->
        <div class="flex items-center gap-2">
          <label class="text-sm text-gray-700">Show:</label>
          <select
            v-model="dashboardState.limit.value"
            class="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            @change="dashboardState.loadDashboard"
          >
            <option :value="10">10 runs</option>
            <option :value="25">25 runs</option>
            <option :value="50">50 runs</option>
            <option :value="100">100 runs</option>
          </select>
        </div>

        <!-- Risk Filter -->
        <div class="flex items-center gap-2">
          <label class="text-sm text-gray-700">Risk:</label>
          <select
            v-model="filters.riskFilter.value"
            class="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All</option>
            <option value="green">Green</option>
            <option value="yellow">Yellow</option>
            <option value="orange">Orange</option>
            <option value="red">Red</option>
            <option value="unknown">Unknown</option>
          </select>
        </div>

        <!-- Status Filter -->
        <div class="flex items-center gap-2">
          <label class="text-sm text-gray-700">Status:</label>
          <select
            v-model="filters.statusFilter.value"
            class="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All</option>
            <option value="pending">Pending</option>
            <option value="running">Running</option>
            <option value="completed">Completed</option>
            <option value="error">Error</option>
          </select>
        </div>

        <!-- Last Updated -->
        <div
          v-if="dashboardState.lastUpdated.value"
          class="ml-auto text-sm text-gray-500"
        >
          Updated: {{ formatTime(dashboardState.lastUpdated.value) }}
        </div>
      </div>
    </div>

    <!-- Error Message -->
    <div
      v-if="dashboardState.error.value"
      class="bg-rose-100 border border-rose-400 text-rose-700 px-4 py-3 rounded-lg mb-6"
    >
      <strong>Error:</strong> {{ dashboardState.error.value }}
    </div>

    <!-- Empty State -->
    <div
      v-if="!dashboardState.loading.value && filters.filteredRuns.value.length === 0"
      class="bg-white rounded-lg shadow p-12 text-center"
    >
      <div class="text-6xl mb-4">
        📊
      </div>
      <h3 class="text-xl font-semibold text-gray-900 mb-2">
        No Runs Found
      </h3>
      <p class="text-gray-600 mb-4">
        {{ dashboardState.dashboard.value?.runs.length === 0 ? 'No job runs in the system yet.' : 'No runs match your current filters.' }}
      </p>
      <button
        v-if="filters.riskFilter.value !== 'all' || filters.statusFilter.value !== 'all'"
        class="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
        @click="filters.clearFilters"
      >
        Clear Filters
      </button>
    </div>

    <!-- Run Cards Grid -->
    <div
      v-else
      class="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6"
    >
      <div
        v-for="run in filters.filteredRuns.value"
        :key="run.run_id"
        class="bg-white rounded-lg shadow hover:shadow-lg transition-shadow border-t-4"
        :class="riskBorderClass(run.risk_bucket.id)"
      >
        <!-- Card Header -->
        <div class="p-4 border-b border-gray-200">
          <div class="flex items-start justify-between mb-2">
            <div class="flex-1 min-w-0">
              <h3
                class="text-sm font-mono text-gray-600 truncate"
                :title="run.run_id"
              >
                {{ run.run_id }}
              </h3>
              <div class="text-xs text-gray-500 mt-1">
                {{ formatDateTime(run.created_at) }}
              </div>
            </div>

            <!-- Risk Badge -->
            <span
              class="px-3 py-1 rounded-full text-xs font-semibold ml-2 flex-shrink-0"
              :class="riskBadgeClass(run.risk_bucket.id)"
            >
              {{ run.risk_bucket.label }}
            </span>
          </div>

          <!-- Operation Info -->
          <div class="flex items-center gap-2 text-sm">
            <span class="px-2 py-0.5 bg-gray-100 rounded text-gray-700">
              {{ run.op_type }}
            </span>
            <span
              class="px-2 py-0.5 rounded text-xs"
              :class="statusBadgeClass(run.status)"
            >
              {{ run.status }}
            </span>
          </div>
        </div>

        <!-- Card Body -->
        <div class="p-4 space-y-3">
          <!-- Machine & Material -->
          <div class="text-sm space-y-1">
            <div class="flex items-center gap-2">
              <span class="text-gray-500 w-24">Machine:</span>
              <span class="font-medium text-gray-900">{{ run.machine_profile }}</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-gray-500 w-24">Material:</span>
              <span class="font-medium text-gray-900">{{ run.material_family }}</span>
            </div>
            <div
              v-if="run.blade_id"
              class="flex items-center gap-2"
            >
              <span class="text-gray-500 w-24">Blade:</span>
              <span class="font-medium text-gray-900">{{ run.blade_id }}</span>
            </div>
          </div>

          <!-- Risk Score -->
          <div class="pt-2 border-t border-gray-100">
            <div class="flex items-center justify-between mb-1">
              <span class="text-sm text-gray-600">Risk Score</span>
              <span
                class="text-lg font-bold"
                :class="riskScoreColor(run.risk_score)"
              >
                {{ run.risk_score.toFixed(2) }}
              </span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-2">
              <div
                class="h-2 rounded-full transition-all"
                :class="riskBarClass(run.risk_bucket.id)"
                :style="{ width: `${run.risk_score * 100}%` }"
              />
            </div>
            <div class="text-xs text-gray-500 mt-1">
              {{ run.risk_bucket.description }}
            </div>
          </div>

          <!-- Metrics (if telemetry available) -->
          <RunTelemetryCard
            v-if="run.has_telemetry && run.metrics"
            :metrics="run.metrics"
          />

          <!-- No Telemetry Message -->
          <div
            v-else
            class="pt-2 border-t border-gray-100 text-center"
          >
            <div class="text-sm text-gray-500 py-2">
              ℹ️ No telemetry data available
            </div>
          </div>
        </div>

        <!-- Card Footer -->
        <div class="p-3 bg-gray-50 border-t border-gray-200 flex gap-2">
          <button
            class="flex-1 px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
            @click="modals.openRunDetail(run)"
          >
            📊 View Details
          </button>
          <button
            v-if="run.has_telemetry && run.metrics"
            class="flex-1 px-3 py-1.5 text-sm bg-purple-600 text-white rounded hover:bg-purple-700 transition-colors"
            @click="modals.openRiskActions(run)"
          >
            ⚙️ Risk Actions
          </button>
        </div>
      </div>
    </div>

    <!-- Empty State (duplicate check) -->
    <div
      v-if="filters.filteredRuns.value.length === 0 && !dashboardState.loading.value"
      class="bg-white rounded-lg shadow p-12 text-center"
    >
      <div class="text-gray-400 text-6xl mb-4">
        🪚
      </div>
      <h3 class="text-xl font-semibold text-gray-900 mb-2">
        No Saw Runs Found
      </h3>
      <p class="text-gray-600">
        {{ dashboardState.error.value ? 'Error loading data. Try refreshing.' : 'No runs match your filters.' }}
      </p>
    </div>
  </div>

  <!-- Run Detail Modal -->
  <Teleport to="body">
    <div
      v-if="modals.selectedRun.value"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
      @click.self="modals.closeRunDetail"
    >
      <div class="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <!-- Modal Header -->
        <div class="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <div>
            <h2 class="text-2xl font-bold text-gray-900">
              Run Details
            </h2>
            <p class="text-sm text-gray-600">
              {{ modals.selectedRun.value.run_id }}
            </p>
          </div>
          <button
            class="text-gray-400 hover:text-gray-600 text-2xl font-bold"
            @click="modals.closeRunDetail"
          >
            ×
          </button>
        </div>

        <!-- Modal Body -->
        <div class="p-6 space-y-6">
          <!-- Run Info -->
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="text-sm font-semibold text-gray-600">Created At</label>
              <p class="text-gray-900">
                {{ formatDateTime(modals.selectedRun.value.created_at) }}
              </p>
            </div>
            <div>
              <label class="text-sm font-semibold text-gray-600">Status</label>
              <p>
                <span
                  class="px-2 py-1 rounded text-sm"
                  :class="statusBadgeClass(modals.selectedRun.value.status)"
                >
                  {{ modals.selectedRun.value.status }}
                </span>
              </p>
            </div>
            <div>
              <label class="text-sm font-semibold text-gray-600">Operation</label>
              <p class="text-gray-900">
                {{ modals.selectedRun.value.op_type }}
              </p>
            </div>
            <div>
              <label class="text-sm font-semibold text-gray-600">Machine</label>
              <p class="text-gray-900">
                {{ modals.selectedRun.value.machine_profile }}
              </p>
            </div>
            <div>
              <label class="text-sm font-semibold text-gray-600">Material</label>
              <p class="text-gray-900">
                {{ modals.selectedRun.value.material_family }}
              </p>
            </div>
            <div v-if="modals.selectedRun.value.blade_id">
              <label class="text-sm font-semibold text-gray-600">Blade</label>
              <p class="text-gray-900">
                {{ modals.selectedRun.value.blade_id }}
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
                  :class="riskBadgeClass(modals.selectedRun.value.risk_bucket.id)"
                >
                  {{ modals.selectedRun.value.risk_bucket.label }}
                </span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-gray-700">Risk Score</span>
                <span
                  class="text-lg font-bold"
                  :class="riskScoreColor(modals.selectedRun.value.risk_score)"
                >
                  {{ modals.selectedRun.value.risk_score.toFixed(3) }}
                </span>
              </div>
              <div class="w-full bg-gray-200 rounded-full h-3">
                <div
                  class="h-3 rounded-full transition-all"
                  :class="riskBarClass(modals.selectedRun.value.risk_bucket.id)"
                  :style="{ width: `${modals.selectedRun.value.risk_score * 100}%` }"
                />
              </div>
              <p class="text-sm text-gray-600 italic">
                {{ modals.selectedRun.value.risk_bucket.description }}
              </p>
            </div>
          </div>

          <!-- Telemetry Metrics -->
          <TelemetryMetricsPanel
            v-if="modals.selectedRun.value.has_telemetry && modals.selectedRun.value.metrics"
            :metrics="modals.selectedRun.value.metrics"
          />

          <!-- Lane Scale History -->
          <LaneScaleHistoryTable
            v-if="modals.selectedRun.value.lane_scale_history.length > 0"
            :history="modals.selectedRun.value.lane_scale_history"
          />
        </div>

        <!-- Modal Footer -->
        <div class="sticky bottom-0 bg-gray-50 border-t border-gray-200 px-6 py-4 flex justify-end gap-3">
          <button
            class="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300 transition-colors"
            @click="modals.closeRunDetail"
          >
            Close
          </button>
          <button
            v-if="modals.selectedRun.value.has_telemetry && modals.selectedRun.value.metrics"
            class="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 transition-colors"
            @click="modals.openRiskActions(modals.selectedRun.value)"
          >
            ⚙️ Risk Actions
          </button>
        </div>
      </div>
    </div>
  </Teleport>

  <!-- Risk Actions Modal -->
  <Teleport to="body">
    <div
      v-if="modals.riskActionsRun.value"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
      @click.self="handleCloseRiskActions"
    >
      <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <!-- Modal Header -->
        <div class="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <div>
            <h2 class="text-2xl font-bold text-gray-900">
              Risk Actions
            </h2>
            <p class="text-sm text-gray-600">
              {{ modals.riskActionsRun.value.run_id }}
            </p>
          </div>
          <button
            class="text-gray-400 hover:text-gray-600 text-2xl font-bold"
            @click="handleCloseRiskActions"
          >
            ×
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
                  :class="riskBadgeClass(modals.riskActionsRun.value.risk_bucket.id)"
                >
                  {{ modals.riskActionsRun.value.risk_bucket.label }}
                </span>
              </div>
              <div>
                <div class="text-sm text-gray-600">
                  Risk Score
                </div>
                <div
                  class="text-2xl font-bold mt-1"
                  :class="riskScoreColor(modals.riskActionsRun.value.risk_score)"
                >
                  {{ modals.riskActionsRun.value.risk_score.toFixed(3) }}
                </div>
              </div>
            </div>
          </div>

          <!-- Recommended Actions -->
          <div class="bg-blue-50 rounded-lg p-4">
            <h3 class="text-lg font-semibold text-gray-900 mb-3">
              💡 Recommended Actions
            </h3>
            <div class="space-y-3">
              <div
                v-for="(action, idx) in riskActions.computedActions.value"
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
                    @click="riskActions.applyOverride(action)"
                  >
                    Apply
                  </button>
                </div>
              </div>
              <div
                v-if="riskActions.computedActions.value.length === 0"
                class="text-center py-4 text-gray-500"
              >
                ✅ No actions required - operation within safe parameters
              </div>
            </div>
          </div>

          <!-- Override Confirmation -->
          <div
            v-if="riskActions.pendingOverride.value"
            class="bg-amber-50 border border-amber-300 rounded-lg p-4"
          >
            <h3 class="text-lg font-semibold text-amber-900 mb-2">
              ⚠️ Confirm Override
            </h3>
            <p class="text-sm text-amber-800 mb-3">
              Apply {{ riskActions.pendingOverride.value.suggested_override }} to future operations with similar conditions?
            </p>
            <div class="flex gap-3">
              <button
                class="flex-1 px-4 py-2 bg-amber-600 text-white rounded hover:bg-amber-700 transition-colors"
                @click="handleConfirmOverride"
              >
                ✓ Confirm
              </button>
              <button
                class="flex-1 px-4 py-2 bg-gray-300 text-gray-800 rounded hover:bg-gray-400 transition-colors"
                @click="riskActions.cancelOverride"
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
            @click="handleCloseRiskActions"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
/**
 * SawLabDashboard - Real-time CNC monitoring with risk classification.
 *
 * Features:
 * - Dashboard summary cards (total runs, risk breakdown)
 * - Filterable run list by risk level and status
 * - Run detail modal with telemetry metrics
 * - Risk actions modal with recommended adjustments
 */
import { onMounted } from 'vue'
import RunTelemetryCard from './saw_lab_dashboard/RunTelemetryCard.vue'
import TelemetryMetricsPanel from './saw_lab_dashboard/TelemetryMetricsPanel.vue'
import LaneScaleHistoryTable from './saw_lab_dashboard/LaneScaleHistoryTable.vue'
import {
  useSawDashboard,
  useSawDashboardFilters,
  useSawDashboardModals,
  useSawRiskActions,
  riskBorderClass,
  riskBadgeClass,
  riskBarClass,
  riskScoreColor,
  statusBadgeClass,
  formatDateTime,
  formatTime
} from './saw_lab_dashboard/composables'

// Initialize composables
const dashboardState = useSawDashboard()
const filters = useSawDashboardFilters(dashboardState.dashboard)
const modals = useSawDashboardModals()
const riskActions = useSawRiskActions(
  modals.riskActionsRun,
  (msg: string) => { dashboardState.error.value = msg }
)

// Event handlers that need coordination between composables
function handleCloseRiskActions(): void {
  modals.closeRiskActions()
  riskActions.cancelOverride()
}

async function handleConfirmOverride(): Promise<void> {
  if (modals.riskActionsRun.value) {
    await riskActions.confirmApplyOverride(
      modals.riskActionsRun.value,
      async () => {
        await dashboardState.loadDashboard()
        handleCloseRiskActions()
      }
    )
  }
}

// Load on mount
onMounted(() => {
  dashboardState.loadDashboard()
})
</script>

<style scoped>
.saw-lab-dashboard {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}
</style>
