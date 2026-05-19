<template>
  <div class="page">
    <header class="header">
      <h1>Ingest Events</h1>
      <p class="sub">
        Audit trail of all acoustics bundle import attempts. Shows accepted, rejected, and error events.
      </p>
    </header>

    <!-- Summary Cards -->
    <div class="summary-cards">
      <div class="summary-card accepted">
        <span class="count">{{ counts?.accepted ?? '—' }}</span>
        <span class="label">Accepted</span>
      </div>
      <div class="summary-card rejected">
        <span class="count">{{ counts?.rejected ?? '—' }}</span>
        <span class="label">Rejected</span>
      </div>
      <div class="summary-card quarantined">
        <span class="count">{{ counts?.quarantined ?? '—' }}</span>
        <span class="label">Quarantined</span>
      </div>
      <div class="summary-card error">
        <span class="count">{{ counts?.error ?? '—' }}</span>
        <span class="label">Errors</span>
      </div>
    </div>

    <div class="layout">
      <!-- Events List Panel -->
      <section class="events-panel card">
        <h2>Recent Events</h2>

        <!-- Filters -->
        <div class="filters">
          <label>
            <span>Outcome</span>
            <select v-model="outcomeFilter" @change="loadEvents">
              <option value="">All</option>
              <option value="accepted">Accepted</option>
              <option value="rejected">Rejected</option>
              <option value="quarantined">Quarantined</option>
              <option value="error">Error</option>
            </select>
          </label>
          <label>
            <span>Session ID</span>
            <input
              v-model="sessionIdFilter"
              type="text"
              placeholder="Filter..."
              @input="debouncedLoad"
            />
          </label>
          <label>
            <span>Batch Label</span>
            <input
              v-model="batchLabelFilter"
              type="text"
              placeholder="Filter..."
              @input="debouncedLoad"
            />
          </label>
        </div>

        <div v-if="eventsLoading" class="muted">Loading events...</div>
        <div v-else-if="eventsError" class="error-box">{{ eventsError }}</div>
        <div v-else-if="!eventsData?.events?.length" class="muted">
          No ingest events found. Import a viewer_pack to see activity here.
        </div>
        <div v-else class="events-list">
          <div
            v-for="event in eventsData.events"
            :key="event.event_id"
            class="event-item"
            :class="{ selected: selectedEventId === event.event_id }"
            @click="selectEvent(event.event_id)"
          >
            <div class="event-header">
              <span class="event-date">{{ formatDate(event.timestamp) }}</span>
              <code class="event-outcome" :class="event.outcome">{{ event.outcome }}</code>
            </div>
            <div class="event-meta">
              <span v-if="event.filename" class="event-filename">📦 {{ event.filename }}</span>
              <span v-if="event.session_id" class="event-session">{{ event.session_id }}</span>
            </div>
            <div v-if="event.rejection_reason" class="event-reason">
              <code>{{ event.rejection_reason }}</code>
            </div>
            <div v-if="event.run_id" class="event-run">
              → Run: <code>{{ event.run_id.slice(0, 12) }}...</code>
            </div>
          </div>

          <button
            v-if="eventsData.total_returned >= limit"
            class="btn load-more"
            @click="loadMore"
          >
            Load More
          </button>
        </div>
      </section>

      <!-- Event Detail Panel -->
      <section class="detail-panel card">
        <template v-if="!selectedEventId">
          <div class="empty-state">
            <p>Select an event from the list to view details.</p>
          </div>
        </template>
        <template v-else-if="detailLoading">
          <div class="muted">Loading event details...</div>
        </template>
        <template v-else-if="detailError">
          <div class="error-box">{{ detailError }}</div>
        </template>
        <template v-else-if="detailData">
          <h2>Event Details</h2>
          
          <!-- Outcome Badge -->
          <div class="outcome-badge" :class="detailData.outcome">
            {{ detailData.outcome.toUpperCase() }}
          </div>

          <div class="detail-meta">
            <div class="meta-row">
              <span class="meta-label">Event ID:</span>
              <code>{{ detailData.event_id }}</code>
            </div>
            <div class="meta-row">
              <span class="meta-label">Timestamp:</span>
              <span>{{ formatDate(detailData.timestamp) }}</span>
            </div>
            <div v-if="detailData.filename" class="meta-row">
              <span class="meta-label">Filename:</span>
              <span>{{ detailData.filename }}</span>
            </div>
            <div v-if="detailData.session_id" class="meta-row">
              <span class="meta-label">Session ID:</span>
              <code>{{ detailData.session_id }}</code>
            </div>
            <div v-if="detailData.batch_label" class="meta-row">
              <span class="meta-label">Batch Label:</span>
              <code>{{ detailData.batch_label }}</code>
            </div>
            <div v-if="detailData.bundle_sha256" class="meta-row">
              <span class="meta-label">Bundle SHA256:</span>
              <code class="sha">{{ detailData.bundle_sha256 }}</code>
            </div>
            <div v-if="detailData.bundle_size_bytes" class="meta-row">
              <span class="meta-label">Bundle Size:</span>
              <span>{{ formatBytes(detailData.bundle_size_bytes) }}</span>
            </div>
          </div>

          <!-- Rejection Details (if rejected/error) -->
          <div v-if="detailData.rejection_reason" class="rejection-section">
            <h3>Rejection Details</h3>
            <div class="meta-row">
              <span class="meta-label">Reason:</span>
              <code class="rejection-reason">{{ detailData.rejection_reason }}</code>
            </div>
            <div v-if="detailData.rejection_message" class="meta-row">
              <span class="meta-label">Message:</span>
              <span class="rejection-message">{{ detailData.rejection_message }}</span>
            </div>
            <div v-if="detailData.errors_count != null" class="meta-row">
              <span class="meta-label">Errors:</span>
              <span>{{ detailData.errors_count }}</span>
            </div>
            <div v-if="detailData.warnings_count != null" class="meta-row">
              <span class="meta-label">Warnings:</span>
              <span>{{ detailData.warnings_count }}</span>
            </div>
            <div v-if="detailData.error_excerpt?.length" class="error-excerpt">
              <h4>Error Excerpt</h4>
              <ul>
                <li v-for="(err, idx) in detailData.error_excerpt" :key="idx">
                  {{ err }}
                </li>
              </ul>
            </div>
          </div>

          <!-- Success Details (if accepted) -->
          <div v-if="detailData.outcome === 'accepted'" class="success-section">
            <h3>Import Details</h3>
            <div v-if="detailData.run_id" class="meta-row">
              <span class="meta-label">Run ID:</span>
              <code>{{ detailData.run_id }}</code>
              <router-link
                :to="{ name: 'RmosRunViewer', params: { runId: detailData.run_id } }"
                class="btn btn-sm"
              >
                View Run →
              </router-link>
            </div>
            <div v-if="detailData.attachments_written != null" class="meta-row">
              <span class="meta-label">Attachments Written:</span>
              <span>{{ detailData.attachments_written }}</span>
            </div>
            <div v-if="detailData.attachments_deduped != null" class="meta-row">
              <span class="meta-label">Attachments Deduped:</span>
              <span>{{ detailData.attachments_deduped }}</span>
            </div>
          </div>

          <!-- Manifest Info -->
          <div v-if="detailData.manifest_event_type || detailData.manifest_tool_id" class="manifest-section">
            <h3>Manifest Info</h3>
            <div v-if="detailData.manifest_event_type" class="meta-row">
              <span class="meta-label">Event Type:</span>
              <code>{{ detailData.manifest_event_type }}</code>
            </div>
            <div v-if="detailData.manifest_tool_id" class="meta-row">
              <span class="meta-label">Tool ID:</span>
              <code>{{ detailData.manifest_tool_id }}</code>
            </div>
            <div v-if="detailData.bundle_id" class="meta-row">
              <span class="meta-label">Bundle ID:</span>
              <code>{{ detailData.bundle_id }}</code>
            </div>
          </div>

          <!-- Request Metadata -->
          <div v-if="detailData.request_id || detailData.client_ip" class="request-section">
            <h3>Request Metadata</h3>
            <div v-if="detailData.request_id" class="meta-row">
              <span class="meta-label">Request ID:</span>
              <code>{{ detailData.request_id }}</code>
            </div>
            <div v-if="detailData.client_ip" class="meta-row">
              <span class="meta-label">Client IP:</span>
              <code>{{ detailData.client_ip }}</code>
            </div>
          </div>
        </template>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useDebounceFn } from '@vueuse/core'

