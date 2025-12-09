// compareLayers.ts
// B22.11: Layer-aware compare model

export type LayerId = string;

/**
 * Layer information for compare mode.
 * Tracks presence in left/right and visibility toggles.
 */
export type LayerInfo = {
  id: LayerId;
  label: string;

  // Presence flags: does this layer exist in each side?
  inLeft: boolean;
  inRight: boolean;

  // Visibility flags: user-controlled toggles
  visibleLeft: boolean;
  visibleRight: boolean;
};

/**
 * Summary of layer differences between left and right.
 */
export type LayerDiffSummary = {
  addedLeftOnly: LayerId[]; // exists only in left
  addedRightOnly: LayerId[]; // exists only in right
  common: LayerId[]; // in both
};

/**
 * Builds layer diff summary from layer list.
 */
export function buildLayerDiffSummary(layers: LayerInfo[]): LayerDiffSummary {
  const addedLeftOnly: LayerId[] = [];
  const addedRightOnly: LayerId[] = [];
  const common: LayerId[] = [];

  for (const layer of layers) {
    if (layer.inLeft && !layer.inRight) {
      addedLeftOnly.push(layer.id);
    } else if (!layer.inLeft && layer.inRight) {
      addedRightOnly.push(layer.id);
    } else if (layer.inLeft && layer.inRight) {
      common.push(layer.id);
    }
  }

  return { addedLeftOnly, addedRightOnly, common };
}

/**
 * Checks if a layer is mismatched (presence or visibility differs).
 */
export function isLayerMismatched(layer: LayerInfo): boolean {
  // Presence mismatch: exists on one side only
  const presenceMismatch = layer.inLeft !== layer.inRight;

  // Visibility mismatch: exists but hidden on at least one side
  const visibilityMismatch =
    (layer.inLeft && !layer.visibleLeft) ||
    (layer.inRight && !layer.visibleRight);

  return presenceMismatch || visibilityMismatch;
}

/**
 * Simple CSS escape for layer IDs used in selectors.
 * Escapes backslashes, quotes, and other special characters.
 */
export function cssEscapeLayerId(id: string): string {
  // Basic escape: backslashes and quotes
  return id
    .replace(/\\/g, "\\\\")
    .replace(/"/g, '\\"')
    .replace(/'/g, "\\'")
    .replace(/\n/g, "\\n")
    .replace(/\r/g, "\\r");
}

/**
 * Builds CSS rules to hide layers by ID.
 * Returns empty string if no layers to hide.
 *
 * @param hiddenLayerIds - Set of layer IDs to hide
 * @returns CSS string like "g#layer1, g#layer2 { display: none !important; }"
 */
export function buildHiddenLayerCss(hiddenLayerIds: Set<LayerId>): string {
  if (hiddenLayerIds.size === 0) return "";

  const selectors = Array.from(hiddenLayerIds).map(
    (id) =>
      `g#${cssEscapeLayerId(id)}, g[data-layer-id="${cssEscapeLayerId(id)}"]`
  );

  return `${selectors.join(", ")} { display: none !important; }`;
}

/**
 * Normalizes layer data from backend response.
 * Ensures visibility flags are set properly.
 */
export function normalizeLayerInfo(layer: Partial<LayerInfo>): LayerInfo {
  return {
    id: layer.id || "",
    label: layer.label || layer.id || "Untitled",
    inLeft: layer.inLeft ?? false,
    inRight: layer.inRight ?? false,
    // Default visibility: visible if present
    visibleLeft:
      typeof layer.visibleLeft === "boolean"
        ? layer.visibleLeft
        : layer.inLeft ?? false,
    visibleRight:
      typeof layer.visibleRight === "boolean"
        ? layer.visibleRight
        : layer.inRight ?? false,
  };
}
