<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useRosetteStore } from "@/stores/rosetteStore";
import { useToastStore } from "@/stores/toastStore";
import { artSnapshotsClient } from "@/api/artSnapshotsClient";

type AnySnap = any;

const store = useRosetteStore();
const toast = useToastStore();

const leftId = ref<string>("");
const rightId = ref<string>("");

const loading = ref(false);
const error = ref<string>("");

// Collapsed by default (32.1.0a)
const isOpen = ref(false);

const left = ref<AnySnap | null>(null);
const right = ref<AnySnap | null>(null);

const canCompare = computed(() => !!leftId.value && !!rightId.value && leftId.value !== rightId.value);

function fmtDate(s: any) {
  try {
    return new Date(String(s)).toLocaleString();
  } catch {
    return String(s || "");
  }
}

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

  const rows = [];
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
    toast.push("error", error.value);
  } finally {
    loading.value = false;
  }
}

// Auto-refresh compare view when ids change
watch(() => [leftId.value, rightId.value], () => {
  void loadSnapshotsForCompare();
});

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

// When opening panel, if left is still empty, try baseline once (32.1.0a)
watch(
  () => isOpen.value,
  (open) => {
    if (!open) return;
    if (!leftId.value) pickBaselineLeft();
  }
);

function pickBaselineLeft() {
  const base = (store.snapshots || []).find((s: any) => s.baseline === true);
  if (!base) {
    toast.push("warning", "No baseline snapshot found.");
    return;
  }
  leftId.value = base.snapshot_id;
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
}
</script>

<template>
  <div class="card">
    <div class="row">
      <h3 style="display:flex; align-items:center; gap:8px; margin:0;">
        <button class="btn" @click="isOpen = !isOpen" style="padding:6px 10px;">
          {{ isOpen ? "▾" : "▸" }}
        </button>
        Snapshot Compare
      </h3>
      <div class="actions">
        <button class="btn" @click="store.loadRecentSnapshots()" :disabled="store.snapshotsLoading">
          Refresh list
        </button>
      </div>
    </div>

    <div v-if="isOpen">
    <div class="row">
      <select class="input" v-model="leftId">
        <option value="">Left snapshot…</option>
        <option v-for="s in store.snapshots" :key="s.snapshot_id" :value="s.snapshot_id">
          {{ s.name }} ({{ s.snapshot_id }})
        </option>
      </select>

      <select class="input" v-model="rightId">
        <option value="">Right snapshot…</option>
        <option v-for="s in store.snapshots" :key="s.snapshot_id" :value="s.snapshot_id">
          {{ s.name }} ({{ s.snapshot_id }})
        </option>
      </select>
    </div>

    <div class="row">
      <button class="btn" @click="pickBaselineLeft">Use baseline as Left</button>
      <button class="btn" @click="swapSides" :disabled="!leftId || !rightId">Swap</button>
      <button class="btn" @click="loadSnapshotsForCompare" :disabled="!canCompare">Compare</button>
      <button class="btn" @click="clearCompare">Clear</button>
    </div>

    <div v-if="loading" class="empty">Loading snapshots…</div>
    <div v-else-if="error" class="err">{{ error }}</div>
    <div v-else-if="!leftId || !rightId" class="empty">Select two snapshots to compare.</div>
    <div v-else-if="leftId === rightId" class="hint-red">Pick two different snapshots.</div>

    <div v-else>
      <!-- Header cards that match SnapshotPanel visual language -->
      <div class="list">
        <div class="snap" v-if="left">
          <div class="left">
            <div class="nm">Left: {{ left.name || left.snapshot_id }}</div>
            <div class="meta">
              {{ left.snapshot_id }} - {{ fmtDate(left.updated_at || left.created_at) }}
              <span v-if="left.baseline === true"> • BASELINE</span>
            </div>
            <div class="meta" v-if="left.notes">Notes: {{ left.notes }}</div>
          </div>
          <div class="actions">
            <button class="btn" @click="store.loadSnapshot(left.snapshot_id)">Load</button>
          </div>
        </div>

        <div class="snap" v-if="right">
          <div class="left">
            <div class="nm">Right: {{ right.name || right.snapshot_id }}</div>
            <div class="meta">
              {{ right.snapshot_id }} - {{ fmtDate(right.updated_at || right.created_at) }}
              <span v-if="right.baseline === true"> • BASELINE</span>
            </div>
            <div class="meta" v-if="right.notes">Notes: {{ right.notes }}</div>
          </div>
          <div class="actions">
            <button class="btn" @click="store.loadSnapshot(right.snapshot_id)">Load</button>
          </div>
        </div>
      </div>

      <!-- Compare summary -->
      <div class="snap" style="margin-top: 10px;">
        <div class="left">
          <div class="nm">Summary</div>
          <div class="meta">
            Score Δ:
            <b v-if="scoreDelta !== null">{{ scoreDelta.toFixed(1) }}</b>
            <span v-else>—</span>
            • Warnings Δ: <b>{{ warningDelta }}</b>
          </div>
          <div class="meta">
            Left risk: <b>{{ left?.feasibility?.risk_bucket ?? left?.feasibility?.riskBucket ?? "—" }}</b>
            • Right risk: <b>{{ right?.feasibility?.risk_bucket ?? right?.feasibility?.riskBucket ?? "—" }}</b>
          </div>
        </div>
      </div>

      <!-- Ring deltas displayed in SnapshotPanel-style list rows -->
      <div class="row" style="margin-top: 8px;">
        <h4 style="margin: 0;">Ring width deltas</h4>
        <div class="meta" style="font-size: 12px;">
          Highlight when |Δ| ≥ 0.15mm
        </div>
      </div>

      <div class="list" v-if="deltaRows.length">
        <div class="snap" v-for="r in deltaRows" :key="r.ring">
          <div class="left">
            <div class="nm">
              Ring {{ r.ring }}
              <span v-if="Math.abs(r.delta) >= 0.15" class="hint-red"> • HOT</span>
            </div>
            <div class="meta">
              Left: {{ r.aWidth.toFixed(2) }}mm → Right: {{ r.bWidth.toFixed(2) }}mm
              • Δ {{ r.delta.toFixed(2) }}mm
            </div>
            <div class="meta" v-if="r.aPattern || r.bPattern">
              Pattern: {{ r.aPattern || "—" }} → {{ r.bPattern || "—" }}
            </div>
          </div>
        </div>
      </div>

      <div v-else class="empty">No ring data found in one or both snapshots.</div>
    </div>
    </div>
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
.input {
  flex: 1;
  border: 1px solid #ccc;
  border-radius: 10px;
  padding: 8px;
  min-width: 160px;
}
.btn {
  padding: 8px 10px;
  border-radius: 10px;
  border: 1px solid #ccc;
  background: #f7f7f7;
  cursor: pointer;
}
.btn.primary {
  background: #111;
  color: #fff;
  border-color: #111;
}
.list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 10px;
  max-height: 280px;
  overflow: auto;
}
.snap {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px;
  border: 1px solid #eee;
  border-radius: 12px;
  background: #fafafa;
}
.left {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.nm {
  font-weight: 600;
}
.meta {
  font-size: 12px;
  color: #444;
}
.actions {
  display: flex;
  gap: 8px;
}
.err {
  color: #a00;
  margin: 8px 0;
}
.empty {
  color: #666;
  font-size: 13px;
  padding: 10px;
}
.hint-red {
  font-size: 12px;
  color: #a00;
  margin: 4px 0;
}
</style>
