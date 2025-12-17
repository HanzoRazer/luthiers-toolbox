<script setup lang="ts">
/**
 * AI Image Gallery — Grid Display Component
 * 
 * Displays generated images in a grid with selection,
 * actions, and rating capabilities.
 * 
 * @package features/ai_images
 */

import { ref, computed } from 'vue';
import type { ImageAsset, AssetStatus } from './types';

// =============================================================================
// PROPS & EMITS
// =============================================================================

const props = withDefaults(
  defineProps<{
    images: ImageAsset[];
    selectedId: string | null;
    isLoading?: boolean;
    columns?: number;
  }>(),
  {
    isLoading: false,
    columns: 2,
  }
);

const emit = defineEmits<{
  (e: 'select', id: string): void;
  (e: 'attach', id: string): void;
  (e: 'download', id: string): void;
  (e: 'delete', id: string): void;
  (e: 'rate', id: string, rating: number): void;
}>();

// =============================================================================
// LOCAL STATE
// =============================================================================

const hoveredId = ref<string | null>(null);
const ratingImageId = ref<string | null>(null);

// =============================================================================
// COMPUTED
// =============================================================================

const gridStyle = computed(() => ({
  gridTemplateColumns: `repeat(${props.columns}, 1fr)`,
}));

// =============================================================================
// METHODS
// =============================================================================

function getStatusIcon(status: AssetStatus): string {
  switch (status) {
    case 'generating': return '⏳';
    case 'ready': return '';
    case 'failed': return '❌';
    case 'attached': return '📎';
    default: return '';
  }
}

function getProviderLabel(provider: string): string {
  const labels: Record<string, string> = {
    dalle3: 'DALL-E',
    sdxl: 'SDXL',
    guitar_lora: 'LoRA',
    stub: 'STUB',
    auto: 'AUTO',
  };
  return labels[provider] ?? provider.toUpperCase();
}

function formatTime(timestamp: string): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  
  if (diff < 60000) return 'just now';
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
  return date.toLocaleDateString();
}

function handleSelect(image: ImageAsset): void {
  if (image.status === 'generating') return;
  emit('select', image.id);
}

function handleRate(id: string, rating: number): void {
  emit('rate', id, rating);
  ratingImageId.value = null;
}

function confirmDelete(id: string): void {
  if (confirm('Delete this image?')) {
    emit('delete', id);
  }
}
</script>

