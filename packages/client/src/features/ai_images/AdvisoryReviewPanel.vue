<script setup lang="ts">
/**
 * Advisory Review Panel — Human-in-the-loop Review Workflow
 * 
 * Displays pending AI-generated assets for approval/rejection.
 * Wires to /api/advisory/* endpoints.
 * 
 * @package features/ai_images
 */

import { ref, computed, onMounted } from 'vue';
import {
  listAssets,
  approveAsset,
  rejectAsset,
  bulkReview,
  getPendingAssets,
  attachToRun,
  getStats as getAdvisoryStats,
  type AdvisoryAsset,
  type AdvisoryStats,
} from './api/advisory';

// =============================================================================
// PROPS & EMITS
// =============================================================================

const props = defineProps<{
  projectId?: string;
}>();

const emit = defineEmits<{
  (e: 'asset:approved', asset: AdvisoryAsset): void;
  (e: 'asset:rejected', asset: AdvisoryAsset): void;
  (e: 'asset:attached', assetId: string, runId: string): void;
}>();

// =============================================================================
// STATE
// =============================================================================

const pendingAssets = ref<AdvisoryAsset[]>([]);
const stats = ref<AdvisoryStats | null>(null);
const selectedIds = ref<Set<string>>(new Set());
const isLoading = ref(false);
const error = ref<string | null>(null);

// Rejection modal state
const showRejectModal = ref(false);
const rejectingAssetId = ref<string | null>(null);
const rejectionReason = ref('');

// Attachment modal state
const showAttachModal = ref(false);
const attachingAssetId = ref<string | null>(null);
const targetRunId = ref('');

// =============================================================================
// COMPUTED
// =============================================================================

const hasSelection = computed(() => selectedIds.value.size > 0);
const allSelected = computed(() => 
  pendingAssets.value.length > 0 && 
  selectedIds.value.size === pendingAssets.value.length
);

// =============================================================================
// METHODS
// =============================================================================

async function loadPending(): Promise<void> {
  isLoading.value = true;
  error.value = null;
  
  try {
    pendingAssets.value = await getPendingAssets(props.projectId, 50);
    stats.value = await getAdvisoryStats(props.projectId);
  } catch (err) {
    error.value = `Failed to load: ${err}`;
  } finally {
    isLoading.value = false;
  }
}

async function handleApprove(assetId: string): Promise<void> {
  try {
    const approved = await approveAsset(assetId);
    pendingAssets.value = pendingAssets.value.filter((a: AdvisoryAsset) => a.id !== assetId);
    selectedIds.value.delete(assetId);
    emit('asset:approved', approved);
  } catch (err) {
    error.value = `Failed to approve: ${err}`;
  }
}

function openRejectModal(assetId: string): void {
  rejectingAssetId.value = assetId;
  rejectionReason.value = '';
  showRejectModal.value = true;
}

async function confirmReject(): Promise<void> {
  if (!rejectingAssetId.value || !rejectionReason.value.trim()) return;
  
  try {
    const rejected = await rejectAsset(rejectingAssetId.value, rejectionReason.value);
    pendingAssets.value = pendingAssets.value.filter((a: AdvisoryAsset) => a.id !== rejectingAssetId.value);
    selectedIds.value.delete(rejectingAssetId.value!);
    showRejectModal.value = false;
    emit('asset:rejected', rejected);
  } catch (err) {
    error.value = `Failed to reject: ${err}`;
  }
}

async function handleBulkApprove(): Promise<void> {
  if (!hasSelection.value) return;
  
  try {
    const ids = Array.from(selectedIds.value) as string[];
    await bulkReview(ids, 'approve');
    pendingAssets.value = pendingAssets.value.filter((a: AdvisoryAsset) => !selectedIds.value.has(a.id));
    selectedIds.value.clear();
  } catch (err) {
    error.value = `Bulk approve failed: ${err}`;
  }
}

