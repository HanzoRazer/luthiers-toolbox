<template>
  <div class="p-6 space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <h1 class="text-3xl font-bold">
        Multi-Run Comparison
      </h1>
      <button 
        class="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700" 
        @click="fetchPresets"
      >
        🔄 Refresh Presets
      </button>
    </div>

    <!-- Preset Selector -->
    <div class="bg-white border rounded-lg p-4">
      <h2 class="text-xl font-semibold mb-3">
        Select Presets to Compare
      </h2>
      <p class="text-sm text-gray-600 mb-4">
        Choose at least 2 presets that were cloned from JobInt runs (B19). Only presets with job lineage can be compared.
      </p>

      <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 max-h-64 overflow-y-auto p-2">
        <label 
          v-for="preset in presetsWithLineage" 
          :key="preset.id"
          class="flex items-start gap-2 p-3 border rounded hover:bg-gray-50 cursor-pointer"
          :class="{'bg-blue-50 border-blue-300': selectedPresetIds.includes(preset.id)}"
        >
          <input 
            v-model="selectedPresetIds" 
            type="checkbox" 
            :value="preset.id"
            class="mt-1"
          >
          <div class="flex-1">
            <p class="font-medium text-sm">{{ preset.name }}</p>
            <p class="text-xs text-gray-500">{{ preset.kind }}</p>
            <p
              v-if="preset.job_source_id"
              class="text-xs text-gray-400"
            >
              Job: {{ preset.job_source_id.slice(0, 8) }}...
            </p>
          </div>
        </label>
      </div>

      <div
        v-if="presetsWithLineage.length === 0"
        class="text-center py-8 text-gray-500"
      >
        <p class="mb-2">
          📭 No presets with job lineage found
        </p>
        <p class="text-sm">
          Clone jobs as presets using B19 feature in JobInt view
        </p>
      </div>

      <div class="flex items-center gap-4 mt-4">
        <button 
          :disabled="selectedPresetIds.length < 2 || loading"
          class="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          @click="runComparison"
        >
          {{ loading ? '⏳ Analyzing...' : '🔍 Compare Runs' }}
        </button>
        <span class="text-sm text-gray-600">
          {{ selectedPresetIds.length }} preset{{ selectedPresetIds.length !== 1 ? 's' : '' }} selected
        </span>
        <button 
          v-if="selectedPresetIds.length > 0"
          class="text-sm text-gray-600 hover:text-gray-800 underline"
          @click="selectedPresetIds = []"
        >
          Clear selection
        </button>
      </div>
    </div>

    <!-- Error Message -->
    <div
      v-if="errorMessage"
      class="p-4 bg-red-50 border border-red-200 rounded text-red-700"
    >
      {{ errorMessage }}
    </div>

    <!-- Comparison Results -->
    <div
      v-if="comparisonResult"
      class="space-y-6"
    >
      <!-- Summary Stats -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div class="bg-white border rounded-lg p-4">
          <p class="text-sm text-gray-600 mb-1">
            Runs Compared
          </p>
          <p class="text-2xl font-bold">
            {{ comparisonResult.runs.length }}
          </p>
        </div>
        <div class="bg-white border rounded-lg p-4">
          <p class="text-sm text-gray-600 mb-1">
            Avg Time
          </p>
          <p class="text-2xl font-bold">
            {{ comparisonResult.avg_time_s ? comparisonResult.avg_time_s.toFixed(1) : 'N/A' }}s
          </p>
        </div>
        <div class="bg-white border rounded-lg p-4">
          <p class="text-sm text-gray-600 mb-1">
            Avg Energy
          </p>
          <p class="text-2xl font-bold">
            {{ comparisonResult.avg_energy_j ? comparisonResult.avg_energy_j.toFixed(0) : 'N/A' }}J
          </p>
        </div>
        <div class="bg-white border rounded-lg p-4">
          <p class="text-sm text-gray-600 mb-1">
            Avg Moves
          </p>
          <p class="text-2xl font-bold">
            {{ comparisonResult.avg_move_count || 'N/A' }}
          </p>
        </div>
      </div>

      <!-- Trends -->
      <div
        v-if="comparisonResult.time_trend || comparisonResult.energy_trend"
        class="bg-white border rounded-lg p-4"
      >
        <h3 class="text-lg font-semibold mb-3">
          📈 Performance Trends
        </h3>
        <div class="grid md:grid-cols-2 gap-4">
          <div v-if="comparisonResult.time_trend">
            <p class="text-sm font-medium text-gray-700 mb-1">
              Time Trend:
            </p>
            <span 
              class="inline-block px-3 py-1 rounded text-sm font-medium"
              :class="{
                'bg-green-100 text-green-700': comparisonResult.time_trend === 'improving',
                'bg-red-100 text-red-700': comparisonResult.time_trend === 'degrading',
                'bg-gray-100 text-gray-700': comparisonResult.time_trend === 'stable'
              }"
            >
              {{ comparisonResult.time_trend === 'improving' ? '✅ Improving' : 
                comparisonResult.time_trend === 'degrading' ? '⚠️ Degrading' : '➡️ Stable' }}
            </span>
          </div>
          <div v-if="comparisonResult.energy_trend">
            <p class="text-sm font-medium text-gray-700 mb-1">
              Energy Trend:
            </p>
            <span 
              class="inline-block px-3 py-1 rounded text-sm font-medium"
              :class="{
                'bg-green-100 text-green-700': comparisonResult.energy_trend === 'improving',
                'bg-red-100 text-red-700': comparisonResult.energy_trend === 'degrading',
                'bg-gray-100 text-gray-700': comparisonResult.energy_trend === 'stable'
              }"
            >
              {{ comparisonResult.energy_trend === 'improving' ? '✅ Improving' : 
                comparisonResult.energy_trend === 'degrading' ? '⚠️ Degrading' : '➡️ Stable' }}
            </span>
          </div>
        </div>
      </div>

      <!-- Recommendations -->
      <div
        v-if="comparisonResult.recommendations.length > 0"
        class="bg-blue-50 border border-blue-200 rounded-lg p-4"
      >
        <h3 class="text-lg font-semibold mb-3">
          💡 Recommendations
        </h3>
        <ul class="space-y-2">
          <li
            v-for="(rec, idx) in comparisonResult.recommendations"
            :key="idx"
            class="text-sm"
          >
            {{ rec }}
          </li>
        </ul>
      </div>

      <!-- Detailed Run Comparison Table -->
      <div class="bg-white border rounded-lg p-4">
        <h3 class="text-lg font-semibold mb-3">
          📊 Detailed Run Comparison
        </h3>
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Preset Name
                </th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Time (s)
                </th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Energy (J)
                </th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Moves
                </th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Issues
                </th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Strategy
                </th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Feed XY
                </th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Efficiency
                </th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr 
                v-for="run in comparisonResult.runs" 
                :key="run.preset_id"
                :class="{
                  'bg-green-50': run.preset_id === comparisonResult.best_run_id,
                  'bg-red-50': run.preset_id === comparisonResult.worst_run_id
                }"
              >
                <td class="px-4 py-3 text-sm font-medium">
                  {{ run.preset_name }}
                  <span
                    v-if="run.preset_id === comparisonResult.best_run_id"
                    class="ml-2 text-green-600"
                  >
                    🏆 Best
                  </span>
                  <span
                    v-if="run.preset_id === comparisonResult.worst_run_id"
                    class="ml-2 text-red-600"
                  >
                    ⚠️ Worst
                  </span>
                </td>
                <td class="px-4 py-3 text-sm">
                  {{ run.sim_time_s ? run.sim_time_s.toFixed(2) : 'N/A' }}
                </td>
                <td class="px-4 py-3 text-sm">
                  {{ run.sim_energy_j !== null && run.sim_energy_j !== undefined ? run.sim_energy_j.toFixed(0) : 'N/A' }}
                </td>
                <td class="px-4 py-3 text-sm">
                  {{ run.sim_move_count || 'N/A' }}
                </td>
                <td class="px-4 py-3 text-sm">
                  <span 
                    v-if="run.sim_issue_count"
                    :class="{'text-red-600 font-medium': run.sim_issue_count > 0}"
                  >
                    {{ run.sim_issue_count }}
                  </span>
                  <span
                    v-else
                    class="text-gray-400"
                  >0</span>
                </td>
                <td class="px-4 py-3 text-sm">
                  {{ run.strategy || 'N/A' }}
                </td>
                <td class="px-4 py-3 text-sm">
                  {{ run.feed_xy ? run.feed_xy.toFixed(0) : 'N/A' }}
                </td>
                <td class="px-4 py-3 text-sm">
                  <div
                    v-if="run.efficiency_score !== null && run.efficiency_score !== undefined"
                    class="flex items-center gap-2"
                  >
                    <div class="w-16 bg-gray-200 rounded-full h-2">
                      <div 
                        class="h-2 rounded-full"
                        :class="{
                          'bg-green-500': run.efficiency_score >= 70,
                          'bg-yellow-500': run.efficiency_score >= 40 && run.efficiency_score < 70,
                          'bg-red-500': run.efficiency_score < 40
                        }"
                        :style="{width: `${run.efficiency_score}%`}"
                      />
                    </div>
                    <span class="text-xs font-medium">{{ run.efficiency_score.toFixed(0) }}/100</span>
                  </div>
                  <span
                    v-else
                    class="text-gray-400"
                  >N/A</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Time Comparison Chart -->
      <div class="bg-white border rounded-lg p-4">
        <h3 class="text-lg font-semibold mb-3">
          📉 Time Comparison
        </h3>
        <div
          v-if="chartData.labels.length > 0"
          class="h-64"
        >
          <canvas ref="timeChartCanvas" />
        </div>
        <p
          v-else
          class="text-center text-gray-500 py-8"
        >
          No time data available for charting
        </p>
      </div>

      <!-- Actions -->
      <div class="flex gap-4">
        <button 
          class="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
          @click="exportComparisonCSV"
        >
          📥 Export as CSV
        </button>
        <button 
          class="px-4 py-2 border rounded hover:bg-gray-50"
          @click="resetComparison"
        >
          🔄 New Comparison
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { api } from '@/services/apiBase';
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

