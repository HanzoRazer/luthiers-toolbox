<script setup lang="ts">
/**
 * EstimatorPresetsPanel - Save and load estimate presets
 *
 * Features:
 * - Save current form state as a named preset
 * - Load presets to populate form
 * - Delete presets
 * - Persistent storage in localStorage
 */
import { ref, computed, onMounted } from "vue";
import type { EstimateRequest } from "@/types/businessEstimator";

const props = defineProps<{
  currentRequest: EstimateRequest;
}>();

const emit = defineEmits<{
  loadPreset: [request: EstimateRequest];
}>();

// ============================================================================
// TYPES
// ============================================================================

interface Preset {
  id: string;
  name: string;
  description: string;
  request: EstimateRequest;
  createdAt: string;
  updatedAt: string;
}

// ============================================================================
// CONSTANTS
// ============================================================================

const STORAGE_KEY = "ltb:estimator:presets:v1";

// ============================================================================
// STATE
// ============================================================================

const presets = ref<Preset[]>([]);
const showSaveDialog = ref(false);
const newPresetName = ref("");
const newPresetDescription = ref("");
const selectedPresetId = ref<string | null>(null);
const confirmDeleteId = ref<string | null>(null);

// ============================================================================
// COMPUTED
// ============================================================================

const sortedPresets = computed(() => {
  return [...presets.value].sort(
    (a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
  );
});

const selectedPreset = computed(() => {
  return presets.value.find((p) => p.id === selectedPresetId.value) ?? null;
});

const canSave = computed(() => {
  return newPresetName.value.trim().length > 0;
});

// ============================================================================
// PERSISTENCE
// ============================================================================

function loadPresets(): void {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      presets.value = JSON.parse(stored);
    }
  } catch (e) {
    console.warn("[EstimatorPresetsPanel] Failed to load presets:", e);
    presets.value = [];
  }
}

function savePresets(): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(presets.value));
  } catch (e) {
    console.warn("[EstimatorPresetsPanel] Failed to save presets:", e);
  }
}

// ============================================================================
// ACTIONS
// ============================================================================

function openSaveDialog(): void {
  newPresetName.value = "";
  newPresetDescription.value = "";
  showSaveDialog.value = true;
}

function closeSaveDialog(): void {
  showSaveDialog.value = false;
}

