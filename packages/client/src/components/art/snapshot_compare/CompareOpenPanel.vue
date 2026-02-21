<template>
  <div>
    <div class="row">
      <select
        :value="leftId"
        class="input"
        @change="emit('update:leftId', ($event.target as HTMLSelectElement).value)"
      >
        <option value="">
          Left snapshot…
        </option>
        <option
          v-for="s in snapshots"
          :key="s.snapshot_id"
          :value="s.snapshot_id"
        >
          {{ s.name }} ({{ s.snapshot_id }})
        </option>
      </select>

      <select
        :value="rightId"
        class="input"
        @change="emit('update:rightId', ($event.target as HTMLSelectElement).value)"
      >
        <option value="">
          Right snapshot…
        </option>
        <option
          v-for="s in snapshots"
          :key="s.snapshot_id"
          :value="s.snapshot_id"
        >
          {{ s.name }} ({{ s.snapshot_id }})
        </option>
      </select>
    </div>

    <div class="row">
      <button
        class="btn"
        @click="emit('pick-baseline-left')"
      >
        Use baseline as Left
      </button>
      <button
        class="btn"
        :disabled="!leftId || !rightId"
        @click="emit('swap-sides')"
      >
        Swap
      </button>
      <button
        class="btn"
        :disabled="!canCompare"
        @click="emit('compare')"
      >
        Compare
      </button>
      <button
        class="btn"
        @click="emit('clear')"
      >
        Clear
      </button>
    </div>

    <!-- Keyboard hints with user toggle -->
    <div class="keyboard-hints-row">
      <label class="hint-toggle">
        <input
          :checked="showKeyboardHints"
          type="checkbox"
          @change="emit('update:showKeyboardHints', ($event.target as HTMLInputElement).checked)"
        >
        Show keyboard hints
      </label>
      <div
        v-if="showKeyboardHints"
        class="hint-text"
      >
        <kbd>[</kbd> / <kbd>]</kbd> step <strong>Right</strong>
        <span class="hint-sep">·</span>
        <kbd>Shift</kbd>+<kbd>[</kbd> / <kbd>]</kbd> step <strong>Left</strong>
      </div>
    </div>

    <div
      class="row"
      style="justify-content:flex-start;"
    >
      <label
        class="meta"
        style="display:flex; align-items:center; gap:6px; cursor:pointer;"
      >
        <input
          :checked="liveCompare"
          type="checkbox"
          @change="emit('update:liveCompare', ($event.target as HTMLInputElement).checked)"
        >
        Live compare
      </label>
      <span
        class="meta"
        style="font-size:11px; color:#888;"
      >
        (auto-runs on selection change)
      </span>
    </div>

    <div
      v-if="loading"
      class="empty"
    >
      Loading snapshots…
    </div>
    <div
      v-else-if="error"
      class="err"
    >
      {{ error }}
    </div>
    <div
      v-else-if="!leftId || !rightId"
      class="empty"
    >
      Select two snapshots to compare.
    </div>
    <div
      v-else-if="leftId === rightId"
      class="hint-red"
    >
      Pick two different snapshots.
    </div>

    <div v-else>
      <!-- Header cards -->
      <div class="list">
        <div
          v-if="left"
          class="snap"
        >
          <div class="left">
            <div class="nm">
              Left: {{ left.name || left.snapshot_id }}
            </div>
            <div class="meta">
              {{ left.snapshot_id }} - {{ fmtDate(left.updated_at || left.created_at) }}
              <span v-if="left.baseline === true"> • BASELINE</span>
            </div>
            <div
              v-if="left.notes"
              class="meta"
            >
              Notes: {{ left.notes }}
            </div>
          </div>
          <div class="actions">
            <button
              class="btn"
              @click="emit('load-snapshot', left.snapshot_id)"
            >
              Load
            </button>
          </div>
        </div>

        <div
          v-if="right"
          class="snap"
        >
          <div class="left">
            <div class="nm">
              Right: {{ right.name || right.snapshot_id }}
            </div>
            <div class="meta">
              {{ right.snapshot_id }} - {{ fmtDate(right.updated_at || right.created_at) }}
              <span v-if="right.baseline === true"> • BASELINE</span>
            </div>
            <div
              v-if="right.notes"
              class="meta"
            >
              Notes: {{ right.notes }}
            </div>
          </div>
          <div class="actions">
            <button
              class="btn"
              @click="emit('load-snapshot', right.snapshot_id)"
            >
              Load
            </button>
          </div>
        </div>
      </div>

      <!-- Compare summary -->
      <div
        class="snap"
        style="margin-top: 10px;"
      >
        <div class="left">
          <div class="nm">
            Summary
            <!-- Tooltip wrapper for confidence badge + trend -->
            <span
              class="confidence-tooltip-wrap"
              :title="confidenceTooltip"
            >
              <!-- Confidence badge -->
              <span
                class="confidence-badge"
                :data-level="confidenceLevel"
              >
                {{ confidenceLevel }}
              </span>
              <!-- Confidence trend arrow -->
              <span
                class="confidence-trend"
                :data-trend="confidenceTrend"
              >
                <span v-if="confidenceTrend === 'UP'">↑</span>
                <span v-else-if="confidenceTrend === 'DOWN'">↓</span>
                <span v-else-if="confidenceTrend === 'FLAT'">→</span>
              </span>
            </span>
            <!-- Confidence Legend Modal -->
            <ConfidenceLegendModal />
          </div>
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

      <!-- Ring deltas header -->
      <div
        class="row"
        style="margin-top: 8px;"
      >
        <h4 style="margin: 0;">
          Ring width deltas
        </h4>
        <div
          class="meta"
          style="font-size: 12px;"
        >
          Highlight when |Δ| ≥ 0.15mm
        </div>
      </div>

      <!-- Delta rows -->
      <div
        v-if="deltaRows.length"
        class="list"
      >
        <div
          v-for="r in deltaRows"
          :key="r.ring"
          class="snap"
        >
          <div class="left">
            <div class="nm">
              Ring {{ r.ring }}
              <span
                v-if="Math.abs(r.delta) >= 0.15"
                class="hint-red"
              > • HOT</span>
            </div>
            <div class="meta">
              Left: {{ r.aWidth.toFixed(2) }}mm → Right: {{ r.bWidth.toFixed(2) }}mm
              • Δ {{ r.delta.toFixed(2) }}mm
            </div>
            <div
              v-if="r.aPattern || r.bPattern"
              class="meta"
            >
              Pattern: {{ r.aPattern || "—" }} → {{ r.bPattern || "—" }}
            </div>
          </div>
        </div>
      </div>

      <div
        v-else
        class="empty"
      >
        No ring data found in one or both snapshots.
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import ConfidenceLegendModal from "@/components/rmos/ConfidenceLegendModal.vue";
import type { ConfLevel } from "@/utils/rmosConfidence";