interface Preset {
  id: string
  name: string
  kind: string
  job_source_id?: string
  created_at: string
}

interface ComparisonRun {
  preset_id: string
  preset_name: string
  job_source_id?: string
  run_id?: string
  sim_time_s?: number
  sim_energy_j?: number
  sim_move_count?: number
  sim_issue_count?: number
  sim_max_dev_pct?: number
  stepover?: number
  feed_xy?: number
  strategy?: string
  efficiency_score?: number
  created_at?: string
}

interface ComparisonResult {
  runs: ComparisonRun[]
  avg_time_s?: number
  min_time_s?: number
  max_time_s?: number
  avg_energy_j?: number
  avg_move_count?: number
  time_trend?: string
  energy_trend?: string
  best_run_id?: string
  worst_run_id?: string
  recommendations: string[]
}

// State persistence keys
const STORAGE_KEYS = {
  SELECTED_PRESETS: 'multirun.selectedPresets',
  LAST_COMPARISON: 'multirun.lastComparison',
  LAST_UPDATED: 'multirun.lastUpdated'
}

const allPresets = ref<Preset[]>([])
const selectedPresetIds = ref<string[]>([])
const loading = ref(false)
const errorMessage = ref<string>('')
const comparisonResult = ref<ComparisonResult | null>(null)
const timeChartCanvas = ref<HTMLCanvasElement | null>(null)
let timeChart: Chart | null = null

