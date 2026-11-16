/**
 * useAuthStore.signOut() — "Sign out" must sign THIS device out.
 *
 * supabase-js 2.119.0 (auth-js #2786) changed the default `global` scope:
 * when the server logout request fails (offline, 5xx) the local session is
 * now RETAINED, no SIGNED_OUT event fires, and `{ error }` is returned
 * instead of thrown. Before 2.119.0 the local session was removed anyway.
 *
 * These tests drive the REAL supabase-js client (only `fetch` and storage
 * are substituted), so they exercise the library behavior itself rather
 * than a mock of it. The assertion that matters is the persisted session:
 * `getAccessToken()` reads it and the SDK attaches it to every API call,
 * and `initialize()` restores the user from it on the next page load.
 */
import { describe, it, expect, beforeEach, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";

const h = vi.hoisted(() => {
  const store = new Map<string, string>();
  const state = {
    logoutMode: "ok" as "ok" | "offline" | "503",
    logoutScopes: [] as string[],
  };
  return { store, state };
});

vi.mock("@/auth/supabase", async () => {
  const { createClient } = await import("@supabase/supabase-js");
  const fetchImpl = async (input: RequestInfo | URL): Promise<Response> => {
    const url = new URL(typeof input === "string" ? input : input.toString());
    if (url.pathname.endsWith("/auth/v1/logout")) {
      h.state.logoutScopes.push(url.searchParams.get("scope") ?? "");
      if (h.state.logoutMode === "offline") throw new TypeError("Failed to fetch");
      if (h.state.logoutMode === "503") {
        return new Response(JSON.stringify({ message: "unavailable" }), {
          status: 503,
          headers: { "content-type": "application/json" },
        });
      }
      return new Response(null, { status: 204 });
    }
    throw new Error(`unexpected request in test: ${url}`);
  };
  const supabase = createClient("https://test.supabase.co", "test-anon-key", {
    auth: {
      autoRefreshToken: false,
      persistSession: true,
      detectSessionInUrl: false,
      storage: {
        getItem: (k: string) => h.store.get(k) ?? null,
        setItem: (k: string, v: string) => void h.store.set(k, v),
        removeItem: (k: string) => void h.store.delete(k),
      },
    },
    global: { fetch: fetchImpl as typeof fetch },
  });
  return {
    supabase,
    default: supabase,
    isSupabaseConfigured: () => true,
    getAccessToken: async () => {
      const { data } = await supabase.auth.getSession();
      return data.session?.access_token ?? null;
    },
  };
});

vi.mock("@/sdk/endpoints", () => ({ auth: {} }));

import { useAuthStore } from "@/stores/useAuthStore";
import { getAccessToken } from "@/auth/supabase";

const STORAGE_KEY = "sb-test-auth-token";

function seedSession(): void {
  const now = Math.floor(Date.now() / 1000);
  h.store.set(
    STORAGE_KEY,
    JSON.stringify({
      access_token: "test-access-token",
      refresh_token: "test-refresh-token",
      token_type: "bearer",
      expires_in: 3600,
      expires_at: now + 3600,
      user: {
        id: "00000000-0000-0000-0000-000000000001",
        aud: "authenticated",
        role: "authenticated",
        email: "shop@example.test",
        app_metadata: {},
        user_metadata: {},
        created_at: new Date().toISOString(),
      },
    })
  );
}

describe("useAuthStore.signOut (supabase-js >= 2.119.0 global-scope semantics)", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    h.store.clear();
    h.state.logoutMode = "ok";
    h.state.logoutScopes = [];
    seedSession();
    vi.spyOn(console, "warn").mockImplementation(() => {});
    vi.spyOn(console, "error").mockImplementation(() => {});
  });

  it("precondition: the seeded session is live", async () => {
    expect(await getAccessToken()).toBe("test-access-token");
  });

  it("server reachable: signs out globally and clears the session", async () => {
    const auth = useAuthStore();
    await auth.signOut();
    expect(h.state.logoutScopes).toEqual(["global"]);
    expect(h.store.has(STORAGE_KEY)).toBe(false);
    expect(await getAccessToken()).toBeNull();
    expect(auth.isAuthenticated).toBe(false);
  });

  it("offline: still clears this device's session (falls back to local)", async () => {
    h.state.logoutMode = "offline";
    const auth = useAuthStore();
    await auth.signOut();
    expect(await getAccessToken()).toBeNull();
    expect(h.store.has(STORAGE_KEY)).toBe(false);
    expect(auth.isAuthenticated).toBe(false);
    expect(h.state.logoutScopes[0]).toBe("global");
    expect(h.state.logoutScopes).toContain("local");
  });

  it("server 5xx: still clears this device's session (falls back to local)", async () => {
    h.state.logoutMode = "503";
    const auth = useAuthStore();
    await auth.signOut();
    expect(await getAccessToken()).toBeNull();
    expect(h.store.has(STORAGE_KEY)).toBe(false);
    expect(auth.isAuthenticated).toBe(false);
    expect(h.state.logoutScopes[0]).toBe("global");
    expect(h.state.logoutScopes).toContain("local");
  });

  it("library contract this store depends on: a failed global sign-out keeps the session", async () => {
    // Pins the 2.119.0 behavior directly. If supabase-js reverts or changes
    // it, this test flags that the fallback above should be re-evaluated.
    h.state.logoutMode = "503";
    const { supabase } = await import("@/auth/supabase");
    const { error } = await supabase.auth.signOut();
    expect(error).not.toBeNull();
    expect(h.store.has(STORAGE_KEY)).toBe(true);
  });
});
