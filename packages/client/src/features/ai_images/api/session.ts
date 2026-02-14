/**
 * Session API Client
 * 
 * Wires to /api/ai/session/* endpoints (2 total).
 * Session management for AI image generation.
 * 
 * @package features/ai_images/api
 */

import { getJson, postJson } from './http';

const BASE = (import.meta as any).env?.VITE_API_BASE || '';
const API_BASE = `${BASE}/api/ai/session`;

// =============================================================================
// TYPES
// =============================================================================

export interface SessionSummary {
  sessionId: string;
  startedAt: string;
  lastActivityAt: string;
  stats: {
    totalGenerations: number;
    totalImages: number;
    totalCost: number;
    avgRating: number;
    successRate: number;
  };
  providerUsage: Record<string, {
    generations: number;
    images: number;
    cost: number;
    avgTime: number;
  }>;
  recentPrompts: {
    prompt: string;
    timestamp: string;
    imageCount: number;
    rating?: number;
  }[];
  topCategories: { category: string; count: number }[];
}

export interface SessionResetResult {
  previousSessionId: string;
  newSessionId: string;
  resetAt: string;
  archivedStats: SessionSummary['stats'];
}

// =============================================================================
// ENDPOINTS
// =============================================================================

/**
 * Get current session summary.
 * 
 * GET /api/ai/session/summary
 */
export async function getSessionSummary(): Promise<SessionSummary> {
  return getJson(`${API_BASE}/summary`);
}

/**
 * Reset session (start fresh).
 * 
 * POST /api/ai/session/reset
 */
export async function resetSession(params?: {
  archiveStats?: boolean;
  reason?: string;
}): Promise<SessionResetResult> {
  return postJson(`${API_BASE}/reset`, {
    archive_stats: params?.archiveStats ?? true,
    reason: params?.reason,
  });
}

// =============================================================================
// CONVENIENCE FUNCTIONS
// =============================================================================

/**
 * Get session cost so far.
 */
export async function getSessionCost(): Promise<number> {
  const summary = await getSessionSummary();
  return summary.stats.totalCost;
}

/**
 * Get session image count.
 */
export async function getSessionImageCount(): Promise<number> {
  const summary = await getSessionSummary();
  return summary.stats.totalImages;
}

/**
 * Check if session is active (has activity).
 */
export async function isSessionActive(): Promise<boolean> {
  const summary = await getSessionSummary();
  return summary.stats.totalGenerations > 0;
}
