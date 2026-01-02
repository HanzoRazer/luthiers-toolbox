<script setup lang="ts">
/**
 * ManufacturingCandidatesPanel.vue
 *
 * Panel for managing manufacturing candidates.
 * Features: triage UX, filters, search, bulk decisions, zip downloads.
 */
import { computed, nextTick, onMounted, ref, watch } from "vue";
import BulkDecisionModal from "@/components/rmos/BulkDecisionModal.vue";
import DisabledReasonWrap from "@/components/rmos/DisabledReasonWrap.vue";
import {
  fetchManufacturingCandidates,
  setManufacturingCandidateDecision,
  downloadManufacturingCandidateZip,
  saveBlobToDisk,
  type ManufacturingCandidate,
  type CandidateDecision,
} from "@/api/rmosRuns";

const props = defineProps<{
  runId: string;
  apiBase?: string;
}>();

const apiBase = computed(() => props.apiBase ?? "/api");

// Data state
const candidates = ref<ManufacturingCandidate[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);

// Filters
const q = ref("");
const filter = ref<"ALL" | "NEEDS_DECISION" | "APPROVED" | "REJECTED">("ALL");
const sort = ref<"SCORE_DESC" | "NEWEST">("SCORE_DESC");

// Multi-select state
const selectedCandidateIds = ref<Set<string>>(new Set());
const bulkBusy = ref(false);
const bulkError = ref<string | null>(null);
const bulkDecisionOpen = ref(false);

// Per-row busy state
const rowBusy = ref<Record<string, boolean>>({});

// Inline note editor state
const noteEditFor = ref<string | null>(null);
const noteDraft = ref("");
const noteBusy = ref<Record<string, boolean>>({});
const noteError = ref<Record<string, string | null>>({});

function idOf(c: ManufacturingCandidate): string {
  return String(c.candidate_id ?? (c as any).id ?? "");
}

function decisionOf(c: ManufacturingCandidate): CandidateDecision | null {
  // Handle different backend field names
  const d = c.decision ?? null;
  if (d) return d;
  // Map legacy status to decision
  const status = c.status;
  if (status === "ACCEPTED") return "GREEN";
  if (status === "REJECTED") return "RED";
  return null;
}

function isSelectedCandidate(id: string) {
  return selectedCandidateIds.value.has(id);
}

function toggleSelectedCandidate(id: string) {
  const s = new Set(selectedCandidateIds.value);
  if (s.has(id)) s.delete(id);
  else s.add(id);
  selectedCandidateIds.value = s;
}

function clearCandidateSelection() {
  selectedCandidateIds.value = new Set();
}

// Bundle 13: Auto-prune selection to GREEN after decision changes
function pruneSelectionToGreen() {
  if (selectedCandidateIds.value.size === 0) return;

  const keep = new Set<string>();
  for (const c of candidates.value) {
    const id = idOf(c);
    if (!selectedCandidateIds.value.has(id)) continue;
    if (decisionOf(c) === "GREEN") keep.add(id);
  }
  selectedCandidateIds.value = keep;
}

const selectedCount = computed(() => selectedCandidateIds.value.size);
const selectedIds = computed(() => Array.from(selectedCandidateIds.value));

// Bundle 11: Bulk download eligibility (GREEN-only gate)
const selectedCandidates = computed(() => {
  const selected = new Set(selectedCandidateIds.value);
  return candidates.value.filter((c) => selected.has(idOf(c)));
});

const bulkDownloadEligibility = computed(() => {
  const items = selectedCandidates.value;

  if (bulkBusy.value) {
    return { allowed: false, reason: "Download in progress…" };
  }

  if (!items.length) {
    return { allowed: false, reason: "Select one or more candidates to download." };
  }

  let undecided = 0;
  let yellow = 0;
  let red = 0;
  let green = 0;

  for (const c of items) {
    const d = decisionOf(c);
    if (d === null) undecided++;
    else if (d === "GREEN") green++;
    else if (d === "YELLOW") yellow++;
    else if (d === "RED") red++;
  }

  // Policy: bulk download only when ALL selected are GREEN
  const allowed = undecided === 0 && yellow === 0 && red === 0 && green === items.length;

  if (allowed) {
    return { allowed: true, reason: "Ready: all selected candidates are GREEN." };
  }

  const parts: string[] = ["Bulk download blocked: only GREEN candidates can be downloaded in bulk."];
  if (undecided) parts.push(`${undecided} undecided`);
  if (yellow) parts.push(`${yellow} YELLOW`);
  if (red) parts.push(`${red} RED`);
  parts.push("Fix: mark remaining selections GREEN (or deselect them).");

  return { allowed: false, reason: parts.join(" • ") };
});

