// Wave 6A (Safe Sync): shared selection state
// Invariant: selection is a UI cursor / navigation hint ONLY.
// Do NOT add derived fields (scores, warnings, recommendations) here.

export type EvidenceSelectionSource =
  | "spectrum"
  | "wsi"
  | "ods"
  | "wolf"
  | "point_tree";

export type EvidenceSelection = {
  /** Point context (e.g. "A1") if explicitly chosen (tree click or peak click). */
  pointId: string | null;
  /** Frequency cursor in Hz if explicitly chosen (peak click / chart click). */
  freqHz: number | null;
  /** Where the selection originated. */
  source: EvidenceSelectionSource | null;
};

export function makeEmptySelection(): EvidenceSelection {
  return { pointId: null, freqHz: null, source: null };
}

export function setPoint(selection: EvidenceSelection, pointId: string | null): EvidenceSelection {
  return { ...selection, pointId, source: pointId ? "point_tree" : selection.source };
}

export function setFreq(
  selection: EvidenceSelection,
  freqHz: number | null,
  source: EvidenceSelectionSource | null,
  pointId?: string | null,
): EvidenceSelection {
  return {
    pointId: typeof pointId === "undefined" ? selection.pointId : pointId,
    freqHz,
    source,
  };
}
