<template>
  <div class="border rounded bg-white p-2 text-[10px] hover:shadow-sm transition-shadow">
    <div class="flex items-center justify-between mb-1">
      <span class="font-mono text-[9px] text-gray-600">
        {{ formatDate(snapshot.created_at) }}
      </span>
      <span
        class="px-1.5 py-0.5 rounded text-[9px] font-semibold"
        :class="riskClass(snapshot.risk_score)"
      >
        {{ snapshot.risk_score.toFixed(1) }}%
      </span>
    </div>

    <!-- Sparkline -->
    <div class="mb-1">
      <svg
        viewBox="0 0 80 20"
        class="w-full h-5"
      >
        <polyline
          :points="sparklinePoints"
          fill="none"
          :stroke="riskColor(snapshot.risk_score)"
          stroke-width="1.5"
        />
      </svg>
    </div>

    <div class="text-[9px] text-gray-700">
      <div>Seg Δ: {{ snapshot.diff_summary.segments_delta }}</div>
      <div>Inner Δ: {{ snapshot.diff_summary.inner_radius_delta?.toFixed(2) }}</div>
      <div>Outer Δ: {{ snapshot.diff_summary.outer_radius_delta?.toFixed(2) }}</div>
    </div>

    <div
      v-if="snapshot.lane"
      class="mt-1 text-[9px] text-gray-500"
    >
      Lane: {{ snapshot.lane }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

export interface RosetteDiffSummary {
  segments_delta: number
  inner_radius_delta: number
  outer_radius_delta: number
  preset_a?: string
  preset_b?: string
}

export interface CompareSnapshot {
  id: number
  job_id_a: string
  job_id_b: string
  lane: string | null
  risk_score: number
  diff_summary: RosetteDiffSummary
  note: string | null
  created_at: string
}

const props = defineProps<{
  snapshot: CompareSnapshot
}>()

const sparklinePoints = computed(() => {
  const segDelta = Math.abs(props.snapshot.diff_summary.segments_delta || 0);
  const innerDelta = Math.abs(props.snapshot.diff_summary.inner_radius_delta || 0);
  const outerDelta = Math.abs(props.snapshot.diff_summary.outer_radius_delta || 0);

  const segY = Math.min(segDelta * 2, 18);
  const innerY = Math.min(innerDelta * 3, 18);
  const outerY = Math.min(outerDelta * 3, 18);

  return `0,${20 - segY} 40,${20 - innerY} 80,${20 - outerY}`;
})

function formatDate(isoString: string): string {
  try {
    const date = new Date(isoString);
    return date.toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return isoString.slice(0, 16);
  }
}

function riskClass(score: number): string {
  if (score >= 70) return "bg-red-100 text-red-800";
  if (score >= 40) return "bg-yellow-100 text-yellow-800";
  return "bg-green-100 text-green-800";
}

function riskColor(score: number): string {
  if (score >= 70) return "#ef4444";
  if (score >= 40) return "#f59e0b";
  return "#10b981";
}
</script>
