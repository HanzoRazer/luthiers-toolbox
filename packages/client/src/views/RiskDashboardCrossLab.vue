<template>
  <div class="p-4 flex flex-col gap-4">
    <!-- Header -->
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h1 class="text-sm font-semibold text-gray-900">
          Cross-Lab Preset Risk Dashboard
        </h1>
        <p class="text-[11px] text-gray-600">
          Aggregated compare history across lanes (Rosette, Adaptive, Relief, Pipeline)
          grouped by lane &amp; preset.
        </p>
      </div>
      <div class="flex items-center gap-2 text-[11px] text-gray-600">
        <button
          class="px-3 py-1 rounded border text-[11px] text-gray-700 hover:bg-gray-50"
          @click="refresh"
        >
          Refresh
        </button>
        <button
          class="px-3 py-1 rounded border text-[11px] text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          :disabled="!buckets.length"
          @click="exportCsv"
        >
          Export CSV
        </button>
      </div>
    </div>

    <!-- Filters -->
    <div class="flex flex-wrap items-center gap-3 text-[11px] text-gray-700">
      <div class="flex items-center gap-2">
        <span class="font-semibold">Lane:</span>
        <select
          v-model="laneFilter"
          class="px-2 py-1 border rounded text-[11px]"
        >
          <option value="">
            All
          </option>
          <option
            v-for="laneOpt in allLanes"
            :key="laneOpt"
            :value="laneOpt"
          >
            {{ laneOpt }}
          </option>
        </select>
      </div>

      <div class="flex items-center gap-2">
        <span class="font-semibold">Preset:</span>
        <select
          v-model="presetFilter"
          class="px-2 py-1 border rounded text-[11px]"
        >
          <option value="">
            All
          </option>
          <option
            v-for="presetOpt in allPresets"
            :key="presetOpt"
            :value="presetOpt"
          >
            {{ presetOpt }}
          </option>
        </select>
      </div>

      <div class="flex items-center gap-2">
        <span class="font-semibold">Job ID (contains):</span>
        <input
          v-model="jobFilter"
          type="text"
          placeholder="e.g. rosette_"
          class="px-2 py-1 border rounded text-[11px] w-40"
        >
      </div>
    </div>

    <!-- Summary chips -->
    <div
      v-if="filteredBuckets.length"
      class="text-[11px] text-gray-700 flex flex-wrap gap-3"
    >
      <span>
        Buckets: <span class="font-mono">{{ filteredBuckets.length }}</span>
      </span>
      <span>
        Entries: <span class="font-mono">{{ filteredEntriesCount }}</span>
      </span>
    </div>

    <div
      v-else
      class="text-[11px] text-gray-500 italic"
    >
      No entries match the current filters.
    </div>

    <!-- Buckets table -->
    <div
      v-if="filteredBuckets.length"
      class="overflow-x-auto"
    >
      <table class="min-w-full text-[11px] text-left">
        <thead class="border-b bg-gray-50">
          <tr>
            <th class="px-2 py-1 whitespace-nowrap">
              Lane
            </th>
            <th class="px-2 py-1 whitespace-nowrap">
              Preset
            </th>
            <th class="px-2 py-1 whitespace-nowrap text-right">
              Entries
            </th>
            <th class="px-2 py-1 whitespace-nowrap text-right">
              Avg +Added
            </th>
            <th class="px-2 py-1 whitespace-nowrap text-right">
              Avg -Removed
            </th>
            <th class="px-2 py-1 whitespace-nowrap text-right">
              Avg =Unchanged
            </th>
            <th class="px-2 py-1 whitespace-nowrap">
              Risk
            </th>
            <th class="px-2 py-1 whitespace-nowrap">
              Trend (Added)
            </th>
            <th class="px-2 py-1 whitespace-nowrap">
              Trend (Removed)
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="bucket in filteredBuckets"
            :key="bucket.key"
            class="border-b last:border-0 hover:bg-gray-50 cursor-pointer"
            :title="`Open ${bucket.lane} lab for preset '${bucket.preset}'`"
            @click="goToLab(bucket)"
          >
            <td class="px-2 py-1 whitespace-nowrap">
              {{ bucket.lane }}
            </td>
            <td class="px-2 py-1 whitespace-nowrap">
              {{ bucket.preset }}
            </td>
            <td class="px-2 py-1 text-right">
              {{ bucket.count }}
            </td>
            <td class="px-2 py-1 text-right text-emerald-700">
              {{ bucket.avgAdded.toFixed(1) }}
            </td>
            <td class="px-2 py-1 text-right text-rose-700">
              {{ bucket.avgRemoved.toFixed(1) }}
            </td>
            <td class="px-2 py-1 text-right">
              {{ bucket.avgUnchanged.toFixed(1) }}
            </td>
            <td class="px-2 py-1 whitespace-nowrap">
              <span
                class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium"
                :class="riskChipClass(bucket.riskScore)"
              >
                {{ bucket.riskLabel }}
              </span>
            </td>
            <td class="px-2 py-1 whitespace-nowrap">
              <svg
                :width="sparkWidth"
                :height="sparkHeight"
                viewBox="0 0 60 20"
              >
                <polyline
                  v-if="bucket.addedPath"
                  :points="bucket.addedPath"
                  fill="none"
                  stroke="#22c55e"
                  stroke-width="1.2"
                />
              </svg>
            </td>
            <td class="px-2 py-1 whitespace-nowrap">
              <svg
                :width="sparkWidth"
                :height="sparkHeight"
                viewBox="0 0 60 20"
              >
                <polyline
                  v-if="bucket.removedPath"
                  :points="bucket.removedPath"
                  fill="none"
                  stroke="#ef4444"
                  stroke-width="1.2"
                />
              </svg>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import axios from "axios";
