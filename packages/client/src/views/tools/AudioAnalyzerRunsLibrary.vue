<template>
  <div class="page">
    <header class="header">
      <h1>Acoustics Runs</h1>
      <p class="sub">
        Browse imports/sessions by run. Click a run to see attachments.
      </p>
    </header>

    <div class="layout">
      <!-- Runs List Panel -->
      <section class="runs-panel card">
        <h2>Recent Runs</h2>

        <!-- Filters -->
        <div class="filters">
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

        <div v-if="runsLoading" class="muted">Loading runs...</div>
        <div v-else-if="runsError" class="error-box">{{ runsError }}</div>
        <div v-else-if="!runsData?.runs?.length" class="muted">
          No runs found. Import a viewer_pack in the Library.
        </div>
        <div v-else class="runs-list">
          <div
            v-for="run in runsData.runs"
            :key="run.run_id"
            class="run-item"
            :class="{ selected: selectedRunId === run.run_id }"
            @click="selectRun(run.run_id)"
          >
            <div class="run-header">
              <span class="run-date">{{ formatDate(run.created_at_utc) }}</span>
              <code class="run-status" :class="run.status.toLowerCase()">{{ run.status }}</code>
            </div>
            <div class="run-meta">
              <span v-if="run.session_id" class="run-session">{{ run.session_id }}</span>
              <span v-if="run.batch_label" class="run-batch">{{ run.batch_label }}</span>
            </div>
            <div class="run-stats">
              <span>{{ run.attachment_count }} files</span>
              <span v-if="run.viewer_pack_count">• {{ run.viewer_pack_count }} viewer packs</span>
            </div>
            <div v-if="run.kinds_present.length" class="run-kinds">
              <code v-for="k in run.kinds_present.slice(0, 4)" :key="k" class="kind-chip">{{ k }}</code>
              <span v-if="run.kinds_present.length > 4" class="muted">+{{ run.kinds_present.length - 4 }}</span>
            </div>
          </div>

          <button
            v-if="runsData.next_cursor"
            class="btn load-more"
            @click="loadMoreRuns"
          >
            Load More
          </button>
        </div>
      </section>

      <!-- Run Detail Panel -->
      <section class="detail-panel card">
        <template v-if="!selectedRunId">
          <div class="empty-state">
            <p>Select a run from the list to view details.</p>
          </div>
        </template>
        <template v-else-if="detailLoading">
          <div class="muted">Loading run details...</div>
        </template>
        <template v-else-if="detailError">
          <div class="error-box">{{ detailError }}</div>
        </template>
        <template v-else-if="detailData">
          <h2>Run Details</h2>
          <div class="detail-meta">
            <div class="meta-row">
              <span class="meta-label">Run ID:</span>
              <code>{{ detailData.run_id }}</code>
            </div>
            <div class="meta-row">
              <span class="meta-label">Created:</span>
              <span>{{ formatDate(detailData.created_at_utc) }}</span>
            </div>
            <div class="meta-row">
              <span class="meta-label">Status:</span>
              <code :class="detailData.status.toLowerCase()">{{ detailData.status }}</code>
            </div>
            <div v-if="detailData.session_id" class="meta-row">
              <span class="meta-label">Session:</span>
              <span>{{ detailData.session_id }}</span>
            </div>
            <div v-if="detailData.batch_label" class="meta-row">
              <span class="meta-label">Batch:</span>
              <span>{{ detailData.batch_label }}</span>
            </div>
          </div>

          <h3>Attachments ({{ detailData.attachment_count }})</h3>
          <table class="tbl" v-if="detailData.attachments?.length">
            <thead>
              <tr>
                <th>Filename</th>
                <th>Kind</th>
                <th>Size</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="att in detailData.attachments" :key="att.sha256">
                <td class="mono filename-cell" :title="att.filename ?? undefined">{{ att.filename }}</td>
                <td><code class="kind-badge">{{ att.kind }}</code></td>
                <td class="mono">{{ formatSize(att.size_bytes ?? 0) }}</td>
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
          <div v-else class="muted">No attachments.</div>
        </template>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import {
  browseRuns,
  getRun,
  getDownloadUrl,
  formatSize,
} from "@/sdk/endpoints/rmosAcoustics";
import type {
  RunsBrowseResponse,
  RunDetailResponse,
} from "@/types/rmosAcoustics";

