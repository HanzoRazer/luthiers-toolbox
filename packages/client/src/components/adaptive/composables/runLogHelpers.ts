/**
 * Shared run-logging utilities for the adaptive CAM domain.
 *
 * Extracted from useLiveLearning.ts and useRunLogging.ts which had
 * identical segment-serialization and run-body construction code.
 */
import type { Move } from './useToolpathRenderer'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface RunSegment {
  idx: number
  code: string
  x: number | undefined
  y: number | undefined
  len_mm: number
  limit: string | null
  slowdown: number | null
  trochoid: boolean
  radius_mm: number | null
  feed_f: number | null
}

export interface RunLogBody {
  job_name: string
  machine_id: string
  material_id: string
  tool_d: number
  stepover: number
  stepdown: number
  post_id: string | null
  feed_xy: number | undefined
  rpm: number | undefined
  est_time_s: number | null
  act_time_s: number | null
  notes: string | null
}

export interface RunLogParams {
  profileId: string
  materialId: string
  toolD: number
  stepoverPct: number
  stepdown: number
  feedXY: number
  estTimeJerk?: number | null
  estTimeClassic?: number | null
  actualSeconds?: number | null
}

// ---------------------------------------------------------------------------
// Functions
// ---------------------------------------------------------------------------

/**
 * Serialize toolpath moves into the segment format expected by the
 * `/api/cam/logs/write` endpoint.
 */
export function serializeMovesToSegments(moves: Move[]): RunSegment[] {
  return moves.map((m, i) => ({
    idx: i,
    code: m.code,
    x: m.x,
    y: m.y,
    len_mm: m._len_mm || 0,
    limit: m.meta?.limit || null,
    slowdown: m.meta?.slowdown ?? null,
    trochoid: !!m.meta?.trochoid,
    radius_mm: m.meta?.radius_mm ?? null,
    feed_f: m.f ?? null,
  }))
}

/**
 * Build the run body payload for `/api/cam/logs/write`.
 */
export function buildRunLogBody(params: RunLogParams): RunLogBody {
  return {
    job_name: 'pocket',
    machine_id: params.profileId || 'Mach4_Router_4x8',
    material_id: params.materialId || 'maple_hard',
    tool_d: params.toolD,
    stepover: params.stepoverPct / 100,
    stepdown: params.stepdown,
    post_id: null,
    feed_xy: params.feedXY || undefined,
    rpm: undefined,
    est_time_s: params.estTimeJerk ?? params.estTimeClassic ?? null,
    act_time_s: params.actualSeconds ?? null,
    notes: null,
  }
}
