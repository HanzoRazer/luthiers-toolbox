This view:

Loads the saved jobs list from /api/art/rosette/jobs

Lets you pick job A and job B

Calls POST /api/art/rosette/compare

Shows two canvases plus a small diff summary panel

<template>
  <div class="p-4 flex gap-4">
    <!-- Main content area -->
    <div class="flex-1 flex flex-col gap-4">
      <!-- Header -->
      <div class="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 class="text-base font-semibold text-gray-900">
            Art Studio · Rosette Compare
          </h1>
          <p class="text-xs text-gray-600 max-w-xl">
            Select two saved rosette jobs (A &amp; B), then compare geometry and key parameters.
            This is the first Compare Mode hook — later we can add overlay coloring and analytics.
          </p>
        </div>
        <div class="flex items-center gap-2">
          <button
            class="px-3 py-1 rounded border text-[11px] text-gray-700 hover:bg-gray-50"
            @click="reloadJobs"
          >
            Reload jobs
          </button>
          <button
            v-if="selectedJobIdA && selectedJobIdB"
            class="px-3 py-1 rounded border text-[11px] text-blue-700 hover:bg-blue-50"
            @click="toggleHistorySidebar"
          >
            {{ showHistory ? 'Hide' : 'Show' }} History
          </button>
        </div>
      </div>

      <!-- Job selectors -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div class="border rounded-lg bg-white shadow-sm p-3 text-[11px] text-gray-800">
          <h2 class="text-[12px] font-semibold mb-2 text-gray-900">
            Baseline (A)
          </h2>
          <select
            v-model="selectedJobIdA"
            class="w-full px-2 py-1 border rounded text-[11px]"
          >
            <option value="">
              (select a job)
            </option>
            <option
              v-for="job in jobs"
              :key="job.job_id"
              :value="job.job_id"
            >
              {{ job.name || job.job_id }} · {{ job.preview.preset || 'no preset' }}
            </option>
          </select>
          <p class="text-[10px] text-gray-500 mt-1">
            Pick the baseline rosette you want to compare from your recent jobs.
          </p>
        </div>

        <div class="border rounded-lg bg-white shadow-sm p-3 text-[11px] text-gray-800">
          <h2 class="text-[12px] font-semibold mb-2 text-gray-900">
            Variant (B)
          </h2>
          <select
            v-model="selectedJobIdB"
            class="w-full px-2 py-1 border rounded text-[11px]"
          >
            <option value="">
              (select a job)
            </option>
            <option
              v-for="job in jobs"
              :key="job.job_id"
              :value="job.job_id"
            >
              {{ job.name || job.job_id }} · {{ job.preview.preset || 'no preset' }}
            </option>
          </select>
          <p class="text-[10px] text-gray-500 mt-1">
            Pick the variant rosette to compare against baseline.
          </p>
        </div>
      </div>

      <div class="flex flex-wrap items-center gap-2">
        <button
          class="px-3 py-1 rounded bg-indigo-600 text-white text-[11px] hover:bg-indigo-700 disabled:opacity-50"
          :disabled="compareLoading || !selectedJobIdA || !selectedJobIdB"
          @click="runCompare"
        >
          {{ compareLoading ? 'Comparing…' : 'Compare A ↔ B' }}
        </button>
        <!-- Phase 27.2: Save to Risk Timeline button -->
        <button
          v-if="compareResult"
          class="px-3 py-1 rounded bg-blue-600 text-white text-[11px] hover:bg-blue-700 disabled:opacity-50"
          :disabled="saveSnapshotLoading"
          @click="saveSnapshot"
        >
          {{ saveSnapshotLoading ? 'Saving…' : '💾 Save to Risk Timeline' }}
        </button>
        <p
          v-if="statusMessage"
          class="text-[10px]"
          :class="statusClass"
        >
          {{ statusMessage }}
        </p>
      </div>

      <!-- Diff summary -->
      <CompareDiffSummary
        v-if="compareResult"
        :diff-summary="compareResult.diff_summary"
      />

      <!-- Dual canvases with Phase 27.1 coloring -->
      <div
        v-if="compareResult"
        class="grid grid-cols-1 md:grid-cols-2 gap-3"
      >
        <!-- Baseline (A) Canvas -->
        <div class="border rounded-lg bg-white shadow-sm p-3 flex flex-col gap-2 relative">
          <!-- Legend -->
          <div class="absolute top-2 right-2 bg-white/90 p-2 rounded shadow text-[10px] z-10 border border-gray-200">
            <div class="flex items-center gap-1">
              <span
                class="w-3 h-3 rounded"
                style="background:#111827;"
              />
              <span>Unchanged</span>
            </div>
            <div class="flex items-center gap-1 mt-1">
              <span
                class="w-3 h-3 rounded"
                style="background:#10b981;"
              />
              <span>Added in A</span>
            </div>
            <div class="flex items-center gap-1 mt-1">
              <span
                class="w-3 h-3 rounded"
                style="background:#ef4444;"
              />
              <span>Removed from A</span>
            </div>
          </div>
        
          <div class="flex items-center justify-between">
            <div>
              <h2 class="text-[12px] font-semibold text-gray-900">
                Baseline (A)
              </h2>
              <p class="text-[10px] text-gray-500">
                {{ compareResult.job_a.name || compareResult.job_a.job_id }} ·
                {{ compareResult.job_a.preset || 'no preset' }}
              </p>
            </div>
            <div class="text-[10px] font-mono text-gray-500">
              {{ compareResult.job_a.segments }} seg
            </div>
          </div>
          <div
            class="border rounded bg-gray-50 flex items-center justify-center"
            style="height: 260px;"
          >
            <svg
              v-if="compareResult.job_a.paths.length"
              :viewBox="viewBoxUnion"
              preserveAspectRatio="xMidYMid meet"
              class="w-full h-full"
            >
              <!-- Unchanged paths (common segment count) -->
              <polyline
                v-for="(path, idx) in unchangedPathsA"
                :key="'a_unchanged_' + idx"
                :points="polylinePoints(path.points)"
                fill="none"
                stroke="#111827"
                stroke-width="0.4"
              />
              <!-- Added paths (A has more segments than B) -->
              <polyline
                v-for="(path, idx) in addedPathsA"
                :key="'a_added_' + idx"
                :points="polylinePoints(path.points)"
                fill="none"
                stroke="#10b981"
                stroke-width="0.7"
              />
            </svg>
            <div
              v-else
              class="text-[10px] text-gray-500 italic"
            >
              No geometry for job A.
            </div>
          </div>
        </div>

        <!-- Variant (B) Canvas -->
        <div class="border rounded-lg bg-white shadow-sm p-3 flex flex-col gap-2 relative">
          <!-- Legend -->
          <div class="absolute top-2 right-2 bg-white/90 p-2 rounded shadow text-[10px] z-10 border border-gray-200">
            <div class="flex items-center gap-1">
              <span
                class="w-3 h-3 rounded"
                style="background:#111827;"
              />
              <span>Unchanged</span>
            </div>
            <div class="flex items-center gap-1 mt-1">
              <span
                class="w-3 h-3 rounded"
                style="background:#10b981;"
              />
              <span>Added in B</span>
            </div>
            <div class="flex items-center gap-1 mt-1">
              <span
                class="w-3 h-3 rounded"
                style="background:#ef4444;"
              />
              <span>Removed from B</span>
            </div>
          </div>
        
          <div class="flex items-center justify-between">
            <div>
              <h2 class="text-[12px] font-semibold text-gray-900">
                Variant (B)
              </h2>
              <p class="text-[10px] text-gray-500">
                {{ compareResult.job_b.name || compareResult.job_b.job_id }} ·
                {{ compareResult.job_b.preset || 'no preset' }}
              </p>
            </div>
            <div class="text-[10px] font-mono text-gray-500">
              {{ compareResult.job_b.segments }} seg
            </div>
          </div>
          <div
            class="border rounded bg-gray-50 flex items-center justify-center"
            style="height: 260px;"
          >
            <svg
              v-if="compareResult.job_b.paths.length"
              :viewBox="viewBoxUnion"
              preserveAspectRatio="xMidYMid meet"
              class="w-full h-full"
            >
              <!-- Unchanged paths (common segment count) -->
              <polyline
                v-for="(path, idx) in unchangedPathsB"
                :key="'b_unchanged_' + idx"
                :points="polylinePoints(path.points)"
                fill="none"
                stroke="#111827"
                stroke-width="0.4"
              />
              <!-- Added paths (B has more segments than A) -->
              <polyline
                v-for="(path, idx) in addedPathsB"
                :key="'b_added_' + idx"
                :points="polylinePoints(path.points)"
                fill="none"
                stroke="#10b981"
                stroke-width="0.7"
              />
            </svg>
            <div
              v-else
              class="text-[10px] text-gray-500 italic"
            >
              No geometry for job B.
            </div>
          </div>
        </div>
      </div>

      <div
        v-else
        class="text-[11px] text-gray-500 italic"
      >
        Pick two jobs and run a comparison to see dual canvases and a diff summary.
      </div>
    </div> <!-- End main content area -->

    <!-- History Sidebar -->
    <CompareHistorySidebar
      v-if="showHistory && selectedJobIdA && selectedJobIdB"
      v-model:group-by-preset="groupByPreset"
      :history-snapshots="historySnapshots"
      :history-loading="historyLoading"
      :expanded-groups="expandedGroups"
      :grouped-snapshots="groupedSnapshots"
      :average-risk="averageRisk"
      :low-risk-count="lowRiskCount"
      :medium-risk-count="mediumRiskCount"
      :high-risk-count="highRiskCount"
      @toggle-group="toggleGroup"
      @export-csv="exportHistoryCSV"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import axios from "axios";