// Runs list state
const runsData = ref<RunsBrowseResponse | null>(null);
const runsLoading = ref(false);
const runsError = ref("");
const sessionIdFilter = ref("");
const batchLabelFilter = ref("");

// Detail state
const selectedRunId = ref<string | null>(null);
const detailData = ref<RunDetailResponse | null>(null);
const detailLoading = ref(false);
const detailError = ref("");

// Debounce timer
let debounceTimer: ReturnType<typeof setTimeout> | null = null;

function debouncedLoad() {
  if (debounceTimer) clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    loadRuns();
  }, 300);
}

async function loadRuns() {
  runsLoading.value = true;
  runsError.value = "";
  try {
    runsData.value = await browseRuns({
      limit: 20,
      session_id: sessionIdFilter.value || undefined,
      batch_label: batchLabelFilter.value || undefined,
    });
  } catch (e) {
    runsError.value = e instanceof Error ? e.message : String(e);
  } finally {
    runsLoading.value = false;
  }
}

async function loadMoreRuns() {
  if (!runsData.value?.next_cursor) return;
  runsLoading.value = true;
  try {
    const more = await browseRuns({
      limit: 20,
      cursor: runsData.value.next_cursor,
      session_id: sessionIdFilter.value || undefined,
      batch_label: batchLabelFilter.value || undefined,
    });
    runsData.value = {
      ...more,
      runs: [...(runsData.value?.runs ?? []), ...more.runs],
    };
  } catch (e) {
    runsError.value = e instanceof Error ? e.message : String(e);
  } finally {
    runsLoading.value = false;
  }
}

async function selectRun(runId: string) {
  selectedRunId.value = runId;
  detailLoading.value = true;
  detailError.value = "";
  detailData.value = null;
  try {
    detailData.value = await getRun(runId, { include_urls: true });
  } catch (e) {
    detailError.value = e instanceof Error ? e.message : String(e);
  } finally {
    detailLoading.value = false;
  }
}

function formatDate(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleString();
  } catch {
    return iso;
  }
}

onMounted(() => {
  loadRuns();
});
</script>

<style scoped>
.page {
  padding: 16px;
  max-width: 1400px;
  margin: 0 auto;
}

.header h1 {
  margin: 0;
}

.sub {
  opacity: 0.8;
  margin-top: 6px;
}

.layout {
  display: grid;
  grid-template-columns: 380px 1fr;
  gap: 16px;
  margin-top: 16px;
}

@media (max-width: 900px) {
  .layout {
    grid-template-columns: 1fr;
  }
}

.card {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  padding: 12px;
}

.card h2 {
  margin: 0 0 12px 0;
  font-size: 1rem;
}

.card h3 {
  margin: 16px 0 8px 0;
  font-size: 0.95rem;
}

/* Filters */
.filters {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.filters label {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 0.8rem;
}

.filters label span {
  opacity: 0.7;
}

.filters input {
  padding: 6px 10px;
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  background: rgba(255, 255, 255, 0.06);
  color: inherit;
  width: 140px;
}

/* Runs List */
.runs-list {
  display: grid;
  gap: 8px;
  max-height: 70vh;
  overflow-y: auto;
}

.run-item {
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
  cursor: pointer;
  border: 1px solid transparent;
}

.run-item:hover {
  background: rgba(255, 255, 255, 0.06);
}

.run-item.selected {
  background: rgba(66, 184, 131, 0.12);
  border-color: rgba(66, 184, 131, 0.3);
}

.run-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.run-date {
  font-size: 0.85rem;
}

.run-status {
  font-size: 0.75rem;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.1);
}

.run-status.ok {
  background: rgba(66, 184, 131, 0.2);
  color: #42b883;
}

.run-status.error {
  background: rgba(255, 0, 0, 0.2);
  color: #ff6b6b;
}

.run-status.blocked {
  background: rgba(255, 165, 0, 0.2);
  color: #ffa500;
}

.run-meta {
  display: flex;
  gap: 8px;
  margin-top: 4px;
  font-size: 0.8rem;
  opacity: 0.7;
}

.run-stats {
  font-size: 0.8rem;
  opacity: 0.6;
  margin-top: 4px;
}

.run-kinds {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 6px;
}

.kind-chip {
  font-size: 0.7rem;
  padding: 2px 6px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 4px;
}

.load-more {
  margin-top: 8px;
}

/* Detail Panel */
.detail-panel {
  min-height: 400px;
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

/* Table */
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

/* Buttons */
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

/* Utils */
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
</style>
