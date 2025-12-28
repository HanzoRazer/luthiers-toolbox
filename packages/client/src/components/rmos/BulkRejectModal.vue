<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { rejectAdvisoryVariant, type RejectReasonCode } from "@/api/rmosRuns";

const props = defineProps<{
  open: boolean;
  runId: string;
  advisoryIds: string[];
  apiBase?: string; // default "/api"
}>();

const emit = defineEmits<{
  (e: "close"): void;
  (e: "done"): void;
}>();

const apiBase = computed(() => props.apiBase ?? "/api");

const reasonCode = ref<RejectReasonCode>("GEOMETRY_UNSAFE");
const reasonDetail = ref("");
const operatorNote = ref("");

const busy = ref(false);
const error = ref<string | null>(null);
const doneCount = ref(0);

const total = computed(() => props.advisoryIds.length);
const canSubmit = computed(() => !busy.value && total.value > 0);

watch(
  () => props.open,
  (v) => {
    if (v) {
      reasonCode.value = "GEOMETRY_UNSAFE";
      reasonDetail.value = "";
      operatorNote.value = "";
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
    for (const advisoryId of props.advisoryIds) {
      await rejectAdvisoryVariant(apiBase.value, props.runId, advisoryId, {
        reason_code: reasonCode.value,
        reason_detail: reasonDetail.value.trim() || null,
        operator_note: operatorNote.value.trim() || null,
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
  <div v-if="open" class="modal" @click.self="emit('close')">
    <div class="card">
      <div class="title">Reject Selected Variants</div>
      <div class="subtle">
        This will reject <strong>{{ total }}</strong> variant(s).
      </div>

      <label class="ctl">
        <span>Reason</span>
        <select v-model="reasonCode">
          <option value="GEOMETRY_UNSAFE">Geometry unsafe</option>
          <option value="TEXT_REQUIRES_OUTLINE">Text requires outline</option>
          <option value="AESTHETIC">Aesthetic</option>
          <option value="DUPLICATE">Duplicate</option>
          <option value="OTHER">Other</option>
        </select>
      </label>

      <label class="ctl">
        <span>Reason detail (optional)</span>
        <input v-model="reasonDetail" placeholder="Short detail applied to all..." />
      </label>

      <label class="ctl">
        <span>Operator note (optional)</span>
        <textarea v-model="operatorNote" placeholder="Longer note applied to all..." />
      </label>

      <div v-if="busy" class="subtle">Rejecting... {{ doneCount }} / {{ total }}</div>
      <div v-if="error" class="error">{{ error }}</div>

      <div class="row">
        <button class="btn tiny secondary" :disabled="busy" @click="emit('close')">Cancel</button>
        <button class="btn tiny danger" :disabled="!canSubmit" @click="submit">
          {{ busy ? "Rejecting..." : "Reject Selected" }}
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
  width: min(640px, 100%);
  background: white;
  border-radius: 14px;
  border: 1px solid rgba(0,0,0,0.12);
  padding: 12px;
}
.title { font-weight: 900; font-size: 16px; margin-bottom: 6px; }
.subtle { opacity: 0.75; margin-bottom: 10px; }
.ctl { display:flex; flex-direction:column; gap:4px; margin-top: 10px; font-size:12px; }
.ctl select, .ctl input, .ctl textarea {
  border:1px solid rgba(0,0,0,0.18);
  border-radius:10px;
  padding:8px;
}
.ctl textarea { min-height: 90px; }
.row { display:flex; justify-content:flex-end; gap:8px; margin-top: 12px; }
.btn { padding:8px 10px; border:1px solid rgba(0,0,0,0.2); border-radius:10px; background:white; cursor:pointer; }
.btn.tiny { padding:4px 8px; font-size:0.9em; }
.btn.secondary { opacity:0.85; }
.btn.danger { border-color: rgba(176,0,32,0.35); background: rgba(176,0,32,0.06); }
.error { color:#b00020; margin-top: 8px; }
</style>
