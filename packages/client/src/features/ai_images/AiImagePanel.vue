<script setup lang="ts">
/**
 * AI Image Panel — Main Component
 * 
 * Provides prompt input, generation options, and gallery display.
 * This is the primary interface for the AI image generation feature.
 * 
 * @package features/ai_images
 */

import { ref, computed, watch, onMounted } from 'vue';
import { useAiImageStore } from './useAiImageStore';
import AiImageGallery from './AiImageGallery.vue';
import type {
  ImageProvider,
  ImageQuality,
  PhotoStyle,
  QuickTag,
} from './types';

// =============================================================================
// PROPS & EMITS
// =============================================================================

const props = defineProps<{
  projectId: string;
}>();

const emit = defineEmits<{
  (e: 'image:select', id: string): void;
  (e: 'image:attach', imageId: string, targetId: string): void;
  (e: 'close'): void;
}>();

// =============================================================================
// STORE
// =============================================================================

const store = useAiImageStore();

// =============================================================================
// LOCAL STATE
// =============================================================================

const prompt = ref('');
const selectedStyle = ref<PhotoStyle>('product');
const selectedProvider = ref<ImageProvider>('auto');
const selectedQuality = ref<ImageQuality>('standard');
const imageCount = ref(2);

const showAdvanced = ref(false);
const promptPreview = ref<string | null>(null);
const previewConfidence = ref(0);

// =============================================================================
// COMPUTED
// =============================================================================

const costEstimate = computed(() => {
  return store.getEstimate(imageCount.value, selectedQuality.value, selectedProvider.value);
});

const canGenerate = computed(() => {
  return prompt.value.trim().length > 0 && !store.isGenerating;
});

const providerOptions = computed(() => {
  const options = [{ value: 'auto', label: 'Auto (Best)' }];
  
  for (const provider of store.providers) {
    options.push({
      value: provider.id,
      label: `${provider.name}${provider.available ? '' : ' (unavailable)'}`,
    });
  }
  
  return options;
});

// =============================================================================
// QUICK TAGS
// =============================================================================

const quickTags: QuickTag[] = [
  { label: 'Les Paul', value: 'les paul', category: 'body' },
  { label: 'Strat', value: 'stratocaster', category: 'body' },
  { label: 'Tele', value: 'telecaster', category: 'body' },
  { label: 'Dreadnought', value: 'dreadnought', category: 'body' },
  { label: 'ES-335', value: 'es-335', category: 'body' },
  { label: 'Sunburst', value: 'sunburst', category: 'finish' },
  { label: 'Black', value: 'black', category: 'finish' },
  { label: 'Natural', value: 'natural', category: 'finish' },
  { label: 'Gold HW', value: 'gold hardware', category: 'hardware' },
  { label: 'Chrome HW', value: 'chrome hardware', category: 'hardware' },
  { label: 'Flame', value: 'flame maple top', category: 'wood' },
  { label: 'Quilted', value: 'quilted maple', category: 'wood' },
];

// =============================================================================
// METHODS
// =============================================================================

function addTag(tag: QuickTag): void {
  const current = prompt.value.trim();
  if (current) {
    prompt.value = `${current}, ${tag.value}`;
  } else {
    prompt.value = tag.value;
  }
}

async function generate(): Promise<void> {
  if (!canGenerate.value) return;
  
  try {
    await store.generate({
      prompt: prompt.value,
      numImages: imageCount.value,
      quality: selectedQuality.value,
      style: selectedStyle.value,
      provider: selectedProvider.value,
      projectId: props.projectId,
    });
  } catch (err) {
    console.error('Generation failed:', err);
  }
}

async function updatePreview(): Promise<void> {
  if (!prompt.value.trim()) {
    promptPreview.value = null;
    return;
  }
  
  try {
    const result = await store.previewPrompt(prompt.value, selectedStyle.value);
    promptPreview.value = result.positivePrompt;
    previewConfidence.value = result.confidence;
  } catch (err) {
    promptPreview.value = null;
  }
}

function handleImageSelect(id: string): void {
  store.selectImage(id);
  emit('image:select', id);
}

function handleAttach(imageId: string): void {
  emit('image:attach', imageId, ''); // Target determined by parent
}

// =============================================================================
// LIFECYCLE
// =============================================================================

onMounted(async () => {
  await store.initialize(props.projectId);
});

// Debounced preview update
let previewTimeout: number | null = null;
watch(prompt, () => {
  if (previewTimeout) clearTimeout(previewTimeout);
  previewTimeout = window.setTimeout(updatePreview, 500);
});
</script>

