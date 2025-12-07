<template>
  <div class="border rounded bg-white p-3 text-xs">
    <h3 class="text-[11px] font-semibold text-gray-700 mb-2">
      Window Comparison
      <span class="text-gray-400 font-normal">(current vs previous)</span>
    </h3>

    <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
      <!-- Avg Risk -->
      <div>
        <div class="flex items-center justify-between mb-1">
          <span class="text-gray-600">Avg risk</span>
          <span class="text-gray-800">
            {{ fmt(curr.avgRisk) }} vs {{ fmt(prev.avgRisk) }}
            <span :class="deltaClass(deltaRisk)">
              {{ deltaArrow(deltaRisk) }}{{ fmt(deltaRisk, 2, true) }}
            </span>
          </span>
        </div>
        <div class="w-full h-4 bg-gray-100 rounded relative overflow-hidden">
          <div
            class="h-4 bg-blue-500/70"
            :style="{ width: currBarW }"
            title="current"
          />
          <div
            class="h-4 bg-gray-400/60 absolute top-0"
            :style="{ width: prevBarW }"
            title="previous"
          />
        </div>
      </div>

      <!-- Critical incidents -->
      <div>
        <div class="flex items-center justify-between mb-1">
          <span class="text-gray-600">Critical incidents</span>
          <span class="text-gray-800">
            {{ curr.totalCritical }} vs {{ prev.totalCritical }}
            <span :class="deltaClass(deltaCritical)">
              {{ deltaArrow(deltaCritical) }}{{ fmt(deltaCritical, 0, true) }}
            </span>
          </span>
        </div>
        <div class="w-full h-4 bg-gray-100 rounded relative overflow-hidden">
          <div
            class="h-4 bg-red-500/70"
            :style="{ width: currCritBarW }"
            title="current"
          />
          <div
            class="h-4 bg-gray-400/60 absolute top-0"
            :style="{ width: prevCritBarW }"
            title="previous"
          />
        </div>
      </div>
    </div>

    <p class="mt-2 text-[10px] text-gray-500">
      Bars are normalized to the max of the two values for each metric.
    </p>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

interface SummaryLike {
  jobsCount: number;
  avgRisk: number;
  totalCritical: number;
}

const props = defineProps<{
  curr: SummaryLike;
  prev: SummaryLike;
}>();

function fmt(v: number, fixed = 2, signed = false) {
  if (v === undefined || v === null || Number.isNaN(v)) return "—";
  const s = v.toFixed(fixed);
  if (signed && v > 0) return `+${s}`;
  return s;
}

const deltaRisk = computed(() => (props.curr.avgRisk ?? 0) - (props.prev.avgRisk ?? 0));
const deltaCritical = computed(
  () => (props.curr.totalCritical ?? 0) - (props.prev.totalCritical ?? 0)
);

function deltaClass(d: number) {
  if (d > 0) return "text-red-600 ml-1";
  if (d < 0) return "text-green-600 ml-1";
  return "text-gray-500 ml-1";
}
function deltaArrow(d: number) {
  if (d > 0) return "▲";
  if (d < 0) return "▼";
  return "•";
}

function normWidth(currV: number, prevV: number) {
  const maxV = Math.max(currV, prevV, 1e-9);
  const wCurr = Math.max(0, Math.min(100, (currV / maxV) * 100));
  const wPrev = Math.max(0, Math.min(100, (prevV / maxV) * 100));
  return { wCurr, wPrev };
}

// bars for avg risk
const riskBars = computed(() => {
  const { wCurr, wPrev } = normWidth(props.curr.avgRisk ?? 0, props.prev.avgRisk ?? 0);
  return { wCurr, wPrev };
});
const currBarW = computed(() => riskBars.value.wCurr + "%");
const prevBarW = computed(() => riskBars.value.wPrev + "%");

// bars for critical incidents
const critBars = computed(() => {
  const { wCurr, wPrev } = normWidth(props.curr.totalCritical ?? 0, props.prev.totalCritical ?? 0);
  return { wCurr, wPrev };
});
const currCritBarW = computed(() => critBars.value.wCurr + "%");
const prevCritBarW = computed(() => critBars.value.wPrev + "%");
</script>
