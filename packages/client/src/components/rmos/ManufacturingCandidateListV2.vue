<script setup lang="ts">
/**
 * ManufacturingCandidateListV2 - Orchestrator Component
 * Decomposed from ManufacturingCandidateList.vue (1559 LOC → ~380 LOC)
 * Uses 10 composables for logic separation.
 */
import CandidateRowItem from '@/components/rmos/CandidateRowItem.vue'
import CandidateFiltersSection from '@/components/rmos/CandidateFiltersSection.vue'
import BulkDecisionBar from '@/components/rmos/BulkDecisionBar.vue'
import BulkDecisionControlsV2 from '@/components/rmos/BulkDecisionControlsV2.vue'
import BulkHistoryPanel, { type BulkHistoryRecord } from '@/components/rmos/BulkHistoryPanel.vue'
import UndoHistoryPanel from '@/components/rmos/UndoHistoryPanel.vue'
import ExportPolicyCard from '@/components/rmos/ExportPolicyCard.vue'
import ManufacturingSummaryBar from '@/components/rmos/ManufacturingSummaryBar.vue'
import { computed, onMounted, ref, watch } from 'vue'
import {
  decideManufacturingCandidate,
  listManufacturingCandidates,
  type ManufacturingCandidate,
  type RiskLevel,
} from '@/sdk/rmos/runs'
import {
  useCandidateSelection,
  useCandidateFilters,
  useBulkExport,
  useBulkDecisionV2,
  useOperatorIdentity,
  useToast,
  useKeyboardShortcuts,
  useInlineEditor,
  useLegacyBulkDecision,
  useCandidateHelpers,
} from './composables'

const props = defineProps<{
  runId: string
  currentOperator?: string | null
}>()

type CandidateRow = ManufacturingCandidate & { candidate_id: string }

// Core state
const loading = ref(false)
const error = ref<string | null>(null)
const requestId = ref<string>('')
const candidates = ref<CandidateRow[]>([])
const openHistoryFor = ref<string | null>(null)

// Toast composable
const { toast, showToast } = useToast()

// Operator identity composable
const {
  myOperatorId,
  stampDecisionsWithOperator,
  effectiveOperatorId,
  getDecidedByOrNull,
} = useOperatorIdentity(() => props.currentOperator)

// Selection composable
const {
  selectedIds,
  lastClickedId,
  toggleSelection,
  selectRange: composableSelectRange,
  clearSelection,
  selectAllFiltered: composableSelectAllFiltered,
  clearAllFiltered: composableClearAllFiltered,
  invertSelectionFiltered: composableInvertSelectionFiltered,
  toggleAllFiltered: composableToggleAllFiltered,
  getSelectedCandidates,
} = useCandidateSelection()

// Filter composable
const {
  decisionFilter,
  statusFilter,
  showSelectedOnly,
  searchText,
  filterDecidedBy,
  filterOnlyMine,
  compact,
  sortKey,
  loadPrefs,
  resetPrefs,
  clearFilters: composableClearFilters,
  quickUndecided: composableQuickUndecided,
  cycleAuditSort,
  filterCandidates,
} = useCandidateFilters(() => props.runId)

// Helpers composable
const { summary, decidedByOptions } = useCandidateHelpers(candidates)

// Helper: update candidate from API response
function updateCandidateFromResponse(id: string, res: any) {
  const idx = candidates.value.findIndex((x) => x.candidate_id === id)
  if (idx === -1) return
  candidates.value[idx] = {
    ...candidates.value[idx],
    decision: (res.decision ?? null) as RiskLevel | null,
    status: (res.status ?? candidates.value[idx].status) as any,
    decision_note: (res.decision_note ?? null) as string | null,
    decided_at_utc: (res.decided_at_utc ?? null) as string | null,
    decided_by: (res.decided_by ?? null) as string | null,
    decision_history: (res.decision_history ?? candidates.value[idx].decision_history ?? null) as any,
  }
}

function updateRequestId(newId: string) {
  requestId.value = newId
}

// Inline editor composable
const {
  editingId,
  editValue,
  saving,
  saveError,
  startEdit,
  cancelEdit,
  saveEdit: composableSaveEdit,
} = useInlineEditor(updateCandidateFromResponse, updateRequestId)

// Legacy bulk decision composable (old undo stack)
const {
  undoStack,
  undoBusy,
  undoError,
  bulkSetDecision,
  bulkClearDecision,
  undoLast,
  undoStackHover,
} = useLegacyBulkDecision(
  () => props.runId,
  candidates,
  selectedIds,
  getDecidedByOrNull,
  updateCandidateFromResponse,
  updateRequestId,
  saving,
  saveError
)

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
} = useBulkExport(() => props.runId, candidates, loading, showToast)

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
  getDecidedByOrNull,
  showToast,
  updateCandidateFromResponse
)

// Filtered candidates
const filteredCandidates = computed(() => {
  const filtered = filterCandidates(candidates.value, selectedIds.value, effectiveOperatorId.value)
  const sk = sortKey.value
  return [...filtered].sort((a, b) => {
    if (sk === 'id') return a.candidate_id.localeCompare(b.candidate_id)
    if (sk === 'id_desc') return b.candidate_id.localeCompare(a.candidate_id)
    if (sk === 'created') return (a.created_at_utc ?? '').localeCompare(b.created_at_utc ?? '')
    if (sk === 'created_desc') return (b.created_at_utc ?? '').localeCompare(a.created_at_utc ?? '')
    if (sk === 'decided_at') return (a.decided_at_utc ?? '').localeCompare(b.decided_at_utc ?? '')
    if (sk === 'decided_at_desc') return (b.decided_at_utc ?? '').localeCompare(a.decided_at_utc ?? '')
    if (sk === 'decided_by') return (a.decided_by ?? '').localeCompare(b.decided_by ?? '')
    if (sk === 'decided_by_desc') return (b.decided_by ?? '').localeCompare(a.decided_by ?? '')
    if (sk === 'status') return (a.status ?? '').localeCompare(b.status ?? '')
    if (sk === 'decision') return (a.decision ?? 'ZZZ').localeCompare(b.decision ?? 'ZZZ')
    return 0
  })
})

