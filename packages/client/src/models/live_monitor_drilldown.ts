/**
 * RMOS N10.1: LiveMonitor Drill-Down Models
 * 
 * TypeScript interfaces for subjob and CAM event drill-down data.
 */

export type SubjobType =
  | "roughing"
  | "profiling"
  | "finishing"
  | "cleanup"
  | "infeed"
  | "outfeed";

export type FeedState =
  | "stable"
  | "increasing"
  | "decreasing"
  | "danger_low"
  | "danger_high";

export type HeuristicLevel = "info" | "warning" | "danger";

/**
 * Individual CAM event within a subjob.
 * 
 * Captures feed/spindle/DOC state with heuristic risk evaluation.
 */
export interface CAMEvent {
  timestamp: string;
  feedrate: number;
  spindle_speed: number;
  doc: number;
  feed_state: FeedState;
  heuristic: HeuristicLevel;
  message?: string | null;
}

/**
 * A subjob phase within a larger job (e.g., roughing → profiling → finishing).
 * 
 * Contains timeline and associated CAM events with heuristics.
 */
export interface SubjobEvent {
  subjob_type: SubjobType;
  started_at: string;
  ended_at?: string | null;
  cam_events: CAMEvent[];
}

/**
 * Complete drill-down response for a job.
 */
export interface DrilldownResponse {
  job_id: string;
  subjobs: SubjobEvent[];
}

/**
 * Helper to get CSS class for feed state badges.
 */
export function feedStateClass(state: FeedState): string {
  switch (state) {
    case 'stable': return 'feed-stable'
    case 'increasing': return 'feed-increasing'
    case 'decreasing': return 'feed-decreasing'
    case 'danger_low': return 'feed-danger-low'
    case 'danger_high': return 'feed-danger-high'
  }
}

/**
 * Helper to get CSS class for heuristic badges.
 */
export function heuristicClass(level: HeuristicLevel): string {
  switch (level) {
    case 'info': return 'heuristic-info'
    case 'warning': return 'heuristic-warning'
    case 'danger': return 'heuristic-danger'
  }
}

/**
 * Helper to get human-readable label for subjob type.
 */
export function subjobLabel(type: SubjobType): string {
  return type.charAt(0).toUpperCase() + type.slice(1)
}

/**
 * Helper to format timestamp for display.
 */
export function formatTimestamp(ts: string): string {
  try {
    const date = new Date(ts)
    return date.toLocaleTimeString()
  } catch {
    return ts
  }
}
