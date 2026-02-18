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
          grouped by lane &amp; preset. Time window filters apply to this view and
          the JSON snapshot download. Filters are URL-synced and can be saved as named views.
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
          :disabled="!hasAnyFilter"
          @click="clearAllFilters"
        >
          Clear filters
        </button>
        <button
          class="px-3 py-1 rounded border text-[11px] text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          :disabled="!filteredBuckets.length"
          @click="exportCsv"
        >
          Export All CSV
        </button>
        <button
          class="px-3 py-1 rounded border text-[11px] text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          :disabled="!selectedBucket"
          @click="exportBucketCsv"
        >
          Export Bucket CSV
        </button>
        <button
          class="px-3 py-1 rounded border text-[11px] text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          :disabled="!selectedBucket"
          @click="exportBucketJson"
        >
          Export Bucket JSON
        </button>
        <button
          class="px-3 py-1 rounded border text-[11px] text-gray-700 hover:bg-gray-50"
          @click="downloadSnapshotJson"
        >
          Download JSON snapshot
        </button>
      </div>
    </div>

    <!-- Filters -->
    <FiltersBar
      v-model:lane="laneFilter"
      v-model:preset="presetFilter"
      v-model:job-hint="jobFilter"
      v-model:since="since"
      v-model:until="until"
      v-model:quick-range="quickRangeMode"
      :all-lanes="allLanes"
      :all-presets="allPresets"
      :lane-presets="lanePresets"
      @apply-quick-range="applyQuickRange"
      @apply-lane-preset="applyLanePreset"
    />

    <!-- Saved Views -->
    <SavedViewsPanel
      ref="savedViewsPanelRef"
      storage-key="ltb_crosslab_risk_views"
      :get-current-filters="getCurrentFilters"
      @apply="handleApplyFilters"
    />

    <!-- Summary chips -->
    <div
      v-if="filteredBuckets.length"
      class="text-[11px] text-gray-700 flex flex-wrap gap-3"
    >
      <span>
        Buckets: <span class="font-mono">{{ filteredBuckets.length }}</span>
      </span>
      <span>
        Entries (sum of bucket counts): <span class="font-mono">{{ filteredEntriesCount }}</span>
      </span>
      <span
        v-if="since || until"
        class="text-[10px] text-gray-500"
      >
        Window:
        <span v-if="since">from <span class="font-mono">{{ since }}</span></span>
        <span v-if="since && until"> to </span>
        <span v-if="until"> <span class="font-mono">{{ until }}</span> </span>
      </span>
      <span
        v-if="quickRangeMode"
        class="text-[10px] text-indigo-600"
      >
        Quick range: <span class="font-mono">{{ currentQuickRangeLabel }}</span>
      </span>
    </div>

    <div
      v-else
      class="text-[11px] text-gray-500 italic"
    >
      No buckets match the current filters (or time window).
    </div>

    <!-- Buckets table -->
    <BucketsTable
      :buckets="filteredBuckets"
      @select-bucket="loadBucketDetails"
      @go-to-lab="goToLab"
    />

    <!-- Bucket details panel -->
    <BucketDetailsPanel
      :bucket="selectedBucket"
      :entries="bucketEntries"
      :loading="bucketEntriesLoading"
      :error="bucketEntriesError"
      :job-filter="jobFilter"
      @export-csv="exportBucketCsv"
      @download-json="downloadBucketJson"
      @close="clearBucketDetails"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from "vue";
import axios from "axios";
import { useRouter, useRoute } from "vue-router";
import { SavedViewsPanel } from "@/components/ui";
import {
  FiltersBar,
  BucketsTable,
  BucketDetailsPanel,
  type LanePresetDef,
  type QuickRangeMode,
  type Bucket,
  type BucketEntry,
} from "@/components/dashboard";

