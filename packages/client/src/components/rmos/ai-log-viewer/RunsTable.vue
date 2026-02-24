<script setup lang="ts">
/**
 * RunsTable.vue - AI log runs table display
 * Extracted from RmosAiLogViewer.vue
 */

export interface RunRow {
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
}

defineProps<{
  rows: RunRow[];
}>();

function prettyTime(raw: string): string {
  try {
    const d = new Date(raw);
    return d.toLocaleString();
  } catch {
    return raw;
  }
}
</script>

<template>
  <div>
    <h3 class="text-sm font-semibold mb-2">
      Runs ({{ rows.length }})
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
            v-for="row in rows"
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
              {{ row.attempts }}
            </td>
            <td class="px-2 py-1 border text-center">
              {{ row.max_attempts }}
            </td>
            <td class="px-2 py-1 border text-right">
              {{ row.selected_score != null ? row.selected_score.toFixed(3) : "—" }}
            </td>
            <td class="px-2 py-1 border text-center">
              {{ row.selected_risk_bucket || "—" }}
            </td>
            <td
              class="px-2 py-1 border text-center"
              :class="row.success ? 'text-green-600' : 'text-red-600'"
            >
              {{ row.success ? "Yes" : "No" }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