const canBulkDownload = computed(() => bulkDownloadEligibility.value.allowed);
const bulkDownloadBlockedReason = computed(() => bulkDownloadEligibility.value.reason);

// Bundle 12: GREEN-only selection helpers
const allGreenCandidateIds = computed(() => {
  return candidates.value
    .filter((c) => decisionOf(c) === "GREEN")
    .map((c) => idOf(c));
});

const selectedGreenCandidateIds = computed(() => {
  const selected = selectedCandidateIds.value; // Set<string>
  return candidates.value
    .filter((c) => selected.has(idOf(c)) && decisionOf(c) === "GREEN")
    .map((c) => idOf(c));
});

function selectGreenOnly() {
  // If there is an active selection, keep only GREEN within it.
  // If nothing selected, select ALL GREEN candidates.
  const nextIds =
    selectedCandidateIds.value.size > 0
      ? selectedGreenCandidateIds.value
      : allGreenCandidateIds.value;

  selectedCandidateIds.value = new Set(nextIds);
}

// Filtering + sorting
const filteredSorted = computed(() => {
  const needle = q.value.trim().toLowerCase();
  let rows = candidates.value.slice();

  // Search filter
  if (needle) {
    rows = rows.filter((c) => idOf(c).toLowerCase().includes(needle));
  }

  // Status filter
  if (filter.value === "NEEDS_DECISION") {
    rows = rows.filter((c) => !decisionOf(c));
  } else if (filter.value === "APPROVED") {
    rows = rows.filter((c) => decisionOf(c) === "GREEN");
  } else if (filter.value === "REJECTED") {
    rows = rows.filter((c) => decisionOf(c) === "RED");
  }

  // Sort
  if (sort.value === "SCORE_DESC") {
    rows.sort((a, b) => (Number(b.score ?? -1) - Number(a.score ?? -1)));
  } else {
    rows.sort((a, b) => String(b.created_at_utc ?? "").localeCompare(String(a.created_at_utc ?? "")));
  }

  return rows;
});

function selectAllVisible() {
  const s = new Set(selectedCandidateIds.value);
  for (const c of filteredSorted.value) s.add(idOf(c));
  selectedCandidateIds.value = s;
}

async function load() {
  if (!props.runId) return;
  loading.value = true;
  error.value = null;
  try {
    const rows = await fetchManufacturingCandidates(apiBase.value, props.runId);
    candidates.value = rows ?? [];
    // Bundle 13: Prune selection to GREEN + known IDs
    if (selectedCandidateIds.value.size > 0) {
      pruneSelectionToGreen();
    }
  } catch (e: any) {
    error.value = e?.message ?? String(e);
    candidates.value = [];
    clearCandidateSelection();
  } finally {
    loading.value = false;
  }
}

// Per-row quick decision
async function setDecision(id: string, decision: CandidateDecision) {
  rowBusy.value = { ...rowBusy.value, [id]: true };
  error.value = null;
  try {
    await setManufacturingCandidateDecision(apiBase.value, props.runId, id, { decision, note: null });
    await load();
  } catch (e: any) {
    error.value = e?.message ?? String(e);
  } finally {
    rowBusy.value = { ...rowBusy.value, [id]: false };
  }
}

// Download single zip
async function downloadZip(id: string) {
  try {
    const blob = await downloadManufacturingCandidateZip(apiBase.value, props.runId, id);
    saveBlobToDisk(blob, `run_${props.runId}__candidate_${id}.zip`);
  } catch (e: any) {
    error.value = e?.message ?? String(e);
  }
}

// Bulk download zips
async function downloadSelectedCandidateZips() {
  if (!canBulkDownload.value) return; // Bundle 11: safety guard
  bulkError.value = null;
  const ids = Array.from(selectedCandidateIds.value);
  if (!ids.length) return;

  bulkBusy.value = true;
  try {
    for (const candidateId of ids) {
      const blob = await downloadManufacturingCandidateZip(apiBase.value, props.runId, candidateId);
      saveBlobToDisk(blob, `run_${props.runId}__candidate_${candidateId}.zip`);
    }
  } catch (e: any) {
    bulkError.value = e?.message ?? String(e);
  } finally {
    bulkBusy.value = false;
  }
}