import { useRouter } from "vue-router";

// Backend response from /api/compare/risk_aggregate
interface RiskAggregateBucket {
  lane: string;
  preset: string;
  count: number;
  avg_added: number;
  avg_removed: number;
  avg_unchanged: number;
  risk_score: number;
  risk_label: string;
  added_series: number[];
  removed_series: number[];
}

// Frontend bucket structure with computed sparkline paths
interface Bucket {
  key: string;
  lane: string;
  preset: string;
  count: number;
  avgAdded: number;
  avgRemoved: number;
  avgUnchanged: number;
  riskScore: number;
  riskLabel: string;
  addedPath: string;
  removedPath: string;
}

const router = useRouter();

// Backend aggregated buckets
const buckets = ref<RiskAggregateBucket[]>([]);

// filters
const laneFilter = ref<string>("");
const presetFilter = ref<string>("");
const jobFilter = ref<string>("");

// sparkline config
const sparkWidth = 60;
const sparkHeight = 20;

const allLanes = computed(() => {
  const set = new Set<string>();
  for (const b of buckets.value) {
    if (b.lane) set.add(b.lane);
  }
  return Array.from(set).sort();
});

const allPresets = computed(() => {
  const set = new Set<string>();
  for (const b of buckets.value) {
    const p = (b.preset && b.preset.trim()) || "(none)";
    set.add(p);
  }
  return Array.from(set).sort();
});

const filteredBucketsBackend = computed(() => {
  return buckets.value.filter((b) => {
    if (laneFilter.value && b.lane !== laneFilter.value) return false;
    const presetName = (b.preset && b.preset.trim()) || "(none)";
    if (presetFilter.value && presetName !== presetFilter.value) return false;
    // Note: jobFilter not directly filterable from aggregated buckets
    // Backend doesn't store individual job IDs in buckets
    // If job filtering is critical, consider server-side filtering in future
    return true;
  });
});

const filteredEntriesCount = computed(() => {
  // Sum of bucket counts
  return filteredBucketsBackend.value.reduce((sum, b) => sum + b.count, 0);
});

const filteredBuckets = computed<Bucket[]>(() => {
  // Transform backend buckets to frontend format with sparklines
  return filteredBucketsBackend.value.map((b) => {
    const key = `${b.lane}::${b.preset}`;
    const addedPath = buildSparklineFromSeries(b.added_series, sparkWidth, sparkHeight);
    const removedPath = buildSparklineFromSeries(b.removed_series, sparkWidth, sparkHeight);

    return {
      key,
      lane: b.lane,
      preset: b.preset,
      count: b.count,
      avgAdded: b.avg_added,
      avgRemoved: b.avg_removed,
      avgUnchanged: b.avg_unchanged,
      riskScore: b.risk_score,
      riskLabel: b.risk_label,
      addedPath,
      removedPath,
    };
  });
});

