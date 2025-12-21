/**
 * Art Preview API Client - Bundle 31.0.5
 */

import { fetchJson } from "./http";
import type { RosettePreviewSvgRequest, RosettePreviewSvgResponse } from "../types/preview";

export const artPreviewClient = {
  previewSvg(req: RosettePreviewSvgRequest) {
    return fetchJson<RosettePreviewSvgResponse>(`/api/art/rosette/preview/svg`, {
      method: "POST",
      body: JSON.stringify(req),
    });
  },
};
