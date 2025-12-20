# AI Images Feature — Schema & Architecture Reference

> **Package:** `@/features/ai_images`  
> **Backend:** `services/api/app/_experimental/ai_graphics/`  
> **Last Updated:** December 19, 2025

---

## Table of Contents

1. [Overview](#overview)
2. [File Structure](#file-structure)
3. [Backend ↔ Frontend Connection Map](#backend--frontend-connection-map)
4. [Schema Reference](#schema-reference)
   - [Enums](#enums)
   - [Request Types](#request-types)
   - [Response Types](#response-types)
   - [Asset Storage Types](#asset-storage-types)
   - [UI Types](#ui-types)
5. [API Client Functions](#api-client-functions)
6. [Pinia Store API](#pinia-store-api)
7. [Component Hierarchy](#component-hierarchy)
8. [Usage Examples](#usage-examples)

---

## Overview

The AI Images feature provides guitar-specific image generation using multiple providers (DALL-E 3, SDXL, Guitar LoRA). Images are stored as **project assets** (not run artifacts) and support vocabulary-driven prompt engineering optimized for lutherie photography.

**Key Capabilities:**
- Natural language prompt → guitar-optimized engineered prompt
- Multi-provider support with cost tracking
- Project-scoped asset storage with manifest
- Rating/feedback loop for model improvement
- Vocabulary-driven dropdowns (body shapes, finishes, styles)

---

## File Structure

```
packages/client/src/features/ai_images/
├── index.ts                 # Public API — barrel exports
├── types.ts                 # TypeScript interfaces & enums (388 lines)
├── api.ts                   # HTTP client for /api/vision/* (438 lines)
├── useAiImageStore.ts       # Pinia composable store (620 lines)
├── AiImagePanel.vue         # Main generation UI (661 lines)
├── AiImageGallery.vue       # Grid display component (529 lines)
├── AiImageProperties.vue    # Detail sidebar panel (417 lines)
└── AI_IMAGES_INTEGRATION.md # Integration documentation
```

### Backend Structure

```
services/api/app/_experimental/ai_graphics/
├── __init__.py
├── api/
│   ├── __init__.py
│   ├── ai_routes.py           # General AI routes
│   ├── vision_routes.py       # Guitar Vision Engine (803 lines)
│   ├── session_routes.py      # Session management
│   ├── advisory_routes.py     # Advisory system
│   └── teaching_routes.py     # Learning/feedback routes
├── schemas/                   # Pydantic models
├── services/                  # Business logic
├── advisory_store.py
├── image_providers.py         # Provider adapters
├── image_transport.py         # Image transfer utilities
├── prompt_engine.py           # Prompt engineering
├── rosette_generator.py       # Rosette-specific generation
├── sessions.py                # Session state
└── vocabulary.py              # Guitar vocabulary definitions
```

---

## Backend ↔ Frontend Connection Map

| Backend Endpoint | Method | Frontend File | Function |
|------------------|--------|---------------|----------|
| `/api/vision/generate` | POST | `api.ts` | `generateImages()` |
| `/api/vision/prompt` | POST | `api.ts` | `previewPrompt()` |
| `/api/vision/feedback` | POST | `api.ts` | `submitFeedback()` |
| `/api/vision/vocabulary` | GET | `api.ts` | `getVocabulary()` |
| `/api/vision/providers` | GET | `api.ts` | `getProviders()` |
| `/api/vision/health` | GET | `api.ts` | (health check) |

### Component → API Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  AiImagePanel.vue                                               │
│  ├── prompt input → previewPrompt() → /api/vision/prompt        │
│  ├── generate btn → generateImages() → /api/vision/generate     │
│  └── provider select ← getProviders() ← /api/vision/providers   │
├─────────────────────────────────────────────────────────────────┤
│  AiImageGallery.vue                                             │
│  ├── grid display ← store.filteredImages                        │
│  └── rate action → submitFeedback() → /api/vision/feedback      │
├─────────────────────────────────────────────────────────────────┤
│  AiImageProperties.vue                                          │
│  ├── detail view ← store.selectedImage                          │
│  └── download/attach/delete → asset storage APIs                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Schema Reference

### Enums

```typescript
// Image provider options
enum ImageProvider {
  AUTO = 'auto',           // Server selects best provider
  DALLE3 = 'dalle3',       // OpenAI DALL-E 3
  SDXL = 'sdxl',           // Stable Diffusion XL
  GUITAR_LORA = 'guitar_lora', // Fine-tuned guitar model
  STUB = 'stub',           // Testing stub
}

// Quality levels (affects cost and resolution)
enum ImageQuality {
  DRAFT = 'draft',         // Fast, low quality
  STANDARD = 'standard',   // Balanced
  HD = 'hd',               // High definition
}

// Output dimensions
enum ImageSize {
  SQUARE_SM = '512x512',
  SQUARE_MD = '768x768',
  SQUARE_LG = '1024x1024',
  LANDSCAPE = '1792x1024',
  PORTRAIT = '1024x1792',
}

// Photography style presets
enum PhotoStyle {
  PRODUCT = 'product',     // Clean product shot
  DRAMATIC = 'dramatic',   // High contrast lighting
  STUDIO = 'studio',       // Professional studio
  LIFESTYLE = 'lifestyle', // In-use context
  VINTAGE = 'vintage',     // Aged/retro look
  CINEMATIC = 'cinematic', // Film-like quality
  WORKSHOP = 'workshop',   // Luthier workshop setting
}

// Guitar classification
enum GuitarCategory {
  ELECTRIC = 'electric',
  ACOUSTIC = 'acoustic',
  CLASSICAL = 'classical',
  BASS = 'bass',
  ARCHTOP = 'archtop',
  UNKNOWN = 'unknown',
}

// Asset lifecycle status
enum AssetStatus {
  GENERATING = 'generating', // In progress
  READY = 'ready',           // Available for use
  FAILED = 'failed',         // Generation failed
  ATTACHED = 'attached',     // Linked to design element
}
```

---

### Request Types

#### `GenerationRequest` — POST /api/vision/generate

```typescript
interface GenerationRequest {
  /** Natural language description of desired guitar image */
  prompt: string;
  
  /** Number of images to generate (1-4, default: 2) */
  numImages?: number;
  
  /** Output dimensions (default: 1024x1024) */
  size?: ImageSize;
  
  /** Quality level affecting cost (default: standard) */
  quality?: ImageQuality;
  
  /** Photography style preset (default: product) */
  style?: PhotoStyle;
  
  /** Force specific provider (default: auto) */
  provider?: ImageProvider;
  
  /** Project ID for asset storage */
  projectId?: string;
}
```

#### `PromptPreviewRequest` — POST /api/vision/prompt

```typescript
interface PromptPreviewRequest {
  /** Raw user prompt to analyze */
  prompt: string;
  
  /** Style to apply (optional) */
  style?: PhotoStyle;
  
  /** Include style variations in response */
  includeVariations?: boolean;
}
```

---

### Response Types

#### `GenerationResponse` — POST /api/vision/generate

```typescript
interface GenerationResponse {
  /** Operation success */
  success: boolean;
  
  /** Unique request ID for feedback/tracking */
  requestId: string;
  
  /** Generated images */
  images: GeneratedImage[];
  
  /** The optimized prompt sent to provider */
  engineeredPrompt: string;
  
  /** Detected guitar attributes from prompt parsing */
  detectedCategory: GuitarCategory;
  detectedBodyShape?: string;
  detectedFinish?: string;
  parseConfidence: number;  // 0.0-1.0
  
  /** Provider that fulfilled the request */
  providerUsed: ImageProvider;
  
  /** Cost tracking (USD) */
  estimatedCost: number;
  actualCost: number;
  
  /** Performance metrics */
  totalTimeMs: number;
  
  /** Error message if failed */
  error?: string;
}

interface GeneratedImage {
  imageId: string;
  url: string;
  base64Data?: string;       // Embedded data (optional)
  provider: ImageProvider;
  revisedPrompt?: string;    // DALL-E's revised prompt
}
```

#### `PromptPreviewResponse` — POST /api/vision/prompt

```typescript
interface PromptPreviewResponse {
  /** Optimized positive prompt */
  positivePrompt: string;
  
  /** Negative prompt (what to avoid) */
  negativePrompt: string;
  
  /** Detected guitar attributes */
  category: GuitarCategory;
  bodyShape?: string;
  finish?: string;
  confidence: number;
  
  /** Style variations (if requested) */
  variations?: PromptVariation[];
}

interface PromptVariation {
  style: PhotoStyle;
  positivePrompt: string;
}
```

#### `VocabularyResponse` — GET /api/vision/vocabulary

```typescript
interface VocabularyResponse {
  /** Body shapes by category */
  bodyShapes: {
    electric: string[];    // ['les paul', 'stratocaster', 'telecaster', ...]
    acoustic: string[];    // ['dreadnought', 'jumbo', 'parlor', ...]
    classical: string[];
    bass: string[];
    archtop: string[];
  };
  
  /** Finish options by category */
  finishes: {
    solid: string[];       // ['black', 'white', 'red', ...]
    burst: string[];       // ['sunburst', 'honeyburst', 'cherry burst', ...]
    natural: string[];     // ['natural', 'blonde', ...]
    metallic: string[];
  };
  
  /** Available photo styles */
  photoStyles: string[];
}
```

#### `ProvidersResponse` — GET /api/vision/providers

```typescript
interface ProvidersResponse {
  providers: ProviderInfo[];
}

interface ProviderInfo {
  id: ImageProvider;
  name: string;
  available: boolean;
  reason?: string;          // Why unavailable (e.g., "API key not configured")
  costs: {
    draft: number;
    standard: number;
    hd: number;
  };
}
```

---

### Asset Storage Types

#### `ImageAsset` — Project Asset Record

```typescript
/**
 * AI-generated image stored as a project asset.
 * Storage path: data/projects/{projectId}/assets/ai_images/
 */
interface ImageAsset {
  /** Unique asset ID */
  id: string;
  
  /** Original filename */
  filename: string;
  
  /** Relative path within project assets */
  path: string;
  
  /** Full URL for display */
  url: string;
  
  /** Current lifecycle status */
  status: AssetStatus;
  
  /** Original user prompt */
  userPrompt: string;
  
  /** Engineered prompt sent to provider */
  engineeredPrompt: string;
  
  /** Provider that generated this image */
  provider: ImageProvider;
  
  /** Detected guitar attributes */
  category: GuitarCategory;
  bodyShape?: string;
  finish?: string;
  
  /** Generation settings */
  size: ImageSize;
  quality: ImageQuality;
  style: PhotoStyle;
  
  /** Cost in USD */
  cost: number;
  
  /** Timestamps */
  createdAt: string;   // ISO 8601
  updatedAt: string;   // ISO 8601
  
  /** Attached to design element (optional) */
  attachedTo?: string;
  
  /** User rating for feedback (1-5) */
  rating?: number;
  
  /** User notes */
  notes?: string;
}
```

#### `ImageAssetManifest` — Project Manifest

```typescript
/**
 * Manifest file tracking all AI images in a project.
 * Path: data/projects/{projectId}/assets/ai_images/manifest.json
 */
interface ImageAssetManifest {
  version: string;
  projectId: string;
  images: ImageAsset[];
  
  /** Aggregated statistics */
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
```

---

### UI Types

```typescript
/** Quick tag for prompt building */
interface QuickTag {
  label: string;
  value: string;
  category: 'body' | 'finish' | 'hardware' | 'wood' | 'style';
}

/** Gallery filter options */
interface GalleryFilters {
  category?: GuitarCategory;
  provider?: ImageProvider;
  status?: AssetStatus;
  minRating?: number;
  search?: string;
}

/** Sort options */
type GallerySortBy = 'createdAt' | 'rating' | 'cost' | 'provider';
type SortDirection = 'asc' | 'desc';

/** Component events */
interface AiImageEvents {
  'generation:complete': GenerationResponse;
  'image:select': ImageAsset;
  'image:attach': { imageId: string; targetId: string };
  'image:download': ImageAsset;
  'image:delete': string;
  'image:rate': { imageId: string; rating: number };
}
```

---

## API Client Functions

Location: `api.ts`

| Function | Endpoint | Description |
|----------|----------|-------------|
| `generateImages(request)` | `POST /api/vision/generate` | Generate guitar images |
| `previewPrompt(request)` | `POST /api/vision/prompt` | Preview engineered prompt |
| `getVocabulary()` | `GET /api/vision/vocabulary` | Get dropdown options |
| `getProviders()` | `GET /api/vision/providers` | List available providers |
| `submitFeedback(requestId, imageId, rating?)` | `POST /api/vision/feedback` | Submit rating feedback |
| `uploadAsset(projectId, image, metadata)` | `POST /api/assets/upload` | Store image in project |
| `getProjectAssets(projectId)` | `GET /api/assets/{projectId}` | List project images |
| `deleteAsset(assetId)` | `DELETE /api/assets/{id}` | Remove image |
| `updateAsset(assetId, updates)` | `PATCH /api/assets/{id}` | Update metadata |
| `estimateCost(count, quality, provider)` | (local) | Calculate cost estimate |
| `downloadImageFromUrl(url)` | (utility) | Download image blob |
| `downloadBase64Image(data)` | (utility) | Convert base64 to blob |

---

## Pinia Store API

Location: `useAiImageStore.ts`

### State

```typescript
interface AiImageState {
  images: ImageAsset[];              // All images in project
  selectedId: string | null;         // Currently selected
  projectId: string | null;          // Current project
  isGenerating: boolean;             // Generation in progress
  isLoadingVocabulary: boolean;
  isLoadingProviders: boolean;
  isLoadingAssets: boolean;
  vocabulary: VocabularyResponse | null;
  providers: ProviderInfo[];
  sessionCost: number;               // Cost this session
  sessionCount: number;              // Images this session
  error: string | null;
  filters: GalleryFilters;
  sortBy: GallerySortBy;
  sortDirection: SortDirection;
  lastGenerationResponse: GenerationResponse | null;
}
```

### Getters

```typescript
selectedImage: ImageAsset | null        // Currently selected image
filteredImages: ImageAsset[]            // After filters & sorting
generatingImages: ImageAsset[]          // Status === 'generating'
totalCost: number                       // Sum of all image costs
providerStats: Record<string, Stats>    // Per-provider statistics
availableProviders: ProviderInfo[]      // Only available providers
bodyShapeOptions: string[]              // From vocabulary
finishOptions: string[]                 // From vocabulary
```

### Actions

```typescript
// Generation
generate(request: GenerationRequest): Promise<void>
previewPrompt(prompt: string, style?: PhotoStyle): Promise<PromptPreviewResponse>

// Selection
selectImage(id: string): void
clearSelection(): void

// Asset management
loadProjectAssets(projectId: string): Promise<void>
rateImage(id: string, rating: number): Promise<void>
deleteImage(id: string): Promise<void>
attachImage(imageId: string, targetId: string): Promise<void>
downloadImage(id: string): Promise<void>

// Data loading
loadVocabulary(): Promise<void>
loadProviders(): Promise<void>

// Filtering
setFilter(key: keyof GalleryFilters, value: any): void
clearFilters(): void
setSort(by: GallerySortBy, direction?: SortDirection): void

// Utilities
getEstimate(count: number, quality: ImageQuality, provider: ImageProvider): number
```

---

## Component Hierarchy

```
┌─────────────────────────────────────────────────────────────────┐
│  AiImagePanel.vue                        (Main Entry Point)     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Quick Tags Row                                           │  │
│  │  [Les Paul] [Strat] [Tele] [Sunburst] [Natural] ...      │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Prompt Input                                             │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │ Describe your guitar...                             │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Options Row                                              │  │
│  │  Provider: [Auto ▾]  Quality: [Standard ▾]  Count: [2]   │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  [✨ Generate]                          Est: $0.04       │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  AiImageGallery.vue                                       │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐         │  │
│  │  │  img 1  │ │  img 2  │ │  img 3  │ │  img 4  │         │  │
│  │  │ ⭐⭐⭐⭐ │ │ ⭐⭐⭐   │ │ ⏳      │ │ ❌      │         │  │
│  │  │ DALL-E  │ │ SDXL    │ │ ...     │ │ Failed  │         │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘         │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  AiImageProperties.vue                   (Right Sidebar)        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  [Large Image Preview]                                    │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Details                                                  │  │
│  │  ID:       abc123...                                      │  │
│  │  Provider: DALL-E 3                                       │  │
│  │  Category: Electric                                       │  │
│  │  Body:     Les Paul                                       │  │
│  │  Finish:   Sunburst                                       │  │
│  │  Cost:     $0.02                                          │  │
│  │  Created:  12/19/2025, 3:45 PM                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Rating: ⭐⭐⭐⭐☆                                         │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  [📎 Attach] [⬇ Download] [🔄 Regenerate] [🗑 Delete]    │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Usage Examples

### Basic Import

```typescript
import {
  AiImagePanel,
  AiImageGallery,
  AiImageProperties,
  useAiImageStore,
  type ImageAsset,
  type GenerationRequest,
} from '@/features/ai_images';
```

### Initialize Store

```typescript
const store = useAiImageStore();

// Load vocabulary and providers on mount
onMounted(async () => {
  await store.loadVocabulary();
  await store.loadProviders();
  await store.loadProjectAssets(projectId);
});
```

### Generate Images

```typescript
async function handleGenerate() {
  await store.generate({
    prompt: 'Les Paul with cherry sunburst finish and gold hardware',
    numImages: 2,
    quality: 'standard',
    style: 'product',
    provider: 'auto',
    projectId: currentProjectId,
  });
}
```

### Preview Prompt Engineering

```typescript
const preview = await store.previewPrompt(
  'sunburst strat',
  'dramatic'
);

console.log(preview.positivePrompt);
// → "Professional studio photograph of a Fender Stratocaster 
//    electric guitar with classic sunburst finish, dramatic 
//    lighting with deep shadows..."

console.log(preview.category);      // 'electric'
console.log(preview.bodyShape);     // 'stratocaster'
console.log(preview.confidence);    // 0.95
```

### Handle Selection & Actions

```typescript
// In template
<AiImageGallery
  :images="store.filteredImages"
  :selected-id="store.selectedId"
  @select="store.selectImage"
  @rate="(id, rating) => store.rateImage(id, rating)"
  @download="store.downloadImage"
  @delete="store.deleteImage"
/>

<AiImageProperties
  :image="store.selectedImage"
  @attach="handleAttach"
  @regenerate="handleRegenerate"
/>
```

### Filter Gallery

```typescript
// By category
store.setFilter('category', 'electric');

// By provider
store.setFilter('provider', 'dalle3');

// By minimum rating
store.setFilter('minRating', 4);

// Search
store.setFilter('search', 'sunburst');

// Clear all filters
store.clearFilters();

// Sort
store.setSort('rating', 'desc');
```

---

## Related Documentation

- [AI_IMAGES_INTEGRATION.md](./AI_IMAGES_INTEGRATION.md) — Integration guide
- [vision_routes.py](../../../services/api/app/_experimental/ai_graphics/api/vision_routes.py) — Backend endpoints
- [vocabulary.py](../../../services/api/app/_experimental/ai_graphics/vocabulary.py) — Guitar vocabulary definitions
- [prompt_engine.py](../../../services/api/app/_experimental/ai_graphics/prompt_engine.py) — Prompt engineering logic
