<template>
  <div class="border rounded-lg p-3 space-y-3 text-xs">
    <header class="flex items-center justify-between">
      <div>
        <h2 class="text-sm font-semibold">
          Manufacturing Plan
        </h2>
        <p class="text-gray-500">
          Compute tile & strip requirements for this pattern.
        </p>
      </div>
      <button
        class="border rounded px-2 py-1 hover:bg-gray-100"
        :disabled="store.loading || !patternId"
        @click="requestPlan"
      >
        {{ store.loading ? 'Planning…' : 'Generate plan' }}
      </button>
    </header>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
      <div class="space-y-2">
        <label class="block">
          Guitars
          <input
            v-model.number="guitars"
            type="number"
            min="1"
            class="mt-1 w-full border rounded px-2 py-1"
          >
        </label>
        <label class="block">
          Tile length (mm)
          <input
            v-model.number="tileLength"
            type="number"
            step="0.1"
            class="mt-1 w-full border rounded px-2 py-1"
          >
        </label>
        <label class="block">
          Scrap factor
          <input
            v-model.number="scrapFactor"
            type="number"
            step="0.01"
            class="mt-1 w-full border rounded px-2 py-1"
          >
        </label>
      </div>

      <div
        v-if="plan"
        class="space-y-1"
      >
        <p>
          <span class="font-semibold">Pattern:</span> {{ plan.pattern.name }}
        </p>
        <p>
          <span class="font-semibold">Guitars:</span> {{ plan.guitars }}
        </p>
        <p>
          <span class="font-semibold">Strip families:</span>
          {{ plan.strip_plans.length }}
        </p>
      </div>

      <div
        v-if="plan?.notes"
        class="text-gray-600"
      >
        {{ plan.notes }}
      </div>
    </div>

    <div
      v-if="plan"
      class="grid grid-cols-1 md:grid-cols-2 gap-3"
    >
      <div>
        <h3 class="font-semibold mb-1">
          Per-ring requirements
        </h3>
        <table class="w-full border-collapse">
          <thead>
            <tr class="border-b">
              <th class="text-left p-1">
                Ring
              </th>
              <th class="text-left p-1">
                Family
              </th>
              <th class="text-left p-1">
                Circ (mm)
              </th>
              <th class="text-left p-1">
                Tiles/gtr
              </th>
              <th class="text-left p-1">
                Total
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="r in plan.ring_requirements"
              :key="r.ring_index"
              class="border-b last:border-0"
            >
              <td class="p-1">
                {{ r.ring_index }}
              </td>
              <td class="p-1">
                {{ r.strip_family_id }}
              </td>
              <td class="p-1">
                {{ r.circumference_mm.toFixed(1) }}
              </td>
              <td class="p-1">
                {{ r.tiles_per_guitar }}
              </td>
              <td class="p-1">
                {{ r.total_tiles }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div>
        <h3 class="font-semibold mb-1">
          Per-strip-family plan
        </h3>
        <table class="w-full border-collapse">
          <thead>
            <tr class="border-b">
              <th class="text-left p-1">
                Family
              </th>
              <th class="text-left p-1">
                Tiles
              </th>
              <th class="text-left p-1">
                m total
              </th>
              <th class="text-left p-1">
                Sticks
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="sp in plan.strip_plans"
              :key="sp.strip_family_id"
              class="border-b last:border-0"
            >
              <td class="p-1">
                {{ sp.strip_family_id }}
                <span
                  v-if="sp.color_hint"
                  class="text-gray-500"
                >
                  ({{ sp.color_hint }})
                </span>
              </td>
              <td class="p-1">
                {{ sp.total_tiles_needed }}
              </td>
              <td class="p-1">
                {{ sp.total_strip_length_m.toFixed(2) }}
              </td>
              <td class="p-1">
                {{ sp.sticks_needed }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <p
      v-if="store.error"
      class="text-xs text-red-600"
    >
      {{ store.error }}
    </p>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useManufacturingPlanStore } from '@/stores/useManufacturingPlanStore';

const props = defineProps<{
  patternId: string | null;
}>();

const store = useManufacturingPlanStore();

const guitars = ref(4);
const tileLength = ref(8.0);
const scrapFactor = ref(0.12);

const plan = computed(() => store.currentPlan);

async function requestPlan() {
  if (!props.patternId) return;
  await store.fetchPlan({
    pattern_id: props.patternId,
    guitars: guitars.value,
    tile_length_mm: tileLength.value,
    scrap_factor: scrapFactor.value,
    record_joblog: true,
  });
}
</script>
