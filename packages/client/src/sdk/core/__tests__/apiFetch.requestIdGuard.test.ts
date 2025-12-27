/**
 * apiFetch Request-ID Guard Integration Tests
 *
 * These tests prove that the X-Request-Id enforcement is wired into apiFetch.
 * If someone removes the assertRequestIdHeader call during refactoring,
 * these tests will fail.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

// We need to mock fetch before importing apiFetch
const originalFetch = globalThis.fetch;

function mockFetchWithHeaders(
  headers: Record<string, string>,
  body: unknown = {}
) {
  return vi.fn(async () =>
    new Response(JSON.stringify(body), {
      status: 200,
      headers: { "Content-Type": "application/json", ...headers },
    })
  );
}

describe("apiFetch request-id guard integration", () => {
  beforeEach(() => {
    vi.resetModules();
    vi.restoreAllMocks();
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  it("warns when response is missing X-Request-Id (default warn mode)", async () => {
    // Mock fetch without X-Request-Id header
    globalThis.fetch = mockFetchWithHeaders({});

    const warn = vi.spyOn(console, "warn").mockImplementation(() => {});

    // Import fresh to get clean module state
    const { apiFetch } = await import("../apiFetch");

    // Should not throw in default warn mode
    await expect(
      apiFetch("/rmos/health", { method: "GET" })
    ).resolves.toBeDefined();

    // But should warn
    expect(warn).toHaveBeenCalledWith(
      expect.stringContaining("Missing X-Request-Id"),
      expect.any(Object)
    );
  });

  it("does not warn when X-Request-Id exists", async () => {
    // Mock fetch WITH X-Request-Id header
    globalThis.fetch = mockFetchWithHeaders({ "X-Request-Id": "req_abc123" });

    const warn = vi.spyOn(console, "warn").mockImplementation(() => {});

    const { apiFetch } = await import("../apiFetch");

    await expect(
      apiFetch("/rmos/health", { method: "GET" })
    ).resolves.toBeDefined();

    // Should not warn when header exists
    expect(warn).not.toHaveBeenCalled();
  });

  it("sends X-Request-Id header in request", async () => {
    const fetchMock = mockFetchWithHeaders({ "X-Request-Id": "req_echo" });
    globalThis.fetch = fetchMock;

    const { apiFetch } = await import("../apiFetch");

    await apiFetch("/rmos/runs", { method: "GET" });

    // Verify the request included X-Request-Id
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(init.headers).toBeDefined();
    expect((init.headers as Record<string, string>)["X-Request-Id"]).toBeTruthy();
  });

  it("uses provided requestId when passed in options", async () => {
    const fetchMock = mockFetchWithHeaders({ "X-Request-Id": "req_custom" });
    globalThis.fetch = fetchMock;

    const { apiFetch } = await import("../apiFetch");

    await apiFetch("/rmos/runs", { method: "GET" }, { requestId: "my-custom-id" });

    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect((init.headers as Record<string, string>)["X-Request-Id"]).toBe(
      "my-custom-id"
    );
  });

  it("generates unique requestId for each call when not provided", async () => {
    const fetchMock = mockFetchWithHeaders({ "X-Request-Id": "req_echo" });
    globalThis.fetch = fetchMock;

    const { apiFetch } = await import("../apiFetch");

    await apiFetch("/rmos/runs", { method: "GET" });
    await apiFetch("/rmos/workflow/sessions", { method: "GET" });

    expect(fetchMock).toHaveBeenCalledTimes(2);

    const [, init1] = fetchMock.mock.calls[0] as [string, RequestInit];
    const [, init2] = fetchMock.mock.calls[1] as [string, RequestInit];

    const reqId1 = (init1.headers as Record<string, string>)["X-Request-Id"];
    const reqId2 = (init2.headers as Record<string, string>)["X-Request-Id"];

    expect(reqId1).toBeTruthy();
    expect(reqId2).toBeTruthy();
    expect(reqId1).not.toBe(reqId2);
  });
});

describe("apiFetch request-id guard strict mode", () => {
  const originalEnv = (import.meta as any).env;

  beforeEach(() => {
    vi.resetModules();
    vi.restoreAllMocks();
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
    (import.meta as any).env = originalEnv;
  });

  it("throws when VITE_REQUIRE_REQUEST_ID=true and header missing", async () => {
    // Mock environment for strict mode
    (import.meta as any).env = {
      ...originalEnv,
      VITE_REQUIRE_REQUEST_ID: "true",
    };

    // Mock fetch without X-Request-Id header
    globalThis.fetch = mockFetchWithHeaders({});

    // Re-import to pick up new env
    const { assertRequestIdHeader } = await import("../assertRequestId");

    // Create a response without the header
    const res = new Response("{}", { status: 200 });

    // Should throw in strict mode
    expect(() =>
      assertRequestIdHeader(res, { mode: "strict" })
    ).toThrow(/Missing X-Request-Id/);
  });
});