// Bundle 13: Clean handler for BulkDecisionModal @done
async function onBulkDecisionDone() {
  bulkDecisionOpen.value = false;
  await load(); // load() prunes to GREEN-only
}

function statusClass(decision: CandidateDecision | null): string {
  if (decision === "GREEN") return "green";
  if (decision === "YELLOW") return "yellow";
  if (decision === "RED") return "red";
  return "none";
}

// --- Audit hover helpers ---
function fmtUtc(s?: string | null): string {
  if (!s) return "—";
  return s;
}

function lastDecisionRecord(c: ManufacturingCandidate) {
  const hist = (c as any).decision_history as any[] | null | undefined;
  if (hist && hist.length) {
    return hist[hist.length - 1];
  }
  if (c.decision || c.decision_note || c.decided_at_utc || (c as any).decided_by) {
    return {
      decision: c.decision,
      note: c.decision_note,
      decided_at_utc: c.decided_at_utc,
      decided_by: (c as any).decided_by,
    };
  }
  return null;
}

function auditHoverText(c: ManufacturingCandidate): string {
  const rec = lastDecisionRecord(c);
  if (!rec) return "No decision yet";

  const lines: string[] = [];
  lines.push(`Decision: ${rec.decision ?? "—"}`);
  if (rec.decided_by) lines.push(`By: ${rec.decided_by}`);
  if (rec.decided_at_utc) lines.push(`At: ${rec.decided_at_utc}`);
  if (rec.note) lines.push(`Note: ${rec.note}`);
  return lines.join("\n");
}

function compactDecisionLine(c: ManufacturingCandidate): string | null {
  const rec = lastDecisionRecord(c);
  if (!rec || (!rec.decision && !rec.decided_at_utc && !rec.decided_by && !rec.note)) return null;

  const bits: string[] = [];
  if (rec.decision) bits.push(String(rec.decision));
  if (rec.decided_by) bits.push(String(rec.decided_by));
  if (rec.decided_at_utc) bits.push(String(rec.decided_at_utc));
  if (rec.note) bits.push(`"${String(rec.note)}"`);
  return bits.join(" • ");
}

// --- Inline note editor helpers ---
function openNoteEditor(c: ManufacturingCandidate) {
  const id = idOf(c);
  noteEditFor.value = id;

  // Seed draft from last decision record (history-aware)
  const rec = lastDecisionRecord(c) as any;
  noteDraft.value = String(rec?.note ?? c.decision_note ?? "").trim();

  noteError.value = { ...noteError.value, [id]: null };

  // Focus textarea next tick
  nextTick(() => {
    const el = document.getElementById(`note-editor-${id}`) as HTMLTextAreaElement | null;
    el?.focus();
    el?.setSelectionRange(el.value.length, el.value.length);
  });
}

function closeNoteEditor() {
  noteEditFor.value = null;
  noteDraft.value = "";
}

function currentDecisionFor(c: ManufacturingCandidate): "GREEN" | "YELLOW" | "RED" {
  // We must send a decision with the note update.
  // If no decision exists yet, default to YELLOW (caution) rather than GREEN.
  const d = (decisionOf(c) ?? c.decision ?? null) as any;
  if (d === "GREEN" || d === "YELLOW" || d === "RED") return d;
  return "YELLOW";
}

async function saveNote(c: ManufacturingCandidate) {
  const id = idOf(c);
  const decision = currentDecisionFor(c);
  const note = noteDraft.value.trim();
  const payloadNote = note.length ? note : null;

  noteBusy.value = { ...noteBusy.value, [id]: true };
  noteError.value = { ...noteError.value, [id]: null };

  try {
    await setManufacturingCandidateDecision(apiBase.value, props.runId, id, {
      decision,
      note: payloadNote,
    });

    // Reload to reflect decided_at_utc / decided_by / history
    await load();
    closeNoteEditor();
  } catch (e: any) {
    noteError.value = { ...noteError.value, [id]: e?.message ?? String(e) };
  } finally {
    noteBusy.value = { ...noteBusy.value, [id]: false };
  }
}

onMounted(load);
watch(() => props.runId, () => { clearCandidateSelection(); load(); });
</script>

