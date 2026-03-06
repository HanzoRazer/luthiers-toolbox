<script setup lang="ts">
/**
 * ImageActionsPanel - Action buttons for AI image operations
 * Extracted from AiImageProperties.vue
 */
defineEmits<{
  attach: []
  download: []
  regenerate: []
  delete: []
  vectorize: []  // Send to Blueprint Lab for vectorization
}>()
</script>

<template>
  <div class="actions-section">
    <h4>Actions</h4>

    <button
      class="action-btn primary"
      @click="$emit('attach')"
    >
      <span>📎</span>
      <span>Attach to Design</span>
    </button>

    <button
      class="action-btn"
      @click="$emit('download')"
    >
      <span>⬇️</span>
      <span>Download PNG</span>
    </button>
    <button
      class="action-btn accent"
      @click="$emit('vectorize')"
    >
      <span>📐</span>
      <span>Send to Blueprint Lab</span>
    </button>

    <button
      class="action-btn"
      @click="$emit('regenerate')"
    >
      <span>🔄</span>
      <span>Regenerate</span>
    </button>

    <button
      class="action-btn danger"
      @click="$emit('delete')"
    >
      <span>🗑️</span>
      <span>Delete</span>
    </button>
  </div>
</template>

<style scoped>
.actions-section {
  padding: 16px;
  border-bottom: 1px solid var(--border, #2a3f5f);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.actions-section h4 {
  font-size: 12px;
  color: var(--text-dim, #8892a0);
  text-transform: uppercase;
  margin: 0 0 8px 0;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border, #2a3f5f);
}

.action-btn {
  background: var(--bg-input, #0f1629);
  border: 1px solid var(--border, #2a3f5f);
  border-radius: 6px;
  padding: 10px 12px;
  color: var(--text, #e0e0e0);
  font-size: 13px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.15s;
}

.action-btn:hover {
  border-color: var(--accent, #4fc3f7);
  background: rgba(79, 195, 247, 0.1);
}

.action-btn.primary {
  background: var(--accent, #4fc3f7);
  border-color: var(--accent, #4fc3f7);
  color: #000;
}

.action-btn.primary:hover {
  background: var(--accent-hover, #81d4fa);
}

.action-btn.danger:hover {
  border-color: #f44336;
  background: rgba(244, 67, 54, 0.1);
  color: #f44336;
}
.action-btn.accent {
  border-color: #9c27b0;
  color: #ce93d8;
}

.action-btn.accent:hover {
  border-color: #ba68c8;
  background: rgba(156, 39, 176, 0.15);
}
</style>
