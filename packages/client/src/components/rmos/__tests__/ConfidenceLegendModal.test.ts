/**
 * ConfidenceLegendModal.test.ts
 * Bundle 09: Unit tests for confidence legend modal
 */

import { describe, it, expect } from "vitest";
import { mount } from "@vue/test-utils";
import ConfidenceLegendModal from "../ConfidenceLegendModal.vue";

describe("ConfidenceLegendModal", () => {
  it("renders legend button", () => {
    const w = mount(ConfidenceLegendModal);
    expect(w.text()).toContain("?");
  });

  it("opens modal on click", async () => {
    const w = mount(ConfidenceLegendModal);
    expect(w.find(".modal-backdrop").exists()).toBe(false);

    await w.find("button.legend-btn").trigger("click");

    expect(w.find(".modal-backdrop").exists()).toBe(true);
    expect(w.text()).toContain("Confidence legend");
    expect(w.text()).toContain("HIGH");
    expect(w.text()).toContain("MED");
    expect(w.text()).toContain("LOW");
  });

  it("closes modal on close button click", async () => {
    const w = mount(ConfidenceLegendModal);
    await w.find("button.legend-btn").trigger("click");
    expect(w.find(".modal-backdrop").exists()).toBe(true);

    await w.find("button.close-btn").trigger("click");
    expect(w.find(".modal-backdrop").exists()).toBe(false);
  });

  it("closes modal on OK button click", async () => {
    const w = mount(ConfidenceLegendModal);
    await w.find("button.legend-btn").trigger("click");
    expect(w.find(".modal-backdrop").exists()).toBe(true);

    await w.find("button.ok-btn").trigger("click");
    expect(w.find(".modal-backdrop").exists()).toBe(false);
  });

  it("displays trend explanations", async () => {
    const w = mount(ConfidenceLegendModal);
    await w.find("button.legend-btn").trigger("click");

    expect(w.text()).toContain("↑");
    expect(w.text()).toContain("→");
    expect(w.text()).toContain("↓");
    expect(w.text()).toContain("Improved vs previous compare");
  });
});
