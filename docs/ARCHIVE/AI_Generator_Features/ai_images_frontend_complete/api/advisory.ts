/**
 * Advisory API Client
 * 
 * Wires to /api/advisory/* endpoints (45 total).
 * Human-in-the-loop review workflow for AI-generated images.
 * 
 * @package features/ai_images/api
 */

import { fetchWithTimeout, postJson, getJson, patchJson, deleteJson } from './http';

const API_BASE = '/api/advisory';

// =============================================================================
// TYPES
// =============================================================================

export interface AdvisoryAsset {
  id: string;
  projectId: string;
  imageUrl: string;
  thumbnailUrl?: string;
  prompt: string;
  engineeredPrompt: string;
  provider: string;
  status: 'pending' | 'approved' | 'rejected';
  category: string;
  bodyShape?: string;
  finish?: string;
  style: string;
  quality: string;
  size: string;
  cost: number;
  rating?: number;
  notes?: string;
  reviewedBy?: string;
  reviewedAt?: string;
  attachedToRunId?: string;
  attachedAt?: string;
  contentHash: string;
  createdAt: string;
  updatedAt: string;
}

export interface AdvisoryListResponse {
  assets: AdvisoryAsset[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}

export interface AdvisoryStats {
  total: number;
  pending: number;
  approved: number;
  rejected: number;
  attached: number;
  totalCost: number;
  avgRating: number;
  byProvider: Record<string, { count: number; cost: number; avgRating: number }>;
  byCategory: Record<string, number>;
}

export interface CostEstimate {
  provider: string;
  quality: string;
  size: string;
  numImages: number;
  unitCost: number;
  totalCost: number;
  currency: string;
}

export interface BudgetStatus {
  dailyLimit: number;
  dailyUsed: number;
  dailyRemaining: number;
  monthlyLimit: number;
  monthlyUsed: number;
  monthlyRemaining: number;
  lastReset: string;
}

export interface StylePreset {
  id: string;
  name: string;
  description: string;
  promptModifiers: string[];
  negativePrompt: string;
  recommendedProvider: string;
  exampleUrl?: string;
}

export interface PromptTemplate {
  id: string;
  name: string;
  template: string;
  variables: string[];
  category: string;
  createdAt: string;
}

export interface SimilarityMatch {
  assetId: string;
  similarity: number;
  asset: AdvisoryAsset;
}

// =============================================================================
// ASSET CRUD
// =============================================================================

/**
 * Generate new advisory asset.
 */
export async function generateAsset(params: {
  projectId: string;
  prompt: string;
  style?: string;
  quality?: string;
  size?: string;
  provider?: string;
  numImages?: number;
}): Promise<AdvisoryAsset[]> {
  return postJson(`${API_BASE}/assets/generate`, {
    project_id: params.projectId,
    prompt: params.prompt,
    style: params.style ?? 'product',
    quality: params.quality ?? 'standard',
    size: params.size ?? '1024x1024',
    provider: params.provider ?? 'auto',
    num_images: params.numImages ?? 1,
  });
}

/**
 * List advisory assets with filtering.
 */
export async function listAssets(params?: {
  projectId?: string;
  status?: 'pending' | 'approved' | 'rejected';
  category?: string;
  provider?: string;
  minRating?: number;
  search?: string;
  page?: number;
  pageSize?: number;
  sortBy?: string;
  sortDir?: 'asc' | 'desc';
}): Promise<AdvisoryListResponse> {
  const query = new URLSearchParams();
  if (params?.projectId) query.set('project_id', params.projectId);
  if (params?.status) query.set('status', params.status);
  if (params?.category) query.set('category', params.category);
  if (params?.provider) query.set('provider', params.provider);
  if (params?.minRating) query.set('min_rating', String(params.minRating));
  if (params?.search) query.set('search', params.search);
  if (params?.page) query.set('page', String(params.page));
  if (params?.pageSize) query.set('page_size', String(params.pageSize));
  if (params?.sortBy) query.set('sort_by', params.sortBy);
  if (params?.sortDir) query.set('sort_dir', params.sortDir);
  
  const url = query.toString() ? `${API_BASE}/assets?${query}` : `${API_BASE}/assets`;
  return getJson(url);
}

/**
 * Get single asset by ID.
 */
export async function getAsset(assetId: string): Promise<AdvisoryAsset> {
  return getJson(`${API_BASE}/assets/${assetId}`);
}

/**
 * Update asset metadata.
 */
export async function updateAsset(
  assetId: string,
  updates: Partial<Pick<AdvisoryAsset, 'rating' | 'notes' | 'category' | 'bodyShape' | 'finish'>>
): Promise<AdvisoryAsset> {
  return patchJson(`${API_BASE}/assets/${assetId}`, updates);
}

/**
 * Delete asset.
 */
export async function deleteAsset(assetId: string): Promise<void> {
  return deleteJson(`${API_BASE}/assets/${assetId}`);
}

// =============================================================================
// REVIEW WORKFLOW
// =============================================================================

/**
 * Approve asset for use.
 */
export async function approveAsset(
  assetId: string,
  reviewerNotes?: string
): Promise<AdvisoryAsset> {
  return postJson(`${API_BASE}/assets/${assetId}/approve`, {
    reviewer_notes: reviewerNotes,
  });
}

/**
 * Reject asset.
 */
export async function rejectAsset(
  assetId: string,
  reason: string
): Promise<AdvisoryAsset> {
  return postJson(`${API_BASE}/assets/${assetId}/reject`, {
    reason,
  });
}

/**
 * Bulk review multiple assets.
 */
export async function bulkReview(
  assetIds: string[],
  action: 'approve' | 'reject',
  reason?: string
): Promise<{ processed: number; failed: string[] }> {
  return postJson(`${API_BASE}/assets/bulk-review`, {
    asset_ids: assetIds,
    action,
    reason,
  });
}

/**
 * Get pending assets for review.
 */
export async function getPendingAssets(
  projectId?: string,
  limit?: number
): Promise<AdvisoryAsset[]> {
  const query = new URLSearchParams();
  if (projectId) query.set('project_id', projectId);
  if (limit) query.set('limit', String(limit));
  
  const url = query.toString() ? `${API_BASE}/pending?${query}` : `${API_BASE}/pending`;
  return getJson(url);
}

// =============================================================================
// RUN ATTACHMENT
// =============================================================================

/**
 * Attach asset to a run (immutable audit trail).
 */
export async function attachToRun(
  assetId: string,
  runId: string,
  attachmentType?: string
): Promise<AdvisoryAsset> {
  return postJson(`${API_BASE}/assets/${assetId}/attach-to-run`, {
    run_id: runId,
    attachment_type: attachmentType ?? 'reference',
  });
}

/**
 * Get assets attached to a run.
 */
export async function getRunAttachments(runId: string): Promise<AdvisoryAsset[]> {
  return getJson(`${API_BASE}/runs/${runId}/attachments`);
}

/**
 * Detach asset from run (if allowed).
 */
export async function detachFromRun(
  assetId: string,
  runId: string
): Promise<void> {
  return deleteJson(`${API_BASE}/assets/${assetId}/detach/${runId}`);
}

// =============================================================================
// COST & BUDGET
// =============================================================================

/**
 * Get cost estimate for generation.
 */
export async function estimateCost(params: {
  provider: string;
  quality: string;
  size: string;
  numImages: number;
}): Promise<CostEstimate> {
  return postJson(`${API_BASE}/cost/estimate`, {
    provider: params.provider,
    quality: params.quality,
    size: params.size,
    num_images: params.numImages,
  });
}

/**
 * Get budget status.
 */
export async function getBudgetStatus(): Promise<BudgetStatus> {
  return getJson(`${API_BASE}/cost/budget`);
}

/**
 * Compare costs across providers.
 */
export async function compareCosts(params: {
  quality: string;
  size: string;
  numImages: number;
}): Promise<CostEstimate[]> {
  return postJson(`${API_BASE}/cost/compare`, params);
}

// =============================================================================
// STYLE PRESETS
// =============================================================================

/**
 * Get available style presets.
 */
export async function getStylePresets(): Promise<StylePreset[]> {
  return getJson(`${API_BASE}/styles`);
}

/**
 * Get single style preset.
 */
export async function getStylePreset(presetId: string): Promise<StylePreset> {
  return getJson(`${API_BASE}/styles/${presetId}`);
}

/**
 * Create custom style preset.
 */
export async function createStylePreset(preset: Omit<StylePreset, 'id'>): Promise<StylePreset> {
  return postJson(`${API_BASE}/styles`, preset);
}

/**
 * Update style preset.
 */
export async function updateStylePreset(
  presetId: string,
  updates: Partial<StylePreset>
): Promise<StylePreset> {
  return patchJson(`${API_BASE}/styles/${presetId}`, updates);
}

/**
 * Delete style preset.
 */
export async function deleteStylePreset(presetId: string): Promise<void> {
  return deleteJson(`${API_BASE}/styles/${presetId}`);
}

// =============================================================================
// DUPLICATE DETECTION
// =============================================================================

/**
 * Check for duplicate/similar images.
 */
export async function checkDuplicates(
  assetId: string,
  threshold?: number
): Promise<SimilarityMatch[]> {
  const query = threshold ? `?threshold=${threshold}` : '';
  return getJson(`${API_BASE}/assets/${assetId}/duplicates${query}`);
}

/**
 * Find similar images by content hash.
 */
export async function findSimilar(
  contentHash: string,
  limit?: number
): Promise<SimilarityMatch[]> {
  const query = new URLSearchParams({ hash: contentHash });
  if (limit) query.set('limit', String(limit));
  return getJson(`${API_BASE}/similar?${query}`);
}

// =============================================================================
// PROMPT HISTORY & TEMPLATES
// =============================================================================

/**
 * Get prompt history.
 */
export async function getPromptHistory(params?: {
  projectId?: string;
  limit?: number;
}): Promise<{ prompt: string; usedAt: string; resultCount: number }[]> {
  const query = new URLSearchParams();
  if (params?.projectId) query.set('project_id', params.projectId);
  if (params?.limit) query.set('limit', String(params.limit));
  
  const url = query.toString() ? `${API_BASE}/prompts/history?${query}` : `${API_BASE}/prompts/history`;
  return getJson(url);
}

/**
 * Get prompt templates.
 */
export async function getPromptTemplates(category?: string): Promise<PromptTemplate[]> {
  const url = category ? `${API_BASE}/prompts/templates?category=${category}` : `${API_BASE}/prompts/templates`;
  return getJson(url);
}

/**
 * Create prompt template.
 */
export async function createPromptTemplate(
  template: Omit<PromptTemplate, 'id' | 'createdAt'>
): Promise<PromptTemplate> {
  return postJson(`${API_BASE}/prompts/templates`, template);
}

/**
 * Delete prompt template.
 */
export async function deletePromptTemplate(templateId: string): Promise<void> {
  return deleteJson(`${API_BASE}/prompts/templates/${templateId}`);
}

// =============================================================================
// FAVORITES & QUEUES
// =============================================================================

/**
 * Add asset to favorites.
 */
export async function addToFavorites(assetId: string): Promise<void> {
  return postJson(`${API_BASE}/assets/${assetId}/favorite`, {});
}

/**
 * Remove from favorites.
 */
export async function removeFromFavorites(assetId: string): Promise<void> {
  return deleteJson(`${API_BASE}/assets/${assetId}/favorite`);
}

/**
 * Get favorite assets.
 */
export async function getFavorites(projectId?: string): Promise<AdvisoryAsset[]> {
  const url = projectId ? `${API_BASE}/favorites?project_id=${projectId}` : `${API_BASE}/favorites`;
  return getJson(url);
}

/**
 * Get review queue (pending sorted by priority).
 */
export async function getReviewQueue(limit?: number): Promise<AdvisoryAsset[]> {
  const url = limit ? `${API_BASE}/queue?limit=${limit}` : `${API_BASE}/queue`;
  return getJson(url);
}

// =============================================================================
// EXPORT
// =============================================================================

/**
 * Export assets as JSON.
 */
export async function exportAsJson(params?: {
  projectId?: string;
  status?: string;
  fromDate?: string;
  toDate?: string;
}): Promise<Blob> {
  const query = new URLSearchParams();
  if (params?.projectId) query.set('project_id', params.projectId);
  if (params?.status) query.set('status', params.status);
  if (params?.fromDate) query.set('from_date', params.fromDate);
  if (params?.toDate) query.set('to_date', params.toDate);
  
  const url = query.toString() ? `${API_BASE}/export/json?${query}` : `${API_BASE}/export/json`;
  const response = await fetchWithTimeout(url);
  return response.blob();
}

/**
 * Export assets as CSV.
 */
export async function exportAsCsv(params?: {
  projectId?: string;
  status?: string;
}): Promise<Blob> {
  const query = new URLSearchParams();
  if (params?.projectId) query.set('project_id', params.projectId);
  if (params?.status) query.set('status', params.status);
  
  const url = query.toString() ? `${API_BASE}/export/csv?${query}` : `${API_BASE}/export/csv`;
  const response = await fetchWithTimeout(url);
  return response.blob();
}

/**
 * Export as training data format.
 */
export async function exportTrainingData(params?: {
  projectId?: string;
  minRating?: number;
  format?: 'kohya' | 'dreambooth' | 'lora';
}): Promise<Blob> {
  const query = new URLSearchParams();
  if (params?.projectId) query.set('project_id', params.projectId);
  if (params?.minRating) query.set('min_rating', String(params.minRating));
  if (params?.format) query.set('format', params.format);
  
  const url = query.toString() ? `${API_BASE}/export/training?${query}` : `${API_BASE}/export/training`;
  const response = await fetchWithTimeout(url);
  return response.blob();
}

// =============================================================================
// STATS
// =============================================================================

/**
 * Get advisory statistics.
 */
export async function getStats(projectId?: string): Promise<AdvisoryStats> {
  const url = projectId ? `${API_BASE}/stats?project_id=${projectId}` : `${API_BASE}/stats`;
  return getJson(url);
}
