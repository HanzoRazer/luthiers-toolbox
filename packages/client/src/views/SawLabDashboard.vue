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
    <SummaryCards
      :total-runs="dashboardState.dashboard.value?.total_runs || 0"
      :risk-counts="filters.riskCounts.value"
    />

    <!-- Controls -->
    <DashboardControls
      :loading="dashboardState.loading.value"
      :limit="dashboardState.limit.value"
      :risk-filter="filters.riskFilter.value"
      :status-filter="filters.statusFilter.value"
      :last-updated="dashboardState.lastUpdated.value ? formatTime(dashboardState.lastUpdated.value) : null"
      @refresh="handleRefresh"
      @update:limit="handleLimitChange"
      @update:risk-filter="filters.riskFilter.value = $event"
      @update:status-filter="filters.statusFilter.value = $event"
    />

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
  <RunDetailModal
    :run="modals.selectedRun.value"
    @close="modals.closeRunDetail"
    @open-risk-actions="modals.openRiskActions"
  />

  <!-- Risk Actions Modal -->
  <RiskActionsModal
    :run="modals.riskActionsRun.value"
    :computed-actions="riskActions.computedActions.value"
    :pending-override="riskActions.pendingOverride.value"
    @close="handleCloseRiskActions"
    @apply-override="riskActions.applyOverride"
    @confirm-override="handleConfirmOverride"
    @cancel-override="riskActions.cancelOverride"
  />
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
import SummaryCards from './saw_lab_dashboard/SummaryCards.vue'
import DashboardControls from './saw_lab_dashboard/DashboardControls.vue'
import RunDetailModal from './saw_lab_dashboard/RunDetailModal.vue'
import RiskActionsModal from './saw_lab_dashboard/RiskActionsModal.vue'
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

// Event handlers for DashboardControls
function handleRefresh(): void {
  dashboardState.loadDashboard()
}

function handleLimitChange(value: number): void {
  dashboardState.limit.value = value
  dashboardState.loadDashboard()
}

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
