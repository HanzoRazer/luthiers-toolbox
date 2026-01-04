// ─────────────────────────────────────────────────────────────────────────────
// Renderer Registry - Picks the appropriate renderer component by file kind
// ─────────────────────────────────────────────────────────────────────────────

import type { Component } from "vue";
import { kindToCategory, type RendererCategory } from "./types";
import AudioRenderer from "./AudioRenderer.vue";
import ImageRenderer from "./ImageRenderer.vue";
import CsvRenderer from "./CsvRenderer.vue";
import JsonRenderer from "./JsonRenderer.vue";
import MarkdownRenderer from "./MarkdownRenderer.vue";
import UnknownRenderer from "./UnknownRenderer.vue";

/**
 * Map of renderer category to Vue component.
 */
const rendererMap: Record<RendererCategory, Component> = {
  audio: AudioRenderer,
  image: ImageRenderer,
  csv: CsvRenderer,
  json: JsonRenderer,
  markdown: MarkdownRenderer,
  unknown: UnknownRenderer,
};

/**
 * Pick the appropriate renderer component for a given file kind.
 *
 * @param kind - The EvidenceFileKind (e.g., "audio_wav", "spectrum_csv")
 * @returns The Vue component to render that file type
 */
export function pickRenderer(kind: string): Component {
  const category = kindToCategory(kind);
  return rendererMap[category] ?? UnknownRenderer;
}

/**
 * Get the renderer category for a file kind (useful for UI filtering).
 */
export function getRendererCategory(kind: string): RendererCategory {
  return kindToCategory(kind);
}

// Re-export types
export type { RendererProps, RendererCategory } from "./types";
