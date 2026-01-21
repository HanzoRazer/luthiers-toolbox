<template>
  <div class="page">
    <header class="header">
      <h1>Ingest Audit Log</h1>
      <p class="sub">
        Browse all <code>/import-zip</code> events with outcome status.
      </p>
    </header>

    <!-- Outcome Filter -->
    <section class="card">
      <h2>Filter by Outcome</h2>
      <div class="outcome-filters">
        <button
          v-for="o in outcomes"
          :key="o.value"
          class="outcome-chip"
          :class="{ active: outcomeFilter === o.value, [o.color]: true }"
          @click="toggleOutcome(o.value)"
        >
          <span class="chip-icon">{{ o.icon }}</span>
          {{ o.label }}
        </button>
        <button
          v-if="outcomeFilter"
          class="btn-clear"
          @click="outcomeFilter = null"
        >
          Clear
        </button>
      </div>
    </section>

    <!-- Events List -->
    <section class="card wide">
      <h2>Events</h2>
      <div class="list-header">
        <span class="list-count">
          Showing {{ events.length }} events
          <template v-if="outcomeFilter"> ({{ outcomeFilter }})</template>
        </span>
        <button
          class="btn"
          :disabled="loading"
          @click="loadEvents"
        >
          {{ loading ? "Loading..." : "Refresh" }}
        </button>
      </div>

      <div
        v-if="loading && !events.length"
        class="muted"
      >
        Loading events...
      </div>
      <div
        v-else-if="error"
        class="error"
      >
        {{ error }}
      </div>
      <div
        v-else-if="!events.length"
        class="muted"
      >
        No events found. Import a viewer_pack to create events.
      </div>

      <table
        v-else
        class="tbl"
      >
        <thead>
          <tr>
            <th>Outcome</th>
            <th>Time</th>
            <th>File</th>
            <th>Size</th>
            <th>Run</th>
            <th>Error</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="evt in events"
            :key="evt.event_id"
            :class="['event-row', evt.outcome]"
          >
            <td>
              <span
                class="outcome-badge"
                :class="evt.outcome"
                :title="getOutcomeTooltip(evt.outcome)"
              >
                {{ getOutcomeIcon(evt.outcome) }} {{ evt.outcome }}
              </span>
            </td>
            <td
              class="time-cell"
              :title="evt.created_at_utc"
            >
              {{ formatRelative(evt.created_at_utc) }}
            </td>
            <td
              class="filename-cell"
              :title="evt.uploader_filename || '-'"
            >
              {{ truncate(evt.uploader_filename || "-", 30) }}
            </td>
            <td class="size-cell">
              {{ formatSize(evt.zip_size_bytes) }}
            </td>
            <td class="run-cell">
              <router-link
                v-if="evt.run_id"
                :to="`/rmos/run/${evt.run_id}`"
                class="run-link"
              >
                {{ evt.run_id.slice(0, 8) }}...
              </router-link>
              <span
                v-else
                class="muted"
              >-</span>
            </td>
            <td class="error-cell">
              <span
                v-if="evt.error_code"
                class="error-code"
                :title="evt.error_message ?? undefined"
              >
                {{ evt.error_code }}
              </span>
              <span
                v-else
                class="muted"
              >-</span>
            </td>
            <td class="actions-cell">
              <button
                class="btn btn-sm"
                @click="showDetail(evt)"
              >
                Detail
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <div
        v-if="nextCursor"
        class="load-more"
      >
        <button
          class="btn"
          :disabled="loadingMore"
          @click="loadMore"
        >
          {{ loadingMore ? "Loading..." : "Load More" }}
        </button>
      </div>
    </section>

    <!-- Detail Modal -->
    <div
      v-if="detailEvent"
      class="modal-overlay"
      @click.self="detailEvent = null"
    >
      <div class="modal">
        <header class="modal-header">
          <h3>Event Detail</h3>
          <button
            class="modal-close"
            @click="detailEvent = null"
          >
            X
          </button>
        </header>
        <div class="modal-body">
          <dl class="detail-grid">
            <dt>Event ID</dt>
            <dd><code>{{ detailEvent.event_id }}</code></dd>

            <dt>Created</dt>
            <dd>{{ detailEvent.created_at_utc }}</dd>

            <dt>Outcome</dt>
            <dd>
              <span
                class="outcome-badge"
                :class="detailEvent.outcome"
              >
                {{ getOutcomeIcon(detailEvent.outcome) }} {{ detailEvent.outcome }}
              </span>
            </dd>

            <dt>HTTP Status</dt>
            <dd>{{ detailEvent.http_status || "-" }}</dd>

            <dt>Filename</dt>
            <dd>{{ detailEvent.uploader_filename || "-" }}</dd>

            <dt>ZIP SHA256</dt>
            <dd>
              <code
                v-if="detailEvent.zip_sha256"
                class="sha"
              >
                {{ detailEvent.zip_sha256 }}
              </code>
              <span v-else>-</span>
            </dd>

            <dt>Size</dt>
            <dd>{{ formatSize(detailEvent.zip_size_bytes) }}</dd>

            <dt>Session ID</dt>
            <dd>{{ detailEvent.session_id || "-" }}</dd>

            <dt>Batch Label</dt>
            <dd>{{ detailEvent.batch_label || "-" }}</dd>

            <template v-if="detailEvent.run_id">
              <dt>Run ID</dt>
              <dd>
                <router-link :to="`/rmos/run/${detailEvent.run_id}`">
                  {{ detailEvent.run_id }}
                </router-link>
              </dd>
            </template>

            <template v-if="detailEvent.bundle_id">
              <dt>Bundle ID</dt>
              <dd><code>{{ detailEvent.bundle_id }}</code></dd>
            </template>

            <template v-if="detailEvent.error">
              <dt>Error Code</dt>
              <dd class="error">
                {{ detailEvent.error.code }}
              </dd>

              <dt>Error Message</dt>
              <dd class="error">
                {{ detailEvent.error.message }}
              </dd>

              <template v-if="detailEvent.error.detail">
                <dt>Error Detail</dt>
                <dd>
                  <pre class="detail-pre">{{ JSON.stringify(detailEvent.error.detail, null, 2) }}</pre>
                </dd>
              </template>
            </template>

            <template v-if="detailEvent.validation">
              <dt>Validation Passed</dt>
              <dd :class="detailEvent.validation.passed ? 'ok' : 'error'">
                {{ detailEvent.validation.passed ? "Yes" : "No" }}
              </dd>

              <dt>Validation Errors</dt>
              <dd>{{ detailEvent.validation.errors_count ?? 0 }}</dd>

              <dt>Validation Warnings</dt>
              <dd>{{ detailEvent.validation.warnings_count ?? 0 }}</dd>

              <template v-if="detailEvent.validation.reason">
                <dt>Reason</dt>
                <dd>{{ detailEvent.validation.reason }}</dd>
              </template>
            </template>
          </dl>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from "vue";
