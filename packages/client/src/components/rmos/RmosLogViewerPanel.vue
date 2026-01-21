<template>
  <div
    ref="containerRef"
    class="rmos-log-viewer-panel"
  >
    <!-- Header with filters and controls -->
    <div class="header">
      <div class="title-row">
        <h3>RMOS Run Logs</h3>
        <div class="header-actions">
          <!-- H2.5: New runs badge -->
          <button
            v-if="newRunsCount > 0"
            class="badge-btn"
            @click="jumpToNewest"
          >
            {{ newRunsCount }} new
          </button>

          <!-- H2.4: Jump to newest -->
          <button
            class="btn icon"
            title="Jump to newest"
            :disabled="loading"
            @click="jumpToNewest"
          >
            <span class="icon-arrow-up" />
          </button>

          <!-- Refresh -->
          <button
            class="btn"
            :disabled="loading"
            @click="refresh"
          >
            {{ loading ? "Loading..." : "Refresh" }}
          </button>
        </div>
      </div>

      <!-- Filters -->
      <div class="filters">
        <select
          v-model="filters.mode"
          @change="refresh"
        >
          <option value="">
            All modes
          </option>
          <option value="art_studio">
            Art Studio
          </option>
          <option value="saw">
            Saw
          </option>
          <option value="router">
            Router
          </option>
        </select>

        <select
          v-model="filters.status"
          @change="refresh"
        >
          <option value="">
            All statuses
          </option>
          <option value="OK">
            OK
          </option>
          <option value="BLOCKED">
            BLOCKED
          </option>
          <option value="ERROR">
            ERROR
          </option>
        </select>

        <select
          v-model="filters.risk_level"
          @change="refresh"
        >
          <option value="">
            All risk levels
          </option>
          <option value="GREEN">
            GREEN
          </option>
          <option value="YELLOW">
            YELLOW
          </option>
          <option value="RED">
            RED
          </option>
          <option value="ERROR">
            ERROR
          </option>
        </select>

        <input
          v-model="filters.tool_id"
          placeholder="Tool ID"
          @keyup.enter="refresh"
          @input="onFilterInput"
        >

        <!-- H2.8: Soft cap dropdown -->
        <select
          v-model="softCapValue"
          class="cap-select"
          title="Auto-refresh cap"
        >
          <option :value="10">
            Cap: 10
          </option>
          <option :value="25">
            Cap: 25
          </option>
          <option :value="50">
            Cap: 50
          </option>
        </select>

        <!-- H2.10: Reset cap button -->
        <button
          class="btn small"
          title="Reset cap to default"
          @click="resetCapForFilter"
        >
          Reset
        </button>
      </div>
    </div>

    <!-- Error display -->
    <div
      v-if="error"
      class="error-banner"
    >
      {{ error }}
    </div>

    <!-- H2.7: Overflow indicator -->
    <div
      v-if="overflowCount > 0"
      class="overflow-row"
      @click="jumpToNewest"
    >
      +{{ overflowCount }} more runs available
    </div>

    <!-- Log entries table -->
    <div
      ref="tableContainerRef"
      class="table-container"
      @scroll="onScroll"
    >
      <table class="log-table">
        <thead>
          <tr>
            <th>Time</th>
            <th>Run ID</th>
            <th>Mode</th>
            <th>Tool</th>
            <th>Status</th>
            <th>Risk</th>
            <th>Score</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="entry in entries"
            :key="entry.run_id"
            :data-run-id="entry.run_id"
            :class="{
              selected: selectedRunId === entry.run_id,
              'risk-green': entry.risk_level === 'GREEN',
              'risk-yellow': entry.risk_level === 'YELLOW',
              'risk-red': entry.risk_level === 'RED' || entry.risk_level === 'ERROR',
            }"
            @click="selectRun(entry)"
          >
            <td class="time">
              {{ formatTime(entry.created_at_utc) }}
            </td>
            <td class="run-id mono">
              {{ entry.run_id.slice(0, 16) }}...
            </td>
            <td>{{ entry.mode }}</td>
            <td>{{ entry.tool_id || "-" }}</td>
            <td class="status">
              {{ entry.status }}
            </td>
            <td class="risk">
              {{ entry.risk_level }}
            </td>
            <td class="score">
              {{ entry.score?.toFixed(2) ?? "-" }}
            </td>
          </tr>

          <!-- H2.3: Sentinel row -->
          <tr
            v-if="hasMore || loadingMore"
            class="sentinel-row"
          >
            <td
              colspan="7"
              class="sentinel-cell"
            >
              <span v-if="loadingMore">Loading older...</span>
              <span
                v-else-if="hasMore"
                @click="loadMore"
              >Load more</span>
            </td>
          </tr>
          <tr
            v-else-if="entries.length > 0"
            class="sentinel-row"
          >
            <td
              colspan="7"
              class="sentinel-cell end"
            >
              End of list
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- H2.1: Load more button (fallback) -->
    <div
      v-if="hasMore && !loadingMore"
      class="load-more-row"
    >
      <button
        class="btn"
        :disabled="loadingMore"
        @click="loadMore"
      >
        Load More
      </button>
    </div>

    <!-- Empty state -->
    <div
      v-if="!loading && entries.length === 0"
      class="empty-state"
    >
      No runs found for current filters.
    </div>

    <!-- Selected run details panel -->
    <div
      v-if="selectedEntry"
      class="details-panel"
    >
      <div class="details-header">
        <h4>Run Details</h4>
        <button
          class="btn small"
          @click="selectedEntry = null"
        >
          Close
        </button>
      </div>
      <div class="details-content">
        <div><strong>Run ID:</strong> {{ selectedEntry.run_id }}</div>
        <div><strong>Created:</strong> {{ selectedEntry.created_at_utc }}</div>
        <div><strong>Mode:</strong> {{ selectedEntry.mode }}</div>
        <div><strong>Status:</strong> {{ selectedEntry.status }}</div>
        <div><strong>Risk:</strong> {{ selectedEntry.risk_level }}</div>
        <div v-if="selectedEntry.warnings?.length">
          <strong>Warnings:</strong>
          <ul>
            <li
              v-for="(w, i) in selectedEntry.warnings"
              :key="i"
            >
              {{ w }}
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from "vue";
import {
  fetchRecentLogs,
  fetchNextPage,
  checkForNewerRuns,
  getSoftCap,
  setSoftCap,
  resetSoftCap,
  getBackoffMs,
  type RunLogEntry,
  type RecentLogsResponse,
} from "@/api/rmosLogsClient";

