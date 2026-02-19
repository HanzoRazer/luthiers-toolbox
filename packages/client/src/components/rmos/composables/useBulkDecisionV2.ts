import { ref, type Ref } from 'vue'
import { decideManufacturingCandidate, type ManufacturingCandidate, type RiskLevel } from '@/sdk/rmos/runs'

type RiskDecision = 'GREEN' | 'YELLOW' | 'RED'

export interface BulkUndoItem {
  candidate_id: string
  prev_decision: RiskDecision | null
  prev_note: string | null
  next_decision: RiskDecision | null
  next_note: string | null
}

export interface BulkActionRecord {
  id: string
  at_utc: string
  decision: RiskDecision | null
  note: string | null
  selected_count: number
  applied_count: number
  failed_count: number
  items: BulkUndoItem[]
}

export interface BulkDecisionV2State {
  bulkDecision: Ref<RiskDecision | null>
  bulkNote: Ref<string>
  bulkClearNoteToo: Ref<boolean>
  bulkApplying: Ref<boolean>
  bulkProgress: Ref<{ total: number; done: number; fail: number } | null>
  bulkHistory: Ref<BulkActionRecord[]>
  showBulkHistory: Ref<boolean>
  applyBulkDecision: () => Promise<void>
  undoLastBulkAction: () => Promise<void>
  clearBulkDecision: () => Promise<void>
}

