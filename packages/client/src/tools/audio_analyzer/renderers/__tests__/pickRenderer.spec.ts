/**
 * @vitest-environment jsdom
 *
 * Tests for pickRenderer dispatch logic.
 * Validates that all kinds route to appropriate renderer components.
 */
import { describe, it, expect } from "vitest";
import { pickRenderer, getRendererCategory } from "../pickRenderer";

// Import renderer components for identity checks
import AudioRenderer from "../AudioRenderer.vue";
import ImageRenderer from "../ImageRenderer.vue";
import CsvRenderer from "../CsvRenderer.vue";
import JsonRenderer from "../JsonRenderer.vue";
import MarkdownRenderer from "../MarkdownRenderer.vue";
import UnknownRenderer from "../UnknownRenderer.vue";
import SpectrumChartRenderer from "../SpectrumChartRenderer.vue";
import TransferFunctionRenderer from "../TransferFunctionRenderer.vue";
import WsiCurveRenderer from "../WsiCurveRenderer.vue";

describe("pickRenderer", () => {
  describe("audio kinds", () => {
    it("picks AudioRenderer for audio_raw", () => {
      expect(pickRenderer("audio_raw")).toBe(AudioRenderer);
    });

    it("picks AudioRenderer for audio_wav", () => {
      expect(pickRenderer("audio_wav")).toBe(AudioRenderer);
    });

    it("picks AudioRenderer for audio_flac", () => {
      expect(pickRenderer("audio_flac")).toBe(AudioRenderer);
    });
  });

  describe("spectrum chart kinds", () => {
    it("picks SpectrumChartRenderer for spectrum_csv", () => {
      expect(pickRenderer("spectrum_csv")).toBe(SpectrumChartRenderer);
    });

    it("picks SpectrumChartRenderer for coherence_csv", () => {
      expect(pickRenderer("coherence_csv")).toBe(SpectrumChartRenderer);
    });
  });

  describe("bode plot kinds", () => {
    it("picks TransferFunctionRenderer for transfer_function", () => {
      expect(pickRenderer("transfer_function")).toBe(TransferFunctionRenderer);
    });
  });

  describe("image kinds", () => {
    it("picks ImageRenderer for plot_png", () => {
      expect(pickRenderer("plot_png")).toBe(ImageRenderer);
    });

    it("picks ImageRenderer for image_png", () => {
      expect(pickRenderer("image_png")).toBe(ImageRenderer);
    });

    it("picks ImageRenderer for image_jpg", () => {
      expect(pickRenderer("image_jpg")).toBe(ImageRenderer);
    });
  });

  describe("wsi chart kinds", () => {
    it("picks WsiCurveRenderer for wsi_curve", () => {
      expect(pickRenderer("wsi_curve")).toBe(WsiCurveRenderer);
    });
  });

  describe("csv kinds (table)", () => {
    it("picks CsvRenderer for peaks_csv", () => {
      expect(pickRenderer("peaks_csv")).toBe(CsvRenderer);
    });

    it("picks CsvRenderer for waveform_csv", () => {
      expect(pickRenderer("waveform_csv")).toBe(CsvRenderer);
    });
  });

  describe("json kinds", () => {
    it("picks JsonRenderer for analysis_peaks", () => {
      expect(pickRenderer("analysis_peaks")).toBe(JsonRenderer);
    });

    it("picks JsonRenderer for coherence", () => {
      expect(pickRenderer("coherence")).toBe(JsonRenderer);
    });

    it("picks JsonRenderer for wolf_candidates", () => {
      expect(pickRenderer("wolf_candidates")).toBe(JsonRenderer);
    });

    it("picks JsonRenderer for provenance", () => {
      expect(pickRenderer("provenance")).toBe(JsonRenderer);
    });

    it("picks JsonRenderer for session_meta", () => {
      expect(pickRenderer("session_meta")).toBe(JsonRenderer);
    });
  });

  describe("markdown kinds", () => {
    it("picks MarkdownRenderer for notes_md", () => {
      expect(pickRenderer("notes_md")).toBe(MarkdownRenderer);
    });
  });

  describe("fallback behavior", () => {
    it("picks UnknownRenderer for unknown kind", () => {
      expect(pickRenderer("unknown")).toBe(UnknownRenderer);
    });

    it("picks UnknownRenderer for unrecognized kinds", () => {
      expect(pickRenderer("some_new_kind")).toBe(UnknownRenderer);
      expect(pickRenderer("")).toBe(UnknownRenderer);
      expect(pickRenderer("future_tap_tone_kind")).toBe(UnknownRenderer);
    });
  });
});

describe("getRendererCategory", () => {
  it("returns correct category for each kind", () => {
    expect(getRendererCategory("audio_raw")).toBe("audio");
    expect(getRendererCategory("spectrum_csv")).toBe("spectrum_chart");
    expect(getRendererCategory("transfer_function")).toBe("bode_plot");
    expect(getRendererCategory("plot_png")).toBe("image");
    expect(getRendererCategory("wsi_curve")).toBe("wsi_chart");
    expect(getRendererCategory("analysis_peaks")).toBe("json");
    expect(getRendererCategory("notes_md")).toBe("markdown");
    expect(getRendererCategory("unknown")).toBe("unknown");
  });
});

describe("viewer_pack_v1 schema coverage", () => {
  /**
   * All kinds from the viewer_pack_v1 schema.
   * If tap_tone_pi adds a new kind, this test documents what happens.
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
  ];

  it("all schema kinds have a renderer", () => {
    for (const kind of SCHEMA_KINDS) {
      const renderer = pickRenderer(kind);
      expect(renderer).toBeDefined();
      // Soft fallback: we don't require specialized renderers for all kinds
      // Just verify dispatch doesn't throw
    }
  });

  it("no schema kind throws during dispatch", () => {
    for (const kind of SCHEMA_KINDS) {
      expect(() => pickRenderer(kind)).not.toThrow();
      expect(() => getRendererCategory(kind)).not.toThrow();
    }
  });
});
