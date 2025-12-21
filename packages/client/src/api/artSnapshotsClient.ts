/**
 * Art Snapshots API Client - Bundle 31.0.5
 */

import { fetchJson } from "./http";
import type {
  DesignSnapshot,
  SnapshotCreateRequest,
  SnapshotExportResponse,
  SnapshotImportRequest,
  SnapshotListResponse,
  SnapshotUpdateRequest,
} from "../types/designSnapshot";

export const artSnapshotsClient = {
  create(req: SnapshotCreateRequest) {
    return fetchJson<DesignSnapshot>(`/api/art/snapshots`, {
      method: "POST",
      body: JSON.stringify(req),
    });
  },

  listRecent(params?: { q?: string; tag?: string; pattern_id?: string; limit?: number }) {
    const qs = new URLSearchParams();
    if (params?.q) qs.set("q", params.q);
    if (params?.tag) qs.set("tag", params.tag);
    if (params?.pattern_id) qs.set("pattern_id", params.pattern_id);
    if (params?.limit) qs.set("limit", String(params.limit));
    const url = `/api/art/snapshots/recent${qs.toString() ? `?${qs.toString()}` : ""}`;
    return fetchJson<SnapshotListResponse>(url);
  },

  get(snapshot_id: string) {
    return fetchJson<DesignSnapshot>(`/api/art/snapshots/${encodeURIComponent(snapshot_id)}`);
  },

  update(snapshot_id: string, req: SnapshotUpdateRequest) {
    return fetchJson<DesignSnapshot>(`/api/art/snapshots/${encodeURIComponent(snapshot_id)}`, {
      method: "PUT",
      body: JSON.stringify(req),
    });
  },

  delete(snapshot_id: string) {
    return fetchJson<{ ok: boolean; snapshot_id: string }>(
      `/api/art/snapshots/${encodeURIComponent(snapshot_id)}`,
      { method: "DELETE" }
    );
  },

  export(snapshot_id: string) {
    return fetchJson<SnapshotExportResponse>(
      `/api/art/snapshots/${encodeURIComponent(snapshot_id)}/export`
    );
  },

  exportDownloadUrl(snapshot_id: string) {
    return `/api/art/snapshots/${encodeURIComponent(snapshot_id)}/export/download`;
  },

  import(req: SnapshotImportRequest) {
    return fetchJson<DesignSnapshot>(`/api/art/snapshots/import`, {
      method: "POST",
      body: JSON.stringify(req),
    });
  },
};
