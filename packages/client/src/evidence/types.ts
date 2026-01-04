export type EvidenceLane = "AUDIO_ANALYZER" | "RMOS" | "CAM" | "OTHER";

export type EvidenceFileKind =
  | "audio_wav"
  | "audio_flac"
  | "audio_raw"
  | "spectrum_csv"
  | "peaks_csv"
  | "coherence_csv"
  | "waveform_csv"
  | "wsi_curve"
  | "notes_md"
  | "image_png"
  | "image_jpg"
  | "plot_png"
  | "analysis_peaks"
  | "provenance"
  | "session_meta"
  | "transfer_function"
  | "wolf_candidates"
  | "unknown";

export type EvidenceFileEntry = {
  path: string;          // path inside the pack
  kind: EvidenceFileKind;
  mime?: string;
  size_bytes?: number;
  sha256?: string;
};

export type EvidenceManifestV1 = {
  schema_version: "toolbox_evidence_manifest_v1";
  bundle_id: string;
  created_at_utc: string;

  lane?: EvidenceLane;

  source?: {
    tool?: string;               // e.g., "tap_tone_pi"
    device?: string;             // e.g., "raspi5"
    exporter_version?: string;
  };

  audio?: {
    sample_rate_hz?: number;
    channels?: string[];         // e.g., ["ref","mic"]
    duration_sec?: number;
  };

  files: EvidenceFileEntry[];

  notes?: string;
};

export type EvidenceLoadedFile = {
  entry: EvidenceFileEntry;
  bytes: Uint8Array;
};

export type EvidenceBundle = {
  manifest: EvidenceManifestV1;
  filesByPath: Map<string, EvidenceLoadedFile>;
};

// ─────────────────────────────────────────────────────────────────────────────
// viewer_pack_v1 schema (canonical for tap_tone_pi → ToolBox interchange)
// ─────────────────────────────────────────────────────────────────────────────

export type ViewerPackFileEntry = {
  relpath: string;
  sha256?: string;
  bytes: number;
  mime: string;
  kind: string;
};

export type ViewerPackManifestV1 = {
  viewer_pack_version: string;
  schema_id: "viewer_pack_v1";
  created_at_utc: string;
  source_capdir?: string;
  detected_phase?: string;
  measurement_only?: boolean;
  interpretation?: string;
  contents?: Record<string, boolean>;
  files: ViewerPackFileEntry[];
  bundle_sha256?: string;
};

// ─────────────────────────────────────────────────────────────────────────────
// NormalizedPack — internal unified model (both schemas map to this)
// ─────────────────────────────────────────────────────────────────────────────

export type NormalizedFileEntry = {
  relpath: string;
  kind: EvidenceFileKind | string;
  mime: string;
  bytes: number;
  sha256?: string;
};

export type NormalizedPack = {
  schema_id: "viewer_pack_v1" | "toolbox_evidence_manifest_v1";
  created_at_utc: string;
  source_capdir?: string;
  detected_phase?: string;
  measurement_only: boolean;
  interpretation?: string;
  bundle_sha256?: string;
  files: NormalizedFileEntry[];
  /** Resolve file bytes by relpath */
  resolveFile: (relpath: string) => Uint8Array | null;
};

