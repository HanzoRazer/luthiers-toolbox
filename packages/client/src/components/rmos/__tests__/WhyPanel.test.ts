/**
 * WhyPanel.test.ts
 * Unit tests for the RMOS "Why?" explainability panel
 */

import { describe, it, expect, vi } from "vitest";
import { mount } from "@vue/test-utils";
import WhyPanel from "../WhyPanel.vue";

// Mock the feasibilityRuleRegistry
vi.mock("@/lib/feasibilityRuleRegistry", () => ({
  explainRule: (ruleId: string) => {
    const rules: Record<string, any> = {
      F001: {
        rule_id: "F001",
        level: "RED",
        summary: "Invalid tool diameter",
        operator_hint: "Check tool definition",
      },
      F010: {
        rule_id: "F010",
        level: "YELLOW",
        summary: "Tool may be too large",
        operator_hint: "Consider smaller tool",
      },
      F011: {
        rule_id: "F011",
        level: "YELLOW",
        summary: "Plunge feed too high",
        operator_hint: null,
      },
    };
    return (
      rules[ruleId.toUpperCase()] ?? {
        rule_id: ruleId,
        level: "YELLOW",
        summary: "Unknown rule",
        operator_hint: null,
      }
    );
  },
}));

describe("WhyPanel", () => {
  describe("header", () => {
    it("displays risk level in header", () => {
      const w = mount(WhyPanel, { props: { riskLevel: "RED" } });
      expect(w.find(".why-header h3").text()).toContain("RED");
    });

    it("normalizes lowercase risk level", () => {
      const w = mount(WhyPanel, { props: { riskLevel: "yellow" } });
      expect(w.find(".why-header h3").text()).toContain("YELLOW");
    });

    it("handles empty risk level", () => {
      const w = mount(WhyPanel, { props: {} });
      expect(w.find(".why-header h3").exists()).toBe(true);
    });
  });

  describe("rules display", () => {
    it("displays triggered rules from rulesTriggered prop", () => {
      const w = mount(WhyPanel, {
        props: { riskLevel: "RED", rulesTriggered: ["F001"] },
      });
      expect(w.find(".why-list").exists()).toBe(true);
      expect(w.text()).toContain("F001");
      expect(w.text()).toContain("Invalid tool diameter");
    });

    it("displays triggered rules from explanation prop", () => {
      const w = mount(WhyPanel, {
        props: {
          riskLevel: "YELLOW",
          explanation: { rules_triggered: ["F010", "F011"] },
        },
      });
      expect(w.findAll(".why-item")).toHaveLength(2);
      expect(w.text()).toContain("F010");
      expect(w.text()).toContain("F011");
    });

    it("shows rule level pill with correct data-level", () => {
      const w = mount(WhyPanel, {
        props: { riskLevel: "RED", rulesTriggered: ["F001"] },
      });
      const pill = w.find(".rule-pill");
      expect(pill.attributes("data-level")).toBe("RED");
    });

    it("shows operator hint when available", () => {
      const w = mount(WhyPanel, {
        props: { riskLevel: "RED", rulesTriggered: ["F001"] },
      });
      expect(w.text()).toContain("Check tool definition");
    });

    it("hides hint element when not available", () => {
      const w = mount(WhyPanel, {
        props: { riskLevel: "YELLOW", rulesTriggered: ["F011"] },
      });
      // F011 has no operator_hint
      const items = w.findAll(".why-item");
      expect(items.length).toBe(1);
      expect(w.findAll(".rule-hint")).toHaveLength(0);
    });

    it("handles empty rules gracefully", () => {
      const w = mount(WhyPanel, {
        props: { riskLevel: "GREEN", rulesTriggered: [] },
      });
      expect(w.find(".why-list").exists()).toBe(false);
    });
  });

  describe("summary text", () => {
    it("shows blocking summary for RED rules", () => {
      const w = mount(WhyPanel, {
        props: { riskLevel: "RED", rulesTriggered: ["F001"] },
      });
      expect(w.find(".why-summary").text()).toContain("blocking");
    });

    it("shows warning summary for YELLOW rules", () => {
      const w = mount(WhyPanel, {
        props: { riskLevel: "YELLOW", rulesTriggered: ["F010"] },
      });
      expect(w.find(".why-summary").text()).toContain("warning");
    });

    it("shows count of rules", () => {
      const w = mount(WhyPanel, {
        props: { riskLevel: "YELLOW", rulesTriggered: ["F010", "F011"] },
      });
      expect(w.find(".why-summary").text()).toContain("2");
    });
  });

  describe("explanation text", () => {
    it("displays explanation.text when provided", () => {
      const w = mount(WhyPanel, {
        props: {
          explanation: { text: "This operation is unsafe because..." },
        },
      });
      expect(w.find(".why-text").text()).toBe(
        "This operation is unsafe because..."
      );
    });

    it("hides why-text when no explanation provided", () => {
      const w = mount(WhyPanel, { props: { riskLevel: "GREEN" } });
      expect(w.find(".why-text").exists()).toBe(false);
    });
  });

  describe("override hints", () => {
    it("shows override hint for YELLOW when showOverrideHint is true", () => {
      const w = mount(WhyPanel, {
        props: { riskLevel: "YELLOW", showOverrideHint: true },
      });
      expect(w.text()).toContain("Operator Pack requires an override");
    });

    it("hides override hint when riskLevel is not YELLOW", () => {
      const w = mount(WhyPanel, {
        props: { riskLevel: "RED", showOverrideHint: true },
      });
      expect(w.text()).not.toContain("Operator Pack requires an override");
    });

    it("shows override recorded message when hasOverride is true", () => {
      const w = mount(WhyPanel, {
        props: { riskLevel: "YELLOW", hasOverride: true },
      });
      expect(w.text()).toContain("Override recorded");
    });

    it("override recorded hint has success styling", () => {
      const w = mount(WhyPanel, {
        props: { riskLevel: "YELLOW", hasOverride: true },
      });
      const hint = w.find(".why-hint-ok");
      expect(hint.exists()).toBe(true);
    });
  });
});
