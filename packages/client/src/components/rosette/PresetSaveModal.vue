<template>
  <div v-if="open" class="modal-backdrop" @click.self="emit('close')">
    <div class="modal" role="dialog" aria-modal="true" aria-label="Save preset">
      <div class="modal-header">
        <div class="modal-title">Save Preset</div>
        <button class="close-btn" type="button" @click="emit('close')" aria-label="Close">×</button>
      </div>

      <div class="modal-body">
        <!-- Dirty warning -->
        <div v-if="mode === 'dirty'" class="warning">
          <strong>{{ presetName }}</strong> has unsaved changes.
        </div>

        <!-- New preset name input -->
        <div v-if="showNameInput" class="name-input">
          <label for="preset-name">New preset name</label>
          <input
            id="preset-name"
            ref="nameInputRef"
            v-model="newName"
            type="text"
            placeholder="Enter name..."
            @keyup.enter="handleSaveNew"
          />
        </div>
      </div>

      <div class="modal-footer">
        <button class="btn cancel" type="button" @click="emit('close')">
          Cancel
        </button>

        <template v-if="mode === 'dirty'">
          <button class="btn secondary" type="button" @click="startSaveNew">
            Save as New
          </button>
          <button class="btn primary" type="button" @click="handleOverwrite">
            Overwrite
          </button>
        </template>

        <template v-else-if="mode === 'new'">
          <button class="btn primary" type="button" @click="handleSaveNew" :disabled="!newName.trim()">
            Save
          </button>
        </template>

        <template v-else-if="mode === 'saveNew'">
          <button class="btn primary" type="button" @click="handleSaveNew" :disabled="!newName.trim()">
            Save as New
          </button>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * PresetSaveModal.vue
 * Bundle 32.6.5: Replace prompt() with modal for preset save UX
 *
 * Modes:
 * - "dirty": Selected preset has changes. Show Overwrite / Save as New / Cancel
 * - "new": No preset selected. Show name input + Save / Cancel
 * - "saveNew": User clicked "Save as New" from dirty mode. Show name input.
 */
import { ref, watch, nextTick } from "vue";

const props = defineProps<{
  open: boolean;
  presetName: string;
  suggestedName: string;
  isDirty: boolean;
}>();

const emit = defineEmits<{
  (e: "close"): void;
  (e: "overwrite"): void;
  (e: "saveNew", name: string): void;
}>();

const mode = ref<"dirty" | "new" | "saveNew">("dirty");
const newName = ref("");
const nameInputRef = ref<HTMLInputElement | null>(null);

const showNameInput = computed(() => mode.value === "new" || mode.value === "saveNew");

import { computed } from "vue";

// Reset state when modal opens
watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) {
      if (props.isDirty && props.presetName) {
        mode.value = "dirty";
        newName.value = `${props.presetName} (variant)`;
      } else {
        mode.value = "new";
        newName.value = props.suggestedName || "";
        nextTick(() => nameInputRef.value?.focus());
      }
    }
  }
);

function startSaveNew() {
  mode.value = "saveNew";
  newName.value = `${props.presetName} (variant)`;
  nextTick(() => nameInputRef.value?.focus());
}

function handleOverwrite() {
  emit("overwrite");
  emit("close");
}

function handleSaveNew() {
  const name = newName.value.trim();
  if (!name) return;
  emit("saveNew", name);
  emit("close");
}
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  z-index: 9999;
}

.modal {
  width: min(400px, 94vw);
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 16px 60px rgba(0, 0, 0, 0.25);
  overflow: hidden;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  border-bottom: 1px solid #eee;
}

.modal-title {
  font-weight: 700;
}

.close-btn {
  border: 0;
  background: transparent;
  font-size: 18px;
  cursor: pointer;
}

.modal-body {
  padding: 14px;
}

.warning {
  background: #fff8e6;
  border: 1px solid #f0d060;
  border-radius: 8px;
  padding: 10px 12px;
  margin-bottom: 12px;
  font-size: 0.9rem;
}

.name-input {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.name-input label {
  font-size: 0.85rem;
  font-weight: 600;
  color: #555;
}

.name-input input {
  padding: 8px 10px;
  border: 1px solid #ccc;
  border-radius: 8px;
  font-size: 0.95rem;
}

.name-input input:focus {
  outline: none;
  border-color: #0066cc;
  box-shadow: 0 0 0 2px rgba(0, 102, 204, 0.15);
}

.modal-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  padding: 12px 14px;
  border-top: 1px solid #eee;
}

.btn {
  padding: 8px 14px;
  border-radius: 8px;
  font-size: 0.9rem;
  cursor: pointer;
  border: 1px solid #ccc;
  background: #fff;
  transition: background 0.15s, border-color 0.15s;
}

.btn:hover {
  background: #f5f5f5;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn.cancel {
  color: #666;
}

.btn.secondary {
  background: #f0f0f0;
  border-color: #ddd;
}

.btn.secondary:hover {
  background: #e5e5e5;
}

.btn.primary {
  background: #0066cc;
  border-color: #0066cc;
  color: #fff;
}

.btn.primary:hover {
  background: #0055aa;
}

.btn.primary:disabled {
  background: #88b3dd;
  border-color: #88b3dd;
}
</style>
