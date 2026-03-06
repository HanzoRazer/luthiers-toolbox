/**
 * Composable for attaching assets to runs and promoting variants.
 */
import type { Ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  attachAdvisoryToRun,
  createRun,
  listRecentRuns,
  type VisionAsset
} from '../api/visionApi'
import { promoteAdvisoryVariant } from '@/sdk/rmos/runs'
import type { RunSummary } from './galleryTypes'

// ============================================================================
// Types
// ============================================================================

export interface AssetAttachmentReturn {
  ensureRunSelected: () => Promise<string | null>
  doAttach: (a: VisionAsset) => Promise<void>
  doPromote: (a: VisionAsset) => Promise<void>
  toggleReview: (a: VisionAsset) => void
}

// ============================================================================
// Composable
// ============================================================================

export function useAssetAttachment(
  selectedRunId: Ref<string | null>,
  runs: Ref<RunSummary[]>,
  isAttaching: Ref<string | null>,
  isPromoting: Ref<string | null>,
  advisoryIdByAssetSha: Ref<Record<string, string>>,
  lastAttachedRunId: Ref<string | null>,
  openReviewFor: Ref<string | null>,
  attachDisabledReason: (a: VisionAsset) => string | null,
  promoteDisabledReason: (a: VisionAsset) => string | null,
  advisoryIdForAsset: (a: VisionAsset) => string | null,
  variantForAsset: (a: VisionAsset) => any,
  refreshVariants: () => Promise<void>,
  toastOk: (msg: string) => void,
  toastErr: (msg: string) => void
): AssetAttachmentReturn {
  const router = useRouter()

  async function ensureRunSelected(): Promise<string | null> {
    if (selectedRunId.value) return selectedRunId.value

    try {
      const created = await createRun({ event_type: 'vision_image_review' })
      selectedRunId.value = created.run_id

      // Keep dropdown in sync (best-effort, non-blocking)
      try {
        runs.value = (await listRecentRuns()).runs
      } catch {
        // ignore
      }

      toastOk('Created new run.')
      return created.run_id
    } catch (e: any) {
      toastErr(e?.message || 'Create run failed.')
      return null
    }
  }

  async function doAttach(a: VisionAsset): Promise<void> {
    const sha = (a as any).sha256 as string | undefined
    if (!sha) {
      toastErr('Asset missing sha256.')
      return
    }
    const deny = attachDisabledReason(a)
    if (deny) {
      toastErr(deny)
      return
    }

    const runId = await ensureRunSelected()
    if (!runId) return

    isAttaching.value = sha
    try {
      const res = await attachAdvisoryToRun(runId, {
        advisory_id: sha,
        kind: 'advisory'
      })

      const advisoryId = (res?.advisory_id ?? sha) as string
      advisoryIdByAssetSha.value = { ...advisoryIdByAssetSha.value, [sha]: advisoryId }
      lastAttachedRunId.value = selectedRunId.value

      await refreshVariants()

      // Auto-deeplink to review surface
      try {
        router.push({ name: 'RunVariantsReview', params: { run_id: selectedRunId.value } })
      } catch {
        // Non-fatal
      }

      toastOk('Attached to run.')
    } catch (e: any) {
      toastErr(e?.message || 'Attach failed.')
    } finally {
      isAttaching.value = null
    }
  }

  async function doPromote(a: VisionAsset): Promise<void> {
    const deny = promoteDisabledReason(a)
    if (deny) {
      toastErr(deny)
      return
    }
    if (!selectedRunId.value) return

    const advisoryId = advisoryIdForAsset(a)
    if (!advisoryId) {
      toastErr('Missing advisory id.')
      return
    }

    isPromoting.value = advisoryId
    try {
      await promoteAdvisoryVariant(selectedRunId.value, advisoryId)
      await refreshVariants()
      toastOk('Promoted to manufacturing.')
    } catch (e: any) {
      // Handle 404 errors with clear guidance
      const status = e?.response?.status ?? e?.status
      if (status === 404) {
        // Clear stale state
        window.localStorage.removeItem('tb.visionAttach.selectedRunId')
        toastErr('Run not found. Please select a valid run and try again.')
      } else {
        toastErr(e?.message || 'Promote failed.')
      }
    } finally {
      isPromoting.value = null
    }
  }

  function toggleReview(a: VisionAsset): void {
    const v = variantForAsset(a)
    if (!v) {
      toastErr('Attach to a run first.')
      return
    }
    openReviewFor.value = openReviewFor.value === v.advisory_id ? null : v.advisory_id
  }

  return {
    ensureRunSelected,
    doAttach,
    doPromote,
    toggleReview
  }
}
