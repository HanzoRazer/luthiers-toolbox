<template>
  <div class="compare-runs-panel">
    <header class="panel-header">
      <h2>Compare Runs</h2>
      <div class="actions">
        <button
          class="secondary"
          :disabled="selectedRunIds.length < 2"
          @click="loadComparison"
        >
          Compare Selected ({{ selectedRunIds.length }})
        </button>
        <button
          v-if="comparisonData"
          class="ghost"
          @click="exportCsv"
        >
          Export CSV
        </button>
        <button
          class="ghost"
          @click="clearSelection"
        >
          Clear
        </button>
      </div>
    </header>

    <div v-if="error" class="error-banner">
      {{ error }}
    </div>

    <div v-if="!comparisonData && !loading" class="empty-state">
      <p>Select 2-4 jobs from the history table to compare.</p>
      <p class="hint">Checkboxes will appear when jobs are loaded.</p>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Loading comparison...</p>
    </div>

    <div v-if="comparisonData" class="comparison-table-wrapper">
      <table class="comparison-table">
        <thead>
          <tr>
            <th class="metric-name">Metric</th>
            <th
              v-for="(job, idx) in comparisonData.jobs"
              :key="job.run_id"
              :class="{ baseline: job.is_baseline }"
            >
              <div class="job-header">
                <span class="job-name">{{ job.job_name || job.run_id.slice(0, 8) }}</span>
                <span v-if="job.is_baseline" class="baseline-badge">Baseline</span>
              </div>
              <div class="job-meta">
                {{ job.machine_id }} · {{ job.post_id }}
              </div>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(metric, key) in comparisonData.comparison" :key="key">
            <td class="metric-name">{{ formatMetricName(key) }}</td>
            <td
              v-for="(value, idx) in metric.values"
              :key="idx"
              :class="{
                winner: metric.winner === idx,
                'has-direction': metric.direction
              }"
            >
              <div class="metric-value">
                <span v-if="metric.winner === idx" class="winner-icon">🏆</span>
                {{ formatValue(value, key) }}
              </div>
              <div v-if="metric.direction && idx > 0 && typeof value === 'number'" class="delta">
                {{ formatDelta(value as number, metric.values[0] as number, metric.direction) }}
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <div class="actions-footer">
        <button
          class="secondary"
          @click="setBaseline"
          :disabled="!comparisonData || comparisonData.jobs.length === 0"
        >
          Set Winner as Baseline
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

interface Job {
  run_id: string
  job_name?: string
  machine_id?: string
  post_id?: string
  is_baseline: boolean
}

interface Metric {
  values: (number | string | null)[]
  winner: number | null
  direction?: 'lower' | 'higher'
}

interface ComparisonData {
  jobs: Job[]
  comparison: Record<string, Metric>
  job_count: number
}

const props = defineProps<{
  selectedRunIds: string[]
}>()

const emit = defineEmits<{
  (e: 'clear-selection'): void
  (e: 'set-baseline', runId: string): void
}>()

const comparisonData = ref<ComparisonData | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

async function loadComparison() {
  if (props.selectedRunIds.length < 2 || props.selectedRunIds.length > 4) {
    error.value = 'Select 2-4 jobs to compare'
    return
  }

  loading.value = true
  error.value = null

  try {
    const ids = props.selectedRunIds.join(',')
    const response = await fetch(`/api/cnc/jobs/compare?ids=${encodeURIComponent(ids)}`)

    if (!response.ok) {
      const text = await response.text()
      throw new Error(text || `HTTP ${response.status}`)
    }

    comparisonData.value = await response.json()
  } catch (e: any) {
    error.value = `Failed to load comparison: ${e.message}`
    console.error(e)
  } finally {
    loading.value = false
  }
}

function clearSelection() {
  comparisonData.value = null
  error.value = null
  emit('clear-selection')
}

function setBaseline() {
  if (!comparisonData.value) return

  // Find job with most wins
  const wins = comparisonData.value.jobs.map(() => 0)
  Object.values(comparisonData.value.comparison).forEach((metric) => {
    if (metric.winner !== null && metric.winner >= 0) {
      wins[metric.winner]++
    }
  })

  const winnerIdx = wins.indexOf(Math.max(...wins))
  if (winnerIdx >= 0) {
    const winnerId = comparisonData.value.jobs[winnerIdx].run_id
    markAsBaseline(winnerId)
  }
}

async function markAsBaseline(runId: string) {
  try {
    const response = await fetch(`/api/cnc/jobs/${runId}/set-baseline`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ baseline_id: runId })
    })

    if (!response.ok) {
      const text = await response.text()
      throw new Error(text || `HTTP ${response.status}`)
    }

    // Reload comparison to show baseline badge
    await loadComparison()
    
    // Notify parent
    emit('set-baseline', runId)
  } catch (e: any) {
    error.value = `Failed to set baseline: ${e.message}`
    console.error(e)
  }
}

