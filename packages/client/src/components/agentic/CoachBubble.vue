<script setup lang="ts">
/**
 * CoachBubble — M1 Advisory Mode directive renderer.
 *
 * Shows a single directive at a time with:
 * - Title and detail text
 * - "Helpful" (thumbs up) button
 * - "Too much" (thumbs down) button
 * - Dismiss (X) button
 *
 * Only renders when:
 * - VITE_AGENTIC_MODE=M1 (or M2)
 * - currentDirective is not null
 * - Directive hasn't been dismissed
 */

import { computed } from "vue";
import { useAgenticDirectiveStore } from "@/stores/agenticDirectiveStore";

const store = useAgenticDirectiveStore();

const directive = computed(() => store.currentDirective);
const isVisible = computed(() => store.isEnabled && directive.value !== null);

function onHelpful() {
  store.submitFeedback("helpful");
}

function onTooMuch() {
  store.submitFeedback("too_much");
}

function onDismiss() {
  store.dismissDirective();
}

// Action icon based on directive type
const actionIcon = computed(() => {
  switch (directive.value?.action) {
    case "INSPECT":
      return "🔍";
    case "REVIEW":
      return "📋";
    case "COMPARE":
      return "⚖️";
    case "DECIDE":
      return "🎯";
    case "CONFIRM":
      return "✅";
    default:
      return "💡";
  }
});
</script>

<template>
  <Transition name="coach-bubble">
    <div v-if="isVisible" class="coach-bubble" role="complementary" aria-label="Coach suggestion">
      <div class="coach-bubble__header">
        <span class="coach-bubble__icon">{{ actionIcon }}</span>
        <span class="coach-bubble__title">{{ directive?.title }}</span>
        <button
          class="coach-bubble__dismiss"
          @click="onDismiss"
          aria-label="Dismiss suggestion"
          title="Dismiss"
        >
          ×
        </button>
      </div>

      <p v-if="directive?.detail" class="coach-bubble__detail">
        {{ directive.detail }}
      </p>

      <div class="coach-bubble__actions">
        <button
          class="coach-bubble__btn coach-bubble__btn--helpful"
          @click="onHelpful"
          aria-label="Mark as helpful"
          title="Helpful"
        >
          👍 Helpful
        </button>
        <button
          class="coach-bubble__btn coach-bubble__btn--too-much"
          @click="onTooMuch"
          aria-label="Too much guidance"
          title="Too much"
        >
          👎 Too much
        </button>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.coach-bubble {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 1000;

  width: 320px;
  max-width: calc(100vw - 48px);

  background: var(--color-bg-elevated, #ffffff);
  border: 1px solid var(--color-border, #e0e0e0);
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);

  font-family: var(--font-family, system-ui, sans-serif);
}

.coach-bubble__header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px 8px;
}

.coach-bubble__icon {
  font-size: 1.25rem;
  flex-shrink: 0;
}

.coach-bubble__title {
  flex: 1;
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text-primary, #1a1a1a);
}

.coach-bubble__dismiss {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  padding: 0;
  border: none;
  background: transparent;
  color: var(--color-text-secondary, #666666);
  font-size: 1.25rem;
  line-height: 1;
  cursor: pointer;
  border-radius: 4px;
  transition: background-color 0.15s, color 0.15s;
}

.coach-bubble__dismiss:hover {
  background: var(--color-bg-hover, #f0f0f0);
  color: var(--color-text-primary, #1a1a1a);
}

.coach-bubble__detail {
  margin: 0;
  padding: 0 16px 12px;
  font-size: 0.875rem;
  color: var(--color-text-secondary, #666666);
  line-height: 1.4;
}

.coach-bubble__actions {
  display: flex;
  gap: 8px;
  padding: 0 16px 16px;
}

.coach-bubble__btn {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid var(--color-border, #e0e0e0);
  border-radius: 6px;
  background: var(--color-bg-secondary, #f5f5f5);
  color: var(--color-text-primary, #1a1a1a);
  font-size: 0.813rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.15s, border-color 0.15s;
}

.coach-bubble__btn:hover {
  background: var(--color-bg-hover, #e8e8e8);
}

.coach-bubble__btn--helpful:hover {
  border-color: var(--color-success, #22c55e);
  background: var(--color-success-bg, #dcfce7);
}

.coach-bubble__btn--too-much:hover {
  border-color: var(--color-warning, #f59e0b);
  background: var(--color-warning-bg, #fef3c7);
}

/* Transition animations */
.coach-bubble-enter-active,
.coach-bubble-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.coach-bubble-enter-from,
.coach-bubble-leave-to {
  opacity: 0;
  transform: translateY(16px);
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
  .coach-bubble {
    --color-bg-elevated: #2a2a2a;
    --color-border: #404040;
    --color-text-primary: #f0f0f0;
    --color-text-secondary: #a0a0a0;
    --color-bg-secondary: #333333;
    --color-bg-hover: #404040;
    --color-success-bg: #166534;
    --color-warning-bg: #92400e;
  }
}
</style>
