/**
 * AI Images Feature — API Client
 * 
 * Calls the server-side /api/vision/* endpoints.
 * Server handles provider API keys and cost tracking.
 * 
 * @package features/ai_images
 */

import {
  ImageQuality,
  ImageSize,
  PhotoStyle,
  ImageProvider,
} from './types';
import type {
  GenerationRequest,
  GenerationResponse,
  PromptPreviewRequest,
  PromptPreviewResponse,
  VocabularyResponse,
  ProvidersResponse,
  ImageAsset,
  ImageAssetManifest,
} from './types';

// =============================================================================
// CONFIGURATION
// =============================================================================

/** Base URL for API calls - uses VITE_API_BASE for cross-origin deployments */
const BASE = (import.meta as any).env?.VITE_API_BASE || '';
const API_BASE = `${BASE}/api`;

/** Default timeout for generation (images can take a while) */
const GENERATION_TIMEOUT_MS = 60000;

/** Default timeout for other requests */
const DEFAULT_TIMEOUT_MS = 10000;

// =============================================================================
// HTTP HELPERS
// =============================================================================

interface FetchOptions extends RequestInit {
  timeout?: number;
}

/**
 * Fetch with timeout and error handling.
 */
async function fetchWithTimeout(
  url: string,
  options: FetchOptions = {}
): Promise<Response> {
  const { timeout = DEFAULT_TIMEOUT_MS, ...fetchOptions } = options;
  
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);
  
  try {
    const response = await fetch(url, {
      ...fetchOptions,
      signal: controller.signal,
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new ApiError(
        error.detail || error.message || `HTTP ${response.status}`,
        response.status
      );
    }
    
    return response;
  } finally {
    clearTimeout(timeoutId);
  }
}

/**
 * POST JSON request.
 */
async function postJson<T>(
  url: string,
  body: unknown,
  timeout?: number
): Promise<T> {
  const response = await fetchWithTimeout(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
    timeout,
  });
  return response.json();
}

/**
 * GET request.
 */
async function getJson<T>(url: string): Promise<T> {
  const response = await fetchWithTimeout(url);
  return response.json();
}

// =============================================================================
// ERROR HANDLING
// =============================================================================