interface RiskAggregateBucketResponse {
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

// Bucket and BucketEntry imported from dashboard components
// QuickRangeMode and LanePresetDef imported from FiltersBar

const router = useRouter();
const route = useRoute();

const bucketsRaw = ref<Bucket[]>([]);

// filters
const laneFilter = ref<string>("");
const presetFilter = ref<string>("");
const jobFilter = ref<string>("");

// time window (ISO date)
const since = ref<string>("");
const until = ref<string>("");

// quick range
const quickRangeMode = ref<QuickRangeMode>("");

// sparkline config
const sparkWidth = 60;
const sparkHeight = 20;

// bucket details
const selectedBucket = ref<Bucket | null>(null);
const bucketEntries = ref<BucketEntry[]>([]);
const bucketEntriesLoading = ref<boolean>(false);
const bucketEntriesError = ref<string | null>(null);

// saved views panel ref
const savedViewsPanelRef = ref<InstanceType<typeof SavedViewsPanel> | null>(null);

// saved views integration
function getCurrentFilters(): Record<string, string> {
  return {
    lane: laneFilter.value,
    preset: presetFilter.value,
    jobHint: jobFilter.value,
    since: since.value,
    until: until.value,
  };
}

function handleApplyFilters(filters: Record<string, string>) {
  laneFilter.value = filters.lane || "";
  presetFilter.value = filters.preset || "";
  jobFilter.value = filters.jobHint || "";
  since.value = filters.since || "";
  until.value = filters.until || "";

  // Derive quick range mode
  quickRangeMode.value = !since.value && !until.value ? "all" : "";

  syncFiltersToQuery();
  clearBucketDetails();
  refresh();
}

// quick range modes
const quickRangeModes = [
  { id: "all" as QuickRangeMode, label: "All" },
  { id: "last7" as QuickRangeMode, label: "Last 7d" },
  { id: "last30" as QuickRangeMode, label: "Last 30d" },
  { id: "last90" as QuickRangeMode, label: "Last 90d" },
  { id: "year" as QuickRangeMode, label: "This year" },
];

const currentQuickRangeLabel = computed(() => {
  const entry = quickRangeModes.find((m) => m.id === quickRangeMode.value);
  return entry ? entry.label : "Custom";
});

// lane preset definitions
const lanePresets = ref<LanePresetDef[]>([
  {
    id: "rosette_safe_30",
    label: "Rosette · Safe (30d)",
    lane: "Rosette",
    preset: "Safe",
    defaultQuickRange: "last30",
    badge: "Rosette",
  },
  {
    id: "adaptive_aggressive_30",
    label: "Adaptive · Aggressive (30d)",
    lane: "Adaptive",
    preset: "Aggressive",
    defaultQuickRange: "last30",
    badge: "Adaptive",
  },
  {
    id: "relief_safe_90",
    label: "Relief · Safe (90d)",
    lane: "Relief",
    preset: "Safe",
    defaultQuickRange: "last90",
    badge: "Relief",
  },
  {
    id: "pipeline_any_30",
    label: "Pipeline · Any (30d)",
    lane: "Pipeline",
    preset: "",
    defaultQuickRange: "last30",
    badge: "Pipeline",
  },
]);

// helper for ISO date (YYYY-MM-DD)
function toIsoDate(d: Date): string {
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function applyQuickRange(mode: QuickRangeMode) {
  const today = new Date();
  let start: string | "" = "";
  let end: string | "" = "";

  if (mode === "all") {
    start = "";
    end = "";
  } else if (mode === "last7") {
    const d = new Date(today);
    d.setDate(d.getDate() - 7);
    start = toIsoDate(d);
    end = toIsoDate(today);
  } else if (mode === "last30") {
    const d = new Date(today);
    d.setDate(d.getDate() - 30);
    start = toIsoDate(d);
    end = toIsoDate(today);
  } else if (mode === "last90") {
    const d = new Date(today);
    d.setDate(d.getDate() - 90);
    start = toIsoDate(d);
    end = toIsoDate(today);
  } else if (mode === "year") {
    const yearStart = new Date(today.getFullYear(), 0, 1);
    start = toIsoDate(yearStart);
    end = toIsoDate(today);
  }

  quickRangeMode.value = mode;
  since.value = start;
  until.value = end;

  syncFiltersToQuery();
  clearBucketDetails();
  refresh();
}

// lane preset application
function applyLanePreset(id: string) {
  const preset = lanePresets.value.find((p) => p.id === id);
  if (!preset) return;

  // set lane + preset
  laneFilter.value = preset.lane || "";
  presetFilter.value = preset.preset || "";

  // compute & apply quick range if defined
  const mode = preset.defaultQuickRange || "last30";
  const today = new Date();
  let start: string | "" = "";
  let end: string | "" = "";

  if (mode === "all") {
    start = "";
    end = "";
  } else if (mode === "last7") {
    const d = new Date(today);
    d.setDate(d.getDate() - 7);
    start = toIsoDate(d);
    end = toIsoDate(today);
  } else if (mode === "last30") {
    const d = new Date(today);
    d.setDate(d.getDate() - 30);
    start = toIsoDate(d);
    end = toIsoDate(today);
  } else if (mode === "last90") {
    const d = new Date(today);
    d.setDate(d.getDate() - 90);
    start = toIsoDate(d);
    end = toIsoDate(today);
  } else if (mode === "year") {
    const yearStart = new Date(today.getFullYear(), 0, 1);
    start = toIsoDate(yearStart);
    end = toIsoDate(today);
  }

  quickRangeMode.value = mode;
  since.value = start;
  until.value = end;

  syncFiltersToQuery();
  clearBucketDetails();
  refresh();
}

// computed: whether any filters are active
const hasAnyFilter = computed(() => {
  return (
    !!laneFilter.value ||
    !!presetFilter.value ||
    !!jobFilter.value ||
    !!since.value ||
    !!until.value
  );
});

// URL <-> filter sync helpers
function applyQueryToFilters() {
  const q = route.query;

  laneFilter.value = typeof q.lane === "string" ? q.lane : "";
  presetFilter.value = typeof q.preset === "string" ? q.preset : "";
  jobFilter.value = typeof q.job_hint === "string" ? q.job_hint : "";

  since.value = typeof q.since === "string" ? q.since : "";
  until.value = typeof q.until === "string" ? q.until : "";

  // derive quick range from query if it matches common patterns
  quickRangeMode.value = "";
  if (!since.value && !until.value) {
    quickRangeMode.value = "all";
  }
}

function syncFiltersToQuery() {
  const q: Record<string, any> = { ...route.query };

  function setOrDelete(key: string, val: string) {
    if (val && val.trim() !== "") {
      q[key] = val.trim();
    } else {
      delete q[key];
    }
  }

  setOrDelete("lane", laneFilter.value);
  setOrDelete("preset", presetFilter.value);
  setOrDelete("job_hint", jobFilter.value);
  setOrDelete("since", since.value);
  setOrDelete("until", until.value);

  router.replace({ query: q }).catch(() => {});
}

const allLanes = computed(() => {
  const set = new Set<string>();
  for (const b of bucketsRaw.value) {
    if (b.lane) set.add(b.lane);
  }
  return Array.from(set).sort();
});

const allPresets = computed(() => {
  const set = new Set<string>();
  for (const b of bucketsRaw.value) {
    set.add(b.preset || "(none)");
  }
  return Array.from(set).sort();
});

const filteredBuckets = computed<Bucket[]>(() => {
  return bucketsRaw.value.filter((b) => {
    if (laneFilter.value && b.lane !== laneFilter.value) return false;
    if (presetFilter.value && b.preset !== presetFilter.value) return false;
    return true;
  });
});

const filteredEntriesCount = computed(() => {
  return filteredBuckets.value.reduce((acc, b) => acc + b.count, 0);
});

function computeRiskScoreLabel(score: number): string {
  if (score < 1) return "Low";
  if (score < 3) return "Medium";
  if (score < 6) return "High";
  return "Extreme";
}

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
    const v = values[i] ?? 0;
    const norm = maxVal > 0 ? v / maxVal : 0;
    const y = height - norm * (height - 2) - 1;
    points.push(`${x.toFixed(1)},${y.toFixed(1)}`);
  }

