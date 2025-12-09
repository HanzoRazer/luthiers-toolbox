// compareLayerVisibility.ts
// B22.11: Composable for managing layer visibility state and CSS injection

import { computed, type Ref } from "vue";
import {
  buildHiddenLayerCss,
  type LayerInfo,
  type LayerId,
} from "./compareLayers";

export interface LayerVisibility {
  hiddenLeftLayers: Ref<Set<LayerId>>;
  hiddenRightLayers: Ref<Set<LayerId>>;
  leftLayerCss: Ref<string>;
  rightLayerCss: Ref<string>;
}

/**
 * Composable for managing layer visibility and generating CSS to hide layers.
 *
 * @param layers - Reactive ref containing layer info array
 * @returns Computed sets of hidden layers and CSS strings for injection
 */
export function useLayerVisibility(layers: Ref<LayerInfo[]>): LayerVisibility {
  // Compute hidden layers for left side
  const hiddenLeftLayers = computed(() => {
    return new Set(layers.value.filter((l) => !l.visibleLeft).map((l) => l.id));
  });

  // Compute hidden layers for right side
  const hiddenRightLayers = computed(() => {
    return new Set(
      layers.value.filter((l) => !l.visibleRight).map((l) => l.id)
    );
  });

  // Build CSS for left pane
  const leftLayerCss = computed(() => {
    return buildHiddenLayerCss(hiddenLeftLayers.value);
  });

  // Build CSS for right pane
  const rightLayerCss = computed(() => {
    return buildHiddenLayerCss(hiddenRightLayers.value);
  });

  return {
    hiddenLeftLayers,
    hiddenRightLayers,
    leftLayerCss,
    rightLayerCss,
  };
}

/**
 * Helper to inject layer visibility CSS into SVG container.
 * Returns a style element string for insertion into SVG <defs>.
 *
 * @param css - CSS string to inject
 * @returns Style element markup or empty string if no CSS
 */
export function createLayerStyleElement(css: string): string {
  if (!css) return "";
  return `<style type="text/css">${css}</style>`;
}
