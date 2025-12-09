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
          <option value="">(select a job)</option>
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
          <option value="">(select a job)</option>
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
      <p v-if="statusMessage" class="text-[10px]" :class="statusClass">
        {{ statusMessage }}
      </p>
    </div>

    <!-- Diff summary -->
    <div
      v-if="compareResult"
      class="border rounded-lg bg-white shadow-sm p-3 text-[11px] text-gray-800"
    >
      <h2 class="text-[12px] font-semibold text-gray-900 mb-1">
        Diff Summary
      </h2>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-2">
        <div>
          <h3 class="font-semibold text-[11px] text-gray-900 mb-0.5">
            Pattern & Segments
          </h3>
          <p class="text-[10px] text-gray-700">
            A: {{ compareResult.diff_summary.pattern_type_a }} ·
            {{ compareResult.diff_summary.segments_a }} seg
          </p>
          <p class="text-[10px] text-gray-700">
            B: {{ compareResult.diff_summary.pattern_type_b }} ·
            {{ compareResult.diff_summary.segments_b }} seg
          </p>
          <p class="text-[10px]" :class="deltaClass(compareResult.diff_summary.segments_delta)">
            Δ segments: {{ signed(compareResult.diff_summary.segments_delta) }}
          </p>
        </div>
        <div>
          <h3 class="font-semibold text-[11px] text-gray-900 mb-0.5">
            Radii
          </h3>
          <p class="text-[10px] text-gray-700">
            Inner A: {{ compareResult.diff_summary.inner_radius_a }} ·
            B: {{ compareResult.diff_summary.inner_radius_b }}
          </p>
          <p class="text-[10px]" :class="deltaClass(compareResult.diff_summary.inner_radius_delta)">
            Δ inner: {{ signedFloat(compareResult.diff_summary.inner_radius_delta) }}
          </p>
          <p class="text-[10px] text-gray-700 mt-1">
            Outer A: {{ compareResult.diff_summary.outer_radius_a }} ·
            B: {{ compareResult.diff_summary.outer_radius_b }}
          </p>
          <p class="text-[10px]" :class="deltaClass(compareResult.diff_summary.outer_radius_delta)">
            Δ outer: {{ signedFloat(compareResult.diff_summary.outer_radius_delta) }}
          </p>
        </div>
        <div>
          <h3 class="font-semibold text-[11px] text-gray-900 mb-0.5">
            Units & BBox
          </h3>
          <p class="text-[10px] text-gray-700">
            Units A: {{ compareResult.diff_summary.units_a }} ·
            B: {{ compareResult.diff_summary.units_b }}
          </p>
          <p class="text-[10px]" :class="compareResult.diff_summary.units_same ? 'text-emerald-700' : 'text-amber-700'">
            Units {{ compareResult.diff_summary.units_same ? 'match' : 'differ' }}
          </p>
          <p class="text-[10px] text-gray-700 mt-1">
            BBox union:
            [{{ compareResult.diff_summary.bbox_union.join(', ') }}]
          </p>
        </div>
      </div>
    </div>

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
            <span class="w-3 h-3 rounded" style="background:#111827;"></span>
            <span>Unchanged</span>
          </div>
          <div class="flex items-center gap-1 mt-1">
            <span class="w-3 h-3 rounded" style="background:#10b981;"></span>
            <span>Added in A</span>
          </div>
          <div class="flex items-center gap-1 mt-1">
            <span class="w-3 h-3 rounded" style="background:#ef4444;"></span>
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
          <div v-else class="text-[10px] text-gray-500 italic">
            No geometry for job A.
          </div>
        </div>
      </div>

      <!-- Variant (B) Canvas -->
      <div class="border rounded-lg bg-white shadow-sm p-3 flex flex-col gap-2 relative">
        <!-- Legend -->
        <div class="absolute top-2 right-2 bg-white/90 p-2 rounded shadow text-[10px] z-10 border border-gray-200">
          <div class="flex items-center gap-1">
            <span class="w-3 h-3 rounded" style="background:#111827;"></span>
            <span>Unchanged</span>
          </div>
          <div class="flex items-center gap-1 mt-1">
            <span class="w-3 h-3 rounded" style="background:#10b981;"></span>
            <span>Added in B</span>
          </div>
          <div class="flex items-center gap-1 mt-1">
            <span class="w-3 h-3 rounded" style="background:#ef4444;"></span>
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
          <div v-else class="text-[10px] text-gray-500 italic">
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

    <!-- Phase 27.3: History Sidebar -->
    <div
      v-if="showHistory && selectedJobIdA && selectedJobIdB"
      class="w-80 border-l bg-gray-50 p-3 flex flex-col gap-2 overflow-y-auto"
      style="max-height: calc(100vh - 4rem);"
    >
      <div class="flex items-center justify-between mb-2">
        <h2 class="text-[13px] font-semibold text-gray-900">
          Comparison History
        </h2>
        <button
          class="px-2 py-0.5 rounded border text-[10px] text-blue-700 hover:bg-blue-50"
          @click="exportHistoryCSV"
          :disabled="historyLoading || !historySnapshots.length"
        >
          Export CSV
        </button>
      </div>

      <!-- Phase 27.4: Preset grouping toggle -->
      <div
        v-if="historySnapshots.length > 0"
        class="flex items-center gap-2 mb-2 pb-2 border-b"
      >
        <label class="flex items-center gap-1 text-[10px] text-gray-700 cursor-pointer">
          <input
            type="checkbox"
            v-model="groupByPreset"
            class="rounded"
          />
          Group by Preset
        </label>
      </div>

      <!-- Phase 27.5: Risk Metrics Bar -->
      <div
        v-if="historySnapshots.length > 0"
        class="border rounded bg-white p-2 mb-2"
      >
        <div class="text-[10px] font-semibold text-gray-900 mb-1.5">
          Risk Overview
        </div>
        <div class="grid grid-cols-2 gap-2 text-[9px]">
          <div>
            <div class="text-gray-600">Total</div>
            <div class="font-semibold text-gray-900">{{ historySnapshots.length }}</div>
          </div>
          <div>
            <div class="text-gray-600">Avg Risk</div>
            <div class="font-semibold" :class="riskTextClass(averageRisk)">
              {{ averageRisk.toFixed(1) }}%
            </div>
          </div>
          <div>
            <div class="text-green-700">Low (<40%)</div>
            <div class="font-semibold text-green-800">{{ lowRiskCount }}</div>
          </div>
          <div>
            <div class="text-yellow-700">Med (40-70%)</div>
            <div class="font-semibold text-yellow-800">{{ mediumRiskCount }}</div>
          </div>
          <div class="col-span-2">
            <div class="text-red-700">High (>70%)</div>
            <div class="font-semibold text-red-800">{{ highRiskCount }}</div>
          </div>
        </div>
        
        <!-- Risk distribution bar -->
        <div class="mt-2 flex h-2 rounded overflow-hidden">
          <div
            v-if="lowRiskCount > 0"
            class="bg-green-500"
            :style="{ width: `${(lowRiskCount / historySnapshots.length) * 100}%` }"
          ></div>
          <div
            v-if="mediumRiskCount > 0"
            class="bg-yellow-500"
            :style="{ width: `${(mediumRiskCount / historySnapshots.length) * 100}%` }"
          ></div>
          <div
            v-if="highRiskCount > 0"
            class="bg-red-500"
            :style="{ width: `${(highRiskCount / historySnapshots.length) * 100}%` }"
          ></div>
        </div>
      </div>

      <!-- Phase 27.6: Preset Scorecards -->
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
            <div class="text-[10px] font-semibold text-gray-900 mb-1 truncate" :title="group.presetLabel">
              {{ group.presetLabel }}
            </div>
            
            <!-- Scorecard metrics -->
            <div class="grid grid-cols-2 gap-1 text-[9px] mb-1.5">
              <div>
                <div class="text-gray-600">Total</div>
                <div class="font-semibold text-gray-900">{{ group.snapshots.length }}</div>
              </div>
              <div>
                <div class="text-gray-600">Avg</div>
                <div class="font-semibold" :class="riskTextClass(group.avgRisk)">
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
              <svg viewBox="0 0 120 20" class="w-full h-4">
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

      <div v-if="historyLoading" class="text-[10px] text-gray-500 italic">
        Loading history...
      </div>

      <div
        v-else-if="historySnapshots.length === 0"
        class="text-[10px] text-gray-500 italic"
      >
        No comparison history for these jobs yet. Run a comparison and save to timeline.
      </div>

      <!-- Phase 27.4: Grouped or flat history display -->
      <div v-else-if="!groupByPreset" class="flex flex-col gap-2">
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

          <!-- Sparkline: segments over time (simplified inline SVG) -->
          <div class="mb-1">
            <svg viewBox="0 0 80 20" class="w-full h-5">
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

          <div v-if="snapshot.lane" class="mt-1 text-[9px] text-gray-500">
            Lane: {{ snapshot.lane }}
          </div>
        </div>
      </div>

      <!-- Phase 27.4: Preset-grouped history -->
      <div v-else class="flex flex-col gap-2">
        <div
          v-for="(group, groupKey) in groupedSnapshots"
          :key="groupKey"
          class="border rounded bg-white overflow-hidden"
        >
          <!-- Group header -->
          <button
            @click="toggleGroup(groupKey)"
            class="w-full px-2 py-1.5 flex items-center justify-between hover:bg-gray-50 text-left"
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
              {{ expandedGroups.has(groupKey) ? '▼' : '▶' }}
            </span>
          </button>

          <!-- Group content (collapsible) -->
          <div
            v-if="expandedGroups.has(groupKey)"
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
                <svg viewBox="0 0 80 20" class="w-full h-5">
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

              <div v-if="snapshot.lane" class="mt-1 text-[9px] text-gray-500">
                Lane: {{ snapshot.lane }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import axios from "axios";
import { useRoute } from "vue-router";

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

function signed(n: number): string {
  if (n > 0) return `+${n}`;
  return `${n}`;
}

function signedFloat(n: number): string {
  const fixed = n.toFixed(2);
  if (n > 0) return `+${fixed}`;
  return fixed;
}

function deltaClass(delta: number): string {
  if (delta === 0) return "text-[10px] text-gray-600";
  if (delta > 0) return "text-[10px] text-indigo-700";
  return "text-[10px] text-amber-700";
}

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

// Phase 27.3: Format date for display
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

// Phase 27.3: Risk score color class
function riskClass(score: number): string {
  if (score >= 70) return "bg-red-100 text-red-800";
  if (score >= 40) return "bg-yellow-100 text-yellow-800";
  return "bg-green-100 text-green-800";
}

// Phase 27.3: Risk score stroke color
function riskColor(score: number): string {
  if (score >= 70) return "#ef4444"; // red
  if (score >= 40) return "#f59e0b"; // yellow
  return "#10b981"; // green
}

// Phase 27.5: Risk score text color class
function riskTextClass(score: number): string {
  if (score >= 70) return "text-red-700";
  if (score >= 40) return "text-yellow-700";
  return "text-green-700";
}

// Phase 27.3: Generate sparkline points (simplified - just showing risk trend)
function generateSparkline(snapshot: CompareSnapshot): string {
  // For now, create a simple visualization based on deltas
  // In a full implementation, you'd show trend over time
  const segDelta = Math.abs(snapshot.diff_summary.segments_delta || 0);
  const innerDelta = Math.abs(snapshot.diff_summary.inner_radius_delta || 0);
  const outerDelta = Math.abs(snapshot.diff_summary.outer_radius_delta || 0);

  // Normalize to 0-20 range for SVG viewBox
  const segY = Math.min(segDelta * 2, 18);
  const innerY = Math.min(innerDelta * 3, 18);
  const outerY = Math.min(outerDelta * 3, 18);

  // Create a simple 3-point line showing the delta magnitudes
  return `0,${20 - segY} 40,${20 - innerY} 80,${20 - outerY}`;
}

// Phase 27.6: Generate preset-level sparkline (risk trend over time)
function generatePresetSparkline(snapshots: CompareSnapshot[]): string {
  if (snapshots.length === 0) return "0,10 120,10";
  if (snapshots.length === 1) {
    const y = 20 - (snapshots[0].risk_score / 100) * 18;
    return `0,${y} 120,${y}`;
  }

  // Sort by timestamp (oldest first)
  const sorted = [...snapshots].sort((a, b) =>
    a.created_at.localeCompare(b.created_at)
  );

  // Generate points across the width
  const width = 120;
  const points = sorted.map((s, i) => {
    const x = (i / (sorted.length - 1)) * width;
    const y = 20 - (s.risk_score / 100) * 18; // 0-100% mapped to 20-2 (inverted Y)
    return `${x},${y}`;
  });

  return points.join(" ");
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

3️⃣ Frontend: Add Compare route to router

In your main router (packages/client/src/router/index.ts or equivalent), add:

// packages/client/src/router/index.ts
