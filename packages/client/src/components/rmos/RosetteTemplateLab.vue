<template>
  <div class="space-y-4">
    <header class="flex items-center justify-between">
      <div>
        <h2 class="text-lg font-semibold">
          Rosette Manufacturing OS
        </h2>
        <p class="text-sm text-gray-500">
          Edit rings, strip families, and defaults. Batch op updates automatically.
        </p>
      </div>
    </header>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <!-- Pattern meta -->
      <div class="space-y-2 border rounded-lg p-3">
        <h3 class="font-semibold text-sm">
          Pattern Info
        </h3>
        <label class="block text-xs">
          Name
          <input
            v-model="localPattern.name"
            type="text"
            class="mt-1 w-full border rounded px-2 py-1 text-sm"
          >
        </label>
        <div class="grid grid-cols-2 gap-2">
          <label class="block text-xs">
            Center X (mm)
            <input
              v-model.number="localPattern.center_x_mm"
              type="number"
              class="mt-1 w-full border rounded px-2 py-1 text-sm"
            >
          </label>
          <label class="block text-xs">
            Center Y (mm)
            <input
              v-model.number="localPattern.center_y_mm"
              type="number"
              class="mt-1 w-full border rounded px-2 py-1 text-sm"
            >
          </label>
        </div>
        <div class="grid grid-cols-2 gap-2">
          <label class="block text-xs">
            Default slice thickness (mm)
            <input
              v-model.number="localPattern.default_slice_thickness_mm"
              type="number"
              step="0.01"
              class="mt-1 w-full border rounded px-2 py-1 text-sm"
            >
          </label>
          <label class="block text-xs">
            Passes
            <input
              v-model.number="localPattern.default_passes"
              type="number"
              class="mt-1 w-full border rounded px-2 py-1 text-sm"
            >
          </label>
        </div>
        <label class="block text-xs">
          Default workholding
          <input
            v-model="localPattern.default_workholding"
            type="text"
            class="mt-1 w-full border rounded px-2 py-1 text-sm"
          >
        </label>
        <label class="block text-xs">
          Default tool id
          <input
            v-model="localPattern.default_tool_id"
            type="text"
            class="mt-1 w-full border rounded px-2 py-1 text-sm"
          >
        </label>
      </div>

      <!-- Rings table -->
      <div class="space-y-2 border rounded-lg p-3">
        <div class="flex items-center justify-between">
          <h3 class="font-semibold text-sm">
            Rings
          </h3>
          <button
            class="text-xs border rounded px-2 py-1 hover:bg-gray-100"
            @click="addRing"
          >
            + Add ring
          </button>
        </div>

        <div
          v-if="localPattern.ring_bands.length === 0"
          class="text-xs text-gray-500"
        >
          No rings yet. Add one to get started.
        </div>

        <table
          v-else
          class="w-full text-xs border-collapse"
        >
          <thead>
            <tr class="border-b">
              <th class="text-left p-1">
                Idx
              </th>
              <th class="text-left p-1">
                Radius
              </th>
              <th class="text-left p-1">
                Width
              </th>
              <th class="text-left p-1">
                Family
              </th>
              <th class="text-left p-1">
                Angle
              </th>
              <th class="text-left p-1">
                Tile L
              </th>
              <th class="text-left p-1">
                Color
              </th>
              <th class="p-1" />
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="ring in sortedRings"
              :key="ring.id"
              class="border-b last:border-0"
            >
              <td class="p-1">
                <input
                  v-model.number="ring.index"
                  type="number"
                  class="w-12 border rounded px-1 py-0.5"
                >
              </td>
              <td class="p-1">
                <input
                  v-model.number="ring.radius_mm"
                  type="number"
                  step="0.1"
                  class="w-16 border rounded px-1 py-0.5"
                >
              </td>
              <td class="p-1">
                <input
                  v-model.number="ring.width_mm"
                  type="number"
                  step="0.1"
                  class="w-16 border rounded px-1 py-0.5"
                >
              </td>
              <td class="p-1">
                <input
                  v-model="ring.strip_family_id"
                  type="text"
                  class="w-24 border rounded px-1 py-0.5"
                >
              </td>
              <td class="p-1">
                <input
                  v-model.number="ring.slice_angle_deg"
                  type="number"
                  step="1"
                  class="w-16 border rounded px-1 py-0.5"
                >
              </td>
              <td class="p-1">
                <input
                  v-model.number="ring.tile_length_override_mm"
                  type="number"
                  step="0.1"
                  class="w-16 border rounded px-1 py-0.5"
                >
              </td>
              <td class="p-1">
                <input
                  v-model="ring.color_hint"
                  type="text"
                  class="w-20 border rounded px-1 py-0.5"
                >
              </td>
              <td class="p-1 text-right">
                <button
                  class="text-red-500 hover:underline"
                  @click="removeRing(ring.id)"
                >
                  ✕
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Small preview of generated batch op -->
    <div class="border rounded-lg p-3 text-xs bg-gray-50">
      <h3 class="font-semibold mb-1">
        Derived Saw Batch Op (circle mode)
      </h3>
      <pre class="overflow-x-auto whitespace-pre-wrap">
{{ JSON.stringify(currentBatchOp, null, 2) }}
      </pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, watch } from 'vue';
