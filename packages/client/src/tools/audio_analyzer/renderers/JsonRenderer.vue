<template>
  <div class="json-renderer">
    <div class="header">
      <span class="label">{{ entry.kind }}</span>
      <span class="path">{{ entry.relpath }}</span>
      <button
        class="copy-btn"
        @click="copyToClipboard"
      >
        📋 Copy
      </button>
      <button
        class="toggle-btn"
        @click="collapsed = !collapsed"
      >
        {{ collapsed ? "▶ Expand" : "▼ Collapse" }}
      </button>
    </div>

    <div
      v-if="!collapsed"
      class="json-content"
    >
      <pre v-if="parsedJson !== null">{{ formattedJson }}</pre>
      <div
        v-else
        class="error"
      >
        Invalid JSON: {{ parseError }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import type { RendererProps } from "./types";

const props = defineProps<RendererProps>();

const collapsed = ref(false);

const rawText = computed(() => {
  return new TextDecoder("utf-8").decode(props.bytes);
});

const parsedJson = computed<unknown | null>(() => {
  try {
    return JSON.parse(rawText.value);
  } catch {
    return null;
  }
});

const parseError = computed(() => {
  try {
    JSON.parse(rawText.value);
    return null;
  } catch (e) {
    return e instanceof Error ? e.message : String(e);
  }
});

const formattedJson = computed(() => {
  if (parsedJson.value === null) return "";
  return JSON.stringify(parsedJson.value, null, 2);
});

async function copyToClipboard() {
  try {
    await navigator.clipboard.writeText(formattedJson.value || rawText.value);
  } catch (e) {
    console.warn("Failed to copy JSON to clipboard:", e);
  }
}
</script>

<style scoped>
.json-renderer {
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
  flex-wrap: wrap;
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

.copy-btn,
.toggle-btn {
  padding: 0.25rem 0.5rem;
  font-size: 0.8rem;
  background: var(--vt-c-bg-mute, #2a2a2a);
  border: 1px solid var(--vt-c-divider-light, #444);
  border-radius: 4px;
  cursor: pointer;
  color: inherit;
}

.copy-btn {
  margin-left: auto;
}

.copy-btn:hover,
.toggle-btn:hover {
  background: var(--vt-c-bg, #252525);
}

.json-content {
  max-height: 500px;
  overflow: auto;
}

pre {
  margin: 0;
  padding: 1rem;
  font-family: "Fira Code", "Consolas", monospace;
  font-size: 0.8rem;
  line-height: 1.4;
  white-space: pre-wrap;
  word-break: break-word;
  color: var(--vt-c-text-2, #ccc);
}

.error {
  padding: 1rem;
  color: var(--vt-c-red, #f44);
  font-style: italic;
}
</style>
