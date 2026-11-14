/**
 * RosetteCompareHistory types.
 */

export interface CompareHistoryEntry {
  ts: string
  job_id: string | null
  lane: string
  baseline_id: string
  baseline_path_count: number
  current_path_count: number
  added_paths: number
  removed_paths: number
  unchanged_paths: number
  preset?: string | null
}

export interface PresetBucket {
  name: string
  entries: CompareHistoryEntry[]
}

export interface PresetSparklineData {
  name: string
  addedPath: string
  removedPath: string
}

export interface OverlayPaths {
  a: string
  b: string
}

export interface PairStats {
  aName: string
  bName: string
  aAdded: number
  bAdded: number
  deltaAdded: number
  aRemoved: number
  bRemoved: number
  deltaRemoved: number
  aUnchanged: number
  bUnchanged: number
  deltaUnchanged: number
}

// Sparkline dimensions
export const SPARK_WIDTH = 60
export const SPARK_HEIGHT = 20
