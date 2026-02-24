<script setup lang="ts">
/**
 * AdvisoryAssetList - Asset cards list for review
 * Extracted from AdvisoryReviewPanel.vue
 */
import type { AdvisoryAsset } from '../api/advisory'

defineProps<{
  assets: AdvisoryAsset[]
  selectedIds: Set<string>
}>()

const emit = defineEmits<{
  'toggle-select': [assetId: string]
  'approve': [assetId: string]
  'open-reject': [assetId: string]
  'open-attach': [assetId: string]
}>()
</script>

<template>
  <div class="asset-list">
    <div
      v-for="asset in assets"
      :key="asset.id"
      class="asset-card"
      :class="{ selected: selectedIds.has(asset.id) }"
    >
      <label class="checkbox">
        <input
          type="checkbox"
          :checked="selectedIds.has(asset.id)"
          @change="emit('toggle-select', asset.id)"
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
          @click="emit('approve', asset.id)"
        >
          ✓
        </button>
        <button
          class="btn reject"
          title="Reject"
          @click="emit('open-reject', asset.id)"
        >
          ✗
        </button>
        <button
          class="btn attach"
          title="Attach to Run"
          @click="emit('open-attach', asset.id)"
        >
          📎
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
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
  background: var(--bg-input, #0f1629);
  border-radius: 8px;
  border: 2px solid transparent;
  transition: all 0.15s;
}

.asset-card.selected {
  border-color: var(--accent, #4fc3f7);
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
  color: var(--text-dim, #8892a0);
}

.asset-actions {
  display: flex;
  gap: 6px;
}

.btn {
  width: 32px;
  height: 32px;
  padding: 0;
  border: none;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
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

.btn:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}
</style>