import {
  browseIngestEvents,
  getIngestEvent,
  formatRelativeTime,
  formatSize,
} from "@/sdk/endpoints/rmosAcousticsIngest";
import type {
  IngestEventSummary,
  IngestEventDetail,
} from "@/types/rmosAcousticsIngest";

// State
const events = ref<IngestEventSummary[]>([]);
const loading = ref(false);
const loadingMore = ref(false);
const error = ref<string | null>(null);
const nextCursor = ref<string | null>(null);
const outcomeFilter = ref<string | null>(null);
const detailEvent = ref<IngestEventDetail | null>(null);

// Outcome chips
const outcomes = [
  { value: "accepted", label: "Accepted", icon: "\u2713", color: "green" },
  { value: "rejected", label: "Rejected", icon: "\u2717", color: "red" },
  { value: "quarantined", label: "Quarantined", icon: "\u26a0", color: "yellow" },
];

// Load events
async function loadEvents() {
  loading.value = true;
  error.value = null;
  try {
    const result = await browseIngestEvents({
      limit: 50,
      outcome: outcomeFilter.value as "accepted" | "rejected" | "quarantined" | undefined,
    });
    events.value = result.entries;
    nextCursor.value = result.next_cursor;
  } catch (e) {
    error.value = String(e);
  } finally {
    loading.value = false;
  }
}

// Load more
async function loadMore() {
  if (!nextCursor.value) return;
  loadingMore.value = true;
  try {
    const result = await browseIngestEvents({
      limit: 50,
      cursor: nextCursor.value,
      outcome: outcomeFilter.value as "accepted" | "rejected" | "quarantined" | undefined,
    });
    events.value.push(...result.entries);
    nextCursor.value = result.next_cursor;
  } catch (e) {
    error.value = String(e);
  } finally {
    loadingMore.value = false;
  }
}

// Show detail
async function showDetail(evt: IngestEventSummary) {
  try {
    detailEvent.value = await getIngestEvent(evt.event_id);
  } catch (e) {
    error.value = `Failed to load detail: ${e}`;
  }
}

// Toggle outcome filter
function toggleOutcome(value: string) {
  outcomeFilter.value = outcomeFilter.value === value ? null : value;
}

// Helpers
function formatRelative(ts: string): string {
  return formatRelativeTime(ts);
}

function truncate(s: string, len: number): string {
  return s.length > len ? s.slice(0, len - 3) + "..." : s;
}

function getOutcomeIcon(outcome: string): string {
  switch (outcome) {
    case "accepted":
      return "\u2713";
    case "rejected":
      return "\u2717";
    case "quarantined":
      return "\u26a0";
    default:
      return "?";
  }
}

function getOutcomeTooltip(outcome: string): string {
  switch (outcome) {
    case "accepted":
      return "Pack imported successfully";
    case "rejected":
      return "Pack rejected (400/422)";
    case "quarantined":
      return "Import failed (500)";
    default:
      return outcome;
  }
}

// Watch filter changes
watch(outcomeFilter, () => {
  loadEvents();
});

