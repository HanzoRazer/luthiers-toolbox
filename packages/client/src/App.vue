<template>
  <div class="app-container">
    <AppNav />
    <main class="app-main">
      <router-view />
    </main>
    <!-- M1 Advisory Mode: Coach Bubble + Idle Detection -->
    <CoachBubble />
    <IdleDetector :threshold-ms="8000" />
  </div>
</template>

<script setup lang="ts">
import '@/styles/design-tokens.css'
import AppNav from '@/components/AppNav.vue'
import CoachBubble from '@/components/agentic/CoachBubble.vue'
import IdleDetector from '@/components/agentic/IdleDetector.vue'
</script>

<style>
/* Global styles - uses design tokens */
body {
  margin: 0;
  padding: 0;
  font-family: var(--font-family-sans);
  font-size: var(--font-size-base);
  line-height: var(--line-height-normal);
  color: var(--color-text);
  background: var(--color-surface);
}

* {
  box-sizing: border-box;
}

/* Focus visible for keyboard navigation */
:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

/* Remove default focus outline (use :focus-visible instead) */
:focus:not(:focus-visible) {
  outline: none;
}

/* Smooth scrolling (respects reduced motion) */
@media (prefers-reduced-motion: no-preference) {
  html {
    scroll-behavior: smooth;
  }
}

.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-main {
  flex: 1;
  padding: var(--space-4);
}

/* Utility classes */
.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

/* Link styles */
a {
  color: var(--color-primary);
  text-decoration: none;
  transition: color var(--transition-fast);
}

a:hover {
  color: var(--color-primary-hover);
  text-decoration: underline;
}

/* Button reset for custom buttons */
button {
  font-family: inherit;
  font-size: inherit;
}
</style>
