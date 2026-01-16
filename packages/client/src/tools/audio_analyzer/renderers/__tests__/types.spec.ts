/**
 * @vitest-environment jsdom
 *
 * Tests for audio_analyzer/renderers/types.ts
 * Validates kind → category mapping matches contract.
 */
import { describe, it, expect } from "vitest";
import { kindToCategory, type RendererCategory } from "../types";

/**
 * Canonical kind vocabulary from viewer_pack_v1 schema.
 * Source: contracts/viewer_pack_v1.schema.json → $defs.fileEntry.properties.kind.enum
 */
const SCHEMA_KINDS = [
  "audio_raw",
  "spectrum_csv",
  "analysis_peaks",
  "coherence",
  "transfer_function",
  "wolf_candidates",
  "wsi_curve",
  "provenance",
  "plot_png",
  "session_meta",
  "manifest",
  "unknown",
] as const;

describe("kindToCategory", () => {
  describe("audio kinds", () => {
    it("maps audio_wav to audio", () => {
      expect(kindToCategory("audio_wav")).toBe("audio");
    });

    it("maps audio_flac to audio", () => {
      expect(kindToCategory("audio_flac")).toBe("audio");
    });

    it("maps audio_raw to audio", () => {
      expect(kindToCategory("audio_raw")).toBe("audio");
    });
  });

  describe("spectrum chart kinds", () => {
    it("maps spectrum_csv to spectrum_chart", () => {
      expect(kindToCategory("spectrum_csv")).toBe("spectrum_chart");
    });

    it("maps coherence_csv to spectrum_chart", () => {
      expect(kindToCategory("coherence_csv")).toBe("spectrum_chart");
    });
  });

  describe("bode plot kinds", () => {
    it("maps transfer_function to bode_plot", () => {
      expect(kindToCategory("transfer_function")).toBe("bode_plot");
    });
  });

  describe("image kinds", () => {
    it("maps image_png to image", () => {
      expect(kindToCategory("image_png")).toBe("image");
    });

    it("maps image_jpg to image", () => {
      expect(kindToCategory("image_jpg")).toBe("image");
    });

    it("maps plot_png to image", () => {
      expect(kindToCategory("plot_png")).toBe("image");
    });
  });

  describe("csv kinds (table display)", () => {
    it("maps peaks_csv to csv", () => {
      expect(kindToCategory("peaks_csv")).toBe("csv");
    });

    it("maps waveform_csv to csv", () => {
      expect(kindToCategory("waveform_csv")).toBe("csv");
    });

    it("maps wsi_curve to csv", () => {
      expect(kindToCategory("wsi_curve")).toBe("csv");
    });
  });

  describe("json kinds", () => {
    it("maps analysis_peaks to json", () => {
      expect(kindToCategory("analysis_peaks")).toBe("json");
    });

    it("maps coherence to json", () => {
      expect(kindToCategory("coherence")).toBe("json");
    });

    it("maps wolf_candidates to json", () => {
      expect(kindToCategory("wolf_candidates")).toBe("json");
    });

    it("maps provenance to json", () => {
      expect(kindToCategory("provenance")).toBe("json");
    });

    it("maps session_meta to json", () => {
      expect(kindToCategory("session_meta")).toBe("json");
    });
  });

  describe("markdown kinds", () => {
    it("maps notes_md to markdown", () => {
      expect(kindToCategory("notes_md")).toBe("markdown");
    });
  });

  describe("fallback behavior", () => {
    it("maps unknown kinds to unknown", () => {
      expect(kindToCategory("unknown")).toBe("unknown");
      expect(kindToCategory("some_future_kind")).toBe("unknown");
      expect(kindToCategory("")).toBe("unknown");
    });
  });

  describe("schema contract coverage", () => {
    it("handles all kinds from viewer_pack_v1 schema", () => {
      // Every kind from the schema should map to a valid category
      const validCategories: RendererCategory[] = [
        "audio",
        "image",
        "csv",
        "json",
        "markdown",
        "spectrum_chart",
        "bode_plot",
        "unknown",
      ];

      for (const kind of SCHEMA_KINDS) {
        const category = kindToCategory(kind);
        expect(validCategories).toContain(category);
      }
    });

    it("soft fallback: unrecognized kinds return unknown (not throw)", () => {
      // Contract: soft fallback for forward compatibility
      expect(() => kindToCategory("new_kind_from_tap_tone_pi_v2")).not.toThrow();
      expect(kindToCategory("new_kind_from_tap_tone_pi_v2")).toBe("unknown");
    });
  });
});

describe("RendererCategory exhaustiveness", () => {
  it("all categories are documented", () => {
    // If this test fails, RENDERER_KINDS.md needs updating
    const documentedCategories: RendererCategory[] = [
      "audio",
      "image",
      "csv",
      "json",
      "markdown",
      "spectrum_chart",
      "bode_plot",
      "unknown",
    ];

    // Map a sample kind to each category to verify mapping works
    const categoryToKind: Record<RendererCategory, string> = {
      audio: "audio_raw",
      image: "plot_png",
      csv: "wsi_curve",
      json: "analysis_peaks",
      markdown: "notes_md",
      spectrum_chart: "spectrum_csv",
      bode_plot: "transfer_function",
      unknown: "some_random_string",
    };

    for (const [category, kind] of Object.entries(categoryToKind)) {
      expect(kindToCategory(kind)).toBe(category);
    }
  });
});
