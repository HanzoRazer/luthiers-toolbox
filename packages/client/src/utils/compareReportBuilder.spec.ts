// compareReportBuilder.spec.ts
// B22.12: Unit tests for diff report builder

import { describe, it, expect } from "vitest";
import {
  buildDiffReportPayload,
  buildDiffReportHtml,
  type CompareMode,
  type CompareLayerInfo,
  type CompareResultJson,
} from "./compareReportBuilder";

describe("compareReportBuilder", () => {
  describe("buildDiffReportPayload", () => {
    it("builds payload with basic data", () => {
      const result: CompareResultJson = {
        fullBBox: { minX: 0, minY: 0, maxX: 100, maxY: 100 },
        diffBBox: { minX: 10, minY: 10, maxX: 90, maxY: 90 },
      };

      const layers: CompareLayerInfo[] = [
        {
          id: "body",
          label: "Body",
          inLeft: true,
          inRight: true,
          enabled: true,
        },
        {
          id: "neck",
          label: "Neck",
          inLeft: true,
          inRight: false,
          enabled: false,
        },
      ];

      const payload = buildDiffReportPayload({
        mode: "overlay",
        diffDisabledReason: null,
        result,
        layers,
      });

      expect(payload.mode).toBe("overlay");
      expect(payload.diffDisabledReason).toBeNull();
      expect(payload.layers).toHaveLength(2);
      expect(payload.layers[0].id).toBe("body");
      expect(payload.layers[0].enabled).toBe(true);
      expect(payload.bbox).toEqual(result.diffBBox);
    });

    it("uses fullBBox when diffBBox is null", () => {
      const result: CompareResultJson = {
        fullBBox: { minX: 0, minY: 0, maxX: 200, maxY: 150 },
        diffBBox: null,
      };

      const payload = buildDiffReportPayload({
        mode: "side-by-side",
        diffDisabledReason: null,
        result,
        layers: [],
      });

      expect(payload.bbox).toEqual(result.fullBBox);
    });

    it("handles null result", () => {
      const payload = buildDiffReportPayload({
        mode: "delta",
        diffDisabledReason: "No SVG loaded",
        result: null,
        layers: [],
      });

      expect(payload.bbox).toBeNull();
      expect(payload.diffDisabledReason).toBe("No SVG loaded");
    });

    it("includes warnings when provided", () => {
      const payload = buildDiffReportPayload({
        mode: "overlay",
        diffDisabledReason: null,
        warnings: ["Arc tolerance exceeded", "Layer mismatch detected"],
        result: null,
        layers: [],
      });

      expect(payload.warnings).toHaveLength(2);
      expect(payload.warnings[0]).toBe("Arc tolerance exceeded");
    });

    it("includes screenshot data URL", () => {
      const dataUrl = "data:image/svg+xml;base64,PHN2Zz48L3N2Zz4=";

      const payload = buildDiffReportPayload({
        mode: "blink",
        diffDisabledReason: null,
        result: null,
        layers: [],
        screenshotDataUrl: dataUrl,
      });

      expect(payload.screenshotDataUrl).toBe(dataUrl);
    });

    it("sets generatedAt timestamp", () => {
      const before = new Date().toISOString();

      const payload = buildDiffReportPayload({
        mode: "xray",
        diffDisabledReason: null,
        result: null,
        layers: [],
      });

      const after = new Date().toISOString();

      expect(payload.generatedAt).toMatch(/^\d{4}-\d{2}-\d{2}T/);
      expect(payload.generatedAt >= before).toBe(true);
      expect(payload.generatedAt <= after).toBe(true);
    });

    it("normalizes layer data", () => {
      const layers: CompareLayerInfo[] = [
        { id: "layer1" }, // Minimal layer
        {
          id: "layer2",
          label: "Custom Label",
          inLeft: false,
          inRight: true,
          hasDiff: true,
          enabled: true,
        },
      ];

      const payload = buildDiffReportPayload({
        mode: "overlay",
        diffDisabledReason: null,
        result: null,
        layers,
      });

      // Minimal layer uses id as label
      expect(payload.layers[0].label).toBe("layer1");
      expect(payload.layers[0].inLeft).toBe(false);
      expect(payload.layers[0].inRight).toBe(false);

      // Full layer preserves data
      expect(payload.layers[1].label).toBe("Custom Label");
      expect(payload.layers[1].inRight).toBe(true);
      expect(payload.layers[1].hasDiff).toBe(true);
    });
  });

  describe("buildDiffReportHtml", () => {
    it("generates valid HTML structure", () => {
      const payload = buildDiffReportPayload({
        mode: "overlay",
        diffDisabledReason: null,
        result: { fullBBox: { minX: 0, minY: 0, maxX: 100, maxY: 100 } },
        layers: [],
      });

      const html = buildDiffReportHtml(payload);

      expect(html).toContain("<!doctype html>");
      expect(html).toContain("<html");
      expect(html).toContain("</html>");
      expect(html).toContain("<head>");
      expect(html).toContain("<body>");
      expect(html).toContain("CompareLab Diff Report");
    });

    it("includes mode badge", () => {
      const payload = buildDiffReportPayload({
        mode: "delta",
        diffDisabledReason: null,
        result: null,
        layers: [],
      });

      const html = buildDiffReportHtml(payload);

      expect(html).toContain("delta");
      expect(html).toContain("badge-mode");
    });

    it("shows diff disabled warning when present", () => {
      const payload = buildDiffReportPayload({
        mode: "overlay",
        diffDisabledReason: "No baseline selected",
        result: null,
        layers: [],
      });

      const html = buildDiffReportHtml(payload);

      expect(html).toContain("Diff Disabled");
      expect(html).toContain("No baseline selected");
      expect(html).toContain("warning");
    });

    it("shows success message when diff active", () => {
      const payload = buildDiffReportPayload({
        mode: "overlay",
        diffDisabledReason: null,
        result: { fullBBox: { minX: 0, minY: 0, maxX: 100, maxY: 100 } },
        layers: [],
      });

      const html = buildDiffReportHtml(payload);

      expect(html).toContain("Diff active");
      expect(html).toContain("success");
    });

    it("includes bounding box coordinates", () => {
      const payload = buildDiffReportPayload({
        mode: "overlay",
        diffDisabledReason: null,
        result: {
          fullBBox: { minX: 10.5, minY: 20.75, maxX: 110.5, maxY: 120.75 },
        },
        layers: [],
      });

      const html = buildDiffReportHtml(payload);

      expect(html).toContain("10.50");
      expect(html).toContain("20.75");
      expect(html).toContain("110.50");
      expect(html).toContain("120.75");
    });

    it("renders layer table with data", () => {
      const layers: CompareLayerInfo[] = [
        {
          id: "body",
          label: "Body",
          inLeft: true,
          inRight: true,
          hasDiff: false,
          enabled: true,
        },
        {
          id: "inlay",
          label: "Inlay",
          inLeft: false,
          inRight: true,
          hasDiff: true,
          enabled: true,
        },
      ];

      const payload = buildDiffReportPayload({
        mode: "overlay",
        diffDisabledReason: null,
        result: null,
        layers,
      });

      const html = buildDiffReportHtml(payload);

      expect(html).toContain("<table>");
      expect(html).toContain("Body");
      expect(html).toContain("Inlay");
      expect(html).toContain("✓"); // Checkmarks for enabled/present
      expect(html).toContain("–"); // Dashes for not present
    });

    it("includes screenshot when provided", () => {
      const dataUrl = "data:image/svg+xml;base64,test123";

      const payload = buildDiffReportPayload({
        mode: "overlay",
        diffDisabledReason: null,
        result: null,
        layers: [],
        screenshotDataUrl: dataUrl,
      });

      const html = buildDiffReportHtml(payload);

      expect(html).toContain(`src="${dataUrl}"`);
      expect(html).toContain('alt="Compare screenshot"');
    });

    it("shows no screenshot message when not provided", () => {
      const payload = buildDiffReportPayload({
        mode: "overlay",
        diffDisabledReason: null,
        result: null,
        layers: [],
      });

      const html = buildDiffReportHtml(payload);

      expect(html).toContain("no screenshot captured");
    });

    it("escapes HTML special characters", () => {
      const layers: CompareLayerInfo[] = [
        { id: "layer<script>", label: "Layer with <script>", enabled: true },
      ];

      const payload = buildDiffReportPayload({
        mode: "overlay",
        diffDisabledReason: "Error: <div>test</div>",
        warnings: ["Warning with <tags>"],
        result: null,
        layers,
      });

      const html = buildDiffReportHtml(payload);

      expect(html).not.toContain("<script>");
      expect(html).toContain("&lt;script&gt;");
      expect(html).toContain("&lt;div&gt;");
      expect(html).toContain("&lt;tags&gt;");
    });

    it("includes warnings list", () => {
      const payload = buildDiffReportPayload({
        mode: "overlay",
        diffDisabledReason: null,
        warnings: ["Arc tolerance exceeded", "Layer count mismatch"],
        result: null,
        layers: [],
      });

      const html = buildDiffReportHtml(payload);

      expect(html).toContain("<ul>");
      expect(html).toContain("Arc tolerance exceeded");
      expect(html).toContain("Layer count mismatch");
    });

    it("shows 'None' when no warnings", () => {
      const payload = buildDiffReportPayload({
        mode: "overlay",
        diffDisabledReason: null,
        result: null,
        layers: [],
      });

      const html = buildDiffReportHtml(payload);

      expect(html).toContain("None");
    });
  });
});
