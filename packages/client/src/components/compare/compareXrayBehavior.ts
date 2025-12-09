// compareXrayBehavior.ts
// B22.10: X-ray mode behavior hook

import { ref, computed, type Ref, type ComputedRef } from "vue";
import type { CompareMode } from "./compareModes";

export interface XrayBehavior {
  isXray: ComputedRef<boolean>;
  xrayMix: Ref<number>;
  leftOpacity: ComputedRef<number>;
  rightOpacity: ComputedRef<number>;
}

/**
 * Manages X-ray mode behavior with crossfade opacity control.
 * Allows continuous blending between left and right SVG displays.
 *
 * @param compareMode - Reactive compare mode ref
 * @param initialMix - Initial mix value (0.0 = left only, 1.0 = right only, default: 0.5)
 * @returns XrayBehavior interface with state and computed opacities
 */
export function useXrayBehavior(
  compareMode: Ref<CompareMode>,
  initialMix: number = 0.5
): XrayBehavior {
  // Clamp initial mix to valid range
  const xrayMix = ref(Math.max(0, Math.min(1, initialMix)));

  const isXray = computed(() => compareMode.value === "xray");

  // Left opacity: 1.0 (full) when mix = 0.0, 0.0 (transparent) when mix = 1.0
  const leftOpacity = computed(() => 1 - xrayMix.value);

  // Right opacity: 0.0 (transparent) when mix = 0.0, 1.0 (full) when mix = 1.0
  const rightOpacity = computed(() => xrayMix.value);

  return {
    isXray,
    xrayMix,
    leftOpacity,
    rightOpacity,
  };
}