  return points.join(" ");
}

async function refresh() {
  try {
    const params: Record<string, string> = {};
    if (since.value) params.since = since.value;
    if (until.value) params.until = until.value;

    const res = await axios.get<RiskAggregateBucketResponse[]>(
      "/api/compare/risk_aggregate",
      { params }
    );
    const data = res.data || [];
    bucketsRaw.value = data.map((row) => {
      const addedSeries = Array.isArray(row.added_series)
        ? row.added_series.map((v) => Number(v) || 0)
        : [];
      const removedSeries = Array.isArray(row.removed_series)
        ? row.removed_series.map((v) => Number(v) || 0)
        : [];
      const riskScore = Number(row.risk_score) || 0;
      const riskLabel = row.risk_label || computeRiskScoreLabel(riskScore);

      return {
        key: `${row.lane}::${row.preset}`,
        lane: row.lane,
        preset: row.preset,
        count: row.count,
        avgAdded: row.avg_added,
        avgRemoved: row.avg_removed,
        avgUnchanged: row.avg_unchanged,
        riskScore,
        riskLabel,
        addedSeries,
        removedSeries,
        addedPath: buildSparklineFromSeries(addedSeries, sparkWidth, sparkHeight),
        removedPath: buildSparklineFromSeries(removedSeries, sparkWidth, sparkHeight),
      };
    });
  } catch (err) {
    console.error("Failed to load risk aggregates", err);
    bucketsRaw.value = [];
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
      b.avgAdded,
      b.avgRemoved,
      b.avgUnchanged,
      b.riskScore,
      b.riskLabel,
    ]
      .map((val) => csvEscape(val))
      .join(",")
  );

  const csvContent = [headers.join(","), ...rows].join("\r\n");
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);

  const stamp = new Date().toISOString().replace(/[:.]/g, "-");
  const windowPart =
    (since.value ? `_from-${since.value}` : "") +
    (until.value ? `_to-${until.value}` : "");
  const filename = `crosslab_risk_aggregate${windowPart}_${stamp}.csv`;

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

