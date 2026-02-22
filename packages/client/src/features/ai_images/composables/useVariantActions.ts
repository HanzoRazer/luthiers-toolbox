/**
 * Composable for variant review/promote actions.
 */
import type { Ref } from 'vue'
import {
  listAdvisoryVariants,
  reviewAdvisoryVariant,
  promoteAdvisoryVariant,
  type AdvisoryVariantSummary,
  type RejectReasonCode
} from '@/sdk/rmos/runs'
import type { BusyState } from './galleryTypes'

// ============================================================================
// Types
// ============================================================================

export interface VariantActionsReturn {
  refreshVariants: () => Promise<void>
  quickReject: (advisoryId: string, code: RejectReasonCode) => Promise<void>
  undoReject: (advisoryId: string) => Promise<void>
  quickPromote: (advisoryId: string) => Promise<void>
}

// ============================================================================
// Composable
// ============================================================================

export function useVariantActions(
  selectedRunId: Ref<string | null>,
  variantById: Ref<Record<string, AdvisoryVariantSummary>>,
  busyByAdvisoryId: Ref<Record<string, BusyState>>,
  toastOk: (msg: string) => void,
  toastErr: (msg: string) => void
): VariantActionsReturn {
  function setBusy(advisoryId: string, v: BusyState): void {
    busyByAdvisoryId.value = { ...busyByAdvisoryId.value, [advisoryId]: v }
  }

  async function refreshVariants(): Promise<void> {
    if (!selectedRunId.value) return

    try {
      const res = await listAdvisoryVariants(selectedRunId.value)
      const next: Record<string, AdvisoryVariantSummary> = {}
      for (const it of res.items ?? []) next[it.advisory_id] = it
      variantById.value = next
    } catch (e: any) {
      toastErr(e?.message || 'Failed to load run variants.')
    }
  }

  async function quickReject(advisoryId: string, code: RejectReasonCode): Promise<void> {
    const runId = selectedRunId.value
    if (!runId) return
    if (busyByAdvisoryId.value[advisoryId]) return

    setBusy(advisoryId, 'review')
    try {
      const res = await reviewAdvisoryVariant(runId, advisoryId, {
        rejected: true,
        rejection_reason_code: code,
        status: 'REJECTED'
      })
      await refreshVariants()
      toastOk(`Rejected (${code}).${res.requestId ? ` req:${res.requestId}` : ''}`)
    } catch (e: any) {
      toastErr(e?.message || 'Reject failed.')
    } finally {
      setBusy(advisoryId, null)
    }
  }

  async function undoReject(advisoryId: string): Promise<void> {
    const runId = selectedRunId.value
    if (!runId) return
    if (busyByAdvisoryId.value[advisoryId]) return

    setBusy(advisoryId, 'review')
    try {
      const res = await reviewAdvisoryVariant(runId, advisoryId, {
        rejected: false,
        status: 'REVIEWED',
        rejection_reason_code: null as any,
        rejection_reason_detail: null as any,
        rejection_operator_note: null as any
      })
      await refreshVariants()
      toastOk(`Rejection cleared.${res.requestId ? ` req:${res.requestId}` : ''}`)
    } catch (e: any) {
      toastErr(e?.message || 'Undo reject failed.')
    } finally {
      setBusy(advisoryId, null)
    }
  }

  async function quickPromote(advisoryId: string): Promise<void> {
    const runId = selectedRunId.value
    if (!runId) return
    if (busyByAdvisoryId.value[advisoryId]) return

    setBusy(advisoryId, 'promote')
    try {
      const res = await promoteAdvisoryVariant(runId, advisoryId)
      await refreshVariants()
      toastOk(`Promoted.${res.requestId ? ` req:${res.requestId}` : ''}`)
    } catch (e: any) {
      toastErr(e?.message || 'Promote failed.')
    } finally {
      setBusy(advisoryId, null)
    }
  }

  return {
    refreshVariants,
    quickReject,
    undoReject,
    quickPromote
  }
}
