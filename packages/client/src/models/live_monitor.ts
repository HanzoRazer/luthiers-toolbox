/**
 * MM-6: Fragility-Aware Live Monitor Models
 * 
 * TypeScript models for real-time job events with material fragility context.
 * Extends N10.0 Live Monitor with materials[], worst_fragility_score, fragility_band, lane_hint.
 */

/**
 * Fragility bands for material profiles
 * - stable: < 0.4 (green badges, safe for all lanes)
 * - medium: 0.4-0.69 (yellow badges, caution in promotion lanes)
 * - fragile: ≥ 0.7 (red badges, critical risk, blocked from promotion)
 * - unknown: None (gray badges, no CAM profile data)
 */
export type FragilityBand = 'stable' | 'medium' | 'fragile' | 'unknown'

/**
 * Live Monitor WebSocket event with fragility enrichment
 * 
 * Enriched by backend services/api/app/websocket/monitor.py via
 * build_fragility_context_for_job() from live_monitor_fragility.py
 */
export interface LiveMonitorEvent {
  type: string          // e.g., 'job:started', 'pattern:created'
  timestamp: string     // ISO 8601 timestamp
  data: {
    job_id?: string
    name?: string
    status?: string
    
    // MM-6 Fragility Context (enriched by backend)
    materials?: string[]              // e.g., ['maple', 'walnut']
    worst_fragility_score?: number    // 0.0-1.0 (highest risk across all materials)
    fragility_band?: FragilityBand    // Classified risk level
    lane_hint?: string                // Suggested lane: 'baseline' | 'promo' | 'stable'
    
    // Other job fields (flexible)
    [key: string]: any
  }
}

/**
 * Helper to classify fragility scores into bands
 * Matches backend logic in services/api/app/core/live_monitor_fragility.py
 */
export function classifyFragility(score: number | null | undefined): FragilityBand {
  if (score === null || score === undefined) return 'unknown'
  if (score < 0.4) return 'stable'
  if (score < 0.7) return 'medium'
  return 'fragile'
}

/**
 * Badge color classes for fragility bands
 */
export function fragilityBadgeClass(band: FragilityBand): string {
  switch (band) {
    case 'stable': return 'fragility-stable'
    case 'medium': return 'fragility-medium'
    case 'fragile': return 'fragility-fragile'
    case 'unknown': return 'fragility-unknown'
  }
}

/**
 * Human-readable labels for fragility bands
 */
export function fragilityLabel(band: FragilityBand): string {
  switch (band) {
    case 'stable': return 'Stable'
    case 'medium': return 'Medium'
    case 'fragile': return 'Fragile'
    case 'unknown': return 'Unknown'
  }
}

/**
 * Tooltip titles for fragility bands
 */
export function fragilityTitle(band: FragilityBand, score?: number): string {
  const scoreStr = score !== undefined ? ` (${(score * 100).toFixed(0)}%)` : ''
  switch (band) {
    case 'stable': return `Stable profile${scoreStr} - Safe for all lanes`
    case 'medium': return `Medium risk${scoreStr} - Caution in promo lanes`
    case 'fragile': return `Fragile profile${scoreStr} - High risk, avoid promotion`
    case 'unknown': return 'No fragility data available'
  }
}
