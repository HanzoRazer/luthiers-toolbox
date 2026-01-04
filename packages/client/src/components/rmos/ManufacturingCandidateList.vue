<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import {
  decideManufacturingCandidate,
  listManufacturingCandidates,
  type ManufacturingCandidate,
  type RiskLevel,
} from "@/sdk/rmos/runs";

const props = defineProps<{
  runId: string;
}>();

type CandidateRow = ManufacturingCandidate & {
  // normalize optional fields for UI convenience
  candidate_id: string;
};

const loading = ref(false);
const error = ref<string | null>(null);
const requestId = ref<string>("");

const candidates = ref<CandidateRow[]>([]);

// Inline editor state
const editingId = ref<string | null>(null);
const editValue = ref<string>("");
const saving = ref(false);
const saveError = ref<string | null>(null);

function decisionBadge(decision: RiskLevel | null | undefined) {
  if (decision == null) return "NEEDS_DECISION";
  return decision;
}

function statusText(c: CandidateRow) {
  // backend may provide status, but decision is authoritative for gating UX
  if (c.decision == null) return "Needs decision";
  if (c.decision === "GREEN") return "Accepted";
  if (c.decision === "YELLOW") return "Caution";
  if (c.decision === "RED") return "Rejected";
  return "—";
}

function auditHover(c: CandidateRow) {
  const who = c.decided_by ?? "—";
  const when = c.decided_at_utc ?? "—";
  const note = c.decision_note ?? "";
  const notePreview = note.length > 80 ? note.slice(0, 80) + "…" : note;
  const lines = [
    `Decision: ${decisionBadge(c.decision)}`,
    `By: ${who}`,
    `At: ${when}`,
    note ? `Note: ${notePreview}` : `Note: —`,
  ];

  // Include history if present (compact)
  if (c.decision_history && c.decision_history.length > 0) {
    const tail = c.decision_history
      .slice(-3)
      .map((h) => `${h.decision} · ${h.decided_by ?? "—"} · ${h.decided_at_utc ?? "—"}`)
      .join(" | ");
    lines.push(`History (last): ${tail}`);
  }
  return lines.join("\n");
}

async function load() {
  if (!props.runId) return;
  loading.value = true;
  error.value = null;
  try {
    const res = await listManufacturingCandidates(props.runId);
    candidates.value = (res.items ?? []) as CandidateRow[];
    requestId.value = res.requestId ?? "";
  } catch (e: any) {
    error.value = e?.message ?? String(e);
  } finally {
    loading.value = false;
  }
}

onMounted(load);
watch(() => props.runId, load);

function startEdit(c: CandidateRow) {
  // Only allow note editing if a decision exists.
  if (c.decision == null) return;
  editingId.value = c.candidate_id;
  editValue.value = c.decision_note ?? "";
  saveError.value = null;
}

function cancelEdit() {
  editingId.value = null;
  editValue.value = "";
  saveError.value = null;
}

async function saveEdit(c: CandidateRow) {
  if (!props.runId) return;
  if (c.decision == null) return; // spine-locked: cannot save note without decision
  saving.value = true;
  saveError.value = null;
  try {
    const res = await decideManufacturingCandidate(props.runId, c.candidate_id, {
      decision: c.decision, // keep decision stable; only update note
      note: editValue.value,
      decided_by: null,
    });
    requestId.value = res.requestId ?? requestId.value;

    // Update row in-place
    const idx = candidates.value.findIndex((x) => x.candidate_id === c.candidate_id);
    if (idx >= 0) {
      candidates.value[idx] = {
        ...candidates.value[idx],
        decision: res.decision ?? candidates.value[idx].decision ?? null,
        status: res.status ?? candidates.value[idx].status ?? null,
        decision_note: res.decision_note ?? editValue.value,
        decided_at_utc: res.decided_at_utc ?? candidates.value[idx].decided_at_utc ?? null,
        decided_by: res.decided_by ?? candidates.value[idx].decided_by ?? null,
        decision_history: res.decision_history ?? candidates.value[idx].decision_history ?? null,
      };
    }

    cancelEdit();
  } catch (e: any) {
    saveError.value = e?.message ?? String(e);
  } finally {
    saving.value = false;
  }
}