// =============================================================================
// Props & Emits
// =============================================================================

const props = defineProps<{
  initialLimit?: number;
}>();

const emit = defineEmits<{
  (e: "select", entry: RunLogEntry): void;
}>();

// =============================================================================
// Refs
// =============================================================================

const containerRef = ref<HTMLElement | null>(null);
const tableContainerRef = ref<HTMLElement | null>(null);

const entries = ref<RunLogEntry[]>([]);
const loading = ref(false);
const loadingMore = ref(false);
const error = ref<string | null>(null);

const hasMore = ref(false);
const nextCursor = ref<string | null>(null);

const selectedRunId = ref<string | null>(null);
const selectedEntry = ref<RunLogEntry | null>(null);

// H2.5: New runs badge
const newRunsCount = ref(0);
const newestTimestamp = ref<string | null>(null);

// H2.7: Overflow tracking
const overflowCount = ref(0);

// Filters
const filters = ref({
  mode: "",
  status: "",
  risk_level: "",
  tool_id: "",
  source: "",
});

// H2.8: Soft cap (per-filter)
const softCapValue = ref(25);

// Polling
let pollInterval: ReturnType<typeof setInterval> | null = null;
let isPollingPaused = false;

// =============================================================================
// Computed
// =============================================================================

const filterParams = computed(() => ({
  mode: filters.value.mode || undefined,
  status: filters.value.status || undefined,
  risk_level: filters.value.risk_level || undefined,
  tool_id: filters.value.tool_id || undefined,
  source: filters.value.source || undefined,
}));

// =============================================================================
// Methods
// =============================================================================

function formatTime(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleString();
  } catch {
    return iso;
  }
}

function selectRun(entry: RunLogEntry) {
  selectedRunId.value = entry.run_id;
  selectedEntry.value = entry;
  emit("select", entry);

  // H2.2: Pause polling when details open
  isPollingPaused = true;
}

// H2.9: Load soft cap for current filter
function loadSoftCapForFilter() {
  softCapValue.value = getSoftCap(filters.value.mode, filters.value.source);
}

// H2.8: Save soft cap when changed
watch(softCapValue, (val) => {
  setSoftCap(val, filters.value.mode, filters.value.source);
});

// H2.10: Reset cap for current filter
function resetCapForFilter() {
  resetSoftCap(filters.value.mode, filters.value.source);
  loadSoftCapForFilter();
}

