<script setup lang="ts">
/**
 * GcodeSourcePanel — G-code source viewer panel for ToolpathPlayer
 *
 * Extracted from ToolpathPlayer.vue to reduce component size.
 * Shows the G-code source with line numbers and selection highlighting.
 */
import GcodeViewer from '../GcodeViewer.vue';

interface Props {
  hasSelection: boolean;
  maxHeight?: string;
}

const props = withDefaults(defineProps<Props>(), {
  maxHeight: '250px',
});

const emit = defineEmits<{
  close: [];
  clearSelection: [];
}>();
</script>

<template>
  <div class="gcode-panel">
    <div class="panel-header">
      <span>G-code Source</span>
      <div class="panel-header-actions">
        <button
          v-if="hasSelection"
          class="clear-selection-btn"
          title="Clear selection"
          @click="emit('clearSelection')"
        >
          Clear
        </button>
        <button @click="emit('close')">✕</button>
      </div>
    </div>
    <GcodeViewer
      :max-height="maxHeight"
      :show-line-numbers="true"
      :auto-scroll="true"
    />
  </div>
</template>

<style scoped>
.gcode-panel {
  position: absolute;
  left: 10px;
  bottom: 90px;
  width: 400px;
  max-height: 320px;
  background: #1a1a2e;
  border: 1px solid #3a3a5c;
  border-radius: 8px;
  overflow: hidden;
  z-index: 10;
  font-size: 11px;
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

.panel-header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.panel-header-actions button {
  background: transparent;
  border: none;
  color: #666;
  cursor: pointer;
  font-size: 14px;
  padding: 0 4px;
}
.panel-header-actions button:hover { color: #e74c3c; }

.clear-selection-btn {
  font-size: 10px !important;
  padding: 2px 6px !important;
  background: #252538 !important;
  border: 1px solid #3a3a5c !important;
  border-radius: 3px;
  color: #888 !important;
}
.clear-selection-btn:hover {
  background: #33334a !important;
  color: #ffd700 !important;
}
</style>
