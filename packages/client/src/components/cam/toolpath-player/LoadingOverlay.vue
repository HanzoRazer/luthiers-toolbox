<script setup lang="ts">
/**
 * LoadingOverlay — Loading spinner with progress for ToolpathPlayer
 *
 * Extracted from ToolpathPlayer.vue to reduce component size.
 * Shows loading state with animated spinner and progress bar.
 */

interface ParseProgress {
  stage: 'uploading' | 'simulating' | 'idle' | 'complete';
  percent: number;
}

interface Props {
  progress: ParseProgress;
}

defineProps<Props>();

function getStageLabel(stage: string): string {
  switch (stage) {
    case 'uploading': return 'Uploading…';
    case 'simulating': return 'Simulating…';
    default: return 'Loading…';
  }
}
</script>

<template>
  <div class="loading-overlay">
    <div class="loading-inner">
      <svg
        class="spinner"
        viewBox="0 0 24 24"
        fill="none"
      >
        <circle
          cx="12"
          cy="12"
          r="10"
          stroke="#4A90D9"
          stroke-width="2"
          stroke-dasharray="32"
          stroke-linecap="round"
        />
      </svg>
      <div class="progress-box">
        <span class="progress-label">
          {{ getStageLabel(progress.stage) }} {{ progress.percent }}%
        </span>
        <div class="progress-track">
          <div
            class="progress-fill"
            :style="{ width: progress.percent + '%' }"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.loading-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  font-size: 13px;
  color: #888;
  background: rgba(30, 30, 46, 0.85);
  pointer-events: none;
  z-index: 5;
}

.loading-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  min-width: 260px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.spinner {
  width: 28px;
  height: 28px;
  animation: spin 1s linear infinite;
}

.progress-box {
  width: 100%;
}

.progress-label {
  display: block;
  text-align: center;
  color: #4A90D9;
  font-size: 12px;
  margin-bottom: 6px;
}

.progress-track {
  width: 100%;
  height: 5px;
  background: #2a2a4a;
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #4A90D9, #2ECC71);
  transition: width 0.2s;
}
</style>