<template>
  <div class="manufacturing-panel">
    <div class="panel-header">
      <div>
        <h3 class="title">Manufacturing Candidates</h3>
        <p class="subtitle">Review candidates: quick Green/Yellow/Red decisions or bulk actions.</p>
      </div>
      <button class="btn btn-secondary" @click="load" :disabled="loading">
        {{ loading ? "Loading..." : "Refresh" }}
      </button>
    </div>

    <!-- Toolbar: search + filter + sort -->
    <div class="toolbar">
      <input
        v-model="q"
        type="text"
        class="search-input"
        placeholder="🔍 Search by candidate ID..."
      />

      <select v-model="filter" class="filter-select">
        <option value="ALL">All</option>
        <option value="NEEDS_DECISION">Needs decision</option>
        <option value="APPROVED">Approved</option>
        <option value="REJECTED">Rejected</option>
      </select>

      <select v-model="sort" class="sort-select">
        <option value="SCORE_DESC">Score ↓</option>
        <option value="NEWEST">Newest first</option>
      </select>
    </div>

    <div v-if="error" class="error-banner">
      {{ error }}
      <button @click="error = null">&times;</button>
    </div>

    <div v-if="loading && !candidates.length" class="loading">Loading candidates...</div>
    <div v-else-if="!candidates.length" class="empty">No manufacturing candidates yet.</div>

    <!-- Bulk action bar -->
    <div class="bulk-bar" v-if="candidates.length > 0">
      <div class="bulk-left">
        <strong>{{ selectedCount }}</strong> selected
        <span class="subtle" v-if="filteredSorted.length !== candidates.length">
          ({{ filteredSorted.length }} visible)
        </span>
      </div>
      <div class="bulk-right">
        <button class="btn btn-secondary btn-sm" :disabled="bulkBusy" @click="selectAllVisible">
          Select visible
        </button>
        <button class="btn btn-secondary btn-sm" :disabled="bulkBusy || !selectedCount" @click="clearCandidateSelection">
          Clear
        </button>
        <button
          class="btn btn-primary btn-sm"
          :disabled="bulkBusy || !selectedCount"
          @click="bulkDecisionOpen = true"
        >
          Bulk decision…
        </button>
        <!-- Bundle 12: Select GREEN only quick action -->
        <button
          class="btn btn-secondary btn-sm"
          type="button"
          :disabled="bulkBusy || candidates.length === 0"
          title="Keep only GREEN candidates selected (or select all GREEN if none selected)"
          @click="selectGreenOnly"
        >
          Select GREEN only
        </button>
        <!-- Bundle 11: Bulk download gated to GREEN-only with hover reason -->
        <DisabledReasonWrap
          v-if="!canBulkDownload"
          :reason="bulkDownloadBlockedReason"
        >
          <button class="btn btn-secondary btn-sm" type="button" disabled>
            {{ bulkBusy ? "Downloading…" : "Download zips" }}
          </button>
        </DisabledReasonWrap>
        <button
          v-else
          class="btn btn-secondary btn-sm"
          type="button"
          :disabled="bulkBusy"
          @click="downloadSelectedCandidateZips"
        >
          {{ bulkBusy ? "Downloading…" : "Download zips" }}
        </button>
      </div>
    </div>

    <div v-if="bulkError" class="error-banner">
      {{ bulkError }}
      <button @click="bulkError = null">&times;</button>
    </div>

    <!-- Candidate list -->
    <div class="candidate-list" v-if="filteredSorted.length > 0">
      <div
        v-for="c in filteredSorted"
        :key="idOf(c)"
        class="candidate-row"
        :class="{ selected: isSelectedCandidate(idOf(c)) }"
        :title="auditHoverText(c)"
      >
        <div class="row-select" @click.stop="toggleSelectedCandidate(idOf(c))">
          <input type="checkbox" :checked="isSelectedCandidate(idOf(c))" />
        </div>

        <div class="row-main">
          <div class="row-identity">
            <div class="id-block">
              <code class="candidate-id">{{ idOf(c) }}</code>
              <!-- Audit / Note line (click to edit) -->
              <div
                v-if="compactDecisionLine(c) && noteEditFor !== idOf(c)"
                class="audit-line clickable"
                @click.stop="openNoteEditor(c)"
                title="Click to edit decision note"
              >
                {{ compactDecisionLine(c) }}
              </div>
              <!-- No decision line yet: show placeholder -->
              <div
                v-else-if="noteEditFor !== idOf(c)"
                class="audit-line clickable subtle"
                @click.stop="openNoteEditor(c)"
                title="Click to add a decision note"
              >
                + Add decision note…
              </div>

              <!-- Inline note editor -->
              <div v-if="noteEditFor === idOf(c)" class="note-editor" @click.stop>
                <div class="note-title">Edit decision note</div>

                <textarea
                  class="note-textarea"
                  :id="`note-editor-${idOf(c)}`"
                  v-model="noteDraft"
                  placeholder="Add a note… (e.g., 'tool clearance concern near inner ring')"
                  @keydown.esc="closeNoteEditor"
                ></textarea>

                <div v-if="noteError[idOf(c)]" class="note-error">{{ noteError[idOf(c)] }}</div>

                <div class="note-actions">
                  <button class="btn btn-sm btn-secondary" :disabled="noteBusy[idOf(c)]" @click="closeNoteEditor">
                    Cancel
                  </button>
                  <button class="btn btn-sm btn-primary" :disabled="noteBusy[idOf(c)]" @click="saveNote(c)">
                    {{ noteBusy[idOf(c)] ? "Saving…" : "Save note" }}
                  </button>
                </div>

                <div class="note-hint subtle">
                  Decision is preserved as <strong>{{ currentDecisionFor(c) }}</strong>.
                  <span v-if="!decisionOf(c)">If no decision existed, note-save will set decision to <strong>YELLOW</strong> (caution).</span>
                </div>
              </div>
            </div>
            <span class="decision-badge" :class="statusClass(decisionOf(c))">
              {{ decisionOf(c) ?? "—" }}
            </span>
            <span class="score-label" v-if="c.score != null">Score: {{ c.score }}</span>
          </div>
          <div class="row-meta subtle">
            <span v-if="c.advisory_id">advisory: {{ String(c.advisory_id).slice(0, 10) }}…</span>
            <span v-if="c.created_at_utc">created: {{ fmtUtc(c.created_at_utc) }}</span>
          </div>
        </div>

        <!-- Quick decision buttons -->
        <div class="row-actions">
          <button
            class="quick-btn green"
            :disabled="rowBusy[idOf(c)]"
            title="Approve (GREEN)"
            @click="setDecision(idOf(c), 'GREEN')"
          >✓</button>
          <button
            class="quick-btn yellow"
            :disabled="rowBusy[idOf(c)]"
            title="Caution (YELLOW)"
            @click="setDecision(idOf(c), 'YELLOW')"
          >⚠</button>
          <button
            class="quick-btn red"
            :disabled="rowBusy[idOf(c)]"
            title="Reject (RED)"
            @click="setDecision(idOf(c), 'RED')"
          >✗</button>
          <button
            class="btn btn-sm btn-secondary"
            title="Download ZIP"
            @click="downloadZip(idOf(c))"
          >📦</button>
        </div>
      </div>
    </div>
    <div v-else-if="candidates.length > 0 && filteredSorted.length === 0" class="empty">
      No candidates match current filters.
    </div>

    <!-- Bulk decision modal -->
    <BulkDecisionModal
      :open="bulkDecisionOpen"
      :candidateIds="selectedIds"
      :runId="runId"
      :apiBase="apiBase"
      @close="bulkDecisionOpen = false"
      @done="onBulkDecisionDone"
    />
  </div>
