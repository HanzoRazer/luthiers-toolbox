<script setup lang="ts">
import CandidateDecisionHistoryPopover from "@/components/rmos/CandidateDecisionHistoryPopover.vue";
import CandidateRowItem from "@/components/rmos/CandidateRowItem.vue";
import CandidateFiltersSection from "@/components/rmos/CandidateFiltersSection.vue";
import BulkDecisionBar from "@/components/rmos/BulkDecisionBar.vue";
import BulkDecisionControlsV2 from "@/components/rmos/BulkDecisionControlsV2.vue";
import BulkHistoryPanel, { type BulkHistoryRecord } from "@/components/rmos/BulkHistoryPanel.vue";
import UndoHistoryPanel from "@/components/rmos/UndoHistoryPanel.vue";
import ExportPolicyCard from "@/components/rmos/ExportPolicyCard.vue";
import ManufacturingSummaryBar from "@/components/rmos/ManufacturingSummaryBar.vue";
import { computed, onMounted, ref, watch } from "vue";
import {
  decideManufacturingCandidate,
  listManufacturingCandidates,
  type ManufacturingCandidate,
  type RiskLevel,
} from "@/sdk/rmos/runs";
import { useCandidateSelection } from "./composables/useCandidateSelection";
import { useCandidateFilters, type DecisionFilter, type StatusFilter } from "./composables/useCandidateFilters";
import { useBulkExport } from "./composables/useBulkExport";
import { useBulkDecisionV2 } from "./composables/useBulkDecisionV2";
import { useUndoStack, type CandidateRow } from "./composables/useUndoStack";
import { useCandidateKeyboard, getHotkeyHelp } from "./composables/useCandidateKeyboard";
import { useClipboardToast } from "./composables/useClipboardToast";
import { useCandidateHelpers } from "./composables/useCandidateHelpers";

const props = defineProps<{
  runId: string;
  /** Optional: parent-supplied operator identity (overrides localStorage) */
  currentOperator?: string | null;
}>();

const loading = ref(false);
const error = ref<string | null>(null);
const requestId = ref<string>("");

const candidates = ref<CandidateRow[]>([]);

// -----------------------------------------------------------------------------
// Product micro-follow: "Show only my decisions"
// -----------------------------------------------------------------------------
const OPERATOR_ID_KEY = "rmos.operator_id";
const myOperatorId = ref<string>("");
try {
  myOperatorId.value = String(localStorage.getItem(OPERATOR_ID_KEY) || "");
} catch { }
watch(myOperatorId, (v) => {
  try {
    localStorage.setItem(OPERATOR_ID_KEY, String(v || ""));
  } catch { }
});

// Effective operator: prop overrides localStorage
const effectiveOperatorId = computed(() => {
  const fromProp = (props.currentOperator ?? "").trim();
  if (fromProp) return fromProp;
  return (myOperatorId.value || "").trim();
});

// Stamp decided_by on save/bulk
const stampDecisionsWithOperator = ref<boolean>(true);
function _decidedByOrNull(): string | null {
  if (!stampDecisionsWithOperator.value) return null;
  const v = effectiveOperatorId.value;
  return v ? v : null;
}

// Toast/clipboard composable
const { toast, showToast, copyText } = useClipboardToast();

function resetViewPrefs() {
  resetPrefs();
  showToast("View reset");
}

// Save / decision state
const saving = ref(false);
const saveError = ref<string | null>(null);

// history popover (product-only)
const openHistoryFor = ref<string | null>(null);

// Inline note editor state
const editingId = ref<string | null>(null);
const editValue = ref<string>("");

// Selection state (from composable)
const {
  selectedIds,
  lastClickedId,
  selectedCount,
  isSelected,
  toggleSelection,
  selectRange: composableSelectRange,
  clearSelection,
  selectAllFiltered: composableSelectAllFiltered,
  clearAllFiltered: composableClearAllFiltered,
  invertSelectionFiltered: composableInvertSelectionFiltered,
  toggleAllFiltered: composableToggleAllFiltered,
  getSelectedCandidates,
} = useCandidateSelection();

