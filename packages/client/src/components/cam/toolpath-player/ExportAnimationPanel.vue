<script setup lang="ts">
/**
 * ExportAnimationPanel — Animation export controls for ToolpathPlayer
 *
 * Extracted from ToolpathPlayer.vue to reduce component size.
 * Handles export configuration and progress display.
 */
import type { ExportConfig, ExportProgress } from '@/util/animationExporter';

interface Props {
  isExporting: boolean;
  exportProgress: ExportProgress | null;
  config: Partial<ExportConfig>;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  close: [];
  startExport: [];
  cancelExport: [];
  'update:config': [config: Partial<ExportConfig>];
}>();

function updateConfig<K extends keyof ExportConfig>(key: K, value: ExportConfig[K]): void {
  emit('update:config', { ...props.config, [key]: value });
}
</script>

<template>
  <!-- Export Configuration Panel -->
  <div
    v-if="!isExporting"
    class="export-panel"
  >
    <div class="panel-header">
      <span>📹 Export Animation</span>
      <button @click="emit('close')">✕</button>
    </div>
    <div class="export-options">
      <div class="export-row">
        <label>Format:</label>
        <select
          :value="config.format"
          class="export-select"
          @change="updateConfig('format', ($event.target as HTMLSelectElement).value as 'webm' | 'gif')"
        >
          <option value="webm">WebM Video</option>
          <option value="gif">GIF Animation</option>
        </select>
      </div>
      <div class="export-row">
        <label>FPS:</label>
        <select
          :value="config.fps"
          class="export-select"
          @change="updateConfig('fps', parseInt(($event.target as HTMLSelectElement).value))"
        >
          <option :value="15">15 fps</option>
          <option :value="24">24 fps</option>
          <option :value="30">30 fps</option>
          <option :value="60">60 fps</option>
        </select>
      </div>
      <div class="export-row">
        <label>Quality:</label>
        <input
          :value="config.quality"
          type="range"
          min="0.3"
          max="1"
          step="0.1"
          class="export-slider"
          @input="updateConfig('quality', parseFloat(($event.target as HTMLInputElement).value))"
        >
        <span class="export-val">{{ Math.round((config.quality ?? 0.8) * 100) }}%</span>
      </div>
      <div class="export-row">
        <label>Duration:</label>
        <div class="export-duration">
          <input
            :value="config.duration"
            type="number"
            min="1"
            max="300"
            step="1"
            placeholder="Full"
            class="export-input"
            @input="updateConfig('duration', ($event.target as HTMLInputElement).value ? parseInt(($event.target as HTMLInputElement).value) : null)"
          >
          <span class="export-hint">sec (blank = full animation)</span>
        </div>
      </div>
      <div class="export-info">
        <span v-if="config.format === 'webm'">
          📼 WebM: High quality, smaller file, plays in browsers
        </span>
        <span v-else>
          🎞️ GIF: Universal support, larger file, limited colors
        </span>
      </div>
      <button
        class="export-start-btn"
        @click="emit('startExport')"
      >
        Start Export
      </button>
    </div>
  </div>

  <!-- Export Progress Overlay -->
  <div
    v-if="isExporting && exportProgress"
    class="export-overlay"
  >
    <div class="export-progress-box">
      <div class="export-progress-header">
        <span>
          {{ exportProgress.phase === 'recording'
            ? '🔴 Recording'
            : exportProgress.phase === 'encoding'
              ? '⚙️ Encoding'
              : '📹 Exporting' }}
        </span>
        <button
          class="export-cancel-btn"
          @click="emit('cancelExport')"
        >
          Cancel
        </button>
      </div>
      <div class="export-progress-info">
        {{ exportProgress.message }}
      </div>
      <div class="export-progress-track">
        <div
          class="export-progress-fill"
          :style="{ width: exportProgress.percent + '%' }"
        />
      </div>
      <div class="export-progress-stats">
        {{ exportProgress.framesCaptured }} / {{ exportProgress.totalFrames }} frames
      </div>
    </div>
  </div>

  <!-- Export Complete/Error Toast -->
  <div
    v-if="!isExporting && exportProgress?.phase === 'complete'"
    class="export-toast success"
  >
    ✅ {{ exportProgress.message }}
  </div>
  <div
    v-if="!isExporting && exportProgress?.phase === 'error'"
    class="export-toast error"
  >
    ❌ {{ exportProgress.message }}
  </div>
