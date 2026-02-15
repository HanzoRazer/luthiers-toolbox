<!-- Bundle #13 (Part A) - RMOS Studio CNC History View -->

<template>
  <div class="cnc-history-view">
    <h1>RMOS Studio – CNC History</h1>

    <div class="controls">
      <label>
        Show last
        <input
          v-model.number="limit"
          type="number"
          min="1"
          max="500"
        >
        jobs
      </label>
      <button
        :disabled="loading"
        @click="loadHistory"
      >
        Refresh
      </button>
      <span v-if="loading">Loading...</span>
    </div>

    <p
      v-if="error"
      class="error"
    >
      {{ error }}
    </p>

    <table
      v-if="items.length"
      class="history-table"
    >
      <thead>
        <tr>
          <th>Job ID</th>
          <th>Date/Time</th>
          <th>Status</th>
          <th>Ring ID</th>
          <th>Material</th>
          <th>Safety</th>
          <th>Runtime (s)</th>
          <th>Report</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="item in items"
          :key="item.job_id"
          :class="rowClass(item)"
          @click="goToDetail(item.job_id)"
        >
          <td class="mono job-id-cell">
            {{ item.job_id }}
          </td>
          <td>
            <span v-if="item.created_at">
              {{ formatDate(item.created_at) }}
            </span>
            <span v-else>—</span>
          </td>
          <td>
            <!-- Status badge -->
            <span :class="['badge', statusClass(item.status)]">
              {{ item.status }}
            </span>
          </td>
          <td class="mono">
            {{ item.ring_id ?? '—' }}
          </td>
          <td>{{ item.material ?? '—' }}</td>
          <td>
            <!-- Safety + risk badge -->
            <div class="safety-cell">
              <span
                v-if="item.safety_decision"
                class="safety-decision"
              >
                {{ item.safety_decision }}
              </span>
              <span
                v-if="item.safety_risk_level"
                :class="['badge', riskClass(item.safety_risk_level)]"
              >
                {{ item.safety_risk_level }}
              </span>
              <span
                v-else
                class="badge badge-na"
              >n/a</span>
            </div>
          </td>
          <td>
            <span v-if="item.runtime_sec != null">
              {{ item.runtime_sec.toFixed(1) }}
            </span>
            <span v-else>—</span>
          </td>
          <td @click.stop>
            <button
              type="button"
              @click="downloadReport(item.job_id)"
            >
              PDF
            </button>
          </td>
        </tr>
      </tbody>
    </table>

    <p
      v-else-if="!loading && !error"
      class="no-data"
    >
      No CNC jobs found.
    </p>
  </div>
</template>

<script setup lang="ts">
import { api } from '@/services/apiBase';
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

interface CNCHistoryItem {
  job_id: string
  created_at: string | null
  status: string
  ring_id: number | null
  material: string | null
  safety_decision: string | null
  safety_risk_level: string | null
  runtime_sec: number | null
  pattern_id: string | null
}

const items = ref<CNCHistoryItem[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const limit = ref(50)
const router = useRouter()

async function loadHistory() {
  loading.value = true
  error.value = null
  try {
    const resp = await api(`/api/rmos/rosette/cnc-history?limit=${limit.value}`)
    if (!resp.ok) throw new Error(`History request failed: ${resp.status}`)
    const data = await resp.json()
    items.value = data.items ?? []
  } catch (e: any) {
    error.value = e?.message ?? String(e)
  } finally {
    loading.value = false
  }
}

function downloadReport(jobId: string) {
  const url = `/api/rmos/rosette/operator-report-pdf/${encodeURIComponent(jobId)}`
  window.open(url, '_blank')
}

function formatDate(isoStr: string): string {
  try {
    const d = new Date(isoStr)
    return d.toLocaleString()
  } catch {
    return isoStr
  }
}

// ---- Badge helpers ----

function statusClass(status: string): string {
  const s = status.toLowerCase()
  if (s === 'completed' || s === 'success') return 'badge-status-ok'
  if (s === 'running' || s === 'in-progress') return 'badge-status-running'
  if (s === 'failed' || s === 'error') return 'badge-status-failed'
  return 'badge-status-other'
}

function riskClass(risk: string): string {
  const r = risk.toLowerCase()
  if (r === 'low') return 'badge-risk-low'
  if (r === 'medium') return 'badge-risk-medium'
  if (r === 'high') return 'badge-risk-high'
  return 'badge-risk-na'
}

function rowClass(item: CNCHistoryItem): string[] {
  const classes: string[] = ['row-clickable']
  const risk = (item.safety_risk_level || '').toLowerCase()
  if (risk === 'high') classes.push('row-risk-high')
  else if (risk === 'medium') classes.push('row-risk-medium')
  else if (risk === 'low') classes.push('row-risk-low')
  else classes.push('row-risk-na')
  return classes
}

function goToDetail(jobId: string) {
  router.push({ name: 'RmosCncJobDetail', params: { jobId } })
}

onMounted(() => {
  loadHistory()
})
</script>

<style scoped>
.cnc-history-view {
  padding: 1rem;
  font-size: 0.9rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.controls {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.controls input {
  width: 4rem;
  padding: 0.2rem 0.3rem;
  font-size: 0.85rem;
}

.history-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8rem;
}

.history-table th,
.history-table td {
  border: 1px solid #ddd;
  padding: 0.3rem 0.4rem;
}

.history-table th {
  background-color: #f8f8f8;
}

.mono {
  font-family: monospace;
}

.error {
  color: #c00;
}

/* Row-level tints + clickable affordance */
.row-clickable {
  cursor: pointer;
}

.row-clickable:hover {
  filter: brightness(0.98);
}

.row-risk-high {
  background-color: #fff0f0;
}

.row-risk-medium {
  background-color: #fff9ea;
}

.row-risk-low {
  background-color: #f5fbf7;
}

.row-risk-na {
  background-color: #f7f8fa;
}

.job-id-cell {
  white-space: nowrap;
}

/* ---- Badges ---- */

.badge {
  display: inline-block;
  padding: 0.12rem 0.4rem;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  border: 1px solid transparent;
}

/* Status badges */
.badge-status-ok {
  background-color: #e6f6ea;
  color: #1d7a36;
  border-color: #aadaaf;
}

.badge-status-running {
  background-color: #fff8e0;
  color: #8b6b00;
  border-color: #f3d880;
}

.badge-status-failed {
  background-color: #fde7e7;
  color: #b11a1a;
  border-color: #f3aaaa;
}

.badge-status-other {
  background-color: #eef0f4;
  color: #444;
  border-color: #d0d4db;
}

/* Risk badges */
.badge-risk-low {
  background-color: #e5faf2;
  color: #117a4b;
  border-color: #abe0c6;
}

.badge-risk-medium {
  background-color: #fff4e0;
  color: #9b6200;
  border-color: #f2d29a;
}

.badge-risk-high {
  background-color: #ffe7e5;
  color: #b3261e;
  border-color: #f3b0a9;
}

.badge-risk-na,
.badge-na {
  background-color: #eef0f4;
  color: #666;
  border-color: #d0d4db;
}

/* Safety cell layout */
.safety-cell {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.safety-decision {
  font-size: 0.78rem;
}
</style>