async function refresh() {
  loading.value = true;
  error.value = null;
  newRunsCount.value = 0;
  overflowCount.value = 0;

  try {
    const response = await fetchRecentLogs({
      limit: props.initialLimit || 50,
      ...filterParams.value,
    });

    entries.value = response.entries;
    hasMore.value = response.has_more;
    nextCursor.value = response.next_cursor;

    if (response.entries.length > 0) {
      newestTimestamp.value = response.entries[0].created_at_utc;
    }
  } catch (e: any) {
    error.value = e?.message || "Failed to load logs";
  } finally {
    loading.value = false;
  }
}

// H2.1: Load more with cursor + selection pinning
async function loadMore() {
  if (!hasMore.value || loadingMore.value || !nextCursor.value) return;

  loadingMore.value = true;

  // H2.1: Remember scroll position for selection pinning
  const scrollBefore = tableContainerRef.value?.scrollTop ?? 0;
  const selectedId = selectedRunId.value;

  try {
    const response = await fetchRecentLogs({
      limit: props.initialLimit || 50,
      cursor: nextCursor.value,
      ...filterParams.value,
    });

    entries.value = [...entries.value, ...response.entries];
    hasMore.value = response.has_more;
    nextCursor.value = response.next_cursor;

    // H2.1: Selection pinning - scroll to keep selected item in view
    if (selectedId && tableContainerRef.value) {
      // Use nextTick to wait for DOM update
      setTimeout(() => {
        const selectedRow = tableContainerRef.value?.querySelector(
          `tr[data-run-id="${selectedId}"]`
        ) as HTMLElement | null;
        if (selectedRow) {
          const containerRect = tableContainerRef.value!.getBoundingClientRect();
          const rowRect = selectedRow.getBoundingClientRect();
          // If selected row is now out of view, scroll to it
          if (rowRect.bottom > containerRect.bottom || rowRect.top < containerRect.top) {
            selectedRow.scrollIntoView({ block: "center", behavior: "smooth" });
          }
        }
      }, 50);
    }
  } catch (e: any) {
    error.value = e?.message || "Failed to load more logs";
  } finally {
    loadingMore.value = false;
  }
}

// H2.4: Jump to newest
async function jumpToNewest() {
  // Scroll to top
  if (tableContainerRef.value) {
    tableContainerRef.value.scrollTop = 0;
  }

  // Reset and refresh
  newRunsCount.value = 0;
  overflowCount.value = 0;
  await refresh();
}

// H2.6: Soft refresh (prepend new runs)
async function softRefresh() {
  if (!newestTimestamp.value) return;

  try {
    const result = await checkForNewerRuns(newestTimestamp.value, filterParams.value);

    if (result.count > 0) {
      const cap = softCapValue.value;

      if (result.count <= cap) {
        // H2.6: Prepend new runs
        const response = await fetchRecentLogs({
          limit: result.count,
          ...filterParams.value,
        });

        // Filter to only truly newer entries
        const newEntries = response.entries.filter(
          (e) => e.created_at_utc > newestTimestamp.value!
        );

        if (newEntries.length > 0) {
          entries.value = [...newEntries, ...entries.value];
          newestTimestamp.value = newEntries[0].created_at_utc;
        }
      } else {
        // H2.7: Cap exceeded, show overflow
        overflowCount.value = result.count - cap;
        newRunsCount.value = result.count;
      }
    }
  } catch {
    // Silent fail for background refresh
  }
}

// H2.5: Poll for new runs
function startPolling() {
  if (pollInterval) return;

  pollInterval = setInterval(async () => {
    if (isPollingPaused || loading.value || loadingMore.value) return;

    // Check for new runs
    if (newestTimestamp.value) {
      const result = await checkForNewerRuns(newestTimestamp.value, filterParams.value);
      if (result.count > 0) {
        // Check if at top of list
        const atTop = tableContainerRef.value?.scrollTop === 0;

        if (atTop) {
          // H2.6: Auto-prepend if at top
          await softRefresh();
        } else {
          // H2.5: Show badge
          newRunsCount.value = result.count;
        }
      }
    }
  }, getBackoffMs());
}

function stopPolling() {
  if (pollInterval) {
    clearInterval(pollInterval);
    pollInterval = null;
  }
}

// H2.2: Infinite scroll detection
function onScroll() {
  if (!tableContainerRef.value || loadingMore.value || !hasMore.value) return;

  const { scrollTop, scrollHeight, clientHeight } = tableContainerRef.value;
  const nearBottom = scrollHeight - scrollTop - clientHeight < 100;

  if (nearBottom) {
    loadMore();
  }

  // Resume polling if scrolled to top
  if (scrollTop === 0) {
    isPollingPaused = false;
  }
}