import { useRoute } from "vue-router";
import CompareDiffSummary from "./rosette_compare/CompareDiffSummary.vue";
import CompareHistorySidebar from "./rosette_compare/CompareHistorySidebar.vue";

interface RosettePath {
  points: [number, number][];
}

interface RosettePreview {
  job_id: string;
  pattern_type: string;
  segments: number;
  inner_radius: number;
  outer_radius: number;
  units: string;
  preset: string | null;
  name: string | null;
  paths: RosettePath[];
  bbox: [number, number, number, number];
}

interface RosetteJob {
  job_id: string;
  name: string | null;
  preset: string | null;
  created_at: string;
  preview: RosettePreview;
}

interface RosetteDiffSummary {
  job_id_a: string;
  job_id_b: string;
  pattern_type_a: string;
  pattern_type_b: string;
  pattern_type_same: boolean;
  segments_a: number;
  segments_b: number;
  segments_delta: number;
  inner_radius_a: number;
  inner_radius_b: number;
  inner_radius_delta: number;
  outer_radius_a: number;
  outer_radius_b: number;
  outer_radius_delta: number;
  units_a: string;
  units_b: string;
  units_same: boolean;
  bbox_union: [number, number, number, number];
  bbox_a: [number, number, number, number];
  bbox_b: [number, number, number, number];
  preset_a?: string;  // Phase 27.4: Optional preset fields
  preset_b?: string;
}

