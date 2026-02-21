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
import {
  ImageProvider,
  ImageQuality,
  PhotoStyle,
} from './types';
import type { QuickTag } from './types';
import styles from './AiImagePanel.module.css';

function getCategoryClass(category: string) {
  switch (category) {
    case 'body': return styles.quickTagBody;
    case 'finish': return styles.quickTagFinish;
    case 'hardware': return styles.quickTagHardware;
    case 'wood': return styles.quickTagWood;
    default: return styles.quickTag;
  }
}

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
const selectedStyle = ref<PhotoStyle>(PhotoStyle.PRODUCT);
const selectedProvider = ref<ImageProvider>(ImageProvider.AUTO);
const selectedQuality = ref<ImageQuality>(ImageQuality.STANDARD);
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
  <div :class="styles.aiImagePanel">
    <!-- Header -->
    <div :class="styles.panelHeader">
      <span :class="styles.icon">Guitar</span>
      <h2>AI Image Generator</h2>
      <span :class="styles.betaBadge">BETA</span>
      <button
        :class="styles.closeBtn"
        title="Close"
        @click="emit('close')"
      >
        x
      </button>
    </div>

    <!-- Prompt Section -->
    <div :class="styles.promptSection">
      <label :class="styles.sectionLabel">Describe your guitar</label>
      <textarea
        v-model="prompt"
        :class="styles.promptTextarea"
        placeholder="emerald green les paul with gold hardware, flame maple top..."
        rows="3"
      />

      <!-- Quick Tags -->
      <div :class="styles.quickTags">
        <button
          v-for="tag in quickTags"
          :key="tag.value"
          :class="getCategoryClass(tag.category)"
          @click="addTag(tag)"
        >
          {{ tag.label }}
        </button>
      </div>

      <!-- Prompt Preview -->
      <div
        v-if="promptPreview"
        :class="styles.promptPreview"
      >
        <div :class="styles.previewLabel">
          <span>Engineered prompt</span>
          <span :class="styles.confidence">{{ Math.round(previewConfidence * 100) }}% confidence</span>
        </div>
        <div :class="styles.previewText">
          {{ promptPreview }}
        </div>
      </div>
    </div>

    <!-- Options Section -->
    <div :class="styles.optionsSection">
      <div :class="styles.optionsGrid">
        <div :class="styles.optionGroup">
          <label>Style</label>
          <select v-model="selectedStyle">
            <option value="product">
              Product Shot
            </option>
            <option value="dramatic">
              Dramatic
            </option>
            <option value="studio">
              Studio
            </option>
            <option value="lifestyle">
              Lifestyle
            </option>
            <option value="vintage">
              Vintage
            </option>
            <option value="cinematic">
              Cinematic
            </option>
          </select>
        </div>

        <div :class="styles.optionGroup">
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

        <div :class="styles.optionGroup">
          <label>Quality</label>
          <select v-model="selectedQuality">
            <option value="draft">
              Draft
            </option>
            <option value="standard">
              Standard
            </option>
            <option value="hd">
              HD (+$)
            </option>
          </select>
        </div>

        <div :class="styles.optionGroup">
          <label>Count</label>
          <select v-model="imageCount">
            <option :value="1">
              1 image
            </option>
            <option :value="2">
              2 images
            </option>
            <option :value="4">
              4 images
            </option>
          </select>
        </div>
      </div>

      <!-- Advanced Options Toggle -->
      <button
        :class="styles.advancedToggle"
        @click="showAdvanced = !showAdvanced"
      >
        {{ showAdvanced ? 'v' : '>' }} Advanced options
      </button>

      <div
        v-if="showAdvanced"
        :class="styles.advancedOptions"
      >
        <div :class="styles.optionGroupFullWidth">
          <label>Negative prompt</label>
          <input
            type="text"
            placeholder="blurry, low quality, distorted..."
            :class="styles.textInput"
          >
        </div>
      </div>
    </div>

    <!-- Generate Button -->
    <div :class="styles.generateSection">
      <button
        :class="store.isGenerating ? styles.generateBtnLoading : styles.generateBtn"
        :disabled="!canGenerate"
        @click="generate"
      >
        <template v-if="store.isGenerating">
          <span :class="styles.spinner" />
          <span>Generating...</span>
        </template>
        <template v-else>
          <span>*</span>
          <span>Generate</span>
        </template>
      </button>
      <div :class="styles.costEstimate">
        Est. cost: ${{ costEstimate.toFixed(2) }}
        ({{ imageCount }} x ${{ (costEstimate / imageCount).toFixed(2) }})
      </div>
    </div>

    <!-- Error Display -->
    <div
      v-if="store.error"
      :class="styles.errorBanner"
    >
      <span>Warning: {{ store.error }}</span>
      <button @click="store.clearError">
        x
      </button>
    </div>

    <!-- Gallery -->
    <div :class="styles.gallerySection">
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
    <div :class="styles.sessionStats">
      <div :class="styles.stat">
        <span :class="styles.statValue">{{ store.sessionCount }}</span>
        <span :class="styles.statLabel">images</span>
      </div>
      <div :class="styles.stat">
        <span :class="styles.statValue">${{ store.sessionCost.toFixed(2) }}</span>
        <span :class="styles.statLabel">spent</span>
      </div>
      <div
        v-if="store.providerStats['guitar_lora']"
        :class="styles.stat"
      >
        <span :class="styles.statValue">
          {{ Math.round((store.providerStats['guitar_lora']?.count ?? 0) / Math.max(store.sessionCount, 1) * 100) }}%
        </span>
        <span :class="styles.statLabel">LoRA</span>
      </div>
    </div>
  </div>
</template>
