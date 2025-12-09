// packages/client/src/api/curvelab.ts
// REST helpers for CurveLab DXF preflight + auto-fix endpoints

import type {
  AutoFixRequest,
  AutoFixResponse,
  CurvePreflightRequest,
  CurvePreflightResponse,
  ValidationReport,
} from "@/types/curvelab";

const JSON_HEADERS = { "Content-Type": "application/json" } as const;

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `CurveLab request failed (${res.status})`);
  }
  return (await res.json()) as T;
}

export async function fetchCurveReport(
  payload: CurvePreflightRequest,
): Promise<CurvePreflightResponse> {
  const res = await fetch("/api/dxf/preflight/curve_report", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify(payload),
  });
  return handleResponse<CurvePreflightResponse>(res);
}

export async function autoFixDxf(
  payload: AutoFixRequest,
): Promise<AutoFixResponse> {
  const res = await fetch("/api/dxf/preflight/auto_fix", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify(payload),
  });
  return handleResponse<AutoFixResponse>(res);
}

export async function validateDxf(
  dxfBase64: string,
  filename: string,
): Promise<ValidationReport> {
  const res = await fetch("/api/dxf/preflight/validate_base64", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({ dxf_base64: dxfBase64, filename }),
  });
  return handleResponse<ValidationReport>(res);
}
