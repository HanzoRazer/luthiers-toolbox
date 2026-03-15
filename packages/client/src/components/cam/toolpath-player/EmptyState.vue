<script setup lang="ts">
/**
 * EmptyState — Empty/error state display for ToolpathPlayer
 *
 * Extracted from ToolpathPlayer.vue to reduce component size.
 * Shows empty state message or error message.
 */

interface Props {
  error?: string | null;
}

defineProps<Props>();
</script>

<template>
  <div
    v-if="error"
    class="state-overlay error"
  >
    <span>⚠ {{ error }}</span>
  </div>
  <div
    v-else
    class="state-overlay empty"
  >
    <span>No toolpath loaded</span>
  </div>
</template>

<style scoped>
.state-overlay {
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

.state-overlay.error {
  color: #e74c3c;
  pointer-events: auto;
}
</style>
