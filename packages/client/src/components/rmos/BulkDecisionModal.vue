<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { setManufacturingCandidateDecision, type CandidateDecision } from "@/api/rmosRuns";

const props = defineProps<{
  open: boolean;
  apiBase?: string; // default "/api"
  runId: string;
  candidateIds: string[];
}>();

const emit = defineEmits<{
  (e: "close"): void;
  (e: "done"): void;
}>();

const apiBase = computed(() => props.apiBase ?? "/api");

const decision = ref<CandidateDecision>("GREEN");
const note = ref("");

const busy = ref(false);
const error = ref<string | null>(null);
const doneCount = ref(0);

const total = computed(() => props.candidateIds.length);
const canSubmit = computed(() => !busy.value && total.value > 0);

watch(
  () => props.open,
  (v) => {
    if (v) {
      decision.value = "GREEN";
      note.value = "";
      busy.value = false;
      error.value = null;
      doneCount.value = 0;
    }
  }
);

async function submit() {
  if (!canSubmit.value) return;
  busy.value = true;
  error.value = null;
  doneCount.value = 0;

  try {
    for (const id of props.candidateIds) {
      await setManufacturingCandidateDecision(apiBase.value, props.runId, id, {
        decision: decision.value,
        note: note.value.trim() || null,
      });
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
        Bulk Decision
      </div>
      <div class="subtle">
        Apply one decision to <strong>{{ total }}</strong> candidate(s).
      </div>

      <label class="ctl">
        <span>Decision</span>
        <select v-model="decision">
          <option value="GREEN">Approve (GREEN)</option>
          <option value="YELLOW">Caution (YELLOW)</option>
          <option value="RED">Reject (RED)</option>
        </select>
      </label>

      <label class="ctl">
        <span>Note (optional)</span>
        <textarea
          v-model="note"
          placeholder="Applies to all selected…"
        />
      </label>

      <div
        v-if="busy"
        class="subtle"
      >
        Saving… {{ doneCount }} / {{ total }}
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
          {{ busy ? "Applying…" : "Apply" }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal{position:fixed;inset:0;background:rgba(0,0,0,.35);display:flex;align-items:center;justify-content:center;padding:16px;z-index:1000}
.card{width:min(640px,100%);background:#fff;border-radius:14px;border:1px solid rgba(0,0,0,.12);padding:12px}
.title{font-weight:900;font-size:16px;margin-bottom:6px}
.subtle{opacity:.75;margin-bottom:10px}
.ctl{display:flex;flex-direction:column;gap:4px;margin-top:10px;font-size:12px}
.ctl select,.ctl textarea{border:1px solid rgba(0,0,0,.18);border-radius:10px;padding:8px}
.ctl textarea{min-height:90px}
.row{display:flex;justify-content:flex-end;gap:8px;margin-top:12px}
.btn{padding:8px 10px;border:1px solid rgba(0,0,0,.2);border-radius:10px;background:#fff;cursor:pointer}
.btn.tiny{padding:4px 8px;font-size:.9em}
.btn.secondary{opacity:.85}
.error{color:#b00020;margin-top:8px}
</style>
