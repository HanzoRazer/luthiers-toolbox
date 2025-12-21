/**
 * Art Patterns API Client - Bundle 31.0.5
 */

import { fetchJson } from "./http";
import type {
  PatternCreateRequest,
  PatternListResponse,
  PatternRecord,
  PatternUpdateRequest,
} from "../types/patternLibrary";

export const artPatternsClient = {
  list(params?: { q?: string; tag?: string; generator_key?: string; limit?: number }) {
    const qs = new URLSearchParams();
    if (params?.q) qs.set("q", params.q);
    if (params?.tag) qs.set("tag", params.tag);
    if (params?.generator_key) qs.set("generator_key", params.generator_key);
    if (params?.limit) qs.set("limit", String(params.limit));
    const url = `/api/art/patterns${qs.toString() ? `?${qs.toString()}` : ""}`;
    return fetchJson<PatternListResponse>(url);
  },

  create(req: PatternCreateRequest) {
    return fetchJson<PatternRecord>(`/api/art/patterns`, {
      method: "POST",
      body: JSON.stringify(req),
    });
  },

  get(pattern_id: string) {
    return fetchJson<PatternRecord>(`/api/art/patterns/${encodeURIComponent(pattern_id)}`);
  },

  update(pattern_id: string, req: PatternUpdateRequest) {
    return fetchJson<PatternRecord>(`/api/art/patterns/${encodeURIComponent(pattern_id)}`, {
      method: "PUT",
      body: JSON.stringify(req),
    });
  },

  delete(pattern_id: string) {
    return fetchJson<{ ok: boolean; pattern_id: string }>(
      `/api/art/patterns/${encodeURIComponent(pattern_id)}`,
      { method: "DELETE" }
    );
  },
};
