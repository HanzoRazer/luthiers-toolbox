<template>
  <div class="border rounded-lg p-3 space-y-2 text-xs">
    <div class="flex items-center justify-between">
      <h2 class="text-sm font-semibold">Rosette Pattern Library</h2>
      <button
        class="border rounded px-2 py-1 hover:bg-gray-100"
        @click="createQuickPattern"
      >
        + New
      </button>
    </div>

    <div v-if="store.loading" class="text-gray-500">
      Loading patterns…
    </div>
    <div v-else-if="store.patterns.length === 0" class="text-gray-500">
      No patterns yet.
    </div>

    <ul v-else class="divide-y">
      <li
        v-for="p in store.patterns"
        :key="p.id"
        class="py-1 flex items-center justify-between"
      >
        <button
          class="text-left flex-1 hover:underline"
          :class="p.id === store.selectedPatternId ? 'font-semibold' : ''"
          @click="selectPattern(p.id)"
        >
          {{ p.name }}
          <span class="text-gray-400">({{ p.id }})</span>
        </button>
        <button
          class="ml-2 text-red-500 hover:underline"
          @click="deletePattern(p.id)"
        >
          Delete
        </button>
      </li>
    </ul>

    <p v-if="store.error" class="text-red-600">
      {{ store.error }}
    </p>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useRosettePatternStore } from '@/stores/useRosettePatternStore';
import type { RosettePattern } from '@/models/rmos';

const emit = defineEmits<{
  (e: 'pattern-selected', pattern: RosettePattern | null): void;
}>();

const store = useRosettePatternStore();

onMounted(async () => {
  await store.fetchPatterns();
  emit('pattern-selected', store.selectedPattern);
});

function selectPattern(id: string) {
  store.selectPattern(id);
  emit('pattern-selected', store.selectedPattern);
}

async function deletePattern(id: string) {
  if (!confirm(`Delete pattern ${id}?`)) return;
  await store.deletePattern(id);
  emit('pattern-selected', store.selectedPattern);
}

async function createQuickPattern() {
  const id = prompt('Pattern id (e.g. rosette_default):');
  if (!id) return;
  const name = prompt('Pattern name:', 'New Rosette Pattern') ?? 'New Rosette Pattern';
  const pattern: RosettePattern = {
    id,
    name,
    center_x_mm: 0,
    center_y_mm: 0,
    ring_bands: [],
    default_slice_thickness_mm: 1.0,
    default_passes: 1,
    default_workholding: 'vacuum',
    default_tool_id: 'saw_default',
  };
  await store.createPattern(pattern);
  emit('pattern-selected', store.selectedPattern);
}
</script>