type AnySnap = any;

interface DeltaRow {
  ring: number
  aWidth: number
  bWidth: number
  delta: number
  aPattern: string
  bPattern: string
}

defineProps<{
  leftId: string
  rightId: string
  snapshots: any[]
  loading: boolean
  error: string
  left: AnySnap | null
  right: AnySnap | null
  canCompare: boolean
  liveCompare: boolean
  showKeyboardHints: boolean
  deltaRows: DeltaRow[]
  confidenceLevel: ConfLevel
  confidenceTrend: "UP" | "DOWN" | "FLAT" | "NONE"
  confidenceTooltip: string
  scoreDelta: number | null
  warningDelta: number
}>()

const emit = defineEmits<{
  'update:leftId': [value: string]
  'update:rightId': [value: string]
  'update:liveCompare': [value: boolean]
  'update:showKeyboardHints': [value: boolean]
  'pick-baseline-left': []
  'swap-sides': []
  'compare': []
  'clear': []
  'load-snapshot': [snapshotId: string]
}>()

function fmtDate(s: any) {
  try {
    return new Date(String(s)).toLocaleString();
  } catch {
    return String(s || "");
  }
}
</script>

<style scoped>
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

/* Keyboard hints styling */
.keyboard-hints-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 8px 0;
  flex-wrap: wrap;
}

.hint-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #666;
  cursor: pointer;
  user-select: none;
}

.hint-toggle input[type="checkbox"] {
  margin: 0;
  cursor: pointer;
}

.hint-text {
  font-size: 12px;
  color: #555;
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
}

.hint-text kbd {
  background: #f3f3f3;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 2px 6px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 11px;
  color: #333;
  box-shadow: 0 1px 1px rgba(0,0,0,0.08);
}

.hint-text strong {
  font-weight: 600;
}

.hint-sep {
  color: #999;
  margin: 0 4px;
}

/* Confidence badge styling */
.confidence-badge {
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
  margin-left: 0.5rem;
}

.confidence-tooltip-wrap {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  cursor: help;
}

.confidence-badge[data-level="HIGH"] {
  background: #e6f7ee;
  color: #18794e;
}

.confidence-badge[data-level="MED"] {
  background: #fff4e5;
  color: #8a5a00;
}

.confidence-badge[data-level="LOW"] {
  background: #fdecea;
  color: #b42318;
}

/* Confidence trend arrow styling */
.confidence-trend {
  margin-left: 6px;
  font-weight: 700;
  font-size: 0.85rem;
  opacity: 0.9;
}

.confidence-trend[data-trend="NONE"] {
  display: none;
}

.confidence-trend[data-trend="UP"] {
  color: #18794e;
}

.confidence-trend[data-trend="DOWN"] {
  color: #b42318;
}

.confidence-trend[data-trend="FLAT"] {
  color: #8a5a00;
}
</style>
