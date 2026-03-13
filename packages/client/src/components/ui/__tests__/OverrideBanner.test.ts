/**
 * OverrideBanner.test.ts
 * Unit tests for the RMOS override notification banner
 */

import { describe, it, expect } from "vitest";
import { mount } from "@vue/test-utils";
import OverrideBanner from "../OverrideBanner.vue";

describe("OverrideBanner", () => {
  describe("visibility", () => {
    it("is hidden when no override props provided", () => {
      const w = mount(OverrideBanner, { props: {} });
      expect(w.find(".override-banner").exists()).toBe(false);
    });

    it("is visible when reason is provided", () => {
      const w = mount(OverrideBanner, {
        props: { reason: "Operator approved" },
      });
      expect(w.find(".override-banner").exists()).toBe(true);
    });

    it("is visible when overrideArtifact is provided", () => {
      const w = mount(OverrideBanner, {
        props: { overrideArtifact: { sha256: "abc123def456" } },
      });
      expect(w.find(".override-banner").exists()).toBe(true);
    });

    it("is hidden when reason is null", () => {
      const w = mount(OverrideBanner, { props: { reason: null } });
      expect(w.find(".override-banner").exists()).toBe(false);
    });

    it("is hidden when reason is empty string", () => {
      const w = mount(OverrideBanner, { props: { reason: "" } });
      expect(w.find(".override-banner").exists()).toBe(false);
    });
  });

  describe("content", () => {
    it("displays 'Override Applied' title", () => {
      const w = mount(OverrideBanner, { props: { reason: "Test" } });
      expect(w.find(".override-title").text()).toBe("Override Applied");
    });

    it("displays the provided reason", () => {
      const reason = "Supervisor approved after visual inspection";
      const w = mount(OverrideBanner, { props: { reason } });
      expect(w.find(".override-reason").text()).toBe(reason);
    });

    it("displays default message when only artifact is provided", () => {
      const w = mount(OverrideBanner, {
        props: { overrideArtifact: { sha256: "abc123" } },
      });
      expect(w.find(".override-reason").text()).toContain("see artifact");
    });

    it("displays lightning bolt icon", () => {
      const w = mount(OverrideBanner, { props: { reason: "Test" } });
      expect(w.find(".override-icon").text()).toBe("⚡");
    });
  });

  describe("artifact SHA display", () => {
    it("displays truncated SHA when artifact has sha256", () => {
      const sha = "abc123def456ghi789jkl012mno345";
      const w = mount(OverrideBanner, {
        props: { overrideArtifact: { sha256: sha } },
      });
      expect(w.find(".override-meta").exists()).toBe(true);
      expect(w.find(".override-meta code").text()).toContain("abc123def456");
    });

    it("hides SHA display when artifact has no sha256", () => {
      const w = mount(OverrideBanner, {
        props: { reason: "Test", overrideArtifact: {} },
      });
      expect(w.find(".override-meta").exists()).toBe(false);
    });

    it("shows SHA with ellipsis truncation", () => {
      const sha = "abcdefghijklmnopqrstuvwxyz0123456789";
      const w = mount(OverrideBanner, {
        props: { overrideArtifact: { sha256: sha } },
      });
      // First 12 chars + ellipsis
      expect(w.find(".override-meta").text()).toContain("abcdefghijkl");
    });
  });

  describe("accessibility", () => {
    it("has role=alert for screen readers", () => {
      const w = mount(OverrideBanner, { props: { reason: "Test" } });
      expect(w.find(".override-banner").attributes("role")).toBe("alert");
    });

    it("icon has aria-hidden for accessibility", () => {
      const w = mount(OverrideBanner, { props: { reason: "Test" } });
      expect(w.find(".override-icon").attributes("aria-hidden")).toBe("true");
    });
  });
});