// Filter state (from composable)
const {
  decisionFilter,
  statusFilter,
  showSelectedOnly,
  searchText,
  filterDecidedBy,
  filterOnlyMine,
  compact,
  sortKey,
  auditSortLabel,
  auditSortArrow,
  loadPrefs,
  resetPrefs,
  clearFilters: composableClearFilters,
  quickUndecided: composableQuickUndecided,
  cycleAuditSort,
  filterCandidates,
  sortCandidates,
  normalize,
  matchesSearch,
} = useCandidateFilters(() => props.runId);

// Helper functions (from composable)
const {
  summary,
  decidedByOptions,
  decisionBadge,
  statusText,
  notePreview,
  auditHover,
  chipClass,
} = useCandidateHelpers(candidates);

// Bulk Export composable
const {
  exporting,
  exportError,
  bulkPackaging,
  bulkPackageName,
  greenCandidates,
  undecidedCount,
  yellowCount,
  redCount,
  runReadyLabel,
  runReadyHover,
  exportBlockedReason,
  exportPackageDisabledReason,
  canExportGreenOnly,
  runReadyBadgeClass,
  exportGreenOnlyZips,
  exportGreenOnlyPackageZip,
} = useBulkExport(
  () => props.runId,
  candidates,
  loading,
  showToast
);

// Helper: update candidate from decision response
function _updateCandidateFromDecisionResponse(id: string, res: any) {
  const idx = candidates.value.findIndex((x) => x.candidate_id === id);
  if (idx === -1) return;
  candidates.value[idx] = {
    ...candidates.value[idx],
    decision: (res.decision ?? null) as any,
    status: (res.status ?? candidates.value[idx].status) as any,
    decision_note: (res.decision_note ?? null) as any,
    decided_at_utc: (res.decided_at_utc ?? null) as any,
    decided_by: (res.decided_by ?? null) as any,
    decision_history: (res.decision_history ?? candidates.value[idx].decision_history ?? null) as any,
  };
}

// Bulk Decision V2 composable
const {
  bulkDecision,
  bulkNote,
  bulkClearNoteToo,
  bulkApplying,
  bulkProgress,
  bulkHistory,
  showBulkHistory,
  applyBulkDecision,
  undoLastBulkAction,
  clearBulkDecision: clearBulkDecisionV2,
} = useBulkDecisionV2(
  () => props.runId,
  candidates,
  selectedIds,
  _decidedByOrNull,
  showToast,
  _updateCandidateFromDecisionResponse
);

// Undo stack composable
const {
  undoStack,
  undoBusy,
  undoError,
  saving: undoSaving,
  saveError: undoSaveError,
  bulkSetDecision,
  bulkClearDecision,
  undoLast,
  undoStackHover,
  clearErrors: clearUndoErrors,
} = useUndoStack(
  () => props.runId,
  candidates,
  selectedIds,
  _decidedByOrNull,
  _updateCandidateFromDecisionResponse,
  showToast
);

const selectingAll = computed(() => candidates.value.length > 0 && selectedIds.value.size === candidates.value.length);

// -------------------------
// Filtered view (product-only)
// -------------------------
const filteredCandidates = computed(() => {
  // Filter using composable (handles decision, status, search, decidedBy, onlyMine, selectedOnly)
  const filtered = filterCandidates(candidates.value, selectedIds.value, effectiveOperatorId.value);

  // Sort (includes 'created' sorts not in composable)
  const sk = sortKey.value;
  return [...filtered].sort((a, b) => {
    if (sk === "id") return a.candidate_id.localeCompare(b.candidate_id);
    if (sk === "id_desc") return b.candidate_id.localeCompare(a.candidate_id);
    if (sk === "created") return (a.created_at_utc ?? "").localeCompare(b.created_at_utc ?? "");
    if (sk === "created_desc") return (b.created_at_utc ?? "").localeCompare(a.created_at_utc ?? "");
    if (sk === "decided_at") return (a.decided_at_utc ?? "").localeCompare(b.decided_at_utc ?? "");
    if (sk === "decided_at_desc") return (b.decided_at_utc ?? "").localeCompare(a.decided_at_utc ?? "");
    if (sk === "decided_by") return (a.decided_by ?? "").localeCompare(b.decided_by ?? "");
    if (sk === "decided_by_desc") return (b.decided_by ?? "").localeCompare(a.decided_by ?? "");
    if (sk === "status") return (a.status ?? "").localeCompare(b.status ?? "");
    if (sk === "decision") return (a.decision ?? "ZZZ").localeCompare(b.decision ?? "ZZZ");
    return 0;
  });
});

