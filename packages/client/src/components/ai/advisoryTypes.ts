export type EvidenceRef = {
  relpath: string;
  kind?: string;
  sha256?: string;
  bytes?: number;
};

export type AdvisoryBlock =
  | { type: "heading"; level?: 2 | 3 | 4; text: string }
  | { type: "paragraph"; text: string }
  | { type: "bullet_list"; items: string[] }
  | { type: "code_block"; language?: string; code: string }
  | { type: "quote"; text: string }
  | { type: "evidence_refs"; refs: EvidenceRef[]; title?: string };

export type AdvisoryDraftV1 = {
  schema_id: "advisory_draft_v1";
  kind: "explanation" | string;
  content: AdvisoryBlock[];
  citations?: EvidenceRef[]; // legacy: allow top-level citations too
};

export type AdvisoryArtifact = {
  schema_id: "rmos_advisory_artifact_v1";
  advisory_id: string;
  created_at_utc: string;
  draft: AdvisoryDraftV1 | any;
  engine?: Record<string, any>;
  governance?: Record<string, any>;
};
