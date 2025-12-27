/**
 * Art Studio Snapshots Client
 *
 * Type-safe client for /api/art/snapshots and /api/art/rosette/snapshots endpoints.
 */

import { get, post, put, del } from "../core/apiFetch";
import type { ApiFetchOptions, Timestamped } from "../core/types";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

/** Design snapshot metadata */
export type DesignSnapshot = Timestamped & {
  snapshot_id: string;
  name?: string;
  description?: string;
  generator_key?: string;
  pattern_id?: string;
  tags?: string[];
  meta?: Record<string, unknown>;
};

/** Full snapshot with data */
export type DesignSnapshotFull = DesignSnapshot & {
  data: Record<string, unknown>;
};

/** Rosette-specific snapshot */
export type RosetteSnapshot = DesignSnapshot & {
  rosette_type?: string;
  ring_count?: number;
  preview_svg?: string;
};

// ---------------------------------------------------------------------------
// API Functions - Generic Snapshots
// ---------------------------------------------------------------------------

/**
 * List recent design snapshots.
 */
export async function listSnapshots(
  params: { limit?: number } = {},
  opts?: ApiFetchOptions
): Promise<{ items: DesignSnapshot[] }> {
  const qs = params.limit ? `?limit=${params.limit}` : "";
  return get<{ items: DesignSnapshot[] }>(`/art/snapshots/recent${qs}`, opts);
}

/**
 * Get a single snapshot by ID.
 */
export async function getSnapshot(
  snapshotId: string,
  opts?: ApiFetchOptions
): Promise<DesignSnapshotFull> {
  return get<DesignSnapshotFull>(
    `/art/snapshots/${encodeURIComponent(snapshotId)}`,
    opts
  );
}

/**
 * Update a snapshot.
 */
export async function updateSnapshot(
  snapshotId: string,
  update: Partial<Pick<DesignSnapshot, "name" | "description" | "tags" | "meta">>,
  opts?: ApiFetchOptions
): Promise<DesignSnapshot> {
  return put<DesignSnapshot>(
    `/art/snapshots/${encodeURIComponent(snapshotId)}`,
    update,
    opts
  );
}

/**
 * Delete a snapshot.
 */
export async function deleteSnapshot(
  snapshotId: string,
  opts?: ApiFetchOptions
): Promise<{ deleted: boolean }> {
  return del<{ deleted: boolean }>(
    `/art/snapshots/${encodeURIComponent(snapshotId)}`,
    opts
  );
}

/**
 * Export a snapshot.
 */
export async function exportSnapshot(
  snapshotId: string,
  opts?: ApiFetchOptions
): Promise<Record<string, unknown>> {
  return get<Record<string, unknown>>(
    `/art/snapshots/${encodeURIComponent(snapshotId)}/export`,
    opts
  );
}

/**
 * Get snapshot export download URL.
 */
export function getSnapshotExportUrl(
  snapshotId: string,
  baseUrl = "/api"
): string {
  return `${baseUrl}/art/snapshots/${encodeURIComponent(snapshotId)}/export/download`;
}

/**
 * Import a snapshot from exported data.
 */
export async function importSnapshot(
  data: Record<string, unknown>,
  opts?: ApiFetchOptions
): Promise<DesignSnapshot> {
  return post<DesignSnapshot>("/art/snapshots/import", data, opts);
}

// ---------------------------------------------------------------------------
// API Functions - Rosette Snapshots
// ---------------------------------------------------------------------------

/**
 * List recent rosette snapshots.
 */
export async function listRosetteSnapshots(
  params: { limit?: number } = {},
  opts?: ApiFetchOptions
): Promise<{ items: RosetteSnapshot[] }> {
  const qs = params.limit ? `?limit=${params.limit}` : "";
  return get<{ items: RosetteSnapshot[] }>(`/art/rosette/snapshots/recent${qs}`, opts);
}

/**
 * Get a single rosette snapshot by ID.
 */
export async function getRosetteSnapshot(
  snapshotId: string,
  opts?: ApiFetchOptions
): Promise<RosetteSnapshot> {
  return get<RosetteSnapshot>(
    `/art/rosette/snapshots/${encodeURIComponent(snapshotId)}`,
    opts
  );
}

/**
 * Update a rosette snapshot.
 */
export async function updateRosetteSnapshot(
  snapshotId: string,
  update: Partial<Pick<RosetteSnapshot, "name" | "description" | "tags" | "meta">>,
  opts?: ApiFetchOptions
): Promise<RosetteSnapshot> {
  return put<RosetteSnapshot>(
    `/art/rosette/snapshots/${encodeURIComponent(snapshotId)}`,
    update,
    opts
  );
}

/**
 * Delete a rosette snapshot.
 */
export async function deleteRosetteSnapshot(
  snapshotId: string,
  opts?: ApiFetchOptions
): Promise<{ deleted: boolean }> {
  return del<{ deleted: boolean }>(
    `/art/rosette/snapshots/${encodeURIComponent(snapshotId)}`,
    opts
  );
}

/**
 * Export a rosette snapshot.
 */
export async function exportRosetteSnapshot(
  snapshotId: string,
  opts?: ApiFetchOptions
): Promise<Record<string, unknown>> {
  return get<Record<string, unknown>>(
    `/art/rosette/snapshots/${encodeURIComponent(snapshotId)}/export`,
    opts
  );
}

/**
 * Import a rosette snapshot.
 */
export async function importRosetteSnapshot(
  data: Record<string, unknown>,
  opts?: ApiFetchOptions
): Promise<RosetteSnapshot> {
  return post<RosetteSnapshot>("/art/rosette/snapshots/import", data, opts);
}
