<script setup lang="ts">
import { computed, ref, watch, onMounted, onBeforeUnmount } from "vue";
import { useRosetteStore } from "@/stores/rosetteStore";
import { useToastStore } from "@/stores/toastStore";
import { artSnapshotsClient } from "@/api/artSnapshotsClient";
import {
  computeConfidence,
  computeConfidenceTrend,
  getConfidenceTooltipText,
  type ConfLevel,
} from "@/utils/rmosConfidence";
import CompareOpenPanel from "./snapshot_compare/CompareOpenPanel.vue";

type AnySnap = any;

const store = useRosetteStore();
const toast = useToastStore();

const leftId = ref<string>("");
const rightId = ref<string>("");

const loading = ref(false);
const error = ref<string>("");

// Collapsed by default (32.1.0a)
const isOpen = ref(false);

// Auto-compare guard (32.1.0c)
const autoComparedOnce = ref(false);

// 32.1.0d: Live compare toggle (default OFF)
const liveCompare = ref(false);
let liveTimer: number | null = null;

// Bundle 03: Keyboard hints toggle with localStorage persistence
const KEYBOARD_HINTS_KEY = "compare.showKeyboardHints";
const showKeyboardHints = ref(true);

function scheduleLiveCompare() {
  if (!liveCompare.value) return;
  if (!isOpen.value) return;
  if (!leftId.value || !rightId.value) return;
  if (leftId.value === rightId.value) return;

  if (liveTimer) window.clearTimeout(liveTimer);
  liveTimer = window.setTimeout(() => {
    void loadSnapshotsForCompare();
  }, 200);
}

const left = ref<AnySnap | null>(null);
const right = ref<AnySnap | null>(null);

const canCompare = computed(() => !!leftId.value && !!rightId.value && leftId.value !== rightId.value);

function ringRows(snapshot: AnySnap | null) {
  const rings = snapshot?.spec?.ring_params || snapshot?.spec?.ringParams || [];
  return (rings || []).map((r: any, idx: number) => ({
    idx,
    width_mm: Number(r.width_mm ?? r.widthMm ?? 0),
    pattern: String(r.pattern_key ?? r.patternKey ?? r.pattern_type ?? r.patternType ?? ""),
  }));
}

const deltaRows = computed(() => {
  const a = ringRows(left.value);
  const b = ringRows(right.value);
  const n = Math.max(a.length, b.length);

  const rows: { ring: number; aWidth: number; bWidth: number; delta: number; aPattern: string; bPattern: string }[] = [];
  for (let i = 0; i < n; i++) {
    const aw = a[i]?.width_mm ?? 0;
    const bw = b[i]?.width_mm ?? 0;
    rows.push({
      ring: i + 1,
      aWidth: aw,
      bWidth: bw,
      delta: bw - aw,
      aPattern: a[i]?.pattern ?? "",
      bPattern: b[i]?.pattern ?? "",
    });
  }
  return rows;
});

const scoreDelta = computed(() => {
  const a = left.value?.feasibility?.overall_score ?? left.value?.feasibility?.overallScore ?? null;
  const b = right.value?.feasibility?.overall_score ?? right.value?.feasibility?.overallScore ?? null;
  if (a == null || b == null) return null;
  return Number(b) - Number(a);
});

const warningDelta = computed(() => {
  const a = left.value?.feasibility?.warnings?.length ?? 0;
  const b = right.value?.feasibility?.warnings?.length ?? 0;
  return b - a;
});

// Bundle 08: Use centralized confidence heuristic from rmosConfidence util
const confidenceLevel = computed<ConfLevel>(() => {
  // No compare result yet → safe default
  if (!left.value || !right.value) return "LOW";

  // Count "hot" rings (|Δ| >= 0.15mm)
  const hotRings = deltaRows.value.filter((r) => Math.abs(r.delta) >= 0.15).length;

  // Pattern changes count as structural
  const patternChanges = deltaRows.value.filter(
    (r) => r.aPattern !== r.bPattern && (r.aPattern || r.bPattern)
  ).length;

  return computeConfidence({ hotRings, patternChanges, warningDelta: warningDelta.value });
});

