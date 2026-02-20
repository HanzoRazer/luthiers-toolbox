/**
 * Composable for attaching vision assets to runs.
 * Extracted from VisionAttachToRunWidget.vue
 */
import { ref, computed, type Ref, type ComputedRef } from 'vue'
import { useRouter } from 'vue-router'
import { attachAdvisoryToRun, type VisionAsset } from '../api/visionApi'

// =============================================================================
// Types
// =============================================================================

export interface AttachResult {
  runId: string
  advisoryId: string
}

export interface VisionAttachState {
  /** Whether attachment is in progress */
  isAttaching: Ref<boolean>
  /** Last successful attachment */
  lastAttached: Ref<AttachResult | null>
  /** Whether attachment can proceed */
  canAttach: ComputedRef<boolean>
  /** Attach selected asset to selected run */
  attachToRun: () => Promise<{ success: boolean; message?: string; error?: string }>
  /** Navigate to review page for a run */
  goToReview: (runId: string) => void
}

// =============================================================================
// Composable
// =============================================================================

export function useVisionAttach(
  getSelectedAssetSha: () => string | null,
  getSelectedRunId: () => string | null,
  getSelectedAsset: () => VisionAsset | null,
  autoNavigate: () => boolean
): VisionAttachState {
  const router = useRouter()
  const isAttaching = ref(false)
  const lastAttached = ref<AttachResult | null>(null)

  // ===========================================================================
  // Computed
  // ===========================================================================

  const canAttach = computed(() => {
    return (
      getSelectedAssetSha() !== null &&
      getSelectedRunId() !== null &&
      !isAttaching.value
    )
  })

  // ===========================================================================
  // Methods
  // ===========================================================================

  async function attachToRun(): Promise<{ success: boolean; message?: string; error?: string }> {
    const selectedAssetSha = getSelectedAssetSha()
    const selectedRunId = getSelectedRunId()
    const asset = getSelectedAsset()

    if (!canAttach.value || !selectedAssetSha || !selectedRunId) {
      return { success: false, error: 'Cannot attach' }
    }

    isAttaching.value = true

    try {
      const res = await attachAdvisoryToRun(selectedRunId, {
        advisory_id: selectedAssetSha,
        kind: 'advisory',
        mime: asset?.mime,
        filename: asset?.filename,
        size_bytes: asset?.size_bytes,
      })

      if (res.attached) {
        lastAttached.value = { runId: res.run_id, advisoryId: res.advisory_id }

        if (autoNavigate()) {
          router.push({ name: 'RunVariantsReview', params: { run_id: res.run_id } })
        }

        return {
          success: true,
          message: `Attached advisory ${res.advisory_id.slice(0, 10)}… to run ${res.run_id}`,
        }
      } else {
        return { success: true, message: res.message || 'Already attached' }
      }
    } catch (e: any) {
      return { success: false, error: e.message || 'Failed to attach to run' }
    } finally {
      isAttaching.value = false
    }
  }

  function goToReview(runId: string) {
    router.push({ name: 'RunVariantsReview', params: { run_id: runId } })
  }

  return {
    isAttaching,
    lastAttached,
    canAttach,
    attachToRun,
    goToReview,
  }
}