<template>
  <div class="ai-image-panel">
    <!-- Header -->
    <div class="panel-header">
      <span class="icon">🎸</span>
      <h2>AI Image Generator</h2>
      <span class="beta-badge">BETA</span>
      <button class="close-btn" @click="emit('close')" title="Close">×</button>
    </div>

    <!-- Prompt Section -->
    <div class="prompt-section">
      <label class="section-label">Describe your guitar</label>
      <textarea
        v-model="prompt"
        class="prompt-textarea"
        placeholder="emerald green les paul with gold hardware, flame maple top..."
        rows="3"
      />

      <!-- Quick Tags -->
      <div class="quick-tags">
        <button
          v-for="tag in quickTags"
          :key="tag.value"
          class="quick-tag"
          :class="tag.category"
          @click="addTag(tag)"
        >
          {{ tag.label }}
        </button>
      </div>

      <!-- Prompt Preview -->
      <div v-if="promptPreview" class="prompt-preview">
        <div class="preview-label">
          <span>Engineered prompt</span>
          <span class="confidence">{{ Math.round(previewConfidence * 100) }}% confidence</span>
        </div>
        <div class="preview-text">{{ promptPreview }}</div>
      </div>
    </div>

    <!-- Options Section -->
    <div class="options-section">
      <div class="options-grid">
        <div class="option-group">
          <label>Style</label>
          <select v-model="selectedStyle">
            <option value="product">Product Shot</option>
            <option value="dramatic">Dramatic</option>
            <option value="studio">Studio</option>
            <option value="lifestyle">Lifestyle</option>
            <option value="vintage">Vintage</option>
            <option value="cinematic">Cinematic</option>
          </select>
        </div>

        <div class="option-group">
          <label>Provider</label>
          <select v-model="selectedProvider">
            <option
              v-for="opt in providerOptions"
              :key="opt.value"
              :value="opt.value"
            >
              {{ opt.label }}
            </option>
          </select>
        </div>

        <div class="option-group">
          <label>Quality</label>
          <select v-model="selectedQuality">
            <option value="draft">Draft</option>
            <option value="standard">Standard</option>
            <option value="hd">HD (+$)</option>
          </select>
        </div>

        <div class="option-group">
          <label>Count</label>
          <select v-model="imageCount">
            <option :value="1">1 image</option>
            <option :value="2">2 images</option>
            <option :value="4">4 images</option>
          </select>
        </div>
      </div>

      <!-- Advanced Options Toggle -->
      <button class="advanced-toggle" @click="showAdvanced = !showAdvanced">
        {{ showAdvanced ? '▼' : '▶' }} Advanced options
      </button>

      <div v-if="showAdvanced" class="advanced-options">
        <div class="option-group full-width">
          <label>Negative prompt</label>
          <input
            type="text"
            placeholder="blurry, low quality, distorted..."
            class="text-input"
          />
        </div>
      </div>
    </div>

    <!-- Generate Button -->
    <div class="generate-section">
      <button
        class="generate-btn"
        :class="{ loading: store.isGenerating }"
        :disabled="!canGenerate"
        @click="generate"
      >
        <template v-if="store.isGenerating">
          <span class="spinner" />
          <span>Generating...</span>
        </template>
        <template v-else>
          <span>✨</span>
          <span>Generate</span>
        </template>
      </button>
      <div class="cost-estimate">
        Est. cost: ${{ costEstimate.toFixed(2) }}
        ({{ imageCount }} × ${{ (costEstimate / imageCount).toFixed(2) }})
      </div>
    </div>

    <!-- Error Display -->
    <div v-if="store.error" class="error-banner">
      <span>⚠️ {{ store.error }}</span>
      <button @click="store.clearError">×</button>
    </div>

    <!-- Gallery -->
    <div class="gallery-section">
      <AiImageGallery
        :images="store.filteredImages"
        :selected-id="store.selectedId"
        :is-loading="store.isLoadingAssets"
        @select="handleImageSelect"
        @attach="handleAttach"
        @download="store.downloadImage"
        @delete="store.deleteImage"
        @rate="store.rateImage"
      />
    </div>

    <!-- Session Stats -->
    <div class="session-stats">
      <div class="stat">
        <span class="stat-value">{{ store.sessionCount }}</span>
        <span class="stat-label">images</span>
      </div>
      <div class="stat">
        <span class="stat-value">${{ store.sessionCost.toFixed(2) }}</span>
        <span class="stat-label">spent</span>
      </div>
      <div class="stat" v-if="store.providerStats['guitar_lora']">
        <span class="stat-value">
          {{ Math.round((store.providerStats['guitar_lora']?.count ?? 0) / Math.max(store.sessionCount, 1) * 100) }}%
        </span>
        <span class="stat-label">LoRA</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.ai-image-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-panel, #16213e);
  color: var(--text, #e0e0e0);
  overflow: hidden;
}