const previousConfidence = ref<ConfLevel | null>(null);

const confidenceTrend = computed(() =>
  computeConfidenceTrend(confidenceLevel.value, previousConfidence.value)
);

// Bundle 07: Tooltip explaining confidence and trend (now from centralized util)
const confidenceTooltip = computed(() => getConfidenceTooltipText());

async function loadSnapshotsForCompare() {
  error.value = "";
  left.value = null;
  right.value = null;

  if (!canCompare.value) return;

  loading.value = true;
  try {
    const [a, b] = await Promise.all([
      artSnapshotsClient.get(leftId.value),
      artSnapshotsClient.get(rightId.value),
    ]);
    left.value = a as AnySnap;
    right.value = b as AnySnap;
  } catch (e: any) {
    error.value = e?.message || String(e);
    toast.error( error.value);
  } finally {
    loading.value = false;
  }
}

// 32.1.0d: Live compare triggers on id change (manual mode uses Compare button)
watch(() => [leftId.value, rightId.value], () => {
  scheduleLiveCompare();
});

// Bundle 06: Track previous confidence when compare results change
watch(
  () => [left.value, right.value] as const,
  ([newLeft, newRight], [oldLeft, oldRight]) => {
    // Only update trend baseline when compare results actually change
    if (!newLeft || !newRight) return;

    // If we had a previous valid compare, record its confidence as baseline
    if (oldLeft && oldRight) {
      // Compute what the previous confidence was (before reactivity updates it)
      const oldHotRings = deltaRows.value.filter((r) => Math.abs(r.delta) >= 0.15).length;
      // Use current confidenceLevel as the "previous" since it will update after this
      previousConfidence.value = confidenceLevel.value;
      return;
    }

    // First result in session: no arrow yet
    previousConfidence.value = null;
  }
);

// Auto-select Left=baseline when snapshots list changes and Left is empty (32.1.0a)
watch(
  () => store.snapshots,
  (snaps) => {
    if (!snaps || !snaps.length) return;
    if (leftId.value) return;

    const base = snaps.find((s: any) => s.baseline === true);
    if (base?.snapshot_id) {
      leftId.value = base.snapshot_id;
    }
  },
  { immediate: true, deep: false }
);

// Auto-select Right=most recent non-baseline when Left is set (32.1.0b)
watch(
  () => [store.snapshots, leftId.value],
  () => {
    const snaps = store.snapshots || [];
    if (!snaps.length) return;

    // If left is set but right is empty, pick a default right
    if (leftId.value && !rightId.value) {
      pickMostRecentNonBaselineAsRight();
      return;
    }

    // If right equals left, re-pick
    if (leftId.value && rightId.value && leftId.value === rightId.value) {
      rightId.value = "";
      pickMostRecentNonBaselineAsRight();
    }
  },
  { immediate: true }
);

// When opening panel, ensure both defaults are set (32.1.0a + 32.1.0b)
watch(
  () => isOpen.value,
  (open) => {
    if (!open) return;
    if (!leftId.value) pickBaselineLeft();
    if (leftId.value && !rightId.value) pickMostRecentNonBaselineAsRight();
  }
);

// 32.1.0c: Auto-run Compare when panel opens with both IDs set
watch(
  () => [isOpen.value, leftId.value, rightId.value],
  async ([open, l, r]) => {
    if (!open) return;
    if (!l || !r) return;
    if (l === r) return;

    // Run once per open session (prevents loops / spam)
    if (autoComparedOnce.value) return;

    autoComparedOnce.value = true;
    await loadSnapshotsForCompare();
  },
  { immediate: true }
);

