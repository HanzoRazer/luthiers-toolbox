/**
 * Art Generators API Client - Bundle 31.0.5
 */

import { fetchJson } from "./http";
import type {
  GeneratorGenerateRequest,
  GeneratorGenerateResponse,
  GeneratorListResponse,
} from "../types/generators";

export const artGeneratorsClient = {
  list() {
    return fetchJson<GeneratorListResponse>(`/api/art/generators`);
  },

  generate(generator_key: string, req: GeneratorGenerateRequest) {
    return fetchJson<GeneratorGenerateResponse>(
      `/api/art/generators/${encodeURIComponent(generator_key)}/generate`,
      { method: "POST", body: JSON.stringify(req) }
    );
  },
};