export function useBulkDecisionV2(
  runId: () => string,
  candidates: Ref<ManufacturingCandidate[]>,
  selectedIds: Ref<Set<string>>,
  getDecidedBy: () => string | null,
  showToast: (msg: string, variant?: 'ok' | 'err') => void,
  updateCandidate: (id: string, res: any) => void
): BulkDecisionV2State {
  const bulkDecision = ref<RiskDecision | null>(null)
  const bulkNote = ref('')
  const bulkClearNoteToo = ref(false)
  const bulkApplying = ref(false)
  const bulkProgress = ref<{ total: number; done: number; fail: number } | null>(null)
  const bulkHistory = ref<BulkActionRecord[]>([])
  const showBulkHistory = ref(false)

  function _utcNowIso(): string {
    return new Date().toISOString()
  }

  function _mkId(prefix = 'bulk'): string {
    return `${prefix}_${Math.random().toString(16).slice(2)}_${Date.now()}`
  }

  function _getSelectedCandidates(): ManufacturingCandidate[] {
    return candidates.value.filter((c) => selectedIds.value.has(c.candidate_id))
  }

  async function applyBulkDecision() {
    if (bulkApplying.value) return
    const sel = _getSelectedCandidates()
    if (!sel.length) {
      showToast('No candidates selected', 'err')
      return
    }
    if (bulkDecision.value == null) {
      showToast('Choose GREEN/YELLOW/RED', 'err')
      return
    }

    const rid = runId()
    bulkApplying.value = true
    bulkProgress.value = { total: sel.length, done: 0, fail: 0 }

    const record: BulkActionRecord = {
      id: _mkId('bulk_decision'),
      at_utc: _utcNowIso(),
      decision: bulkDecision.value,
      note: bulkNote.value.trim() || null,
      selected_count: sel.length,
      applied_count: 0,
      failed_count: 0,
      items: [],
    }

    try {
      for (const c of sel) {
        const prev_decision = (c.decision ?? null) as RiskDecision | null
        const prev_note = (c.decision_note ?? null) as string | null
        const next_decision = bulkDecision.value
        const next_note = record.note

        record.items.push({
          candidate_id: c.candidate_id,
          prev_decision,
          prev_note,
          next_decision,
          next_note,
        })

        try {
          const res = await decideManufacturingCandidate(rid, c.candidate_id, {
            decision: next_decision as RiskLevel,
            note: next_note,
            decided_by: getDecidedBy(),
          } as any)
          updateCandidate(c.candidate_id, res)
          record.applied_count += 1
        } catch {
          record.failed_count += 1
          bulkProgress.value = {
            total: bulkProgress.value!.total,
            done: bulkProgress.value!.done,
            fail: bulkProgress.value!.fail + 1,
          }
        } finally {
          bulkProgress.value = {
            total: bulkProgress.value!.total,
            done: bulkProgress.value!.done + 1,
            fail: bulkProgress.value!.fail,
          }
        }
      }

      bulkHistory.value = [record, ...bulkHistory.value].slice(0, 10)
      showToast(
        record.failed_count
          ? `Bulk set done (${record.applied_count} ok, ${record.failed_count} failed)`
          : `Bulk set decision: ${record.decision}`,
        record.failed_count ? 'err' : 'ok'
      )
    } finally {
      bulkApplying.value = false
      window.setTimeout(() => (bulkProgress.value = null), 900)
    }
  }

  async function undoLastBulkAction() {
    if (bulkApplying.value) return
    const rec = bulkHistory.value[0]
    if (!rec) {
      showToast('No bulk history to undo', 'err')
      return
    }

    const rid = runId()
    bulkApplying.value = true
    bulkProgress.value = { total: rec.items.length, done: 0, fail: 0 }

    try {
      for (const it of rec.items) {
        try {
          const res = await decideManufacturingCandidate(rid, it.candidate_id, {
            decision: it.prev_decision as RiskLevel | null,
            note: it.prev_note,
            decided_by: getDecidedBy(),
          } as any)
          updateCandidate(it.candidate_id, res)
        } catch {
          bulkProgress.value = {
            total: bulkProgress.value!.total,
            done: bulkProgress.value!.done,
            fail: bulkProgress.value!.fail + 1,
          }
        } finally {
          bulkProgress.value = {
            total: bulkProgress.value!.total,
            done: bulkProgress.value!.done + 1,
            fail: bulkProgress.value!.fail,
          }
        }
      }

      bulkHistory.value = bulkHistory.value.slice(1)
      showToast('Undid last bulk decision')
    } finally {
      bulkApplying.value = false
      window.setTimeout(() => (bulkProgress.value = null), 900)
    }
  }

  async function clearBulkDecision() {
    if (bulkApplying.value) return
    const sel = _getSelectedCandidates()
    if (!sel.length) {
      showToast('No candidates selected', 'err')
      return
    }

    const rid = runId()
    bulkApplying.value = true
    bulkProgress.value = { total: sel.length, done: 0, fail: 0 }

    const record: BulkActionRecord = {
      id: _mkId('bulk_clear'),
      at_utc: _utcNowIso(),
      decision: null,
      note: null,
      selected_count: sel.length,
      applied_count: 0,
      failed_count: 0,
      items: [],
    }

    try {
      for (const c of sel) {
        const prev_decision = (c.decision ?? null) as RiskDecision | null
        const prev_note = (c.decision_note ?? null) as string | null
        const next_note = bulkClearNoteToo.value ? null : prev_note

        record.items.push({
          candidate_id: c.candidate_id,
          prev_decision,
          prev_note,
          next_decision: null,
          next_note,
        })

        try {
          const res = await decideManufacturingCandidate(rid, c.candidate_id, {
            decision: null,
            note: next_note,
            decided_by: getDecidedBy(),
          } as any)
          updateCandidate(c.candidate_id, res)
          record.applied_count += 1
        } catch {
          record.failed_count += 1
          bulkProgress.value = {
            total: bulkProgress.value!.total,
            done: bulkProgress.value!.done,
            fail: bulkProgress.value!.fail + 1,
          }
        } finally {
          bulkProgress.value = {
            total: bulkProgress.value!.total,
            done: bulkProgress.value!.done + 1,
            fail: bulkProgress.value!.fail,
          }
        }
      }

      bulkHistory.value = [record, ...bulkHistory.value].slice(0, 10)
      showToast(
        record.failed_count
          ? `Bulk clear done (${record.applied_count} ok, ${record.failed_count} failed)`
          : 'Cleared decision for selected candidates',
        record.failed_count ? 'err' : 'ok'
      )
    } finally {
      bulkApplying.value = false
      window.setTimeout(() => (bulkProgress.value = null), 900)
    }
  }

  return {
    bulkDecision,
    bulkNote,
    bulkClearNoteToo,
    bulkApplying,
    bulkProgress,
    bulkHistory,
    showBulkHistory,
    applyBulkDecision,
    undoLastBulkAction,
    clearBulkDecision,
  }
}
