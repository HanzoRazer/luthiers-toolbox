<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import CandidateDecisionHistoryPopover from "@/components/rmos/CandidateDecisionHistoryPopover.vue";
import {
  decideManufacturingCandidate,
  downloadManufacturingCandidateZip,
  listManufacturingCandidates,
  type ManufacturingCandidate,
  type RiskLevel,
} from "@/sdk/rmos/runs";

const props = defineProps<{
  runId: string;
}>();

type CandidateRow = ManufacturingCandidate & {
  candidate_id: string;
};

const loading = ref(false);
const error = ref<string | null>(null);
const requestId = ref<string>("");

const candidates = ref<CandidateRow[]>([]);

// -------------------------
// Filters (product-only)
// -------------------------
type DecisionFilter = "ALL" | "UNDECIDED" | "GREEN" | "YELLOW" | "RED";
type StatusFilter = "ALL" | "PROPOSED" | "ACCEPTED" | "REJECTED";

const decisionFilter = ref<DecisionFilter>("ALL");
const statusFilter = ref<StatusFilter>("ALL");
const showSelectedOnly = ref(false);
const searchText = ref("");

// Save / decision state
const saving = ref(false);
const saveError = ref<string | null>(null);

// history popover (product-only)
const openHistoryFor = ref<string | null>(null);
function toggleHistory(id: string) { openHistoryFor.value = openHistoryFor.value === id ? null : id; }

// Inline note editor state
const editingId = ref<string | null>(null);
const editValue = ref<string>("");

// Bulk export state
const exporting = ref(false);
const exportError = ref<string | null>(null);

// Selection state (bulk decision)
const selectedIds = ref<Set<string>>(new Set());
const selectingAll = computed(() => candidates.value.length > 0 && selectedIds.value.size === candidates.value.length);

// Undo stack for bulk decisions (client-side)
type UndoItem = {
  ts_utc: string;
  run_id: string;
  label: string;
  applied_decision: RiskLevel;
  candidate_ids: string[];
  // snapshot needed to restore
  prev: Record<
    string,
    {
      decision: RiskLevel | null;
      decision_note: string | null;
    }
  >;
};
const undoStack = ref<UndoItem[]>([]);
const undoBusy = ref(false);
const undoError = ref<string | null>(null);

function decisionBadge(decision: RiskLevel | null | undefined) {
  if (decision == null) return "NEEDS_DECISION";
  return decision;
}

function normalize(s: unknown) {
  return String(s ?? "").trim().toLowerCase();
}

function matchesSearch(c: CandidateRow, q: string) {
  if (!q) return true;
  const hay = [
    c.candidate_id,
    c.advisory_id ?? "",
    c.decision_note ?? "",
    c.decided_by ?? "",
    c.created_by ?? "",
  ].map(normalize).join(" | ");
  return hay.includes(q);
}

function statusText(c: CandidateRow) {
  if (c.decision == null) return "Needs decision";
  if (c.decision === "GREEN") return "Accepted";
  if (c.decision === "YELLOW") return "Caution";
  if (c.decision === "RED") return "Rejected";
  return "—";
}

function notePreview(note?: string | null) {
  const n = note ?? "";
  if (!n) return "—";
  return n.length > 120 ? n.slice(0, 120) + "…" : n;
}

function auditHover(c: CandidateRow) {
  const who = c.decided_by ?? "—";
  const when = c.decided_at_utc ?? "—";
  const note = c.decision_note ?? "";
  const preview = note ? (note.length > 80 ? note.slice(0, 80) + "…" : note) : "—";

  const lines = [
    `Decision: ${decisionBadge(c.decision)}`,
    `By: ${who}`,
    `At: ${when}`,
    `Note: ${preview}`,
  ];

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
  exportError.value = null;
  undoError.value = null;
  try {
    const res = await listManufacturingCandidates(props.runId);
    candidates.value = (res.items ?? []) as CandidateRow[];
    requestId.value = res.requestId ?? "";
    // prune selection set to only existing candidates
    const existing = new Set(candidates.value.map((c) => c.candidate_id));
    const next = new Set<string>();
    for (const id of selectedIds.value) if (existing.has(id)) next.add(id);
    selectedIds.value = next;
    // If you were in "selected only" mode and selection got emptied, auto-disable it.
    if (showSelectedOnly.value && selectedIds.value.size === 0) showSelectedOnly.value = false;
  } catch (e: any) {
    error.value = e?.message ?? String(e);
  } finally {
    loading.value = false;
  }
}

