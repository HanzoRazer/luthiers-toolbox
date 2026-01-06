// compareBlinkBehavior.spec.ts
// B22.10: Unit tests for blink behavior hook

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { ref, nextTick } from "vue";
import { useBlinkBehavior } from "./compareBlinkBehavior";
import type { CompareMode } from "./compareModes";

describe("useBlinkBehavior", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("initializes with left phase and not blinking", () => {
    const compareMode = ref<CompareMode>("side-by-side");
    const behavior = useBlinkBehavior(compareMode);

    expect(behavior.blinkPhase.value).toBe("left");
    expect(behavior.isBlinking.value).toBe(false);
  });

  it("sets isBlinking to true when mode is blink", () => {
    const compareMode = ref<CompareMode>("blink");
    const behavior = useBlinkBehavior(compareMode);

    expect(behavior.isBlinking.value).toBe(true);
  });

  it("starts blinking automatically when mode changes to blink", async () => {
    const compareMode = ref<CompareMode>("side-by-side");
    const behavior = useBlinkBehavior(compareMode, 100);

    expect(behavior.blinkPhase.value).toBe("left");

    // Change to blink mode
    compareMode.value = "blink";

    // Wait for Vue watcher to process the change
    await nextTick();

    // Advance timer by one interval
    vi.advanceTimersByTime(100);
    expect(behavior.blinkPhase.value).toBe("right");

    // Advance timer by another interval
    vi.advanceTimersByTime(100);
    expect(behavior.blinkPhase.value).toBe("left");
  });

  it("stops blinking and resets phase when mode changes away from blink", async () => {
    const compareMode = ref<CompareMode>("blink");
    const behavior = useBlinkBehavior(compareMode, 100);

    // Advance to right phase
    vi.advanceTimersByTime(100);
    expect(behavior.blinkPhase.value).toBe("right");

    // Change mode away from blink
    compareMode.value = "overlay";

    // Wait for Vue watcher to process the change
    await nextTick();

    // Phase should reset to left
    expect(behavior.blinkPhase.value).toBe("left");

    // Timer should stop (no more changes)
    vi.advanceTimersByTime(500);
    expect(behavior.blinkPhase.value).toBe("left");
  });

  it("uses custom interval when specified", () => {
    const compareMode = ref<CompareMode>("blink");
    const behavior = useBlinkBehavior(compareMode, 500);

    // Should not toggle before interval
    vi.advanceTimersByTime(400);
    expect(behavior.blinkPhase.value).toBe("left");

    // Should toggle after interval
    vi.advanceTimersByTime(100);
    expect(behavior.blinkPhase.value).toBe("right");
  });

  it("manual startBlink does not create multiple timers", () => {
    const compareMode = ref<CompareMode>("side-by-side");
    const behavior = useBlinkBehavior(compareMode, 100);

    behavior.startBlink();
    behavior.startBlink(); // Second call should be no-op

    // Should only toggle once per interval
    vi.advanceTimersByTime(100);
    expect(behavior.blinkPhase.value).toBe("right");

    vi.advanceTimersByTime(100);
    expect(behavior.blinkPhase.value).toBe("left");
  });

  it("manual stopBlink clears timer and resets phase", () => {
    const compareMode = ref<CompareMode>("blink");
    const behavior = useBlinkBehavior(compareMode, 100);

    vi.advanceTimersByTime(100);
    expect(behavior.blinkPhase.value).toBe("right");

    behavior.stopBlink();
    expect(behavior.blinkPhase.value).toBe("left");

    // Timer should be cleared
    vi.advanceTimersByTime(500);
    expect(behavior.blinkPhase.value).toBe("left");
  });

  it("default interval is 700ms", () => {
    const compareMode = ref<CompareMode>("blink");
    const behavior = useBlinkBehavior(compareMode);

    // Should not toggle before 700ms
    vi.advanceTimersByTime(600);
    expect(behavior.blinkPhase.value).toBe("left");

    // Should toggle at 700ms
    vi.advanceTimersByTime(100);
    expect(behavior.blinkPhase.value).toBe("right");
  });
});