</template>

<style scoped>
.manufacturing-panel {
  border: 1px solid #dee2e6;
  border-radius: 12px;
  background: #fff;
  overflow: hidden;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 1rem;
  background: #f8f9fa;
  border-bottom: 1px solid #dee2e6;
}

.title {
  margin: 0 0 0.25rem 0;
  font-size: 1.1rem;
  font-weight: 600;
}

.subtitle {
  margin: 0;
  font-size: 0.85rem;
  color: #6c757d;
}

/* Toolbar */
.toolbar {
  display: flex;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  background: #fafbfc;
  border-bottom: 1px solid #dee2e6;
  flex-wrap: wrap;
}

.search-input {
  flex: 1;
  min-width: 180px;
  padding: 0.45rem 0.65rem;
  border: 1px solid #ced4da;
  border-radius: 6px;
  font-size: 0.9rem;
}

.search-input:focus {
  outline: none;
  border-color: #0066cc;
  box-shadow: 0 0 0 2px rgba(0, 102, 204, 0.15);
}

.filter-select,
.sort-select {
  padding: 0.45rem 0.65rem;
  border: 1px solid #ced4da;
  border-radius: 6px;
  font-size: 0.9rem;
  background: #fff;
}

.error-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background: #f8d7da;
  color: #721c24;
  border-bottom: 1px solid #f5c6cb;
}

.error-banner button {
  background: none;
  border: none;
  font-size: 1.25rem;
  cursor: pointer;
  color: inherit;
}

