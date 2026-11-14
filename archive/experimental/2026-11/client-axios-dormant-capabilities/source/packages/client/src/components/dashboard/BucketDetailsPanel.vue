<script setup lang="ts">
/**
 * BucketDetailsPanel.vue - Bucket drill-down details panel
 *
 * Shows individual entries for a selected risk bucket.
 *
 * Example:
 * ```vue
 * <BucketDetailsPanel
 *   :bucket="selectedBucket"
 *   :entries="bucketEntries"
 *   :loading="bucketEntriesLoading"
 *   :error="bucketEntriesError"
 *   :job-filter="jobFilter"
 *   @export-csv="exportBucketCsv"
 *   @download-json="downloadBucketJson"
 *   @close="clearBucketDetails"
 * />
 * ```
 */

export interface Bucket {
  key: string;
  lane: string;
  preset: string;
  count: number;
  avgAdded: number;
  avgRemoved: number;
  avgUnchanged: number;
  riskScore: number;
  riskLabel: string;
}

export interface BucketEntry {
  ts: string;
  job_id: string | null;
  lane: string;
  preset: string | null;
  baseline_id: string;
  baseline_path_count: number;
  current_path_count: number;
  added_paths: number;
  removed_paths: number;
  unchanged_paths: number;
}

defineProps<{
  bucket: Bucket | null;
  entries: BucketEntry[];
  loading: boolean;
  error: string | null;
  jobFilter?: string;
}>();

defineEmits<{
  exportCsv: [];
  downloadJson: [];
  close: [];
}>();

function formatTime(ts: string): string {
  try {
    const d = new Date(ts);
    return d.toLocaleString();
  } catch {
    return ts;
  }
}
</script>

<template>
  <div
    v-if="bucket"
    class="mt-3 border rounded bg-white shadow-sm p-3 flex flex-col gap-2 text-[11px]"
  >
    <div class="flex items-center justify-between gap-2">
      <div>
        <div class="font-semibold text-gray-900">
          Bucket Details – {{ bucket.lane }} / {{ bucket.preset }}
        </div>
        <div class="text-[10px] text-gray-600">
          Showing underlying compare snapshots for this lane + preset.
          <span v-if="jobFilter">
            Filtered by job hint: <span class="font-mono">{{ jobFilter }}</span>
          </span>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <button
          class="px-2 py-0.5 rounded border text-[10px] text-gray-700 hover:bg-gray-100 disabled:opacity-50"
          :disabled="!entries.length"
          @click="$emit('exportCsv')"
        >
          Export entries CSV
        </button>
        <button
          class="px-2 py-0.5 rounded border text-[10px] text-gray-700 hover:bg-gray-100"
          @click="$emit('downloadJson')"
        >
          Download JSON report
        </button>
        <button
          class="px-2 py-0.5 rounded border text-[10px] text-gray-700 hover:bg-gray-100"
          @click="$emit('close')"
        >
          Close
        </button>
      </div>
    </div>

    <div
      v-if="loading"
      class="text-[10px] text-gray-500 italic"
    >
      Loading bucket entries…
    </div>
    <div
      v-else-if="error"
      class="text-[10px] text-rose-600"
    >
      {{ error }}
    </div>
    <div
      v-else-if="!entries.length"
      class="text-[10px] text-gray-500 italic"
    >
      No entries found for this bucket (with current job hint).
    </div>
    <div
      v-else
      class="overflow-x-auto max-h-64 border-t pt-2"
    >
      <table class="min-w-full text-[10px] text-left">
        <thead>
          <tr class="border-b bg-gray-50">
            <th class="px-2 py-1 whitespace-nowrap">
              Time
            </th>
            <th class="px-2 py-1 whitespace-nowrap">
              Job ID
            </th>
            <th class="px-2 py-1 whitespace-nowrap text-right">
              Baseline
            </th>
            <th class="px-2 py-1 whitespace-nowrap text-right">
              Current
            </th>
            <th class="px-2 py-1 whitespace-nowrap text-right">
              +Added
            </th>
            <th class="px-2 py-1 whitespace-nowrap text-right">
              -Removed
            </th>
            <th class="px-2 py-1 whitespace-nowrap text-right">
              =Unchanged
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="entry in entries"
            :key="entry.ts + '::' + (entry.job_id || '') + '::' + entry.baseline_id"
            class="border-b last:border-0"
          >
            <td class="px-2 py-1 whitespace-nowrap">
              {{ formatTime(entry.ts) }}
            </td>
            <td class="px-2 py-1 whitespace-nowrap font-mono">
              {{ entry.job_id || '—' }}
            </td>
            <td class="px-2 py-1 text-right font-mono">
              {{ entry.baseline_path_count }}
            </td>
            <td class="px-2 py-1 text-right font-mono">
              {{ entry.current_path_count }}
            </td>
            <td class="px-2 py-1 text-right text-emerald-700 font-mono">
              {{ entry.added_paths }}
            </td>
            <td class="px-2 py-1 text-right text-rose-700 font-mono">
              {{ entry.removed_paths }}
            </td>
            <td class="px-2 py-1 text-right font-mono">
              {{ entry.unchanged_paths }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
