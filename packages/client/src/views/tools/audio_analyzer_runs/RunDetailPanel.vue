<template>
  <section class="detail-panel card">
    <template v-if="!runId">
      <div class="empty-state">
        <p>Select a run from the list to view details.</p>
      </div>
    </template>
    <template v-else-if="loading">
      <div class="muted">
        Loading run details...
      </div>
    </template>
    <template v-else-if="error">
      <div class="error-box">
        {{ error }}
      </div>
    </template>
    <template v-else-if="data">
      <h2>Run Details</h2>
      <div class="detail-meta">
        <div class="meta-row">
          <span class="meta-label">Run ID:</span>
          <code>{{ data.run_id }}</code>
        </div>
        <div class="meta-row">
          <span class="meta-label">Created:</span>
          <span>{{ formatDate(data.created_at_utc) }}</span>
        </div>
        <div class="meta-row">
          <span class="meta-label">Status:</span>
          <code :class="data.status.toLowerCase()">{{ data.status }}</code>
        </div>
        <div
          v-if="data.session_id"
          class="meta-row"
        >
          <span class="meta-label">Session:</span>
          <span>{{ data.session_id }}</span>
        </div>
        <div
          v-if="data.batch_label"
          class="meta-row"
        >
          <span class="meta-label">Batch:</span>
          <span>{{ data.batch_label }}</span>
        </div>
      </div>

      <h3>Attachments ({{ data.attachment_count }})</h3>
      <table
        v-if="data.attachments?.length"
        class="tbl"
      >
        <thead>
          <tr>
            <th>Filename</th>
            <th>Kind</th>
            <th>Size</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="att in data.attachments"
            :key="att.sha256"
          >
            <td
              class="mono filename-cell"
              :title="att.filename ?? undefined"
            >
              {{ att.filename }}
            </td>
            <td><code class="kind-badge">{{ att.kind }}</code></td>
            <td class="mono">
              {{ formatSize(att.size_bytes ?? 0) }}
            </td>
            <td class="actions-cell">
              <a
                v-if="att.kind === 'viewer_pack'"
                class="btn btn-sm"
                :href="`/tools/audio-analyzer?sha256=${att.sha256}`"
              >
                Open
              </a>
              <a
                class="btn btn-sm"
                :href="getDownloadUrl(att.sha256)"
                download
              >
                Download
              </a>
            </td>
          </tr>
        </tbody>
      </table>
      <div
        v-else
        class="muted"
      >
        No attachments.
      </div>
    </template>
  </section>
</template>

<script setup lang="ts">
import {
  getDownloadUrl,
  formatSize,
} from "@/sdk/endpoints/rmosAcoustics"

interface Attachment {
  sha256: string
  filename?: string | null
  kind: string | null
  mime?: string | null
  size_bytes?: number | null
  created_at_utc?: string | null
  download_url?: string
}

interface RunDetail {
  run_id: string
  created_at_utc: string
  status: string
  session_id?: string | null
  batch_label?: string | null
  event_type?: string | null
  attachment_count: number
  attachments?: Attachment[]
}

defineProps<{
  runId: string | null
  data: RunDetail | null
  loading: boolean
  error: string
}>()

function formatDate(iso: string): string {
  try {
    const d = new Date(iso)
    return d.toLocaleString()
  } catch {
    return iso
  }
}
</script>

<style scoped>
.detail-panel {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  padding: 12px;
  min-height: 400px;
}

.detail-panel h2 {
  margin: 0 0 12px 0;
  font-size: 1rem;
}

.detail-panel h3 {
  margin: 16px 0 8px 0;
  font-size: 0.95rem;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
  opacity: 0.6;
}

.detail-meta {
  display: grid;
  gap: 6px;
  margin-bottom: 16px;
}

.meta-row {
  display: flex;
  gap: 8px;
  font-size: 0.9rem;
}

.meta-label {
  opacity: 0.7;
  min-width: 80px;
}

.tbl {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}

.tbl th,
.tbl td {
  padding: 8px 10px;
  text-align: left;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.tbl th {
  opacity: 0.7;
  font-weight: 500;
}

.mono {
  font-family: monospace;
}

.filename-cell {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.kind-badge {
  font-size: 0.75rem;
  padding: 2px 6px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
}

.actions-cell {
  display: flex;
  gap: 6px;
}

.muted {
  opacity: 0.6;
}

.error-box {
  padding: 8px 12px;
  background: rgba(255, 0, 0, 0.12);
  border: 1px solid rgba(255, 0, 0, 0.25);
  border-radius: 8px;
  font-size: 0.9rem;
}

.btn {
  padding: 6px 12px;
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  background: rgba(255, 255, 255, 0.08);
  color: inherit;
  cursor: pointer;
  font-size: 0.85rem;
  text-decoration: none;
}

.btn:hover {
  background: rgba(255, 255, 255, 0.12);
}

.btn-sm {
  padding: 4px 10px;
  font-size: 0.8rem;
}

code.ok {
  background: rgba(66, 184, 131, 0.2);
  color: #42b883;
}

code.error {
  background: rgba(255, 0, 0, 0.2);
  color: #ff6b6b;
}
</style>
