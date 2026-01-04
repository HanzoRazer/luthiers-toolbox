<template>
  <div class="audio-renderer">
    <div v-if="audioUrl" class="player">
      <audio ref="audioEl" :src="audioUrl" controls preload="metadata" />
      <div class="info">
        <span class="label">{{ entry.kind }}</span>
        <span class="size">{{ formatBytes(entry.bytes) }}</span>
      </div>
    </div>
    <div v-else class="error">Unable to create audio playback</div>
  </div>
</template>

<script setup lang="ts">
import { computed, onUnmounted } from "vue";
import type { RendererProps } from "./types";

const props = defineProps<RendererProps>();

/**
 * Create a blob URL for audio playback.
 * Supports WAV, FLAC; raw PCM would need additional handling.
 */
const audioUrl = computed(() => {
  if (!props.bytes || props.bytes.length === 0) return null;

  // Determine MIME type
  let mime = "audio/wav";
  if (props.entry.kind === "audio_flac") {
    mime = "audio/flac";
  } else if (props.entry.kind === "audio_raw") {
    // Raw PCM typically can't be played directly without headers
    // For now, attempt WAV interpretation
    mime = "audio/wav";
  }

  // Create blob from ArrayBuffer (not Uint8Array directly for better compat)
  const blob = new Blob([props.bytes.buffer.slice(props.bytes.byteOffset, props.bytes.byteOffset + props.bytes.byteLength)], { type: mime });
  return URL.createObjectURL(blob);
});

// Clean up blob URL on unmount
onUnmounted(() => {
  if (audioUrl.value) {
    URL.revokeObjectURL(audioUrl.value);
  }
});

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}
</script>

<style scoped>
.audio-renderer {
  padding: 1rem;
  background: var(--vt-c-bg-soft, #1e1e1e);
  border-radius: 8px;
}

.player {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.player audio {
  width: 100%;
  border-radius: 4px;
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

.error {
  color: var(--vt-c-red, #f44);
  font-style: italic;
}
</style>
