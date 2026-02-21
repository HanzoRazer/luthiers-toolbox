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
    <JobSelectionList
      v-if="!comparisonResult"
      v-model="selectedIds"
      :jobs="jobs"
      :loading="loading"
    />

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

      <ComparisonTable :result="comparisonResult" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { api } from '@/services/apiBase';
import { onMounted, ref } from 'vue'
import JobSelectionList from './compare_runs_panel/JobSelectionList.vue'
import ComparisonTable from './compare_runs_panel/ComparisonTable.vue'

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

</style>
