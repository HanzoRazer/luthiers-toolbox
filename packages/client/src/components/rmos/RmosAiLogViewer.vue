<template>
  <div class="rmos-log-viewer max-w-5xl mx-auto p-4 space-y-4">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <h2 class="text-xl font-semibold">
        RMOS AI Log Viewer
      </h2>
      <div class="text-xs text-gray-500">
        Filter by run_id, tool_id, or material_id
      </div>
    </div>

    <!-- Filters -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-3 items-end">
      <div>
        <label class="block text-xs font-medium text-gray-600 mb-1">Run ID</label>
        <input
          v-model="filters.runId"
          type="text"
          class="w-full border rounded px-2 py-1 text-sm"
          placeholder="run_id (optional)"
        >
      </div>

      <div>
        <label class="block text-xs font-medium text-gray-600 mb-1">Tool ID</label>
        <input
          v-model="filters.toolId"
          type="text"
          class="w-full border rounded px-2 py-1 text-sm"
          placeholder="tool_id (optional)"
        >
      </div>

      <div>
        <label class="block text-xs font-medium text-gray-600 mb-1">Material ID</label>
        <input
          v-model="filters.materialId"
          type="text"
          class="w-full border rounded px-2 py-1 text-sm"
          placeholder="material_id (optional)"
        >
      </div>

      <div class="flex flex-col space-y-2">
        <div>
          <label class="block text-xs font-medium text-gray-600 mb-1">View</label>
          <select
            v-model="filters.view"
            class="w-full border rounded px-2 py-1 text-sm"
          >
            <option value="attempts">
              Attempts
            </option>
            <option value="runs">
              Runs
            </option>
          </select>
        </div>

        <button
          class="w-full text-sm border rounded px-2 py-1 bg-gray-900 text-white hover:bg-gray-800"
          :disabled="loading"
          @click="loadLogs"
        >
          <span v-if="!loading">Refresh</span>
          <span v-else>Loading...</span>
        </button>
      </div>
    </div>

    <!-- Error -->
    <div
      v-if="error"
      class="text-sm text-red-600"
    >
      {{ error }}
    </div>

    <!-- Empty state -->
    <div
      v-if="!loading && logs.length === 0"
      class="text-sm text-gray-500 border border-dashed rounded p-3"
    >
      No logs found for current filters.
    </div>

    <!-- Attempts table -->
    <AttemptsTable
      v-if="!loading && logs.length > 0 && filters.view === 'attempts'"
      :rows="(logs as AttemptRow[])"
    />

    <!-- Runs table -->
    <RunsTable
      v-if="!loading && logs.length > 0 && filters.view === 'runs'"
      :rows="(logs as RunRow[])"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import {
  AttemptsTable,
  RunsTable,
  type AttemptRow,
  type RunRow,
} from "./ai-log-viewer";

type ViewMode = "attempts" | "runs";

const filters = ref<{
  runId: string;
  toolId: string;
  materialId: string;
  view: ViewMode;
}>({
  runId: "",
  toolId: "",
  materialId: "",
  view: "attempts",
});

const logs = ref<Array<AttemptRow | RunRow>>([]);
const loading = ref(false);
const error = ref<string | null>(null);

const API_BASE = "/api/rmos/logs/ai";

async function loadLogs() {
  loading.value = true;
  error.value = null;
  logs.value = [];

  const params = new URLSearchParams();
  if (filters.value.runId) params.append("run_id", filters.value.runId);
  if (filters.value.toolId) params.append("tool_id", filters.value.toolId);
  if (filters.value.materialId)
    params.append("material_id", filters.value.materialId);
  params.append("limit", "100");

  const endpoint =
    filters.value.view === "attempts"
      ? `${API_BASE}/attempts`
      : `${API_BASE}/runs`;

  try {
    const res = await fetch(`${endpoint}?${params.toString()}`);
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }
    const data = await res.json();
    logs.value = data;
  } catch (e: any) {
    console.error(e);
    error.value = "Failed to load logs. Check console for details.";
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  loadLogs();
});
</script>

<style scoped>
.rmos-log-viewer {
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI",
    sans-serif;
}
</style>