interface RosetteCompareResult {
  job_a: RosettePreview;
  job_b: RosettePreview;
  diff_summary: RosetteDiffSummary;
}

// Phase 27.3: History snapshot interface
interface CompareSnapshot {
  id: number;
  job_id_a: string;
  job_id_b: string;
  lane: string | null;
  risk_score: number;
  diff_summary: RosetteDiffSummary;
  note: string | null;
  created_at: string;
}

const route = useRoute();

const jobs = ref<RosetteJob[]>([]);
const jobsLoading = ref(false);
const jobsError = ref<string | null>(null);

const selectedJobIdA = ref<string>("");
const selectedJobIdB = ref<string>("");

const compareResult = ref<RosetteCompareResult | null>(null);
const compareLoading = ref(false);

const statusMessage = ref("");
const statusIsError = ref(false);

// Phase 27.2: Save snapshot state
const saveSnapshotLoading = ref(false);

// Phase 27.3: History sidebar state
const showHistory = ref(false);
const historySnapshots = ref<CompareSnapshot[]>([]);
const historyLoading = ref(false);

// Phase 27.4: Preset grouping state
const groupByPreset = ref(false);
const expandedGroups = ref<Set<string>>(new Set());

const statusClass = computed(() =>
  statusIsError.value ? "text-[10px] text-rose-600" : "text-[10px] text-emerald-700"
);

function setStatus(msg: string, isError = false) {
  statusMessage.value = msg;
  statusIsError.value = isError;
}

function polylinePoints(pts: [number, number][]): string {
  return pts.map(([x, y]) => `${x},${y}`).join(" ");
}