async function decide(c: CandidateRow, decision: RiskLevel) {
  if (!props.runId) return;
  saving.value = true;
  saveError.value = null;
  try {
    const res = await decideManufacturingCandidate(props.runId, c.candidate_id, {
      decision,
      note: c.decision_note ?? null,
      decided_by: null,
    });
    requestId.value = res.requestId ?? requestId.value;

    const idx = candidates.value.findIndex((x) => x.candidate_id === c.candidate_id);
    if (idx >= 0) {
      candidates.value[idx] = {
        ...candidates.value[idx],
        decision: res.decision ?? decision,
        status: res.status ?? candidates.value[idx].status ?? null,
        decision_note: res.decision_note ?? candidates.value[idx].decision_note ?? null,
        decided_at_utc: res.decided_at_utc ?? candidates.value[idx].decided_at_utc ?? null,
        decided_by: res.decided_by ?? candidates.value[idx].decided_by ?? null,
        decision_history: res.decision_history ?? candidates.value[idx].decision_history ?? null,
      };
    }
  } catch (e: any) {
    saveError.value = e?.message ?? String(e);
  } finally {
    saving.value = false;
  }
}

const hasAny = computed(() => candidates.value.length > 0);
</script>

<template>
  <section class="rmos-candidates">
    <div class="header">
      <h3>Manufacturing Candidates</h3>
      <div class="meta">
        <span v-if="requestId" class="reqid" title="X-Request-Id">req: {{ requestId }}</span>
        <button class="btn" @click="load" :disabled="loading">Refresh</button>
      </div>
    </div>

    <p v-if="error" class="error">Error: {{ error }}</p>
    <p v-if="saveError" class="error">Save error: {{ saveError }}</p>
    <p v-if="loading" class="muted">Loading candidates…</p>
    <p v-else-if="!hasAny" class="muted">No candidates yet.</p>

    <div v-else class="table">
      <div class="row head">
        <div>Candidate</div>
        <div>Advisory</div>
        <div>Decision</div>
        <div>Status</div>
        <div class="note">Decision Note</div>
        <div class="actions">Actions</div>
      </div>

      <div
        v-for="c in candidates"
        :key="c.candidate_id"
        class="row"
        :title="auditHover(c)"
      >
        <div class="mono">{{ c.candidate_id }}</div>
        <div class="mono">{{ c.advisory_id ?? "—" }}</div>
        <div>
          <span class="badge" :data-badge="decisionBadge(c.decision)">
            {{ decisionBadge(c.decision) }}
          </span>
        </div>
        <div class="muted">{{ statusText(c) }}</div>

        <div class="note">
          <!-- Inline note editor -->
          <div v-if="editingId === c.candidate_id" class="editor">
            <textarea v-model="editValue" rows="2" />
            <div class="editor-actions">
              <button class="btn" @click="saveEdit(c)" :disabled="saving">Save</button>
              <button class="btn ghost" @click="cancelEdit" :disabled="saving">Cancel</button>
            </div>
          </div>
          <div v-else class="note-display">
            <span class="muted" v-if="!c.decision_note">—</span>
            <span v-else>{{ c.decision_note }}</span>
          </div>
        </div>

        <div class="actions">
          <button class="btn" @click="decide(c, 'GREEN')" :disabled="saving">GREEN</button>
          <button class="btn" @click="decide(c, 'YELLOW')" :disabled="saving">YELLOW</button>
          <button class="btn danger" @click="decide(c, 'RED')" :disabled="saving">RED</button>

          <button
            class="btn ghost"
            @click="startEdit(c)"
            :disabled="saving || c.decision == null"
            :title="c.decision == null ? 'Decide first to enable note editing' : 'Edit decision note'"
          >
            Edit Note
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.rmos-candidates { display: flex; flex-direction: column; gap: 10px; }
.header { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.meta { display: flex; align-items: center; gap: 10px; }
.reqid { font-size: 12px; opacity: 0.75; }
.error { color: #b00020; }
.muted { opacity: 0.75; }
.mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; font-size: 12px; }
.table { display: grid; gap: 6px; }
.row { display: grid; grid-template-columns: 140px 1fr 120px 140px 2fr 360px; gap: 10px; align-items: start; padding: 8px; border: 1px solid rgba(0,0,0,0.12); border-radius: 10px; }
.row.head { font-weight: 600; background: rgba(0,0,0,0.04); }
.actions { display: flex; flex-wrap: wrap; gap: 6px; }
.btn { padding: 6px 10px; border: 1px solid rgba(0,0,0,0.16); border-radius: 10px; background: white; cursor: pointer; }
.btn.ghost { background: transparent; }
.btn.danger { border-color: rgba(176,0,32,0.35); }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.badge { display: inline-flex; align-items: center; justify-content: center; padding: 2px 8px; border-radius: 999px; font-size: 12px; border: 1px solid rgba(0,0,0,0.14); }
.badge[data-badge="NEEDS_DECISION"] { opacity: 0.75; }
.badge[data-badge="GREEN"] { }
.badge[data-badge="YELLOW"] { }
.badge[data-badge="RED"] { }
.note textarea { width: 100%; resize: vertical; padding: 6px; border-radius: 10px; border: 1px solid rgba(0,0,0,0.16); }
.editor-actions { display: flex; gap: 6px; margin-top: 6px; }
</style>
