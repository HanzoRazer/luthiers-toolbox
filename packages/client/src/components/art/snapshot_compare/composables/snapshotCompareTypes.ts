/**
 * SnapshotComparePanel types.
 */

export type AnySnap = any

export interface RingRow {
  idx: number
  width_mm: number
  pattern: string
}

export interface DeltaRow {
  ring: number
  aWidth: number
  bWidth: number
  delta: number
  aPattern: string
  bPattern: string
}

export interface SnapshotItem {
  snapshot_id: string
  baseline?: boolean
  created_at?: string
  updated_at?: string
  [key: string]: unknown
}