function saveNewPreset(): void {
  if (!canSave.value) return;

  const now = new Date().toISOString();
  const preset: Preset = {
    id: `preset_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
    name: newPresetName.value.trim(),
    description: newPresetDescription.value.trim(),
    request: { ...props.currentRequest },
    createdAt: now,
    updatedAt: now,
  };

  presets.value.push(preset);
  savePresets();
  closeSaveDialog();
}

function updatePreset(presetId: string): void {
  const idx = presets.value.findIndex((p) => p.id === presetId);
  if (idx >= 0) {
    presets.value[idx] = {
      ...presets.value[idx],
      request: { ...props.currentRequest },
      updatedAt: new Date().toISOString(),
    };
    savePresets();
  }
}

function loadPreset(preset: Preset): void {
  emit("loadPreset", { ...preset.request });
  selectedPresetId.value = preset.id;
}

function confirmDelete(presetId: string): void {
  confirmDeleteId.value = presetId;
}

function cancelDelete(): void {
  confirmDeleteId.value = null;
}

function deletePreset(presetId: string): void {
  presets.value = presets.value.filter((p) => p.id !== presetId);
  savePresets();
  if (selectedPresetId.value === presetId) {
    selectedPresetId.value = null;
  }
  confirmDeleteId.value = null;
}

function formatDate(isoDate: string): string {
  return new Date(isoDate).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function formatInstrumentType(type: string): string {
  return type
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

// ============================================================================
// LIFECYCLE
// ============================================================================

onMounted(() => {
  loadPresets();
});
</script>

<template>
  <div class="presets-panel">
    <header class="panel-header">
      <h3>Presets</h3>
      <button type="button" class="btn-save" @click="openSaveDialog">
        + Save Current
      </button>
    </header>

    <!-- Empty State -->
    <div v-if="presets.length === 0" class="empty-state">
      <p>No saved presets yet.</p>
      <p class="hint">Save your current configuration as a preset for quick access later.</p>
    </div>

    <!-- Preset List -->
    <div v-else class="preset-list">
      <div
        v-for="preset in sortedPresets"
        :key="preset.id"
        class="preset-card"
        :class="{ selected: selectedPresetId === preset.id }"
      >
        <div class="preset-info" @click="loadPreset(preset)">
          <div class="preset-name">{{ preset.name }}</div>
          <div class="preset-meta">
            {{ formatInstrumentType(preset.request.instrument_type) }}
            <span class="separator">·</span>
            {{ formatDate(preset.updatedAt) }}
          </div>
          <div v-if="preset.description" class="preset-description">
            {{ preset.description }}
          </div>
        </div>

        <div class="preset-actions">
          <button
            type="button"
            class="btn-icon"
            title="Update with current values"
            @click.stop="updatePreset(preset.id)"
          >
            ↻
          </button>
          <button
            v-if="confirmDeleteId !== preset.id"
            type="button"
            class="btn-icon delete"
            title="Delete preset"
            @click.stop="confirmDelete(preset.id)"
          >
            ×
          </button>
          <template v-else>
            <button
              type="button"
              class="btn-confirm-delete"
              @click.stop="deletePreset(preset.id)"
            >
              Delete
            </button>
            <button
              type="button"
              class="btn-cancel-delete"
              @click.stop="cancelDelete"
            >
              Cancel
            </button>
          </template>
        </div>
      </div>
    </div>

    <!-- Save Dialog -->
    <div v-if="showSaveDialog" class="save-dialog-overlay" @click.self="closeSaveDialog">
      <div class="save-dialog">
        <h4>Save Preset</h4>

        <label class="form-field">
          <span class="label">Name</span>
          <input
            v-model="newPresetName"
            type="text"
            placeholder="e.g., Dreadnought Standard"
            class="text-input"
            @keydown.enter="saveNewPreset"
          />
        </label>

        <label class="form-field">
          <span class="label">Description (optional)</span>
          <textarea
            v-model="newPresetDescription"
            placeholder="Notes about this configuration..."
            class="text-input"
            rows="2"
          ></textarea>
        </label>

        <div class="dialog-actions">
          <button type="button" class="btn-secondary" @click="closeSaveDialog">
            Cancel
          </button>
          <button
            type="button"
            class="btn-primary"
            :disabled="!canSave"
            @click="saveNewPreset"
          >
            Save Preset
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.presets-panel {
  background: #0d1020;
  border: 1px solid #1e2438;
  border-radius: 4px;
  padding: 16px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.panel-header h3 {
  font-size: 10px;
  letter-spacing: 2px;
  color: #4060c0;
  text-transform: uppercase;
  margin: 0;
}

.btn-save {
  padding: 6px 12px;
  font-size: 10px;
  font-family: inherit;
  letter-spacing: 1px;
  background: #2050a0;
  border: 1px solid #3060c0;
  color: #e0e8ff;
  border-radius: 3px;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-save:hover {
  background: #2860c0;
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 24px 16px;
  color: #506090;
}

.empty-state p {
  margin: 0;
  font-size: 12px;
}

.empty-state .hint {
  font-size: 11px;
  color: #404870;
  margin-top: 8px;
}

/* Preset List */
.preset-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 300px;
  overflow-y: auto;
}

.preset-card {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  background: #14192a;
  border: 1px solid #1e2438;
  border-radius: 4px;
  padding: 10px 12px;
  cursor: pointer;
  transition: all 0.15s;
}

.preset-card:hover {
  border-color: #3060c0;
}

.preset-card.selected {
  border-color: #4080f0;
  background: #1a2040;
}

.preset-info {
  flex: 1;
  min-width: 0;
}

.preset-name {
  font-size: 12px;
  font-weight: 600;
  color: #c0c8e0;
  margin-bottom: 4px;
}

.preset-meta {
  font-size: 10px;
  color: #506090;
}

.separator {
  margin: 0 6px;
  color: #2a3040;
}

.preset-description {
  font-size: 10px;
  color: #606888;
  margin-top: 6px;
  font-style: italic;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Preset Actions */
.preset-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-left: 12px;
}

.btn-icon {
  width: 24px;
  height: 24px;
  padding: 0;
  font-size: 14px;
  font-family: inherit;
  background: transparent;
  border: 1px solid #2a3040;
  color: #6080b0;
  border-radius: 3px;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-icon:hover {
  border-color: #4060c0;
  color: #80a0d0;
}

.btn-icon.delete:hover {
  border-color: #c04040;
  color: #f06060;
}

.btn-confirm-delete,
.btn-cancel-delete {
  padding: 4px 8px;
  font-size: 9px;
  font-family: inherit;
  border-radius: 3px;
  cursor: pointer;
}

.btn-confirm-delete {
  background: #802020;
  border: 1px solid #a03030;
  color: #ffb0b0;
}

.btn-cancel-delete {
  background: transparent;
  border: 1px solid #2a3040;
  color: #6080b0;
}

/* Save Dialog */
.save-dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.save-dialog {
  background: #0d1020;
  border: 1px solid #2a3040;
  border-radius: 6px;
  padding: 20px;
  width: 100%;
  max-width: 400px;
}

.save-dialog h4 {
  font-size: 12px;
  letter-spacing: 2px;
  color: #f0c060;
  text-transform: uppercase;
  margin: 0 0 16px;
}

.form-field {
  display: block;
  margin-bottom: 12px;
}

.form-field .label {
  display: block;
  font-size: 9px;
  letter-spacing: 1px;
  color: #506090;
  text-transform: uppercase;
  margin-bottom: 6px;
}

.text-input {
  width: 100%;
  background: #14192a;
  border: 1px solid #2a3040;
  color: #e0e8ff;
  padding: 8px 10px;
  font-size: 12px;
  font-family: inherit;
  border-radius: 3px;
  resize: vertical;
}

.text-input:focus {
  outline: none;
  border-color: #4060c0;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #1e2438;
}

.btn-secondary,
.btn-primary {
  padding: 8px 16px;
  font-size: 10px;
  font-family: inherit;
  letter-spacing: 1px;
  text-transform: uppercase;
  border-radius: 3px;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-secondary {
  background: #14192a;
  border: 1px solid #2a3040;
  color: #8090b0;
}

.btn-secondary:hover {
  border-color: #4060c0;
  color: #c0c8e0;
}

.btn-primary {
  background: #2050a0;
  border: 1px solid #3060c0;
  color: #e0e8ff;
}

.btn-primary:hover {
  background: #2860c0;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
