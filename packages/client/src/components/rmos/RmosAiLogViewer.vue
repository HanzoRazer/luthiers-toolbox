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
    <div v-if="!loading && logs.length > 0 && filters.view === 'attempts'">
      <h3 class="text-sm font-semibold mb-2">
        Attempts ({{ logs.length }})
      </h3>
      <div class="overflow-x-auto">
        <table class="min-w-full text-xs border">
          <thead class="bg-gray-100">
            <tr>
              <th class="px-2 py-1 border">
                Time
              </th>
              <th class="px-2 py-1 border">
                Run ID
              </th>
              <th class="px-2 py-1 border">
                Attempt
              </th>
              <th class="px-2 py-1 border">
                Mode
              </th>
              <th class="px-2 py-1 border">
                Tool
              </th>
              <th class="px-2 py-1 border">
                Material
              </th>
              <th class="px-2 py-1 border">
                Engine
              </th>
              <th class="px-2 py-1 border">
                Score
              </th>
              <th class="px-2 py-1 border">
                Risk
              </th>
              <th class="px-2 py-1 border">
                Acceptable
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="row in logs"
              :key="`attempt-${row.run_id}-${(row as any).attempt_index}-${row.timestamp}`"
            >
              <td class="px-2 py-1 border whitespace-nowrap">
                {{ prettyTime(row.timestamp) }}
              </td>
              <td class="px-2 py-1 border font-mono text-[10px]">
                {{ row.run_id }}
              </td>
              <td class="px-2 py-1 border text-center">
                {{ (row as any).attempt_index }}
              </td>
              <td class="px-2 py-1 border">
                {{ row.workflow_mode }}
              </td>
              <td class="px-2 py-1 border">
                {{ row.tool_id || "—" }}
              </td>
              <td class="px-2 py-1 border">
                {{ row.material_id || "—" }}
              </td>
              <td class="px-2 py-1 border">
                {{ row.geometry_engine || "—" }}
              </td>
              <td class="px-2 py-1 border text-right">
                {{ ((row as any).score || 0).toFixed(3) }}
              </td>
              <td class="px-2 py-1 border text-center">
                {{ (row as any).risk_bucket }}
              </td>
              <td
                class="px-2 py-1 border text-center"
                :class="(row as any).is_acceptable ? 'text-green-600' : 'text-gray-500'"
              >
                {{ (row as any).is_acceptable ? "Yes" : "No" }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Runs table -->
    <div v-if="!loading && logs.length > 0 && filters.view === 'runs'">
      <h3 class="text-sm font-semibold mb-2">
        Runs ({{ logs.length }})
      </h3>
      <div class="overflow-x-auto">
        <table class="min-w-full text-xs border">
          <thead class="bg-gray-100">
            <tr>
              <th class="px-2 py-1 border">
                Time
              </th>
              <th class="px-2 py-1 border">
                Run ID
              </th>
              <th class="px-2 py-1 border">
                Mode
              </th>
              <th class="px-2 py-1 border">
                Tool
              </th>
              <th class="px-2 py-1 border">
                Material
              </th>
              <th class="px-2 py-1 border">
                Engine
              </th>
              <th class="px-2 py-1 border">
                Attempts
              </th>
              <th class="px-2 py-1 border">
                Max
              </th>
              <th class="px-2 py-1 border">
                Score
              </th>
              <th class="px-2 py-1 border">
                Risk
              </th>
              <th class="px-2 py-1 border">
                Success
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="row in logs"
              :key="`run-${row.run_id}-${row.timestamp}`"
            >
              <td class="px-2 py-1 border whitespace-nowrap">
                {{ prettyTime(row.timestamp) }}
              </td>
              <td class="px-2 py-1 border font-mono text-[10px]">
                {{ row.run_id }}
              </td>
              <td class="px-2 py-1 border">
                {{ row.workflow_mode }}
              </td>
              <td class="px-2 py-1 border">
                {{ row.tool_id || "—" }}
              </td>
              <td class="px-2 py-1 border">
                {{ row.material_id || "—" }}
              </td>
              <td class="px-2 py-1 border">
                {{ row.geometry_engine || "—" }}
              </td>
              <td class="px-2 py-1 border text-center">
                {{ (row as any).attempts }}
              </td>
              <td class="px-2 py-1 border text-center">
                {{ (row as any).max_attempts }}
              </td>
              <td class="px-2 py-1 border text-right">
                {{
                  (row as any).selected_score != null
                    ? (row as any).selected_score.toFixed(3)
                    : "—"
                }}
              </td>
              <td class="px-2 py-1 border text-center">
                {{ (row as any).selected_risk_bucket || "—" }}
              </td>
              <td
                class="px-2 py-1 border text-center"
                :class="(row as any).success ? 'text-green-600' : 'text-red-600'"
              >
                {{ (row as any).success ? "Yes" : "No" }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";

type AttemptRow = {
  run_id: string;
  timestamp: string;
  attempt_index: number;
  workflow_mode: string;
  tool_id?: string | null;
  material_id?: string | null;
  machine_id?: string | null;
  geometry_engine?: string | null;
  score: number;
  risk_bucket: string;
  is_acceptable: boolean;
  design_version?: string | null;
  ring_count?: number | null;
  notes?: string | null;
};

type RunRow = {
  run_id: string;
  timestamp: string;
  workflow_mode: string;
  max_attempts: number;
  time_limit_seconds: number;
  attempts: number;
  success: boolean;
  reason: string;
  selected_score?: number | null;
  selected_risk_bucket?: string | null;
  tool_id?: string | null;
  material_id?: string | null;
  machine_id?: string | null;
  geometry_engine?: string | null;
};

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

function prettyTime(raw: string) {
  try {
    const d = new Date(raw);
    return d.toLocaleString();
  } catch {
    return raw;
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
