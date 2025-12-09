// compareXrayBehavior.spec.ts
// B22.10: Unit tests for X-ray behavior hook

import { describe, it, expect } from "vitest";
import { ref } from "vue";
import { useXrayBehavior } from "./compareXrayBehavior";
import type { CompareMode } from "./compareModes";

describe("useXrayBehavior", () => {
  it("initializes with 0.5 mix and not xray mode", () => {
    const compareMode = ref<CompareMode>("side-by-side");
    const behavior = useXrayBehavior(compareMode);

    expect(behavior.xrayMix.value).toBe(0.5);
    expect(behavior.isXray.value).toBe(false);
  });

  it("sets isXray to true when mode is xray", () => {
    const compareMode = ref<CompareMode>("xray");
    const behavior = useXrayBehavior(compareMode);

    expect(behavior.isXray.value).toBe(true);
  });

  it("computes correct opacities at mix = 0.0 (full left)", () => {
    const compareMode = ref<CompareMode>("xray");
    const behavior = useXrayBehavior(compareMode, 0.0);

    expect(behavior.leftOpacity.value).toBe(1.0);
    expect(behavior.rightOpacity.value).toBe(0.0);
  });

  it("computes correct opacities at mix = 1.0 (full right)", () => {
    const compareMode = ref<CompareMode>("xray");
    const behavior = useXrayBehavior(compareMode, 1.0);

    expect(behavior.leftOpacity.value).toBe(0.0);
    expect(behavior.rightOpacity.value).toBe(1.0);
  });

  it("computes correct opacities at mix = 0.5 (equal blend)", () => {
    const compareMode = ref<CompareMode>("xray");
    const behavior = useXrayBehavior(compareMode, 0.5);

    expect(behavior.leftOpacity.value).toBe(0.5);
    expect(behavior.rightOpacity.value).toBe(0.5);
  });

  it("opacities update reactively when mix changes", () => {
    const compareMode = ref<CompareMode>("xray");
    const behavior = useXrayBehavior(compareMode, 0.5);

    expect(behavior.leftOpacity.value).toBe(0.5);
    expect(behavior.rightOpacity.value).toBe(0.5);

    // Slide toward right
    behavior.xrayMix.value = 0.75;
    expect(behavior.leftOpacity.value).toBe(0.25);
    expect(behavior.rightOpacity.value).toBe(0.75);

    // Slide toward left
    behavior.xrayMix.value = 0.25;
    expect(behavior.leftOpacity.value).toBe(0.75);
    expect(behavior.rightOpacity.value).toBe(0.25);
  });

  it("clamps initial mix below 0 to 0", () => {
    const compareMode = ref<CompareMode>("xray");
    const behavior = useXrayBehavior(compareMode, -0.5);

    expect(behavior.xrayMix.value).toBe(0);
  });

  it("clamps initial mix above 1 to 1", () => {
    const compareMode = ref<CompareMode>("xray");
    const behavior = useXrayBehavior(compareMode, 1.5);

    expect(behavior.xrayMix.value).toBe(1);
  });

  it("opacities sum to 1.0 at any mix value", () => {
    const compareMode = ref<CompareMode>("xray");
    const behavior = useXrayBehavior(compareMode);

    const testValues = [0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0];

    testValues.forEach((mix) => {
      behavior.xrayMix.value = mix;
      const sum = behavior.leftOpacity.value + behavior.rightOpacity.value;
      expect(sum).toBeCloseTo(1.0, 10);
    });
  });

  it("uses custom initial mix when specified", () => {
    const compareMode = ref<CompareMode>("xray");
    const behavior = useXrayBehavior(compareMode, 0.3);

    expect(behavior.xrayMix.value).toBe(0.3);
    expect(behavior.leftOpacity.value).toBe(0.7);
    expect(behavior.rightOpacity.value).toBe(0.3);
  });
});