function riskChipClass(score: number): string {
  if (score < 1) return "bg-emerald-50 text-emerald-700 border border-emerald-200";
  if (score < 3) return "bg-amber-50 text-amber-700 border border-amber-200";
  if (score < 6) return "bg-orange-50 text-orange-700 border border-orange-200";
  return "bg-rose-50 text-rose-700 border border-rose-200";
}

/**
 * Build a simple polyline "x,y x,y ..." for a sparkline from series array.
 */
function buildSparklineFromSeries(
  values: number[],
  width: number,
  height: number
): string {
  if (!values.length) return "";

  const maxVal = Math.max(...values, 1);
  const n = values.length;

  if (n === 1) {
    const y = height / 2;
    return `0,${y} ${width},${y}`;
  }

  const stepX = width / (n - 1);
  const points: string[] = [];

  for (let i = 0; i < n; i++) {
    const x = stepX * i;
    const v = values[i];
    const norm = maxVal > 0 ? v / maxVal : 0;
    const y = height - norm * (height - 2) - 1;
    points.push(`${x.toFixed(1)},${y.toFixed(1)}`);
  }

  return points.join(" ");
}

async function refresh() {
  try {
    const res = await axios.get<RiskAggregateBucket[]>("/api/compare/risk_aggregate");
    buckets.value = res.data;
  } catch (err) {
    console.error("Failed to load cross-lab risk aggregates", err);
  }
}

function exportCsv() {
  if (!filteredBuckets.value.length) return;

  const headers = [
    "lane",
    "preset",
    "count",
    "avg_added",
    "avg_removed",
    "avg_unchanged",
    "risk_score",
    "risk_label",
  ];

  const rows = filteredBuckets.value.map((b) =>
    [
      b.lane,
      b.preset,
      b.count,
      b.avgAdded.toFixed(2),
      b.avgRemoved.toFixed(2),
      b.avgUnchanged.toFixed(2),
      b.riskScore.toFixed(2),
      b.riskLabel,
    ]
      .map((val) => csvEscape(val))
      .join(",")
  );

  const csvContent = [headers.join(","), ...rows].join("\r\n");
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);

  const stamp = new Date().toISOString().replace(/[:.]/g, "-");
  const filename = `crosslab_risk_aggregates_${stamp}.csv`;

  const link = document.createElement("a");
  link.href = url;
  link.setAttribute("download", filename);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

function csvEscape(val: unknown): string {
  if (val === null || val === undefined) return "";
  const s = String(val);
  if (s.includes(",") || s.includes('"') || s.includes("\n")) {
    return `"${s.replace(/"/g, '""')}"`;
  }
  return s;
}

/**
 * Row → Deep link into labs.
 * Adjust paths if your actual route paths differ.
 */
function goToLab(bucket: Bucket) {
  const lane = bucket.lane.toLowerCase();
  const preset = bucket.preset;
  const jobHint = jobFilter.value || "";

  // Common query params we pass along
  const query: Record<string, string> = {};
  if (preset && preset !== "(none)") query.preset = preset;
  if (lane) query.lane = lane;
  if (jobHint) query.job_hint = jobHint;

  if (lane.startsWith("rosette")) {
    // Art Studio / Rosette compare tab
    router.push({
      path: "/art-studio",
      query: {
        tab: "compare",
        ...query,
      },
    });
  } else if (lane.startsWith("adaptive")) {
    router.push({
      path: "/lab/adaptive",
      query,
    });
  } else if (lane.startsWith("relief")) {
    router.push({
      path: "/lab/relief",
      query,
    });
  } else if (lane.startsWith("pipeline")) {
    router.push({
      path: "/lab/pipeline",
      query,
    });
  } else {
    // Fallback: go back to dashboard with same filters
    router.push({
      path: "/lab/risk-dashboard",
      query,
    });
  }
}

onMounted(() => {
  refresh();
});
</script>
