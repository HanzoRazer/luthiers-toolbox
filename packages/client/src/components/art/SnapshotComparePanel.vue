<template>
  <div class="flex flex-col gap-4 p-4">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <h3 class="text-sm font-semibold text-gray-800">Snapshot Compare</h3>
      <button
        class="text-xs text-gray-500 hover:text-gray-700"
        @click="$emit('close')"
      >
        Close
      </button>
    </div>

    <!-- Snapshot Selectors -->
    <div class="grid grid-cols-2 gap-4">
      <!-- Left: Baseline -->
      <div class="flex flex-col gap-2">
        <label class="text-xs font-medium text-gray-600">Baseline Snapshot</label>
        <div
          v-if="baselineSnapshot"
          class="border rounded p-2 bg-emerald-50 border-emerald-200"
        >
          <div class="text-sm font-medium text-emerald-800">
            {{ baselineSnapshot.metadata?.name || baselineSnapshot.snapshot_id }}
          </div>
          <div class="text-xs text-emerald-600">
            {{ formatDate(baselineSnapshot.created_at_utc) }}
          </div>
          <div v-if="baselineSnapshot.metadata?.notes" class="text-xs text-gray-600 mt-1 italic">
            {{ truncate(baselineSnapshot.metadata.notes, 80) }}
          </div>
        </div>
        <div v-else class="border rounded p-2 bg-gray-50 text-xs text-gray-500">
          No baseline set. Mark a snapshot as baseline to compare.
        </div>
      </div>

      <!-- Right: Compare Target -->
      <div class="flex flex-col gap-2">
        <label class="text-xs font-medium text-gray-600">Compare With</label>
        <select
          v-model="compareSnapshotId"
          class="border rounded px-2 py-1 text-xs"
          :disabled="!baselineSnapshot"
        >
          <option :value="null">-- select snapshot --</option>
          <option
            v-for="snap in availableSnapshots"
            :key="snap.snapshot_id"
            :value="snap.snapshot_id"
          >
            {{ snap.metadata?.name || snap.snapshot_id }}
          </option>
        </select>
        <div
          v-if="compareSnapshot"
          class="border rounded p-2 bg-blue-50 border-blue-200"
        >
          <div class="text-sm font-medium text-blue-800">
            {{ compareSnapshot.metadata?.name || compareSnapshot.snapshot_id }}
          </div>
          <div class="text-xs text-blue-600">
            {{ formatDate(compareSnapshot.created_at_utc) }}
          </div>
          <div v-if="compareSnapshot.metadata?.notes" class="text-xs text-gray-600 mt-1 italic">
            {{ truncate(compareSnapshot.metadata.notes, 80) }}
          </div>
        </div>
      </div>
    </div>

    <!-- Diff Display -->
    <div v-if="baselineSnapshot && compareSnapshot" class="border rounded bg-white">
      <div class="border-b px-3 py-2 bg-gray-50 text-xs font-medium text-gray-700">
        Parameter Differences
      </div>
      <div class="p-3 text-xs font-mono max-h-64 overflow-y-auto">
        <div v-if="paramDiffs.length === 0" class="text-gray-500 italic">
          No differences detected.
        </div>
        <div
          v-for="diff in paramDiffs"
          :key="diff.path"
          class="flex gap-2 py-1 border-b border-gray-100 last:border-0"
        >
          <span class="text-gray-600 w-1/3 truncate" :title="diff.path">
            {{ diff.path }}
          </span>
          <span class="text-rose-600 w-1/3 truncate" :title="String(diff.baseline)">
            {{ formatValue(diff.baseline) }}
          </span>
          <span class="text-emerald-600 w-1/3 truncate" :title="String(diff.compare)">
            {{ formatValue(diff.compare) }}
          </span>
        </div>
      </div>
    </div>

    <!-- Feasibility Comparison -->
    <div v-if="baselineSnapshot && compareSnapshot" class="border rounded bg-white">
      <div class="border-b px-3 py-2 bg-gray-50 text-xs font-medium text-gray-700">
        Feasibility Comparison
      </div>
      <div class="grid grid-cols-2 gap-4 p-3">
        <!-- Baseline Feasibility -->
        <div class="flex flex-col gap-1">
          <div class="text-xs font-medium text-gray-600">Baseline</div>
          <FeasibilityBadge
            v-if="baselineSnapshot.feasibility"
            :feasibility="baselineSnapshot.feasibility"
          />
          <span v-else class="text-xs text-gray-400">No feasibility data</span>
        </div>
        <!-- Compare Feasibility -->
        <div class="flex flex-col gap-1">
          <div class="text-xs font-medium text-gray-600">Compare</div>
          <FeasibilityBadge
            v-if="compareSnapshot.feasibility"
            :feasibility="compareSnapshot.feasibility"
          />
          <span v-else class="text-xs text-gray-400">No feasibility data</span>
        </div>
      </div>
    </div>

    <!-- Actions -->
    <div v-if="baselineSnapshot && compareSnapshot" class="flex gap-2">
      <button
        class="px-3 py-1 text-xs rounded bg-blue-600 text-white hover:bg-blue-700"
        @click="applyCompareSnapshot"
      >
        Apply Compare Snapshot
      </button>
      <button
        class="px-3 py-1 text-xs rounded bg-emerald-600 text-white hover:bg-emerald-700"
        @click="applyBaselineSnapshot"
      >
        Apply Baseline
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { artSnapshotsClient } from "@/api/artSnapshotsClient";
import type { DesignSnapshot } from "@/types/designSnapshot";