onMounted(load);
watch(() => props.runId, load);

function startEdit(c: CandidateRow) {
  // Spine-locked: don't allow note editing until a decision exists
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
  if (c.decision == null) return;
  saving.value = true;
  saveError.value = null;
  try {
    const res = await decideManufacturingCandidate(props.runId, c.candidate_id, {
      decision: c.decision, // keep decision stable; update note only
      note: editValue.value,
      decided_by: null,
    });
    requestId.value = res.requestId ?? requestId.value;

    const idx = candidates.value.findIndex((x) => x.candidate_id === c.candidate_id);
    if (idx >= 0) {
      candidates.value[idx] = {
        ...candidates.value[idx],
        decision: (res.decision ?? candidates.value[idx].decision ?? null) as any,
        status: (res.status ?? candidates.value[idx].status ?? null) as any,
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
        decision: (res.decision ?? decision) as any,
        status: (res.status ?? candidates.value[idx].status ?? null) as any,
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

// -------------------------
// Bulk decision (GREEN/YELLOW/RED) with undo
// -------------------------
const selectedRows = computed(() => {
  const s = selectedIds.value;
  return candidates.value.filter((c) => s.has(c.candidate_id));
});

// micro-follow: bulk clear decision (set to null) for selected
// This aligns with migration: decision=null == NEEDS_DECISION
// Clears decision_note as well (note is tied to decision record).
// Uses decideManufacturingCandidate() only (runs.ts lockpoint).

function canBulkClearDecision(): { ok: boolean; reason?: string } {
  const sel = selectedRows.value;
  if (sel.length === 0) return { ok: false, reason: "Select candidates to clear decision." };
  // allow clearing any decided candidate; no-op if already undecided
  const anyDecided = sel.some((c) => c.decision !== null);
  if (!anyDecided) return { ok: false, reason: "All selected candidates are already undecided." };
  return { ok: true };
}

function bulkClearBlockedHover(): string {
  const chk = canBulkClearDecision();
  return chk.ok ? "Clear decision → NEEDS_DECISION (decision=null). Note cleared too." : (chk.reason ?? "Blocked");
}

// -------------------------
// Filtered view (product-only)
// -------------------------
const filteredCandidates = computed(() => {
  const df = decisionFilter.value;
  const sf = statusFilter.value;
  const onlySel = showSelectedOnly.value;
  const sel = selectedIds.value;
  const q = normalize(searchText.value);

  return candidates.value.filter((c) => {
    if (onlySel && !sel.has(c.candidate_id)) return false;

    // decision filter
    if (df === "UNDECIDED") {
      if (c.decision != null) return false;
    } else if (df === "GREEN" || df === "YELLOW" || df === "RED") {
      if (c.decision !== df) return false;
    }

    // status filter
    if (sf !== "ALL") {
      if ((c.status ?? null) !== sf) return false;
    }

    // search
    if (!matchesSearch(c, q)) return false;
    return true;
  });
});

const filteredCount = computed(() => filteredCandidates.value.length);

function quickUndecided() {
  decisionFilter.value = "UNDECIDED";
}

function clearFilters() {
  decisionFilter.value = "ALL";
  statusFilter.value = "ALL";
  showSelectedOnly.value = false;
  searchText.value = "";
}

function toggleOne(id: string) {
  const next = new Set(selectedIds.value);
  if (next.has(id)) next.delete(id);
  else next.add(id);
  selectedIds.value = next;
}

function toggleAll() {
  if (selectingAll.value) {
    selectedIds.value = new Set();
    return;
  }
  selectedIds.value = new Set(candidates.value.map((c) => c.candidate_id));
}

function utcNowIso() {
  return new Date().toISOString();
}

async function bulkSetDecision(decision: RiskLevel) {
  if (!props.runId) return;
  undoError.value = null;
  saveError.value = null;

  const rows = selectedRows.value;
  if (rows.length === 0) {
    undoError.value = "Select at least one candidate first.";
    return;
  }

  // Snapshot previous states (for undo)
  const prev: UndoItem["prev"] = {};
  for (const r of rows) {
    prev[r.candidate_id] = {
      decision: (r.decision ?? null) as any,
      decision_note: (r.decision_note ?? null) as any,
    };
  }

  saving.value = true;
  try {
    // Sequential, deterministic updates (keeps audit clean and avoids request bursts)
    for (const r of rows) {
      const res = await decideManufacturingCandidate(props.runId, r.candidate_id, {
        decision,
        note: r.decision_note ?? null,
        decided_by: null,
      });
      requestId.value = res.requestId ?? requestId.value;

      const idx = candidates.value.findIndex((x) => x.candidate_id === r.candidate_id);
      if (idx >= 0) {
        candidates.value[idx] = {
          ...candidates.value[idx],
          decision: (res.decision ?? decision) as any,
          status: (res.status ?? candidates.value[idx].status ?? null) as any,
          decision_note: res.decision_note ?? candidates.value[idx].decision_note ?? null,
          decided_at_utc: res.decided_at_utc ?? candidates.value[idx].decided_at_utc ?? null,
          decided_by: res.decided_by ?? candidates.value[idx].decided_by ?? null,
          decision_history: res.decision_history ?? candidates.value[idx].decision_history ?? null,
        };
      }
      await new Promise((rr) => setTimeout(rr, 40));
    }

    // push undo record
    undoStack.value.unshift({
      ts_utc: utcNowIso(),
      run_id: props.runId,
      label: `Bulk set ${rows.length} → ${decision}`,
      applied_decision: decision,
      candidate_ids: rows.map((x) => x.candidate_id),
      prev,
    });
    // keep stack small/high-signal
    if (undoStack.value.length > 20) undoStack.value = undoStack.value.slice(0, 20);
  } catch (e: any) {
    saveError.value = e?.message ?? String(e);
  } finally {
    saving.value = false;
  }
}

async function bulkClearDecision() {
  const chk = canBulkClearDecision();
  if (!chk.ok) return;

  saving.value = true;
  saveError.value = null;

  const sel = selectedRows.value;
  const nowIso = utcNowIso();

  // Snapshot "before" for undo per candidate that is changing
  const changed = sel.filter((c) => c.decision !== null);
  const prev: UndoItem["prev"] = {};
  for (const c of changed) {
    prev[c.candidate_id] = {
      decision: (c.decision ?? null) as any,
      decision_note: (c.decision_note ?? null) as any,
    };
  }

  try {
    for (const c of changed) {
      const res = await decideManufacturingCandidate(props.runId, c.candidate_id, {
        decision: null,
        note: null,
        decided_by: null,
      });
      requestId.value = res.requestId ?? requestId.value;

      // optimistic local update
      const idx = candidates.value.findIndex((x) => x.candidate_id === c.candidate_id);
      if (idx >= 0) {
        candidates.value[idx] = {
          ...candidates.value[idx],
          decision: (res.decision ?? null) as any,
          status: (res.status ?? candidates.value[idx].status ?? null) as any,
          decision_note: res.decision_note ?? null,
          decided_at_utc: res.decided_at_utc ?? null,
          decided_by: res.decided_by ?? null,
          decision_history: res.decision_history ?? candidates.value[idx].decision_history ?? null,
        };
      }
      await new Promise((rr) => setTimeout(rr, 40));
    }

    // push undo record
    undoStack.value.unshift({
      ts_utc: nowIso,
      run_id: props.runId,
      label: `Bulk clear ${changed.length} → NEEDS_DECISION`,
      applied_decision: null as any,
      candidate_ids: changed.map((x) => x.candidate_id),
      prev,
    });
    if (undoStack.value.length > 20) undoStack.value = undoStack.value.slice(0, 20);
  } catch (e: any) {
    saveError.value = e?.message ?? String(e);
  } finally {
    saving.value = false;
  }
}

async function undoLast() {
  if (!props.runId) return;
  if (undoStack.value.length === 0) return;
  undoBusy.value = true;
  undoError.value = null;

  const item = undoStack.value[0];
  try {
    for (const id of item.candidate_ids) {
      const snap = item.prev[id];
      if (!snap) continue;
      const res = await decideManufacturingCandidate(props.runId, id, {
        decision: snap.decision, // may be null (back to NEEDS_DECISION)
        note: snap.decision_note,
        decided_by: null,
      });
      requestId.value = res.requestId ?? requestId.value;

      const idx = candidates.value.findIndex((x) => x.candidate_id === id);
      if (idx >= 0) {
        candidates.value[idx] = {
          ...candidates.value[idx],
          decision: (res.decision ?? snap.decision ?? null) as any,
          status: (res.status ?? candidates.value[idx].status ?? null) as any,
          decision_note: res.decision_note ?? snap.decision_note ?? null,
          decided_at_utc: res.decided_at_utc ?? candidates.value[idx].decided_at_utc ?? null,
          decided_by: res.decided_by ?? candidates.value[idx].decided_by ?? null,
          decision_history: res.decision_history ?? candidates.value[idx].decision_history ?? null,
        };
      }
      await new Promise((rr) => setTimeout(rr, 40));
    }
    // pop after successful undo
    undoStack.value.shift();
  } catch (e: any) {
    undoError.value = e?.message ?? String(e);
  } finally {
    undoBusy.value = false;
  }
}

function undoStackHover(item: UndoItem) {
  const ids = item.candidate_ids.slice(0, 6).join(", ");
  const more = item.candidate_ids.length > 6 ? ` …(+${item.candidate_ids.length - 6})` : "";
  return [
    `When: ${item.ts_utc}`,
    `Run: ${item.run_id}`,
    `Action: ${item.label}`,
    `Candidates: ${ids}${more}`,
    `Undo applies previous decision + note (including null).`,
  ].join("\n");
}

// -------------------------
// Bulk export (GREEN-only)
// -------------------------
const undecidedCount = computed(() => candidates.value.filter((c) => c.decision == null).length);
const greenCandidates = computed(() => candidates.value.filter((c) => c.decision === "GREEN"));

const exportBlockedReason = computed(() => {
  if (candidates.value.length === 0) return "No candidates to export.";
  if (undecidedCount.value > 0) {
    return `Export blocked: ${undecidedCount.value} candidate(s) still NEED DECISION. Decide all candidates before exporting.`;
  }
  if (greenCandidates.value.length === 0) {
    return "Export blocked: there are no GREEN candidates to export.";
  }
  return null;
});

const canExportGreenOnly = computed(() => exportBlockedReason.value == null && !exporting.value);

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  // give the browser a beat before revoking
  setTimeout(() => URL.revokeObjectURL(url), 2500);
}

async function exportGreenOnlyZips() {
  if (!props.runId) return;
  exportError.value = null;

  const reason = exportBlockedReason.value;
  if (reason) {
    exportError.value = reason;
    return;
  }

  exporting.value = true;
  try {
    // Download each GREEN candidate zip. (Product-only: no server-side bundling.)
    for (const c of greenCandidates.value) {
      const res = await downloadManufacturingCandidateZip(props.runId, c.candidate_id);
      requestId.value = res.requestId ?? requestId.value;
      const fname = `rmos_${props.runId}_candidate_${c.candidate_id}_GREEN.zip`;
      downloadBlob(res.blob, fname);
      // small delay to avoid browser throttling
      await new Promise((r) => setTimeout(r, 250));
    }
  } catch (e: any) {
    exportError.value = e?.message ?? String(e);
  } finally {
    exporting.value = false;
  }
}
</script>

<template>
  <section class="rmos-candidates">
    <div class="header">
      <div class="title">
        <h3>Manufacturing Candidates</h3>
        <div class="subtitle muted">
          Decision is <span class="mono">null</span> until operator decides (spine-locked).
        </div>
      </div>
      <div class="meta">
        <span v-if="requestId" class="reqid" title="X-Request-Id">req: {{ requestId }}</span>
        <button class="btn" @click="load" :disabled="loading || exporting">Refresh</button>

        <!-- Bulk export (GREEN-only), blocked if any undecided -->
        <button
          class="btn"
          @click="exportGreenOnlyZips"
          :disabled="!canExportGreenOnly"
          :title="exportBlockedReason ?? 'Download zips for GREEN candidates only'"
        >
          {{ exporting ? "Exporting…" : "Export GREEN zips" }}
        </button>
      </div>
    </div>

    <p v-if="error" class="error">Error: {{ error }}</p>
    <p v-if="saveError" class="error">Save error: {{ saveError }}</p>
    <p v-if="exportError" class="error">Export: {{ exportError }}</p>
    <p v-if="undoError" class="error">Undo: {{ undoError }}</p>

    <p v-if="loading" class="muted">Loading candidates…</p>
    <p v-else-if="candidates.length === 0" class="muted">No candidates yet.</p>

    <div v-else class="table">
      <!-- Filters -->
      <div class="filters">
        <div class="filters-left">
          <div class="field">
            <label class="muted">Decision</label>
            <select v-model="decisionFilter" :disabled="saving || exporting || undoBusy">
              <option value="ALL">All</option>
              <option value="UNDECIDED">Undecided</option>
              <option value="GREEN">GREEN</option>
              <option value="YELLOW">YELLOW</option>
              <option value="RED">RED</option>
            </select>
          </div>

          <div class="field">
            <label class="muted">Status</label>
            <select v-model="statusFilter" :disabled="saving || exporting || undoBusy">
              <option value="ALL">All</option>
              <option value="PROPOSED">PROPOSED</option>
              <option value="ACCEPTED">ACCEPTED</option>
              <option value="REJECTED">REJECTED</option>
            </select>
          </div>

          <div class="field grow">
            <label class="muted">Search</label>
            <input
              v-model="searchText"
              type="text"
              placeholder="candidate id, advisory id, note, decided_by…"
              :disabled="saving || exporting || undoBusy"
            />
          </div>
        </div>

        <div class="filters-right">
          <label class="check">
            <input type="checkbox" v-model="showSelectedOnly" :disabled="saving || exporting || undoBusy || selectedIds.size === 0" />
            <span class="muted">Selected only</span>
          </label>

          <button class="btn ghost" @click="quickUndecided" :disabled="saving || exporting || undoBusy" title="Jump to undecided candidates">
            Undecided-only
          </button>
          <button class="btn ghost" @click="clearFilters" :disabled="saving || exporting || undoBusy" title="Clear all filters">
            Clear filters
          </button>

          <div class="muted small">
            Showing <strong>{{ filteredCount }}</strong> / {{ candidates.length }}
          </div>
        </div>
      </div>

      <div class="row head">
        <div class="sel">
          <input
            type="checkbox"
            :checked="selectingAll"
            @change="toggleAll"
            :disabled="saving || exporting || undoBusy"
            title="Select all"
          />
        </div>
        <div>Candidate</div>
        <div>Advisory</div>
        <div>Decision</div>
        <div>History</div>
        <div>Status</div>
        <div class="note">Decision Note</div>
        <div class="actions">Actions</div>
      </div>

      <!-- Bulk decision bar -->
      <div class="bulkbar" v-if="candidates.length > 0">
        <div class="bulk-left">
          <span class="muted">
            Selected: <strong>{{ selectedIds.size }}</strong>
          </span>
          <span class="muted" v-if="selectedIds.size === 0"> (select rows to bulk-set decision)</span>
        </div>
        <div class="bulk-actions">
          <button class="btn" @click="bulkSetDecision('GREEN')" :disabled="saving || exporting || undoBusy || selectedIds.size === 0" title="Set selected to GREEN">
            Bulk GREEN
          </button>
          <button class="btn" @click="bulkSetDecision('YELLOW')" :disabled="saving || exporting || undoBusy || selectedIds.size === 0" title="Set selected to YELLOW">
            Bulk YELLOW
          </button>
          <button class="btn danger" @click="bulkSetDecision('RED')" :disabled="saving || exporting || undoBusy || selectedIds.size === 0" title="Set selected to RED">
            Bulk RED
          </button>
          <button
            class="btn ghost"
            @click="bulkClearDecision"
            :disabled="saving || exporting || undoBusy || !canBulkClearDecision().ok"
            :title="bulkClearBlockedHover()"
          >
            Clear decision
          </button>
          <button
            class="btn ghost"
            @click="undoLast"
            :disabled="undoBusy || saving || exporting || undoStack.length === 0"
            :title="undoStack.length ? undoStackHover(undoStack[0]) : 'Nothing to undo'"
          >
            {{ undoBusy ? "Undoing…" : "Undo last" }}
          </button>
        </div>
      </div>

      <!-- Undo history display -->
      <div class="undolist" v-if="undoStack.length > 0">
        <div class="undotitle muted">Undo history (most recent first)</div>
        <div class="undoitem" v-for="(u, idx) in undoStack.slice(0, 5)" :key="u.ts_utc + ':' + idx" :title="undoStackHover(u)">
          <span class="mono">{{ u.ts_utc }}</span>
          <span>—</span>
          <span>{{ u.label }}</span>
        </div>
      </div>

      <div
        v-for="c in filteredCandidates"
        :key="c.candidate_id"
        class="row"
        :title="auditHover(c)"
      >
        <div class="sel">
          <input
            type="checkbox"
            :checked="selectedIds.has(c.candidate_id)"
            @change="toggleOne(c.candidate_id)"
            :disabled="saving || exporting || undoBusy"
            :title="selectedIds.has(c.candidate_id) ? 'Selected' : 'Select'"
          />
        </div>
        <div class="mono">{{ c.candidate_id }}</div>
        <div class="mono">{{ c.advisory_id ?? "—" }}</div>

        <div>
          <span class="badge" :data-badge="decisionBadge(c.decision)">
            {{ decisionBadge(c.decision) }}
          </span>
        </div>

        <div class="history">
          <button class="btn ghost smallbtn" @click="toggleHistory(c.candidate_id)" :disabled="saving || exporting || undoBusy">
            {{ openHistoryFor === c.candidate_id ? "Hide" : "View" }}
          </button>
          <div v-if="openHistoryFor === c.candidate_id" class="popover">
            <CandidateDecisionHistoryPopover
              :items="c.decision_history ?? null"
              :currentDecision="c.decision ?? null"
              :currentNote="c.decision_note ?? null"
              :currentBy="c.decided_by ?? null"
              :currentAt="c.decided_at_utc ?? null"
            />
          </div>
        </div>

        <div class="muted">{{ statusText(c) }}</div>

        <div class="note">
          <div v-if="editingId === c.candidate_id" class="editor">
            <textarea v-model="editValue" rows="2" />
            <div class="editor-actions">
              <button class="btn" @click="saveEdit(c)" :disabled="saving || exporting">Save</button>
              <button class="btn ghost" @click="cancelEdit" :disabled="saving || exporting">Cancel</button>
            </div>
          </div>
          <div v-else class="note-display">
            <span class="muted" v-if="!c.decision_note">—</span>
            <span v-else>{{ notePreview(c.decision_note) }}</span>
          </div>
        </div>

        <div class="actions">
          <button class="btn" @click="decide(c, 'GREEN')" :disabled="saving || exporting">GREEN</button>
          <button class="btn" @click="decide(c, 'YELLOW')" :disabled="saving || exporting">YELLOW</button>
          <button class="btn danger" @click="decide(c, 'RED')" :disabled="saving || exporting">RED</button>

          <button
            class="btn ghost"
            @click="startEdit(c)"
            :disabled="saving || exporting || c.decision == null"
            :title="c.decision == null ? 'Decide first to enable note editing' : 'Edit decision note'"
          >
            Edit Note
          </button>
        </div>
      </div>
    </div>

    <!-- Export policy explainers (visible, not just hover) -->
    <div class="policy muted" v-if="candidates.length > 0">
      <div><strong>Export policy:</strong></div>
      <ul>
        <li>Export is blocked while any candidate is <span class="mono">NEEDS_DECISION</span>.</li>
        <li>Export downloads zips for <strong>GREEN</strong> candidates only.</li>
        <li>Hover the export button to see the exact block reason.</li>
      </ul>
    </div>
  </section>
</template>

<style scoped>
.rmos-candidates { display: flex; flex-direction: column; gap: 10px; }
.header { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.title { display: flex; flex-direction: column; gap: 4px; }
.subtitle { font-size: 12px; }
.meta { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; justify-content: flex-end; }
.reqid { font-size: 12px; opacity: 0.75; }
.error { color: #b00020; }
.muted { opacity: 0.75; }
.small { font-size: 12px; }
.mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; font-size: 12px; }

.table { display: grid; gap: 6px; }
.row { display: grid; grid-template-columns: 34px 140px 1fr 140px 120px 140px 2fr 360px; gap: 10px; align-items: start; padding: 8px; border: 1px solid rgba(0,0,0,0.12); border-radius: 10px; position: relative; }
.row.head { font-weight: 600; background: rgba(0,0,0,0.04); }
.sel { display: flex; align-items: center; justify-content: center; padding-top: 2px; }

.filters { display: flex; gap: 10px; align-items: end; justify-content: space-between; padding: 8px; border: 1px solid rgba(0,0,0,0.10); border-radius: 10px; }
.filters-left { display: flex; gap: 10px; align-items: end; flex-wrap: wrap; flex: 1; }
.filters-right { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; justify-content: flex-end; }
.field { display: flex; flex-direction: column; gap: 4px; }
.field.grow { min-width: 280px; flex: 1; }
.field label { font-size: 12px; }
.field select, .field input { padding: 6px 10px; border: 1px solid rgba(0,0,0,0.16); border-radius: 10px; background: white; }
.check { display: inline-flex; gap: 6px; align-items: center; }

.actions { display: flex; flex-wrap: wrap; gap: 6px; }
.btn { padding: 6px 10px; border: 1px solid rgba(0,0,0,0.16); border-radius: 10px; background: white; cursor: pointer; }
.btn.ghost { background: transparent; }
.btn.danger { border-color: rgba(176,0,32,0.35); }
.smallbtn { padding: 4px 8px; font-size: 12px; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }

.badge { display: inline-flex; align-items: center; justify-content: center; padding: 2px 8px; border-radius: 999px; font-size: 12px; border: 1px solid rgba(0,0,0,0.14); }
.badge[data-badge="NEEDS_DECISION"] { opacity: 0.75; }

.note textarea { width: 100%; resize: vertical; padding: 6px; border-radius: 10px; border: 1px solid rgba(0,0,0,0.16); }
.editor-actions { display: flex; gap: 6px; margin-top: 6px; }

.bulkbar { display: flex; align-items: center; justify-content: space-between; gap: 10px; padding: 8px; border: 1px dashed rgba(0,0,0,0.18); border-radius: 10px; }
.bulk-actions { display: flex; gap: 6px; flex-wrap: wrap; justify-content: flex-end; }
.undolist { display: grid; gap: 4px; padding: 8px; border: 1px solid rgba(0,0,0,0.10); border-radius: 10px; }
.undotitle { font-size: 12px; }
.undoitem { display: flex; gap: 8px; align-items: center; font-size: 12px; }

.policy ul { margin: 6px 0 0 18px; }

.history { position: relative; }
.popover { position: absolute; z-index: 50; top: 30px; left: 0; }
</style>
