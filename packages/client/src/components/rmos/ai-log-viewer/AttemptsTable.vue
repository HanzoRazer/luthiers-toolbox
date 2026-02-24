<script setup lang="ts">
/**
 * AttemptsTable.vue - AI log attempts table display
 * Extracted from RmosAiLogViewer.vue
 */

export interface AttemptRow {
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
}

defineProps<{
  rows: AttemptRow[];
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
      Attempts ({{ rows.length }})
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
            v-for="row in rows"
            :key="`attempt-${row.run_id}-${row.attempt_index}-${row.timestamp}`"
          >
            <td class="px-2 py-1 border whitespace-nowrap">
              {{ prettyTime(row.timestamp) }}
            </td>
            <td class="px-2 py-1 border font-mono text-[10px]">
              {{ row.run_id }}
            </td>
            <td class="px-2 py-1 border text-center">
              {{ row.attempt_index }}
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
              {{ (row.score || 0).toFixed(3) }}
            </td>
            <td class="px-2 py-1 border text-center">
              {{ row.risk_bucket }}
            </td>
            <td
              class="px-2 py-1 border text-center"
              :class="row.is_acceptable ? 'text-green-600' : 'text-gray-500'"
            >
              {{ row.is_acceptable ? "Yes" : "No" }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
