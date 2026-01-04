// Renderers barrel export
export { pickRenderer, getRendererCategory } from "./pickRenderer";
export type { RendererProps, RendererCategory } from "./types";
export { kindToCategory } from "./types";

// Individual renderers (for direct import if needed)
export { default as AudioRenderer } from "./AudioRenderer.vue";
export { default as ImageRenderer } from "./ImageRenderer.vue";
export { default as CsvRenderer } from "./CsvRenderer.vue";
export { default as JsonRenderer } from "./JsonRenderer.vue";
export { default as MarkdownRenderer } from "./MarkdownRenderer.vue";
export { default as UnknownRenderer } from "./UnknownRenderer.vue";
