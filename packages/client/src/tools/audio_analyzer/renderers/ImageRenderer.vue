<template>
  <div class="image-renderer">
    <div v-if="imageUrl" class="image-container">
      <img :src="imageUrl" :alt="entry.relpath" loading="lazy" />
      <div class="info">
        <span class="label">{{ entry.kind }}</span>
        <span class="path">{{ entry.relpath }}</span>
      </div>
    </div>
    <div v-else class="error">Unable to render image</div>
  </div>
</template>

<script setup lang="ts">
import { computed, onUnmounted } from "vue";
import type { RendererProps } from "./types";

const props = defineProps<RendererProps>();

const imageUrl = computed(() => {
  if (!props.bytes || props.bytes.length === 0) return null;

  // Determine MIME type
  let mime = "image/png";
  if (props.entry.kind === "image_jpg" || props.entry.relpath.endsWith(".jpg") || props.entry.relpath.endsWith(".jpeg")) {
    mime = "image/jpeg";
  }

  // Create blob from ArrayBuffer for better compatibility
  const blob = new Blob([(props.bytes.buffer as ArrayBuffer).slice(props.bytes.byteOffset, props.bytes.byteOffset + props.bytes.byteLength)], { type: mime });
  return URL.createObjectURL(blob);
});

onUnmounted(() => {
  if (imageUrl.value) {
    URL.revokeObjectURL(imageUrl.value);
  }
});
</script>

<style scoped>
.image-renderer {
  padding: 1rem;
  background: var(--vt-c-bg-soft, #1e1e1e);
  border-radius: 8px;
}

.image-container {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.image-container img {
  max-width: 100%;
  height: auto;
  border-radius: 4px;
  background: #000;
}

.info {
  display: flex;
  gap: 1rem;
  font-size: 0.85rem;
  color: var(--vt-c-text-2, #aaa);
}

.label {
  font-family: monospace;
  background: var(--vt-c-bg-mute, #2a2a2a);
  padding: 0.125rem 0.5rem;
  border-radius: 4px;
}

.path {
  font-family: monospace;
  opacity: 0.7;
}

.error {
  color: var(--vt-c-red, #f44);
  font-style: italic;
}
</style>