// 32.1.0c + 32.1.0d: Reset guards and timer when panel closes
watch(
  () => isOpen.value,
  (open) => {
    if (!open) {
      autoComparedOnce.value = false;
      if (liveTimer) {
        window.clearTimeout(liveTimer);
        liveTimer = null;
      }
    }
  }
);

function pickBaselineLeft() {
  const base = (store.snapshots || []).find((s: any) => s.baseline === true);
  if (!base) {
    toast.warning( "No baseline snapshot found.");
    return;
  }
  leftId.value = base.snapshot_id;
}

// 32.1.0b: Pick the most recent non-baseline snapshot as Right
function pickMostRecentNonBaselineAsRight() {
  const snaps = store.snapshots || [];
  if (!snaps.length) return;

  // Filter to non-baseline snapshots that are not the left snapshot
  const candidates = snaps.filter(
    (s: any) => s?.baseline !== true && s?.snapshot_id && s.snapshot_id !== leftId.value
  );

  if (!candidates.length) return;

  // Sort by created_at/updated_at descending (most recent first) — Bundle 04 nuance fix
  const sorted = [...candidates].sort((a: any, b: any) => {
    const aDate = a.updated_at || a.created_at || "";
    const bDate = b.updated_at || b.created_at || "";
    return String(bDate).localeCompare(String(aDate));
  });

  if (sorted[0]?.snapshot_id) {
    rightId.value = sorted[0].snapshot_id;
  }
}

function swapSides() {
  const tmp = leftId.value;
  leftId.value = rightId.value;
  rightId.value = tmp;
}

function clearCompare() {
  leftId.value = "";
  rightId.value = "";
  left.value = null;
  right.value = null;
  error.value = "";
  autoComparedOnce.value = false; // 32.1.0c: reset guard
  // 32.1.0d: clear live timer
  if (liveTimer) {
    window.clearTimeout(liveTimer);
    liveTimer = null;
  }
}

// 32.1.0e: Keyboard shortcuts [ and ] to step Right snapshot
function _isTypingTarget(el: EventTarget | null): boolean {
  const node = el as HTMLElement | null;
  if (!node) return false;
  const tag = (node.tagName || "").toLowerCase();
  return tag === "input" || tag === "textarea" || tag === "select" || node.isContentEditable;
}

function _snapshotIndexById(id: string): number {
  const snaps = store.snapshots || [];
  return snaps.findIndex((s: any) => s?.snapshot_id === id);
}

function stepRight(delta: number) {
  const snaps = store.snapshots || [];
  if (!snaps.length) return;

  const curIdx = _snapshotIndexById(rightId.value);
  // If no right selected, pick first non-baseline
  if (curIdx < 0) {
    pickMostRecentNonBaselineAsRight();
    scheduleLiveCompare();
    return;
  }

  let nextIdx = curIdx + delta;
  nextIdx = Math.max(0, Math.min(snaps.length - 1, nextIdx));

  const next = snaps[nextIdx];
  if (!next?.snapshot_id) return;

  // Avoid right == left; if collision, try stepping one more in same direction
  if (next.snapshot_id === leftId.value) {
    const altIdx = Math.max(0, Math.min(snaps.length - 1, nextIdx + delta));
    const alt = snaps[altIdx];
    if (alt?.snapshot_id && alt.snapshot_id !== leftId.value) {
      rightId.value = alt.snapshot_id;
      scheduleLiveCompare();
      return;
    }
  }

  rightId.value = next.snapshot_id;
  scheduleLiveCompare();
}

