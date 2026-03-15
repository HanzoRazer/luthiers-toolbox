<script setup lang="ts">
/**
 * KeyboardShortcutsOverlay — Keyboard shortcuts help overlay for ToolpathPlayer
 *
 * Extracted from ToolpathPlayer.vue to reduce component size.
 * Shows categorized keyboard shortcuts in a modal overlay.
 */
import { computed } from 'vue';

interface Shortcut {
  key: string;
  description: string;
  category: 'playback' | 'view' | 'tools' | 'navigation';
}

interface Props {
  shortcuts: Shortcut[];
}

const props = defineProps<Props>();

const emit = defineEmits<{
  close: [];
}>();

const categories = ['playback', 'view', 'tools', 'navigation'] as const;

function getShortcutsForCategory(cat: typeof categories[number]) {
  return props.shortcuts.filter(s => s.category === cat);
}
</script>

<template>
  <div
    class="shortcuts-overlay"
    @click.self="emit('close')"
  >
    <div class="shortcuts-panel">
      <div class="panel-header">
        <span>Keyboard Shortcuts</span>
        <button @click="emit('close')">✕</button>
      </div>
      <div class="shortcuts-grid">
        <div
          v-for="cat in categories"
          :key="cat"
          class="shortcuts-category"
        >
          <h4 class="shortcuts-cat-title">{{ cat }}</h4>
          <ul class="shortcuts-list">
            <li
              v-for="s in getShortcutsForCategory(cat)"
              :key="s.key"
              class="shortcut-item"
            >
              <kbd class="shortcut-key">{{ s.key }}</kbd>
              <span class="shortcut-desc">{{ s.description }}</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.shortcuts-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.85);
  z-index: 25;
  animation: fade-in 0.15s ease;
}

@keyframes fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

.shortcuts-panel {
  width: 600px;
  max-width: 90vw;
  max-height: 80vh;
  background: #1a1a2e;
  border: 1px solid #9b59b6;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 8px 40px rgba(155, 89, 182, 0.3);
  animation: scale-in 0.2s ease;
}

@keyframes scale-in {
  from { transform: scale(0.95); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, #2a1a3a 0%, #1a1a2e 100%);
  border-bottom: 1px solid #9b59b6;
  padding: 12px 16px;
  color: #9b59b6;
  font-size: 14px;
  font-weight: 600;
}

.panel-header button {
  background: transparent;
  border: none;
  color: #666;
  cursor: pointer;
  font-size: 14px;
  padding: 0 4px;
}

.panel-header button:hover {
  color: #9b59b6;
}

.shortcuts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  padding: 16px;
  max-height: calc(80vh - 60px);
  overflow-y: auto;
}

.shortcuts-category {
  background: #252538;
  border-radius: 8px;
  padding: 12px;
}

.shortcuts-cat-title {
  margin: 0 0 10px 0;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #9b59b6;
  border-bottom: 1px solid #3a3a5c;
  padding-bottom: 6px;
}

.shortcuts-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.shortcut-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 5px 0;
  font-size: 12px;
}

.shortcut-key {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 28px;
  height: 24px;
  padding: 0 8px;
  background: linear-gradient(180deg, #3a3a5c 0%, #252538 100%);
  border: 1px solid #4a4a6c;
  border-radius: 4px;
  font-family: inherit;
  font-size: 11px;
  font-weight: 600;
  color: #ddd;
  box-shadow: 0 2px 0 #1a1a2e;
}

.shortcut-desc {
  color: #aaa;
  flex: 1;
}
</style>
