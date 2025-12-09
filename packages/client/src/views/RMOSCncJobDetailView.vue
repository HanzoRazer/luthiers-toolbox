<!-- Bundle #13 (Part A+) - RMOS CNC Job Detail View -->

<template>
  <div class="job-detail-view">
    <h1>RMOS CNC Job Detail</h1>

    <p class="back-link">
      <router-link to="/rmos/cnc-history">← Back to CNC History</router-link>
    </p>

    <p v-if="loading">Loading job...</p>
    <p v-if="error" class="error">{{ error }}</p>

    <div v-if="job" class="job-layout">
      <section class="card">
        <h2>Job Summary</h2>
        <p>
          <strong>Job ID:</strong> <span class="mono">{{ job.job_id }}</span><br />
          <strong>Status:</strong>
          <span :class="['badge', statusClass(job.status)]">{{ job.status }}</span><br />
          <strong>Ring ID:</strong> {{ job.ring_id ?? '—' }}<br />
          <strong>Material:</strong> {{ job.material ?? '—' }}<br />
          <strong>Pattern ID:</strong> {{ job.pattern_id ?? '—' }}<br />
          <strong>Created:</strong>
          <span v-if="job.created_at">{{ formatDate(job.created_at) }}</span>
          <span v-else>—</span>
        </p>
      </section>

      <section class="card" v-if="job.safety">
        <h2>Safety</h2>
        <p>
          <strong>Decision:</strong> {{ job.safety.decision }}<br />
          <strong>Risk level:</strong>
          <span
            :class="['badge', riskClass(job.safety.risk_level)]"
          >
            {{ job.safety.risk_level }}
          </span><br />
          <strong>Override required:</strong>
          {{ job.safety.requires_override ? 'Yes' : 'No' }}
        </p>
        <div v-if="job.safety.reasons && job.safety.reasons.length">
          <h3>Safety Notes</h3>
          <ul>
            <li v-for="(reason, idx) in job.safety.reasons" :key="idx">
              {{ reason }}
            </li>
          </ul>
        </div>
      </section>

      <section class="card" v-if="job.simulation || job.toolpath_stats">
        <h2>Toolpath & Runtime</h2>

        <p v-if="job.toolpath_stats">
          <strong>Segments:</strong> {{ job.toolpath_stats.segment_count }}<br />
          <strong>Origin (mm):</strong>
          <span v-if="job.toolpath_stats.origin_x_mm != null">
            X = {{ job.toolpath_stats.origin_x_mm.toFixed(2) }},
            Y = {{ job.toolpath_stats.origin_y_mm?.toFixed(2) ?? '—' }}
          </span>
          <span v-else>—</span><br />
          <strong>Rotation (deg):</strong>
          <span v-if="job.toolpath_stats.rotation_deg != null">
            {{ job.toolpath_stats.rotation_deg.toFixed(1) }}
          </span>
          <span v-else>—</span>
        </p>

        <p v-if="job.simulation">
          <strong>Estimated runtime:</strong>
          {{ job.simulation.estimated_runtime_sec.toFixed(1) }} s<br />
          <strong>Passes:</strong> {{ job.simulation.passes }}<br />
          <strong>Max feed:</strong>
          {{ job.simulation.max_feed_mm_per_min.toFixed(0) }} mm/min<br />
          <strong>Envelope OK:</strong> {{ job.simulation.envelope_ok ? 'Yes' : 'No' }}
        </p>
      </section>

      <section class="card">
        <h2>Operator Report</h2>
        <p class="note" v-if="!job?.operator_report_md">
          No operator report stored for this job.
        </p>

        <!-- Render Markdown as HTML -->
        <div
          v-else
          class="report-html"
          v-html="operatorReportHtml"
        ></div>

        <button
          v-if="job?.job_id"
          type="button"
          class="download-button"
          @click="downloadPdf(job.job_id)"
        >
          Download PDF
        </button>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { marked } from 'marked'

interface SafetyModel {
  decision: string
  risk_level: string
  requires_override: boolean
  reasons: string[]
}

interface SimulationModel {
  passes: number
  estimated_runtime_sec: number
  max_feed_mm_per_min: number
  envelope_ok: boolean
}

interface ToolpathStatsModel {
  segment_count: number
  origin_x_mm: number | null
  origin_y_mm: number | null
  rotation_deg: number | null
}

interface CNCJobDetail {
  job_id: string
  pattern_id: string | null
  status: string
  ring_id: number | null
  material: string | null
  created_at: string | null
  safety: SafetyModel | null
  simulation: SimulationModel | null
  toolpath_stats: ToolpathStatsModel | null
  operator_report_md: string | null
  metadata: Record<string, any>
  parameters: Record<string, any>
}

const route = useRoute()
const job = ref<CNCJobDetail | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

// Computed HTML for operator report
const operatorReportHtml = computed(() => {
  const md = job.value?.operator_report_md
  if (!md) return ''
  return marked(md)
})

async function loadJob() {
  const jobId = route.params.jobId as string
  if (!jobId) {
    error.value = 'Missing jobId parameter.'
    return
  }

  loading.value = true
  error.value = null

  try {
    const resp = await fetch(`/api/rmos/rosette/cnc-job/${encodeURIComponent(jobId)}`)
    if (!resp.ok) throw new Error(`Job detail request failed: ${resp.status}`)
    const data = await resp.json()
    job.value = data as CNCJobDetail
  } catch (e: any) {
    error.value = e?.message ?? String(e)
  } finally {
    loading.value = false
  }
}

function downloadPdf(jobId: string) {
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

onMounted(() => {
  loadJob()
})
</script>

<style scoped>
.job-detail-view {
  padding: 1rem;
  font-size: 0.9rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.back-link {
  margin-bottom: 0.5rem;
}

.error {
  color: #c00;
}

.job-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(0, 1.1fr);
  gap: 1rem;
}

.card {
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 0.75rem;
  background-color: #fafbfc;
}

.card h2 {
  margin-top: 0;
  margin-bottom: 0.35rem;
  font-size: 1rem;
}

.card h3 {
  margin-top: 0.6rem;
  margin-bottom: 0.3rem;
  font-size: 0.9rem;
}

.mono {
  font-family: monospace;
}

.report-html {
  background-color: #f5f5f5;
  border-radius: 4px;
  padding: 0.6rem 0.7rem;
  max-height: 300px;
  overflow: auto;
  font-size: 0.85rem;
}

.report-html h1,
.report-html h2,
.report-html h3 {
  margin-top: 0.6rem;
  margin-bottom: 0.25rem;
}

.report-html ul,
.report-html ol {
  margin-left: 1.2rem;
  margin-bottom: 0.4rem;
}

.report-html code {
  font-family: monospace;
  font-size: 0.8rem;
}

.note {
  font-style: italic;
  color: #666;
}

.download-button {
  margin-top: 0.5rem;
  font-size: 0.8rem;
  padding: 0.35rem 0.7rem;
}

/* Reuse badge styles from history view (can be refactored to a global later) */

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

.badge-risk-na {
  background-color: #eef0f4;
  color: #666;
  border-color: #d0d4db;
}
</style>
