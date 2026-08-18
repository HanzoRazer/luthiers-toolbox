// packages/client/src/views/AppDashboardView.spec.ts
// SPINE-005: the Dashboard Instrument Hub link is Project-addressed only from an explicit
// route query, with a truthful label, and never falls back to the singleton Project.

import { describe, it, expect, vi, afterEach } from "vitest";
import { mount, flushPromises } from "@vue/test-utils";
import { createRouter, createMemoryHistory, type Router } from "vue-router";
import { routes } from "@/router/index";
import AppDashboardView from "./AppDashboardView.vue";

// The Dashboard reads the singleton only for the (unrelated) AI Assistant link. Mock it
// with a loaded Project so we can prove the Instrument Hub link ignores it as a fallback.
// Held in a mutable box rather than a fixed ref: LAB-023 needs a genuinely Project-less
// case, which a hard-coded ref cannot express. `vi.hoisted` because the mock factory is
// hoisted above these imports.
const hub = vi.hoisted(() => ({ projectId: "SINGLETON-ID" as string | null }));

vi.mock("@/instrument-workspace/shared-state/useInstrumentProject", async () => {
  const { ref } = await import("vue");
  return { useInstrumentProject: () => ({ projectId: ref(hub.projectId) }) };
});

afterEach(() => {
  hub.projectId = "SINGLETON-ID";
});

// LAB-023: AI Assistant link uses production route name `AiAssistant` only
// (`/ai/assistant/:project_id?`). No fixture route injection required.
async function mountAt(query: string) {
  const router: Router = createRouter({
    history: createMemoryHistory(),
    routes,
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

  it("falls back when the Project query is an array without a usable value", async () => {
    // §9: array-without-value query falls back. Repeated empty keys → ['', ''] → q[0] falsy.
    const wrapper = await mountAt("/?project_id=&project_id=");
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

describe("LAB-023 Dashboard AI Assistant navigation", () => {
  function assistantLink(wrapper: Awaited<ReturnType<typeof mountAt>>) {
    const link = wrapper
      .findAll("a.quick-link-card")
      .find((a) => a.text().includes("AI Assistant"));
    expect(link, "AI Assistant quick-link not rendered").toBeTruthy();
    return link!;
  }

  // Contract test, held against the production route table rather than the component.
  // RouterLink calls router.resolve() during render and THROWS on an unknown route name,
  // so reintroducing `AiAssistantProject` does not merely produce a wrong href — it takes
  // down the entire Dashboard render for anyone with a Project loaded.
  it("pins the production route contract: AiAssistant exists, AiAssistantProject does not", () => {
    const router = createRouter({ history: createMemoryHistory(), routes });
    expect(router.hasRoute("AiAssistant")).toBe(true);
    expect(router.hasRoute("AiAssistantProject")).toBe(false);
    expect(
      router.resolve({ name: "AiAssistant", params: { project_id: "A" } }).path,
    ).toBe("/ai/assistant/A");
    expect(router.resolve({ name: "AiAssistant" }).path).toBe("/ai/assistant");
  });

  it("prefers the query Project id over the singleton", async () => {
    hub.projectId = "SINGLETON-ID";
    const wrapper = await mountAt("/?project_id=A");
    expect(assistantLink(wrapper).attributes("href")).toBe("/ai/assistant/A");
  });

  it("falls back to the singleton Project when the query names none", async () => {
    const wrapper = await mountAt("/");
    // Deliberate asymmetry with the Instrument Hub link, which under SPINE-005 must NOT
    // fall back to the singleton. Asserted exactly so the difference stays intentional.
    expect(assistantLink(wrapper).attributes("href")).toBe(
      "/ai/assistant/SINGLETON-ID",
    );
  });

  it("uses the bare assistant route when no Project is known anywhere", async () => {
    hub.projectId = null;
    const wrapper = await mountAt("/");
    expect(assistantLink(wrapper).attributes("href")).toBe("/ai/assistant");
  });
});