// H2.2: Pause polling when typing
function onFilterInput() {
  isPollingPaused = true;
}

// =============================================================================
// Lifecycle
// =============================================================================

onMounted(() => {
  loadSoftCapForFilter();
  refresh();
  startPolling();
});

onUnmounted(() => {
  stopPolling();
});

// Reload soft cap when filters change
watch(
  () => [filters.value.mode, filters.value.source],
  () => {
    loadSoftCapForFilter();
  }
);
</script>

<style scoped>
.rmos-log-viewer-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  font-family: system-ui, -apple-system, sans-serif;
  font-size: 14px;
}

.header {
  padding: 12px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  background: #fafafa;
}

.title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.title-row h3 {
  margin: 0;
  font-size: 16px;
}

.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.filters {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.filters select,
.filters input {
  padding: 6px 8px;
  border: 1px solid rgba(0, 0, 0, 0.15);
  border-radius: 4px;
  font-size: 13px;
}

.cap-select {
  width: 80px;
}

.btn {
  padding: 6px 12px;
  border: 1px solid rgba(0, 0, 0, 0.2);
  border-radius: 4px;
  background: white;
  cursor: pointer;
  font-size: 13px;
}

.btn:hover {
  background: #f0f0f0;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn.small {
  padding: 4px 8px;
  font-size: 12px;
}

.btn.icon {
  padding: 6px 8px;
}

/* H2.5: Badge button */
.badge-btn {
  padding: 4px 10px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 12px;
  cursor: pointer;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

/* H2.7: Overflow row */
.overflow-row {
  padding: 8px 12px;
  background: #fef3c7;
  color: #92400e;
  text-align: center;
  cursor: pointer;
  font-size: 13px;
}

.overflow-row:hover {
  background: #fde68a;
}

.error-banner {
  padding: 8px 12px;
  background: #fee2e2;
  color: #b91c1c;
  font-size: 13px;
}

.table-container {
  flex: 1;
  overflow: auto;
}

.log-table {
  width: 100%;
  border-collapse: collapse;
}

.log-table th,
.log-table td {
  padding: 8px 10px;
  text-align: left;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.log-table th {
  background: #f5f5f5;
  font-weight: 600;
  font-size: 12px;
  text-transform: uppercase;
  color: #666;
  position: sticky;
  top: 0;
}

.log-table tbody tr {
  cursor: pointer;
}

.log-table tbody tr:hover {
  background: rgba(0, 0, 0, 0.02);
}

.log-table tbody tr.selected {
  background: rgba(59, 130, 246, 0.1);
}

.log-table .time {
  white-space: nowrap;
  font-size: 12px;
  color: #666;
}

.log-table .run-id {
  font-size: 11px;
}

.log-table .mono {
  font-family: ui-monospace, monospace;
}

.log-table .score {
  text-align: right;
}

/* Risk level colors */
.log-table tr.risk-green .risk {
  color: #16a34a;
}

.log-table tr.risk-yellow .risk {
  color: #ca8a04;
}

.log-table tr.risk-red .risk {
  color: #dc2626;
}

/* H2.3: Sentinel row */
.sentinel-row td {
  text-align: center;
  padding: 16px;
}

.sentinel-cell {
  color: #666;
  font-size: 13px;
}

.sentinel-cell:not(.end) {
  cursor: pointer;
}

.sentinel-cell:not(.end):hover {
  color: #3b82f6;
}

.sentinel-cell.end {
  color: #999;
  font-style: italic;
}

/* H2.1: Load more row */
.load-more-row {
  padding: 12px;
  text-align: center;
  border-top: 1px solid rgba(0, 0, 0, 0.1);
}

.empty-state {
  padding: 40px;
  text-align: center;
  color: #666;
}

/* Details panel */
.details-panel {
  border-top: 1px solid rgba(0, 0, 0, 0.1);
  padding: 12px;
  background: #fafafa;
  max-height: 200px;
  overflow: auto;
}

.details-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.details-header h4 {
  margin: 0;
  font-size: 14px;
}

.details-content {
  font-size: 13px;
}

.details-content > div {
  margin-bottom: 4px;
}

.details-content ul {
  margin: 4px 0 0 16px;
  padding: 0;
}

.icon-arrow-up::before {
  content: "\2191";
}
</style>
