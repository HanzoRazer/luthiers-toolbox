<script setup lang="ts">
/**
 * PlaybackControlsBar — Playback controls for ToolpathPlayer
 *
 * Extracted from ToolpathPlayer.vue to reduce component size.
 * Handles play/pause, step, stop, scrubbing, and speed selection.
 */
import { computed } from 'vue';

interface Props {
  playState: 'idle' | 'playing' | 'paused';
  progress: number;
  speed: number;
  segmentCount: number;
  disabled?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
});

const emit = defineEmits<{
  play: [];
  pause: [];
  stop: [];
  stepForward: [];
  stepBackward: [];
  seek: [progress: number];
  setSpeed: [speed: number];
}>();

const speeds = [0.5, 1, 2, 5, 10] as const;

const playIcon = computed(() =>
  props.playState === 'playing' ? '⏸' : '▶'
);

const playLabel = computed(() =>
  props.playState === 'playing' ? 'Pause' : 'Play'
);

function togglePlay(): void {
  if (props.playState === 'playing') {
    emit('pause');
  } else {
    emit('play');
  }
}

function onScrubInput(e: Event): void {
  emit('seek', parseFloat((e.target as HTMLInputElement).value));
}
</script>

<template>
  <div class="playback-controls">
    <button
      class="ctrl-btn"
      title="Step back"
      :disabled="disabled || segmentCount === 0"
      @click="emit('stepBackward')"
    >
      ◀◀
    </button>

    <button
      class="ctrl-btn play-btn"
      :title="playLabel"
      :disabled="disabled || segmentCount === 0"
      @click="togglePlay"
    >
      {{ playIcon }}
    </button>

    <button
      class="ctrl-btn"
      title="Step forward"
      :disabled="disabled || segmentCount === 0"
      @click="emit('stepForward')"
    >
      ▶▶
    </button>

    <button
      class="ctrl-btn stop-btn"
      title="Stop"
      :disabled="disabled || segmentCount === 0"
      @click="emit('stop')"
    >
      ■
    </button>

    <input
      type="range"
      class="scrub-bar"
      min="0"
      max="1"
      step="0.0005"
      :value="progress"
      :disabled="disabled || segmentCount === 0"
      @input="onScrubInput"
    >

    <span class="pct">{{ (progress * 100).toFixed(0) }}%</span>

    <div class="speed-group">
      <button
        v-for="s in speeds"
        :key="s"
        class="speed-btn"
        :class="{ active: speed === s }"
        :disabled="disabled"
        @click="emit('setSpeed', s)"
      >
        {{ s }}×
      </button>
    </div>
  </div>
</template>

<style scoped>
.playback-controls {
  display: flex;
  align-items: center;
  gap: 6px;
}

.ctrl-btn {
  background: #252538;
  border: 1px solid #3a3a5c;
  color: #ccc;
  border-radius: 4px;
  width: 30px;
  height: 28px;
  font-size: 11px;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
  flex-shrink: 0;
}

.ctrl-btn:hover:not(:disabled) {
  background: #33334a;
  color: #fff;
}

.ctrl-btn:disabled {
  opacity: 0.35;
  cursor: default;
}

.play-btn {
  width: 36px;
  font-size: 14px;
  color: #4a90d9;
  border-color: #4a90d9;
}

.play-btn:hover:not(:disabled) {
  background: #1a3a6b;
  color: #fff;
}

.stop-btn {
  color: #e74c3c;
  border-color: #e74c3c;
}

.stop-btn:hover:not(:disabled) {
  background: #5c1a1a;
  color: #fff;
}

.scrub-bar {
  flex: 1;
  min-width: 60px;
  accent-color: #4a90d9;
  height: 4px;
  cursor: pointer;
}

.scrub-bar:disabled {
  opacity: 0.35;
  cursor: default;
}

.pct {
  font-size: 11px;
  color: #666;
  width: 34px;
  text-align: right;
  flex-shrink: 0;
}

.speed-group {
  display: flex;
  gap: 3px;
  flex-shrink: 0;
}

.speed-btn {
  background: #252538;
  border: 1px solid #3a3a5c;
  color: #888;
  border-radius: 4px;
  padding: 2px 6px;
  font-size: 11px;
  cursor: pointer;
  transition: background 0.12s, color 0.12s;
}

.speed-btn:hover:not(:disabled) {
  background: #33334a;
  color: #ccc;
}

.speed-btn:disabled {
  opacity: 0.35;
  cursor: default;
}

.speed-btn.active {
  background: #1a3a6b;
  border-color: #4a90d9;
  color: #4a90d9;
}
</style>
