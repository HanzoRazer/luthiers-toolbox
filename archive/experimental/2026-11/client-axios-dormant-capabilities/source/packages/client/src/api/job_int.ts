// File: client/src/api/job_int.ts
// NEW – Job Intelligence API client for pipeline run history

import axios from 'axios';

/**
 * Lightweight job log entry for listing.
 */
export interface JobIntLogEntry {
  run_id: string;
  job_name: string | null;
  machine_id: string | null;
  post_id: string | null;
  gcode_key: string | null;
  use_helical: boolean;
  favorite?: boolean;

  sim_time_s: number | null;
  sim_energy_j: number | null;
  sim_move_count: number | null;

  sim_issue_count: number | null;
  sim_max_dev_pct: number | null;

  created_at: string;
  source: string;
}

/**
 * Detailed job log entry with full simulation data.
 */
export interface JobIntLogEntryDetail extends JobIntLogEntry {
  sim_stats: Record<string, any>;
  sim_issues: Record<string, any>;
}

/**
 * Query parameters for fetching job logs.
 */
export interface JobIntLogQuery {
  machine_id?: string;
  post_id?: string;
  helical_only?: boolean;
  favorites_only?: boolean;
  limit?: number;
  offset?: number;
}

/**
 * Response from list endpoint with pagination.
 */
export interface JobIntLogListResponse {
  total: number;
  items: JobIntLogEntry[];
}

/**
 * Fetch paginated job intelligence log with filtering.
 */
export async function fetchJobIntLog(
  params: JobIntLogQuery = {}
): Promise<JobIntLogListResponse> {
  const res = await axios.get<JobIntLogListResponse>('/api/cam/job-int/log', {
    params,
  });
  return res.data;
}

/**
 * Get detailed job log entry by run_id.
 */
export async function getJobIntLogEntry(
  runId: string
): Promise<JobIntLogEntryDetail> {
  const res = await axios.get<JobIntLogEntryDetail>(
    `/api/cam/job-int/log/${encodeURIComponent(runId)}`
  );
  return res.data;
}

/**
 * Toggle favorite flag for a job run.
 */
export async function updateJobIntFavorite(
  runId: string,
  favorite: boolean
): Promise<JobIntLogEntryDetail> {
  const res = await axios.post<JobIntLogEntryDetail>(
    `/api/cam/job-int/favorites/${encodeURIComponent(runId)}`,
    { favorite }
  );
  return res.data;
}
