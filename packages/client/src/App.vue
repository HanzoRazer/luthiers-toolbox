<template>
  <div class="app-container">
    <AppNav />
    <main class="app-main">
      <router-view />
    </main>
    <!-- M1 Advisory Mode: Coach Bubble -->
    <CoachBubble />
  </div>
</template>

<script setup lang="ts">
import AppNav from '@/components/AppNav.vue';
import CoachBubble from '@/components/agentic/CoachBubble.vue';
</script>

<style>
/* Global styles can be added here */
body {
  margin: 0;
  padding: 0;
  font-family: system-ui, -apple-system, sans-serif;
}

* {
  box-sizing: border-box;
}

.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-main {
  flex: 1;
}
</style>
