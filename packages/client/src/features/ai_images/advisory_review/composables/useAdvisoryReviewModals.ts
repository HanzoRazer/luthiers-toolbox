/**
 * Advisory Review Panel modal helpers composable.
 */
import type { Ref } from 'vue'

// ============================================================================
// Types
// ============================================================================

export interface AdvisoryReviewModalsReturn {
  openRejectModal: (assetId: string) => void
  openAttachModal: (assetId: string) => void
}

// ============================================================================
// Composable
// ============================================================================

export function useAdvisoryReviewModals(
  showRejectModal: Ref<boolean>,
  rejectingAssetId: Ref<string | null>,
  rejectionReason: Ref<string>,
  showAttachModal: Ref<boolean>,
  attachingAssetId: Ref<string | null>,
  targetRunId: Ref<string>
): AdvisoryReviewModalsReturn {
  /**
   * Open rejection modal for an asset.
   */
  function openRejectModal(assetId: string): void {
    rejectingAssetId.value = assetId
    rejectionReason.value = ''
    showRejectModal.value = true
  }

  /**
   * Open attachment modal for an asset.
   */
  function openAttachModal(assetId: string): void {
    attachingAssetId.value = assetId
    targetRunId.value = ''
    showAttachModal.value = true
  }

  return {
    openRejectModal,
    openAttachModal
  }
}
