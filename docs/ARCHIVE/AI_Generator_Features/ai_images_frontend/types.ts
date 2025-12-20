/**
 * AI Images Feature — Type Definitions
 * 
 * Types for the user-side AI image generation layer.
 * These images are PROJECT ASSETS, not run artifacts.
 * 
 * @package features/ai_images
 */

// =============================================================================
// ENUMS
// =============================================================================

export enum ImageProvider {
  AUTO = 'auto',
  DALLE3 = 'dalle3',
  SDXL = 'sdxl',
  GUITAR_LORA = 'guitar_lora',
  STUB = 'stub',
}

export enum ImageQuality {
  DRAFT = 'draft',
  STANDARD = 'standard',
  HD = 'hd',
}

export enum ImageSize {
  SQUARE_SM = '512x512',
  SQUARE_MD = '768x768',
  SQUARE_LG = '1024x1024',
  LANDSCAPE = '1792x1024',
  PORTRAIT = '1024x1792',
}

export enum PhotoStyle {
  PRODUCT = 'product',
  DRAMATIC = 'dramatic',
  STUDIO = 'studio',
  LIFESTYLE = 'lifestyle',
  VINTAGE = 'vintage',
  CINEMATIC = 'cinematic',
  WORKSHOP = 'workshop',
}

export enum GuitarCategory {
  ELECTRIC = 'electric',
  ACOUSTIC = 'acoustic',
  CLASSICAL = 'classical',
  BASS = 'bass',
  ARCHTOP = 'archtop',
  UNKNOWN = 'unknown',
}

export enum AssetStatus {
  GENERATING = 'generating',
  READY = 'ready',
  FAILED = 'failed',
  ATTACHED = 'attached',
}

export enum FinishType {
  SOLID = 'solid',
  BURST = 'burst',
  NATURAL = 'natural',
  METALLIC = 'metallic',
  SPARKLE = 'sparkle',
  RELIC = 'relic',
}

// =============================================================================
// REQUEST TYPES
// =============================================================================

/**
 * Request to generate guitar images.
 * Sent to POST /api/vision/generate
 */
export interface GenerationRequest {
  /** Natural language description */
  prompt: string;
  
  /** Number of images to generate (1-4) */
  numImages?: number;
  
  /** Image dimensions */
  size?: ImageSize;
  
  /** Quality level */
  quality?: ImageQuality;
  
  /** Photography style */
  style?: PhotoStyle;
  
  /** Force specific provider (default: auto) */
  provider?: ImageProvider;
  
  /** Project ID for asset storage */
  projectId?: string;
}

/**
 * Request to preview prompt engineering.
 * Sent to POST /api/vision/prompt
 */
export interface PromptPreviewRequest {
  prompt: string;
  style?: PhotoStyle;
  includeVariations?: boolean;
}

// =============================================================================
// RESPONSE TYPES
// =============================================================================

/**
 * A single generated image from the API.
 */
export interface GeneratedImage {
  /** Unique image ID */
  imageId: string;
  
  /** URL to access the image */
  url: string;
  
  /** Base64 data (if embedded) */
  base64Data?: string;
  
  /** Provider that generated this image */
  provider: ImageProvider;
  
  /** Revised prompt (from DALL-E) */
  revisedPrompt?: string;
}

/**
 * Response from POST /api/vision/generate
 */
export interface GenerationResponse {
  success: boolean;
  requestId: string;
  images: GeneratedImage[];
  
  /** The engineered prompt that was sent to the provider */
  engineeredPrompt: string;
  
  /** Detected guitar attributes */
  detectedCategory: GuitarCategory;
  detectedBodyShape?: string;
  detectedFinish?: string;
  parseConfidence: number;
  
  /** Provider used */
  providerUsed: ImageProvider;
  
  /** Cost tracking */
  estimatedCost: number;
  actualCost: number;
  
  /** Timing */
  totalTimeMs: number;
  
  /** Error if failed */
  error?: string;
}

/**
 * Response from POST /api/vision/prompt
 */
export interface PromptPreviewResponse {
  positivePrompt: string;
  negativePrompt: string;
  
  category: GuitarCategory;
  bodyShape?: string;
  finish?: string;
  confidence: number;
  
  variations?: PromptVariation[];
}

export interface PromptVariation {
  style: PhotoStyle;
  positivePrompt: string;
}

/**
 * Response from GET /api/vision/vocabulary
 */
