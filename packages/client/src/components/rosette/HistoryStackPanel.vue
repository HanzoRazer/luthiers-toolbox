<script setup lang="ts">
import { computed } from "vue";
import { useRosetteStore } from "@/stores/rosetteStore";

// Bundle 32.4.8: Prop for hotkey highlight
const props = defineProps<{
  highlightIdxFromTop?: number | null; // 0 = newest row
}>();

// Bundle 32.4.9: Emit when row is reverted (for flash on click)
// Bundle 32.4.16: Emit when history header is hovered (re-show hotkey hint)
const emit = defineEmits<{
  (e: "reverted", idxFromTop: number): void;
  (e: "hoverHint"): void;
}>();

const store = useRosetteStore();

// Bundle 32.4.8: Helper to check if row should flash
function isHotkeyHighlighted(i: number): boolean {
  return props.highlightIdxFromTop === i;
}

// Bundle 32.4.4 + 32.4.5: HistoryItem with action label, params summary, and timestamp
type HistoryItem = {
  label: string;       // action name (e.g., "Ring 3 +0.10mm")
  paramsLabel: string; // summary (e.g., "4 rings • Σ width 12.80mm")
  idxFromTop: number;  // 0 = newest
  ts: number;          // timestamp (ms since epoch)
  age: string;         // relative age (e.g., "12s ago")
  abs: string;         // absolute time (locale string)
};

// Bundle 32.4.5: Format timestamp as locale string
function fmtAbsolute(ts: number): string {
  try {
    return new Date(ts).toLocaleString();
  } catch {
    return String(ts);
  }
}

// Bundle 32.4.5: Format relative age
function fmtAge(ts: number): string {
  const now = Date.now();
  const diff = Math.max(0, now - ts);

  const s = Math.floor(diff / 1000);
  if (s < 60) return `${s}s ago`;

  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ago`;

  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;

  const d = Math.floor(h / 24);
  return `${d}d ago`;
}

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

// Bundle 32.4.4 + 32.4.5: Pull action labels and timestamps from HistoryEntry objects
const recent = computed<HistoryItem[]>(() => {
  const stack = store.historyStack ?? [];
  const take = stack.slice(Math.max(0, stack.length - 5)); // last 5
  // newest first
  const newestFirst = [...take].reverse();

  return newestFirst.map((entry: any, i: number) => {
    const ts = Number(entry?.ts ?? Date.now());
    return {
      label: entry?.label || "Edit",
      paramsLabel: describeParams(entry?.params),
      idxFromTop: i,
      ts,
      age: fmtAge(ts),
      abs: fmtAbsolute(ts),
    };
  });
});

function revertTo(idxFromTop: number) {
  // idxFromTop 0 = newest; translate to absolute index in historyStack
  const stack = store.historyStack ?? [];
  if (!stack.length) return;

  const abs = stack.length - 1 - idxFromTop;
  store.revertToHistoryIndex(abs);

  // Bundle 32.4.9: Emit for flash on click
  emit("reverted", idxFromTop);
}

function clearAll() {
  store.clearHistory();
}
</script>

<template>
  <div class="panel" v-if="(store.historyStack?.length ?? 0) > 0">
    <div class="hdr">
      <div
        class="title"
        title="Hotkeys: 1–5 (1 = newest)"
        @mouseenter="emit('hoverHint')"
      >
        History
      </div>
      <div
        class="hint"
        title="Hotkeys: 1–5 (1 = newest)"
        @mouseenter="emit('hoverHint')"
      >
        1–5
      </div>
      <div class="meta">{{ store.historyStack.length }} saved</div>
      <button class="miniBtn" type="button" @click="clearAll" title="Clear undo history">
        Clear
      </button>
    </div>

    <div class="list">
      <button
        v-for="(it, i) in recent"
        :key="i"
        :class="['row', { hotkeyFlash: isHotkeyHighlighted(i) }]"
        type="button"
        @click="revertTo(it.idxFromTop)"
        :title="'Revert to: ' + it.label + ' (' + it.paramsLabel + ')'"
      >
        <span class="dot" />
        <span class="txt">
          <span class="k">{{ it.label }}</span>
          <span class="v">{{ it.paramsLabel }}</span>
          <span class="t" :title="it.abs">{{ it.age }}</span>
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

/* Bundle 32.4.7: Hotkeys hint badge */
.hint {
  font-size: 10px;
  font-weight: 900;
  padding: 2px 6px;
  border-radius: 999px;
  border: 1px solid #e6e6e6;
  background: #fafafa;
  color: #444;
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

/* Bundle 32.4.5: Timestamp line */
.t {
  font-size: 10px;
  color: #777;
  margin-top: 2px;
}

/* Bundle 32.4.8: Hotkey flash animation */
@keyframes hotFlash {
  0%   { background: #fff; border-color: #f0f0f0; }
  20%  { background: #fff7dc; border-color: #ffe3a3; }
  100% { background: #fff; border-color: #f0f0f0; }
}

.hotkeyFlash {
  animation: hotFlash 700ms ease-out;
}
</style>
