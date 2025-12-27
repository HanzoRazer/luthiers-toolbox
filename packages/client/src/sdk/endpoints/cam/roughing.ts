/**
 * CAM Roughing Endpoints (H8.3)
 *
 * Typed helpers for roughing G-code generation:
 * - POST /cam/roughing_gcode (legacy entity-based)
 * - POST /cam/roughing_gcode_intent (intent-native)
 *
 * Both return { gcode, summary, requestId }
 * Summary is parsed from X-CAM-Summary header.
 */

import { postRaw } from "@/sdk/core/apiFetchRaw";
import type {
  RoughingGcodeRequest,
  RoughingGcodeResult,
  CamSummary,
} from "./types";

/**
 * Parse X-CAM-Summary header into typed summary object.
 */
function parseCamSummary(response: Response): CamSummary | null {
  const hdr = response.headers.get("X-CAM-Summary");
  if (!hdr) return null;

  try {
    return JSON.parse(hdr) as CamSummary;
  } catch {
    console.warn("[CAM] Failed to parse X-CAM-Summary header:", hdr);
    return null;
  }
}

/**
 * POST /cam/roughing_gcode
 *
 * Legacy entity-based roughing G-code generation.
 * Returns gcode text + optional summary from X-CAM-Summary header.
 *
 * @throws ApiError with request-id on failure
 */
export async function roughingGcode(
  payload: RoughingGcodeRequest
): Promise<RoughingGcodeResult> {
  const { data, response } = await postRaw<string>(
    "/cam/roughing_gcode",
    payload
  );

  const requestId = response.headers.get("x-request-id") || undefined;
  const summary = parseCamSummary(response);

  return {
    gcode: data,
    summary,
    requestId,
  };
}

/**
 * POST /cam/roughing_gcode_intent
 *
 * Intent-native roughing G-code generation.
 * Accepts CamIntentV1 envelope with design/machine/tool intent.
 * Returns same shape as legacy endpoint (text + X-CAM-Summary).
 *
 * @param intent - CamIntentV1 typed envelope
 * @param strict - If true, appends ?strict=true query param (422 on issues)
 * @throws ApiError with request-id on failure
 */
export async function roughingGcodeIntent<TIntent extends Record<string, unknown>>(
  intent: TIntent,
  strict = false
): Promise<RoughingGcodeResult> {
  const path = strict
    ? "/cam/roughing_gcode_intent?strict=true"
    : "/cam/roughing_gcode_intent";

  const { data, response } = await postRaw<string>(path, intent);

  const requestId = response.headers.get("x-request-id") || undefined;
  const summary = parseCamSummary(response);

  return {
    gcode: data,
    summary,
    requestId,
  };
}
