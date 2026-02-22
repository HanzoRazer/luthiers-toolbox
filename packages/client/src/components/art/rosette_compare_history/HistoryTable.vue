<template>
  <div class="overflow-x-auto mt-2">
    <table class="min-w-full text-[11px] text-left">
      <thead class="border-b bg-gray-50">
        <tr>
          <th class="px-2 py-1 whitespace-nowrap">
            Time
          </th>
          <th class="px-2 py-1 whitespace-nowrap">
            Baseline
          </th>
          <th class="px-2 py-1 whitespace-nowrap text-right">
            Base
          </th>
          <th class="px-2 py-1 whitespace-nowrap text-right">
            Curr
          </th>
          <th class="px-2 py-1 whitespace-nowrap text-right text-emerald-700">
            +Add
          </th>
          <th class="px-2 py-1 whitespace-nowrap text-right text-rose-700">
            -Rem
          </th>
          <th class="px-2 py-1 whitespace-nowrap text-right">
            =Unch
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="(e, idx) in entries"
          :key="idx"
          class="border-b last:border-0 hover:bg-gray-50"
        >
          <td class="px-2 py-1 whitespace-nowrap">
            {{ formatTime(e.ts) }}
          </td>
          <td class="px-2 py-1 whitespace-nowrap font-mono text-[10px]">
            {{ e.baseline_id.slice(0, 8) }}…
          </td>
          <td class="px-2 py-1 text-right">
            {{ e.baseline_path_count }}
          </td>
          <td class="px-2 py-1 text-right">
            {{ e.current_path_count }}
          </td>
          <td class="px-2 py-1 text-right text-emerald-700">
            {{ e.added_paths }}
          </td>
          <td class="px-2 py-1 text-right text-rose-700">
            {{ e.removed_paths }}
          </td>
          <td class="px-2 py-1 text-right">
            {{ e.unchanged_paths }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
interface CompareHistoryEntry {
  ts: string
  job_id: string | null
  lane: string
  baseline_id: string
  baseline_path_count: number
  current_path_count: number
  added_paths: number
  removed_paths: number
  unchanged_paths: number
  preset?: string | null
}

defineProps<{
  entries: CompareHistoryEntry[]
}>()

function formatTime(ts: string): string {
  try {
    const d = new Date(ts)
    return d.toLocaleString()
  } catch {
    return ts
  }
}
</script>
