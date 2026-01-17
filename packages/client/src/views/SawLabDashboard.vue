<template>
  <div class="saw-lab-dashboard min-h-screen bg-gray-50 p-6">
    <!-- Header -->
    <div class="mb-6">
      <h1 class="text-3xl font-bold text-gray-900 mb-2">Saw Lab Dashboard</h1>
      <p class="text-gray-600">Real-time CNC monitoring with risk classification</p>
    </div>

    <!-- Summary Cards -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      <div class="bg-white rounded-lg shadow p-4 border-l-4 border-blue-500">
        <div class="text-sm text-gray-600 mb-1">Total Runs</div>
        <div class="text-2xl font-bold text-gray-900">{{ dashboard?.total_runs || 0 }}</div>
      </div>
      
      <div class="bg-white rounded-lg shadow p-4 border-l-4 border-green-500">
        <div class="text-sm text-gray-600 mb-1">Green (Safe)</div>
        <div class="text-2xl font-bold text-green-700">{{ riskCounts.green }}</div>
      </div>
      
      <div class="bg-white rounded-lg shadow p-4 border-l-4 border-amber-500">
        <div class="text-sm text-gray-600 mb-1">Yellow + Orange</div>
        <div class="text-2xl font-bold text-amber-700">{{ riskCounts.yellow + riskCounts.orange }}</div>
      </div>
      
      <div class="bg-white rounded-lg shadow p-4 border-l-4 border-rose-500">
        <div class="text-sm text-gray-600 mb-1">Red (Danger)</div>
        <div class="text-2xl font-bold text-rose-700">{{ riskCounts.red }}</div>
      </div>
    </div>

    <!-- Controls -->
    <div class="bg-white rounded-lg shadow p-4 mb-6">
      <div class="flex flex-wrap gap-4 items-center">
        <!-- Refresh Button -->
        <button
          @click="loadDashboard"
          :disabled="loading"
          class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          <span v-if="loading">⏳ Loading...</span>
          <span v-else>🔄 Refresh</span>
        </button>

        <!-- Limit Selector -->
        <div class="flex items-center gap-2">
          <label class="text-sm text-gray-700">Show:</label>
          <select
            v-model="limit"
            @change="loadDashboard"
            class="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
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
            v-model="riskFilter"
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
            v-model="statusFilter"
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
        <div v-if="lastUpdated" class="ml-auto text-sm text-gray-500">
          Updated: {{ formatTime(lastUpdated) }}
        </div>
      </div>
    </div>

    <!-- Error Message -->
    <div v-if="error" class="bg-rose-100 border border-rose-400 text-rose-700 px-4 py-3 rounded-lg mb-6">
      <strong>Error:</strong> {{ error }}
    </div>

    <!-- Empty State -->
    <div v-if="!loading && filteredRuns.length === 0" class="bg-white rounded-lg shadow p-12 text-center">
      <div class="text-6xl mb-4">📊</div>
      <h3 class="text-xl font-semibold text-gray-900 mb-2">No Runs Found</h3>
      <p class="text-gray-600 mb-4">
        {{ dashboard?.runs.length === 0 ? 'No job runs in the system yet.' : 'No runs match your current filters.' }}
      </p>
      <button
        v-if="riskFilter !== 'all' || statusFilter !== 'all'"
        @click="clearFilters"
        class="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
      >
        Clear Filters
      </button>
    </div>

    <!-- Run Cards Grid -->
    <div v-else class="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
      <div
        v-for="run in filteredRuns"
        :key="run.run_id"
        class="bg-white rounded-lg shadow hover:shadow-lg transition-shadow border-t-4"
        :class="riskBorderClass(run.risk_bucket.id)"
      >
        <!-- Card Header -->
        <div class="p-4 border-b border-gray-200">
          <div class="flex items-start justify-between mb-2">
            <div class="flex-1 min-w-0">
              <h3 class="text-sm font-mono text-gray-600 truncate" :title="run.run_id">
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
            <div v-if="run.blade_id" class="flex items-center gap-2">
              <span class="text-gray-500 w-24">Blade:</span>
              <span class="font-medium text-gray-900">{{ run.blade_id }}</span>
            </div>
          </div>

          <!-- Risk Score -->
          <div class="pt-2 border-t border-gray-100">
            <div class="flex items-center justify-between mb-1">
              <span class="text-sm text-gray-600">Risk Score</span>
              <span class="text-lg font-bold" :class="riskScoreColor(run.risk_score)">
                {{ run.risk_score.toFixed(2) }}
              </span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-2">
              <div
                class="h-2 rounded-full transition-all"
                :class="riskBarClass(run.risk_bucket.id)"
                :style="{ width: `${run.risk_score * 100}%` }"
              ></div>
            </div>
            <div class="text-xs text-gray-500 mt-1">
              {{ run.risk_bucket.description }}
            </div>
          </div>

          <!-- Metrics (if telemetry available) -->
          <div v-if="run.has_telemetry && run.metrics" class="pt-2 border-t border-gray-100">
            <div class="text-xs text-gray-600 mb-2 font-semibold">Telemetry Metrics</div>
            <div class="grid grid-cols-2 gap-2 text-xs">
              <div class="bg-gray-50 rounded p-2">
                <div class="text-gray-500">Avg Load</div>
                <div class="font-semibold text-gray-900">
                  {{ run.metrics.avg_spindle_load_pct?.toFixed(1) || 'N/A' }}%
                </div>
              </div>
              <div class="bg-gray-50 rounded p-2">
                <div class="text-gray-500">Max Load</div>
                <div class="font-semibold text-gray-900">
                  {{ run.metrics.max_spindle_load_pct?.toFixed(1) || 'N/A' }}%
                </div>
              </div>
              <div class="bg-gray-50 rounded p-2">
                <div class="text-gray-500">Avg RPM</div>
                <div class="font-semibold text-gray-900">
                  {{ run.metrics.avg_rpm?.toFixed(0) || 'N/A' }}
                </div>
              </div>
              <div class="bg-gray-50 rounded p-2">
                <div class="text-gray-500">Vibration</div>
                <div class="font-semibold text-gray-900">
                  {{ run.metrics.avg_vibration_rms?.toFixed(2) || 'N/A' }} mm/s
                </div>
              </div>
            </div>
            <div class="text-xs text-gray-500 mt-1">
              {{ run.metrics.n_samples }} samples
            </div>
          </div>

          <!-- No Telemetry Message -->
          <div v-else class="pt-2 border-t border-gray-100 text-center">
            <div class="text-sm text-gray-500 py-2">
              ℹ️ No telemetry data available
            </div>
          </div>
        </div>

        <!-- Card Footer -->
        <div class="p-3 bg-gray-50 border-t border-gray-200 flex gap-2">
          <button
            @click="openRunDetail(run)"
            class="flex-1 px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
          >
            📊 View Details
          </button>
          <button
            v-if="run.has_telemetry && run.metrics"
            @click="openRiskActions(run)"
            class="flex-1 px-3 py-1.5 text-sm bg-purple-600 text-white rounded hover:bg-purple-700 transition-colors"
          >
            ⚙️ Risk Actions
          </button>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-if="filteredRuns.length === 0 && !loading" class="bg-white rounded-lg shadow p-12 text-center">
      <div class="text-gray-400 text-6xl mb-4">🪚</div>
      <h3 class="text-xl font-semibold text-gray-900 mb-2">No Saw Runs Found</h3>
      <p class="text-gray-600">{{ error ? 'Error loading data. Try refreshing.' : 'No runs match your filters.' }}</p>
    </div>
  </div>

  <!-- Run Detail Modal -->
  <Teleport to="body">
    <div
      v-if="selectedRun"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
      @click.self="closeRunDetail"
    >
      <div class="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <!-- Modal Header -->
        <div class="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <div>
            <h2 class="text-2xl font-bold text-gray-900">Run Details</h2>
            <p class="text-sm text-gray-600">{{ selectedRun.run_id }}</p>
          </div>
          <button
            @click="closeRunDetail"
            class="text-gray-400 hover:text-gray-600 text-2xl font-bold"
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
              <p class="text-gray-900">{{ formatDateTime(selectedRun.created_at) }}</p>
            </div>
            <div>
              <label class="text-sm font-semibold text-gray-600">Status</label>
              <p>
                <span class="px-2 py-1 rounded text-sm" :class="statusBadgeClass(selectedRun.status)">
                  {{ selectedRun.status }}
                </span>
              </p>
            </div>
            <div>
              <label class="text-sm font-semibold text-gray-600">Operation</label>
              <p class="text-gray-900">{{ selectedRun.op_type }}</p>
            </div>
            <div>
              <label class="text-sm font-semibold text-gray-600">Machine</label>
              <p class="text-gray-900">{{ selectedRun.machine_profile }}</p>
            </div>
            <div>
              <label class="text-sm font-semibold text-gray-600">Material</label>
              <p class="text-gray-900">{{ selectedRun.material_family }}</p>
            </div>
            <div v-if="selectedRun.blade_id">
              <label class="text-sm font-semibold text-gray-600">Blade</label>
              <p class="text-gray-900">{{ selectedRun.blade_id }}</p>
            </div>
          </div>

          <!-- Risk Assessment -->
          <div class="bg-gray-50 rounded-lg p-4">
            <h3 class="text-lg font-semibold text-gray-900 mb-3">Risk Assessment</h3>
            <div class="space-y-3">
              <div class="flex items-center justify-between">
                <span class="text-gray-700">Risk Level</span>
                <span
                  class="px-3 py-1 rounded-full text-sm font-semibold"
                  :class="riskBadgeClass(selectedRun.risk_bucket.id)"
                >
                  {{ selectedRun.risk_bucket.label }}
                </span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-gray-700">Risk Score</span>
                <span class="text-lg font-bold" :class="riskScoreColor(selectedRun.risk_score)">
                  {{ selectedRun.risk_score.toFixed(3) }}
                </span>
              </div>
              <div class="w-full bg-gray-200 rounded-full h-3">
                <div
                  class="h-3 rounded-full transition-all"
                  :class="riskBarClass(selectedRun.risk_bucket.id)"
                  :style="{ width: `${selectedRun.risk_score * 100}%` }"
                ></div>
              </div>
              <p class="text-sm text-gray-600 italic">{{ selectedRun.risk_bucket.description }}</p>
            </div>
          </div>

          <!-- Telemetry Metrics -->
          <div v-if="selectedRun.has_telemetry && selectedRun.metrics" class="bg-blue-50 rounded-lg p-4">
            <h3 class="text-lg font-semibold text-gray-900 mb-3">Telemetry Metrics</h3>
            <div class="grid grid-cols-2 gap-4">
              <div class="bg-white rounded p-3">
                <div class="text-sm text-gray-600">Average Spindle Load</div>
                <div class="text-2xl font-bold text-gray-900">
                  {{ selectedRun.metrics.avg_spindle_load_pct?.toFixed(1) }}%
                </div>
              </div>
              <div class="bg-white rounded p-3">
                <div class="text-sm text-gray-600">Max Spindle Load</div>
                <div class="text-2xl font-bold text-gray-900">
                  {{ selectedRun.metrics.max_spindle_load_pct?.toFixed(1) }}%
                </div>
              </div>
              <div class="bg-white rounded p-3">
                <div class="text-sm text-gray-600">Average RPM</div>
                <div class="text-2xl font-bold text-gray-900">
                  {{ selectedRun.metrics.avg_rpm?.toFixed(0) }}
                </div>
              </div>
              <div class="bg-white rounded p-3">
                <div class="text-sm text-gray-600">Max RPM</div>
                <div class="text-2xl font-bold text-gray-900">
                  {{ (selectedRun.metrics as any).max_rpm?.toFixed(0) }}
                </div>
              </div>
              <div class="bg-white rounded p-3">
                <div class="text-sm text-gray-600">Average Feed Rate</div>
                <div class="text-2xl font-bold text-gray-900">
                  {{ selectedRun.metrics.avg_feed_mm_min?.toFixed(0) }} mm/min
                </div>
              </div>
              <div class="bg-white rounded p-3">
                <div class="text-sm text-gray-600">Vibration (RMS)</div>
                <div class="text-2xl font-bold text-gray-900">
                  {{ selectedRun.metrics.avg_vibration_rms?.toFixed(2) }} mm/s
                </div>
              </div>
            </div>
            <div class="mt-3 text-sm text-gray-600">
              📊 {{ selectedRun.metrics.n_samples }} telemetry samples recorded
            </div>
          </div>

          <!-- Lane Scale History -->
          <div v-if="selectedRun.lane_scale_history.length > 0" class="bg-purple-50 rounded-lg p-4">
            <h3 class="text-lg font-semibold text-gray-900 mb-3">Lane Scale History</h3>
            <div class="overflow-x-auto">
              <table class="min-w-full divide-y divide-gray-300">
                <thead>
                  <tr class="bg-white">
                    <th class="px-3 py-2 text-left text-xs font-semibold text-gray-900">Timestamp</th>
                    <th class="px-3 py-2 text-left text-xs font-semibold text-gray-900">Scale</th>
                    <th class="px-3 py-2 text-left text-xs font-semibold text-gray-900">Source</th>
                    <th class="px-3 py-2 text-left text-xs font-semibold text-gray-900">Reason</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-gray-200 bg-white">
                  <tr v-for="(hist, idx) in selectedRun.lane_scale_history" :key="idx">
                    <td class="px-3 py-2 text-sm text-gray-900">{{ formatDateTime((hist as any).timestamp || hist.ts) }}</td>
                    <td class="px-3 py-2 text-sm font-semibold text-gray-900">{{ hist.lane_scale.toFixed(2) }}</td>
                    <td class="px-3 py-2 text-sm text-gray-600">{{ hist.source }}</td>
                    <td class="px-3 py-2 text-sm text-gray-600">{{ (hist as any).meta?.reason || 'N/A' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- Modal Footer -->
        <div class="sticky bottom-0 bg-gray-50 border-t border-gray-200 px-6 py-4 flex justify-end gap-3">
          <button
            @click="closeRunDetail"
            class="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300 transition-colors"
          >
            Close
          </button>
          <button
            v-if="selectedRun.has_telemetry && selectedRun.metrics"
            @click="openRiskActions(selectedRun)"
            class="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 transition-colors"
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
      v-if="riskActionsRun"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
      @click.self="closeRiskActions"
    >
      <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <!-- Modal Header -->
        <div class="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <div>
            <h2 class="text-2xl font-bold text-gray-900">Risk Actions</h2>
            <p class="text-sm text-gray-600">{{ riskActionsRun.run_id }}</p>
          </div>
          <button
            @click="closeRiskActions"
            class="text-gray-400 hover:text-gray-600 text-2xl font-bold"
          >
            ×
          </button>
        </div>

        <!-- Modal Body -->
        <div class="p-6 space-y-6">
          <!-- Current Status -->
          <div class="bg-gray-50 rounded-lg p-4">
            <h3 class="text-lg font-semibold text-gray-900 mb-3">Current Status</h3>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <div class="text-sm text-gray-600">Risk Level</div>
                <span
                  class="inline-block px-3 py-1 rounded-full text-sm font-semibold mt-1"
                  :class="riskBadgeClass(riskActionsRun.risk_bucket.id)"
                >
                  {{ riskActionsRun.risk_bucket.label }}
                </span>
              </div>
              <div>
                <div class="text-sm text-gray-600">Risk Score</div>
                <div class="text-2xl font-bold mt-1" :class="riskScoreColor(riskActionsRun.risk_score)">
                  {{ riskActionsRun.risk_score.toFixed(3) }}
                </div>
              </div>
            </div>
          </div>

          <!-- Recommended Actions -->
          <div class="bg-blue-50 rounded-lg p-4">
            <h3 class="text-lg font-semibold text-gray-900 mb-3">💡 Recommended Actions</h3>
            <div class="space-y-3">
              <div v-for="(action, idx) in computedActions" :key="idx" class="bg-white rounded-lg p-4 border-l-4" :class="action.severity === 'critical' ? 'border-rose-500' : action.severity === 'warning' ? 'border-amber-500' : 'border-blue-500'">
                <div class="flex items-start justify-between">
                  <div class="flex-1">
                    <div class="font-semibold text-gray-900 mb-1">{{ action.title }}</div>
                    <p class="text-sm text-gray-600 mb-2">{{ action.description }}</p>
                    <div v-if="action.suggested_override" class="text-xs font-mono bg-gray-100 px-2 py-1 rounded">
                      Suggested: {{ action.suggested_override }}
                    </div>
                  </div>
                  <button
                    v-if="action.action_type === 'apply_override'"
                    @click="applyOverride(action)"
                    class="ml-3 px-3 py-1 text-sm bg-purple-600 text-white rounded hover:bg-purple-700 transition-colors"
                  >
                    Apply
                  </button>
                </div>
              </div>
              <div v-if="computedActions.length === 0" class="text-center py-4 text-gray-500">
                ✅ No actions required - operation within safe parameters
              </div>
            </div>
          </div>

          <!-- Override Confirmation -->
          <div v-if="pendingOverride" class="bg-amber-50 border border-amber-300 rounded-lg p-4">
            <h3 class="text-lg font-semibold text-amber-900 mb-2">⚠️ Confirm Override</h3>
            <p class="text-sm text-amber-800 mb-3">
              Apply {{ pendingOverride.suggested_override }} to future operations with similar conditions?
            </p>
            <div class="flex gap-3">
              <button
                @click="confirmApplyOverride"
                class="flex-1 px-4 py-2 bg-amber-600 text-white rounded hover:bg-amber-700 transition-colors"
              >
                ✓ Confirm
              </button>
              <button
                @click="cancelOverride"
                class="flex-1 px-4 py-2 bg-gray-300 text-gray-800 rounded hover:bg-gray-400 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>

        <!-- Modal Footer -->
        <div class="sticky bottom-0 bg-gray-50 border-t border-gray-200 px-6 py-4 flex justify-end">
          <button
            @click="closeRiskActions"
            class="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { getDashboardRuns, type DashboardSummary, type RunSummaryItem, type RiskBucketId } from '@/api/sawLab'

// ============================================================================
// STATE
// ============================================================================

const dashboard = ref<DashboardSummary | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)
const lastUpdated = ref<Date | null>(null)

// Filters
const limit = ref(50)
const riskFilter = ref<RiskBucketId | 'all'>('all')
const statusFilter = ref('all')

// Modals
const selectedRun = ref<RunSummaryItem | null>(null)
const riskActionsRun = ref<RunSummaryItem | null>(null)
const pendingOverride = ref<{
  title: string
  suggested_override: string
  action_type: string
} | null>(null)

// ============================================================================
// COMPUTED
// ============================================================================

const filteredRuns = computed(() => {
  if (!dashboard.value) return []
  
  let runs = dashboard.value.runs
  
  // Filter by risk
  if (riskFilter.value !== 'all') {
    runs = runs.filter(r => r.risk_bucket.id === riskFilter.value)
  }
  
  // Filter by status
  if (statusFilter.value !== 'all') {
    runs = runs.filter(r => r.status === statusFilter.value)
  }
  
  return runs
})

const riskCounts = computed(() => {
  const counts = {
    unknown: 0,
    green: 0,
    yellow: 0,
    orange: 0,
    red: 0
  }
  
  dashboard.value?.runs.forEach(run => {
    counts[run.risk_bucket.id as RiskBucketId]++
  })
  
  return counts
})

// Computed actions based on run telemetry
const computedActions = computed(() => {
  if (!riskActionsRun.value || !riskActionsRun.value.metrics) return []
  
  const actions: any[] = []
  const metrics = riskActionsRun.value.metrics
  const avgLoad = metrics.avg_spindle_load_pct || 0
  const maxLoad = metrics.max_spindle_load_pct || 0
  const avgVibration = metrics.avg_vibration_rms || 0
  
  // High load detection
  if (avgLoad > 80) {
    actions.push({
      title: 'High Average Spindle Load Detected',
      description: `Average load of ${avgLoad.toFixed(1)}% exceeds safe threshold (80%). Reduce feed rate to prevent blade damage.`,
      severity: 'critical',
      action_type: 'apply_override',
      suggested_override: 'Feed rate -20%'
    })
  } else if (avgLoad > 70) {
    actions.push({
      title: 'Elevated Spindle Load',
      description: `Average load of ${avgLoad.toFixed(1)}% is approaching limits. Consider reducing feed rate.`,
      severity: 'warning',
      action_type: 'apply_override',
      suggested_override: 'Feed rate -10%'
    })
  }
  
  // Peak load detection
  if (maxLoad > 90) {
    actions.push({
      title: 'Critical Peak Load',
      description: `Peak load of ${maxLoad.toFixed(1)}% indicates potential stall conditions. Immediate feed reduction required.`,
      severity: 'critical',
      action_type: 'apply_override',
      suggested_override: 'Feed rate -30%'
    })
  }
  
  // Low load - can speed up
  if (avgLoad < 40 && maxLoad < 50) {
    actions.push({
      title: 'Low Spindle Load - Optimization Opportunity',
      description: `Average load of ${avgLoad.toFixed(1)}% suggests feed rate can be safely increased for faster cycle times.`,
      severity: 'info',
      action_type: 'apply_override',
      suggested_override: 'Feed rate +15%'
    })
  }
  
  // Vibration detection
  if (avgVibration > 10) {
    actions.push({
      title: 'Excessive Vibration Detected',
      description: `Average vibration of ${avgVibration.toFixed(2)} mm/s RMS indicates blade imbalance or looseness. Inspect blade mounting.`,
      severity: 'critical',
      action_type: 'manual_check',
      suggested_override: null
    })
  } else if (avgVibration > 5) {
    actions.push({
      title: 'Elevated Vibration',
      description: `Vibration of ${avgVibration.toFixed(2)} mm/s RMS is above normal. Check blade condition and mounting.`,
      severity: 'warning',
      action_type: 'manual_check',
      suggested_override: null
    })
  }
  
  return actions
})

// ============================================================================
// METHODS
// ============================================================================

async function loadDashboard() {
  loading.value = true
  error.value = null
  
  try {
    dashboard.value = await getDashboardRuns(limit.value)
    lastUpdated.value = new Date()
  } catch (err: any) {
    error.value = err.response?.data?.detail || err.message || 'Failed to load dashboard'
    console.error('Dashboard load error:', err)
  } finally {
    loading.value = false
  }
}

function clearFilters() {
  riskFilter.value = 'all'
  statusFilter.value = 'all'
}

function openRunDetail(run: RunSummaryItem) {
  selectedRun.value = run
  riskActionsRun.value = null  // Close risk actions if open
}

function closeRunDetail() {
  selectedRun.value = null
}

function openRiskActions(run: RunSummaryItem) {
  riskActionsRun.value = run
  selectedRun.value = null  // Close run detail if open
  pendingOverride.value = null
}

function closeRiskActions() {
  riskActionsRun.value = null
  pendingOverride.value = null
}

function applyOverride(action: any) {
  pendingOverride.value = action
}

async function confirmApplyOverride() {
  if (!pendingOverride.value || !riskActionsRun.value) return
  
  try {
    // TODO: Call backend API to apply override
    console.log('Applying override:', {
      run_id: riskActionsRun.value.run_id,
      override: pendingOverride.value.suggested_override,
      action: pendingOverride.value.title
    })
    
    // Show success message (placeholder)
    alert(`✓ Override applied: ${pendingOverride.value.suggested_override}`)
    
    // Reload dashboard
    await loadDashboard()
    
    // Close modals
    closeRiskActions()
  } catch (err: any) {
    error.value = err.message || 'Failed to apply override'
    console.error('Override apply error:', err)
  }
}

function cancelOverride() {
  pendingOverride.value = null
}

// ============================================================================
// STYLING HELPERS
// ============================================================================

function riskBorderClass(bucketId: RiskBucketId): string {
  const classes = {
    unknown: 'border-gray-400',
    green: 'border-green-500',
    yellow: 'border-amber-500',
    orange: 'border-orange-500',
    red: 'border-rose-500'
  }
  return classes[bucketId]
}

function riskBadgeClass(bucketId: RiskBucketId): string {
  const classes = {
    unknown: 'bg-gray-100 text-gray-700',
    green: 'bg-green-100 text-green-800',
    yellow: 'bg-amber-100 text-amber-800',
    orange: 'bg-orange-100 text-orange-800',
    red: 'bg-rose-100 text-rose-800'
  }
  return classes[bucketId]
}

function riskBarClass(bucketId: RiskBucketId): string {
  const classes = {
    unknown: 'bg-gray-400',
    green: 'bg-green-500',
    yellow: 'bg-amber-500',
    orange: 'bg-orange-500',
    red: 'bg-rose-500'
  }
  return classes[bucketId]
}

function riskScoreColor(score: number): string {
  if (score < 0.3) return 'text-green-700'
  if (score < 0.6) return 'text-amber-700'
  if (score < 0.85) return 'text-orange-700'
  return 'text-rose-700'
}

function statusBadgeClass(status: string): string {
  const classes: Record<string, string> = {
    pending: 'bg-blue-100 text-blue-800',
    running: 'bg-purple-100 text-purple-800',
    completed: 'bg-green-100 text-green-800',
    error: 'bg-rose-100 text-rose-800'
  }
  return classes[status] || 'bg-gray-100 text-gray-800'
}

// ============================================================================
// FORMATTING HELPERS
// ============================================================================

function formatDateTime(isoString: string): string {
  const date = new Date(isoString)
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// ============================================================================
// LIFECYCLE
// ============================================================================

onMounted(() => {
  loadDashboard()
})
</script>

<style scoped>
.saw-lab-dashboard {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}
</style>
