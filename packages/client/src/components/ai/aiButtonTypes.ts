export type EvidenceSelection = {
  pointId?: string | null;
  freqHz?: number | null;
  source?: string | null;
  activeRelpath?: string | null;
};

export type AiRunState =
  | { state: "idle" }
  | { state: "running" }
  | { state: "success"; advisoryId: string }
  | { state: "error"; message: string };

export type ExplainButtonInputs = {
  hasPack: boolean;
  hasActiveFile: boolean;
  selection: EvidenceSelection | null;
  canRunWithoutFreq?: boolean; // default false: require freqHz
  disabledOverride?: string | null; // if provided, forces disabled with this reason
};
