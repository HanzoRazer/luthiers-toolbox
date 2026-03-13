/**
 * RiskBadge.test.ts
 * Unit tests for the RMOS risk level badge component
 */

import { describe, it, expect } from "vitest";
import { mount } from "@vue/test-utils";
import RiskBadge from "../RiskBadge.vue";

describe("RiskBadge", () => {
  describe("rendering", () => {
    it("renders with default props (UNKNOWN)", () => {
      const w = mount(RiskBadge);
      expect(w.text()).toContain("UNKNOWN");
      expect(w.find(".risk-badge").classes()).toContain("unknown");
    });

    it("renders GREEN level", () => {
      const w = mount(RiskBadge, { props: { level: "GREEN" } });
      expect(w.text()).toContain("GREEN");
      expect(w.find(".risk-badge").classes()).toContain("green");
    });

    it("renders YELLOW level", () => {
      const w = mount(RiskBadge, { props: { level: "YELLOW" } });
      expect(w.text()).toContain("YELLOW");
      expect(w.find(".risk-badge").classes()).toContain("yellow");
    });

    it("renders RED level", () => {
      const w = mount(RiskBadge, { props: { level: "RED" } });
      expect(w.text()).toContain("RED");
      expect(w.find(".risk-badge").classes()).toContain("red");
    });

    it("normalizes lowercase level to uppercase", () => {
      const w = mount(RiskBadge, { props: { level: "green" } });
      expect(w.text()).toContain("GREEN");
      expect(w.find(".risk-badge").classes()).toContain("green");
    });

    it("handles null level as UNKNOWN", () => {
      const w = mount(RiskBadge, { props: { level: null } });
      expect(w.text()).toContain("UNKNOWN");
    });
  });

  describe("icons", () => {
    it("shows checkmark icon for GREEN", () => {
      const w = mount(RiskBadge, { props: { level: "GREEN", showIcon: true } });
      expect(w.find(".icon").text()).toBe("✓");
    });

    it("shows warning icon for YELLOW", () => {
      const w = mount(RiskBadge, { props: { level: "YELLOW", showIcon: true } });
      expect(w.find(".icon").text()).toBe("⚠");
    });

    it("shows blocked icon for RED", () => {
      const w = mount(RiskBadge, { props: { level: "RED", showIcon: true } });
      expect(w.find(".icon").text()).toBe("⛔");
    });

    it("shows question mark for UNKNOWN", () => {
      const w = mount(RiskBadge, { props: { level: "UNKNOWN", showIcon: true } });
      expect(w.find(".icon").text()).toBe("?");
    });

    it("hides icon when showIcon is false", () => {
      const w = mount(RiskBadge, { props: { level: "GREEN", showIcon: false } });
      expect(w.find(".icon").exists()).toBe(false);
    });

    it("icon has aria-hidden for accessibility", () => {
      const w = mount(RiskBadge, { props: { level: "GREEN", showIcon: true } });
      expect(w.find(".icon").attributes("aria-hidden")).toBe("true");
    });
  });

  describe("tooltips", () => {
    it("shows correct tooltip for GREEN", () => {
      const w = mount(RiskBadge, { props: { level: "GREEN" } });
      expect(w.find(".risk-badge").attributes("title")).toBe(
        "Safe to run under current parameters"
      );
    });

    it("shows correct tooltip for YELLOW", () => {
      const w = mount(RiskBadge, { props: { level: "YELLOW" } });
      expect(w.find(".risk-badge").attributes("title")).toBe(
        "Review warnings before running"
      );
    });

    it("shows correct tooltip for RED", () => {
      const w = mount(RiskBadge, { props: { level: "RED" } });
      expect(w.find(".risk-badge").attributes("title")).toContain("Blocked");
    });

    it("shows correct tooltip for UNKNOWN", () => {
      const w = mount(RiskBadge, { props: { level: "UNKNOWN" } });
      expect(w.find(".risk-badge").attributes("title")).toBe(
        "Risk level not determined"
      );
    });
  });

  describe("sizes", () => {
    it("renders sm size", () => {
      const w = mount(RiskBadge, { props: { size: "sm" } });
      expect(w.find(".risk-badge").classes()).toContain("sm");
    });

    it("renders md size by default", () => {
      const w = mount(RiskBadge);
      expect(w.find(".risk-badge").classes()).toContain("md");
    });

    it("renders lg size", () => {
      const w = mount(RiskBadge, { props: { size: "lg" } });
      expect(w.find(".risk-badge").classes()).toContain("lg");
    });
  });

  describe("accessibility", () => {
    it("has role=status for screen readers", () => {
      const w = mount(RiskBadge);
      expect(w.find(".risk-badge").attributes("role")).toBe("status");
    });
  });
});
