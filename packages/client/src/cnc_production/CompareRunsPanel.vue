<template>
  <div class="compare-panel">
    <div class="panel-header">
      <div>
        <h3>Compare Runs</h3>
        <p>Select 2–4 jobs to compare metrics side-by-side.</p>
      </div>
      <div class="header-actions">
        <button 
          class="primary" 
          :disabled="selectedIds.length < 2 || selectedIds.length > 4 || comparing" 
          @click="compare"
        >
          {{ comparing ? 'Comparing…' : `Compare ${selectedIds.length} Jobs` }}
        </button>
        <button
          class="secondary"
          :disabled="selectedIds.length === 0"
          @click="clearSelection"
        >
          Clear
        </button>
        <button
          class="refresh"
          :disabled="loading"
          @click="refreshJobs"
        >
          {{ loading ? 'Loading…' : 'Refresh' }}
        </button>
      </div>
    </div>

    <p
      v-if="error"
      class="error"
    >
      {{ error }}
    </p>

    <!-- Job Selection List -->
    <div
      v-if="!comparisonResult"
      class="job-list"
    >
      <div 
        v-for="job in jobs" 
        :key="job.run_id" 
        class="job-row"
        :class="{ selected: selectedIds.includes(job.run_id) }"
      >
        <label class="checkbox-label">
          <input 
            v-model="selectedIds" 
            type="checkbox"
            :value="job.run_id"
            :disabled="selectedIds.length >= 4 && !selectedIds.includes(job.run_id)"
          >
          <div class="job-info">
            <div class="job-name">{{ job.job_name || job.run_id }}</div>
            <div class="job-meta">
              <span>{{ job.machine_id || '—' }}</span>
              <span>{{ job.material || '—' }}</span>
              <span>{{ job.post_id || '—' }}</span>
              <span v-if="job.sim_time_s">{{ formatTime(job.sim_time_s) }}</span>
              <span
                v-if="job.sim_issue_count !== undefined"
                :class="issueClass(job.sim_issue_count)"
              >
                {{ job.sim_issue_count }} issues
              </span>
            </div>
          </div>
        </label>
      </div>

      <p
        v-if="!loading && jobs.length === 0"
        class="empty"
      >
        No jobs found. Run some adaptive pocket or pipeline operations first.
      </p>
    </div>

    <!-- Comparison Table -->
    <div
      v-if="comparisonResult"
      class="comparison-view"
    >
      <div class="comparison-header">
        <h4>Comparison Results</h4>
        <div class="comparison-actions">
          <button
            class="secondary"
            :disabled="exporting"
            @click="exportCsv"
          >
            {{ exporting ? 'Exporting…' : 'Export CSV' }}
          </button>
          <button
            class="secondary"
            @click="backToSelection"
          >
            ← Back to Selection
          </button>
        </div>
      </div>

      <div class="comparison-table-wrapper">
        <table class="comparison-table">
          <thead>
            <tr>
              <th>Metric</th>
              <th
                v-for="(job, idx) in comparisonResult.jobs"
                :key="job.run_id"
              >
                Job {{ idx + 1 }}
                <div class="job-id">
                  {{ job.job_name || job.run_id.slice(0, 8) }}
                </div>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td class="metric-name">
                Machine
              </td>
              <td
                v-for="(val, idx) in comparisonResult.comparison.machine?.values"
                :key="idx"
              >
                {{ val }}
              </td>
            </tr>
            <tr>
              <td class="metric-name">
                Material
              </td>
              <td
                v-for="(val, idx) in comparisonResult.comparison.material?.values"
                :key="idx"
              >
                {{ val }}
              </td>
            </tr>
            <tr>
              <td class="metric-name">
                Post Processor
              </td>
              <td
                v-for="(val, idx) in comparisonResult.comparison.post?.values"
                :key="idx"
              >
                {{ val }}
              </td>
            </tr>
            <tr v-if="comparisonResult.comparison.predicted_time_s">
              <td class="metric-name">
                Predicted Time
              </td>
              <td 
                v-for="(val, idx) in comparisonResult.comparison.predicted_time_s.values" 
                :key="idx"
                :class="winnerClass(idx, comparisonResult.comparison.predicted_time_s.winner)"
              >
                {{ val !== null ? formatTime(val) : '—' }}
                <span
                  v-if="idx === comparisonResult.comparison.predicted_time_s.winner"
                  class="winner-badge"
                >✓</span>
              </td>
            </tr>
            <tr v-if="comparisonResult.comparison.energy_j">
              <td class="metric-name">
                Energy (J)
              </td>
              <td 
                v-for="(val, idx) in comparisonResult.comparison.energy_j.values" 
                :key="idx"
                :class="winnerClass(idx, comparisonResult.comparison.energy_j.winner)"
              >
                {{ val !== null ? val.toFixed(1) : '—' }}
                <span
                  v-if="idx === comparisonResult.comparison.energy_j.winner"
                  class="winner-badge"
                >✓</span>
              </td>
            </tr>
            <tr v-if="comparisonResult.comparison.move_count">
              <td class="metric-name">
                Move Count
              </td>
              <td 
                v-for="(val, idx) in comparisonResult.comparison.move_count.values" 
                :key="idx"
                :class="winnerClass(idx, comparisonResult.comparison.move_count.winner)"
              >
                {{ val !== null ? val : '—' }}
                <span
                  v-if="idx === comparisonResult.comparison.move_count.winner"
                  class="winner-badge"
                >✓</span>
              </td>
            </tr>
            <tr v-if="comparisonResult.comparison.issue_count">
              <td class="metric-name">
                Issue Count
              </td>
              <td 
                v-for="(val, idx) in comparisonResult.comparison.issue_count.values" 
                :key="idx"
                :class="winnerClass(idx, comparisonResult.comparison.issue_count.winner)"
              >
                {{ val !== null ? val : '—' }}
                <span
                  v-if="idx === comparisonResult.comparison.issue_count.winner"
                  class="winner-badge"
                >✓</span>
              </td>
            </tr>
            <tr v-if="comparisonResult.comparison.max_deviation_pct">
              <td class="metric-name">
                Max Deviation (%)
              </td>
              <td 
                v-for="(val, idx) in comparisonResult.comparison.max_deviation_pct.values" 
                :key="idx"
                :class="winnerClass(idx, comparisonResult.comparison.max_deviation_pct.winner)"
              >
                {{ val !== null ? val.toFixed(2) : '—' }}
                <span
                  v-if="idx === comparisonResult.comparison.max_deviation_pct.winner"
                  class="winner-badge"
                >✓</span>
              </td>
            </tr>
            <tr>
              <td class="metric-name">
                Notes
              </td>
              <td
                v-for="(val, idx) in comparisonResult.comparison.notes?.values"
                :key="idx"
                class="notes-cell"
              >
                {{ val || '—' }}
              </td>
            </tr>
            <tr>
              <td class="metric-name">
                Tags
              </td>
              <td
                v-for="(val, idx) in comparisonResult.comparison.tags?.values"
                :key="idx"
              >
                <span v-if="val.length === 0">—</span>
                <span
                  v-else
                  class="tag-list"
                >
                  <span
                    v-for="tag in val"
                    :key="tag"
                    class="tag"
                  >#{{ tag }}</span>
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { api } from '@/services/apiBase';
import { onMounted, ref } from 'vue'