// 32.1.0f: Step Left snapshot with Shift+[ / Shift+]
function stepLeft(delta: number) {
  const snaps = store.snapshots || [];
  if (!snaps.length) return;

  const curIdx = _snapshotIndexById(leftId.value);
  // If no left selected, try baseline first
  if (curIdx < 0) {
    pickBaselineLeft();
    scheduleLiveCompare();
    return;
  }

  let nextIdx = curIdx + delta;
  nextIdx = Math.max(0, Math.min(snaps.length - 1, nextIdx));

  const next = snaps[nextIdx];
  if (!next?.snapshot_id) return;

  // Avoid left == right; try stepping one more if needed
  if (next.snapshot_id === rightId.value) {
    const altIdx = Math.max(0, Math.min(snaps.length - 1, nextIdx + delta));
    const alt = snaps[altIdx];
    if (alt?.snapshot_id && alt.snapshot_id !== rightId.value) {
      leftId.value = alt.snapshot_id;
      scheduleLiveCompare();
      return;
    }
  }

  leftId.value = next.snapshot_id;
  scheduleLiveCompare();
}

function onKeyDown(e: KeyboardEvent) {
  if (!isOpen.value) return;
  if (_isTypingTarget(e.target)) return;

  // 32.1.0f: Shift+[ / Shift+] steps Left; plain [ / ] steps Right
  if (e.key === "[") {
    e.preventDefault();
    if (e.shiftKey) {
      stepLeft(-1);
    } else {
      stepRight(-1);
    }
  } else if (e.key === "]") {
    e.preventDefault();
    if (e.shiftKey) {
      stepLeft(1);
    } else {
      stepRight(1);
    }
  }
}

onMounted(() => {
  window.addEventListener("keydown", onKeyDown);

  // Bundle 03: Restore keyboard hints preference from localStorage
  const savedHints = localStorage.getItem(KEYBOARD_HINTS_KEY);
  if (savedHints !== null) {
    showKeyboardHints.value = savedHints === "true";
  }
});

// Bundle 03: Persist keyboard hints preference
watch(showKeyboardHints, (val) => {
  localStorage.setItem(KEYBOARD_HINTS_KEY, String(val));
});

onBeforeUnmount(() => {
  window.removeEventListener("keydown", onKeyDown);
});
</script>

<template>
  <div class="card">
    <div class="row">
      <h3 style="display:flex; align-items:center; gap:8px; margin:0;">
        <button
          class="btn"
          style="padding:6px 10px;"
          @click="isOpen = !isOpen"
        >
          {{ isOpen ? "▾" : "▸" }}
        </button>
        Snapshot Compare
      </h3>
      <div class="actions">
        <button
          class="btn"
          :disabled="store.snapshotsLoading"
          @click="store.loadRecentSnapshots()"
        >
          Refresh list
        </button>
      </div>
    </div>

    <CompareOpenPanel
      v-if="isOpen"
      v-model:left-id="leftId"
      v-model:right-id="rightId"
      v-model:live-compare="liveCompare"
      v-model:show-keyboard-hints="showKeyboardHints"
      :snapshots="store.snapshots"
      :loading="loading"
      :error="error"
      :left="left"
      :right="right"
      :can-compare="canCompare"
      :delta-rows="deltaRows"
      :confidence-level="confidenceLevel"
      :confidence-trend="confidenceTrend"
      :confidence-tooltip="confidenceTooltip"
      :score-delta="scoreDelta"
      :warning-delta="warningDelta"
      @pick-baseline-left="pickBaselineLeft"
      @swap-sides="swapSides"
      @compare="loadSnapshotsForCompare"
      @clear="clearCompare"
      @load-snapshot="store.loadSnapshot"
    />
  </div>
</template>

<style scoped>
/* Mirror SnapshotPanel.vue styling so it feels native */
.card {
  border: 1px solid #ddd;
  border-radius: 12px;
  padding: 12px;
  background: #fff;
}

.row {
  display: flex;
  gap: 10px;
  align-items: center;
  justify-content: space-between;
  margin: 8px 0;
  flex-wrap: wrap;
}

.btn {
  padding: 8px 10px;
  border-radius: 10px;
  border: 1px solid #ccc;
  background: #f7f7f7;
  cursor: pointer;
}

.actions {
  display: flex;
  gap: 8px;
}
</style>