const filteredCount = computed(() => filteredCandidates.value.length);

const filteredIds = computed(() => new Set(filteredCandidates.value.map((c) => c.candidate_id)));
const allFilteredSelected = computed(() => {
  const f = filteredIds.value;
  if (f.size === 0) return false;
  for (const id of f) if (!selectedIds.value.has(id)) return false;
  return true;
});

// Selection helpers (wrappers around composable)
function selectAllFiltered() {
  composableSelectAllFiltered(filteredCandidates.value);
}
function clearAllFiltered() {
  composableClearAllFiltered(filteredCandidates.value);
}
function invertSelectionFiltered() {
  composableInvertSelectionFiltered(filteredCandidates.value);
}

function quickUndecided() {
  composableQuickUndecided();
}

function clearFilters() {
  composableClearFilters();
}

function toggleOne(id: string, ev?: MouseEvent) {
  if (ev?.shiftKey && lastClickedId.value && lastClickedId.value !== id) {
    composableSelectRange(filteredCandidates.value, id);
  } else {
    toggleSelection(id);
  }
}

function toggleAllFiltered() {
  composableToggleAllFiltered(filteredCandidates.value);
}

// Keyboard shortcuts (from composable)
useCandidateKeyboard(selectedIds, showBulkHistory, {
  clearSelection,
  selectAllFiltered,
  clearAllFiltered,
  invertSelectionFiltered,
  toggleBulkHistory: () => { showBulkHistory.value = !showBulkHistory.value; },
  bulkSetDecision,
  bulkClearDecision,
  exportGreenOnlyZips,
});

function openDecisionHistory(id: string) {
  openHistoryFor.value = openHistoryFor.value === id ? null : id;
}

async function load() {
  if (!props.runId) return;
  loading.value = true;
  error.value = null;
  exportError.value = null;
  clearUndoErrors();
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

onMounted(() => {
  // restore prefs first (so first render matches user intent)
  loadPrefs();
  load();
});

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
      decided_by: _decidedByOrNull(),
    });
    requestId.value = res.requestId ?? requestId.value;
    _updateCandidateFromDecisionResponse(c.candidate_id, res);
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
      decided_by: _decidedByOrNull(),
    });
    requestId.value = res.requestId ?? requestId.value;
    _updateCandidateFromDecisionResponse(c.candidate_id, res);
  } catch (e: any) {
    saveError.value = e?.message ?? String(e);
  } finally {
    saving.value = false;
  }
}

