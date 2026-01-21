<script setup lang="ts">
/**
 * RunArtifactPanel.vue
 *
 * Master list panel for browsing run artifacts.
 * Includes filtering controls and delegates row rendering to RunArtifactRow.
 */
import { onMounted, watch } from "vue";
import { useRmosRunsStore } from "@/stores/rmosRunsStore";
import RunArtifactRow from "./RunArtifactRow.vue";

const store = useRmosRunsStore();

// Load runs on mount
onMounted(() => {
  store.loadRuns();
});

// Reload when filters change
watch(
  () => store.filters,
  () => {
    store.loadRuns();
  },
  { deep: true }
);

function handleRowSelect(runId: string) {
  store.setLastSelected(runId);
  store.select(runId);
}

function handleRefresh() {
  store.loadRuns();
}
</script>

<template>
  <div class="run-artifact-panel">
    <!-- Header -->
    <div class="panel-header">
      <h3>Run Artifacts</h3>
      <button
        class="btn-refresh"
        :disabled="store.loading"
        @click="handleRefresh"
      >
        {{ store.loading ? "Loading…" : "Refresh" }}
      </button>
    </div>

    <!-- Filters -->
    <div class="filters">
      <label>
        Status
        <select v-model="store.filters.status">
          <option value="">All</option>
          <option value="OK">OK</option>
          <option value="BLOCKED">Blocked</option>
          <option value="ERROR">Error</option>
        </select>
      </label>

      <label>
        Event Type
        <input
          v-model="store.filters.event_type"
          type="text"
          placeholder="e.g., approval"
        >
      </label>

      <label>
        Tool ID
        <input
          v-model="store.filters.tool_id"
          type="text"
          placeholder="e.g., T102"
        >
      </label>

      <button
        class="btn-clear"
        @click="store.clearFilters"
      >
        Clear
      </button>
    </div>

    <!-- Column Headers -->
    <div class="column-headers">
      <div>Run ID</div>
      <div>Status</div>
      <div>Event</div>
      <div>Tool</div>
      <div class="text-right">
        Created
      </div>
    </div>

    <!-- Run List -->
    <div class="run-list">
      <template v-if="store.loading && store.items.length === 0">
        <div class="loading">
          Loading runs…
        </div>
      </template>

      <template v-else-if="store.error">
        <div class="error">
          {{ store.error }}
        </div>
      </template>

      <template v-else-if="store.items.length === 0">
        <div class="empty">
          No run artifacts found.
        </div>
      </template>

      <template v-else>
        <RunArtifactRow
          v-for="r in store.items"
          :key="r.run_id"
          :run="r"
          :selected="store.selected?.run_id === r.run_id"
          @select="handleRowSelect(r.run_id)"
        />
      </template>
    </div>

    <!-- Status Bar -->
    <div class="status-bar">
      <span>{{ store.items.length }} run(s)</span>
      <span
        v-if="store.lastSelectedRunId"
        class="last-selected"
      >
        Last: {{ store.lastSelectedRunId.slice(0, 12) }}…
      </span>
    </div>
  </div>
</template>

<style scoped>
.run-artifact-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  border: 1px solid #dee2e6;
  border-radius: 8px;
  background: #fff;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #eee;
  background: #f8f9fa;
  border-radius: 8px 8px 0 0;
}

.panel-header h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
}

.btn-refresh {
  padding: 0.35rem 0.75rem;
  font-size: 0.85rem;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  background: #fff;
  cursor: pointer;
}

.btn-refresh:hover:not(:disabled) {
  background: #e9ecef;
}

.btn-refresh:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.filters {
  display: flex;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #eee;
  background: #fafafa;
  flex-wrap: wrap;
  align-items: flex-end;
}

.filters label {
  display: flex;
  flex-direction: column;
  font-size: 0.75rem;
  color: #666;
}

.filters select,
.filters input {
  margin-top: 0.25rem;
  padding: 0.4rem 0.5rem;
  font-size: 0.85rem;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  min-width: 100px;
}

.btn-clear {
  padding: 0.4rem 0.75rem;
  font-size: 0.8rem;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  background: #fff;
  cursor: pointer;
}

.btn-clear:hover {
  background: #e9ecef;
}

.column-headers {
  display: grid;
  grid-template-columns: 140px 80px 120px 100px 1fr;
  gap: 0.75rem;
  padding: 0.5rem 0.8rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: #6c757d;
  text-transform: uppercase;
  border-bottom: 2px solid #dee2e6;
  background: #f8f9fa;
}

.text-right {
  text-align: right;
}

.run-list {
  flex: 1;
  overflow-y: auto;
  min-height: 200px;
}

.loading,
.error,
.empty {
  padding: 2rem;
  text-align: center;
  color: #6c757d;
}

.error {
  color: #dc3545;
}

.status-bar {
  display: flex;
  justify-content: space-between;
  padding: 0.5rem 1rem;
  font-size: 0.75rem;
  color: #868e96;
  border-top: 1px solid #eee;
  background: #f8f9fa;
  border-radius: 0 0 8px 8px;
}

.last-selected {
  font-family: monospace;
}
</style>
