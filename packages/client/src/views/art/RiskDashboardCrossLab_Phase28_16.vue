Phase 28.16 – Quick Time Range Chips as a single drop-in bundle.
What this adds on top of 28.15:


A quick time-range bar next to the date filters:


All · Last 7d · Last 30d · Last 90d · This year




Clicking a chip:


Automatically sets since / until


Syncs URL query


Triggers a fresh risk_aggregate load




Keeps manual date inputs working exactly as before



1️⃣ Frontend – RiskDashboardCrossLab.vue
File: client/src/views/RiskDashboardCrossLab.vue
Action: Replace the entire file with this version.
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
          Export CSV
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
    <div class="flex flex-col gap-2 text-[11px] text-gray-700">
      <div class="flex flex-wrap items-center gap-3">
        <div class="flex items-center gap-2">
          <span class="font-semibold">Lane:</span>
          <select
            v-model="laneFilter"
            class="px-2 py-1 border rounded text-[11px]"
          >
            <option value="">All</option>
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
            <option value="">All</option>
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
          <span class="font-semibold">Job hint:</span>
          <input
            v-model="jobFilter"
            type="text"
            placeholder="rosette_, neck_pocket..."
            class="px-2 py-1 border rounded text-[11px] w-48"
          />
          <span class="text-[10px] text-gray-500">
            Used for deep links &amp; bucket details (not filtering aggregates).
          </span>
        </div>
      </div>

      <!-- Date + quick range row -->
      <div class="flex flex-wrap items-center gap-3">
        <div class="flex items-center gap-2">
          <span class="font-semibold">Since:</span>
          <input
            v-model="since"
            type="date"
            class="px-2 py-1 border rounded text-[11px]"
          />
          <span class="font-semibold">Until:</span>
          <input
            v-model="until"
            type="date"
            class="px-2 py-1 border rounded text-[11px]"
          />
        </div>

        <!-- Quick time range chips -->
        <div class="flex flex-wrap items-center gap-1">
          <span class="text-[10px] text-gray-500 mr-1">
            Quick range:
          </span>
          <button
            v-for="mode in quickRangeModes"
            :key="mode.id"
            class="px-2 py-0.5 rounded-full border text-[10px] transition"
            :class="quickRangeMode === mode.id
              ? 'bg-indigo-600 text-white border-indigo-600'
              : 'bg-white text-gray-700 hover:bg-gray-50 border-gray-300'"
            @click="applyQuickRange(mode.id)"
          >
            {{ mode.label }}
          </button>
        </div>

        <span class="text-[10px] text-gray-500">
          Quick ranges set dates &amp; reload aggregates; manual edits still work.
        </span>
      </div>
    </div>

    <!-- Saved Views -->
    <div class="flex flex-col gap-2 text-[11px] text-gray-700 border rounded bg-gray-50/60 p-2">
      <div class="flex flex-wrap items-start gap-3">
        <span class="font-semibold text-gray-800 mt-1">Saved Views:</span>

        <!-- Create view block -->
        <div class="flex flex-col gap-1 w-full max-w-lg">
          <div class="flex items-center gap-2">
            <input
              v-model="newViewName"
              type="text"
              placeholder="e.g. Rosette Safe Last 30d"
              class="px-2 py-1 border rounded text-[11px] w-52"
            />
            <button
              class="px-2 py-1 rounded border text-[11px] text-gray-700 hover:bg-gray-100 disabled:opacity-50"
              :disabled="!canSaveCurrentView"
              @click="saveCurrentView"
            >
              Save current view
            </button>
          </div>
          <div class="flex flex-wrap items-center gap-2">
            <input
              v-model="newViewDescription"
              type="text"
              placeholder="Optional description (e.g. 'High-risk Adaptive night jobs')"
              class="px-2 py-1 border rounded text-[11px] flex-1 min-w-[220px]"
            />
          </div>
          <div class="flex flex-wrap items-center gap-2">
            <input
              v-model="newViewTags"
              type="text"
              placeholder="Tags (comma-separated: rosette, safe, q4, maple)"
              class="px-2 py-1 border rounded text-[11px] flex-1 min-w-[220px]"
            />
            <span class="text-[10px] text-gray-500">
              Tags help you remember intent (e.g., <span class="font-mono">rosette, safe, test</span>).
            </span>
          </div>
        </div>

        <!-- View list controls -->
        <div class="flex flex-col gap-1 ml-auto min-w-[260px]">
          <div class="flex items-center gap-2">
            <span class="text-[10px] text-gray-500">Sort views by:</span>
            <select
              v-model="viewSortMode"
              class="px-2 py-1 border rounded text-[10px]"
            >
              <option value="default">Default priority</option>
              <option value="name">Name</option>
              <option value="created">Created time</option>
              <option value="lastUsed">Last used</option>
            </select>
          </div>

          <div class="flex items-center gap-2">
            <span class="text-[10px] text-gray-500">Filter views:</span>
            <input
              v-model="viewSearch"
              type="text"
              placeholder="Search name/description/tags"
              class="px-2 py-1 border rounded text-[10px] flex-1"
            />
          </div>

          <div class="flex items-center gap-2">
            <span class="text-[10px] text-gray-500">Tag:</span>
            <select
              v-model="viewTagFilter"
              class="px-2 py-1 border rounded text-[10px] flex-1"
            >
              <option value="">All tags</option>
              <option
                v-for="tag in allViewTags"
                :key="tag"
                :value="tag"
              >
                {{ tag }}
              </option>
            </select>
          </div>

          <div class="flex items-center gap-2">
            <input
              ref="importInputRef"
              type="file"
              accept="application/json"
              class="hidden"
              @change="handleImportFile"
            />
            <button
              class="px-2 py-1 rounded border text-[11px] text-gray-700 hover:bg-gray-100"
              @click="triggerImport"
            >
              Import views
            </button>
            <button
              class="px-2 py-1 rounded border text-[11px] text-gray-700 hover:bg-gray-100 disabled:opacity-50"
              :disabled="!savedViews.length"
              @click="exportViews"
            >
              Export views
            </button>
          </div>
        </div>
      </div>

      <!-- Recently used strip -->
      <div v-if="recentViews.length" class="flex flex-wrap items-center gap-2 mt-1">
        <span class="text-[10px] text-gray-500">
          Recently used:
        </span>
        <button
          v-for="view in recentViews"
          :key="view.id"
          class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border bg-white text-[10px] text-gray-800 hover:bg-gray-100"
          @click="applySavedView(view)"
          :title="viewTooltip(view)"
        >
          <span class="font-mono truncate max-w-[160px]">
            {{ view.name }}
          </span>
          <span class="text-[9px] text-gray-500">
            ({{ formatRelativeMetaTime(view.lastUsedAt || view.createdAt) }})
          </span>
        </button>
      </div>

      <!-- Saved views status line -->
      <div class="flex flex-wrap items-center gap-2 mt-1">
        <span v-if="saveError" class="text-[10px] text-rose-600">
          {{ saveError }}
        </span>
        <span v-else-if="saveHint" class="text-[10px] text-gray-500">
          {{ saveHint }}
        </span>
        <span v-else class="text-[10px] text-gray-500">
          Default view:
          <span class="font-mono">{{ defaultViewLabel }}</span>
          <span v-if="viewSearch || viewTagFilter" class="ml-2">
            · Filtered showing
            <span class="font-mono">{{ sortedViews.length }}</span>
            of
            <span class="font-mono">{{ savedViews.length }}</span>
            saved views
          </span>
        </span>
      </div>

      <!-- Saved views chips + metadata -->
      <div v-if="sortedViews.length" class="flex flex-col gap-1">
        <div class="text-[10px] text-gray-500">
          Click name to apply · ✏ rename · ⧉ duplicate · ⭐ set default · 🗑 remove · hover for filters, description &amp; tags
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <div
            v-for="view in sortedViews"
            :key="view.id"
            class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border bg-white shadow-sm"
          >
            <button
              class="text-[10px] text-gray-800 font-medium hover:underline"
              @click="applySavedView(view)"
              :title="viewTooltip(view)"
            >
              {{ view.name }}
            </button>
            <span
              v-if="view.tags && view.tags.length"
              class="inline-flex items-center gap-0.5 ml-1"
            >
              <span
                v-for="tag in view.tags"
                :key="view.id + ':' + tag"
                class="px-1 rounded-full bg-sky-50 border border-sky-100 text-[9px] text-sky-700 cursor-pointer"
                @click.stop="toggleTagFilter(tag)"
                :title="`Filter by tag '${tag}'`"
              >
                {{ tag }}
              </span>
            </span>
            <button
              class="text-[10px] text-gray-500 hover:text-gray-700"
              title="Rename view"
              @click="renameView(view.id)"
            >
              ✏
            </button>
            <button
              class="text-[10px] text-gray-500 hover:text-gray-700"
              title="Duplicate view"
              @click="duplicateView(view.id)"
            >
              ⧉
            </button>
            <button
              class="text-[10px]"
              :class="view.isDefault ? 'text-amber-500' : 'text-gray-400 hover:text-amber-500'"
              @click="setDefaultView(view.id)"
              :title="view.isDefault ? 'Default view' : 'Set as default view'"
            >
              ⭐
            </button>
            <button
              class="text-[10px] text-gray-500 hover:text-rose-600"
              @click="deleteSavedView(view.id)"
              title="Delete this view"
            >
              🗑
            </button>
          </div>
        </div>

        <div class="text-[10px] text-gray-500 mt-1 max-w-full space-y-0.5">
          <div
            v-for="view in sortedViews"
            :key="view.id + 'meta'"
            class="flex flex-wrap items-center gap-2"
          >
            <span class="font-mono text-[10px]">
              {{ view.name }}
            </span>
            <span v-if="view.isDefault" class="text-amber-600 text-[10px]">
              (default)
            </span>
            <span
              v-if="view.description"
              class="text-gray-600 text-[10px]"
            >
              — {{ view.description }}
            </span>
            <span class="text-gray-500 text-[10px]">
              created: {{ formatMetaTime(view.createdAt) }}
            </span>
            <span class="text-gray-500 text-[10px]">
              last used: {{ formatMetaTime(view.lastUsedAt || view.createdAt) }}
            </span>
          </div>
        </div>
      </div>

      <div v-else class="text-[10px] text-gray-500 italic">
        No saved views match the current view filters.
        <span v-if="savedViews.length">
          Try clearing search or tag filter.
        </span>
        <span v-else>
          Create your first view above.
        </span>
      </div>
    </div>

    <!-- Summary chips -->
    <div v-if="filteredBuckets.length" class="text-[11px] text-gray-700 flex flex-wrap gap-3">
      <span>
        Buckets: <span class="font-mono">{{ filteredBuckets.length }}</span>
      </span>
      <span>
        Entries (sum of bucket counts): <span class="font-mono">{{ filteredEntriesCount }}</span>
      </span>
      <span v-if="since || until" class="text-[10px] text-gray-500">
        Window:
        <span v-if="since">from <span class="font-mono">{{ since }}</span></span>
        <span v-if="since && until"> to </span>
        <span v-if="until"> <span class="font-mono">{{ until }}</span> </span>
      </span>
      <span v-if="quickRangeMode" class="text-[10px] text-indigo-600">
        Quick range: <span class="font-mono">{{ currentQuickRangeLabel }}</span>
      </span>
    </div>

    <div v-else class="text-[11px] text-gray-500 italic">
      No buckets match the current filters (or time window).
    </div>

    <!-- Buckets table -->
    <div v-if="filteredBuckets.length" class="overflow-x-auto">
      <table class="min-w-full text-[11px] text-left">
        <thead class="border-b bg-gray-50">
          <tr>
            <th class="px-2 py-1 whitespace-nowrap">Lane</th>
            <th class="px-2 py-1 whitespace-nowrap">Preset</th>
            <th class="px-2 py-1 whitespace-nowrap text-right">Entries</th>
            <th class="px-2 py-1 whitespace-nowrap text-right">Avg +Added</th>
            <th class="px-2 py-1 whitespace-nowrap text-right">Avg -Removed</th>
            <th class="px-2 py-1 whitespace-nowrap text-right">Avg =Unchanged</th>
            <th class="px-2 py-1 whitespace-nowrap">Risk</th>
            <th class="px-2 py-1 whitespace-nowrap">Trend (Added)</th>
            <th class="px-2 py-1 whitespace-nowrap">Trend (Removed)</th>
            <th class="px-2 py-1 whitespace-nowrap">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="bucket in filteredBuckets"
            :key="bucket.key"
            class="border-b last:border-0 hover:bg-gray-50"
          >
            <td
              class="px-2 py-1 whitespace-nowrap cursor-pointer"
              @click="goToLab(bucket)"
              :title="`Open ${bucket.lane} lab for preset '${bucket.preset}'`"
            >
              {{ bucket.lane }}
            </td>
            <td
              class="px-2 py-1 whitespace-nowrap cursor-pointer"
              @click="goToLab(bucket)"
              :title="`Open ${bucket.lane} lab for preset '${bucket.preset}'`"
            >
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
              <svg :width="sparkWidth" :height="sparkHeight" viewBox="0 0 60 20">
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
              <svg :width="sparkWidth" :height="sparkHeight" viewBox="0 0 60 20">
                <polyline
                  v-if="bucket.removedPath"
                  :points="bucket.removedPath"
                  fill="none"
                  stroke="#ef4444"
                  stroke-width="1.2"
                />
              </svg>
            </td>
            <td class="px-2 py-1 whitespace-nowrap">
              <button
                class="px-2 py-0.5 rounded border text-[10px] text-gray-700 hover:bg-gray-100"
                @click="loadBucketDetails(bucket)"
              >
                Details
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Bucket details panel -->
    <div
      v-if="selectedBucket"
      class="mt-3 border rounded bg-white shadow-sm p-3 flex flex-col gap-2 text-[11px]"
    >
      <div class="flex items-center justify-between gap-2">
        <div>
          <div class="font-semibold text-gray-900">
            Bucket Details – {{ selectedBucket.lane }} / {{ selectedBucket.preset }}
          </div>
          <div class="text-[10px] text-gray-600">
            Showing underlying compare snapshots for this lane + preset.
            <span v-if="jobFilter">
              Filtered by job hint: <span class="font-mono">{{ jobFilter }}</span>
            </span>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <button
            class="px-2 py-0.5 rounded border text-[10px] text-gray-700 hover:bg-gray-100 disabled:opacity-50"
            :disabled="!bucketEntries.length"
            @click="exportBucketCsv"
          >
            Export entries CSV
          </button>
          <button
            class="px-2 py-0.5 rounded border text-[10px] text-gray-700 hover:bg-gray-100"
            @click="downloadBucketJson"
          >
            Download JSON report
          </button>
          <button
            class="px-2 py-0.5 rounded border text-[10px] text-gray-700 hover:bg-gray-100"
            @click="clearBucketDetails"
          >
            Close
          </button>
        </div>
      </div>

      <div v-if="bucketEntriesLoading" class="text-[10px] text-gray-500 italic">
        Loading bucket entries…
      </div>
      <div v-else-if="bucketEntriesError" class="text-[10px] text-rose-600">
        {{ bucketEntriesError }}
      </div>
      <div v-else-if="!bucketEntries.length" class="text-[10px] text-gray-500 italic">
        No entries found for this bucket (with current job hint).
      </div>
      <div v-else class="overflow-x-auto max-h-64 border-t pt-2">
        <table class="min-w-full text-[10px] text-left">
          <thead class="">
            <tr class="border-b bg-gray-50">
              <th class="px-2 py-1 whitespace-nowrap">Time</th>
              <th class="px-2 py-1 whitespace-nowrap">Job ID</th>
              <th class="px-2 py-1 whitespace-nowrap text-right">Baseline</th>
              <th class="px-2 py-1 whitespace-nowrap text-right">Current</th>
              <th class="px-2 py-1 whitespace-nowrap text-right">+Added</th>
              <th class="px-2 py-1 whitespace-nowrap text-right">-Removed</th>
              <th class="px-2 py-1 whitespace-nowrap text-right">=Unchanged</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="entry in bucketEntries"
              :key="entry.ts + '::' + (entry.job_id || '') + '::' + entry.baseline_id"
              class="border-b last:border-0"
            >
              <td class="px-2 py-1 whitespace-nowrap">
                {{ formatTime(entry.ts) }}
              </td>
              <td class="px-2 py-1 whitespace-nowrap font-mono">
                {{ entry.job_id || '—' }}
              </td>
              <td class="px-2 py-1 text-right font-mono">
                {{ entry.baseline_path_count }}
              </td>
              <td class="px-2 py-1 text-right font-mono">
                {{ entry.current_path_count }}
              </td>
              <td class="px-2 py-1 text-right text-emerald-700 font-mono">
                {{ entry.added_paths }}
              </td>
              <td class="px-2 py-1 text-right text-rose-700 font-mono">
                {{ entry.removed_paths }}
              </td>
              <td class="px-2 py-1 text-right font-mono">
                {{ entry.unchanged_paths }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import axios from "axios";
import { useRouter, useRoute } from "vue-router";

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
  addedSeries: number[];
  removedSeries: number[];
  addedPath: string;
  removedPath: string;
}

