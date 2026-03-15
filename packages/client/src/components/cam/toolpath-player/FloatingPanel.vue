<script setup lang="ts">
/**
 * FloatingPanel — Positioned panel wrapper for ToolpathPlayer
 *
 * Extracted from ToolpathPlayer.vue to reduce component size.
 * Provides consistent positioning for floating panels.
 */

interface Props {
  position?: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right';
  width?: string;
  zIndex?: number;
  accent?: string;
}

const props = withDefaults(defineProps<Props>(), {
  position: 'top-right',
  width: '320px',
  zIndex: 15,
  accent: '#4a90d9',
});

const positionStyles = {
  'top-left': { left: '10px', top: '10px' },
  'top-right': { right: '10px', top: '10px' },
  'bottom-left': { left: '10px', bottom: '120px' },
  'bottom-right': { right: '10px', bottom: '120px' },
};
</script>

<template>
  <div
    class="floating-panel"
    :style="{
      ...positionStyles[props.position],
      width: props.width,
      zIndex: props.zIndex,
      '--panel-accent': props.accent,
    }"
  >
    <slot />
  </div>
</template>

<style scoped>
.floating-panel {
  position: absolute;
  max-height: calc(100% - 120px);
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 20px color-mix(in srgb, var(--panel-accent) 20%, transparent);
}

.floating-panel > :deep(*) {
  flex: 1;
  overflow: hidden;
  border: 1px solid var(--panel-accent);
  border-radius: 8px;
}
</style>
