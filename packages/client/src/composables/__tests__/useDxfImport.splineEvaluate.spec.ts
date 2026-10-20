/**
 * The routed importer fails before it can ask for the missing spline route.
 * This locks the behavior witnessed on /art-studio/inlay-workspace.
 */
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useDxfImport } from "../useDxfImport";

describe("spline evaluate is not requested when the parser is absent", () => {
  beforeEach(() => {
    delete (window as unknown as { DxfParser?: unknown }).DxfParser;
  });

  it("records a visible parser error and does not call fetch", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch");
    const storageBefore = window.localStorage.length;
    const dxf = useDxfImport();
    const file = new File(
      ["0\nSECTION\n2\nENTITIES\n0\nSPLINE\n0\nENDSEC\n0\nEOF\n"],
      "witness.dxf",
      { type: "application/dxf" },
    );

    await dxf.loadFile(file);

    expect(dxf.error.value).toBe("Error: DxfParser not loaded");
    expect(dxf.pipeStage.value).toBe("idle");
    expect(dxf.rawPaths.value).toEqual([]);
    expect(dxf.normPaths.value).toEqual([]);
    expect(window.localStorage.length).toBe(storageBefore);
    const urls = fetchSpy.mock.calls.map((call) => String(call[0]));
    expect(urls.some((url) => url.includes("spline/evaluate"))).toBe(false);
    expect(fetchSpy).not.toHaveBeenCalled();
    fetchSpy.mockRestore();
  });
});
