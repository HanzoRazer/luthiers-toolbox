// packages/client/src/views/AppDashboardView.spec.ts
// SPINE-005: the Dashboard Instrument Hub link is Project-addressed only from an explicit
// route query, with a truthful label, and never falls back to the singleton Project.

import { describe, it, expect, vi } from "vitest";
import { ref } from "vue";
import { mount, flushPromises } from "@vue/test-utils";
import { createRouter, createMemoryHistory, type Router } from "vue-router";
import { routes } from "@/router/index";
import AppDashboardView from "./AppDashboardView.vue";

// The Dashboard reads the singleton only for the (unrelated) AI Assistant link. Mock it
// with a loaded Project so we can prove the Instrument Hub link ignores it as a fallback.
vi.mock("@/instrument-workspace/shared-state/useInstrumentProject", () => ({
  useInstrumentProject: () => ({ projectId: ref("SINGLETON-ID") }),
}));

// The Dashboard's unrelated AI Assistant link targets route name `AiAssistantProject`,
// which the production router does not define (a pre-existing mismatch LAB-023 recorded and
// SPINE-005 leaves untouched). Provide it in the test fixture only so the component mounts;
// this does not alter production routing or that link's behavior.
const testRoutes = [
  ...routes,
  {
    path: "/ai/assistant/project/:projectId",
    name: "AiAssistantProject",
    component: { template: "<div />" },
  },
];

async function mountAt(query: string) {
  const router: Router = createRouter({
    history: createMemoryHistory(),
    routes: testRoutes,
  });
  await router.replace(query);
  await router.isReady();
  const wrapper = mount(AppDashboardView, { global: { plugins: [router] } });
  // Open the Design dropdown (first nav-item) so its links render.
  await wrapper.find(".nav-item").trigger("mouseenter");
  await flushPromises();
  return wrapper;
}

/** The Design-module link that is either Instrument Hub or Instrument Geometry. */
function hubLink(wrapper: Awaited<ReturnType<typeof mountAt>>) {
  return wrapper
    .findAll("a.dropdown-link")
    .find((a) => /Instrument (Hub|Geometry)/.test(a.text()));
}

describe("SPINE-005 Dashboard Instrument Hub navigation", () => {
  it("uses the named Project route when the query names a Project", async () => {
    const wrapper = await mountAt("/?project_id=A");
    const link = hubLink(wrapper);
    expect(link).toBeTruthy();
    expect(link!.text()).toContain("Instrument Hub");
    expect(link!.attributes("href")).toBe("/instrument-hub/A");
  });

  it("falls back to Instrument Geometry when no Project query is present", async () => {
    const wrapper = await mountAt("/");
    const link = hubLink(wrapper);
    expect(link!.text()).toContain("Instrument Geometry");
    expect(link!.attributes("href")).toBe("/instrument-geometry");
  });

  it("falls back when the Project query is present but empty", async () => {
    const wrapper = await mountAt("/?project_id=");
    const link = hubLink(wrapper);
    expect(link!.text()).toContain("Instrument Geometry");
    expect(link!.attributes("href")).toBe("/instrument-geometry");
  });

  it("does not use the singleton Project ID as an implicit Hub-link fallback", async () => {
    // The singleton is mocked to a loaded Project; with no query, the link must still
    // be the legacy route, never /instrument-hub/SINGLETON-ID.
    const wrapper = await mountAt("/");
    const link = hubLink(wrapper);
    expect(link!.attributes("href")).toBe("/instrument-geometry");
    expect(link!.attributes("href")).not.toContain("SINGLETON-ID");
  });

  it("labels the destination truthfully so one label never names two workflows", async () => {
    const project = hubLink(await mountAt("/?project_id=A"));
    const legacy = hubLink(await mountAt("/"));
    expect(project!.text()).toContain("Instrument Hub");
    expect(project!.text()).not.toContain("Instrument Geometry");
    expect(legacy!.text()).toContain("Instrument Geometry");
    expect(legacy!.text()).not.toContain("Instrument Hub");
  });
});