export interface VocabularyResponse {
  bodyShapes: VocabularyCategory;
  finishes: VocabularyCategory;
  photoStyles: string[];
}

export interface VocabularyCategory {
  [category: string]: string[];
}

/**
 * Response from GET /api/vision/providers
 */
export interface ProvidersResponse {
  providers: ProviderInfo[];
}

export interface ProviderInfo {
  id: ImageProvider;
  name: string;
  available: boolean;
  reason?: string;
  costs: {
    [quality: string]: number;
  };
}

// =============================================================================
// ASSET TYPES (Stored in project)
// =============================================================================

/**
 * An AI-generated image stored as a project asset.
 * Lives in: data/projects/{projectId}/assets/ai_images/
 */
export interface ImageAsset {
  /** Unique asset ID */
  id: string;
  
  /** Original filename */
  filename: string;
  
  /** Relative path within project assets */
  path: string;
  
  /** Full URL for display */
  url: string;
  
  /** Current status */
  status: AssetStatus;
  
  /** Original user prompt */
  userPrompt: string;
  
  /** Engineered prompt sent to provider */
  engineeredPrompt: string;
  
  /** Provider that generated this */
  provider: ImageProvider;
  
  /** Detected attributes */
  category: GuitarCategory;
  bodyShape?: string;
  finish?: string;
  
  /** Generation settings */
  size: ImageSize;
  quality: ImageQuality;
  style: PhotoStyle;
  
  /** Cost */
  cost: number;
  
  /** Timestamps */
  createdAt: string;
  updatedAt: string;
  
  /** Optional: attached to design element ID */
  attachedTo?: string;
  
  /** User rating (1-5) for learning */
  rating?: number;
  
  /** User notes */
  notes?: string;
}

/**
 * Manifest file for AI images in a project.
 * Stored at: data/projects/{projectId}/assets/ai_images/manifest.json
 */
export interface ImageAssetManifest {
  version: string;
  projectId: string;
  images: ImageAsset[];
  
  /** Session stats */
  stats: {
    totalGenerated: number;
    totalCost: number;
    providerBreakdown: {
      [provider: string]: {
        count: number;
        cost: number;
        avgRating?: number;
      };
    };
  };
  
  updatedAt: string;
}

// =============================================================================
// STORE STATE
// =============================================================================

/**
 * Pinia store state for AI Images feature.
 */
export interface AiImageState {
  /** All image assets in current project */
  images: ImageAsset[];
  
  /** Currently selected image ID */
  selectedId: string | null;
  
  /** Current project ID */
  projectId: string | null;
  
  /** Loading states */
  isGenerating: boolean;
  isLoadingVocabulary: boolean;
  isLoadingProviders: boolean;
  isLoadingAssets: boolean;
  
  /** Cached vocabulary */
  vocabulary: VocabularyResponse | null;
  
  /** Available providers */
  providers: ProviderInfo[];
  
  /** Session cost tracking */
  sessionCost: number;
  sessionCount: number;
  
  /** Error state */
  error: string | null;
  
  /** Gallery filters */
  filters: GalleryFilters;
  
  /** Sort settings */
  sortBy: GallerySortBy;
  sortDirection: SortDirection;
  
  /** Last generation response (for feedback) */
  lastGenerationResponse: GenerationResponse | null;
}

// =============================================================================
// UI TYPES
// =============================================================================

/**
 * Quick tag for prompt building.
 */
export interface QuickTag {
  label: string;
  value: string;
  category: 'body' | 'finish' | 'hardware' | 'wood' | 'style';
}

/**
 * Gallery filter options.
 */
export interface GalleryFilters {
  category?: GuitarCategory;
  provider?: ImageProvider;
  status?: AssetStatus;
  minRating?: number;
  search?: string;
}

/**
 * Sort options for gallery.
 */
export type GallerySortBy = 'createdAt' | 'rating' | 'cost' | 'provider';
export type SortDirection = 'asc' | 'desc';

// =============================================================================
// EVENT TYPES
// =============================================================================

/**
 * Events emitted by AI Image components.
 */
export interface AiImageEvents {
  /** Image generation completed */
  'generation:complete': GenerationResponse;
  
  /** Image selected in gallery */
  'image:select': ImageAsset;
  
  /** Image attached to design */
  'image:attach': { imageId: string; targetId: string };
  
  /** Image downloaded */
  'image:download': ImageAsset;
  
  /** Image deleted */
  'image:delete': string;
  
  /** Rating changed */
  'image:rate': { imageId: string; rating: number };
}