// Load state from localStorage
function loadPersistedState() {
  try {
    // Load selected preset IDs
    const savedSelection = localStorage.getItem(STORAGE_KEYS.SELECTED_PRESETS)
    if (savedSelection) {
      const parsed = JSON.parse(savedSelection)
      if (Array.isArray(parsed)) {
        selectedPresetIds.value = parsed
      }
    }

    // Load last comparison result (within 24 hours)
    const savedComparison = localStorage.getItem(STORAGE_KEYS.LAST_COMPARISON)
    const savedTimestamp = localStorage.getItem(STORAGE_KEYS.LAST_UPDATED)
    if (savedComparison && savedTimestamp) {
      const timestamp = parseInt(savedTimestamp, 10)
      const age = Date.now() - timestamp
      const maxAge = 24 * 60 * 60 * 1000 // 24 hours

      if (age < maxAge) {
        comparisonResult.value = JSON.parse(savedComparison)
      } else {
        // Clear stale data
        localStorage.removeItem(STORAGE_KEYS.LAST_COMPARISON)
        localStorage.removeItem(STORAGE_KEYS.LAST_UPDATED)
      }
    }
  } catch (error) {
    console.error('Failed to load persisted state:', error)
    // Clear corrupted data
    clearPersistedState()
  }
}

// Save state to localStorage
function savePersistedState() {
  try {
    // Save selected preset IDs
    localStorage.setItem(
      STORAGE_KEYS.SELECTED_PRESETS,
      JSON.stringify(selectedPresetIds.value)
    )

    // Save comparison result (if exists)
    if (comparisonResult.value) {
      localStorage.setItem(
        STORAGE_KEYS.LAST_COMPARISON,
        JSON.stringify(comparisonResult.value)
      )
      localStorage.setItem(
        STORAGE_KEYS.LAST_UPDATED,
        Date.now().toString()
      )
    }
  } catch (error) {
    console.error('Failed to save state:', error)
  }
}

// Clear all persisted state
function clearPersistedState() {
  localStorage.removeItem(STORAGE_KEYS.SELECTED_PRESETS)
  localStorage.removeItem(STORAGE_KEYS.LAST_COMPARISON)
  localStorage.removeItem(STORAGE_KEYS.LAST_UPDATED)
}

