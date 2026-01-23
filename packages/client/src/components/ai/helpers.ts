import type { ExplainButtonInputs } from "./types";

export function computeDisabledReason(inputs: ExplainButtonInputs): string | null {
  if (inputs.disabledOverride) return inputs.disabledOverride;

  if (!inputs.hasPack) return "Load an evidence ZIP first.";
  if (!inputs.hasActiveFile) return "Select a file to preview.";
  if (!inputs.selection) return "Click a peak or set a selection first.";

  const freq = inputs.selection.freqHz;
  if (!inputs.canRunWithoutFreq && typeof freq !== "number") {
    return "Select a frequency (click a peak in Spectrum/WSI) to explain.";
  }
  return null;
}

export function selectionSummary(sel: { pointId?: string | null; freqHz?: number | null } | null): string {
  if (!sel) return "No selection";
  const p = sel.pointId ? `Point ${sel.pointId}` : "No point";
  const f = typeof sel.freqHz === "number" ? `${sel.freqHz.toFixed(1)} Hz` : "No freq";
  return `${p} • ${f}`;
}
