/**
 * Saw Lab API Client
 * 
 * TypeScript client for CP-S59, CP-S60, CP-S61/62 backend APIs:
 * - JobLog & Telemetry (CP-S59)
 * - Live Learn Ingestor (CP-S60)
 * - Dashboard & Risk Actions (CP-S61/62)
 */

import axios from 'axios'

const API_BASE = '/api'

// ============================================================================
// TYPES - Risk & Dashboard (CP-S61/62)
// ============================================================================

export type RiskBucketId = 'unknown' | 'green' | 'yellow' | 'orange' | 'red'

export interface RiskBucketInfo {
  id: RiskBucketId
  label: string
  description: string
}

export interface MetricsSummary {
  n_samples: number
  avg_rpm?: number
  avg_feed_mm_min?: number
  avg_spindle_load_pct?: number
  max_spindle_load_pct?: number
  avg_vibration_rms?: number
  max_vibration_rms?: number
}

export interface LaneScaleHistoryPoint {
  ts: string
  lane_scale: number
  source?: string
}

export interface RunSummaryItem {
  run_id: string
  created_at: string
  
  // Metadata
  op_type: string
  machine_profile: string
  material_family: string
  blade_id?: string
  
  // Status
  status: string
  started_at?: string
  completed_at?: string
  
  // Metrics
  has_telemetry: boolean
  metrics?: MetricsSummary
  
  // Risk
  risk_score: number
  risk_bucket: RiskBucketInfo
  
  // History
  lane_scale_history: LaneScaleHistoryPoint[]
}

export interface DashboardSummary {
  total_runs: number
  returned_runs: number
  runs: RunSummaryItem[]
}

// ============================================================================
// TYPES - JobLog & Telemetry (CP-S59)
// ============================================================================

export interface SawRunMeta {
  op_type: string
  machine_profile: string
  material_family: string
  blade_id?: string
  safe_z_mm: number
  depth_passes: number
  total_length_mm: number
}

export interface SawRunRecord {
  run_id: string
  status: string
  created_at: string
  started_at?: string
  completed_at?: string
  error_message?: string
  meta: SawRunMeta
  gcode: string
}

export interface TelemetrySample {
  timestamp: string
  x_mm?: number
  y_mm?: number
  z_mm?: number
  rpm_actual?: number
  feed_actual_mm_min?: number
  spindle_load_percent?: number
  motor_current_amps?: number
  temp_c?: number
  vibration_mg?: number
  in_cut: boolean
}

export interface SawTelemetryRecord {
  run_id: string
  samples: TelemetrySample[]
}

// ============================================================================
// TYPES - Live Learn (CP-S60)
// ============================================================================

export interface TelemetryIngestRequest {
  run_id: string
  tool_id: string
  material: string
  mode: string
  machine_profile: string
  current_lane_scale?: number
  apply?: boolean
}

export interface LaneAdjustment {
  tool_id: string
  material: string
  mode: string
  machine_profile: string
  metrics: MetricsSummary
  risk_score: number
  recommended_scale_delta: number
  new_lane_scale?: number
  applied: boolean
  reason: string
}

export interface TelemetryIngestResponse {
  run_id: string
  metrics: MetricsSummary
  adjustment: LaneAdjustment
}

// ============================================================================
// API METHODS - Dashboard (CP-S61/62)
// ============================================================================

/**
 * Get recent CNC runs with risk classifications and metrics.
 * 
 * Returns dashboard summary with runs sorted by creation time (newest first).
 * Each run includes:
 * - Metadata (op_type, machine, material)
 * - Telemetry metrics (load, rpm, vibration)
 * - Risk score (0-1) and color-coded bucket
 * 
 * @param limit Maximum number of runs to return (1-500, default: 50)
 */
export async function getDashboardRuns(limit: number = 50): Promise<DashboardSummary> {
  const response = await axios.get<DashboardSummary>(
    `${API_BASE}/dashboard/saw/runs`,
    { params: { limit } }
  )
  return response.data
}

/**
 * Dashboard health check.
 */
