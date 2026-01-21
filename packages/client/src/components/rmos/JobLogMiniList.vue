<template>
  <div class="border rounded-lg p-3 space-y-2 text-xs">
    <header class="flex items-center justify-between">
      <h2 class="text-sm font-semibold">
        JobLog
      </h2>
      <button
        class="border rounded px-2 py-1 hover:bg-gray-100"
        :disabled="store.loading"
        @click="store.fetchJobLog"
      >
        {{ store.loading ? 'Refreshing…' : 'Refresh' }}
      </button>
    </header>

    <p
      v-if="store.error"
      class="text-red-600"
    >
      {{ store.error }}
    </p>

    <div
      v-if="store.entries.length === 0 && !store.loading"
      class="text-gray-500"
    >
      No joblog entries yet.
    </div>

    <div
      v-else
      class="space-y-1 max-h-64 overflow-y-auto"
    >
      <div
        v-for="entry in store.entries"
        :key="entry.id"
        class="border rounded px-2 py-1 flex items-center justify-between"
      >
        <div class="flex-1">
          <p>
            <span
              class="px-1 py-0.5 rounded text-[11px] mr-1"
              :class="badgeClass(entry.job_type)"
            >
              {{ entry.job_type }}
            </span>
            <span class="text-gray-600">
              {{ truncateId(entry.id) }}
            </span>
          </p>
          <p class="text-[11px] text-gray-500">
            {{ formatDate(entry.created_at) }}
          </p>
        </div>
        <div class="text-right text-[11px]">
          <template v-if="entry.job_type === 'rosette_plan'">
            <p>Pattern: {{ (entry as any).plan_pattern_id }}</p>
            <p>Gtrs: {{ (entry as any).plan_guitars }}</p>
            <p>Tiles: {{ (entry as any).plan_total_tiles }}</p>
          </template>
          <template v-else>
            <p>Tool: {{ (entry as any).tool_id }}</p>
            <p>Slices: {{ (entry as any).num_slices }}</p>
            <p>Grade: {{ (entry as any).overall_risk_grade }}</p>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useJobLogStore } from '@/stores/useJobLogStore';

const store = useJobLogStore();

onMounted(() => {
  store.fetchJobLog();
});

function formatDate(iso: string) {
  try {
    const d = new Date(iso);
    return d.toLocaleString();
  } catch {
    return iso;
  }
}

function truncateId(id: string, len = 24) {
  return id.length > len ? id.slice(0, len) + '…' : id;
}

function badgeClass(jobType: string) {
  if (jobType === 'rosette_plan') return 'bg-blue-100 text-blue-700';
  if (jobType === 'saw_slice_batch') return 'bg-green-100 text-green-700';
  return 'bg-gray-100 text-gray-700';
}
</script>