export class ApiError extends Error {
  constructor(
    message: string,
    public statusCode: number = 500,
    public details?: unknown
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// =============================================================================
// VISION API
// =============================================================================

/**
 * Generate guitar images.
 * 
 * @param request - Generation parameters
 * @returns Generated images and metadata
 */
export async function generateImages(
  request: GenerationRequest
): Promise<GenerationResponse> {
  // Map to API expected format (snake_case)
  const apiRequest = {
    prompt: request.prompt,
    num_images: request.numImages ?? 2,
    size: request.size ?? ImageSize.SQUARE_LG,
    quality: request.quality ?? ImageQuality.STANDARD,
    photo_style: request.style ?? PhotoStyle.PRODUCT,
    provider: request.provider ?? ImageProvider.AUTO,
  };
  
  const response = await postJson<any>(
    `${API_BASE}/vision/generate`,
    apiRequest,
    GENERATION_TIMEOUT_MS
  );
  
  // Map response to camelCase
  return {
    success: response.success,
    requestId: response.request_id,
    images: response.images.map((img: any) => ({
      imageId: img.image_id,
      url: img.url,
      base64Data: img.base64_data,
      provider: img.provider,
      revisedPrompt: img.revised_prompt,
    })),
    engineeredPrompt: response.engineered_prompt,
    detectedCategory: response.detected_category,
    detectedBodyShape: response.detected_body_shape,
    detectedFinish: response.detected_finish,
    parseConfidence: response.parse_confidence,
    providerUsed: response.provider_used,
    estimatedCost: response.estimated_cost,
    actualCost: response.actual_cost,
    totalTimeMs: response.total_time_ms,
    error: response.error,
  };
}

/**
 * Preview prompt engineering without generating.
 * 
 * @param request - Prompt to analyze
 * @returns Engineered prompts and detected attributes
 */
export async function previewPrompt(
  request: PromptPreviewRequest
): Promise<PromptPreviewResponse> {
  const apiRequest = {
    prompt: request.prompt,
    photo_style: request.style,
    include_variations: request.includeVariations ?? false,
  };
  
  const response = await postJson<any>(
    `${API_BASE}/vision/prompt`,
    apiRequest
  );
  
  return {
    positivePrompt: response.positive_prompt,
    negativePrompt: response.negative_prompt,
    category: response.category,
    bodyShape: response.body_shape,
    finish: response.finish,
    confidence: response.confidence,
    variations: response.variations?.map((v: any) => ({
      style: v.style,
      positivePrompt: v.positive_prompt,
    })),
  };
}

/**
 * Get vocabulary for dropdowns.
 */
export async function getVocabulary(): Promise<VocabularyResponse> {
  const response = await getJson<any>(`${API_BASE}/vision/vocabulary`);
  
  return {
    bodyShapes: response.body_shapes,
    finishes: response.finishes,
    photoStyles: response.photo_styles,
  };
}

/**
 * Get available providers and their status.
 * FIX: Maps API's "configured" field to frontend's "available" field.
 */
export async function getProviders(): Promise<ProvidersResponse> {
  const response = await getJson<any>(`${API_BASE}/vision/providers`);

  // Debug: log raw API response (remove after verification)
  console.log('[ai-images/api] getProviders raw response:', response);

  return {
    providers: response.providers.map((p: any) => ({
      id: p.id ?? p.name,
      name: p.name,
      // API returns "configured" not "available" - map correctly
      available: p.available ?? p.configured ?? false,
      reason: p.reason,
      costs: p.costs,
    })),
  };
}

/**
 * Submit feedback for a generation (for learning).
 * 
 * @param requestId - The generation request ID
 * @param selectedImageId - Which image the user preferred
 * @param rating - Optional 1-5 rating
 */
export async function submitFeedback(
  requestId: string,
  selectedImageId: string,
  rating?: number
): Promise<void> {
  await postJson(`${API_BASE}/vision/feedback`, {
    request_id: requestId,
    selected_image_id: selectedImageId,
    rating,
  });
}

// =============================================================================
// ASSET STORAGE API
// =============================================================================

/**
 * Upload an image to the project asset store.
 * 
 * @param projectId - Project to store in
 * @param image - Image data (URL or base64)
 * @param metadata - Asset metadata
 * @returns Stored asset
 */
export async function uploadAsset(
  projectId: string,
  image: { url?: string; base64?: string },
  metadata: Partial<ImageAsset>
): Promise<ImageAsset> {
  const formData = new FormData();
  
  // If we have base64, convert to blob
  if (image.base64) {
    const blob = base64ToBlob(image.base64, 'image/png');
    formData.append('file', blob, `${metadata.id ?? 'image'}.png`);
  } else if (image.url) {
    formData.append('url', image.url);
  }
  
  formData.append('metadata', JSON.stringify(metadata));
  
  const response = await fetchWithTimeout(
    `${API_BASE}/projects/${projectId}/assets/ai_images`,
    {
      method: 'POST',
      body: formData,
    }
  );
  
  return response.json();
}

/**
 * Get all AI image assets for a project.
 */
export async function getProjectAssets(
  projectId: string
): Promise<ImageAsset[]> {
  const response = await getJson<ImageAssetManifest>(
    `${API_BASE}/projects/${projectId}/assets/ai_images`
  );
  return response.images;
}

/**
 * Get asset manifest for a project.
 */
export async function getAssetManifest(
  projectId: string
): Promise<ImageAssetManifest> {
  return getJson(`${API_BASE}/projects/${projectId}/assets/ai_images/manifest`);
}

/**
 * Delete an asset.
 */
export async function deleteAsset(
  projectId: string,
  assetId: string
): Promise<void> {
  await fetchWithTimeout(
    `${API_BASE}/projects/${projectId}/assets/ai_images/${assetId}`,
    { method: 'DELETE' }
  );
}

/**
 * Update asset metadata (rating, notes, etc).
 */
export async function updateAsset(
  projectId: string,
  assetId: string,
  updates: Partial<ImageAsset>
): Promise<ImageAsset> {
  return postJson(
    `${API_BASE}/projects/${projectId}/assets/ai_images/${assetId}`,
    updates
  );
}

// =============================================================================
// UTILITIES
// =============================================================================

/**
 * Convert base64 string to Blob.
 */
function base64ToBlob(base64: string, mimeType: string): Blob {
  const byteCharacters = atob(base64);
  const byteNumbers = new Array(byteCharacters.length);
  
  for (let i = 0; i < byteCharacters.length; i++) {
    byteNumbers[i] = byteCharacters.charCodeAt(i);
  }
  
  const byteArray = new Uint8Array(byteNumbers);
  return new Blob([byteArray], { type: mimeType });
}

/**
 * Download an image from URL.
 */
export async function downloadImageFromUrl(
  url: string,
  filename: string
): Promise<void> {
  const response = await fetch(url);
  const blob = await response.blob();
  
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(link.href);
}

/**
 * Download base64 image.
 */
export function downloadBase64Image(
  base64: string,
  filename: string
): void {
  const link = document.createElement('a');
  link.href = `data:image/png;base64,${base64}`;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

/**
 * Get estimated cost for a generation request.
 */
export function estimateCost(
  numImages: number,
  quality: ImageQuality,
  provider: ImageProvider
): number {
  const baseCosts: Record<ImageProvider, Record<ImageQuality, number>> = {
    [ImageProvider.DALLE3]: {
      [ImageQuality.DRAFT]: 0.04,
      [ImageQuality.STANDARD]: 0.04,
      [ImageQuality.HD]: 0.08,
    },
    [ImageProvider.SDXL]: {
      [ImageQuality.DRAFT]: 0.002,
      [ImageQuality.STANDARD]: 0.004,
      [ImageQuality.HD]: 0.008,
    },
    [ImageProvider.GUITAR_LORA]: {
      [ImageQuality.DRAFT]: 0.005,
      [ImageQuality.STANDARD]: 0.01,
      [ImageQuality.HD]: 0.02,
    },
    [ImageProvider.STUB]: {
      [ImageQuality.DRAFT]: 0,
      [ImageQuality.STANDARD]: 0,
      [ImageQuality.HD]: 0,
    },
    [ImageProvider.AUTO]: {
      [ImageQuality.DRAFT]: 0.01,
      [ImageQuality.STANDARD]: 0.02,
      [ImageQuality.HD]: 0.04,
    },
  };
  
  const providerCosts = baseCosts[provider] ?? baseCosts[ImageProvider.AUTO];
  const unitCost = providerCosts[quality] ?? providerCosts[ImageQuality.STANDARD];
  
  return numImages * unitCost;
}
