/**
 * Art Feasibility API Client - Bundle 31.0.6
 */

import { fetchJson } from "./http";
import type {
  RosetteFeasibilityBatchRequest,
  RosetteFeasibilityBatchResponse,
} from "../types/feasibility";

export const artFeasibilityClient = {
  batch(req: RosetteFeasibilityBatchRequest) {
    return fetchJson<RosetteFeasibilityBatchResponse>(`/api/art/rosette/feasibility/batch`, {
      method: "POST",
      body: JSON.stringify(req),
    });
  },
};
