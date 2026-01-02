<script setup lang="ts">
import { computed } from "vue";
import { useRosetteStore } from "@/stores/rosetteStore";

const store = useRosetteStore();

type HistoryItem = {
  label: string;
  idxFromTop: number; // 0 = newest
};

function describeParams(p: any): string {
  try {
    // Adapt to ring_params (canonical) with fallback to rings
    const rings = p?.ring_params ?? p?.rings ?? [];
    const n = Array.isArray(rings) ? rings.length : 0;

    // Sum widths (best-effort)
    let sum = 0;
    for (let i = 0; i < n; i++) {
      const r = rings[i];
      const w = Number(r?.width_mm ?? r?.widthMm ?? 0);
      if (Number.isFinite(w)) sum += w;
    }

    return `${n} rings • Σ width ${sum.toFixed(2)}mm`;
  } catch {
    return "Design state";
  }
}

const recent = computed<HistoryItem[]>(() => {
  const stack = store.historyStack ?? [];
  const take = stack.slice(Math.max(0, stack.length - 5)); // last 5
  // newest first
  const newestFirst = [...take].reverse();

  return newestFirst.map((p, i) => ({
    label: describeParams(p),
    idxFromTop: i,
  }));
});

function revertTo(idxFromTop: number) {
  // idxFromTop 0 = newest; translate to absolute index in historyStack
  const stack = store.historyStack ?? [];
  if (!stack.length) return;

  const abs = stack.length - 1 - idxFromTop;
  store.revertToHistoryIndex(abs);
}

function clearAll() {
  store.clearHistory();
}
</script>

<template>
  <div class="panel" v-if="(store.historyStack?.length ?? 0) > 0">
    <div class="hdr">
      <div class="title">History</div>
      <div class="meta">{{ store.historyStack.length }} saved</div>
      <button class="miniBtn" type="button" @click="clearAll" title="Clear undo history">
        Clear
      </button>
    </div>

    <div class="list">
      <button
        v-for="(it, i) in recent"
        :key="i"
        class="row"
        type="button"
        @click="revertTo(it.idxFromTop)"
        :title="'Revert to: ' + it.label"
      >
        <span class="dot" />
        <span class="txt">
          <span class="k">Revert</span>
          <span class="v">{{ it.label }}</span>
        </span>
      </button>
    </div>
  </div>

  <div class="panel empty" v-else>
    <div class="hdr">
      <div class="title">History</div>
      <div class="meta">No edits yet</div>
    </div>
  </div>
</template>

<style scoped>
.panel {
  border: 1px solid #e6e6e6;
  border-radius: 12px;
  padding: 10px 12px;
  background: #fff;
}

.panel.empty {
  opacity: 0.8;
}

.hdr {
  display: flex;
  align-items: center;
  gap: 8px;
}

.title {
  font-size: 12px;
  font-weight: 900;
}

.meta {
  font-size: 11px;
  color: #666;
  margin-left: 4px;
}

.miniBtn {
  margin-left: auto;
  font-size: 10px;
  font-weight: 800;
  padding: 3px 8px;
  border-radius: 999px;
  border: 1px solid #ddd;
  background: #fafafa;
  cursor: pointer;
}
.miniBtn:hover { background: #f2f2f2; }

.list {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 8px;
  border-radius: 10px;
  border: 1px solid #f0f0f0;
  background: #fff;
  cursor: pointer;
  text-align: left;
}
.row:hover { background: #fafafa; }

.dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: #ddd;
  flex: 0 0 auto;
}

.txt {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.k {
  font-size: 10px;
  font-weight: 900;
  color: #444;
}

.v {
  font-size: 11px;
  color: #222;
}
</style>