// Placeholder for FeasibilityBadge - can be a simple inline display
const FeasibilityBadge = {
  props: ["feasibility"],
  template: `
    <div class="flex items-center gap-1">
      <span
        class="inline-block w-2 h-2 rounded-full"
        :class="{
          'bg-emerald-500': feasibility?.verdict === 'go',
          'bg-amber-500': feasibility?.verdict === 'caution',
          'bg-rose-500': feasibility?.verdict === 'no_go',
          'bg-gray-400': !feasibility?.verdict
        }"
      ></span>
      <span class="text-xs">{{ feasibility?.verdict || 'unknown' }}</span>
      <span v-if="feasibility?.score" class="text-xs text-gray-500">
        ({{ Math.round(feasibility.score * 100) }}%)
      </span>
    </div>
  `,
};

interface RosetteSnapshot {
  snapshot_id: string;
  design_fingerprint: string;
  created_at_utc: string;
  design: Record<string, any>;
  feasibility?: {
    verdict?: string;
    score?: number;
    issues?: string[];
  } | null;
  metadata?: {
    name?: string | null;
    description?: string | null;
    notes?: string | null;
    tags?: string[];
  };
  baseline?: boolean;
}

const emit = defineEmits<{
  (e: "close"): void;
  (e: "apply", snapshot: RosetteSnapshot): void;
}>();

const baselineSnapshot = ref<RosetteSnapshot | null>(null);
const compareSnapshotId = ref<string | null>(null);
const compareSnapshot = ref<RosetteSnapshot | null>(null);
const allSnapshots = ref<RosetteSnapshot[]>([]);

const availableSnapshots = computed(() =>
  allSnapshots.value.filter(
    (s) => s.snapshot_id !== baselineSnapshot.value?.snapshot_id
  )
);

interface ParamDiff {
  path: string;
  baseline: any;
  compare: any;
}

const paramDiffs = computed<ParamDiff[]>(() => {
  if (!baselineSnapshot.value || !compareSnapshot.value) return [];

  const baseDesign = baselineSnapshot.value.design || {};
  const compDesign = compareSnapshot.value.design || {};

  const diffs: ParamDiff[] = [];
  const allKeys = new Set([
    ...Object.keys(baseDesign),
    ...Object.keys(compDesign),
  ]);

  for (const key of allKeys) {
    const baseVal = baseDesign[key];
    const compVal = compDesign[key];

    if (JSON.stringify(baseVal) !== JSON.stringify(compVal)) {
      diffs.push({
        path: key,
        baseline: baseVal,
        compare: compVal,
      });
    }
  }

  return diffs;
});

function formatDate(dt: string | undefined): string {
  if (!dt) return "";
  try {
    return new Date(dt).toLocaleString();
  } catch {
    return dt;
  }
}

function truncate(s: string | undefined | null, max: number): string {
  if (!s) return "";
  if (s.length <= max) return s;
  return s.slice(0, max) + "...";
}

function formatValue(v: any): string {
  if (v === undefined) return "(undefined)";
  if (v === null) return "(null)";
  if (typeof v === "object") {
    try {
      return JSON.stringify(v);
    } catch {
      return "[object]";
    }
  }
  return String(v);
}

async function loadSnapshots() {
  try {
    // Load all snapshots
    const res = await fetch("/api/art-studio/rosette/snapshots/?limit=100");
    if (res.ok) {
      const data = await res.json();
      allSnapshots.value = data.snapshots || [];
    }
  } catch (err) {
    console.error("Failed to load snapshots", err);
  }
}

async function loadBaseline() {
  try {
    const res = await fetch("/api/art-studio/rosette/snapshots/baseline");
    if (res.ok) {
      baselineSnapshot.value = await res.json();
    } else if (res.status === 404) {
      baselineSnapshot.value = null;
    }
  } catch (err) {
    console.error("Failed to load baseline", err);
  }
}

async function loadCompareSnapshot(id: string) {
  try {
    const res = await fetch(`/api/art-studio/rosette/snapshots/${encodeURIComponent(id)}`);
    if (res.ok) {
      compareSnapshot.value = await res.json();
    }
  } catch (err) {
    console.error("Failed to load compare snapshot", err);
  }
}

function applyCompareSnapshot() {
  if (compareSnapshot.value) {
    emit("apply", compareSnapshot.value);
  }
}

function applyBaselineSnapshot() {
  if (baselineSnapshot.value) {
    emit("apply", baselineSnapshot.value);
  }
}

watch(compareSnapshotId, (id) => {
  if (id) {
    loadCompareSnapshot(id);
  } else {
    compareSnapshot.value = null;
  }
});

onMounted(() => {
  loadSnapshots();
  loadBaseline();
});
</script>
