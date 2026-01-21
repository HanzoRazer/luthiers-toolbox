<script setup lang="ts">
import { computed } from "vue";
import ConfidenceBadge from "@/components/art/ConfidenceBadge.vue";
import { getConfidenceReason, diffFeasibility } from "@/utils/confidenceReasons";

type SnapshotLike = {
  snapshot_id?: string;
  name?: string;
  created_at?: string;
  feasibility?: any;
  // Optional future shape:
  ring_diagnostics?: any[]; // if backend adds later
};

const props = defineProps<{
  current: SnapshotLike | null;
  previous?: SnapshotLike | null;
  onFocusWorstRing?: (diag: any) => void;
}>();

const reason = computed(() => getConfidenceReason(props.current?.feasibility ?? null));
const change = computed(() => diffFeasibility(props.previous?.feasibility ?? null, props.current?.feasibility ?? null));

const headline = computed(() => {
  // If no previous, just show reason
  if (!props.previous) return reason.value.short;

  const scoreDelta = change.value.scoreDelta;
  const warnDelta = change.value.warnDelta;

  // Small, clear message
  if (scoreDelta <= -2 || warnDelta >= 1 || change.value.aRisk !== change.value.bRisk) {
    return "Confidence changed";
  }
  return "Stable signal";
});

const warnings = computed<string[]>(() => props.current?.feasibility?.warnings ?? []);
const topWarnings = computed(() => warnings.value.slice(0, 3));

const ringDiagnostics = computed<any[]>(() => {
  // Support either embedded ring_diagnostics or feasibility.ring_diagnostics in future
  const d1 = (props.current as any)?.ring_diagnostics;
  const d2 = (props.current?.feasibility as any)?.ring_diagnostics;
  return (Array.isArray(d1) ? d1 : Array.isArray(d2) ? d2 : []);
});

const worstRing = computed(() => {
  if (!ringDiagnostics.value.length) return null;
  // Conservative: pick the first RED, else first YELLOW, else first
  const reds = ringDiagnostics.value.filter((d) => String(d?.risk_bucket ?? d?.riskBucket) === "RED");
  if (reds.length) return reds[0];
  const yellows = ringDiagnostics.value.filter((d) => String(d?.risk_bucket ?? d?.riskBucket) === "YELLOW");
  if (yellows.length) return yellows[0];
  return ringDiagnostics.value[0];
});

function onFocus() {
  if (!worstRing.value || !props.onFocusWorstRing) return;
  props.onFocusWorstRing(worstRing.value);
}
</script>

<template>
  <div class="wrap">
    <div class="row">
      <div class="left">
        <div class="title">
          {{ headline }}
        </div>
        <div
          class="sub"
          :title="reason.detail"
        >
          {{ reason.short }}
        </div>
      </div>

      <div class="right">
        <ConfidenceBadge :feasibility="current?.feasibility" />
      </div>
    </div>

    <div
      v-if="previous && current"
      class="diff"
    >
      <div class="diffRow">
        <span class="k">Score</span>
        <span class="v">{{ change.aScore.toFixed(1) }} &rarr; {{ change.bScore.toFixed(1) }}</span>
      </div>

      <div class="diffRow">
        <span class="k">Warnings</span>
        <span class="v">{{ change.aWarn }} &rarr; {{ change.bWarn }}</span>
      </div>

      <div
        v-if="change.riskChanged"
        class="diffRow"
      >
        <span class="k">Risk</span>
        <span class="v">{{ change.aRisk }} &rarr; {{ change.bRisk }}</span>
      </div>
    </div>

    <div
      v-if="topWarnings.length"
      class="warnings"
    >
      <div class="sectionTitle">
        Top warnings
      </div>
      <ul>
        <li
          v-for="(w, i) in topWarnings"
          :key="i"
        >
          {{ w }}
        </li>
      </ul>
    </div>

    <div
      v-if="worstRing && onFocusWorstRing"
      class="actions"
    >
      <button
        class="btn"
        type="button"
        @click="onFocus"
      >
        Focus worst ring
      </button>
      <span class="hint">
        (only shown when ring diagnostics exist)
      </span>
    </div>
  </div>
</template>

<style scoped>
.wrap {
  border: 1px solid #e6e6e6;
  border-radius: 12px;
  padding: 12px;
  background: #fff;
}

.row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.title {
  font-weight: 700;
  font-size: 13px;
}

.sub {
  font-size: 12px;
  color: #666;
  margin-top: 2px;
}

.diff {
  margin-top: 10px;
  border-top: 1px solid #f0f0f0;
  padding-top: 10px;
}

.diffRow {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  padding: 2px 0;
}

.k { color: #666; }
.v { font-weight: 600; }

.warnings {
  margin-top: 10px;
  border-top: 1px solid #f0f0f0;
  padding-top: 10px;
}

.sectionTitle {
  font-size: 12px;
  font-weight: 700;
  margin-bottom: 6px;
}

ul {
  margin: 0;
  padding-left: 16px;
  font-size: 12px;
  color: #333;
}

.actions {
  margin-top: 10px;
  border-top: 1px solid #f0f0f0;
  padding-top: 10px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.btn {
  font-size: 12px;
  font-weight: 700;
  padding: 6px 10px;
  border-radius: 10px;
  border: 1px solid #ddd;
  background: #fafafa;
  cursor: pointer;
}
.btn:hover {
  background: #f2f2f2;
}

.hint {
  font-size: 11px;
  color: #777;
}
</style>
