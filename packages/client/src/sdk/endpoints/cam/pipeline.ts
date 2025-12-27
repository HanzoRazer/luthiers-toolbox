/**
 * CAM Pipeline Endpoints (H8.3)
 *
 * Typed helper for CAM pipeline runner FormData submission surface.
 * - POST /cam/pipeline/run
 */

import { postFormRaw } from "@/sdk/core/apiFetchRaw";
import type { PipelineRunResult } from "./types";

/**
 * POST /cam/pipeline/run
 *
 * Execute CAM pipeline with FormData payload (file uploads + config).
 * Returns JSON result + request-id for correlation.
 *
 * @param form - FormData with pipeline config and optional file uploads
 * @throws ApiError with request-id on failure
 */
export async function runPipeline(form: FormData): Promise<PipelineRunResult> {
  const { data, response } = await postFormRaw<unknown>(
    "/cam/pipeline/run",
    form
  );

  const requestId = response.headers.get("x-request-id") || undefined;

  return {
    result: data,
    requestId,
  };
}
