<script setup lang="ts">
/**
 * BottleneckMapPanel.vue - M.1.1 Bottleneck Map controls and pie chart
 *
 * Shows bottleneck map toggle, legend, export CSV, and pie chart.
 *
 * Example:
 * ```vue
 * <BottleneckMapPanel
 *   v-model:show-map="showBottleneckMap"
 *   :has-moves="!!planOut?.moves"
 *   :stats="planOut?.stats"
 *   @export-csv="exportBottleneckCsv"
 * />
 * ```
 */

import { computed } from "vue";

export interface BottleneckCaps {
  feed_cap: number;
  accel: number;
  jerk: number;
  none: number;
}

export interface PlanStats {
  caps?: BottleneckCaps;
}

const props = defineProps<{
  showMap: boolean;
  hasMoves: boolean;
  stats: PlanStats | null;
}>();

const emit = defineEmits<{
  "update:showMap": [value: boolean];
  exportCsv: [];
}>();

interface PieSlice {
  label: string;
  v: number;
  color: string;
  pct: number;
}

const capsPie = computed<PieSlice[]>(() => {
  const c = props.stats?.caps || { feed_cap: 0, accel: 0, jerk: 0, none: 0 };
  const total = Math.max(1, c.feed_cap + c.accel + c.jerk + c.none);
  return [
    { label: "Feed cap", v: c.feed_cap, color: "#f59e0b" },
    { label: "Accel", v: c.accel, color: "#14b8a6" },
    { label: "Jerk", v: c.jerk, color: "#ec4899" },
    { label: "None", v: c.none, color: "#9ca3af" },
  ].map((s) => ({ ...s, pct: s.v / total }));
});

function arcPath(index: number): string {
  const slices = capsPie.value;
  const tau = Math.PI * 2;
  let a0 = 0;
  for (let i = 0; i < index; i++) {
    a0 += slices[i].pct * tau;
  }
  const a1 = a0 + slices[index].pct * tau;
  const R = 50;
  const x0 = Math.cos(a0) * R;
  const y0 = Math.sin(a0) * R;
  const x1 = Math.cos(a1) * R;
  const y1 = Math.sin(a1) * R;
  const large = a1 - a0 > Math.PI ? 1 : 0;
  return `M0,0 L${x0},${y0} A${R},${R} 0 ${large} 1 ${x1},${y1} Z`;
}
</script>

<template>
  <div class="flex items-center gap-4 mb-2">
    <label class="text-sm flex items-center gap-2">
      <input
        :checked="showMap"
        type="checkbox"
        @change="$emit('update:showMap', ($event.target as HTMLInputElement).checked)"
      > Bottleneck Map
    </label>
    <div
      v-if="showMap"
      class="text-xs text-gray-600 flex items-center gap-3"
    >
      <span class="flex items-center gap-1">
        <span
          class="inline-block w-3 h-3 rounded"
          style="background: #f59e0b"
        />
        feed cap
      </span>
      <span class="flex items-center gap-1">
        <span
          class="inline-block w-3 h-3 rounded"
          style="background: #14b8a6"
        />
        accel
      </span>
      <span class="flex items-center gap-1">
        <span
          class="inline-block w-3 h-3 rounded"
          style="background: #ec4899"
        />
        jerk
      </span>
    </div>

    <!-- M.3 Export Bottleneck CSV -->
    <button
      v-if="showMap && hasMoves"
      class="ml-auto px-3 py-1 rounded bg-slate-600 text-white text-xs hover:bg-slate-700"
      @click="$emit('exportCsv')"
    >
      Export CSV
    </button>

    <!-- M.3 Bottleneck Pie Chart -->
    <div
      v-if="showMap && stats?.caps"
      class="ml-auto border rounded p-2 bg-white"
    >
      <div class="text-sm font-medium mb-1">
        Bottleneck Share
      </div>
      <svg
        viewBox="0 0 120 120"
        class="w-28 h-28 mx-auto"
      >
        <g transform="translate(60,60)">
          <template
            v-for="(s, i) in capsPie"
            :key="i"
          >
            <path
              :d="arcPath(i)"
              :fill="s.color"
              :title="s.label + ': ' + Math.round(s.pct * 100) + '%'"
            />
          </template>
          <circle
            cx="0"
            cy="0"
            r="26"
            fill="#fff"
          />
        </g>
      </svg>
      <div class="text-xs mt-2 grid grid-cols-2 gap-1">
        <div
          v-for="s in capsPie"
          :key="s.label"
          class="flex items-center gap-1"
        >
          <i
            class="inline-block w-3 h-3 rounded"
            :style="{ background: s.color }"
          />
          <span>{{ s.label }} {{ Math.round(s.pct * 100) }}%</span>
        </div>
      </div>
    </div>
  </div>
</template>
