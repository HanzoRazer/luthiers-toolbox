import { ref, type Ref, computed } from 'vue'
import { decideManufacturingCandidate, type RiskLevel, type ManufacturingCandidate } from '@/sdk/rmos/runs'

export type CandidateRow = ManufacturingCandidate & {
  candidate_id: string
}

export type UndoItem = {
  ts_utc: string
  run_id: string
  label: string
  applied_decision: RiskLevel | null
  candidate_ids: string[]
  /** Snapshot needed to restore */
  prev: Record<
    string,
    {
      decision: RiskLevel | null
      decision_note: string | null
    }
  >
}

export function useUndoStack(
  getRunId: () => string,
  candidates: Ref<CandidateRow[]>,
  selectedIds: Ref<Set<string>>,
  getDecidedBy: () => string | null,
  updateCandidate: (id: string, res: any) => void,
  onToast?: (msg: string) => void
) {
  const undoStack = ref<UndoItem[]>([])
  const undoBusy = ref(false)
  const undoError = ref<string | null>(null)
  const saving = ref(false)
  const saveError = ref<string | null>(null)

  // Internal request ID tracker
  const requestId = ref<string>('')

  // Selected rows helper
  const selectedRows = computed(() => {
    const s = selectedIds.value
    return candidates.value.filter((c) => s.has(c.candidate_id))
  })

  function utcNowIso() {
    return new Date().toISOString()
  }

  // Check if bulk clear is possible
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

  // Bulk set decision (GREEN/YELLOW/RED) with undo
  async function bulkSetDecision(decision: RiskLevel) {
    const runId = getRunId()
    if (!runId) return

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
        decision: (r.decision ?? null) as any,
        decision_note: (r.decision_note ?? null) as any,
      }
    }

    saving.value = true
    try {
      // Sequential, deterministic updates (keeps audit clean and avoids request bursts)
      for (const r of rows) {
        const res = await decideManufacturingCandidate(runId, r.candidate_id, {
          decision,
          note: r.decision_note ?? null,
          decided_by: getDecidedBy(),
        })
        requestId.value = res.requestId ?? requestId.value
        updateCandidate(r.candidate_id, res)
        await new Promise((rr) => setTimeout(rr, 40))
      }

      // Push undo record
      undoStack.value.unshift({
        ts_utc: utcNowIso(),
        run_id: runId,
        label: `Bulk set ${rows.length} → ${decision}`,
        applied_decision: decision,
        candidate_ids: rows.map((x) => x.candidate_id),
        prev,
      })
      // Keep stack small/high-signal
      if (undoStack.value.length > 20) undoStack.value = undoStack.value.slice(0, 20)
    } catch (e: any) {
      saveError.value = e?.message ?? String(e)
    } finally {
      saving.value = false
    }
  }

  // Bulk clear decision (set to null)
  async function bulkClearDecision() {
    const chk = canBulkClearDecision()
    if (!chk.ok) return

    const runId = getRunId()
    if (!runId) return

    saving.value = true
    saveError.value = null

    const sel = selectedRows.value
    const nowIso = utcNowIso()

    // Snapshot "before" for undo per candidate that is changing
    const changed = sel.filter((c) => c.decision !== null)
    const prev: UndoItem['prev'] = {}
    for (const c of changed) {
      prev[c.candidate_id] = {
        decision: (c.decision ?? null) as any,
        decision_note: (c.decision_note ?? null) as any,
      }
    }

    try {
      for (const c of changed) {
        const res = await decideManufacturingCandidate(runId, c.candidate_id, {
          decision: null,
          note: null,
          decided_by: getDecidedBy(),
        })
        requestId.value = res.requestId ?? requestId.value
        updateCandidate(c.candidate_id, res)
        await new Promise((rr) => setTimeout(rr, 40))
      }

      // Push undo record
      undoStack.value.unshift({
        ts_utc: nowIso,
        run_id: runId,
        label: `Bulk clear ${changed.length} → NEEDS_DECISION`,
        applied_decision: null,
        candidate_ids: changed.map((x) => x.candidate_id),
        prev,
      })
      if (undoStack.value.length > 20) undoStack.value = undoStack.value.slice(0, 20)
    } catch (e: any) {
      saveError.value = e?.message ?? String(e)
    } finally {
      saving.value = false
    }
  }

  // Undo last bulk action
  async function undoLast() {
    const runId = getRunId()
    if (!runId) return
    if (undoStack.value.length === 0) return

    undoBusy.value = true
    undoError.value = null

    const item = undoStack.value[0]
    try {
      for (const id of item.candidate_ids) {
        const snap = item.prev[id]
        if (!snap) continue
        const res = await decideManufacturingCandidate(runId, id, {
          decision: snap.decision, // may be null (back to NEEDS_DECISION)
          note: snap.decision_note,
          decided_by: getDecidedBy(),
        })
        requestId.value = res.requestId ?? requestId.value
        updateCandidate(id, res)
        await new Promise((rr) => setTimeout(rr, 40))
      }
      // Pop after successful undo
      undoStack.value.shift()
    } catch (e: any) {
      undoError.value = e?.message ?? String(e)
    } finally {
      undoBusy.value = false
    }
  }

  // Hover text for undo item
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

  // Clear errors on load
  function clearErrors() {
    undoError.value = null
    saveError.value = null
  }

  return {
    undoStack,
    undoBusy,
    undoError,
    saving,
    saveError,
    requestId,
    selectedRows,
    canBulkClearDecision,
    bulkClearBlockedHover,
    bulkSetDecision,
    bulkClearDecision,
    undoLast,
    undoStackHover,
    clearErrors,
  }
}
