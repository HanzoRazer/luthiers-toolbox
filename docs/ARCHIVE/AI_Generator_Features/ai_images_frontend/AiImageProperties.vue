<script setup lang="ts">
/**
 * AI Image Properties — Detail Panel Component
 * 
 * Shows details and actions for the selected image.
 * Typically displayed in a right sidebar.
 * 
 * @package features/ai_images
 */

import { computed } from 'vue';
import { useAiImageStore } from './useAiImageStore';
import type { ImageAsset } from './types';

// =============================================================================
// PROPS & EMITS
// =============================================================================

const props = defineProps<{
  image: ImageAsset | null;
}>();

const emit = defineEmits<{
  (e: 'attach'): void;
  (e: 'download'): void;
  (e: 'regenerate'): void;
  (e: 'delete'): void;
  (e: 'rate', rating: number): void;
}>();

// =============================================================================
// STORE
// =============================================================================

const store = useAiImageStore();

// =============================================================================
// COMPUTED
// =============================================================================

const formattedDate = computed(() => {
  if (!props.image) return '';
  const date = new Date(props.image.createdAt);
  return date.toLocaleString();
});

const providerName = computed(() => {
  if (!props.image) return '';
  const names: Record<string, string> = {
    dalle3: 'DALL-E 3',
    sdxl: 'Stable Diffusion XL',
    guitar_lora: 'Guitar LoRA',
    stub: 'Stub (Testing)',
    auto: 'Auto',
  };
  return names[props.image.provider] ?? props.image.provider;
});

const categoryName = computed(() => {
  if (!props.image) return '';
  return props.image.category.charAt(0).toUpperCase() + props.image.category.slice(1);
});

// =============================================================================
// METHODS
// =============================================================================

function copyPrompt(): void {
  if (!props.image) return;
  navigator.clipboard.writeText(props.image.engineeredPrompt);
}
</script>

