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
export { default as AdvisoryReviewPanel } from './AdvisoryReviewPanel.vue';
export { default as AiImageFilterToolbar } from './AiImageFilterToolbar.vue';
export { default as TeachingLoopPanel } from './TeachingLoopPanel.vue';

// =============================================================================
// STORE
// =============================================================================

export { useAiImageStore } from './useAiImageStore';
export type { AiImageStore } from './useAiImageStore';

// =============================================================================
// API
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

// Re-export modular API clients for advanced usage
export * as aiApi from './api/ai';
export * as sessionApi from './api/session';
export * as teachingApi from './api/teaching';
export * as advisoryApi from './api/advisory';

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