</template>

<style scoped>
.export-panel {
  position: absolute;
  right: 10px;
  top: 10px;
  width: 280px;
  background: #1a1a2e;
  border: 1px solid #3a3a5c;
  border-radius: 8px;
  overflow: hidden;
  z-index: 15;
  font-size: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #252538;
  border-bottom: 1px solid #3a3a5c;
  font-weight: 600;
  color: #ddd;
}

.panel-header button {
  background: transparent;
  border: none;
  color: #666;
  cursor: pointer;
  font-size: 14px;
  padding: 0 4px;
}

.panel-header button:hover {
  color: #e74c3c;
}

.export-options {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.export-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.export-row label {
  min-width: 60px;
  color: #888;
  font-size: 11px;
}

.export-select {
  flex: 1;
  padding: 4px 8px;
  background: #252538;
  border: 1px solid #3a3a5c;
  border-radius: 4px;
  color: #ccc;
  font-size: 11px;
}

.export-slider {
  flex: 1;
  accent-color: #4a90d9;
  height: 4px;
}

.export-val {
  min-width: 36px;
  color: #4a90d9;
  font-size: 11px;
}

.export-duration {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 6px;
}

.export-input {
  width: 60px;
  padding: 4px 8px;
  background: #252538;
  border: 1px solid #3a3a5c;
  border-radius: 4px;
  color: #ccc;
  font-size: 11px;
}

.export-hint {
  color: #666;
  font-size: 10px;
}

.export-info {
  padding: 8px;
  background: #13131f;
  border-radius: 4px;
  color: #888;
  font-size: 10px;
}

.export-start-btn {
  padding: 8px 16px;
  background: #1a3a6b;
  border: 1px solid #4a90d9;
  border-radius: 4px;
  color: #4a90d9;
  font-size: 12px;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
  font-weight: 600;
}

.export-start-btn:hover {
  background: #2a4a8b;
  color: #fff;
}

/* Export Progress Overlay */
.export-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.85);
  z-index: 20;
}

.export-progress-box {
  width: 320px;
  background: #1a1a2e;
  border: 1px solid #3a3a5c;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
}

.export-progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  color: #ddd;
  font-weight: 600;
}

.export-cancel-btn {
  padding: 4px 10px;
  background: #5c1a1a;
  border: 1px solid #e74c3c;
  border-radius: 4px;
  color: #e74c3c;
  font-size: 11px;
  cursor: pointer;
}

.export-cancel-btn:hover {
  background: #7c2a2a;
  color: #fff;
}

.export-progress-info {
  color: #888;
  font-size: 11px;
  margin-bottom: 8px;
}

.export-progress-track {
  width: 100%;
  height: 6px;
  background: #252538;
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 8px;
}

.export-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #4a90d9, #2ecc71);
  transition: width 0.2s;
}

.export-progress-stats {
  color: #666;
  font-size: 10px;
  text-align: center;
}

/* Toast notifications */
.export-toast {
  position: absolute;
  bottom: 100px;
  left: 50%;
  transform: translateX(-50%);
  padding: 10px 20px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  z-index: 25;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
}

.export-toast.success {
  background: #1a4a3a;
  border: 1px solid #2ecc71;
  color: #2ecc71;
}

.export-toast.error {
  background: #5c1a1a;
  border: 1px solid #e74c3c;
  color: #e74c3c;
}
</style>