const jobs = ref<any[]>([])
const selectedIds = ref<string[]>([])
const comparisonResult = ref<any>(null)
const loading = ref(false)
const comparing = ref(false)
const exporting = ref(false)
const error = ref<string | null>(null)

async function refreshJobs() {
  loading.value = true
  error.value = null
  try {
    const resp = await api('/api/cam/job-int/log')
    if (!resp.ok) throw new Error(await resp.text())
    const data = await resp.json()
    jobs.value = data.items || []
  } catch (err: any) {
    error.value = err?.message ?? String(err)
  } finally {
    loading.value = false
  }
}

async function compare() {
  if (selectedIds.value.length < 2 || selectedIds.value.length > 4) return
  
  comparing.value = true
  error.value = null
  try {
    const idsParam = selectedIds.value.join(',')
    const resp = await api(`/api/cnc/jobs/compare?ids=${encodeURIComponent(idsParam)}`)
    if (!resp.ok) throw new Error(await resp.text())
    comparisonResult.value = await resp.json()
  } catch (err: any) {
    error.value = err?.message ?? String(err)
  } finally {
    comparing.value = false
  }
}

function clearSelection() {
  selectedIds.value = []
}

function backToSelection() {
  comparisonResult.value = null
}

async function exportCsv() {
  if (!comparisonResult.value) return
  
  exporting.value = true
  try {
    const csv = generateCsv(comparisonResult.value)
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `comparison_${Date.now()}.csv`
    a.click()
    URL.revokeObjectURL(url)
  } catch (err: any) {
    alert(err?.message ?? String(err))
  } finally {
    exporting.value = false
  }
}

