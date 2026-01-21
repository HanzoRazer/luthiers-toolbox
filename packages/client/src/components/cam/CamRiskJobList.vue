<template>
  <div class="space-y-1 text-xs">
    <div
      v-for="job in jobs"
      :key="job.id"
      class="flex items-center justify-between border rounded px-2 py-1 bg-white hover:bg-gray-50"
    >
      <div class="flex flex-col">
        <div class="flex items-center gap-2">
          <span class="font-semibold">
            {{ job.pipeline_id || job.pipelineId || "unknown_pipeline" }}
          </span>
          <span class="text-gray-400">
            • {{ job.op_id || job.opId || "op" }}
          </span>
        </div>
        <div class="flex items-center gap-2 mt-0.5">
          <span class="text-gray-500">
            Risk: <strong>{{ (job.analytics?.risk_score ?? 0).toFixed(1) }}</strong>
          </span>

          <!-- Preset chip -->
          <span
            v-if="job.meta?.preset"
            class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px]"
            :class="presetChipClass(job.meta.preset)"
          >
            <span class="uppercase tracking-wide">
              Preset:
            </span>
            <span class="font-semibold">
              {{ job.meta.preset.name || "Custom" }}
            </span>
            <span
              v-if="job.meta.preset.source"
              class="text-[9px] text-gray-700"
            >
              ({{ job.meta.preset.source }})
            </span>
          </span>
        </div>
      </div>

      <div class="text-right text-gray-400">
        <div>
          {{ formatDate(job.created_at || job.timestamp) }}
        </div>
        <div v-if="job.analytics">
          issues: {{ job.analytics.total_issues ?? "?" }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
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
  };
  meta?: {
    preset?: RiskPresetMeta;
    [key: string]: unknown;
  };
}

defineProps<{
  jobs: RiskJob[];
}>();

function formatDate(raw: string | undefined) {
  if (!raw) return "";
  try {
    const d = new Date(raw);
    if (Number.isNaN(d.getTime())) return raw;
    return d.toLocaleString();
  } catch {
    return raw;
  }
}

function presetChipClass(preset: RiskPresetMeta) {
  const name = (preset.name || "").toLowerCase();
  if (name.includes("safe")) {
    return "bg-green-100 text-green-800 border border-green-300";
  }
  if (name.includes("agg") || name.includes("aggressive")) {
    return "bg-red-100 text-red-800 border border-red-300";
  }
  return "bg-yellow-100 text-yellow-800 border border-yellow-300";
}
</script>
