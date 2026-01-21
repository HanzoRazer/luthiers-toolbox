<script setup lang="ts">
/**
 * SvgPreview.vue
 *
 * Safe inline SVG preview with XSS protection.
 * Uses the blob download endpoint and sanitizes content.
 */
import { computed, ref, watch } from "vue";

const props = defineProps<{
  runId: string;
  advisoryId: string;
  apiBase?: string;
}>();

const apiBase = computed(() => props.apiBase ?? "/api");
const loading = ref(false);
const error = ref<string | null>(null);
const svg = ref<string | null>(null);
const blocked = ref<string | null>(null);

function sanitize(svgText: string): string {
  // Preview-only safety: remove scripts / foreignObject / image
  return svgText
    .replace(/<script[\s\S]*?>[\s\S]*?<\/script>/gi, "")
    .replace(/<foreignObject[\s\S]*?>[\s\S]*?<\/foreignObject>/gi, "")
    .replace(/<image[\s\S]*?(?:\/>|>[\s\S]*?<\/image>)/gi, "")
    .replace(/\s+on\w+\s*=\s*["'][^"']*["']/gi, "");
}

async function load() {
  if (!props.runId || !props.advisoryId) return;
  loading.value = true;
  error.value = null;
  svg.value = null;
  blocked.value = null;

  try {
    // Use the authoritative blob download endpoint
    const url = `${apiBase.value}/rmos/runs/${encodeURIComponent(props.runId)}/advisory/blobs/${encodeURIComponent(props.advisoryId)}/download`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`Download failed (${res.status})`);

    const text = await res.text();
    const lower = text.toLowerCase();

    // Mirror server preview flags (defense-in-depth)
    if (lower.includes("<script")) { blocked.value = "script"; return; }
    if (lower.includes("foreignobject")) { blocked.value = "foreignObject"; return; }
    if (lower.includes("<image")) { blocked.value = "image"; return; }
    if (lower.includes("<text")) { blocked.value = "text"; return; }

    svg.value = sanitize(text);
  } catch (e: any) {
    error.value = e?.message ?? String(e);
  } finally {
    loading.value = false;
  }
}

watch(() => [props.runId, props.advisoryId], () => load(), { immediate: true });
</script>

<template>
  <div class="svg-preview">
    <div
      v-if="loading"
      class="subtle"
    >
      Loading preview...
    </div>
    <div
      v-else-if="error"
      class="error"
    >
      {{ error }}
    </div>
    <div
      v-else-if="blocked"
      class="warn"
    >
      Preview blocked ({{ blocked }}). Download is still available.
    </div>
    <div
      v-else-if="svg"
      class="svg-container"
      v-html="svg"
    />
    <div
      v-else
      class="subtle"
    >
      No preview.
    </div>
  </div>
</template>

<style scoped>
.svg-preview {
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 8px;
  padding: 10px;
  background: rgba(0, 0, 0, 0.01);
  min-height: 100px;
}

.svg-container :deep(svg) {
  width: 100%;
  height: auto;
  display: block;
  max-height: 300px;
}

.subtle {
  opacity: 0.7;
  text-align: center;
  padding: 1rem;
}

.error {
  color: #b00020;
  padding: 0.5rem;
}

.warn {
  color: #8a5a00;
  padding: 0.5rem;
  background: #fff3cd;
  border-radius: 4px;
}
</style>