const filteredCount = computed(() => filteredCandidates.value.length)
const filteredIds = computed(() => new Set(filteredCandidates.value.map((c) => c.candidate_id)))
const allFilteredSelected = computed(() => {
  const f = filteredIds.value
  if (f.size === 0) return false
  for (const id of f) if (!selectedIds.value.has(id)) return false
  return true
})

// Selection helpers
function selectAllFiltered() {
  composableSelectAllFiltered(filteredCandidates.value)
}
function clearAllFiltered() {
  composableClearAllFiltered(filteredCandidates.value)
}
function invertSelectionFiltered() {
  composableInvertSelectionFiltered(filteredCandidates.value)
}
function toggleAllFiltered() {
  composableToggleAllFiltered(filteredCandidates.value)
}
function quickUndecided() {
  composableQuickUndecided()
}
function clearFilters() {
  composableClearFilters()
}

// Keyboard shortcuts
useKeyboardShortcuts(selectedIds, showBulkHistory, {
  clearSelection,
  selectAllFiltered,
  clearAllFiltered,
  invertSelectionFiltered,
  bulkSetDecision,
  bulkClearDecision,
  exportGreenOnlyZips,
  toggleBulkHistory: () => {
    showBulkHistory.value = !showBulkHistory.value
  },
  clearBulkDecisionV2,
})

// Toggle selection with shift-click range support
function toggleOne(id: string, ev?: MouseEvent) {
  if (ev?.shiftKey && lastClickedId.value && lastClickedId.value !== id) {
    composableSelectRange(filteredCandidates.value, id)
  } else {
    toggleSelection(id)
  }
}

// Decision history popover
function openDecisionHistory(id: string) {
  openHistoryFor.value = openHistoryFor.value === id ? null : id
}

// Single candidate decision
async function decide(c: CandidateRow, decision: RiskLevel) {
  if (!props.runId) return
  saving.value = true
  saveError.value = null
  try {
    const res = await decideManufacturingCandidate(props.runId, c.candidate_id, {
      decision,
      note: c.decision_note ?? null,
      decided_by: getDecidedByOrNull(),
    })
    if (res.requestId) requestId.value = res.requestId
    updateCandidateFromResponse(c.candidate_id, res)
  } catch (e: unknown) {
    saveError.value = e instanceof Error ? e.message : String(e)
  } finally {
    saving.value = false
  }
}

// Save edit wrapper
async function saveEdit(c: CandidateRow) {
  await composableSaveEdit(props.runId, c, getDecidedByOrNull())
}

// Copy to clipboard
async function copyText(label: string, value: string) {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(value)
    } else {
      const ta = document.createElement('textarea')
      ta.value = value
      ta.style.position = 'fixed'
      ta.style.left = '-9999px'
      document.body.appendChild(ta)
      ta.select()
      document.execCommand('copy')
      document.body.removeChild(ta)
    }
    showToast(`Copied ${label}`)
  } catch {
    showToast('Copy failed')
  }
}

// Reset view preferences
function resetViewPrefs() {
  resetPrefs()
  showToast('View reset')
}

// Load candidates
async function load() {
  if (!props.runId) return
  loading.value = true
  error.value = null
  exportError.value = null
  undoError.value = null
  try {
    const res = await listManufacturingCandidates(props.runId)
    candidates.value = (res.items ?? []) as CandidateRow[]
    requestId.value = res.requestId ?? ''
    // Prune selection to existing candidates
    const existing = new Set(candidates.value.map((c) => c.candidate_id))
    const next = new Set<string>()
    for (const id of selectedIds.value) if (existing.has(id)) next.add(id)
    selectedIds.value = next
    if (showSelectedOnly.value && selectedIds.value.size === 0) showSelectedOnly.value = false
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadPrefs()
  load()
})

watch(() => props.runId, load)
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
        <button class="btn" :disabled="loading || exporting" @click="load">Refresh</button>
        <button
          class="btn"
          :disabled="!canExportGreenOnly"
          :title="exportBlockedReason ?? 'Download zips for GREEN candidates only'"
          @click="exportGreenOnlyZips"
        >
          {{ exporting ? 'Exporting…' : 'Export GREEN zips' }}
        </button>
      </div>
    </div>

    <p v-if="error" class="error">Error: {{ error }}</p>
    <p v-if="saveError" class="error">Save error: {{ saveError }}</p>
    <p v-if="exportError" class="error">Export: {{ exportError }}</p>
    <p v-if="undoError" class="error">Undo: {{ undoError }}</p>

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

    <p v-if="loading" class="muted">Loading candidates…</p>
    <p v-else-if="candidates.length === 0" class="muted">No candidates yet.</p>

    <div v-else class="table" :class="{ compact }">
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

      <UndoHistoryPanel v-if="undoStack.length > 0" :history="undoStack" :max-items="5" />

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

    <ExportPolicyCard v-if="candidates.length > 0" />

    <div v-if="toast" class="toast">{{ toast }}</div>
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

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;
  font-size: 12px;
}

.table {
  display: grid;
  gap: 6px;
}

.table.compact .mono {
  font-size: 11px;
}

.btn {
  padding: 6px 10px;
  border: 1px solid rgba(0, 0, 0, 0.16);
  border-radius: 10px;
  background: white;
  cursor: pointer;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

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
</style>
