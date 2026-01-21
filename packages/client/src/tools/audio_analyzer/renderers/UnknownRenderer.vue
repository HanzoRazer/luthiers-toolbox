<template>
  <div class="unknown-renderer">
    <div class="icon">
      ❓
    </div>
    <div class="info">
      <div class="kind">
        {{ entry.kind }}
      </div>
      <div class="path">
        {{ entry.relpath }}
      </div>
      <div class="meta">
        <span>{{ formatBytes(entry.bytes) }}</span>
        <span v-if="entry.mime">{{ entry.mime }}</span>
      </div>
    </div>
    <div class="actions">
      <button
        class="download-btn"
        @click="downloadFile"
      >
        ⬇️ Download
      </button>
      <button
        v-if="isTextLike"
        class="view-btn"
        @click="showRawText = !showRawText"
      >
        {{ showRawText ? "Hide" : "View Raw" }}
      </button>
    </div>

    <div
      v-if="showRawText && isTextLike"
      class="raw-content"
    >
      <pre>{{ rawText }}</pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import type { RendererProps } from "./types";

const props = defineProps<RendererProps>();

const showRawText = ref(false);

const isTextLike = computed(() => {
  const mime = props.entry.mime ?? "";
  return (
    mime.startsWith("text/") ||
    mime === "application/json" ||
    mime === "application/xml" ||
    props.entry.relpath.match(/\.(txt|log|md|json|xml|yaml|yml|ini|cfg|conf|csv)$/i)
  );
});

const rawText = computed(() => {
  if (!isTextLike.value) return "";
  try {
    return new TextDecoder("utf-8").decode(props.bytes);
  } catch {
    return "[Unable to decode as UTF-8]";
  }
});

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function downloadFile() {
  const mime = props.entry.mime ?? "application/octet-stream";
  // Create blob from ArrayBuffer for better compatibility
  const blob = new Blob([(props.bytes.buffer as ArrayBuffer).slice(props.bytes.byteOffset, props.bytes.byteOffset + props.bytes.byteLength)], { type: mime });
  const url = URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = url;
  a.download = props.entry.relpath.split("/").pop() ?? "download";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
</script>

<style scoped>
.unknown-renderer {
  padding: 1rem;
  background: var(--vt-c-bg-soft, #1e1e1e);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.icon {
  font-size: 2rem;
  text-align: center;
}

.info {
  text-align: center;
}

.kind {
  font-family: monospace;
  font-size: 0.9rem;
  background: var(--vt-c-bg-mute, #2a2a2a);
  display: inline-block;
  padding: 0.125rem 0.5rem;
  border-radius: 4px;
  margin-bottom: 0.25rem;
}

.path {
  font-family: monospace;
  font-size: 0.85rem;
  color: var(--vt-c-text-2, #aaa);
  word-break: break-all;
}

.meta {
  display: flex;
  justify-content: center;
  gap: 1rem;
  font-size: 0.8rem;
  color: var(--vt-c-text-3, #888);
  margin-top: 0.25rem;
}

.actions {
  display: flex;
  justify-content: center;
  gap: 0.5rem;
}

.download-btn,
.view-btn {
  padding: 0.35rem 0.75rem;
  font-size: 0.85rem;
  background: var(--vt-c-bg-mute, #2a2a2a);
  border: 1px solid var(--vt-c-divider-light, #444);
  border-radius: 4px;
  cursor: pointer;
  color: inherit;
}

.download-btn:hover,
.view-btn:hover {
  background: var(--vt-c-bg, #252525);
}

.raw-content {
  margin-top: 0.5rem;
  max-height: 300px;
  overflow: auto;
  background: var(--vt-c-bg-mute, #2a2a2a);
  border-radius: 4px;
}

.raw-content pre {
  margin: 0;
  padding: 0.75rem;
  font-size: 0.8rem;
  white-space: pre-wrap;
  word-break: break-all;
  color: var(--vt-c-text-2, #ccc);
}
</style>