const viewBoxUnion = computed(() => {
  if (!compareResult.value) return "-60 -60 120 120";
  const u = compareResult.value.diff_summary.bbox_union;
  const pad = 5;
  const width = u[2] - u[0] || 1;
  const height = u[3] - u[1] || 1;
  const x = u[0] - pad;
  const y = u[1] - pad;
  const w = width + pad * 2;
  const h = height + pad * 2;
  return `${x} ${y} ${w} ${h}`;
});

// Phase 27.1: Computed properties for colored segments
// Strategy: Split paths based on segment count difference
// - If A has more paths than B, the extras are "added in A" (green)
// - If B has more paths than A, the extras are "added in B" (green)
// - Common path count is "unchanged" (gray)
const commonPathCount = computed(() => {
  if (!compareResult.value) return 0;
  return Math.min(
    compareResult.value.job_a.paths.length,
    compareResult.value.job_b.paths.length
  );
});

const unchangedPathsA = computed(() => {
  if (!compareResult.value) return [];
  return compareResult.value.job_a.paths.slice(0, commonPathCount.value);
});

const addedPathsA = computed(() => {
  if (!compareResult.value) return [];
  return compareResult.value.job_a.paths.slice(commonPathCount.value);
});

const unchangedPathsB = computed(() => {
  if (!compareResult.value) return [];
  return compareResult.value.job_b.paths.slice(0, commonPathCount.value);
});

const addedPathsB = computed(() => {
  if (!compareResult.value) return [];
  return compareResult.value.job_b.paths.slice(commonPathCount.value);
});

// Phase 27.4: Group snapshots by preset pair
const groupedSnapshots = computed(() => {
  if (!historySnapshots.value.length) return {};

  const groups: Record<string, {
    presetLabel: string;
    snapshots: CompareSnapshot[];
    avgRisk: number;
  }> = {};

  historySnapshots.value.forEach((snapshot) => {
    const presetA = snapshot.diff_summary.preset_a || "Unknown";
    const presetB = snapshot.diff_summary.preset_b || "Unknown";
    const groupKey = `${presetA} vs ${presetB}`;

    if (!groups[groupKey]) {
      groups[groupKey] = {
        presetLabel: groupKey,
        snapshots: [],
        avgRisk: 0,
      };
    }

    groups[groupKey].snapshots.push(snapshot);
  });

  // Calculate average risk for each group
  Object.values(groups).forEach((group) => {
    const totalRisk = group.snapshots.reduce((sum, s) => sum + s.risk_score, 0);
    group.avgRisk = group.snapshots.length > 0 ? totalRisk / group.snapshots.length : 0;
  });

  return groups;
});

// Phase 27.5: Risk metrics computed properties
const averageRisk = computed(() => {
  if (!historySnapshots.value.length) return 0;
  const total = historySnapshots.value.reduce((sum, s) => sum + s.risk_score, 0);
  return total / historySnapshots.value.length;
});

const lowRiskCount = computed(() => {
  return historySnapshots.value.filter(s => s.risk_score < 40).length;
});

const mediumRiskCount = computed(() => {
  return historySnapshots.value.filter(s => s.risk_score >= 40 && s.risk_score < 70).length;
});

const highRiskCount = computed(() => {
  return historySnapshots.value.filter(s => s.risk_score >= 70).length;
});

async function reloadJobs() {
  jobsLoading.value = true;
  jobsError.value = null;
  try {
    const res = await axios.get<RosetteJob[]>("/api/art/rosette/jobs", {
      params: { limit: 50 },
    });
    jobs.value = res.data || [];
  } catch (err) {
    console.error("Failed to load rosette jobs", err);
    jobsError.value = "Failed to load rosette jobs.";
  } finally {
    jobsLoading.value = false;
  }
}

async function runCompare() {
  if (!selectedJobIdA.value || !selectedJobIdB.value) {
    setStatus("Please select both A and B jobs.", true);
    return;
  }
  setStatus("");
  compareLoading.value = true;
  compareResult.value = null;
  try {
    const payload = {
      job_id_a: selectedJobIdA.value,
      job_id_b: selectedJobIdB.value,
    };
    const res = await axios.post<RosetteCompareResult>("/api/art/rosette/compare", payload);
    compareResult.value = res.data;
    setStatus("Compare complete.", false);
  } catch (err: any) {
    console.error("Compare failed", err);
    const msg =
      err?.response?.data?.detail ||
      "Failed to compare rosette jobs.";
    setStatus(msg, true);
  } finally {
    compareLoading.value = false;
  }
}

