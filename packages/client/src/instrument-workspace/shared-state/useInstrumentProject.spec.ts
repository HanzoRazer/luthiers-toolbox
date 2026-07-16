// packages/client/src/instrument-workspace/shared-state/useInstrumentProject.spec.ts
// SPINE-005: concurrency safety for the Project singleton.
//
// The composable is a module singleton observed outside the Hub (Sidebar, Dashboard,
// Assistant). These tests prove latest-request-wins loading, stale load/save response
// isolation, single-flight explicit commits, and that the existing public interface and
// write authority are unchanged. They assert public state and API call shape only —
// never private token variables.

import { describe, it, expect, beforeEach, vi, type Mock } from "vitest";
import { useInstrumentProject } from "./useInstrumentProject";
import type {
  DesignStateResponse,
  InstrumentSpec,
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

// --- helpers ---------------------------------------------------------------

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

const SPEC: InstrumentSpec = {
  scale_length_mm: 648,
  fret_count: 22,
  string_count: 6,
  nut_width_mm: 42,
  heel_width_mm: 56,
  neck_angle_degrees: 0,
  neck_joint_type: "bolt_on",
  body_join_fret: 14,
  tremolo_style: "hardtail",
};

function designState(): InstrumentProjectData {
  return {
    schema_version: "1.0",
    instrument_type: "electric_guitar",
    spec: SPEC,
  } as InstrumentProjectData;
}

function response(id: string, updatedAt = `updated-${id}`): DesignStateResponse {
  return {
    project_id: id,
    name: `name-${id}`,
    instrument_type: "electric_guitar",
    design_state: designState(),
    created_at: "created",
    updated_at: updatedAt,
  };
}

// The singleton persists across tests; reset it deterministically each time.
beforeEach(() => {
  vi.clearAllMocks();
  useInstrumentProject().clearProject();
});

// --- latest-request-wins loading -------------------------------------------

describe("SPINE-005 latest-request-wins loading", () => {
  it("ends with B active when responses resolve in order A then B", async () => {
    const hub = useInstrumentProject();
    const a = deferred<DesignStateResponse>();
    const b = deferred<DesignStateResponse>();
    mockGet.mockReturnValueOnce(a.promise).mockReturnValueOnce(b.promise);

    const loadA = hub.loadProject("A");
    const loadB = hub.loadProject("B");

    a.resolve(response("A"));
    b.resolve(response("B"));
    await Promise.all([loadA, loadB]);

    expect(hub.projectId.value).toBe("B");
    expect(hub.projectName.value).toBe("name-B");
    expect(hub.isLoading.value).toBe(false);
  });

  it("ends with B active when responses resolve in order B then A", async () => {
    const hub = useInstrumentProject();
    const a = deferred<DesignStateResponse>();
    const b = deferred<DesignStateResponse>();
    mockGet.mockReturnValueOnce(a.promise).mockReturnValueOnce(b.promise);

    const loadA = hub.loadProject("A");
    const loadB = hub.loadProject("B");

    b.resolve(response("B"));
    await loadB;
    a.resolve(response("A")); // late, superseded — must be discarded
    await loadA;

    expect(hub.projectId.value).toBe("B");
    expect(hub.projectName.value).toBe("name-B");
    expect(hub.isLoading.value).toBe(false);
  });

  it("leaves no stale A content renderable when a later B load fails", async () => {
    const hub = useInstrumentProject();
    mockGet.mockResolvedValueOnce(response("A"));
    await hub.loadProject("A");
    expect(hub.isLoaded.value).toBe(true);

    const b = deferred<DesignStateResponse>();
    mockGet.mockReturnValueOnce(b.promise);
    const loadB = hub.loadProject("B");
    b.reject(new Error("boom"));
    await loadB;

    expect(hub.projectId.value).toBe("B");
    expect(hub.isLoaded.value).toBe(false); // A is not renderable under B
    expect(hub.spec.value).toBeNull();
    expect(hub.loadError.value).toBe("boom");
    expect(hub.isLoading.value).toBe(false);
  });

  it("does not let a superseded load error surface under the newer Project", async () => {
    const hub = useInstrumentProject();
    const a = deferred<DesignStateResponse>();
    const b = deferred<DesignStateResponse>();
    mockGet.mockReturnValueOnce(a.promise).mockReturnValueOnce(b.promise);

    const loadA = hub.loadProject("A");
    const loadB = hub.loadProject("B");

    b.resolve(response("B"));
    await loadB;
    a.reject(new Error("A failed late"));
    await loadA;

    expect(hub.projectId.value).toBe("B");
    expect(hub.loadError.value).toBeNull(); // A's late error is not published under B
    expect(hub.isLoaded.value).toBe(true);
  });
});

// --- single-flight explicit commits ----------------------------------------

describe("SPINE-005 single-flight explicit commits", () => {
  it("rejects a second commit while one is in flight without a request or metadata change", async () => {
    const hub = useInstrumentProject();
    mockGet.mockResolvedValueOnce(response("A"));
    await hub.loadProject("A");
    hub.markDirty();
    expect(hub.isDirty.value).toBe(true);

    const put = deferred<DesignStateResponse>();
    mockPut.mockReturnValueOnce(put.promise);

    const first = hub.commitSpec(SPEC); // in flight
    const second = await hub.commitSpec(SPEC); // must be refused immediately

    expect(second).toBe(false);
    expect(mockPut).toHaveBeenCalledTimes(1); // no second request
    expect(hub.isDirty.value).toBe(true); // caller's draft preserved
    expect(hub.isSaving.value).toBe(true); // active save's metadata untouched
    expect(hub.saveError.value).toBeNull();

    put.resolve(response("A", "saved"));
    await expect(first).resolves.toBe(true);
    expect(hub.isDirty.value).toBe(false);
    expect(hub.isSaving.value).toBe(false);
  });

  it("preserves existing commit request shape and target authority", async () => {
    const hub = useInstrumentProject();
    mockGet.mockResolvedValueOnce(response("A"));
    await hub.loadProject("A");

    mockPut.mockResolvedValueOnce(response("A", "saved"));
    const ok = await hub.commitSpec(SPEC, "electric_guitar");

    expect(ok).toBe(true);
    expect(mockPut).toHaveBeenCalledTimes(1);
    const [calledId, calledState, message] = mockPut.mock.calls[0];
    expect(calledId).toBe("A");
    expect(calledState.spec).toEqual(SPEC);
    expect(typeof message).toBe("string");
  });
});

// --- cross-Project save/load isolation -------------------------------------

describe("SPINE-005 stale save response isolation", () => {
  it("does not apply an A-commit response after navigation selected B", async () => {
    const hub = useInstrumentProject();
    mockGet.mockResolvedValueOnce(response("A"));
    await hub.loadProject("A");

    const put = deferred<DesignStateResponse>();
    mockPut.mockReturnValueOnce(put.promise);
    const commitA = hub.commitSpec(SPEC); // targets A, in flight

    // Navigate to B and let it fully load while A's save is pending.
    mockGet.mockResolvedValueOnce(response("B"));
    await hub.loadProject("B");
    expect(hub.projectId.value).toBe("B");

    // A's save now resolves late — the server write stands, but B state is untouched.
    put.resolve(response("A", "late-A-save"));
    await expect(commitA).resolves.toBe(true);

    expect(hub.projectId.value).toBe("B");
    expect(hub.projectName.value).toBe("name-B");
    expect(hub.lastSavedAt.value).not.toBe("late-A-save");
    expect(hub.isSaving.value).toBe(false);
    expect(hub.saveError.value).toBeNull();
  });

  it("lets a fresh commit succeed on B after a superseded A save settles", async () => {
    const hub = useInstrumentProject();
    mockGet.mockResolvedValueOnce(response("A"));
    await hub.loadProject("A");

    const putA = deferred<DesignStateResponse>();
    mockPut.mockReturnValueOnce(putA.promise);
    const commitA = hub.commitSpec(SPEC);

    mockGet.mockResolvedValueOnce(response("B"));
    await hub.loadProject("B");

    putA.resolve(response("A", "late-A"));
    await commitA; // releases the single-flight guard

    mockPut.mockResolvedValueOnce(response("B", "saved-B"));
    const okB = await hub.commitSpec(SPEC);
    expect(okB).toBe(true);
    expect(hub.lastSavedAt.value).toBe("saved-B");
  });
});

// --- interface stability ----------------------------------------------------

describe("SPINE-005 preserves the public composable interface", () => {
  it("still exposes every documented export with the same kinds", () => {
    const hub = useInstrumentProject();
    for (const key of [
      "projectId",
      "projectName",
      "isLoading",
      "isSaving",
      "loadError",
      "saveError",
      "lastSavedAt",
      "isDirty",
      "isLoaded",
      "isCamReady",
      "instrumentType",
      "spec",
      "blueprintGeometry",
      "bridgeState",
      "neckState",
      "materialSelection",
      "analyzerObservations",
      "manufacturingState",
      "scaleLengthMm",
      "fretCount",
      "neckAngleDeg",
    ] as const) {
      expect(hub[key]).toHaveProperty("value");
    }
    for (const fn of [
      "loadProject",
      "clearProject",
      "commitSpec",
      "commitInstrumentType",
      "commitBridgeState",
      "commitNeckState",
      "commitMaterialSelection",
      "markDirty",
      "getDefaultSpec",
      "isOperationComplete",
    ] as const) {
      expect(typeof hub[fn]).toBe("function");
    }
  });

  it("clearProject resets observable state deterministically", async () => {
    const hub = useInstrumentProject();
    mockGet.mockResolvedValueOnce(response("A"));
    await hub.loadProject("A");
    expect(hub.isLoaded.value).toBe(true);

    hub.clearProject();
    expect(hub.projectId.value).toBeNull();
    expect(hub.isLoaded.value).toBe(false);
    expect(hub.isLoading.value).toBe(false);
    expect(hub.isSaving.value).toBe(false);
    expect(hub.loadError.value).toBeNull();
    expect(hub.saveError.value).toBeNull();
  });

  it("discards an in-flight load that resolves after clearProject", async () => {
    const hub = useInstrumentProject();
    const a = deferred<DesignStateResponse>();
    mockGet.mockReturnValueOnce(a.promise);
    const loadA = hub.loadProject("A");

    hub.clearProject();
    a.resolve(response("A"));
    await loadA;

    expect(hub.projectId.value).toBeNull(); // no stale repopulation after clear
    expect(hub.isLoaded.value).toBe(false);
  });
});