function exportCsv() {
  if (!comparisonData.value) return

  const rows: string[][] = []

  // Header row
  const header = ['Metric', ...comparisonData.value.jobs.map((j: Job) => j.job_name || j.run_id)]
  rows.push(header)

  // Data rows
  Object.entries(comparisonData.value.comparison).forEach(([key, metricUnknown]) => {
    const metric = metricUnknown as Metric
    const row = [formatMetricName(key), ...metric.values.map((v: number | string | null) => formatValue(v, key))]
    rows.push(row)
  })

  // Convert to CSV
  const csv = rows.map((row) => row.map((cell) => `"${cell}"`).join(',')).join('\n')

  // Download
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `compare_${Date.now()}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

function formatMetricName(key: string): string {
  const names: Record<string, string> = {
    machine: 'Machine',
    material: 'Material',
    post: 'Post Processor',
    predicted_time_s: 'Cycle Time (s)',
    energy_j: 'Energy (J)',
    move_count: 'Move Count',
    issue_count: 'Issue Count',
    max_deviation_pct: 'Max Deviation (%)',
    notes: 'Notes',
    tags: 'Tags',
  }
  return names[key] || key
}

function formatValue(value: any, key: string): string {
  if (value === null || value === undefined) return '—'
  if (typeof value === 'number') {
    if (key.includes('time')) return value.toFixed(2)
    if (key.includes('energy')) return value.toFixed(0)
    if (key.includes('pct')) return value.toFixed(2)
    return value.toString()
  }
  if (Array.isArray(value)) return value.join(', ')
  return String(value)
}

function formatDelta(current: number, baseline: number, direction: string): string {
  if (typeof baseline !== 'number') return ''

  const delta = current - baseline
  const pct = ((delta / baseline) * 100).toFixed(1)

  const isImprovement =
    (direction === 'lower' && delta < 0) || (direction === 'higher' && delta > 0)

  const sign = delta > 0 ? '+' : ''
  const color = isImprovement ? 'green' : 'red'

  return `<span style="color: ${color}">${sign}${pct}%</span>`
}
</script>

<style scoped>
.compare-runs-panel {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 1.5rem;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #e5e7eb;
}

.panel-header h2 {
  margin: 0;
  font-size: 1.5rem;
  color: #1f2937;
}

.actions {
  display: flex;
  gap: 0.5rem;
}

.error-banner {
  background: #fee2e2;
  border: 1px solid #fecaca;
  color: #991b1b;
  padding: 0.75rem 1rem;
  border-radius: 6px;
  margin-bottom: 1rem;
}

.empty-state,
.loading-state {
  text-align: center;
  padding: 3rem 1rem;
  color: #6b7280;
}

.hint {
  font-size: 0.875rem;
  color: #9ca3af;
  margin-top: 0.5rem;
}

.spinner {
  margin: 0 auto 1rem;
  width: 40px;
  height: 40px;
  border: 4px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.comparison-table-wrapper {
  overflow-x: auto;
}

.comparison-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.comparison-table th,
.comparison-table td {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid #e5e7eb;
}

.comparison-table thead th {
  background: #f9fafb;
  font-weight: 600;
  color: #374151;
  position: sticky;
  top: 0;
  z-index: 10;
}

.comparison-table thead th.baseline {
  background: #dbeafe;
}

.metric-name {
  font-weight: 500;
  color: #1f2937;
  width: 200px;
}

.job-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.25rem;
}

.job-name {
  font-weight: 600;
}

.baseline-badge {
  background: #3b82f6;
  color: white;
  font-size: 0.75rem;
  padding: 0.125rem 0.5rem;
  border-radius: 12px;
}

.job-meta {
  font-size: 0.75rem;
  color: #6b7280;
}

.metric-value {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.winner-icon {
  font-size: 1.25rem;
}

.winner {
  background: #f0fdf4;
  font-weight: 600;
}

.delta {
  font-size: 0.75rem;
  margin-top: 0.25rem;
}

.actions-footer {
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid #e5e7eb;
  display: flex;
  justify-content: flex-end;
}

button {
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-size: 0.875rem;
  cursor: pointer;
  border: 1px solid #d1d5db;
  background: white;
  color: #374151;
  transition: all 0.2s;
}

button:hover:not(:disabled) {
  background: #f3f4f6;
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

button.primary {
  background: #3b82f6;
  color: white;
  border-color: #3b82f6;
}

button.primary:hover:not(:disabled) {
  background: #2563eb;
}

button.secondary {
  background: #10b981;
  color: white;
  border-color: #10b981;
}

button.secondary:hover:not(:disabled) {
  background: #059669;
}

button.ghost {
  background: transparent;
  border-color: transparent;
}

button.ghost:hover:not(:disabled) {
  background: #f3f4f6;
}
</style>
