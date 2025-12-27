import { describe, it, expect, vi, beforeEach } from "vitest";
import { assertRequestIdHeader } from "../assertRequestId";

function makeResponse(headers: Record<string, string>, status = 200) {
  return new Response("ok", { status, headers });
}

describe("assertRequestIdHeader", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("does nothing when X-Request-Id exists", () => {
    const res = makeResponse({ "X-Request-Id": "req_123" });
    expect(() => assertRequestIdHeader(res, { mode: "strict" })).not.toThrow();
  });

  it("throws in strict mode when missing X-Request-Id", () => {
    const res = makeResponse({});
    expect(() =>
      assertRequestIdHeader(res, {
        mode: "strict",
        endpoint: "/api/foo",
        method: "GET",
      })
    ).toThrow(/Missing X-Request-Id/);
  });

  it("includes context in strict mode error", () => {
    const res = makeResponse({});
    try {
      assertRequestIdHeader(res, {
        mode: "strict",
        endpoint: "/api/rmos/runs",
        method: "POST",
      });
      expect.fail("should have thrown");
    } catch (err) {
      expect((err as Error).message).toContain("/api/rmos/runs");
      expect((err as Error).message).toContain("POST");
    }
  });

  it("warns in warn mode when missing X-Request-Id", () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
    const res = makeResponse({});

    expect(() =>
      assertRequestIdHeader(res, {
        mode: "warn",
        endpoint: "/api/foo",
        method: "GET",
      })
    ).not.toThrow();

    expect(warn).toHaveBeenCalledTimes(1);
    expect(warn).toHaveBeenCalledWith(
      expect.stringContaining("Missing X-Request-Id"),
      expect.objectContaining({ endpoint: "/api/foo", method: "GET" })
    );
  });

  it("no-ops in off mode even when header missing", () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
    const res = makeResponse({});

    expect(() => assertRequestIdHeader(res, { mode: "off" })).not.toThrow();
    expect(warn).not.toHaveBeenCalled();
  });

  it("respects header regardless of response status", () => {
    // Even on 4xx/5xx responses, we should still check the header
    const res = makeResponse({ "X-Request-Id": "req_456" }, 500);
    expect(() => assertRequestIdHeader(res, { mode: "strict" })).not.toThrow();
  });
});
