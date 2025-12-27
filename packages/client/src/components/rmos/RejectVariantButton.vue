<script setup lang="ts">
import { computed, ref } from "vue";
import { rejectAdvisoryVariant, type RejectReasonCode } from "@/api/rmosRuns";

const props = defineProps<{
  runId: string;
  advisoryId: string;
  disabled?: boolean;
}>();

const emit = defineEmits<{ (e: "rejected"): void }>();

const open = ref(false);
const saving = ref(false);
const error = ref<string | null>(null);

const reasonCode = ref<RejectReasonCode>("GEOMETRY_UNSAFE");
const reasonDetail = ref("");
const operatorNote = ref("");

const canSubmit = computed(() => {
  // Always require a code; detail optional
  return !!reasonCode.value && !saving.value;
});

function reset() {
  reasonCode.value = "GEOMETRY_UNSAFE";
  reasonDetail.value = "";
  operatorNote.value = "";
  error.value = null;
}

async function submit() {
  saving.value = true;
  error.value = null;
  try {
    await rejectAdvisoryVariant(props.runId, props.advisoryId, {
      reason_code: reasonCode.value,
      reason_detail: reasonDetail.value.trim() || null,
      operator_note: operatorNote.value.trim() || null,
    });
    open.value = false;
    reset();
    // Let parent refresh list (simple, predictable)
    emit("rejected");
  } catch (e: any) {
    error.value = e?.message ?? String(e);
  } finally {
    saving.value = false;
  }
}

function cancel() {
  open.value = false;
  reset();
}
</script>

<template>
  <button class="btn tiny danger" :disabled="disabled" @click="open = true">
    Reject
  </button>

  <Teleport to="body">
    <div v-if="open" class="modal" @click.self="cancel">
      <div class="card">
        <div class="title">Reject Variant</div>
        <div class="subtle mono">{{ advisoryId }}</div>

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
          <input
            v-model="reasonDetail"
            placeholder="Short detail for the rejection…"
            maxlength="500"
          />
        </label>

        <label class="ctl">
          <span>Operator note (optional)</span>
          <textarea
            v-model="operatorNote"
            placeholder="Longer note (what you saw, what to fix, etc.)"
            maxlength="2000"
          />
        </label>

        <div v-if="error" class="error">{{ error }}</div>

        <div class="row">
          <button class="btn tiny secondary" :disabled="saving" @click="cancel">
            Cancel
          </button>
          <button class="btn tiny danger" :disabled="!canSubmit" @click="submit">
            {{ saving ? "Rejecting…" : "Confirm Reject" }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.btn {
  padding: 8px 10px;
  border: 1px solid rgba(0, 0, 0, 0.2);
  border-radius: 10px;
  background: white;
  cursor: pointer;
}
.btn.tiny {
  padding: 4px 8px;
  font-size: 0.9em;
}
.btn.secondary {
  opacity: 0.85;
}
.btn.danger {
  border-color: rgba(176, 0, 32, 0.35);
  background: rgba(176, 0, 32, 0.06);
}
.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.modal {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  z-index: 1000;
}
.card {
  width: min(620px, 100%);
  background: white;
  border-radius: 14px;
  border: 1px solid rgba(0, 0, 0, 0.12);
  padding: 12px;
}
.title {
  font-weight: 900;
  font-size: 16px;
}
.subtle {
  opacity: 0.75;
  margin-bottom: 10px;
}
.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas,
    "Liberation Mono", "Courier New", monospace;
  font-size: 0.85em;
  word-break: break-all;
}

.ctl {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 10px;
  font-size: 12px;
}
.ctl select,
.ctl input,
.ctl textarea {
  border: 1px solid rgba(0, 0, 0, 0.18);
  border-radius: 10px;
  padding: 8px;
}
.ctl textarea {
  min-height: 90px;
  resize: vertical;
}

.row {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 12px;
}
.error {
  color: #b00020;
  margin-top: 8px;
  font-size: 0.9em;
}
</style>
