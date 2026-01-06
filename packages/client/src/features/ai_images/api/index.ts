/**
 * AI Images API — Barrel Export
 * 
 * Unified exports for all API clients.
 * 
 * @package features/ai_images/api
 */

// =============================================================================
// HTTP UTILITIES
// =============================================================================

export {
  ApiError,
  fetchWithTimeout,
  postJson,
  getJson,
  patchJson,
  putJson,
  deleteJson,
  postFormData,
  GENERATION_TIMEOUT_MS,
} from './http';

// =============================================================================
// ADVISORY API (45 endpoints)
// =============================================================================

export {
  // Types
  type AdvisoryAsset,
  type AdvisoryListResponse,
  type AdvisoryStats,
  type CostEstimate,
  type BudgetStatus,
  type StylePreset,
  type PromptTemplate,
  type SimilarityMatch,

  // Asset CRUD
  generateAsset,
  listAssets,
  getAsset,
  updateAsset as updateAdvisoryAsset,
  deleteAsset as deleteAdvisoryAsset,

  // Review Workflow
  approveAsset,
  rejectAsset,
  bulkReview,
  getPendingAssets,

  // Run Attachment
  attachToRun,
  getRunAttachments,
  detachFromRun,

  // Cost & Budget
  estimateCost as estimateAdvisoryCost,
  getBudgetStatus,
  compareCosts,

  // Style Presets
  getStylePresets,
  getStylePreset,
  createStylePreset,
  updateStylePreset,
  deleteStylePreset,

  // Duplicate Detection
  checkDuplicates,
  findSimilar,

  // Prompt History & Templates
  getPromptHistory,
  getPromptTemplates,
  createPromptTemplate,
  deletePromptTemplate,

  // Favorites & Queues
  addToFavorites,
  removeFromFavorites,
  getFavorites,
  getReviewQueue,

  // Export
  exportAsJson,
  exportAsCsv,
  exportTrainingData as exportAdvisoryTrainingData,

  // Stats
  getStats as getAdvisoryStats,
} from './advisory';

// =============================================================================
// TEACHING API (4 endpoints)
// =============================================================================

export {
  // Types
  type TeachingStats,
  type TrainingReadiness,
  type WorkflowStatus,
  type TrainingExport,
  
  // Endpoints
  exportTrainingData,
  getTeachingStats,
  checkTrainingReadiness,
  getWorkflowStatus,
  
  // Convenience
  canStartTraining,
  getTrainingProgress,
} from './teaching';

// =============================================================================
// SESSION API (2 endpoints)
// =============================================================================

export {
  // Types
  type SessionSummary,
  type SessionResetResult,
  
  // Endpoints
  getSessionSummary,
  resetSession,
  
  // Convenience
  getSessionCost,
  getSessionImageCount,
  isSessionActive,
} from './session';

// =============================================================================
// AI API (2 endpoints)
// =============================================================================

export {
  // Types
  type AiSuggestion,
  type AiHealthStatus,
  
  // Endpoints
  getAiSuggestions,
  getAiHealth,
  
  // Convenience
  isAiAvailable,
  getBestProvider,
  getSuggestedParams,
} from './ai';
