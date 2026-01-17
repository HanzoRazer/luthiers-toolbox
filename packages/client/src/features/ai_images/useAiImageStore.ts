/**
 * AI Images Feature — Pinia Store
 * 
 * Manages state for AI image generation and assets.
 * Images are stored as project assets, NOT run artifacts.
 * 
 * @package features/ai_images
 */

import { defineStore } from 'pinia';
import { ref, computed, watch } from 'vue';
import { nanoid } from 'nanoid';

import type {
  ImageAsset,
  GenerationRequest,
  GenerationResponse,
  VocabularyResponse,
  ProviderInfo,
  GalleryFilters,
  GallerySortBy,
  SortDirection,
  ImageProvider,
  ImageQuality,
  ImageSize,
  PhotoStyle,
  AssetStatus,
  GuitarCategory,
} from './types';

import {
  generateImages as apiGenerateImages,
  previewPrompt as apiPreviewPrompt,
  getVocabulary as apiGetVocabulary,
  getProviders as apiGetProviders,
  getProjectAssets,
  uploadAsset,
  deleteAsset as apiDeleteAsset,
  updateAsset as apiUpdateAsset,
  submitFeedback,
  estimateCost,
  downloadImageFromUrl,
  downloadBase64Image,
} from './api';

// =============================================================================
// STORE DEFINITION
// =============================================================================

