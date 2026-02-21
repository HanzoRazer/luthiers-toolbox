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
import styles from "./ManufacturingCandidateList.module.css";
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
  <section :class="styles.rmosCandidates">
    <div :class="styles.header">
      <div :class="styles.title">
        <h3>Manufacturing Candidates</h3>
        <div :class="[styles.subtitle, styles.muted]">
          Decision is <span :class="styles.mono">null</span> until operator decides (spine-locked).
        </div>
      </div>
      <div :class="styles.meta">
        <span
          v-if="requestId"
          :class="styles.reqid"
          title="X-Request-Id"
        >req: {{ requestId }}</span>
        <button
          :class="styles.btn"
          :disabled="loading || exporting"
          @click="load"
        >
          Refresh
        </button>

        <!-- Bulk export (GREEN-only), blocked if any undecided -->
        <button
          :class="styles.btn"
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
      :class="styles.error"
    >
      Error: {{ error }}
    </p>
    <p
      v-if="saveError"
      :class="styles.error"
    >
      Save error: {{ saveError }}
    </p>
    <p
      v-if="exportError"
      :class="styles.error"
    >
      Export: {{ exportError }}
    </p>
    <p
      v-if="undoError"
      :class="styles.error"
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
      :class="styles.muted"
    >
      Loading candidates…
    </p>
    <p
      v-else-if="candidates.length === 0"
      :class="styles.muted"
    >
      No candidates yet.
    </p>

    <div
      v-else
      :class="[styles.table, { [styles.tableCompact]: compact }]"
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
      :class="styles.toast"
    >
      {{ toast }}
    </div>
  </section>
</template>
