<template>
  <div
    class="w-80 border-l bg-gray-50 p-3 flex flex-col gap-2 overflow-y-auto"
    style="max-height: calc(100vh - 4rem);"
  >
    <div class="flex items-center justify-between mb-2">
      <h2 class="text-[13px] font-semibold text-gray-900">
        Comparison History
      </h2>
      <button
        class="px-2 py-0.5 rounded border text-[10px] text-blue-700 hover:bg-blue-50"
        :disabled="historyLoading || !historySnapshots.length"
        @click="emit('export-csv')"
      >
        Export CSV
      </button>
    </div>

    <!-- Preset grouping toggle -->
    <div
      v-if="historySnapshots.length > 0"
      class="flex items-center gap-2 mb-2 pb-2 border-b"
    >
      <label class="flex items-center gap-1 text-[10px] text-gray-700 cursor-pointer">
        <input
          :checked="groupByPreset"
          type="checkbox"
          class="rounded"
          @change="emit('update:groupByPreset', ($event.target as HTMLInputElement).checked)"
        >
        Group by Preset
      </label>
    </div>

    <!-- Risk Metrics Bar -->
    <div
      v-if="historySnapshots.length > 0"
      class="border rounded bg-white p-2 mb-2"
    >
      <div class="text-[10px] font-semibold text-gray-900 mb-1.5">
        Risk Overview
      </div>
      <div class="grid grid-cols-2 gap-2 text-[9px]">
        <div>
          <div class="text-gray-600">
            Total
          </div>
          <div class="font-semibold text-gray-900">
            {{ historySnapshots.length }}
          </div>
        </div>
        <div>
          <div class="text-gray-600">
            Avg Risk
          </div>
          <div
            class="font-semibold"
            :class="riskTextClass(averageRisk)"
          >
            {{ averageRisk.toFixed(1) }}%
          </div>
        </div>
        <div>
          <div class="text-green-700">
            Low (&lt;40%)
          </div>
          <div class="font-semibold text-green-800">
            {{ lowRiskCount }}
          </div>
        </div>
        <div>
          <div class="text-yellow-700">
            Med (40-70%)
          </div>
          <div class="font-semibold text-yellow-800">
            {{ mediumRiskCount }}
          </div>
        </div>
        <div class="col-span-2">
          <div class="text-red-700">
            High (&gt;70%)
          </div>
          <div class="font-semibold text-red-800">
            {{ highRiskCount }}
          </div>
        </div>
      </div>

      <!-- Risk distribution bar -->
      <div class="mt-2 flex h-2 rounded overflow-hidden">
        <div
          v-if="lowRiskCount > 0"
          class="bg-green-500"
          :style="{ width: `${(lowRiskCount / historySnapshots.length) * 100}%` }"
        />
        <div
          v-if="mediumRiskCount > 0"
          class="bg-yellow-500"
          :style="{ width: `${(mediumRiskCount / historySnapshots.length) * 100}%` }"
        />
        <div
          v-if="highRiskCount > 0"
          class="bg-red-500"
          :style="{ width: `${(highRiskCount / historySnapshots.length) * 100}%` }"
        />
      </div>
    </div>

    <!-- Preset Scorecards -->
    <div
      v-if="Object.keys(groupedSnapshots).length > 1"
      class="mb-2"
    >
      <div class="text-[10px] font-semibold text-gray-900 mb-1.5 px-1">
        Preset Analytics
      </div>
      <div class="flex gap-2 overflow-x-auto pb-2">
        <div
          v-for="(group, groupKey) in groupedSnapshots"
          :key="groupKey"
          class="border rounded bg-white p-2 flex-shrink-0 w-36"
        >
          <div
            class="text-[10px] font-semibold text-gray-900 mb-1 truncate"
            :title="group.presetLabel"
          >
            {{ group.presetLabel }}
          </div>

          <!-- Scorecard metrics -->
          <div class="grid grid-cols-2 gap-1 text-[9px] mb-1.5">
            <div>
              <div class="text-gray-600">
                Total
              </div>
              <div class="font-semibold text-gray-900">
                {{ group.snapshots.length }}
              </div>
            </div>
            <div>
              <div class="text-gray-600">
                Avg
              </div>
              <div
                class="font-semibold"
                :class="riskTextClass(group.avgRisk)"
              >
                {{ group.avgRisk.toFixed(1) }}%
              </div>
            </div>
          </div>

          <!-- Risk breakdown -->
          <div class="text-[8px] mb-1.5">
            <div class="flex justify-between">
              <span class="text-green-700">Low</span>
              <span class="font-semibold text-green-800">
                {{ group.snapshots.filter(s => s.risk_score < 40).length }}
              </span>
            </div>
            <div class="flex justify-between">
              <span class="text-yellow-700">Med</span>
              <span class="font-semibold text-yellow-800">
                {{ group.snapshots.filter(s => s.risk_score >= 40 && s.risk_score < 70).length }}
              </span>
            </div>
            <div class="flex justify-between">
              <span class="text-red-700">High</span>
              <span class="font-semibold text-red-800">
                {{ group.snapshots.filter(s => s.risk_score >= 70).length }}
              </span>
            </div>
          </div>

          <!-- Mini sparkline showing risk trend -->
          <div class="border-t pt-1">
            <svg
              viewBox="0 0 120 20"
              class="w-full h-4"
            >
              <polyline
                :points="generatePresetSparkline(group.snapshots)"
                fill="none"
                :stroke="riskColor(group.avgRisk)"
                stroke-width="1.5"
              />
            </svg>
          </div>
        </div>
      </div>
    </div>

    <div
      v-if="historyLoading"
      class="text-[10px] text-gray-500 italic"
    >
      Loading history...
    </div>

    <div
      v-else-if="historySnapshots.length === 0"
      class="text-[10px] text-gray-500 italic"
    >
      No comparison history for these jobs yet. Run a comparison and save to timeline.
    </div>

    <!-- Flat history display -->
    <div
      v-else-if="!groupByPreset"
      class="flex flex-col gap-2"
    >
      <div
        v-for="snapshot in historySnapshots"
        :key="snapshot.id"
        class="border rounded bg-white p-2 text-[10px] hover:shadow-sm transition-shadow"
      >
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
              :points="generateSparkline(snapshot)"
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
    </div>

    <!-- Preset-grouped history -->
    <div
      v-else
      class="flex flex-col gap-2"
    >
      <div
        v-for="(group, groupKey) in groupedSnapshots"
        :key="groupKey"
        class="border rounded bg-white overflow-hidden"
      >
        <!-- Group header -->
        <button
          class="w-full px-2 py-1.5 flex items-center justify-between hover:bg-gray-50 text-left"
          @click="emit('toggle-group', groupKey as string)"
        >
          <div class="flex-1">
            <div class="text-[11px] font-semibold text-gray-900">
              {{ group.presetLabel }}
            </div>
            <div class="text-[9px] text-gray-600">
              {{ group.snapshots.length }} comparison{{ group.snapshots.length !== 1 ? 's' : '' }} ·
              Avg risk: {{ group.avgRisk.toFixed(1) }}%
            </div>
          </div>
          <span class="text-gray-400 text-[10px]">
            {{ expandedGroups.has(groupKey as string) ? '▼' : '▶' }}
          </span>
        </button>

        <!-- Group content (collapsible) -->
        <div
          v-if="expandedGroups.has(groupKey as string)"
          class="border-t bg-gray-50 p-2 flex flex-col gap-2"
        >
          <div
            v-for="snapshot in group.snapshots"
            :key="snapshot.id"
            class="border rounded bg-white p-2 text-[10px] hover:shadow-sm transition-shadow"
          >
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
                  :points="generateSparkline(snapshot)"
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
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface RosetteDiffSummary {
  segments_delta: number
  inner_radius_delta: number
  outer_radius_delta: number
  preset_a?: string
  preset_b?: string
}

