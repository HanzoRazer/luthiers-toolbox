<template>
  <div
    v-if="show"
    class="modal-backdrop"
    @click.self="$emit('close')"
  >
    <div class="modal">
      <div class="modal-header">
        <h3>Override Required</h3>
        <button
          class="icon-btn"
          :disabled="isSubmitting"
          @click="$emit('close')"
        >
          ×
        </button>
      </div>
      <p class="muted">
        This run is <strong>YELLOW</strong>. To download an operator pack, record an override reason for audit.
      </p>

      <label class="field">
        <div class="label">Reason (required)</div>
        <textarea
          v-model="reason"
          rows="4"
          placeholder="Why is it safe to proceed?"
        />
      </label>

      <label class="field">
        <div class="label">Operator (optional)</div>
        <input
          v-model="operator"
          type="text"
          placeholder="Name / initials"
        >
      </label>

      <div
        v-if="error"
        class="override-error"
      >
        {{ error }}
      </div>

      <div class="modal-actions">
        <button
          class="btn-secondary"
          :disabled="isSubmitting"
          @click="$emit('close')"
        >
          Cancel
        </button>
        <button
          class="btn-primary"
          :disabled="isSubmitting"
          @click="submit"
        >
          {{ isSubmitting ? 'Submitting...' : 'Submit Override & Download' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  show: boolean
  isSubmitting?: boolean
  error?: string | null
}>()

const emit = defineEmits<{
  close: []
  submit: [reason: string, operator: string]
}>()

const reason = ref('')
const operator = ref('')

// Reset fields when modal opens
watch(() => props.show, (isOpen) => {
  if (isOpen) {
    reason.value = ''
    operator.value = ''
  }
})

function submit() {
  const trimmedReason = reason.value.trim()
  if (!trimmedReason) return
  emit('submit', trimmedReason, operator.value.trim())
}
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  z-index: 50;
}

.modal {
  width: 100%;
  max-width: 560px;
  background: white;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.18);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.125rem;
}

.icon-btn {
  border: none;
  background: transparent;
  font-size: 18px;
  cursor: pointer;
  padding: 4px 8px;
  color: #6b7280;
}

.icon-btn:hover {
  color: #374151;
}

.muted {
  color: #6b7280;
  font-size: 0.875rem;
  margin: 0 0 16px 0;
}

.field {
  display: block;
  margin-top: 12px;
}

.field .label {
  font-size: 0.75rem;
  color: #6b7280;
  margin-bottom: 6px;
  font-weight: 500;
}

.field textarea,
.field input {
  width: 100%;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 10px;
  font-size: 0.875rem;
  box-sizing: border-box;
}

.field textarea:focus,
.field input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
}

.override-error {
  margin-top: 12px;
  color: #b91c1c;
  font-size: 0.875rem;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 20px;
}

.btn-secondary {
  padding: 0.5rem 1rem;
  background: #e5e7eb;
  color: #374151;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
}

.btn-secondary:hover:not(:disabled) {
  background: #d1d5db;
}

.btn-secondary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  padding: 0.5rem 1rem;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
}

.btn-primary:hover:not(:disabled) {
  background: #2563eb;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
