<template>
  <div
    ref="containerRef"
    :class="$style.panel"
  >
    <!-- Header with filters and controls -->
    <div :class="$style.header">
      <div :class="$style.titleRow">
        <h3>RMOS Run Logs</h3>
        <div :class="$style.headerActions">
          <!-- H2.5: New runs badge -->
          <button
            v-if="newRunsCount > 0"
            :class="$style.badgeBtn"
            @click="handleJumpToNewest"
          >
            {{ newRunsCount }} new
          </button>

          <!-- H2.4: Jump to newest -->
          <button
            :class="[$style.btn, $style.btnIcon]"
            title="Jump to newest"
            :disabled="loading"
            @click="handleJumpToNewest"
          >
            <span :class="$style.iconArrowUp" />
          </button>

          <!-- Refresh -->
          <button
            :class="$style.btn"
            :disabled="loading"
            @click="handleRefresh"
          >
            {{ loading ? "Loading..." : "Refresh" }}
          </button>
        </div>
      </div>

      <!-- Filters -->
      <div :class="$style.filters">
        <select
          v-model="filters.mode"
          @change="handleRefresh"
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
          @change="handleRefresh"
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
          @change="handleRefresh"
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
          @keyup.enter="handleRefresh"
          @input="pausePolling"
        >

        <!-- H2.8: Soft cap dropdown -->
        <select
          v-model="softCapValue"
          :class="$style.capSelect"
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
          :class="[$style.btn, $style.btnSmall]"
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
      :class="$style.errorBanner"
    >
      {{ error }}
    </div>

    <!-- H2.7: Overflow indicator -->
    <div
      v-if="overflowCount > 0"
      :class="$style.overflowRow"
      @click="handleJumpToNewest"
    >
      +{{ overflowCount }} more runs available
    </div>

    <!-- Log entries table -->
    <div
      ref="tableContainerRef"
      :class="$style.tableContainer"
      @scroll="onScroll"
    >
      <table :class="$style.logTable">
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
              [$style.rowSelected]: selectedRunId === entry.run_id,
            }"
            @click="selectRun(entry)"
          >
            <td :class="$style.cellTime">
              {{ formatTime(entry.created_at_utc) }}
            </td>
            <td :class="[$style.cellRunId, $style.cellMono]">
              {{ entry.run_id.slice(0, 16) }}...
            </td>
            <td>{{ entry.mode }}</td>
            <td>{{ entry.tool_id || "-" }}</td>
            <td>{{ entry.status }}</td>
            <td :class="riskClass(entry.risk_level)">
              {{ entry.risk_level }}
            </td>
            <td :class="$style.cellScore">
              {{ entry.score?.toFixed(2) ?? "-" }}
            </td>
          </tr>

          <!-- H2.3: Sentinel row -->
          <tr
            v-if="hasMore || loadingMore"
            :class="$style.sentinelRow"
          >
            <td
              colspan="7"
              :class="$style.sentinelCell"
            >
              <span v-if="loadingMore">Loading older...</span>
              <span
                v-else-if="hasMore"
                :class="$style.sentinelClickable"
                @click="loadMore"
              >Load more</span>
            </td>
          </tr>
          <tr
            v-else-if="entries.length > 0"
            :class="$style.sentinelRow"
          >
            <td
              colspan="7"
              :class="[$style.sentinelCell, $style.sentinelEnd]"
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
      :class="$style.loadMoreRow"
    >
      <button
        :class="$style.btn"
        :disabled="loadingMore"
        @click="loadMore"
      >
        Load More
      </button>
    </div>

    <!-- Empty state -->
    <div
      v-if="!loading && entries.length === 0"
      :class="$style.emptyState"
    >
      No runs found for current filters.
    </div>

    <!-- Selected run details panel -->
    <div
      v-if="selectedEntry"
      :class="$style.detailsPanel"
    >
      <div :class="$style.detailsHeader">
        <h4>Run Details</h4>
        <button
          :class="[$style.btn, $style.btnSmall]"
          @click="clearSelection"
        >
          Close
        </button>
      </div>
      <div :class="$style.detailsContent">
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
import { ref, onMounted, onUnmounted, useCssModule } from 'vue'
import type { RunLogEntry } from '@/api/rmosLogsClient'
import {
  useLogFilters,
  useLogEntries,
  useLogPolling,
  useLogSelection,
  formatTime
} from './log-viewer'

// =============================================================================
// Props & Emits
// =============================================================================

const props = defineProps<{
  initialLimit?: number
}>()

const emit = defineEmits<{
  (e: 'select', entry: RunLogEntry): void
}>()

// =============================================================================
// CSS Module
// =============================================================================

const $style = useCssModule()

// =============================================================================
// Refs
// =============================================================================

const containerRef = ref<HTMLElement | null>(null)
const tableContainerRef = ref<HTMLElement | null>(null)

// =============================================================================
// Composables
// =============================================================================

const {
  filters,
  softCapValue,
  filterParams,
  loadSoftCapForFilter,
  resetCapForFilter
} = useLogFilters()

const {
  selectedRunId,
  selectedEntry,
  selectRun: doSelectRun,
  clearSelection
} = useLogSelection({
  onSelect: (entry) => emit('select', entry),
  onPausePolling: () => pausePolling()
})

const {
  entries,
  loading,
  loadingMore,
  error,
  hasMore,
  newestTimestamp,
  overflowCount,
  refresh,
  loadMore,
  jumpToNewest,
  prependEntries
} = useLogEntries({
  initialLimit: props.initialLimit || 50,
  filterParams,
  tableContainerRef,
  selectedRunId
})

const {
  newRunsCount,
  startPolling,
  stopPolling,
  pausePolling,
  resumePolling,
  resetNewRunsCount
} = useLogPolling({
  filterParams,
  softCapValue,
  newestTimestamp,
  overflowCount,
  loading,
  loadingMore,
  tableContainerRef,
  prependEntries
})

// =============================================================================
// Methods
// =============================================================================

function selectRun(entry: RunLogEntry): void {
  doSelectRun(entry)
}

async function handleRefresh(): Promise<void> {
  resetNewRunsCount()
  await refresh()
}

async function handleJumpToNewest(): Promise<void> {
  resetNewRunsCount()
  await jumpToNewest()
}

function onScroll(): void {
  if (!tableContainerRef.value || loadingMore.value || !hasMore.value) return

  const { scrollTop, scrollHeight, clientHeight } = tableContainerRef.value
  const nearBottom = scrollHeight - scrollTop - clientHeight < 100

  if (nearBottom) {
    loadMore()
  }

  // Resume polling if scrolled to top
  if (scrollTop === 0) {
    resumePolling()
  }
}

function riskClass(level: string): string {
  switch (level) {
    case 'GREEN':
      return $style.riskGreen
    case 'YELLOW':
      return $style.riskYellow
    case 'RED':
    case 'ERROR':
      return $style.riskRed
    default:
      return ''
  }
}

// =============================================================================
// Lifecycle
// =============================================================================

onMounted(() => {
  loadSoftCapForFilter()
  refresh()
  startPolling()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style module src="./log-viewer/RmosLogViewer.module.css" />
