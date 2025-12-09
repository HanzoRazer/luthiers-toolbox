// compareModes.spec.ts
// B22.10: Unit tests for compare mode utilities

import { describe, it, expect } from "vitest";
import {
  COMPARE_MODES,
  toBackendMode,
  getModeLabel,
  type CompareMode,
} from "./compareModes";

describe("compareModes", () => {
  it("exports all 5 compare modes", () => {
    expect(COMPARE_MODES).toHaveLength(5);
    expect(COMPARE_MODES).toContain("side-by-side");
    expect(COMPARE_MODES).toContain("overlay");
    expect(COMPARE_MODES).toContain("delta");
    expect(COMPARE_MODES).toContain("blink");
    expect(COMPARE_MODES).toContain("xray");
  });

  describe("toBackendMode", () => {
    it("maps side-by-side to backend side-by-side", () => {
      expect(toBackendMode("side-by-side")).toBe("side-by-side");
    });

    it("maps overlay to backend overlay", () => {
      expect(toBackendMode("overlay")).toBe("overlay");
    });

    it("maps delta to backend delta", () => {
      expect(toBackendMode("delta")).toBe("delta");
    });

    it("maps blink to backend overlay (client-side effect)", () => {
      expect(toBackendMode("blink")).toBe("overlay");
    });

    it("maps xray to backend overlay (client-side effect)", () => {
      expect(toBackendMode("xray")).toBe("overlay");
    });
  });

  describe("getModeLabel", () => {
    it("returns correct labels for all modes", () => {
      expect(getModeLabel("side-by-side")).toBe("Side-by-side");
      expect(getModeLabel("overlay")).toBe("Overlay");
      expect(getModeLabel("delta")).toBe("Delta only");
      expect(getModeLabel("blink")).toBe("Blink");
      expect(getModeLabel("xray")).toBe("X-ray");
    });

    it("returns mode string as fallback for unknown modes", () => {
      expect(getModeLabel("unknown" as CompareMode)).toBe("unknown");
    });
  });

  describe("type safety", () => {
    it("CompareMode type only accepts valid modes", () => {
      const validModes: CompareMode[] = [
        "side-by-side",
        "overlay",
        "delta",
        "blink",
        "xray",
      ];

      validModes.forEach((mode) => {
        expect(COMPARE_MODES).toContain(mode);
      });
    });
  });
});
