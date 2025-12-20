/**
 * AI Routes API Client
 * 
 * Wires to /api/ai/* endpoints (2 total).
 * AI parameter suggestions and health checks.
 * 
 * @package features/ai_images/api
 */

import { getJson, postJson } from './http';

const API_BASE = '/api/ai';

// =============================================================================
// TYPES
// =============================================================================

export interface AiSuggestion {
  provider: string;
  providerReason: string;
  quality: string;
  qualityReason: string;
  style: string;
  styleReason: string;
  promptEnhancements: string[];
  negativePrompt: string;
  estimatedCost: number;
  estimatedTime: number;
  confidence: number;
}

export interface AiHealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  providers: Record<string, {
    available: boolean;
    latency: number;
    errorRate: number;
    lastError?: string;
  }>;
  services: Record<string, {
    status: 'up' | 'down' | 'degraded';
    message?: string;
  }>;
  timestamp: string;
}

// =============================================================================
// ENDPOINTS
// =============================================================================

/**
 * Get AI parameter suggestions based on prompt.
 * 
 * POST /api/ai/suggest
 */
export async function getAiSuggestions(params: {
  prompt: string;
  context?: {
    projectType?: string;
    preferredProvider?: string;
    budgetLimit?: number;
    qualityPriority?: 'speed' | 'quality' | 'balanced';
  };
}): Promise<AiSuggestion> {
  return postJson(`${API_BASE}/suggest`, {
    prompt: params.prompt,
    context: params.context ? {
      project_type: params.context.projectType,
      preferred_provider: params.context.preferredProvider,
      budget_limit: params.context.budgetLimit,
      quality_priority: params.context.qualityPriority,
    } : undefined,
  });
}

/**
 * Check AI subsystem health.
 * 
 * GET /api/ai/health
 */
export async function getAiHealth(): Promise<AiHealthStatus> {
  return getJson(`${API_BASE}/health`);
}

// =============================================================================
// CONVENIENCE FUNCTIONS
// =============================================================================

/**
 * Check if AI services are available.
 */
export async function isAiAvailable(): Promise<boolean> {
  try {
    const health = await getAiHealth();
    return health.status !== 'unhealthy';
  } catch {
    return false;
  }
}

/**
 * Get best provider based on current health.
 */
export async function getBestProvider(): Promise<string | null> {
  const health = await getAiHealth();
  
  let bestProvider: string | null = null;
  let bestLatency = Infinity;
  
  for (const [provider, status] of Object.entries(health.providers)) {
    if (status.available && status.latency < bestLatency) {
      bestLatency = status.latency;
      bestProvider = provider;
    }
  }
  
  return bestProvider;
}

/**
 * Get suggested parameters with smart defaults.
 */
export async function getSuggestedParams(prompt: string): Promise<{
  provider: string;
  quality: string;
  style: string;
}> {
  const suggestion = await getAiSuggestions({ prompt });
  return {
    provider: suggestion.provider,
    quality: suggestion.quality,
    style: suggestion.style,
  };
}
