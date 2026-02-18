<script setup lang="ts">
/**
 * EnergyHeatPanel.vue - M.3 Energy & Heat display panel
 *
 * Shows energy totals, heat partition bar, and cumulative energy chart.
 *
 * Example:
 * ```vue
 * <EnergyHeatPanel
 *   v-model:material-id="materialId"
 *   :has-toolpath="moves.length > 0"
 *   :energy-out="energyOut"
 *   :chip-pct="chipPct"
 *   :tool-pct="toolPct"
 *   :work-pct="workPct"
 *   :energy-polyline="energyPolyline"
 *   @run-energy="runEnergy"
 *   @export-csv="exportEnergyCsv"
 * />
 * ```
 */

export interface EnergyTotals {
  volume_mm3: number;
  energy_j: number;
  heat: {
    chip_j: number;
    tool_j: number;
    work_j: number;
  };
}

export interface EnergyOutput {
  totals: EnergyTotals;
}

const props = defineProps<{
  materialId: string;
  hasToolpath: boolean;
  energyOut: EnergyOutput | null;
  chipPct: number;
  toolPct: number;
  workPct: number;
  energyPolyline: string;
}>();

const emit = defineEmits<{
  "update:materialId": [value: string];
  runEnergy: [];
  exportCsv: [];
}>();

function onMaterialChange(event: Event) {
  const target = event.target as HTMLSelectElement;
  emit("update:materialId", target.value);
}
</script>

<template>
  <div class="mt-4 border rounded-xl p-3">
    <div class="flex items-center justify-between mb-3">
      <h3 class="font-semibold text-sm">
        Energy & Heat
      </h3>
      <div class="flex items-center gap-2">
        <select
          :value="materialId"
          class="border px-2 py-1 rounded text-xs"
          @change="onMaterialChange"
        >
          <option value="maple_hard">
            Maple (hard)
          </option>
          <option value="mahogany">
            Mahogany
          </option>
          <option value="al_6061">
            Al 6061
          </option>
          <option value="custom">
            Custom
          </option>
        </select>
        <button
          class="px-3 py-1 border rounded text-xs bg-emerald-600 text-white hover:bg-emerald-700"
          :disabled="!hasToolpath"
          @click="$emit('runEnergy')"
        >
          Compute
        </button>
        <button
          class="px-3 py-1 border rounded text-xs bg-white hover:bg-gray-50"
          :disabled="!energyOut"
          @click="$emit('exportCsv')"
        >
          Export CSV
        </button>
      </div>
    </div>

    <div
      v-if="energyOut"
      class="mt-3 grid md:grid-cols-3 gap-3"
    >
      <!-- Totals Card -->
      <div class="border rounded p-2 text-sm bg-white">
        <div class="font-medium mb-2">
          Totals
        </div>
        <div>Volume: <b>{{ energyOut.totals.volume_mm3.toFixed(0) }} mm³</b></div>
        <div>Energy: <b>{{ energyOut.totals.energy_j.toFixed(1) }} J</b></div>
        <div class="mt-2 text-xs text-gray-600">
          <div>Heat (J):</div>
          <div>• chip {{ energyOut.totals.heat.chip_j.toFixed(1) }}</div>
          <div>• tool {{ energyOut.totals.heat.tool_j.toFixed(1) }}</div>
          <div>• work {{ energyOut.totals.heat.work_j.toFixed(1) }}</div>
        </div>
      </div>

      <!-- Heat Partition Bar -->
      <div class="border rounded p-2 bg-white">
        <div class="text-sm font-medium mb-2">
          Heat Partition
        </div>
        <div class="w-full h-5 bg-slate-100 rounded overflow-hidden flex">
          <div
            :style="{ width: chipPct + '%' }"
            class="bg-amber-400"
            :title="`Chip: ${chipPct.toFixed(1)}%`"
          />
          <div
            :style="{ width: toolPct + '%' }"
            class="bg-rose-400"
            :title="`Tool: ${toolPct.toFixed(1)}%`"
          />
          <div
            :style="{ width: workPct + '%' }"
            class="bg-emerald-400"
            :title="`Work: ${workPct.toFixed(1)}%`"
          />
        </div>
        <div class="text-xs mt-2 flex gap-3">
          <span class="inline-flex items-center gap-1">
            <i class="w-3 h-3 bg-amber-400 inline-block rounded" />
            chip {{ chipPct.toFixed(0) }}%
          </span>
          <span class="inline-flex items-center gap-1">
            <i class="w-3 h-3 bg-rose-400 inline-block rounded" />
            tool {{ toolPct.toFixed(0) }}%
          </span>
          <span class="inline-flex items-center gap-1">
            <i class="w-3 h-3 bg-emerald-400 inline-block rounded" />
            work {{ workPct.toFixed(0) }}%
          </span>
        </div>
      </div>

      <!-- Cumulative Energy Chart -->
      <div class="border rounded p-2 bg-white">
        <div class="text-sm font-medium mb-2">
          Cumulative Energy
        </div>
        <svg
          viewBox="0 0 300 120"
          class="w-full h-28"
        >
          <polyline
            :points="energyPolyline"
            fill="none"
            stroke="currentColor"
            stroke-width="1.5"
          />
        </svg>
      </div>
    </div>
  </div>
</template>