// Types
interface IngestEventSummary {
  event_id: string
  timestamp: string
  outcome: string
  session_id?: string
  batch_label?: string
  filename?: string
  bundle_sha256?: string
  rejection_reason?: string
  run_id?: string
}

interface IngestEventDetail {
  event_id: string
  timestamp: string
  outcome: string
  session_id?: string
  batch_label?: string
  filename?: string
  bundle_sha256?: string
  bundle_id?: string
  manifest_event_type?: string
  manifest_tool_id?: string
  rejection_reason?: string
  rejection_message?: string
  errors_count?: number
  warnings_count?: number
  error_excerpt?: string[]
  run_id?: string
  attachments_written?: number
  attachments_deduped?: number
  request_id?: string
  client_ip?: string
  bundle_size_bytes?: number
}

interface IngestEventsResponse {
  events: IngestEventSummary[]
  total_returned: number
  limit: number
  offset: number
}

interface IngestEventCounts {
  accepted: number
  rejected: number
  quarantined: number
  error: number
  total: number
}

// State
const outcomeFilter = ref('')
const sessionIdFilter = ref('')
const batchLabelFilter = ref('')
const limit = ref(50)
const offset = ref(0)

const eventsLoading = ref(false)
const eventsError = ref<string | null>(null)
const eventsData = ref<IngestEventsResponse | null>(null)

