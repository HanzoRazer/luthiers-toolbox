// compareLayerVisibility.spec.ts
// B22.11: Unit tests for layer visibility composable

import { describe, it, expect } from "vitest";
import { ref } from "vue";
import {
  useLayerVisibility,
  createLayerStyleElement,
} from "./compareLayerVisibility";
import type { LayerInfo } from "./compareLayers";

describe("compareLayerVisibility", () => {
  describe("useLayerVisibility", () => {
    it("computes empty hidden sets when all layers visible", () => {
      const layers = ref<LayerInfo[]>([
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
      ]);

      const { hiddenLeftLayers, hiddenRightLayers } =
        useLayerVisibility(layers);

      expect(hiddenLeftLayers.value.size).toBe(0);
      expect(hiddenRightLayers.value.size).toBe(0);
    });

    it("identifies hidden left layers", () => {
      const layers = ref<LayerInfo[]>([
        {
          id: "body",
          label: "Body",
          inLeft: true,
          inRight: true,
          visibleLeft: false, // Hidden on left
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
      ]);

      const { hiddenLeftLayers } = useLayerVisibility(layers);

      expect(hiddenLeftLayers.value.has("body")).toBe(true);
      expect(hiddenLeftLayers.value.has("neck")).toBe(false);
    });

    it("identifies hidden right layers", () => {
      const layers = ref<LayerInfo[]>([
        {
          id: "inlay",
          label: "Inlay",
          inLeft: true,
          inRight: true,
          visibleLeft: true,
          visibleRight: false, // Hidden on right
        },
        {
          id: "bridge",
          label: "Bridge",
          inLeft: true,
          inRight: true,
          visibleLeft: true,
          visibleRight: true,
        },
      ]);

      const { hiddenRightLayers } = useLayerVisibility(layers);

      expect(hiddenRightLayers.value.has("inlay")).toBe(true);
      expect(hiddenRightLayers.value.has("bridge")).toBe(false);
    });

    it("builds CSS for hidden layers", () => {
      const layers = ref<LayerInfo[]>([
        {
          id: "body",
          label: "Body",
          inLeft: true,
          inRight: true,
          visibleLeft: false,
          visibleRight: true,
        },
      ]);

      const { leftLayerCss, rightLayerCss } = useLayerVisibility(layers);

      expect(leftLayerCss.value).toContain("g#body");
      expect(leftLayerCss.value).toContain("display: none !important");
      expect(rightLayerCss.value).toBe(""); // Right is visible
    });

    it("updates reactively when layer visibility changes", () => {
      const layers = ref<LayerInfo[]>([
        {
          id: "body",
          label: "Body",
          inLeft: true,
          inRight: true,
          visibleLeft: true,
          visibleRight: true,
        },
      ]);

      const { hiddenLeftLayers, leftLayerCss } = useLayerVisibility(layers);

      // Initially visible
      expect(hiddenLeftLayers.value.size).toBe(0);
      expect(leftLayerCss.value).toBe("");

      // Hide layer
      layers.value[0].visibleLeft = false;

      // Should update reactively
      expect(hiddenLeftLayers.value.has("body")).toBe(true);
      expect(leftLayerCss.value).toContain("g#body");
    });

    it("handles empty layer list", () => {
      const layers = ref<LayerInfo[]>([]);

      const {
        hiddenLeftLayers,
        hiddenRightLayers,
        leftLayerCss,
        rightLayerCss,
      } = useLayerVisibility(layers);

      expect(hiddenLeftLayers.value.size).toBe(0);
      expect(hiddenRightLayers.value.size).toBe(0);
      expect(leftLayerCss.value).toBe("");
      expect(rightLayerCss.value).toBe("");
    });

    it("handles multiple hidden layers on same side", () => {
      const layers = ref<LayerInfo[]>([
        {
          id: "body",
          label: "Body",
          inLeft: true,
          inRight: true,
          visibleLeft: false,
          visibleRight: true,
        },
        {
          id: "neck",
          label: "Neck",
          inLeft: true,
          inRight: true,
          visibleLeft: false,
          visibleRight: true,
        },
      ]);

      const { hiddenLeftLayers, leftLayerCss } = useLayerVisibility(layers);

      expect(hiddenLeftLayers.value.size).toBe(2);
      expect(leftLayerCss.value).toContain("g#body");
      expect(leftLayerCss.value).toContain("g#neck");
    });
  });

  describe("createLayerStyleElement", () => {
    it("wraps CSS in style element", () => {
      const css = "g#body { display: none !important; }";
      const styleElement = createLayerStyleElement(css);

      expect(styleElement).toContain('<style type="text/css">');
      expect(styleElement).toContain(css);
      expect(styleElement).toContain("</style>");
    });

    it("returns empty string for empty CSS", () => {
      const styleElement = createLayerStyleElement("");
      expect(styleElement).toBe("");
    });

    it("preserves complex CSS", () => {
      const css =
        'g#body, g#neck, g[data-layer-id="inlay"] { display: none !important; }';
      const styleElement = createLayerStyleElement(css);

      expect(styleElement).toContain(css);
    });
  });
});