interface BucketEntry {
  ts: string;
  job_id: string | null;
  lane: string;
  preset: string | null;
  baseline_id: string;
  baseline_path_count: number;
  current_path_count: number;
  added_paths: number;
  removed_paths: number;
  unchanged_paths: number;
}

interface SavedView {
  id: string;
  name: string;
  lane: string;
  preset: string;
  jobHint: string;
  since: string;
  until: string;
  description?: string;
  tags?: string[];
  createdAt: string;
  lastUsedAt?: string | null;
  isDefault?: boolean;
}

type ViewSortMode = "default" | "name" | "created" | "lastUsed";
type QuickRangeMode = "" | "all" | "last7" | "last30" | "last90" | "year";

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

// saved views
const savedViews = ref<SavedView[]>([]);
const newViewName = ref<string>("");
const newViewDescription = ref<string>("");
const newViewTags = ref<string>("");
const saveError = ref<string | null>(null);
const saveHint = ref<string>("");

// view filters
const viewSearch = ref<string>("");
const viewTagFilter = ref<string>("");

// sort mode for views
const viewSortMode = ref<ViewSortMode>("default");

// file input ref for import
const importInputRef = ref<HTMLInputElement | null>(null);

// localStorage key
const STORAGE_KEY = "ltb_crosslab_risk_views";

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

