export type EvidenceSelection = {
  pointId?: string | null;
  freqHz?: number | null;
  source?: "spectrum" | "wsi" | "wolf" | "ods" | "tree" | "manual" | null;
  activeRelpath?: string | null;
};

export type EvidenceRef = {
  relpath: string;
  kind?: string;
  sha256?: string;
  bytes?: number;
};

export type AIContextPacketV1 = {
  schema_id: "ai_context_packet_v1";
  created_at_utc: string;
  request: {
    kind: "explanation";
    template_id: "explain_selection";
    template_version: "1.0.0";
    notes?: string;
  };
  evidence: {
    schema_id?: string;
    bundle_sha256?: string | null;
    selection: {
      pointId: string | null;
      freqHz: number | null;
      activeRelpath: string | null;
      source: string | null;
    };
    refs: EvidenceRef[];
  };
  excerpts?: {
    wsiRow?: Record<string, any> | null;
    spectrumRow?: Record<string, any> | null;
    peaks?: Array<Record<string, any>> | null;
  };
};
