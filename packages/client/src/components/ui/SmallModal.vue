<template>
  <div
    v-if="open"
    class="modal-backdrop"
    @click.self="cancel"
  >
    <div
      class="modal-card"
      role="dialog"
      aria-modal="true"
    >
      <div class="modal-header">
        <div class="modal-title">
          {{ title }}
        </div>
        <button
          class="modal-close"
          aria-label="Close"
          @click="cancel"
        >
          ×
        </button>
      </div>

      <div class="modal-body">
        <div
          v-if="message"
          class="modal-message"
        >
          {{ message }}
        </div>
        <input
          v-if="mode === 'prompt'"
          ref="inputRef"
          v-model="draft"
          class="modal-input"
          type="text"
          :placeholder="placeholder"
          @keydown.enter.prevent="ok"
        >
      </div>

      <div class="modal-footer">
        <button
          class="modal-btn ghost"
          @click="cancel"
        >
          {{ cancelText }}
        </button>
        <button
          v-for="b in extraButtons"
          :key="b.key"
          class="modal-btn ghost"
          @click="extra(b.key)"
        >
          {{ b.label }}
        </button>
        <button
          class="modal-btn primary"
          @click="ok"
        >
          {{ okText }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * SmallModal.vue (Bundle 32.6.5)
 *
 * Generic small modal for confirm/prompt dialogs.
 * Replaces browser prompt()/confirm() with consistent UI.
 *
 * Modes:
 * - "confirm": Just OK/Cancel buttons
 * - "prompt": Text input + OK/Cancel buttons
 */
import { ref, watch, nextTick, onMounted } from "vue";

type ExtraButton = { key: string; label: string };

const props = withDefaults(
  defineProps<{
    open: boolean;
    mode: "confirm" | "prompt";
    title: string;
    message?: string;
    placeholder?: string;
    initialValue?: string;
    okText?: string;
    cancelText?: string;
    extraButtons?: ExtraButton[];
  }>(),
  {
    message: "",
    placeholder: "",
    initialValue: "",
    okText: "OK",
    cancelText: "Cancel",
    extraButtons: () => [],
  }
);

const emit = defineEmits<{
  (e: "ok", value?: string): void;
  (e: "cancel"): void;
  (e: "extra", key: string, value?: string): void;
}>();

const draft = ref(props.initialValue);
const inputRef = ref<HTMLInputElement | null>(null);

// Reset and focus when modal opens
watch(
  () => props.open,
  async (isOpen) => {
    if (isOpen) {
      draft.value = props.initialValue;
      if (props.mode === "prompt") {
        await nextTick();
        inputRef.value?.focus();
        inputRef.value?.select();
      }
    }
  }
);

function ok() {
  if (props.mode === "prompt") {
    emit("ok", draft.value);
  } else {
    emit("ok");
  }
}

function cancel() {
  emit("cancel");
}

function extra(key: string) {
  emit("extra", key, props.mode === "prompt" ? draft.value : undefined);
}
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9000;
}

.modal-card {
  width: 420px;
  max-width: 90vw;
  border-radius: 14px;
  background: #fff;
  border: 1px solid rgba(0, 0, 0, 0.12);
  box-shadow: 0 14px 40px rgba(0, 0, 0, 0.18);
  animation: modal-pop 150ms ease-out;
}

@keyframes modal-pop {
  from {
    transform: scale(0.95);
    opacity: 0.8;
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 14px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}

.modal-title {
  font-weight: 700;
  font-size: 14px;
}

.modal-close {
  border: 0;
  background: transparent;
  font-size: 20px;
  cursor: pointer;
  opacity: 0.6;
  padding: 0 4px;
}

.modal-close:hover {
  opacity: 1;
}

.modal-body {
  padding: 14px;
}

.modal-message {
  font-size: 13px;
  opacity: 0.85;
  margin-bottom: 12px;
  white-space: pre-line;
}

.modal-input {
  width: 100%;
  border-radius: 10px;
  border: 1px solid rgba(0, 0, 0, 0.18);
  padding: 10px 12px;
  font-size: 13px;
}

.modal-input:focus {
  outline: none;
  border-color: rgba(0, 100, 200, 0.5);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 12px 14px;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
}

.modal-btn {
  border-radius: 10px;
  border: 1px solid rgba(0, 0, 0, 0.18);
  padding: 8px 14px;
  font-size: 12px;
  cursor: pointer;
  background: #fff;
  transition: background 0.1s;
}

.modal-btn:hover {
  background: rgba(0, 0, 0, 0.04);
}

.modal-btn.primary {
  font-weight: 700;
  background: rgba(0, 0, 0, 0.04);
}

.modal-btn.ghost {
  background: transparent;
}
</style>
