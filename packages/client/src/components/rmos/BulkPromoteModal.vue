<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { promoteAdvisoryVariant } from "@/api/rmosRuns";

type Risk = "GREEN" | "YELLOW" | "RED" | "UNKNOWN" | "ERROR";

const props = defineProps<{
  open: boolean;
  runId: string;
  advisoryIds: string[];
  // optional parallel arrays, used for summary only (no hard dependency)
  riskById?: Record<string, Risk | undefined>;
  apiBase?: string; // default "/api"
}>();

const emit = defineEmits<{
  (e: "close"): void;
  (e: "done"): void;
}>();

const apiBase = computed(() => props.apiBase ?? "/api");

const busy = ref(false);
const error = ref<string | null>(null);
const doneCount = ref(0);

// Confirmation gate: require explicit tick if any YELLOW/RED/UNKNOWN/ERROR
const acknowledgedRisk = ref(false);

const total = computed(() => props.advisoryIds.length);

const riskCounts = computed(() => {
  const counts: Record<string, number> = { GREEN: 0, YELLOW: 0, RED: 0, UNKNOWN: 0, ERROR: 0 };
  const map = props.riskById ?? {};
  for (const id of props.advisoryIds) {
    const r = (map[id] ?? "UNKNOWN") as Risk;
    if (!counts[r]) counts[r] = 0;
    counts[r] += 1;
  }
  return counts;
});

const hasNonGreen = computed(() => {
  const c = riskCounts.value;
  return (c.YELLOW + c.RED + c.UNKNOWN + c.ERROR) > 0;
});

const canSubmit = computed(() => {
  if (busy.value) return false;
  if (total.value <= 0) return false;
  if (hasNonGreen.value && !acknowledgedRisk.value) return false;
  return true;
});

watch(
  () => props.open,
  (v) => {
    if (v) {
      busy.value = false;
      error.value = null;
      doneCount.value = 0;
      acknowledgedRisk.value = false;
    }
  }
);

async function submit() {
  if (!canSubmit.value) return;
  busy.value = true;
  error.value = null;
  doneCount.value = 0;

  try {
    // Sequential for safety + predictable failure behavior
    for (const advisoryId of props.advisoryIds) {
      await promoteAdvisoryVariant(apiBase.value, props.runId, advisoryId);
      doneCount.value += 1;
    }
    emit("done");
  } catch (e: any) {
    error.value = e?.message ?? String(e);
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <div
    v-if="open"
    class="modal"
    @click.self="emit('close')"
  >
    <div class="card">
      <div class="title">
        Promote Selected → Manufacturing Candidates
      </div>

      <div class="subtle">
        This will promote <strong>{{ total }}</strong> variant(s) into manufacturing candidates.
      </div>

      <div class="summary">
        <div class="pill">
          GREEN: <strong>{{ riskCounts.GREEN }}</strong>
        </div>
        <div class="pill warn">
          YELLOW: <strong>{{ riskCounts.YELLOW }}</strong>
        </div>
        <div class="pill danger">
          RED: <strong>{{ riskCounts.RED }}</strong>
        </div>
        <div class="pill">
          UNKNOWN: <strong>{{ riskCounts.UNKNOWN }}</strong>
        </div>
        <div class="pill">
          ERROR: <strong>{{ riskCounts.ERROR }}</strong>
        </div>
      </div>

      <label
        v-if="hasNonGreen"
        class="ack"
      >
        <input
          v-model="acknowledgedRisk"
          type="checkbox"
        >
        <span>
          I acknowledge some selections are not GREEN (YELLOW/RED/UNKNOWN/ERROR) and I still want to promote them.
        </span>
      </label>

      <div
        v-if="busy"
        class="subtle"
      >
        Promoting… {{ doneCount }} / {{ total }}
      </div>
      <div
        v-if="error"
        class="error"
      >
        {{ error }}
      </div>

      <div class="row">
        <button
          class="btn tiny secondary"
          :disabled="busy"
          @click="emit('close')"
        >
          Cancel
        </button>
        <button
          class="btn tiny"
          :disabled="!canSubmit"
          @click="submit"
        >
          {{ busy ? "Promoting…" : "Promote Selected" }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.35);
  display:flex; align-items:center; justify-content:center;
  padding: 16px;
  z-index: 1000;
}
.card {
  width: min(720px, 100%);
  background: white;
  border-radius: 14px;
  border: 1px solid rgba(0,0,0,0.12);
  padding: 12px;
}
.title { font-weight: 900; font-size: 16px; margin-bottom: 6px; }
.subtle { opacity: 0.75; margin-bottom: 10px; }
.summary { display:flex; flex-wrap:wrap; gap:8px; margin: 8px 0 10px; }
.pill {
  border: 1px solid rgba(0,0,0,0.14);
  border-radius: 999px;
  padding: 6px 10px;
  font-size: 12px;
  background: rgba(0,0,0,0.02);
}
.pill.warn { border-color: rgba(168,120,0,0.28); background: rgba(168,120,0,0.06); }
.pill.danger { border-color: rgba(176,0,32,0.35); background: rgba(176,0,32,0.06); }

.ack { display:flex; gap:10px; align-items:flex-start; margin: 6px 0 4px; font-size: 12px; }
.ack input { margin-top: 2px; }

.row { display:flex; justify-content:flex-end; gap:8px; margin-top: 12px; }
.btn { padding:8px 10px; border:1px solid rgba(0,0,0,0.2); border-radius:10px; background:white; cursor:pointer; }
.btn.tiny { padding:4px 8px; font-size:0.9em; }
.btn.secondary { opacity:0.85; }
.error { color:#b00020; margin-top: 8px; }
</style>