// Filter presets with job lineage (B19 cloned jobs)
const presetsWithLineage = computed(() => {
  return allPresets.value.filter(p => p.job_source_id)
})

// Chart data
const chartData = computed(() => {
  if (!comparisonResult.value) {
    return { labels: [], datasets: [] }
  }

  const runs = comparisonResult.value.runs.filter(r => r.sim_time_s !== null && r.sim_time_s !== undefined)
  const labels = runs.map(r => r.preset_name)
  const data = runs.map(r => r.sim_time_s || 0)

  return {
    labels,
    datasets: [{
      label: 'Simulation Time (s)',
      data,
      backgroundColor: runs.map(r => 
        r.preset_id === comparisonResult.value?.best_run_id ? 'rgba(34, 197, 94, 0.6)' :
        r.preset_id === comparisonResult.value?.worst_run_id ? 'rgba(239, 68, 68, 0.6)' :
        'rgba(59, 130, 246, 0.6)'
      ),
      borderColor: runs.map(r => 
        r.preset_id === comparisonResult.value?.best_run_id ? 'rgb(34, 197, 94)' :
        r.preset_id === comparisonResult.value?.worst_run_id ? 'rgb(239, 68, 68)' :
        'rgb(59, 130, 246)'
      ),
      borderWidth: 2
    }]
  }
})

async function fetchPresets() {
  try {
    const response = await api('/api/presets')
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    allPresets.value = await response.json()
  } catch (error) {
    console.error('Failed to fetch presets:', error)
    errorMessage.value = 'Failed to load presets. Check console for details.'
  }
}

async function runComparison() {
  if (selectedPresetIds.value.length < 2) {
    errorMessage.value = 'Please select at least 2 presets to compare'
    return
  }

  loading.value = true
  errorMessage.value = ''
  comparisonResult.value = null

  try {
    const response = await api('/api/presets/compare-runs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        preset_ids: selectedPresetIds.value,
        include_trends: true,
        include_recommendations: true
      })
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || `HTTP ${response.status}`)
    }

    comparisonResult.value = await response.json()
    
    // Persist state after successful comparison
    savePersistedState()
  } catch (error: any) {
    console.error('Comparison failed:', error)
    errorMessage.value = `Comparison failed: ${error.message}`
  } finally {
    loading.value = false
  }
}

function resetComparison() {
  comparisonResult.value = null
  selectedPresetIds.value = []
  errorMessage.value = ''
  if (timeChart) {
    timeChart.destroy()
    timeChart = null
  }
  
  // Clear persisted state
  clearPersistedState()
}

function exportComparisonCSV() {
  if (!comparisonResult.value) return

  const headers = ['Preset Name', 'Time (s)', 'Energy (J)', 'Moves', 'Issues', 'Strategy', 'Feed XY', 'Efficiency Score']
  const rows = comparisonResult.value.runs.map(run => [
    run.preset_name,
    run.sim_time_s?.toFixed(2) || 'N/A',
    run.sim_energy_j?.toFixed(0) || 'N/A',
    run.sim_move_count || 'N/A',
    run.sim_issue_count || '0',
    run.strategy || 'N/A',
    run.feed_xy?.toFixed(0) || 'N/A',
    run.efficiency_score?.toFixed(0) || 'N/A'
  ])

  const csv = [
    headers.join(','),
    ...rows.map(row => row.join(','))
  ].join('\n')

  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `multi-run-comparison-${Date.now()}.csv`
  link.click()
  URL.revokeObjectURL(url)
}

// Watch for comparison result changes and update chart
watch(() => comparisonResult.value, async (newResult) => {
  if (newResult && chartData.value.labels.length > 0) {
    await nextTick()
    if (timeChartCanvas.value) {
      if (timeChart) {
        timeChart.destroy()
      }

      timeChart = new Chart(timeChartCanvas.value, {
        type: 'bar',
        data: chartData.value,
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: false
            },
            tooltip: {
              callbacks: {
                label: (context) => {
                  return `${(context.parsed.y ?? 0).toFixed(2)}s`
                }
              }
            }
          },
          scales: {
            y: {
              beginAtZero: true,
              title: {
                display: true,
                text: 'Time (seconds)'
              }
            }
          }
        }
      })
    }
  }
}, { immediate: true })

onMounted(async () => {
  // Load persisted state first
  loadPersistedState()
  
  // Fetch fresh preset list
  await fetchPresets()
})

// Watch for selection changes and persist
watch(() => selectedPresetIds.value, () => {
  savePersistedState()
}, { deep: true })

</script>

<style scoped>
/* Tailwind handles most styling */
</style>