// can save current view?
const canSaveCurrentView = computed(() => {
  return !!newViewName.value.trim();
});

// default view label
const defaultViewLabel = computed(() => {
  const d = savedViews.value.find((v) => v.isDefault);
  return d ? d.name : "none";
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

// saved views helpers
function loadSavedViews() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      savedViews.value = [];
      return;
    }
    const parsed = JSON.parse(raw);
    if (Array.isArray(parsed)) {
      savedViews.value = parsed
        .filter((v: any) => v && typeof v === "object")
        .map((v: any) => ({
          ...v,
          isDefault: !!v.isDefault,
          lastUsedAt: v.lastUsedAt || null,
          description: v.description || "",
          tags: Array.isArray(v.tags)
            ? v.tags.map((t: any) => String(t)).filter((t: string) => t.trim().length > 0)
            : [],
        }));
    } else {
      savedViews.value = [];
    }
  } catch (err) {
    console.error("Failed to load saved views", err);
    savedViews.value = [];
  }
}

function persistSavedViews() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(savedViews.value));
  } catch (err) {
    console.error("Failed to persist saved views", err);
  }
}

function makeViewId(): string {
  return `view_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

function nowIso(): string {
  return new Date().toISOString();
}

function parseTags(input: string): string[] {
  if (!input.trim()) return [];
  return input
    .split(",")
    .map((s) => s.trim())
    .filter((s) => s.length > 0);
}

function saveCurrentView() {
  saveError.value = null;
  saveHint.value = "";
  const name = newViewName.value.trim();
  if (!name) {
    saveError.value = "Name is required.";
    return;
  }

  const existing = savedViews.value.find(
    (v) => v.name.toLowerCase() === name.toLowerCase()
  );
  if (existing) {
    saveError.value = "A view with this name already exists.";
    return;
  }

  const now = nowIso();

  const view: SavedView = {
    id: makeViewId(),
    name,
    lane: laneFilter.value || "",
    preset: presetFilter.value || "",
    jobHint: jobFilter.value || "",
    since: since.value || "",
    until: until.value || "",
    description: newViewDescription.value.trim() || "",
    tags: parseTags(newViewTags.value),
    createdAt: now,
    lastUsedAt: null,
    isDefault: savedViews.value.length === 0,
  };

  savedViews.value = [...savedViews.value, view];
  persistSavedViews();
  newViewName.value = "";
  newViewDescription.value = "";
  newViewTags.value = "";
  saveHint.value = "View saved.";
}

function applySavedView(view: SavedView) {
  laneFilter.value = view.lane || "";
  presetFilter.value = view.preset || "";
  jobFilter.value = view.jobHint || "";
  since.value = view.since || "";
  until.value = view.until || "";

  // when a view is applied, we consider the range "custom" unless both dates are empty
  quickRangeMode.value = !since.value && !until.value ? "all" : "";

  const now = nowIso();
  savedViews.value = savedViews.value.map((v) =>
    v.id === view.id ? { ...v, lastUsedAt: now } : v
  );
  persistSavedViews();

  syncFiltersToQuery();
  clearBucketDetails();
  refresh();
}

function renameView(id: string) {
  const view = savedViews.value.find((v) => v.id === id);
  if (!view) return;
  const currentName = view.name;
  const newName = window.prompt("Rename view:", currentName);
  if (newName === null) return;
  const trimmed = newName.trim();
  if (!trimmed) {
    saveError.value = "Name cannot be empty.";
    return;
  }

  const exists = savedViews.value.find(
    (v) =>
      v.id !== id && v.name.toLowerCase() === trimmed.toLowerCase()
  );
  if (exists) {
    saveError.value = "Another view already uses that name.";
    return;
  }

  savedViews.value = savedViews.value.map((v) =>
    v.id === id ? { ...v, name: trimmed } : v
  );
  persistSavedViews();
  saveHint.value = "View renamed.";
  saveError.value = null;
}

function duplicateView(id: string) {
  const original = savedViews.value.find((v) => v.id === id);
  if (!original) return;

  const now = nowIso();
  const baseName = `${original.name} copy`;
  let candidate = baseName;
  let counter = 2;
  while (
    savedViews.value.some(
      (v) => v.name.toLowerCase() === candidate.toLowerCase()
    )
  ) {
    candidate = `${baseName} ${counter}`;
    counter += 1;
  }

  const clone: SavedView = {
    ...original,
    id: makeViewId(),
    name: candidate,
    createdAt: now,
    lastUsedAt: null,
    isDefault: false,
  };

  savedViews.value = [...savedViews.value, clone];
  persistSavedViews();
  saveHint.value = "View duplicated.";
  saveError.value = null;
}

function deleteSavedView(id: string) {
  const wasDefault = savedViews.value.find((v) => v.id === id)?.isDefault;
  savedViews.value = savedViews.value.filter((v) => v.id !== id);

  if (wasDefault && savedViews.value.length > 0) {
    savedViews.value = savedViews.value.map((v) => ({ ...v, isDefault: false }));
  }

  persistSavedViews();
}

function setDefaultView(id: string) {
  let found = false;
  savedViews.value = savedViews.value.map((v) => {
    if (v.id === id) {
      found = true;
      return { ...v, isDefault: true };
    }
    return { ...v, isDefault: false };
  });
  if (found) {
    persistSavedViews();
    saveHint.value = "Default view updated.";
    saveError.value = null;
  }
}

function viewTooltip(view: SavedView): string {
  const parts: string[] = [];
  if (view.lane) parts.push(`lane=${view.lane}`);
  if (view.preset) parts.push(`preset=${view.preset}`);
  if (view.jobHint) parts.push(`job_hint=${view.jobHint}`);
  if (view.since) parts.push(`since=${view.since}`);
  if (view.until) parts.push(`until=${view.until}`);
  if (view.description) parts.push(`desc=${view.description}`);
  if (view.tags && view.tags.length) {
    parts.push(`tags=${view.tags.join(", ")}`);
  }
  return parts.length ? parts.join(" · ") : "No filters";
}

const allViewTags = computed<string[]>(() => {
  const set = new Set<string>();
  for (const v of savedViews.value) {
    if (Array.isArray(v.tags)) {
      for (const tag of v.tags) {
        const t = tag.trim();
        if (t) set.add(t);
      }
    }
  }
  return Array.from(set).sort((a, b) => a.localeCompare(b));
});

function viewMatchesFilter(view: SavedView): boolean {
  const s = viewSearch.value.trim().toLowerCase();
  const tagFilter = viewTagFilter.value.trim();

  if (tagFilter) {
    const tags = view.tags || [];
    if (!tags.some((t) => t === tagFilter)) {
      return false;
    }
  }

  if (!s) return true;

  const haystackParts: string[] = [];
  haystackParts.push(view.name || "");
  if (view.description) haystackParts.push(view.description);
  if (view.tags && view.tags.length) haystackParts.push(view.tags.join(" "));

  const haystack = haystackParts.join(" ").toLowerCase();
  return haystack.includes(s);
}

const sortedViews = computed<SavedView[]>(() => {
  const base = savedViews.value.filter(viewMatchesFilter);
  const arr = [...base];

  function parseTime(t?: string | null): number {
    if (!t) return 0;
    const d = Date.parse(t);
    return isNaN(d) ? 0 : d;
  }

  if (viewSortMode.value === "name") {
    return arr.sort((a, b) =>
      a.name.toLowerCase().localeCompare(b.name.toLowerCase())
    );
  }

  if (viewSortMode.value === "created") {
    return arr.sort((a, b) => parseTime(b.createdAt) - parseTime(a.createdAt));
  }

  if (viewSortMode.value === "lastUsed") {
    return arr.sort((a, b) => {
      const at = parseTime(a.lastUsedAt || a.createdAt);
      const bt = parseTime(b.lastUsedAt || b.createdAt);
      return bt - at;
    });
  }

  return arr.sort((a, b) => {
    if (a.isDefault && !b.isDefault) return -1;
    if (!a.isDefault && b.isDefault) return 1;

    const at = parseTime(a.lastUsedAt || a.createdAt);
    const bt = parseTime(b.lastUsedAt || b.createdAt);
    if (bt !== at) return bt - at;

    return a.name.toLowerCase().localeCompare(b.name.toLowerCase());
  });
});

// recent views (top 5 by lastUsedAt, fallback to createdAt)
const recentViews = computed<SavedView[]>(() => {
  function parseTime(t?: string | null): number {
    if (!t) return 0;
    const d = Date.parse(t);
    return isNaN(d) ? 0 : d;
  }
  const withTime = savedViews.value
    .map((v) => ({
      view: v,
      t: parseTime(v.lastUsedAt || v.createdAt),
    }))
    .filter((x) => x.t > 0);
  withTime.sort((a, b) => b.t - a.t);
  return withTime.slice(0, 5).map((x) => x.view);
});

// import/export views
function triggerImport() {
  if (importInputRef.value) {
    importInputRef.value.value = "";
    importInputRef.value.click();
  }
}

function handleImportFile(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files && input.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = () => {
    try {
      const text = String(reader.result || "");
      const data = JSON.parse(text);
      if (!Array.isArray(data)) {
        saveError.value = "Invalid views file (expected an array).";
        return;
      }

      const incoming: SavedView[] = data
        .filter((v: any) => v && typeof v === "object")
        .map((v: any) => ({
          id: v.id || makeViewId(),
          name: String(v.name || "Unnamed view"),
          lane: v.lane || "",
          preset: v.preset || "",
          jobHint: v.jobHint || "",
          since: v.since || "",
          until: v.until || "",
          description: v.description || "",
          tags: Array.isArray(v.tags)
            ? v.tags.map((t: any) => String(t)).filter((t: string) => t.trim().length > 0)
            : [],
          createdAt: v.createdAt || nowIso(),
          lastUsedAt: v.lastUsedAt || null,
          isDefault: !!v.isDefault,
        }));

      const byName = new Map<string, SavedView>();
      for (const v of savedViews.value) {
        byName.set(v.name.toLowerCase(), v);
      }
      for (const v of incoming) {
        byName.set(v.name.toLowerCase(), v);
      }

      const merged = Array.from(byName.values());

      let defaultSeen = false;
      const normalized = merged.map((v) => {
        if (v.isDefault) {
          if (defaultSeen) {
            return { ...v, isDefault: false };
          }
          defaultSeen = true;
          return v;
        }
        return v;
      });

      savedViews.value = normalized;
      persistSavedViews();
      saveError.value = null;
      saveHint.value = "Views imported.";
    } catch (err) {
      console.error("Failed to import views", err);
      saveError.value = "Failed to import views.";
    }
  };
  reader.readAsText(file);
}

function exportViews() {
  if (!savedViews.value.length) return;
  try {
    const blob = new Blob([JSON.stringify(savedViews.value, null, 2)], {
      type: "application/json",
    });
    const stamp = new Date().toISOString().replace(/[:.]/g, "-");
    const filename = `crosslab_risk_views_${stamp}.json`;
    const url = URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  } catch (err) {
    console.error("Failed to export views", err);
    saveError.value = "Failed to export views.";
  }
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

function riskChipClass(score: number): string {
  if (score < 1) return "bg-emerald-50 text-emerald-700 border border-emerald-200";
  if (score < 3) return "bg-amber-50 text-amber-700 border border-amber-200";
  if (score < 6) return "bg-orange-50 text-orange-700 border border-orange-200";
  return "bg-rose-50 text-rose-700 border border-rose-200";
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
      "/api/compare/risk_bucket_entries",
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

function formatTime(ts: string): string {
  try {
    const d = new Date(ts);
    return d.toLocaleString();
  } catch {
    return ts;
  }
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

function exportBucketCsv() {
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

  const def = savedViews.value.find((v) => v.isDefault);
  if (!def) {
    // if no default view, default quick range is "all"
    quickRangeMode.value = "all";
    return;
  }
  applySavedView(def);
}

onMounted(() => {
  loadSavedViews();
  applyQueryToFilters();
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
</script>

That’s the complete Phase 28.16 bundle.