const counts = ref<IngestEventCounts | null>(null)

const selectedEventId = ref<string | null>(null)
const detailLoading = ref(false)
const detailError = ref<string | null>(null)
const detailData = ref<IngestEventDetail | null>(null)

// API calls
async function loadCounts() {
  try {
    const res = await fetch('/api/rmos/acoustics/ingest-events/counts')
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    counts.value = await res.json()
  } catch (e: any) {
    console.error('Failed to load counts:', e)
  }
}

async function loadEvents() {
  eventsLoading.value = true
  eventsError.value = null
  
  try {
    const params = new URLSearchParams()
    if (outcomeFilter.value) params.set('outcome', outcomeFilter.value)
    if (sessionIdFilter.value) params.set('session_id', sessionIdFilter.value)
    if (batchLabelFilter.value) params.set('batch_label', batchLabelFilter.value)
    params.set('limit', limit.value.toString())
    params.set('offset', offset.value.toString())
    
    const res = await fetch(`/api/rmos/acoustics/ingest-events?${params}`)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    eventsData.value = await res.json()
  } catch (e: any) {
    eventsError.value = e.message || 'Failed to load events'
  } finally {
    eventsLoading.value = false
  }
}

const debouncedLoad = useDebounceFn(() => {
  offset.value = 0
  loadEvents()
}, 300)

async function loadMore() {
  offset.value += limit.value
  await loadEvents()
}

async function selectEvent(eventId: string) {
  selectedEventId.value = eventId
  detailLoading.value = true
  detailError.value = null
  detailData.value = null
  
  try {
    const res = await fetch(`/api/rmos/acoustics/ingest-events/${eventId}`)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    detailData.value = await res.json()
  } catch (e: any) {
    detailError.value = e.message || 'Failed to load event details'
  } finally {
    detailLoading.value = false
  }
}

