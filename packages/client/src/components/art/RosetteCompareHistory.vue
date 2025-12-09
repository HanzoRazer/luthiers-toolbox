<template>
  <div class="mt-4 border rounded bg-white p-3">
    <div class="flex items-center justify-between mb-2">
      <h3 class="text-xs font-semibold text-gray-800">
        Compare History
      </h3>
      <div class="flex items-center gap-2">
        <button
          class="px-2 py-1 rounded border text-[10px] text-gray-600 hover:bg-gray-50"
          @click="refresh"
        >
          Refresh
        </button>
        <button
          class="px-2 py-1 rounded border text-[10px] text-gray-600 hover:bg-gray-50 disabled:opacity-50"
          :disabled="!entries.length"
          @click="exportCsv"
        >
          Export CSV
        </button>
      </div>
    </div>

    <div class="flex flex-wrap items-center gap-2 mb-2 text-[11px] text-gray-600">
      <span class="font-semibold">Lane:</span>
      <span class="font-mono">{{ lane }}</span>
      <span class="mx-1 text-gray-400">•</span>
      <span class="font-semibold">Job ID:</span>
      <span class="font-mono">
        {{ effectiveJobId || "— none —" }}
      </span>
    </div>

    <!-- Summary bar + sparkline -->
    <div v-if="entries.length" class="mb-2 flex flex-col gap-2">
      <div class="flex flex-wrap items-center gap-3">
        <div class="text-[11px] text-gray-700 flex flex-wrap gap-3">
          <span>
            Entries: <span class="font-mono">{{ entries.length }}</span>
          </span>
          <span class="text-emerald-700">
            Avg Added: <span class="font-mono">{{ avgAdded }}</span>
          </span>
          <span class="text-rose-700">
            Avg Removed: <span class="font-mono">{{ avgRemoved }}</span>
          </span>
          <span class="text-gray-700">
            Avg Unchanged: <span class="font-mono">{{ avgUnchanged }}</span>
          </span>
        </div>

        <!-- Compare presets toggle -->
        <label class="flex items-center gap-1 text-[10px] text-gray-600 cursor-pointer">
          <input
            type="checkbox"
            v-model="comparePresets"
            class="h-3 w-3"
          />
          <span>Compare presets</span>
        </label>
      </div>

      <!-- Global sparklines (default mode) -->
      <div
        v-if="!comparePresets"
        class="flex items-center gap-2 text-[10px] text-gray-600"
      >
        <div class="flex items-center gap-1">
          <svg :width="sparkWidth" :height="sparkHeight" viewBox="0 0 60 20">
            <polyline
              v-if="addedSparkPath"
              :points="addedSparkPath"
              fill="none"
              stroke="#22c55e"
              stroke-width="1.2"
            />
          </svg>
          <span>Added trend</span>
        </div>
        <div class="flex items-center gap-1">
          <svg :width="sparkWidth" :height="sparkHeight" viewBox="0 0 60 20">
            <polyline
              v-if="removedSparkPath"
              :points="removedSparkPath"
              fill="none"
              stroke="#ef4444"
              stroke-width="1.2"
            />
          </svg>
          <span>Removed trend</span>
        </div>
      </div>

      <!-- Per-preset sparklines (compare mode) -->
      <div
        v-else
        class="flex flex-wrap items-center gap-4 text-[10px] text-gray-600"
      >
        <div
          v-for="preset in presetSparklines"
          :key="preset.name"
          class="flex items-center gap-2"
        >
          <span class="font-semibold">{{ preset.name }}</span>
          <svg :width="sparkWidth" :height="sparkHeight" viewBox="0 0 60 20">
            <polyline
              v-if="preset.addedPath"
              :points="preset.addedPath"
              fill="none"
              stroke="#22c55e"
              stroke-width="1.2"
            />
          </svg>
          <svg :width="sparkWidth" :height="sparkHeight" viewBox="0 0 60 20">
            <polyline
              v-if="preset.removedPath"
              :points="preset.removedPath"
              fill="none"
              stroke="#ef4444"
              stroke-width="1.2"
            />
          </svg>
        </div>
      </div>

      <!-- Phase 27.5: Two-preset A/B overlay compare -->
      <div
        v-if="comparePresets && presetBuckets.length >= 2"
        class="mt-2 border rounded bg-gray-50 p-2 flex flex-col gap-2"
      >
        <div class="flex flex-wrap items-center gap-2 text-[10px] text-gray-700">
          <span class="font-semibold">A/B Overlay:</span>
          <select
            v-model="presetCompareA"
            class="border rounded px-1 py-0.5 text-[10px]"
          >
            <option
              v-for="bucket in presetBuckets"
              :key="bucket.name"
              :value="bucket.name"
            >
              {{ bucket.name }}
            </option>
          </select>
          <span class="text-gray-500">vs</span>
          <select
            v-model="presetCompareB"
            class="border rounded px-1 py-0.5 text-[10px]"
          >
            <option
              v-for="bucket in presetBuckets"
              :key="bucket.name"
              :value="bucket.name"
            >
              {{ bucket.name }}
            </option>
          </select>
        </div>

        <div class="flex items-center gap-3 text-[10px]">
          <div class="flex items-center gap-1">
            <span class="font-semibold text-gray-700">Added:</span>
            <svg :width="sparkWidth" :height="sparkHeight" viewBox="0 0 60 20">
              <polyline
                v-if="pairAddedOverlay.a"
                :points="pairAddedOverlay.a"
                fill="none"
                stroke="#22c55e"
                stroke-width="1.5"
              />
              <polyline
                v-if="pairAddedOverlay.b"
                :points="pairAddedOverlay.b"
                fill="none"
                stroke="#f97316"
                stroke-width="1.5"
              />
            </svg>
            <div class="flex items-center gap-1">
              <div class="w-2 h-2 rounded-full bg-emerald-500"></div>
              <span class="text-gray-600">A</span>
            </div>
            <div class="flex items-center gap-1">
              <div class="w-2 h-2 rounded-full bg-orange-500"></div>
              <span class="text-gray-600">B</span>
            </div>
          </div>

          <div class="flex items-center gap-1">
            <span class="font-semibold text-gray-700">Removed:</span>
            <svg :width="sparkWidth" :height="sparkHeight" viewBox="0 0 60 20">
              <polyline
                v-if="pairRemovedOverlay.a"
                :points="pairRemovedOverlay.a"
                fill="none"
                stroke="#ef4444"
                stroke-width="1.5"
              />
              <polyline
                v-if="pairRemovedOverlay.b"
                :points="pairRemovedOverlay.b"
                fill="none"
                stroke="#6366f1"
                stroke-width="1.5"
              />
            </svg>
            <div class="flex items-center gap-1">
              <div class="w-2 h-2 rounded-full bg-red-500"></div>
              <span class="text-gray-600">A</span>
            </div>
            <div class="flex items-center gap-1">
              <div class="w-2 h-2 rounded-full bg-indigo-500"></div>
              <span class="text-gray-600">B</span>
            </div>
          </div>
        </div>

        <!-- Phase 27.6: Numeric delta badges -->
        <div
          v-if="pairStats"
          class="mt-2 text-[10px] text-gray-700 flex flex-wrap gap-3"
        >
          <div>
            <span class="font-semibold">Added avg:</span>
            <span class="ml-1 font-mono">
              A {{ pairStats.aAdded.toFixed(1) }} ·
              B {{ pairStats.bAdded.toFixed(1) }}
            </span>
            <span
              class="ml-1 px-1 rounded border"
              :class="pairStats.deltaAdded >= 0 ? 'border-emerald-500 text-emerald-700' : 'border-rose-500 text-rose-700'"
            >
              Δ B–A = {{ formatDelta(pairStats.deltaAdded) }}
            </span>
          </div>

          <div>
            <span class="font-semibold">Removed avg:</span>
            <span class="ml-1 font-mono">
              A {{ pairStats.aRemoved.toFixed(1) }} ·
              B {{ pairStats.bRemoved.toFixed(1) }}
            </span>
            <span
              class="ml-1 px-1 rounded border"
              :class="pairStats.deltaRemoved >= 0 ? 'border-emerald-500 text-emerald-700' : 'border-rose-500 text-rose-700'"
            >
              Δ B–A = {{ formatDelta(pairStats.deltaRemoved) }}
            </span>
          </div>

          <div>
            <span class="font-semibold">Unchanged avg:</span>
            <span class="ml-1 font-mono">
              A {{ pairStats.aUnchanged.toFixed(1) }} ·
              B {{ pairStats.bUnchanged.toFixed(1) }}
            </span>
            <span
              class="ml-1 px-1 rounded border border-gray-400 text-gray-700"
            >
              Δ B–A = {{ formatDelta(pairStats.deltaUnchanged) }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="text-[11px] text-gray-500 italic">
      No compare history yet for this lane/job.
    </div>

    <!-- History table -->
    <div v-if="entries.length" class="overflow-x-auto mt-2">
      <table class="min-w-full text-[11px] text-left">
        <thead class="border-b bg-gray-50">
          <tr>
            <th class="px-2 py-1 whitespace-nowrap">Time</th>
            <th class="px-2 py-1 whitespace-nowrap">Baseline</th>
            <th class="px-2 py-1 whitespace-nowrap text-right">Base</th>
            <th class="px-2 py-1 whitespace-nowrap text-right">Curr</th>
            <th class="px-2 py-1 whitespace-nowrap text-right text-emerald-700">+Add</th>
            <th class="px-2 py-1 whitespace-nowrap text-right text-rose-700">-Rem</th>
            <th class="px-2 py-1 whitespace-nowrap text-right">=Unch</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(e, idx) in entries"
            :key="idx"
            class="border-b last:border-0 hover:bg-gray-50"
          >
            <td class="px-2 py-1 whitespace-nowrap">
              {{ formatTime(e.ts) }}
            </td>
            <td class="px-2 py-1 whitespace-nowrap font-mono text-[10px]">
              {{ e.baseline_id.slice(0, 8) }}…
            </td>
            <td class="px-2 py-1 text-right">
              {{ e.baseline_path_count }}
            </td>
            <td class="px-2 py-1 text-right">
              {{ e.current_path_count }}
            </td>
            <td class="px-2 py-1 text-right text-emerald-700">
              {{ e.added_paths }}
            </td>
            <td class="px-2 py-1 text-right text-rose-700">
              {{ e.removed_paths }}
            </td>
            <td class="px-2 py-1 text-right">
              {{ e.unchanged_paths }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import axios from "axios";

interface CompareHistoryEntry {
  ts: string;
  job_id: string | null;
  lane: string;
  baseline_id: string;
  baseline_path_count: number;
  current_path_count: number;
  added_paths: number;
  removed_paths: number;
  unchanged_paths: number;
  preset?: string | null; // Phase 27.4: preset label (Safe, Aggressive, etc.)
}

const props = defineProps<{
  lane?: string;
  jobId?: string | null;
}>();

const lane = computed(() => props.lane ?? "rosette");
const effectiveJobId = computed(() =>
  (props.jobId && props.jobId.trim()) || null
);

const entries = ref<CompareHistoryEntry[]>([]);

const avgAdded = computed(() => {
  if (!entries.value.length) return 0;
  const sum = entries.value.reduce((acc, e) => acc + (e.added_paths || 0), 0);
  return (sum / entries.value.length).toFixed(1);
});

const avgRemoved = computed(() => {
  if (!entries.value.length) return 0;
  const sum = entries.value.reduce((acc, e) => acc + (e.removed_paths || 0), 0);
  return (sum / entries.value.length).toFixed(1);
});

const avgUnchanged = computed(() => {
  if (!entries.value.length) return 0;
  const sum = entries.value.reduce((acc, e) => acc + (e.unchanged_paths || 0), 0);
  return (sum / entries.value.length).toFixed(1);
});

// Sparkline configuration
const sparkWidth = 60;
const sparkHeight = 20;

// Global sparklines (all entries)
const addedSparkPath = computed(() =>
  buildSparkline(entries.value, "added_paths", sparkWidth, sparkHeight)
);
const removedSparkPath = computed(() =>
  buildSparkline(entries.value, "removed_paths", sparkWidth, sparkHeight)
);

// === Phase 27.4/27.5: Preset grouping & compare mode ===

const comparePresets = ref<boolean>(false);

function normalizePresetName(e: CompareHistoryEntry): string {
  return (e.preset && e.preset.trim()) || "(none)";
}

const presetBuckets = computed(() => {
  const map = new Map<string, CompareHistoryEntry[]>();
  for (const e of entries.value) {
    const key = normalizePresetName(e);
    if (!map.has(key)) {
      map.set(key, []);
    }
    map.get(key)!.push(e);
  }
  const sortedKeys = Array.from(map.keys()).sort();
  return sortedKeys.map((name) => ({
    name,
    entries: map.get(name)!,
  }));
});

const presetSparklines = computed(() =>
  presetBuckets.value.map((bucket) => ({
    name: bucket.name,
    addedPath: buildSparkline(bucket.entries, "added_paths", sparkWidth, sparkHeight),
    removedPath: buildSparkline(
      bucket.entries,
      "removed_paths",
      sparkWidth,
      sparkHeight
    ),
  }))
);

// Phase 27.5: A/B preset compare selection
const presetCompareA = ref<string | null>(null);
const presetCompareB = ref<string | null>(null);

// keep A/B in range when buckets change
watch(
  () => presetBuckets.value,
  (buckets) => {
    if (!buckets.length) {
      presetCompareA.value = null;
      presetCompareB.value = null;
      return;
    }
    const names = buckets.map((b) => b.name);
    if (!presetCompareA.value || !names.includes(presetCompareA.value)) {
      presetCompareA.value = names[0];
    }
    if (names.length > 1) {
      if (!presetCompareB.value || !names.includes(presetCompareB.value)) {
        presetCompareB.value = names[1];
      }
    } else {
      presetCompareB.value = null;
    }
  },
  { immediate: true }
);

const presetCompareAEntries = computed(() => {
  if (!presetCompareA.value) return [];
  return entries.value.filter(
    (e) => normalizePresetName(e) === presetCompareA.value
  );
});

const presetCompareBEntries = computed(() => {
  if (!presetCompareB.value) return [];
  return entries.value.filter(
    (e) => normalizePresetName(e) === presetCompareB.value
  );
});

const pairAddedOverlay = computed(() =>
  buildOverlaySparkline(
    presetCompareAEntries.value,
    presetCompareBEntries.value,
    "added_paths",
    sparkWidth,
    sparkHeight
  )
);

const pairRemovedOverlay = computed(() =>
  buildOverlaySparkline(
    presetCompareAEntries.value,
    presetCompareBEntries.value,
    "removed_paths",
    sparkWidth,
    sparkHeight
  )
);

function formatTime(ts: string): string {
  try {
    const d = new Date(ts);
    return d.toLocaleString();
  } catch {
    return ts;
  }
}

async function refresh() {
  try {
    const params: any = { lane: lane.value };
    if (effectiveJobId.value) {
      params.job_id = effectiveJobId.value;
    }
    const res = await axios.get<CompareHistoryEntry[]>("/api/compare/history", {
      params,
    });
    entries.value = res.data;
  } catch (err) {
    console.error("Failed to load compare history", err);
  }
}

function exportCsv() {
  if (!entries.value.length) return;

  const headers = [
    "ts",
    "job_id",
    "lane",
    "baseline_id",
    "baseline_path_count",
    "current_path_count",
    "added_paths",
    "removed_paths",
    "unchanged_paths",
    "preset",
  ];

  const rows = entries.value.map((e) =>
    [
      e.ts,
      e.job_id ?? "",
      e.lane,
      e.baseline_id,
      e.baseline_path_count,
      e.current_path_count,
      e.added_paths,
      e.removed_paths,
      e.unchanged_paths,
      e.preset ?? "",
    ]
      .map((val) => csvEscape(val))
      .join(",")
  );

  const csvContent = [headers.join(","), ...rows].join("\r\n");
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);

  const stamp = new Date().toISOString().replace(/[:.]/g, "-");
  const nameParts = [
    "compare_history",
    lane.value,
    effectiveJobId.value || "all",
    stamp,
  ];
  const filename = nameParts.join("_") + ".csv";

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

// Phase 27.6: A/B delta badge helpers
function averageMetric(
  data: CompareHistoryEntry[],
  key: keyof CompareHistoryEntry
): number {
  if (!data.length) return 0;
  const nums = data.map((e) => {
    const v = e[key];
    return typeof v === "number" ? v : 0;
  });
  const sum = nums.reduce((acc, v) => acc + v, 0);
  return sum / data.length;
}

function formatDelta(delta: number): string {
  if (delta === 0) return "0.0";
  const s = delta.toFixed(1);
  return delta > 0 ? `+${s}` : s;
}

const pairStats = computed(() => {
  if (!presetCompareA.value || !presetCompareB.value) return null;
  if (!presetCompareAEntries.value.length && !presetCompareBEntries.value.length) {
    return null;
  }

  const aName = presetCompareA.value;
  const bName = presetCompareB.value;

  const aAdded = averageMetric(presetCompareAEntries.value, "added_paths");
  const bAdded = averageMetric(presetCompareBEntries.value, "added_paths");
  const deltaAdded = bAdded - aAdded;

  const aRemoved = averageMetric(presetCompareAEntries.value, "removed_paths");
  const bRemoved = averageMetric(presetCompareBEntries.value, "removed_paths");
  const deltaRemoved = bRemoved - aRemoved;

  const aUnchanged = averageMetric(presetCompareAEntries.value, "unchanged_paths");
  const bUnchanged = averageMetric(presetCompareBEntries.value, "unchanged_paths");
  const deltaUnchanged = bUnchanged - aUnchanged;

  return {
    aName,
    bName,
    aAdded,
    bAdded,
    deltaAdded,
    aRemoved,
    bRemoved,
    deltaRemoved,
    aUnchanged,
    bUnchanged,
    deltaUnchanged,
  };
});

/**
 * Build a simple polyline "x,y x,y ..." for a sparkline.
 * key: 'added_paths' | 'removed_paths' | ...
 */
function buildSparkline(
  data: CompareHistoryEntry[],
  key: keyof CompareHistoryEntry,
  width: number,
  height: number
): string {
  if (!data.length) return "";

  const values: number[] = data.map((e) => {
    const v = e[key];
    return typeof v === "number" ? v : 0;
  });

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

/**
 * Phase 27.5: Build overlay sparkline paths for A and B sharing the same scale.
 */
function buildOverlaySparkline(
  dataA: CompareHistoryEntry[],
  dataB: CompareHistoryEntry[],
  key: keyof CompareHistoryEntry,
  width: number,
  height: number
): { a: string; b: string } {
  const empty = { a: "", b: "" };
  if (!dataA.length && !dataB.length) return empty;

  const toValues = (data: CompareHistoryEntry[]) =>
    data.map((e) => {
      const v = e[key];
      return typeof v === "number" ? v : 0;
    });

  const valuesA = toValues(dataA);
  const valuesB = toValues(dataB);
  const allVals = [...valuesA, ...valuesB];
  const maxVal = Math.max(...allVals, 1);

  const buildForSeries = (values: number[]): string => {
    if (!values.length) return "";
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
  };

  return {
    a: buildForSeries(valuesA),
    b: buildForSeries(valuesB),
  };
}

onMounted(() => {
  refresh();
});

watch(
  () => effectiveJobId.value,
  () => {
    refresh();
  }
);

watch(
  () => lane.value,
  () => {
    refresh();
  }
);
</script>