function generateCsv(result: any): string {
  const rows: string[][] = []
  
  // Header
  const header = ['Metric', ...result.jobs.map((j: any, idx: number) => `Job ${idx + 1} (${j.job_name || j.run_id.slice(0, 8)})`)]
  rows.push(header)
  
  // Metrics
  const comp = result.comparison
  if (comp.machine) rows.push(['Machine', ...comp.machine.values])
  if (comp.material) rows.push(['Material', ...comp.material.values])
  if (comp.post) rows.push(['Post Processor', ...comp.post.values])
  if (comp.predicted_time_s) rows.push(['Predicted Time (s)', ...comp.predicted_time_s.values.map((v: any) => v ?? '—')])
  if (comp.energy_j) rows.push(['Energy (J)', ...comp.energy_j.values.map((v: any) => v?.toFixed(1) ?? '—')])
  if (comp.move_count) rows.push(['Move Count', ...comp.move_count.values.map((v: any) => v ?? '—')])
  if (comp.issue_count) rows.push(['Issue Count', ...comp.issue_count.values.map((v: any) => v ?? '—')])
  if (comp.max_deviation_pct) rows.push(['Max Deviation (%)', ...comp.max_deviation_pct.values.map((v: any) => v?.toFixed(2) ?? '—')])
  if (comp.notes) rows.push(['Notes', ...comp.notes.values.map((v: any) => v || '—')])
  if (comp.tags) rows.push(['Tags', ...comp.tags.values.map((v: any[]) => v.join(', ') || '—')])
  
  return rows.map(row => row.map(escapeCSV).join(',')).join('\n')
}

function escapeCSV(val: any): string {
  const str = String(val)
  if (str.includes(',') || str.includes('"') || str.includes('\n')) {
    return `"${str.replace(/"/g, '""')}"`
  }
  return str
}

function formatTime(seconds: number): string {
  if (seconds < 60) return `${seconds.toFixed(1)}s`
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}m ${secs}s`
}

function issueClass(count: number): string {
  if (count === 0) return 'no-issues'
  if (count <= 2) return 'minor-issues'
  return 'major-issues'
}

function winnerClass(idx: number, winnerIdx: number | null | undefined): string {
  return idx === winnerIdx ? 'winner' : ''
}

onMounted(() => {
  refreshJobs()
})
</script>

<style scoped>
.compare-panel {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
  gap: 20px;
}

.panel-header h3 {
  margin: 0 0 4px 0;
  font-size: 20px;
  font-weight: 600;
}

.panel-header p {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.header-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

button {
  padding: 8px 16px;
  border-radius: 4px;
  border: none;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.primary {
  background: #4f46e5;
  color: white;
}

.primary:hover:not(:disabled) {
  background: #4338ca;
}

.secondary {
  background: #e5e7eb;
  color: #374151;
}

.secondary:hover:not(:disabled) {
  background: #d1d5db;
}

.refresh {
  background: transparent;
  color: #4f46e5;
  border: 1px solid #4f46e5;
}

.refresh:hover:not(:disabled) {
  background: #f0f0ff;
}

.error {
  color: #dc2626;
  background: #fef2f2;
  padding: 12px;
  border-radius: 4px;
  margin-bottom: 16px;
}

.job-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 400px;
  overflow-y: auto;
}

.job-row {
  border: 2px solid #e5e7eb;
  border-radius: 6px;
  transition: all 0.2s;
}

.job-row.selected {
  border-color: #4f46e5;
  background: #f0f0ff;
}

.checkbox-label {
  display: flex;
  align-items: flex-start;
  padding: 12px;
  cursor: pointer;
  gap: 12px;
}

.checkbox-label input[type="checkbox"] {
  margin-top: 4px;
  cursor: pointer;
}

.job-info {
  flex: 1;
}

.job-name {
  font-weight: 600;
  margin-bottom: 4px;
}

.job-meta {
  display: flex;
  gap: 12px;
  font-size: 13px;
  color: #666;
}

.no-issues { color: #059669; font-weight: 500; }
.minor-issues { color: #d97706; }
.major-issues { color: #dc2626; font-weight: 500; }

.empty {
  text-align: center;
  color: #9ca3af;
  padding: 40px 20px;
  font-style: italic;
}

.comparison-view {
  margin-top: 20px;
}

.comparison-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.comparison-header h4 {
  margin: 0;
  font-size: 18px;
}

.comparison-actions {
  display: flex;
  gap: 8px;
}

.comparison-table-wrapper {
  overflow-x: auto;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
}

.comparison-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.comparison-table th {
  background: #f9fafb;
  padding: 12px;
  text-align: left;
  font-weight: 600;
  border-bottom: 2px solid #e5e7eb;
}

.comparison-table td {
  padding: 12px;
  border-bottom: 1px solid #f3f4f6;
}

.metric-name {
  font-weight: 500;
  background: #fafafa;
  white-space: nowrap;
}

.job-id {
  font-size: 11px;
  color: #6b7280;
  font-weight: normal;
  margin-top: 2px;
}

.winner {
  background: #d1fae5;
  font-weight: 600;
  position: relative;
}

.winner-badge {
  color: #059669;
  margin-left: 4px;
  font-weight: bold;
}

.notes-cell {
  max-width: 200px;
  white-space: normal;
  word-wrap: break-word;
  font-size: 13px;
}

.tag-list {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.tag {
  background: #e0e7ff;
  color: #4338ca;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 12px;
}
</style>
