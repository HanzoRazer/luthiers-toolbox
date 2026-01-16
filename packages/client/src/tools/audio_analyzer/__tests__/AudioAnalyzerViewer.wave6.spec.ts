/**
 * @vitest-environment jsdom
 *
 * Wave 6A + 6B.1 acceptance test stubs.
 * These document the expected behaviors; implementation deferred.
 */
import { describe, it } from "vitest";

describe("Wave 6A – Linked Selection Cursor", () => {
  it.todo("persists selection across file switches until cleared");
  it.todo("clears cursor without clearing selection context");
  it.todo("passes selected-freq-hz as null when cursor is cleared");
});

describe("Spectrum Selection", () => {
  it.todo("sets pointId and freqHz on peak click");
  it.todo("renders vertical cursor line at selected frequency");
  it.todo("populates Selection Details with spectrum + analysis relpaths");
});

describe("Audio Navigation", () => {
  it.todo("opens point audio when selection has pointId");
  it.todo("shows warning and does not navigate if audio is missing");
});

describe("WSI Curve Renderer (6B.1)", () => {
  it.todo("renders wsi_curve.csv as a chart with freq_hz on X axis");
  it.todo("plots wsi with secondary coh_mean and phase_disorder traces");
  it.todo("shades admissible regions using exporter field only");
});

describe("WSI Selection Semantics", () => {
  it.todo("sets freqHz only when clicking WSI chart");
  it.todo("does not overwrite existing pointId on WSI selection");
  it.todo("shows WSI row fields in Selection Details panel");
  it.todo("uses raw exporter row as selection payload");
});

describe("Governance Invariants", () => {
  it.todo("does not compute derived metrics from selection");
  it.todo("does not perform scoring, ranking, or interpretation");
});
