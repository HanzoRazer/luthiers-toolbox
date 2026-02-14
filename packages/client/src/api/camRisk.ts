// client/src/api/camRisk.ts
/**
 * CAM Risk Analytics API Client - Phase 18.0
 * 
 * Client for job risk reporting and timeline browsing.
 */

export interface RiskIssue {
  index: number
  type: string
  severity: string
  x: number
  y: number
  z?: number | null
  extra_time_s?: number | null
  note?: string | null
  meta?: Record<string, any>
}

export interface RiskAnalytics {
  total_issues: number
  severity_counts: Record<string, number>
  risk_score: number
  total_extra_time_s: number
  total_extra_time_human: string
}

export interface RiskReportIn {
  job_id: string
  pipeline_id?: string | null
  op_id?: string | null
  machine_profile_id?: string | null
  post_preset?: string | null
  design_source?: string | null
  design_path?: string | null
  issues: RiskIssue[]
  analytics: RiskAnalytics
}

export interface RiskReportOut {
  id: string
  created_at: string
  job_id: string
  pipeline_id?: string | null
  op_id?: string | null
  machine_profile_id?: string | null
  post_preset?: string | null
  design_source?: string | null
  design_path?: string | null
  issues: RiskIssue[]
  analytics: RiskAnalytics
  meta?: Record<string, any>
}

// Alias for full stored reports (Phase 19.0)
export type RiskReportStored = RiskReportOut

export interface RiskReportSummary {
  id: string
  created_at: string
  job_id: string
  pipeline_id?: string | null
  op_id?: string | null
  machine_profile_id?: string | null
  post_preset?: string | null
  total_issues: number
  critical_count: number
  high_count: number
  medium_count: number
  low_count: number
  info_count: number
  risk_score: number
  total_extra_time_s: number
}

export interface CamRiskTimelineReport {
  id: string
  created_at: number
  lane: string
  job_id?: string | null
  preset?: string | null
  source?: string | null
  summary: Record<string, any>
}

export interface CamRiskTimelineQuery {
  lane?: string | null
  preset?: string | null
  limit?: number
  startTs?: number | null
  endTs?: number | null
}

/**
 * Submit a new CAM risk report.
 * Called after simulation to log risk analytics.
 */
export async function postRiskReport(report: RiskReportIn): Promise<RiskReportOut> {
  const response = await fetch('/api/cam/jobs/risk_report', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(report)
  })

  if (!response.ok) {
    const text = await response.text()
    throw new Error(text || `HTTP ${response.status}`)
  }

  return response.json()
}

/**
 * Get risk timeline for a specific job.
 * Returns all risk reports for the given job_id.
 */
export async function getJobRiskTimeline(
  jobId: string,
  limit: number = 50
): Promise<RiskReportOut[]> {
  const response = await fetch(`/api/cam/jobs/${jobId}/risk_timeline?limit=${limit}`)

  if (!response.ok) {
    const text = await response.text()
    throw new Error(text || `HTTP ${response.status}`)
  }

  return response.json()
}

/**
 * Get recent risk reports across all jobs.
 * Returns lightweight summaries for timeline browsing.
 */
export async function getRecentRiskReports(
  limit: number = 100
): Promise<RiskReportSummary[]> {
  const response = await fetch(`/api/cam/jobs/recent?limit=${limit}`)

  if (!response.ok) {
    const text = await response.text()
    throw new Error(text || `HTTP ${response.status}`)
  }

  return response.json()
}

export async function fetchCamRiskTimelineReports(
  query: CamRiskTimelineQuery = {},
): Promise<CamRiskTimelineReport[]> {
  const params = new URLSearchParams()
  if (query.lane) params.set('lane', query.lane)
  if (query.preset) params.set('preset', query.preset)
  if (query.limit) params.set('limit', String(query.limit))
  if (typeof query.startTs === 'number') params.set('start_ts', String(query.startTs))
  if (typeof query.endTs === 'number') params.set('end_ts', String(query.endTs))

  const qs = params.toString()
  const url = qs ? `/api/cam/risk/reports?${qs}` : '/api/cam/risk/reports'
  const response = await fetch(url)

  if (!response.ok) {
    const text = await response.text()
    throw new Error(text || `HTTP ${response.status}`)
  }

  return response.json()
}

// Legacy stubs for backward compatibility
export function buildRiskReportPayload(data: any): any {
  console.warn('buildRiskReportPayload: Legacy stub, use RiskReportIn interface directly')
  return data
}

export async function patchRiskNotes(_id: string, _notes: string): Promise<any> {
  console.warn('patchRiskNotes: Not implemented in Phase 18.0')
  return { success: false, message: 'Not implemented' }
}

export async function attachRiskBackplot(_id: string, _backplot: any): Promise<any> {
  console.warn('attachRiskBackplot: Not implemented in Phase 18.0')
  return { success: false, message: 'Not implemented' }
}

export interface RiskBackplotMoveOut {
  x?: number
  y?: number
  z?: number
  type?: string
}
