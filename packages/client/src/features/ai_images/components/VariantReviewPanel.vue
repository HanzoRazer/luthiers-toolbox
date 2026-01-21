<script setup lang="ts">
import { computed, ref, watch } from "vue";
import {
  reviewAdvisoryVariant,
  type RejectReasonCode,
  type VariantStatus,
} from "@/sdk/rmos/runs";

type Props = {
  runId: string;
  advisoryId: string;

  // For display + defaults
  filename?: string | null;
  mime?: string | null;

  // Current server state (optional; used to prefill)
  initial?: {
    rejected?: boolean | null;
    rejection_reason_code?: RejectReasonCode | null;
    rejection_reason_detail?: string | null;
    rejection_operator_note?: string | null;
    rating?: number | null;
    notes?: string | null;
    status?: VariantStatus | null;
  } | null;
};

const props = defineProps<Props>();
const emit = defineEmits<{
  (e: "saved", payload: { advisoryId: string }): void;
  (e: "error", message: string): void;
}>();

const saving = ref(false);

// Local form state
const rejected = ref<boolean>(false);
const reasonCode = ref<RejectReasonCode | null>(null);
const reasonDetail = ref<string>("");
const operatorNote = ref<string>("");
const rating = ref<number | null>(null);
const notes = ref<string>("");

// Prefill from initial server state
watch(
  () => props.initial,
  (v) => {
    rejected.value = Boolean(v?.rejected ?? false);
    reasonCode.value = (v?.rejection_reason_code ?? null) as any;
    reasonDetail.value = v?.rejection_reason_detail ?? "";
    operatorNote.value = v?.rejection_operator_note ?? "";
    rating.value = typeof v?.rating === "number" ? v!.rating! : null;
    notes.value = v?.notes ?? "";
  },
  { immediate: true }
);

// Status rule: rejected -> REJECTED, else REVIEWED
const computedStatus = computed<VariantStatus>(() => {
  return rejected.value ? "REJECTED" : "REVIEWED";
});

const canSave = computed(() => {
  if (saving.value) return false;
  if (rejected.value) {
    // If rejected, we strongly prefer a reason code
    return reasonCode.value !== null;
  }
  return true;
});

const reasonOptions: Array<{ code: RejectReasonCode; label: string }> = [
  { code: "GEOMETRY_UNSAFE", label: "Geometry unsafe" },
  { code: "TEXT_REQUIRES_OUTLINE", label: "Text requires outline" },
  { code: "AESTHETIC", label: "Aesthetic" },
  { code: "DUPLICATE", label: "Duplicate" },
  { code: "OTHER", label: "Other" },
];

function _trimOrNull(s: string): string | null {
  const t = (s ?? "").trim();
  return t.length ? t : null;
}

async function save() {
  if (!canSave.value) {
    emit("error", rejected.value ? "Pick a rejection reason code." : "Unable to save right now.");
    return;
  }

  saving.value = true;
  try {
    const payload: any = {
      rejected: rejected.value,
      status: computedStatus.value,

      // Review fields
      rating: rating.value,
      notes: _trimOrNull(notes.value),

      // Reject fields (only meaningful if rejected=true)
      rejection_reason_code: rejected.value ? reasonCode.value : null,
      rejection_reason_detail: rejected.value ? _trimOrNull(reasonDetail.value) : null,
      rejection_operator_note: rejected.value ? _trimOrNull(operatorNote.value) : null,
    };

    // If un-rejecting, be explicit: clear reject fields
    if (!rejected.value) {
      payload.rejection_reason_code = null;
      payload.rejection_reason_detail = null;
      payload.rejection_operator_note = null;
    }

    await reviewAdvisoryVariant(props.runId, props.advisoryId, payload);
    emit("saved", { advisoryId: props.advisoryId });
  } catch (e: any) {
    emit("error", e?.message || "Failed to save review.");
  } finally {
    saving.value = false;
  }
}
</script>

<template>
  <div class="panel">
    <div class="hdr">
      <div class="title">
        Review
        <span
          v-if="filename || mime"
          class="meta"
        >
          · {{ filename || "variant" }} <span v-if="mime">({{ mime }})</span>
        </span>
      </div>
      <div
        class="statusPill"
        :data-status="computedStatus"
      >
        {{ computedStatus }}
      </div>
    </div>

    <div class="row">
      <label class="check">
        <input
          v-model="rejected"
          type="checkbox"
        >
        Reject
      </label>

      <div
        v-if="rejected"
        class="rejectBlock"
      >
        <label class="lbl">Reason code</label>
        <select
          v-model="reasonCode"
          class="sel"
        >
          <option :value="null">
            Select…
          </option>
          <option
            v-for="r in reasonOptions"
            :key="r.code"
            :value="r.code"
          >
            {{ r.label }}
          </option>
        </select>

        <label class="lbl">Reason detail (optional)</label>
        <input
          v-model="reasonDetail"
          class="inp"
          placeholder="Short detail…"
        >

        <label class="lbl">Operator note (optional)</label>
        <textarea
          v-model="operatorNote"
          class="ta"
          rows="2"
          placeholder="Internal note…"
        />
      </div>
    </div>

    <div class="row">
      <div class="col">
        <label class="lbl">Rating</label>
        <select
          v-model="rating"
          class="sel"
        >
          <option :value="null">
            —
          </option>
          <option :value="5">
            5
          </option>
          <option :value="4">
            4
          </option>
          <option :value="3">
            3
          </option>
          <option :value="2">
            2
          </option>
          <option :value="1">
            1
          </option>
        </select>
      </div>

      <div class="col grow">
        <label class="lbl">Notes</label>
        <input
          v-model="notes"
          class="inp"
          placeholder="Visible review note…"
        >
      </div>
    </div>

    <div class="actions">
      <button
        class="btn primary"
        :disabled="!canSave"
        @click="save"
      >
        {{ saving ? "Saving…" : "Save review" }}
      </button>
      <div
        v-if="rejected && reasonCode === null"
        class="hint"
      >
        Rejection requires a reason code.
      </div>
    </div>
  </div>
</template>

<style scoped>
.panel {
  border: 1px solid rgba(0,0,0,0.14);
  border-radius: 14px;
  padding: 12px;
  background: rgba(255,255,255,0.7);
}

.hdr {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 10px;
}

.title {
  font-weight: 600;
  font-size: 14px;
}

.meta {
  font-weight: 400;
  opacity: 0.7;
}

.statusPill {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid rgba(0,0,0,0.14);
  background: rgba(0,0,0,0.03);
}

.row {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  margin-top: 10px;
}

.col {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 120px;
}

.col.grow { flex: 1; }

.lbl {
  font-size: 12px;
  opacity: 0.75;
}

.sel, .inp, .ta {
  border: 1px solid rgba(0,0,0,0.18);
  border-radius: 10px;
  padding: 6px 10px;
  font-size: 13px;
  background: white;
}

.ta { resize: vertical; }

.check {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  user-select: none;
}

.rejectBlock {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr;
  gap: 6px;
  padding: 10px;
  border-radius: 12px;
  border: 1px dashed rgba(0,0,0,0.18);
  background: rgba(255, 240, 240, 0.6);
}

.actions {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 12px;
}

.btn {
  border: 1px solid rgba(0,0,0,0.18);
  border-radius: 12px;
  padding: 7px 12px;
  font-size: 13px;
  background: white;
  cursor: pointer;
}

.btn.primary {
  background: rgba(0,0,0,0.08);
  font-weight: 600;
}

.btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.hint {
  font-size: 12px;
  opacity: 0.75;
}
</style>
