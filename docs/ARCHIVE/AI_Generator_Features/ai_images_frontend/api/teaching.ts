/**
 * Teaching API Client
 * 
 * Wires to /api/teaching/* endpoints (4 total).
 * User feedback collection and LoRA training data generation.
 * 
 * @package features/ai_images/api
 */

import { getJson, postJson } from './http';

const API_BASE = '/api/teaching';

// =============================================================================
// TYPES
// =============================================================================

export interface TeachingStats {
  totalFeedback: number;
  positiveFeedback: number;
  negativeFeedback: number;
  averageRating: number;
  ratingDistribution: Record<number, number>;
  topPrompts: { prompt: string; avgRating: number; count: number }[];
  providerPreference: Record<string, { preferred: number; total: number }>;
  recentActivity: { date: string; count: number }[];
}

export interface TrainingReadiness {
  ready: boolean;
  reasons: string[];
  metrics: {
    totalSamples: number;
    minRequired: number;
    highQualitySamples: number;
    diversityScore: number;
    recommendedEpochs: number;
  };
  recommendations: string[];
}

export interface WorkflowStatus {
  stage: 'collecting' | 'preparing' | 'training' | 'evaluating' | 'complete' | 'idle';
  progress: number;
  currentStep: string;
  estimatedTimeRemaining?: number;
  lastTrainingRun?: {
    startedAt: string;
    completedAt?: string;
    samplesUsed: number;
    epochs: number;
    finalLoss?: number;
  };
  nextScheduledRun?: string;
}

export interface TrainingExport {
  format: 'kohya' | 'dreambooth' | 'lora';
  samples: number;
  downloadUrl: string;
  expiresAt: string;
  config: Record<string, unknown>;
}

// =============================================================================
// ENDPOINTS
// =============================================================================

/**
 * Export training data for LoRA fine-tuning.
 * 
 * POST /api/teaching/export
 */
export async function exportTrainingData(params?: {
  format?: 'kohya' | 'dreambooth' | 'lora';
  minRating?: number;
  maxSamples?: number;
  includeNegative?: boolean;
}): Promise<TrainingExport> {
  return postJson(`${API_BASE}/export`, {
    format: params?.format ?? 'kohya',
    min_rating: params?.minRating ?? 4,
    max_samples: params?.maxSamples,
    include_negative: params?.includeNegative ?? false,
  });
}

/**
 * Get learning statistics.
 * 
 * GET /api/teaching/stats
 */
export async function getTeachingStats(params?: {
  projectId?: string;
  fromDate?: string;
  toDate?: string;
}): Promise<TeachingStats> {
  const query = new URLSearchParams();
  if (params?.projectId) query.set('project_id', params.projectId);
  if (params?.fromDate) query.set('from_date', params.fromDate);
  if (params?.toDate) query.set('to_date', params.toDate);
  
  const url = query.toString() ? `${API_BASE}/stats?${query}` : `${API_BASE}/stats`;
  return getJson(url);
}

/**
 * Check training readiness.
 * 
 * GET /api/teaching/ready
 */
export async function checkTrainingReadiness(params?: {
  targetSamples?: number;
  minQuality?: number;
}): Promise<TrainingReadiness> {
  const query = new URLSearchParams();
  if (params?.targetSamples) query.set('target_samples', String(params.targetSamples));
  if (params?.minQuality) query.set('min_quality', String(params.minQuality));
  
  const url = query.toString() ? `${API_BASE}/ready?${query}` : `${API_BASE}/ready`;
  return getJson(url);
}

/**
 * Get LoRA workflow status.
 * 
 * GET /api/teaching/workflow
 */
export async function getWorkflowStatus(): Promise<WorkflowStatus> {
  return getJson(`${API_BASE}/workflow`);
}

// =============================================================================
// CONVENIENCE FUNCTIONS
// =============================================================================

/**
 * Check if enough data exists for training.
 */
export async function canStartTraining(minSamples: number = 100): Promise<boolean> {
  const readiness = await checkTrainingReadiness({ targetSamples: minSamples });
  return readiness.ready;
}

/**
 * Get training progress (0-100).
 */
export async function getTrainingProgress(): Promise<number> {
  const status = await getWorkflowStatus();
  return status.progress;
}
