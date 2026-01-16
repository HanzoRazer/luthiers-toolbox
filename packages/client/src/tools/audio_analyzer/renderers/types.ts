// ─────────────────────────────────────────────────────────────────────────────
// Renderer Types - Evidence file renderer interface
// ─────────────────────────────────────────────────────────────────────────────

import type { NormalizedFileEntry, EvidenceFileKind } from "@/evidence/types";

/**
 * Props passed to all evidence file renderers.
 */
export interface RendererProps {
  /** File entry metadata (relpath, kind, mime, etc.) */
  entry: NormalizedFileEntry;
  /** Raw bytes for the file */
  bytes: Uint8Array;
}

/**
 * Category of renderer to dispatch to.
 * Used by pickRenderer() to select the appropriate component.
 */
export type RendererCategory = "audio" | "image" | "csv" | "json" | "markdown" | "spectrum_chart" | "unknown";

/**
 * Maps a file kind to its renderer category.
 */
export function kindToCategory(kind: EvidenceFileKind | string): RendererCategory {
  switch (kind) {
    // Audio files
    case "audio_wav":
    case "audio_flac":
    case "audio_raw":
      return "audio";

    // Image files
    case "image_png":
    case "image_jpg":
    case "plot_png":
      return "image";

    // Spectrum chart (visual frequency analysis)
    case "spectrum_csv":
    case "coherence_csv":
      return "spectrum_chart";

    // CSV-based files (table display)
    case "peaks_csv":
    case "waveform_csv":
    case "wsi_curve":
      return "csv";

    // JSON-based files
    case "analysis_peaks":
    case "coherence":           // viewer_pack_v1 schema kind
    case "provenance":
    case "session_meta":
    case "transfer_function":
    case "wolf_candidates":
      return "json";

    // Markdown
    case "notes_md":
      return "markdown";

    // Unknown / fallback
    default:
      return "unknown";
  }
}
