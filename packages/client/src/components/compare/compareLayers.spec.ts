// compareLayers.spec.ts
// B22.11: Unit tests for layer-aware compare utilities

import { describe, it, expect } from "vitest";
import {
  buildLayerDiffSummary,
  isLayerMismatched,
  cssEscapeLayerId,
  buildHiddenLayerCss,
  normalizeLayerInfo,
  type LayerInfo,
} from "./compareLayers";

describe("compareLayers", () => {
  describe("buildLayerDiffSummary", () => {
    it("identifies layers present only in left", () => {
      const layers: LayerInfo[] = [
        {
          id: "body",
          label: "Body",
          inLeft: true,
          inRight: false,
          visibleLeft: true,
          visibleRight: false,
        },
        {
          id: "neck",
          label: "Neck",
          inLeft: true,
          inRight: true,
          visibleLeft: true,
          visibleRight: true,
        },
      ];

      const summary = buildLayerDiffSummary(layers);

      expect(summary.addedLeftOnly).toEqual(["body"]);
      expect(summary.addedRightOnly).toEqual([]);
      expect(summary.common).toEqual(["neck"]);
    });

    it("identifies layers present only in right", () => {
      const layers: LayerInfo[] = [
        {
          id: "inlay",
          label: "Inlay",
          inLeft: false,
          inRight: true,
          visibleLeft: false,
          visibleRight: true,
        },
        {
          id: "bridge",
          label: "Bridge",
          inLeft: true,
          inRight: true,
          visibleLeft: true,
          visibleRight: true,
        },
      ];

      const summary = buildLayerDiffSummary(layers);

      expect(summary.addedLeftOnly).toEqual([]);
      expect(summary.addedRightOnly).toEqual(["inlay"]);
      expect(summary.common).toEqual(["bridge"]);
    });

    it("identifies common layers", () => {
      const layers: LayerInfo[] = [
        {
          id: "body",
          label: "Body",
          inLeft: true,
          inRight: true,
          visibleLeft: true,
          visibleRight: true,
        },
        {
          id: "neck",
          label: "Neck",
          inLeft: true,
          inRight: true,
          visibleLeft: true,
          visibleRight: true,
        },
      ];

      const summary = buildLayerDiffSummary(layers);

      expect(summary.addedLeftOnly).toEqual([]);
      expect(summary.addedRightOnly).toEqual([]);
      expect(summary.common).toEqual(["body", "neck"]);
    });

    it("handles layers absent from both sides", () => {
      const layers: LayerInfo[] = [
        {
          id: "ghost",
          label: "Ghost",
          inLeft: false,
          inRight: false,
          visibleLeft: false,
          visibleRight: false,
        },
      ];

      const summary = buildLayerDiffSummary(layers);

      expect(summary.addedLeftOnly).toEqual([]);
      expect(summary.addedRightOnly).toEqual([]);
      expect(summary.common).toEqual([]);
    });

    it("handles empty layer list", () => {
      const summary = buildLayerDiffSummary([]);

      expect(summary.addedLeftOnly).toEqual([]);
      expect(summary.addedRightOnly).toEqual([]);
      expect(summary.common).toEqual([]);
    });
  });

  describe("isLayerMismatched", () => {
    it("returns true for presence mismatch (left only)", () => {
      const layer: LayerInfo = {
        id: "body",
        label: "Body",
        inLeft: true,
        inRight: false,
        visibleLeft: true,
        visibleRight: false,
      };

      expect(isLayerMismatched(layer)).toBe(true);
    });

    it("returns true for presence mismatch (right only)", () => {
      const layer: LayerInfo = {
        id: "inlay",
        label: "Inlay",
        inLeft: false,
        inRight: true,
        visibleLeft: false,
        visibleRight: true,
      };

      expect(isLayerMismatched(layer)).toBe(true);
    });

    it("returns true for visibility mismatch (left hidden)", () => {
      const layer: LayerInfo = {
        id: "neck",
        label: "Neck",
        inLeft: true,
        inRight: true,
        visibleLeft: false, // Hidden on left
        visibleRight: true,
      };

      expect(isLayerMismatched(layer)).toBe(true);
    });

    it("returns true for visibility mismatch (right hidden)", () => {
      const layer: LayerInfo = {
        id: "bridge",
        label: "Bridge",
        inLeft: true,
        inRight: true,
        visibleLeft: true,
        visibleRight: false, // Hidden on right
      };

      expect(isLayerMismatched(layer)).toBe(true);
    });

    it("returns false when layer is present and visible on both sides", () => {
      const layer: LayerInfo = {
        id: "body",
        label: "Body",
        inLeft: true,
        inRight: true,
        visibleLeft: true,
        visibleRight: true,
      };

      expect(isLayerMismatched(layer)).toBe(false);
    });
  });

  describe("cssEscapeLayerId", () => {
    it("escapes backslashes", () => {
      expect(cssEscapeLayerId("layer\\with\\backslash")).toBe(
        "layer\\\\with\\\\backslash"
      );
    });

    it("escapes double quotes", () => {
      expect(cssEscapeLayerId('layer"with"quotes')).toBe(
        'layer\\"with\\"quotes'
      );
    });

    it("escapes single quotes", () => {
      expect(cssEscapeLayerId("layer'with'quotes")).toBe(
        "layer\\'with\\'quotes"
      );
    });

    it("escapes newlines", () => {
      expect(cssEscapeLayerId("layer\nwith\nnewlines")).toBe(
        "layer\\nwith\\nnewlines"
      );
    });

    it("handles normal IDs without changes", () => {
      expect(cssEscapeLayerId("body-layer-01")).toBe("body-layer-01");
    });
  });

  describe("buildHiddenLayerCss", () => {
    it("returns empty string for no hidden layers", () => {
      const css = buildHiddenLayerCss(new Set());
      expect(css).toBe("");
    });

    it("builds CSS for single hidden layer", () => {
      const css = buildHiddenLayerCss(new Set(["body"]));
      expect(css).toContain("g#body");
      expect(css).toContain('g[data-layer-id="body"]');
      expect(css).toContain("display: none !important");
    });

    it("builds CSS for multiple hidden layers", () => {
      const css = buildHiddenLayerCss(new Set(["body", "neck", "inlay"]));
      expect(css).toContain("g#body");
      expect(css).toContain("g#neck");
      expect(css).toContain("g#inlay");
      expect(css).toContain("display: none !important");
    });

    it("escapes special characters in layer IDs", () => {
      const css = buildHiddenLayerCss(new Set(['layer"with"quotes']));
      expect(css).toContain('layer\\"with\\"quotes');
    });
  });

  describe("normalizeLayerInfo", () => {
    it("sets default label from id when missing", () => {
      const normalized = normalizeLayerInfo({ id: "body" });
      expect(normalized.label).toBe("body");
    });

    it("uses provided label", () => {
      const normalized = normalizeLayerInfo({
        id: "body",
        label: "Body Layer",
      });
      expect(normalized.label).toBe("Body Layer");
    });

    it("defaults inLeft/inRight to false when missing", () => {
      const normalized = normalizeLayerInfo({ id: "body" });
      expect(normalized.inLeft).toBe(false);
      expect(normalized.inRight).toBe(false);
    });

    it("defaults visibility to match presence", () => {
      const normalized = normalizeLayerInfo({
        id: "body",
        inLeft: true,
        inRight: false,
      });
      expect(normalized.visibleLeft).toBe(true);
      expect(normalized.visibleRight).toBe(false);
    });

    it("respects explicit visibility flags", () => {
      const normalized = normalizeLayerInfo({
        id: "body",
        inLeft: true,
        inRight: true,
        visibleLeft: false,
        visibleRight: false,
      });
      expect(normalized.visibleLeft).toBe(false);
      expect(normalized.visibleRight).toBe(false);
    });

    it("handles empty id with fallback label", () => {
      const normalized = normalizeLayerInfo({});
      expect(normalized.id).toBe("");
      expect(normalized.label).toBe("Untitled");
    });
  });
});
