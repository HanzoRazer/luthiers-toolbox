<script setup lang="ts">
/**
 * PanelContainer — Reusable panel wrapper for ToolpathPlayer
 *
 * Provides consistent styling for floating panels with:
 * - Header with title and close button
 * - Optional header actions slot
 * - Customizable position and accent color
 */
import { computed } from 'vue';

type Position = 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right';
type AccentColor = 'blue' | 'orange' | 'cyan' | 'purple' | 'green' | 'red';

interface Props {
  title: string;
  position?: Position;
  accent?: AccentColor;
  width?: string;
  maxHeight?: string;
  zIndex?: number;
}

const props = withDefaults(defineProps<Props>(), {
  position: 'top-left',
  accent: 'blue',
  width: '380px',
  maxHeight: 'calc(100% - 120px)',
  zIndex: 12,
});

const emit = defineEmits<{
  close: [];
}>();

const positionStyles = computed(() => {
  const styles: Record<string, string> = {};
  if (props.position.includes('top')) styles.top = '10px';
  if (props.position.includes('bottom')) styles.bottom = '90px';
  if (props.position.includes('left')) styles.left = '10px';
  if (props.position.includes('right')) styles.right = '10px';
  return styles;
});

const accentColors: Record<AccentColor, { border: string; bg: string; text: string }> = {
  blue: { border: '#3498db', bg: '#1a2a4a', text: '#3498db' },
  orange: { border: '#f39c12', bg: '#3a2a1a', text: '#f39c12' },
  cyan: { border: '#00ffff', bg: 'rgba(0,255,255,0.1)', text: '#00ffff' },
  purple: { border: '#9b59b6', bg: '#2a1a3a', text: '#9b59b6' },
  green: { border: '#2ecc71', bg: '#1a3a2a', text: '#2ecc71' },
  red: { border: '#e74c3c', bg: '#3a1a1a', text: '#e74c3c' },
};

const colors = computed(() => accentColors[props.accent]);
</script>

<template>
  <div
    class="panel-container"
    :style="{
      ...positionStyles,
      width: props.width,
      maxHeight: props.maxHeight,
      zIndex: props.zIndex,
      borderColor: colors.border,
    }"
  >
    <div
      class="panel-header"
      :style="{
        background: `linear-gradient(135deg, ${colors.bg} 0%, #1a1a2e 100%)`,
        borderColor: colors.border,
        color: colors.text,
      }"
    >
      <span>{{ title }}</span>
      <div class="panel-header-actions">
        <slot name="actions" />
        <button
          class="close-btn"
          :style="{ '--hover-color': colors.text }"
          @click="emit('close')"
        >
          x
        </button>
      </div>
    </div>
    <div class="panel-content">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.panel-container {
  position: absolute;
  background: #1a1a2e;
  border: 1px solid;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  border-bottom: 1px solid;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.panel-header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.close-btn {
  background: transparent;
  border: none;
  color: #666;
  cursor: pointer;
  font-size: 14px;
  padding: 0 4px;
  transition: color 0.15s;
}

.close-btn:hover {
  color: var(--hover-color, #e74c3c);
}

.panel-content {
  flex: 1;
  overflow: auto;
}

/* Slot for action buttons in header */
:slotted(.action-btn) {
  font-size: 10px;
  padding: 2px 6px;
  background: #252538;
  border: 1px solid #3a3a5c;
  border-radius: 3px;
  color: #888;
  cursor: pointer;
}

:slotted(.action-btn:hover) {
  background: #33334a;
  color: #fff;
}
</style>