export const useAiImageStore = defineStore('aiImages', () => {
  // ===========================================================================
  // STATE
  // ===========================================================================
  
  /** All image assets in current project */
  const images = ref<ImageAsset[]>([]);
  
  /** Currently selected image ID */
  const selectedId = ref<string | null>(null);
  
  /** Current project ID */
  const projectId = ref<string | null>(null);
  
  /** Loading states */
  const isGenerating = ref(false);
  const isLoadingVocabulary = ref(false);
  const isLoadingProviders = ref(false);
  const isLoadingAssets = ref(false);
  
  /** Cached vocabulary */
  const vocabulary = ref<VocabularyResponse | null>(null);
  
  /** Available providers */
  const providers = ref<ProviderInfo[]>([]);
  
  /** Session tracking */
  const sessionCost = ref(0);
  const sessionCount = ref(0);
  
  /** Error state */
  const error = ref<string | null>(null);
  
  /** Gallery filters */
  const filters = ref<GalleryFilters>({});
  
  /** Sort settings */
  const sortBy = ref<GallerySortBy>('createdAt');
  const sortDirection = ref<SortDirection>('desc');
  
  /** Last generation response (for feedback) */
  const lastGenerationResponse = ref<GenerationResponse | null>(null);
  
  // ===========================================================================
  // GETTERS
  // ===========================================================================
  
  /** Currently selected image */
  const selectedImage = computed<ImageAsset | null>(() => {
    if (!selectedId.value) return null;
    return images.value.find(img => img.id === selectedId.value) ?? null;
  });
  
  /** Filtered and sorted images */
  const filteredImages = computed<ImageAsset[]>(() => {
    let result = [...images.value];
    
    // Apply filters
    if (filters.value.category) {
      result = result.filter(img => img.category === filters.value.category);
    }
    if (filters.value.provider) {
      result = result.filter(img => img.provider === filters.value.provider);
    }
    if (filters.value.status) {
      result = result.filter(img => img.status === filters.value.status);
    }
    if (filters.value.minRating) {
      result = result.filter(
        img => (img.rating ?? 0) >= filters.value.minRating!
      );
    }
    if (filters.value.search) {
      const search = filters.value.search.toLowerCase();
      result = result.filter(
        img =>
          img.userPrompt.toLowerCase().includes(search) ||
          img.bodyShape?.toLowerCase().includes(search) ||
          img.finish?.toLowerCase().includes(search)
      );
    }
    
    // Sort
    result.sort((a, b) => {
      let comparison = 0;
      
      switch (sortBy.value) {
        case 'createdAt':
          comparison = new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime();
          break;
        case 'rating':
          comparison = (a.rating ?? 0) - (b.rating ?? 0);
          break;
        case 'cost':
          comparison = a.cost - b.cost;
          break;
        case 'provider':
          comparison = a.provider.localeCompare(b.provider);
          break;
      }
      
      return sortDirection.value === 'desc' ? -comparison : comparison;
    });
    
    return result;
  });
  
  /** Images currently generating */
  const generatingImages = computed<ImageAsset[]>(() =>
    images.value.filter(img => img.status === 'generating')
  );
  
  /** Total cost of all images */
  const totalCost = computed<number>(() =>
    images.value.reduce((sum, img) => sum + img.cost, 0)
  );
  
  /** Provider stats */
  const providerStats = computed(() => {
    const stats: Record<string, { count: number; cost: number; avgRating: number }> = {};
    
    for (const img of images.value) {
      if (!stats[img.provider]) {
        stats[img.provider] = { count: 0, cost: 0, avgRating: 0 };
      }
      stats[img.provider].count++;
      stats[img.provider].cost += img.cost;
    }
    
    // Calculate average ratings
    for (const provider of Object.keys(stats)) {
      const rated = images.value.filter(
        img => img.provider === provider && img.rating
      );
      if (rated.length > 0) {
        stats[provider].avgRating =
          rated.reduce((sum, img) => sum + (img.rating ?? 0), 0) / rated.length;
      }
    }
    
    return stats;
  });
  
  /** Available providers (ready to use) */
  const availableProviders = computed(() =>
    providers.value.filter(p => p.available)
  );
  
  /** Body shapes for dropdowns */
  const bodyShapeOptions = computed(() => {
    if (!vocabulary.value) return [];
    const shapes: string[] = [];
    for (const category of Object.values(vocabulary.value.bodyShapes)) {
      shapes.push(...category);
    }
    return [...new Set(shapes)].sort();
  });
  
  /** Finishes for dropdowns */
  const finishOptions = computed(() => {
    if (!vocabulary.value) return [];
    const finishes: string[] = [];
    for (const category of Object.values(vocabulary.value.finishes)) {
      finishes.push(...category);
    }
    return [...new Set(finishes)].sort();
  });
  
  // ===========================================================================
  // ACTIONS
  // ===========================================================================
  
  /**
   * Initialize store for a project.
   */
  async function initialize(newProjectId: string): Promise<void> {
    projectId.value = newProjectId;
    error.value = null;
    
    // Load in parallel
    await Promise.all([
      loadAssets(),
      loadVocabulary(),
      loadProviders(),
    ]);
  }
  
  /**
   * Load assets from project.
   */
  async function loadAssets(): Promise<void> {
    if (!projectId.value) return;
    
    isLoadingAssets.value = true;
    error.value = null;
    
    try {
      images.value = await getProjectAssets(projectId.value);
    } catch (err) {
      error.value = `Failed to load assets: ${err}`;
      console.error('Failed to load AI image assets:', err);
    } finally {
      isLoadingAssets.value = false;
    }
  }
  
  /**
   * Load vocabulary for dropdowns.
   */
  async function loadVocabulary(): Promise<void> {
    if (vocabulary.value) return; // Already loaded
    
    isLoadingVocabulary.value = true;
    
    try {
      vocabulary.value = await apiGetVocabulary();
    } catch (err) {
      console.error('Failed to load vocabulary:', err);
    } finally {
      isLoadingVocabulary.value = false;
    }
  }
  
  /**
   * Load available providers.
   */
  async function loadProviders(): Promise<void> {
    isLoadingProviders.value = true;
    
    try {
      const response = await apiGetProviders();
      providers.value = response.providers;
    } catch (err) {
      console.error('Failed to load providers:', err);
    } finally {
      isLoadingProviders.value = false;
    }
  }
  
  /**
   * Generate new images.
   */
  async function generate(request: GenerationRequest): Promise<ImageAsset[]> {
    isGenerating.value = true;
    error.value = null;
    
    // Create placeholder assets for UI feedback
    const numImages = request.numImages ?? 2;
    const placeholders: ImageAsset[] = [];
    
    for (let i = 0; i < numImages; i++) {
      const placeholder: ImageAsset = {
        id: nanoid(),
        filename: '',
        path: '',
        url: '',
        status: 'generating' as AssetStatus,
        userPrompt: request.prompt,
        engineeredPrompt: '',
        provider: request.provider ?? ('auto' as ImageProvider),
        category: 'unknown' as GuitarCategory,
        size: request.size ?? ('1024x1024' as ImageSize),
        quality: request.quality ?? ('standard' as ImageQuality),
        style: request.style ?? ('product' as PhotoStyle),
        cost: 0,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };
      placeholders.push(placeholder);
      images.value.unshift(placeholder);
    }
    
    try {
      const response = await apiGenerateImages(request);
      lastGenerationResponse.value = response;
      
      if (!response.success) {
        throw new Error(response.error ?? 'Generation failed');
      }
      
      // Update placeholders with real data
      const newAssets: ImageAsset[] = [];
      
      for (let i = 0; i < response.images.length; i++) {
        const img = response.images[i];
        const placeholder = placeholders[i];
        
        if (placeholder) {
          // Update placeholder in place
          const idx = images.value.findIndex(a => a.id === placeholder.id);
          if (idx !== -1) {
            const asset: ImageAsset = {
              ...placeholder,
              filename: `${img.imageId}.png`,
              url: img.url,
              status: 'ready' as AssetStatus,
              engineeredPrompt: response.engineeredPrompt,
              provider: response.providerUsed,
              category: response.detectedCategory,
              bodyShape: response.detectedBodyShape,
              finish: response.detectedFinish,
              cost: response.actualCost / response.images.length,
              updatedAt: new Date().toISOString(),
            };
            
            images.value[idx] = asset;
            newAssets.push(asset);
          }
        }
      }
      
      // Remove extra placeholders if fewer images returned
      for (let i = response.images.length; i < placeholders.length; i++) {
        const idx = images.value.findIndex(a => a.id === placeholders[i].id);
        if (idx !== -1) {
          images.value.splice(idx, 1);
        }
      }
      
      // Update session stats
      sessionCost.value += response.actualCost;
      sessionCount.value += response.images.length;
      
      // Select first new image
      if (newAssets.length > 0) {
        selectedId.value = newAssets[0].id;
      }
      
      // Persist to project (background)
      if (projectId.value) {
        for (const asset of newAssets) {
          uploadAsset(projectId.value, { url: asset.url }, asset).catch(err => {
            console.error('Failed to persist asset:', err);
          });
        }
      }
      
      return newAssets;
      
    } catch (err) {
      // Mark placeholders as failed
      for (const placeholder of placeholders) {
        const idx = images.value.findIndex(a => a.id === placeholder.id);
        if (idx !== -1) {
          images.value[idx] = {
            ...images.value[idx],
            status: 'failed' as AssetStatus,
          };
        }
      }
      
      error.value = `Generation failed: ${err}`;
      throw err;
      
    } finally {
      isGenerating.value = false;
    }
  }
  
  /**
   * Preview prompt without generating.
   */
  async function previewPrompt(prompt: string, style?: PhotoStyle) {
    return apiPreviewPrompt({ prompt, style, includeVariations: true });
  }
  
  /**
   * Select an image.
   */
  function selectImage(id: string | null): void {
    selectedId.value = id;
  }
  
  /**
   * Rate an image (for learning).
   */
  async function rateImage(id: string, rating: number): Promise<void> {
    const image = images.value.find(img => img.id === id);
    if (!image) return;
    
    image.rating = rating;
    image.updatedAt = new Date().toISOString();
    
    // Submit feedback to backend
    if (lastGenerationResponse.value) {
      try {
        await submitFeedback(
          lastGenerationResponse.value.requestId,
          id,
          rating
        );
      } catch (err) {
        console.error('Failed to submit feedback:', err);
      }
    }
    
    // Persist
    if (projectId.value) {
      try {
        await apiUpdateAsset(projectId.value, id, { rating });
      } catch (err) {
        console.error('Failed to update asset:', err);
      }
    }
  }
  
  /**
   * Delete an image.
   */
  async function deleteImage(id: string): Promise<void> {
    const idx = images.value.findIndex(img => img.id === id);
    if (idx === -1) return;
    
    images.value.splice(idx, 1);
    
    if (selectedId.value === id) {
      selectedId.value = images.value[0]?.id ?? null;
    }
    
    // Delete from backend
    if (projectId.value) {
      try {
        await apiDeleteAsset(projectId.value, id);
      } catch (err) {
        console.error('Failed to delete asset:', err);
      }
    }
  }
  
  /**
   * Download an image.
   */
  async function downloadImage(id: string): Promise<void> {
    const image = images.value.find(img => img.id === id);
    if (!image) return;
    
    const filename = `guitar_${image.bodyShape ?? 'image'}_${image.id}.png`
      .toLowerCase()
      .replace(/\s+/g, '_');
    
    await downloadImageFromUrl(image.url, filename);
  }
  
  /**
   * Attach image to a design element.
   */
  function attachToDesign(imageId: string, targetId: string): void {
    const image = images.value.find(img => img.id === imageId);
    if (!image) return;
    
    image.attachedTo = targetId;
    image.status = 'attached' as AssetStatus;
    image.updatedAt = new Date().toISOString();
    
    // Persist
    if (projectId.value) {
      apiUpdateAsset(projectId.value, imageId, {
        attachedTo: targetId,
        status: 'attached' as AssetStatus,
      }).catch(err => {
        console.error('Failed to update asset:', err);
      });
    }
  }
  
  /**
   * Set gallery filters.
   */
  function setFilters(newFilters: GalleryFilters): void {
    filters.value = newFilters;
  }

  /**
   * Set a single filter key.
   */
  function setFilter<K extends keyof GalleryFilters>(key: K, value: GalleryFilters[K]): void {
    filters.value = { ...filters.value, [key]: value };
  }

  /**
   * Clear all filters.
   */
  function clearFilters(): void {
    filters.value = {};
  }
  
  /**
   * Set sort options.
   */
  function setSort(by: GallerySortBy, direction: SortDirection): void {
    sortBy.value = by;
    sortDirection.value = direction;
  }
  
  /**
   * Clear error state.
   */
  function clearError(): void {
    error.value = null;
  }
  
  /**
   * Get cost estimate for current settings.
   */
  function getEstimate(
    numImages: number,
    quality: ImageQuality,
    provider: ImageProvider
  ): number {
    return estimateCost(numImages, quality, provider);
  }
  
  /**
   * Reset store state.
   */
  function reset(): void {
    images.value = [];
    selectedId.value = null;
    projectId.value = null;
    isGenerating.value = false;
    error.value = null;
    filters.value = {};
    sessionCost.value = 0;
    sessionCount.value = 0;
    lastGenerationResponse.value = null;
  }
  
  // ===========================================================================
  // RETURN
  // ===========================================================================
  
  return {
    // State
    images,
    selectedId,
    projectId,
    isGenerating,
    isLoadingVocabulary,
    isLoadingProviders,
    isLoadingAssets,
    vocabulary,
    providers,
    sessionCost,
    sessionCount,
    error,
    filters,
    sortBy,
    sortDirection,
    
    // Getters
    selectedImage,
    filteredImages,
    generatingImages,
    totalCost,
    providerStats,
    availableProviders,
    bodyShapeOptions,
    finishOptions,
    
    // Actions
    initialize,
    loadAssets,
    loadVocabulary,
    loadProviders,
    generate,
    previewPrompt,
    selectImage,
    rateImage,
    deleteImage,
    downloadImage,
    attachToDesign,
    setFilters,
    setFilter,
    clearFilters,
    setSort,
    clearError,
    getEstimate,
    reset,
  };
});

// =============================================================================
// TYPE EXPORT FOR CONSUMERS
// =============================================================================

export type AiImageStore = ReturnType<typeof useAiImageStore>;