function goToLab(bucket: Bucket) {
  const lane = bucket.lane.toLowerCase();
  const preset = bucket.preset;
  const jobHint = jobFilter.value || "";

  const query: Record<string, string> = {};
  if (preset && preset !== "(none)") query.preset = preset;
  if (lane) query.lane = lane;
  if (jobHint) query.job_hint = jobHint;

  if (lane.startsWith("rosette")) {
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
    router.push({
      path: "/lab/risk-dashboard",
      query,
    });
  }
}

async function loadBucketDetails(bucket: Bucket) {
  selectedBucket.value = bucket;
  bucketEntriesLoading.value = true;
  bucketEntriesError.value = null;
  bucketEntries.value = [];
  try {
    const params: Record<string, string> = {
      lane: bucket.lane,
      preset: bucket.preset,
    };
    if (jobFilter.value) {
      params.job_hint = jobFilter.value;
    }
    const res = await axios.get<BucketEntry[]>(
      "/api/compare/risk_bucket_detail",
      { params }
    );
    bucketEntries.value = res.data || [];
  } catch (err) {
    console.error("Failed to load bucket entries", err);
    bucketEntriesError.value = "Failed to load bucket entries.";
  } finally {
    bucketEntriesLoading.value = false;
  }
}

function clearBucketDetails() {
  selectedBucket.value = null;
  bucketEntries.value = [];
  bucketEntriesError.value = null;
  bucketEntriesLoading.value = false;
}

function formatMetaTime(ts?: string | null): string {
  if (!ts) return "—";
  try {
    const d = new Date(ts);
    return d.toLocaleString();
  } catch {
    return ts;
  }
}

// rough "x time ago" helper for recent views
function formatRelativeMetaTime(ts?: string | null): string {
  if (!ts) return "unknown";
  const t = Date.parse(ts);
  if (isNaN(t)) return ts;
  const now = Date.now();
  const diffMs = now - t;
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHr = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHr / 24);

  if (diffDay > 0) return `${diffDay}d ago`;
  if (diffHr > 0) return `${diffHr}h ago`;
  if (diffMin > 0) return `${diffMin}m ago`;
  return "just now";
}

