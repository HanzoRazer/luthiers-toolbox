/**
 * Composable for legacy bulk decision operations with undo stack.
 * This is the original bulk decision system using client-side undo tracking.
 * Note: useBulkDecisionV2 is the newer system with bulkHistory.
 */
import { ref, computed, type Ref, type ComputedRef } from 'vue'
import { decideManufacturingCandidate, type ManufacturingCandidate, type RiskLevel } from '@/sdk/rmos/runs'

export interface UndoItem {
  ts_utc: string
  run_id: string
  label: string
  applied_decision: RiskLevel | null
  candidate_ids: string[]
  prev: Record<string, { decision: RiskLevel | null; decision_note: string | null }>
}

export interface LegacyBulkDecisionState {
  undoStack: Ref<UndoItem[]>
  undoBusy: Ref<boolean>
  undoError: Ref<string | null>
  selectedRows: ComputedRef<ManufacturingCandidate[]>
  canBulkClearDecision: () => { ok: boolean; reason?: string }
  bulkClearBlockedHover: () => string
  bulkSetDecision: (decision: RiskLevel) => Promise<void>
  bulkClearDecision: () => Promise<void>
  undoLast: () => Promise<void>
  undoStackHover: (item: UndoItem) => string
}

function utcNowIso(): string {
  return new Date().toISOString()
}

export function useLegacyBulkDecision(
  runId: () => string,
  candidates: Ref<ManufacturingCandidate[]>,
  selectedIds: Ref<Set<string>>,
  getDecidedBy: () => string | null,
  onUpdateCandidate: (id: string, res: any) => void,
  onUpdateRequestId: (requestId: string) => void,
  saving: Ref<boolean>,
  saveError: Ref<string | null>
): LegacyBulkDecisionState {
  const undoStack = ref<UndoItem[]>([])
  const undoBusy = ref(false)
  const undoError = ref<string | null>(null)

  const selectedRows = computed(() => {
    const s = selectedIds.value
    return candidates.value.filter((c) => s.has(c.candidate_id))
  })

  function canBulkClearDecision(): { ok: boolean; reason?: string } {
    const sel = selectedRows.value
    if (sel.length === 0) return { ok: false, reason: 'Select candidates to clear decision.' }
    const anyDecided = sel.some((c) => c.decision !== null)
    if (!anyDecided) return { ok: false, reason: 'All selected candidates are already undecided.' }
    return { ok: true }
  }

  function bulkClearBlockedHover(): string {
    const chk = canBulkClearDecision()
    return chk.ok
      ? 'Clear decision → NEEDS_DECISION (decision=null). Note cleared too.'
      : (chk.reason ?? 'Blocked')
  }

  async function bulkSetDecision(decision: RiskLevel) {
    const rid = runId()
    if (!rid) return
    undoError.value = null
    saveError.value = null

    const rows = selectedRows.value
    if (rows.length === 0) {
      undoError.value = 'Select at least one candidate first.'
      return
    }

    // Snapshot previous states (for undo)
    const prev: UndoItem['prev'] = {}
    for (const r of rows) {
      prev[r.candidate_id] = {
        decision: (r.decision ?? null) as RiskLevel | null,
        decision_note: (r.decision_note ?? null) as string | null,
      }
    }

    saving.value = true
    try {
      // Sequential, deterministic updates
      for (const r of rows) {
        const res = await decideManufacturingCandidate(rid, r.candidate_id, {
          decision,
          note: r.decision_note ?? null,
          decided_by: getDecidedBy(),
        })
        if (res.requestId) {
          onUpdateRequestId(res.requestId)
        }
        onUpdateCandidate(r.candidate_id, res)
        await new Promise((resolve) => setTimeout(resolve, 40))
      }

      // Push undo record
      undoStack.value.unshift({
        ts_utc: utcNowIso(),
        run_id: rid,
        label: `Bulk set ${rows.length} → ${decision}`,
        applied_decision: decision,
        candidate_ids: rows.map((x) => x.candidate_id),
        prev,
      })
      // Keep stack small
      if (undoStack.value.length > 20) {
        undoStack.value = undoStack.value.slice(0, 20)
      }
    } catch (e: unknown) {
      saveError.value = e instanceof Error ? e.message : String(e)
    } finally {
      saving.value = false
    }
  }

  async function bulkClearDecision() {
    const chk = canBulkClearDecision()
    if (!chk.ok) return

    const rid = runId()
    if (!rid) return

    saving.value = true
    saveError.value = null

    const sel = selectedRows.value
    const nowIso = utcNowIso()

    // Snapshot "before" for undo
    const changed = sel.filter((c) => c.decision !== null)
    const prev: UndoItem['prev'] = {}
    for (const c of changed) {
      prev[c.candidate_id] = {
        decision: (c.decision ?? null) as RiskLevel | null,
        decision_note: (c.decision_note ?? null) as string | null,
      }
    }

    try {
      for (const c of changed) {
        const res = await decideManufacturingCandidate(rid, c.candidate_id, {
          decision: null,
          note: null,
          decided_by: getDecidedBy(),
        })
        if (res.requestId) {
          onUpdateRequestId(res.requestId)
        }
        onUpdateCandidate(c.candidate_id, res)
        await new Promise((resolve) => setTimeout(resolve, 40))
      }

      // Push undo record
      undoStack.value.unshift({
        ts_utc: nowIso,
        run_id: rid,
        label: `Bulk clear ${changed.length} → NEEDS_DECISION`,
        applied_decision: null,
        candidate_ids: changed.map((x) => x.candidate_id),
        prev,
      })
      if (undoStack.value.length > 20) {
        undoStack.value = undoStack.value.slice(0, 20)
      }
    } catch (e: unknown) {
      saveError.value = e instanceof Error ? e.message : String(e)
    } finally {
      saving.value = false
    }
  }

  async function undoLast() {
    const rid = runId()
    if (!rid) return
    if (undoStack.value.length === 0) return

    undoBusy.value = true
    undoError.value = null

    const item = undoStack.value[0]
    try {
      for (const id of item.candidate_ids) {
        const snap = item.prev[id]
        if (!snap) continue
        const res = await decideManufacturingCandidate(rid, id, {
          decision: snap.decision,
          note: snap.decision_note,
          decided_by: getDecidedBy(),
        })
        if (res.requestId) {
          onUpdateRequestId(res.requestId)
        }
        onUpdateCandidate(id, res)
        await new Promise((resolve) => setTimeout(resolve, 40))
      }
      // Pop after successful undo
      undoStack.value.shift()
    } catch (e: unknown) {
      undoError.value = e instanceof Error ? e.message : String(e)
    } finally {
      undoBusy.value = false
    }
  }

  function undoStackHover(item: UndoItem): string {
    const ids = item.candidate_ids.slice(0, 6).join(', ')
    const more = item.candidate_ids.length > 6 ? ` …(+${item.candidate_ids.length - 6})` : ''
    return [
      `When: ${item.ts_utc}`,
      `Run: ${item.run_id}`,
      `Action: ${item.label}`,
      `Candidates: ${ids}${more}`,
      `Undo applies previous decision + note (including null).`,
    ].join('\n')
  }

  return {
    undoStack,
    undoBusy,
    undoError,
    selectedRows,
    canBulkClearDecision,
    bulkClearBlockedHover,
    bulkSetDecision,
    bulkClearDecision,
    undoLast,
    undoStackHover,
  }
}
