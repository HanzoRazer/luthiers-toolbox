// packages/client/src/instrument-workspace/hub/InstrumentHubShell.spec.ts
// SPINE-005: activation behavior of the existing Instrument Hub at the Project route.
//
// Proves the Hub loads exactly the route-supplied Project, reloads on prop change,
// renders no stale content across a failed load, performs no automatic write on mount
// or input, and still delegates explicit "Apply to Project" to the existing composable
// commit path. Assertions are on rendered behavior and API call shape only.

import { describe, it, expect, beforeEach, vi, type Mock } from "vitest";
import { nextTick } from "vue";
import { mount, flushPromises } from "@vue/test-utils";
import InstrumentHubShell from "./InstrumentHubShell.vue";
import { useInstrumentProject } from "../shared-state/useInstrumentProject";
import type {
  DesignStateResponse,
  InstrumentProjectData,
} from "@/api/projects";

vi.mock("@/api/projects", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/api/projects")>();
  return {
    ...actual,
    getDesignState: vi.fn(),
    putDesignState: vi.fn(),
  };
});

import { getDesignState, putDesignState } from "@/api/projects";
const mockGet = getDesignState as unknown as Mock;
const mockPut = putDesignState as unknown as Mock;

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

function response(id: string): DesignStateResponse {
  return {
    project_id: id,
    name: `Project ${id}`,
    instrument_type: "electric_guitar",
    design_state: {
      schema_version: "1.0",
      instrument_type: "electric_guitar",
      spec: {
        scale_length_mm: 648,
        fret_count: 22,
        string_count: 6,
        nut_width_mm: 42,
        heel_width_mm: 56,
        neck_angle_degrees: 0,
        neck_joint_type: "bolt_on",
        body_join_fret: 14,
        tremolo_style: "hardtail",
      },
    } as InstrumentProjectData,
    created_at: "created",
    updated_at: "updated",
  };
}

// A Project whose design_state exists (so isLoaded is true and the editor renders) but
// carries no committed spec yet — the case that used to leak the prior Project's draft.
function responseNoSpec(id: string): DesignStateResponse {
  return {
    project_id: id,
    name: `Project ${id}`,
    instrument_type: "electric_guitar",
    design_state: {
      schema_version: "1.0",
      instrument_type: "electric_guitar",
    } as InstrumentProjectData,
    created_at: "created",
    updated_at: "updated",
  };
}

beforeEach(() => {
  vi.clearAllMocks();
  useInstrumentProject().clearProject();
});

