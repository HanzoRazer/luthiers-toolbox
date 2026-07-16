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

  it("is deterministic under repeated same-id navigation with out-of-order responses", async () => {
    // §9: repeated same-ID behavior is deterministic; the latest request still wins.
    const hub = useInstrumentProject();
    const first = deferred<DesignStateResponse>();
    const second = deferred<DesignStateResponse>();
    mockGet.mockReturnValueOnce(first.promise).mockReturnValueOnce(second.promise);

    const loadA1 = hub.loadProject("A");
    const loadA2 = hub.loadProject("A");

    second.resolve(response("A", "second"));
    await loadA2;
    first.resolve(response("A", "first")); // stale, superseded — must be discarded
    await loadA1;

    expect(hub.projectId.value).toBe("A");
    expect(hub.lastSavedAt.value).toBe("second"); // newest request wins, not the late one
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

  it("clears the saving indicator when a same-id reload supersedes an in-flight save", async () => {
    // Regression: the completing save must clear _isSaving even when its response is
    // discarded because a same-id loadProject bumped the generation past it.
    const hub = useInstrumentProject();
    mockGet.mockResolvedValueOnce(response("A"));
    await hub.loadProject("A");

    const put = deferred<DesignStateResponse>();
    mockPut.mockReturnValueOnce(put.promise);
    const commit = hub.commitSpec(SPEC); // in flight
    expect(hub.isSaving.value).toBe(true);

    // Same-id reload supersedes the save's generation without quarantining (not a switch).
    mockGet.mockResolvedValueOnce(response("A"));
    await hub.loadProject("A");

    put.resolve(response("A", "discarded")); // response is discarded (superseded)
    await commit;

    expect(hub.isSaving.value).toBe(false); // no stuck "Saving…" indicator
    expect(hub.saveError.value).toBeNull();
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

  it("does not publish an A-commit failure under B after navigation", async () => {
    // §9: save/load errors remain attributable to the correct Project operation.
    const hub = useInstrumentProject();
    mockGet.mockResolvedValueOnce(response("A"));
    await hub.loadProject("A");

    const put = deferred<DesignStateResponse>();
    mockPut.mockReturnValueOnce(put.promise);
    const commitA = hub.commitSpec(SPEC); // targets A, in flight

    mockGet.mockResolvedValueOnce(response("B"));
    await hub.loadProject("B");
    expect(hub.projectId.value).toBe("B");

    put.reject(new Error("A save failed late"));
    await expect(commitA).resolves.toBe(false);

    expect(hub.saveError.value).toBeNull(); // A's error is not shown under B
    expect(hub.isSaving.value).toBe(false);
    expect(hub.projectName.value).toBe("name-B");
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

// --- higher-order interleaving witnesses (§4.4, §5.4) ----------------------

describe("SPINE-005 higher-order request interleaving", () => {
  it("publishes only the latest of A1 -> A2 -> B -> A3 under mixed resolution order (§4.4)", async () => {
    const hub = useInstrumentProject();
    const d1 = deferred<DesignStateResponse>();
    const d2 = deferred<DesignStateResponse>();
    const d3 = deferred<DesignStateResponse>();
    const d4 = deferred<DesignStateResponse>();
    mockGet
      .mockReturnValueOnce(d1.promise) // A1
      .mockReturnValueOnce(d2.promise) // A2
      .mockReturnValueOnce(d3.promise) // B
      .mockReturnValueOnce(d4.promise); // A3 (latest generation)

    const l1 = hub.loadProject("A");
    const l2 = hub.loadProject("A");
    const l3 = hub.loadProject("B");
    const l4 = hub.loadProject("A");

    // Settle in a deliberately scrambled order; only the last-issued request may win.
    d2.resolve(response("A", "gen2"));
    d4.resolve(response("A", "gen4"));
    d1.resolve(response("A", "gen1"));
    d3.resolve(response("B", "genB"));
    await Promise.all([l1, l2, l3, l4]);

    expect(hub.projectId.value).toBe("A"); // final state = last requested Project
    expect(hub.lastSavedAt.value).toBe("gen4"); // no stale generation repopulated state
    expect(hub.loadError.value).toBeNull();
    expect(hub.isLoading.value).toBe(false);
  });

  it("discards an in-flight save that resolves after clearProject and frees the guard (§5.4)", async () => {
    const hub = useInstrumentProject();
    mockGet.mockResolvedValueOnce(response("A"));
    await hub.loadProject("A");

    const put = deferred<DesignStateResponse>();
    mockPut.mockReturnValueOnce(put.promise);
    const saving = hub.commitSpec({ ...SPEC, scale_length_mm: 700 });

    hub.clearProject(); // clear while the save is still in flight
    put.resolve(response("A", "after-clear")); // server write stood, but must not repopulate
    const ok = await saving;

    expect(ok).toBe(true); // the server write itself succeeded
    expect(hub.projectId.value).toBeNull(); // cleared state is NOT repopulated
    expect(hub.spec.value).toBeNull();
    expect(hub.isSaving.value).toBe(false); // display flag released
    expect(hub.lastSavedAt.value).toBeNull(); // no stale save metadata under a cleared hub

    // The single-flight guard was released: a later Project can load and commit.
    mockGet.mockResolvedValueOnce(response("B"));
    await hub.loadProject("B");
    const put2 = deferred<DesignStateResponse>();
    mockPut.mockReturnValueOnce(put2.promise);
    const saving2 = hub.commitSpec({ ...SPEC, scale_length_mm: 660 });
    put2.resolve(response("B", "b-saved"));

    expect(await saving2).toBe(true);
    expect(hub.lastSavedAt.value).toBe("b-saved");
  });
});
