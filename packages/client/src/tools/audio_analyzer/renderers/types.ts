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
  /** Optional sibling peaks data (analysis.json bytes for spectrum CSV) */
  peaksBytes?: Uint8Array | null;
}

/**
 * Category of renderer to dispatch to.
 * Used by pickRenderer() to select the appropriate component.
 */
export type RendererCategory = "audio" | "image" | "csv" | "json" | "markdown" | "spectrum_chart" | "wsi_chart" | "bode_plot" | "unknown";

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

    // WSI curve (session-level wolf stress index)
    case "wsi_curve":
      return "wsi_chart";

    // Bode plot (transfer function / frequency response)
    case "transfer_function":
      return "bode_plot";

    // CSV-based files (table display)
    case "peaks_csv":
    case "waveform_csv":
      return "csv";

    // JSON-based files
    case "analysis_peaks":
    case "coherence":           // viewer_pack_v1 schema kind (JSON metadata)
    case "provenance":
    case "session_meta":
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