async function handleBulkReject(): Promise<void> {
  if (!hasSelection.value) return;
  
  const reason = prompt('Enter rejection reason for all selected:');
  if (!reason) return;
  
  try {
    const ids = Array.from(selectedIds.value) as string[];
    await bulkReview(ids, 'reject', reason);
    pendingAssets.value = pendingAssets.value.filter((a: AdvisoryAsset) => !selectedIds.value.has(a.id));
    selectedIds.value.clear();
  } catch (err) {
    error.value = `Bulk reject failed: ${err}`;
  }
}

function openAttachModal(assetId: string): void {
  attachingAssetId.value = assetId;
  targetRunId.value = '';
  showAttachModal.value = true;
}

async function confirmAttach(): Promise<void> {
  if (!attachingAssetId.value || !targetRunId.value.trim()) return;
  
  try {
    await attachToRun(attachingAssetId.value, targetRunId.value);
    showAttachModal.value = false;
    emit('asset:attached', attachingAssetId.value, targetRunId.value);
    await loadPending(); // Refresh list
  } catch (err) {
    error.value = `Failed to attach: ${err}`;
  }
}

function toggleSelect(assetId: string): void {
  if (selectedIds.value.has(assetId)) {
    selectedIds.value.delete(assetId);
  } else {
    selectedIds.value.add(assetId);
  }
}

function toggleSelectAll(): void {
  if (allSelected.value) {
    selectedIds.value.clear();
  } else {
    selectedIds.value = new Set(pendingAssets.value.map((a: AdvisoryAsset) => a.id));
  }
}

// =============================================================================
// LIFECYCLE
// =============================================================================

onMounted(loadPending);
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
    <div
      v-else
      class="asset-list"
    >
      <div 
        v-for="asset in pendingAssets" 
        :key="asset.id"
        class="asset-card"
        :class="{ selected: selectedIds.has(asset.id) }"
      >
        <label class="checkbox">
          <input 
            type="checkbox"
            :checked="selectedIds.has(asset.id)"
            @change="toggleSelect(asset.id)"
          >
        </label>

        <img
          :src="asset.imageUrl"
          :alt="asset.prompt"
          class="thumbnail"
        >

        <div class="asset-info">
          <div class="prompt">
            {{ asset.prompt }}
          </div>
          <div class="meta">
            <span class="provider">{{ asset.provider }}</span>
            <span class="category">{{ asset.category }}</span>
            <span class="cost">${{ asset.cost.toFixed(3) }}</span>
          </div>
        </div>

        <div class="asset-actions">
          <button
            class="btn approve"
            title="Approve"
            @click="handleApprove(asset.id)"
          >
            ✓
          </button>
          <button
            class="btn reject"
            title="Reject"
            @click="openRejectModal(asset.id)"
          >
            ✗
          </button>
          <button
            class="btn attach"
            title="Attach to Run"
            @click="openAttachModal(asset.id)"
          >
            📎
          </button>
        </div>
      </div>
    </div>

    <!-- Reject Modal -->
    <div
      v-if="showRejectModal"
      class="modal-overlay"
      @click.self="showRejectModal = false"
    >
      <div class="modal">
        <h3>Reject Asset</h3>
        <textarea 
          v-model="rejectionReason"
          placeholder="Enter rejection reason..."
          rows="3"
        />
        <div class="modal-actions">
          <button
            class="btn cancel"
            @click="showRejectModal = false"
          >
            Cancel
          </button>
          <button 
            class="btn reject" 
            :disabled="!rejectionReason.trim()"
            @click="confirmReject"
          >
            Reject
          </button>
        </div>
      </div>
    </div>

    <!-- Attach Modal -->
    <div
      v-if="showAttachModal"
      class="modal-overlay"
      @click.self="showAttachModal = false"
    >
      <div class="modal">
        <h3>Attach to Run</h3>
        <input 
          v-model="targetRunId"
          placeholder="Enter Run ID..."
          type="text"
        >
        <div class="modal-actions">
          <button
            class="btn cancel"
            @click="showAttachModal = false"
          >
            Cancel
          </button>
          <button 
            class="btn primary" 
            :disabled="!targetRunId.trim()"
            @click="confirmAttach"
          >
            Attach
          </button>
        </div>
      </div>
    </div>
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