// Phase 27.2: Calculate risk score from diff summary
// Formula: base_score = abs(segments_delta) / max(seg_a, seg_b) * 50
//          radius_contribution = abs(inner_delta + outer_delta) / 10 * 50
//          risk_score = clamp(base_score + radius_contribution, 0, 100)
function calculateRiskScore(diff: RosetteDiffSummary): number {
  const segA = diff.segments_a || 0;
  const segB = diff.segments_b || 0;
  const maxSeg = Math.max(segA, segB);
  const segDelta = Math.abs(diff.segments_delta || 0);

  const innerDelta = Math.abs(diff.inner_radius_delta || 0);
  const outerDelta = Math.abs(diff.outer_radius_delta || 0);

  const baseScore = maxSeg > 0 ? (segDelta / maxSeg) * 50 : 0;
  const radiusScore = ((innerDelta + outerDelta) / 10) * 50;

  const totalScore = baseScore + radiusScore;
  return Math.min(Math.max(totalScore, 0), 100);
}

// Phase 27.2: Save comparison snapshot to risk timeline
async function saveSnapshot() {
  if (!compareResult.value) {
    setStatus("No comparison result to save.", true);
    return;
  }

  saveSnapshotLoading.value = true;
  setStatus("");

  const riskScore = calculateRiskScore(compareResult.value.diff_summary);

  try {
    const payload = {
      job_id_a: compareResult.value.diff_summary.job_id_a,
      job_id_b: compareResult.value.diff_summary.job_id_b,
      risk_score: riskScore,
      diff_summary: compareResult.value.diff_summary,
      lane: "production", // Default lane (could make this configurable later)
      note: null, // Optional note field (could add textarea input later)
    };

    const res = await axios.post("/api/art/rosette/compare/snapshot", payload);
    console.log("Snapshot saved:", res.data);
    setStatus(`✓ Saved to Risk Timeline (risk: ${riskScore.toFixed(1)}%)`, false);
  } catch (err: any) {
    console.error("Failed to save snapshot:", err);
    const msg =
      err?.response?.data?.detail ||
      "Failed to save comparison snapshot.";
    setStatus(msg, true);
  } finally {
    saveSnapshotLoading.value = false;
  }
}

// Phase 27.3: Toggle history sidebar
function toggleHistorySidebar() {
  showHistory.value = !showHistory.value;
  if (showHistory.value && selectedJobIdA.value && selectedJobIdB.value) {
    loadHistory();
  }
}

// Phase 27.4: Toggle preset group expansion
function toggleGroup(groupKey: string) {
  if (expandedGroups.value.has(groupKey)) {
    expandedGroups.value.delete(groupKey);
  } else {
    expandedGroups.value.add(groupKey);
  }
  // Force reactivity update
  expandedGroups.value = new Set(expandedGroups.value);
}

// Phase 27.3: Load comparison history from backend
async function loadHistory() {
  if (!selectedJobIdA.value || !selectedJobIdB.value) return;

  historyLoading.value = true;
  try {
    const res = await axios.get<CompareSnapshot[]>("/api/art/rosette/compare/snapshots", {
      params: {
        job_id_a: selectedJobIdA.value,
        job_id_b: selectedJobIdB.value,
        limit: 50,
      },
    });
    historySnapshots.value = res.data || [];
  } catch (err) {
    console.error("Failed to load history:", err);
    historySnapshots.value = [];
  } finally {
    historyLoading.value = false;
  }
}

// Phase 27.3: Export history as CSV
async function exportHistoryCSV() {
  if (!selectedJobIdA.value || !selectedJobIdB.value) return;

  try {
    const params = new URLSearchParams({
      job_id_a: selectedJobIdA.value,
      job_id_b: selectedJobIdB.value,
      limit: "100",
    });

    // Open CSV in new tab (browser will download it)
    window.open(`/api/art/rosette/compare/export_csv?${params.toString()}`, "_blank");
  } catch (err) {
    console.error("Failed to export CSV:", err);
    setStatus("Failed to export CSV.", true);
  }
}

onMounted(async () => {
  await reloadJobs();

  // Optional: pre-fill from query params (e.g. /art-studio/rosette/compare?jobA=...&jobB=...)
  const jobA = route.query.jobA as string | undefined;
  const jobB = route.query.jobB as string | undefined;
  if (jobA) selectedJobIdA.value = jobA;
  if (jobB) selectedJobIdB.value = jobB;
});
</script>