// Initial load
onMounted(() => {
  loadEvents();
});
</script>

<style scoped>
.page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1rem;
}

.header {
  margin-bottom: 1.5rem;
}

.header h1 {
  margin: 0 0 0.5rem 0;
}

.sub {
  color: var(--color-text-muted, #666);
  margin: 0;
}

.card {
  background: var(--color-bg-secondary, #1a1a1a);
  border: 1px solid var(--color-border, #333);
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1rem;
}

.card.wide {
  max-width: none;
}

.card h2 {
  margin: 0 0 1rem 0;
  font-size: 1.1rem;
}

/* Outcome filters */
.outcome-filters {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  align-items: center;
}

.outcome-chip {
  padding: 0.4rem 0.8rem;
  border-radius: 16px;
  border: 1px solid var(--color-border, #444);
  background: transparent;
  cursor: pointer;
  font-size: 0.85rem;
  display: flex;
  align-items: center;
  gap: 0.3rem;
}

.outcome-chip:hover {
  background: var(--color-bg-hover, #333);
}

.outcome-chip.active {
  border-color: currentColor;
}

.outcome-chip.green {
  color: var(--color-success, #4caf50);
}

.outcome-chip.red {
  color: var(--color-error, #f44336);
}

.outcome-chip.yellow {
  color: var(--color-warning, #ff9800);
}

.btn-clear {
  padding: 0.3rem 0.6rem;
  font-size: 0.8rem;
  background: transparent;
  border: none;
  color: var(--color-text-muted, #888);
  cursor: pointer;
}

.btn-clear:hover {
  color: var(--color-text, #fff);
}

/* List header */
.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.list-count {
  color: var(--color-text-muted, #888);
  font-size: 0.9rem;
}

/* Table */
.tbl {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}

.tbl th,
.tbl td {
  padding: 0.5rem;
  text-align: left;
  border-bottom: 1px solid var(--color-border, #333);
}

.tbl th {
  font-weight: 600;
  color: var(--color-text-muted, #888);
}

.event-row.accepted {
  background: rgba(76, 175, 80, 0.05);
}

.event-row.rejected {
  background: rgba(244, 67, 54, 0.05);
}

.event-row.quarantined {
  background: rgba(255, 152, 0, 0.05);
}

/* Outcome badge */
.outcome-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 500;
}

.outcome-badge.accepted {
  background: rgba(76, 175, 80, 0.2);
  color: var(--color-success, #4caf50);
}

.outcome-badge.rejected {
  background: rgba(244, 67, 54, 0.2);
  color: var(--color-error, #f44336);
}

.outcome-badge.quarantined {
  background: rgba(255, 152, 0, 0.2);
  color: var(--color-warning, #ff9800);
}

/* Cells */
.time-cell {
  white-space: nowrap;
}

.filename-cell {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.size-cell {
  text-align: right;
  white-space: nowrap;
}

.run-link {
  color: var(--color-primary, #4a9eff);
  text-decoration: none;
}

.run-link:hover {
  text-decoration: underline;
}

.error-code {
  color: var(--color-error, #f44336);
  font-family: monospace;
  font-size: 0.8rem;
}

.muted {
  color: var(--color-text-muted, #888);
}

.error {
  color: var(--color-error, #f44336);
}

.ok {
  color: var(--color-success, #4caf50);
}

/* Load more */
.load-more {
  margin-top: 1rem;
  text-align: center;
}

/* Buttons */
.btn {
  padding: 0.5rem 1rem;
  border-radius: 4px;
  border: 1px solid var(--color-border, #444);
  background: var(--color-bg-secondary, #2a2a2a);
  color: var(--color-text, #fff);
  cursor: pointer;
}

.btn:hover:not(:disabled) {
  background: var(--color-bg-hover, #333);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-sm {
  padding: 0.25rem 0.5rem;
  font-size: 0.8rem;
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: var(--color-bg-secondary, #1a1a1a);
  border: 1px solid var(--color-border, #333);
  border-radius: 8px;
  max-width: 600px;
  width: 90%;
  max-height: 80vh;
  overflow: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid var(--color-border, #333);
}

.modal-header h3 {
  margin: 0;
}

.modal-close {
  background: transparent;
  border: none;
  color: var(--color-text-muted, #888);
  cursor: pointer;
  font-size: 1.2rem;
}

.modal-body {
  padding: 1rem;
}

.detail-grid {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0.5rem 1rem;
  margin: 0;
}

.detail-grid dt {
  font-weight: 600;
  color: var(--color-text-muted, #888);
}

.detail-grid dd {
  margin: 0;
  word-break: break-all;
}

.sha {
  font-size: 0.75rem;
  word-break: break-all;
}

.detail-pre {
  background: var(--color-bg, #111);
  padding: 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  overflow-x: auto;
  max-height: 200px;
}

code {
  background: var(--color-bg, #111);
  padding: 0.1rem 0.3rem;
  border-radius: 3px;
  font-size: 0.85em;
}
</style>
