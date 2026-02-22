/**
 * Composable for variant helper functions.
 */
import type { Ref } from 'vue'
import type { VisionAsset, AdvisoryVariantSummary, BusyState } from './galleryTypes'

// ============================================================================
// Types
// ============================================================================

export interface VariantHelpersReturn {
  advisoryIdForAsset: (a: VisionAsset) => string | null
  variantForAsset: (a: VisionAsset) => AdvisoryVariantSummary | null
  attachDisabledReason: (a: VisionAsset) => string | null
  promoteDisabledReason: (a: VisionAsset) => string | null
  rejectionHover: (v: AdvisoryVariantSummary | null | undefined) => string
  canUndoReject: (v: AdvisoryVariantSummary | null | undefined) => string | null
  isRowBusy: (advisoryId: string, kind: 'review' | 'promote') => boolean
  setBusy: (advisoryId: string, v: BusyState) => void
}

// ============================================================================
// Composable
// ============================================================================

export function useVariantHelpers(
  selectedRunId: Ref<string | null>,
  variantById: Ref<Record<string, AdvisoryVariantSummary>>,
  advisoryIdByAssetSha: Ref<Record<string, string>>,
  busyByAdvisoryId: Ref<Record<string, BusyState>>
): VariantHelpersReturn {
  function advisoryIdForAsset(a: VisionAsset): string | null {
    const sha = (a as any).sha256 as string | undefined
    if (!sha) return null
    return advisoryIdByAssetSha.value[sha] ?? sha
  }

  function variantForAsset(a: VisionAsset): AdvisoryVariantSummary | null {
    const advisoryId = advisoryIdForAsset(a)
    if (!advisoryId) return null
    return variantById.value[advisoryId] ?? null
  }

  function attachDisabledReason(a: VisionAsset): string | null {
    if (!selectedRunId.value) return 'Select a run first.'
    const v = variantForAsset(a)
    if (v) return 'Already attached to this run.'
    return null
  }

  function promoteDisabledReason(a: VisionAsset): string | null {
    const v = variantForAsset(a)
    if (!v) return 'Attach to a run first.'
    if (v.rejected) return 'Rejected variants cannot be promoted.'
    if (v.promoted) return 'Already promoted.'
    if (v.status !== 'REVIEWED') return 'Must be reviewed first (status=REVIEWED).'
    return null
  }

  function rejectionHover(v: AdvisoryVariantSummary | null | undefined): string {
    if (!v) return ''
    if (!v.rejected) return 'Not rejected.'
    const parts: string[] = []
    if ((v as any).rejection_reason_code) parts.push(`Code: ${(v as any).rejection_reason_code}`)
    if ((v as any).rejection_reason_detail) parts.push(`Detail: ${(v as any).rejection_reason_detail}`)
    if ((v as any).rejection_operator_note) parts.push(`Note: ${(v as any).rejection_operator_note}`)
    if ((v as any).rejected_at_utc) parts.push(`At: ${(v as any).rejected_at_utc}`)
    return parts.length ? parts.join('\n') : 'Rejected.'
  }

  function canUndoReject(v: AdvisoryVariantSummary | null | undefined): string | null {
    if (!v) return 'Attach first'
    if (!v.rejected) return 'Not rejected'
    if (v.status === 'PROMOTED' || v.promoted) return 'Already promoted'
    return null
  }

  function isRowBusy(advisoryId: string, kind: 'review' | 'promote'): boolean {
    return busyByAdvisoryId.value[advisoryId] === kind
  }

  function setBusy(advisoryId: string, v: BusyState): void {
    busyByAdvisoryId.value = { ...busyByAdvisoryId.value, [advisoryId]: v }
  }

  return {
    advisoryIdForAsset,
    variantForAsset,
    attachDisabledReason,
    promoteDisabledReason,
    rejectionHover,
    canUndoReject,
    isRowBusy,
    setBusy
  }
}
