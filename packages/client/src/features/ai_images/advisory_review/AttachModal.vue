<script setup lang="ts">
/**
 * AttachModal - Attach asset to run dialog
 * Extracted from AdvisoryReviewPanel.vue
 */
defineProps<{
  visible: boolean
  targetRunId: string
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  'update:targetRunId': [value: string]
  'confirm': []
}>()
</script>

<template>
  <div
    v-if="visible"
    class="modal-overlay"
    @click.self="emit('update:visible', false)"
  >
    <div class="modal">
      <h3>Attach to Run</h3>
      <input
        :value="targetRunId"
        placeholder="Enter Run ID..."
        type="text"
        @input="emit('update:targetRunId', ($event.target as HTMLInputElement).value)"
      >
      <div class="modal-actions">
        <button
          class="btn cancel"
          @click="emit('update:visible', false)"
        >
          Cancel
        </button>
        <button
          class="btn primary"
          :disabled="!targetRunId.trim()"
          @click="emit('confirm')"
        >
          Attach
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: var(--bg-panel, #16213e);
  border-radius: 12px;
  padding: 24px;
  min-width: 320px;
  max-width: 480px;
  color: var(--text, #e0e0e0);
}

.modal h3 {
  margin: 0 0 16px;
  font-size: 16px;
}

.modal input {
  width: 100%;
  background: var(--bg-input, #0f1629);
  border: 1px solid var(--border, #2a3f5f);
  border-radius: 6px;
  padding: 10px;
  color: var(--text);
  font-size: 13px;
  margin-bottom: 16px;
}

.modal input:focus {
  outline: none;
  border-color: var(--accent, #4fc3f7);
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.btn {
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s;
}

.btn.cancel {
  background: var(--bg-input);
  color: var(--text);
  border: 1px solid var(--border);
}

.btn.primary {
  background: var(--accent, #4fc3f7);
  color: black;
}

.btn:hover {
  opacity: 0.9;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
