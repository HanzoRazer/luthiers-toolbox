/**
 * rmosConfidence.spec.ts
 * Bundle 08: Unit tests for centralized confidence heuristic
 */

import { describe, it, expect } from "vitest";
import {
  computeConfidence,
  computeConfidenceTrend,
  confidenceToRank,
  getConfidenceTooltipText,
  type ConfLevel,
  type ConfidenceMetrics,
} from "./rmosConfidence";

describe("rmosConfidence", () => {
  describe("computeConfidence", () => {
    it("returns HIGH when no hot rings, no pattern changes, warningDelta <= 0", () => {
      const metrics: ConfidenceMetrics = {
        hotRings: 0,
        patternChanges: 0,
        warningDelta: 0,
      };
      expect(computeConfidence(metrics)).toBe("HIGH");
    });

    it("returns HIGH when warningDelta is negative (fewer warnings)", () => {
      const metrics: ConfidenceMetrics = {
        hotRings: 0,
        patternChanges: 0,
        warningDelta: -2,
      };
      expect(computeConfidence(metrics)).toBe("HIGH");
    });

    it("returns MED when ≤2 hot rings, ≤1 pattern change, warningDelta ≤ 2", () => {
      const metrics: ConfidenceMetrics = {
        hotRings: 2,
        patternChanges: 1,
        warningDelta: 2,
      };
      expect(computeConfidence(metrics)).toBe("MED");
    });

    it("returns MED at boundary (1 hot ring, 0 pattern changes, 1 warning)", () => {
      const metrics: ConfidenceMetrics = {
        hotRings: 1,
        patternChanges: 0,
        warningDelta: 1,
      };
      expect(computeConfidence(metrics)).toBe("MED");
    });

    it("returns LOW when many hot rings", () => {
      const metrics: ConfidenceMetrics = {
        hotRings: 5,
        patternChanges: 0,
        warningDelta: 0,
      };
      expect(computeConfidence(metrics)).toBe("LOW");
    });

    it("returns LOW when many pattern changes", () => {
      const metrics: ConfidenceMetrics = {
        hotRings: 0,
        patternChanges: 3,
        warningDelta: 0,
      };
      expect(computeConfidence(metrics)).toBe("LOW");
    });

    it("returns LOW when warningDelta exceeds threshold", () => {
      const metrics: ConfidenceMetrics = {
        hotRings: 0,
        patternChanges: 0,
        warningDelta: 5,
      };
      expect(computeConfidence(metrics)).toBe("LOW");
    });

    it("returns LOW when all metrics exceed thresholds", () => {
      const metrics: ConfidenceMetrics = {
        hotRings: 10,
        patternChanges: 5,
        warningDelta: 10,
      };
      expect(computeConfidence(metrics)).toBe("LOW");
    });
  });

  describe("computeConfidenceTrend", () => {
    it("returns NONE when prev is null", () => {
      expect(computeConfidenceTrend("HIGH", null)).toBe("NONE");
      expect(computeConfidenceTrend("MED", null)).toBe("NONE");
      expect(computeConfidenceTrend("LOW", null)).toBe("NONE");
    });

    it("returns UP when confidence improved", () => {
      expect(computeConfidenceTrend("HIGH", "MED")).toBe("UP");
      expect(computeConfidenceTrend("HIGH", "LOW")).toBe("UP");
      expect(computeConfidenceTrend("MED", "LOW")).toBe("UP");
    });

    it("returns DOWN when confidence decreased", () => {
      expect(computeConfidenceTrend("LOW", "HIGH")).toBe("DOWN");
      expect(computeConfidenceTrend("LOW", "MED")).toBe("DOWN");
      expect(computeConfidenceTrend("MED", "HIGH")).toBe("DOWN");
    });

    it("returns FLAT when confidence unchanged", () => {
      expect(computeConfidenceTrend("HIGH", "HIGH")).toBe("FLAT");
      expect(computeConfidenceTrend("MED", "MED")).toBe("FLAT");
      expect(computeConfidenceTrend("LOW", "LOW")).toBe("FLAT");
    });
  });

  describe("confidenceToRank", () => {
    it("returns 3 for HIGH", () => {
      expect(confidenceToRank("HIGH")).toBe(3);
    });

    it("returns 2 for MED", () => {
      expect(confidenceToRank("MED")).toBe(2);
    });

    it("returns 1 for LOW", () => {
      expect(confidenceToRank("LOW")).toBe(1);
    });
  });

  describe("getConfidenceTooltipText", () => {
    it("returns a non-empty string", () => {
      const text = getConfidenceTooltipText();
      expect(text).toBeTruthy();
      expect(typeof text).toBe("string");
    });

    it("contains confidence level explanations", () => {
      const text = getConfidenceTooltipText();
      expect(text).toContain("HIGH:");
      expect(text).toContain("MED:");
      expect(text).toContain("LOW:");
    });

    it("contains trend explanations", () => {
      const text = getConfidenceTooltipText();
      expect(text).toContain("Trend");
      expect(text).toContain("↑");
      expect(text).toContain("→");
      expect(text).toContain("↓");
    });

    it("explains hot ring threshold", () => {
      const text = getConfidenceTooltipText();
      expect(text).toContain("0.15mm");
    });
  });
});