describe("SPINE-005 Instrument Hub activation", () => {
  it("loads exactly the supplied Project ID on mount", async () => {
    mockGet.mockResolvedValue(response("P1"));
    const wrapper = mount(InstrumentHubShell, { props: { projectId: "P1" } });
    await flushPromises();

    expect(mockGet).toHaveBeenCalledTimes(1);
    expect(mockGet).toHaveBeenCalledWith("P1");
    expect(wrapper.find(".ihs-project-name").text()).toBe("Project P1");
  });

  it("performs no automatic commit on mount or load", async () => {
    mockGet.mockResolvedValue(response("P1"));
    mount(InstrumentHubShell, { props: { projectId: "P1" } });
    await flushPromises();

    expect(mockPut).not.toHaveBeenCalled();
  });

  it("reloads with the new Project when the route prop changes A -> B", async () => {
    mockGet.mockResolvedValue(response("A"));
    const wrapper = mount(InstrumentHubShell, { props: { projectId: "A" } });
    await flushPromises();

    mockGet.mockClear();
    mockGet.mockResolvedValue(response("B"));
    await wrapper.setProps({ projectId: "B" });
    await flushPromises();

    expect(mockGet).toHaveBeenCalledWith("B");
    expect(wrapper.find(".ihs-project-name").text()).toBe("Project B");
  });

  it("shows a controlled error and no stale content when a later load fails", async () => {
    mockGet.mockResolvedValueOnce(response("A"));
    const wrapper = mount(InstrumentHubShell, { props: { projectId: "A" } });
    await flushPromises();
    expect(wrapper.find(".ihs-project-name").text()).toBe("Project A");

    const b = deferred<DesignStateResponse>();
    mockGet.mockReturnValueOnce(b.promise);
    await wrapper.setProps({ projectId: "B" });
    b.reject(new Error("unauthorized"));
    await flushPromises();

    expect(wrapper.find(".ihs-error").exists()).toBe(true);
    expect(wrapper.find(".ihs-content").exists()).toBe(false); // A no longer rendered
    expect(wrapper.text()).toContain("unauthorized");
  });

  it("retry re-requests the current prop after a failed load", async () => {
    const a = deferred<DesignStateResponse>();
    mockGet.mockReturnValueOnce(a.promise);
    const wrapper = mount(InstrumentHubShell, { props: { projectId: "B" } });
    a.reject(new Error("network"));
    await flushPromises();
    expect(wrapper.find(".ihs-error").exists()).toBe(true);

    mockGet.mockClear();
    mockGet.mockResolvedValueOnce(response("B"));
    await wrapper.find(".ihs-error button").trigger("click"); // Retry
    await flushPromises();

    expect(mockGet).toHaveBeenCalledTimes(1);
    expect(mockGet).toHaveBeenCalledWith("B");
  });

  it("delegates explicit Apply to Project to the existing commit path", async () => {
    mockGet.mockResolvedValue(response("P1"));
    mockPut.mockResolvedValue(response("P1"));
    const wrapper = mount(InstrumentHubShell, { props: { projectId: "P1" } });
    await flushPromises();

    // No write yet — the Hub never auto-commits.
    expect(mockPut).not.toHaveBeenCalled();

    // Make an explicit edit: pick an instrument type other than the loaded one.
    const typeButtons = wrapper.findAll(".ihs-type-btn");
    const unselected = typeButtons.find(
      (b) => !b.classes().includes("ihs-type-btn--selected"),
    );
    expect(unselected).toBeTruthy();
    await unselected!.trigger("click"); // sets a local buffer + marks dirty

    // Explicit user action commits through useInstrumentProject.
    await wrapper.find(".ihs-btn--primary").trigger("click");
    await flushPromises();

    expect(mockPut).toHaveBeenCalled();
    expect(mockPut.mock.calls[0][0]).toBe("P1"); // committed to the active Project
  });

  it("does not carry an edited spec draft into a Project that has no committed spec (§5.1)", async () => {
    // Load A (has a committed spec) and make an uncommitted local draft edit.
    mockGet.mockResolvedValueOnce(response("A"));
    const wrapper = mount(InstrumentHubShell, { props: { projectId: "A" } });
    await flushPromises();
    const vm = wrapper.vm as unknown as { localSpec: Record<string, unknown> };
    expect(vm.localSpec.scale_length_mm).toBe(648);
    vm.localSpec.scale_length_mm = 700; // uncommitted draft under A
    await nextTick();

    // Switch to B, whose state exists but has NO spec section.
    mockGet.mockResolvedValueOnce(responseNoSpec("B"));
    await wrapper.setProps({ projectId: "B" });
    await flushPromises();

    // The editor renders for B (state present), but A's draft must not survive: the spec
    // buffer resets to the empty baseline rather than presenting 700 as B's value.
    expect(wrapper.find(".ihs-content").exists()).toBe(true);
    expect(vm.localSpec.scale_length_mm).toBeUndefined();
  });

  it("disables Apply while a commit is in flight so it cannot be double-submitted (§4.1)", async () => {
    mockGet.mockResolvedValueOnce(response("P1"));
    const wrapper = mount(InstrumentHubShell, { props: { projectId: "P1" } });
    await flushPromises();
    const vm = wrapper.vm as unknown as { markDirty: () => void };

    // Dirty without changing the instrument type, so Apply takes the single material-commit
    // path (one PUT) and the button is enabled (dirty, not saving).
    vm.markDirty();
    await nextTick();
    const applyBtn = () => wrapper.find(".ihs-btn--primary");
    expect(applyBtn().attributes("disabled")).toBeUndefined();

    // Begin a commit that stays in flight — the button must go disabled so a second Apply
    // (which the composable would refuse via single-flight) can never be issued from the UI.
    const put = deferred<DesignStateResponse>();
    mockPut.mockReturnValueOnce(put.promise);
    await applyBtn().trigger("click");
    await nextTick();
    expect(applyBtn().attributes("disabled")).toBeDefined();

    put.resolve(response("P1"));
    await flushPromises();
  });
});
