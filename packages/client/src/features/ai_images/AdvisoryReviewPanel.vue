<script setup lang="ts">
/**
 * Advisory Review Panel — Human-in-the-loop Review Workflow
 *
 * Displays pending AI-generated assets for approval/rejection.
 * Wires to /api/advisory/* endpoints.
 *
 * REFACTORED: Uses composables for cleaner separation of concerns.
 *
 * @package features/ai_images
 */

import { onMounted } from 'vue'
import type { AdvisoryAsset } from './api/advisory'
import AdvisoryAssetList from './advisory_review/AdvisoryAssetList.vue'
import RejectModal from './advisory_review/RejectModal.vue'
import AttachModal from './advisory_review/AttachModal.vue'
import {
  useAdvisoryReviewState,
  useAdvisoryReviewActions,
  useAdvisoryReviewModals
} from './advisory_review/composables'

// =============================================================================
// PROPS & EMITS
// =============================================================================

const props = defineProps<{
  projectId?: string
}>()

const emit = defineEmits<{
  (e: 'asset:approved', asset: AdvisoryAsset): void
  (e: 'asset:rejected', asset: AdvisoryAsset): void
  (e: 'asset:attached', assetId: string, runId: string): void
}>()

// =============================================================================
// COMPOSABLES
// =============================================================================

// State
const {
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
} = useAdvisoryReviewState()

// Actions
const {
  loadPending,
  handleApprove,
  confirmReject,
  handleBulkApprove,
  handleBulkReject,
  confirmAttach,
  toggleSelect,
  toggleSelectAll
} = useAdvisoryReviewActions(
  props.projectId,
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
  allSelected,
  {
    onApproved: (asset) => emit('asset:approved', asset),
    onRejected: (asset) => emit('asset:rejected', asset),
    onAttached: (assetId, runId) => emit('asset:attached', assetId, runId)
  }
)

// Modal helpers
const { openRejectModal, openAttachModal } = useAdvisoryReviewModals(
  showRejectModal,
  rejectingAssetId,
  rejectionReason,
  showAttachModal,
  attachingAssetId,
  targetRunId
)

// =============================================================================
// LIFECYCLE
// =============================================================================

onMounted(loadPending)
</script>

<template>
  <div class="advisory-review-panel">
    <!-- Header -->
    <div class="panel-header">
      <h2>🔍 Review Queue</h2>
      <div
        v-if="stats"
        class="stats"
      >
        <span class="stat pending">{{ stats.pending }} pending</span>
        <span class="stat approved">{{ stats.approved }} approved</span>
        <span class="stat rejected">{{ stats.rejected }} rejected</span>
      </div>
    </div>

    <!-- Bulk Actions -->
    <div
      v-if="pendingAssets.length > 0"
      class="bulk-actions"
    >
      <label class="select-all">
        <input 
          type="checkbox" 
          :checked="allSelected"
          @change="toggleSelectAll"
        >
        Select All
      </label>
      <div
        v-if="hasSelection"
        class="action-buttons"
      >
        <button
          class="btn approve"
          @click="handleBulkApprove"
        >
          ✓ Approve Selected ({{ selectedIds.size }})
        </button>
        <button
          class="btn reject"
          @click="handleBulkReject"
        >
          ✗ Reject Selected
        </button>
      </div>
    </div>

    <!-- Error -->
    <div
      v-if="error"
      class="error-banner"
    >
      {{ error }}
      <button @click="error = null">
        ×
      </button>
    </div>

    <!-- Loading -->
    <div
      v-if="isLoading"
      class="loading"
    >
      <span class="spinner" />
      Loading pending assets...
    </div>

    <!-- Empty State -->
    <div
      v-else-if="pendingAssets.length === 0"
      class="empty-state"
    >
      <span class="icon">✨</span>
      <p>No assets pending review</p>
    </div>

    <!-- Asset List -->
    <AdvisoryAssetList
      v-else
      :assets="pendingAssets"
      :selected-ids="selectedIds"
      @toggle-select="toggleSelect"
      @approve="handleApprove"
      @open-reject="openRejectModal"
      @open-attach="openAttachModal"
    />

    <!-- Reject Modal -->
    <RejectModal
      v-model:visible="showRejectModal"
      v-model:rejection-reason="rejectionReason"
      @confirm="confirmReject"
    />

    <!-- Attach Modal -->
    <AttachModal
      v-model:visible="showAttachModal"
      v-model:target-run-id="targetRunId"
      @confirm="confirmAttach"
    />
  </div>
</template>

<style scoped>
.advisory-review-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-panel, #16213e);
  color: var(--text, #e0e0e0);
}

.panel-header {
  padding: 16px;
  border-bottom: 1px solid var(--border, #2a3f5f);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-header h2 {
  margin: 0;
  font-size: 16px;
}

.stats {
  display: flex;
  gap: 12px;
  font-size: 12px;
}

.stat {
  padding: 4px 8px;
  border-radius: 4px;
  background: var(--bg-input, #0f1629);
}

.stat.pending { color: #ffc107; }
.stat.approved { color: #4caf50; }
.stat.rejected { color: #f44336; }

.bulk-actions {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.select-all {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  cursor: pointer;
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.btn {
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s;
}

.btn.approve {
  background: #4caf50;
  color: white;
}

.btn.reject {
  background: #f44336;
  color: white;
}

.btn.attach {
  background: var(--accent, #4fc3f7);
  color: black;
}

.btn.cancel {
  background: var(--bg-input);
  color: var(--text);
  border: 1px solid var(--border);
}

.btn.primary {
  background: var(--accent);
  color: black;
}

.btn:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.error-banner {
  margin: 12px 16px;
  padding: 10px 16px;
  background: rgba(244, 67, 54, 0.1);
  border: 1px solid #f44336;
  border-radius: 6px;
  display: flex;
  justify-content: space-between;
  color: #f44336;
  font-size: 13px;
}

.error-banner button {
  background: none;
  border: none;
  color: #f44336;
  cursor: pointer;
}

.loading, .empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-dim, #8892a0);
}

.empty-state .icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.spinner {
  width: 24px;
  height: 24px;
  border: 2px solid transparent;
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 12px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.asset-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.asset-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: var(--bg-input);
  border-radius: 8px;
  border: 2px solid transparent;
  transition: all 0.15s;
}

.asset-card.selected {
  border-color: var(--accent);
}

.asset-card:hover {
  background: rgba(79, 195, 247, 0.05);
}

.checkbox {
  cursor: pointer;
}

.thumbnail {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: 6px;
}

.asset-info {
  flex: 1;
  min-width: 0;
}

.prompt {
  font-size: 13px;
  margin-bottom: 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.meta {
  display: flex;
  gap: 12px;
  font-size: 11px;
  color: var(--text-dim);
}

.asset-actions {
  display: flex;
  gap: 6px;
}

.asset-actions .btn {
  width: 32px;
  height: 32px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: var(--bg-panel);
  border-radius: 12px;
  padding: 24px;
  min-width: 320px;
  max-width: 480px;
}

.modal h3 {
  margin: 0 0 16px;
  font-size: 16px;
}

.modal textarea,
.modal input {
  width: 100%;
  background: var(--bg-input);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 10px;
  color: var(--text);
  font-size: 13px;
  margin-bottom: 16px;
}

.modal textarea:focus,
.modal input:focus {
  outline: none;
  border-color: var(--accent);
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
