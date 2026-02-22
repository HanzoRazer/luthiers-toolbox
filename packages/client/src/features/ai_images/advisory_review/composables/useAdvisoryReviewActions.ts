/**
 * Advisory Review Panel actions composable.
 */
import type { Ref } from 'vue'
import {
  getPendingAssets,
  getStats as getAdvisoryStats,
  approveAsset,
  rejectAsset,
  bulkReview,
  attachToRun,
  type AdvisoryAsset,
  type AdvisoryStats
} from '../../api/advisory'

// ============================================================================
// Types
// ============================================================================

export interface AdvisoryReviewActionsReturn {
  loadPending: () => Promise<void>
  handleApprove: (assetId: string) => Promise<void>
  confirmReject: () => Promise<void>
  handleBulkApprove: () => Promise<void>
  handleBulkReject: () => Promise<void>
  confirmAttach: () => Promise<void>
  toggleSelect: (assetId: string) => void
  toggleSelectAll: () => void
}

export interface AdvisoryReviewEmits {
  onApproved: (asset: AdvisoryAsset) => void
  onRejected: (asset: AdvisoryAsset) => void
  onAttached: (assetId: string, runId: string) => void
}

// ============================================================================
// Composable
// ============================================================================

export function useAdvisoryReviewActions(
  projectId: string | undefined,
  pendingAssets: Ref<AdvisoryAsset[]>,
  stats: Ref<AdvisoryStats | null>,
  selectedIds: Ref<Set<string>>,
  isLoading: Ref<boolean>,
  error: Ref<string | null>,
  showRejectModal: Ref<boolean>,
  rejectingAssetId: Ref<string | null>,
  rejectionReason: Ref<string>,
  showAttachModal: Ref<boolean>,
  attachingAssetId: Ref<string | null>,
  targetRunId: Ref<string>,
  hasSelection: { value: boolean },
  allSelected: { value: boolean },
  emits: AdvisoryReviewEmits
): AdvisoryReviewActionsReturn {
  /**
   * Load pending assets from API.
   */
  async function loadPending(): Promise<void> {
    isLoading.value = true
    error.value = null

    try {
      pendingAssets.value = await getPendingAssets(projectId, 50)
      stats.value = await getAdvisoryStats(projectId)
    } catch (err) {
      error.value = `Failed to load: ${err}`
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Approve a single asset.
   */
  async function handleApprove(assetId: string): Promise<void> {
    try {
      const approved = await approveAsset(assetId)
      pendingAssets.value = pendingAssets.value.filter(
        (a: AdvisoryAsset) => a.id !== assetId
      )
      selectedIds.value.delete(assetId)
      emits.onApproved(approved)
    } catch (err) {
      error.value = `Failed to approve: ${err}`
    }
  }

  /**
   * Confirm rejection with reason.
   */
  async function confirmReject(): Promise<void> {
    if (!rejectingAssetId.value || !rejectionReason.value.trim()) return

    try {
      const rejected = await rejectAsset(
        rejectingAssetId.value,
        rejectionReason.value
      )
      pendingAssets.value = pendingAssets.value.filter(
        (a: AdvisoryAsset) => a.id !== rejectingAssetId.value
      )
      selectedIds.value.delete(rejectingAssetId.value!)
      showRejectModal.value = false
      emits.onRejected(rejected)
    } catch (err) {
      error.value = `Failed to reject: ${err}`
    }
  }

  /**
   * Bulk approve selected assets.
   */
  async function handleBulkApprove(): Promise<void> {
    if (!hasSelection.value) return

    try {
      const ids = Array.from(selectedIds.value) as string[]
      await bulkReview(ids, 'approve')
      pendingAssets.value = pendingAssets.value.filter(
        (a: AdvisoryAsset) => !selectedIds.value.has(a.id)
      )
      selectedIds.value.clear()
    } catch (err) {
      error.value = `Bulk approve failed: ${err}`
    }
  }

  /**
   * Bulk reject selected assets.
   */
  async function handleBulkReject(): Promise<void> {
    if (!hasSelection.value) return

    const reason = prompt('Enter rejection reason for all selected:')
    if (!reason) return

    try {
      const ids = Array.from(selectedIds.value) as string[]
      await bulkReview(ids, 'reject', reason)
      pendingAssets.value = pendingAssets.value.filter(
        (a: AdvisoryAsset) => !selectedIds.value.has(a.id)
      )
      selectedIds.value.clear()
    } catch (err) {
      error.value = `Bulk reject failed: ${err}`
    }
  }

  /**
   * Confirm attachment to run.
   */
  async function confirmAttach(): Promise<void> {
    if (!attachingAssetId.value || !targetRunId.value.trim()) return

    try {
      await attachToRun(attachingAssetId.value, targetRunId.value)
      showAttachModal.value = false
      emits.onAttached(attachingAssetId.value, targetRunId.value)
      await loadPending() // Refresh list
    } catch (err) {
      error.value = `Failed to attach: ${err}`
    }
  }

  /**
   * Toggle selection for an asset.
   */
  function toggleSelect(assetId: string): void {
    if (selectedIds.value.has(assetId)) {
      selectedIds.value.delete(assetId)
    } else {
      selectedIds.value.add(assetId)
    }
  }

  /**
   * Toggle select all assets.
   */
  function toggleSelectAll(): void {
    if (allSelected.value) {
      selectedIds.value.clear()
    } else {
      selectedIds.value = new Set(
        pendingAssets.value.map((a: AdvisoryAsset) => a.id)
      )
    }
  }

  return {
    loadPending,
    handleApprove,
    confirmReject,
    handleBulkApprove,
    handleBulkReject,
    confirmAttach,
    toggleSelect,
    toggleSelectAll
  }
}