<template>
  <div class="ai-image-properties">
    <!-- No Selection -->
    <div v-if="!image" class="no-selection">
      <span class="icon">🖼️</span>
      <p>Select an image to view details</p>
    </div>

    <!-- Image Details -->
    <template v-else>
      <!-- Preview -->
      <div class="preview-section">
        <img :src="image.url" :alt="image.userPrompt" class="preview-image" />
      </div>

      <!-- Details Section -->
      <div class="details-section">
        <h4>Image Details</h4>
        
        <div class="property-row">
          <span class="label">ID</span>
          <span class="value mono">{{ image.id.slice(0, 10) }}...</span>
        </div>
        
        <div class="property-row">
          <span class="label">Provider</span>
          <span class="value accent">{{ providerName }}</span>
        </div>
        
        <div class="property-row">
          <span class="label">Size</span>
          <span class="value">{{ image.size }}</span>
        </div>
        
        <div class="property-row">
          <span class="label">Quality</span>
          <span class="value">{{ image.quality }}</span>
        </div>
        
        <div class="property-row">
          <span class="label">Style</span>
          <span class="value">{{ image.style }}</span>
        </div>
        
        <div class="property-row">
          <span class="label">Cost</span>
          <span class="value">${{ image.cost.toFixed(4) }}</span>
        </div>
        
        <div class="property-row">
          <span class="label">Generated</span>
          <span class="value">{{ formattedDate }}</span>
        </div>
        
        <div class="property-row" v-if="image.attachedTo">
          <span class="label">Attached to</span>
          <span class="value accent">{{ image.attachedTo }}</span>
        </div>
      </div>

      <!-- Prompt Section -->
      <div class="prompt-section">
        <div class="section-header">
          <h4>Prompt</h4>
          <button class="copy-btn" @click="copyPrompt" title="Copy prompt">
            📋
          </button>
        </div>
        
        <div class="prompt-display">
          {{ image.engineeredPrompt }}
        </div>
        
        <div class="property-row">
          <span class="label">Detected</span>
          <span class="value">{{ categoryName }} / {{ image.bodyShape ?? 'Unknown' }}</span>
        </div>
        
        <div class="property-row" v-if="image.finish">
          <span class="label">Finish</span>
          <span class="value">{{ image.finish }}</span>
        </div>
      </div>

      <!-- Rating Section -->
      <div class="rating-section">
        <h4>Rating</h4>
        <div class="rating-stars">
          <button
            v-for="i in 5"
            :key="i"
            class="star-btn"
            :class="{ filled: i <= (image.rating ?? 0) }"
            @click="emit('rate', i)"
          >
            ★
          </button>
        </div>
        <p class="rating-hint">Rate to improve AI routing</p>
      </div>

      <!-- Actions Section -->
      <div class="actions-section">
        <h4>Actions</h4>
        
        <button class="action-btn primary" @click="emit('attach')">
          <span>📎</span>
          <span>Attach to Design</span>
        </button>
        
        <button class="action-btn" @click="emit('download')">
          <span>⬇️</span>
          <span>Download PNG</span>
        </button>
        
        <button class="action-btn" @click="emit('regenerate')">
          <span>🔄</span>
          <span>Regenerate</span>
        </button>
        
        <button class="action-btn danger" @click="emit('delete')">
          <span>🗑️</span>
          <span>Delete</span>
        </button>
      </div>

      <!-- Session Stats -->
      <div class="stats-section">
        <h4>Session Stats</h4>
        
        <div class="property-row">
          <span class="label">Images today</span>
          <span class="value">{{ store.sessionCount }}</span>
        </div>
        
        <div class="property-row">
          <span class="label">Total cost</span>
          <span class="value">${{ store.totalCost.toFixed(2) }}</span>
        </div>
        
        <div class="property-row" v-if="store.providerStats[image.provider]">
          <span class="label">{{ providerName }} count</span>
          <span class="value">{{ store.providerStats[image.provider]?.count ?? 0 }}</span>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.ai-image-properties {
  display: flex;
  flex-direction: column;
  gap: 0;
  height: 100%;
  overflow-y: auto;
  background: var(--bg-panel, #16213e);
  color: var(--text, #e0e0e0);
}

/* No Selection */
.no-selection {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: var(--text-dim, #8892a0);
  text-align: center;
}

.no-selection .icon {
  font-size: 48px;
  margin-bottom: 12px;
  opacity: 0.5;
}

/* Preview */
.preview-section {
  padding: 16px;
  border-bottom: 1px solid var(--border, #2a3f5f);
}

.preview-image {
  width: 100%;
  border-radius: 8px;
}

/* Sections */
.details-section,
.prompt-section,
.rating-section,
.actions-section,
.stats-section {
  padding: 16px;
  border-bottom: 1px solid var(--border);
}

h4 {
  font-size: 12px;
  color: var(--text-dim);
  text-transform: uppercase;
  margin: 0 0 12px 0;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border);
}

/* Property Rows */
.property-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 13px;
}

.property-row .label {
  color: var(--text-dim);
}

.property-row .value {
  color: var(--text);
}

.property-row .value.accent {
  color: var(--accent, #4fc3f7);
}

.property-row .value.mono {
  font-family: monospace;
  font-size: 12px;
}

/* Prompt Section */
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-header h4 {
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
}

.copy-btn {
  background: none;
  border: none;
  font-size: 14px;
  cursor: pointer;
  padding: 4px;
  opacity: 0.6;
}

.copy-btn:hover {
  opacity: 1;
}

.prompt-display {
  background: var(--bg-input, #0f1629);
  border-radius: 6px;
  padding: 10px;
  font-size: 12px;
  line-height: 1.5;
  color: var(--text-dim);
  margin: 12px 0;
}

/* Rating */
.rating-stars {
  display: flex;
  gap: 4px;
  margin-bottom: 8px;
}

.star-btn {
  background: none;
  border: none;
  font-size: 24px;
  color: var(--text-dim);
  cursor: pointer;
  transition: all 0.15s;
  padding: 0;
}

.star-btn:hover,
.star-btn.filled {
  color: #ffc107;
}

.rating-hint {
  font-size: 11px;
  color: var(--text-dim);
  margin: 0;
}

/* Actions */
.actions-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.actions-section h4 {
  margin-bottom: 8px;
}

.action-btn {
  background: var(--bg-input);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 10px 12px;
  color: var(--text);
  font-size: 13px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.15s;
}

.action-btn:hover {
  border-color: var(--accent);
  background: rgba(79, 195, 247, 0.1);
}

.action-btn.primary {
  background: var(--accent);
  border-color: var(--accent);
  color: #000;
}

.action-btn.primary:hover {
  background: var(--accent-hover, #81d4fa);
}

.action-btn.danger:hover {
  border-color: #f44336;
  background: rgba(244, 67, 54, 0.1);
  color: #f44336;
}
</style>
