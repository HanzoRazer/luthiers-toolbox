<template>
  <div class="w-full h-20 border rounded bg-white flex items-center px-2 py-1">
    <div
      v-if="points.length === 0"
      class="text-[11px] text-gray-400"
    >
      No jobs to plot.
    </div>

    <svg
      v-else
      :width="width"
      :height="height"
      class="w-full h-full"
      viewBox="0 0 100 30"
      preserveAspectRatio="none"
    >
      <!-- Baseline -->
      <line
        x1="0"
        :y1="30 - 5"
        x2="100"
        :y2="30 - 5"
        stroke="#e5e7eb"
        stroke-width="0.3"
        stroke-dasharray="1,1"
      />

      <!-- Polyline for risk trend -->
      <polyline
        :points="polylinePoints"
        fill="none"
        stroke="#2563eb"
        stroke-width="0.8"
      />

      <!-- Last point highlight -->
      <circle
        v-if="points.length"
        :cx="points[points.length - 1].x"
        :cy="points[points.length - 1].y"
        r="1.3"
        fill="#dc2626"
      />
    </svg>

    <div class="ml-2 text-[11px] text-gray-500 whitespace-nowrap">
      <div>
        Last: <strong>{{ lastRiskString }}</strong>
      </div>
      <div v-if="deltaString">
        Δ: <span :class="deltaClass">{{ deltaString }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

interface SeverityCounts {
  info?: number;
  low?: number;
  medium?: number;
  high?: number;
  critical?: number;
  [key: string]: number | undefined;
}

interface RiskPresetMeta {
  name?: string;
  source?: string;
  config?: unknown;
}

interface RiskJob {
  id: string;
  pipeline_id?: string;
  pipelineId?: string;
  op_id?: string;
  opId?: string;
  created_at?: string;
  timestamp?: string;
  analytics?: {
    risk_score?: number;
    total_issues?: number;
    severity_counts?: SeverityCounts;
  };
  meta?: {
    preset?: RiskPresetMeta;
    [key: string]: unknown;
  };
}

const props = defineProps<{
  jobs: RiskJob[];
}>();

const width = 100;
const height = 30;

const points = computed(() => {
  if (!props.jobs || props.jobs.length === 0) return [] as { x: number; y: number }[];

  const risks = props.jobs.map((j) => j.analytics?.risk_score ?? 0);
  const maxRisk = Math.max(...risks, 1);
  const minRisk = Math.min(...risks, 0);
  const span = Math.max(maxRisk - minRisk, 1);

  const n = props.jobs.length;
  return risks.map((val, idx) => {
    const x = (idx / Math.max(n - 1, 1)) * 100;
    // invert y (SVG origin top-left)
    const normalized = (val - minRisk) / span;
    const y = (1 - normalized) * 25 + 3; // margin top/bottom
    return { x, y };
  });
});

const polylinePoints = computed(() => points.value.map((p) => `${p.x},${p.y}`).join(" "));

const lastRisk = computed(() => {
  if (!props.jobs.length) return null as number | null;
  const r = props.jobs[props.jobs.length - 1].analytics?.risk_score ?? 0;
  return r;
});

const prevRisk = computed(() => {
  if (props.jobs.length < 2) return null as number | null;
  return props.jobs[props.jobs.length - 2].analytics?.risk_score ?? 0;
});

const lastRiskString = computed(() => {
  if (lastRisk.value == null) return "—";
  return lastRisk.value.toFixed(2);
});

const deltaString = computed(() => {
  if (lastRisk.value == null || prevRisk.value == null) return "";
  const delta = lastRisk.value - prevRisk.value;
  if (Math.abs(delta) < 1e-3) return "0.00";
  const sign = delta > 0 ? "+" : "";
  return `${sign}${delta.toFixed(2)}`;
});

const deltaClass = computed(() => {
  if (!deltaString.value) return "";
  if (deltaString.value.startsWith("+")) {
    return "text-red-600";
  }
  if (deltaString.value.startsWith("-")) {
    return "text-green-600";
  }
  return "text-gray-500";
});
</script>