// Formatting helpers
function formatDate(isoString: string): string {
  if (!isoString) return '—'
  const d = new Date(isoString)
  return d.toLocaleString()
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

// Lifecycle
onMounted(() => {
  loadCounts()
  loadEvents()
})
</script>

<style scoped>
.page {
  padding: 1.5rem;
  max-width: 1400px;
  margin: 0 auto;
}

.header {
  margin-bottom: 1.5rem;
}

.header h1 {
  margin: 0 0 0.5rem;
  font-size: 1.75rem;
}

.sub {
  color: var(--text-muted, #666);
  margin: 0;
}

/* Summary Cards */
.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.summary-card {
  padding: 1rem;
  border-radius: 8px;
  text-align: center;
  background: var(--card-bg, #fff);
  border: 1px solid var(--border-color, #ddd);
}

.summary-card .count {
  display: block;
  font-size: 2rem;
  font-weight: 700;
  line-height: 1.2;
}

.summary-card .label {
  font-size: 0.85rem;
  color: var(--text-muted, #666);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.summary-card.accepted .count { color: #22c55e; }
.summary-card.rejected .count { color: #ef4444; }
.summary-card.quarantined .count { color: #f59e0b; }
.summary-card.error .count { color: #6b7280; }

/* Layout */
.layout {
  display: grid;
  grid-template-columns: 400px 1fr;
  gap: 1.5rem;
}

@media (max-width: 900px) {
  .layout {
    grid-template-columns: 1fr;
  }
}

.card {
  background: var(--card-bg, #fff);
  border: 1px solid var(--border-color, #ddd);
  border-radius: 8px;
  padding: 1rem;
}

.card h2 {
  margin: 0 0 1rem;
  font-size: 1.1rem;
}

/* Filters */
.filters {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.filters label {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.85rem;
}

.filters label span {
  color: var(--text-muted, #666);
}

.filters input,
.filters select {
  padding: 0.4rem 0.6rem;
  border: 1px solid var(--border-color, #ddd);
  border-radius: 4px;
  font-size: 0.9rem;
}

/* Events List */
.events-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-height: 600px;
  overflow-y: auto;
}

.event-item {
  padding: 0.75rem;
  border: 1px solid var(--border-color, #ddd);
  border-radius: 6px;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
}

.event-item:hover {
  border-color: var(--primary, #3b82f6);
  background: var(--hover-bg, #f8fafc);
}

.event-item.selected {
  border-color: var(--primary, #3b82f6);
  background: var(--selected-bg, #eff6ff);
}

.event-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.25rem;
}

.event-date {
  font-size: 0.8rem;
  color: var(--text-muted, #666);
}

.event-outcome {
  font-size: 0.75rem;
  padding: 0.15rem 0.4rem;
  border-radius: 3px;
  font-weight: 500;
}

.event-outcome.accepted { background: #dcfce7; color: #166534; }
.event-outcome.rejected { background: #fee2e2; color: #991b1b; }
.event-outcome.quarantined { background: #fef3c7; color: #92400e; }
.event-outcome.error { background: #f3f4f6; color: #374151; }

.event-meta {
  font-size: 0.85rem;
  color: var(--text-muted, #666);
  margin-bottom: 0.25rem;
}

.event-filename {
  display: block;
  font-family: monospace;
  font-size: 0.8rem;
}

.event-reason code {
  font-size: 0.75rem;
  color: #991b1b;
}

.event-run {
  font-size: 0.8rem;
  color: var(--text-muted, #666);
}

/* Detail Panel */
.detail-panel {
  min-height: 400px;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 300px;
  color: var(--text-muted, #666);
}

.outcome-badge {
  display: inline-block;
  padding: 0.4rem 0.8rem;
  border-radius: 4px;
  font-weight: 600;
  font-size: 0.9rem;
  margin-bottom: 1rem;
}

.outcome-badge.accepted { background: #dcfce7; color: #166534; }
.outcome-badge.rejected { background: #fee2e2; color: #991b1b; }
.outcome-badge.quarantined { background: #fef3c7; color: #92400e; }
.outcome-badge.error { background: #f3f4f6; color: #374151; }

.detail-meta,
.rejection-section,
.success-section,
.manifest-section,
.request-section {
  margin-bottom: 1.25rem;
}

.detail-meta h3,
.rejection-section h3,
.success-section h3,
.manifest-section h3,
.request-section h3 {
  font-size: 0.95rem;
  margin: 0 0 0.5rem;
  color: var(--text-muted, #666);
  border-bottom: 1px solid var(--border-color, #ddd);
  padding-bottom: 0.25rem;
}

.meta-row {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
  margin: 0.3rem 0;
  font-size: 0.9rem;
}

.meta-label {
  font-weight: 500;
  min-width: 140px;
  color: var(--text-muted, #666);
}

code {
  font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
  font-size: 0.85rem;
  background: var(--code-bg, #f1f5f9);
  padding: 0.1rem 0.3rem;
  border-radius: 3px;
}

code.sha {
  font-size: 0.75rem;
  word-break: break-all;
}

.rejection-reason {
  color: #991b1b;
}

.rejection-message {
  color: #dc2626;
}

.error-excerpt {
  margin-top: 0.75rem;
}

.error-excerpt h4 {
  font-size: 0.85rem;
  margin: 0 0 0.5rem;
}

.error-excerpt ul {
  margin: 0;
  padding-left: 1.25rem;
  font-size: 0.85rem;
  color: #991b1b;
}

/* Buttons */
.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  font-size: 0.9rem;
  cursor: pointer;
  background: var(--primary, #3b82f6);
  color: #fff;
}

.btn:hover {
  opacity: 0.9;
}

.btn.load-more {
  width: 100%;
  margin-top: 0.5rem;
}

.btn-sm {
  padding: 0.25rem 0.5rem;
  font-size: 0.8rem;
  margin-left: 0.5rem;
}

/* Status */
.muted {
  color: var(--text-muted, #666);
  font-style: italic;
}

.error-box {
  padding: 0.75rem;
  background: #fee2e2;
  border: 1px solid #fecaca;
  border-radius: 4px;
  color: #991b1b;
}
</style>
