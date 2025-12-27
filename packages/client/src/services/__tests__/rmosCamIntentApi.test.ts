/* eslint-disable @typescript-eslint/no-explicit-any */

import { describe, it, expect, afterEach } from "vitest";
import { normalizeCamIntent, RmosApiError } from "../rmosCamIntentApi";

describe("normalizeCamIntent()", () => {
  const realFetch = globalThis.fetch;

  afterEach(() => {
    globalThis.fetch = realFetch;
  });

  it("returns {intent, issues} on 200", async () => {
    globalThis.fetch = (async () =>
      new Response(
        JSON.stringify({
          intent: { mode: "saw", units: "mm", created_at_utc: "2025-12-26T00:00:00Z" },
          issues: [{ code: "I001", message: "ok", severity: "INFO" }],
          normalized_at_utc: "2025-12-26T00:00:00Z",
        }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      )) as any;

    const out = await normalizeCamIntent(
      {
        intent: { mode: "saw", units: "mm", design: {} },
        strict: false,
      },
      { apiBaseUrl: "http://localhost:8000/api", requestId: "test-req-1" }
    );

    expect(out.intent.mode).toBe("saw");
    expect(Array.isArray(out.issues)).toBe(true);
    expect(out.issues[0].code).toBe("I001");
  });

  it("throws RmosApiError on 422", async () => {
    globalThis.fetch = (async () =>
      new Response(
        JSON.stringify({
          detail: {
            message: "invalid_intent",
            issues: [{ code: "E001", message: "bad", severity: "ERROR" }],
          },
        }),
        { status: 422, headers: { "Content-Type": "application/json" } }
      )) as any;

    await expect(
      normalizeCamIntent(
        { intent: { mode: "saw", units: "mm", design: {} }, strict: true },
        { apiBaseUrl: "http://localhost:8000/api" }
      )
    ).rejects.toBeInstanceOf(RmosApiError);
  });

  it("throws RmosApiError on 500", async () => {
    globalThis.fetch = (async () =>
      new Response(
        JSON.stringify({
          detail: { message: "internal_error" },
        }),
        { status: 500, headers: { "Content-Type": "application/json" } }
      )) as any;

    await expect(
      normalizeCamIntent(
        { intent: { mode: "router_3axis", units: "mm", design: {} } },
        { apiBaseUrl: "http://localhost:8000/api" }
      )
    ).rejects.toBeInstanceOf(RmosApiError);
  });

  it("uses default normalize_to_units and strict values", async () => {
    let capturedBody: any = null;

    globalThis.fetch = (async (_url: string, init: RequestInit) => {
      capturedBody = JSON.parse(init.body as string);
      return new Response(
        JSON.stringify({
          intent: { mode: "saw", units: "mm" },
          issues: [],
          normalized_at_utc: "2025-12-26T00:00:00Z",
        }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      );
    }) as any;

    await normalizeCamIntent(
      { intent: { mode: "saw" } },
      { apiBaseUrl: "http://localhost:8000/api" }
    );

    expect(capturedBody.normalize_to_units).toBe("mm");
    expect(capturedBody.strict).toBe(false);
  });

  it("passes X-Request-Id header when provided", async () => {
    let capturedHeaders: Record<string, string> = {};

    globalThis.fetch = (async (_url: string, init: RequestInit) => {
      capturedHeaders = Object.fromEntries(
        Object.entries(init.headers as Record<string, string>)
      );
      return new Response(
        JSON.stringify({
          intent: { mode: "saw", units: "mm" },
          issues: [],
          normalized_at_utc: "2025-12-26T00:00:00Z",
        }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      );
    }) as any;

    await normalizeCamIntent(
      { intent: { mode: "saw" } },
      { apiBaseUrl: "http://localhost:8000/api", requestId: "custom-req-id" }
    );

    expect(capturedHeaders["X-Request-Id"]).toBe("custom-req-id");
  });
});
