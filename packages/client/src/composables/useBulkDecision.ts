/**
 * useBulkDecision - Bulk decision operations for manufacturing candidates
 *
 * Extracted from ManufacturingCandidateList.vue to reduce component complexity.
 * Handles bulk set/clear decision state, progress tracking, and history.
 */

import { ref, computed, type Ref } from "vue";

// ═══════════════════════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════════════════════

export type RiskDecision = "GREEN" | "YELLOW" | "RED";

export interface BulkUndoItem {
  candidate_id: string;
  prev_decision: RiskDecision | null;
  prev_note: string | null;
  next_decision: RiskDecision | null;
  next_note: string | null;
}

export interface BulkActionRecord {
  id: string;
  at_utc: string;
  decision: RiskDecision | null;
  note: string | null;
  selected_count: number;
  applied_count: number;
  failed_count: number;
  items: BulkUndoItem[];
}

export interface BulkProgress {
  total: number;
  done: number;
  fail: number;
}

export interface CandidateMinimal {
  candidate_id: string;
  decision?: RiskDecision | null;
  decision_note?: string | null;
}

export interface UseBulkDecisionOptions {
  /** Function to get currently selected candidates */
  getSelectedCandidates: () => CandidateMinimal[];
  /** Function to apply a decision to a single candidate (API call) */
  applyDecision: (
    candidateId: string,
    decision: RiskDecision | null,
    note: string | null
  ) => Promise<void>;
  /** Function to show toast notification */
  showToast: (message: string, type: "ok" | "err") => void;
  /** Max history records to keep */
  maxHistory?: number;
}

// ═══════════════════════════════════════════════════════════════════════════
// Composable
// ═══════════════════════════════════════════════════════════════════════════