import { nanoid } from 'nanoid';
import type { RosettePattern, RosetteRingBand, SawSliceBatchOpCircle } from '@/models/rmos';

const props = defineProps<{
  pattern: RosettePattern;
}>();

const emit = defineEmits<{
  (e: 'update:pattern', value: RosettePattern): void;
  (e: 'update:batchOp', value: SawSliceBatchOpCircle): void;
}>();

const localPattern = reactive<RosettePattern>(structuredClone(props.pattern));

watch(
  () => props.pattern,
  (val) => {
    Object.assign(localPattern, structuredClone(val));
  },
  { deep: true }
);

const sortedRings = computed(() =>
  [...localPattern.ring_bands].sort((a, b) => a.index - b.index)
);

function addRing() {
  const nextIndex = localPattern.ring_bands.length;
  const ring: RosetteRingBand = {
    id: nanoid(),
    index: nextIndex,
    radius_mm: 40 + nextIndex * 3,
    width_mm: 2,
    color_hint: '',
    strip_family_id: 'default_family',
    slice_angle_deg: 0,
    tile_length_override_mm: undefined,
  };
  localPattern.ring_bands.push(ring);
}

function removeRing(id: string) {
  const idx = localPattern.ring_bands.findIndex((r) => r.id === id);
  if (idx >= 0) {
    localPattern.ring_bands.splice(idx, 1);
  }
}

// Pattern → SawSliceBatchOpCircle derivation
const currentBatchOp = computed<SawSliceBatchOpCircle>(() => {
  const rings = sortedRings.value;
  const baseRadius = rings.length > 0 ? rings[0].radius_mm : 40;
  let radialStep = 1;
  if (rings.length > 1) {
    const diffs: number[] = [];
    for (let i = 1; i < rings.length; i++) {
      diffs.push(Math.abs(rings[i].radius_mm - rings[i - 1].radius_mm));
    }
    const avg = diffs.reduce((a, b) => a + b, 0) / diffs.length;
    radialStep = avg || 1;
  }

  return {
    id: `rosette_batch_${localPattern.id}`,
    op_type: 'saw_slice_batch',
    tool_id: localPattern.default_tool_id || 'saw_default',
    geometry_source: 'circle_param',
    base_circle: {
      center_x_mm: localPattern.center_x_mm,
      center_y_mm: localPattern.center_y_mm,
      radius_mm: baseRadius,
    },
    num_rings: rings.length || 1,
    radial_step_mm: radialStep,
    radial_sign: 1,
    slice_thickness_mm: localPattern.default_slice_thickness_mm,
    passes: localPattern.default_passes,
    material: 'hardwood',
    workholding: localPattern.default_workholding || 'vacuum',
  };
});

// Emit whenever pattern changes
watch(
  localPattern,
  () => {
    emit('update:pattern', structuredClone(localPattern));
    emit('update:batchOp', currentBatchOp.value);
  },
  { deep: true }
);
</script>
