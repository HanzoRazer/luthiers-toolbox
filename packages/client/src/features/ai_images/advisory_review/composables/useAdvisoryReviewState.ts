/**
 * Advisory Review Panel state composable.
 */
import { ref, computed, type Ref, type ComputedRef } from 'vue'
import type { AdvisoryAsset, AdvisoryStats } from '../../api/advisory'

// ============================================================================
// Types
// ============================================================================

export interface AdvisoryReviewStateReturn {
  // Core state
  pendingAssets: Ref<AdvisoryAsset[]>
  stats: Ref<AdvisoryStats | null>
  selectedIds: Ref<Set<string>>
  isLoading: Ref<boolean>
  error: Ref<string | null>

  // Rejection modal
  showRejectModal: Ref<boolean>
  rejectingAssetId: Ref<string | null>
  rejectionReason: Ref<string>

  // Attachment modal
  showAttachModal: Ref<boolean>
  attachingAssetId: Ref<string | null>
  targetRunId: Ref<string>

  // Computed
  hasSelection: ComputedRef<boolean>
  allSelected: ComputedRef<boolean>
}

// ============================================================================
// Composable
// ============================================================================

export function useAdvisoryReviewState(): AdvisoryReviewStateReturn {
  // Core state
  const pendingAssets = ref<AdvisoryAsset[]>([])
  const stats = ref<AdvisoryStats | null>(null)
  const selectedIds = ref<Set<string>>(new Set())
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Rejection modal state
  const showRejectModal = ref(false)
  const rejectingAssetId = ref<string | null>(null)
  const rejectionReason = ref('')

  // Attachment modal state
  const showAttachModal = ref(false)
  const attachingAssetId = ref<string | null>(null)
  const targetRunId = ref('')

  // Computed
  const hasSelection = computed(() => selectedIds.value.size > 0)
  const allSelected = computed(
    () =>
      pendingAssets.value.length > 0 &&
      selectedIds.value.size === pendingAssets.value.length
  )

  return {
    pendingAssets,
    stats,
    selectedIds,
    isLoading,
    error,
    showRejectModal,
    rejectingAssetId,
    rejectionReason,
    showAttachModal,
    attachingAssetId,
    targetRunId,
    hasSelection,
    allSelected
  }
}