/* Header */
.panel-header {
  padding: 16px 20px;
  border-bottom: 1px solid var(--border, #2a3f5f);
  display: flex;
  align-items: center;
  gap: 10px;
}

.panel-header h2 {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
  flex: 1;
}

.panel-header .icon {
  font-size: 20px;
}

.beta-badge {
  background: var(--accent, #4fc3f7);
  color: #000;
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  color: var(--text-dim, #8892a0);
  font-size: 20px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: var(--text);
}

/* Prompt Section */
.prompt-section {
  padding: 16px;
  border-bottom: 1px solid var(--border);
}

.section-label {
  display: block;
  font-size: 12px;
  color: var(--text-dim);
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.prompt-textarea {
  width: 100%;
  background: var(--bg-input, #0f1629);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 12px;
  color: var(--text);
  font-size: 14px;
  font-family: inherit;
  resize: none;
}

.prompt-textarea:focus {
  outline: none;
  border-color: var(--accent);
}

.prompt-textarea::placeholder {
  color: var(--text-dim);
}

/* Quick Tags */
.quick-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 10px;
}

.quick-tag {
  background: var(--bg-input);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 4px 10px;
  font-size: 11px;
  color: var(--text-dim);
  cursor: pointer;
  transition: all 0.15s;
}

.quick-tag:hover {
  border-color: var(--accent);
  color: var(--accent);
}

.quick-tag.body { border-left: 2px solid #4fc3f7; }
.quick-tag.finish { border-left: 2px solid #81c784; }
.quick-tag.hardware { border-left: 2px solid #ffb74d; }
.quick-tag.wood { border-left: 2px solid #a1887f; }

/* Prompt Preview */
.prompt-preview {
  margin-top: 12px;
  background: var(--bg-input);
  border-radius: 6px;
  padding: 10px;
}

.preview-label {
  display: flex;
  justify-content: space-between;
  font-size: 10px;
  color: var(--text-dim);
  text-transform: uppercase;
  margin-bottom: 6px;
}

.confidence {
  color: var(--accent);
}

.preview-text {
  font-size: 11px;
  line-height: 1.5;
  color: var(--text-dim);
}

/* Options */
.options-section {
  padding: 16px;
  border-bottom: 1px solid var(--border);
}

.options-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.option-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.option-group.full-width {
  grid-column: span 2;
}

.option-group label {
  font-size: 11px;
  color: var(--text-dim);
  text-transform: uppercase;
}

.option-group select,
.option-group .text-input {
  background: var(--bg-input);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 8px 10px;
  color: var(--text);
  font-size: 13px;
}

.option-group select:focus,
.option-group .text-input:focus {
  outline: none;
  border-color: var(--accent);
}

.advanced-toggle {
  background: none;
  border: none;
  color: var(--text-dim);
  font-size: 12px;
  cursor: pointer;
  padding: 8px 0;
  text-align: left;
  width: 100%;
}

.advanced-toggle:hover {
  color: var(--text);
}

.advanced-options {
  margin-top: 12px;
}

/* Generate Button */
.generate-section {
  padding: 16px;
  border-bottom: 1px solid var(--border);
}

.generate-btn {
  width: 100%;
  background: linear-gradient(135deg, var(--accent), #29b6f6);
  border: none;
  border-radius: 8px;
  padding: 14px;
  color: #000;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.2s;
}

.generate-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(79, 195, 247, 0.3);
}

.generate-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.generate-btn.loading {
  background: var(--bg-input);
  color: var(--text);
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid transparent;
  border-top-color: currentColor;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.cost-estimate {
  text-align: center;
  font-size: 11px;
  color: var(--text-dim);
  margin-top: 8px;
}

/* Error Banner */
.error-banner {
  background: rgba(244, 67, 54, 0.1);
  border: 1px solid #f44336;
  border-radius: 6px;
  padding: 10px 16px;
  margin: 0 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
  color: #f44336;
}

.error-banner button {
  background: none;
  border: none;
  color: #f44336;
  cursor: pointer;
  font-size: 16px;
}

/* Gallery Section */
.gallery-section {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

/* Session Stats */
.session-stats {
  padding: 12px 16px;
  border-top: 1px solid var(--border);
  display: flex;
  justify-content: space-around;
  background: var(--bg-input);
}

.stat {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 16px;
  font-weight: 600;
  color: var(--accent);
}

.stat-label {
  font-size: 10px;
  color: var(--text-dim);
  text-transform: uppercase;
}
</style>