interface CompareSnapshot {
  id: number
  job_id_a: string
  job_id_b: string
  lane: string | null
  risk_score: number
  diff_summary: RosetteDiffSummary
  note: string | null
  created_at: string
}

interface SnapshotGroup {
  presetLabel: string
  snapshots: CompareSnapshot[]
  avgRisk: number
}

defineProps<{
  historySnapshots: CompareSnapshot[]
  historyLoading: boolean
  groupByPreset: boolean
  expandedGroups: Set<string>
  groupedSnapshots: Record<string, SnapshotGroup>
  averageRisk: number
  lowRiskCount: number
  mediumRiskCount: number
  highRiskCount: number
}>()

const emit = defineEmits<{
  'update:groupByPreset': [value: boolean]
  'toggle-group': [groupKey: string]
  'export-csv': []
}>()

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

function riskTextClass(score: number): string {
  if (score >= 70) return "text-red-700";
  if (score >= 40) return "text-yellow-700";
  return "text-green-700";
}

function generateSparkline(snapshot: CompareSnapshot): string {
  const segDelta = Math.abs(snapshot.diff_summary.segments_delta || 0);
  const innerDelta = Math.abs(snapshot.diff_summary.inner_radius_delta || 0);
  const outerDelta = Math.abs(snapshot.diff_summary.outer_radius_delta || 0);

  const segY = Math.min(segDelta * 2, 18);
  const innerY = Math.min(innerDelta * 3, 18);
  const outerY = Math.min(outerDelta * 3, 18);

  return `0,${20 - segY} 40,${20 - innerY} 80,${20 - outerY}`;
}

function generatePresetSparkline(snapshots: CompareSnapshot[]): string {
  if (snapshots.length === 0) return "0,10 120,10";
  if (snapshots.length === 1) {
    const y = 20 - (snapshots[0].risk_score / 100) * 18;
    return `0,${y} 120,${y}`;
  }

  const sorted = [...snapshots].sort((a, b) =>
    a.created_at.localeCompare(b.created_at)
  );

  const width = 120;
  const points = sorted.map((s, i) => {
    const x = (i / (sorted.length - 1)) * width;
    const y = 20 - (s.risk_score / 100) * 18;
    return `${x},${y}`;
  });

  return points.join(" ");
}
</script>
