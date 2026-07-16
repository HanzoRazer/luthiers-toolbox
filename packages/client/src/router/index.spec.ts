// packages/client/src/router/index.spec.ts
// SPINE-005: Project-scoped Instrument Hub route contract.
//
// Guards the locked contract: /instrument-hub/:projectId is the only Project-addressed
// Hub entry, bare /instrument-hub is a compatibility redirect to the unchanged legacy
// Instrument Geometry route, and no Project identity is ever inferred.

import { describe, it, expect, beforeEach } from "vitest";
import { createRouter, createMemoryHistory, type Router } from "vue-router";
import { routes } from "./index";

let router: Router;

beforeEach(async () => {
  router = createRouter({ history: createMemoryHistory(), routes });
  await router.push("/");
  await router.isReady();
});

describe("SPINE-005 canonical Instrument Hub route", () => {
  it("registers the named route InstrumentHub", () => {
    expect(router.hasRoute("InstrumentHub")).toBe(true);
  });

  it("resolves /instrument-hub/:projectId and retains the projectId param", () => {
    const resolved = router.resolve("/instrument-hub/proj-abc123");
    expect(resolved.name).toBe("InstrumentHub");
    expect(resolved.params.projectId).toBe("proj-abc123");
  });

  it("passes projectId to the component as an explicit route prop", () => {
    const record = router.getRoutes().find((r) => r.name === "InstrumentHub");
    // props: true — the param is delivered as a prop, not read from global state.
    expect(record?.props).toMatchObject({ default: true });
  });

  it("builds /instrument-hub/A from named navigation with an explicit projectId", () => {
    const resolved = router.resolve({
      name: "InstrumentHub",
      params: { projectId: "A" },
    });
    expect(resolved.path).toBe("/instrument-hub/A");
  });

  it("rejects named Hub navigation that supplies no projectId", () => {
    // No implicit Project lookup: a missing param is a routing failure, not a fallback.
    expect(() => router.resolve({ name: "InstrumentHub", params: {} })).toThrow();
  });
});

describe("SPINE-005 bare /instrument-hub compatibility redirect", () => {
  it("redirects bare /instrument-hub to /instrument-geometry", async () => {
    await router.push("/instrument-hub");
    expect(router.currentRoute.value.path).toBe("/instrument-geometry");
    expect(router.currentRoute.value.name).toBe("InstrumentGeometry");
  });

  it("preserves query and hash across the redirect", async () => {
    await router.push("/instrument-hub?x=1#y");
    expect(router.currentRoute.value.path).toBe("/instrument-geometry");
    expect(router.currentRoute.value.query).toEqual({ x: "1" });
    expect(router.currentRoute.value.hash).toBe("#y");
  });

  it("does not treat a project_id query on the bare path as Project identity", async () => {
    // The query is forwarded verbatim; it must never promote to the Hub route.
    await router.push("/instrument-hub?project_id=A");
    expect(router.currentRoute.value.path).toBe("/instrument-geometry");
    expect(router.currentRoute.value.name).not.toBe("InstrumentHub");
    expect(router.currentRoute.value.params.projectId).toBeUndefined();
    expect(router.currentRoute.value.query).toEqual({ project_id: "A" });
  });
});

describe("SPINE-005 legacy Instrument Geometry route is unchanged", () => {
  it("keeps /instrument-geometry on route name InstrumentGeometry", () => {
    const resolved = router.resolve("/instrument-geometry");
    expect(resolved.name).toBe("InstrumentGeometry");
  });

  it("no longer aliases /instrument-hub onto the legacy route", () => {
    // The alias is removed so the bare path can carry the redirect instead;
    // deep links keep working, but the two surfaces are no longer conflated.
    const record = router
      .getRoutes()
      .find((r) => r.name === "InstrumentGeometry");
    expect(record?.aliasOf).toBeUndefined();
    const hubRecords = router
      .getRoutes()
      .filter((r) => r.path === "/instrument-hub");
    expect(hubRecords.every((r) => r.name !== "InstrumentGeometry")).toBe(true);
  });

  it("resolves the legacy route and the Hub route to different records", () => {
    expect(router.resolve("/instrument-geometry").name).toBe(
      "InstrumentGeometry",
    );
    expect(router.resolve("/instrument-hub/A").name).toBe("InstrumentHub");
  });
});
