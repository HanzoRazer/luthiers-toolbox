<script setup lang="ts">
/**
 * IdleDetector — Emits idle_timeout events for HESITATION moment detection.
 *
 * Tracks user activity (mousemove, keydown, click, scroll) and emits
 * an idle_timeout event after IDLE_THRESHOLD_MS of inactivity.
 *
 * Only active when VITE_AGENTIC_MODE is M1 or M2.
 */

import { onMounted, onUnmounted, computed } from "vue";
import { useAgenticEvents } from "@/composables/useAgenticEvents";

const props = defineProps<{
  /** Idle threshold in milliseconds (default: 8000) */
  thresholdMs?: number;
}>();

const IDLE_THRESHOLD_MS = props.thresholdMs ?? 8000;

const { emitIdleTimeout, store } = useAgenticEvents();

const isEnabled = computed(() => store.isEnabled);

let idleTimer: number | null = null;

function resetIdleTimer() {
  if (!isEnabled.value) return;

  if (idleTimer) {
    clearTimeout(idleTimer);
  }

  idleTimer = window.setTimeout(() => {
    emitIdleTimeout(IDLE_THRESHOLD_MS / 1000);
  }, IDLE_THRESHOLD_MS);
}

function setupListeners() {
  const events = ["mousemove", "keydown", "click", "scroll", "touchstart"];
  events.forEach((evt) => {
    window.addEventListener(evt, resetIdleTimer, { passive: true });
  });
}

function teardownListeners() {
  const events = ["mousemove", "keydown", "click", "scroll", "touchstart"];
  events.forEach((evt) => {
    window.removeEventListener(evt, resetIdleTimer);
  });
}

onMounted(() => {
  if (isEnabled.value) {
    setupListeners();
    resetIdleTimer();
  }
});

onUnmounted(() => {
  if (idleTimer) {
    clearTimeout(idleTimer);
  }
  teardownListeners();
});
</script>

<template>
  <!-- Renderless component -->
</template>