function exportBucketCsvLocal() {
  if (!selectedBucket.value || !bucketEntries.value.length) return;

  const b = selectedBucket.value;
  const headers = [
    "ts",
    "job_id",
    "lane",
    "preset",
    "baseline_id",
    "baseline_path_count",
    "current_path_count",
    "added_paths",
    "removed_paths",
    "unchanged_paths",
  ];

  const rows = bucketEntries.value.map((e) =>
    [
      e.ts,
      e.job_id ?? "",
      e.lane,
      e.preset ?? "",
      e.baseline_id,
      e.baseline_path_count,
      e.current_path_count,
      e.added_paths,
      e.removed_paths,
      e.unchanged_paths,
    ]
      .map((v) => csvEscape(v))
      .join(",")
  );

  const csvContent = [headers.join(","), ...rows].join("\r\n");
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const hintPart = jobFilter.value ? `_hint-${jobFilter.value}` : "";
  const windowPart =
    (since.value ? `_from-${since.value}` : "") +
    (until.value ? `_to-${until.value}` : "");
  const stamp = new Date().toISOString().replace(/[:.]/g, "-");
  const filename = `bucket_${b.lane}_${b.preset}${hintPart}${windowPart}_${stamp}.csv`;

  const link = document.createElement("a");
  link.href = url;
  link.setAttribute("download", filename);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

async function downloadBucketJson() {
  if (!selectedBucket.value) return;
  const b = selectedBucket.value;

  try {
    const params: Record<string, string> = {
      lane: b.lane,
      preset: b.preset,
    };
    if (jobFilter.value) {
      params.job_hint = jobFilter.value;
    }

    const res = await axios.get("/api/compare/risk_bucket_report", {
      params,
      responseType: "json",
    });
    const jsonData = res.data;
    const blob = new Blob([JSON.stringify(jsonData, null, 2)], {
      type: "application/json",
    });
    const hintPart = jobFilter.value ? `_hint-${jobFilter.value}` : "";
    const windowPart =
      (since.value ? `_from-${since.value}` : "") +
      (until.value ? `_to-${until.value}` : "");
    const stamp = new Date().toISOString().replace(/[:.]/g, "-");
    const filename = `bucket_report_${b.lane}_${b.preset}${hintPart}${windowPart}_${stamp}.json`;

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  } catch (err) {
    console.error("Failed to download bucket JSON report", err);
    bucketEntriesError.value = "Failed to download bucket JSON report.";
  }
}

async function downloadSnapshotJson() {
  try {
    const params: Record<string, string> = {};
    if (since.value) params.since = since.value;
    if (until.value) params.until = until.value;

    const res = await axios.get("/api/compare/risk_snapshot", {
      params,
      responseType: "json",
    });
    const jsonData = res.data;
    const blob = new Blob([JSON.stringify(jsonData, null, 2)], {
      type: "application/json",
    });
    const windowPart =
      (since.value ? `_from-${since.value}` : "") +
      (until.value ? `_to-${until.value}` : "");
    const stamp = new Date().toISOString().replace(/[:.]/g, "-");
    const filename = `risk_snapshot${windowPart}_${stamp}.json`;
    const url = URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  } catch (err) {
    console.error("Failed to download global risk snapshot", err);
  }
}

// Phase 28.5: Export selected bucket as CSV
async function exportBucketCsv() {
  if (!selectedBucket.value) return;
  try {
    const params: Record<string, string> = {
      lane: selectedBucket.value.lane,
      preset: selectedBucket.value.preset,
      format: 'csv'
    };
    const res = await axios.get("/api/compare/risk_bucket_export", {
      params,
      responseType: 'blob'
    });
    
    const filename = `risk_bucket_${selectedBucket.value.lane}_${selectedBucket.value.preset}.csv`;
    const url = URL.createObjectURL(new Blob([res.data]));
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  } catch (err) {
    console.error("Failed to export bucket CSV", err);
  }
}

// Phase 28.5: Export selected bucket as JSON
async function exportBucketJson() {
  if (!selectedBucket.value) return;
  try {
    const params: Record<string, string> = {
      lane: selectedBucket.value.lane,
      preset: selectedBucket.value.preset,
      format: 'json'
    };
    const res = await axios.get("/api/compare/risk_bucket_export", {
      params,
      responseType: 'blob'
    });
    
    const filename = `risk_bucket_${selectedBucket.value.lane}_${selectedBucket.value.preset}.json`;
    const url = URL.createObjectURL(new Blob([res.data]));
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  } catch (err) {
    console.error("Failed to export bucket JSON", err);
  }
}

// toggle tag filter (used by tag chips in the view)
function toggleTagFilter(tag: string) {
  // For now, just log - implement filtering by tag if needed
  console.log('Toggle tag filter:', tag);
}

// clear all filters in one shot
function clearAllFilters() {
  laneFilter.value = "";
  presetFilter.value = "";
  jobFilter.value = "";
  since.value = "";
  until.value = "";
  quickRangeMode.value = "all";
  clearBucketDetails();
  syncFiltersToQuery();
  refresh();
}

function filtersAreEmpty(): boolean {
  return (
    !laneFilter.value &&
    !presetFilter.value &&
    !jobFilter.value &&
    !since.value &&
    !until.value
  );
}

function applyDefaultViewIfNeeded() {
  const hasQuery =
    typeof route.query.lane === "string" ||
    typeof route.query.preset === "string" ||
    typeof route.query.job_hint === "string" ||
    typeof route.query.since === "string" ||
    typeof route.query.until === "string";

  if (hasQuery) return;
  if (!filtersAreEmpty()) return;

  // Access default view from the panel component
  const def = savedViewsPanelRef.value?.defaultView;
  if (!def) {
    // if no default view, default quick range is "all"
    quickRangeMode.value = "all";
    return;
  }
  handleApplyFilters(def.filters);
}

onMounted(async () => {
  applyQueryToFilters();
  // Wait for panel to mount and load views before applying default
  await nextTick();
  applyDefaultViewIfNeeded();
  refresh();
});

watch(
  () => [laneFilter.value, presetFilter.value, jobFilter.value],
  () => {
    // if user manually changes these, quick range remains unchanged
    syncFiltersToQuery();
    clearBucketDetails();
  }
);

watch(
  () => [since.value, until.value],
  () => {
    // manual date edits switch quick range to "custom"
    if (since.value || until.value) {
      quickRangeMode.value = "";
    } else {
      quickRangeMode.value = "all";
    }
    syncFiltersToQuery();
    clearBucketDetails();
    refresh();
  }
);