export async function getDashboardHealth(): Promise<{ status: string; module: string; features: string[] }> {
  const response = await axios.get(`${API_BASE}/dashboard/saw/health`)
  return response.data
}

// ============================================================================
// API METHODS - JobLog & Telemetry (CP-S59)
// ============================================================================

/**
 * Create new job run entry.
 * 
 * @param meta Job metadata (op_type, machine, material, etc.)
 * @param gcode Generated G-code program
 */
export async function createSawRun(meta: SawRunMeta, gcode: string): Promise<SawRunRecord> {
  const response = await axios.post<SawRunRecord>(
    `${API_BASE}/joblog/saw_runs`,
    { ...meta, gcode }
  )
  return response.data
}

/**
 * List recent job runs with optional filtering.
 * 
 * @param limit Maximum number of runs to return
 * @param op_type Optional filter by operation type
 * @param machine_profile Optional filter by machine
 */
export async function listSawRuns(
  limit: number = 50,
  op_type?: string,
  machine_profile?: string
): Promise<SawRunRecord[]> {
  const response = await axios.get<SawRunRecord[]>(
    `${API_BASE}/joblog/saw_runs`,
    { params: { limit, op_type, machine_profile } }
  )
  return response.data
}

/**
 * Get specific job run by ID.
 * 
 * @param run_id Unique run identifier
 */
export async function getSawRun(run_id: string): Promise<SawRunRecord> {
  const response = await axios.get<SawRunRecord>(
    `${API_BASE}/joblog/saw_runs/${run_id}`
  )
  return response.data
}

/**
 * Update job run status.
 * 
 * @param run_id Unique run identifier
 * @param status New status (pending/running/completed/error)
 * @param started_at Optional execution start time
 * @param completed_at Optional execution end time
 * @param error_message Optional error description
 */
export async function updateSawRunStatus(
  run_id: string,
  status: string,
  started_at?: string,
  completed_at?: string,
  error_message?: string
): Promise<SawRunRecord> {
  const response = await axios.put<SawRunRecord>(
    `${API_BASE}/joblog/saw_runs/${run_id}/status`,
    { status, started_at, completed_at, error_message }
  )
  return response.data
}

/**
 * Add telemetry sample to run.
 * 
 * @param run_id Unique run identifier
 * @param sample Telemetry sample (position, feeds, loads, temps)
 */
export async function addTelemetrySample(
  run_id: string,
  sample: TelemetrySample
): Promise<SawTelemetryRecord> {
  const response = await axios.post<SawTelemetryRecord>(
    `${API_BASE}/joblog/saw_runs/${run_id}/telemetry`,
    sample
  )
  return response.data
}

/**
 * Get telemetry data for run.
 * 
 * @param run_id Unique run identifier
 * @param compute_stats Whether to compute summary statistics
 */
export async function getRunTelemetry(
  run_id: string,
  compute_stats: boolean = false
): Promise<SawTelemetryRecord> {
  const response = await axios.get<SawTelemetryRecord>(
    `${API_BASE}/joblog/saw_runs/${run_id}/telemetry`,
    { params: { compute_stats } }
  )
  return response.data
}

// ============================================================================
// API METHODS - Live Learn (CP-S60)
// ============================================================================

/**
 * Ingest telemetry and compute lane-scale adjustments.
 * 
 * Analyzes run telemetry and recommends feed/speed adjustments:
 * - High load (>80%) → slow down (-5%)
 * - Low load (<40%) → speed up (+5%)
 * - Neutral (40-80%) → no change
 * 
 * @param request Ingest request with run context and optional apply flag
 */
export async function ingestTelemetry(request: TelemetryIngestRequest): Promise<TelemetryIngestResponse> {
  const response = await axios.post<TelemetryIngestResponse>(
    `${API_BASE}/learn/ingest`,
    request
  )
  return response.data
}

/**
 * Live Learn health check.
 */
export async function getLearnHealth(): Promise<{ status: string; module: string; features: string[] }> {
  const response = await axios.get(`${API_BASE}/learn/health`)
  return response.data
}
