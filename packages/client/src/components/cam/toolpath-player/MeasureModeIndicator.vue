<script setup lang="ts">
/**
 * MeasureModeIndicator — Measurement mode status indicator for ToolpathPlayer
 *
 * Extracted from ToolpathPlayer.vue to reduce component size.
 * Shows current measurement state with pulsing animation.
 */

interface Props {
  pendingStart: boolean;
}

defineProps<Props>();

const emit = defineEmits<{
  cancel: [];
}>();
</script>

<template>
  <div class="measure-indicator">
    <span v-if="!pendingStart">Click first point</span>
    <span v-else>Click second point</span>
    <button
      class="measure-cancel"
      @click="emit('cancel')"
    >
      Cancel
    </button>
  </div>
</template>

<style scoped>
.measure-indicator {
  position: absolute;
  top: 10px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 16px;
  background: rgba(0, 255, 255, 0.15);
  border: 1px solid #00ffff;
  border-radius: 6px;
  font-size: 12px;
  color: #00ffff;
  z-index: 15;
  animation: pulse-border 1.5s ease-in-out infinite;
}

@keyframes pulse-border {
  0%, 100% { box-shadow: 0 0 5px rgba(0, 255, 255, 0.3); }
  50% { box-shadow: 0 0 15px rgba(0, 255, 255, 0.6); }
}

.measure-cancel {
  padding: 3px 10px;
  background: transparent;
  border: 1px solid #00ffff;
  border-radius: 4px;
  color: #00ffff;
  font-size: 11px;
  cursor: pointer;
  transition: background 0.15s;
}

.measure-cancel:hover {
  background: rgba(0, 255, 255, 0.2);
}
</style>
