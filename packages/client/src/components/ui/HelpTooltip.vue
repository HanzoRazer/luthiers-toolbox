<script setup lang="ts">
/**
 * HelpTooltip.vue - Contextual help tooltip with "?" icon
 *
 * Displays help text on hover/focus. Use for inline parameter explanations
 * without cluttering the UI with visible text.
 */
defineOptions({ name: 'HelpTooltip' })

type Position = 'top' | 'bottom' | 'left' | 'right'

withDefaults(defineProps<{
  text: string
  position?: Position
  maxWidth?: string
}>(), {
  position: 'top',
  maxWidth: '250px',
})
</script>

<template>
  <span class="help-tooltip" :class="position">
    <button
      type="button"
      class="help-trigger"
      aria-label="Help"
      tabindex="0"
    >
      ?
    </button>
    <span
      class="help-content"
      role="tooltip"
      :style="{ maxWidth }"
    >
      {{ text }}
    </span>
  </span>
</template>

<style scoped>
.help-tooltip {
  position: relative;
  display: inline-flex;
  align-items: center;
}

.help-trigger {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1rem;
  height: 1rem;
  font-size: 0.625rem;
  font-weight: 600;
  color: #6b7280;
  background: #e5e7eb;
  border: none;
  border-radius: 50%;
  cursor: help;
  transition: background-color 0.15s, color 0.15s;
}

.help-trigger:hover,
.help-trigger:focus {
  background: #2563eb;
  color: white;
  outline: none;
}

.help-content {
  position: absolute;
  z-index: 50;
  padding: 0.5rem 0.75rem;
  font-size: 0.75rem;
  line-height: 1.4;
  color: white;
  background: #1f2937;
  border-radius: 0.375rem;
  box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
  white-space: normal;
  word-wrap: break-word;
  opacity: 0;
  visibility: hidden;
  transition: opacity 0.15s, visibility 0.15s;
  pointer-events: none;
}

/* Show on hover/focus */
.help-trigger:hover + .help-content,
.help-trigger:focus + .help-content {
  opacity: 1;
  visibility: visible;
}

/* Position variants */
.help-tooltip.top .help-content {
  bottom: calc(100% + 0.5rem);
  left: 50%;
  transform: translateX(-50%);
}

.help-tooltip.bottom .help-content {
  top: calc(100% + 0.5rem);
  left: 50%;
  transform: translateX(-50%);
}

.help-tooltip.left .help-content {
  right: calc(100% + 0.5rem);
  top: 50%;
  transform: translateY(-50%);
}

.help-tooltip.right .help-content {
  left: calc(100% + 0.5rem);
  top: 50%;
  transform: translateY(-50%);
}

/* Arrow */
.help-content::after {
  content: '';
  position: absolute;
  border: 5px solid transparent;
}

.help-tooltip.top .help-content::after {
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border-top-color: #1f2937;
}

.help-tooltip.bottom .help-content::after {
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  border-bottom-color: #1f2937;
}

.help-tooltip.left .help-content::after {
  left: 100%;
  top: 50%;
  transform: translateY(-50%);
  border-left-color: #1f2937;
}

.help-tooltip.right .help-content::after {
  right: 100%;
  top: 50%;
  transform: translateY(-50%);
  border-right-color: #1f2937;
}
</style>
