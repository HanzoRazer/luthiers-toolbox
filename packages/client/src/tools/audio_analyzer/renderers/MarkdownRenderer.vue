<template>
  <div class="markdown-renderer">
    <div class="header">
      <span class="label">{{ entry.kind }}</span>
      <span class="path">{{ entry.relpath }}</span>
      <button
        class="toggle-btn"
        @click="showRaw = !showRaw"
      >
        {{ showRaw ? "📝 Rendered" : "📄 Raw" }}
      </button>
    </div>

    <div class="content">
      <div
        v-if="showRaw"
        class="raw"
      >
        <pre>{{ rawText }}</pre>
      </div>
      <div
        v-else
        class="rendered"
        v-html="renderedHtml"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import type { RendererProps } from "./types";

const props = defineProps<RendererProps>();

const showRaw = ref(false);

const rawText = computed(() => {
  return new TextDecoder("utf-8").decode(props.bytes);
});

/**
 * Simple Markdown → HTML converter (basic subset).
 * For production, consider using a library like marked or markdown-it.
 */
const renderedHtml = computed(() => {
  let html = escapeHtml(rawText.value);

  // Headers
  html = html.replace(/^### (.+)$/gm, "<h3>$1</h3>");
  html = html.replace(/^## (.+)$/gm, "<h2>$1</h2>");
  html = html.replace(/^# (.+)$/gm, "<h1>$1</h1>");

  // Bold and italic
  html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  html = html.replace(/\*(.+?)\*/g, "<em>$1</em>");
  html = html.replace(/_(.+?)_/g, "<em>$1</em>");

  // Code blocks
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, "<pre><code>$2</code></pre>");
  html = html.replace(/`([^`]+)`/g, "<code>$1</code>");

  // Links
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');

  // Lists
  html = html.replace(/^- (.+)$/gm, "<li>$1</li>");
  html = html.replace(/(<li>.*<\/li>\n?)+/g, "<ul>$&</ul>");

  // Paragraphs (double newlines)
  html = html.replace(/\n\n+/g, "</p><p>");
  html = `<p>${html}</p>`;

  // Clean up empty paragraphs
  html = html.replace(/<p>\s*<\/p>/g, "");
  html = html.replace(/<p>(<h[1-6]>)/g, "$1");
  html = html.replace(/(<\/h[1-6]>)<\/p>/g, "$1");
  html = html.replace(/<p>(<ul>)/g, "$1");
  html = html.replace(/(<\/ul>)<\/p>/g, "$1");
  html = html.replace(/<p>(<pre>)/g, "$1");
  html = html.replace(/(<\/pre>)<\/p>/g, "$1");

  return html;
});

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}
</script>

<style scoped>
.markdown-renderer {
  background: var(--vt-c-bg-soft, #1e1e1e);
  border-radius: 8px;
  overflow: hidden;
}

.header {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--vt-c-divider-light, #333);
}

.label {
  font-family: monospace;
  background: var(--vt-c-bg-mute, #2a2a2a);
  padding: 0.125rem 0.5rem;
  border-radius: 4px;
  font-size: 0.85rem;
}

.path {
  font-family: monospace;
  font-size: 0.8rem;
  color: var(--vt-c-text-2, #aaa);
}

.toggle-btn {
  margin-left: auto;
  padding: 0.25rem 0.5rem;
  font-size: 0.8rem;
  background: var(--vt-c-bg-mute, #2a2a2a);
  border: 1px solid var(--vt-c-divider-light, #444);
  border-radius: 4px;
  cursor: pointer;
  color: inherit;
}

.toggle-btn:hover {
  background: var(--vt-c-bg, #252525);
}

.content {
  max-height: 500px;
  overflow: auto;
}

.raw pre {
  margin: 0;
  padding: 1rem;
  font-family: monospace;
  font-size: 0.85rem;
  white-space: pre-wrap;
  color: var(--vt-c-text-2, #ccc);
}

.rendered {
  padding: 1rem;
  line-height: 1.6;
  color: var(--vt-c-text-1, #fff);
}

.rendered :deep(h1),
.rendered :deep(h2),
.rendered :deep(h3) {
  margin: 0.5em 0;
  color: var(--vt-c-text-1, #fff);
}

.rendered :deep(h1) {
  font-size: 1.5rem;
}
.rendered :deep(h2) {
  font-size: 1.25rem;
}
.rendered :deep(h3) {
  font-size: 1.1rem;
}

.rendered :deep(code) {
  background: var(--vt-c-bg-mute, #2a2a2a);
  padding: 0.125rem 0.25rem;
  border-radius: 3px;
  font-family: monospace;
  font-size: 0.9em;
}

.rendered :deep(pre) {
  background: var(--vt-c-bg-mute, #2a2a2a);
  padding: 0.75rem;
  border-radius: 4px;
  overflow-x: auto;
}

.rendered :deep(pre code) {
  background: none;
  padding: 0;
}

.rendered :deep(a) {
  color: var(--vt-c-brand, #42b883);
}

.rendered :deep(ul) {
  margin: 0.5em 0;
  padding-left: 1.5em;
}

.rendered :deep(li) {
  margin: 0.25em 0;
}

.rendered :deep(strong) {
  font-weight: 600;
}
</style>