<template>
  <div class="ai-image-gallery">
    <!-- Header -->
    <div class="gallery-header">
      <h3>Generated Images</h3>
      <span class="gallery-count">{{ images.length }} images</span>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="loading-state">
      <span class="spinner" />
      <span>Loading images...</span>
    </div>

    <!-- Empty State -->
    <div v-else-if="images.length === 0" class="empty-state">
      <span class="empty-icon">🎨</span>
      <p>No images yet</p>
      <p class="empty-hint">Generate your first guitar visualization above</p>
    </div>

    <!-- Grid -->
    <div v-else class="gallery-grid" :style="gridStyle">
      <div
        v-for="image in images"
        :key="image.id"
        class="gallery-item"
        :class="{
          selected: image.id === selectedId,
          generating: image.status === 'generating',
          failed: image.status === 'failed',
          attached: image.status === 'attached',
        }"
        @click="handleSelect(image)"
        @mouseenter="hoveredId = image.id"
        @mouseleave="hoveredId = null"
      >
        <!-- Image -->
        <template v-if="image.status === 'generating'">
          <div class="generating-placeholder">
            <span class="spinner large" />
            <span>Generating...</span>
          </div>
        </template>
        
        <template v-else-if="image.status === 'failed'">
          <div class="failed-placeholder">
            <span class="failed-icon">❌</span>
            <span>Failed</span>
          </div>
        </template>
        
        <template v-else>
          <img
            :src="image.url"
            :alt="image.userPrompt"
            loading="lazy"
          />
        </template>

        <!-- Provider Badge -->
        <span class="provider-badge" v-if="image.status !== 'generating'">
          {{ getProviderLabel(image.provider) }}
        </span>

        <!-- Status Icon -->
        <span class="status-icon" v-if="getStatusIcon(image.status)">
          {{ getStatusIcon(image.status) }}
        </span>

        <!-- Rating Display -->
        <div class="rating-display" v-if="image.rating">
          <span v-for="i in 5" :key="i" class="star" :class="{ filled: i <= image.rating }">
            ★
          </span>
        </div>

        <!-- Hover Actions -->
        <div class="actions" v-if="hoveredId === image.id && image.status === 'ready'">
          <button @click.stop="emit('attach', image.id)" title="Attach to design">
            📎
          </button>
          <button @click.stop="emit('download', image.id)" title="Download">
            ⬇️
          </button>
          <button @click.stop="ratingImageId = image.id" title="Rate">
            ⭐
          </button>
          <button @click.stop="confirmDelete(image.id)" title="Delete" class="danger">
            🗑️
          </button>
        </div>

        <!-- Rating Popup -->
        <div
          v-if="ratingImageId === image.id"
          class="rating-popup"
          @click.stop
        >
          <span class="rating-label">Rate this image</span>
          <div class="rating-stars">
            <button
              v-for="i in 5"
              :key="i"
              class="star-btn"
              :class="{ filled: i <= (image.rating ?? 0) }"
              @click="handleRate(image.id, i)"
            >
              ★
            </button>
          </div>
          <button class="cancel-rating" @click="ratingImageId = null">
            Cancel
          </button>
        </div>

        <!-- Info Overlay (on hover) -->
        <div class="info-overlay" v-if="hoveredId === image.id && image.status === 'ready'">
          <div class="info-prompt">{{ image.userPrompt }}</div>
          <div class="info-meta">
            <span>{{ image.bodyShape ?? 'Guitar' }}</span>
            <span>{{ formatTime(image.createdAt) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.ai-image-gallery {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* Header */
.gallery-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.gallery-header h3 {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-dim, #8892a0);
  text-transform: uppercase;
  margin: 0;
}

.gallery-count {
  font-size: 12px;
  color: var(--text-dim);
}

/* States */
.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: var(--text-dim);
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
  opacity: 0.5;
}

.empty-state p {
  margin: 4px 0;
}

.empty-hint {
  font-size: 12px;
  opacity: 0.7;
}

/* Grid */
.gallery-grid {
  display: grid;
  gap: 10px;
}

/* Item */
.gallery-item {
  aspect-ratio: 1;
  background: var(--bg-input, #0f1629);
  border-radius: 8px;
  border: 2px solid transparent;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: all 0.15s;
}

.gallery-item:hover {
  border-color: var(--accent, #4fc3f7);
}

.gallery-item.selected {
  border-color: var(--success, #4caf50);
}

.gallery-item.generating {
  cursor: wait;
}

.gallery-item.failed {
  opacity: 0.6;
}

.gallery-item.attached {
  border-color: var(--warning, #ff9800);
}

.gallery-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* Placeholders */
.generating-placeholder,
.failed-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: var(--text-dim);
  font-size: 12px;
}

.failed-icon {
  font-size: 24px;
}

/* Spinner */
.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid transparent;
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.spinner.large {
  width: 32px;
  height: 32px;
  border-width: 3px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Badges */
.provider-badge {
  position: absolute;
  top: 6px;
  left: 6px;
  background: rgba(0, 0, 0, 0.7);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 9px;
  color: var(--text, #e0e0e0);
  font-weight: 600;
}

.status-icon {
  position: absolute;
  top: 6px;
  right: 6px;
  font-size: 12px;
}

/* Rating Display */
.rating-display {
  position: absolute;
  bottom: 6px;
  left: 6px;
  display: flex;
  gap: 1px;
}

.rating-display .star {
  font-size: 10px;
  color: var(--text-dim);
}

.rating-display .star.filled {
  color: #ffc107;
}

/* Actions */
.actions {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(transparent, rgba(0, 0, 0, 0.9));
  padding: 24px 8px 8px;
  display: flex;
  justify-content: center;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.15s;
}

.gallery-item:hover .actions {
  opacity: 1;
}

.actions button {
  background: rgba(255, 255, 255, 0.15);
  border: none;
  border-radius: 4px;
  padding: 6px 10px;
  color: var(--text);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s;
}

.actions button:hover {
  background: var(--accent);
  color: #000;
}

.actions button.danger:hover {
  background: #f44336;
  color: #fff;
}

/* Rating Popup */
.rating-popup {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.9);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  z-index: 10;
}

.rating-label {
  font-size: 12px;
  color: var(--text-dim);
}

.rating-stars {
  display: flex;
  gap: 4px;
}

.star-btn {
  background: none;
  border: none;
  font-size: 24px;
  color: var(--text-dim);
  cursor: pointer;
  transition: all 0.15s;
}

.star-btn:hover,
.star-btn.filled {
  color: #ffc107;
  transform: scale(1.2);
}

.cancel-rating {
  background: none;
  border: none;
  color: var(--text-dim);
  font-size: 11px;
  cursor: pointer;
  padding: 4px 8px;
}

.cancel-rating:hover {
  color: var(--text);
}

/* Info Overlay */
.info-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(transparent, rgba(0, 0, 0, 0.9));
  padding: 40px 8px 32px;
  pointer-events: none;
}

.info-prompt {
  font-size: 11px;
  color: var(--text);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.info-meta {
  display: flex;
  justify-content: space-between;
  margin-top: 4px;
  font-size: 10px;
  color: var(--text-dim);
}
</style>