.loading,
.empty {
  padding: 2rem;
  text-align: center;
  color: #6c757d;
}

/* Bulk bar */
.bulk-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #dee2e6;
  background: #f8f9fa;
}

.bulk-left {
  font-size: 0.9rem;
}

.bulk-right {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  justify-content: flex-end;
}

/* List view */
.candidate-list {
  display: flex;
  flex-direction: column;
}

.candidate-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #f0f0f0;
}

.candidate-row:hover {
  background: #fafbfc;
}

.candidate-row.selected {
  background: rgba(0, 102, 204, 0.05);
}

.row-select {
  cursor: pointer;
}

.row-select input {
  cursor: pointer;
  width: 16px;
  height: 16px;
}

.row-main {
  flex: 1;
  min-width: 0;
}

.row-identity {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.row-meta {
  font-size: 0.75rem;
  margin-top: 0.2rem;
}

.row-meta span {
  margin-right: 0.75rem;
}

.candidate-id {
  font-size: 0.8rem;
  background: #e9ecef;
  padding: 0.15rem 0.4rem;
  border-radius: 4px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

.decision-badge {
  font-size: 0.7rem;
  padding: 0.15rem 0.4rem;
  border-radius: 4px;
  font-weight: 600;
  text-transform: uppercase;
}

.decision-badge.green {
  background: #d4edda;
  color: #155724;
}

.decision-badge.yellow {
  background: #fff3cd;
  color: #856404;
}

.decision-badge.red {
  background: #f8d7da;
  color: #721c24;
}

.decision-badge.none {
  background: #e9ecef;
  color: #6c757d;
}

.score-label {
  font-size: 0.75rem;
  color: #6c757d;
}

/* Row actions */
.row-actions {
  display: flex;
  gap: 0.35rem;
  flex-shrink: 0;
}

.quick-btn {
  width: 32px;
  height: 32px;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  font-size: 1rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  transition: background 0.15s;
}

.quick-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.quick-btn.green:hover:not(:disabled) {
  background: #d4edda;
  border-color: #28a745;
}

.quick-btn.yellow:hover:not(:disabled) {
  background: #fff3cd;
  border-color: #ffc107;
}

.quick-btn.red:hover:not(:disabled) {
  background: #f8d7da;
  border-color: #dc3545;
}

/* Buttons */
.btn {
  padding: 0.4rem 0.75rem;
  font-size: 0.85rem;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
}

.btn:hover:not(:disabled) {
  background: #e9ecef;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-sm {
  padding: 0.3rem 0.6rem;
  font-size: 0.8rem;
}

.btn-secondary {
  opacity: 0.85;
}

.btn-primary {
  background: #0066cc;
  border-color: #0066cc;
  color: #fff;
}

.btn-primary:hover:not(:disabled) {
  background: #0056b3;
}

.subtle {
  color: #6c757d;
  opacity: 0.85;
}

/* Audit line (decision history) */
.id-block {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.audit-line {
  font-size: 0.7rem;
  color: #6c757d;
  opacity: 0.85;
  line-height: 1.2;
  max-width: 400px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.audit-line.clickable {
  cursor: pointer;
  border-radius: 3px;
  padding: 1px 4px;
  margin-left: -4px;
}

.audit-line.clickable:hover {
  background: rgba(0, 102, 204, 0.08);
  color: #0056b3;
}

.audit-line.placeholder {
  font-style: italic;
  opacity: 0.6;
}

/* Inline note editor */
.note-editor {
  margin-top: 8px;
  padding: 10px;
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 12px;
  background: rgba(0, 0, 0, 0.02);
}

.note-title {
  font-weight: 600;
  font-size: 0.75rem;
  margin-bottom: 6px;
}

.note-textarea {
  width: 100%;
  min-height: 80px;
  border: 1px solid rgba(0, 0, 0, 0.18);
  border-radius: 8px;
  padding: 8px;
  font-size: 0.8rem;
  font-family: inherit;
  background: #fff;
  resize: vertical;
}

.note-textarea:focus {
  outline: none;
  border-color: #0066cc;
  box-shadow: 0 0 0 2px rgba(0, 102, 204, 0.15);
}

.note-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 8px;
}

.note-error {
  color: #b00020;
  margin-top: 6px;
  font-size: 0.75rem;
}

.note-hint {
  margin-top: 6px;
  font-size: 0.7rem;
}

code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.85em;
}
</style>
