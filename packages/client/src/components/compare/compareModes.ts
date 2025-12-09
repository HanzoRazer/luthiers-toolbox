// compareModes.ts
// B22.10: Compare mode types and constants

export type CompareMode =
  | "side-by-side"
  | "overlay"
  | "delta"
  | "blink"
  | "xray";

export const COMPARE_MODES: CompareMode[] = [
  "side-by-side",
  "overlay",
  "delta",
  "blink",
  "xray",
];

/**
 * Maps front-end compare modes to backend API modes.
 * Blink and X-ray reuse overlay/delta geometry but render differently on the client.
 */
export function toBackendMode(mode: CompareMode): string {
  switch (mode) {
    case "overlay":
      return "overlay";
    case "delta":
      return "delta";
    case "blink":
    case "xray":
      // Both use overlay geometry; visual effect is client-side only
      return "overlay";
    case "side-by-side":
    default:
      return "side-by-side";
  }
}

/**
 * Returns human-readable label for compare mode.
 */
export function getModeLabel(mode: CompareMode): string {
  switch (mode) {
    case "side-by-side":
      return "Side-by-side";
    case "overlay":
      return "Overlay";
    case "delta":
      return "Delta only";
    case "blink":
      return "Blink";
    case "xray":
      return "X-ray";
    default:
      return mode;
  }
}