export function useBulkDecision(options: UseBulkDecisionOptions) {
  const { getSelectedCandidates, applyDecision, showToast, maxHistory = 10 } = options;

  // ─────────────────────────────────────────────────────────────────────────
  // State
  // ─────────────────────────────────────────────────────────────────────────

  const bulkDecision = ref<RiskDecision | null>(null);
  const bulkNote = ref<string>("");
  const bulkApplying = ref(false);
  const bulkProgress = ref<BulkProgress | null>(null);
  const bulkHistory = ref<BulkActionRecord[]>([]);
  const showBulkHistory = ref(false);
  const bulkClearNoteToo = ref(false);

  // ─────────────────────────────────────────────────────────────────────────
  // Helpers
  // ─────────────────────────────────────────────────────────────────────────

  function _utcNowIso(): string {
    return new Date().toISOString();
  }

  function _mkId(prefix = "bulk"): string {
    return `${prefix}_${Math.random().toString(16).slice(2)}_${Date.now()}`;
  }

  // ─────────────────────────────────────────────────────────────────────────
  // Computed
  // ─────────────────────────────────────────────────────────────────────────

  const hasBulkSelection = computed(() => getSelectedCandidates().length > 0);
  const bulkSelectionCount = computed(() => getSelectedCandidates().length);

  // ─────────────────────────────────────────────────────────────────────────
  // Actions
  // ─────────────────────────────────────────────────────────────────────────

  /**
   * Apply the current bulkDecision to all selected candidates
   */
  async function applyBulkDecision() {
    if (bulkApplying.value) return;
    if (bulkDecision.value === null) {
      showToast("Select a decision first", "err");
      return;
    }

    const sel = getSelectedCandidates();
    if (!sel.length) {
      showToast("No candidates selected", "err");
      return;
    }

    bulkApplying.value = true;
    bulkProgress.value = { total: sel.length, done: 0, fail: 0 };

    const record: BulkActionRecord = {
      id: _mkId("bulk_set"),
      at_utc: _utcNowIso(),
      decision: bulkDecision.value,
      note: bulkNote.value || null,
      selected_count: sel.length,
      applied_count: 0,
      failed_count: 0,
      items: [],
    };

    try {
      for (const c of sel) {
        const prev_decision = (c.decision ?? null) as RiskDecision | null;
        const prev_note = (c.decision_note ?? null) as string | null;

        record.items.push({
          candidate_id: c.candidate_id,
          prev_decision,
          prev_note,
          next_decision: bulkDecision.value,
          next_note: bulkNote.value || null,
        });

        try {
          await applyDecision(c.candidate_id, bulkDecision.value, bulkNote.value || null);
          record.applied_count += 1;
        } catch {
          record.failed_count += 1;
          bulkProgress.value = {
            total: bulkProgress.value!.total,
            done: bulkProgress.value!.done,
            fail: bulkProgress.value!.fail + 1,
          };
        } finally {
          bulkProgress.value = {
            total: bulkProgress.value!.total,
            done: bulkProgress.value!.done + 1,
            fail: bulkProgress.value!.fail,
          };
        }
      }

      bulkHistory.value = [record, ...bulkHistory.value].slice(0, maxHistory);

      const msg = record.failed_count
        ? `Bulk set done (${record.applied_count} ok, ${record.failed_count} failed)`
        : `Applied ${bulkDecision.value} to ${record.applied_count} candidates`;
      showToast(msg, record.failed_count ? "err" : "ok");
    } finally {
      bulkApplying.value = false;
      window.setTimeout(() => (bulkProgress.value = null), 900);
    }
  }

  /**
   * Clear decision for all selected candidates (set to null/NEEDS_DECISION)
   */
  async function clearBulkDecision() {
    if (bulkApplying.value) return;

    const sel = getSelectedCandidates();
    if (!sel.length) {
      showToast("No candidates selected", "err");
      return;
    }

    bulkApplying.value = true;
    bulkProgress.value = { total: sel.length, done: 0, fail: 0 };

    const record: BulkActionRecord = {
      id: _mkId("bulk_clear"),
      at_utc: _utcNowIso(),
      decision: null,
      note: null,
      selected_count: sel.length,
      applied_count: 0,
      failed_count: 0,
      items: [],
    };

    try {
      for (const c of sel) {
        const prev_decision = (c.decision ?? null) as RiskDecision | null;
        const prev_note = (c.decision_note ?? null) as string | null;
        const next_note = bulkClearNoteToo.value ? null : prev_note;

        record.items.push({
          candidate_id: c.candidate_id,
          prev_decision,
          prev_note,
          next_decision: null,
          next_note,
        });

        try {
          await applyDecision(c.candidate_id, null, next_note);
          record.applied_count += 1;
        } catch {
          record.failed_count += 1;
          bulkProgress.value = {
            total: bulkProgress.value!.total,
            done: bulkProgress.value!.done,
            fail: bulkProgress.value!.fail + 1,
          };
        } finally {
          bulkProgress.value = {
            total: bulkProgress.value!.total,
            done: bulkProgress.value!.done + 1,
            fail: bulkProgress.value!.fail,
          };
        }
      }

      bulkHistory.value = [record, ...bulkHistory.value].slice(0, maxHistory);

      const msg = record.failed_count
        ? `Bulk clear done (${record.applied_count} ok, ${record.failed_count} failed)`
        : "Cleared decision for selected candidates";
      showToast(msg, record.failed_count ? "err" : "ok");
    } finally {
      bulkApplying.value = false;
      window.setTimeout(() => (bulkProgress.value = null), 900);
    }
  }

  /**
   * Toggle bulk history panel visibility
   */
  function toggleBulkHistory() {
    showBulkHistory.value = !showBulkHistory.value;
  }

  /**
   * Reset bulk decision form state
   */
  function resetBulkForm() {
    bulkDecision.value = null;
    bulkNote.value = "";
  }

  // ─────────────────────────────────────────────────────────────────────────
  // Return
  // ─────────────────────────────────────────────────────────────────────────

  return {
    // State
    bulkDecision,
    bulkNote,
    bulkApplying,
    bulkProgress,
    bulkHistory,
    showBulkHistory,
    bulkClearNoteToo,

    // Computed
    hasBulkSelection,
    bulkSelectionCount,

    // Actions
    applyBulkDecision,
    clearBulkDecision,
    toggleBulkHistory,
    resetBulkForm,
  };
}
