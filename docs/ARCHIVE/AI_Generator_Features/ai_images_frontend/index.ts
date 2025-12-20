/**
 * AI Images Feature — Public API
 * 
 * Clean exports for the AI image generation feature.
 * Import from this file, not individual modules.
 * 
 * @package features/ai_images
 * 
 * @example
 * ```ts
 * import {
 *   AiImagePanel,
 *   AiImageGallery,
 *   useAiImageStore,
 *   type ImageAsset,
 * } from '@/features/ai_images';
 * ```
 */

// =============================================================================
// COMPONENTS
// =============================================================================

export { default as AiImagePanel } from './AiImagePanel.vue';
export { default as AiImageGallery } from './AiImageGallery.vue';
export { default as AiImageProperties } from './AiImageProperties.vue';
export { default as AiImageFilterToolbar } from './AiImageFilterToolbar.vue';

// =============================================================================
// STORE
// =============================================================================

export { useAiImageStore } from './useAiImageStore';
export type { AiImageStore } from './useAiImageStore';

// =============================================================================
// API (Legacy - Vision endpoints)
// =============================================================================

export {
  generateImages,
  previewPrompt,
  getVocabulary,
  getProviders,
  submitFeedback,
  uploadAsset,
  getProjectAssets,
  deleteAsset,
  updateAsset,
  downloadImageFromUrl,
  estimateCost,
  ApiError,
} from './api';

// =============================================================================
// API (New - All endpoints)
// =============================================================================

export * from './api/index';

// =============================================================================
// TYPES
// =============================================================================

export type {
  // Enums
  ImageProvider,
  ImageQuality,
  ImageSize,
  PhotoStyle,
  GuitarCategory,
  AssetStatus,
  FinishType,
  
  // Request/Response
  GenerationRequest,
  GenerationResponse,
  PromptPreviewRequest,
  PromptPreviewResponse,
  VocabularyResponse,
  ProvidersResponse,
  GeneratedImage,
  ProviderInfo,
  PromptVariation,
  VocabularyCategory,
  
  // Assets
  ImageAsset,
  ImageAssetManifest,
  
  // Store
  AiImageState,
  
  // UI
  QuickTag,
  GalleryFilters,
  GallerySortBy,
  SortDirection,
  
  // Events
  AiImageEvents,
} from './types';

// Re-export enums as values (not just types)
export {
  ImageProvider,
  ImageQuality,
  ImageSize,
  PhotoStyle,
  GuitarCategory,
  AssetStatus,
  FinishType,
} from './types';
