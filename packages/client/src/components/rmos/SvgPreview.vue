<script setup lang="ts">
/**
 * SvgPreview.vue
 *
 * Safe inline SVG preview with script/foreign element stripping.
 * Prevents XSS by removing dangerous elements before rendering.
 */
import { computed, ref } from "vue";

const props = defineProps<{
  /** Raw SVG content string */
  svg: string;
  /** Maximum height in pixels (default: 300) */
  maxHeight?: number;
  /** Show expand/collapse toggle */
  expandable?: boolean;
}>();

const emit = defineEmits<{
  (e: "error", msg: string): void;
}>();

const expanded = ref(false);

/**
 * Sanitize SVG by removing dangerous elements.
 * Strips: <script>, <foreignObject>, <image> (external references)
 */
function sanitizeSvg(svg: string): string {
  if (!svg) return "";

  return svg
    // Remove script tags and their contents
    .replace(/<script[\s\S]*?>[\s\S]*?<\/script>/gi, "")
    // Remove foreignObject (can embed arbitrary HTML)
    .replace(/<foreignObject[\s\S]*?>[\s\S]*?<\/foreignObject>/gi, "")
    // Remove image tags (external references)
    .replace(/<image[\s\S]*?(?:\/>|>[\s\S]*?<\/image>)/gi, "")
    // Remove event handlers (onclick, onload, etc.)
    .replace(/\s+on\w+\s*=\s*["'][^"']*["']/gi, "")
    // Remove javascript: URLs
    .replace(/href\s*=\s*["']javascript:[^"']*["']/gi, "");
}

const sanitizedSvg = computed(() => {
  try {
    return sanitizeSvg(props.svg);
  } catch (err) {
    emit("error", String(err));
    return "";
  }
});

const containerStyle = computed(() => ({
  maxHeight: expanded.value ? "none" : `${props.maxHeight || 300}px`,
}));

function toggleExpand() {
  expanded.value = !expanded.value;
}
</script>

<template>
  <div class="svg-preview">
    <div
      v-if="sanitizedSvg"
      class="svg-container"
      :style="containerStyle"
      v-html="sanitizedSvg"
    />
    <div v-else class="svg-empty">
      No SVG content
    </div>

    <button
      v-if="expandable && sanitizedSvg"
      class="expand-toggle"
      @click="toggleExpand"
    >
      {{ expanded ? "Collapse" : "Expand" }}
    </button>
  </div>
</template>

<style scoped>
.svg-preview {
  position: relative;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  background: #fafafa;
  overflow: hidden;
}

.svg-container {
  overflow: auto;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.5rem;
}

.svg-container :deep(svg) {
  max-width: 100%;
  height: auto;
}

.svg-empty {
  padding: 2rem;
  text-align: center;
  color: #6c757d;
  font-size: 0.9rem;
}

.expand-toggle {
  position: absolute;
  bottom: 0.5rem;
  right: 0.5rem;
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid #dee2e6;
  border-radius: 4px;
  cursor: pointer;
}

.expand-toggle:hover {
  background: #e9ecef;
}
</style>
