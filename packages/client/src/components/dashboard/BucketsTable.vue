<script setup lang="ts">
/**
 * BucketsTable.vue - Risk buckets table with sparklines
 *
 * Displays aggregated risk buckets with trend sparklines.
 *
 * Example:
 * ```vue
 * <BucketsTable
 *   :buckets="filteredBuckets"
 *   @select-bucket="loadBucketDetails"
 *   @go-to-lab="goToLab"
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
  addedSeries: number[];
  removedSeries: number[];
  addedPath: string;
  removedPath: string;
}

const props = withDefaults(
  defineProps<{
    buckets: Bucket[];
    sparkWidth?: number;
    sparkHeight?: number;
  }>(),
  {
    sparkWidth: 60,
    sparkHeight: 20,
  }
);

const emit = defineEmits<{
  selectBucket: [bucket: Bucket];
  goToLab: [bucket: Bucket];
}>();

function riskChipClass(score: number): string {
  if (score < 1) return "bg-emerald-50 text-emerald-700 border border-emerald-200";
  if (score < 3) return "bg-amber-50 text-amber-700 border border-amber-200";
  if (score < 6) return "bg-orange-50 text-orange-700 border border-orange-200";
  return "bg-rose-50 text-rose-700 border border-rose-200";
}
</script>

<template>
  <div
    v-if="buckets.length"
    class="overflow-x-auto"
  >
    <table class="min-w-full text-[11px] text-left">
      <thead class="border-b bg-gray-50">
        <tr>
          <th class="px-2 py-1 whitespace-nowrap">
            Lane
          </th>
          <th class="px-2 py-1 whitespace-nowrap">
            Preset
          </th>
          <th class="px-2 py-1 whitespace-nowrap text-right">
            Entries
          </th>
          <th class="px-2 py-1 whitespace-nowrap text-right">
            Avg +Added
          </th>
          <th class="px-2 py-1 whitespace-nowrap text-right">
            Avg -Removed
          </th>
          <th class="px-2 py-1 whitespace-nowrap text-right">
            Avg =Unchanged
          </th>
          <th class="px-2 py-1 whitespace-nowrap">
            Risk
          </th>
          <th class="px-2 py-1 whitespace-nowrap">
            Trend (Added)
          </th>
          <th class="px-2 py-1 whitespace-nowrap">
            Trend (Removed)
          </th>
          <th class="px-2 py-1 whitespace-nowrap">
            Actions
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="bucket in buckets"
          :key="bucket.key"
          class="border-b last:border-0 hover:bg-gray-50"
        >
          <td
            class="px-2 py-1 whitespace-nowrap cursor-pointer"
            :title="`Open ${bucket.lane} lab for preset '${bucket.preset}'`"
            @click="$emit('goToLab', bucket)"
          >
            {{ bucket.lane }}
          </td>
          <td
            class="px-2 py-1 whitespace-nowrap cursor-pointer"
            :title="`Open ${bucket.lane} lab for preset '${bucket.preset}'`"
            @click="$emit('goToLab', bucket)"
          >
            {{ bucket.preset }}
          </td>
          <td class="px-2 py-1 text-right">
            {{ bucket.count }}
          </td>
          <td class="px-2 py-1 text-right text-emerald-700">
            {{ bucket.avgAdded.toFixed(1) }}
          </td>
          <td class="px-2 py-1 text-right text-rose-700">
            {{ bucket.avgRemoved.toFixed(1) }}
          </td>
          <td class="px-2 py-1 text-right">
            {{ bucket.avgUnchanged.toFixed(1) }}
          </td>
          <td class="px-2 py-1 whitespace-nowrap">
            <span
              class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium"
              :class="riskChipClass(bucket.riskScore)"
            >
              {{ bucket.riskLabel }}
            </span>
          </td>
          <td class="px-2 py-1 whitespace-nowrap">
            <svg
              :width="sparkWidth"
              :height="sparkHeight"
              viewBox="0 0 60 20"
            >
              <polyline
                v-if="bucket.addedPath"
                :points="bucket.addedPath"
                fill="none"
                stroke="#22c55e"
                stroke-width="1.2"
              />
            </svg>
          </td>
          <td class="px-2 py-1 whitespace-nowrap">
            <svg
              :width="sparkWidth"
              :height="sparkHeight"
              viewBox="0 0 60 20"
            >
              <polyline
                v-if="bucket.removedPath"
                :points="bucket.removedPath"
                fill="none"
                stroke="#ef4444"
                stroke-width="1.2"
              />
            </svg>
          </td>
          <td class="px-2 py-1 whitespace-nowrap">
            <button
              class="px-2 py-0.5 rounded border text-[10px] text-gray-700 hover:bg-gray-100"
              @click="$emit('selectBucket', bucket)"
            >
              Details
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