function setDecisionFilter(v: string) {
  decisionFilter.value = v as DecisionFilter;
}
function setStatusFilter(v: string) {
  statusFilter.value = v as StatusFilter;
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
        <span
          v-if="requestId"
          class="reqid"
          title="X-Request-Id"
        >req: {{ requestId }}</span>
        <button
          class="btn"
          :disabled="loading || exporting"
          @click="load"
        >
          Refresh
        </button>

        <!-- Bulk export (GREEN-only), blocked if any undecided -->
        <button
          class="btn"
          :disabled="!canExportGreenOnly"
          :title="exportBlockedReason ?? 'Download zips for GREEN candidates only'"
          @click="exportGreenOnlyZips"
        >
          {{ exporting ? "Exporting…" : "Export GREEN zips" }}
        </button>
      </div>
    </div>

    <p
      v-if="error"
      class="error"
    >
      Error: {{ error }}
    </p>
    <p
      v-if="saveError"
      class="error"
    >
      Save error: {{ saveError }}
    </p>
    <p
      v-if="exportError"
      class="error"
    >
      Export: {{ exportError }}
    </p>
    <p
      v-if="undoError"
      class="error"
    >
      Undo: {{ undoError }}
    </p>

    <!-- Manufacturing Summary Bar (extracted component) -->
    <ManufacturingSummaryBar
      v-if="!loading && candidates.length > 0"
      :total-count="candidates.length"
      :green-count="greenCandidates.length"
      :undecided-count="undecidedCount"
      :yellow-count="yellowCount"
      :red-count="redCount"
      :run-ready-label="runReadyLabel"
      :run-ready-hover="runReadyHover"
      :run-ready-badge-class="runReadyBadgeClass()"
      :package-name="bulkPackageName"
      :bulk-packaging="bulkPackaging"
      :export-disabled-reason="exportPackageDisabledReason"
      @update:package-name="bulkPackageName = $event"
      @export-package="exportGreenOnlyPackageZip"
    />

    <p
      v-if="loading"
      class="muted"
    >
      Loading candidates…
    </p>
    <p
      v-else-if="candidates.length === 0"
      class="muted"
    >
      No candidates yet.
    </p>

    <div
      v-else
      class="table"
      :class="{ compact }"
    >
      <CandidateFiltersSection
        v-model:decision-filter="decisionFilter"
        v-model:status-filter="statusFilter"
        v-model:filter-decided-by="filterDecidedBy"
        v-model:search-text="searchText"
        v-model:sort-key="sortKey"
        v-model:my-operator-id="myOperatorId"
        v-model:stamp-decisions-with-operator="stampDecisionsWithOperator"
        v-model:filter-only-mine="filterOnlyMine"
        v-model:show-selected-only="showSelectedOnly"
        v-model:compact="compact"
        :decided-by-options="decidedByOptions"
        :summary="summary"
        :effective-operator-id="effectiveOperatorId"
        :filtered-count="filteredCount"
        :selected-count="selectedIds.size"
        :total-count="candidates.length"
        :all-filtered-selected="allFilteredSelected"
        :disabled="saving || exporting || undoBusy"
        @select-all-filtered="selectAllFiltered"
        @clear-all-filtered="clearAllFiltered"
        @invert-selection-filtered="invertSelectionFiltered"
        @quick-undecided="quickUndecided"
        @clear-filters="clearFilters"
        @reset-view-prefs="resetViewPrefs"
        @toggle-all-filtered="toggleAllFiltered"
        @cycle-audit-sort="cycleAuditSort"
      />

      <!-- Bulk decision bar -->
      <BulkDecisionBar
        v-if="candidates.length > 0"
        :selected-count="selectedIds.size"
        :disabled="saving || exporting || undoBusy"
        :undo-stack-length="undoStack.length"
        :undo-busy="undoBusy"
        :last-undo-label="undoStack.length ? undoStackHover(undoStack[0]) : undefined"
        @bulk-green="bulkSetDecision('GREEN')"
        @bulk-yellow="bulkSetDecision('YELLOW')"
        @bulk-red="bulkSetDecision('RED')"
        @clear-decision="bulkClearDecision"
        @undo-last="undoLast"
      />

      <!-- Undo history display -->
      <UndoHistoryPanel
        v-if="undoStack.length > 0"
        :history="undoStack"
        :max-items="5"
      />

      <!-- Bulk decision v2 controls -->
      <BulkDecisionControlsV2
        v-if="selectedIds.size > 0"
        :selected-count="selectedIds.size"
        :bulk-decision="bulkDecision"
        :bulk-note="bulkNote"
        :bulk-clear-note-too="bulkClearNoteToo"
        :bulk-applying="bulkApplying"
        :bulk-progress="bulkProgress"
        :saving="saving"
        :exporting="exporting"
        :bulk-history-length="bulkHistory.length"
        :show-bulk-history="showBulkHistory"
        @update:bulk-decision="bulkDecision = $event"
        @update:bulk-note="bulkNote = $event"
        @update:bulk-clear-note-too="bulkClearNoteToo = $event"
        @update:show-bulk-history="showBulkHistory = $event"
        @apply="applyBulkDecision"
        @clear="clearBulkDecisionV2"
        @undo="undoLastBulkAction"
      />

      <!-- Bulk history panel -->
      <BulkHistoryPanel
        v-if="showBulkHistory && bulkHistory.length > 0"
        :history="bulkHistory as BulkHistoryRecord[]"
      />

      <CandidateRowItem
        v-for="c in filteredCandidates"
        :key="c.candidate_id"
        :candidate="c"
        :is-selected="selectedIds.has(c.candidate_id)"
        :disabled="saving || exporting || undoBusy"
        :is-history-open="openHistoryFor === c.candidate_id"
        :is-editing="editingId === c.candidate_id"
        :edit-value="editValue"
        @toggle="toggleOne"
        @open-history="openDecisionHistory"
        @decide="decide"
        @start-edit="startEdit"
        @save-edit="saveEdit"
        @cancel-edit="cancelEdit"
        @copy="copyText"
        @update:edit-value="editValue = $event"
      />
    </div>

    <!-- Export policy explainers (visible, not just hover) -->
    <ExportPolicyCard v-if="candidates.length > 0" />

    <!-- Copy toast -->
    <div
      v-if="toast"
      class="toast"
    >
      {{ toast }}
    </div>
  </section>
</template>

<style scoped>
.rmos-candidates {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.title {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.subtitle {
  font-size: 12px;
}

.meta {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.reqid {
  font-size: 12px;
  opacity: 0.75;
}

.error {
  color: #b00020;
}

.muted {
  opacity: 0.75;
}

.small {
  font-size: 12px;
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  font-size: 12px;
}

.table {
  display: grid;
  gap: 6px;
}

.row {
  display: grid;
  grid-template-columns: 34px 140px 1fr 140px 120px 140px 2fr 190px 360px;
  gap: 10px;
  align-items: start;
  padding: 8px;
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 10px;
  position: relative;
  background: white;
}

.row.head {
  font-weight: 600;
  background: rgba(0, 0, 0, 0.04);
  position: sticky;
  top: 0;
  z-index: 3;
  border-radius: 10px;
  backdrop-filter: blur(6px);
}

.row.clickable {
  cursor: pointer;
}

/* micro-follow: compact density */
.table.compact .row {
  padding: 6px;
  gap: 8px;
}

.table.compact .mono {
  font-size: 11px;
}

.table.compact .btn {
  padding: 4px 8px;
}

.table.compact .copyCol {
  gap: 4px;
}

/* copyCol layout */
.copyCol {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

/* -------------------------------------------------------------------------- */
/* Audit column layout                                                        */
/* -------------------------------------------------------------------------- */
.audit {
  min-width: 140px;
  max-width: 180px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.auditBy {
  font-weight: 600;
}

.auditAt {
  font-size: 11px;
  line-height: 1.15;
  opacity: 0.75;
}

.auditHeader {
  cursor: pointer;
  user-select: none;
  display: flex;
  align-items: center;
  gap: 4px;
}

.auditHeader:hover {
  color: var(--vscode-textLink-foreground, #3794ff);
}

.sortHint {
  opacity: 0.6;
  font-size: 12px;
}

.kbdhint {
  cursor: help;
  border: 1px solid rgba(0, 0, 0, 0.15);
  padding: 2px 8px;
  border-radius: 999px;
  display: inline-block;
}

.sel {
  display: flex;
  align-items: center;
  justify-content: center;
  padding-top: 2px;
}

.filters {
  display: flex;
  gap: 10px;
  align-items: end;
  justify-content: space-between;
  padding: 8px;
  border: 1px solid rgba(0, 0, 0, 0.10);
  border-radius: 10px;
}

.filters-left {
  display: flex;
  gap: 10px;
  align-items: end;
  flex-wrap: wrap;
  flex: 1;
}

.filters-right {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.field.grow {
  min-width: 280px;
  flex: 1;
}

.field label {
  font-size: 12px;
}

.field select,
.field input {
  padding: 6px 10px;
  border: 1px solid rgba(0, 0, 0, 0.16);
  border-radius: 10px;
  background: white;
}

.check {
  display: inline-flex;
  gap: 6px;
  align-items: center;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.btn {
  padding: 6px 10px;
  border: 1px solid rgba(0, 0, 0, 0.16);
  border-radius: 10px;
  background: white;
  cursor: pointer;
}

.btn.ghost {
  background: transparent;
}

.btn.danger {
  border-color: rgba(176, 0, 32, 0.35);
}

.smallbtn {
  padding: 4px 8px;
  font-size: 12px;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 12px;
  border: 1px solid rgba(0, 0, 0, 0.14);
}

.badge[data-badge="NEEDS_DECISION"] {
  opacity: 0.75;
}

.note textarea {
  width: 100%;
  resize: vertical;
  padding: 6px;
  border-radius: 10px;
  border: 1px solid rgba(0, 0, 0, 0.16);
}

.editor-actions {
  display: flex;
  gap: 6px;
  margin-top: 6px;
}

.bulkbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 8px;
  border: 1px dashed rgba(0, 0, 0, 0.18);
  border-radius: 10px;
}

.bulk-actions {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.undolist {
  display: grid;
  gap: 4px;
  padding: 8px;
  border: 1px solid rgba(0, 0, 0, 0.10);
  border-radius: 10px;
}

.undotitle {
  font-size: 12px;
}

.undoitem {
  display: flex;
  gap: 8px;
  align-items: center;
  font-size: 12px;
}

.policy ul {
  margin: 6px 0 0 18px;
}

.history {
  position: relative;
}

.popover {
  position: absolute;
  z-index: 50;
  top: 30px;
  left: 0;
}

/* toast (copy feedback) */
.toast {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: #323232;
  color: #fff;
  padding: 10px 20px;
  border-radius: 10px;
  z-index: 100;
  font-size: 14px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.25);
}

.chipsRow {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}

.chipsGroup {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.chip {
  border: 1px solid rgba(0, 0, 0, 0.14);
  background: white;
  border-radius: 999px;
  padding: 6px 10px;
  font-size: 12px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.chip .count {
  font-variant-numeric: tabular-nums;
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid rgba(0, 0, 0, 0.10);
  background: rgba(0, 0, 0, 0.03);
}

.chip.active {
  border-color: rgba(0, 0, 0, 0.28);
  box-shadow: 0 6px 14px rgba(0, 0, 0, 0.06);
}

.chip.good.active {
  border-color: #22c55e;
}

.chip.warn.active {
  border-color: #eab308;
}

.chip.bad.active {
  border-color: #ef4444;
}

.chip.muted.active {
  border-color: #6b7280;
}

.chip:hover {
  border-color: rgba(0, 0, 0, 0.22);
}

/* Decision cell with history count badge */
.decision-cell {
  display: flex;
  align-items: center;
  gap: 6px;
}

.history-count {
  font-size: 11px;
  color: #6b7280;
  cursor: pointer;
}

.history-count:hover {
  color: #374151;
  text-decoration: underline;
}

/* Bulk decision v2 */
.bulkbar2 {
  padding: 10px 14px;
  background: #f0f7ff;
  border-radius: 8px;
  margin-bottom: 10px;
}

.bulk-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.selectSmall {
  padding: 4px 8px;
  font-size: 13px;
  border-radius: 4px;
  border: 1px solid #ccc;
}

.inputSmall {
  padding: 4px 8px;
  font-size: 13px;
  border-radius: 4px;
  border: 1px solid #ccc;
  min-width: 180px;
}

.inlineCheck {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: rgba(0, 0, 0, 0.66);
  user-select: none;
}

.tiny {
  font-size: 11px;
  line-height: 1.15;
  opacity: 0.85;
}

/* Bulk history panel */
.bulkHistory {
  background: #fafafa;
  border: 1px solid #e5e5e5;
  border-radius: 8px;
  padding: 10px 14px;
  margin-bottom: 12px;
}

.bulkHistoryHeader {
  font-weight: 600;
  margin-bottom: 8px;
}

.bulkHistoryList {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 200px;
  overflow-y: auto;
}

.bulkHistoryRow {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
}

.badge.bGREEN {
  background: #dcfce7;
  color: #166534;
}

.badge.bYELLOW {
  background: #fef9c3;
  color: #854d0e;
}

.badge.bRED {
  background: #fee2e2;
  color: #991b1b;
}
</style>
