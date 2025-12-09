// compareBlinkBehavior.ts
// B22.10: Blink mode behavior hook

import {
  ref,
  computed,
  watch,
  onBeforeUnmount,
  type Ref,
  type ComputedRef,
} from "vue";
import type { CompareMode } from "./compareModes";

export type BlinkPhase = "left" | "right";

export interface BlinkBehavior {
  isBlinking: ComputedRef<boolean>;
  blinkPhase: Ref<BlinkPhase>;
  startBlink: () => void;
  stopBlink: () => void;
}

/**
 * Manages blink mode behavior with automatic timer control.
 * Toggles between left and right SVG display at regular intervals.
 *
 * @param compareMode - Reactive compare mode ref
 * @param intervalMs - Blink interval in milliseconds (default: 700ms)
 * @returns BlinkBehavior interface with state and control functions
 */
export function useBlinkBehavior(
  compareMode: Ref<CompareMode>,
  intervalMs: number = 700
): BlinkBehavior {
  const blinkPhase = ref<BlinkPhase>("left");
  let blinkTimer: number | null = null;

  const isBlinking = computed(() => compareMode.value === "blink");

  function startBlink() {
    if (blinkTimer !== null) return; // Already blinking

    blinkTimer = window.setInterval(() => {
      blinkPhase.value = blinkPhase.value === "left" ? "right" : "left";
    }, intervalMs);
  }

  function stopBlink() {
    if (blinkTimer !== null) {
      window.clearInterval(blinkTimer);
      blinkTimer = null;
    }
    // Reset to neutral phase
    blinkPhase.value = "left";
  }

  // Auto-start/stop blink when mode changes
  watch(
    compareMode,
    (mode) => {
      if (mode === "blink") {
        startBlink();
      } else {
        stopBlink();
      }
    },
    { immediate: false }
  );

  // Cleanup on unmount
  onBeforeUnmount(() => {
    stopBlink();
  });

  return {
    isBlinking,
    blinkPhase,
    startBlink,
    stopBlink,
  };
}
